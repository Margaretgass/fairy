# Stage 2 — Focus timer

> **By the end of this stage** you will have a focus timer with thirteen tests that run in
> hundredths of a second, and you'll be able to say *"start a 25 minute focus session"* to
> Claude Desktop.

**Sessions:** 4 · **Time:** ~2 weeks

### What you'll learn

| Concept | Where |
|---|---|
| What "pure function" means, and why it matters | Session 1 |
| Dataclasses, `frozen=True`, and immutability | Session 2 |
| `replace()` — changing data without mutating it | Session 2 |
| State machines | Session 2 |
| Porting a specification faithfully | Sessions 1–2 |
| Separating pure logic from storage | Session 3 |

### Why this stage is your best one

The original `bloom-engine.js` was written in a pure, time-injected style **and ships with
a test suite**. You are translating a known-correct specification, not inventing behaviour.
That means when a test fails, the test is right and your code is wrong — which is a
wonderfully clear place to learn from.

Source files in the old repo:
- `ADHD_Fairy_Final_Handoff/prototype/bloom-engine.js`
- `ADHD_Fairy_Final_Handoff/tests/bloom-engine.test.cjs`

---

## The rules you're implementing

| Rule | Value |
|---|---|
| One focus block | 25 minutes |
| One break | 5 minutes |
| A bloomed flower | 100 focused minutes = 4 blocks |
| Growth stages | Seed → Sprout (10m) → Leaves (25m) → Growing tall (50m) → Bud (75m) → Bloomed (100m) |
| Species | Daisy, Lavender, Rose, Sunflower, Bluebell — chosen once per plant |

Six behaviours the original tests pin down. Each exists because of a real-world situation:

| Behaviour | The situation it handles |
|---|---|
| A 10-minute session **saves progress** | You got interrupted. You shouldn't lose the plant. |
| Break time **does not** grow the plant | Resting is not focusing. |
| Paused time is **excluded** | You walked away. That's not focus. |
| A late tick advances **one phase only** | You closed your laptop for 16 hours. You don't get 16 hours of credit. |
| A **backwards clock** gives no credit | Daylight saving, NTP correction, manual clock change. |
| Blooming is **idempotent** | The UI ticks constantly. You get one flower, not fifty. |

---

## Session 1 — The tests

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** write the specification down before writing any code.

These are ported from `bloom-engine.test.cjs`, so the expected values are known good.

`tests/test_bloom.py`:

