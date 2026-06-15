# Tim FAQ — AI-Powered Knowledge Base FAQ Generator

Tim FAQ lets users upload documents (PDF, DOCX, TXT, MD) or ask free-form questions and automatically generates a direct answer plus a set of related FAQ pairs. It combines a Flask web app (user-facing client) with a FastAPI backend that runs a RAG (Retrieval-Augmented Generation) pipeline backed by ChromaDB and LLMs (Gemini, with Groq as fallback).

---

## 1. Architecture Overview

```
User Browser
    │
    ▼
Flask Client (client/)  — http://127.0.0.1:5000
    ├── /login, /signup, Google OAuth  → SQLite/Postgres (users, chats, messages, FAQs)
    ├── /chat                          → renders chat.html
    │       │
    │       │  internal HTTP call (JS fetch from chat.html → Flask route → requests.post)
    │       ▼
    │   FastAPI Backend (backend/)  — http://127.0.0.1:8000
    │       ├── /api/v1/faq/generate, /generate-all, /translate, /export/pdf
    │       ├── RAG pipeline:
    │       │     ├── embed   → ChromaDB (via Nomic embeddings)
    │       │     ├── retrieve → ChromaDB similarity search
    │       │     └── generate → Gemini 2.5 Flash (fallback: Groq Llama 3.3 70B)
    │       └── returns { source, direct_answer, faq_pairs, total }
    │
    └── /admin → user/chat/FAQ stats dashboard
```

Two separate processes run side by side:
- **FastAPI backend** (`backend/`) — stateless RAG/AI service, port 8000.
- **Flask client** (`client/`) — user accounts, chat history, UI, port 5000. Talks to the backend over HTTP using `requests`.

---

## 2. Project Structure

```
tim/
├── .env                      # environment variables (secrets, API keys)
├── pyproject.toml            # Poetry dependency manifest
├── requirements.txt          # pip-style dependency list (legacy/alt)
├── README.md                 # setup/run instructions
├── chroma_db/                # ChromaDB persistent vector store (auto-generated)
│
├── backend/                  # FastAPI service — RAG + FAQ generation
│   ├── main.py               # FastAPI app entrypoint
│   ├── api/
│   │   ├── routes/
│   │   │   ├── faq.py        # FAQ generation, translation, export, delete endpoints
│   │   │   └── health.py     # health check endpoint
│   │   └── middleware/
│   │       └── auth.py       # (currently empty/unused)
│   ├── core/
│   │   ├── config.py         # Settings (env vars) via pydantic-settings
│   │   └── db.py              # SQLAlchemy engine/session (Postgres)
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response models
│   └── rag/
│       ├── embedder.py       # Embedding + ChromaDB vectorstore management
│       ├── retriever.py      # Similarity search / chunk retrieval
│       ├── generator.py      # LLM prompt construction + response parsing
│       └── pipeline.py       # Orchestrates embed → retrieve → generate
│
├── client/                   # Flask web app — UI, auth, chat history
│   ├── run.py                # Flask entrypoint (alt)
│   ├── client.db             # SQLite DB (default, if CLIENT_DATABASE_URL unset)
│   └── app/
│       ├── __init__.py       # create_app() factory, blueprint registration
│       ├── run.py            # Flask entrypoint (alt)
│       ├── models/
│       │   ├── user.py       # User model (Flask-Login, bcrypt password hash)
│       │   ├── chat.py       # Chat, Message, FAQCollection, FAQPair, Document models
│       │   └── __init__.py
│       ├── routes/
│       │   ├── auth.py       # signup/login/logout
│       │   ├── google_auth.py # Google OAuth login
│       │   ├── chat.py        # chat CRUD, FAQ generation calls to backend, rating/editing
│       │   └── admin.py       # admin dashboard (user management, stats)
│       ├── static/
│       │   ├── css/style.css # "Neural Glitch" theme (dark cyberpunk + light theme toggle)
│       │   └── js/            # (currently empty)
│       └── templates/
│           ├── base.html      # layout, sidebar, theme toggle, star canvas
│           ├── signup.html    # landing/marketing page + signup form
│           ├── login.html      # login form + Google OAuth
│           ├── chat.html       # main chat UI (file upload, FAQ generation, voice, translation)
│           ├── admin.html      # admin stats + user management table
│           └── share.html      # public read-only FAQ share page
│
├── ideas/
│   └── str.txt               # architecture sketch (ASCII diagram)
└── tests/                     # (empty — no tests yet)
```

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Frontend | Flask + Jinja2 templates |
| Frontend DB | SQLite (default) or Postgres via `CLIENT_DATABASE_URL` |
| Backend DB | Postgres via `DATABASE_URL` (SQLAlchemy, currently set up but not actively used by FAQ routes) |
| Vector store | ChromaDB (persisted to `./chroma_db`) |
| Embeddings | Nomic (`nomic-embed-text-v1.5` via `langchain-nomic`) |
| LLMs | Gemini 2.5 Flash (primary), Groq Llama 3.3 70B (fallback) |
| Auth | Flask-Login + bcrypt; Google OAuth via Flask-Dance |
| File parsing | `pypdf` (PDF), `python-docx` (DOCX) |
| PDF export | ReportLab |
| Text splitting | LangChain `RecursiveCharacterTextSplitter` |

