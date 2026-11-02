# Security scan report

Scan of the JARVIS_RELOADED repository on 2 November 2026 (commits up to `3007c8a`, plus the fixes listed below).

## Result in one paragraph

**No secrets were found in any commit.** One real weakness was found and fixed (the API answered to any host name, which allows a "DNS rebinding" attack from a web page). Four smaller hardening items were fixed. The dependency checks found no problem that affects how Jarvis uses its packages. Everything else the tools reported is a false alarm or a deliberate design choice, explained below.

## What was checked

| Check | Tool or method | Result |
|---|---|---|
| Secrets in all 4 commits (API keys, tokens, private keys, passwords, `.env`, key files, contact and data files) | Pattern search over every added line and every file name in history | **Clean.** The only password-like text is the placeholder `YOUR_APP_PASSWORD` in the two old scripts |
| Python code (2,956 lines) | Bandit 1.9.4 | 1 high, 3 medium, 18 low reports. **None is a real vulnerability** (see below). 2 items were tidied |
| Python packages (103 pinned versions) | pip-audit 2.10.1 | 5 advisories, all in `chromadb`. **Not applicable** (see below) |
| JavaScript packages | `npm audit --omit=dev` | **0 vulnerabilities** |
| Cross-site requests (a web page you visit calling Jarvis) | Hand-written tests with a foreign origin | **Blocked** for simple requests and for JSON requests (the browser's permission check fails) |
| DNS rebinding (a web page that makes its own host name point at your computer) | Test with a foreign `Host` header | **Was open. Fixed** |
| Email header injection | Test with line breaks in the subject | **Blocked** (refused) |
| File download, uploads, studio pictures | Code review and tests | Names are cleaned, downloads are limited to the output folder, sizes are limited, huge pictures are refused |
| Front end | Search for `innerHTML`, `eval`, `window.open`, links | One fixed inline script (theme), `window.open` uses `noopener`. No user text is inserted as HTML |
| Programs started by commands | Code review | Only fixed names (Notepad, Command Prompt, Chrome, Calculator) and audio files from the music folder. No text is run in a shell |

## Fixed

| # | Severity | Problem | Fix |
|---|---|---|---|
| 1 | Medium (for a local app) | The API answered requests for **any host name**. A malicious web page can use DNS rebinding to make `evil.example` point to `127.0.0.1`, and then read and drive the API as if it were its own page, bypassing the browser's cross-site rules | The API now answers only to `127.0.0.1` and `localhost`. Setting: `ALLOWED_HOSTS`. New test in `backend/tests/test_documents.py` |
| 2 | Low | The page had no browser hardening headers | Added `X-Frame-Options: DENY` (no framing), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and a `Permissions-Policy` that allows only the microphone and camera |
| 3 | Low | Web requests did not check the address starts with `https://` | Weather, currency and Wikipedia requests now refuse anything that is not `https://` |
| 4 | Info | SHA-1 used to make short ids was flagged | Marked `usedforsecurity=False` (it is not used for security) |

Checked afterwards: 84 backend tests pass, the front end type check is clean, and a real Chrome loaded the page, got a reply from the backend, and showed no errors apart from a missing favicon.

## Reported, but not a problem

| Report | Why it is not a risk here |
|---|---|
| **chromadb** PYSEC-2026-311, -3813, -3814, -3815 (CVE-2026-45829, -45830, -45831, -45833) | They affect the **ChromaDB server** (multi-user tenants, remote model repositories, its authorization module). Jarvis uses ChromaDB **inside the program** (`PersistentClient`). It never starts the server, opens no ChromaDB port and loads no remote model repositories. No fixed version exists yet, so keep watching for one |
| Bandit B324 (SHA-1) | Used only for short ids. Now marked as not for security |
| Bandit B310 (`urlopen`) | Every address is built in code with `https://`. Now enforced |
| Bandit B404, B603, B606, B607 (starting programs) | Program names and arguments are fixed in code. Only the music file path comes from the user's folder, and only audio file types are selected |
| Bandit B406 (XML) | The code only **writes** escaped text. It does not read XML from outside |
| Bandit B311 (random) | Used for jokes, coin and dice, not for security |

## Still true, by design (see [Security and privacy](07-SECURITY-PRIVACY.md))

- There is **no login**. Anyone who can use the computer can use Jarvis. Never expose ports 3000 or 8000 to a network.
- "Index folder" reads any folder you type. Data on disk is not encrypted.
- Voice goes through the browser vendor's speech service.

## Recommended next steps

1. Keep the GitHub repository **private** until you have a product name and a licence.
2. In the GitHub repository settings turn on **Secret scanning** and **Push protection**, and **Dependabot alerts**. They are free for private repositories on most plans and catch a future password or a new vulnerable package.
3. Install customers' copies from `backend/requirements.lock.txt` (exact tested versions), not the unpinned `requirements.txt`.
4. Re-run this scan before each release: `bandit -r backend/jarvis backend/main.py`, `pip-audit -r backend/requirements.lock.txt`, and `npm audit --omit=dev` in `frontend`.
5. If you ever add accounts, a hosted version or HTTPS, repeat this review with authentication, session handling and rate limiting in scope.
6. Optional: add a `favicon.ico` (the browser asks for it and gets a 404).
