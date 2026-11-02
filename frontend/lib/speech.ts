import type { Lang } from "./api";

export const LOCALE: Record<Lang, string> = { en: "en-US", hi: "hi-IN" };

// The Web Speech API is not in TypeScript's DOM lib, so keep a minimal shape here.
/* eslint-disable @typescript-eslint/no-explicit-any */
type Recognition = any;

export function recognitionSupported(): boolean {
  return typeof window !== "undefined" && !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
}

/**
 * One recognition session = one spoken request. The browser's own end-of-speech detection is very
 * impatient (it cuts you off at the first pause), so we listen continuously and only finish after
 * `silenceMs()` of quiet. onFinal receives everything said in the session, once, right before onEnd.
 */
export function createRecognition(
  lang: Lang,
  handlers: {
    onInterim: (text: string) => void;
    onFinal: (text: string) => void;
    onEnd: () => void;
    onError: (code: string) => void;
  },
  silenceMs: () => number = () => 1800,
): Recognition {
  const Ctor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  const rec = new Ctor();
  rec.lang = LOCALE[lang];
  rec.interimResults = true;
  rec.continuous = true;

  let finals = "";
  let interim = "";
  let timer = 0;
  let aborted = false;

  rec.onresult = (e: any) => {
    interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i];
      if (r.isFinal) finals = (finals + " " + r[0].transcript.trim()).trim();
      else interim += r[0].transcript;
    }
    handlers.onInterim((finals + " " + interim).trim());
    clearTimeout(timer);
    timer = window.setTimeout(() => rec.stop(), silenceMs());
  };
  rec.onerror = (e: any) => handlers.onError(e.error);
  rec.onend = () => {
    clearTimeout(timer);
    const text = (finals + " " + interim).trim();
    finals = interim = "";
    if (text && !aborted) handlers.onFinal(text);
    handlers.onEnd();
  };
  const abort = rec.abort?.bind(rec);
  rec.abort = () => {
    aborted = true; // an abandoned session must not deliver half a sentence
    clearTimeout(timer);
    abort?.();
  };
  return rec;
}

let speakToken = 0;

export function speak(text: string, lang: Lang, onDone: () => void) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return onDone();
  window.speechSynthesis.cancel();
  const token = ++speakToken;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = LOCALE[lang];
  const voice = window.speechSynthesis.getVoices().find((v) => v.lang.replace("_", "-").startsWith(lang));
  if (voice) u.voice = voice;
  // Only a natural end (or failure) reports back; stopSpeaking() invalidates the token.
  u.onend = () => token === speakToken && onDone();
  u.onerror = () => token === speakToken && onDone();
  window.speechSynthesis.speak(u);
}

export function stopSpeaking() {
  speakToken++;
  if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
}

const words = (s: string) => s.toLowerCase().split(/[^\p{L}\p{M}\p{N}]+/u).filter((w) => w.length > 1);

/** True when what the microphone heard is mostly the assistant's own voice coming out of the speakers. */
export function isEcho(heard: string, spoken: string): boolean {
  const h = words(heard);
  if (!h.length) return true;
  const said = new Set(words(spoken));
  return h.filter((w) => said.has(w)).length / h.length >= 0.6;
}

export const STOP_WORDS = /^\W*(?:stop|quiet|enough|shut up|be quiet|चुप|रुको|बस|रुक जाओ)\W*$/i;
