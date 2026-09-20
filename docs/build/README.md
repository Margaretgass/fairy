# Building NeuroFairy — the follow-along curriculum

This folder is the canonical, project-based learning path for NeuroFairy.

The curriculum starts from the repository that exists today. It does not ask you to
rebuild working foundations, pretend planned features are complete, or replace the local
AI stack with a hosted provider.

Use the separate [NeuroFairy architecture map](ARCHITECTURE.md) to see the current runtime,
target V1, tech stack, integration boundaries, communication sequences, data ownership,
and the visible product at each stage.

> **Curriculum revision status:** the index, architecture map, Stage 1, and Stage 2 are
> current. The remaining stage documents still contain useful historical material and
> will be revised one at a time. Their status is shown below so you do not accidentally
> follow an obsolete sequence.

---

## Product goal

NeuroFairy is a calm, local-first executive-function companion. It helps someone move
from:

> “I am overwhelmed, distracted, stuck, or unsure what to do”

to:

> “I know one realistic next action, and I have started it.”

The core loop is:

1. Capture what is on the user's mind.
2. Recommend one small, visible next action.
3. Support starting and optional focus time.
4. Record the user's explicit outcome.
5. Respond without shame and help them return or re-plan.

NeuroFairy is evidence-informed executive-function support. It is not therapy, diagnosis,
medical care, medication advice, crisis care, or an autonomous life manager.

---

## Current verified starting point

The repository already contains more than the old stage order implied.

| Area | Current status |
|---|---|
| Python project managed by `uv` | Implemented and verified |
| FastAPI application | Implemented and verified |
| Existing browser UI served by FastAPI | Implemented and verified |
| Browser `POST /api/chat` integration | Implemented and live-smoke-tested |
| LangChain `ChatOllama` service | Implemented and live-smoke-tested |
| Local Ollama model `qwen2.5:3b` | Installed and verified |
| SQLite task operations | Add/list/complete/get are tested; delete exists but still needs Stage 3 coverage |
| FastMCP task tools | Implemented; registration verified |
| Automated chat-route tests | Not implemented yet |
| Desktop floating Fairy | Planned next |
| Structured brain dump and daily plan | Planned |
| Python focus/body-doubling service | Planned |
| LangChain tool execution | Planned |
| Calendar and other connectors | Planned; none connected |
| Backend-persisted charms and garden | Deferred |

The current quality baseline is also explicit:

- `pytest`: 8 passing tests
- `ruff format --check`: passing
- `ruff check`: two known line-length failures in `prompts.py` and `web_app.py`

Stage 1 closes those gaps before new product behavior is added.

---

## Current working architecture

This is the short current-state view. The [architecture map](ARCHITECTURE.md) contains the
full diagrams and clearly separates implemented, prototype, planned, and future-optional
parts.

```text
Browser UI
  uiux/ui/index.html + app.js
          │
          │ POST /api/chat  {"message": "..."}
          ▼
FastAPI route
  src/fairy/web_app.py
          │
          ▼
Local chat service
  src/fairy/neurofairy_chat.py
          │
          ▼
LangChain ChatOllama
          │
          ▼
Local Ollama service
  qwen2.5:3b
          │
          ▼
JSON reply returned to the browser
```

The task/MCP path is separate today:

```text
MCP client
    │
    ▼
FastMCP task server
  src/fairy/servers/tasks_server.py
    │
    ▼
Task operations + SQLite store
  src/fairy/servers/tasks.py
  src/fairy/servers/store.py
    │
    ▼
~/.fairy/fairy.db
```

The browser's tasks, quests, focus timer, inbox, and charms still use browser
`localStorage`. They are prototype behavior, not synchronized backend features.

---

## Revised stage order

| # | Stage | Status | Outcome |
|---|---|---|---|
| [1](stage-1-working-local-app.md) | Existing local app foundation | **Core complete; hardening remains** | Understand and protect the working browser → FastAPI → Ollama chat slice |
| [2](stage-2-desktop-fairy.md) | Desktop Fairy companion | **Next priority** | A draggable, hoverable, clickable macOS Fairy using PySide6 + PyObjC |
| 3 | Internal tasks and next actions | **Partly implemented** | One shared task source for app services, API, UI, and optional MCP clients |
| 4 | Brain dump and realistic daily planning | **Planned** | Reviewable categories, Anchor/Quest/Maintenance plan, one next action |
| 5 | Gentle focus and body doubling | **Planned** | Tested focus sessions shared by browser and desktop Fairy |
| 6 | Safe LangChain tools | **Planned** | Typed local tools, validation, limits, logs, and safe fallback behavior |
| 7 | Read-only calendar and connector privacy | **Later** | Consent-based calendar context with OAuth, revocation, and provenance |
| 8 | Charms, evaluation, and pilot readiness | **Deferred** | Non-punitive rewards, AI evaluations, accessibility, and portfolio proof |

### Historical documents awaiting revision

These documents remain useful references, but their numbering, paths, providers, or stage
assumptions are not yet current:

- `stage-1-tasks-mcp.md` — will become revised Stage 3
- `stage-2-focus-timer.md` — will become revised Stage 5
- `stage-4-connectors.md` — will become revised Stage 7
- `stage-5-agent.md` — will become revised Stage 6
- `stage-7-charms.md` — will become revised Stage 8

Do not follow a historical document as the next stage until its revision status changes.

---

## How each stage works

Every stage produces a usable, testable increment. Each session stops after one coherent
change so errors stay understandable.

Every revised stage contains:

