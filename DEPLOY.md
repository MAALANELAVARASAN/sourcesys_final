# Tim — Render Deployment Guide

## Pre-Deploy Fixes (do these before pushing to GitHub)

### Fix 1 — Remove insecure OAuth transport flag for production

In `client/app/__init__.py`, the line:
```python
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
```
must only run in development, not on Render (which uses HTTPS).

Change it to:
```python
if os.getenv("ENVIRONMENT") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
```

---

### Fix 2 — Make ChromaDB path use env variable

In whatever file initializes ChromaDB (likely `backend/rag/embedder.py` or `pipeline.py`),
make sure it reads from config instead of a hardcoded path:

```python
from backend.core.config import settings
import os

os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)

# Then use settings.CHROMA_DB_PATH when creating your Chroma client
# e.g. chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
```

On Render free tier `CHROMA_DB_PATH` is set to `/tmp/chroma_db` (writable, resets on redeploy).

---

### Fix 3 — Add `__init__.py` files at package roots

Render runs from the project root, so Python needs these to exist (even if empty):

```powershell
# Run in your tim/ root
New-Item -ItemType File -Path "backend\__init__.py" -Force
New-Item -ItemType File -Path "client\__init__.py" -Force
```

---

### Fix 4 — Tighten CORS after deploy

In `backend/main.py`, after you have your Render client URL, change:
```python
allow_origins=["*"],
```
to:
```python
allow_origins=["https://tim-client.onrender.com"],
```

---

## Deploy Steps

### Step 1 — Gitignore
Create `.gitignore` in project root if you don't have one:
```
__pycache__/
*.pyc
.env
chroma_db/
uploads/
*.db
.venv/
poetry.lock
```

### Step 2 — Push to GitHub
```powershell
cd C:\Users\TYSON\Desktop\Projects\tim
git init
git add .
git commit -m "chore: prepare for Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/tim.git
git push -u origin main
```

### Step 3 — Deploy on Render
1. Go to https://render.com → sign up free (no card needed)
2. Dashboard → **New** → **Blueprint**
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates:
   - `tim-backend` (FastAPI)
   - `tim-client` (Flask)
   - `tim-db` (PostgreSQL for backend)
   - `tim-client-db` (PostgreSQL for Flask/users)

### Step 4 — Add secret env vars in Render dashboard
After services are created, go to each service → **Environment** tab:

**tim-backend** (add these manually):
| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | your key |
| `GROQ_API_KEY` | your key |
| `NOMIC_API_KEY` | your key |

**tim-client** (add these manually):
| Key | Value |
|-----|-------|
| `FLASK_SECRET_KEY` | any long random string |
| `GOOGLE_CLIENT_ID` | from Google Cloud Console (if using OAuth) |
| `GOOGLE_CLIENT_SECRET` | from Google Cloud Console (if using OAuth) |

### Step 5 — Update cross-service URLs
Once both services have deployed URLs:
- Go to `tim-client` → Environment → update `BACKEND_URL` to your actual backend URL
- Go to `backend/main.py` → update CORS `allow_origins` to your client URL
- Commit + push → Render auto-redeploys

---

## After Deployment

| Thing | Detail |
|-------|--------|
| Cold starts | Free tier sleeps after 15 min idle; first request ~30s |
| ChromaDB | Resets on every redeploy (stored in `/tmp`) — re-upload docs after deploy |
| DB expiry | Render free PostgreSQL expires after 90 days |
| Logs | Render dashboard → service → **Logs** tab |

---

## Common Errors

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'backend'` | Add empty `backend/__init__.py` |
| `ModuleNotFoundError: No module named 'client'` | Add empty `client/__init__.py` |
| `pydantic_settings validation error` | A required env var is missing — check all keys in `Settings` class |
| `FLASK_SECRET_KEY missing` | Add it in Render dashboard → tim-client → Environment |
| `CORS error in browser` | Update `allow_origins` in `backend/main.py` with client URL |
| `OAuth InsecureTransportError` | Apply Fix 1 above (OAUTHLIB env var guarded by ENVIRONMENT) |
