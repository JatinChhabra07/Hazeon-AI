"""
Dashboard Router — Institute-level analytics and student progress tracking.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.schemas import QuestionCreate, QuestionUpdate, QuestionOut

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.models import User, Institute, Submission, Evaluation, Question
from app.routers.auth import get_current_user
from app.schemas.schemas import BatchAnalytics, StudentProgress, UserOut

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/batch-analytics", response_model=BatchAnalytics)
def get_batch_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get batch-level analytics for the institute."""
    institute_id = user.institute_id

    # Get all students in this institute
    students = db.query(User).filter(
        User.institute_id == institute_id,
        User.role == "student"
    ).all()
    student_ids = [s.id for s in students]

    if not student_ids:
        return BatchAnalytics(
            total_students=0, total_submissions=0, total_evaluated=0,
            average_score=0, score_distribution={}, subject_performance={},
            weak_areas=[], top_performers=[]
        )

    # Submissions
    submissions = db.query(Submission).filter(Submission.student_id.in_(student_ids)).all()
    total_submissions = len(submissions)
    evaluated = [s for s in submissions if s.status == "evaluated"]
    total_evaluated = len(evaluated)

    # Evaluations
    evaluations = db.query(Evaluation).join(Submission).filter(
        Submission.student_id.in_(student_ids)
    ).all()

    if not evaluations:
        return BatchAnalytics(
            total_students=len(students), total_submissions=total_submissions,
            total_evaluated=0, average_score=0, score_distribution={},
            subject_performance={}, weak_areas=[], top_performers=[]
        )

    avg_score = sum(e.overall_score for e in evaluations) / len(evaluations)

    # Score distribution
    dist = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
    for e in evaluations:
        if e.overall_score < 2: dist["0-2"] += 1
        elif e.overall_score < 4: dist["2-4"] += 1
        elif e.overall_score < 6: dist["4-6"] += 1
        elif e.overall_score < 8: dist["6-8"] += 1
        else: dist["8-10"] += 1

    # Subject performance — load all submissions + questions in bulk to avoid N+1
    sub_ids = [e.submission_id for e in evaluations]
    subs_map = {s.id: s for s in db.query(Submission).filter(Submission.id.in_(sub_ids)).all()}
    q_ids = {s.question_id for s in subs_map.values()}
    questions_map = {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()}

    subject_scores = {}
    for e in evaluations:
        sub = subs_map.get(e.submission_id)
        if sub:
            q = questions_map.get(sub.question_id)
            if q:
                if q.subject not in subject_scores:
                    subject_scores[q.subject] = []
                subject_scores[q.subject].append(e.overall_score)
    subject_performance = {
        k: round(sum(v)/len(v), 1) for k, v in subject_scores.items()
    }

    # Weak areas (lowest scoring parameters)
    params = [
        ("Relevance", "relevance_score"), ("Introduction", "intro_score"),
        ("Body/Content", "body_score"), ("Keywords", "keyword_score"),
        ("Structure", "structure_score"), ("Factual Accuracy", "factual_score"),
        ("Conclusion", "conclusion_score"), ("Word Limit", "word_limit_score"),
        ("Analysis Depth", "analysis_score"), ("Diagrams", "diagram_score"),
        ("Multi-dimensional", "multidimensional_score"),
    ]
    weak_areas = []
    for label, attr in params:
        avg = sum(getattr(e, attr, 0) for e in evaluations) / len(evaluations)
        weak_areas.append({"parameter": label, "avg_score": round(avg, 1)})
    weak_areas.sort(key=lambda x: x["avg_score"])

    # Top performers — reuse subs_map loaded above
    student_avgs = {}
    for e in evaluations:
        sub = subs_map.get(e.submission_id)
        if sub:
            if sub.student_id not in student_avgs:
                student_avgs[sub.student_id] = []
            student_avgs[sub.student_id].append(e.overall_score)

    students_by_id = {s.id: s for s in students}
    top_performers = []
    for sid, scores in student_avgs.items():
        student = students_by_id.get(sid)
        if student:
            top_performers.append({
                "student_id": sid,
                "name": student.full_name,
                "email": student.email,
                "avg_score": round(sum(scores)/len(scores), 1),
                "submissions": len(scores),
            })
    top_performers.sort(key=lambda x: x["avg_score"], reverse=True)

    return BatchAnalytics(
        total_students=len(students),
        total_submissions=total_submissions,
        total_evaluated=total_evaluated,
        average_score=round(avg_score, 1),
        score_distribution=dist,
        subject_performance=subject_performance,
        weak_areas=weak_areas[:5],
        top_performers=top_performers[:10],
    )


