"use client";

import { useEffect, useRef, useState } from "react";
import { makeFile, sendEmail, sendMail, type FormField, type Lang, type MailDraft } from "@/lib/api";

const COLORS = ["#00d4ff", "#ff5d73", "#ffd166", "#06d6a0", "#a78bfa", "#fb923c"];

export function Chart({ kind, title, data }: { kind: "pie" | "bar"; title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  const total = entries.reduce((s, [, v]) => s + v, 0) || 1;
  const max = Math.max(...entries.map(([, v]) => v), 1);

  let angle = -Math.PI / 2;
  const slices = entries.map(([label, v], i) => {
    const a0 = angle;
    angle += (v / total) * Math.PI * 2;
    const [x0, y0, x1, y1] = [Math.cos(a0), Math.sin(a0), Math.cos(angle), Math.sin(angle)].map((n) => n * 90);
    const large = angle - a0 > Math.PI ? 1 : 0;
    return { label, v, color: COLORS[i % COLORS.length], d: `M0 0 L${x0} ${y0} A90 90 0 ${large} 1 ${x1} ${y1} Z` };
  });

  return (
    <div className="panel-body">
      <h3>{title}</h3>
      {kind === "pie" ? (
        <svg viewBox="-100 -100 200 200" width="220" height="220" role="img" aria-label={title}>
          {slices.map((s) => (
            <path key={s.label} d={s.d} fill={s.color} stroke="#0b1220" strokeWidth="1" />
          ))}
        </svg>
      ) : (
        <svg viewBox="0 0 200 120" width="260" height="160" role="img" aria-label={title}>
          {entries.map(([label, v], i) => {
            const h = (v / max) * 90;
            const w = 160 / entries.length;
            return (
              <g key={label}>
                <rect x={20 + i * w + 4} y={100 - h} width={w - 8} height={h} fill={COLORS[i % COLORS.length]} rx="2" />
                <text x={20 + i * w + w / 2} y="114" textAnchor="middle" fontSize="8" fill="#9fb3c8">
                  {label}
                </text>
              </g>
            );
          })}
        </svg>
      )}
      <ul className="legend">
        {slices.map((s) => (
          <li key={s.label}>
            <i style={{ background: s.color }} /> {s.label}: {s.v}
            {kind === "pie" && ` (${((s.v / total) * 100).toFixed(1)}%)`}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Spiral() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d")!;
    const colors = ["#ff4d4d", "#a855f7", "#3b82f6", "#22c55e", "#f97316", "#facc15"];
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, c.width, c.height);
    let x = c.width / 2, y = c.height / 2, heading = 0;
    let i = 0;
    const scale = 0.5;
    let raf = 0;
    const step = () => {
      for (let n = 0; n < 4 && i < 360; n++, i++) {
        const nx = x + Math.cos(heading) * i * scale;
        const ny = y + Math.sin(heading) * i * scale;
        ctx.strokeStyle = colors[i % 6];
        ctx.lineWidth = i / 100 + 1;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(nx, ny);
        ctx.stroke();
        x = nx;
        y = ny;
        heading += (59 * Math.PI) / 180;
      }
      if (i < 360) raf = requestAnimationFrame(step);
    };
    step();
    return () => cancelAnimationFrame(raf);
  }, []);
  return (
    <div className="panel-body">
      <canvas ref={ref} width={320} height={320} style={{ maxWidth: "100%", borderRadius: 12 }} />
    </div>
  );
}

export function Camera() {
  const video = useRef<HTMLVideoElement>(null);
  const [shot, setShot] = useState<string | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let stream: MediaStream | undefined;
    navigator.mediaDevices
      ?.getUserMedia({ video: true })
      .then((s) => {
        stream = s;
        if (video.current) video.current.srcObject = s;
      })
      .catch((e) => setErr(e.message || "Camera not available"));
    return () => stream?.getTracks().forEach((t) => t.stop());
  }, []);

  const capture = () => {
    const v = video.current;
    if (!v) return;
    const c = document.createElement("canvas");
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    c.getContext("2d")!.drawImage(v, 0, 0);
    setShot(c.toDataURL("image/png"));
  };

  if (err) return <div className="panel-body error">{err}</div>;
  return (
    <div className="panel-body">
      {shot ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={shot} alt="Captured" style={{ maxWidth: "100%", borderRadius: 12 }} />
          <div className="row">
            <a className="btn" href={shot} download={`jarvis-${Date.now()}.png`}>Save</a>
            <button className="btn ghost" onClick={() => setShot(null)}>Retake</button>
          </div>
        </>
      ) : (
        <>
          <video ref={video} autoPlay playsInline muted style={{ maxWidth: "100%", borderRadius: 12 }} />
          <div className="row"><button className="btn" onClick={capture}>Capture</button></div>
        </>
      )}
    </div>
  );
}