```python
from fairy.domain import bloom
from fairy.domain.bloom import BLOCK_MS, BREAK_MS, MINUTE_MS, Phase

PICK_ROSE = 0.41  # 0.41 * 5 -> index 2 -> "Rose"
PICK_BLUEBELL = 0.9  # 0.9 * 5 -> index 4 -> "Bluebell"


def fresh():
    return bloom.create("plant-1", PICK_ROSE, now_ms=0)


def test_species_is_chosen_from_the_pick():
    assert fresh().plant.species == "Rose"
    assert bloom.create("p", PICK_BLUEBELL, now_ms=0).plant.species == "Bluebell"


def test_short_session_is_saved_and_is_not_a_flower():
    s = bloom.start(fresh(), now_ms=0, minutes=10)
    s = bloom.tick(s, now_ms=10 * MINUTE_MS)

    assert s.plant.focus_ms == 10 * MINUTE_MS
    assert s.phase is Phase.PAUSED_FOCUS
    assert bloom.stage(s) == "Sprout"
    assert s.collection == ()


def test_two_short_sessions_complete_one_block():
    s = bloom.start(fresh(), now_ms=0, minutes=10)
    s = bloom.tick(s, now_ms=10 * MINUTE_MS)
    s = bloom.start(s, now_ms=10 * MINUTE_MS, minutes=15)
    s = bloom.tick(s, now_ms=25 * MINUTE_MS)

    assert s.phase is Phase.BREAK
    assert s.plant.focus_ms == BLOCK_MS


def test_break_does_not_grow_the_plant():
    s = bloom.start(fresh(), now_ms=0, minutes=25)
    s = bloom.tick(s, now_ms=25 * MINUTE_MS)  # block done, now on break
    s = bloom.tick(s, now_ms=30 * MINUTE_MS)  # break elapses

    assert s.phase is Phase.READY
    assert s.plant.focus_ms == BLOCK_MS


def test_next_block_requires_an_explicit_start():
    s = bloom.start(fresh(), now_ms=0, minutes=25)
    s = bloom.tick(s, now_ms=25 * MINUTE_MS)
    s = bloom.tick(s, now_ms=30 * MINUTE_MS)
    s = bloom.tick(s, now_ms=999 * MINUTE_MS)  # idle for ages

    assert s.plant.focus_ms == BLOCK_MS  # no free progress


def test_paused_time_is_excluded():
    s = bloom.start(fresh(), now_ms=0)
    s = bloom.pause(s, now_ms=5 * MINUTE_MS)
    s = bloom.tick(s, now_ms=40 * MINUTE_MS)

    assert s.plant.focus_ms == 5 * MINUTE_MS


def test_resume_still_respects_the_block_cap():
    s = bloom.start(fresh(), now_ms=0)
    s = bloom.pause(s, now_ms=5 * MINUTE_MS)
    s = bloom.resume(s, now_ms=40 * MINUTE_MS)
    s = bloom.tick(s, now_ms=60 * MINUTE_MS)

    assert s.phase is Phase.BREAK


def test_a_very_late_tick_advances_one_phase_only():
    s = bloom.start(fresh(), now_ms=0)
    s = bloom.tick(s, now_ms=1000 * MINUTE_MS)

    assert s.plant.focus_ms == BLOCK_MS
    assert s.remaining_ms == BREAK_MS  # on break, not past it


def test_a_paused_break_is_frozen():
    s = bloom.start(fresh(), now_ms=0)
    s = bloom.tick(s, now_ms=1000 * MINUTE_MS)
    s = bloom.pause(s, now_ms=1001 * MINUTE_MS)
    s = bloom.tick(s, now_ms=1005 * MINUTE_MS)

    assert s.phase is Phase.PAUSED_BREAK
    assert s.remaining_ms == 4 * MINUTE_MS


def test_a_backwards_clock_gives_no_credit():
    s = bloom.start(fresh(), now_ms=100)
    s = bloom.tick(s, now_ms=50)  # clock went backwards
    s = bloom.tick(s, now_ms=150)

    assert s.plant.focus_ms == 50  # not 100 — no double credit


def test_four_blocks_make_one_flower():
    s = fresh()
    now = 0
    for i in range(4):
        s = bloom.start(s, now_ms=now)
        now += BLOCK_MS
        s = bloom.tick(s, now_ms=now)
        if i < 3:
            assert s.collection == ()  # no early bloom
            now += BREAK_MS
            s = bloom.tick(s, now_ms=now)

    assert now == 115 * MINUTE_MS  # 4x25 focus + 3x5 break
    assert s.phase is Phase.BLOOMED
    assert len(s.collection) == 1


def test_blooming_is_idempotent():
    s = fresh()
    now = 0
    for i in range(4):
        s = bloom.start(s, now_ms=now)
        now += BLOCK_MS
        s = bloom.tick(s, now_ms=now)
        if i < 3:
            now += BREAK_MS
            s = bloom.tick(s, now_ms=now)

    s = bloom.tick(s, now_ms=now + 100_000_000)
    assert len(s.collection) == 1


def test_next_plant_keeps_the_collection():
    s = fresh()
    now = 0
    for i in range(4):
        s = bloom.start(s, now_ms=now)
        now += BLOCK_MS
        s = bloom.tick(s, now_ms=now)
        if i < 3:
            now += BREAK_MS
            s = bloom.tick(s, now_ms=now)

    s = bloom.next_plant(s, "plant-2", PICK_BLUEBELL, now_ms=now)

    assert len(s.collection) == 1
    assert s.plant.focus_ms == 0
    assert s.plant.species == "Bluebell"
```

**Why milliseconds and not seconds.** Integers are exact; floats are not. `0.1 + 0.2` is
`0.30000000000000004` in Python, which would make time comparisons flaky. Integer
milliseconds sidestep the whole problem.

