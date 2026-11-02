# 4. Configuration and administration

## Settings file

Settings live in `backend\.env` (copy it from `backend\.env.example`). The file is not shared or committed. Restart the backend after you change it.

| Setting | Default | What it does |
|---|---|---|
| `ANTHROPIC_API_KEY` | empty | Optional. Turns on Claude for open-ended questions, longer requests, attached images and written document answers. Leave empty for offline mode. |
| `JARVIS_MODEL` | `claude-haiku-5-5` | Model for quick chat (only used with a key). |
| `JARVIS_AGENT_MODEL` | `claude-sonnet-5-5` | Model for files and long requests (only used with a key). |
| `SMTP_HOST` | `smtp.gmail.com` | Mail server used to send email directly. |
| `SMTP_PORT` | `587` | Mail server port (STARTTLS). |
| `SMTP_USER` | empty | Your email address. With `SMTP_PASSWORD` it turns on direct sending. |
| `SMTP_PASSWORD` | empty | An **app password** (not your normal password). |
| `SENDER_NAME` | empty | Name printed at the end of emails ("Regards, ..."). |
| `MUSIC_DIR` | empty | Optional default music folder. Normally Jarvis asks for the folder the first time and saves it, so you can leave this empty. |
| `RAG_EMBEDDER` | `auto` | Document-search method. `auto` uses the local MiniLM model and falls back to keyword matching if it cannot be loaded. `default` forces the model. `hash` forces keyword matching (no download). |
| `OUTPUT_DIR` | `backend\outputs` | Where generated files are saved. |
| `DATA_DIR` | `backend\data` | Where contacts, notes, tasks, settings and the document index are saved. |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost,testserver` | Host names the backend answers to. Protects against DNS rebinding. Change only if you open Jarvis under another name. |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Pages allowed to call the backend. Change only if you serve the front end from another address. |

## Turning on email sending

Without these settings Jarvis opens a ready-filled Gmail draft and you press Send. To send directly:

1. In your Google account turn on 2-step verification.
2. Create an **App password** (Google account, Security, App passwords).
3. Put it in `backend\.env`:

```
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-16-letter-app-password
SENDER_NAME=Your Name
```

4. Restart the backend. The email draft card now says it will send directly. Check: open `http://127.0.0.1:8000/api/health`; it shows `"email": true`.

Never use your normal password and never share the `.env` file.

## Turning on Claude (optional)

1. Create a key at console.anthropic.com.
2. Put it in `backend\.env`: `ANTHROPIC_API_KEY=your-key`.
3. Restart the backend. The header changes from **Offline mode** to **Claude · the model name**.

Costs are billed by Anthropic to the key's owner. With a key, any message longer than six words, any message with an attached file, and requests that start with words like "write", "explain" or "translate" go to Claude. Short known commands such as "what is the time" still run locally.

## Where your data is stored

| What | Where | Notes |
|---|---|---|
| Address book | `backend\data\contacts.json` | Every email address Jarvis hears. |
| Notes | `backend\data\notes.json` | |
| Tasks | `backend\data\tasks.json` | |
| Assistant name, music folder | `backend\data\settings.json` | |
| Document index (search) | `backend\data\chroma\` | ChromaDB. Contains the text of your indexed files in small pieces. |
| Generated files | `backend\outputs\` | Word, Excel, PDF and other files Jarvis made. Never deleted automatically. |
| Search model | `C:\Users\<you>\.cache\chroma\` | Downloaded once, about 170 MB. |
| Page preferences | Browser storage | Theme, language, listening mode, voice on or off, studio draft. |

Pending timers, the conversation and attached files live in memory only and are lost when the backend stops.

## Backup and restore

Close Jarvis, then copy `backend\data`, `backend\outputs` and `backend\.env` to a safe place. To restore, copy them back before starting. Treat the backup as private: it contains your contacts and the text of your documents.

## Reset

| To reset | Do this |
|---|---|
| Notes or tasks | Say "clear my notes" or "clear my tasks". |
| Address book | Delete `backend\data\contacts.json`. |
| Assistant name and music folder | Delete `backend\data\settings.json`. |
| All indexed documents | Open the Documents panel and press **Clear all**, or delete `backend\data\chroma`. |
| Everything | Delete the whole `backend\data` folder. |
| Page preferences | Clear the site data for `127.0.0.1:3000` in the browser. |

## Limits

| Limit | Value |
|---|---|
| Size of one uploaded file | 20 MB |
| Files indexed from one folder | 2,000 |
| Studio: one picture | 10 MB (larger pictures are shrunk in the browser first) |
| Studio: all pictures together | 40 MB |
| Studio: blocks per document | 600 |
| Text read from one attached file | first 80,000 characters |
| Message length | 20,000 characters |

## Running more than one copy

Each copy needs its own `DATA_DIR`, and the ports in `start.bat` changed (and `ALLOWED_ORIGINS` updated). The page is built to call the backend at `http://127.0.0.1:8000`, so a second copy also needs `NEXT_PUBLIC_API_URL` set before the front end is built.
