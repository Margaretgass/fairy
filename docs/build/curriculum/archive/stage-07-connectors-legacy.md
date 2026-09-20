# Stage 4 — Real integrations

> **Historical reference — do not follow as Stage 4.** Connector concepts will be narrowed
> into revised Stage 7 after the local product loop works. All third-party integrations
> begin read-only with explicit consent, provenance, revocation, and no silent writes.
> Return to the [current curriculum index](README.md) before making changes.

> **By the end of this stage** you can ask *"what's due this week and what's in my inbox?"*
> and get an answer from your actual school and work life.

**Sessions:** one per source · **Time:** ~1 week each, ongoing

### What you'll learn

| Concept | Where |
|---|---|
| `Protocol` — interfaces without inheritance | Session 1 |
| Normalising different sources into one shape | Session 1 |
| HTTP clients and parsing real-world formats | Session 2 |
| Splitting network code from parsing code (for testability) | Session 2 |
| Running other programs from Python (`subprocess`) | Session 4 |
| OAuth — what the dance actually is | Session 6 |
| Secret hygiene on a public repo | Throughout |

### The pattern you'll repeat

Every connector has the same three parts. The first one is hard; the rest are variations:

```
src/fairy/connectors/<name>.py   fetch raw data, normalise it    <- the work
src/fairy/servers/<name>.py      expose it as MCP tools          <- ~30 lines
tests/test_<name>.py             test against a saved fixture    <- no network
```

---

## Session 1 — The Connector protocol

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** decide the one shape every source will be converted into.

```bash
touch ~/code/fairy/src/fairy/connectors/base.py
```

`src/fairy/connectors/base.py`:

```python
"""What every connector must provide."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class ConnectorError(Exception):
    """A source could not be read. Carries a human-readable reason."""


class SourceItem(BaseModel):
    """One normalised thing from any source: an assignment, note, email, file."""

    source: str  # "d2l", "notion", "gmail"
    external_id: str  # stable id in that system
    title: str
    body: str | None = None
    due_at: datetime | None = None
    url: str | None = None
    fetched_at: datetime


class Connector(Protocol):
    name: str

    def fetch(self) -> list[SourceItem]:
        """Read from the source. Raises ConnectorError on failure."""
        ...
```

### Understanding `Protocol`

**New concept: `Protocol`** — a structural interface. Any class with a `name` and a
`fetch()` satisfies it. No inheritance needed.

```python
class D2LConnector:          # inherits from nothing
    name = "d2l"
    def fetch(self) -> list[SourceItem]: ...
# ...and this already IS a Connector, as far as type checkers care
```

"Duck typing with types" — if it walks like a duck it's a duck, and your editor can now
check the walking. Your connectors stay independent of each other.

### Why one `SourceItem` for everything

A Notion page, a Gmail thread, and a D2L assignment are wildly different. If you pass all
three shapes to the agent in Stage 5, the agent has to understand seven formats.

Normalise them here instead, and everything downstream handles **one** shape. That's the
whole trick, and it's why `external_id` exists — you keep the original id so you can link
back, without the rest of your code caring what system it came from.

### Also write `FixtureConnector`

A connector that reads `SourceItem`s from a JSON file instead of a network:

```python
class FixtureConnector:
    """Reads invented data from a JSON file. For tests and demo mode."""
    name = "fixture"
```

Two things from one small class:
- **Fast tests** — no network, works offline, works in CI
- **Demo mode** in Stage 6 — a stranger runs your project with no credentials

Ten minutes now. Painful to retrofit later.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
from fairy.connectors.base import SourceItem
from datetime import UTC, datetime
i = SourceItem(source='test', external_id='1', title='hello', fetched_at=datetime.now(UTC))
print(i.model_dump(mode='json'))
"
```

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `ValidationError: fetched_at field required` | Every `SourceItem` needs it — that's deliberate, provenance matters |
| `ImportError: cannot import name 'Protocol'` | It's in `typing`, not `typing_extensions`, on 3.14 |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add Connector protocol and SourceItem model" && git push
```


---

## Session 2 — D2L / Brightspace

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

