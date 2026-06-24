from fastapi import APIRouter
from pydantic import BaseModel
from app.core.orchestrator import OnboardingAgent

router = APIRouter()
_agent: OnboardingAgent | None = None


def set_agent(agent: OnboardingAgent) -> None:
    global _agent
    _agent = agent


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    source: str | None
    escalated_to: str | None
    session_id: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    assert _agent is not None, "Agent not initialized"
    result = _agent.chat(session_id=req.session_id, message=req.message)
    return ChatResponse(**result)


@router.get("/health")
def health() -> dict:
    return {"ok": True}
