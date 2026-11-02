"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BASE, buildDoc, type Lang } from "@/lib/api";
import { createRecognition, recognitionSupported } from "@/lib/speech";

type Kind = "heading" | "paragraph" | "quote" | "bullets" | "numbered" | "table" | "image" | "pagebreak";
type Align = "left" | "center" | "right" | "justify";

interface Blk {
  id: number;
  type: Kind;
  text: string;
  level: 1 | 2 | 3;
  items: string; // bullets / numbered: one item per line
  rows: string[][];
  header: boolean;
  data: string; // image as a data URL
  width: number;
  caption: string;
  align: Align;
}

const DRAFT_KEY = "jarvis-studio-draft";
const FONTS = ["Calibri", "Arial", "Times New Roman", "Georgia", "Verdana"];

const T = {
  en: {
    title: "Document studio",
    sub: "Write a whole document with headings, formatting, tables and pictures. Then download it as Word or PDF.",
    docTitle: "Document title",
    subtitle: "Subtitle (optional)",
    author: "Author (optional)",
    add: "Add",
    heading: "Heading",
    paragraph: "Text",
    quote: "Quote",
    bullets: "Bullets",
    numbered: "Numbered",
    table: "Table",
    image: "Picture",
    pagebreak: "Page break",
    paste: "Paste text",
    pasteHint: "Paste your text. # Heading, - bullets, 1. numbers, | a | b | tables, > quote and --- (page break) are turned into blocks.",
    addPasted: "Add to document",
    empty: "Nothing here yet. Add a heading, some text or a picture with the buttons above, or paste text.",
    up: "Move up",
    down: "Move down",
    del: "Delete",
    bold: "Bold",
    italic: "Italic",
    dictate: "Dictate by voice",
    stop: "Stop dictating",
    itemsPh: "One item per line",
    textPh: "Write here. **bold** and *italic* work.",
    captionPh: "Caption (optional)",
    width: "Width",
    addRow: "+ Row",
    addCol: "+ Column",
    delRow: "- Row",
    delCol: "- Column",
    header: "First row is a header",
    font: "Font",
    size: "Size",
    pageNos: "Page numbers",
    format: "Create as",
    word: "Word (.docx)",
    pdf: "PDF",
    create: "Create file",
    creating: "Creating…",
    clear: "Clear draft",
    confirmClear: "Discard everything in this draft?",
    close: "Close",
    ready: "Your file is ready:",
    saved: "Draft saved in this browser",
    noMic: "Voice typing needs Chrome or Edge.",
    pickPic: "Choose a picture",
  },
  hi: {
    title: "डॉक्यूमेंट स्टूडियो",
    sub: "हेडिंग, फ़ॉर्मेटिंग, टेबल और तस्वीरों के साथ पूरा दस्तावेज़ लिखें। फिर Word या PDF में डाउनलोड करें।",
    docTitle: "दस्तावेज़ का शीर्षक",
    subtitle: "उप-शीर्षक (वैकल्पिक)",
    author: "लेखक (वैकल्पिक)",
    add: "जोड़ें",
    heading: "हेडिंग",
    paragraph: "टेक्स्ट",
    quote: "उद्धरण",
    bullets: "बुलेट",
    numbered: "क्रमांक",
    table: "टेबल",
    image: "तस्वीर",
    pagebreak: "नया पेज",
    paste: "टेक्स्ट पेस्ट करें",
    pasteHint: "अपना टेक्स्ट पेस्ट करें। # हेडिंग, - बुलेट, 1. क्रमांक, | a | b | टेबल, > उद्धरण और --- (नया पेज) अपने आप ब्लॉक बन जाएँगे।",
    addPasted: "दस्तावेज़ में जोड़ें",
    empty: "अभी कुछ नहीं है। ऊपर के बटनों से हेडिंग, टेक्स्ट या तस्वीर जोड़ें, या टेक्स्ट पेस्ट करें।",
    up: "ऊपर",
    down: "नीचे",
    del: "हटाएँ",
    bold: "बोल्ड",
    italic: "इटैलिक",
    dictate: "बोलकर लिखें",
    stop: "बोलना बंद करें",
    itemsPh: "हर पंक्ति में एक बिंदु",
    textPh: "यहाँ लिखें। **बोल्ड** और *इटैलिक* चलते हैं।",
    captionPh: "कैप्शन (वैकल्पिक)",
    width: "चौड़ाई",
    addRow: "+ पंक्ति",
    addCol: "+ कॉलम",
    delRow: "- पंक्ति",
    delCol: "- कॉलम",
    header: "पहली पंक्ति हेडर है",
    font: "फ़ॉन्ट",
    size: "आकार",
    pageNos: "पेज नंबर",
    format: "इस रूप में बनाएँ",
    word: "Word (.docx)",
    pdf: "PDF",
    create: "फ़ाइल बनाएँ",
    creating: "बना रहा हूँ…",
    clear: "ड्राफ़्ट हटाएँ",
    confirmClear: "इस ड्राफ़्ट का सब कुछ हटा दें?",
    close: "बंद करें",
    ready: "आपकी फ़ाइल तैयार है:",
    saved: "ड्राफ़्ट इस ब्राउज़र में सेव है",
    noMic: "बोलकर लिखने के लिए Chrome या Edge चाहिए।",
    pickPic: "तस्वीर चुनें",
  },
} as const;

