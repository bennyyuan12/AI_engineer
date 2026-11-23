# Apply the Python 3.14-compatible event-loop patch before importing Ragas.
import nest_asyncio2

nest_asyncio2.apply()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import Client
from ragas import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    ResponseRelevancy,
)

from api.agents.retrieval_generation import rag_pipeline


def predict(inputs: dict) -> dict:
    return rag_pipeline(inputs["question"])


def evaluate_ragas(inputs: dict, outputs: dict, reference_outputs: dict) -> list[dict]:
    retrieved = outputs["retrieved_context"]
    sample = SingleTurnSample(
        user_input=inputs["question"],
        response=outputs["answer"],
        retrieved_contexts=[
            f"ID: {book_id}, Rating: {rating}, Description: {description}"
            for book_id, rating, description in zip(
                retrieved["context_ids"], retrieved["ratings"], retrieved["context"]
            )
        ],
        reference=reference_outputs["ground_truth"],
    )

    # Each example gets its own judge because Ragas changes the model's settings.
    judge = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1-mini", temperature=0))
    embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model="text-embedding-3-small")
    )
    metrics = [
        LLMContextRecall(llm=judge),
        LLMContextPrecisionWithReference(name="context_precision", llm=judge),
        Faithfulness(llm=judge),
        ResponseRelevancy(
            name="response_relevancy", llm=judge, embeddings=embeddings
        ),
    ]

    return [
        {"key": metric.name, "score": metric.single_turn_score(sample)}
        for metric in metrics
    ]


def main():
    return Client().evaluate(
        predict,
        data="rag-evaluation-dataset",
        evaluators=[evaluate_ragas],
        experiment_prefix="retriever",
        max_concurrency=10,
    ) # type: ignore


if __name__ == "__main__":
    main()
