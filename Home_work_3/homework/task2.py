"""Task 2. The self-correcting code agent with an AI reviewer instead of a human reviewer.

Graph:
  START → generate → test ──ok──→ reviewer ──approved──────────────→ END
              ↑  ↑       │fail        │changes requested (1st time)
              │  │       ↓            └──→ generate  (comments as feedback)
              │  └─── reflect         │rejected twice
              │   (attempts < MAX)    ↓
              │                  human_review ──yes──→ END
              └──────────────────────┘ feedback
                      attempts ≥ MAX after a failed test → END

The human is only a safety net: the run pauses with interrupt() after the reviewer has
rejected the code twice.

The tests DELIBERATELY demand a bit more than the task says (whitespace, case, errors), and
the reviewer is strict (docstring + type hints), so the correction loops kick in.

Run:  python homework/task2.py            (--mermaid prints the graph)
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

MAX_ATTEMPTS = 5          # total generations: test-failure retries AND reviewer-driven rewrites share it
MAX_REVIEW_REJECTIONS = 2  # after this many rejections in a row the human decides

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
    review_comments: str | None   # comments from the AI reviewer
    review_rejections: int        # how many times in a row the AI reviewer rejected the code
    approved: bool                # the AI reviewer's last verdict
    attempts: int


class Solution(BaseModel):
    """Structured model output."""
    explanation: str = Field(description="One or two sentences on how the solution works")
    code: str = Field(description="Python code with the function only, no ```markdown``` fences, under 40 lines. Concise by default; add a docstring or comments only when a reviewer asks for them")


class Review(BaseModel):
    """Structured output of the AI reviewer."""
    approved: bool = Field(description="True only if the code fully satisfies the task AND every review criterion")
    comments: str = Field(description="If not approved: a short, concrete list of what to change. If approved: empty string")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
coder = llm.with_structured_output(Solution).with_retry(stop_after_attempt=3)
review_llm = llm.with_structured_output(Review).with_retry(stop_after_attempt=3)

REVIEW_CRITERIA = """You are a strict senior code reviewer. Check the code against the task.
Request changes unless ALL of these hold:
1. It solves the task as written (not just the sample inputs).
2. The function has a docstring that says what it does and when it raises.
3. Every parameter and the return value have type hints.
4. Names are clear and there is no dead or needlessly complex code."""


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
    if state.get("review_comments"):
        prompt += f"\nComments from the AI reviewer (fix every one of them):\n{state['review_comments']}\n"
    prompt += ("\nReturn the complete, corrected function code. Keep it short: no docstring and no comments "
               "unless a reviewer asked for them above.")

    solution = coder.invoke(prompt)
    attempt = state.get("attempts", 0) + 1
    print(f"\n🛠  generate (attempt {attempt}): {solution.explanation}")
    return {"code": solution.code, "attempts": attempt, "feedback": None, "review_comments": None}


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


def reviewer(state: AgentState) -> dict:
    """AI reviewer: replaces the human in the normal path. Only runs on code that passed the tests."""
    review = review_llm.invoke(
        f"{REVIEW_CRITERIA}\n\nTask:\n{state['task']}\n\nCode (it already passes the unit tests):\n{state['code']}\n\n"
        "Return approved=true only if all criteria hold; otherwise list exactly what to change."
    )
    if review.approved:
        print("🔍 reviewer: approved ✅")
        return {"approved": True, "review_comments": None, "review_rejections": 0}
    rejections = state.get("review_rejections", 0) + 1
    print(f"🔍 reviewer: changes requested ({rejections}/{MAX_REVIEW_REJECTIONS}): {review.comments}")
    return {"approved": False, "review_comments": review.comments, "review_rejections": rejections}


def human_review(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    """Safety net: reached only after the AI reviewer rejected the code MAX_REVIEW_REJECTIONS times."""
    answer = interrupt({
        "code": state["code"],
        "reviewer_comments": state.get("review_comments"),
        "question": f"The AI reviewer rejected the code {state.get('review_rejections', 0)} times. "
                    "Accept the code anyway? (yes / your feedback)",
    })
    if str(answer).strip().lower() in {"yes", "y"}:
        return Command(goto=END)
    # The human's word replaces the reviewer's comments, and the reviewer gets a fresh budget.
    return Command(goto="generate", update={"feedback": answer, "review_comments": None,
                                            "review_rejections": 0, "error": None, "reflection": None})


# ── Edges ────────────────────────────────────────────────────────────────────
def after_test(state: AgentState) -> Literal["reviewer", "reflect", "__end__"]:
    if state.get("error") is None:
        return "reviewer"
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        print(f"🏳  giving up after {MAX_ATTEMPTS} attempts")
        return END
    return "reflect"


def after_review(state: AgentState) -> Literal["human_review", "generate", "__end__"]:
    if state.get("approved"):
        return END
    if state.get("review_rejections", 0) >= MAX_REVIEW_REJECTIONS:
        print("🙋 reviewer rejected the code twice: asking a human")
        return "human_review"
    return "generate"


builder = StateGraph(AgentState)
builder.add_node("generate", generate)
builder.add_node("test", test)
builder.add_node("reflect", reflect)
builder.add_node("reviewer", reviewer)
builder.add_node("human_review", human_review)
builder.add_edge(START, "generate")
builder.add_edge("generate", "test")
builder.add_conditional_edges("test", after_test)
builder.add_conditional_edges("reviewer", after_review)
builder.add_edge("reflect", "generate")
graph = builder.compile(checkpointer=InMemorySaver())


# ── Runner ───────────────────────────────────────────────────────────────────
def run() -> None:
    cfg = {"configurable": {"thread_id": "workshop-1"}, "recursion_limit": 50}
    result = graph.invoke({"task": TASK, "attempts": 0}, cfg)
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\n{payload['code']}\n" + "─" * 60)
        print(f"Last reviewer comments: {payload.get('reviewer_comments')}")
        answer = input(f"{payload['question']} > ")
        result = graph.invoke(Command(resume=answer), cfg)

    if result.get("error") is not None:
        status = "failed the tests ❌"
    elif result.get("approved"):
        status = "approved by the AI reviewer ✅"
    else:
        status = "accepted by the human after the AI reviewer rejected it ✅"
    print(f"\nFinal code:\n{result.get('code')}")
    print(f"\nResult: code {status}, attempts: {result.get('attempts')}, "
          f"reviewer rejections left in state: {result.get('review_rejections', 0)}")


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
    else:
        run()
