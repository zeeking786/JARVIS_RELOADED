import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
JARVIS_MODEL = os.getenv("JARVIS_MODEL", "").strip() or "claude-haiku-5-5"  # blank in .env means "use the default"
JARVIS_AGENT_MODEL = os.getenv("JARVIS_AGENT_MODEL", "").strip() or "claude-sonnet-5-5"
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs"))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
MUSIC_DIR =os.getenv("MUSIC_DIR", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SENDER_NAME = os.getenv("SENDER_NAME", "").strip()
# "auto": ChromaDB's local MiniLM model if it can be loaded, else keyword embeddings. Force with "default" or "hash".
RAG_EMBEDDER = os.getenv("RAG_EMBEDDER", "auto").strip().lower()
# Host names the API answers to. A web page cannot make the browser send any other Host to this port (DNS rebinding).
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if h.strip()]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]