**Why `now_ms=0` as the starting point.** Time is just a number here, so "zero" is a
perfectly good moment. Your tests don't care what year it is — they only care about
*differences*. That's what injecting time buys you.

**Why `s = bloom.tick(s, ...)` reassigns.** Every function returns a **new** state instead
of modifying the old one. More on that in Session 2.

**Notice `115 * MINUTE_MS`** in the four-blocks test: 4 focus blocks (100 min) plus 3 breaks
(15 min). Three breaks, not four — there's no break after the last block. Details like that
are exactly what a ported test suite gives you for free.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run pytest tests/test_bloom.py
```

All thirteen should fail with `ModuleNotFoundError: No module named 'fairy.domain.bloom'`.
**That's the correct first failure** — the tests are real and they're running your code.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `collected 0 items` | The filename must start with `test_`, and functions with `test_` |
| `ImportError` on `fairy.domain` | Missing `src/fairy/domain/__init__.py` |
| Tests *pass* before you wrote the engine | Something is wrong — you may have an old `bloom.py` lying around |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "test: port bloom engine tests from the JS prototype" && git push
```


---

## Session 2 — The engine

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** make thirteen tests pass, and understand pure functions properly.

### What "pure" actually means

A pure function:

1. Given the same inputs, always returns the same output
2. Changes nothing outside itself — no database writes, no network, no clock reads

`bloom.tick(state, now_ms)` is pure. Call it with the same state and same `now_ms` a
thousand times and you get the identical answer every time.

That's why these thirteen tests run in about **0.02 seconds**. No database to set up, no
waiting for a real 25 minutes to pass. Compare that with testing a timer that reads the
clock itself — you'd have to actually wait, or resort to elaborate mocking.

### `src/fairy/domain/bloom.py`

