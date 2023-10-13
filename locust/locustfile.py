from locust import HttpUser, task, constant, events
import random


data = bytearray(random.getrandbits(8) for _ in range(1024 * 1024))

class WebsiteUser(HttpUser):
    wait_time = constant(0)
    
    @task
    def send_random_data(self):
        self.client.post("/", data=data, headers={"content-type": "application/octet-stream"})

