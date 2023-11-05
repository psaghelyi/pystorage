.PHONY: run_locust

all:
	docker compose up -d --scale frontend=8 --build

clean:
	docker compose down --rmi all

log_backend:
	docker compose logs -f backend0 backend1 backend2 backend3 backend4 backend5 backend6 backend7

log_frontend:
	docker compose logs -f frontend

run_locust:
	docker run --rm --name locust -p 8089:8089 --network pystorage_net-frontend -e PAYLOAD_SIZE=1048576 -v ${PWD}/locust:/locust locustio/locust -f /locust/locustfile.py --host http://frontend:8080
