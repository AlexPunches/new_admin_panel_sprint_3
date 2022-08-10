build:
	docker-compose -f 01_etl/docker-compose.yml build
up:
	docker-compose -f 01_etl/docker-compose.yml up -d
makemigrations:
	docker-compose -f 01_etl/docker-compose.yml exec service python manage.py makemigrations
migrate:
	docker-compose -f 01_etl/docker-compose.yml exec service python manage.py migrate
load-data:
	docker-compose -f 01_etl/docker-compose.yml run etl python sqlite_to_postgres/load_data.py
pytest:
	docker-compose -f 01_etl/docker-compose.yml run etl pytest -v
down:
	docker-compose -f 01_etl/docker-compose.yml down
logs:
	docker-compose -f 01_etl/docker-compose.yml logs -f
load-es-movies:
	docker-compose -f 01_etl/docker-compose.yml run etl python postgres_to_es/load_indexes.py
