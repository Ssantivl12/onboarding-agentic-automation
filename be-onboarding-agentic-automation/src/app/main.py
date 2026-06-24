from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.llm.factory import get_provider
from app.core.orchestrator import OnboardingAgent
from app.api.chat import router, set_agent

app = FastAPI(title="30X Onboarding Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

provider = get_provider()
agent = OnboardingAgent(provider)
set_agent(agent)

app.include_router(router)