---

## 4. Environment Variables (`.env`)

Required by `backend/core/config.py` and `client/app/__init__.py`:

| Variable | Used by | Notes |
|---|---|---|
| `FASTAPI_HOST`, `FASTAPI_PORT` | backend | default `127.0.0.1:8000` |
| `FLASK_HOST`, `FLASK_PORT` | client | default `127.0.0.1:5000` |
| `FLASK_SECRET_KEY` | client | required, used for sessions |
| `DATABASE_URL` | backend | Postgres connection string (required by `Settings`, even if unused) |
| `CLIENT_DATABASE_URL` | client | optional; falls back to local SQLite `client.db` |
| `GEMINI_API_KEY` | backend | primary LLM |
| `GROQ_API_KEY` | backend | fallback LLM |
| `OPENROUTER_API_KEY` | backend | optional, currently unused in code |
| `NOMIC_API_KEY` | backend | embeddings |
| `CHROMA_DB_PATH` | backend | default `./chroma_db` |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | client | Google OAuth login |

---

## 5. Running the Project

```powershell
# 1. Activate the virtual environment
"C:\Users\TYSON\AppData\Local\pypoetry\Cache\virtualenvs\tim-rf3smOIg-py3.13\Scripts\activate.ps1"

# 2. Start the FastAPI backend (port 8000)
python -m backend.main

# 3. Start the Flask client (port 5000)
python -m client.run
```

Visit `http://127.0.0.1:5000`. The Flask app redirects to `/login` (unauthenticated) or `/chat` (authenticated).

> The first user to register via Google OAuth is automatically promoted to `admin`.

---

## 6. Backend (FastAPI) — `backend/`

### 6.1 `main.py`
Creates the FastAPI app, adds CORS (allowing the Flask client at `127.0.0.1:5000`), and mounts two routers under `/api/v1`:
- `faq` (tag: FAQ)
- `health` (tag: Health)

### 6.2 Routes — `api/routes/health.py`

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Returns `{"status": "ok", "version": "1.0.0"}` |

