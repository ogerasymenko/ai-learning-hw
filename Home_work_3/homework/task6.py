"""Multi-agent orchestration: a supervisor and a small dev team — FIXED version.
Run stretch_supervisor.py first: there coder and tester ping-pong forever. Two bugs:
  1. tester only says "AssertionError" — nobody knows WHICH test failed or what the code returned;
  2. nothing notices the loop — the supervisor keeps sending work back to the coder.
The task contains a mistake on purpose: the example from the ticket contradicts the rules.
Fixes here (search for "FIX"):
  1. tester reports every failing assert with the actual vs expected value;
  2. guard counts consecutive test failures: after 2 in a row the work goes to the planner,
     because the tests themselves may be wrong.

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

Task 6 additions (search for "TASK 6"):
  1. Escalation: if the reviewer requests changes 3 times IN A ROW, the guard stops the team before the
     supervisor is even asked, and a human decides via interrupt(): `continue`, `finish`, or free-text
     instructions that go straight to the coder.
  2. Budget: LLM calls are counted per agent; the run stops with a clear message before the total would go
     over MAX_LLM_CALLS, and a table (agent -> calls) is printed at the end.
  3. Another task: --task k8s-cpu (a DevOps function) or --task-file my_task.txt.

Run:  python homework/task6.py                          (add --mermaid for the graph)
      python homework/task6.py --picky-reviewer         reviewer with a house rule the coder resists -> escalation
      python homework/task6.py --budget 6               tiny budget -> the run stops on it
      python homework/task6.py --task k8s-cpu           a different task
"""
import ast
import operator
import os
import sys
import traceback
from pathlib import Path
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from common import get_llm

MAX_TURNS = 20              # TASK 6: was 14; raised so the call budget (below) is the limit that binds first
REVIEW_ESCALATION = 3       # TASK 6: reviewer rejections in a row before a human is asked
MAX_LLM_CALLS = 25          # TASK 6: budget for all agents together (--budget N overrides)
AGENTS = ["supervisor", "planner", "coder", "reviewer"]      # the agents that call an LLM (the tester does not)
PICKY_RULE = ("\n\nHouse rule: also request changes unless the function has a docstring AND at least one inline "
              "comment.")   # --picky-reviewer: the coder is told to be terse, so the two tend to disagree

TASK = """Write a Python function slugify(title: str, max_len: int = 40) -> str that turns an article
title into a URL slug:
- lowercase; accented letters become plain ones (é → e); any other non [a-z0-9] characters are separators;
- words are joined by single hyphens, no leading or trailing hyphens;
- if the slug is longer than max_len, cut it at the last hyphen that keeps it within max_len
  (if there is no such hyphen, hard-cut at max_len).
Example from the product manager's ticket — include it in the tests as is:
  slugify('Hello, World!', max_len=8) == 'hello-wo'"""


# TASK 6 (part 3): a task from my own domain. Select with --task k8s-cpu
TASKS = {
    "slugify": TASK,
    "k8s-cpu": """Write a Python function parse_cpu(quantity: str) -> int that converts a Kubernetes CPU
quantity into millicores (an integer):
- '250m' is 250 millicores; a plain number is whole cores: '2' is 2000;
- decimal cores are allowed: '0.5' is 500, '1.5' is 1500, '0.1' is 100;
- the result is always an int (round to the nearest millicore, halves round up);
- anything else raises ValueError: empty string, negative numbers, unknown suffixes ('2g'), spaces, '1.5m'
  (fractional millicores are not allowed), and '1e3'.
Example from the ticket — include it in the tests as is:
  parse_cpu('100m') == 0.1""",
}


# ── State ────────────────────────────────────────────────────────────────────
def merge_counts(old: dict[str, int] | None, new: dict[str, int] | None) -> dict[str, int]:
    """Reducer: add per-agent counters instead of overwriting them."""
    merged = dict(old or {})
    for agent_name, n in (new or {}).items():
        merged[agent_name] = merged.get(agent_name, 0) + n
    return merged


