# The Hindu Newspaper Q&A Generator

A small full-stack article question-and-answer demo: a Vue 3 + Vite interface sends article text to a FastAPI service, which returns sentence-derived question-and-answer pairs. It is intended for experimenting with newspaper-style article content supplied by the user.

**Important implementation status:** despite the repository's RAG-oriented name and earlier descriptions, the active application does **not** currently implement retrieval-augmented generation. It does not chunk a document corpus, create Sentence Transformer embeddings, build or query a FAISS index, or call an LLM for answers. The active endpoint uses a basic sentence-splitting/template heuristic. RAG and model-based generation are future work, not working features. This project is not affiliated with or endorsed by The Hindu.

## Problem and objectives

The demo provides a browser workflow for submitting article text and viewing generated Q&A pairs. It is useful as a lightweight UI/API prototype, but generated questions may be repetitive or low quality and answers are selected from the submitted text rather than independently verified.

## Features currently present

- Vue 3 single-page frontend with text input, file upload UI, results, browser-local history, and JSON export.
- FastAPI API for submitting text, uploading a file, checking an in-memory job result, and health checks.
- Heuristic sentence-based Q&A generation. The active route currently considers at most the first five eligible sentences, regardless of a larger requested count.
- Local development proxy from Vite's `/api` path to the backend.

Not implemented in the active path: newspaper URL ingestion, PDF/DOCX text extraction, durable server-side job history, a RAG pipeline, embeddings/vector search, and live LLM answer generation. Other provider/model code in the repository is not called by the active API routes.

## Technology

- Python, FastAPI, Uvicorn, and Pydantic
- Vue 3, Vite, Pinia, Axios, and lucide-vue-next
- Dependency manifests: [requirements.txt](requirements.txt), [requirements-minimal.txt](requirements-minimal.txt), [requirements-prod.txt](requirements-prod.txt), and [ai-qa-dashboard/package.json](ai-qa-dashboard/package.json)

The active routes are defined in [app/api/qa_routes.py](app/api/qa_routes.py); the app entry point is [app/main.py](app/main.py). The browser application lives in [ai-qa-dashboard/](ai-qa-dashboard/). The separate [backend/](backend/) folder is a minimal scaffold and is not the application mounted by `app/main.py`.

## Architecture and current request flow

```text
Browser (Vue/Vite)
  -> POST /api/v1/process or POST /api/v1/upload
  -> FastAPI active router
  -> simple sentence splitting and question templates
  -> Q&A JSON response and in-memory job record
  -> browser displays result; history is stored in browser local storage
```

The intended RAG workflow is not implemented. In particular, there is no working pipeline of document extraction → chunking → Sentence Transformer embeddings → FAISS indexing → semantic retrieval → retrieved context → LLM-generated answer. Do not treat the current generated Q&A as RAG-grounded output.

## Requirements

- Windows 10/11 (commands below use PowerShell), Python compatible with the pinned packages in `requirements.txt`, and Node.js/npm compatible with the Vite project.
- No API key or downloaded model is required for the active heuristic `/process` endpoint.
- Do not put licensed newspaper archives, personal data, credentials, vector indexes, or model weights in the repository.

## Setup on Windows / VS Code

Open this repository folder in VS Code. In a PowerShell terminal at the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use a Command Prompt terminal and activate with `.venv\Scripts\activate.bat`, or run the venv executable directly as `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

For the frontend, open a second terminal:

```powershell
Set-Location .\ai-qa-dashboard
npm ci
npm run dev
```

The root `requirements.txt` is the preferred manifest for the app. `requirements-minimal.txt` and `requirements-prod.txt` are alternate manifests retained from the existing project; they are not interchangeable with a verified deployment profile. The frontend's `npm run lint` script uses ESLint with auto-fix, but ESLint is not declared in this package manifest, so it is not documented as a ready-to-run check.

## Start the backend

From the repository root, in an activated virtual environment:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- Frontend: <http://localhost:5173>
- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/api/v1/health>

The Vite dev server proxies `/api` requests to `http://localhost:8000`. The frontend can also be built and previewed from `ai-qa-dashboard` with `npm run build` and `npm run preview`. The backend serves the frontend source directory as static files; use the Vite dev server for the documented development workflow.

## Configuration

The backend settings in [app/config.py](app/config.py) load a root `.env` when present. Copy [.env.example](.env.example) to `.env` for local overrides; keep `.env` private and never commit it. The active heuristic route does not require provider credentials. Optional variables shown in the example reflect settings already present in the application; setting a key does not mean the active route uses an LLM.