> ⚠️ **Read this before you spend an afternoon on the API.**
>
> **The Brightspace API will almost certainly not work for you.** It requires your app to
> be registered through **Manage Extensibility**, which is an *institution admin* tool.
> Students generally cannot self-register against their school's instance.
>
> **Use the iCal feed instead.** Every student has access to it.

### Get your feed URL

1. In Brightspace open **Calendar**
2. **Settings** → tick **Enable Calendar Feeds** → Save
3. **Subscribe** → choose *All Calendars* → copy the URL

That URL gives you every assignment due date, with no OAuth at all.

```bash
cd ~/code/fairy && uv add httpx icalendar
```

`src/fairy/connectors/d2l.py`:

```python
"""Read assignment due dates from a Brightspace iCal feed."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from icalendar import Calendar

from fairy.connectors.base import SourceItem


def parse_ics(raw: bytes, *, now: datetime) -> list[SourceItem]:
    """Pure: bytes in, items out. No network — so it's easy to test."""
    calendar = Calendar.from_ical(raw)
    items: list[SourceItem] = []
    for component in calendar.walk("VEVENT"):
        items.append(
            SourceItem(
                source="d2l",
                external_id=str(component.get("UID")),
                title=str(component.get("SUMMARY")),
                due_at=component.get("DTSTART").dt,
                fetched_at=now,
            )
        )
    return items


def fetch(url: str, *, now: datetime | None = None) -> list[SourceItem]:
    """Download the feed and parse it."""
    now = now or datetime.now(UTC)
    response = httpx.get(url, timeout=20, follow_redirects=True)
    response.raise_for_status()
    return parse_ics(response.content, now=now)
```

### The most important idea in this session

**`parse_ics` and `fetch` are separate on purpose.**

`fetch` touches the network — slow, needs internet, needs your credentials, and gives a
different answer every day. `parse_ics` is **pure**: bytes in, items out.

So you save one real response to `tests/fixtures/d2l.ics`, and test the parser against it:

```python
def test_parses_assignment_due_dates():
    raw = (FIXTURES / "d2l.ics").read_bytes()
    items = d2l.parse_ics(raw, now=NOW)
    assert len(items) == 3
    assert items[0].source == "d2l"
```

Fast, offline, deterministic, and it works in CI — which has no access to your school's
servers anyway. **This same split applies to every connector you write.** Network in one
function, parsing in another, tests on the parsing.

### Secrets

Put the feed URL in `.env`:

```bash
echo 'D2L_ICS_URL=https://your-school.brightspace.com/d2l/le/calendar/feed/user/feed.ics' >> ~/code/fairy/.env
```

Read it with `os.environ["D2L_ICS_URL"]`. **That URL is a secret** — anyone holding it can
read your whole schedule. `.env` is gitignored; `.env.example` shows the key name with no
value.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
import os
from fairy.connectors import d2l
items = d2l.fetch(os.environ['D2L_ICS_URL'])
print(f'{len(items)} events')
for i in items[:3]: print(' ', i.due_at, i.title)
"
```

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `KeyError: 'D2L_ICS_URL'` | Not in `.env`, or you didn't load `.env` — use `python-dotenv` or export it |
| `404` | Feeds not enabled yet. Calendar → Settings → Enable Calendar Feeds |
| Zero events | The feed is real but empty — check you picked *All Calendars*, not one course |
| `due_at` off by hours | `DTSTART` can be a date or a datetime, with or without a timezone. Handle both |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add D2L calendar connector" && git push
```


---

## Session 3 — Files and folders

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** the easiest connector. No auth, no API, pure standard library.

```python
def search_files(root: Path, query: str, limit: int = 20) -> list[SourceItem]:
    """Find files under root whose name matches query."""
```

Three rules, and they matter:

1. **Allow-list the folders** in config. Never let a tool walk your entire home directory —
   an AI with unrestricted filesystem search is a bad idea even when it's your own.
2. **Skip large files.** Anything over a few MB doesn't belong in a model's context.
3. **Skip binaries.** A PDF read as text is noise.

Use `pathlib`'s `Path.rglob("*")` to walk recursively.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
from pathlib import Path
from fairy.connectors import files
print([i.title for i in files.search_files(Path.home()/'Documents', 'pdf', limit=5)])
"
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| Takes forever | You're walking the whole home directory. Allow-list specific folders |
| `PermissionError` | Some system folders are unreadable — catch and skip, don't crash |
| Returns junk | Filter by extension and size before returning |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add local file search connector" && git push
```


---

## Session 4 — Apple Notes

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** talk to a macOS app that has no Python API.

Apple Notes has no API. You drive **AppleScript** through `subprocess`:

```python
import subprocess

