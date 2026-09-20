# Stage 1 — Existing local app foundation

> **Status:** Core implementation complete and live-verified. The browser UI is already
> connected to the local AI. This stage does not rebuild that connection. It documents the
> working architecture and adds missing automated coverage and quality cleanup.

**Stage outcome:** you can explain and safely verify the connection you already built, and
CI protects its API contract before work begins on the desktop Fairy.

**Estimated sessions:** 3 small sessions. Stop after each session and report the result
before continuing.

---

## Why this stage matters

The repository already has a real vertical slice:

```text
Browser → FastAPI → LangChain ChatOllama → local Ollama → qwen2.5:3b → browser
```

The connection is done. The remaining work here is characterization testing, cleanup, and
accurate documentation—not another integration project. After this short hardening pass,
the desktop Fairy reuses the existing API instead of creating a second chat system.

The [NeuroFairy architecture map](ARCHITECTURE.md) shows this current path alongside the
target desktop, task, planning, focus, safe-tool, and read-only integration architecture.

---

## Current starting point

### Implemented and verified

- Python 3.14 project managed with `uv`
- FastAPI application in `src/fairy/web_app.py`
- Existing UI served from `uiux/ui/`
- Browser chat submission to `POST /api/chat`
- Local chat service using LangChain `ChatOllama`
- Installed local model `qwen2.5:3b`
- Direct model smoke test
- Live FastAPI-to-Ollama request returning HTTP 200
- Eight passing SQLite task tests

**The Talk UI already sends real messages to the local model and renders its replies.** The
words “simulated AI” and “scripted replies” still visible in the prototype are stale labels,
not a description of the current chat behavior.

### Implemented but missing committed automated coverage

- Chat route success behavior
- Empty-message behavior
- Request validation behavior
- Model-failure fallback
- Static UI serving

### Known baseline issues

- `ruff check .` reports two line-length errors.
- `.env.example` names `qwen3:4b`, while the working service uses `qwen2.5:3b`.
- The browser still labels the conversation as simulated/scripted.
- The root README says only Stage 1 task work exists.
- Most non-chat UI state is a browser prototype stored in `localStorage`.

Do not “fix” those facts by changing the status labels. Fix the behavior or documentation,
verify it, and then update the status.

---

## Learning goals

By the end of this stage, you should be able to explain:

- What an HTTP route is
- How Pydantic validates an API request schema
- Why the route and local-model service are separate layers
- How the browser sends JSON and receives JSON
- Why a deterministic integration test replaces the live model with a fake
- What a live-model smoke test proves that deterministic tests do not
- How a lockfile and reproducible commands support portfolio credibility
- How to distinguish implemented UI behavior from prototype-only state

---

## Concepts in plain English

### Route

A route connects an HTTP method and URL to a Python function. Here, `POST /api/chat` calls
`chat_with_neurofairy()`.

### Schema

A schema describes and validates data crossing a boundary. `ChatRequest` requires a
`message` string before the route runs.

### Service

A service performs an application operation behind a stable function boundary.
`reply_to_user(message)` hides the details of LangChain and Ollama from the FastAPI route.

### Dependency

A dependency is code this project relies on, such as FastAPI or `langchain-ollama`.
Dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

### Integration test

An integration test verifies that multiple units work together. The route tests in this
stage exercise FastAPI request parsing, routing, response formatting, and fallback behavior.
They replace the actual model call so they remain fast and deterministic.

### Smoke test

A smoke test answers “does the real path basically work?” The direct Ollama test is useful,
but its wording can vary and it requires a running local model, so it does not belong in
normal CI.

---

## Files used in this stage

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Python version, dependencies, scripts, and test/lint configuration |
| `uv.lock` | Exact resolved dependency versions |
| `.env.example` | Documented optional environment configuration; never real secrets |
| `src/fairy/prompts.py` | NeuroFairy system prompt |
| `src/fairy/neurofairy_chat.py` | LangChain/ChatOllama service boundary |
| `src/fairy/test_local_model.py` | Manual live-model smoke test |
| `src/fairy/web_app.py` | FastAPI route and static UI mounts |
| `uiux/ui/index.html` | Browser shell |
| `uiux/ui/app.js` | Browser state, rendering, and `/api/chat` request |
| `tests/test_web_app.py` | Deterministic API integration tests added in this stage |
| `README.md` | Current project setup and honest status summary |
| `docs/build/ARCHITECTURE.md` | Current and target system diagrams maintained across stages |

