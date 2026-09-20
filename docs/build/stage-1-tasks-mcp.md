# Stage 1 — Tasks MCP server

> **Historical reference — do not follow as Stage 1.** The implemented task, SQLite, and
> FastMCP material will be reconciled into revised Stage 3. Claude Desktop setup, this stage
> number, and any instruction that rebuilds existing files are obsolete. Return to the
> [current curriculum index](README.md) before making changes.

> **By the end of this stage** you will say *"add a task to email my professor"* to Claude
> Desktop, and it will land in a database you built.

**Sessions:** 6 · **Time:** ~2 weeks at 10 h/week

### What you'll learn

| Concept | Where |
|---|---|
| Type hints, and what Python does *not* do with them | Session 2 |
| Pydantic — validating data at the boundary | Session 2 |
| SQL, placeholders, and SQL injection | Session 2–3 |
| Context managers (`with`) and why they exist | Session 2 |
| pytest fixtures, and test isolation | Session 3 |
| Test-driven development — red, then green | Session 3 |
| Keyword-only arguments | Session 3 |
| MCP — how an AI discovers and calls your code | Session 4 |

---

## Session 1 — Project setup ✅ DONE

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

Your repo already has `pyproject.toml`, `.gitignore`, `.env.example`, CI, VS Code
settings, and the `src/fairy/` skeleton.

```bash
uv sync && uv run ruff check . && uv run pytest
```

pytest saying "no tests ran" is correct — you haven't written any yet.

---

## Session 2 — Models and storage

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** define what a task *is*, and where it lives.

**Two files:** `models.py` (shapes) and `store.py` (storage). Keeping those separate is the
first architectural decision you make, and everything later depends on it.

### Part A — `src/fairy/models.py`

**What it does:** defines the shape of a task. No database, no network — just definitions.

**Why it matters:**
- Every other part of Fairy agrees on these shapes — MCP server, web UI, desktop fairy
- Pydantic rejects bad data here, before it reaches your database

Start with the imports:

```python
"""Typed objects shared by every part of Fairy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field
```

**Line by line:**

| Line | What it does |
|---|---|
| `"""Typed..."""` | A **module docstring** — the first statement in a file. Unlike a `#` comment it's stored on the object and readable via `help(fairy.models)`. In Session 4 docstrings become load-bearing, so build the habit now. |
| *(blank line)* | Ruff's formatter requires one after the docstring. Format-on-save adds it for you. |
| `from __future__ import annotations` | Makes type hints lazy — stored as text, evaluated only if something asks. On **3.14 this is mostly redundant** (Python 3.14 made annotations lazy by default), but it's harmless, keeps the file working on 3.13, and you'll see it everywhere in real code. |
| `from datetime import datetime` | The class is `datetime`, inside a module also called `datetime`. Confusing, but standard. |
| `from enum import StrEnum` | A fixed set of named string values. More below. |
| *(blank line)* then `pydantic` | Import order is **stdlib, blank line, third-party**. Ruff's `I` rules enforce it and fix it on save. |

Now the first type:

```python
class Category(StrEnum):
    """How a task fits into the day. From the original design docs."""

    ANCHOR = "Anchor"
    QUEST = "Quest"
    MAINTENANCE = "Maintenance"
    OPTIONAL = "Optional"
```

**What an enum is:** a fixed set of allowed values with names. `Category.ANCHOR` is a real
object; `"Anchor"` is just a string. The difference matters:

```python
task.category = "Anchr"         # a plain string — typo, silently stored forever
task.category = Category.ANCHR  # AttributeError, immediately, at the typo
```

**Why `StrEnum` and not `(str, Enum)`:** `StrEnum` (Python 3.11+) behaves like a string
where you need one — SQLite stores it directly — while still being a real enum. You'll see
the older `class Category(str, Enum)` spelling in many tutorials. Avoid it:

```python
str(Old.ANCHOR)   # 'Category.ANCHOR'   <- ends up in your database
str(New.ANCHOR)   # 'Anchor'            <- what you meant
```

Ruff's `UP042` rule flags the old form for you.

Then the model itself:

```python
class Task(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=200)
    category: Category = Category.OPTIONAL
    done: bool = False
    created_at: datetime
    completed_at: datetime | None = None
```

**The single most important idea in this session:**

> Python does **not** enforce type hints at runtime. `id: int` is documentation — plain
> Python will happily let you put a string there. **Pydantic is what makes them real.**