from fairy.connectors.base import ConnectorError


def _osascript(script: str) -> str:
    """Run an AppleScript and return its output."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise ConnectorError(result.stderr.strip())
    return result.stdout.strip()
```

### Understanding `subprocess`

`subprocess.run` launches another program and waits for it. The arguments:

| Argument | Why |
|---|---|
| `["osascript", "-e", script]` | A **list**, not a string. Lists avoid shell-injection entirely — the same idea as SQL placeholders |
| `capture_output=True` | Collect stdout and stderr instead of printing them |
| `text=True` | Give me strings, not raw bytes |
| `timeout=30` | **Always set one.** Without it a hung app hangs your program forever |

`returncode` is 0 for success by Unix convention. Anything else is a failure, and `stderr`
usually explains why — so we raise `ConnectorError` with that message rather than swallowing
it.

macOS will show a permission prompt the first time. **Start read-only** — get listing and
reading working before you even consider writing.

### ✔ Check yourself

```bash
osascript -e 'tell application "Notes" to get name of every note' | head -c 300
```

Run that in the terminal **first** — if it works there, your Python will work too.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `Not authorized to send Apple events` | Approve the permission prompt; if you missed it, System Settings → Privacy & Security → Automation |
| Hangs forever | Notes is showing a dialog. Always pass `timeout=30` |
| Empty output | Notes has no local notes, or they're all in an unopened iCloud account |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add Apple Notes connector" && git push
```


---

## Session 5 — Notion

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

```bash
cd ~/code/fairy && uv add notion-client
```

1. Create an **internal integration** at notion.so/my-integrations
2. Copy the token into `.env` as `NOTION_TOKEN`
3. **Share the specific pages or databases with your integration** — from each page's ⋯
   menu → Connections → your integration

> ⚠️ **Step 3 is the one everybody misses.** The Notion API returns *empty results* for
> anything you haven't explicitly shared — no error, no warning, just nothing. If your
> connector returns zero items and you're sure the token is right, this is why.

Query only the databases you name in config. Do not walk the whole workspace — it's slow,
and it drags private pages into your agent's context.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -c "
import os
from notion_client import Client
c = Client(auth=os.environ['NOTION_TOKEN'])
print([r['id'] for r in c.search()['results'][:5]])
"
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| **Empty list, no error** | The classic — you didn't share any page with the integration. ⋯ menu → Connections |
| `APIResponseError: unauthorized` | Token wrong, or you copied the "internal integration secret" incorrectly |
| `object_not_found` for an id you can see | Same cause: it's not shared with the integration |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add Notion connector" && git push
```


---

## Session 6 — Gmail

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** understand OAuth by doing it once.

The fiddliest connector. Do this one when you have a clear couple of hours.

```bash
cd ~/code/fairy && uv add google-api-python-client google-auth-oauthlib
```

1. Google Cloud Console → new project → enable the **Gmail API**
2. Create **OAuth client ID** → **Desktop app** → download `credentials.json`
3. Scope: **`gmail.readonly`** and nothing more

### Understanding OAuth in one paragraph

You never give your app your Gmail password.

1. Your app opens a Google page
2. **You** log in there, and Google asks "allow this app to read your mail?"
3. On yes, Google hands your app a **token**

The token is limited to the scope you approved and revocable from your Google account.
Delegated, limited, revocable — that's OAuth.

### Where the two files go

```
~/.fairy/google_credentials.json   the client id — downloaded from Google
~/.fairy/google_token.json         your access + refresh token — written by the library
```

**Neither goes in `.env`, neither goes in git.**

| File type | Where | Why |
|---|---|---|
| Static API keys | `.env` | Set once, never change |
| OAuth tokens | `~/.fairy/*.json` | They **rotate** — your code rewrites them |

Both paths sit outside the repo entirely, which is the safest arrangement: there's no way
to accidentally `git add` them.

**Start narrow:** unread messages from the last 7 days, subject and sender only. You want
an *action summary*, not a mirror of your mailbox.

### ✔ Check yourself

The first run opens a browser for consent. After that it uses the saved token.

```bash
cd ~/code/fairy && uv run python -c "
from fairy.connectors import gmail
for i in gmail.fetch()[:5]: print(i.title)
"
```

```bash
ls -l ~/.fairy/google_token.json
```

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `redirect_uri_mismatch` | You created a *Web* client. Delete it, create a **Desktop app** client |
| `access_denied` | Your project is in testing mode — add your own email under Test users |
| `insufficient permissions` | Scope too narrow, or you changed scopes without deleting `google_token.json` |
| Browser opens every run | The token isn't being saved — check the path is writable |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add read-only Gmail connector" && git push
```


---

## Session 7 — iMessage

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

> ⚠️ **Two traps, both of which waste an afternoon if you don't know them.**

Messages live in a SQLite database — which you already know how to read:

```
~/Library/Messages/chat.db
```

**Trap 1 — Full Disk Access.** Whichever app runs your code (Terminal or VS Code) needs it:
System Settings → Privacy & Security → Full Disk Access. **Fully quit and reopen the app
afterwards** or the grant won't take effect.

**Trap 2 — do not copy the file.** Copying a TCC-protected file:
- *appears* to succeed and returns exit code 0
- silently produces an **empty database**
- fails later with `no such table: message`, which looks like a schema problem

Read it in place, read-only:

```python
conn = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
```

`?mode=ro` with `uri=True` opens read-only — you cannot corrupt your own message history
even with a buggy query.

**One more gotcha:** message timestamps are **nanoseconds since 2001-01-01**, not Unix
seconds. You have to convert, or every message will appear to be from 1970.

### ✔ Check yourself

```bash
sqlite3 "file:$HOME/Library/Messages/chat.db?mode=ro" "SELECT COUNT(*) FROM message;"
```

If that prints a number, Full Disk Access is working. If it errors, fix that before writing
any Python.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `no such table: message` | **Almost always Full Disk Access**, not a schema problem. Grant it, then fully quit and reopen the app |
| `unable to open database file` | Same — permissions |
| `authorization denied` | Same again |
| All dates are 1970 or 2001 | Apple timestamps are **nanoseconds since 2001-01-01**. Convert |
| Empty results after copying the file | You copied a TCC-protected file and got an empty one. Read it in place |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add read-only iMessage connector" && git push
```


---

## Secrets — set this up before the first real key

```
.env                      static API keys. Gitignored.
.env.example              the template, no values. Committed.
~/.fairy/*_token.json     OAuth tokens. Outside the repo entirely.
```

Install the guard **now**, before you put a real key anywhere:

```bash
brew install gitleaks
```

```bash
cd ~/code/fairy && printf '#!/bin/sh\ngitleaks protect --staged --redact -v\n' > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit && echo "hook installed"
```

Now a commit containing a key-shaped string is **blocked** instead of pushed to a public
repo. Test it deliberately:

```bash
cd ~/code/fairy && echo 'AWS_SECRET=AKIAIOSFODNN7EXAMPLE' > /tmp/fake.txt && cp /tmp/fake.txt ./fake.txt && git add fake.txt && git commit -m "test" ; rm -f fake.txt && git reset
```

It should refuse. Good — now you know the guard is real.

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "chore: add gitleaks pre-commit hook" && git push
```


---

## ✅ Stage 4 complete

**You built:** connectors to your real school and work life, all normalised into one shape.

**You learned:**

- `Protocol` — structural interfaces, no inheritance required
- **Normalising** many sources into one model
- **Splitting network from parsing** so tests stay fast and offline
- `subprocess` with list arguments and timeouts
- What **OAuth** actually is, and where tokens belong
- Secret hygiene, verified by an actual blocked commit

### Stretch exercise (optional)

Write `tests/test_connector_protocol.py` that asserts each of your connectors satisfies the
`Connector` protocol — `name` exists and `fetch()` returns `list[SourceItem]`.

Then add a deliberately broken one, watch the test catch it, and delete it. That's a
*contract test*, and it's how you stop connector number seven from quietly drifting away
from the shape everything else expects.

Historical next step: [legacy agent guide](stage-06-agent-legacy.md)
