"""Task 3. Time travel: replay the agent from a checkpoint, with changed state.

Prerequisite (once):  python homework/task3_solution.py     (stores the run in task3.db)
Then:                 python homework/task3_result.py       (add --yes to auto-approve the human review)

What it does, on the same graph and thread_id as task3_solution.py:
  1. prints the checkpoint history: step, next node, attempts, whether there was an error;
  2. finds the FIRST checkpoint right after `test` failed;
  3. forks from it with update_state(feedback=...) and continues the run, printing every node
     that executes, so you can see that nothing before the checkpoint is run again.
"""
import sys

from langgraph.types import Command

from task3_solution import DB_PATH, THREAD_ID, graph

FEEDBACK = "Use a regular expression with re.fullmatch"
AUTO_YES = "--yes" in sys.argv

cfg = {"configurable": {"thread_id": THREAD_ID}}


def one_line(error: str | None) -> str:
    return error.strip().splitlines()[-1][:60] if error else ""


def checkpoint_id(snap) -> str:
    return snap.config["configurable"]["checkpoint_id"][-6:]


def print_history(history: list, mark: str | None = None) -> None:
    """History is listed oldest first."""
    print(f"{'step':>4}  {'id':6}  {'next':14} {'attempts':>8}  error")
    for snap in history:
        v = snap.values
        pointer = "  ◀ chosen" if mark and checkpoint_id(snap) == mark else ""
        print(f"{snap.metadata.get('step'):>4}  {checkpoint_id(snap):6}  {str(snap.next or '(end)'):14} "
              f"{v.get('attempts', '-'):>8}  {one_line(v.get('error')) or '-'}{pointer}")


def first_failed_test(history: list):
    """After `test` fails the state holds the error and the next node is `reflect`."""
    for snap in history:                                  # oldest first
        if snap.values.get("error") and snap.next == ("reflect",):
            return snap
    return None


def run_from(config: dict, first_input) -> dict | None:
    """Continue the graph, printing each node as it runs. Handles human-review pauses."""
    executed = []
    for _ in range(5):                                    # a few human pauses at most
        paused = None
        for update in graph.stream(first_input, config, stream_mode="updates"):
            for node, out in update.items():
                if node == "__interrupt__":
                    paused = out[0].value
                    continue
                executed.append(node)
                if node == "generate":
                    print(f"   ▶ generate (attempt {out['attempts']})")
                elif node == "test":
                    print(f"   ▶ test: {'passed' if out['error'] is None else one_line(out['error'])}")
                else:
                    print(f"   ▶ {node}")
        if paused is None:
            return executed
        print("\n" + "─" * 60 + f"\n{paused['code']}\n" + "─" * 60)
        answer = "yes" if AUTO_YES else input(f"{paused['question']} > ")
        print(f"   human: {answer}")
        # Resume on the thread's LATEST checkpoint. `config` pins the checkpoint we forked from,
        # and resuming with it would restart the fork from there.
        config, first_input = cfg, Command(resume=answer)
    raise RuntimeError("too many human-review pauses")


def main() -> int:
    history = list(reversed(list(graph.get_state_history(cfg))))
    if not history:
        sys.exit(f"No history for thread {THREAD_ID!r} in {DB_PATH.name}. Run task3_solution.py first.")

    print(f"═══ 1. Checkpoint history of thread {THREAD_ID!r} ({len(history)} checkpoints) ═══")
    print_history(history)

    print("\n═══ 2. First checkpoint right after `test` failed ═══")
    chosen = first_failed_test(history)
    if chosen is None:
        sys.exit("`test` never failed in this run, so there is nothing to replay. "
                 "Delete homework/task3.db and run task3_solution.py again.")
    print(f"checkpoint {checkpoint_id(chosen)}: step={chosen.metadata.get('step')}, "
          f"attempts={chosen.values['attempts']}, next={chosen.next}")
    print(f"error: {one_line(chosen.values['error'])}")

    print(f"\n═══ 3. Fork from it with feedback: {FEEDBACK!r} ═══")
    new_cfg = graph.update_state(chosen.config, {"feedback": FEEDBACK})
    print("nodes executed in the replay (steps before the checkpoint are NOT re-run):")
    executed = run_from(new_cfg, None)                    # None = no new input, continue from the checkpoint

    final = graph.get_state(cfg).values                   # newest checkpoint of the thread = end of the new branch
    print("\n═══ Result ═══")
    print(f"first node after the checkpoint: {executed[0]};  generate calls in the replay: {executed.count('generate')}")
    print(f"history grew from {len(history)} to {len(list(graph.get_state_history(cfg)))} checkpoints (a new branch)")
    print(f"tests passing: {final.get('error') is None}, attempts: {final.get('attempts')}")
    print(f"\nFinal code:\n{final.get('code')}")
    return 0 if final.get("error") is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
