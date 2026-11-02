# Jarvis test results

Run on 02 November 2026. **193 of 193 command checks passed**, and the **83 automated backend tests passed** (`cd backend && .venv\Scripts\python -m pytest`). The frontend type check (`npx tsc --noEmit`) is clean.

Personal details such as the IP address, MAC address and folder names were replaced with examples.

Every line below is one thing you can say or do. It was run against the real Jarvis code in a sandbox: temporary data, and no real browser tab, program, music player, shutdown or email was started. Weather and currency used the real internet.

| Area | Passed |
|---|---|
| Talk | 16 / 16 |
| Time and computer | 6 / 6 |
| Maths and conversion | 11 / 11 |
| Weather | 3 / 3 |
| Timers | 5 / 5 |
| Tasks and notes | 12 / 12 |
| Fun | 5 / 5 |
| Open, search, play online | 15 / 15 |
| Charts, drawing, camera | 5 / 5 |
| Music from your folder | 18 / 18 |
| Contacts and email | 22 / 22 |
| Make documents (forms) | 28 / 28 |
| Document studio | 6 / 6 |
| Work on an attached file | 9 / 9 |
| Chat with your documents | 13 / 13 |
| Assistant name | 8 / 8 |
| Safety | 8 / 8 |
| Anything else | 3 / 3 |
| **All** | **193 / 193** |

## Talk

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `hello` | a greeting | Good afternoon! |
| PASS | `how are you` | says it is fine | I am doing great and ready to assist you. |
| PASS | `what is your name` | says its name | I am Jarvis, your voice assistant. |
| PASS | `who are you` | says its name | I am Jarvis, your voice assistant. |
| PASS | `good morning` | greets back | Good morning! How can I help you? |
| PASS | `good afternoon` | greets back | Good afternoon! How can I help you? |
| PASS | `good evening` | greets back | Good evening! How can I help you? |
| PASS | `good night` | greets back | Good night! How can I help you? |
| PASS | `Hey Jarvis good morning` | wake word, then greets | Good morning! How can I help you? |
| PASS | `Jarvis` | wake word alone: 'I'm listening' | Yes? I'm listening. |
| PASS | `bye` | goes to sleep | [sleep] Okay, bye! |
| PASS | `goodbye` | goes to sleep | [sleep] Okay, bye! |
| PASS | `नमस्ते` | Hindi greeting | नमस्कार! |
| PASS | `सुप्रभात` | Hindi good morning | शुभ प्रभात! मैं आपकी क्या मदद करूँ? |
| PASS | `आप कैसे हैं` | Hindi how are you | मैं ठीक हूँ और आपकी सहायता के लिए तैयार हूँ। |
| PASS | `अलविदा` | Hindi bye, sleeps | [sleep] ठीक है, अलविदा! |

## Time and computer

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `what is the time` | the time | The time is 03:16 PM. |
| PASS | `what is the date` | today's date | Today is Monday, 02 November 2026. |
| PASS | `what is my ip address` | an IP address | Your IP address is 192.0.2.10. |
| PASS | `what is my mac address` | a MAC address | Your MAC address is 00:00:5e:00:53:01. |
| PASS | `समय क्या है` | Hindi time | अभी समय है 03:16 PM। |
| PASS | `आज की तारीख क्या है` | Hindi date | आज की तारीख है Monday, 02 November 2026। |

## Maths and conversion

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `what is 12 plus 30` | 42 | The answer is 42. |
| PASS | `25 multiplied by 4` | 100 | The answer is 100. |
| PASS | `100 divided by 8` | 12.5 | The answer is 12.5. |
| PASS | `what is 50 minus 8` | 42 | The answer is 42. |
| PASS | `what is 2 power 5` | 32 | The answer is 32. |
| PASS | `convert 5 km to miles` | 3.11 miles | 5 km = 3.11 miles |
| PASS | `100 c to f` | 212 f | 100 c = 212 f |
| PASS | `10 kg to pounds` | 22.05 pounds | 10 kg = 22.05 pounds |
| PASS | `convert 5 liters to gallons` | about 1.32 gallons | 5 liters = 1.32 gallons |
| PASS | `convert 50 usd to inr` | a live rate (needs internet) | 50 USD = 4,747.5 INR |
| PASS | `12 जोड़ 30` | Hindi maths: 42 | उत्तर है 42। |