export function MailCard({
  draft,
  lang,
  session,
  onSent,
  onDiscard,
}: {
  draft: MailDraft;
  lang: Lang;
  session: string;
  onSent: (reply: string) => void;
  onDiscard: () => void;
}) {
  const hi = lang === "hi";
  const L = hi
    ? { to: "प्रति", cc: "कॉपी (CC)", bcc: "बीसीसी (BCC)", sub: "विषय", msg: "संदेश", send: "भेजें", gmail: "Gmail में खोलें", drop: "रद्द करें", hint: "कुछ भी बदल सकते हैं। कई पते कॉमा से अलग करें।", busy: "…" }
    : { to: "To", cc: "Cc", bcc: "Bcc", sub: "Subject", msg: "Message", send: "Send", gmail: "Open in Gmail", drop: "Discard", hint: "Everything here can be edited. Separate several addresses with commas.", busy: "…" };
  const [to, setTo] = useState(draft.to_emails.join(", "));
  const [cc, setCc] = useState(draft.cc_emails.join(", "));
  const [bcc, setBcc] = useState(draft.bcc_emails.join(", "));
  const [subject, setSubject] = useState(draft.subject);
  const [body, setBody] = useState(draft.body);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const list = (s: string) => s.split(/[,;]+/).map((x) => x.trim()).filter(Boolean);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await sendMail({ to: list(to), cc: list(cc), bcc: list(bcc), subject, body }, lang, session);
      if (r.url) window.open(r.url, "_blank", "noopener"); // Gmail compose, already filled in
      onSent(r.reply);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="mail-card" onSubmit={submit}>
      <div className="mail-stamp">{draft.via === "smtp" ? (hi ? "सीधे भेजा जाएगा" : "Sends directly") : hi ? "Gmail में खुलेगा" : "Opens in Gmail"}</div>
      <label className="mail-row"><span>{L.to}</span><input value={to} onChange={(e) => setTo(e.target.value)} required placeholder="name@example.com" /></label>
      <label className="mail-row"><span>{L.cc}</span><input value={cc} onChange={(e) => setCc(e.target.value)} /></label>
      <label className="mail-row"><span>{L.bcc}</span><input value={bcc} onChange={(e) => setBcc(e.target.value)} /></label>
      <label className="mail-row"><span>{L.sub}</span><input value={subject} onChange={(e) => setSubject(e.target.value)} /></label>
      <label className="mail-row top"><span>{L.msg}</span><textarea rows={7} value={body} onChange={(e) => setBody(e.target.value)} /></label>
      {err && <p className="error">{err}</p>}
      <p className="mail-hint">{L.hint}</p>
      <div className="row">
        <button className="btn" disabled={busy || !to.trim()}>{busy ? L.busy : draft.via === "smtp" ? L.send : L.gmail}</button>
        <button type="button" className="btn ghost" onClick={onDiscard}>{L.drop}</button>
      </div>
    </form>
  );
}

export function EmailForm({ lang, onDone }: { lang: Lang; onDone: (msg: string) => void }) {
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await sendEmail(to, subject, body, lang);
      onDone(r.reply);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="panel-body form" onSubmit={submit}>
      <input type="email" required placeholder="To" value={to} onChange={(e) => setTo(e.target.value)} />
      <input placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
      <textarea rows={5} placeholder="Message" value={body} onChange={(e) => setBody(e.target.value)} />
      {err && <p className="error">{err}</p>}
      <div className="row"><button className="btn" disabled={busy}>{busy ? "Sending…" : "Send"}</button></div>
    </form>
  );
}

export function FormPanel({
  template,
  title,
  fields,
  lang,
  onDone,
}: {
  template: string;
  title: string;
  fields: FormField[];
  lang: Lang;
  onDone: (reply: string, files: { name: string; url: string }[]) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(fields.map((f) => [f.key, f.default])));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await makeFile(template, values, lang);
      onDone(r.reply, r.files);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  };

  const set = (k: string, v: string) => setValues((cur) => ({ ...cur, [k]: v }));

  return (
    <form className="panel-body form" onSubmit={submit}>
      <h3>{title}</h3>
      {fields.map((f) => (
        <label key={f.key} className="field">
          <span>{f.label}</span>
          {f.options.length > 0 ? (
            <select value={values[f.key]} onChange={(e) => set(f.key, e.target.value)}>
              {f.options.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          ) : f.multiline ? (
            <textarea rows={4} required={f.required} value={values[f.key]} onChange={(e) => set(f.key, e.target.value)} />
          ) : (
            <input required={f.required} value={values[f.key]} onChange={(e) => set(f.key, e.target.value)} />
          )}
        </label>
      ))}
      {err && <p className="error">{err}</p>}
      <div className="row"><button className="btn" disabled={busy}>{busy ? "…" : lang === "hi" ? "फ़ाइल बनाएँ" : "Create file"}</button></div>
    </form>
  );
}
