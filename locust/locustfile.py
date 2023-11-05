from locust import HttpUser, FastHttpUser, task, constant 
import os, io

class StorageUser(FastHttpUser):
    wait_time = constant(0)

    def on_start(self):
        payload_size = int(os.environ.get("PAYLOAD_SIZE", -1))
        if payload_size < 0:
            raise Exception("Invalid payload size.")
        print(f"payload_size: {payload_size}")
        random_bytes = os.urandom(payload_size)
        self.content = io.BytesIO(random_bytes)

    @task
    def store_operation(self):
        self.content.seek(0)
        self.client.put("/", files={'media': self.content})