Because `Task` inherits from `BaseModel`, Pydantic checks every field when you construct
one, converts where sensible (an ISO string becomes a `datetime`), and raises where it
can't. That's why nonsense can't get past this line into your database.

`Field(min_length=1, max_length=200)` adds rules beyond the type. `datetime | None = None`
means "a datetime or nothing, defaulting to nothing" — `|` is Python's *union* syntax.

### The complete file

When all three pieces are in place, `src/fairy/models.py` reads:

```python
"""Typed objects shared by every part of Fairy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    """How a task fits into the day. From the original design docs."""

    ANCHOR = "Anchor"
    QUEST = "Quest"
    MAINTENANCE = "Maintenance"
    OPTIONAL = "Optional"


class Task(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=200)
    category: Category = Category.OPTIONAL
    done: bool = False
    created_at: datetime
    completed_at: datetime | None = None
```

Twenty-six lines. That's the whole thing.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "from fairy.models import Category; print(Category.ANCHOR, '|', Category.ANCHOR.value)"
```

Expect `Anchor | Anchor`. Both identical — that's `StrEnum` working.

Now deliberately break it:

```bash
cd ~/code/fairy && uv run python -c "from fairy.models import Task; Task(id=1, title='', created_at='2026-09-17T09:00')"
```

This **must fail** with a Pydantic error mentioning `title` and `min_length`. Read the
error — it names the field, the rule, and the value it got. Getting comfortable reading
these now saves hours later.

### Part B — `src/fairy/store.py`

**What it does:** creates `~/.fairy/fairy.db` and hands other code a safe connection to it.

**Why it matters** — three separate programs share this one file:

```
Claude Desktop -> MCP server  --+
                                |
The floating fairy  -----------+--->  store.py  --->  ~/.fairy/fairy.db
                                |
