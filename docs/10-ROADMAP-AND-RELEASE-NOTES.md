# 10. Roadmap, limits and release notes

## Release notes

### Version 1.0

**Voice and screen**
- English and Hindi, by voice or typing.
- Three listening modes: Tap, Hands-free, and the "Hey Jarvis" wake word. Talk over Jarvis to interrupt it.
- Renamable assistant (wake word, title and replies follow the name).
- Light and dark themes. Works on phone-sized screens.

**Everyday help**
- Time, date, IP and MAC address, maths, unit and currency conversion, weather, jokes, coin, dice, random numbers.
- Timers and reminders, tasks, notes.
- Open websites, Notepad, Calculator, Chrome, Command Prompt. Google, YouTube and image search.
- Play songs from your own music folder (asks for the folder once and remembers it), or the first matching YouTube video.
- Pie chart, bar graph, pattern drawing, camera.

**Email by talking**
- Step-by-step spoken email: who, CC, BCC, subject, message, with "skip".
- Address book saved automatically, name search, numbered choice when a name has several addresses.
- Editable draft card, confirmation before sending, Gmail draft or direct SMTP.

**Documents**
- Form templates: leave letter, resignation letter, invoice, budget, meeting minutes, checklist, resume, and free documents in seven formats.
- **Document studio**: headings, bold and italic, lists, tables, pictures with captions, quotes and page breaks, saved as Word or PDF.
- Work on attached files: summary, key words, word count, find, read aloud, convert.
- **Chat with your documents**: ChromaDB index of uploaded files or a whole folder, answers with sources.

**Safety and quality**
- Shutdown and email always ask first.
- 84 automated tests and 193 command checks pass. See [Test results](TEST-RESULTS.md).

## Known limits

| Limit | Why | Workaround |
|---|---|---|
| Does not write new content without AI | No model is built in | Add a Claude key, or use templates and the studio |
| Cannot read scanned PDFs or photos | No text layer, no OCR | Add a Claude key, or attach a text PDF |
| Chat-with-documents answers are quoted, not rewritten | Offline mode extracts sentences | Add a Claude key |
| "Summarize my documents" needs a topic | The search is topic-based | Say "explain the leave policy" |
| No follow-up memory in document chat | Each question is searched on its own | Ask complete questions |
| Cannot stop or pause a song | The song plays in your own music player | Use the player |
| Cannot control other programs | Only a fixed list is supported | See the roadmap |
| Timers are lost if the page reloads | Timers live in the page | Keep the page open |
| Studio PDFs cannot contain Hindi | PDF font support | Create Word, then Save as PDF |
| Studio has no live page preview | Blocks are shown, not the page | Open the downloaded file to check |
| Windows only | Program launching and music use Windows features | Other systems are not tested |
| One user per computer, no login | Built as a personal assistant | Add authentication before any shared use |
| Needs Chrome or Edge for voice | Uses the browser's speech feature | Use typing in other browsers |

## Not yet tested

- A full install on a clean computer that has never had Python or Node installed.
- Speaking into a real microphone for every command (the automated checks send text).
- Spoken replies and talking over Jarvis on other computers, headsets and Windows versions.
- A real SMTP send and a real song file starting in a player.
- Scanned documents, very large folders (thousands of files) and very long documents.

## Roadmap ideas

These are suggestions, not promises.

| Idea | Value |
|---|---|
| **Open and control installed programs** (find programs from the Start Menu; ask before typing or clicking in them) | The most requested "assistant" feature |
| **Installer** (one setup file that includes Python and Node, offline model, desktop shortcut) | Makes selling and supporting much easier |
| Official weather, YouTube and speech services behind each customer's own key | Removes the main licence risks |
| Login and per-user data, HTTPS | Allows shared or hosted versions |
| Ollama or other local AI model support | Written answers with no cloud and no key |
| Built-in music player with pause and stop | "Stop the song" |
| Calendar and reminders that survive a restart | Reliable reminders |
| OCR for scanned documents | Reads scans and photos offline |
| Live page preview in the studio, PDF with Hindi | Better document writing |
| Follow-up questions in document chat | Natural conversation |
| More languages | Wider market |
