# AI Engineer: book recommendation app

Run all commands below from the repository root. Docker Compose 2.20+ is required for `include`.

```sh
docker compose up --build -d --wait
# equivalent: make up
```

Open the chat at http://localhost:8501 and API docs at http://localhost:8000/docs.
The backend needs the repository's `.env` file and the existing Qdrant book collection.
The root Compose file includes `apps/docker-compose.yml`; either entrypoint now starts
the same `ai-engineer` project, with `chatbot-ui`, `api`, and `qdrant` services.

The active frontend is `apps/chatbot_ui/src/chatbot_ui/app.py`.
The older `src/app.py` and root `Dockerfile` are from the earlier direct-model demo and
are not used by Compose. Only the backend receives provider API keys.

## Request path and contract

```text
Browser (localhost:8501)
  -> Streamlit server (chatbot-ui)
  -> POST http://api:8000/rag/    {"query": "science fiction"}
  -> FastAPI -> embedding API -> Qdrant -> answer API
  <- {"answer": "..."}
```

The browser uses published host ports. Python in one container uses the other
service's name: `http://api:8000` or `http://qdrant:6333`. Inside a container,
`localhost` refers to that container.

## Debug from the outside in

Start with a reproducible symptom and a single hypothesis. Test the first boundary
you cannot prove works; change one cause, then repeat the same check.

1. **Confirm the running code.** Save your editor buffer. Check the process and
   source mount before blaming caching:

   ```sh
   docker compose ps
   docker compose top chatbot-ui
   docker inspect "$(docker compose ps -q chatbot-ui)" --format '{{json .Mounts}}'
   ```

   The command must run `chatbot_ui/app.py`, and the source mount must point at
   `apps/chatbot_ui/src`. Rebuilding a different service cannot apply your edit.

2. **Prove the backend responds without a model call.**

   ```sh
   curl -i --max-time 5 http://localhost:8000/health
   curl -i --max-time 5 http://localhost:8000/openapi.json
   docker compose logs --tail=80 api
   ```

   Health should return HTTP 200. A running container alone does not prove its
   HTTP worker started. This health check covers HTTP liveness, not Qdrant or model readiness.

3. **Test from the caller's environment.** A successful host request does not prove
   the Streamlit container can reach the API:

   ```sh
   docker compose exec -T chatbot-ui python -c "import requests; r=requests.get('http://api:8000/health', timeout=5); print(r.status_code, r.text)"
   ```

4. **Check the HTTP contract.** Verify method, path, JSON field names, status, and
   response shape. Missing required fields should produce 422 before any model call:

   ```sh
   curl -i --max-time 5 http://localhost:8000/rag/ \
     -H 'Content-Type: application/json' -d '{}'
   ```

   A real RAG check below uses the configured model APIs:

   ```sh
   curl -i --max-time 95 http://localhost:8000/rag/ \
     -H 'Content-Type: application/json' \
     -d '{"query":"Recommend one science fiction book with its rating."}'
   ```

5. **Trace the failing request.** Open UI and API logs together:

   ```sh
   docker compose logs -f --tail=100 chatbot-ui api
   ```

   If no API request appears, investigate the UI, configuration, or network first.
   If the API receives it, inspect its status and traceback. The `X-Request-ID`
   response header matches the backend log's `request_id`. Errors shown by the UI
   include this ID when the API supplies it. HTTP 422 suggests input validation;
   404 suggests a path mismatch; 500 requires the backend traceback. A timeout
   calls for checking the last completed stage (embedding, Qdrant, or generation).

## Apply the right kind of change

| Change | Action |
| --- | --- |
| Mounted `.py` file | Save; the UI reruns and Uvicorn reloads. Refresh the browser if needed. |
| Dependency or Dockerfile | `docker compose up --build -d --wait SERVICE` |
| Compose environment or `.env` | `docker compose up -d --force-recreate SERVICE` |
| Restart an unchanged process | `docker compose restart SERVICE` |

Replace `SERVICE` with `api` or `chatbot-ui`. Restarting alone does not rebuild an
image or apply changed container environment. Streamlit uses polling and reruns on
save for this Docker development setup. Existing chat history remains in Streamlit
session state; use a fresh session when testing a changed greeting.

See Docker's [Compose up behavior](https://docs.docker.com/reference/cli/docker/compose/up/)
and [include path rules](https://docs.docker.com/reference/compose-file/include/), and
Streamlit's [configuration reference](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).

## Repeatable checks

```sh
make test
```

The tests cover the current `/rag/` request/response contract, health/docs startup,
the absence of the provider sidebar, answer rendering, and connection, timeout,
HTTP, and malformed-response errors. They mock model calls and require no paid requests.
The old `/chat` provider tests have been replaced because that endpoint is no longer served.

The UI tests use [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest);
API tests use FastAPI's TestClient. Requests have explicit connect/read timeouts;
see [Requests timeout semantics](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts).
