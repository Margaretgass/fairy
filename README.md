# NeuroFairy

An ADHD aware executive functioning agent. 

Status: **Stage 1 — in progress.**

## What this is

NeuroFairy is a cute, pixlated local AI assistant that floats on your desktop (and in lives in a fairy cottage web app), helping you organize and simplify tasks, focus time, calendar, notes etc. Inspired by researched executive functioning tecniques such as body doubling, pomodoro timers, and brain dumping. 

## Tech Stack (so far)
Python 3, SQLite, CSS, Ollama (Qwen2.5:3), Langchain, FastMCP

## Architecture 
┌──────────────────────────────────────────────────────────────┐
│ Browser: existing prebuilt Fairy UI                           │
│                                                              │
│ • Chat interface                                             │
│ • Brain-dump interface or planned brain-dump interface       │
│ • Task/focus UI (current or upcoming)                        │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP requests
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI application: src/fairy/web_app.py                    │
│                                                              │
│ • Serves the frontend/static UI                              │
│ • Receives POST /api/chat                                    │
│ • Returns JSON responses for the browser                     │
│ • Future home for task, brain-dump, focus, and connector API │
└─────────────┬────────────────────────────┬───────────────────┘
              │                            │
              │ chat                       │ future deterministic
              │                            │ app services
              ▼                            ▼
┌───────────────────────────────┐  ┌──────────────────────────┐
│ neurofairy_chat.py            │  │ domain/ + services/       │
│                               │  │ connectors/ + servers/    │
│ • reply_to_user(message)      │  │                          │
│ • Builds model messages       │  │ • Tasks                  │
│ • Applies system prompt       │  │ • Focus sessions         │
└─────────────┬─────────────────┘  │ • Brain-dump storage      │
              │                    │ • Calendar permission     │
              ▼                    │   and confirmation logic  │
┌───────────────────────────────┐  └──────────────────────────┘
│ prompts.py                    │
│                               │
│ • Neurofairy voice/rules      │
│ • Concise, warm, practical    │
│ • One visible next action     │
└─────────────┬─────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────┐
│ LangChain: ChatOllama                                         │
│                                                              │
│ • Python integration layer                                   │
│ • Message formatting                                         │
│ • Later: typed tool definitions and tool-call orchestration  │
└──────────────────────────┬───────────────────────────────────┘
                           │ local HTTP
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Ollama running locally on your Mac                            │
│                                                              │
│ • qwen2.5:3b                                                  │
│ • Generates Neurofairy responses locally                      │
└──────────────────────────────────────────────────────────────┘

## Progress Photos - Sept 20th, 2026
<img width="1191" height="711" alt="Screenshot 2026-09-20 at 4 01 50 PM" src="https://github.com/user-attachments/assets/9322f504-aff1-4944-8e6e-a61e8d3bc243" />

<img width="805" height="391" alt="Screenshot 2026-09-20 at 4 01 16 PM" src="https://github.com/user-attachments/assets/1442e022-106a-401d-b772-69dfc9dbe6a4" />

## License

MIT