The web UI  -------------------+
```

- They never talk to each other
- They stay in sync because all three call `store.session()`
- This is Fairy's whole integration strategy — a file path instead of a server

```python
"""SQLite storage. One file, shared by every part of Fairy."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path.home() / ".fairy" / "fairy.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT 'Optional',
    done         INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL,
    completed_at TEXT
);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open the database, creating the file and schema if they don't exist."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # rows can be indexed by column name
    conn.execute("PRAGMA journal_mode=WAL")  # two processes can read at once
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, always close."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
```

**Understanding the SQL.** `CREATE TABLE IF NOT EXISTS` makes running this twice safe — so
`connect()` can create the schema every time without tracking whether it already exists.

`INTEGER PRIMARY KEY AUTOINCREMENT` makes SQLite assign ids for you: 1, 2, 3.
SQLite has **no boolean type**, so `done` is an `INTEGER` holding 0 or 1 — which is why
`tasks.py` later writes `bool(row["done"])` to convert it back.

**Understanding `Path`.** `Path.home() / ".fairy" / "fairy.db"` — the `/` operator joins
path segments. Reads like a path, works on any OS, much better than gluing strings.

**Understanding the three setup lines:**

| Line | Why |
|---|---|
| `row_factory = sqlite3.Row` | Without it rows are tuples and you write `row[1]`. With it, `row["title"]`. Column order stops mattering. |
| `PRAGMA journal_mode=WAL` | Write-Ahead Logging. Lets one process read while another writes. **Stage 3's desktop fairy depends on this** — without it you get `database is locked`. |
| `executescript(SCHEMA)` | Runs several SQL statements at once. `execute()` only runs one. |

**New concept: `@contextmanager`**

```python
@contextmanager
def session(db_path=None):
    conn = connect(db_path)
    try:
        yield conn          # hand the connection to the `with` block
        conn.commit()       # runs if the block finished cleanly
    finally:
        conn.close()        # runs ALWAYS, even if the block raised
```

This turns a function into something usable with `with`:

```python
with store.session() as conn:
    tasks.add_task(conn, "hello")
# committed and closed automatically, here
```

- Before `yield` — setup
- `yield conn` — hands the connection to the `with` block
- After `yield` — runs on success (`commit`)
- `finally` — runs always, even on a crash (`close`)

Without `finally`, a crash leaks a database connection.

**Why `db_path=None`:** tests pass a throwaway path. Without it, running your tests would
wipe your real tasks.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "from fairy import store; c = store.connect(); print(c.execute('SELECT name FROM sqlite_master').fetchall())"
```

You should see your `tasks` table. The file now exists at `~/.fairy/fairy.db`.

### ⚠ If it breaks

| Error | Meaning |
|---|---|
| `ModuleNotFoundError: No module named 'fairy'` | File is in the wrong folder, or run `uv sync` again |
| `ImportError: cannot import name 'StrEnum'` | Python older than 3.11 — check your interpreter |
| Squiggles on unused imports | Normal until you use them. Don't run `ruff --fix` on a half-written file |
| `SyntaxError: expected ':'` on a `def` line | A line got split where there's no open bracket. Put the whole signature on one line |
| Many squiggles at once, all below one point | **One** syntax error. Fix the topmost; the rest are fallout |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add Task model and SQLite store" && git push
```


---

## Session 3 — Task operations, test-first

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** learn test-driven development on the easiest possible example.

**The method:** write a test that fails. Watch it fail. Write just enough code to pass. The
failure matters — a test you've never seen fail might not be testing anything.

### Part A — the tests, written first

`tests/test_tasks.py`:

```python
from datetime import UTC, datetime

import pytest

from fairy import store, tasks
from fairy.models import Category

NOW = datetime(2026, 9, 17, 9, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    """A fresh empty database for every single test."""
    with store.session(tmp_path / "test.db") as c:
        yield c


def test_add_task_assigns_an_id(conn):
    task = tasks.add_task(conn, "email professor", now=NOW)
    assert task.id == 1
    assert task.title == "email professor"
    assert task.done is False


def test_add_task_strips_whitespace(conn):
    task = tasks.add_task(conn, "  spaced out  ", now=NOW)
    assert task.title == "spaced out"


def test_add_task_defaults_to_optional(conn):
    task = tasks.add_task(conn, "something", now=NOW)
    assert task.category is Category.OPTIONAL


def test_add_task_accepts_a_category(conn):
    task = tasks.add_task(conn, "class at 2", Category.ANCHOR, now=NOW)
    assert task.category is Category.ANCHOR


def test_list_tasks_hides_completed_by_default(conn):
    tasks.add_task(conn, "keep me", now=NOW)
    finish = tasks.add_task(conn, "finish me", now=NOW)
    tasks.complete_task(conn, finish.id, now=NOW)

    assert [t.title for t in tasks.list_tasks(conn)] == ["keep me"]
    assert len(tasks.list_tasks(conn, include_done=True)) == 2


def test_complete_task_sets_timestamp(conn):
    task = tasks.add_task(conn, "do the thing", now=NOW)
    done = tasks.complete_task(conn, task.id, now=NOW)
    assert done.done is True
    assert done.completed_at == NOW


def test_get_unknown_task_raises(conn):
    with pytest.raises(KeyError):
        tasks.get_task(conn, 999)


def test_complete_unknown_task_raises(conn):
    with pytest.raises(KeyError):
        tasks.complete_task(conn, 999, now=NOW)
```

**Understanding fixtures.** A `@pytest.fixture` is setup shared between tests. Any test that
names `conn` as a parameter gets a freshly built one — pytest matches by **name**, which
feels like magic the first time.

`tmp_path` is a fixture pytest provides: a brand-new temporary folder per test, deleted
afterwards. Every test starts from an empty database, so **tests can't affect each other**.
Test isolation is the whole reason `connect()` took that `db_path` argument.

**Understanding `assert`.** Plain Python. If the expression is false the test fails, and
pytest prints both sides. No assertion library needed.

`assert task.done is False` uses `is`, not `==`, because we want the actual boolean
`False` — not `0` or `""`, which would pass an `==` check.

**Understanding `pytest.raises`.** Sometimes the behaviour *is* the error. These two tests
assert that asking for a nonexistent task raises `KeyError`. If nothing is raised the test
fails — which is what you want, because silently returning `None` is how bugs hide.

**Now watch them fail:**

```bash
cd ~/code/fairy && uv run pytest
```

You'll get:

```
ImportError: cannot import name 'tasks' from 'fairy'
```

**That's the correct first failure** — `tasks.py` doesn't exist yet, and it proves the test
is really running your code rather than passing by accident.

(You may see `ModuleNotFoundError` instead, depending on import style. `from fairy import
tasks` gives `ImportError`; `import fairy.tasks` gives `ModuleNotFoundError`. Same meaning:
the file isn't there.)

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `ModuleNotFoundError: fairy.tasks` before you wrote it | Correct — that's the red step |
| `TypeError: add_task() takes 3 positional arguments` | You passed `now` positionally. The `*` makes it keyword-only |
| `sqlite3.ProgrammingError: parameters supplied` | Missing the trailing comma in `(task_id,)` — it must be a tuple |
| `TypeError: now() takes at most 1 argument` | You wrote `datetime.now(2026, 9, ...)`. `datetime(...)` is the constructor; `.now()` is a method returning the current time. Drop the `.now` |
| `F821 Undefined name 'get_task'` | You skipped `get_task` — `add_task` and `complete_task` both call it |
| `sqlite3.OperationalError` on INSERT | Column count doesn't match placeholder count. Ruff can't see inside SQL strings |
| `assert task.id == 1` fails with `2` | Your fixture isn't giving each test a fresh database |
| `completed_at` compares unequal | You stored a naive datetime; keep everything timezone-aware with `UTC` |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "test: add failing tests for task operations" && git push
```


### Part B — make them pass

**What it does:** the four things you can do with a task — add, get, list, complete.

- `models.py` = what a task is · `store.py` = where it lives · `tasks.py` = what you do with it
- All SQL lives here. The MCP server and web UI just call these functions

`src/fairy/tasks.py`:

```python
"""Task operations. Time is always passed in, never read from the clock."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from fairy.models import Category, Task