@router.get("/student/{student_id}/progress", response_model=StudentProgress)
def get_student_progress(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get detailed progress for a specific student."""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    evaluations = (
        db.query(Evaluation)
        .join(Submission)
        .filter(Submission.student_id == student_id)
        .order_by(Submission.created_at)
        .all()
    )

    # Scores over time — load all submissions in bulk
    eval_sub_ids = [e.submission_id for e in evaluations]
    eval_subs_map = {s.id: s for s in db.query(Submission).filter(Submission.id.in_(eval_sub_ids)).all()} if eval_sub_ids else {}

    scores_over_time = []
    for e in evaluations:
        sub = eval_subs_map.get(e.submission_id)
        scores_over_time.append({
            "date": sub.created_at.isoformat() if sub else "",
            "overall": e.overall_score,
            "relevance": e.relevance_score,
            "structure": e.structure_score,
            "analysis": e.analysis_score,
        })

    # Parameter averages
    params = ["relevance_score", "intro_score", "body_score", "keyword_score",
              "structure_score", "factual_score", "conclusion_score",
              "word_limit_score", "analysis_score", "diagram_score", "multidimensional_score"]

    param_avgs = {}
    if evaluations:
        for p in params:
            avg = sum(getattr(e, p, 0) for e in evaluations) / len(evaluations)
            param_avgs[p] = round(avg, 1)

    # Improvement rate
    improvement_rate = 0.0
    if len(evaluations) >= 2:
        first_half = evaluations[:len(evaluations)//2]
        second_half = evaluations[len(evaluations)//2:]
        avg_first = sum(e.overall_score for e in first_half) / len(first_half)
        avg_second = sum(e.overall_score for e in second_half) / len(second_half)
        improvement_rate = round(((avg_second - avg_first) / max(avg_first, 1)) * 100, 1)

    return StudentProgress(
        student=UserOut.model_validate(student),
        scores_over_time=scores_over_time,
        parameter_averages=param_avgs,
        total_submissions=len(evaluations),
        improvement_rate=improvement_rate,
    )


@router.get("/students", response_model=list)
def get_institute_students(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all students for the institute with summary stats."""
    students = db.query(User).filter(
        User.institute_id == user.institute_id,
        User.role == "student"
    ).all()

    if not students:
        return []

    student_ids = [s.id for s in students]

    # Bulk-fetch avg scores and submission counts in 2 queries instead of N*2
    eval_agg = (
        db.query(
            Submission.student_id,
            func.count(Evaluation.id).label("eval_count"),
            func.avg(Evaluation.overall_score).label("avg_score"),
        )
        .join(Evaluation, Evaluation.submission_id == Submission.id)
        .filter(Submission.student_id.in_(student_ids))
        .group_by(Submission.student_id)
        .all()
    )
    eval_map = {row.student_id: row for row in eval_agg}

    # Bulk-fetch last submission date per student
    last_sub_agg = (
        db.query(
            Submission.student_id,
            func.max(Submission.created_at).label("last_at"),
        )
        .filter(Submission.student_id.in_(student_ids))
        .group_by(Submission.student_id)
        .all()
    )
    last_sub_map = {row.student_id: row.last_at for row in last_sub_agg}

    results = []
    for student in students:
        agg = eval_map.get(student.id)
        last_at = last_sub_map.get(student.id) or student.created_at
        results.append({
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "total_submissions": agg.eval_count if agg else 0,
            "avg_score": round(float(agg.avg_score), 1) if agg else 0.0,
            "last_active": last_at.isoformat(),
        })

    return results


@router.get("/questions", response_model=list)
def get_questions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get questions scoped to the user's institute (or all if no institute set)."""
    query = db.query(Question)
    if user.institute_id:
        # Return institute-specific questions + unowned global questions
        query = query.filter(
            (Question.institute_id == user.institute_id) | (Question.institute_id == None)  # noqa: E711
        )
    questions = query.order_by(Question.created_at.desc()).all()
    return [{
        "id": q.id,
        "text": q.text,
        "subject": q.subject,
        "topic": q.topic,
        "exam_type": q.exam_type,
        "marks": q.marks,
        "word_limit": q.word_limit,
        "difficulty": q.difficulty,
        "model_answer_points": q.model_answer_points,
        "year": q.year,
        "institute_id": q.institute_id,
    } for q in questions]


@router.post("/reseed-questions", response_model=dict)
def reseed_questions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Force-reseed the question bank if it's empty. Admin only."""
    if user.role != "institute_admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    count = db.query(Question).count()
    if count > 0:
        return {"message": "Question bank already populated.", "count": count}

    sample_questions = [
        Question(text="Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency at the district level.", subject="GS2 - Governance", topic="Good Governance", year=2025, exam_type="HCS", marks=15, word_limit=250, difficulty="moderate", model_answer_points=["Define good governance pillars", "Cite SARAL, CM Window", "District admin challenges", "e-governance initiatives", "Way Forward with recommendations"]),
        Question(text="Analyze the impact of Green Revolution on agriculture in Haryana. What are the emerging challenges and how can sustainable agriculture be promoted?", subject="GS3 - Economy", topic="Agriculture", year=2025, exam_type="HCS", marks=15, word_limit=250, difficulty="moderate", model_answer_points=["Green Revolution impact with data", "Water depletion crisis", "Stubble burning", "MSP dependency", "Crop diversification", "Natural farming initiatives"]),
        Question(text="Examine the changing sex ratio in Haryana. Evaluate the effectiveness of Beti Bachao Beti Padhao campaign.", subject="GS1 - Society", topic="Gender Issues", year=2024, exam_type="HCS", marks=15, word_limit=250, difficulty="moderate", model_answer_points=["Census data on sex ratio", "BBBP scheme details", "Outcomes and improvements", "Remaining challenges", "Multi-stakeholder approach"]),
        Question(text="'Cooperative federalism is the need of the hour for India.' Discuss with reference to recent Centre-State relations.", subject="GS2 - Polity", topic="Federalism", year=2025, exam_type="HCS", marks=20, word_limit=300, difficulty="hard", model_answer_points=["Constitutional provisions Art 245-263", "GST impact on fiscal federalism", "NITI Aayog role", "Recent disputes", "ISC meetings", "Way Forward"]),
        Question(text="What are the ethical challenges faced by civil servants in India? Discuss with examples from Haryana context.", subject="GS4 - Ethics", topic="Ethics in Governance", year=2025, exam_type="HCS", marks=15, word_limit=250, difficulty="moderate", model_answer_points=["Define ethical governance", "Common dilemmas", "Conflict of interest", "Haryana-specific examples", "ARC recommendations", "Code of conduct"]),
        Question(text="Critically analyze the industrial development of Haryana with special focus on the IT corridor of Gurugram and its socio-economic impact.", subject="GS3 - Economy", topic="Industrial Development", year=2024, exam_type="HCS", marks=15, word_limit=250, difficulty="moderate", model_answer_points=["Industrial policy overview", "Gurugram IT sector", "HSIIDC role", "Employment generation", "Urban challenges", "Regional imbalance"]),
        Question(text="Discuss the significance of Panchayati Raj Institutions in Haryana for grassroots democracy. What reforms are needed?", subject="GS2 - Governance", topic="Local Governance", year=2024, exam_type="HCS", marks=15, word_limit=250, difficulty="easy", model_answer_points=["73rd Amendment", "Haryana Panchayati Raj Act", "Women reservation", "Gram Sabha empowerment", "Financial autonomy", "Capacity building"]),
        Question(text="Examine the water crisis in Haryana and suggest a comprehensive water management strategy.", subject="GS3 - Environment", topic="Water Management", year=2025, exam_type="HCS", marks=15, word_limit=250, difficulty="moderate", model_answer_points=["Groundwater depletion data", "SYL canal issue", "Paddy cultivation impact", "Micro-irrigation", "Jal Jeevan Mission", "Policy recommendations"]),
        Question(text="Discuss the role of education in social transformation of Haryana. Evaluate recent education policies.", subject="GS1 - Society", topic="Education", year=2024, exam_type="HCS", marks=15, word_limit=250, difficulty="easy", model_answer_points=["Literacy rates progression", "NEP 2020 implementation", "Super 100 scheme", "School consolidation", "Higher education", "Skill development"]),
        Question(text="Analyze India's neighborhood first policy and its implications for regional stability in South Asia.", subject="GS2 - IR", topic="Foreign Policy", year=2025, exam_type="UPSC", marks=15, word_limit=250, difficulty="hard", model_answer_points=["Neighborhood first policy evolution", "Bilateral relations", "SAGAR doctrine", "BRI challenge", "Connectivity projects", "Way Forward"]),
    ]
    db.add_all(sample_questions)
    db.commit()
    count = db.query(Question).count()
    return {"message": f"Seeded {count} questions into question bank.", "count": count}


# ── Question CRUD (admin only) ─────────────────────────────────────────────────

@router.post("/questions", response_model=QuestionOut, status_code=201)
def create_question(
    data: QuestionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new question in the institute's question bank. Admin only."""
    if user.role not in ("institute_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required.")

    q = Question(
        text=data.text,
        subject=data.subject,
        topic=data.topic,
        year=data.year,
        exam_type=data.exam_type,
        marks=data.marks,
        word_limit=data.word_limit,
        model_answer_points=data.model_answer_points or [],
        difficulty=data.difficulty,
        institute_id=user.institute_id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    logger.info("Question %d created by user %d (%s)", q.id, user.id, user.email)
    return QuestionOut.model_validate(q)


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an existing question. Admin only."""
    if user.role not in ("institute_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required.")

    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")
    if user.institute_id and q.institute_id and q.institute_id != user.institute_id:
        raise HTTPException(status_code=403, detail="Cannot edit another institute's question.")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(q, field, value)
    db.commit()
    db.refresh(q)
    logger.info("Question %d updated by user %d", q.id, user.id)
    return QuestionOut.model_validate(q)


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a question. Admin only. Returns 204 No Content."""
    if user.role not in ("institute_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required.")

    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")
    if user.institute_id and q.institute_id and q.institute_id != user.institute_id:
        raise HTTPException(status_code=403, detail="Cannot delete another institute's question.")

    db.delete(q)
    db.commit()
    logger.info("Question %d deleted by user %d", question_id, user.id)
