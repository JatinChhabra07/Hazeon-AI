"""
Topper Answer Router — Manage the topper answer database (the competitive moat).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.models import TopperAnswer, Question
from app.routers.auth import get_current_user, require_role
from app.services.storage_service import save_upload
from app.services.ocr_service import perform_ocr
from app.schemas.schemas import TopperAnswerOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/topper-answers", tags=["Topper Answers"])


@router.get("/", response_model=list[TopperAnswerOut])
def list_topper_answers(
    subject: Optional[str] = None,
    exam_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List topper answers with optional filters."""
    query = db.query(TopperAnswer)
    if subject:
        query = query.filter(TopperAnswer.subject == subject)
    if exam_type:
        query = query.filter(TopperAnswer.exam_type == exam_type)

    answers = query.order_by(TopperAnswer.created_at.desc()).limit(50).all()

    # Bulk-load all referenced questions in ONE query instead of N queries
    from app.schemas.schemas import QuestionOut
    q_ids = {a.question_id for a in answers if a.question_id}
    questions_map = (
        {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()}
        if q_ids else {}
    )

    results = []
    for a in answers:
        out = TopperAnswerOut.model_validate(a)
        if a.question_id and a.question_id in questions_map:
            out.question = QuestionOut.model_validate(questions_map[a.question_id])
        results.append(out)
    return results


@router.get("/subjects/list")
def get_available_subjects(db: Session = Depends(get_db)):
    """Get list of subjects that have topper answers."""
    subjects = db.query(TopperAnswer.subject).distinct().all()
    return [s[0] for s in subjects if s[0]]


@router.get("/{answer_id}", response_model=TopperAnswerOut)
def get_topper_answer(
    answer_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific topper answer."""
    answer = db.query(TopperAnswer).filter(TopperAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Topper answer not found")

    from app.schemas.schemas import QuestionOut
    out = TopperAnswerOut.model_validate(answer)
    if answer.question_id:
        q = db.query(Question).filter(Question.id == answer.question_id).first()
        if q:
            out.question = QuestionOut.model_validate(q)
    return out


@router.post("/upload", response_model=TopperAnswerOut)
def upload_topper_answer(
    file: UploadFile = File(...),
    question_id: int = Form(None),
    score: float = Form(None),
    rank: int = Form(None),
    year: int = Form(None),
    exam_type: str = Form("HCS"),
    subject: str = Form(None),
    tags: str = Form(""),  # comma-separated
    db: Session = Depends(get_db),
    user = Depends(require_role("institute_admin", "super_admin")),
):
    """Upload a topper answer sheet. Admin-only endpoint."""
    file_path = save_upload(file, subfolder="topper_answers")
    ocr_text, _ = perform_ocr(file_path)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    topper = TopperAnswer(
        question_id=question_id,
        file_path=file_path,
        ocr_text=ocr_text,
        score=score,
        rank=rank,
        year=year,
        exam_type=exam_type,
        subject=subject,
        tags=tag_list,
        is_anonymized=True,
    )
    db.add(topper)
    db.commit()
    db.refresh(topper)

    # Add to ChromaDB for RAG
    try:
        _add_to_vector_db(topper)
    except Exception as e:
        logger.warning("ChromaDB vector insert skipped for topper %d: %s", topper.id, e)

    return TopperAnswerOut.model_validate(topper)


def _add_to_vector_db(topper: TopperAnswer):
    """Add topper answer to ChromaDB for similarity search."""
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name="topper_answers",
        metadata={"hnsw:space": "cosine"}
    )
    if topper.ocr_text:
        collection.add(
            documents=[topper.ocr_text],
            metadatas=[{
                "subject": topper.subject or "",
                "exam_type": topper.exam_type or "HCS",
                "year": str(topper.year or ""),
                "score": str(topper.score or ""),
            }],
            ids=[f"topper_{topper.id}"]
        )
