# Stage 6 — Web UI

> **By the end of this stage** your own designs run in a browser on your own backend, with
> a public link a stranger can open.

**Sessions:** 5 · **Time:** ~3 weeks

### What you'll learn

| Concept | Where |
|---|---|
| FastAPI routes and request handling | Session 1 |
| Server-side templating with Jinja2 | Session 1 |
| HTMX — interactivity without a JS framework | Session 2 |
| Returning HTML fragments instead of JSON | Session 2 |
| Demo mode and why portfolios need it | Session 4 |
| Docker and deployment | Session 5 |
| Localhost threat modelling | Session 5 |

### Setup

```bash
cd ~/code/fairy && uv add fastapi uvicorn jinja2 python-multipart
```

```bash
cd ~/code/fairy && mkdir -p src/fairy/web/static src/fairy/web/templates && touch src/fairy/web/__init__.py
```

```bash
cp ~/Desktop/adhdfairy/ADHD_Fairy_Final_Handoff/prototype/*.css ~/code/fairy/src/fairy/web/static/ && cp -r ~/code/fairy/assets ~/code/fairy/src/fairy/web/static/assets && ls ~/code/fairy/src/fairy/web/static/
```

---

## Why Jinja and HTMX, not React

Your prototype's `app.js` is already doing server-side rendering — it just does it in the
browser. Every page is a function that returns an HTML string:

```js
function questForm(q){ return `<h2>${q ? 'Your quest book' : 'A new adventure'}</h2>...` }
```

That maps **one to one** onto a Jinja template. And `render()` replacing
`document.querySelector('#main').innerHTML` is precisely what HTMX does with
`hx-target="#main"`.

So the port is: template literals become Jinja templates, and all the logic moves to
Python. **Your CSS and assets carry over untouched.** You write essentially no JavaScript —
which is what you wanted from the start.

---

## Session 1 — The app shell

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** serve one page with your real stylesheet.

`src/fairy/web/app.py`:

```python
"""The Fairy web app."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

WEB = Path(__file__).parent
app = FastAPI(title="Fairy")
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")
templates = Jinja2Templates(directory=WEB / "templates")


@app.get("/", response_class=HTMLResponse)
def today(request: Request):
    return templates.TemplateResponse(request, "today.html", {"tasks": []})
```

```bash
cd ~/code/fairy && uv run uvicorn fairy.web.app:app --reload
```

Open http://127.0.0.1:8000

### Understanding the route decorator

```python
@app.get("/", response_class=HTMLResponse)
def today(request: Request):
```

`@app.get("/")` says *"when a browser asks for `/`, call this function."* The URL path and
the HTTP method (`get`) together identify the route. This is the same decorator idea as
`@mcp.tool` from Stage 1 — you write a plain function, and the decorator wires it up.

### Understanding `def` vs `async def` here

Note it's plain `def`, not `async def`.

**FastAPI runs sync endpoints in a threadpool automatically**, so your `sqlite3` code is
perfectly safe in one and much simpler to write. Use `async def` only where it earns
something — the LLM calls from Stage 5 and HTTP calls to connectors.

This is the same lesson as Stage 5: **async is for waiting on something else.** SQLite is
local and fast; there's nothing to wait for.

### Understanding templates

`Jinja2Templates` renders an HTML file with variables substituted in. `templates/base.html`
holds the shell — sidebar, titlebar, your `<link>` tags — and every page extends it:

```html
{% extends "base.html" %}
{% block content %}
  <h1>Today</h1>
{% endblock %}
```

`{% ... %}` is logic (loops, conditionals, inheritance). `{{ ... }}` inserts a value. Those
two are 90% of Jinja.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run uvicorn fairy.web.app:app --reload
```

Open http://127.0.0.1:8000 — you should see your page **with your own cream background and
Pixelify font**, not unstyled HTML.

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/styles.css
```

