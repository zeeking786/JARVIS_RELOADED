"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { kbClear, kbDelete, kbFolder, kbInfo, kbJob, kbMode, kbUpload, type KbInfo, type KbJob, type Lang } from "@/lib/api";

const T = {
  en: {
    title: "Your documents",
    sub: "Add files or a whole folder. Then ask questions and Jarvis answers from them.",
    chat: "Chat with my documents",
    chatHint: "Every question is answered from your documents (commands like “open YouTube” still work).",
    addFiles: "Add files",
    folder: "Or index a folder",
    folderPh: "e.g. D:\\Company\\Policies",
    index: "Index folder",
    empty: "Nothing indexed yet.",
    clear: "Clear all",
    confirmClear: "Remove every indexed document? Your original files are not touched.",
    files: "files",
    chunks: "passages",
    search: { minilm: "semantic search", keyword: "keyword search (offline)" },
    answers: { claude: "answers written by Claude", extractive: "answers quote your documents" },
    done: "Done",
    skipped: "skipped",
    unchanged: "unchanged",
    close: "Close",
    remove: "Remove",
    working: "Indexing…",
    limited: "Only the first 2000 files were indexed; point at a smaller folder for the rest.",
  },
  hi: {
    title: "आपके दस्तावेज़",
    sub: "फ़ाइलें या पूरा फ़ोल्डर जोड़ें। फिर सवाल पूछें, जार्विस उन्हीं से जवाब देगा।",
    chat: "मेरे दस्तावेज़ों से बात करें",
    chatHint: "हर सवाल का जवाब आपके दस्तावेज़ों से आएगा (“यूट्यूब खोलो” जैसे कमांड फिर भी चलेंगे)।",
    addFiles: "फ़ाइलें जोड़ें",
    folder: "या पूरा फ़ोल्डर जोड़ें",
    folderPh: "जैसे D:\\Company\\Policies",
    index: "फ़ोल्डर जोड़ें",
    empty: "अभी कुछ जोड़ा नहीं गया।",
    clear: "सब हटाएँ",
    confirmClear: "सभी जोड़े गए दस्तावेज़ हटा दें? आपकी असली फ़ाइलें नहीं छुई जाएँगी।",
    files: "फ़ाइलें",
    chunks: "अंश",
    search: { minilm: "अर्थ आधारित खोज", keyword: "कीवर्ड खोज (ऑफ़लाइन)" },
    answers: { claude: "जवाब Claude लिखता है", extractive: "जवाब आपके दस्तावेज़ों से उद्धृत" },
    done: "पूरा",
    skipped: "छोड़े गए",
    unchanged: "जैसे थे",
    close: "बंद करें",
    remove: "हटाएँ",
    working: "जोड़ रहा हूँ…",
    limited: "सिर्फ़ पहली 2000 फ़ाइलें जोड़ी गईं; बाक़ी के लिए छोटा फ़ोल्डर चुनें।",
  },
} as const;

