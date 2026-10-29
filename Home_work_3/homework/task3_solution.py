"""Task 3, step 1: the self-correcting code agent (workshop solution) with a SQLite checkpointer.

The only change from workshop/solution.py: the checkpoints are stored in task3.db instead of
process memory, so task3_result.py can read the history and replay it after this script exits.
Start from a clean history with:  rm homework/task3.db

Run:  python homework/task3_solution.py   ->   then:  python homework/task3_result.py

Original docstring follows.

Graph:
  START → generate → test ──ok──→ human_review ──yes──→ END
              ↑          │fail             │feedback
              └─ reflect ←┘ (attempts < MAX) └──→ generate
                         │attempts ≥ MAX → END

The tests DELIBERATELY demand a bit more than the task says (whitespace, case, errors),
so the self-correction loop almost certainly kicks in at least once.

Run:  python workshop/solution.py
"""
import os
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.sqlite import SqliteSaver
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


# ── State ────────────────────────────────────────────────────────────────────
class AgentState(TypedDict, total=False):
    task: str
    code: str
    error: str | None
    reflection: str | None
    feedback: str | None      # comment from the human reviewer
    attempts: int


class Solution(BaseModel):
    """Structured model output."""
    explanation: str = Field(description="One or two sentences on how the solution works")
    code: str = Field(description="Python code with the function only, no ```markdown``` fences, concise: no docstring, no comments, under 30 lines")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
coder = llm.with_structured_output(Solution).with_retry(stop_after_attempt=3)


# ── Nodes ────────────────────────────────────────────────────────────────────
def generate(state: AgentState) -> dict:
    prompt = f"Task:\n{state['task']}\n"
    if state.get("code"):
        prompt += f"\nPrevious version of the code:\n{state['code']}\n"
    if state.get("error"):
        prompt += f"\nThe tests failed with this error:\n{state['error']}\n"
    if state.get("reflection"):
        prompt += f"\nAnalysis of the error:\n{state['reflection']}\n"
    if state.get("feedback"):
        prompt += f"\nComment from the human reviewer:\n{state['feedback']}\n"
    prompt += "\nReturn the complete, corrected function code. Keep it short: no docstring, no comments."

    solution = coder.invoke(prompt)
    attempt = state.get("attempts", 0) + 1
    print(f"\n🛠  generate (attempt {attempt}): {solution.explanation}")
    return {"code": solution.code, "attempts": attempt, "feedback": None}


def test(state: AgentState) -> dict:
    namespace: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(state["code"], namespace)
        exec(TESTS, namespace)
    except Exception:
        err = traceback.format_exc(limit=1)
        print(f"❌ test: {err.strip().splitlines()[-1]}")
        return {"error": err}
    print("✅ test: all tests passed")
    return {"error": None}


def reflect(state: AgentState) -> dict:
    msg = llm.invoke(
        "Briefly (2-3 bullet points) explain why the code failed the test and what to fix.\n\n"
        f"Code:\n{state['code']}\n\nError:\n{state['error']}"
    )
    print(f"🤔 reflect: {msg.text[:200]}")
    return {"reflection": msg.text}


def human_review(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    answer = interrupt({"code": state["code"], "question": "Accept the code? (yes / your feedback)"})
    if str(answer).strip().lower() in {"yes", "y"}:
        return Command(goto=END)
    return Command(goto="generate", update={"feedback": answer, "error": None, "reflection": None})


# ── Edges ────────────────────────────────────────────────────────────────────
def after_test(state: AgentState) -> Literal["human_review", "reflect", "__end__"]:
    if state.get("error") is None:
        return "human_review"
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        print(f"🏳  giving up after {MAX_ATTEMPTS} attempts")
        return END
    return "reflect"


builder = StateGraph(AgentState)
builder.add_node("generate", generate)
builder.add_node("test", test)
builder.add_node("reflect", reflect)
builder.add_node("human_review", human_review)
builder.add_edge(START, "generate")
builder.add_edge("generate", "test")
builder.add_conditional_edges("test", after_test)
builder.add_edge("reflect", "generate")
DB_PATH = Path(__file__).resolve().parent / "task3.db"
THREAD_ID = "workshop-1"
graph = builder.compile(checkpointer=SqliteSaver(sqlite3.connect(DB_PATH, check_same_thread=False)))


# ── Runner ───────────────────────────────────────────────────────────────────
def run() -> None:
    cfg = {"configurable": {"thread_id": THREAD_ID}, "recursion_limit": 50}
    result = graph.invoke({"task": TASK, "attempts": 0}, cfg)
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\n{payload['code']}\n" + "─" * 60)
        answer = input(f"{payload['question']} > ")
        result = graph.invoke(Command(resume=answer), cfg)

    status = "accepted ✅" if result.get("error") is None else "failed the tests ❌"
    print(f"\nResult: code {status}, attempts: {result.get('attempts')}")


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
    else:
        run()
