import re
from collections import defaultdict
from app.llm.base import LLMProvider, Message
from app.core.system_prompt import SYSTEM_PROMPT
from app.kb.loader import load_kb


class OnboardingAgent:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self._sessions: dict[str, list[Message]] = defaultdict(list)

    def chat(self, session_id: str, message: str) -> dict:
        history = list(self._sessions[session_id])
        user_msg: Message = {"role": "user", "content": message}
        messages = history + [user_msg]

        system = SYSTEM_PROMPT + load_kb()
        reply = self._provider.generate(system=system, messages=messages)

        source = _extract_tag(reply, "source")
        escalated_to = _extract_tag(reply, "escalated_to")
        clean = _strip_meta_tags(reply)

        self._sessions[session_id] = messages + [{"role": "assistant", "content": clean}]

        return {
            "reply": clean,
            "source": source,
            "escalated_to": escalated_to,
            "session_id": session_id,
        }


def _extract_tag(text: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def _strip_meta_tags(text: str) -> str:
    clean = re.sub(r"<(source|escalated_to)>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", clean).strip()