## Weather

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `weather in Varanasi` | weather of Varanasi (needs internet) | Varanasi, India: 28°C, clear sky, humidity 60%, wind 6 km/h. |
| PASS | `weather` | asks which city | Which city? Say, for example: weather in Varanasi. |
| PASS | `वाराणसी का मौसम` | Hindi weather | वाराणसी, भारत: 28°C, साफ आसमान, नमी 60%, हवा 6 किमी/घंटा। |

## Timers

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `set a timer for 5 minutes` | timer of 300 seconds | [timer] Timer set for 5 minutes. |
| PASS | `remind me in 10 minutes to drink water` | reminder with label | [timer] Okay, I will remind you to drink water in 10 minutes. |
| PASS | `set an alarm for 2 minutes` | timer of 120 seconds | [timer] Timer set for 2 minutes. |
| PASS | `set a timer` | asks for how long | For how long? Say, for example: set a timer for 5 minutes. |
| PASS | `5 मिनट का टाइमर लगाओ` | Hindi timer | [timer] 5 मिनट का टाइमर लग गया। |

## Tasks and notes

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `add task buy milk` | adds task 1 | Task added. You have 1 task(s). |
| PASS | `add task call Ravi` | adds task 2 | Task added. You have 2 task(s). |
| PASS | `show my tasks` | lists both | 1. [ ] buy milk / 2. [ ] call ravi |
| PASS | `done 1` | marks task 1 done | Marked done: buy milk |
| PASS | `clear my tasks` | clears all | All tasks cleared. |
| PASS | `show my tasks` | none left | You have no tasks. |
| PASS | `take a note meeting at 5 pm` | saves a note | Noted. You have 1 note(s). |
| PASS | `show my notes` | lists the note | 1. meeting at 5 pm (02 Nov 15:16) |
| PASS | `clear my notes` | clears all | All notes cleared. |
| PASS | `नया काम जोड़ो दूध लाना` | Hindi: adds task | काम जोड़ दिया। अब 1 काम हैं। |
| PASS | `मेरे काम` | Hindi: lists tasks | 1. [ ] दूध लाना |
| PASS | `सभी काम हटाओ` | Hindi: clears tasks | सभी काम हटा दिए। |

## Fun

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `tell me a joke` | a joke | A SQL query walks into a bar, walks up to two tables and asks: can I join you? |
| PASS | `flip a coin` | heads or tails | Tails. |
| PASS | `roll a dice` | number 1-6 | You rolled a 6. |
| PASS | `random number between 1 and 50` | number 1-50 | Your number is 7. |
| PASS | `चुटकुला सुनाओ` | Hindi joke | टीचर: बताओ सबसे तेज़ क्या चलता है? छात्र: मोबाइल का डेटा, खत्म भी तेज़ होता है। |

## Open, search, play online

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `open youtube` | opens YouTube | [opened] Opening YouTube. |
| PASS | `open google` | opens Google | [opened] Opening Google. |
| PASS | `open gmail` | opens Gmail | [opened] Opening Gmail. |
| PASS | `open github.com` | opens github.com | [opened] Opening github.com. |
| PASS | `open geeksforgeeks` | opens the site | [opened] Opening GeeksforGeeks. |
| PASS | `open notepad` | starts Notepad | [opened] Opening Notepad. |
| PASS | `open calculator` | starts Calculator | [opened] Opening Calculator. |
| PASS | `open chrome` | starts Chrome | [opened] Opening Chrome. |
| PASS | `open command prompt` | starts Command Prompt | [opened] Opening Command Prompt. |
| PASS | `search for python tutorials` | Google search | [opened] Searching for python tutorials. |
| PASS | `youtube videos of cricket` | YouTube search | [opened] Searching for cricket. |
| PASS | `images of taj mahal` | Google Images | [opened] Searching for taj mahal. |
| PASS | `play online believer` | opens the video itself (starts playing) | [opened] Playing believer. |
| PASS | `यूट्यूब खोलो` | Hindi: opens YouTube | [opened] YouTube खोल रहा हूँ। |
| PASS | `play song` | asks which song | Which song should I play? Say, play song, followed by the name. |

