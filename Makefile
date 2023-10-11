all:
	docker compose up -d --scale frontend=8 --scale locust-worker=4 --build

clean:
	docker compose down

log_backend:
	docker compose logs -f backend

log_frontend:
	docker compose logs -f frontend