```python
"""The focus timer. PURE — no database, no network, no clock.

Time is always passed in as `now_ms`, an integer of milliseconds. That is what makes
every rule in here testable in microseconds.

Ported from the original prototype's bloom-engine.js.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

MINUTE_MS = 60_000
BLOCK_MS = 25 * MINUTE_MS
BREAK_MS = 5 * MINUTE_MS
TARGET_MS = 4 * BLOCK_MS  # 100 focused minutes = one flower

SPECIES = ("Daisy", "Lavender", "Rose", "Sunflower", "Bluebell")


class Phase(StrEnum):
    READY = "ready"
    FOCUS = "focus"
    BREAK = "break"
    PAUSED_FOCUS = "pausedFocus"
    PAUSED_BREAK = "pausedBreak"
    BLOOMED = "bloomed"


@dataclass(frozen=True)
class Plant:
    id: str
    species: str
    focus_ms: int = 0
    planted_at_ms: int = 0
    bloomed_at_ms: int | None = None


@dataclass(frozen=True)
class BloomState:
    plant: Plant
    phase: Phase = Phase.READY
    remaining_ms: int = BLOCK_MS
    anchor_ms: int = 0
    collection: tuple[Plant, ...] = ()


def create(
    plant_id: str,
    pick: float,
    now_ms: int,
    collection: tuple[Plant, ...] = (),
) -> BloomState:
    """Start a new plant. `pick` is a 0..1 number choosing the species."""
    index = min(len(SPECIES) - 1, max(0, int(pick * len(SPECIES))))
    return BloomState(
        plant=Plant(id=plant_id, species=SPECIES[index], planted_at_ms=now_ms),
        phase=Phase.READY,
        remaining_ms=BLOCK_MS,
        anchor_ms=now_ms,
        collection=collection,
    )


def stage(state: BloomState) -> str:
    """The plant's visible growth stage."""
    minutes = state.plant.focus_ms / MINUTE_MS
    if minutes >= 100:
        return "Bloomed"
    if minutes >= 75:
        return "Bud"
    if minutes >= 50:
        return "Growing tall"
    if minutes >= 25:
        return "Leaves"
    if minutes >= 10:
        return "Sprout"
    return "Seed"


def tick(state: BloomState, now_ms: int) -> BloomState:
    """Advance the clock. Safe to call at any time, any number of times."""
    if state.phase not in (Phase.FOCUS, Phase.BREAK):
        return state

    elapsed = max(0, now_ms - state.anchor_ms)
    anchor = max(now_ms, state.anchor_ms)  # a backwards clock never rewinds us
    used = min(elapsed, state.remaining_ms)
    remaining = state.remaining_ms - used

    if state.phase is Phase.FOCUS:
        focus_ms = min(TARGET_MS, state.plant.focus_ms + used)
        plant = replace(state.plant, focus_ms=focus_ms)
        collection = state.collection
        phase = state.phase

        if remaining == 0:
            if focus_ms == TARGET_MS:
                phase = Phase.BLOOMED
                if not any(p.id == plant.id for p in collection):
                    collection = (*collection, replace(plant, bloomed_at_ms=now_ms))
            elif focus_ms % BLOCK_MS == 0:
                phase = Phase.BREAK
                remaining = BREAK_MS
            else:
                phase = Phase.PAUSED_FOCUS

        return replace(
            state,
            plant=plant,
            phase=phase,
            remaining_ms=remaining,
            anchor_ms=anchor,
            collection=collection,
        )

    # on a break — time passes but the plant does not grow
    if remaining == 0:
        return replace(state, phase=Phase.READY, remaining_ms=BLOCK_MS, anchor_ms=anchor)
    return replace(state, remaining_ms=remaining, anchor_ms=anchor)


def start(state: BloomState, now_ms: int, minutes: float = 25) -> BloomState:
    """Begin or resume focusing."""
    state = tick(state, now_ms)

    if state.phase is Phase.PAUSED_BREAK:
        return replace(state, phase=Phase.BREAK, anchor_ms=now_ms)

    if state.phase not in (Phase.READY, Phase.PAUSED_FOCUS):
        return state
    if minutes <= 0:
        return state

    # never overshoot the end of the current 25-minute block
    room = BLOCK_MS - (state.plant.focus_ms % BLOCK_MS)
    return replace(
        state,
        phase=Phase.FOCUS,
        remaining_ms=min(round(minutes * MINUTE_MS), room),
        anchor_ms=now_ms,
    )


def pause(state: BloomState, now_ms: int) -> BloomState:
    """Stop the clock without losing progress."""
    state = tick(state, now_ms)
    if state.phase is Phase.FOCUS:
        return replace(state, phase=Phase.PAUSED_FOCUS)
    if state.phase is Phase.BREAK:
        return replace(state, phase=Phase.PAUSED_BREAK)
    return state


def resume(state: BloomState, now_ms: int) -> BloomState:
    """Continue from wherever we paused."""
    if state.phase is Phase.PAUSED_FOCUS:
        minutes = state.remaining_ms / MINUTE_MS or 25
        return start(state, now_ms, minutes)
    return start(state, now_ms)


def next_plant(state: BloomState, plant_id: str, pick: float, now_ms: int) -> BloomState:
    """After a bloom, plant the next one. Keeps everything already grown."""
    if state.phase is not Phase.BLOOMED:
        return state
    return create(plant_id, pick, now_ms, state.collection)
```

### Understanding dataclasses

```python
@dataclass(frozen=True)
class Plant:
    id: str
    species: str
    focus_ms: int = 0
```

`@dataclass` writes the boring parts for you — the `__init__`, a readable `__repr__`, and
`==` that compares field values. You declare the fields; Python generates the rest.

`frozen=True` makes instances **immutable**: `plant.focus_ms = 5` raises an error. That
sounds inconvenient until you see what it buys you.

### Understanding `replace()`

Since you can't modify a frozen object, you make a **modified copy**:

```python
new_plant = replace(old_plant, focus_ms=1500)
```

Reads as: *a copy of `old_plant`, but with `focus_ms` set to 1500.* Everything else is
carried over. The original is untouched.

**Why bother?** Three reasons, all of which you'll feel:

1. **No spooky action at a distance.** A function can never secretly modify state that
   something else is holding.
2. **Tests can compare before and after** — the old state still exists.
3. **Stage 3's desktop fairy** can hold a state and tick it locally without any risk of
   corrupting what's in the database.

