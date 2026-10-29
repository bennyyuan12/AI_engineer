import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

with patch.dict(os.environ, {
    "OPENAI_API_KEY": "test-openai-key",
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "GROK_API_KEY": "test-grok-key",
    "GOOGLE_API_KEY": "test-google-key",
}):
    from api.app import app


class ChatProviderTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.payload = {
            "provider": "OpenAI",
            "model_name": "gpt-5-nano",
            "messages": [{"role": "user", "content": "Write me a sad poem"}],
        }

    def tearDown(self):
        self.client.close()

    @patch("api.app.OpenAI")
    def test_openai_provider_case_variations(self, openai):
        openai.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="A sad poem"))]
        )
        for provider in ("OpenAI", "Openai", "openai", "OPENAI", " OpenAI "):
            with self.subTest(provider=provider):
                response = self.client.post("/chat", json={**self.payload, "provider": provider})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"message": "A sad poem"})

    @patch("api.app.Anthropic")
    def test_anthropic_provider_case_variations(self, anthropic):
        anthropic.return_value.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="A sad poem")]
        )
        for provider in ("Anthropic", "anthropic", "ANTHROPIC", " Anthropic "):
            with self.subTest(provider=provider):
                response = self.client.post("/chat", json={
                    **self.payload,
                    "provider": provider,
                    "model_name": "test-anthropic-model",
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"message": "A sad poem"})

    @patch("api.app.run_llm")
    def test_invalid_provider_returns_validation_error(self, run_llm):
        for provider in ("Groq", "", None, 123):
            with self.subTest(provider=provider):
                response = self.client.post("/chat", json={**self.payload, "provider": provider})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"], ["body", "provider"])
        run_llm.assert_not_called()

    @patch("api.app.run_llm")
    def test_invalid_token_budget_is_rejected_before_calling_model(self, run_llm):
        response = self.client.post("/chat", json={**self.payload, "max_tokens": 0})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "max_tokens"])
        run_llm.assert_not_called()

    @patch("api.app.OpenAI")
    def test_empty_model_response_returns_clear_error(self, openai):
        for content in ("", None):
            with self.subTest(content=content):
                openai.return_value.chat.completions.create.return_value = SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
                )
                response = self.client.post("/chat", json=self.payload)
                self.assertEqual(response.status_code, 502)
                self.assertIn("max_tokens", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
