from langsmith import traceable, get_current_run_tree
from openai import OpenAI
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv


load_dotenv(
    "/Users/benny/AI-Engineer/.env",
    override=True,
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

#### Embedding function
@traceable(
        name = "embed_query",
        run_type="embedding",
        metadata={"ls_provider": "openai", "ls_model": "text-embedding-3-small"}
)
def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(
        input=text,
        model=model,
    )
    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata["usage_metadata"]= {
            "input_tokens": response.usage.prompt_tokens,
            "total_tokens": response.usage.total_tokens,
            "embedding_model": model
        }
    return response.data[0].embedding
#### Retrieval function
@traceable(
        name="retrieve_similar_books",
        run_type="retriever"

)
def retrieve_similar_books(query, qdrant_client, top_k=5):

    query_embedding = get_embedding(query)
    
    search_result = qdrant_client.query_points(
        collection_name="amazon_books_collection_sampled",
        query=query_embedding,
        limit=top_k,
    )

    retrieved_context_ids = []
    retrieved_context = []
    similarity_scores = []
    retrieved_context_ratings = []

    for result in search_result.points:
        retrieved_context_ids.append(result.payload['parent_asin'])
        retrieved_context.append(result.payload['description'])
        similarity_scores.append(result.score)
        retrieved_context_ratings.append(result.payload['average_rating'])
    
    return {
        "context_ids": retrieved_context_ids,
        "context": retrieved_context,
        "similarity_scores": similarity_scores,
        "ratings": retrieved_context_ratings
    }
    
#### format retrieved context function
@traceable(
        name='format_retrieved_context',
        run_type='prompt'
)
def process_context(retrieved_context):
    formatted_context = ""

    for id, chunk, rating in zip(retrieved_context["context_ids"], retrieved_context["context"], retrieved_context["ratings"]):
        formatted_context += f"- ID: {id}, Rating: {rating}, Description: {chunk}\n\n"
    return formatted_context
#### Create prompt function
@traceable(
        name='create_prompt',
        run_type='prompt'
)
def build_prompt(preprocessed_context, user_query):
    prompt = f"""
    You are a book recommendation assistant that can answer questions about the books in stock.

    You will be given a question and a list of context.

    Instructions:
    - You need to answer the question based on the provided context only.
    - Never use word context and refer to it as the available products
    
    Context:
    {preprocessed_context}
    
    Question: {user_query}
    
    Answer:
    """
    return prompt

#### Generate answer function
@traceable (
        name='generate_answer',
        run_type='llm',
        metadata={"ls_provider": "openai", "ls_model": "gpt-5-nano"}
) 
def generate_answer(prompt):
    response = client.chat.completions.create(
        model = 'gpt-5-nano',
        messages =[{"role": "system", "content": prompt}],
        reasoning_effort = 'minimal'
    )
    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata["usage_metadata"] = {
            "input_tokens": response.usage.prompt_tokens, # type: ignore
            "output_tokens": response.usage.completion_tokens, # type: ignore
            "total_tokens": response.usage.total_tokens, # type: ignore
            "llm_model": 'gpt-5-nano'
        }

    return response.choices[0].message.content

#### Combined RAG pipeline
@traceable(
        name='rag_pipeline'
)
def rag_pipeline(question, top_k=5):

    qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))

    retrieved_context = retrieve_similar_books(question, qdrant_client, top_k)
    processed_context = process_context(retrieved_context)
    prompt = build_prompt(processed_context, question)
    answer = generate_answer(prompt)

    final_result = {
        'answer': answer,
        'question': question,
        'retrieved_context': retrieved_context,
        'retrieved_context_ids': retrieved_context["context_ids"],
        'similarity_scores': retrieved_context["similarity_scores"]
    }
    return final_result
