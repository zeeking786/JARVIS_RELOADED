# Jarvis

Bilingual (English / Hindi) voice assistant. **Next.js** UI + **FastAPI** backend.

**Full documentation (overview, install, user guide, command list, API, security, licences, test results): [docs/README.md](docs/README.md).**

```
frontend/   Next.js 16 (React 19) — orb UI, voice in/out (Web Speech API), chart/camera/email panels
backend/    FastAPI — command router (jarvis/commands.py), sessions (engine.py), Claude/Wikipedia (brain.py)
JarvisEng.txt, JarvisHindi.txt   original scripts, kept for reference only
```

## Run

Double-click `start.bat` (first run installs everything), or manually:

```bash
cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
```bash
cd frontend && npm install && npm run dev
```

Open http://127.0.0.1:3000 in **Chrome or Edge** (voice input uses the browser's speech recognition).

## Configure (`backend/.env`, copy from `.env.example`)

- `ANTHROPIC_API_KEY` — turns on Claude for open-ended questions (otherwise Wikipedia, then Google).
- `SMTP_USER` / `SMTP_PASSWORD` — "send email" (Gmail **app password**).
- `SENDER_NAME` — optional name used to sign emails ("Regards, <name>").
- `MUSIC_DIR` — optional default music folder. Normally Jarvis asks for the folder the first time you say "play <song>" and saves it.

## Talk to it like Jarvis (wake word)

Under the orb pick how Jarvis listens:

- **Tap** — press the orb, speak once.
- **Hands-free** — keeps listening and answers everything it hears.
- **Hey Jarvis** — keeps listening quietly and only reacts when you say its name: "Hey Jarvis, good morning", "Jarvis, set a timer for 5 minutes",
  or with the name last: "Send an email, Jarvis". Say just "Jarvis" and it answers "Yes? I'm listening." After a reply it stays awake for about
  12 seconds (25 while it waits for a yes/no or email details), so you can answer without repeating the name. "Bye"/"sleep" sends it back to waiting.

The chosen mode is remembered and starts listening by itself when the page opens (Chrome asks for the microphone once; allow it for 127.0.0.1).
The name works when typed too ("Hey Jarvis what is the time").

**Rename it:** click the pencil next to the name, or say / type "change your name to Friday", "call yourself Nova", "your name is ...",
Hindi: "अपना नाम फ्राइडे रखो". The wake word, title and replies change with it (stored in `backend/data/settings.json`). Names up to 20 letters.

## Write whole documents (Document studio, no API key)

Click the pen icon (or say "open document studio", "write a report with images"). Build the document block by block: **Heading**, **Text**
(`**bold**`, `*italic*`, alignment), **Bullets**, **Numbered** lists, **Table** (add/remove rows and columns, header row), **Picture**
(any image; resized automatically, with width, alignment and caption), **Quote** and **Page break**. Move blocks up/down or delete them.
**Paste text** turns `# Heading`, `- bullets`, `1. numbers`, `| a | b |` tables, `> quotes` and `---` (page break) into blocks in one go.
The mic button on a Text block lets you dictate (Chrome/Edge; turns Hands-free off while you dictate). Pick font, size and page numbers,
then **Create file** as **Word (.docx)** or **PDF**. The draft is saved in your browser, so you can close the panel and come back.
Hindi works in Word; PDF is English/Latin only (use Word, then Save as PDF).

## Chat with your documents (RAG, no API key)

Click the book icon (Documents). Add files, or type a folder path (e.g. `D:\Company\Policies`) and press **Index folder**: every PDF, Word,
Excel, PowerPoint, text and code file inside it (sub-folders too) is split into passages and stored in a local ChromaDB (`backend/data/chroma`).
Re-indexing only reads files that changed. Then:

- switch on **Chat with my documents**, or say "chat with my documents" - every question is answered from them (commands like "open youtube" still work);
- or ask one-off: "from my documents, what is the notice period", "according to my documents ...".

Search is semantic (Chroma's local MiniLM model, ~80 MB downloaded once; works without internet afterwards and falls back to keyword
matching if it can never be downloaded) and re-ranked with exact keywords. The answer quotes the best sentences with their source files; with
`ANTHROPIC_API_KEY` set, Claude writes a proper answer from the same passages (and cites [1], [2]). Scanned PDFs and images have no text, so they are skipped.