let nextBlock = 1;
const blank = (type: Kind, over: Partial<Blk> = {}): Blk => ({
  id: nextBlock++, type, text: "", level: 1, items: "", rows: [["", "", ""], ["", "", ""], ["", "", ""]], header: true, data: "", width: 80, caption: "", align: "left", ...over,
});

/** "# Title\n\ntext\n- a\n- b" -> blocks. Deliberately forgiving: anything unknown is a paragraph. */
export function parseText(src: string): Blk[] {
  const out: Blk[] = [];
  let para: string[] = [];
  let list: { kind: "bullets" | "numbered"; items: string[] } | null = null;
  let table: string[][] | null = null;
  const flush = () => {
    if (para.length) out.push(blank("paragraph", { text: para.join(" ") }));
    if (list) out.push(blank(list.kind, { items: list.items.join("\n") }));
    if (table && table.length) out.push(blank("table", { rows: table }));
    para = [];
    list = null;
    table = null;
  };
  for (const raw of src.replace(/\r/g, "").split("\n")) {
    const line = raw.trim();
    let m: RegExpMatchArray | null;
    if (!line) flush();
    else if (/^-{3,}$|^\*{3,}$/.test(line)) { flush(); out.push(blank("pagebreak")); }
    else if ((m = line.match(/^(#{1,3})\s+(.*)$/))) { flush(); out.push(blank("heading", { level: m[1].length as 1 | 2 | 3, text: m[2] })); }
    else if ((m = line.match(/^>\s?(.*)$/))) { flush(); out.push(blank("quote", { text: m[1] })); }
    else if ((m = line.match(/^[-*•]\s+(.*)$/))) {
      if (list?.kind !== "bullets") { flush(); list = { kind: "bullets", items: [] }; }
      list!.items.push(m[1]);
    } else if ((m = line.match(/^\d+[.)]\s+(.*)$/))) {
      if (list?.kind !== "numbered") { flush(); list = { kind: "numbered", items: [] }; }
      list!.items.push(m[1]);
    } else if (line.startsWith("|") && line.split("|").length > 2) {
      if (/^\|?[\s:|-]+\|?$/.test(line)) continue; // | --- | --- |
      if (!table) { flush(); table = []; }
      table.push(line.replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
    } else {
      if (list || table) flush();
      para.push(line);
    }
  }
  flush();
  return out;
}

/** Shrink a picture to at most 1600 px so the document stays small. PNG keeps transparency, everything else becomes JPEG. */
async function prepareImage(file: File): Promise<string> {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise<HTMLImageElement>((ok, bad) => {
      const i = new Image();
      i.onload = () => ok(i);
      i.onerror = () => bad(new Error(`${file.name} is not a picture`));
      i.src = url;
    });
    const scale = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight));
    const c = document.createElement("canvas");
    c.width = Math.max(1, Math.round(img.naturalWidth * scale));
    c.height = Math.max(1, Math.round(img.naturalHeight * scale));
    const ctx = c.getContext("2d")!;
    if (/png|gif|webp|svg/.test(file.type)) {
      ctx.drawImage(img, 0, 0, c.width, c.height);
      const png = c.toDataURL("image/png");
      if (png.length < 5_500_000) return png;
    }
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.drawImage(img, 0, 0, c.width, c.height);
    return c.toDataURL("image/jpeg", 0.88);
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function DocStudio({
  lang,
  onDone,
  onClose,
  onPauseListening,
}: {
  lang: Lang;
  onDone: (reply: string, files: { name: string; url: string }[]) => void;
  onClose: () => void;
  onPauseListening: () => void;
}) {
  const L = T[lang];
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [author, setAuthor] = useState("");
  const [font, setFont] = useState("Calibri");
  const [fontSize, setFontSize] = useState(11);
  const [pageNos, setPageNos] = useState(true);
  const [format, setFormat] = useState<"docx" | "pdf">("docx");
  const [blocks, setBlocks] = useState<Blk[]>([]);
  const [showPaste, setShowPaste] = useState(false);
  const [pasted, setPasted] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [made, setMade] = useState<{ name: string; url: string }[]>([]);
  const [dictating, setDictating] = useState<number | null>(null);
  const [focusId, setFocusId] = useState<number | null>(null);
  const picker = useRef<HTMLInputElement>(null);
  const loaded = useRef(false);
  const dictRef = useRef<number | null>(null);
  const recRef = useRef<ReturnType<typeof createRecognition> | null>(null);

  // restore the draft once, then save it on every change (a draft survives closing the panel or the tab)
  useEffect(() => {
    try {
      const d = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? "null");
      if (d) {
        setTitle(d.title ?? "");
        setSubtitle(d.subtitle ?? "");
        setAuthor(d.author ?? "");
        setFont(d.font ?? "Calibri");
        setFontSize(d.fontSize ?? 11);
        setPageNos(d.pageNos ?? true);
        const bs: Blk[] = (d.blocks ?? []).map((b: Blk) => ({ ...blank(b.type), ...b, id: nextBlock++ }));
        setBlocks(bs);
      }
    } catch {
      /* no draft, or storage unavailable */
    }
    loaded.current = true;
  }, []);

  useEffect(() => {
    if (!loaded.current) return;
    const id = window.setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify({ title, subtitle, author, font, fontSize, pageNos, blocks }));
      } catch {
        /* too big for storage (many pictures): the draft just isn't kept */
      }
    }, 600);
    return () => clearTimeout(id);
  }, [title, subtitle, author, font, fontSize, pageNos, blocks]);

  useEffect(() => {
    return () => {
      dictRef.current = null;
      recRef.current?.abort?.();
    };
  }, []);

  const patch = (id: number, p: Partial<Blk>) => setBlocks((bs) => bs.map((b) => (b.id === id ? { ...b, ...p } : b)));
  const insert = useCallback((nb: Blk[]) => {
    setBlocks((bs) => {
      const at = focusId == null ? -1 : bs.findIndex((b) => b.id === focusId);
      return at < 0 ? [...bs, ...nb] : [...bs.slice(0, at + 1), ...nb, ...bs.slice(at + 1)];
    });
    setFocusId(nb[nb.length - 1]?.id ?? null);
  }, [focusId]);
  const move = (id: number, d: -1 | 1) =>
    setBlocks((bs) => {
      const i = bs.findIndex((b) => b.id === id);
      const j = i + d;
      if (i < 0 || j < 0 || j >= bs.length) return bs;
      const c = [...bs];
      [c[i], c[j]] = [c[j], c[i]];
      return c;
    });

  const addImages = async (files: FileList | null) => {
    if (!files?.length) return;
    setErr("");
    try {
      const fresh: Blk[] = [];
      for (const f of Array.from(files)) fresh.push(blank("image", { data: await prepareImage(f), caption: "" }));
      insert(fresh);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const wrap = (id: number, mark: string) => {
    const el = document.getElementById(`blk-${id}`) as HTMLTextAreaElement | null;
    const b = blocks.find((x) => x.id === id);
    if (!el || !b) return;
    const [s, e] = [el.selectionStart, el.selectionEnd];
    const sel = b.text.slice(s, e) || "text";
    patch(id, { text: b.text.slice(0, s) + mark + sel + mark + b.text.slice(e) });
  };

  const stopDictation = () => {
    dictRef.current = null;
    setDictating(null);
    recRef.current?.abort?.();
  };

  const toggleDictation = (id: number) => {
    if (dictRef.current === id) return stopDictation();
    onPauseListening(); // the browser allows one microphone listener at a time
    recRef.current?.abort?.();
    dictRef.current = id;
    setDictating(id);
    const start = () => {
      const rec = createRecognition(lang, {
        onInterim: () => {},
        onFinal: (text) => {
          if (dictRef.current !== id) return;
          setBlocks((bs) => bs.map((b) => (b.id === id ? { ...b, text: (b.text ? b.text.replace(/\s*$/, " ") : "") + text } : b)));
        },
        onEnd: () => {
          if (dictRef.current === id && recRef.current === rec) window.setTimeout(() => dictRef.current === id && start(), 150);
        },
        onError: (code) => {
          if (code === "not-allowed" || code === "service-not-allowed") stopDictation();
        },
      }, () => 3500);
      recRef.current = rec;
      try {
        rec.start();
      } catch {
        /* already running */
      }
    };
    start();
  };

  const create = async () => {
    setBusy(true);
    setErr("");
    setMade([]);
    try {
      const r = await buildDoc(
        {
          title, subtitle, author, font, font_size: fontSize, page_numbers: pageNos, format,
          blocks: blocks.map((b) => ({
            type: b.type, text: b.text, level: b.level, header: b.header, data: b.data, width: b.width, caption: b.caption, align: b.align,
            items: b.items.split("\n").map((s) => s.trim()).filter(Boolean),
            rows: b.rows,
          })),
        },
        lang,
      );
      setMade(r.files);
      onDone(r.reply, r.files);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const addTable = () => insert([blank("table")]);
  const setCell = (id: number, ri: number, ci: number, v: string) =>
    setBlocks((bs) => bs.map((b) => (b.id === id ? { ...b, rows: b.rows.map((r, i) => (i === ri ? r.map((c, j) => (j === ci ? v : c)) : r)) } : b)));
  const resize = (id: number, dr: number, dc: number) =>
    setBlocks((bs) => bs.map((b) => {
      if (b.id !== id) return b;
      let rows = b.rows.map((r) => [...r]);
      if (dr > 0) rows.push(Array(rows[0]?.length ?? 3).fill(""));
      if (dr < 0 && rows.length > 1) rows = rows.slice(0, -1);
      if (dc > 0) rows = rows.map((r) => [...r, ""]);
      if (dc < 0 && (rows[0]?.length ?? 0) > 1) rows = rows.map((r) => r.slice(0, -1));
      return { ...b, rows };
    }));

  const label = (b: Blk) => ({ heading: L.heading, paragraph: L.paragraph, quote: L.quote, bullets: L.bullets, numbered: L.numbered, table: L.table, image: L.image, pagebreak: L.pagebreak })[b.type];

  return (
    <section className="panel studio">
      <button className="close" onClick={onClose} aria-label={L.close}>×</button>
      <h3>{L.title}</h3>
      <p className="kb-sub">{L.sub}</p>

      <div className="studio-head">
        <input className="studio-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder={L.docTitle} aria-label={L.docTitle} />
        <input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} placeholder={L.subtitle} aria-label={L.subtitle} />
        <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder={L.author} aria-label={L.author} />
      </div>

      <div className="studio-bar" role="toolbar" aria-label={L.add}>
        <span>{L.add}:</span>
        <button onClick={() => insert([blank("heading")])}>{L.heading}</button>
        <button onClick={() => insert([blank("paragraph")])}>{L.paragraph}</button>
        <button onClick={() => insert([blank("bullets")])}>{L.bullets}</button>
        <button onClick={() => insert([blank("numbered")])}>{L.numbered}</button>
        <button onClick={addTable}>{L.table}</button>
        <button onClick={() => picker.current?.click()}>{L.image}</button>
        <button onClick={() => insert([blank("quote")])}>{L.quote}</button>
        <button onClick={() => insert([blank("pagebreak")])}>{L.pagebreak}</button>
        <button className="alt" onClick={() => setShowPaste((v) => !v)} aria-expanded={showPaste}>{L.paste}</button>
        <input ref={picker} type="file" accept="image/*" multiple hidden aria-label={L.pickPic} onChange={(e) => { addImages(e.target.files); e.target.value = ""; }} />
      </div>

      {showPaste && (
        <div className="studio-paste">
          <p>{L.pasteHint}</p>
          <textarea rows={7} value={pasted} onChange={(e) => setPasted(e.target.value)} />
          <button className="btn ghost" disabled={!pasted.trim()} onClick={() => { insert(parseText(pasted)); setPasted(""); setShowPaste(false); }}>{L.addPasted}</button>
        </div>
      )}

      <div className="studio-blocks">
        {blocks.length === 0 && <p className="kb-hint">{L.empty}</p>}
        {blocks.map((b, i) => (
          <div key={b.id} className={`blk ${focusId === b.id ? "focus" : ""}`} onFocus={() => setFocusId(b.id)} onClick={() => setFocusId(b.id)}>
            <div className="blk-head">
              <b>{label(b)}</b>
              {b.type === "heading" && (
                <select value={b.level} onChange={(e) => patch(b.id, { level: Number(e.target.value) as 1 | 2 | 3 })} aria-label="Heading level">
                  <option value={1}>H1</option><option value={2}>H2</option><option value={3}>H3</option>
                </select>
              )}
              {(b.type === "paragraph") && (
                <>
                  <select value={b.align} onChange={(e) => patch(b.id, { align: e.target.value as Align })} aria-label="Alignment">
                    <option value="left">⟸</option><option value="center">≡</option><option value="right">⟹</option><option value="justify">☰</option>
                  </select>
                </>
              )}
              {(b.type === "paragraph" || b.type === "quote" || b.type === "heading") && (
                <>
                  <button title={L.bold} aria-label={L.bold} onClick={() => wrap(b.id, "**")}><b>B</b></button>
                  <button title={L.italic} aria-label={L.italic} onClick={() => wrap(b.id, "*")}><i>I</i></button>
                </>
              )}
              {b.type === "paragraph" && recognitionSupported() && (
                <button className={dictating === b.id ? "rec" : ""} title={dictating === b.id ? L.stop : L.dictate} aria-label={dictating === b.id ? L.stop : L.dictate} aria-pressed={dictating === b.id} onClick={() => toggleDictation(b.id)}>
                  {dictating === b.id ? "■" : "🎙"}
                </button>
              )}
              <span className="grow" />
              <button title={L.up} aria-label={L.up} disabled={i === 0} onClick={() => move(b.id, -1)}>↑</button>
              <button title={L.down} aria-label={L.down} disabled={i === blocks.length - 1} onClick={() => move(b.id, 1)}>↓</button>
              <button title={L.del} aria-label={L.del} onClick={() => { if (dictating === b.id) stopDictation(); setBlocks((bs) => bs.filter((x) => x.id !== b.id)); }}>✕</button>
            </div>

            {(b.type === "heading") && <input id={`blk-${b.id}`} className={`h${b.level}`} value={b.text} onChange={(e) => patch(b.id, { text: e.target.value })} placeholder={L.heading} />}
            {(b.type === "paragraph" || b.type === "quote") && (
              <textarea id={`blk-${b.id}`} rows={b.type === "quote" ? 2 : 4} value={b.text} onChange={(e) => patch(b.id, { text: e.target.value })} placeholder={L.textPh} />
            )}
            {(b.type === "bullets" || b.type === "numbered") && (
              <textarea id={`blk-${b.id}`} rows={4} value={b.items} onChange={(e) => patch(b.id, { items: e.target.value })} placeholder={L.itemsPh} />
            )}
            {b.type === "table" && (
              <div className="tbl-edit">
                <div className="tbl-tools">
                  <button onClick={() => resize(b.id, 1, 0)}>{L.addRow}</button>
                  <button onClick={() => resize(b.id, -1, 0)}>{L.delRow}</button>
                  <button onClick={() => resize(b.id, 0, 1)}>{L.addCol}</button>
                  <button onClick={() => resize(b.id, 0, -1)}>{L.delCol}</button>
                  <label><input type="checkbox" checked={b.header} onChange={(e) => patch(b.id, { header: e.target.checked })} /> {L.header}</label>
                </div>
                <div className="tbl-scroll">
                  <table>
                    <tbody>
                      {b.rows.map((r, ri) => (
                        <tr key={ri}>
                          {r.map((c, ci) => (
                            <td key={ci} className={ri === 0 && b.header ? "th" : ""}>
                              <input value={c} onChange={(e) => setCell(b.id, ri, ci, e.target.value)} aria-label={`row ${ri + 1} column ${ci + 1}`} />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {b.type === "image" && (
              <div className="img-edit">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={b.data} alt={b.caption || "picture"} style={{ width: `${b.width}%` }} />
                <div className="img-tools">
                  <label>{L.width}: {b.width}% <input type="range" min={10} max={100} step={5} value={b.width} onChange={(e) => patch(b.id, { width: Number(e.target.value) })} /></label>
                  <select value={b.align === "left" || b.align === "right" ? b.align : "center"} onChange={(e) => patch(b.id, { align: e.target.value as Align })} aria-label="Alignment">
                    <option value="left">⟸</option><option value="center">≡</option><option value="right">⟹</option>
                  </select>
                </div>
                <input value={b.caption} onChange={(e) => patch(b.id, { caption: e.target.value })} placeholder={L.captionPh} />
              </div>
            )}
            {b.type === "pagebreak" && <hr className="pb" />}
          </div>
        ))}
      </div>

      <div className="studio-foot">
        <label>{L.font} <select value={font} onChange={(e) => setFont(e.target.value)}>{FONTS.map((f) => <option key={f}>{f}</option>)}</select></label>
        <label>{L.size} <input type="number" min={8} max={20} value={fontSize} onChange={(e) => setFontSize(Math.max(8, Math.min(20, Number(e.target.value) || 11)))} /></label>
        <label className="chk"><input type="checkbox" checked={pageNos} onChange={(e) => setPageNos(e.target.checked)} /> {L.pageNos}</label>
        <label>{L.format} <select value={format} onChange={(e) => setFormat(e.target.value as "docx" | "pdf")}><option value="docx">{L.word}</option><option value="pdf">{L.pdf}</option></select></label>
        <span className="grow" />
        <button className="btn ghost" onClick={() => { if (window.confirm(L.confirmClear)) { setBlocks([]); setTitle(""); setSubtitle(""); setAuthor(""); setMade([]); } }}>{L.clear}</button>
        <button className="btn" disabled={busy || (!title.trim() && blocks.length === 0)} onClick={create}>{busy ? L.creating : L.create}</button>
      </div>
      {err && <p className="error">{err}</p>}
      {made.length > 0 && (
        <p className="studio-done">{L.ready} {made.map((f) => <a key={f.url} className="file" href={BASE + f.url} download={f.name}>⬇ {f.name}</a>)}</p>
      )}
      <p className="kb-hint">{L.saved}{!recognitionSupported() ? ` · ${L.noMic}` : ""}</p>
    </section>
  );
}