class TeamState(TypedDict, total=False):
    task: str
    spec: str
    tests: str
    code: str
    test_report: str
    tests_passed: bool
    fail_streak: int            # FIX 2: consecutive test failures
    review: str
    review_ok: bool
    turns: int
    trace: Annotated[list[str], operator.add]   # route log, appended by every node
    review_streak: int          # TASK 6: consecutive reviewer rejections
    human_instructions: str     # TASK 6: free-text instructions from the human, consumed by the coder
    calls: Annotated[dict[str, int], merge_counts]   # TASK 6: LLM calls per agent
    stop_reason: str            # done | max_turns | budget | human_finish


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


PICKY = "--picky-reviewer" in sys.argv

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
        f"consecutive test failures: {state.get('fail_streak', 0)}\n"
        f"last test report: {state.get('test_report') or '-'}\n"
        f"reviewer approved current code: {yn(state.get('review_ok'))}\n"
        f"consecutive reviewer rejections: {state.get('review_streak', 0)}\n"
        f"last review: {state.get('review') or '-'}"
    )


def guard(state: TeamState, nxt: str) -> tuple[str, str | None]:
    """Deterministic rules the LLM is not allowed to break."""
    if not state.get("spec") and nxt != "planner":
        return "planner", "nothing to work on without a spec"
    if nxt == "coder" and state.get("fail_streak", 0) >= 2:          # FIX 2: break the loop
        return "planner", "tests failed twice in a row — the tests themselves may be wrong"
    if nxt in ("tester", "reviewer") and not state.get("code"):
        return "coder", "there is no code yet"
    if nxt == "FINISH" and not (state.get("tests_passed") and state.get("review_ok")):
        if not state.get("test_report"):
            return "tester", "the current code was never tested"
        if not state.get("tests_passed"):
            return "coder", "tests are failing"
        return "reviewer", "the reviewer has not approved yet"
    return nxt, None


def supervisor(state: TeamState) -> Command[Literal["planner", "coder", "tester", "reviewer", "human_escalation", "__end__"]]:
    turns = state.get("turns", 0)
    if turns >= MAX_TURNS:
        print(f"⏹  MAX_TURNS={MAX_TURNS} reached, stopping")
        return Command(goto=END, update={"trace": ["MAX_TURNS"], "stop_reason": "max_turns"})

    # TASK 6 (2) budget guard. This decision costs 1 call and the worker after it at most 1 more, so stop
    # BEFORE the total could go over the limit.
    spent = sum(state.get("calls", {}).values())
    if spent + 2 > MAX_LLM_CALLS:
        print(f"\n💸 BUDGET: {spent} LLM calls used, the next step needs up to 2 more, the limit is "
              f"{MAX_LLM_CALLS}. Stopping the team.")
        return Command(goto=END, update={"trace": ["BUDGET"], "stop_reason": "budget"})

    # TASK 6 (1) escalation guard: runs BEFORE the router, so no LLM call is wasted on a decision we would override.
    if state.get("review_streak", 0) >= REVIEW_ESCALATION:
        print(f"\n🛡  guard: the reviewer requested changes {state['review_streak']} times in a row "
              "→ stopping the team and asking a human")
        return Command(goto="human_escalation",
                       update={"turns": turns + 1, "trace": ["human_escalation🛡"]})

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

    update = {"turns": turns + 1, "trace": [nxt if not why else f"{nxt}🛡"], "calls": {"supervisor": 1}}
    if nxt == "FINISH":
        update["stop_reason"] = "done"
    return Command(goto=END if nxt == "FINISH" else nxt, update=update)


def human_escalation(state: TeamState) -> Command[Literal["supervisor", "coder", "__end__"]]:
    """TASK 6 (1): the team is stopped; a human decides. The graph waits in the checkpointer for Command(resume=...)."""
    answer = str(interrupt({
        "question": f"The reviewer requested changes {state.get('review_streak', 0)} times in a row. "
                    "What now? continue / finish / or type instructions for the coder",
        "code": state.get("code", ""),
        "review": state.get("review", ""),
        "test_report": state.get("test_report", ""),
    })).strip()
    choice = answer.lower()
    if choice in {"finish", "f"}:
        return Command(goto=END, update={"trace": ["👤finish"], "stop_reason": "human_finish"})
    if choice in {"continue", "c", ""}:
        return Command(goto="supervisor", update={"trace": ["👤continue"], "review_streak": 0})
    # Free text: the human's words go straight to the coder, and the reviewer gets a fresh budget of rejections.
    return Command(goto="coder", update={"trace": ["👤instructions"], "review_streak": 0,
                                         "human_instructions": answer})


