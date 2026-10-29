"""Multi-agent orchestration: a supervisor and a small dev team.
Shown as a live demo to everyone at the end of the hands-on.

Team:
  planner   (LLM)    writes a short spec and the test cases (assert statements)
  coder     (LLM)    writes / fixes the function
  tester    (no LLM) runs the code against the planner's tests — plain Python
  reviewer  (LLM)    reviews the code against the spec, approves or asks for changes
  supervisor (LLM)   decides who works next, based on a status summary

Guard (code, not LLM): the supervisor cannot FINISH until the tests pass AND the
reviewer approved, and cannot send work to someone who has nothing to work on.
The model decides, code keeps it safe.

           ┌─────────── supervisor ───────────┐        guard checks every
           ↓        ↓          ↓          ↓    │        decision before routing
       planner    coder     tester    reviewer │
           └────────┴──────────┴──────────┴────┘   → FINISH → END

Run:  python workshop/stretch_supervisor.py            (add --mermaid for the graph)
"""
import operator
import os
import sys
import traceback
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from common import get_llm

MAX_TURNS = 14

TASK = """Write a Python function slugify(title: str, max_len: int = 40) -> str that turns an article
title into a URL slug:
- lowercase; accented letters become plain ones (é → e); any other non [a-z0-9] characters are separators;
- words are joined by single hyphens, no leading or trailing hyphens;
- if the slug is longer than max_len, cut it at the last hyphen that keeps it within max_len
  (if there is no such hyphen, hard-cut at max_len).
Example from the product manager's ticket — include it in the tests as is:
  slugify('Hello, World!', max_len=8) == 'hello-wo'"""


# ── State ────────────────────────────────────────────────────────────────────
class TeamState(TypedDict, total=False):
    task: str
    spec: str
    tests: str
    code: str
    test_report: str
    tests_passed: bool
    review: str
    review_ok: bool
    turns: int
    trace: Annotated[list[str], operator.add]   # route log, appended by every node


# ── Structured outputs ───────────────────────────────────────────────────────
class Plan(BaseModel):
    spec: str = Field(description="Short spec as bullet points: behaviour and edge cases")
    tests: str = Field(description="6-10 Python assert statements calling the function, one per line, "
                                   "no imports, no function definition, no markdown")


class CodeDraft(BaseModel):
    code: str = Field(description="Complete Python code of the function with any imports it needs, no markdown, concise: no docstring, no comments, under 30 lines")
    notes: str = Field(description="One sentence: what you did or changed")


class Review(BaseModel):
    approved: bool = Field(description="True if the code is correct and matches the spec")
    comments: str = Field(description="Concrete problems to fix, or a short approval note")


class Route(BaseModel):
    next: Literal["planner", "coder", "tester", "reviewer", "FINISH"]
    reason: str = Field(description="One short sentence")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
planner_llm = llm.with_structured_output(Plan).with_retry(stop_after_attempt=3)
coder_llm = llm.with_structured_output(CodeDraft).with_retry(stop_after_attempt=3)
reviewer_llm = llm.with_structured_output(Review).with_retry(stop_after_attempt=3)
router_llm = llm.with_structured_output(Route).with_retry(stop_after_attempt=3)


# ── Supervisor + guard ───────────────────────────────────────────────────────
def status(state: TeamState) -> str:
    def yn(v): return "yes" if v else "no"
    return (
        f"spec and tests written: {yn(state.get('spec'))}\n"
        f"code written: {yn(state.get('code'))}\n"
        f"tests run on current code: {yn(state.get('test_report'))}\n"
        f"tests passed: {yn(state.get('tests_passed'))}\n"
        f"last test report: {state.get('test_report') or '-'}\n"
        f"reviewer approved current code: {yn(state.get('review_ok'))}\n"
        f"last review: {state.get('review') or '-'}"
    )


def guard(state: TeamState, nxt: str) -> tuple[str, str | None]:
    """Deterministic rules the LLM is not allowed to break."""
    if not state.get("spec") and nxt != "planner":
        return "planner", "nothing to work on without a spec"
    if nxt in ("tester", "reviewer") and not state.get("code"):
        return "coder", "there is no code yet"
    if nxt == "FINISH" and not (state.get("tests_passed") and state.get("review_ok")):
        if not state.get("test_report"):
            return "tester", "the current code was never tested"
        if not state.get("tests_passed"):
            return "coder", "tests are failing"
        return "reviewer", "the reviewer has not approved yet"
    return nxt, None


