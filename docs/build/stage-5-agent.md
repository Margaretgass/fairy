# Stage 5 — Your own agent

> **By the end of this stage** you'll run `uv run fairy chat` and talk to a fully local AI
> that uses your tools — no API key, no internet, nothing leaving your machine.

**Sessions:** 5 · **Time:** ~3 weeks

**Your MCP servers do not change at all.** That's the payoff of having built on a protocol:
you swap the client, and the tools stay exactly as they are.

This is the headline stage for an AI-engineering portfolio. The rare skill on display isn't
prompt writing — it's **reliability engineering around a model that isn't reliable**.

### What you'll learn

| Concept | Where |
|---|---|
| Provider abstraction — swapping models with one config line | Session 1 |
| `async`/`await`, and when it's actually worth it | Session 1 |
| Schema-constrained decoding | Session 2 |
| Validate-and-retry loops | Session 2 |
| Evaluating a model instead of trusting it | Session 3 |
| MCP from the **client** side | Session 4 |
| Agent loops and their guardrails | Session 5 |

### Setup

```bash
brew install ollama
```

```bash
ollama serve
```

Leave that running, and in a new terminal tab:

```bash
ollama pull qwen3:4b
```

```bash
ollama run qwen3:4b "say hello in five words"
```

**Why Qwen.** It's explicitly trained for tool calling and has the best structured-output
reliability in the small-model range. On your 8 GB expect **10–20 tokens/sec** — close some
tabs. `ollama stop qwen3:4b` frees the memory when you're done testing.

If it's painfully slow, `ollama pull llama3.2:3b` and change one line of config. That
one-line swap is exactly what Session 1 is for.

```bash
cd ~/code/fairy && uv add ollama
```

---

## Session 1 — The provider interface

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** never call Ollama directly from your app code.

```bash
mkdir -p ~/code/fairy/src/fairy/agent && touch ~/code/fairy/src/fairy/agent/__init__.py
```

`src/fairy/agent/provider.py`:

```python
"""Talking to language models, without caring which one."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel


class Message(BaseModel):
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        messages: list[Message],
        *,
        schema: dict[str, Any] | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        """Return the model's reply. If schema is given, the reply is valid JSON."""
        ...
```

Write **three** implementations:

| Provider | Purpose |
|---|---|
| `OllamaProvider` | local, private, free — your default |
| `GroqProvider` | free tier, fast, no GPU — how other people run your project |
| `StubProvider` | canned replies — tests and demo mode |

### Why `StubProvider` is not optional

It does two jobs that matter enormously:

1. **Your tests become fast and hermetic.** A test suite that needs a 4 GB model running is
   a test suite you stop running. CI can't run one at all.
2. **A stranger can run your project.** Clone, `uv sync`, `FAIRY_LLM_PROVIDER=stub`, and it
   works with no model, no key, no GPU.

Build it now. Retrofitting it later means touching every call site.

### Understanding `async` and `await`

```python
async def complete(self, messages, *, schema=None) -> str:
    response = await client.chat(...)
```

`async def` makes a **coroutine**: a function that can pause partway through. `await` is
where it pauses — "start this, and let other code run while we wait."

**Why here and not in Stage 1?** Waiting for a model takes 5–30 seconds, and that's *waiting
on something else*, not computing. Async lets your program do other things meanwhile.

Your SQLite code stays synchronous, and that's correct — it's fast and local, so there's
nothing to wait for. **Async is for waiting, not for speed.** Adding it where nothing waits
just makes code harder to read.

### Selecting a provider

```bash
cd ~/code/fairy && cat >> .env <<'ENV'
FAIRY_LLM_PROVIDER=ollama
FAIRY_MODEL=qwen3:4b
ENV
```

Read them with `os.environ.get("FAIRY_LLM_PROVIDER", "ollama")`. One line changes your whole
model — that's what the abstraction bought you.

### ✔ Check yourself

```bash
curl -s http://localhost:11434/api/tags | head -c 200
```

That confirms Ollama is running. Then each provider:

```bash
cd ~/code/fairy && uv run python -c "
import asyncio
from fairy.agent.provider import Message, OllamaProvider
async def go():
    p = OllamaProvider()
    print(await p.complete([Message(role='user', content='reply with one word')]))
asyncio.run(go())
"
```

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `Connection refused` on 11434 | `ollama serve` isn't running |
| `model 'qwen3:4b' not found` | `ollama pull qwen3:4b` — and check the tag still exists with `ollama list` |
| `RuntimeWarning: coroutine was never awaited` | You called an `async def` without `await` |
| Extremely slow / machine swapping | 8 GB is tight. Close tabs, or use `llama3.2:3b` |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add LLM provider interface with ollama, groq, and stub" && git push
```


---

## Session 2 — Structured output that actually holds

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** the most valuable technique in this whole project.

### The problem

Ask a 4B model politely for JSON and you'll sometimes get prose, sometimes markdown fences,
sometimes almost-JSON with a trailing comma. Parsing that reliably is impossible.

### The solution: constrain the generation itself

Ollama can **restrict the model's output to a JSON schema**. Not "please produce JSON" —
the invalid tokens are not available to pick. Malformed JSON becomes ungenerable.

```python
from pydantic import BaseModel