def _row_to_task(row: sqlite3.Row) -> Task:
    """Turn a database row into a validated Task."""
    return Task(
        id=row["id"],
        title=row["title"],
        category=Category(row["category"]),
        done=bool(row["done"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        completed_at=(
            datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        ),
    )


def add_task(
    conn: sqlite3.Connection,
    title: str,
    category: Category = Category.OPTIONAL,
    *,
    now: datetime | None = None,
) -> Task:
    """Create a task and return it."""
    now = now or datetime.now(UTC)
    cur = conn.execute(
        "INSERT INTO tasks (title, category, created_at) VALUES (?, ?, ?)",
        (title.strip(), category.value, now.isoformat()),
    )
    return get_task(conn, cur.lastrowid)


def get_task(conn: sqlite3.Connection, task_id: int) -> Task:
    """Fetch one task. Raises KeyError if it doesn't exist."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise KeyError(f"no task with id {task_id}")
    return _row_to_task(row)


def list_tasks(conn: sqlite3.Connection, *, include_done: bool = False) -> list[Task]:
    """List tasks, oldest first. Hides completed tasks unless asked."""
    sql = "SELECT * FROM tasks"
    if not include_done:
        sql += " WHERE done = 0"
    sql += " ORDER BY id"
    return [_row_to_task(row) for row in conn.execute(sql)]


def complete_task(
    conn: sqlite3.Connection, task_id: int, *, now: datetime | None = None
) -> Task:
    """Mark a task done. Raises KeyError if it doesn't exist."""
    now = now or datetime.now(UTC)
    get_task(conn, task_id)  # raises KeyError before we change anything
    conn.execute(
        "UPDATE tasks SET done = 1, completed_at = ? WHERE id = ?",
        (now.isoformat(), task_id),
    )
    return get_task(conn, task_id)
```

**The leading underscore.** `_row_to_task` starts with `_` by convention: "internal, not
part of this module's public interface." Python doesn't enforce it. It's a message to the
next reader, who is usually you.

**SQL placeholders — genuinely important.**

```python
conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))   # correct
conn.execute(f"SELECT * FROM tasks WHERE id = {task_id}")      # never do this
```

The `?` is a placeholder; SQLite substitutes safely. The f-string version is **SQL
injection** — if `task_id` came from user input it could contain SQL that runs as SQL. In a
personal app it's "only" a crash risk; the habit is what matters.

Note `(task_id,)` — the trailing comma makes it a one-item **tuple**. Without it `(x)` is
just `x` in parentheses, and SQLite will complain.

**Keyword-only arguments.** The bare `*` in the signature:

```python
def add_task(conn, title, category=Category.OPTIONAL, *, now=None):
```

Everything after `*` **must** be passed by name. `add_task(conn, "x", now=NOW)` works;
`add_task(conn, "x", cat, NOW)` is an error. It prevents argument-order bugs and makes call
sites self-documenting.

**Why `now` is a parameter:** a function that calls `datetime.now()` inside can't be tested
— the answer changes every run. Passing time in lets tests assert exact values. Stage 2's
whole timer engine is built on this.

**Understanding the list comprehension:**

```python
[_row_to_task(row) for row in conn.execute(sql)]
```

Reads as: for each row the query returns, convert it, collect into a list. The longer form
would be a `for` loop with `result.append(...)`.

**Understanding `or`.** `now = now or datetime.now(UTC)` means "keep `now` if given,
otherwise use the real clock." Python's `or` returns the first truthy value.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run pytest
```

