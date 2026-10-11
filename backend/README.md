# News QA Generator — Backend

This folder contains a minimal FastAPI backend scaffold that provides
an endpoint the frontend can call to generate Q/A pairs from an article.

Endpoints:

- `GET /health` — simple health check
- `POST /generate` — accepts JSON with `title`, `content`, `num_questions`

Run locally:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Next steps:

- Replace `backend/services/generator.py` with a real QA pipeline (LLM or NLP)
- Add auth, rate-limiting, and telemetry as needed