class ExtractedTask(BaseModel):
    title: str
    category: str
    reason: str


class BrainDump(BaseModel):
    tasks: list[ExtractedTask]


async def extract_tasks(provider: LLMProvider, text: str) -> BrainDump:
    schema = BrainDump.model_json_schema()
    raw = await provider.complete(
        [Message(role="user", content=PROMPT.format(text=text))],
        schema=schema,  # Ollama receives this as `format`
    )
    return BrainDump.model_validate_json(raw)
```

`model_json_schema()` is a Pydantic method that turns your class into a JSON Schema
document. You wrote the class once; it serves as the type, the validator, **and** the
constraint handed to the model.

### The three-step loop

```
1. CONSTRAIN   pass the schema      -> invalid JSON cannot be generated
2. VALIDATE    Pydantic checks it   -> valid JSON can still be WRONG
3. RETRY       send the error back  -> twice, then fail honestly
```

**Why step 2 when step 1 guarantees valid JSON?** Because "valid" and "correct" differ. The
model can return `{"category": "Banana"}` — perfectly valid JSON, not one of your four
categories. Pydantic catches that; the schema alone doesn't.

**Why step 3.** Small models make small mistakes. Handing back the actual validation error
("Banana is not a valid Category") usually gets a correct answer on the second try. Cap it
at two retries and then report failure — an agent that retries forever is worse than one
that admits defeat.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
import asyncio
from fairy.agent.extract import extract_tasks
from fairy.agent.provider import OllamaProvider
text = 'email prof about extension, stats hw thursday, laundry sometime'
print(asyncio.run(extract_tasks(OllamaProvider(), text)))
"
```

You should get a `BrainDump` with about three tasks. Expect 5–30 seconds on your hardware.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `ValidationError` on `category` | The model invented a category. This is exactly what the retry loop is for |
| Output is prose, not JSON | The schema isn't reaching Ollama — it goes in the `format` parameter |
| Same wrong answer on every retry | You're not feeding the validation error back into the retry prompt |
| Times out | Lower your expectations of a 4B model, or raise the timeout |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: schema-constrained task extraction from brain dumps" && git push
```


---

## Session 3 — The eval harness ★

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** be able to answer *"is it any good?"* with a number.

Most portfolio projects can't. This is the session that distinguishes yours.

```bash
mkdir -p ~/code/fairy/tests/evals/cases
```

Each case is an input plus what a reasonable answer looks like:

`tests/evals/cases/01-messy-monday.json`:

```json
{
  "name": "messy monday",
  "input": "ugh ok so i need to email prof about the extension, stats hw due thurs, and laundry at some point. also dentist??",
  "expect": {
    "min_tasks": 3,
    "max_tasks": 5,
    "must_mention": ["email", "stats", "laundry"],
    "categories_subset_of": ["Anchor", "Quest", "Maintenance", "Optional"]
  }
}
```

### Why the expectations are ranges, not exact strings

There's no single correct extraction. "email prof about the extension" could reasonably
become *"Email professor about extension"* or *"Ask prof for an extension"* — both fine.

So you assert **properties**, not exact output: how many tasks, which words appear, whether
categories are legal. This is the core skill of evaluating language models — pinning down
what must be true without pretending there's one right answer.

Write ten cases. Include the awkward ones: empty input, a single task, a wall of text, a
message with no tasks in it at all.

### The scorer

About fifty lines: load each case, run the extractor, check the expectations, print a table.

```
provider          model            cases  passed  avg latency
ollama            qwen3:4b            10       9        8.4s
groq              llama-3.3-70b       10      10        0.6s
stub              -                   10      10        0.0s
```

**Put that table in your README.** It demonstrates the judgement an AI team is actually
hiring for: you can *measure* a model rather than just call one.

Mark them slow so normal CI skips them:

```python
@pytest.mark.slow
def test_extraction_eval(): ...
```

```bash
cd ~/code/fairy && uv run pytest -m slow
```

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run pytest -m slow -v
```

