"""Shared helper: load the model from .env so every script works with Anthropic, OpenAI or Groq."""
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DEFAULT_MODEL = "anthropic:claude-haiku-5-5"


def get_llm(temperature: float = 0):
    """Return a chat model from the MODEL string in .env, e.g. 'groq:openai/gpt-oss-120b'."""
    from langchain.chat_models import init_chat_model

    model = os.getenv("MODEL", DEFAULT_MODEL)
    provider = model.split(":", 1)[0] if ":" in model else ""
    key_var = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "groq": "GROQ_API_KEY"}.get(provider)
    key = os.getenv(key_var, "").strip() if key_var else "skip"
    if not key or key.endswith("..."):
        sys.exit(f"❌ {key_var} not found. Put your key in .env (see .env.example).")
    return init_chat_model(model)