---

## Prerequisites

Before starting:

```bash
cd ~/code/fairy
git status --short --branch
uv sync
uv run python --version
ollama list
```

Expected:

- You are in `~/code/fairy`.
- Python is 3.13 or newer; the verified development runtime is 3.14.2.
- `qwen2.5:3b` appears in `ollama list`.
- You understand whether `git status` is clean before making changes.

If `ollama list` reports connection refused, start the Ollama application/service before
running live-model checks. The deterministic tests do not require Ollama.

---

## Session 1 — Orient yourself to the existing connection

### Practical goal

Trace and verify the connection that is already implemented. Do not rewrite it.

### Why no file changes yet

This is an observation session. It establishes the baseline and makes sure you can explain
your own architecture before the desktop app starts consuming the same API.

### Step 1: run the existing deterministic tests

```bash
cd ~/code/fairy
uv run pytest
```

Expected: 8 task tests pass.

### Step 2: check formatting and linting separately

```bash
uv run ruff format --check .
uv run ruff check .
```

Expected at the current baseline:

- Formatting passes.
- Linting reports two `E501` errors: one in `prompts.py` and one in `web_app.py`.

A known failure is not a successful check. Record it so Session 3 can close it.

### Step 3: run the real local-model smoke test

```bash
uv run python -m fairy.test_local_model
```

Expected: a short response that gives one visible first step for emailing a professor. The
exact wording can vary.

### Step 4: run the browser app

```bash
uv run uvicorn fairy.web_app:app --reload
```

Open `http://127.0.0.1:8000`, select **Talk**, send a message, and confirm a reply appears.

In the browser Network tab, inspect the request:

- Method: `POST`
- URL: `/api/chat`
- Request JSON contains `message`
- Response JSON contains `reply`
- Status: `200`

### Most likely error

If the browser shows its connection fallback, look at the terminal running Uvicorn first.
Then check `ollama list`. The browser, FastAPI server, and Ollama service are three separate
process boundaries; identify which one is unavailable before changing code.

### Stop checkpoint

Report:

- pytest result
- Ruff format result
- Ruff lint result
- direct model response
- browser/API result

Do not commit anything from this session because nothing changed.

### Full-file recovery checkpoint

[Session 1 expected baseline output](checkpoints/stage-1-session-1.md) records the complete
test, lint, live-model, and browser result. It explicitly confirms that this observation
session has no code file to replace.

---

## Session 2 — Add deterministic chat-route tests

### Practical goal

Protect the working API contract without starting Ollama during every test run.

### Engineering concept

The route depends on `reply_to_user()`. In a deterministic test, `monkeypatch` temporarily
replaces that function with a controlled fake. This tests the route boundary rather than
the model's creativity or availability.

### Why this belongs in this file

Route behavior belongs in `tests/test_web_app.py`. Model-quality evaluation is a different
kind of test and comes later.

### Exact paths

Create the test file and update the project metadata:

```text
tests/test_web_app.py
pyproject.toml
uv.lock
```

### Change type

Declare the packages this repository uses directly, then add one new test file. Do not
modify application code in this session.

### Step 1: declare direct dependencies

The current dependency graph brings both packages into the environment transitively:
FastAPI supplies Pydantic, while the LangChain stack currently supplies HTTPX. This project
imports Pydantic itself and its route tests rely on HTTPX through `TestClient`, so record
those direct relationships explicitly:

```bash
uv add pydantic
uv add --dev httpx
```

Expected: `pyproject.toml` lists `pydantic` under runtime dependencies and `httpx` under the
development dependency group. `uv.lock` is regenerated. Do not edit the lockfile by hand.

### Step 2: add the smallest complete test file

