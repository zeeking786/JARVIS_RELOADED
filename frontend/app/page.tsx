"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { matchWake } from "@/lib/wake";
import { BASE, getHealth, removeAttachment, sendCommand, setAssistantName, uploadFile, type Action, type Health, type Lang } from "@/lib/api";
import { createRecognition, isEcho, recognitionSupported, speak, STOP_WORDS, stopSpeaking } from "@/lib/speech";
import { Camera, Chart, EmailForm, FormPanel, MailCard, Spiral } from "@/components/Panels";
import { KnowledgePanel } from "@/components/Knowledge";
import { DocStudio } from "@/components/DocStudio";

type Status = "idle" | "listening" | "thinking" | "speaking";
type Mode = "tap" | "hands" | "wake";
const AWAKE_MS = 12000; // after "Hey Jarvis" the next sentence needs no wake word for this long
const AWAKE_LONG_MS = 25000; // longer while Jarvis is waiting for an answer (yes/no, which one, email details)
interface Message {
  id: number;
  who: "you" | "jarvis";
  text: string;
  note?: string;
  files?: { name: string; url: string }[];
  sources?: { n: number; name: string; snippet: string }[];
}

const UI: Record<Lang, Record<string, string>> = {
  en: {
    idle: "Tap the orb and speak",
    listening: "Listening…",
    thinking: "Thinking…",
    speaking: "Speaking…",
    placeholder: "Type anything, or attach a file… (Shift+Enter for a new line)",
    attach: "Attach files",
    drop: "Drop files to attach",
    voice: "Voice replies",
    offline: "Offline mode",
    timerDone: "Time is up",
    handsfree: "Hands-free",
    modeTap: "Tap",
    modeWake: "Hey {n}",
    waiting: "Say “Hey {n}”…",
    wakeAck: "Yes? I'm listening.",
    renameTip: "Rename your assistant",
    renamed: "Okay, from now on I am {n}.",
    listeningMode: "Listening mode",
    docs: "Documents",
    studio: "Document studio",
    docMode: "Document mode",
    yes: "Yes",
    no: "No",
    hello: "What shall we do today?",
    helloSub: "Speak, type, or drop a file anywhere on the page.",
    backendDown: "Backend offline — start it with: uvicorn main:app --port 8000",
    nomic: "Voice input needs Chrome or Edge. You can still type commands.",
  },
  hi: {
    idle: "ऑर्ब दबाएँ और बोलें",
    listening: "सुन रहा हूँ…",
    thinking: "सोच रहा हूँ…",
    speaking: "बोल रहा हूँ…",
    placeholder: "कुछ भी लिखें, या फ़ाइल जोड़ें… (नई पंक्ति: Shift+Enter)",
    attach: "फ़ाइल जोड़ें",
    drop: "फ़ाइलें यहाँ छोड़ें",
    voice: "बोलकर जवाब",
    offline: "ऑफ़लाइन मोड",
    timerDone: "समय पूरा हुआ",
    handsfree: "हैंड्स-फ्री",
    modeTap: "टैप",
    modeWake: "हे {n}",
    waiting: "कहें “हे {n}”…",
    wakeAck: "जी, बोलिए।",
    renameTip: "असिस्टेंट का नाम बदलें",
    renamed: "ठीक है, अब से मेरा नाम {n} है।",
    listeningMode: "सुनने का तरीका",
    docs: "दस्तावेज़",
    studio: "डॉक्यूमेंट स्टूडियो",
    docMode: "दस्तावेज़ मोड",
    yes: "हाँ",
    no: "नहीं",
    hello: "आज क्या करना है?",
    helloSub: "बोलें, लिखें, या कोई फ़ाइल पेज पर छोड़ दें।",
    backendDown: "बैकएंड बंद है — चलाएँ: uvicorn main:app --port 8000",
    nomic: "वॉइस के लिए Chrome या Edge चाहिए। आप टाइप भी कर सकते हैं।",
  },
};

const SUGGEST: Record<Lang, string[]> = {
  en: ["Write a leave letter", "Set a timer for 5 minutes", "Weather in Delhi", "Convert 5 km to miles", "Note: call mom", "Make an invoice", "Tell me a joke"],
  hi: ["छुट्टी का आवेदन बनाओ", "5 मिनट का टाइमर लगाओ", "दिल्ली का मौसम", "नोट करो दूध लाना", "इनवॉइस बनाओ", "कोई चुटकुला सुनाओ"],
};