# ── Workers (every worker reports back to the supervisor) ────────────────────
def planner(state: TeamState) -> Command[Literal["supervisor"]]:
    prompt = (f"Write a short spec and test cases for this task.\n\nTask:\n{state['task']}\n\n"
              "Tests must be plain assert statements with exact expected values you are sure about.")
    if state.get("tests"):   # called again: the supervisor suspects the tests are wrong
        prompt += (f"\n\nYour previous tests:\n{state['tests']}\n\nThey keep failing with:\n"
                   f"{state.get('test_report')}\nFix any test whose expected value is wrong for the task. "
                   "If a test contradicts the rules in the task, the rules win — fix that test, "
                   "even if it came from the ticket.")
    plan = planner_llm.invoke(prompt)
    n = sum(1 for line in plan.tests.splitlines() if line.strip().startswith("assert"))
    print(f"📝 planner: spec ready, {n} tests")
    # new tests → previous test result no longer applies
    return Command(goto="supervisor", update={"spec": plan.spec, "tests": plan.tests,
                                              "test_report": "", "tests_passed": False,
                                              "fail_streak": 0, "calls": {"planner": 1}})


def coder(state: TeamState) -> Command[Literal["supervisor"]]:
    prompt = f"Task:\n{state['task']}\n\nSpec:\n{state['spec']}\n\nTests it must pass:\n{state['tests']}\n"
    if state.get("code"):
        prompt += f"\nCurrent code:\n{state['code']}\n"
    if state.get("test_report") and not state.get("tests_passed"):
        prompt += f"\nTest failure:\n{state['test_report']}\n"
    if state.get("review") and not state.get("review_ok"):
        prompt += f"\nReviewer comments:\n{state['review']}\n"
    if state.get("human_instructions"):
        prompt += f"\nInstructions from the human (they override everything else):\n{state['human_instructions']}\n"
    draft = coder_llm.invoke(prompt + "\nReturn the complete corrected function. Keep it short: no docstring, no comments. Follow the rules in the task; never special-case specific inputs to make a test pass.")
    print(f"🛠  coder: {draft.notes}")
    # new code → previous test and review results no longer apply
    return Command(goto="supervisor", update={
        "code": draft.code, "test_report": "", "tests_passed": False, "review": "", "review_ok": False,
        "human_instructions": "", "calls": {"coder": 1}})


def run_tests(code: str, tests: str) -> tuple[bool, str]:
    """FIX 1: run each assert separately and say exactly what failed."""
    ns: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(code, ns)
    except Exception:
        return False, "the code does not run: " + traceback.format_exc(limit=1).strip().splitlines()[-1]
    fails, total = [], 0
    for line in (l.strip() for l in tests.splitlines()):
        if not line.startswith("assert"):
            continue
        total += 1
        try:
            exec(line, ns)
        except AssertionError:
            detail = line
            try:  # for `assert f(x) == y` show what f(x) actually returned
                test = ast.parse(line).body[0].test
                if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    got = eval(compile(ast.Expression(test.left), "<test>", "eval"), ns)
                    want = eval(compile(ast.Expression(test.comparators[0]), "<test>", "eval"), ns)
                    detail = f"{ast.unparse(test.left)} returned {got!r}, expected {want!r}"
            except Exception:
                pass
            fails.append(detail)
        except Exception as e:
            fails.append(f"{line} raised {type(e).__name__}: {e}")
    if total == 0:
        return False, "no assert statements found in the tests"
    if not fails:
        return True, f"all {total} tests passed"
    return False, f"{len(fails)}/{total} failed: " + "; ".join(fails[:3])


