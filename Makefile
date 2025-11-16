run:
	docker compose up --build

migrate:
	docker compose exec backend python backend/manage.py migrate

createsuperuser:
	docker compose exec backend python backend/manage.py createsuperuser