Eight passing. If one fails, read the failure from the bottom up — pytest shows you the
exact values it compared.

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: implement task operations" && git push
```


---

## Session 4 — The MCP server

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** make your code callable by an AI.

**What it does:** exposes your three task functions to Claude Desktop.

**New concept: MCP.** A standard way for a program to advertise *"here are my tools, here's
what each does, here's what arguments it takes."*

- A client (Claude Desktop, or your own agent in Stage 5) asks for that list
- It shows the list to the model, and runs whichever tool the model picks
- You're writing the **server** side

**Transport is stdio** — the client starts your program and talks over stdin/stdout.
No ports, no HTTP, no auth. That's why this stage has no security section.

This file holds **no logic**. Each tool opens a session, calls `tasks.py`, returns JSON.
The real behaviour is tested in `tasks.py`, so there's almost nothing here to break.

`src/fairy/servers/tasks_server.py`:

```python
"""MCP server exposing Fairy's task list to any MCP client."""

from __future__ import annotations

from fastmcp import FastMCP

from fairy import store, tasks
from fairy.models import Category

mcp = FastMCP("fairy-tasks")


@mcp.tool
def add_task(title: str, category: str = "Optional") -> dict:
    """Add a task to the user's Fairy task list.

    Args:
        title: What needs doing, in the user's own words.
        category: One of Anchor, Quest, Maintenance, Optional.
                  Anchor is a fixed commitment like a class.
                  Quest is part of a bigger project.
                  Maintenance is routine upkeep.
                  Optional is everything else.
    """
    with store.session() as conn:
        task = tasks.add_task(conn, title, Category(category))
        return task.model_dump(mode="json")


@mcp.tool
def list_tasks(include_done: bool = False) -> list[dict]:
    """List the user's tasks. By default only unfinished ones.

    Args:
        include_done: Set true to also return completed tasks.
    """
    with store.session() as conn:
        found = tasks.list_tasks(conn, include_done=include_done)
        return [t.model_dump(mode="json") for t in found]


@mcp.tool
def complete_task(task_id: int) -> dict:
    """Mark a task as finished.

    Args:
        task_id: The id returned by add_task or list_tasks.
    """
    with store.session() as conn:
        return tasks.complete_task(conn, task_id).model_dump(mode="json")


def main() -> None:
    """Entry point for the `fairy-tasks` command."""
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
```

**New concept: decorators.** `@mcp.tool` takes your function and registers it. FastMCP then:

- reads your **type hints** → builds a JSON schema of the arguments
- reads your **docstring** → describes what the tool does

You write an ordinary function; the protocol paperwork is generated.

> **Docstrings are the API.** The model has never seen your code. All it gets is the tool
> name, the argument types, and the text of your docstring. A vague docstring produces
> wrong tool calls — so a bad docstring is a *bug*, not a style problem.

**Understanding `model_dump(mode="json")`.** MCP speaks JSON, and JSON has no `datetime` and
no enums. This converts your `Task` into plain JSON-safe types: `datetime` becomes an ISO
string, `Category.ANCHOR` becomes `"Anchor"`.

**Understanding `if __name__ == "__main__"`.** True only when the file is *run* directly,
false when it's *imported*. It lets one file be both a program and an importable module.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run fairy-tasks
```

It prints a banner then sits silently. **That's correct** — it's waiting for a client on
stdin. `Ctrl-C` to quit.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `fairy-tasks: command not found` | Run `uv sync` after adding it to `[project.scripts]` |
| `AttributeError: 'FastMCP' object has no attribute 'tool'` | Very old fastmcp. `uv add "fastmcp>=4.0.5"` |
| `TypeError: Object of type datetime is not JSON serializable` | You returned the `Task` directly — use `.model_dump(mode="json")` |
| `ValueError: 'Anchor ' is not a valid Category` | Trailing whitespace from the model. Strip before `Category(...)` |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add fairy-tasks MCP server" && git push
```


---

## Session 5 — Connect Claude Desktop

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** the payoff.

```bash
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Your file already has content. **Merge — don't replace.** Add `mcpServers` as another
top-level key:

