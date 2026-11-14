import os
import random
import sys

from langfuse.openai import openai
from langfuse import observe, propagate_attributes
from langfuse import Langfuse

# Add the repo root to path so we can import from shared/
sys.path.append(os.path.abspath(".."))
from shared.shopbot_config import SHOPBOT_SYSTEM_PROMPT

LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI()
langfuse = Langfuse()

print("Setup complete — Langfuse client initialised")
print(f"Traces will appear at: {LANGFUSE_BASE_URL}")


@observe(name="chatbot")
def ask_bot(user_message: str) -> str:
    properties = {"feature": "bot", "channel": "cli"}

    # Attach metadata to the observed function.
    langfuse.update_current_span(metadata=properties)

    # Propagate standard IDs, tags, and metadata to nested observations.
    with propagate_attributes(
        user_id="user_" + str(random.randint(1000, 9999)),
        session_id="session_" + str(random.randint(1000, 9999)),
        tags=["shopbot", "support"],
        metadata=properties,
    ):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SHOPBOT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
    return response.choices[0].message.content

print(ask_bot("What is your return policy?"))
print(ask_bot("What is your refund method?"))
print(ask_bot("What are your customer support hours?"))
print(ask_bot("Do you offer free shipping?"))
