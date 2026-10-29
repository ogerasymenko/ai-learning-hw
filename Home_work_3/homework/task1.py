"""Task 1. Memory that survives a restart: the demo-3 agent with a SQLite checkpointer.

Each run says ONE thing, so memory has to come from memory.db, not from the process:

    python homework/task1.py "My name is Alex"            # run 1
    python homework/task1.py "What's my name?"            # run 2 (separate process) -> Alex
    python homework/task1.py "What's my name?" other      # different thread_id -> knows nothing
    rm homework/memory.db                                 # the agent forgets again

Usage: task1.py "<message>" [thread_id]   (thread_id defaults to "1")
"""
import os
import sqlite3
import sys
from pathlib import Path
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt

from common import get_llm


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email. `body` must be the complete, ready-to-send email text.
    This is a dangerous action: a human approves it before it runs."""
    return f"Email to {to} with subject '{subject}' sent."


TOOLS = [send_email]
llm = get_llm().bind_tools(TOOLS)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


SYSTEM = SystemMessage(
    "You are a helpful assistant that writes and sends emails with the send_email tool. "
    "When the user asks you to prepare, write, draft or send an email, compose it yourself: "
    "a clear subject and a complete, polite body with a greeting and a sign-off, based on what "
    "the user said. Then call send_email right away with that subject and body. "
    "Never ask the user to confirm in plain text and never just show a draft: a human approval "
    "step is built into the system and runs automatically before any email is sent. "
    "If the human rejects the email, rewrite it according to their feedback and call send_email again."
)


def agent(state: State) -> dict:
    return {"messages": [llm.invoke([SYSTEM, *state["messages"]])]}


def human_approval(state: State) -> Command[Literal["tools", "agent"]]:
    """Pause before a dangerous tool. The graph is saved in the checkpointer and waits for Command(resume=...)."""
    last = state["messages"][-1]
    answer = interrupt({
        "question": "Run these tool calls? (yes / reason for rejecting)",
        "tool_calls": [{"name": c["name"], "args": c["args"]} for c in last.tool_calls],
    })
    if str(answer).strip().lower() in {"yes", "y"}:
        return Command(goto="tools")
    # Rejected: every tool_call needs a ToolMessage reply, or the model call fails on the next step
    rejected = [
        ToolMessage(content=f"The human rejected this call: {answer}", tool_call_id=c["id"])
        for c in last.tool_calls
    ]
    return Command(goto="agent", update={"messages": rejected})


builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("human_approval", human_approval)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition, {"tools": "human_approval", END: END})
builder.add_edge("tools", "agent")

# Stored next to this script, so the same memory.db is used whatever the current directory is.
DB_PATH = Path(__file__).resolve().parent / "memory.db"
checkpointer = SqliteSaver(sqlite3.connect(DB_PATH, check_same_thread=False))
graph = builder.compile(checkpointer=checkpointer)   # interrupt doesn't work without a checkpointer


def approve(result: dict, cfg: dict) -> dict:
    """While the graph is paused at human_approval, ask the human and resume."""
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print(f"⏸  {payload['question']}")
        for c in payload["tool_calls"]:
            args = c["args"]
            if c["name"] == "send_email":
                print(f"    To:      {args.get('to')}")
                print(f"    Subject: {args.get('subject')}")
                print("    " + "─" * 50)
                for line in str(args.get("body", "")).splitlines():
                    print(f"    {line}")
                print("    " + "─" * 50)
            else:
                print(f"    {c['name']}({args})")
        answer = input("    your answer > ")
        result = graph.invoke(Command(resume=answer), cfg)  # resume from the same spot
    return result


def say(text: str, thread_id: str) -> None:
    cfg = {"configurable": {"thread_id": thread_id}}
    saved = graph.get_state(cfg)
    print(f"[thread {thread_id}] messages already saved in {DB_PATH.name}: {len(saved.values.get('messages', []))}")

    # A previous run may have been stopped while waiting for approval: settle that first.
    pending = [i for t in saved.tasks for i in t.interrupts]
    if pending:
        print("(this thread was waiting for your approval from an earlier run)")
        approve({"__interrupt__": pending}, cfg)

    print(f"[thread {thread_id}] USER: {text}")
    result = approve(graph.invoke({"messages": [("user", text)]}, cfg), cfg)
    print(f"[thread {thread_id}] AI: {result['messages'][-1].text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    say(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "1")
