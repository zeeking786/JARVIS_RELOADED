// Wake-word matching, mirrored by backend/jarvis/settings.py (split_wake) so typed and spoken input behave alike.

const FILLERS = new Set(["hey", "hi", "hello", "ok", "okay", "yo", "ay", "हे", "हेलो", "हैलो", "ओके", "अरे", "सुनो"]);
const TRAILING = new Set(["please", "pls", "प्लीज़", "प्लीज"]);
// Speech recognition often spells the default name differently.
const ALIASES: Record<string, string[]> = {
  jarvis: ["jarvis", "jarvish", "jarves", "jervis", "jarvas", "जार्विस", "जारविस", "जरविस", "जार्विश"],
};

const norm = (w: string) => w.toLowerCase().replace(/[.,!?;:'"“”‘’।\-]/g, "");

function lev(a: string, b: string): number {
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    }
    prev = cur;
  }
  return prev[b.length];
}

function isName(tok: string, want: string): boolean {
  const t = norm(tok);
  if (!t) return false;
  if ((ALIASES[want] ?? [want]).includes(t)) return true;
  return want.length >= 5 && t.length >= 4 && lev(t, want) <= 1;
}

/** "Hey Jarvis, good morning" -> {matched, rest: "good morning"}. The name only counts at the start or the end. */
export function matchWake(text: string, name: string): { matched: boolean; rest: string } {
  const want = name.split(/\s+/).map(norm).filter(Boolean);
  const words = text.trim().split(/\s+/).filter(Boolean);
  const k = want.length;
  if (!words.length || !k) return { matched: false, rest: text };
  const hit = (seg: string[]) => seg.length === k && seg.every((w, i) => isName(w, want[i]));

  let i = 0;
  while (i < words.length && FILLERS.has(norm(words[i]))) i++;
  if (hit(words.slice(i, i + k))) {
    return { matched: true, rest: words.slice(i + k).join(" ").replace(/^[\s,.:;!-]+/, "").trim() };
  }

  let j = words.length;
  while (j > 0 && TRAILING.has(norm(words[j - 1]))) j--;
  if (j - k >= 0 && hit(words.slice(j - k, j))) {
    let start = j - k;
    while (start > 0 && FILLERS.has(norm(words[start - 1]))) start--;
    return { matched: true, rest: words.slice(0, start).join(" ").replace(/[\s,.:;!-]+$/, "").trim() };
  }
  return { matched: false, rest: text };
}
