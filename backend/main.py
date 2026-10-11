from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import ArticleInput, QAResponse
from backend.services.generator import generate_qa

app = FastAPI(title="News QA Generator Backend")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=QAResponse)
def generate(input: ArticleInput):
    qas = generate_qa(input.title, input.content, input.num_questions)
    return {"title": input.title, "qas": qas}
