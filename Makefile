all:
	docker compose up -d --scale frontend=8 --build

clean:
	docker compose down --rmi all

log_backend:
	docker compose logs -f backend

log_frontend:
	docker compose logs -f frontend
