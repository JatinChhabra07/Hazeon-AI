"""
MCQ Generator Router
====================
Endpoints for UPSC-style MCQ generation from uploaded institute documents.

POST /mcq/upload          — Upload a document + trigger MCQ generation
GET  /mcq/documents       — List all documents for current institute
GET  /mcq/documents/{id}  — Get document details + all its MCQs
DELETE /mcq/documents/{id} — Delete a document and its MCQs
GET  /mcq/questions/{doc_id} — Get all MCQs for a document (with filters)
POST /mcq/regenerate/{doc_id} — Re-run MCQ generation for a document
"""

import os
import shutil
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import MCQDocument, MCQQuestion, User
from app.routers.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcq", tags=["MCQ Generator"])

ALLOWED_TYPES = {"pdf", "txt"}
MCQ_UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "mcq_docs")
os.makedirs(MCQ_UPLOAD_DIR, exist_ok=True)


# ── Background task: extract text + generate MCQs ─────────────────────────────

def _process_document(doc_id: int, file_path: str, file_type: str,
                       num_questions: int, subject_area: str, db_url: str):
    """Runs in background: extracts text, calls MCQ service, saves to DB."""
    from app.database import SessionLocal
    from app.services.mcq_service import extract_text_from_file, generate_mcqs_from_text

    # Reuse the app's shared engine/pool (already has check_same_thread=False for SQLite)
    # Creating a new engine per task causes "database is locked" on concurrent uploads.
    db = SessionLocal()

    try:
        doc = db.query(MCQDocument).filter(MCQDocument.id == doc_id).first()
        if not doc:
            return

        doc.status = "processing"
        db.commit()

        # Step 1: Extract text
        text = extract_text_from_file(file_path, file_type)
        if not text:
            doc.status = "failed"
            db.commit()
            return

        # Scanned PDF with no OCR key — still generate mock UPSC MCQs
        if text == "__SCANNED_PDF__":
            logger.warning(f"Scanned PDF {doc_id}: generating subject-based mock MCQs")
            text = ""  # empty text → mcq_service will use mock generator

        doc.extracted_text = text or "(scanned document)"
        db.commit()

        # Step 2: Generate MCQs
        mcqs = generate_mcqs_from_text(text, num_questions, subject_area)

        # Step 3: Save MCQs to DB
        for mcq_data in mcqs:
            q = MCQQuestion(
                document_id=doc_id,
                question_type=mcq_data.get("question_type", "direct"),
                question_text=mcq_data.get("question_text", ""),
                statements=mcq_data.get("statements"),
                pairs=mcq_data.get("pairs"),
                options=mcq_data.get("options", []),
                correct_option=mcq_data.get("correct_option", "a"),
                explanation=mcq_data.get("explanation"),
                topic=mcq_data.get("topic"),
                difficulty=mcq_data.get("difficulty", "moderate"),
            )
            db.add(q)

        doc.status = "generated"
        doc.num_questions = len(mcqs)
        db.commit()
        logger.info(f"Document {doc_id}: generated {len(mcqs)} MCQs")

    except Exception as e:
        logger.error(f"Document processing failed {doc_id}: {e}")
        try:
            doc = db.query(MCQDocument).filter(MCQDocument.id == doc_id).first()
            if doc:
                doc.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ── Upload endpoint ────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
    subject_area: str = Form(""),
    num_questions: int = Form(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF/TXT document and generate UPSC-style MCQs from it."""
    # Validate file type
    filename = file.filename or "document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '.{ext}' not supported. Use PDF or TXT.")

    # Validate question count
    if not (5 <= num_questions <= 50):
        raise HTTPException(status_code=400, detail="num_questions must be between 5 and 50.")

    # Save file
    safe_name = f"mcqdoc_{current_user.id}_{os.urandom(6).hex()}.{ext}"
    file_path = os.path.join(MCQ_UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create DB record
    doc = MCQDocument(
        institute_id=current_user.institute_id,
        uploaded_by=current_user.id,
        filename=filename,
        file_path=file_path,
        file_type=ext,
        title=title or filename,
        subject_area=subject_area or "General Studies",
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Trigger background processing
    background_tasks.add_task(
        _process_document,
        doc.id, file_path, ext, num_questions, subject_area,
        settings.DATABASE_URL,
    )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "title": doc.title,
        "subject_area": doc.subject_area,
        "status": doc.status,
        "message": f"Document uploaded. Generating {num_questions} UPSC-style MCQs in background...",
    }


# ── List documents ─────────────────────────────────────────────────────────────

@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all MCQ documents uploaded by the current institute."""
    query = db.query(MCQDocument)
    if current_user.role != "super_admin":
        if not current_user.institute_id:
            return []  # no institute assigned — no documents visible
        query = query.filter(MCQDocument.institute_id == current_user.institute_id)
    docs = query.order_by(MCQDocument.created_at.desc()).all()

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "title": d.title,
            "subject_area": d.subject_area,
            "file_type": d.file_type,
            "status": d.status,
            "num_questions": d.num_questions,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


# ── Get document + MCQs ────────────────────────────────────────────────────────

@router.get("/documents/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document details plus all generated MCQs."""
    doc = db.query(MCQDocument).filter(MCQDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if current_user.role != "super_admin" and doc.institute_id != current_user.institute_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    questions = db.query(MCQQuestion).filter(MCQQuestion.document_id == doc_id).all()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "title": doc.title,
        "subject_area": doc.subject_area,
        "file_type": doc.file_type,
        "status": doc.status,
        "num_questions": doc.num_questions,
        "created_at": doc.created_at.isoformat(),
        "questions": [
            {
                "id": q.id,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "statements": q.statements,
                "pairs": q.pairs,
                "options": q.options,
                "correct_option": q.correct_option,
                "explanation": q.explanation,
                "topic": q.topic,
                "difficulty": q.difficulty,
            }
            for q in questions
        ],
    }


# ── Delete document ────────────────────────────────────────────────────────────

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(MCQDocument).filter(MCQDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if current_user.role != "super_admin" and doc.institute_id != current_user.institute_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Remove file from disk
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return {"message": "Document and its MCQs deleted successfully."}


# ── Regenerate MCQs ────────────────────────────────────────────────────────────

@router.post("/regenerate/{doc_id}")
def regenerate_mcqs(
    doc_id: int,
    background_tasks: BackgroundTasks,
    num_questions: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete existing MCQs for a document and regenerate fresh ones."""
    doc = db.query(MCQDocument).filter(MCQDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if current_user.role != "super_admin" and doc.institute_id != current_user.institute_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if doc.status == "processing":
        raise HTTPException(status_code=409, detail="Document is already being processed.")

    # Delete old questions
    db.query(MCQQuestion).filter(MCQQuestion.document_id == doc_id).delete()
    doc.status = "uploaded"
    doc.num_questions = 0
    db.commit()

    background_tasks.add_task(
        _process_document,
        doc.id, doc.file_path, doc.file_type,
        num_questions, doc.subject_area or "",
        settings.DATABASE_URL,
    )

    return {"message": f"Regenerating {num_questions} MCQs for '{doc.title}'..."}
