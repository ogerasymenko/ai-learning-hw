"""Task 4. A notes assistant with real tools: safe tools run freely, the dangerous one always asks a human.

Graph (a ReAct loop with an approval gate):

  START → agent ──no tool calls──────────────────────────→ END
            │  ↑
            │  └────────── tools ←── only safe calls ───┐
            │ tool calls                                 │
            └─ any write_note? ──yes──→ human_approval ──┴─ yes → tools
                                              │ no (feedback) → agent (revises and asks again)

Tools (all restricted to the notes/ folder next to this file):
  list_notes()              safe       what notes exist
  read_note(name)           safe       read one note
  write_note(name, text)    DANGEROUS  always pauses; shows exactly what will be written

Run:  python homework/task4.py # interactive chat (empty line = quit)
      python homework/task4.py "What notes do I have about Kafka?" "Add a summary of all Kafka notes to kafka-summary.md"
      python homework/task4.py --mermaid
"""
import os
import re
import sys
from pathlib import Path
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from common import get_llm

NOTES_DIR = Path(__file__).resolve().parent / "notes"
DANGEROUS = {"write_note"} # tools that must always be approved by a human
MAX_READ_CHARS = 8000
MAX_WRITE_CHARS = 16000
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,80}")


# ── Path safety: never trust a name the model gives you ──────────────────────
def safe_path(name: str) -> Path:
    """Map a note name to a file inside NOTES_DIR, or raise ValueError.

    Only a plain file name is accepted: no folders, no '..', no hidden files. '.md' is added
    when missing. The resolved path must still sit directly in NOTES_DIR (this also stops symlinks
    that point outside).
    """
    name = str(name).strip()
    if not name.lower().endswith(".md"):
        name += ".md"
    if not NAME_RE.fullmatch(name) or ".." in name:
        raise ValueError(f"Invalid note name {name!r}: use a plain file name like 'kafka-summary.md'.")
    root = NOTES_DIR.resolve()
    path = (root / name).resolve()
    if path.parent != root:
        raise ValueError(f"Invalid note name {name!r}: it must stay inside the notes folder.")
    return path


# ── Tools ────────────────────────────────────────────────────────────────────
@tool
def list_notes() -> str:
    """List all notes (.md files) with their first line. Use this first to find out which notes exist
    and which ones are relevant to the user's question."""
    lines = []
    for f in sorted(NOTES_DIR.glob("*.md")):
        first = f.read_text(encoding="utf-8").strip().splitlines()[:1]
        lines.append(f"{f.name} — {first[0].lstrip('# ') if first else '(empty)'}")
    return "\n".join(lines) if lines else "(no notes yet)"


@tool
def read_note(name: str) -> str:
    """Read the full text of one note. `name` is a file name from list_notes, e.g. 'kafka-basics.md'."""
    path = safe_path(name)
    if not path.is_file():
        raise ValueError(f"No note named {path.name!r}. Call list_notes to see what exists.")
    text = path.read_text(encoding="utf-8")
    if len(text) > MAX_READ_CHARS:
        return text[:MAX_READ_CHARS] + f"\n[truncated: showed {MAX_READ_CHARS} of {len(text)} chars]"
    return text


@tool
def write_note(name: str, text: str) -> str:
    """Create or overwrite a note. `name` is a plain file name such as 'kafka-summary.md'; `text` must be
    the complete markdown content of the note, ready to save. This is a dangerous action:
    a human approves the exact text before anything is written."""
    path = safe_path(name)
    if len(text) > MAX_WRITE_CHARS:
        raise ValueError(f"Note is too long ({len(text)} chars, limit {MAX_WRITE_CHARS}).")
    existed = path.exists()
    path.write_text(text, encoding="utf-8")
    return f"{'Overwrote' if existed else 'Created'} {path.name} ({len(text)} chars)."


TOOLS = [list_notes, read_note, write_note]
llm = get_llm().bind_tools(TOOLS)

SYSTEM = SystemMessage(
    "You are a notes assistant for a folder of markdown notes. "
    "To answer questions about the notes, always use the tools: call list_notes first, then read_note for the "
    "relevant ones; never guess what a note contains. Call tools directly, do not ask for permission. "
    "When the user asks you to add, save or write something, compose the complete text yourself from the notes "
    "you read, then call write_note right away. Never show a draft and ask for confirmation in plain text: "
    "a human approval step is built in and runs automatically before anything is written. "
    "If the human rejects a write, revise the text according to their feedback and call write_note again."
)


