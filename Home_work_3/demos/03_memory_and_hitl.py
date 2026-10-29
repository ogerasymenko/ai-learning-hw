"""Demo 3. Checkpointer (memory per thread_id), state inspection, time travel and human-in-the-loop.

Run:  python demos/03_memory_and_hitl.py
"""
import os
import sys
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
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

graph = builder.compile(checkpointer=InMemorySaver())   # interrupt doesn't work without a checkpointer


def say(text: str, thread_id: str) -> None:
    cfg = {"configurable": {"thread_id": thread_id}}
    print(f"\n[thread {thread_id}] USER: {text}")
    result = graph.invoke({"messages": [("user", text)]}, cfg)

    while "__interrupt__" in result:                      # the graph is paused
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

    print(f"[thread {thread_id}] AI: {result['messages'][-1].text}")


if __name__ == "__main__":
    print("═══ 1. Short-term memory = checkpointer + thread_id ═══")
    say("Hi! My name is Alex and I write Python.", "1")
    say("What's my name?", "1")
    say("What's my name?", "2")          # new thread: the agent remembers nothing

    print("\n═══ 2. Inspecting state ═══")
    cfg = {"configurable": {"thread_id": "1"}}
    snapshot = graph.get_state(cfg)
    print("messages in state:", len(snapshot.values["messages"]))
    print("next node:", snapshot.next or "(graph finished)")

    print("\n═══ 3. Time travel: checkpoint history ═══")
    history = list(graph.get_state_history(cfg))
    for s in history[:6]:
        print(f"  step={s.metadata.get('step'):>2}  next={s.next}  msgs={len(s.values.get('messages', []))}")
    print(f"  ... total checkpoints: {len(history)}")
    # To replay from any checkpoint: graph.invoke(None, s.config)

    print("\n═══ 4. Human-in-the-loop ═══")
    # The LLM writes the email itself; the graph pauses before sending it
    say("Prepare an email to boss@example.com: the quarterly report is finished "
        "and I'd like 15 minutes on Friday to walk them through it.", "3")
