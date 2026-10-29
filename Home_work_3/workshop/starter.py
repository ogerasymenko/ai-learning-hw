"""Workshop: self-correcting code agent. STARTER for participants.

Goal: the agent writes a function from a description, runs the tests itself, analyses
the error and corrects itself until the tests pass. Finally a human approves the result.

  START → generate → test ──ok──→ human_review ──yes──→ END
              ↑          │fail             │feedback
              └─ reflect ←┘ (attempts < MAX) └──→ generate
                         │attempts ≥ MAX → END

Steps (search for TODO by number):
  TODO 1 (10 min)  generate node  — LLM + with_structured_output(Solution)
  TODO 2 (8 min)   test node + after_test function (conditional edge)
  TODO 3 (4 min)   reflect node + attempt limit
  TODO 4 (3 min)   checkpointer + interrupt() in human_review

Run:  python workshop/starter.py
"""
import os
import sys
import traceback
from typing import Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from common import get_llm

MAX_ATTEMPTS = 3

TASK = """Write a function parse_duration(s: str) -> int that converts a duration
string such as '1h30m', '45s' or '2h' into a number of seconds."""

TESTS = """
assert parse_duration("45s") == 45
assert parse_duration("2h") == 7200
assert parse_duration("1h30m") == 5400
assert parse_duration("1h0m5s") == 3605
assert parse_duration("90m") == 5400, "minutes may exceed 59"
assert parse_duration(" 1H 30M ") == 5400, "whitespace and case must be ignored"
for bad in ["", "abc", "10", "5x", "h1"]:
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"expected ValueError for {bad!r}")
"""


class AgentState(TypedDict, total=False):
    task: str
    code: str
    error: str | None
    reflection: str | None
    feedback: str | None      # comment from the human reviewer
    attempts: int


class Solution(BaseModel):
    explanation: str = Field(description="One or two sentences on how the solution works")
    code: str = Field(description="Python code with the function only, no ```markdown``` fences, concise: no docstring, no comments, under 30 lines")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
coder = llm.with_structured_output(Solution).with_retry(stop_after_attempt=3)


# ── TODO 1: generate ─────────────────────────────────────────────────────────
def generate(state: AgentState) -> dict:
    """Build a prompt from task (+ code, error, reflection, feedback when present),
    call coder.invoke(prompt) and return a partial state update:
    {"code": ..., "attempts": attempts + 1, "feedback": None}
    """
    raise NotImplementedError("TODO 1")


# ── TODO 2: test + routing ───────────────────────────────────────────────────
def test(state: AgentState) -> dict:
    """exec(state["code"], ns); exec(TESTS, ns) in one shared dict ns.
    Failed → {"error": traceback.format_exc(limit=1)}, passed → {"error": None}
    """
    raise NotImplementedError("TODO 2")


def after_test(state: AgentState) -> Literal["human_review", "reflect", "__end__"]:
    """No error → "human_review"; attempts >= MAX_ATTEMPTS → END; otherwise → "reflect"."""
    raise NotImplementedError("TODO 2 / TODO 3")


# ── TODO 3: reflect ──────────────────────────────────────────────────────────
def reflect(state: AgentState) -> dict:
    """Ask the llm to briefly explain why the code failed. Return {"reflection": msg.text}."""
    raise NotImplementedError("TODO 3")


# ── TODO 4: human-in-the-loop ────────────────────────────────────────────────
def human_review(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    """answer = interrupt({"code": ..., "question": "Accept the code? (yes / your feedback)"})
    yes → Command(goto=END)
    otherwise → Command(goto="generate", update={"feedback": answer, "error": None, "reflection": None})
    """
    raise NotImplementedError("TODO 4")


# ── Graph (uncomment edges as your nodes become ready) ───────────────────────
builder = StateGraph(AgentState)
builder.add_node("generate", generate)
builder.add_node("test", test)
builder.add_node("reflect", reflect)
builder.add_node("human_review", human_review)
builder.add_edge(START, "generate")
builder.add_edge("generate", "test")
# TODO 2: builder.add_conditional_edges("test", after_test)
# TODO 3: builder.add_edge("reflect", "generate")
graph = builder.compile()   # TODO 4: compile(checkpointer=InMemorySaver())


def run() -> None:
    cfg = {"configurable": {"thread_id": "workshop-1"}, "recursion_limit": 50}
    result = graph.invoke({"task": TASK, "attempts": 0}, cfg)
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\n{payload['code']}\n" + "─" * 60)
        answer = input(f"{payload['question']} > ")
        result = graph.invoke(Command(resume=answer), cfg)

    status = "accepted ✅" if result.get("error") is None else "failed the tests ❌"
    print(f"\nResult: code {status}, attempts: {result.get('attempts')}")


if __name__ == "__main__":
    try:
        run()
    except NotImplementedError as e:
        # Expected while you work through the TODOs: show a short hint instead of a traceback
        print(f"\n🧩 {e} is not implemented yet.")
        print(f"   Open workshop/starter.py, find '# ── {str(e).split(' /')[0]}' and fill it in, then run again.")
        sys.exit(1)