1. Purpose and product value
2. Current status and starting point
3. Prerequisites
4. Learning goals
5. Concepts in plain English
6. Exact files involved
7. Small ordered sessions
8. Acceptance criteria
9. Automated and manual verification
10. Common errors and debugging guidance
11. Commit checkpoints
12. Build-now and not-yet boundaries
13. Portfolio evidence
14. A short learner reflection
15. A full-file recovery checkpoint after every session
16. A complete final-code snapshot at the end of the stage

Every implementation session follows the same shape:

```text
Practical goal
Concept
Why this file or layer
Exact path
Add / replace / delete
Smallest complete change
Command to run
Expected result
Likely error and diagnosis
Stop and report the result
Commit only after verification passes
```

The course intentionally avoids giant code dumps. Type or paste one small complete change,
run it, understand the result, and stop before the next change.

### Full-file recovery checkpoints

Incremental instructions teach what changed, but they are difficult to recover from after
one missed edit. Every revised session or step therefore ends with a link to a copy-ready
checkpoint containing:

- the complete contents of every source, test, or configuration file created or changed
  in that session;
- representative terminal output for the documented commands;
- the exact visible result to expect;
- a note identifying output that can legitimately vary.

Every revised stage also ends with one complete final snapshot covering all files produced
by that stage. Generated files such as `uv.lock`, caches, databases, and screenshots are
verified but not pasted as hand-maintained source. The checkpoint is a recovery tool, not a
replacement for working through the smaller changes first.

---

## Status language

Use these labels consistently in documentation and portfolio material:

| Label | Meaning |
|---|---|
| **Implemented and verified** | Code exists and the documented verification passed |
| **Implemented; needs more testing** | Code exists but important automated or manual coverage is missing |
| **In progress** | Some required behavior exists and some does not |
| **Planned next** | The next approved stage or increment |
| **Future optional** | Useful idea, not required for the current product path |

Never describe a mockup, design reference, installed dependency, or old plan as a working
feature.

---

## The architecture boundaries

These terms describe different jobs. Keeping them separate is a central learning goal.

### Domain model

A typed representation of product information and rules, such as `Task`, `DailyPlan`, or
`FocusSession`. Domain logic should be deterministic whenever possible.

### Application service

Normal Python code that coordinates a product operation. A service can call domain logic,
storage, or an AI boundary, but it should not depend on a specific user interface.

### Schema

A validated input or output shape. Pydantic schemas protect API, AI, and tool boundaries
from missing or malformed data.

### FastAPI route

An HTTP entry point. A route validates the request, calls an application service, and
returns a response. It should not contain all of the product logic itself.

### LangChain tool

A typed function description a language model may select. The model proposes a call; normal
application code validates permissions and decides whether execution is allowed.

### MCP server/tool

A protocol-based way to expose typed functions to an external MCP client. MCP remains useful
for interoperability and learning, but not every product operation needs to pass through
MCP.

### Connector

A narrow adapter to an external system. It handles provider-specific authentication and
data formats, then returns normalized application data.

### OAuth

A delegated authorization flow. The user signs in with the provider and grants limited,
revocable access without giving NeuroFairy their password.

### Confirmation gate

Backend enforcement requiring the user to review and approve one exact external action
before it can run. A model saying “the user probably wants this” is never confirmation.

---

## Non-negotiable technical direction

The required application stack is:

```text
Python + FastAPI + existing frontend UI
        + LangChain + ChatOllama
        + local Ollama + qwen2.5:3b
```

The planned desktop stack is:

```text
PySide6 + macOS-specific PyObjC accessory-window behavior
        + existing FastAPI/application services
```

The earlier Swift/SwiftUI/Xcode prototype is historical only. Do not copy it into this
repository, use it as a Stage 2 starting point, or maintain a second native implementation.
`code/fairy` remains the source of truth for this curriculum.

Additional rules:

- Keep the local Ollama path primary and functional.
- Do not introduce a hidden hosted-model dependency.
- Use Pydantic at API, AI, and tool boundaries.
- Keep deterministic rules outside prompts.
- Prefer small services over autonomous agent behavior.
- Verify local-model tool calling before depending on it.
- If tool calling is unreliable, use deliberate UI actions and deterministic Python.
- All third-party integrations begin read-only.
- No external write may bypass exact-action review and explicit confirmation.
- Do not create `design.md`; visual direction is owned separately.

---

## Shared development workflow

Start a learning session:

```bash
cd ~/code/fairy
git status --short --branch
uv sync
```

Run the deterministic quality checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Run the local model smoke test only when Ollama is running:

```bash
ollama list
uv run python -m fairy.test_local_model
```

Run the browser app:

```bash
uv run uvicorn fairy.web_app:app --reload
```

Then open `http://127.0.0.1:8000`.

Before committing, inspect the change:

```bash
git status --short
git diff --check
git diff
```

Only commit after the stage's relevant automated and manual checks pass. Suggested commit
messages appear at the end of each session; they are checkpoints, not commands to run
before verification.

---

## Debugging habits

- Read Python tracebacks from the bottom upward.
- Fix the first reported syntax or lint error before chasing later fallout.
- Identify the responsible layer: browser, route, service, model provider, storage, or
  external connector.
- Reproduce the smallest failure you can.
- Change one thing, then rerun the narrowest relevant test.
- Do not hide a failing check or describe it as unrelated without evidence.

Common signals:

| Symptom | First place to inspect |
|---|---|
| Browser shows connection fallback | Browser Network tab, then FastAPI terminal |
| HTTP 422 | Request schema or JSON body |
| HTTP 500/fallback reply | Route/service exception and Ollama availability |
| Ollama connection refused | `ollama list` and the local Ollama service |
| SQLite state differs from UI | Browser `localStorage` versus `~/.fairy/fairy.db` |
| MCP tool missing | FastMCP registration and server startup |

---

Start with **[Stage 1 — Working local app foundation](stage-1-working-local-app.md)**.
