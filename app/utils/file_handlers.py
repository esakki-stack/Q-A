import os
import shutil
from pathlib import Path
from typing import Optional, List

try:
    import PyPDF2
except ImportError:  # pragma: no cover - optional dependency
    PyPDF2 = None

try:
    from docx import Document
except ImportError:  # pragma: no cover - optional dependency
    Document = None

from app.utils.logger import logger

ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}

def validate_file(file_path: str) -> bool:
    """Validate if file exists and has allowed extension"""
    path = Path(file_path)
    return path.exists() and path.suffix.lower() in ALLOWED_EXTENSIONS

def get_file_extension(file_path: str) -> str:
    """Get file extension"""
    return Path(file_path).suffix.lower()

def save_upload_file(upload_file, save_dir: str = "data/uploads") -> str:
    """Save uploaded file and return path"""
    try:
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, upload_file.filename)
        
        with open(file_path, "wb") as f:
            content = upload_file.file.read()
            f.write(content)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise

def process_uploaded_file(file_path: str) -> str:
    """Process uploaded file and extract text"""
    extension = get_file_extension(file_path)
    
    try:
        if extension == '.txt':
            return extract_text_from_txt(file_path)
        elif extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    if PyPDF2 is None:
        raise RuntimeError("PyPDF2 is not installed. Install requirements to enable PDF processing.")

    text = ""
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Error extracting PDF: {str(e)}")
        raise
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    if Document is None:
        raise RuntimeError("python-docx is not installed. Install requirements to enable DOCX processing.")

    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error extracting DOCX: {str(e)}")
        raise
    return text

def cleanup_file(file_path: str) -> None:
    """Delete file after processing"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)
