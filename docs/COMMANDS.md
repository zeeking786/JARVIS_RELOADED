# Jarvis: everything you can do

Everything here works **without any API key**. Jarvis understands **English and Hindi**.
Switch language with the **EN / हिं** button at the top right.

Every reply listed below was produced by the real backend while writing this guide. The pictures are real screenshots of the running app (in `docs/images/`).

---

## 0. How to talk to Jarvis

| Way | How |
|---|---|
| **Type** | Write in the box at the bottom and press Enter (Shift+Enter = new line). |
| **Tap mode** | Tap the orb, speak, Jarvis answers. |
| **Hands-free** | Jarvis keeps listening. You can interrupt it while it is talking. |
| **Hey Jarvis (wake word)** | Say **"Hey Jarvis, good morning"** or **"Jarvis, send an email"**. It wakes up and runs the command. |
| **Rename it** | Say **"call yourself Friday"**. After that you say "Hey Friday". |
| **Drop a file** | Drag a file onto the page, or use the paperclip. |
| **Header buttons** | Pen = Document studio · Book = Documents (chat with your files) · Moon = light/dark · Speaker = voice on/off. |

![Home, light theme](images/01-home-light.png)
![Home, dark theme](images/02-home-dark.png)

---

## 1. Talk and small talk

| Say | Jarvis replies |
|---|---|
| hello / hi / hey | A greeting for the time of day |
| good morning / good afternoon / good evening / good night | "Good morning! How can I help you?" |
| how are you | "I am doing great and ready to assist you." |
| what is your name / who are you | "I am Jarvis, your voice assistant." |
| bye / goodbye / exit / sleep | "Okay, bye!" and Jarvis goes to sleep |

## 2. Time, date, computer info

| Say | Jarvis replies |
|---|---|
| what is the time | "The time is 02:20 PM." |
| what is the date | "Today is Monday, 02 November 2026." |
| what is my IP address | Your IP address |
| what is my MAC address | Your MAC address |

![Greetings, time and date](images/03-greeting-time-date.png)

## 3. Maths and conversions

| Say | Jarvis replies |
|---|---|
| what is 12 plus 30 | "The answer is 42." |
| 25 multiplied by 4 | "The answer is 100." |
| 100 divided by 8 | "The answer is 12.5." |
| convert 5 km to miles | "5 km = 3.11 miles" |
| 100 c to f | "100 c = 212 f" |
| 10 kg to pounds | "10 kg = 22.05 pounds" |
| convert 50 usd to inr | Live currency rate (needs internet) |

Maths words: plus, minus, times / multiplied by, divided by, power. Units: length, weight, volume, temperature, and 16 currencies.

![Maths and conversions](images/04-maths-and-convert.png)

## 4. Weather (needs internet, no key)

| Say | Jarvis replies |
|---|---|
| weather in Varanasi | "Varanasi, India: 28°C, partly cloudy, humidity 60%, wind 6 km/h." |
| weather | Asks "Which city?" |

![Weather](images/05-weather.png)

## 5. Timers and reminders

| Say | Jarvis replies |
|---|---|
| set a timer for 5 minutes | "Timer set for 5 minutes." |
| remind me in 10 minutes to drink water | "Okay, I will remind you to drink water in 10 minutes." |

When time is up, Jarvis shows and speaks the reminder. (Timers are lost if you reload the page.)

![Timer](images/06-timer.png)

## 6. Tasks and notes (saved on your computer)

| Say | Jarvis replies |
|---|---|
| add task buy milk | "Task added. You have 1 task(s)." |
| show my tasks | "1. [ ] buy milk  2. [ ] call ravi" |
| done 1 | "Marked done: buy milk" |
| clear my tasks | "All tasks cleared." |
| take a note meeting at 5 pm | "Noted. You have 1 note(s)." |
| show my notes | "1. meeting at 5 pm (02 Nov 14:20)" |
| clear my notes | "All notes cleared." |

![Tasks and notes](images/07-tasks-and-notes.png)

## 7. Fun