### 6.3 Routes — `api/routes/faq.py`

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/faq/debug` | Returns total chunks and distinct `doc_id`s currently in ChromaDB (debug only) |
| POST | `/api/v1/faq/generate` | Generate FAQs from a prompt and/or up to 10 uploaded files (single-document focus) |
| POST | `/api/v1/faq/generate-all` | Generate FAQs across **all** uploaded files independently, then combine |
| POST | `/api/v1/faq/translate` | Translate a direct answer + FAQ pairs into a target language |
| POST | `/api/v1/faq/export/pdf` | Render a direct answer + FAQ pairs as a styled PDF (ReportLab) |
| POST | `/api/v1/faq/delete-doc` | Delete all ChromaDB chunks for a given `doc_id` |

**File handling rules** (`read_files`, `extract_text`):
- Max 10 files per request, 10 MB each.
- Supported extensions: `.pdf`, `.docx`/`.doc`, `.txt`, `.md`.
- PDF text extracted via `pypdf`; DOCX via `python-docx`; txt/md decoded as UTF-8.

**`/faq/generate` logic:**
1. Extract text from any uploaded files.
2. If the prompt mentions a specific filename (matched against filename variants), isolate that file.
3. Otherwise, if files were uploaded, use the **last uploaded file** only.
4. If no prompt was given but a file is present, default prompt = "Generate detailed FAQs based on the content of the uploaded document."
5. Calls `run_pipeline(prompt, file_texts)`.

**`/faq/generate-all` logic:**
1. Requires at least one file.
2. If the prompt names a specific file, redirects to single-file `run_pipeline`.
3. Otherwise calls `run_pipeline_all(file_texts, prompt)` — each document is embedded and processed independently, producing its own mini-FAQ set, then all results are merged.

**`/faq/export/pdf`** builds a PDF with a teal-accented title, the direct answer, and numbered Q/A pairs using custom ReportLab paragraph styles.

### 6.4 Core — `core/config.py`
`Settings` (pydantic-settings) loads all environment variables listed in §4 from `.env`. `extra = "ignore"` allows unused vars in `.env` without error.

### 6.5 Core — `core/db.py`
Sets up a SQLAlchemy `engine`, `SessionLocal`, and `Base` against `DATABASE_URL` (Postgres), plus a `get_db()` dependency generator. Not currently wired into any FAQ route — likely scaffolding for future backend-side persistence.

### 6.6 Models — `models/schemas.py`

| Model | Fields | Purpose |
|---|---|---|
| `UnifiedFAQRequest` | `prompt`, `filename?`, `content?` | (defined, not directly used by current routes) |
| `FAQPair` | `question`, `answer` | A single Q&A pair |
| `FAQResponse` | `source` (`knowledge_base` \| `ai_knowledge`), `direct_answer`, `faq_pairs`, `total` | Standard response shape for all generation endpoints |

### 6.7 RAG — `rag/embedder.py`
- Initializes `NomicEmbeddings` (model `nomic-embed-text-v1.5`) and a `Chroma` vectorstore persisted at `CHROMA_DB_PATH`.
- `embed_document(text, doc_id)`: deletes any existing chunks for `doc_id` (avoids duplicates on re-upload), splits text into 500-char chunks with 50-char overlap (`RecursiveCharacterTextSplitter`), and adds them to Chroma with metadata `{"doc_id": doc_id}`.
- `delete_document(doc_id)`: removes all chunks for a given `doc_id`.

> Note: `doc_id` is currently the **filename** — re-uploading a file with the same name overwrites its embeddings.

### 6.8 RAG — `rag/retriever.py`
- `RELEVANCE_THRESHOLD = 0.75` — chunks with a similarity distance score above this are discarded as irrelevant.
- `retrieve_chunks(query, doc_ids=None, k=6)`:
  - If no `doc_ids`, does a global similarity search across the whole vectorstore.
  - If `doc_ids` given, searches each doc's chunks separately (filtered by metadata), merges and sorts by score, returns top `k * len(doc_ids)`.
- `retrieve_chunks_per_doc(query, doc_ids, k_per_doc=6)`: returns a `dict[doc_id -> list[chunks]]`, used by the "generate-all" pipeline so each document gets independent representation.

### 6.9 RAG — `rag/generator.py`
- `get_gemini()` / `get_groq()`: construct LangChain chat model clients.
- `invoke_llm(prompt_text)`: tries Gemini first; on any exception, falls back to Groq; raises `RuntimeError` if both fail.
- `generate_full_response_from_chunks(prompt, chunks)`: builds a context-grounded prompt and asks the LLM to return `ANSWER:` + 5 `Q/A` pairs in a fixed format.
- `generate_full_response_from_prompt(prompt)`: same format but with no document context (pure LLM knowledge) — used as fallback.
- `generate_full_response_from_all_docs(doc_chunks)`: iterates each document's chunks, generates a per-document FAQ set, and concatenates summaries + all FAQ pairs.
- `translate_response(direct_answer, faq_pairs, target_language)`: re-sends the existing answer/FAQs to the LLM with a translation instruction, preserving the same format.
- `parse_full_response(raw)`: parses the LLM's fixed-format text output into `(direct_answer, list[FAQPair])`. If no `ANSWER:` line is found, defaults to a generic message.

### 6.10 RAG — `rag/pipeline.py`
- `NO_INFO_SIGNALS`: list of phrases (e.g. "does not contain", "not mentioned") used to detect when the LLM says the context doesn't answer the question.
- `is_irrelevant_answer(answer)`: checks the direct answer against `NO_INFO_SIGNALS`.

**`run_pipeline(prompt, file_texts)`** (used by `/faq/generate`):
1. Embeds any provided files (registers their `doc_id`s).
2. Retrieves relevant chunks (scoped to those `doc_id`s if files were provided).
3. If files were provided but no chunks pass the relevance threshold → fallback to `generate_full_response_from_prompt` (`source: ai_knowledge`).
4. If chunks exist → generate from chunks. If the answer is flagged as "irrelevant" by `is_irrelevant_answer` → fallback to pure-prompt generation.
5. Otherwise return `source: knowledge_base` with the chunk-grounded answer.
6. If no chunks at all (no files, or empty vectorstore) → fallback to pure-prompt generation.

**`run_pipeline_all(file_texts, prompt)`** (used by `/faq/generate-all`):
1. Embeds all provided files.
2. Retrieves chunks **per document** (6 per doc).
3. If zero chunks across all docs → fallback to pure-prompt generation.
4. Otherwise calls `generate_full_response_from_all_docs` and returns `source: knowledge_base` with the combined answer and all FAQ pairs.

---

## 7. Frontend (Flask) — `client/`

### 7.1 App factory — `app/__init__.py`
- Loads `.env`, sets `OAUTHLIB_INSECURE_TRANSPORT=1` (allows HTTP OAuth callbacks for local dev).
- Configures SQLAlchemy: uses `CLIENT_DATABASE_URL` if set, otherwise falls back to local SQLite `client.db`.
- Registers blueprints: Google OAuth (`google_bp`, `callback_bp`), `auth`, `chat`, `admin`.
- Calls `db.create_all()` on startup (auto-creates tables if missing).
- Root `/` redirects to `/chat` (if logged in) or `/login`.
- `load_user(user_id)` — Flask-Login user loader.

### 7.2 Models — `app/models/`

**`user.py` — `User`**
| Field | Type | Notes |
|---|---|---|
| `id` | int, PK | |
| `username` | string, unique | |
| `email` | string, unique | |
| `password_hash` | string | bcrypt hash; `"google_oauth"` placeholder for OAuth-only accounts |
| `role` | string | `"user"` or `"admin"`; first-ever user via Google OAuth becomes `admin` |
| `created_at` | datetime | |

**`chat.py`**

| Model | Key fields | Relationships |
|---|---|---|
| `Chat` | `id`, `user_id`, `title`, `created_at`, `updated_at` | has many `Message`, `FAQCollection` (cascade delete) |
| `Message` | `id`, `chat_id`, `role` (`user`/`assistant`), `content`, `created_at` | belongs to `Chat` |
| `FAQCollection` | `id`, `chat_id`, `source`, `direct_answer`, `created_at` | has many `FAQPair` (cascade delete) |
| `FAQPair` | `id`, `collection_id`, `question`, `answer`, `rating` (`up`/`down`/null) | belongs to `FAQCollection` |
| `Document` | `id`, `user_id`, `filename`, `doc_id`, `chunk_count`, `uploaded_at` | (defined; not currently populated by any route) |

### 7.3 Routes — `app/routes/auth.py`

| Method | Path | Description |
|---|---|---|
| GET/POST | `/signup` | Create account (username, email, password); password hashed with bcrypt |
| GET/POST | `/login` | Email + password login via Flask-Login |
| GET | `/logout` | Logs out current user |

### 7.4 Routes — `app/routes/google_auth.py`
- Configures a Flask-Dance Google OAuth blueprint (`google_bp`) with `openid`, `userinfo.email`, `userinfo.profile` scopes.
- `/login/google/callback` (`callback_bp`): on success, fetches user info from Google, finds or creates a `User` (first-ever user becomes `admin`, OAuth users get `password_hash="google_oauth"`), logs them in, and redirects to a new chat.

### 7.5 Routes — `app/routes/chat.py`
`FASTAPI_URL = "http://127.0.0.1:8000/api/v1"` — all FAQ generation is proxied to the backend.

| Method | Path | Description |
|---|---|---|
| GET | `/chat` | Redirects to the most recently updated chat, or creates a new one |
| GET | `/chat/new` | Creates a new `Chat` and redirects to it |
| GET | `/chat/<chat_id>` | Renders `chat.html` for a given chat |
| POST | `/chat/<chat_id>/delete` | Deletes a chat (cascades messages/collections) |
| POST | `/chat/<chat_id>/rename` | Renames a chat (max 100 chars) |
| POST | `/chat/<chat_id>/generate` | Forwards prompt+files to backend `/faq/generate`, saves result |
| POST | `/chat/<chat_id>/generate-all` | Forwards prompt+files to backend `/faq/generate-all`, saves result |
| POST | `/chat/faq/<pair_id>/rate` | Sets/toggles a FAQ pair's rating (`up`/`down`) |
| POST | `/chat/faq/<pair_id>/edit` | Edits a FAQ pair's question/answer text |
| GET | `/share/<collection_id>` | Public (no login) read-only view of an `FAQCollection` |
| POST | `/chat/export/pdf` | Proxies to backend `/faq/export/pdf`, streams PDF back to browser |
| GET | `/chat/<chat_id>/history` | Returns full chat history (messages + FAQ collections) as JSON |

**`_call_fastapi(endpoint, prompt, files)`**: builds a multipart request and posts it to the backend with a 180-second timeout; raises with backend error detail on non-200.

**`_save_response(chat_obj, prompt, data)`**: persists the user message, assistant message, `FAQCollection`, and each `FAQPair` to the database; auto-titles new chats from the first prompt; returns a JSON-friendly dict for the frontend.

### 7.6 Routes — `app/routes/admin.py`
Protected by `@login_required` + custom `@admin_required` decorator (checks `current_user.role == "admin"`).

| Method | Path | Description |
|---|---|---|
| GET | `/admin` | Dashboard: total users/admins/regular users, total chats, FAQs, docs, FAQ collections, most-active user (by chat count) |
| POST | `/admin/delete/<user_id>` | Delete a user (cannot delete self) |
| POST | `/admin/promote/<user_id>` | Promote user to admin |
| POST | `/admin/demote/<user_id>` | Demote admin to user (cannot demote self) |

### 7.7 Templates

| Template | Purpose |
|---|---|
| `base.html` | Shared layout: sidebar (chat list, admin link, theme toggle, user info), navbar for logged-out users, animated star-field canvas, flash messages, theme persistence (localStorage) |
| `signup.html` | Marketing landing page + signup form + Google OAuth |
| `login.html` | Login form + Google OAuth |
| `chat.html` | Main chat interface — see §7.8 |
| `admin.html` | Stats grid + most-active-user highlight + user management table (promote/demote/delete) |
| `share.html` | Public, unauthenticated view of a single FAQ collection |

### 7.8 `chat.html` — Main Chat UI
Key client-side features (vanilla JS):
- **History loading**: fetches `/chat/<id>/history` and renders user/assistant message bubbles, including FAQ cards with source badges (`📚 Knowledge Base` vs `🤖 Gemini AI`).
- **File attachments**: drag/select up to 5 files (10 MB each), shown as removable tags; reveals two action buttons once files are attached:
  - **Generate FAQ** (current file) → `/chat/<id>/generate`
  - **Overall FAQ** (all files) → `/chat/<id>/generate-all`
- **FAQ rating**: 👍/👎 buttons per FAQ pair → `/chat/faq/<id>/rate`.
- **Inline editing**: `startEdit(pairId)` swaps a FAQ card's question/answer into editable `<input>`/`<textarea>` fields with Save/Cancel buttons. `saveEdit(pairId)` validates both fields are non-empty, POSTs to `/chat/faq/<id>/edit`, and restores the card with the updated text and edit (✏️) button. `cancelEdit(pairId, origQ, origA)` restores the original text without saving.
- **Copy**: `copyToClipboard(btn)` formats the direct answer plus every "Qn: ... / An: ..." pair into plain text, copies via `navigator.clipboard.writeText`, and briefly shows "✅ Copied" before reverting to "📋 Copy" after 2 seconds.
- **Export PDF**: `exportPDF(btn)` shows "⏳ Exporting...", POSTs the current answer/FAQs to `/chat/export/pdf` (which proxies to the backend), downloads the returned PDF as `faqs.pdf`, and shows "✅ Downloaded" (or "❌ Failed" on error) for 2 seconds before reverting to "📄 PDF".
- **Share**: `shareCollection(collectionId)` copies a public share URL (`/share/<collection_id>`) to the clipboard and alerts the user with the link.
- **Translation**: a language dropdown (Tamil, Hindi, Spanish, French, Arabic, German, Japanese, Chinese) calls the backend `/faq/translate` endpoint directly from the browser and rewrites the displayed answer/FAQs in place.
- **Text-to-speech ("Read aloud")**: `readAloud(btn)` uses the Web Speech API (`SpeechSynthesisUtterance`).
  - Acts as a toggle: if already reading, clicking cancels speech (`speechSynth.cancel()`) and resets the button label back to "🔊 Read".
  - Builds a single utterance from the direct answer plus every FAQ pair, phrased as "Question N: ... Answer: ...".
  - Utterance language is mapped from the selected translation language (same `langMap` as voice input), defaulting to `en-US`; rate is fixed at `0.9`.
  - Button label switches to "⏹ Stop" while speaking and reverts to "🔊 Read" automatically when speech ends (`onend`).
- **Voice input (audio transcriber)**: `toggleMic()` button uses `SpeechRecognition`/`webkitSpeechRecognition`.
  - Alerts "Try Chrome" if the browser doesn't support speech recognition.
  - Acts as a toggle: clicking while recording calls `recognition.stop()`.
  - Recognition language follows the selected translation language (same `langMap` as text-to-speech, e.g. Tamil → `ta-IN`), defaulting to `en-US`.
  - `continuous = false`, `interimResults = true` — live partial transcripts stream into the prompt textarea as the user speaks (`onresult` overwrites the textarea value and calls `autoResize`).
  - `onstart`: adds a `mic-active` class to the mic button and changes the placeholder to "Listening...".
  - `onend`: removes `mic-active` and restores the original placeholder.
  - `onerror`: resets state and shows an alert with the error — except when the error is `"aborted"` (avoids an alert when the user manually stops recording).
- **Theme toggle**: persisted dark/light theme via `localStorage`.

### 7.9 Styling — `static/css/style.css`
A custom dark "Neural Glitch" theme: deep void backgrounds, cyan (`--em`) and magenta (`--indigo`) neon accents, animated aurora gradients, scanline grid overlay, glassmorphism cards, and angular `clip-path` buttons/inputs. Includes a full light-theme override (`body.light-theme`) and responsive breakpoints down to mobile (collapsible sidebar).

---

## 8. Visual Walkthrough — UI Screenshots

### 8.1 Landing Page (Signup/Login)
The homepage showcases Tim FAQ's key features with a dark "Neural Glitch" theme — cyan neon accents, animated aurora backgrounds, and feature cards highlighting multi-file upload, Gemini AI + Groq, vector search, export/share, multi-language support, and voice input.

![Tim FAQ Landing Page - Dark Theme](sec7.png)

### 8.2 Login Page
Clean authentication screen with email + password fields and Google OAuth integration. Same neon cyberpunk aesthetic with a purple gradient login button and responsive form layout.

![Tim FAQ Login Page](src2.png)

### 8.3 Empty Chat (New Chat State)
Shows the main chat interface when no messages exist. Left sidebar displays chat history, theme toggle (Light Mode), admin panel link, and user info. Center pane prompts "Ask anything or upload a document to generate FAQs" with file attachment and voice input buttons at the bottom.

![Tim FAQ Empty Chat - Light Theme](src4.png)

**Dark theme variant:**

![Tim FAQ Empty Chat - Dark Theme](src3.png)

### 8.4 Chat with FAQ Generation Results
After uploading a document or asking a question, the AI returns:
- A **source badge** (cyan "📚 KNOWLEDGE BASE" for document-grounded, or pink "🤖 GEMINI AI" for pure LLM).
- A **direct answer** — the AI's summary of your query.
- **Related FAQs** — numbered Q/A pairs (Q1, Q2, Q3, etc.) with:
  - Edit (✏️) button to modify question/answer inline.
  - Thumbs up/down (👍👎) rating buttons to provide feedback.
- **Action buttons** at the bottom: Copy, PDF, Read (text-to-speech), and Share (public link).

Example showing AI knowledge (no document):

![Tim FAQ Chat - AI-Generated Response](src6.png)

Scrolling down reveals more FAQ pairs:

![Tim FAQ Chat - Additional FAQs with Translations](src7.png)

### 8.5 Translation & Multi-Language Support
Select a language from the dropdown (Tamil, Hindi, Spanish, French, Arabic, German, Japanese, Chinese). The UI re-renders the direct answer and all FAQ pairs in the chosen language. Title and chat history also update in real time.

![Tim FAQ Chat - Tamil Translation](src8.png)

The language selector is visible in the top-right corner. Selecting a language triggers a call to the backend `/faq/translate` endpoint, which re-writes the answer/FAQs in-place without needing to regenerate from scratch.

### 8.6 Admin Dashboard
Admins see a stats grid showing:
- **Total Users**, **Total Chats**, **FAQs Generated**
- **Docs Uploaded**, **FAQ Sessions**, **Admin Count**
- **Most Active User** (by number of chats)

Below is an **All Users** table with columns for ID, Username, Email, Role (Admin/User), Join Date, and Actions (Promote/Demote/Delete). Admins can promote users to admin or demote/delete them (cannot delete self).

![Tim FAQ Admin Dashboard](src5.png)

### 8.7 AI-Powered Answer (Knowledge Base)
When documents are uploaded, the system embeds them into ChromaDB and retrieves the most relevant chunks using vector similarity. The AI uses these chunks to ground its answer, marked with a **"📚 KNOWLEDGE BASE"** badge (cyan).

![Tim FAQ Chat - Knowledge Base Response](src1.png)

---

## 9. End-to-End Request Flow Example

**Scenario:** User uploads `policy.pdf` and asks "What is the refund window?"

1. Browser → `POST /chat/5/generate` (Flask) with `prompt` + file.
2. Flask `_call_fastapi` → `POST http://127.0.0.1:8000/api/v1/faq/generate` (multipart).
3. FastAPI `generate_faq`:
   - Extracts text from `policy.pdf`.
   - Prompt doesn't name the file, but it's the only/last file → isolates it.
   - Calls `run_pipeline(prompt, [("policy.pdf", text)])`.