def supervisor(state: TeamState) -> Command[Literal["planner", "coder", "tester", "reviewer", "__end__"]]:
    turns = state.get("turns", 0)
    if turns >= MAX_TURNS:
        print(f"⏹  MAX_TURNS={MAX_TURNS} reached, stopping")
        return Command(goto=END, update={"trace": ["MAX_TURNS"]})

    decision = router_llm.invoke(
        "You are the tech lead of a small team: planner (spec + tests), coder (writes and fixes code), "
        "tester (runs the tests), reviewer (reviews code). Pick who works next.\n"
        "Typical order: planner → coder → tester → (coder again if tests fail) → reviewer "
        "→ (coder again if changes requested) → FINISH when tests pass and the review is approved.\n"
        "If the same test keeps failing after the coder tried twice, the test itself may be wrong: "
        "send it back to the planner to fix the tests.\n\n"
        f"Task:\n{state['task']}\n\nCurrent status:\n{status(state)}"
    )
    nxt, why = guard(state, decision.next)
    print(f"\n🧭 supervisor → {decision.next}: {decision.reason}")
    if why:
        print(f"🛡  guard: {decision.next} → {nxt} ({why})")

    update = {"turns": turns + 1, "trace": [nxt if not why else f"{nxt}🛡"]}
    return Command(goto=END if nxt == "FINISH" else nxt, update=update)


# ── Workers (every worker reports back to the supervisor) ────────────────────
def planner(state: TeamState) -> Command[Literal["supervisor"]]:
    prompt = (f"Write a short spec and test cases for this task.\n\nTask:\n{state['task']}\n\n"
              "Tests must be plain assert statements with exact expected values you are sure about.")
    if state.get("tests"):   # called again: the supervisor suspects the tests are wrong
        prompt += (f"\n\nYour previous tests:\n{state['tests']}\n\nThey keep failing with:\n"
                   f"{state.get('test_report')}\nFix any test whose expected value is wrong for the task.")
    plan = planner_llm.invoke(prompt)
    n = sum(1 for line in plan.tests.splitlines() if line.strip().startswith("assert"))
    print(f"📝 planner: spec ready, {n} tests")
    # new tests → previous test result no longer applies
    return Command(goto="supervisor", update={"spec": plan.spec, "tests": plan.tests,
                                              "test_report": "", "tests_passed": False})


def coder(state: TeamState) -> Command[Literal["supervisor"]]:
    prompt = f"Task:\n{state['task']}\n\nSpec:\n{state['spec']}\n\nTests it must pass:\n{state['tests']}\n"
    if state.get("code"):
        prompt += f"\nCurrent code:\n{state['code']}\n"
    if state.get("test_report") and not state.get("tests_passed"):
        prompt += f"\nTest failure:\n{state['test_report']}\n"
    if state.get("review") and not state.get("review_ok"):
        prompt += f"\nReviewer comments:\n{state['review']}\n"
    draft = coder_llm.invoke(prompt + "\nReturn the complete corrected function. Keep it short: no docstring, no comments. Follow the rules in the task; never special-case specific inputs to make a test pass.")
    print(f"🛠  coder: {draft.notes}")
    # new code → previous test and review results no longer apply
    return Command(goto="supervisor", update={
        "code": draft.code, "test_report": "", "tests_passed": False, "review": "", "review_ok": False})


def tester(state: TeamState) -> Command[Literal["supervisor"]]:
    ns: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(state["code"], ns)
        exec(state["tests"], ns)
        report, ok = "all tests passed", True
    except Exception:
        report, ok = traceback.format_exc(limit=1).strip().splitlines()[-1], False
    print(f"🧪 tester: {'✅' if ok else '❌'} {report}")
    return Command(goto="supervisor", update={"test_report": report, "tests_passed": ok})


def reviewer(state: TeamState) -> Command[Literal["supervisor"]]:
    review = reviewer_llm.invoke(
        "Review this function against the spec. Be pragmatic: request changes only for real bugs "
        "or missed requirements, not for style. Reject code that special-cases specific inputs.\n\n"
        f"Spec:\n{state['spec']}\n\nCode:\n{state['code']}\n\nTest result: {state.get('test_report')}"
    )
    print(f"🔍 reviewer: {'approved ✅' if review.approved else 'changes requested ✏️'} — {review.comments[:160]}")
    return Command(goto="supervisor", update={"review": review.comments, "review_ok": review.approved})


# ── Graph ────────────────────────────────────────────────────────────────────
builder = StateGraph(TeamState)
builder.add_node("supervisor", supervisor)
for name, fn in [("planner", planner), ("coder", coder), ("tester", tester), ("reviewer", reviewer)]:
    builder.add_node(name, fn)
builder.add_edge(START, "supervisor")      # every other route is chosen at runtime via Command(goto=...)
graph = builder.compile()


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
        sys.exit()

    print(f"TASK: {TASK}")
    result = graph.invoke({"task": TASK, "turns": 0, "trace": []}, {"recursion_limit": 60})

    print("\n" + "═" * 60)
    print("Route (supervisor decides between every step, 🛡 = corrected by the guard):")
    print("  " + " → ".join(result.get("trace", [])))
    done = result.get("tests_passed") and result.get("review_ok")
    print(f"Result: {'done ✅ (tests passed, review approved)' if done else 'stopped before done ❌'}")
    print("─" * 60 + f"\n{result.get('code', '(no code)')}\n" + "─" * 60)
