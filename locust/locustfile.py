from locust import HttpUser, task, constant
import random

class WebsiteUser(HttpUser):
    wait_time = constant(3)
    
    @task
    def send_random_data(self):
        # Generating a random length between 0 and 1MB (1MB = 1024*1024 bytes)
        length = random.randint(0, 100 * 1024*1024)
        
        # Generating random binary content
        data = bytearray(random.getrandbits(8) for _ in range(length))
        
        # Sending the data to the "send_data" endpoint
        self.client.post("/", data=data, headers={"content-type": "application/octet-stream"})

