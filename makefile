.PHONY: run-docker-compose up logs test

run-docker-compose: up

up:
	docker compose up --build -d --wait

logs:
	docker compose logs -f --tail=100 chatbot-ui api

test:
	docker compose exec -T api python -m unittest discover -s /app/apps/api/tests
	docker compose exec -T chatbot-ui python -m unittest discover -s /app/apps/chatbot_ui/tests