## Charts, drawing, camera

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `show pie chart` | pie chart | [chart] Here is your pie chart. |
| PASS | `show bar graph` | bar graph | [chart] Here is your bar graph. |
| PASS | `make a pattern` | drawing | [spiral] Drawing a pattern for you. |
| PASS | `take my photo` | opens camera | [camera] Opening the camera. |
| PASS | `selfie` | opens camera | [camera] Opening the camera. |

## Music from your folder

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `play believer` | no folder saved: asks where your songs are | Where are your songs? Type the folder path, for example D:\Music. Or say skip to use YouTube instead. |
| PASS | `relative\path` | refuses a non-absolute path | I can't find the folder relative\path. Type the full path, like D:\Music, or say skip to use YouTube. |
| PASS | `D:\Music` | saves the folder and plays Believer.mp3 | [opened] Saved D:\Music as your music folder. Playing Believer. |
| PASS | `play shape of you` | next time: plays at once, no question | [opened] Playing Shape of You. |
| PASS | `play shape` | 2 matches: asks for a number | I found 2 matching songs: 1. Shape of You, 2. Shape of Water. Say the number you want. |
| PASS | `seven` | bad number: asks again | Please say a number from 1 to 2. |
| PASS | `2` | plays Shape of Water | [opened] Playing Shape of Water. |
| PASS | `play thunderstruck` | not in folder: says so and plays from YouTube | [opened] I couldn't find thunderstruck in your music folder. Playing thunderstruck. |
| PASS | `where is my music folder` | tells the saved folder | Your music folder is D:\Music. |
| PASS | `use youtube for songs` | switches to YouTube | Okay, I will play songs from YouTube. Say set music folder to use a folder again. |
| PASS | `play believer` | now goes to YouTube | [opened] Playing believer. |
| PASS | `set music folder to D:\Music` | back to the folder | Saved D:\Music as your music folder. |
| PASS | `play believer` | plays from the folder again | [opened] Playing Believer. |
| PASS | `set music folder` | asks for the path | Where are your songs? Type the folder path, for example D:\Music. Or say skip to use YouTube instead. |
| PASS | `cancel` | cancels | Okay, cancelled. |
| PASS | `गाना बजाओ shape of you` | Hindi: plays from the folder | [opened] Shape of You चला रहा हूँ। |
| PASS | `गाना बजाओ believer` | Hindi: asks where songs are | आपके गाने कहाँ हैं? फ़ोल्डर का पाथ लिखें, जैसे D:\Music। या स्किप कहें, मैं YouTube पर चला दूँगा। |
| PASS | `skip` | skip: uses YouTube and remembers | [opened] Playing believer. |

