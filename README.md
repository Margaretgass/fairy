# NeuroFairy

An ADHD aware executive functioning agent. 

Status: **Stage 1 — in progress.**

## What this is

NeuroFairy is a cute, pixlated local AI assistant that floats on your desktop (and in lives in a fairy cottage web app), helping you organize and simplify tasks, focus time, calendar, notes etc. Inspired by researched executive functioning tecniques such as body doubling, pomodoro timers, and brain dumping. 

(I formatted the build docs like a course to help strengthen my own AI and SWE skills!)

## Tech Stack (so far)
Python 3, SQLite, CSS - frontend, Ollama (Qwen2.5:3), Langchain, FastMCP

## Current Runtime Architecture
```mermaid
flowchart TD
    Person["Person using NeuroFairy"]

    subgraph Browser["Browser interface · uiux/ui/"]
        UI["index.html + app.js"]
        Prototype["Tasks, quests, focus and charms"]
        LocalStorage["Browser localStorage"]
        UI --> Prototype
        Prototype <--> LocalStorage
    end

    subgraph API["Python application · src/fairy/"]
        FastAPI["web_app.py · FastAPI"]
        Chat["neurofairy_chat.py"]
        Prompt["prompts.py"]
    end

    subgraph AI["Local AI"]
        LangChain["LangChain ChatOllama"]
        Ollama["Local Ollama service"]
        Model["qwen2.5:3b"]
    end

    Person --> UI
    UI -->|"POST /api/chat"| FastAPI
    FastAPI --> Chat
    Prompt --> Chat
    Chat --> LangChain
    LangChain --> Ollama
    Ollama --> Model
    Model -->|"reply"| UI
```


## Progress Photos - Sept 20th, 2026
<img width="1191" height="711" alt="Screenshot 2026-09-20 at 4 01 50 PM" src="https://github.com/user-attachments/assets/9322f504-aff1-4944-8e6e-a61e8d3bc243" />

<img width="805" height="391" alt="Screenshot 2026-09-20 at 4 01 16 PM" src="https://github.com/user-attachments/assets/1442e022-106a-401d-b772-69dfc9dbe6a4" />

## License

MIT
