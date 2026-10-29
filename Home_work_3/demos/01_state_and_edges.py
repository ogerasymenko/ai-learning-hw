"""Demo 1. State, reducers, nodes, conditional edges and a loop. No LLM or API key needed.

What to show:
  * `log` has a reducer (operator.add) and gets appended; `counter` has none and gets overwritten
  * a node returns a PARTIAL state update
  * a conditional edge is just a function that returns the name of the next node
  * the loop increment -> increment -> ... -> finish

Run:  python demos/01_state_and_edges.py
"""
import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    counter: int                              # no reducer: new value overwrites the old one
    log: Annotated[list[str], operator.add]   # reducer: lists are concatenated


def increment(state: State) -> dict:
    n = state["counter"] + 1
    return {"counter": n, "log": [f"increment: counter = {n}"]}   # only what changes


def finish(state: State) -> dict:
    return {"log": [f"finish: counted to {state['counter']}"]}


def route(state: State) -> Literal["increment", "finish"]:
    return "finish" if state["counter"] >= 3 else "increment"


builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_node("finish", finish)
builder.add_edge(START, "increment")
builder.add_conditional_edges("increment", route)   # loop: increment can go back to increment
builder.add_edge("finish", END)
graph = builder.compile()


if __name__ == "__main__":
    print("── Mermaid (paste into https://mermaid.live) ──")
    print(graph.get_graph().draw_mermaid())

    print("── stream(stream_mode='updates'): what each node returned ──")
    for update in graph.stream({"counter": 0, "log": []}, stream_mode="updates"):
        print(update)

    print("\n── invoke: final state ──")
    final = graph.invoke({"counter": 0, "log": ["start"]})
    for line in final["log"]:
        print("  ", line)
    print("counter =", final["counter"])

    print("\n── Infinite-loop guard: recursion_limit ──")
    try:
        graph.invoke({"counter": -100, "log": []}, {"recursion_limit": 10})
    except Exception as e:  # GraphRecursionError
        print(f"{type(e).__name__}: {str(e).splitlines()[0]}")
