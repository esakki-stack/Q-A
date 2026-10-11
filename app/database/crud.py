"""Database CRUD operations"""
from sqlalchemy.orm import Session
from app.database.models import Article, ProcessingJob, QAPair
from datetime import datetime
import json

# Article CRUD
def create_article(db: Session, title: str, content: str, **kwargs) -> Article:
    """Create a new article"""
    article = Article(
        title=title,
        content=content,
        **kwargs
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article

def get_article(db: Session, article_id: str) -> Article:
    """Get article by ID"""
    return db.query(Article).filter(Article.id == article_id).first()

def get_articles(db: Session, skip: int = 0, limit: int = 100) -> list:
    """Get all articles"""
    return db.query(Article).offset(skip).limit(limit).all()

def update_article(db: Session, article_id: str, **kwargs) -> Article:
    """Update article"""
    article = get_article(db, article_id)
    if article:
        for key, value in kwargs.items():
            setattr(article, key, value)
        article.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(article)
    return article

def delete_article(db: Session, article_id: str) -> bool:
    """Delete article"""
    article = get_article(db, article_id)
    if article:
        db.delete(article)
        db.commit()
        return True
    return False

# QA Job CRUD
def create_qa_job(db: Session, article_id: str, **kwargs) -> ProcessingJob:
    """Create a new QA job"""
    job = ProcessingJob(article_id=article_id, **kwargs)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_qa_job(db: Session, job_id: str) -> ProcessingJob:
    """Get QA job by ID"""
    return db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

def update_qa_job(db: Session, job_id: str, **kwargs) -> ProcessingJob:
    """Update QA job"""
    job = get_qa_job(db, job_id)
    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job

def get_qa_jobs_by_article(db: Session, article_id: str) -> list:
    """Get all QA jobs for an article"""
    return db.query(ProcessingJob).filter(ProcessingJob.article_id == article_id).all()

# QA Pair CRUD
def create_qa_pair(db: Session, qa_job_id: str, article_id: str, question: str, answer: str, **kwargs) -> QAPair:
    """Create a new QA pair"""
    pair = QAPair(
        qa_job_id=qa_job_id,
        article_id=article_id,
        question=question,
        answer=answer,
        **kwargs
    )
    db.add(pair)
    db.commit()
    db.refresh(pair)
    return pair

def get_qa_pairs_by_job(db: Session, qa_job_id: str) -> list:
    """Get all QA pairs for a job"""
    return db.query(QAPair).filter(QAPair.qa_job_id == qa_job_id).all()

def get_qa_pairs_by_article(db: Session, article_id: str) -> list:
    """Get all QA pairs for an article"""
    return db.query(QAPair).filter(QAPair.article_id == article_id).all()
