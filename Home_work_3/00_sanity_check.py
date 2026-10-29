"""Pre-work: check that the environment is installed and the model can make a tool call.

Run:  python 00_sanity_check.py
"""
import os
import sys
from importlib.metadata import version

from langchain_core.tools import tool

from common import get_llm


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def main() -> None:
    print(f"Python          {sys.version.split()[0]}")
    for pkg in ("langgraph", "langchain", "langchain-core"):
        print(f"{pkg:<16}{version(pkg)}")
    print(f"MODEL           {os.getenv('MODEL', '(default)')}\n")

    llm = get_llm().bind_tools([add])
    msg = llm.invoke("What is 2 + 40? You must use the add tool.")

    if not msg.tool_calls:
        sys.exit(f"❌ The model answered without calling the tool:\n{msg.content}")

    call = msg.tool_calls[0]
    result = add.invoke(call["args"])
    print(f"Tool call:  {call['name']}({call['args']}) -> {result}")
    print("✅ Environment is ready")


if __name__ == "__main__":
    main()
