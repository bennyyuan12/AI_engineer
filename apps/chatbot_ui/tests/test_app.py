import json
from pathlib import Path
import unittest
from unittest.mock import patch

import requests
from streamlit.testing.v1 import AppTest

from chatbot_ui.api_client import APIError, request_answer
from chatbot_ui.core.config import config


APP_FILE = Path(__file__).resolve().parents[1] / "src/chatbot_ui/app.py"


def backend_response(status=200, body=None):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body if body is not None else {"answer": "Read Dune."}).encode()
    response.headers["X-Request-ID"] = "test-request-id"
    return response


class ChatbotTests(unittest.TestCase):
    def test_ui_has_no_provider_sidebar(self):
        app = AppTest.from_file(str(APP_FILE)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.sidebar.selectbox), 0)

    @patch("chatbot_ui.api_client.requests.post")
    def test_submitted_question_displays_backend_answer(self, post):
        post.return_value = backend_response()
        app = AppTest.from_file(str(APP_FILE)).run()
        app.chat_input[0].set_value("science fiction").run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Read Dune.", [element.value for element in app.markdown])
        self.assertEqual(app.session_state["messages"][-1], {"role": "assistant", "content": "Read Dune."})
        post.assert_called_once_with(
            f"{config.API_BASE_URL.rstrip('/')}/rag/",
            json={"query": "science fiction"},
            timeout=(5, 90),
        )

    @patch("chatbot_ui.api_client.requests.post")
    def test_backend_error_is_visible_without_key_error(self, post):
        post.return_value = backend_response(503, {"detail": "Unavailable"})
        app = AppTest.from_file(str(APP_FILE)).run()
        app.chat_input[0].set_value("science fiction").run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("HTTP 503", app.error[0].value)
        self.assertIn("test-request-id", app.error[0].value)
        self.assertEqual(app.session_state["messages"][-1]["role"], "user")

    @patch("chatbot_ui.api_client.requests.post")
    def test_transport_failures_have_clear_errors(self, post):
        for error, expected in ((requests.Timeout(), "timed out"), (requests.ConnectionError(), "Could not reach")):
            with self.subTest(error=type(error).__name__):
                post.side_effect = error
                with self.assertRaisesRegex(APIError, expected):
                    request_answer("science fiction", "http://api:8000")

    @patch("chatbot_ui.api_client.requests.post")
    def test_missing_or_empty_answers_are_rejected(self, post):
        for body in ({}, {"answer": None}, {"answer": " "}, ["unexpected"]):
            with self.subTest(body=body):
                post.return_value = backend_response(body=body)
                with self.assertRaisesRegex(APIError, "no answer"):
                    request_answer("science fiction", "http://api:8000")

    @patch("chatbot_ui.api_client.requests.post")
    def test_non_json_success_is_rejected(self, post):
        response = backend_response()
        response._content = b"<html>not JSON</html>"
        post.return_value = response
        with self.assertRaisesRegex(APIError, "invalid response"):
            request_answer("science fiction", "http://api:8000")


if __name__ == "__main__":
    unittest.main()