def tester(state: TeamState) -> Command[Literal["supervisor"]]:
    ok, report = run_tests(state["code"], state["tests"])
    streak = 0 if ok else state.get("fail_streak", 0) + 1
    print(f"🧪 tester: {'✅' if ok else '❌'} {report[:220]}")
    return Command(goto="supervisor", update={"test_report": report, "tests_passed": ok, "fail_streak": streak})


def reviewer(state: TeamState) -> Command[Literal["supervisor"]]:
    review = reviewer_llm.invoke(
        "Review this function against the spec. Be pragmatic: request changes only for real bugs "
        "or missed requirements, not for style. Reject code that special-cases specific inputs."
        + (PICKY_RULE if PICKY else "") + "\n\n"
        f"Spec:\n{state['spec']}\n\nCode:\n{state['code']}\n\nTest result: {state.get('test_report')}"
    )
    print(f"🔍 reviewer: {'approved ✅' if review.approved else 'changes requested ✏️'} — {review.comments[:160]}")
    streak = 0 if review.approved else state.get("review_streak", 0) + 1     # TASK 6: rejections in a row
    return Command(goto="supervisor", update={"review": review.comments, "review_ok": review.approved,
                                              "review_streak": streak, "calls": {"reviewer": 1}})


# ── Graph ────────────────────────────────────────────────────────────────────
builder = StateGraph(TeamState)
builder.add_node("supervisor", supervisor)
builder.add_node("human_escalation", human_escalation)
for name, fn in [("planner", planner), ("coder", coder), ("tester", tester), ("reviewer", reviewer)]:
    builder.add_node(name, fn)
builder.add_edge(START, "supervisor")      # every other route is chosen at runtime via Command(goto=...)
graph = builder.compile(checkpointer=InMemorySaver())   # interrupt() needs a checkpointer


def option(flag: str, default: str | None = None) -> str | None:
    """Value after a command-line flag, e.g. --budget 6."""
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def calls_table(calls: dict[str, int]) -> str:
    total = sum(calls.values())
    rows = [f"  {name:<12}{calls.get(name, 0):>3}" for name in AGENTS] + [f"  {'tester':<12}{'-':>3}  (no LLM)"]
    return "LLM calls per agent:\n" + "\n".join(rows) + f"\n  {'TOTAL':<12}{total:>3} / {MAX_LLM_CALLS}"


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
        sys.exit()

    if option("--budget"):
        MAX_LLM_CALLS = int(option("--budget"))
    if option("--task-file"):
        TASK = Path(option("--task-file")).read_text(encoding="utf-8").strip()
    else:
        TASK = TASKS[option("--task", "slugify")]

    print(f"TASK: {TASK}")
    cfg = {"configurable": {"thread_id": "team-1"}, "recursion_limit": 60}
    result = graph.invoke({"task": TASK, "turns": 0, "trace": [], "fail_streak": 0, "review_streak": 0, "calls": {}}, cfg)
    while "__interrupt__" in result:                                  # the team is paused: a human decides
        payload = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\nCurrent code:\n{payload['code']}\n" + "─" * 60)
        print(f"Last test report: {payload['test_report']}\nLast review:      {payload['review']}")
        result = graph.invoke(Command(resume=input(f"⏸  {payload['question']} > ")), cfg)

    print("\n" + "═" * 60)
    print("Route (supervisor decides between every step, 🛡 = corrected by the guard, 👤 = human):")
    print("  " + " → ".join(result.get("trace", [])))
    done = result.get("tests_passed") and result.get("review_ok")
    reason = result.get("stop_reason", "?")
    summary = {"done": "done ✅ (tests passed, review approved)",
               "human_finish": f"finished by the human ({'tests passing' if result.get('tests_passed') else 'tests NOT passing'}) 👤",
               "budget": "stopped on the LLM-call budget 💸",
               "max_turns": "stopped on MAX_TURNS ⏹"}.get(reason, "stopped before done ❌")
    print(f"Result: {summary}")
    print(calls_table(result.get("calls", {})))
    print("─" * 60 + f"\n{result.get('code', '(no code)')}\n" + "─" * 60)
