"""Demo 2. A ReAct agent built by hand: agent -> tools -> agent -> ... -> END.

Run:  python demos/02_react_agent.py
"""
import os
import sys
from typing import Annotated, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from common import get_llm


@tool
def get_weather(city: str) -> str:
    """Current weather in a city."""
    fake = {"london": "12°C, rain", "berlin": "9°C, cloudy", "lisbon": "21°C, sunny"}
    return fake.get(city.lower(), "15°C, partly cloudy")


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


TOOLS = [get_weather, multiply]
llm = get_llm().bind_tools(TOOLS)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def agent(state: State) -> dict:
    system = SystemMessage(
        "You are a helpful assistant with tools. Always use get_weather for any weather question "
        "and multiply for any multiplication: never guess or compute these yourself. "
        "Call the tools directly instead of asking the user for confirmation, "
        "then answer using the tool results."
    )
    return {"messages": [llm.invoke([system, *state["messages"]])]}


builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)   # tool_calls -> "tools", otherwise -> END
builder.add_edge("tools", "agent")                          # here's the loop
graph = builder.compile()


if __name__ == "__main__":
    question = "Is it warmer in London or in Lisbon right now? And what is the temperature difference multiplied by 3?"
    print(f"USER: {question}\n")
    for update in graph.stream({"messages": [("user", question)]}, stream_mode="updates"):
        for node, payload in update.items():
            for m in payload["messages"]:
                if getattr(m, "tool_calls", None):
                    calls = ", ".join(f"{c['name']}({c['args']})" for c in m.tool_calls)
                    print(f"[{node}] calls tools: {calls}")
                elif m.type == "tool":
                    print(f"[{node}] {m.name} -> {m.content}")
                else:
                    print(f"[{node}] {m.text}")
