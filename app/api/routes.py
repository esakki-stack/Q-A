"""
Simplified API Routes
Actual working Q&A generation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Form
from typing import Optional, List, Dict, Any
import uuid
import logging
import time
from datetime import datetime

from app.schemas import (
    QARequest, ProcessingStatusResponse, ProcessingStatus, 
    QAPair, DifficultyLevel, QuestionType, ArticleMetadata, QAResponse
)
from app.services.simple_qa_generator import SimpleQAGenerator, extract_summary, extract_keywords
from app.services.simple_extraction_service import SimpleExtractionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["qa-generation"])

# In-memory job storage
processing_jobs: Dict[str, Dict[str, Any]] = {}

qa_generator = SimpleQAGenerator()
extraction_service = SimpleExtractionService()


async def process_article_background(
    job_id: str,
    article_text: str,
    question_count: int = 10,
):
    """Background task to process article"""
    try:
        logger.info(f"🔄 Starting background processing: {job_id}")
        processing_jobs[job_id]["status"] = ProcessingStatus.PROCESSING
        processing_jobs[job_id]["started_at"] = datetime.utcnow()
        
        # Step 1: Extract text
        logger.info(f"📥 Extracting article...")
        processing_jobs[job_id]["progress_percentage"] = 25
        
        extracted_text, metadata = await extraction_service.extract(
            article_text=article_text
        )
        
        if not extracted_text.strip():
            raise ValueError("Extracted text is empty")
        
        # Step 2: Generate summary
        logger.info(f"📝 Generating summary...")
        processing_jobs[job_id]["progress_percentage"] = 40
        summary = await extract_summary(extracted_text)
        
        # Step 3: Generate Q&A pairs
        logger.info(f"🧠 Generating Q&A pairs...")
        processing_jobs[job_id]["progress_percentage"] = 60
        qa_pairs_data = await qa_generator.generate_qa_pairs(
            extracted_text,
            question_count=question_count
        )
        
        # Convert to QAPair objects
        qa_pairs = []
        for pair_data in qa_pairs_data:
            try:
                qa = QAPair(
                    question=pair_data["question"],
                    answer=pair_data["answer"],
                    confidence=pair_data["confidence"],
                    difficulty=DifficultyLevel(pair_data["difficulty"]),
                    question_type=QuestionType(pair_data["question_type"]),
                    source_paragraphs=pair_data.get("source_paragraphs", []),
                    source_text=pair_data.get("source_text"),
                    keywords=pair_data.get("keywords", []),
                )
                qa_pairs.append(qa)
            except Exception as e:
                logger.warning(f"⚠️  Error converting Q&A pair: {e}")
                continue
        
        # Step 4: Extract keywords
        logger.info(f"🏷️  Extracting keywords...")
        processing_jobs[job_id]["progress_percentage"] = 80
        keywords = await extract_keywords(extracted_text)
        
        # Step 5: Build response
        logger.info(f"📦 Building response...")
        processing_jobs[job_id]["progress_percentage"] = 95
        
        elapsed_time = time.time() - processing_jobs[job_id]["start_time"]
        
        # Create metadata
        article_metadata = ArticleMetadata(
            title=None,
            author=None,
            publish_date=None,
            source_url=None,
            word_count=metadata.get("word_count", 0),
            reading_time_minutes=metadata.get("reading_time_minutes", 0),
            language="en",
            categories=[]
        )
        
        response = QAResponse(
            job_id=job_id,
            status=ProcessingStatus.COMPLETED,
            article_metadata=article_metadata,
            qa_pairs=qa_pairs,
            summary=summary,
            key_entities=keywords,
            timeline_events=[],
            stats={
                "total_questions": len(qa_pairs),
                "average_confidence": (
                    sum(q.confidence for q in qa_pairs) / len(qa_pairs) if qa_pairs else 0
                ),
                "question_distribution": {},
            },
            processing_time=elapsed_time,
            mode_used="simple",
        )
        
        # Complete
        logger.info(f"✅ Processing completed: {job_id}")
        processing_jobs[job_id]["status"] = ProcessingStatus.COMPLETED
        processing_jobs[job_id]["completed_at"] = datetime.utcnow()
        processing_jobs[job_id]["result"] = response
        processing_jobs[job_id]["progress_percentage"] = 100
        
    except Exception as e:
        logger.error(f"❌ Background processing failed: {e}", exc_info=True)
        processing_jobs[job_id]["status"] = ProcessingStatus.FAILED
        processing_jobs[job_id]["error"] = str(e)
        processing_jobs[job_id]["completed_at"] = datetime.utcnow()
        processing_jobs[job_id]["progress_percentage"] = 0


@router.post("/process", response_model=ProcessingStatusResponse)
async def process_article(
    request: QARequest,
    background_tasks: BackgroundTasks,
):
    """
    Process article and generate Q&A pairs
    Returns immediately with job_id for polling
    """
    try:
        # Validate
        if not request.article_text or not request.article_text.strip():
            raise HTTPException(
                status_code=400,
                detail="article_text is required and cannot be empty"
            )
        
        if len(request.article_text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="Article must be at least 100 characters"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        logger.info(f"📝 New job created: {job_id}")
        
        processing_jobs[job_id] = {
            "job_id": job_id,
            "status": ProcessingStatus.PENDING,
            "progress_percentage": 0,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "start_time": time.time(),
            "error": None,
            "result": None,
        }
        
        # Queue background task
        background_tasks.add_task(
            process_article_background,
            job_id=job_id,
            article_text=request.article_text,
            question_count=min(max(request.question_count, 1), 20),
        )
        
        logger.info(f"✅ Job {job_id} queued")
        
        return ProcessingStatusResponse(
            job_id=job_id,
            status=ProcessingStatus.PENDING,
            progress_percentage=0,
            result=None,
            error=None,
            created_at=datetime.utcnow(),
            estimated_completion=None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=ProcessingStatusResponse)
async def check_status(job_id: str):
    """
    Check job status
    Poll this endpoint until status is 'completed' or 'failed'
    """
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        logger.info(f"📊 Status check: {job_id} -> {job['status'].value} ({job['progress_percentage']}%)")
        
        return ProcessingStatusResponse(
            job_id=job_id,
            status=job["status"],
            progress_percentage=job["progress_percentage"],
            result=job.get("result"),
            error=job.get("error"),
            created_at=job["created_at"],
            estimated_completion=None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NEXUS AI Q&A Generator",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/info")
async def api_info():
    """API information"""
    return {
        "name": "NEXUS AI Q&A Generator API",
        "version": "2.0.0",
        "endpoints": {
            "process": {
                "path": "/api/v1/process",
                "method": "POST",
                "description": "Generate Q&A pairs from article"
            },
            "status": {
                "path": "/api/v1/status/{job_id}",
                "method": "GET",
                "description": "Check job status and retrieve results"
            },
            "health": {
                "path": "/api/v1/health",
                "method": "GET",
                "description": "Health check"
            },
        },
    }
