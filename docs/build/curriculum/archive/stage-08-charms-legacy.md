# Stage 7 — Charms and garden

> **Historical reference — do not follow as Stage 7.** The non-punitive reward rules remain
> useful, but implementation is deferred to revised Stage 8 after the core product,
> evaluation, accessibility, and privacy work. Return to the
> [current curriculum index](README.md) before making changes.

> **By the end of this stage** finishing tasks earns charms, flowers collect in a garden,
> and the project is complete.

**Sessions:** 3 · **Time:** ~2 weeks

### What you'll learn

| Concept | Where |
|---|---|
| Table-driven design — data instead of `if` statements | Session 2 |
| Idempotency — why "run it twice" must be safe | Session 2 |
| Deduplication by identity, not by counting | Session 2 |
| Persisting before presenting | Session 3 |

Like Stage 2, this is a port of a pure engine that already has a test suite. Source files:

- `ADHD_Fairy_Final_Handoff/prototype/charm-engine.js`
- `ADHD_Fairy_Final_Handoff/tests/charms.test.cjs`
- `ADHD_Fairy_Final_Handoff/specs/charm-catalog.json`

---

## The design rules

From the original `GAMIFICATION.md`, and worth preserving exactly:

| Rule | Why it was chosen |
|---|---|
| **No currency** — no stardust, balance, purchases, equipping | Rewards shouldn't become another economy to manage |
| **Charms unlock automatically** from milestones | Nothing to claim; no extra decision |
| **Earned is permanent** | Dismissing a popup acknowledges the *message*, never the ownership |
| **No sequence gate** | You can earn the quest charm without the task charm |
| **Catalog order is display order**, not progression | It's a shelf, not a skill tree |
| **Never punitive** | No flower death, no streak loss, no attention monitoring |

Those last two matter most. This is a tool for people who already feel behind — a reward
system that can take things away would be actively harmful. **That's a product decision
encoded in code**, which is a good thing to be able to talk about.

---

## Session 1 — The tests

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

Ported from `charms.test.cjs`, which pins down the tricky cases.

`tests/test_charms.py`:

```python
from fairy.domain import charms

DAY = "2026-09-14"


def test_a_fresh_shelf_is_empty():
    assert charms.fresh().unlocked == ()


def test_first_task_earns_the_star():
    state = charms.record(charms.fresh(), type="task", item_id="t1", day=DAY, now_ms=1)
    assert [c.id for c in state.unlocked] == ["star"]


def test_the_same_task_only_counts_once():
    state = charms.fresh()
    state = charms.record(state, type="task", item_id="t1", day=DAY, now_ms=1)
    state = charms.record(state, type="task", item_id="t1", day=DAY, now_ms=2)
    assert len(state.tasks) == 1
    assert len(state.unlocked) == 1


def test_five_tasks_earn_matcha():
    state = charms.fresh()
    for i in range(1, 6):
        state = charms.record(state, type="task", item_id=f"t{i}", day=DAY, now_ms=i)
    assert any(c.id == "matcha" for c in state.unlocked)


def test_recompleting_a_quest_does_not_count_twice():
    state = charms.fresh()
    state = charms.record(state, type="quest", item_id="q1", day=DAY, now_ms=1)
    state = charms.record(state, type="quest", item_id="q1", day="2026-09-15", now_ms=2)
    assert len(state.quests) == 1


def test_active_days_need_not_be_consecutive():
    state = charms.fresh()
    state = charms.record(state, type="task", item_id="t1", day="2026-09-14", now_ms=1)
    state = charms.record(state, type="quest", item_id="q1", day="2026-09-15", now_ms=2)
    state = charms.record(state, type="chat", item_id=None, day="2026-09-30", now_ms=3)
    assert len(state.days) == 3
    assert any(c.id == "lantern" for c in state.unlocked)


def test_an_unknown_event_type_changes_nothing():
    state = charms.record(charms.fresh(), type="task", item_id="t1", day=DAY, now_ms=1)
    after = charms.record(state, type="launch", item_id=None, day="2026-10-01", now_ms=2)
    assert after == state


def test_there_is_no_sequence_gate():
    state = charms.record(charms.fresh(), type="quest", item_id="early", day=DAY, now_ms=1)
    ids = {c.id for c in state.unlocked}
    assert "potion" in ids
    assert "star" not in ids


def test_acknowledging_never_removes_ownership():
    state = charms.record(charms.fresh(), type="task", item_id="t1", day=DAY, now_ms=1)
    owned = len(state.unlocked)
    state = charms.acknowledge(state, [c.id for c in state.unlocked])
    assert state.pending == ()
    assert len(state.unlocked) == owned


def test_everything_can_unlock_at_once_and_is_idempotent():
    state = charms.fresh()
    for i in range(250):
        state = charms.record(state, type="task", item_id=f"t{i}", day=DAY, now_ms=i)
    for i in range(30):
        state = charms.record(state, type="quest", item_id=f"q{i}", day=DAY, now_ms=i)
    for i in range(30):
        state = charms.record(state, type="flower", item_id=f"f{i}", day=DAY, now_ms=i)

    once = charms.evaluate(state, now_ms=999)
    twice = charms.evaluate(once, now_ms=1000)
    assert len(once.unlocked) == len(twice.unlocked)
```