`200` means static files are mounted correctly.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `TemplateNotFound: today.html` | The file isn't in `src/fairy/web/templates/` |
| Page loads but is unstyled | CSS 404 — check the `/static` mount path and your `<link href>` |
| `RuntimeError: Directory 'static' does not exist` | You didn't create it, or the path is relative to the wrong file |
| Fonts don't load | Copy the `.woff2` across too, and check the `@font-face` URL |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add FastAPI app shell serving the Fairy design" && git push
```


---

## Session 2 — Today, with HTMX

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** make it interactive without writing a JavaScript app.

Add HTMX to `base.html` — one script tag, no build step:

```html
<script src="https://unpkg.com/htmx.org@2"></script>
```

Port the `today` page from `app.js`. Your class names already match your CSS, so copy the
HTML structure and swap `${...}` for `{{ ... }}`:

```html
{% for task in tasks %}
  <div class="day-row {% if task.done %}done{% endif %}">
    <label>
      <input type="checkbox"
             hx-post="/tasks/{{ task.id }}/complete"
             hx-target="#today-list"
             {% if task.done %}checked{% endif %}>
      <span>
        <span class="eyebrow">{{ task.category.value }}</span>
        <span class="task-name">{{ task.title }}</span>
      </span>
    </label>
  </div>
{% endfor %}
```

### Understanding HTMX in one idea

Those two attributes are the entire frontend framework:

| Attribute | Meaning |
|---|---|
| `hx-post="/tasks/3/complete"` | When this is clicked, POST to that URL |
| `hx-target="#today-list"` | Replace the element with that id using whatever HTML comes back |

So your endpoint returns an **HTML fragment**, not JSON:

```python
@app.post("/tasks/{task_id}/complete", response_class=HTMLResponse)
def complete(request: Request, task_id: int):
    with store.session() as conn:
        tasks.complete_task(conn, task_id)
        return templates.TemplateResponse(
            request, "_task_list.html", {"tasks": tasks.list_tasks(conn)}
        )
```

**Why this is less work than React.** In a React app you'd return JSON, then write client
code to hold state, re-render, and handle errors. With HTMX the server sends back the new
HTML and the browser swaps it in. There is no client state to keep in sync — because there
is no client state.

The `_` prefix on `_task_list.html` is a convention for *partials* — templates meant to be
included or returned as fragments, not rendered as whole pages.

Also add the energy chooser (Low / Medium / High / Survival) and inline quick-add.

### ✔ Check yourself

Add a task, then tick its checkbox. **The row should update without the page reloading.**

Open your browser's Network tab — you'll see a POST returning **HTML**, not JSON. That's
the whole HTMX idea in one observation.

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| Nothing happens on click | HTMX script tag missing — check the console for 404 |
| Whole page replaced by a fragment | `hx-target` missing, or pointing at the wrong id |
| Returns JSON not HTML | You returned the model instead of `TemplateResponse` |
| `405 Method Not Allowed` | You wrote `@app.get` for something HTMX is POSTing to |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add Today page with HTMX task list" && git push
```


---

## Session 3 — Inbox and capture

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** the thought basket.

Capture with no decision required; triage later into Task / Quest / Someday / Note.

Keep the empty state **calm** — that was a deliberate choice in the original design docs and
it's worth honouring. No urgency badges, no red counts, no fake completion checkboxes. The
whole point of an inbox for an ADHD tool is that it doesn't nag you.

### ✔ Check yourself

Capture a thought in the Inbox, then confirm it landed and was **not** scheduled:

```bash
sqlite3 ~/.fairy/fairy.db "SELECT id, title, category FROM tasks ORDER BY id DESC LIMIT 3;"
```

Check the empty state too — delete everything and make sure it reads calmly rather than
shouting at you.

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| Capture also schedules it | Inbox items shouldn't get a date. Capture first, decide later |
| Form submits and navigates away | Missing `hx-post`, so the browser did a normal form submit |
| Unicode breaks on save | You need `python-multipart` installed for form data |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add Inbox capture and triage" && git push
```


---

## Session 4 — Demo mode ★

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** make your repo worth looking at.

**This is the most important session in the stage.** Without it a recruiter clones your
project, has no Ollama and no Gmail token, sees an empty page, and closes the tab.

```bash
cd ~/code/fairy && echo 'FAIRY_MODE=demo' >> .env.example
```

When `FAIRY_MODE=demo`:

- seed the database with **invented** tasks, a part-grown plant, a few earned charms
- use `StubProvider` instead of Ollama (Stage 5 built this)
- use `FixtureConnector` instead of real Gmail and D2L (Stage 4 built this)
- show a small banner saying it's demo data

```bash
cd ~/code/fairy && FAIRY_MODE=demo uv run uvicorn fairy.web.app:app
```

**Notice how little work this is** — because you built `StubProvider` and
`FixtureConnector` when you built their real counterparts. That's why those sessions
insisted on it. Retrofitting demo mode into a project that assumes real credentials
everywhere is genuinely painful.

⚠️ **Fixture data must be invented**, not your real life with the names changed. It's going
in a public repo.

### ✔ Check yourself

```bash
cd ~/code/fairy && FAIRY_MODE=demo uv run uvicorn fairy.web.app:app --port 8001
```

Open http://127.0.0.1:8001 — seeded tasks, a part-grown plant, a few charms, and a demo
banner. **Your real database must be untouched:**

```bash
sqlite3 ~/.fairy/fairy.db "SELECT COUNT(*) FROM tasks;"
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| **Demo data in your real database** | Serious. Demo mode must use a separate file, e.g. `/tmp/fairy-demo.db` |
| Demo mode still calls Ollama | The provider switch isn't reading `FAIRY_MODE` |
| Empty page in demo mode | The seed function never ran — call it at startup |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: add demo mode with seeded fixtures and stub provider" && git push
```


---

## Session 5 — Ship it

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** a link you can put on a résumé.

### The Dockerfile

`Dockerfile` — the web UI only. The desktop fairy stays native and local.

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev
ENV FAIRY_MODE=demo
CMD ["uv", "run", "uvicorn", "fairy.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
cd ~/code/fairy && docker build -t fairy . && docker run -p 8000:8000 fairy
```