| Say | Jarvis replies |
|---|---|
| tell me a joke | A random joke |
| flip a coin | "Heads." / "Tails." |
| roll a dice | "You rolled a 6." |
| random number between 1 and 50 | "Your number is 22." |

![Fun](images/08-fun.png)

## 8. Open websites and apps

| Say | What happens |
|---|---|
| open youtube / google / gmail | Opens the site |
| open tutorialspoint / geeksforgeeks / javatpoint | Opens the site |
| open github.com (any `name.com`, `.in`, `.org` ...) | Opens that website |
| open notepad / calculator / chrome / command prompt | Starts the program |
| search for python tutorials | Google search |
| youtube videos of cricket | YouTube search |
| images of taj mahal | Google Images search |
| play believer | Plays it from **your music folder**. The first time, Jarvis asks where your songs are |
| play online believer | Plays it on YouTube |
| set music folder to D:\Music | Saves a new music folder (also: "my songs are in D:\Music") |
| where is my music folder | Tells you the saved folder |
| use youtube for songs | Always use YouTube instead of a folder |

**First time you say "play believer":** Jarvis asks "Where are your songs?". Type the folder path (for example `D:\Music`), or say it ("d colon backslash music"). It saves the folder, finds the song in it (also inside sub-folders) and starts it in your default player. Next time it plays straight away. Say "skip" to use YouTube instead. If the song is not in the folder, Jarvis tells you and searches YouTube. If several songs match, it lists them and you say the number.

![Open, search, play](images/12-open-search-play.png)

## 9. Charts and drawings

| Say | What happens |
|---|---|
| show pie chart | A pie chart appears in the page |
| show bar graph | A bar graph appears |
| make a pattern | A colourful pattern is drawn |

![Pie chart](images/09-pie-chart.png)
![Bar graph](images/10-bar-graph.png)
![Pattern](images/11-pattern.png)

## 10. Camera

| Say | What happens |
|---|---|
| take my photo / click my picture / selfie | Opens the camera panel (the browser asks for permission) |

---

## 11. Make documents from a form

Say "make / create / write" plus the document. A small form opens, you fill it in, and the file is created and ready to download.

| Say | You get |
|---|---|
| make a word document | Blank document form (Word, text, Markdown, Excel, CSV, PowerPoint, HTML) |
| make an excel sheet / powerpoint / csv | The same form, with that format chosen |
| write a leave letter | Leave application (Word) |
| write a resignation letter | Resignation letter |
| make an invoice | Invoice (Excel, with totals) |
| make a budget | Budget (Excel) |
| make meeting minutes | Meeting minutes |
| make a checklist | Checklist |
| make a resume | Resume |

![Blank document form](images/13-make-word-form.png)
![Leave letter form](images/14-leave-letter-form.png)
![Resume form](images/15-resume-form.png)

## 12. Document studio (write a whole document with pictures)

Say **"open document studio"** or **"write a report with images"**, or click the **pen** icon.
Add headings, text (bold / italic), bullets, numbered lists, tables, **pictures**, quotes and page breaks, then create a **Word** or **PDF** file. Use **Paste text** to build a whole document at once.

| Write this in Paste text | It becomes |
|---|---|
| `# Title` / `## Heading` | Headings |
| `**bold**` / `*italic*` | Bold / italic |
| `- item` | Bullets |
| `1. item` | Numbered list |
| `| a | b |` | Table |
| `> text` | Quote |
| `---` | Page break |

![Studio, empty](images/16-studio-empty.png)
![Paste text](images/17-studio-paste.png)
![Blocks made from the pasted text](images/18-studio-blocks.png)
![Word file created](images/19-studio-file-created.png)

Notes: Hindi text works in Word. PDF is English only. Files are saved in `backend/outputs/`.

## 13. Work on a file you attach

Attach a PDF (with text), Word, Excel, PowerPoint or text file, then say:

| Say | Jarvis does |
|---|---|
| summarize it | Picks the key sentences |
| key words | Lists the main words |
| word count | Words, sentences, reading time |
| find budget in the file | Shows every place the word appears |
| read it | Reads it aloud |
| convert to word / excel / csv / powerpoint / markdown / txt | Makes a new file in that format (a text file cannot become a spreadsheet) |

