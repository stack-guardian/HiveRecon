.PHONY: build up down logs test shell

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

test:
	docker compose exec app pytest tests/ -v

shell:
	docker compose exec app /bin/bash
