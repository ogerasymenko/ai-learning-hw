"""Task 5. Parallel candidates with Send: three solutions are generated at once, all are tested,
the first one that passes wins; if none passes, the old reflect → generate loop takes over.

Graph:
  START ═fan_out (3 × Send)═► generate_one ×3 (parallel) ──► pick_best ──winner──► human_review ─yes─► END
                                                                │ none passed          │ feedback
                                                                ▼                      ▼
                                                             reflect ──► generate ──► test ──ok──► human_review
                                                                 ▲                      │fail
                                                                 └──────────────────────┘ (attempts < MAX, else END)

Why `candidates` MUST have a reducer: the three generate_one runs execute in the SAME step and all write
to the same key. Without a reducer LangGraph cannot decide whose value wins and raises InvalidUpdateError;
with operator.add the three one-item lists are concatenated.

Run:  python homework/task5.py  # (--mermaid prints the graph)
"""
import operator
import os
import sys
import traceback
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt
from pydantic import BaseModel, Field

from common import get_llm

MAX_ATTEMPTS = 3          # the parallel round counts as attempt 1

# One hint per parallel candidate: different strategies make the three attempts really different.
HINTS = [
    "Use the simplest possible approach.",
    "Use a regular expression (re.fullmatch).",
    "Parse the string character by character, without regular expressions.",
]

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
class Candidate(TypedDict):
    idx: int          # position in HINTS: parallel results arrive in any order, this keeps "first" well defined
    hint: str
    explanation: str
    code: str


class AgentState(TypedDict, total=False):
    task: str
    code: str
    error: str | None
    reflection: str | None
    feedback: str | None      # comment from the human reviewer
    attempts: int
    candidates: Annotated[list[Candidate], operator.add]   # parallel writes are merged, not overwritten
    winner: str | None        # hint of the candidate that passed the tests


class Solution(BaseModel):
    """Structured model output."""
    explanation: str = Field(description="One or two sentences on how the solution works")
    code: str = Field(description="Python code with the function only, no ```markdown``` fences, concise: no docstring, no comments, under 30 lines")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
coder = llm.with_structured_output(Solution).with_retry(stop_after_attempt=3)


# ── Nodes ────────────────────────────────────────────────────────────────────
def fan_out(state: AgentState) -> list[Send]:
    """Conditional edge from START: one Send per hint = three parallel generate_one runs."""
    return [Send("generate_one", {"task": state["task"], "hint": h, "idx": i}) for i, h in enumerate(HINTS)]


def generate_one(work: dict) -> dict:
    """Runs once per Send; `work` is the payload of the Send, not the graph state."""
    solution = coder.invoke(
        f"Task:\n{work['task']}\n\nApproach to use: {work['hint']}\n"
        "Return the complete function code. Keep it short: no docstring, no comments."
    )
    print(f"🛠  generate_one [{work['hint']}] done: {solution.explanation}")
    return {"candidates": [{"idx": work["idx"], "hint": work["hint"],
                            "explanation": solution.explanation, "code": solution.code}]}


def pick_best(state: AgentState) -> dict:
    """Test every candidate and keep the first one (in HINTS order) that passes."""
    candidates = sorted(state["candidates"], key=lambda c: c["idx"])
    results = [(c, run_tests(c["code"])) for c in candidates]

    print(f"\n📋 {len(results)} candidates:")
    for n, (c, err) in enumerate(results, 1):
        print(f"\n  candidate {n} — {c['hint']}")
        print("    " + c["code"].replace("\n", "\n    "))
        print(f"    → {'✅ passed' if err is None else '❌ ' + err.strip().splitlines()[-1]}")

    for c, err in results:
        if err is None:
            print(f"\n🏆 winner: {c['hint']}")
            return {"code": c["code"], "error": None, "winner": c["hint"], "attempts": 1}

    print("\n😕 no candidate passed: falling back to the reflect → generate loop")
    first, first_err = results[0]
    summary = "\n".join(f"- {c['hint']} -> {err.strip().splitlines()[-1]}" for c, err in results)
    return {"code": first["code"], "attempts": 1, "winner": None,
            "error": f"{first_err}\nAll three parallel candidates failed:\n{summary}"}


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


def run_tests(code: str) -> str | None:
    """Run the code against TESTS. Returns None if everything passes, otherwise the traceback."""
    namespace: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(code, namespace)
        exec(TESTS, namespace)
    except Exception:
        return traceback.format_exc(limit=1)
    return None


def test(state: AgentState) -> dict:
    err = run_tests(state["code"])
    if err:
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


def after_pick(state: AgentState) -> Literal["human_review", "reflect"]:
    return "human_review" if state.get("error") is None else "reflect"


builder = StateGraph(AgentState)
builder.add_node("generate_one", generate_one)
builder.add_node("pick_best", pick_best)
builder.add_node("generate", generate)
builder.add_node("test", test)
builder.add_node("reflect", reflect)
builder.add_node("human_review", human_review)
builder.add_conditional_edges(START, fan_out, ["generate_one"])   # fan-out: 3 parallel generate_one
builder.add_edge("generate_one", "pick_best")                     # fan-in: pick_best waits for all three
builder.add_conditional_edges("pick_best", after_pick)
builder.add_edge("generate", "test")
builder.add_conditional_edges("test", after_test)
builder.add_edge("reflect", "generate")
graph = builder.compile(checkpointer=InMemorySaver())


# ── Runner ───────────────────────────────────────────────────────────────────
def run() -> None:
    cfg = {"configurable": {"thread_id": "task5-1"}, "recursion_limit": 50}
    result = graph.invoke({"task": TASK, "attempts": 0}, cfg)
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\n{payload['code']}\n" + "─" * 60)
        answer = input(f"{payload['question']} > ")
        result = graph.invoke(Command(resume=answer), cfg)

    status = "accepted ✅" if result.get("error") is None else "failed the tests ❌"
    print(f"\nResult: code {status}, attempts: {result.get('attempts')}, "
          f"parallel winner: {result.get('winner') or 'none (fell back to the loop)'}")


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
    else:
        run()