`--frozen` means "use `uv.lock` exactly, don't re-resolve" — so the container gets the
identical versions you tested with. That's what a lockfile is *for*.

Deploy to a free tier (Fly.io or Render) **in demo mode**, and put the link at the top of
your README.

Don't try to host Ollama — no free tier has the memory. Demo mode uses `StubProvider`, so
it doesn't need one.

### Now the security work — because now it applies

Up to this point Fairy had **no network surface at all**: MCP runs over stdio. An HTTP
server changes that, and this app reads your email and messages.

| Guard | Why it matters |
|---|---|
| Bind `127.0.0.1`, never `0.0.0.0`, when running locally | Nothing else on your wifi can reach it |
| **Validate the `Host` header** against an allowlist | This is what stops **DNS rebinding** — where a web page you visit resolves its own domain to 127.0.0.1 and then makes same-origin requests to your API |
| A token in `~/.fairy/token`, sent as `X-Fairy-Token` | Other local processes can't read your data |
| Never `Access-Control-Allow-Origin: *` | Don't invite every website in |

About thirty lines as a FastAPI dependency.

**Why this wasn't in Stage 1.** It genuinely didn't apply — stdio has no port to attack.
Adding security theatre before there's a threat teaches the wrong lesson. Adding it exactly
when the threat appears is how real engineering works.

Write it up in `docs/decisions/002-localhost-api-security.md`. Being able to say *"I threat
modelled my own localhost API"* is a strong interview signal, and very few candidates can.

### ✔ Check yourself

```bash
cd ~/code/fairy && docker build -t fairy . && docker run --rm -p 8000:8000 fairy
```

Open http://127.0.0.1:8000 — the demo, running in a container with none of your data.

Then confirm the Host guard actually works:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: evil.example.com" http://127.0.0.1:8000/
```

Anything other than `200` means your allowlist is doing its job.

### ⚠ If it breaks

| Error | Cause |
|---|---|
| `uv.lock` not found in build | It's gitignored by mistake, or excluded by `.dockerignore`. It **must** be committed |
| Container starts then exits | Bound to `127.0.0.1` inside the container — must be `0.0.0.0` there |
| Works locally, blank when deployed | Demo seeding didn't run, or the platform gave you a different `$PORT` |
| Host guard blocks your own browser | Add both `127.0.0.1:8000` and `localhost:8000` to the allowlist |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: containerise web UI and add localhost request guards" && git push
```


---

## ✅ Stage 6 complete

**You built:** your design, on your backend, with a public demo link.

**You learned:**

- FastAPI routes, and when sync beats async
- **Server-side templating** with Jinja2
- **HTMX** — interactivity with no client-side state
- Returning **HTML fragments** rather than JSON
- **Demo mode** — the thing portfolio projects forget
- Docker, lockfiles, and deployment
- **Localhost threat modelling** — DNS rebinding and Host validation

### Stretch exercise (optional)

Add a `/healthz` endpoint returning `{"ok": true}` and the app version, excluded from the
token guard.

Then find out why every production web service has one: what would a deploy platform do
with it, and what happens to your Fly.io app without it? The answer changes how you think
about anything you deploy.

Next: [Stage 7 — Charms and garden](stage-7-charms.md)
