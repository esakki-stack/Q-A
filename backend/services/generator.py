import re
from typing import List, Dict


def generate_qa(title: str, content: str, n: int = 3) -> List[Dict[str, str]]:
    """Simple stub QA generator.

    This is a placeholder implementation that extracts up to `n` sentences
    from the article content and returns them as answers with very simple
    synthetic questions. Replace this with an LLM-backed implementation
    or more advanced NLP logic as needed.
    """
    text = (content or "").strip()
    if not text:
        return [{"question": "What is the article about?", "answer": title or ""} for _ in range(n)]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    qas = []
    for i, s in enumerate(sentences[:n]):
        q = f"Summarize sentence {i+1}."
        a = s.strip()
        qas.append({"question": q, "answer": a})

    # If there are fewer than n sentences, pad with a generic QA
    while len(qas) < n:
        qas.append({"question": "What is the article about?", "answer": title or (text[:200] + "...")})

    return qas