const Svg = ({ children }: { children: React.ReactNode }) => (
  <svg viewBox="0 0 24 24" aria-hidden="true">{children}</svg>
);
const IconSound = () => <Svg><path d="M4 9v6h4l5 4V5L8 9H4z" /><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12" /></Svg>;
const IconMute = () => <Svg><path d="M4 9v6h4l5 4V5L8 9H4z" /><path d="M17 9l5 6M22 9l-5 6" /></Svg>;
const IconClip = () => <Svg><path d="M20 11.5l-8 8a5 5 0 0 1-7-7l9-9a3.5 3.5 0 0 1 5 5l-9 9a2 2 0 0 1-3-3l8-8" /></Svg>;
const IconSend = () => <Svg><path d="M12 19V5M5 12l7-7 7 7" /></Svg>;
const IconSun = () => <Svg><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></Svg>;
const IconMoon = () => <Svg><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" /></Svg>;
const IconEdit = () => <Svg><path d="M4 20h4L19 9l-4-4L4 16v4zM13.5 6.5l4 4" /></Svg>;
const IconPen = () => <Svg><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" /></Svg>;
const IconBook = () => <Svg><path d="M4 5a2 2 0 0 1 2-2h13v15H6a2 2 0 0 0-2 2V5zM4 20a2 2 0 0 0 2 2h13v-4" /><path d="M9 8h6M9 12h6" /></Svg>;
const IconDown = () => <Svg><path d="M12 4v12M6 11l6 6 6-6M5 20h14" /></Svg>;

