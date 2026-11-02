# 7. Security and privacy

This document says plainly what Jarvis keeps, what leaves the computer, and where the limits are.

## Summary

- Jarvis runs **on the user's own computer**. The backend and the page listen only on `127.0.0.1`, so other computers on the network cannot reach them.
- Documents, contacts, notes, tasks and the search index are stored **in a folder on that computer** (`backend\data`).
- It needs **no account and no API key**. Jarvis itself sends no usage data to anyone. The document-search database has its anonymous telemetry switched off, and `start.bat` switches off the Next.js build tool's telemetry (`NEXT_TELEMETRY_DISABLED=1`). If you start the front end by hand, run `npx next telemetry disable` once.
- Some features contact outside services by design (listed below). Each one is used only when you ask for it.
- There is **no login**. It is a single-user program. See "Limits" before putting it on a shared or public machine.

## What leaves the computer, and when

| Feature | What is sent | To whom | When |
|---|---|---|---|
| **Voice input** | Your spoken audio | The browser's speech service. Chrome uses Google's speech recognition; Edge uses Microsoft's. | Only while the microphone is listening (Tap, Hands-free or Hey Jarvis mode). Typing sends no audio. |
| **Weather** | The city name | Open-Meteo (geocoding and forecast) | When you ask for weather |
| **Currency conversion** | The two currency codes | Frankfurter | When you ask to convert money |
| **Unknown questions** | The question text | Wikipedia; if nothing is found, a Google search opens in your browser | When no other command matches and no AI key is set |
| **Play a song online** | The song name | youtube.com (the page is read to find the first video, then the video opens in your browser) | When you play from YouTube |
| **Email** | The message and addresses | Gmail (opened in your browser), or your mail server if SMTP is set | Only after you confirm |
| **Claude (optional)** | The conversation, attached files, and the passages found in your documents | Anthropic | Only if you set `ANTHROPIC_API_KEY`. Leave it empty and nothing is sent |
| **Search model download** | A request for the model file | The model host used by ChromaDB | Once, the first time you use Chat with my documents |

Everything else (documents, contacts, notes, tasks, timers, generated files, the document index, the music folder) never leaves the computer.

## What is stored

See [Configuration and administration](04-CONFIGURATION.md#where-your-data-is-stored) for the exact files. The files are **not encrypted**. Anyone who can open the Jarvis folder can read the address book and the text of indexed documents. Protect the computer (Windows account, disk encryption such as BitLocker) as you would for any other work files.

## Secrets

- The API key and the mail password live only in `backend\.env`. Jarvis never prints them, never puts them in replies and never sends them to the page.
- The page can only see whether email is on (`"email": true`) and whether Claude is on, not the values.
- Use a Gmail **app password**, never the normal password.
- Do not share or copy `.env` with a customer's installation. Each customer fills in their own.

## Safety built into the commands

| Risk | Protection |
|---|---|
| Shutting the computer down by mistake | Always asks yes or no. After yes there are 30 seconds to cancel. |
| Sending email by mistake or by a misheard sentence | Always shows the draft and asks first. The draft can be edited. A pending "yes" is cleared when the email is sent from the card, so it cannot send twice. |
| Maths input running code | Maths uses a restricted expression reader (numbers and + - * / % ** only), not `eval`. |
| Bad file names or paths when downloading | Download names are cleaned and only files inside the output folder can be fetched. |
| Hidden instructions inside documents, web pages or Wikipedia text | Text from files, tools and websites is handled as data, never as instructions to Jarvis. |
| Oversized or malformed uploads | Uploads are limited to 20 MB, pictures in the studio to 10 MB, and unreadable files are refused with a message. |
| Other websites calling the backend from your browser | The backend only accepts calls from `localhost:3000` and `127.0.0.1:3000`. |
| Programs started by commands | Only a fixed list (Notepad, Command Prompt, Chrome, Calculator) and music files from the folder you chose. No command text is run in a shell. |

## Limits you should know about

These are not bugs. They follow from the design, and matter if you plan to use Jarvis differently from "one person, one computer".

1. **No login or user separation.** Anyone who can reach port 8000 can use every endpoint. Because the program listens only on the same computer, that means anyone using that computer. Do not expose the ports to a network or the internet. If you want a shared or hosted version, add authentication and per-user storage first.
2. **The backend can read any folder you point it at.** "Index folder" reads the folder path that is typed in the Documents panel. This is the feature, and it is safe on a personal computer. It is not safe on a shared server.
3. **It can start programs and music players on the computer it runs on.** It must run on the user's own machine.
4. **Sessions are identified by an id the page makes up.** There is no protection against someone else on the same computer using the same id.
5. **Data at rest is not encrypted** (see above).
6. **Voice goes through the browser vendor.** If your customers cannot send speech to Google or Microsoft, use typing, or choose the Tap mode only when needed.
7. **Outside services can change.** Weather, currency, Wikipedia and YouTube are used without keys. They can change or stop at any time. See [Licences and compliance](09-LICENSES-AND-COMPLIANCE.md).

## Recommendations for a customer's installation

- Run it under a normal Windows account, not an administrator account.
- Keep Windows, Chrome and the Jarvis dependencies updated.
- Turn on disk encryption.
- Keep `backend\.env` readable only by the user (right-click, Properties, Security).
- Back up `backend\data` and `backend\outputs` to a private place.
- Do not put customer data in the Jarvis folder on a shared drive.

## Reporting a security problem

The seller should publish a contact address for security reports here before release: `[SECURITY CONTACT ADDRESS]`.