### Read three of these carefully

**`test_an_unknown_event_type_changes_nothing`** compares **whole states**:
`assert after == state`.

- Only four event types count
- An unrecognised one like `"launch"` must change *nothing* — not the day list, not the counts
- Comparing whole objects works because frozen dataclasses give you `==` for free

**`test_there_is_no_sequence_gate`** encodes a *product* rule as a test. Finish a quest
before your first task and you get the quest charm and not the task charm. Someone
"optimising" later might be tempted to add ordering; this test stops them.

**`test_everything_can_unlock_at_once_and_is_idempotent`** — running `evaluate` twice must
change nothing the second time.

**New concept: idempotency.** It's what lets you call `evaluate` after every task, on every
app start, whenever — with no risk of double-awarding.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run pytest tests/test_charms.py
```

Every test should fail with `ModuleNotFoundError: No module named 'fairy.domain.charms'`.
**That's the correct first failure** — it proves the tests are running your code.

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "test: port charm engine tests from the JS prototype" && git push
```


---

## Session 2 — The engine

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

`src/fairy/domain/charms.py` — pure, no I/O, same rules as `bloom.py`.

### Table-driven design

The catalog is an 18-row table. Copy the values from `charm-engine.js` exactly:

```python
CATALOG: tuple[Charm, ...] = (
    Charm("star", "First Spark", "tasks", 1),
    Charm("matcha", "A Little Momentum", "tasks", 5),
    Charm("potion", "Something Magical", "quests", 1),
    Charm("lantern", "Welcome Home", "days", 3),
    Charm("daisy", "In Bloom", "flowers", 1),
    Charm("coffee", "Finding Your Rhythm", "tasks", 25),
    # ... 12 more, through:
    Charm("crown", "Every Little Step", "tasks", 250),
)
```

**Why a table and not eighteen `if` statements.** Compare:

```python
# table-driven — 18 rows of DATA
for charm in CATALOG:
    if len(getattr(state, charm.metric)) >= charm.threshold:
        unlock(charm)

# the alternative — 18 branches of CODE
if len(state.tasks) >= 1: unlock("star")
if len(state.tasks) >= 5: unlock("matcha")
...
```

- The table is one piece of logic you test once
- A nineteenth charm is **one new row** — no new code path, no new test
- General habit: when branches differ only in values, turn the values into data

### The four functions

```python
def fresh() -> CharmState:
    """A brand-new empty shelf."""


def record(state, *, type, item_id, day, now_ms) -> CharmState:
    """Note that something happened, then re-evaluate every milestone."""


def evaluate(state, *, now_ms) -> CharmState:
    """Unlock anything whose threshold is now met. Idempotent."""


def acknowledge(state, ids) -> CharmState:
    """Clear pending celebrations. Never touches `unlocked`."""
```

### Deduplicate by identity, not by counting

The single most important implementation detail:

```python
# store ids
tasks: tuple[str, ...] = ()      # ("t1", "t2", "t7")

# NOT a count
task_count: int = 0              # <- wrong
```

**Why.** Complete a task, un-complete it, complete it again. With a counter you'd be at 3.
With a set of ids you're at 1, which is correct — it's the same task.

Reopening and re-finishing a quest gives one credit, forever. That's
`test_recompleting_a_quest_does_not_count_twice`, and a counter cannot pass it.

