"""
Q&A Generation API Routes
Clean, minimal endpoints for article processing and Q&A generation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
import uuid
import json

router = APIRouter(prefix="/api/v1", tags=["qa"])

# ==================== MODELS ====================

class QAPair(BaseModel):
    question: str
    answer: str
    confidence: float


class ProcessResponse(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    questions: List[QAPair] = []
    error: str = None


# ==================== IN-MEMORY JOB STORAGE ====================

jobs_db = {}


# ==================== SIMPLE Q&A GENERATOR ====================

def generate_qa_pairs(text: str) -> List[QAPair]:
    """
    Generate Q&A pairs from article text
    Uses simple sentence extraction and question formation
    """
    
    # Split text into sentences
    import re
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if not sentences:
        return []
    
    qa_pairs = []
    
    # Generate questions from sentences
    for i, sentence in enumerate(sentences[:5]):  # Limit to first 5 sentences
        if len(sentence) < 20:
            continue
            
        words = sentence.split()
        if len(words) < 5:
            continue
        
        # Create question by taking first few words and making it a question
        question_words = words[:6]
        
        # Different question patterns
        if words[0].lower() not in ['the', 'a', 'an', 'if', 'when']:
            question = f"What is {sentence[:50].lower()}?"
        else:
            question = f"{sentence[:60]}?"
        
        # Answer is the full sentence
        answer = sentence.strip()
        
        qa_pairs.append(QAPair(
            question=question,
            answer=answer,
            confidence=0.85 + (i * 0.02)
        ))
    
    return qa_pairs


# ==================== ENDPOINTS ====================

@router.post("/process", response_model=ProcessResponse)
async def process_article(text: str, question_count: int = 5):
    """
    Process article text and generate Q&A pairs
    
    Args:
        text: Article text to process
        question_count: Number of questions to generate
    
    Returns:
        ProcessResponse with job_id and generated questions
    """
    
    if not text or len(text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Article must be at least 100 characters"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    
    # Generate Q&A
    qa_pairs = generate_qa_pairs(text)
    
    # Limit to requested count
    qa_pairs = qa_pairs[:question_count]
    
    if not qa_pairs:
        raise HTTPException(
            status_code=400,
            detail="Could not generate questions from provided text"
        )
    
    # Store in memory
    jobs_db[job_id] = {
        "status": "completed",
        "questions": qa_pairs,
        "error": None
    }
    
    return ProcessResponse(
        job_id=job_id,
        status="completed",
        questions=qa_pairs
    )


@router.post("/upload")
async def upload_article(
    file: UploadFile = File(...),
    question_count: int = 5
):
    """
    Upload a file and process it for Q&A generation
    """
    
    try:
        # Read file
        content = await file.read()
        text = content.decode('utf-8', errors='ignore')
        
        if len(text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="File content must be at least 100 characters"
            )
        
        # Generate Q&A
        job_id = str(uuid.uuid4())
        qa_pairs = generate_qa_pairs(text)
        qa_pairs = qa_pairs[:question_count]
        
        if not qa_pairs:
            raise HTTPException(
                status_code=400,
                detail="Could not generate questions from file content"
            )
        
        jobs_db[job_id] = {
            "status": "completed",
            "questions": qa_pairs,
            "error": None
        }
        
        return {
            "job_id": job_id,
            "status": "completed",
            "questions": [q.dict() for q in qa_pairs],
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Get the status and results of a processing job
    """
    
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job = jobs_db[job_id]
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "questions": [q.dict() if hasattr(q, 'dict') else q for q in job["questions"]],
        "error": job.get("error")
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "NEXUS AI Q&A Generator",
        "version": "1.0.0"
    }
