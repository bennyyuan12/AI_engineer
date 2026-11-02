from fastapi import FastAPI, HTTPException, Request, APIRouter
from pydantic import BaseModel, Field, field_validator
from api.core.config import config
import logging
from api.api.models import RAGRequest, RAGResponse
from api.agents.retrieval_generation import rag_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


rag_router = APIRouter()

app = FastAPI()

@rag_router.post("/")
def rag(
    request: Request,
    payload: RAGRequest
) -> RAGResponse:
    answer = rag_pipeline(payload.query)
    return RAGResponse(request_id=request.state.request_id, answer=answer)

api_router = APIRouter()
api_router.include_router(rag_router, prefix="/rag")
