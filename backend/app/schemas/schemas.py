from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "student"
    institute_id: Optional[int] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    institute_id: Optional[int] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Institute ─────────────────────────────────────────
class InstituteCreate(BaseModel):
    name: str
    code: str
    city: str
    state: str = "Haryana"
    plan_type: str = "pilot"

class InstituteOut(BaseModel):
    id: int
    name: str
    code: str
    city: str
    state: str
    plan_type: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Question ──────────────────────────────────────────
class QuestionCreate(BaseModel):
    text: str
    subject: str
    topic: Optional[str] = None
    year: Optional[int] = None
    exam_type: str = "HCS"
    marks: int = 15
    word_limit: int = 250
    model_answer_points: Optional[List[str]] = None
    difficulty: str = "moderate"

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    year: Optional[int] = None
    exam_type: Optional[str] = None
    marks: Optional[int] = None
    word_limit: Optional[int] = None
    model_answer_points: Optional[List[str]] = None
    difficulty: Optional[str] = None

class QuestionOut(BaseModel):
    id: int
    text: str
    subject: str
    topic: Optional[str] = None
    year: Optional[int] = None
    exam_type: str
    marks: int
    word_limit: int
    model_answer_points: Optional[List[str]] = None
    difficulty: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Submission ────────────────────────────────────────
class SubmissionCreate(BaseModel):
    question_id: int

class SubmissionOut(BaseModel):
    id: int
    student_id: int
    question_id: int
    file_path: str
    file_type: str
    ocr_text: Optional[str] = None
    status: str
    word_count: Optional[int] = None
    created_at: Optional[datetime] = None
    question: Optional[QuestionOut] = None

    class Config:
        from_attributes = True


# ── Evaluation ────────────────────────────────────────
class EvaluationOut(BaseModel):
    id: int
    submission_id: int
    overall_score: float
    relevance_score: float
    intro_score: float
    body_score: float
    keyword_score: float
    structure_score: float
    factual_score: float
    conclusion_score: float
    word_limit_score: float
    analysis_score: float
    diagram_score: float
    multidimensional_score: float
    feedback_summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    model_answer: Optional[str] = None
    keywords_found: Optional[List[str]] = None
    keywords_missed: Optional[List[str]] = None
    topper_benchmark: Optional[str] = None
    dimension_analysis: Optional[dict] = None
    marks_obtained: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Combined ──────────────────────────────────────────
class SubmissionWithEvaluation(BaseModel):
    submission: SubmissionOut
    evaluation: Optional[EvaluationOut] = None

class StudentWithSubmissions(BaseModel):
    student: UserOut
    submissions: List[SubmissionOut] = []
    average_score: float = 0.0
    total_submissions: int = 0


# ── Dashboard ─────────────────────────────────────────
class BatchAnalytics(BaseModel):
    total_students: int
    total_submissions: int
    total_evaluated: int
    average_score: float
    score_distribution: dict  # {range: count}
    subject_performance: dict  # {subject: avg_score}
    weak_areas: List[dict]   # [{parameter, avg_score}]
    top_performers: List[dict]

class StudentProgress(BaseModel):
    student: UserOut
    scores_over_time: List[dict]
    parameter_averages: dict
    total_submissions: int
    improvement_rate: float


# ── Topper Answer ─────────────────────────────────────
class TopperAnswerOut(BaseModel):
    id: int
    question_id: Optional[int] = None
    ocr_text: Optional[str] = None
    score: Optional[float] = None
    rank: Optional[int] = None
    year: Optional[int] = None
    exam_type: str
    subject: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    is_anonymized: bool
    created_at: Optional[datetime] = None
    question: Optional[QuestionOut] = None

    class Config:
        from_attributes = True


# ── Forgot Password ───────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str

class MessageResponse(BaseModel):
    message: str


# Update forward references
Token.model_rebuild()
