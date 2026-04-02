.PHONY: build up down logs pull-model test shell

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

pull-model:
	docker compose exec ollama ollama pull qwen2.5:7b

test:
	docker compose exec app pytest tests/ -v

shell:
	docker compose exec app /bin/bash
