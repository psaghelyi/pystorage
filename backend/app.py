from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import time

app = FastAPI()

@app.post("/")
async def receive_stream(request: Request):
    total_bytes_received = 0
    start_time = time.time()
    
    # Read the incoming stream chunk by chunk
    async for chunk in request.stream():
        total_bytes_received += len(chunk)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    speed = total_bytes_received / elapsed_time / (1024 * 1024)  # MB/s
    
    # Print the statistics to the console
    print(f"Received a total of {total_bytes_received} bytes.")
    print(f"Received at a speed of {speed:.2f} MB/s.")
    
    return PlainTextResponse(f"Data received successfully at {speed:.2f} MB/s")