4. `run_pipeline`:
   - `embed_document(text, "policy.pdf")` → splits into chunks, stores in ChromaDB.
   - `retrieve_chunks(prompt, doc_ids=["policy.pdf"])` → similarity search scoped to that doc.
   - Chunks found and relevant → `generate_full_response_from_chunks(prompt, chunks)` → Gemini (or Groq fallback) returns `ANSWER:` + 5 Q/A pairs.
   - Returns `FAQResponse(source="knowledge_base", direct_answer=..., faq_pairs=[...], total=5)`.
5. Flask `_save_response`: stores `Message` (user + assistant), `FAQCollection`, and 5 `FAQPair` rows; returns JSON to browser.
6. `chat.html` renders the assistant message, source badge, and FAQ cards with rate/edit controls.

---

## 10. Known Gaps / Notes

- `backend/api/middleware/auth.py` is currently empty — no backend-level auth/middleware is enforced; the FastAPI service is only protected by CORS restricting it to the Flask origin (not a real security boundary if exposed publicly).
- `backend/core/db.py` (Postgres via `DATABASE_URL`) is configured but not used by any current route — `Document` model on the client side is also unused.
- `client/app/static/js/` is empty — all chat JS is inline in `chat.html`.
- `tests/` is empty — no automated tests yet.
- `doc_id` = filename means two different users uploading files with the same name will overwrite each other's embeddings in the shared ChromaDB collection — there's no per-user namespacing.
- `requirements.txt` and `pyproject.toml` list overlapping but slightly different dependency sets; Poetry (`pyproject.toml`) appears to be the source of truth given `poetry.lock` is present.