This is also what makes `evaluate` idempotent: it derives everything from the id
collections, so running it again computes the same answer.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run pytest tests/test_charms.py -v
```

All green, in milliseconds. Then see the table-driven design pay off:

```bash
cd ~/code/fairy && uv run python -c "
from fairy.domain import charms
print(len(charms.CATALOG), 'charms in the catalog')
s = charms.fresh()
for i in range(5): s = charms.record(s, type='task', item_id=f't{i}', day='2026-09-17', now_ms=i)
print('earned:', [c.id for c in s.unlocked])
"
```

### ⚠ If it breaks

| Failing test | Cause |
|---|---|
| `the_same_task_only_counts_once` | You're counting instead of storing ids |
| `unknown_event_type_changes_nothing` | Your allow-list of event types is missing, or `day` is recorded before the type check |
| `idempotent` | `evaluate` appends without checking whether it's already unlocked |
| `no_sequence_gate` | You added ordering logic the design explicitly forbids |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: port charm engine to pure Python" && git push
```


---

## Session 3 — Shelf, discover, garden

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

Persist `charms` and `charm_events` tables, then build the three Collection tabs from the
design docs.

**Your charms** — earned only, on a wooden shelf, ordered by earned time. Names go *below*
the shelf, not between icon and wood. One seated fairy at the right of the first row. A
fresh account shows an **empty** shelf — never pre-award samples.

**Discover** — unearned only, two columns, sage progress bar, exact `n/threshold` text. No
fairy, no scene, no "claim" button.

**Garden** — flowers, which unlike charms *can* repeat. Growing and Bloomed, with species,
counts and dates. Plain terracotta pots, no hearts.

### The celebration rules, and why each exists

| Rule | The failure it prevents |
|---|---|
| **Persist the unlock before showing anything** | App crashes mid-celebration → you still own the charm |
| **Batch** multiple new charms into one popup | Finishing a big session shouldn't fire five modals |
| **Defer during a running focus session** | Never interrupt focus. Queue until it pauses or the block ends |
| Dismissing acknowledges **presentation**, not ownership | Closing a window must never cost you something you earned |

**Persist before you present.** Anything you show should already be true in storage — or a
crash between "show" and "save" leaves the user believing something false.

Use the real pixel assets from `assets/charms.png` with the source rectangles in
`sprite-rects.json`. **Never substitute emoji for the collectible art** — that was an
explicit rule in the design handoff, and it's the difference between a crafted thing and a
prototype.

### ✔ Check yourself

Complete your first task in the web UI. You should get **one** congratulations popup for
the `star` charm, and it should appear on the shelf.

```bash
sqlite3 ~/.fairy/fairy.db "SELECT * FROM charms;"
```

Then test the deferral rule: start a focus session, complete a task during it, and confirm
**no popup interrupts you** — it should wait for the break.

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| Popup appears twice | Dismissal isn't persisted before navigating |
| Charm lost after reload | You showed it before saving. **Persist, then present** |
| Popup during focus | The deferral check is missing |
| Five popups at once | Batch them into one modal with a list |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add charms shelf, discover, and garden" && git push
```


---

## ✅ Stage 7 complete — and so is the project

**You built:**

- A local-first ADHD companion you use every day
- Seven MCP servers exposing your real tools
- A local LLM agent with an eval scoreboard
- A floating desktop fairy
- A web UI from your own designs
- A tested pure-domain core
- A public repo with green CI and a clickable demo

**You learned in this stage:**

- **Table-driven design** — data beats branching
- **Idempotency** — safe to run twice, so safe to run always
- **Identity-based deduplication** — store ids, not counts
- **Persist before present** — never show what isn't saved

---

## Finishing touches

### The README

What most people actually read. In this order:

1. The fairy **GIF**
2. **One sentence** on what it is
3. The **demo link**
4. The **architecture diagram**
5. The **eval table** from Stage 5
6. **Setup**
7. **CI badge**

### The decision notes

Write them as you go, not at the end. Good ones from this build:

- MCP-first instead of a web backend
- PySide6 for the desktop surface — with the accessory-policy experiment
- stdlib `sqlite3` over an ORM
- Local-first over hosted
- Which model, backed by your own eval numbers

### What to say in an interview

Not "I built an ADHD app." Try:

> "It's a local-first agent over MCP. Tools are typed Python functions exposed as MCP
> servers, so the same tools work in Claude Desktop or my own Ollama loop. The domain logic
> is pure and time-injected, which is why I can score the planner against fixtures in CI. I
> benchmarked three providers — here's the table."

That's an AI-engineering answer, and every clause of it is true.

### Stretch exercise (optional)

Add charm number nineteen. Notice that it's **one row in `CATALOG`** and one line in the
sprite map — no new logic, no new test for the mechanism.

That's what you get for choosing a table over eighteen `if` statements in Session 2. Sit
with that for a second: the design decision you made weeks ago is why today's change takes
two minutes.
