# 6. API reference

Base address: `http://127.0.0.1:8000`. All bodies are JSON unless stated. Interactive documentation, generated automatically, is at `http://127.0.0.1:8000/docs` while the backend runs.

There is no login. The API is meant to be called only from the Jarvis page on the same computer (see [Security and privacy](07-SECURITY-PRIVACY.md)). Every example below was produced by running the real code.

## Health

### `GET /api/health`

```json
{ "ok": true, "brain": "offline", "model": null, "email": false, "name": "Jarvis" }
```

`brain` is `"claude"` when an API key is set. `email` is `true` when SMTP is configured.

## Talking to Jarvis

### `POST /api/command`

| Field | Type | Notes |
|---|---|---|
| `text` | string, 1 to 20,000 characters | What the user said or typed |
| `lang` | `"en"` or `"hi"` | Default `en` |
| `session` | string, up to 64 characters | Identifies one conversation (confirmations, email draft and attachments are kept per session) |

```json
{ "text": "set a timer for 5 minutes", "lang": "en", "session": "s1" }
```

Response:

```json
{
  "reply": "Timer set for 5 minutes.",
  "action": { "type": "timer", "seconds": 300, "label": "Timer finished" },
  "needs_confirm": false,
  "dictate": false
}
```

| Field | Meaning |
|---|---|
| `reply` | Text to show and speak |
| `action` | `null`, or an object with a `type` (below) |
| `needs_confirm` | `true` when Jarvis is waiting for yes or no (for example shutdown). The next message in the same session is read as the answer |
| `dictate` | `true` when the next message is a long dictated sentence (email subject or message), so the page should wait longer for pauses |

Example of a confirmation:

```json
{ "reply": "Do you really want to shut down the computer? Say yes or no.", "action": null, "needs_confirm": true, "dictate": false }
```

**Action types**

| `type` | Extra fields | The page should |
|---|---|---|
| `sleep` | | Go back to waiting |
| `opened` | `name`, `url?` | Show that a site, program or song was opened |
| `chart` | `kind` (`pie` or `bar`), `title`, `data` | Draw the chart |
| `camera` | | Open the camera panel |
| `spiral` | | Draw the pattern |
| `compose_email` | | Open the email composer |
| `files` | `files: [{name, url}]` | Show download buttons |
| `form` | `template`, `title`, `fields` | Show a form (submit it to `/api/make`) |
| `timer` | `seconds`, `label` | Start a timer |
| `mail_draft` | `draft` | Show the editable email card (send with `/api/mail/send`) |
| `rename` | `name` | Update the displayed name |
| `rag` | `sources`, `mode` | Show the sources under the answer |
| `kb_mode` | `on` | Show or hide the Document mode badge |
| `studio` | | Open the Document studio |
| `reply_options` | `options: [{label, send}]` | Show quick-answer buttons |
| `read` | | Read the reply aloud |
| `ai`, `wiki` | | Mark the answer source |

### `POST /api/name`

Body `{ "name": "Friday" }` returns `{ "name": "Friday" }`. A bad name returns status 400:

```json
{ "detail": "Pick a short name (up to 20 letters or digits)." }
```

## Files you attach

### `POST /api/upload`  (multipart form)

Fields: `file`, `session`, `lang`. Maximum 20 MB. Allowed: PDF, images, Word, Excel, PowerPoint, text and code files.

```json
{ "name": "n.txt", "kind": "text", "size": 26, "truncated": false, "reply": "Got n.txt. Tell me what to do with it." }
```

Then send commands such as `summarize it` to `/api/command` with the same `session`.

### `DELETE /api/attachments/{name}?session=...`

Removes an attached file from the session. Returns `{ "ok": true }`.

### `GET /api/files/{name}`

Downloads a file from the output folder. Returns 404 `{"detail":"File not found"}` if it does not exist. Names that contain path characters are refused.

## Making files

### `POST /api/make`

Builds a file from a template form. Body: `template`, `values` (text fields), `lang`.

Templates: `leave`, `resignation`, `invoice`, `budget`, `minutes`, `todo`, `resume`, `blank`.

```json
{ "template": "todo", "values": { "title": "Trip", "items": "Pack\nBook" }, "lang": "en" }
```