```json
{
  "coworkUserFilesPath": "...leave whatever is already here...",
  "preferences": { "...leave this too..." },
  "mcpServers": {
    "fairy": {
      "command": "uv",
      "args": ["--directory", "/Users/maggiegass/code/fairy", "run", "fairy-tasks"]
    }
  }
}
```

**What this says:** *to start the "fairy" server, run `uv --directory <project> run
fairy-tasks`*. The `--directory` is required — Claude Desktop has no idea where your project
lives, so `uv` must be told which project to run from.

Quit Claude Desktop fully (`Cmd+Q`, not just the window) and reopen. Then:

> "add a task to email my professor about the extension"

> "what's on my task list?"

Prove it's real rather than imagined:

```bash
sqlite3 ~/.fairy/fairy.db "SELECT id, title, category, done FROM tasks;"
```

### ⚠ If it breaks

| Symptom | Cause and fix |
|---|---|
| No `fairy` tools listed | JSON syntax error — trailing comma or missing brace. Paste the file into a JSON validator |
| "server failed to start" | Run `uv --directory /Users/maggiegass/code/fairy run fairy-tasks` by hand; the traceback tells you why |
| Tools appear but every call errors | Usually an import error. The same manual run shows it |
| Changes don't take effect | You must fully `Cmd+Q`, not just close the window |

### ✔ Check yourself

In Claude Desktop, look for the tools icon — `fairy` should be listed with three tools.
Then ask it to add a task, and confirm it reached your database:

```bash
sqlite3 ~/.fairy/fairy.db "SELECT id, title, category, done FROM tasks;"
```

If the row is there, **the whole stage works** — an AI called code you wrote and it changed
real state on your machine.

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "docs: add Claude Desktop setup instructions" && git push
```


---

## Session 6 — README and green CI

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

```bash
gh repo create fairy --public --source=. --remote=origin --push
```

Your README, in this order:

1. **One sentence** on what this is
2. **A screenshot** of Claude Desktop calling your tool — your proof
3. The **architecture diagram** from `docs/build/README.md`
4. **Setup** — `uv sync`, then the config block
5. A **CI badge**: `![CI](https://github.com/<you>/fairy/actions/workflows/ci.yml/badge.svg)`

Check the Actions tab is green.

### ✔ Check yourself

```bash
cd ~/code/fairy && gh repo view --web
```

Check three things on GitHub: the **Actions tab is green**, the README renders with your
screenshot, and `.env` is **not** in the file list.

```bash
cd ~/code/fairy && git ls-files | grep -c "\.env$" || echo "0 env files tracked - good"
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| CI fails on `ruff format --check` | Run `uv run ruff format .` locally and commit the result |
| CI fails on `uv sync` | `uv.lock` isn't committed. It must be |
| Badge shows "no status" | The workflow hasn't run yet, or the filename in the badge URL is wrong |
| `.env` appears on GitHub | Stop. `git rm --cached .env`, commit, and **rotate every key in it** |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "docs: write README with architecture and setup" && git push
```


---

## ✅ Stage 1 complete

**You built:** a public repo with green CI, 8 passing tests, an MCP server driven by Claude
Desktop, and tasks in a database you designed.

**You learned:**

- Type hints are documentation; **Pydantic** is what enforces them
- **Context managers** guarantee cleanup, even when code fails
- **SQL placeholders** prevent injection — always `?`, never f-strings
- **pytest fixtures** with `tmp_path` keep tests isolated
- **TDD**: watch the test fail first, or you don't know it works
- **Injecting time** as a parameter is what makes logic testable
- **MCP** turns typed functions plus docstrings into tools an AI can call

### Stretch exercise (optional)

Add a `delete_task(conn, task_id)` function. Write the test first — including the case
where the id doesn't exist. Then expose it as an MCP tool and ask Claude to delete
something.

Think about this while you do it: should deleting a task that doesn't exist raise, or
quietly do nothing? There's a defensible answer either way. Pick one, write the test that
pins it down, and say why in the docstring. That decision *is* API design.

Next: [Stage 2 — Focus timer](stage-2-focus-timer.md)
