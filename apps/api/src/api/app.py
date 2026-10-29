from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from openai import OpenAI
from anthropic import Anthropic 
from api.core.config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_llm(provider,model_name,messages,max_tokens=4096):
    if provider == "OpenAI":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens
        )
        return response.choices[0].message.content
    elif provider == "Anthropic":
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            messages=messages
        )
        return "".join(block.text for block in response.content if block.type == "text")
    else:
        raise ValueError("Unsupported provider")

class ChatRequest(BaseModel):
    provider: Literal["OpenAI", "Anthropic"]
    model_name: str
    messages: list[dict]
    max_tokens: int = Field(default=4096, ge=1)

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: object) -> object:
        if isinstance(value, str):
            return {
                "openai": "OpenAI",
                "anthropic": "Anthropic",
            }.get(value.strip().casefold(), value)
        return value

class ChatResponse(BaseModel):
    message: str

app = FastAPI()
@app.post("/chat")
def chat(
    request: Request,
    payload: ChatRequest
) -> ChatResponse:
    result = run_llm(
        payload.provider, payload.model_name, payload.messages, max_tokens=payload.max_tokens
    )
    if not result:
        raise HTTPException(
            status_code=502,
            detail="The model returned no text. Try increasing max_tokens.",
        )
    return ChatResponse(message=result)
