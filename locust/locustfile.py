from locust import FastHttpUser, task, constant 
import os, io

class StorageUser(FastHttpUser):
    wait_time = constant(0)

    def on_start(self):
        # Get payload size from environment variable
        payload_size = int(os.environ.get("PAYLOAD_SIZE", 0))
        # Generate random binary content
        random_bytes = os.urandom(payload_size)
        # Convert bytes to file like object
        self.static_content = io.BytesIO(random_bytes)


    @task
    def store_operation(self):
        self.client.post("/", data=self.static_content, headers={"content-type": "application/octet-stream"})
