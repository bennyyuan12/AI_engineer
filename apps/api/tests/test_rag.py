import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


with patch.dict(os.environ, {
    "OPENAI_API_KEY": "test-openai-key",
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "GROK_API_KEY": "test-grok-key",
    "GOOGLE_API_KEY": "test-google-key",
}), patch("openai.OpenAI") as openai, patch("qdrant_client.QdrantClient") as qdrant:
    from api.app import app
    openai.return_value.embeddings.create.assert_not_called()
    openai.return_value.chat.completions.create.assert_not_called()
    qdrant.assert_not_called()


class RAGApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    @patch("api.api.endpoints.rag_pipeline")
    def test_health_and_docs_do_not_call_the_model(self, pipeline):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        for path in ("/docs", "/openapi.json"):
            self.assertEqual(self.client.get(path).status_code, 200)
        pipeline.assert_not_called()

    @patch("api.api.endpoints.rag_pipeline", return_value="A science fiction recommendation")
    def test_rag_contract(self, pipeline):
        response = self.client.post("/rag/", json={"query": "science fiction"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "A science fiction recommendation"})
        self.assertTrue(response.headers["X-Request-ID"])
        pipeline.assert_called_once_with("science fiction")

    @patch("api.api.endpoints.rag_pipeline")
    def test_invalid_query_is_rejected_before_the_model(self, pipeline):
        response = self.client.post("/rag/", json={"wrong_field": "science fiction"})
        self.assertEqual(response.status_code, 422)
        pipeline.assert_not_called()


if __name__ == "__main__":
    unittest.main()