export default function Home() {
  const [lang, setLang] = useState<Lang>("en");
  const [status, setStatus] = useState<Status>("idle");
  const [messages, setMessages] = useState<Message[]>([]);
  const [interim, setInterim] = useState("");
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<Mode>("tap");
  const [showKb, setShowKb] = useState(false);
  const [showStudio, setShowStudio] = useState(false);
  const [kbOn, setKbOn] = useState(false);
  const [name, setName] = useState("Jarvis");
  const [awake, setAwake] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [dark, setDark] = useState(false);
  const [panel, setPanel] = useState<Action | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [quick, setQuick] = useState<{ label: string; send: string }[]>([]);
  const [health, setHealth] = useState<Health | null | "down">(null);
  const [micOk, setMicOk] = useState(true);
  const [error, setError] = useState("");
  const [files, setFiles] = useState<{ name: string }[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [voiceOn, setVoiceOn] = useState(true);
  const fileInput = useRef<HTMLInputElement>(null);
  const voiceOnRef = useRef(true);
  const timers = useRef<number[]>([]);

  const recRef = useRef<ReturnType<typeof createRecognition> | null>(null);
  const langRef = useRef(lang);
  const handsFreeRef = useRef(false);
  const wakeRef = useRef(false);
  const nameRef = useRef("Jarvis");
  const awakeUntil = useRef(0); // epoch ms; 0 = asleep
  const longAwake = useRef(false);
  const dictateRef = useRef(false); // next utterance is a subject/message: tolerate long pauses
  const speakingRef = useRef(false);
  const spokenRef = useRef(""); // what Jarvis is saying right now (to recognise its own voice)
  const session = useRef("");
  const nextId = useRef(1);
  const logEnd = useRef<HTMLDivElement>(null);
  const startListeningRef = useRef<(barge?: boolean) => void>(() => {});

  langRef.current = lang;
  handsFreeRef.current = mode !== "tap";
  wakeRef.current = mode === "wake";
  nameRef.current = name;
  voiceOnRef.current = voiceOn;
  const ui = UI[lang];

  useEffect(() => {
    session.current = crypto.randomUUID();
    setMicOk(recognitionSupported());
    setDark(document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
    const saved = localStorage.getItem("jarvis-lang");
    if (saved === "en" || saved === "hi") setLang(saved);
    if (localStorage.getItem("jarvis-voice") === "off") setVoiceOn(false);
    getHealth()
      .then((h) => {
        setHealth(h);
        if (h.name) setName(h.name);
      })
      .catch(() => setHealth("down"));
    const savedMode = localStorage.getItem("jarvis-mode");
    let boot = 0;
    if ((savedMode === "hands" || savedMode === "wake") && recognitionSupported()) {
      setMode(savedMode);
      handsFreeRef.current = true;
      wakeRef.current = savedMode === "wake";
      boot = window.setTimeout(() => startListeningRef.current(), 700); // start listening on its own
    }
    window.speechSynthesis?.getVoices(); // warm up the voice list
    const pending = timers.current;
    return () => {
      clearTimeout(boot);
      pending.forEach((id) => clearTimeout(id));
    };
  }, []);

  useEffect(() => {
    document.title = name;
  }, [name]);

  // The "awake" window closes by itself a few seconds after the last exchange.
  useEffect(() => {
    const id = window.setInterval(() => {
      if (awakeUntil.current && Date.now() > awakeUntil.current) {
        awakeUntil.current = 0;
        setAwake(false);
      }
    }, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    logEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const add = useCallback((who: Message["who"], text: string, note?: string) => {
    setMessages((m) => [...m, { id: nextId.current++, who, text, note }]);
  }, []);

  const finishSpeaking = useCallback(() => {
    speakingRef.current = false;
    setStatus("idle");
    if (wakeRef.current && awakeUntil.current) {
      awakeUntil.current = Date.now() + (longAwake.current ? AWAKE_LONG_MS : AWAKE_MS);
      setAwake(true);
    }
    if (handsFreeRef.current) {
      if (recRef.current) setStatus("listening"); // already listening (it was open while Jarvis spoke)
      else startListeningRef.current();
    }
  }, []);

  const say = useCallback(
    (text: string) => {
      if (!voiceOnRef.current) return finishSpeaking();
      setStatus("speaking");
      speakingRef.current = true;
      spokenRef.current = text;
      speak(text.length > 1200 ? text.slice(0, 1200) : text, langRef.current, finishSpeaking);
      if (handsFreeRef.current && recognitionSupported()) startListeningRef.current(true); // barge-in: listen while speaking
    },
    [finishSpeaking],
  );

  const run = useCallback(
    async (text: string) => {
      const clean = text.trim();
      if (!clean) return;
      setInterim("");
      setError("");
      setQuick([]);
      add("you", clean);
      setStatus("thinking");
      try {
        const res = await sendCommand(clean, langRef.current, session.current);
        dictateRef.current = !!res.dictate;
        const a = res.action;
        setMessages((m) => [
          ...m,
          {
            id: nextId.current++,
            who: "jarvis",
            text: res.reply,
            note: a?.type === "opened" ? `↗ ${a.name}` : a?.type === "ai" ? "Claude" : a?.type === "rag" ? (a.mode === "claude" ? "Claude · your documents" : "your documents") : undefined,
            files: a?.type === "files" ? a.files : undefined,
            sources: a?.type === "rag" ? a.sources : undefined,
          },
        ]);
        setConfirming(res.needs_confirm);
        setQuick(a?.type === "reply_options" ? a.options : []);
        longAwake.current = res.needs_confirm || a?.type === "reply_options" || a?.type === "mail_draft";
        if (a?.type === "rename") setName(a.name);
        if (a?.type === "kb_mode") setKbOn(a.on);
        if (a?.type === "studio") setShowStudio(true);
        if (a?.type === "sleep") {
          if (wakeRef.current) {
            awakeUntil.current = 0; // back to waiting for the wake word
            setAwake(false);
          } else {
            setMode("tap");
            localStorage.setItem("jarvis-mode", "tap");
          }
        }
        setPanel(a && ["chart", "camera", "spiral", "compose_email", "form", "mail_draft"].includes(a.type) ? a : null);
        if (a?.type === "timer") {
          const label = a.label;
          const id = window.setTimeout(() => {
            const msg = `⏰ ${label}`;
            add("jarvis", msg);
            say(label || ui.timerDone);
          }, a.seconds * 1000);
          timers.current.push(id);
        }
        say(res.reply);
      } catch {
        setHealth("down");
        add("jarvis", ui.backendDown);
        setStatus("idle");
      }
    },
    [add, say, ui.backendDown, ui.timerDone],
  );

  const startListening = useCallback((barge = false) => {
    if (!recognitionSupported()) return;
    if (!barge) {
      stopSpeaking();
      speakingRef.current = false;
    }
    const old = recRef.current;
    recRef.current = null; // detach first so the old session's onEnd is ignored
    old?.abort?.();
    let gotFinal = false;
    const rec = createRecognition(langRef.current, {
      onInterim: (t) => {
        if (speakingRef.current) return; // mostly our own voice while Jarvis is talking
        // In wake-word mode, don't show what is said until it is addressed to the assistant.
        if (!wakeRef.current || awakeUntil.current > Date.now() || matchWake(t, nameRef.current).matched) setInterim(t);
      },
      onFinal: (t) => {
        if (recRef.current !== rec) return; // superseded or cancelled
        if (speakingRef.current) {
          if (isEcho(t, spokenRef.current)) return; // that was Jarvis itself coming out of the speakers
          stopSpeaking(); // the user is talking over Jarvis: be quiet and listen
          speakingRef.current = false;
          setStatus("listening");
          if (STOP_WORDS.test(t)) return; // "stop" only silences; nothing to run
        }
        if (!wakeRef.current) {
          gotFinal = true;
          run(t);
          return;
        }
        const w = matchWake(t, nameRef.current);
        const inConversation = awakeUntil.current > Date.now();
        if (!w.matched && !inConversation) return; // not for us: ignore, keep listening
        gotFinal = true;
        awakeUntil.current = Date.now() + AWAKE_MS;
        setAwake(true);
        const command = w.matched ? w.rest : t;
        if (command) {
          run(command);
        } else {
          add("you", t);
          add("jarvis", ui.wakeAck);
          say(ui.wakeAck);
        }
      },
      onEnd: () => {
        if (recRef.current !== rec) return; // superseded or cancelled
        setInterim("");
        // If something was heard, run() owns the status. Otherwise, in hands-free
        // mode restart quietly (stay "listening"); else go idle.
        if (gotFinal) return;
        if (handsFreeRef.current) {
          setTimeout(() => {
            if (recRef.current === rec && handsFreeRef.current) startListeningRef.current(speakingRef.current);
          }, wakeRef.current ? 250 : 400);
        } else {
          setStatus("idle");
        }
      },
      onError: (code) => {
        if (code === "not-allowed" || code === "service-not-allowed") {
          setError("Microphone permission was blocked. Allow it in the address bar and try again.");
          setMode("tap");
          localStorage.setItem("jarvis-mode", "tap");
        } else if (code !== "no-speech" && code !== "aborted") {
          setError(`Speech recognition error: ${code}`);
        }
      },
    }, () => (dictateRef.current ? 4500 : 1800));
    recRef.current = rec;
    try {
      rec.start();
      if (!barge) setStatus("listening");
    } catch {
      /* already started */
    }
  }, [run, add, say, ui.wakeAck]);
  startListeningRef.current = startListening;

  const onOrb = () => {
    if (status === "listening") {
      recRef.current?.stop(); // finish and send what was heard
      setStatus("idle");
    } else if (status === "speaking") {
      stopSpeaking();
      setStatus("idle");
    } else {
      if (wakeRef.current) {
        awakeUntil.current = Date.now() + AWAKE_MS; // tapping the orb is the same as saying the wake word
        setAwake(true);
      }
      startListening();
    }
  };

  const chooseLang = (l: Lang) => {
    setLang(l);
    localStorage.setItem("jarvis-lang", l);
    const r = recRef.current;
    recRef.current = null;
    r?.abort?.();
    stopSpeaking();
    setStatus("idle");
  };

  const chooseMode = (next: Mode) => {
    setMode(next);
    handsFreeRef.current = next !== "tap";
    wakeRef.current = next === "wake";
    awakeUntil.current = 0;
    setAwake(false);
    localStorage.setItem("jarvis-mode", next);
    if (next !== "tap" && (status === "idle" || status === "listening")) startListening();
    if (next === "tap") {
      const r = recRef.current;
      recRef.current = null;
      r?.abort?.();
      setStatus("idle");
    }
  };

  const saveName = async () => {
    const v = draft.trim();
    setEditing(false);
    if (!v || v === name) return;
    try {
      const r = await setAssistantName(v);
      setName(r.name);
      add("jarvis", ui.renamed.replace("{n}", r.name));
    } catch (ex) {
      setError(ex instanceof Error ? ex.message : String(ex));
    }
  };

  const attach = async (list: FileList | File[]) => {
    setError("");
    setUploading(true);
    for (const f of Array.from(list)) {
      try {
        const r = await uploadFile(f, langRef.current, session.current);
        setFiles((cur) => [...cur.filter((x) => x.name !== r.name), { name: r.name }]);
        add("jarvis", r.reply + (r.truncated ? " (long file: only the first part is read)" : ""));
      } catch (ex) {
        setError(ex instanceof Error ? ex.message : String(ex));
      }
    }
    setUploading(false);
  };

  const detach = (name: string) => {
    setFiles((cur) => cur.filter((f) => f.name !== name));
    removeAttachment(name, session.current).catch(() => {});
  };

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    try { localStorage.setItem("jarvis-theme", next ? "dark" : "light"); } catch { /* private mode */ }
  };

  const toggleVoice = () => {
    const next = !voiceOn;
    setVoiceOn(next);
    localStorage.setItem("jarvis-voice", next ? "on" : "off");
    if (!next) stopSpeaking();
  };

  const submitText = (e: React.SyntheticEvent) => {
    e.preventDefault();
    const v = input;
    setInput("");
    run(v);
  };

  const closePanel = () => setPanel(null);

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (input.trim()) submitText(e);
    }
  };

  return (
    <main
      className="app"
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={(e) => { if (e.currentTarget === e.target) setDragging(false); }}
      onDrop={(e) => { e.preventDefault(); setDragging(false); if (e.dataTransfer.files.length) attach(e.dataTransfer.files); }}
    >
      {dragging && <div className="dropzone">{ui.drop}</div>}
      <header>
        <div className="brand">
          {editing ? (
            <input
              className="name-input"
              autoFocus
              value={draft}
              maxLength={20}
              aria-label={ui.renameTip}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={saveName}
              onKeyDown={(e) => {
                if (e.key === "Enter") saveName();
                if (e.key === "Escape") setEditing(false);
              }}
            />
          ) : (
            <>
              <h1>{name}<b>.</b></h1>
              <button className="rename" title={ui.renameTip} aria-label={ui.renameTip} onClick={() => { setDraft(name); setEditing(true); }}>
                <IconEdit />
              </button>
            </>
          )}
        </div>
        <span className="chip">
          <span className={`dot ${health === "down" ? "bad" : health ? "good" : ""}`} title={health === "down" ? "Backend offline" : "Backend online"} />
          {health === "down" ? "Offline" : health ? (health.brain === "claude" ? `Claude · ${health.model}` : ui.offline) : "…"}
        </span>
        <div className="spacer" />
        <button className={`icon ${showStudio ? "on" : ""}`} onClick={() => setShowStudio((v) => !v)} title={ui.studio} aria-label={ui.studio} aria-pressed={showStudio}>
          <IconPen />
        </button>
        <button className={`icon ${showKb ? "on" : ""}`} onClick={() => setShowKb((v) => !v)} title={ui.docs} aria-label={ui.docs} aria-pressed={showKb}>
          <IconBook />
        </button>
        <button className="icon" onClick={toggleTheme} title="Light / dark" aria-label="Light / dark theme">
          {dark ? <IconSun /> : <IconMoon />}
        </button>
        <button className="icon" onClick={toggleVoice} aria-pressed={voiceOn} title={ui.voice} aria-label={ui.voice}>
          {voiceOn ? <IconSound /> : <IconMute />}
        </button>
        <div className="seg" role="group" aria-label="Language">
          <button className={lang === "en" ? "on" : ""} onClick={() => chooseLang("en")}>EN</button>
          <button className={lang === "hi" ? "on" : ""} onClick={() => chooseLang("hi")}>हिं</button>
        </div>
      </header>

      <section className="stage">
        <button className={`orb ${status}`} onClick={onOrb} aria-label={ui[status]}>
          <span /><span /><span />
        </button>
        <p className="status" aria-live="polite">
          {interim || (mode === "wake" && status === "listening" && !awake ? ui.waiting.replace("{n}", name) : ui[status])}
        </p>
        <div className={`seg modes ${awake ? "awake" : ""}`} role="group" aria-label={ui.listeningMode}>
          {([["tap", ui.modeTap], ["hands", ui.handsfree], ["wake", ui.modeWake.replace("{n}", name)]] as [Mode, string][]).map(([m, label]) => (
            <button key={m} className={mode === m ? "on" : ""} onClick={() => chooseMode(m)} disabled={!micOk && m !== "tap"} aria-pressed={mode === m}>
              {label}
            </button>
          ))}
        </div>
        {kbOn && <span className="chip doc-chip"><IconBook /> {ui.docMode}</span>}
        {!micOk && <p className="hint">{ui.nomic}</p>}
        {health === "down" && <p className="hint error">{ui.backendDown}</p>}
        {error && <p className="hint error">{error}</p>}
      </section>

      {showStudio && (
        <DocStudio
          lang={lang}
          onClose={() => setShowStudio(false)}
          onPauseListening={() => { if (handsFreeRef.current) chooseMode("tap"); }}
          onDone={(reply, files) => {
            setMessages((m) => [...m, { id: nextId.current++, who: "jarvis", text: reply, files }]);
            say(reply);
          }}
        />
      )}

      {showKb && (
        <KnowledgePanel lang={lang} session={session.current} mode={kbOn} onMode={setKbOn} onClose={() => setShowKb(false)} />
      )}

      {panel && (
        <section className="panel">
          <button className="close" onClick={closePanel} aria-label="Close">×</button>
          {panel.type === "chart" && <Chart kind={panel.kind} title={panel.title} data={panel.data} />}
          {panel.type === "spiral" && <Spiral />}
          {panel.type === "mail_draft" && (
            <MailCard
              key={panel.draft.subject + panel.draft.body}
              draft={panel.draft}
              lang={lang}
              session={session.current}
              onDiscard={() => { setConfirming(false); run(ui.no); }}
              onSent={(reply) => {
                closePanel();
                setConfirming(false);
                setQuick([]);
                add("jarvis", reply);
                say(reply);
              }}
            />
          )}
          {panel.type === "camera" && <Camera />}
          {panel.type === "form" && (
            <FormPanel
              key={panel.template + panel.title}
              template={panel.template}
              title={panel.title}
              fields={panel.fields}
              lang={lang}
              onDone={(reply, files) => {
                closePanel();
                setMessages((m) => [...m, { id: nextId.current++, who: "jarvis", text: reply, files }]);
                say(reply);
              }}
            />
          )}
          {panel.type === "compose_email" && (
            <EmailForm
              lang={lang}
              onDone={(msg) => {
                closePanel();
                add("jarvis", msg);
                say(msg);
              }}
            />
          )}
        </section>
      )}

      <section className="log" aria-label="Conversation">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>{ui.hello}</h2>
            <p>{ui.helloSub}</p>
            <div className="suggest">
              {SUGGEST[lang].map((s) => (
                <button key={s} type="button" onClick={() => run(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.who}`}>
            <p>{m.text}</p>
            {m.note && <small>{m.note}</small>}
            {m.sources && m.sources.length > 0 && (
              <div className="sources">
                {m.sources.map((s) => (
                  <span key={s.n} title={s.snippet}>[{s.n}] {s.name}</span>
                ))}
              </div>
            )}
            {m.files && (
              <div className="files">
                {m.files.map((f) => (
                  <a key={f.url} className="file" href={BASE + f.url} download={f.name}><IconDown /> {f.name}</a>
                ))}
              </div>
            )}
          </div>
        ))}
        {confirming && (
          <div className="row confirm">
            <button className="btn" onClick={() => { setConfirming(false); run(ui.yes); }}>{ui.yes}</button>
            <button className="btn ghost" onClick={() => { setConfirming(false); run(ui.no); }}>{ui.no}</button>
          </div>
        )}
        <div ref={logEnd} />
      </section>

      {quick.length > 0 && (
        <div className="quick" role="group" aria-label="Quick replies">
          {quick.map((o) => (
            <button key={o.send + o.label} type="button" onClick={() => run(o.send)}>{o.label}</button>
          ))}
        </div>
      )}
      {files.length > 0 && (
        <div className="chips">
          {files.map((f) => (
            <span key={f.name} className="chip-file">
              {f.name}
              <button onClick={() => detach(f.name)} aria-label={`Remove ${f.name}`}>×</button>
            </span>
          ))}
        </div>
      )}
      <form className="input" onSubmit={submitText}>
        <input
          ref={fileInput}
          type="file"
          multiple
          hidden
          onChange={(e) => { if (e.target.files) attach(e.target.files); e.target.value = ""; }}
        />
        <button type="button" className="icon" onClick={() => fileInput.current?.click()} title={ui.attach} aria-label={ui.attach} disabled={uploading}>
          {uploading ? "…" : <IconClip />}
        </button>
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder={ui.placeholder}
          lang={lang}
        />
        <button className="send" disabled={!input.trim()} aria-label="Send"><IconSend /></button>
      </form>
    </main>
  );
}
