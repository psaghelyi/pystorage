from locust import HttpUser, FastHttpUser, task, constant 
import os

# Get the payload size from the environment variable
payload_size = int(os.environ.get("PAYLOAD_SIZE", -1))
if payload_size < 0:
    raise Exception("Invalid payload size.")
print(f"payload_size: {payload_size}")

class DynamicContentFile:
    def __init__(self, total_size, chunk_size=16384):
        self.total_size = total_size
        self.chunk_size = chunk_size
        self.generated = 0

    def read(self, size=-1):
        if size < 0:
            size = self.chunk_size
        if self.generated >= self.total_size:
            return b''  # No more data to generate

        to_generate = min(self.total_size - self.generated, size)
        self.generated += to_generate
        return os.urandom(to_generate)

class StorageUser(FastHttpUser):
    wait_time = constant(0)

    @task
    def store_operation(self):
        # Stream the file content
        dynamic_content = DynamicContentFile(payload_size)
        self.client.put("/", files={'media': dynamic_content})
        