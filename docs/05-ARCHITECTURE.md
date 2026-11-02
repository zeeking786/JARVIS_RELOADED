# 5. Architecture

For developers who will maintain or extend Jarvis.

## Overview

```
 Browser (Chrome / Edge)                         Your computer
┌──────────────────────────────┐   HTTP/JSON   ┌───────────────────────────────────────────┐
│ Next.js 16 + React 19 (3000) │ ────────────► │ FastAPI backend (8000)                    │
│  • orb UI, chat, panels      │               │  main.py        endpoints                 │
│  • Web Speech API: listen    │ ◄──────────── │  engine.py      sessions, order of rules  │
│    and speak                 │  reply+action │  mail / music / rag / commands / offline  │
│  • wake word, barge-in       │               │  docbuilder, documents, templates, tools  │
└──────────────────────────────┘               │  settings, i18n, brain, agent (optional)  │
                                               └───────────────┬───────────────────────────┘
                                                               │ files
                          backend/data (JSON + ChromaDB)  ·  backend/outputs (generated files)
```

The browser does all speech work (listening and speaking). The backend only sees **text**. It returns a **reply** (text to show and speak) and an optional **action** (a small JSON object telling the page to draw a chart, open a panel, start a timer and so on).

## Technology

| Layer | Technology |
|---|---|
| Front end | Next.js 16 (App Router), React 19, TypeScript, plain CSS (no UI library) |
| Speech | Browser Web Speech API (`SpeechRecognition` for input, `speechSynthesis` for output) |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Document search | ChromaDB (persistent), local MiniLM embeddings through ONNX, keyword fallback |
| Office files | python-docx, openpyxl, python-pptx, pypdf, reportlab, Pillow |
| Optional AI | Anthropic Claude (Messages API) |
| Free web data | Open-Meteo (weather), Frankfurter (currency), Wikipedia (summaries) |

## Request lifecycle

1. The page sends `POST /api/command` with `{text, lang, session}`.
2. `engine.handle()` looks up the session (an in-memory object for that browser tab).
3. The **wake word** is removed from the start or end of the text ("Hey Jarvis ...").
4. If a **yes/no confirmation** is pending (shutdown, email send), the answer is handled first.
5. The text goes through the rules in this order. The first one that answers wins:

| Order | Module | Handles |
|---|---|---|
| 1 | `mail.handle` | Email conversation, contacts ("save contact ...") |
| 2 | `music.handle` | Playing songs, music-folder questions |
| 3 | `rag.handle` | "Chat with my documents" switch, "from my documents, ..." |
| 4 | document mode | When on: `commands.route`, else `rag.answer` |
| 5 | `commands.route` | Exit, shutdown, then `offline.route`, then fixed commands |
| 6 | `offline.route` | Rename, studio, timers, tasks, notes, units, weather, fun, file commands, templates, web search |
| 7 | fallback | Claude (if a key is set), else Wikipedia, else a Google search |

6. The result `{reply, action, needs_confirm, dictate}` is returned and the page speaks and shows it.

Long requests, attached files, and requests starting with words like "write" or "explain" skip steps 5 and 6 and go straight to Claude **only when a key is set**.

## Backend modules (`backend/jarvis/`)

| File | Responsibility |
|---|---|
| `engine.py` | `Session` state (pending confirmation, history, attachments, email draft, document mode, music question) and the order above |
| `commands.py` | `Result` type, fixed commands (sites, apps, date and time, IP and MAC, maths, charts, camera, shutdown, YouTube) |
| `offline.py` | Everything that works without an API key (see table above) |
| `mail.py` | Spoken email as a step-by-step conversation, address book, spoken-address cleanup, Gmail link, SMTP send |
| `music.py` | Music folder question, file search, picking among matches, playing |
| `rag.py` | Reading files, splitting into passages, ChromaDB index, hybrid search, answers, folder indexing jobs |
| `docbuilder.py` | Studio blocks to Word or PDF |
| `documents.py` | Reading uploads (text extraction), converting files, saving generated files |
| `templates.py` | The form templates (leave, invoice, resume, ...) |
| `tools.py` | Timers parsing, tasks, notes, unit and currency conversion, weather, jokes |
| `textutils.py` | Summary, key words, word statistics, find |
| `settings.py` | `settings.json` (name, music folder), wake-word matching |
| `i18n.py` | Every user-facing string in English and Hindi. `{a}` is replaced by the assistant name |
| `brain.py`, `agent.py` | Optional Claude calls and Wikipedia lookup |
| `config.py` | Reads `.env` |

`backend/main.py` holds the HTTP endpoints only. See the [API reference](06-API-REFERENCE.md).

## Front end (`frontend/`)

| File | Responsibility |
|---|---|
| `app/page.tsx` | The whole screen: listening modes, wake word and awake window, barge-in, messages, panels, theme, language |
| `app/globals.css` | All styling (light and dark themes, panels, studio) |
| `lib/api.ts` | Typed calls to the backend and the `Action` type |
| `lib/speech.ts` | Recognition (silence timer, long pauses), speaking, stop words, echo filter |
| `lib/wake.ts` | Wake-word matching |
| `components/Panels.tsx` | Chart, camera, email draft card, forms |
| `components/DocStudio.tsx` | The document studio |
| `components/Knowledge.tsx` | The documents panel |

## Data

| Store | Format |
|---|---|
| Contacts, notes, tasks, settings | JSON files in `backend/data/` |
| Document index | ChromaDB in `backend/data/chroma/` (passages of about 900 characters with 150 overlap; ranking is 65% meaning and 35% keywords) |
| Generated files | `backend/outputs/` |
| Sessions, history, attachments, timers | Memory only |

## Design rules the code follows

- **No key needed.** Every feature has an offline path. Claude only improves answers.
- **Dangerous actions confirm.** Shutdown and sending email return `Result(on_confirm=...)`. They never run directly.
- **Two languages everywhere.** A new command needs strings for both languages in `i18n.py`.
- **Data is not instructions.** Text from files, Wikipedia or tools is treated as data.
- **Secrets stay in `.env`.** Never in code, logs or replies.

## Adding a command

1. Add a rule in `backend/jarvis/commands.py` (fixed commands) or a step in `offline.py` (anything richer). First match wins, so place it carefully.
2. Add its strings for **English and Hindi** in `backend/jarvis/i18n.py`.
3. Add a test in `backend/tests/`. Tests must replace `webbrowser.open`, `subprocess.Popen` and any file-opening function so no real program or page opens.
4. If the page must react (a panel, a chart), return an `action` and handle its `type` in `frontend/app/page.tsx` and add it to the `Action` type in `frontend/lib/api.ts`.
5. Run `cd backend && .venv\Scripts\python -m pytest` and `cd frontend && npx tsc --noEmit`.

## Testing

| What | How |
|---|---|
| Backend tests | `cd backend && .venv\Scripts\python -m pytest` (84 tests, about 10 seconds) |
| Front end types | `cd frontend && npx tsc --noEmit` |
| Full command check | See [Test results](TEST-RESULTS.md) for the 193 checks that were run |

Do not run `next build` while `next dev` is running; they share `.next`.

## Known design limits

- One user, one machine. Sessions are identified by an id the page invents. There is no login.
- Timers are kept by the page and are lost on reload.
- The backend starts programs and music players on the machine it runs on. It must therefore run on the user's own computer.
