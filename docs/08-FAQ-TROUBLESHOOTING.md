# 8. FAQ and troubleshooting

## Questions

**Do I need an API key or a subscription?**
No. Everything in the [command reference](COMMANDS.md) works without one. A Claude key is optional and only improves written answers.

**Does it need the internet?**
Not for most things. Needed for: weather, currency, Wikipedia answers, YouTube, Gmail, and voice recognition in Chrome (it is done by the browser vendor's service). The document-search model is downloaded once and then works offline.

**Is my data sent anywhere?**
Documents, contacts, notes and tasks stay on your computer. See [Security and privacy](07-SECURITY-PRIVACY.md) for the short list of features that contact outside services.

**Which languages?**
English and Hindi, for commands, replies, and speech. Switch with **EN / हिं**.

**Can I change the name "Jarvis"?**
Yes. Say "call yourself Friday". The wake word and replies change with it.

**Can two people use it at the same time?**
It is built for one person on one computer. See the limits in [Security and privacy](07-SECURITY-PRIVACY.md).

**Can it control any program on my computer?**
No. It opens Notepad, Calculator, Chrome and Command Prompt, websites, and plays music files from your folder.

**Why does it say "I can't write new content without AI"?**
Writing new text needs an AI model. Without a key, Jarvis fills templates and arranges the text you give it. Add a Claude key to enable writing.

**Why are document answers quotes from my files and not a written answer?**
Without an AI key the answer is built from the best matching sentences, with the source file shown. A Claude key makes it write a full answer with citations.

**Can it read scanned PDFs or photos?**
Not without a Claude key. Scanned pages have no text for it to read.

**Can the PDF files contain Hindi?**
No. Make a Word file and use Save as PDF in Word.

## Voice problems

| Problem | Fix |
|---|---|
| Nothing happens when I tap the orb | Use Chrome or Edge. Open `http://127.0.0.1:3000` (not `localhost`). Allow the microphone: click the padlock beside the address, set Microphone to Allow, reload. |
| The browser says the microphone is blocked | Same as above. Also check Windows Settings, Privacy, Microphone, and allow desktop apps. |
| It hears me but gets the words wrong | Check the language button (EN or हिं) matches what you are speaking. Speak at normal speed, closer to the microphone. |
| It cuts me off in the middle of a sentence | It waits about 1.8 seconds of silence, and longer (4.5 seconds) when dictating an email subject or message. Pause less, or type long text. |
| It answers itself or loops (hears its own voice) | Use a headset, or lower the speaker volume. Hands-free mode works best with a headset. |
| Hey Jarvis mode does not react | Say the name clearly at the start or the end of the sentence ("Hey Jarvis, ..." or "..., Jarvis"). If you renamed it, use the new name. |
| I hear no spoken replies | Check the speaker icon is on (not crossed out) and that Windows has a voice installed for the language. Hindi speech needs a Hindi voice (Windows Settings, Time and language, Speech). |

## Things that did not work as expected

| Problem | Fix |
|---|---|
| "Play believer" opens YouTube, not my folder | No music folder is saved, or you chose "skip" before. Say "set music folder to D:\Music". |
| Song search says "I couldn't find ... in your music folder" | The file name must contain the words you said. Rename the file, or say the title as it appears in the file name. Sub-folders are searched. Only `.mp3 .m4a .wav .flac .ogg .aac .wma .opus` files count. |
| The YouTube video opens but does not play | Chrome may block sound that starts without a click. Click once on the YouTube tab. |
| Email opens Gmail instead of sending | SMTP is not set. See [Configuration](04-CONFIGURATION.md#turning-on-email-sending). |
| "Could not send email: ..." | Check `SMTP_USER` and the **app password**, and that 2-step verification is on. |
| "I couldn't find that in your documents" | Nothing in your files matches. Rephrase using words that appear in the files. A request like "summarize my documents" needs a topic: "explain the leave policy". |
| "There are no documents in my library yet" | Add files or a folder in the Documents panel (book icon). |
| Weather or currency says it could not fetch | No internet, or the free service is busy. Try again later. |
| Timer did not ring | Timers live in the open page. If the page was closed or reloaded, the timer is lost. |
| Attached file: "I can't read text from ..." | It is an image or a scanned PDF. Attach a PDF with real text, Word, Excel, PowerPoint or a text file. |
| Studio PDF refuses my text | It contains Hindi. Create a Word file instead. |
| Documents panel is slow the first time | The search model (about 80 MB) is downloading once. |

## Page problems

| Problem | Fix |
|---|---|
| Header says **Offline** and nothing answers | The backend is not running. Run `start.bat`, or start it as in the [installation guide](02-INSTALLATION.md#manual-start). |
| Port 8000 or 3000 already in use | Close the other Jarvis window. Find the program with `netstat -ano \| findstr :8000`. |
| Blank page, or `i is not a function` | A build was run while the dev server was running. Stop the front end, delete `frontend\.next`, start again. |
| The page looks old after an update | Hard refresh (Ctrl+Shift+R). |
| Dark or light theme resets | Browser storage is blocked or cleared. Allow site data for `127.0.0.1`. |

## Still stuck?

Collect these three things before asking for support: what you said or typed, what Jarvis answered, and the text in the black **Jarvis backend** window. Never send your `.env` file.
