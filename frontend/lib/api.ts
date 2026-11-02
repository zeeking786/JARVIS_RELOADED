export type Lang = "en" | "hi";

export type Action =
  | { type: "sleep" }
  | { type: "opened"; name: string; url?: string }
  | { type: "chart"; kind: "pie" | "bar"; title: string; data: Record<string, number> }
  | { type: "camera" }
  | { type: "spiral" }
  | { type: "compose_email" }
  | { type: "files"; files: { name: string; url: string }[] }
  | { type: "form"; template: string; title: string; fields: FormField[] }
  | { type: "timer"; seconds: number; label: string }
  | { type: "mail_draft"; draft: MailDraft }
  | { type: "rename"; name: string }
  | { type: "rag"; sources: RagSource[]; mode: "claude" | "extractive" }
  | { type: "kb_mode"; on: boolean }
  | { type: "studio" }
  | { type: "reply_options"; options: { label: string; send: string }[] }
  | { type: "read" }
  | { type: "ai" }
  | { type: "wiki" };

export interface FormField {
  key: string;
  label: string;
  multiline: boolean;
  options: string[];
  default: string;
  required: boolean;
}

export interface MailDraft {
  to: string[];
  cc: string[];
  bcc: string[];
  to_emails: string[];
  cc_emails: string[];
  bcc_emails: string[];
  subject: string;
  body: string;
  via: "smtp" | "gmail";
}

export interface RagSource {
  n: number;
  name: string;
  snippet: string;
}

export interface CommandResponse {
  dictate?: boolean; // the next answer is long (email subject / message): wait longer for pauses
  reply: string;
  action: Action | null;
  needs_confirm: boolean;
}

export interface Health {
  ok: boolean;
  brain: "claude" | "offline";
  model: string | null;
  email: boolean;
  name: string;
}

export const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json" },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `Request failed (${res.status})`);
  return data as T;
}

export const getHealth = () => request<Health>("/api/health");

export const sendCommand = (text: string, lang: Lang, session: string) =>
  request<CommandResponse>("/api/command", {
    method: "POST",
    body: JSON.stringify({ text, lang, session }),
  });

export const sendEmail = (to: string, subject: string, body: string, lang: Lang) =>
  request<{ reply: string }>("/api/email", {
    method: "POST",
    body: JSON.stringify({ to, subject, body, lang }),
  });

export interface Uploaded {
  name: string;
  kind: string;
  size: number;
  truncated: boolean;
  reply: string;
}

export async function uploadFile(file: File, lang: Lang, session: string): Promise<Uploaded> {
  const form = new FormData();
  form.append("file", file);
  form.append("session", session);
  form.append("lang", lang);
  const res = await fetch(BASE + "/api/upload", { method: "POST", body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `Upload failed (${res.status})`);
  return data as Uploaded;
}

export const removeAttachment = (name: string, session: string) =>
  request<{ ok: boolean }>(`/api/attachments/${encodeURIComponent(name)}?session=${encodeURIComponent(session)}`, {
    method: "DELETE",
  });

export const makeFile = (template: string, values: Record<string, string>, lang: Lang) =>
  request<{ reply: string; files: { name: string; url: string }[] }>("/api/make", {
    method: "POST",
    body: JSON.stringify({ template, values, lang }),
  });

export const setAssistantName = (name: string) =>
  request<{ name: string }>("/api/name", { method: "POST", body: JSON.stringify({ name }) });

export const sendMail = (m: { to: string[]; cc: string[]; bcc: string[]; subject: string; body: string }, lang: Lang, session: string) =>
  request<{ reply: string; url: string | null }>("/api/mail/send", { method: "POST", body: JSON.stringify({ ...m, lang, session }) });

// ---- documents (RAG)
export interface KbInfo {
  embedder: "minilm" | "keyword";
  answers: "claude" | "extractive";
  chunks: number;
  sources: { name: string; chunks: number; origin: string }[];
}

export interface KbJob {
  state: "running" | "done" | "error";
  done: number;
  total: number;
  current?: string;
  indexed: number;
  unchanged: number;
  chunks: number;
  skipped?: { name: string; reason: string }[];
  limited?: boolean;
  error?: string;
}

export const kbInfo = () => request<KbInfo>("/api/kb");

export async function kbUpload(files: File[]): Promise<KbInfo & { results: { name: string; chunks: number; skipped?: string }[] }> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(BASE + "/api/kb/upload", { method: "POST", body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `Upload failed (${res.status})`);
  return data;
}

export const kbFolder = (path: string) => request<{ job: string }>("/api/kb/folder", { method: "POST", body: JSON.stringify({ path }) });
export const kbJob = (id: string) => request<KbJob>(`/api/kb/jobs/${id}`);
export const kbDelete = (name: string) => request<KbInfo>(`/api/kb/source?name=${encodeURIComponent(name)}`, { method: "DELETE" });
export const kbClear = () => request<KbInfo>("/api/kb/clear", { method: "POST" });
export const kbMode = (on: boolean, session: string) => request<{ on: boolean }>("/api/kb/mode", { method: "POST", body: JSON.stringify({ on, session }) });

// ---- document studio
export interface DocSpec {
  title: string;
  subtitle: string;
  author: string;
  font: string;
  font_size: number;
  page_numbers: boolean;
  format: "docx" | "pdf";
  blocks: {
    type: string; text: string; level: number; header: boolean; data: string; width: number; caption: string; align: string;
    items: string[]; rows: string[][];
  }[];
}

export const buildDoc = (spec: DocSpec, lang: Lang) =>
  request<{ reply: string; files: { name: string; url: string }[] }>("/api/doc/build", { method: "POST", body: JSON.stringify({ ...spec, lang }) });