## Contacts and email

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `show contacts` | none yet | You have no saved contacts yet. Say: save contact Ravi as ravi at gmail dot com. |
| PASS | `save contact Ravi as ravi at gmail dot com` | saves it | Saved Ravi as ravi@gmail.com. |
| PASS | `save contact Ravi as ravi.k at yahoo dot com` | saves a second Ravi | Saved Ravi as ravi.k@yahoo.com. |
| PASS | `show contacts` | lists both | 1. Ravi: ravi@gmail.com / 2. Ravi: ravi.k@yahoo.com |
| PASS | `send an email to Ravi` | two Ravis: lists them and asks for a number | [reply_options] I found 2 matches for Ravi: 1. ravi@gmail.com; 2. ravi.k@yahoo.com. Say the number you want. |
| PASS | `seven` | bad number: asks again | [reply_options] Please say a number from 1 to 2. |
| PASS | `2` | picks #2, asks CC | [reply_options] Any CC? Say a name or email address, or say skip. |
| PASS | `skip` | asks BCC | [reply_options] Any BCC? Say a name or email address, or say skip. |
| PASS | `skip` | asks subject | [reply_options] What is the subject? Say skip and I will write one for you. |
| PASS | `skip` | asks the message | What should the mail to Ravi say? |
| PASS | `the meeting is moved to Friday` | builds the draft, auto subject | [asks yes/no] [mail_draft] Draft ready for Ravi <ravi.k@yahoo.com>. Shall I open it in Gmail so you can press Send? |
| PASS | `no` | does not send; cancelled | Okay, cancelled. |
| PASS | `send an email to a@b.com saying hello there` | goes straight to CC | [reply_options] Any CC? Say a name or email address, or say skip. |
| PASS | `cancel` | cancels the email | Okay, cancelled. |
| PASS | `send an email to sam at example dot com` | spoken address understood, asks CC | [reply_options] Any CC? Say a name or email address, or say skip. |
| PASS | `sam at example dot com` | CC to the same address is accepted | [reply_options] Any BCC? Say a name or email address, or say skip. |
| PASS | `skip` | asks subject | [reply_options] What is the subject? Say skip and I will write one for you. |
| PASS | `holiday plan` | subject accepted, asks the message | What should the mail to sam@example.com say? |
| PASS | `regarding holiday from 16 November to 27 November 2026` | the whole long sentence reaches the draft | [asks yes/no] [mail_draft] Draft ready for sam@example.com. Shall I open it in Gmail so you can press Send? |
| PASS | `send mail` | asks who to send to | Who should I send it to? Say a name or an email address. |
| PASS | `cancel` | cancels | Okay, cancelled. |
| PASS | `ईमेल भेजो ravi@gmail.com को` | Hindi email flow starts | [reply_options] कोई CC? नाम या ईमेल पता बोलें, या कहें स्किप। |

## Make documents (forms)

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `make a word document` | opens the blank form | [form] Type the title and content, and I will make the file. |
| PASS | `make an excel sheet` | opens the blank form | [form] Type the title and content, and I will make the file. |
| PASS | `make a powerpoint` | opens the blank form | [form] Type the title and content, and I will make the file. |
| PASS | `write a leave letter` | opens the leave form | [form] Fill in the details for your leave application. |
| PASS | `write a resignation letter` | opens the resignation form | [form] Fill in the details for your resignation letter. |
| PASS | `make an invoice` | opens the invoice form | [form] Fill in the details for your invoice (excel). |
| PASS | `make a budget` | opens the budget form | [form] Fill in the details for your budget (excel). |
| PASS | `make meeting minutes` | opens the minutes form | [form] Fill in the details for your meeting minutes. |
| PASS | `make a checklist` | opens the todo form | [form] Fill in the details for your checklist. |
| PASS | `make a resume` | opens the resume form | [form] Fill in the details for your resume. |
| PASS | `make a word document` | format preset to docx | [form] Type the title and content, and I will make the file. |
| PASS | `make an excel sheet` | format preset to xlsx | [form] Type the title and content, and I will make the file. |
| PASS | `make a powerpoint` | format preset to pptx | [form] Type the title and content, and I will make the file. |
| PASS | `छुट्टी का आवेदन बनाओ` | Hindi: leave form | [form] छुट्टी का आवेदन के विवरण भरें। |
| PASS | `[fill the leave form and press Create]` | a real file is created | Leave-application-Asha.docx |
| PASS | `[fill the resignation form and press Create]` | a real file is created | Resignation-Asha.docx |
| PASS | `[fill the invoice form and press Create]` | a real file is created | Invoice-INV-1.xlsx |
| PASS | `[fill the budget form and press Create]` | a real file is created | Budget-Monthly.xlsx |
| PASS | `[fill the minutes form and press Create]` | a real file is created | Minutes-Weekly.docx |
| PASS | `[fill the todo form and press Create]` | a real file is created | Checklist-Trip.docx |
| PASS | `[fill the resume form and press Create]` | a real file is created | Resume-Asha.docx |
| PASS | `[blank document as .docx]` | a .docx file is created | Test.docx |
| PASS | `[blank document as .xlsx]` | a .xlsx file is created | Test.xlsx |
| PASS | `[blank document as .pptx]` | a .pptx file is created | Test.pptx |
| PASS | `[blank document as .csv]` | a .csv file is created | Test.csv |
| PASS | `[blank document as .txt]` | a .txt file is created | Test.txt |
| PASS | `[blank document as .md]` | a .md file is created | Test.md |
| PASS | `[blank document as .html]` | a .html file is created | Test.html |

