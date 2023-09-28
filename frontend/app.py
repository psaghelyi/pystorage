from fastapi import FastAPI, HTTPException, Request
from pyeclib.ec_iface import ECDriver
from typing import List
import aiohttp
import asyncio

app = FastAPI()

# Reed-Solomon parameters
k = 6  # Number of data chunks
m = 2  # Number of parity chunks

ec_driver = ECDriver(k=k, m=m, ec_type="liberasurecode_rs_vand")

# Buffers to hold encoded data before sending
buffers = [asyncio.Queue() for _ in range(k + m)]

# List of endpoints where data will be sent
endpoints = [f"http://backend:9000" for i in range(k + m)]

running = True
failed_count = 0
max_failures = m - 1
state_lock = asyncio.Lock()

@app.post("/")
async def receive_data(request: Request):
    print(f'incoming request {request.url}')
    global running, failed_count
    running = True
    failed_count = 0
    tasks = [write_to_endpoint(buffers[i], endpoints[i]) for i in range(k + m)]
    try:
        async for data_chunk in request.stream():
            if not data_chunk or not running:
                break
        
            encoded_data = ec_driver.encode(data_chunk)
            for idx, chunk in enumerate(encoded_data):
                await buffers[idx].put(chunk)

            async with state_lock:
                if failed_count > max_failures:  # Check if we should stop
                    running = False
                    break

        # Signal end of stream to all sender tasks by placing sentinel in buffers
        for buf in buffers:
            await buf.put(None)

        # Wait for all sender tasks to complete
        await asyncio.gather(*tasks)
        
    except Exception as e:
        async with state_lock:
            running = False
        print(f"Error while encoding or sending data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"status": "success"}


async def stream_from_buffer(buffer: asyncio.Queue):
    global running
    while running:
        chunk = await buffer.get()
        if chunk is None:  # Sentinel value encountered
            break
        yield chunk


async def write_to_endpoint(buffer: asyncio.Queue, endpoint: str):
    global running, failed_count
    async with aiohttp.ClientSession() as session:
        # Prepare the session for streaming
        headers = {"Content-Type": "application/octet-stream"}
        try:
            # Start the stream to the backend
            async with session.post(endpoint, headers=headers, data=stream_from_buffer(buffer)) as response:
                # Handle non-200 response status
                if response.status != 200:
                    raise Exception(f"Failed to send data to {endpoint}. Status: {response.status}")

        except Exception as e:
            print(f"Error with endpoint {endpoint}: {e}")
            async with state_lock:  # Acquire lock before modifying the shared state
                failed_count += 1
                if failed_count > max_failures:
                    running = False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