export function KnowledgePanel({
  lang,
  session,
  mode,
  onMode,
  onClose,
}: {
  lang: Lang;
  session: string;
  mode: boolean;
  onMode: (on: boolean) => void;
  onClose: () => void;
}) {
  const L = T[lang];
  const [info, setInfo] = useState<KbInfo | null>(null);
  const [job, setJob] = useState<KbJob | null>(null);
  const [path, setPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const picker = useRef<HTMLInputElement>(null);
  const poll = useRef(0);

  const refresh = useCallback(() => kbInfo().then(setInfo).catch((e) => setErr(String(e.message ?? e))), []);

  useEffect(() => {
    refresh();
    return () => clearInterval(poll.current);
  }, [refresh]);

  const addFiles = async (list: FileList | null) => {
    if (!list?.length) return;
    setBusy(true);
    setErr("");
    setMsg(L.working);
    try {
      const r = await kbUpload(Array.from(list));
      setInfo(r);
      const bad = r.results.filter((x) => x.skipped);
      setMsg(`${r.results.length - bad.length} ${L.files}` + (bad.length ? ` · ${bad.length} ${L.skipped}: ${bad.map((b) => `${b.name} (${b.skipped})`).join("; ")}` : ""));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setMsg("");
    } finally {
      setBusy(false);
    }
  };

  const indexFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!path.trim()) return;
    setBusy(true);
    setErr("");
    setMsg("");
    setJob(null);
    try {
      const { job: id } = await kbFolder(path.trim());
      clearInterval(poll.current);
      poll.current = window.setInterval(async () => {
        try {
          const j = await kbJob(id);
          setJob(j);
          if (j.state !== "running") {
            clearInterval(poll.current);
            setBusy(false);
            if (j.state === "error") setErr(j.error ?? "Indexing failed");
            else setMsg(`${L.done}: ${j.indexed} ${L.files} · ${j.unchanged} ${L.unchanged}` + (j.skipped?.length ? ` · ${j.skipped.length} ${L.skipped}` : "") + (j.limited ? ` · ${L.limited}` : ""));
            refresh();
          }
        } catch (ex) {
          clearInterval(poll.current);
          setBusy(false);
          setErr(ex instanceof Error ? ex.message : String(ex));
        }
      }, 700);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
      setBusy(false);
    }
  };

  const toggle = async () => {
    const next = !mode;
    onMode(next);
    kbMode(next, session).catch(() => onMode(!next));
  };

  const pct = job && job.total ? Math.round((job.done / job.total) * 100) : 0;

  return (
    <section className="panel kb">
      <button className="close" onClick={onClose} aria-label={L.close}>×</button>
      <h3>{L.title}</h3>
      <p className="kb-sub">{L.sub}</p>

      <label className="toggle kb-mode">
        <input type="checkbox" checked={mode} onChange={toggle} disabled={!info || info.chunks === 0} />
        <i /> <b>{L.chat}</b>
      </label>
      <p className="kb-hint">{L.chatHint}</p>

      <div className="kb-add">
        <input ref={picker} type="file" multiple hidden onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
        <button className="btn" disabled={busy} onClick={() => picker.current?.click()}>{L.addFiles}</button>
        <form className="kb-folder" onSubmit={indexFolder}>
          <input value={path} onChange={(e) => setPath(e.target.value)} placeholder={L.folderPh} aria-label={L.folder} disabled={busy} />
          <button className="btn ghost" disabled={busy || !path.trim()}>{L.index}</button>
        </form>
      </div>

      {job && job.state === "running" && (
        <div className="kb-progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
          <div style={{ width: `${pct}%` }} />
          <span>{job.done} / {job.total} · {job.current}</span>
        </div>
      )}
      {msg && <p className="kb-msg">{msg}</p>}
      {job?.skipped && job.skipped.length > 0 && (
        <details className="kb-skipped">
          <summary>{job.skipped.length} {L.skipped}</summary>
          <ul>{job.skipped.slice(0, 20).map((s) => <li key={s.name}>{s.name} — {s.reason}</li>)}</ul>
        </details>
      )}
      {err && <p className="error">{err}</p>}

      {info && (
        <p className="kb-stats">
          {info.sources.length} {L.files} · {info.chunks} {L.chunks} · {L.search[info.embedder]} · {L.answers[info.answers]}
        </p>
      )}
      {info && info.sources.length === 0 && <p className="kb-hint">{L.empty}</p>}
      {info && info.sources.length > 0 && (
        <>
          <ul className="kb-list">
            {info.sources.map((s) => (
              <li key={s.name}>
                <span title={s.name}>{s.name}</span>
                <small>{s.chunks}</small>
                <button aria-label={`${L.remove} ${s.name}`} onClick={() => kbDelete(s.name).then(setInfo).catch((e) => setErr(String(e.message ?? e)))}>×</button>
              </li>
            ))}
          </ul>
          <div className="row">
            <button className="btn ghost" onClick={() => { if (window.confirm(L.confirmClear)) kbClear().then((i) => { setInfo(i); onMode(false); }); }}>{L.clear}</button>
          </div>
        </>
      )}
    </section>
  );
}