The frontend API base URL can be overridden with `VITE_API_URL` in `ai-qa-dashboard/.env.local` (or provided in the frontend process environment). Its current fallback is the local FastAPI `/api/v1` endpoint. Never put secrets in Vite environment variables: values prefixed for Vite are shipped to the browser.

## Supplying article text and making a request

Use text that you own, have permission to process, or that is legally redistributable. Do not scrape or redistribute copyrighted newspaper archives without the appropriate rights. At present, the reliable input path is plain text pasted into the UI or sent directly to the API. The upload handler decodes bytes as UTF-8; the frontend may display other file types, but PDF/DOCX extraction is not implemented by the active route and is not supported reliably.

`POST /api/v1/process` takes `text` and `question_count` as query parameters (not a JSON body). Example in PowerShell:

```powershell
$article = 'A legally usable sample article with several sentences, each long enough for the sentence-based demo.'
$encoded = [uri]::EscapeDataString($article)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/process?text=$encoded&question_count=5"
```

The endpoint currently requires at least 100 characters. It returns a job ID, `completed` status, and Q&A pair list immediately. The basic generator uses no learned question-answering model and should not be used for operational, legal, or factual decisions without human review.

## API endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| `POST` | `/api/v1/process?text=...&question_count=5` | Generate heuristic Q&A from text (minimum 100 characters). |
| `POST` | `/api/v1/upload?question_count=5` | Accept multipart `file`; bytes are decoded as UTF-8 and processed. Plain-text files only are reliable. |
| `GET` | `/api/v1/status/{job_id}` | Read a job result held in process memory; it is lost when the server restarts. |
| `GET` | `/api/v1/health` | Health response. |

Interactive schemas are available at `/docs` while the backend is running. Note that the implementation registers a health route both on the app and the included API router; the behavior is the same.

## Ingestion, embeddings, FAISS, and LLM status

There are no active corpus-ingestion, chunking, embedding-generation, FAISS-index creation, semantic-retrieval, or LLM-query commands to run. The relevant pieces requested for a full RAG system must be designed, implemented, tested with permitted documents, and documented before describing the project as a functioning RAG application. The codebase lists NLP/model-related dependencies and includes other AI/provider modules, but dependency presence or dormant source code alone is not an active end-to-end pipeline.

## Tests and checks

No maintained root automated test suite or configured frontend lint setup was found during repository review. Useful checks after installing dependencies:

```powershell
python -m py_compile app/main.py app/api/qa_routes.py app/services/simple_extraction_service.py app/services/simple_qa_generator.py
Set-Location .\ai-qa-dashboard
npm run build
```

For API smoke testing, start the backend and call the health and process endpoints above. These checks do not validate a RAG or LLM pipeline, because those workflows are not implemented in the active application.

## Troubleshooting

- **Frontend cannot reach the API:** start Uvicorn on port 8000 and Vite on port 5173; confirm the Vite proxy in `ai-qa-dashboard/vite.config.js`.
- **PowerShell activation is blocked:** use Command Prompt activation or invoke `.venv\Scripts\python.exe` directly.
- **Upload produces poor text:** upload only plain UTF-8 text; the current upload handler does not parse PDF or Word documents.
- **Status returns 404 after restart:** job state is in memory and is not persistent.
- **Install errors for ML packages:** the active text heuristic does not need downloaded model weights, but the full requirements include heavyweight ML packages. Use a Python version/platform supported by the pinned Torch release and consult that package's installation guidance if needed.
- **Lint command fails:** ESLint is not declared in the frontend package dependencies; no lint pass is claimed.

## Security and data privacy

- `.env` and environment-specific `.env.*` files are ignored; only sanitized examples should be committed. Rotate credentials immediately if a real secret was ever published.
- Do not commit private datasets, newspaper archives without redistribution rights, personal information, uploaded documents, generated databases, model caches/weights, or vector indexes.
- The heuristic server keeps submitted job results in process memory. Avoid sending sensitive articles to a publicly exposed demo; the development server is not hardened for public production use.
- Frontend environment variables are public in the built browser bundle. Never place API credentials there.

## Limitations and future improvements

- Implement and test a real corpus/document ingestion and extraction workflow with legally usable source documents.
- Add chunking, a compatible embedding model, FAISS indexing and persistence, retrieval evaluation, and source-cited context-grounded answers.
- Connect a clearly configured local LLM (or a securely proxied provider) to the active API path; do not expose provider credentials in the frontend.
- Improve question generation quality and respect requested question counts.
- Add tests, durable job storage, input validation, upload type/content checks, error handling, and production deployment guidance.
- Reconcile duplicated/archived scaffolds and outdated legacy documentation after confirming which historical material should be retained.
