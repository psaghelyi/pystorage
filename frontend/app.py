from math import log
from fastapi import FastAPI, HTTPException, Request
from pyeclib.ec_iface import ECDriver
import aiohttp
import asyncio
import logging
import random

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARNING)

app = FastAPI()

# Reed-Solomon parameters
K = 6
M = 2
ec_driver = ECDriver(k=K, m=M, ec_type="liberasurecode_rs_vand")

endpoints = [f"http://backend{i}:9000" for i in range(K + M)]
sessions = [aiohttp.ClientSession() for i in range(K + M)]  # HTTP1.1 keep alive
# maximum number of failures to tolerate is half of the number of parity chunks
MAX_FAILURES = M // 2
MAX_BUFFER_SIZE = 64  # maximum number of chunks to buffer in memory
STREAM_SIZE_THRESHOLD = 100 * 1024  # 100 KB


class Frontend:
    def __init__(self):
        self.buffers = [asyncio.Queue(maxsize=MAX_BUFFER_SIZE) for _ in range(K + M)]
        self.state_lock = asyncio.Lock()
        self.failed_count = 0

    async def receive_data(self, request: Request):
        stream_size = 0
        # Random M + 1 nodes for replication if needed
        replication_nodes = random.sample(range(K + M), M + 1)
        replication_chunks = []
        tasks = []

        try:
            async for chunk in request.stream():
                if not chunk:
                    break

                stream_size += len(chunk)

                if stream_size <= STREAM_SIZE_THRESHOLD:
                    replication_chunks.append(chunk)
                else:
                    if replication_chunks:
                        # logging.info("Switching to FEC mode...")
                        tasks = [self.write_to_endpoint(i) for i in range(K + M)]
                        # Process the replication buffer first
                        for replication_chunk in replication_chunks:
                            encoded_data = ec_driver.encode(replication_chunk)
                            for idx, strip in enumerate(encoded_data):
                                await self.buffers[idx].put(strip)
                        # Clear the replication buffer after switching to FEC
                        replication_chunks = []

                    # Continue in FEC mode for the rest of the stream                    
                    encoded_data = ec_driver.encode(chunk)
                    for idx, strip in enumerate(encoded_data):
                        await self.buffers[idx].put(strip)

            # If stream ended and we are still in replication mode
            if replication_chunks:
                tasks = [self.write_to_endpoint(i) for i in replication_nodes]
                # Send replicated chunks to the selected M nodes
                for idx in replication_nodes:
                    # logging.info(f"Sending replicated chunk to backend {idx}...")
                    for chunk in replication_chunks:
                        await self.buffers[idx].put(chunk)

            # Place sentinels in every buffer to signal the end of the stream
            for buffer in self.buffers:
                await buffer.put(None)

        except Exception as e:
            logging.error(f"Error while encoding or sending data: {e}")
            async with self.state_lock:
                # force the failure count to go over the threshold
                self.failed_count = MAX_FAILURES + 1

        finally:
            await asyncio.gather(*tasks)

        if self.failed_count > MAX_FAILURES:
            logging.error("Number of failed backends went over threshold.")
            raise HTTPException(
                status_code=500, detail="Internal Server Error")

        return {"status": "success"}

    async def stream_from_buffer(self, backend_id):
        buffer = self.buffers[backend_id]
        while True:
            chunk = await buffer.get()
            if chunk is None:
                # logging.info(f"backend{backend_id} - End of buffer")
                break
            # logging.info(f"backend{backend_id} - Chunk read from buffer: {len(chunk)}")
            yield chunk

    async def write_to_endpoint(self, backend_id):
        endpoint = endpoints[backend_id]
        session = sessions[backend_id]
        headers = {"Content-Type": "application/octet-stream"}
        url = f"{endpoint}?backend_id={backend_id}"
        try:
            async with session.post(url=url, headers=headers, data=self.stream_from_buffer(backend_id)) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to send data to {endpoint}. Status: {response.status}")

        except Exception as e:
            logging.error(f"Error with endpoint {url}: {e}")
            async with self.state_lock:
                self.failed_count += 1
                # logging.info(f"Failed count: {self.failed_count}")

            # Flush the buffer for this backend
            buffer = self.buffers[backend_id]
            while await buffer.get() is not None:
                pass


@app.post("/")
async def receive_data(request: Request):
    frontend = Frontend()
    return await frontend.receive_data(request)


@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown...")
    for session in sessions:
        await session.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
