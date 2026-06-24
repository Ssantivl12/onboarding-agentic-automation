import json
import re
from collections import defaultdict
from dataclasses import dataclass

from app.config import settings
from app.core.system_prompt import ANSWERABILITY_PROMPT, QUERY_REWRITE_PROMPT, RAG_SYSTEM_PROMPT
from app.llm.base import LLMProvider, Message
from app.rag.retriever import RagRetriever, RetrievedChunk


@dataclass(frozen=True)
class Answerability:
    answerable: str
    reason: str
    source_ids: list[str]


class OnboardingAgent:
    def __init__(self, provider: LLMProvider, retriever: RagRetriever) -> None:
        self._provider = provider
        self._retriever = retriever
        self._sessions: dict[str, list[Message]] = defaultdict(list)

    def chat(self, session_id: str, message: str) -> dict:
        history = list(self._sessions[session_id])
        user_msg: Message = {"role": "user", "content": message}
        search_query = self._build_search_query(history, message)
        chunks = self._retriever.search(search_query, top_k=settings.rag_top_k)

        if not chunks:
            clean = (
                "Eso no esta en los documentos de onboarding cargados. "
                "Te conviene preguntarle al Chief of Staff."
            )
            self._sessions[session_id] = history + [user_msg, {"role": "assistant", "content": clean}]
            return {
                "reply": clean,
                "source": None,
                "escalated_to": "Chief of Staff",
                "session_id": session_id,
            }

        assessment = self._assess_answerability(message, chunks)
        if assessment.answerable == "missing":
            clean = (
                "Eso no esta en los documentos de onboarding cargados. "
                "Te conviene preguntarle al Chief of Staff."
            )
            self._sessions[session_id] = history + [user_msg, {"role": "assistant", "content": clean}]
            return {
                "reply": clean,
                "source": None,
                "escalated_to": "Chief of Staff",
                "session_id": session_id,
            }

        if assessment.answerable == "ambiguous":
            clean = "Necesito una aclaracion breve para responder sin asumir informacion fuera de los documentos."
            self._sessions[session_id] = history + [user_msg, {"role": "assistant", "content": clean}]
            return {
                "reply": clean,
                "source": None,
                "escalated_to": None,
                "session_id": session_id,
            }

        selected_chunks = _select_chunks(chunks, assessment.source_ids)
        context = _format_chunks(selected_chunks)
        final_user_msg: Message = {
            "role": "user",
            "content": (
                f"CONTEXTO RECUPERADO:\n{context}\n\n"
                f"ESTADO DE COBERTURA: {assessment.answerable}\n"
                f"NOTA DE COBERTURA: {assessment.reason}\n\n"
                f"PREGUNTA DEL USUARIO:\n{message}"
            ),
        }
        reply = self._provider.generate(system=RAG_SYSTEM_PROMPT, messages=[*history[-6:], final_user_msg])

        source = _extract_tag(reply, "source") or _fallback_source(selected_chunks)
        escalated_to = _extract_tag(reply, "escalated_to")
        clean = _strip_meta_tags(reply)

        self._sessions[session_id] = history + [user_msg, {"role": "assistant", "content": clean}]

        return {
            "reply": clean,
            "source": source,
            "escalated_to": escalated_to,
            "session_id": session_id,
        }

    def _build_search_query(self, history: list[Message], message: str) -> str:
        if not history:
            return message

        try:
            rewritten = self._provider.generate(
                system=QUERY_REWRITE_PROMPT,
                messages=[*history[-6:], {"role": "user", "content": message}],
            ).strip()
        except Exception:
            return message

        return rewritten.strip('"` \n') or message

    def _assess_answerability(self, message: str, chunks: list[RetrievedChunk]) -> Answerability:
        if not settings.rag_enable_answerability:
            return Answerability("complete", "Answerability gate disabled.", [str(chunk.chunk_id) for chunk in chunks])

        payload = {
            "question": message,
            "chunks": [
                {
                    "source_id": str(chunk.chunk_id),
                    "source": chunk.source_label,
                    "content": chunk.content,
                }
                for chunk in chunks
            ],
        }
        try:
            raw = self._provider.generate(
                system=ANSWERABILITY_PROMPT,
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            )
            data = _extract_json(raw)
            answerable = str(data.get("answerable", "complete")).lower()
            if answerable not in {"complete", "partial", "missing", "ambiguous"}:
                answerable = "complete"
            source_ids = data.get("source_ids", [])
            if not isinstance(source_ids, list):
                source_ids = []
            return Answerability(
                answerable=answerable,
                reason=str(data.get("reason", "")),
                source_ids=[str(item) for item in source_ids],
            )
        except Exception:
            return Answerability("complete", "Answerability fallback: using retrieved context.", [str(chunk.chunk_id) for chunk in chunks])


def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for chunk in chunks:
        parts.append(
            "\n".join(
                [
                    f"[source_id: {chunk.chunk_id}]",
                    f"[source: {chunk.source_label}]",
                    chunk.content,
                ]
            )
        )
    return "\n\n---\n\n".join(parts)


def _select_chunks(chunks: list[RetrievedChunk], source_ids: list[str]) -> list[RetrievedChunk]:
    if not source_ids:
        return chunks
    wanted = set(source_ids)
    selected = [chunk for chunk in chunks if str(chunk.chunk_id) in wanted]
    return selected or chunks


def _fallback_source(chunks: list[RetrievedChunk]) -> str | None:
    if not chunks:
        return None
    labels = []
    for chunk in chunks:
        if chunk.source_label not in labels:
            labels.append(chunk.source_label)
    return ", ".join(labels)


def _extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end >= start:
        candidate = candidate[start : end + 1]
    data = json.loads(candidate)
    if not isinstance(data, dict):
        raise ValueError("Answerability response must be a JSON object.")
    return data


def _extract_tag(text: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def _strip_meta_tags(text: str) -> str:
    clean = re.sub(r"<(source|escalated_to)>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", clean).strip()
