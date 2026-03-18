"""
Upload Router — Handles file upload + triggers OCR + AI evaluation pipeline.
This is the core automation endpoint.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, Question, Submission, Evaluation
from app.routers.auth import get_current_user
from app.services.storage_service import save_upload, get_file_type
from app.services.ocr_service import perform_ocr
from app.services.evaluation_service import run_evaluation
from app.schemas.schemas import SubmissionOut, SubmissionWithEvaluation, EvaluationOut

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])


@router.post("/upload", response_model=SubmissionWithEvaluation)
async def upload_and_evaluate(
    file: UploadFile = File(...),
    question_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload answer sheet → OCR → AI Evaluation (full automation pipeline).

    1. Saves the uploaded PDF/image
    2. Runs OCR (Google Vision or mock)
    3. Runs the LangGraph evaluation pipeline
    4. Stores evaluation results
    5. Returns structured feedback
    """
    # Validate question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Validate file type
    file_type = get_file_type(file.filename)
    if file_type == "unknown":
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, JPG, or PNG.")

    submission = None
    try:
        # Step 1: Save file
        file_path = save_upload(file, subfolder="submissions")

        # Step 2: OCR (Gemini Vision → demo fallback) — run in thread to avoid blocking event loop
        ocr_text, word_count = await asyncio.to_thread(perform_ocr, file_path)

        # Create submission record
        submission = Submission(
            student_id=user.id,
            question_id=question_id,
            file_path=file_path,
            file_type=file_type,
            ocr_text=ocr_text,
            ocr_language="mixed",
            status="processing",
            word_count=word_count,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # Step 3: Run LangGraph evaluation pipeline (Groq → Gemini → smart mock) — in thread
        eval_result = await asyncio.to_thread(
            run_evaluation,
            ocr_text=ocr_text,
            question_text=question.text,
            question_subject=question.subject,
            question_marks=question.marks,
            question_word_limit=question.word_limit,
            model_answer_points=question.model_answer_points,
        )

        # Step 4: Store evaluation
        evaluation = Evaluation(
            submission_id=submission.id,
            overall_score=eval_result.get("overall_score", 0),
            relevance_score=eval_result.get("relevance_score", 0),
            intro_score=eval_result.get("intro_score", 0),
            body_score=eval_result.get("body_score", 0),
            keyword_score=eval_result.get("keyword_score", 0),
            structure_score=eval_result.get("structure_score", 0),
            factual_score=eval_result.get("factual_score", 0),
            conclusion_score=eval_result.get("conclusion_score", 0),
            word_limit_score=eval_result.get("word_limit_score", 0),
            analysis_score=eval_result.get("analysis_score", 0),
            diagram_score=eval_result.get("diagram_score", 0),
            multidimensional_score=eval_result.get("multidimensional_score", 0),
            feedback_summary=eval_result.get("feedback_summary", ""),
            strengths=eval_result.get("strengths", []),
            weaknesses=eval_result.get("weaknesses", []),
            improvements=eval_result.get("improvements", []),
            model_answer=eval_result.get("model_answer", ""),
            keywords_found=eval_result.get("keywords_found", []),
            keywords_missed=eval_result.get("keywords_missed", []),
            topper_benchmark=eval_result.get("topper_benchmark", ""),
            dimension_analysis=eval_result.get("dimension_analysis", {}),
            marks_obtained=eval_result.get("marks_obtained", 0),
        )
        db.add(evaluation)

        submission.status = "evaluated"
        db.commit()
        db.refresh(submission)
        db.refresh(evaluation)

        return SubmissionWithEvaluation(
            submission=SubmissionOut.model_validate(submission),
            evaluation=EvaluationOut.model_validate(evaluation),
        )

    except Exception as e:
        if submission:
            submission.status = "failed"
            db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}. Check your Groq/Gemini API keys in .env",
        )


@router.get("/my-submissions", response_model=list[SubmissionWithEvaluation])
def get_my_submissions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all submissions for the current student."""
    submissions = (
        db.query(Submission)
        .filter(Submission.student_id == user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )

    results = []
    for sub in submissions:
        eval_data = None
        if sub.evaluation:
            eval_data = EvaluationOut.model_validate(sub.evaluation)
        results.append(SubmissionWithEvaluation(
            submission=SubmissionOut.model_validate(sub),
            evaluation=eval_data,
        ))
    return results


@router.get("/{submission_id}", response_model=SubmissionWithEvaluation)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific submission with its evaluation."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    eval_data = None
    if submission.evaluation:
        eval_data = EvaluationOut.model_validate(submission.evaluation)

    return SubmissionWithEvaluation(
        submission=SubmissionOut.model_validate(submission),
        evaluation=eval_data,
    )
