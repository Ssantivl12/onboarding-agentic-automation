from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.llm.factory import get_provider
from app.core.orchestrator import OnboardingAgent
from app.api.chat import router, set_agent
from app.api.kb import router as kb_router
from app.db import init_db

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
agent = OnboardingAgent(provider)
set_agent(agent)

app.include_router(router)
app.include_router(kb_router)
