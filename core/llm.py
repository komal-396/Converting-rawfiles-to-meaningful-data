"""LLM factory — Groq only."""
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from core.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE


def is_llm_configured() -> bool:
    return bool(GROQ_API_KEY)


def get_llm(temperature: float = GROQ_TEMPERATURE) -> BaseChatModel:
    """Return the Groq chat model."""
    return ChatGroq(model=GROQ_MODEL, temperature=temperature, api_key=GROQ_API_KEY)