```json
{ "reply": "Done. Your file Checklist-Trip.docx is ready to download.",
  "files": [ { "name": "Checklist-Trip.docx", "url": "/api/files/Checklist-Trip.docx" } ] }
```

A missing required field returns 400, for example `{"detail":"Please fill in: To (e.g. Principal, Manager)"}`.

The `blank` template takes `title`, `body` and `format` (`docx`, `txt`, `md`, `xlsx`, `csv`, `pptx` or `html`).

### `POST /api/doc/build`

Builds a Word or PDF file from Document studio blocks.

| Field | Notes |
|---|---|
| `title`, `subtitle`, `author` | Optional text |
| `font`, `font_size` | Default Calibri, 11 (range 8 to 20) |
| `page_numbers` | Default `true` |
| `format` | `docx` or `pdf` |
| `blocks` | Up to 600 blocks, each with a `type`: `heading`, `paragraph`, `quote`, `bullets`, `numbered`, `table`, `image`, `pagebreak` |
| `lang` | `en` or `hi` |

Block fields: `text`, `level` (1 to 3), `items`, `rows`, `header`, `data` (base64 image, up to 10 MB each, 40 MB in total), `width` (10 to 100 percent), `caption`, `align` (`left`, `center`, `right`, `justify`).

```json
{ "title": "Report", "format": "docx", "blocks": [ { "type": "heading", "level": 1, "text": "Hello" } ] }
```

```json
{ "reply": "Done. Your file Report.docx is ready to download.",
  "files": [ { "name": "Report.docx", "url": "/api/files/Report.docx" } ] }
```

A PDF that contains Hindi text returns 400 with an explanation. Use `docx` for Hindi.

## Email

### `POST /api/mail/send`

Used by the editable draft card. Body: `to`, `cc`, `bcc` (lists of up to 20 addresses), `subject`, `body`, `lang`, `session`. It also clears any pending voice confirmation so a later "yes" cannot send the same email twice.

With SMTP configured it sends and replies `{ "reply": "Email sent.", "url": null }`. Without SMTP it returns a Gmail link and opens it on the computer:

```json
{ "reply": "Gmail draft opened. Press Send there to finish.",
  "url": "https://mail.google.com/mail/?view=cm&fs=1&to=a%40b.com&su=Hi&body=Hello" }
```

A bad address returns 400. A mail-server failure returns 502.

### `POST /api/email`

Simple single-recipient send. Body `to`, `subject`, `body`, `lang`. Returns 400 if SMTP is not configured.

## Chat with your documents

### `GET /api/kb`

```json
{ "embedder": "minilm", "chunks": 1,
  "sources": [ { "name": "a.txt", "chunks": 1, "origin": "upload" } ],
  "answers": "extractive" }
```

`embedder` is `minilm` (local model) or `hash` (keyword fallback). `answers` is `claude` when a key is set.

### `POST /api/kb/upload`  (multipart form)

Field `files` (up to 50 files). Returns `{ "results": [{ "name", "chunks" }], ...same fields as GET /api/kb }`.

### `POST /api/kb/folder`

Body `{ "path": "D:\\Company\\Policies" }`. Starts indexing in the background (up to 2,000 files, sub-folders included). Returns `{ "job": "<id>" }`. A path that does not exist returns 400.

### `GET /api/kb/jobs/{job_id}`

Progress of a folder job. Returns 404 for an unknown id.

```json
{ "state": "running", "done": 12, "total": 40, "current": "Policies\\leave.docx" }
```

`state` is `running`, `done` or `error` (with an `error` message). When done it also reports `indexed`, `unchanged` and `chunks`. Poll it every second or so.

### `DELETE /api/kb/source?name=...`

Removes one source from the index. Returns the same fields as `GET /api/kb`.

### `POST /api/kb/clear`

Empties the index. Returns the same fields as `GET /api/kb`.

### `POST /api/kb/mode`

Body `{ "on": true, "session": "s1" }` turns document mode on or off for that session. Returns `{ "on": true }`.

## Status codes

| Code | Meaning |
|---|---|
| 200 | Done |
| 400 | The request was understood but cannot be done (bad name, missing field, unreadable file, PDF with Hindi) |
| 404 | File or job not found |
| 422 | The request body has the wrong shape (for example an unknown block type) |
| 502 | An outside service failed (mail server) |
