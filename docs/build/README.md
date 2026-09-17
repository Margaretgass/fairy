# Building Fairy — a follow-along course

Everything you need to build this project, start to finish. No prior knowledge assumed
beyond having written a little Python.

---

## How this course works

Seven **stages**. Each stage is split into **sessions** of roughly 2–3 hours — about one
sitting at 10 hours a week.

Every session has the same shape:

```
▶ Start this session      cd, pull, sync
  Goal                    one sentence
  The code                written out in full, with explanations
✔ Check yourself          a command, and what you should see
⚠ If it breaks            the errors you'll actually hit, and why
■ Finish this session     verify, commit, push
```

**You never have to guess a command.** Every one you need is in a code block you can run.

### The two rules

**1. Type the code, don't paste it.** You'll make typos, the typos produce errors, and
reading those errors is most of what learning to program actually is. Pasting skips the
part that teaches you.

**2. Never move on with a red test.** A broken session compounds into a broken stage. If
something fails, fix it or ask before continuing.

---

## The stages

| # | Stage | Sessions | You end up with |
|---|---|---|---|
| [1](stage-1-tasks-mcp.md) | Tasks MCP server | 6 | Claude Desktop writing to your database |
| [2](stage-2-focus-timer.md) | Focus timer | 4 | A tested timer engine + MCP tools |
| [3](stage-3-desktop-fairy.md) | The desktop fairy | 4 | A fairy floating on your screen |
| [4](stage-4-connectors.md) | Real integrations | 7 | D2L, files, Notes, Notion, Gmail, iMessage |
| [5](stage-5-agent.md) | Your own agent | 5 | A local LLM driving your tools |
| [6](stage-6-web-ui.md) | Web UI | 5 | Your designs, running, deployed |
| [7](stage-7-charms.md) | Charms + garden | 3 | The reward system |

**~34 sessions, ~17 weeks at 10 h/week.** Every stage ends with something that works, so
stopping early still leaves you with a real project.

---

## Git — the whole workflow you need

You work directly on `main`. This is a solo project; branches would add ceremony without
benefit.

**Starting any session:**

```bash
cd ~/code/fairy && git pull && uv sync
```

`git pull` gets anything you pushed from elsewhere. `uv sync` makes sure your installed
packages match `pyproject.toml` — needed after any session that added a dependency.

**Finishing any session:**

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: your message here" && git push
```

**Check what you're about to commit**, if you're unsure:

```bash
cd ~/code/fairy && git status && git diff --stat
```

**If a commit is rejected by gitleaks** (Stage 4 onwards), that's the secret guard working.
Remove the key, put it in `.env`, and commit again.

**If `git push` is rejected**, someone (you, elsewhere) pushed first:

```bash
cd ~/code/fairy && git pull --rebase && git push
```

### Commit message style

Small commits with a type prefix. This history is something people will read.

```
chore:  tooling, config, dependencies
feat:   a new capability
fix:    a bug fix
test:   tests only
docs:   documentation only
```

---

## The one rule of the architecture

> **`src/fairy/domain/` is pure.**
> No database. No network. No clock. No LLM.
> Time is always passed in as a parameter, never read inside.

Everything messy — SQLite, HTTP, Ollama — lives outside `domain/` and calls into it.

This is not style. It's why the timer has thirteen tests that run in 0.02 seconds, why the
charm engine can be verified instantly, and why your desktop fairy in Stage 3 can run the
*same* timer code as your MCP server with no changes.

When you're unsure where code belongs, ask: **does this function need the outside world to
run?** If no, it goes in `domain/`.

---

## Architecture

```
       Claude Desktop  (your agent, stages 1-4)
              │ stdio
       ┌──────▼─────────────────────────────────┐
       │  src/fairy/servers/    MCP servers     │
       │  tasks · timer · calendar · notes …    │
       └──────┬─────────────────────────────────┘
              │
       ┌──────▼──────────┐   ┌──────────────────┐
       │  store.py       │◄──┤ fairy_desktop/   │  PySide6 (stage 3)
       │  ~/.fairy/      │   └──────────────────┘
       │  fairy.db       │   ┌──────────────────┐
       │  SQLite + WAL   │◄──┤ src/fairy/web/   │  FastAPI (stage 6)
       └──────▲──────────┘   └──────────────────┘
              │
       ┌──────┴────────────────┐
       │  src/fairy/domain/    │  PURE
       │  bloom.py charms.py   │
       └───────────────────────┘
```

**Storage is the integration point, not an HTTP API.** Every component reads and writes the
same SQLite file. That one decision removes authentication, CORS, port management, process
supervision, and deployment from stages 1–5 entirely.

---

## Reading errors

A skill, and a learnable one.

**Read from the bottom up.** The last line says *what* went wrong; the lines above say
*where*. Python tracebacks are honest — the hard part is believing them.

| You see | It usually means |
|---|---|
| `ModuleNotFoundError` | File in the wrong folder, or you need `uv sync` |
| `ImportError: cannot import name X` | Typo in the name, or X doesn't exist in that version |
| `AttributeError: 'NoneType' has no attribute` | Something returned `None` and you didn't check |
| `FrozenInstanceError` | You wrote `state.x = y` on a frozen dataclass — use `replace()` |
| `database is locked` | Missing `PRAGMA journal_mode=WAL` |
| A **yellow** squiggle in VS Code | A lint warning. Often just an unused import. Not broken |
| A **red** squiggle saying "could not be resolved" | Wrong interpreter, or package not installed. Actually broken |

**Never run `ruff check --fix` on a half-written file.** It will "helpfully" delete imports
you haven't used yet.

---

## Your environment

Already set up, for reference:

| Thing | Value |
|---|---|
| Project | `~/code/fairy` |
| Python | 3.14.2 |
| Package manager | `uv` |
| Database | `~/.fairy/fairy.db` |
| Editor | VS Code, with the Python and Ruff extensions |
| Interpreter | `./.venv/bin/python` — check the status bar |

---

Start here: **[Stage 1 — Tasks MCP server](stage-1-tasks-mcp.md)**