The original JavaScript achieved the same thing with `structuredClone`. Frozen dataclasses
are Python's cleaner version.

**Why `collection` is a tuple, not a list.** Lists are mutable; tuples aren't. A frozen
dataclass holding a list would still let you do `state.collection.append(...)` — immutable
in name only. `(*collection, new_plant)` builds a new tuple with one more item.

### Understanding the state machine

Six phases, and the rules for moving between them:

```
   READY ──start──► FOCUS ──pause──► PAUSED_FOCUS
     ▲                │                   │
     │                │ block done        │ start
     │                ▼                   ▼
     └──time up──── BREAK ◄───────────── FOCUS
                      │
                      │ pause
                      ▼
                PAUSED_BREAK

   FOCUS ── 100 minutes reached ──► BLOOMED ──next_plant──► READY (new plant)
```

`tick` is the only function that moves time forward. `start`, `pause` and `resume` all call
`tick` first, so no matter which one you call, elapsed time is accounted for before
anything else happens. That single discipline is what makes the awkward cases work.

### Understanding the three defensive lines

These are the ones worth reading twice, because each one exists for a real failure:

```python
elapsed = max(0, now_ms - state.anchor_ms)
```
If the clock went **backwards**, `now_ms - anchor_ms` is negative. `max(0, ...)` turns that
into zero elapsed rather than negative credit.

```python
anchor = max(now_ms, state.anchor_ms)
```
And the anchor never moves backwards either — so a clock correction can't cause the *next*
tick to double-count.

```python
used = min(elapsed, state.remaining_ms)
```
You can only use as much time as this phase had left. Close your laptop for 16 hours and
you get 25 minutes of credit, not 16 hours. This is what makes the "one phase only" test
pass.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run pytest tests/test_bloom.py -v
```

Thirteen green, in around 0.02 seconds.

Now prove immutability to yourself:

```bash
cd ~/code/fairy && uv run python -c "
from fairy.domain import bloom
s = bloom.create('p', 0.41, now_ms=0)
try:
    s.remaining_ms = 5
except Exception as e:
    print(type(e).__name__, '->', e)
"
```

You should get `FrozenInstanceError`. That's `frozen=True` refusing to let anything mutate
your state behind your back.

### ⚠ If it breaks

| Failing test | Most likely cause |
|---|---|
| `backwards_clock` | Missing `max(0, ...)` or `max(now_ms, ...)` |
| `late_tick_advances_one_phase_only` | Missing `min(elapsed, remaining_ms)` |
| `blooming_is_idempotent` | Missing the `if not any(p.id == plant.id ...)` guard |
| `four_blocks_make_one_flower` | Check `TARGET_MS` is `4 * BLOCK_MS`, not `100 * MINUTE_MS` typed wrong |
| `FrozenInstanceError` in your own code | You wrote `state.x = y` somewhere — use `replace()` |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: port bloom timer engine to pure Python" && git push
```


---

## Session 3 — Persistence

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** save the timer, and see why keeping it out of `domain/` was worth it.

The engine is pure. Saving is a *separate job* — that separation is the whole point.

Add to `SCHEMA` in `store.py`:

```sql
CREATE TABLE IF NOT EXISTS focus_state (
    id           INTEGER PRIMARY KEY CHECK (id = 1),   -- only ever one row
    plant_id     TEXT    NOT NULL,
    species      TEXT    NOT NULL,
    focus_ms     INTEGER NOT NULL DEFAULT 0,
    planted_at   INTEGER NOT NULL,
    phase        TEXT    NOT NULL,
    remaining_ms INTEGER NOT NULL,
    anchor_ms    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS garden (
    plant_id   TEXT PRIMARY KEY,
    species    TEXT    NOT NULL,
    bloomed_at INTEGER NOT NULL
);
```

**`CHECK (id = 1)` is a nice trick** — the database itself refuses to store a second row.
You cannot end up with two timers running by accident, no matter what your code does.
Pushing a rule into the schema means it holds even if you write a bug.

Then `src/fairy/focus.py` — the impure layer:

