from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router, set_agent
from app.api.kb import router as kb_router
from app.api.rag import router as rag_router, set_retriever
from app.core.orchestrator import OnboardingAgent
from app.db import init_db
from app.llm.factory import get_provider
from app.rag.embeddings import get_embedder
from app.rag.retriever import RagRetriever

app = FastAPI(title="30X Onboarding Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()

provider = get_provider()
embedder = get_embedder()
retriever = RagRetriever(embedder)
agent = OnboardingAgent(provider, retriever)
set_agent(agent)
set_retriever(retriever)

app.include_router(router)
app.include_router(kb_router)
app.include_router(rag_router)
