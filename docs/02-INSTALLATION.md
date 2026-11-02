# 2. Installation guide

This guide installs Jarvis on one Windows computer. It takes about 15 minutes, most of it downloading.

## Before you start

Install these once:

1. **Python** from python.org. During setup tick **"Add python.exe to PATH"**. Check: open Command Prompt and run `python --version`.
2. **Node.js** (LTS) from nodejs.org. Check: `node --version` and `npm --version`.
3. **Google Chrome** or **Microsoft Edge**.

Copy the Jarvis folder to the computer (for example `D:\JARVIS`). Do not put it in a folder that needs administrator rights.

## Quick start (recommended)

Double-click **`start.bat`**.

The first time it:

1. creates a Python environment in `backend\.venv` and installs the backend packages,
2. installs the front-end packages (`npm install`),
3. builds the front end (`npm run build`),
4. starts the backend (port 8000) and the front end (port 3000),
5. opens **http://127.0.0.1:3000** in your browser.

The first start takes several minutes. Later starts take a few seconds. Two black windows stay open, **Jarvis backend** and **Jarvis frontend**. Close both to stop Jarvis.

## Manual start

Open two Command Prompt windows.

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Front end (development mode):

```bash
cd frontend
npm install
npm run dev
```

Front end (production mode, what `start.bat` uses):

```bash
cd frontend
npm run build
npm start
```

> Do not run `npm run build` while `npm run dev` is running. They share the `.next` folder and the running page breaks. If that happens, stop the dev server, delete `frontend\.next`, and start again.

## First run checklist

1. Open **http://127.0.0.1:3000** in Chrome or Edge. Use `127.0.0.1`, not `localhost`.
2. The header shows **Offline mode** next to the name. That is normal: no API key is set.
3. Type `what is the time` and press Enter. You should get the time.
4. To use the microphone, tap the orb. Chrome asks for permission once: choose **Allow**. If you blocked it by mistake, click the padlock in the address bar and allow the microphone for `127.0.0.1`.
5. The first time you use **Chat with my documents**, a search model of about 80 MB is downloaded once. After that it works without internet.

## Optional settings

Copy `backend\.env.example` to `backend\.env` and fill in only what you need. Every setting is explained in [Configuration and administration](04-CONFIGURATION.md). Restart the backend after changing it.

## Updating

1. Stop Jarvis (close both black windows).
2. Keep a copy of `backend\data` (your contacts, notes, tasks, settings and indexed documents) and `backend\.env`.
3. Replace the program files with the new version, but keep those two.
4. Run `start.bat`. If the package lists changed, delete `backend\.venv` and `frontend\node_modules` first so they are installed again.

## Uninstalling

Close Jarvis and delete the Jarvis folder. Nothing is installed anywhere else, except the optional search model cache in `C:\Users\<you>\.cache\chroma` (about 170 MB), which you can delete too.

## Ports

| Port | Used by |
|---|---|
| 8000 | Backend (API) |
| 3000 | Front end (the page you open) |

Both listen only on `127.0.0.1`, so other computers on the network cannot reach them. If a port is busy, the program that uses it must be closed first. To find it: `netstat -ano | findstr :8000`.

## Installation problems

| What you see | What to do |
|---|---|
| `python` is not recognised | Reinstall Python and tick "Add python.exe to PATH", then open a new Command Prompt. |
| `Unable to copy ... venvlauncher.exe` | The backend is still running and locks the environment. Close the **Jarvis backend** window, then try again. |
| `error while attempting to bind on address ('127.0.0.1', 8000)` | Something is already using port 8000, usually an old Jarvis backend. Close it, or find it with `netstat -ano | findstr :8000` and end that process. |
| Header says **Offline** (and nothing answers) | The backend window is closed or crashed. Start it again (`start.bat`). |
| Blank page or `i is not a function` | A build ran while the dev server was running. Stop it, delete `frontend\.next`, start again. |
| Voice does nothing | Use Chrome or Edge, open `http://127.0.0.1:3000`, and allow the microphone. |

More answers are in the [FAQ and troubleshooting](08-FAQ-TROUBLESHOOTING.md).