# ── State and nodes ──────────────────────────────────────────────────────────
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def agent(state: State) -> dict:
    return {"messages": [llm.invoke([SYSTEM, *state["messages"]])]}


def route(state: State) -> Literal["human_approval", "tools", "__end__"]:
    """Only dangerous calls go through approval; safe calls run straight away."""
    calls = getattr(state["messages"][-1], "tool_calls", None)
    if not calls:
        return END
    if any(c["name"] in DANGEROUS for c in calls):
        return "human_approval"
    return "tools"


def human_approval(state: State) -> Command[Literal["tools", "agent"]]:
    """Pause before a dangerous tool. The graph waits in the checkpointer for Command(resume=...)."""
    last = state["messages"][-1]
    answer = interrupt({
        "question": "Run these tool calls? (yes / reason for rejecting)",
        "tool_calls": [{"name": c["name"], "args": c["args"]} for c in last.tool_calls],
    })
    if str(answer).strip().lower() in {"yes", "y"}:
        return Command(goto="tools")
    # Rejected: every tool_call needs a ToolMessage reply, or the next model call fails.
    rejected = [
        ToolMessage(content=f"The human rejected this call; it was not executed. Feedback: {answer}",
                    tool_call_id=c["id"], name=c["name"])
        for c in last.tool_calls
    ]
    return Command(goto="agent", update={"messages": rejected})


builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("human_approval", human_approval)
# handle_tool_errors: a bad note name goes back to the model as a tool message instead of crashing the run
builder.add_node("tools", ToolNode(TOOLS, handle_tool_errors=True))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route, {"human_approval": "human_approval", "tools": "tools", END: END})
builder.add_edge("tools", "agent")
graph = builder.compile(checkpointer=InMemorySaver()) # interrupt doesn't work without a checkpointer


# ── Runner ───────────────────────────────────────────────────────────────────
def show_call(c: dict) -> None:
    args = c["args"]
    if c["name"] == "write_note":
        try:
            target = safe_path(args.get("name", ""))
            note = f"{target.name} ({'will OVERWRITE an existing note' if target.exists() else 'new file'})"
        except ValueError as exc:
            note = f"{args.get('name')!r}  ⚠ {exc}"
        print(f"    write_note → {note}")
        print("    " + "─" * 50)
        for line in str(args.get("text", "")).splitlines():
            print(f"    {line}")
        print("    " + "─" * 50)
    else:
        print(f"    {c['name']}({args})")


def say(text: str, thread_id: str = "notes") -> None:
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 30}
    print(f"\nUSER: {text}")
    pending: object = {"messages": [("user", text)]}
    while True:
        for update in graph.stream(pending, cfg, stream_mode="updates"):
            for node, payload in update.items():
                if node == "__interrupt__" or not payload:      # pause marker / node with no state update
                    continue
                for m in payload["messages"]:
                    if getattr(m, "tool_calls", None):
                        if any(c["name"] in DANGEROUS for c in m.tool_calls):
                            print("[agent] wants to change something")
                        else:
                            print("[agent] calls: " + ", ".join(f"{c['name']}({c['args']})" for c in m.tool_calls))
                    elif m.type == "tool":
                        shown = m.content if len(m.content) < 150 else m.content[:150] + "…"
                        print(f"[tool]  {m.name} → {shown!r}")
        snapshot = graph.get_state(cfg)
        paused = [i for t in snapshot.tasks for i in t.interrupts]
        if not paused:
            break
        payload = paused[0].value
        print(f"⏸  {payload['question']}")
        for c in payload["tool_calls"]:
            show_call(c)
        pending = Command(resume=input("    your answer > "))
    print(f"AI: {graph.get_state(cfg).values['messages'][-1].text}")


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
    elif len(sys.argv) > 1:
        for message in sys.argv[1:]:
            say(message)
    else:
        print(f"Notes assistant over {NOTES_DIR}. Empty line to quit.")
        while (message := input("\nyou > ").strip()):
            say(message)
