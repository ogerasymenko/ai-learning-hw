# LangGraph Workshop — participant kit

Build stateful, cyclic AI agents with LangGraph: state, nodes, edges, memory,
human-in-the-loop, and a self-correcting agent you write yourself.

## 1. Before the workshop (10 minutes)

You need **Python 3.10+** and an **LLM API key**.

**Get a free key (recommended):** sign in at https://console.groq.com/keys →
*Create API Key* → copy it (starts with `gsk_`, shown only once).

### macOS / Linux

```bash
cd langgraph-workshop
bash setup.sh                 # creates .venv, installs everything, creates .env
source .venv/bin/activate     # run this in EVERY new terminal window
```

### Windows (PowerShell)

```powershell
cd langgraph-workshop
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### Put your key into `.env`

```
GROQ_API_KEY=gsk_your_key_here
MODEL=groq:openai/gpt-oss-120b
```

`MODEL` is always `<provider>:<model id>`. Anthropic or OpenAI keys work too — see `.env.example`.

### Check that everything works

```bash
python 00_sanity_check.py
```

You should see `✅ Environment is ready`. If not, see *Troubleshooting* below or
bring your laptop a few minutes early.

## 2. What's inside

| File | What it is |
|---|---|
| `00_sanity_check.py` | environment and API key check |
| `demos/01_state_and_edges.py` | state, reducers, conditional edges, a loop (no API key needed) |
| `demos/02_react_agent.py` | a ReAct agent with tools, built by hand |
| `demos/03_memory_and_hitl.py` | memory per thread, state inspection, time travel, human-in-the-loop |
| `workshop/starter.py` | **your hands-on task**: a self-correcting code agent with TODO 1–4 |
| `workshop/stretch_supervisor.py` | multi-agent demo: an LLM supervisor runs a team — planner, coder, tester (no LLM), reviewer |

## 3. The hands-on task

Open `workshop/starter.py`. The agent gets a task (write `parse_duration("1h30m") → 5400`),
writes code, runs the tests itself, analyses failures and fixes its own code until the
tests pass — then pauses for your approval.

```bash
python workshop/starter.py
```

Fill in the TODOs in order and uncomment the edges as your nodes become ready.
When the graph pauses, answer `yes` to accept, or type feedback to send the code back.

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found: python` / `pip` | Activate the environment: `source .venv/bin/activate` |
| `No module named pip` inside `.venv` | The env was created with `uv`: use `uv pip install ...` |
| Python is 3.9 or older | macOS: `brew install python@3.12`, then `bash setup.sh` again |
| `Unable to infer model provider` | Add the provider prefix: `MODEL=groq:openai/gpt-oss-120b` |
| `GROQ_API_KEY not found` | Put your real key into `.env` (not `.env.example`) |
| `429` / rate limit | Use your own key, not a shared one |