---

## 14. Email by talking

Say **"send an email to Ravi saying the team meeting is moved to Friday"** (or just "send an email").
Jarvis asks only for what is missing, in this order: **To → CC → BCC → Subject → Message**. (If you already said the message, it skips that question.)
Say **"skip"** for CC, BCC or Subject (it writes the subject for you).
Every address you say is saved. If a name has more than one address, Jarvis lists them and you say the number.
The draft appears in an editable card. You can change anything, then send it (or open it in Gmail if SMTP is not set up).

Say addresses like: **"ravi at gmail dot com"** (also "at the rate").

| Say | What happens |
|---|---|
| send an email | Starts the flow |
| show contacts | Lists saved contacts |
| save contact Ravi as ravi at gmail dot com | "Saved Ravi as ravi@gmail.com." |
| cancel / never mind | Stops the email |

![Contacts](images/20-contacts.png)
![Jarvis asks for CC](images/21-email-asks-cc.png)
![Email draft](images/22-email-draft.png)

## 15. Chat with your documents (RAG)

Click the **book** icon, upload files or give a **folder path**. Jarvis indexes them on your computer (ChromaDB, no key needed).

| Say | What happens |
|---|---|
| chat with my documents | Document mode ON: every question is answered from your files |
| how many days of sick leave do I get? | Answer with the sources it used |
| from my documents, what is the leave policy | One question from your files, without changing mode |
| explain the leave policy / tell me about the leave policy | A short overview of that topic from your files (say the topic; "summarize my documents" with no topic finds nothing) |
| turn off document mode / normal mode / stop chat with my documents | Back to normal |

![Documents panel](images/28-documents-panel.png)
![Chatting with documents](images/29-chat-with-documents.png)

Without an AI key, answers are **taken from your files** (extractive) with their sources. They are not rewritten in new words.

## 16. Change Jarvis's name

| Say | What happens |
|---|---|
| call yourself Friday | "Okay, from now on I am Friday. Say Hey Friday to wake me up." |
| change your name to Nova | Same |
| call yourself Jarvis | Back to the default |

You can also click the small pencil next to the name.

![Rename](images/23-rename-assistant.png)

## 17. Safety: dangerous actions always ask first

| Say | What happens |
|---|---|
| shut down the computer | "Do you really want to shut down the computer? Say yes or no." Nothing happens until you say **yes** |
| cancel shutdown | Stops a shutdown that was started |
| send the email | Always asks for confirmation before sending |

![Asks before shutdown](images/24-shutdown-asks-confirm.png)
![Cancelled](images/25-shutdown-cancelled.png)

---

## 18. Hindi examples

| बोलिए | जवाब |
|---|---|
| नमस्ते | नमस्कार! |
| समय क्या है | अभी समय है … |
| वाराणसी का मौसम | वाराणसी, भारत: 28°C, आंशिक बादल … |
| 5 मिनट का टाइमर लगाओ | 5 मिनट का टाइमर लग गया। |
| चुटकुला सुनाओ | एक चुटकुला |
| यूट्यूब खोलो | YouTube खोल रहा हूँ। |
| डॉक्यूमेंट स्टूडियो खोलो | स्टूडियो खुलता है |
| अपना नाम फ्राइडे रखो | नाम बदल जाता है |

![Hindi](images/26-hindi.png)

## 19. On a phone-sized screen

![Mobile view](images/27-mobile-view.png)

---

## What Jarvis cannot do (no AI key)

- It does not **write new content** by itself (essays, long answers). It fills templates, arranges what you type, and answers from your own files.
- Answers in "Chat with my documents" are quoted from your files, not rewritten.
- Scanned PDFs and photos have no text to read.
- PDF files from the studio cannot contain Hindi (use Word).
- It cannot yet open or control **any** installed app. Only the ones listed in section 8.

With a Claude API key in `backend/.env` (`ANTHROPIC_API_KEY=...`), open-ended questions and document answers are written in full sentences.