## Commands (English / Hindi)

Open sites and apps (YouTube, Google, Gmail, Notepad, cmd, Chrome, Calculator…), time, date, IP, MAC,
YouTube / image search, play song, pie chart, bar graph, pattern, camera, send email, simple maths,
shutdown (asks for confirmation, 30 s abort window), exit/sleep. Anything else goes to Claude → Wikipedia → Google.

## Works without any API key (Offline mode)

Say or type these in English or Hindi:

- **Documents you upload** (PDF with text, Word, Excel, PowerPoint, text/code): "summarise this", "keywords", "word count",
  "find budget in the document", "read it", "convert to Word / Excel / CSV / text / PowerPoint". The summary is extractive
  (it picks the most important sentences; it does not rewrite).
- **Make files from templates:** "write a leave letter", "resignation letter", "make an invoice", "budget", "resume",
  "meeting minutes", "checklist", or "make a document / Excel sheet / slides" for your own text. A form opens, you fill it, you download the file.
- **Productivity:** "set a timer for 5 minutes", "remind me in 10 minutes to call mom" (rings while the page is open),
  "note: ...", "show my notes", "add task ...", "my tasks", "done 2". Notes and tasks are saved in `backend/data/`.
- **Info:** "weather in Delhi" (Open-Meteo), "convert 5 km to miles", "100 celsius to fahrenheit", "convert 10 usd to inr"
  (Frankfurter rates), Wikipedia answers, jokes, coin, dice, random numbers, simple maths.
- **Computer:** open sites/apps, "open github.com", "search for ...", YouTube/image search, play song, charts, camera, email, shutdown (with confirmation).

- **Email by talking:** say "send mail to Ravi" (or a full sentence such as "email Ravi saying I will be late"). Jarvis asks, step by step:
  who -> (which one, if several saved addresses match: "1 abc@gmail.com, 2 xyzabc@gmail.com", say the number or tap it) -> CC -> BCC -> subject -> message,
  then shows a draft and waits for "yes". Say "skip" for CC, BCC or subject (a skipped subject is written from your message). Anything you
  already said in the sentence is not asked again ("cc", "subject ...", "saying ..."). Every address it hears is saved in `backend/data/contacts.json`,
  so next time a name, or any part of the address, is enough. "save contact Ravi as ravi at gmail dot com", "my contacts". Without SMTP settings it
  opens a pre-filled Gmail draft in your browser (you press Send); with `SMTP_USER`/`SMTP_PASSWORD` it sends directly.

Not possible offline: writing new content, translating, reading images/scanned PDFs, free conversation.

## Type anything, upload anything (needs `ANTHROPIC_API_KEY`, optional)

- Short known commands ("open youtube", "time") run locally and instantly. Everything else, and anything
  longer than 6 words, or any message while files are attached, goes to Claude.
- Attach files with the 📎 button or drag and drop. Supported: PDF, images, Word, Excel, PowerPoint, and text/code
  files (up to 20 MB each). Then say what you want, e.g. "summarise this", "translate to Hindi", "make a table of the figures".
- Ask for anything to be made: "write a leave letter as a Word file", "make an Excel budget", "make 5 slides on solar power".
  Claude builds `.docx`, `.xlsx`, `.pptx`, `.md`, `.html`, `.csv`, code and more. A download button appears in the chat;
  files are also saved in `backend/outputs/`.
- Models: `JARVIS_MODEL` (quick chat, default Haiku) and `JARVIS_AGENT_MODEL` (files and long tasks, default Sonnet).
- Uploaded file contents are treated as data, not instructions. Without an API key, uploads are accepted but Jarvis says it needs the key.

## Add a command

Add a rule in `backend/jarvis/commands.py` (`route()`), strings in `backend/jarvis/i18n.py`, and a test in
`backend/tests/test_commands.py`. Run tests: `cd backend && .venv\Scripts\python -m pytest`.

## Security notes

- The backend binds to 127.0.0.1 and only accepts CORS from localhost:3000.
- The old scripts contain a plain-text Gmail password. Change that password and delete it from them.
