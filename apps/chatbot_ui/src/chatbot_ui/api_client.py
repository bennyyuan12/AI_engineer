import requests


class APIError(RuntimeError):
    """A backend failure that the chat UI can display without crashing."""


def request_answer(query: str, base_url: str) -> str:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/rag/",
            json={"query": query},
            timeout=(5, 90),
        )
    except requests.exceptions.Timeout as exc:
        raise APIError("The book service timed out. Please try again.") from exc
    except requests.exceptions.RequestException as exc:
        raise APIError("Could not reach the book service. Please try again shortly.") from exc

    if not response.ok:
        message = f"The book service returned HTTP {response.status_code}."
        request_id = response.headers.get("X-Request-ID")
        if request_id:
            message += f" Request ID: {request_id}"
        raise APIError(message)

    try:
        data = response.json()
    except ValueError as exc:
        raise APIError("The book service returned an invalid response.") from exc

    if not isinstance(data, dict) or not isinstance(data.get("answer"), str) or not data["answer"].strip():
        raise APIError("The book service returned no answer. Please try again.")
    return data["answer"]