```python
from fastapi.testclient import TestClient

from fairy import web_app

client = TestClient(web_app.app)


def test_chat_returns_trimmed_message_to_service(monkeypatch):
    messages: list[str] = []

    def fake_reply(message: str) -> str:
        messages.append(message)
        return "Open the document."

    monkeypatch.setattr(web_app, "reply_to_user", fake_reply)

    response = client.post("/api/chat", json={"message": "  I am stuck  "})

    assert response.status_code == 200
    assert response.json() == {"reply": "Open the document."}
    assert messages == ["I am stuck"]


def test_empty_chat_returns_local_prompt_without_calling_model(monkeypatch):
    def unexpected_call(message: str) -> str:
        raise AssertionError(f"model should not receive {message!r}")

    monkeypatch.setattr(web_app, "reply_to_user", unexpected_call)

    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 200
    assert response.json() == {"reply": "I’m here. Whenever you’re ready."}


def test_missing_message_is_rejected():
    response = client.post("/api/chat", json={})

    assert response.status_code == 422


def test_model_failure_returns_safe_fallback(monkeypatch):
    def failing_reply(message: str) -> str:
        raise RuntimeError(f"Ollama unavailable for {message!r}")

    monkeypatch.setattr(web_app, "reply_to_user", failing_reply)

    response = client.post("/api/chat", json={"message": "Help me start"})

    assert response.status_code == 200
    assert response.json()["reply"].startswith("I'm having trouble")


def test_root_serves_browser_ui():
    response = client.get("/")

    assert response.status_code == 200
    assert "ADHD Fairy" in response.text
```

### Run the narrow test

```bash
uv run pytest tests/test_web_app.py -v
```

Expected: 5 tests pass without contacting Ollama.

Then run the full suite:

```bash
uv run pytest
```

Expected: 13 tests pass.

### Most likely error

If the fake is ignored and the test contacts Ollama, patch the name used by the route:
`fairy.web_app.reply_to_user`. Patching the original definition in
`fairy.neurofairy_chat` does not replace the reference already imported by `web_app.py`.

### Commit checkpoint

Only after both commands pass:

```text
test: cover chat API contract
```

Stop and report the test output before Session 3.

### Full-file recovery checkpoint

If the incremental instructions become unclear, use the
[Session 2 complete files and expected output](checkpoints/stage-1-session-2.md). It links
all of `pyproject.toml` and contains `tests/test_web_app.py` from first line to last line.

---

## Session 3 — Restore the quality baseline and finish the foundation docs

### Practical goal

Fix the two known lint errors, align the documented model, and update stale project copy.

### Engineering concept

Quality checks are executable project policy. Leaving a known lint failure makes future
failures ambiguous and teaches contributors that CI failures are optional.

### Files to edit

```text
src/fairy/prompts.py
src/fairy/web_app.py
.env.example
uiux/ui/index.html
uiux/ui/app.js
README.md
```

### Change 1: replace the long prompt example

In `src/fairy/prompts.py`, replace the first long NeuroFairy example response with:

```text
Neurofairy: "Start with the email if it has a deadline or affects someone else.
Open it and write only the subject line. Then tell me when the assignment is due."
```

This also corrects the existing phrase “what the assignment is due date is.”

### Change 2: shorten the model-error fallback

In `src/fairy/web_app.py`, replace only the fallback reply string with:

```python
"I'm having trouble thinking clearly. Try again later. "
"For now, choose one small action."
```

Do not change the HTTP contract or add logging in this session.

### Change 3: correct the documented model tag

In `.env.example`, change:

```text
FAIRY_MODEL=qwen3:4b
```

to:

```text
FAIRY_MODEL=qwen2.5:3b
```

Also remove the Groq hosted-fallback lines. A future hosted alternative must be clearly
optional and must not become a hidden dependency.

The current code still hard-codes `qwen2.5:3b`; do not imply that `.env.example` is loaded
until a later configuration change actually implements that behavior.

### Change 4: remove stale simulated-chat labels

The chat is already connected. Update only the stale descriptive copy:

- In `uiux/ui/index.html`, keep the design-prototype/sample-data warning but remove the
  claim that AI is simulated or chat is scripted.
- In `uiux/ui/app.js`, replace `Demo · scripted replies` with concise copy that identifies
  the local AI connection, such as `Local AI · Ollama`.

Do not redesign the interface or change the request code in this session.

### Change 5: update the root README

Revise `README.md` so it contains, in this order:

1. One-sentence product purpose
2. Honest current status, including the working UI-to-AI connection
3. Current request-flow diagram
4. Setup prerequisites: Python, `uv`, Ollama, and `qwen2.5:3b`
5. Commands for tests, direct model smoke test, and browser app
6. Implemented versus planned feature summary
7. Link to this build curriculum

Do not claim that the model has tools, that browser state is persisted to SQLite, or that
any connector is working.

### Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Expected:

- Ruff lint passes.
- Ruff formatting passes.
- All 13 tests pass.

Then run the existing live path as a regression smoke test:

```bash
ollama list
uv run python -m fairy.test_local_model
uv run uvicorn fairy.web_app:app --reload
```

Open `http://127.0.0.1:8000`, send one Talk message, confirm the real reply, and stop the
server with `Ctrl-C`. This verifies the connection; it does not implement it.

