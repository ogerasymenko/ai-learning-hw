# LangGraph Workshop — Homework

Six tasks, from a 20-minute warm-up to a small project. Each one builds on code you
already have and practises one idea from the workshop. Do them in order, or pick the
ones that matter for your work — tasks 1–3 are the core, 4–6 go further.

**What you need:** the workshop folder with a working `.venv` and `.env`
(`python 00_sanity_check.py` shows ✅), plus the files from this pack:

| File | What it is |
|---|---|
| `workshop/solution.py` | the finished self-correcting agent from the hands-on |
| `workshop/stretch_supervisor_fixed.py` | the multi-agent team after the debrief |
| `homework/HOMEWORK.md` | this file |

**Rule of thumb for every task:** copy the file you are changing (e.g.
`cp workshop/solution.py homework/task2.py`) and work on the copy.

---

## Task 1 · Memory that survives a restart  ⏱ ~20 min

**Practises:** checkpointers, `thread_id`.

In `demos/03_memory_and_hitl.py` the agent forgets everything when the script exits,
because `InMemorySaver` lives in the process memory.

**Do:** switch the graph to a SQLite checkpointer stored in `memory.db`, then split the
script so that one run says "My name is Alex" and a *second, separate* run asks
"What's my name?" on the same `thread_id`.

**Done when:**
- you run the script twice, and the second run answers "Alex";
- deleting `memory.db` makes the agent forget again;
- a different `thread_id` still knows nothing.

**Hints:**
```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver   # package: langgraph-checkpoint-sqlite (already installed)

checkpointer = SqliteSaver(sqlite3.connect("memory.db", check_same_thread=False))
graph = builder.compile(checkpointer=checkpointer)
```
Use `sys.argv` to choose what the run says, e.g. `python task1.py "What's my name?"`.

---

## Task 2 · Replace the human reviewer with an AI reviewer  ⏱ ~45 min

**Practises:** adding nodes, structured output, conditional edges, human-in-the-loop.

In `workshop/solution.py` a human approves the code in `human_review`. Turn the
self-correcting agent into a small multi-agent system.

**Do:**
1. Add a `reviewer` node: an LLM with structured output
   `Review(approved: bool, comments: str)` that checks the code against the task.
2. After the tests pass, go to `reviewer` instead of `human_review`.
3. Approved → `END`. Changes requested → back to `generate` with the comments as feedback.
4. Keep the human as a safety net: if the reviewer rejected the code **twice**, pause
   with `interrupt()` and let the human decide.

**Done when:**
- a normal run finishes without asking you anything;
- the output shows at least one reviewer comment being fixed by `generate`
  (tip: make the reviewer strict, e.g. "require a docstring and type hints");
- `--mermaid` shows the new `reviewer` node and its edges.

**Hints:** count rejections in state (`review_rejections: int`) and route on it in a
function, exactly like `after_test` routes on `attempts`.

---

## Task 3 · Time travel  ⏱ ~30 min

**Practises:** `get_state_history`, `update_state`, replaying from a checkpoint.

**Do:** run `solution.py` once. Then, in a new script that uses the same graph and
`thread_id` (you'll need the SQLite checkpointer from Task 1, otherwise the history is
gone when the process exits):
1. print the checkpoint history: step, next node, number of attempts, whether there was an error;
2. find the **first** checkpoint right after `test` failed;
3. from there, change the state with `update_state` — e.g. add feedback
   `"Use a regular expression with re.fullmatch"` — and continue the run.

**Done when:** the replay continues from the chosen checkpoint (steps before it are
not re-run — no new `generate` calls for them) and finishes with tests passing.

**Hints:**
```python
for snap in graph.get_state_history(cfg):          # newest first
    print(snap.metadata.get("step"), snap.next, snap.values.get("attempts"))

new_cfg = graph.update_state(snap.config, {"feedback": "..."})
graph.invoke(None, new_cfg)                        # None = no new input, continue
```

---

## Task 4 · Your own agent with real tools  ⏱ ~1 h

**Practises:** `@tool`, `ToolNode`, `tools_condition`, the ReAct loop, `interrupt()`.

Build a small agent for something you actually do. Example: a **notes assistant**
for a folder of `.md` files.

**Do:** a graph like demo 02/03 with at least three tools:
- two *safe* tools, e.g. `list_notes()` and `read_note(name)`;
- one *dangerous* tool, e.g. `write_note(name, text)`, that **always** pauses for
  human approval (and shows exactly what will be written).

**Done when:**
- "What notes do I have about Kafka?" uses the safe tools without asking you;
- "Add a summary of all Kafka notes to kafka-summary.md" pauses before writing;
- rejecting with feedback makes the agent revise the text and ask again.

**Hints:**
- write clear docstrings — they are the prompt for choosing a tool;
- route only the dangerous tool through approval: look at the tool names in
  `tool_calls` and send safe calls straight to `ToolNode`;
- restrict file access to one folder (never trust a path the model gives you).

---

## Task 5 · Parallel candidates with `Send`  ⏱ ~1 h

**Practises:** map-reduce, `Send`, reducers on parallel writes.

Instead of one attempt at a time, let `solution.py` generate **three candidate
solutions in parallel**, test all of them, and keep the first one that passes.

**Do:**
1. a fan-out edge that returns three `Send("generate_one", {...})` calls,
   each with a different hint ("simplest possible", "use regex", "parse char by char");
2. `generate_one` writes its code into a list field with a reducer;
3. a `pick_best` node tests every candidate and stores the first passing one;
4. if none passes, fall back to the old `reflect` → `generate` loop.

**Done when:** the run prints three candidates and which one won, and
`--mermaid` shows the fan-out.

**Hints:**
```python
import operator
from langgraph.types import Send

class AgentState(TypedDict, total=False):
    candidates: Annotated[list[str], operator.add]   # parallel writes are merged, not overwritten

def fan_out(state):
    return [Send("generate_one", {"task": state["task"], "hint": h}) for h in HINTS]

builder.add_conditional_edges(START, fan_out, ["generate_one"])
```
Think about why `candidates` *must* have a reducer here.

---

## Task 6 · Make the supervisor safer  ⏱ ~45 min

**Practises:** guards in code, `interrupt()` inside a multi-agent graph, observability.

In `workshop/stretch_supervisor_fixed.py`:
1. **Escalation:** if the reviewer requested changes **3 times in a row**, the guard
   stops the team and asks a human (`interrupt()`) what to do: `continue`, `finish`
   or free-text instructions for the coder.
2. **Budget:** count LLM calls per agent and stop with a clear message when the total
   goes over a limit (e.g. 25). Print a small table at the end: agent → calls.
3. **Change the task:** replace `slugify` with a function from your own domain and
   check how the team copes. Where does it get stuck? Which guard would fix it?

**Done when:** you can show a run where the escalation triggers, and a run that stops
on the budget.

---

## Bonus · See your graphs

- Print `graph.get_graph().draw_mermaid()` for each task and paste it into
  https://mermaid.live — compare the shapes.
- Stream every step: `for update in graph.stream(inputs, cfg, stream_mode="updates"): print(update)`.
- Try LangGraph Studio or LangSmith tracing on one of your graphs.

---

## How to hand in

Send the instructor a link to a repo or gist with:
- one file per task you did (`task1.py`, `task2.py`, …);
- the console output of one successful run per task;
- 2–3 sentences per task: what surprised you, and where the model needed a guard in code.

**Don't commit your `.env` / API key.** Add `.env` to `.gitignore` before the first commit.