## Document studio

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `open document studio` | opens the studio | [studio] Opening the document studio. Add headings, text, tables and pictures, then create a Word or PDF file. |
| PASS | `write a report with images` | opens the studio | [studio] Opening the document studio. Add headings, text, tables and pictures, then create a Word or PDF file. |
| PASS | `डॉक्यूमेंट स्टूडियो खोलो` | Hindi: opens the studio | [studio] डॉक्यूमेंट स्टूडियो खोल रहा हूँ। हेडिंग, टेक्स्ट, टेबल और तस्वीरें जोड़ें, फिर Word या PDF फ़ाइल बनाएँ। |
| PASS | `[studio: headings, bold, lists, table, picture, quote, page break -> docx]` | a .docx file you can download | Studio-test.docx |
| PASS | `[studio: headings, bold, lists, table, picture, quote, page break -> pdf]` | a .pdf file you can download | Studio-test.pdf |
| PASS | `[studio: Hindi text to PDF]` | refused with a clear message | {"detail":"Hindi text cannot be written to PDF here. Create the Word file, then use Save as PDF in W |

## Work on an attached file

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `[attach notes.txt]` | file accepted | {"name":"notes.txt","kind":"text","size":214,"truncated":false,"reply":"Got notes.txt. Tell me what  |
| PASS | `summarize it` | key sentences | Summary of notes.txt (key sentences picked from the text): / • Jarvis is a voice assistant. / • It can make documents, send email and play songs. / •  |
| PASS | `key words` | lists key words | Key words: assistant, budget, jarvis, voice, works, english, hindi, make |
| PASS | `word count` | words and sentences | notes.txt: 39 words, 6 sentences, about 1 min to read. |
| PASS | `find budget in the file` | finds 'budget' twice | Found “budget” 2 time(s) in notes.txt: / • …documents, send email and play songs. The assistant needs no API key. Budget planning is done every month. |
| PASS | `read it` | reads aloud | [read] Jarvis is a voice assistant. It works in English and Hindi. It can make documents, send email and play songs. The assistant needs no API key. B |
| PASS | `convert to word` | makes notes.docx | [files] Converted to DOCX: notes.docx |
| PASS | `convert to excel` | text file cannot become a spreadsheet: says so clearly | I can't do that conversion: Only CSV or Excel files can become spreadsheets. |
| PASS | `convert to markdown` | makes notes.md | [files] Converted to MD: notes.md |

## Chat with your documents

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `chat with my documents` | mode on, library empty hint | [kb_mode] Document mode is on. Ask me anything about your documents. There are no documents in my library yet. Open the Documents panel to add files o |
| PASS | `[upload Leave-Policy.txt in the Documents panel]` | indexed | [{"name": "Leave-Policy.txt", "chunks": 1, "origin": "upload"}] |
| PASS | `how many days of sick leave do I get?` | answers 10 days with a source | [rag] From your documents: / - Employees get 10 days of paid sick leave per year. [1] |
| PASS | `can I carry forward unused leave?` | answers 8 days | [rag] From your documents: / - Up to 8 unused annual leave days can be carried forward. [1] / - Sick leave cannot be carried forward. [1] |
| PASS | `explain the leave policy` | overview of the topic | [rag] Here is an overview from your documents: / - Leave-Policy.txt: Every employee gets 24 days of paid annual leave each year. Employees get 10 days |
| PASS | `what is the time` | normal commands still work | The time is 03:16 PM. |
| PASS | `turn off document mode` | mode off | [kb_mode] Document mode is off. |
| PASS | `from my documents, how many days of annual leave` | one-off question answered | [rag] From your documents: / - Every employee gets 24 days of paid annual leave each year. [1] / - Employees get 10 days of paid sick leave per year.  |
| PASS | `chat with my documents` | mode on again | [kb_mode] Document mode is on. Ask me anything about your documents. |
| PASS | `normal mode` | mode off | [kb_mode] Document mode is off. |
| PASS | `chat with my documents` | mode on again | [kb_mode] Document mode is on. Ask me anything about your documents. |
| PASS | `stop chat with my documents` | mode off | [kb_mode] Document mode is off. |
| PASS | `मेरे दस्तावेज़ों से कितनी बीमारी की छुट्टी मिलती है` | Hindi one-off question | यह जानकारी मुझे आपके दस्तावेज़ों में नहीं मिली। |

## Assistant name

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `call yourself Friday` | renamed to Friday | [rename] Okay, from now on I am Friday. Say Hey Friday to wake me up. |
| PASS | `Hey Friday what is the time` | new name wakes it | The time is 03:16 PM. |
| PASS | `Hey Jarvis what is the time` | old name no longer a wake word (still answers the time) | The time is 03:16 PM. |
| PASS | `change your name to Nova` | renamed to Nova | [rename] Okay, from now on I am Nova. Say Hey Nova to wake me up. |
| PASS | `call yourself Jarvis` | back to Jarvis | [rename] Okay, from now on I am Jarvis. Say Hey Jarvis to wake me up. |
| PASS | `call yourself a very very very long name that is not allowed` | too long: refused | That name won't work. Pick a short name, up to 20 letters or digits. |
| PASS | `अपना नाम फ्राइडे रखो` | Hindi rename | [rename] ठीक है, अब से मेरा नाम फ्राइडे है। मुझे जगाने के लिए कहें: हे फ्राइडे। |
| PASS | `call yourself Jarvis` | back to Jarvis | [rename] Okay, from now on I am Jarvis. Say Hey Jarvis to wake me up. |

## Safety

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `shut down the computer` | asks yes/no, does nothing yet | [asks yes/no] Do you really want to shut down the computer? Say yes or no. |
| PASS | `no` | cancelled, nothing ran | Okay, cancelled. |
| PASS | `shut down the computer` | asks again | [asks yes/no] Do you really want to shut down the computer? Say yes or no. |
| PASS | `yes` | only now it starts the 30 s shutdown | [sleep] Shutting down in 30 seconds. Say cancel shutdown to stop it. |
| PASS | `cancel shutdown` | stops it | Shutdown cancelled. |
| PASS | `शटडाउन` | Hindi: asks yes/no | [asks yes/no] क्या आप सच में कंप्यूटर बंद करना चाहते हैं? हाँ या नहीं कहिए। |
| PASS | `नहीं` | Hindi: cancelled | ठीक है, रद्द कर दिया। |
| PASS | `send mail to a@b.com` | never sends without asking: flow asks first | [reply_options] Any CC? Say a name or email address, or say skip. |

## Anything else

| Result | You say / do | Expected | What Jarvis answered |
|---|---|---|---|
| PASS | `who is the president of france` | no AI key: looks it up on Wikipedia | [wiki] According to Wikipedia: Wikipedia says something about it. |
| PASS | `write an essay about rivers` | no AI key: says it needs AI | I can't write new content without AI, but I can fill templates (leave letter, resignation, invoice, budget, resume, minutes, checklist) or make a file |
| PASS | `asdf qwer zxcv` | unknown: falls back to Google | [opened] I could not find that, so I searched Google. |

## Not covered by these tests

- Speaking into a microphone, the spoken answers (text to speech), barge-in and wake-word listening: these need a real microphone and speakers.
- Sending a real email (SMTP is not set up here; Jarvis opens a Gmail draft instead).
- A real song file starting in your music player (the check confirms Jarvis picks the right file and starts it).
- YouTube autoplay in your own Chrome (Jarvis opens the first video; Chrome may still ask for one click before sound).
- Answers written by an AI (Claude): no key is set, so these use the built-in offline answers.

## Problems found and fixed while testing

- Hindi: `गाना बजाओ shape of you` left a stray letter in the song name. Fixed, with a regression test.
- The guide said "convert to PDF" was possible for an attached file. It is not: attached files convert to Word, Excel, CSV, PowerPoint, Markdown and text (a text file cannot become a spreadsheet). The guide is corrected.
