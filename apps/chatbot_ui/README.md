# Chatbot UI

Run the Streamlit frontend and FastAPI backend from the repository root:

```sh
docker compose -f apps/docker-compose.yml up --build
```

Open http://localhost:8501 for the chatbot, or http://localhost:8000/docs for the API.
The API loads its provider keys from the repository's `.env` file.

The frontend uses `API_BASE_URL`, which defaults to `http://localhost:8000`.
Compose sets it to `http://api:8000` so the frontend can reach the backend container.
Only the backend needs provider API keys.

To run the frontend locally against a backend already running on port 8000:

```sh
uv run --package chatbot-ui streamlit run apps/chatbot_ui/src/chatbot_ui/app.py
```
