from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import time
import logging


# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

app = FastAPI()

@app.post("/")
async def receive_stream(request: Request, backend_id: str = None):
    total_bytes_received = 0
    start_time = time.time()
    
    # Read the incoming stream chunk by chunk
    async for chunk in request.stream():
        total_bytes_received += len(chunk)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    speed = total_bytes_received / elapsed_time / (1024 * 1024)  # MB/s
    
    #logging.info(f"Received a total of {total_bytes_received} bytes.")
    #logging.info(f"Received at a speed of {speed:.2f} MB/s.")
    #if backend_id:
    #    logging.info(f"Target backend ID: {backend_id}")
        
    return PlainTextResponse(f"Data received successfully at {speed:.2f} MB/s")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="debug")