You should see per-case results and a summary table. **Some failures are fine and
informative** — a 4B model won't score 10/10, and knowing where it fails is the point.

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| `'slow' not found in markers` | Add `markers = ["slow: needs a live model"]` to `[tool.pytest.ini_options]` |
| Every case fails | Run one by hand first — it's usually the provider, not the scoring |
| Results differ every run | Expected. That's why you assert properties, not exact strings |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "test: add eval harness scoring extraction across providers" && git push
```


---

## Session 4 — The MCP client

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** consume the servers you wrote in Stages 1–4.

FastMCP does both sides of the protocol:

```python
from fastmcp import Client


async def list_available_tools() -> list[dict]:
    async with Client("src/fairy/servers/tasks_server.py") as client:
        tools = await client.list_tools()
        return [t.model_dump() for t in tools]
```

`async with` is a context manager like Stage 1's `with store.session()`, except it can
await during setup and teardown. It starts your server as a subprocess, talks to it over
stdio, and shuts it down cleanly when the block ends.

Build a `ToolRegistry` that connects to all your servers, collects every tool definition,
and dispatches a call by name. Your agent then works against **one registry** instead of
knowing about seven servers.

### Something worth trying

Once this works, **Claude Desktop and your own agent can use the same servers at the same
time.** Two different clients, one set of tools, no changes to either. That's what building
on a protocol gets you, and it makes a good thing to demo.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
import asyncio
from fairy.agent.registry import list_available_tools
for t in asyncio.run(list_available_tools()): print(t['name'])
"
```

You should see `add_task`, `list_tasks`, `complete_task` — the tools you wrote in Stage 1,
now discovered over the protocol.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| Hangs with no output | The server crashed on startup. Run `uv run fairy-tasks` directly and read the traceback |
| `FileNotFoundError` on the server path | Use an absolute path, or the command name from `[project.scripts]` |
| Tools list is empty | `@mcp.tool` decorators missing, or the module defining them was never imported |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add MCP client and tool registry" && git push
```


---

## Session 5 — The loop

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** the agent itself. It's smaller than you'd expect.

```
1. build context     time, today's tasks, current timer, relevant items
2. ask the model     with the tool list attached
3. did it call a tool?
      yes -> run it, append the result, go back to 2
      no  -> return the reply to the user
4. stop after N iterations, always
```

That's it. An agent is a while-loop around a model that can call functions.

### The guardrails matter more than the loop

| Guard | Why |
|---|---|
| **Hard iteration cap** (5 is plenty) | Without it, a confused model loops forever burning your battery |
| **Timeout per tool call** | One hung connector shouldn't hang the agent |
| **Never auto-run destructive tools** | Reads run freely. Writes and deletes get confirmed |
| **Log every tool call** — name, arguments, duration | When behaviour is strange, this log is the *only* thing that tells you why |

That last one is worth taking seriously. Debugging an agent without a tool-call log means
guessing at what a model decided to do. With one, you just read what happened.

Add the CLI entry point:

```toml
[project.scripts]
fairy = "fairy.agent.cli:main"
```

```bash
cd ~/code/fairy && uv sync && uv run fairy chat
```

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run fairy chat
```

Try: *"what's on my list?"* then *"add one to buy milk"* then *"what's on my list now?"*

The third answer must include the second — that's proof the loop is actually feeding tool
results back into the conversation.

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| Loops forever | Your iteration cap isn't enforced. Cap at 5 |
| Calls a tool then ignores the result | The tool output isn't being appended to `messages` |
| Invents tools that don't exist | Your tool list isn't reaching the model, or docstrings are too vague |
| Correct but painfully slow | Normal for 4B locally. Try Groq to compare |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add agent loop with tool calling" && git push
```


---

## ✅ Stage 5 complete

**You built:** a fully local agent — no API key, no internet, your data never leaves your
machine.

**You learned:**

- **Provider abstraction** — swap models with one environment variable
- `async`/`await`, and that it's for **waiting**, not speed
- **Schema-constrained decoding** — making invalid output ungenerable
- **Validate-and-retry** — because valid isn't the same as correct
- **Evaluating** a model with property-based expectations
- **MCP from the client side**
- Agent loops, and why the guardrails are the real work

### Stretch exercise (optional)

Add a `--provider` flag to `fairy chat` so you can switch between ollama, groq and stub
without editing `.env`.

Then run the same three eval cases through all three and look at the table. Where does the
4B model fail that the 70B one doesn't? Is it worth the latency difference for your actual
use? **Write the answer in `docs/decisions/`** — a reasoned model-selection note backed by
your own numbers is exactly the kind of artefact that gets discussed in interviews.

Next: [Stage 6 — Web UI](stage-6-web-ui.md)
