from fastapi import FastAPI, HTTPException, Request
from pyeclib.ec_iface import ECDriver
import aiohttp
import asyncio
import logging

# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

app = FastAPI()

# Reed-Solomon parameters
k = 6
m = 2
ec_driver = ECDriver(k=k, m=m, ec_type="liberasurecode_rs_vand")

endpoints = [f"http://backend{i}:900{i}" for i in range(k + m)]
max_failures = m // 2  # maximum number of failures to tolerate is half of the number of parity chunks
max_buffer_size = 64  # maximum number of chunks to buffer in memory


class Frontend:
    def __init__(self):
        self.buffers = [asyncio.Queue(maxsize=max_buffer_size) for _ in range(k + m)]
        self.state_lock = asyncio.Lock()
        self.failed_count = 0

    async def receive_data(self, request: Request):
        tasks = [self.write_to_endpoint(i) for i in range(k + m)]
        try:
            async for chunk in request.stream():
                if not chunk:
                    #logging.info("End of incomming stream")
                    break

                encoded_data = ec_driver.encode(chunk)
                #logging.info(f"Chunk encoded: {len(chunk)}")
                for idx, strip in enumerate(encoded_data):
                    await self.buffers[idx].put(strip)

            # place sentinel values in the queues to signal the end of the stream
            #logging.info("Placing sentinels to buffers")
            for buffer in self.buffers:
                await buffer.put(None)

        except Exception as e:
            logging.error(f"Error while encoding or sending data: {e}")
            async with self.state_lock:
                self.failed_count = max_failures + 1  # force the failure count to go over the threshold

        finally:
            await asyncio.gather(*tasks)

        if self.failed_count > max_failures:
            logging.error("Number of failed backends went over threshold.")
            raise HTTPException(status_code=500, detail="Internal Server Error")

        return {"status": "success"}

    async def stream_from_buffer(self, backend_id):
        buffer = self.buffers[backend_id]
        while True:
            chunk = await buffer.get()
            if chunk is None:
                #logging.info(f"backend{backend_id} - End of buffer")
                break
            #logging.info(f"backend{backend_id} - Chunk read from buffer: {len(chunk)}")
            yield chunk

    async def write_to_endpoint(self, backend_id):
        endpoint = endpoints[backend_id]
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/octet-stream"}
            url = f"{endpoint}?backend_id={backend_id}"
            try:
                async with session.post(url=url, headers=headers, data=self.stream_from_buffer(backend_id)) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to send data to {endpoint}. Status: {response.status}")

            except Exception as e:
                logging.error(f"Error with endpoint {url}: {e}")
                async with self.state_lock:
                    self.failed_count += 1
                    #logging.info(f"Failed count: {self.failed_count}")
                        
                # Flush the buffer for this backend
                buffer = self.buffers[backend_id]
                while await buffer.get() is not None:
                    pass


@app.post("/")
async def receive_data(request: Request):
    frontend = Frontend()
    return await frontend.receive_data(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