### Most likely error

If Ruff still reports `E501`, read the exact file and column it prints. Do not disable the
rule or increase the project line length for two strings.

### Commit checkpoint

Only after all three commands pass:

```text
fix: restore clean local app baseline
```

Stop and report the automated checks and live smoke-test result before starting Stage 2.

### Full-file recovery checkpoint

Use the [Session 3 complete files and expected output](checkpoints/stage-1-session-3.md) if
you get stuck. It provides complete copy-ready versions of every source, configuration,
browser, and README file changed in this session.

---

## Stage acceptance criteria

Stage 1 is complete only when:

- `uv sync` succeeds from the documented setup.
- `uv run ruff check .` passes.
- `uv run ruff format --check .` passes.
- `uv run pytest` passes with the new chat-route tests.
- `qwen2.5:3b` appears in `ollama list`.
- The direct local-model smoke test returns a useful response.
- The browser can send a message through `/api/chat` and display the reply.
- The root README describes the actual stack and status.
- Hosted models are not required.
- No connector, tool-calling, or synchronized task behavior is falsely claimed.

---

## Complete Stage 1 recovery snapshot

The [Stage 1 final recovery snapshot](checkpoints/stage-1-final.md) maps every file created
or changed by this stage to its complete final contents and records the final expected test,
lint, browser, and local-model results.

---

## Automated tests and manual smoke tests

### Automated

- Task add, list, complete, and missing-task tests. `delete_task` exists on the current
  branch but is not covered yet; add its success and missing-task tests in Stage 3 before
  describing the task layer as full CRUD.
- Chat success with a fake service
- Whitespace-only chat behavior
- Missing request field validation
- Model-failure fallback
- Static root serving

### Manual

- Ollama model availability
- Direct ChatOllama response
- Uvicorn startup
- Browser rendering
- Browser-to-API request
- Concise, actionable live response

Live-model output should be assessed by properties, not exact wording: brief, warm,
non-shaming, and centered on one realistic visible action.

---

## Common errors and debugging

| Error or symptom | Responsible layer | Smallest inspection step |
|---|---|---|
| `ModuleNotFoundError: fairy` | Environment/package | Run from `~/code/fairy`, then `uv sync` |
| `Connection refused` on port 11434 | Ollama | Run `ollama list` |
| `model not found` | Ollama model inventory | Run `ollama pull qwen2.5:3b` only if it is absent |
| Browser cannot open port 8000 | Uvicorn | Read the server terminal output |
| HTTP 422 | Request schema | Inspect request JSON for `message` |
| Browser shows connection fallback | Browser/API/model boundary | Inspect Network response, then Uvicorn traceback |
| Tests unexpectedly call Ollama | Test patch target | Patch `fairy.web_app.reply_to_user` |
| Ruff reports two old `E501` errors | Known baseline | Complete Session 3; do not suppress the rule |

---

## Build now

- Deterministic chat-route tests
- Clean lint/format/test baseline
- Correct local-model documentation
- Reproducible setup and run instructions
- Honest current-state README

## Not yet

- Conversation history persistence
- Streaming responses
- LangChain tools or autonomous loops
- Backend task routes
- Structured brain-dump planning
- Calendar or other connectors
- OAuth
- External writes
- Desktop Fairy implementation
- Final visual redesign

Keeping these boundaries prevents Stage 1 from becoming an untestable rewrite.

---

## Portfolio note

After this stage, you can truthfully demonstrate:

- A Python/FastAPI application serving an existing browser UI
- Local LLM inference through LangChain and Ollama
- A tested HTTP contract with deterministic model substitution
- Clear separation between UI, route, and AI service
- Reproducible dependency and quality tooling with `uv`, pytest, and Ruff
- Honest communication about prototype versus integrated behavior

Do not claim tool-using agent behavior yet.

---

## Reflection

Write short answers in your own notes:

1. What does FastAPI validate before `chat_with_neurofairy()` runs?
2. Why does the route test replace the live model?
3. What does the live-model smoke test prove that CI cannot?
4. Where would you look first if the browser fallback appears?
5. Which UI features are real backend behavior, and which still use `localStorage`?
6. How would you explain this vertical slice in an interview without exaggerating it?

---

Next: **[Stage 2 — Desktop Fairy companion](stage-2-desktop-fairy.md)**, using PySide6 for
the desktop interface and PyObjC only for macOS accessory-window behavior.