```python
def load(conn) -> BloomState:
    """Read saved state, or create a fresh plant if there is none."""

def save(conn, state: BloomState) -> None:
    """Write state back. Also inserts any newly bloomed plants into `garden`."""

def current(conn, now_ms: int) -> BloomState:
    """Load, tick to now, save, return. The one function callers need."""
```

**Notice the shape.** `focus.py` does I/O and calls into `bloom.py`, never the reverse.
`domain/` doesn't know a database exists. Keeping the arrow pointing one way is what lets
you test the hard logic without a database at all.

Write tests for these with `tmp_path`, exactly like Stage 1.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
from fairy import store, focus
import time
with store.session() as c:
    s = focus.current(c, int(time.time()*1000))
    print(s.phase, s.plant.species, s.remaining_ms // 60000, 'min left')
"
```

Run it twice. The second run should **load what the first one saved** — not start over.

```bash
sqlite3 ~/.fairy/fairy.db "SELECT * FROM focus_state;"
```

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `CHECK constraint failed: focus_state` | You tried to insert a second row. Use `INSERT OR REPLACE` with `id = 1` |
| State resets every run | `save()` isn't being called, or `load()` isn't finding the row |
| `no such table: focus_state` | You added it to `SCHEMA` but the database already existed — `CREATE TABLE IF NOT EXISTS` won't alter an existing one. Delete `~/.fairy/fairy.db` and let it rebuild, or run the `CREATE` by hand |
| Phase is a string, not a `Phase` | Convert on load: `Phase(row["phase"])` |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: persist focus state and garden" && git push
```


---

## Session 4 — The timer MCP server

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

`src/fairy/servers/timer_server.py` — four tools:

```python
@mcp.tool
def start_focus(minutes: int = 25) -> dict:
    """Start a focus session on the user's current plant.

    Args:
        minutes: How long to focus. Capped at the remaining time in the
                 current 25-minute block.
    """

@mcp.tool
def pause_focus() -> dict:
    """Pause the running focus session without losing progress."""

@mcp.tool
def get_timer() -> dict:
    """Current phase, minutes remaining, growth stage, and total focused time."""

@mcp.tool
def list_garden() -> list[dict]:
    """Every flower the user has fully grown."""
```

**Where the clock lives.** Use `int(time.time() * 1000)` for `now_ms` **here**, in the
server — never inside `domain/bloom.py`. This file is the boundary between your pure logic
and the messy real world, and the clock is part of the messy real world.

Register the command in `pyproject.toml`:

```toml
[project.scripts]
fairy-tasks = "fairy.servers.tasks_server:main"
fairy-timer = "fairy.servers.timer_server:main"
```

```bash
uv sync
```

(`uv sync` is needed after adding a script so the new command exists.) Then add it
alongside `fairy` in `claude_desktop_config.json` and restart Claude Desktop.

### ✔ Check yourself

Ask Claude: *"start a 25 minute focus session"*, then *"how's my plant doing?"*

```bash
sqlite3 ~/.fairy/fairy.db "SELECT phase, focus_ms, remaining_ms FROM focus_state;"
```

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add focus timer MCP server" && git push
```


---

## ✅ Stage 2 complete

**You built:** a tested timer engine, persistent state, and four new MCP tools.

**You learned:**

- **Pure functions** — same input, same output, no side effects
- **Immutability** with frozen dataclasses and `replace()`
- **State machines** — explicit phases and explicit transitions
- **Defensive time handling** — clocks go backwards, laptops sleep
- **Layering** — `domain/` knows nothing about storage, and that's what makes it testable

### Stretch exercise (optional)

The design docs mention a "rescue" feature: when someone can't face a 25-minute block,
offer a smaller step without any punishment.

Add `bloom.suggest_smaller(state) -> int` returning a gentler duration in minutes. Write
the tests first. What should it suggest when the plant is at 0 minutes versus 90? Should it
ever suggest more than the remaining room in the block?

It's a pure function, so it belongs in `domain/` — and your test for it will run in
microseconds.

Next: [Stage 3 — The desktop fairy](stage-3-desktop-fairy.md)
