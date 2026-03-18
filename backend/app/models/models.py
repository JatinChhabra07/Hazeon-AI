import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class Institute(Base):
    __tablename__ = "institutes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), default="Haryana")
    plan_type = Column(String(50), default="pilot")  # pilot, basic, premium
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="institute")
    questions = relationship("Question", back_populates="institute")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # institute_admin, student, super_admin
    institute_id = Column(Integer, ForeignKey("institutes.id"), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    institute = relationship("Institute", back_populates="users")
    submissions = relationship("Submission", back_populates="student")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    subject = Column(String(100), nullable=False)  # GS1, GS2, GS3, GS4, Essay, Optional
    topic = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)
    exam_type = Column(String(50), default="HCS")  # HCS, UPSC
    marks = Column(Integer, default=15)
    word_limit = Column(Integer, default=250)
    model_answer_points = Column(JSON, nullable=True)  # list of key points
    difficulty = Column(String(50), default="moderate")
    institute_id = Column(Integer, ForeignKey("institutes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    institute = relationship("Institute", back_populates="questions")
    submissions = relationship("Submission", back_populates="question")
    topper_answers = relationship("TopperAnswer", back_populates="question")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), default="pdf")  # pdf, jpg, png
    ocr_text = Column(Text, nullable=True)
    ocr_language = Column(String(20), default="en")  # en, hi, mixed
    status = Column(String(50), default="uploaded", index=True)  # uploaded, processing, evaluated, failed
    word_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    student = relationship("User", back_populates="submissions")
    question = relationship("Question", back_populates="submissions")
    evaluation = relationship("Evaluation", back_populates="submission", uselist=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)

    # Scores (0-10 scale)
    overall_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    intro_score = Column(Float, default=0.0)
    body_score = Column(Float, default=0.0)
    keyword_score = Column(Float, default=0.0)
    structure_score = Column(Float, default=0.0)
    factual_score = Column(Float, default=0.0)
    conclusion_score = Column(Float, default=0.0)
    word_limit_score = Column(Float, default=0.0)
    analysis_score = Column(Float, default=0.0)
    diagram_score = Column(Float, default=0.0)
    multidimensional_score = Column(Float, default=0.0)

    # Feedback
    feedback_summary = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)      # list of strength strings
    weaknesses = Column(JSON, nullable=True)      # list of weakness strings
    improvements = Column(JSON, nullable=True)    # list of improvement suggestions
    model_answer = Column(Text, nullable=True)
    keywords_found = Column(JSON, nullable=True)  # keywords detected in answer
    keywords_missed = Column(JSON, nullable=True) # keywords that should have been included
    topper_benchmark = Column(Text, nullable=True)
    dimension_analysis = Column(JSON, nullable=True)  # {political, economic, social, etc.}
    marks_obtained = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    submission = relationship("Submission", back_populates="evaluation")


class MCQDocument(Base):
    """Document uploaded by institute for UPSC-style MCQ generation."""
    __tablename__ = "mcq_documents"

    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), default="pdf")  # pdf, txt, docx
    title = Column(String(500), nullable=True)
    subject_area = Column(String(200), nullable=True)  # History, Polity, Geography, etc.
    extracted_text = Column(Text, nullable=True)
    status = Column(String(50), default="uploaded")  # uploaded, processing, generated, failed
    num_questions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    mcq_questions = relationship("MCQQuestion", back_populates="document", cascade="all, delete-orphan")
    institute = relationship("Institute")
    uploader = relationship("User")


class MCQQuestion(Base):
    """UPSC-style MCQ generated from an uploaded document."""
    __tablename__ = "mcq_questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("mcq_documents.id"), nullable=False, index=True)
    question_type = Column(String(100), nullable=False)
    # multi_statement | assertion_reason | match_following | how_many | direct | negative
    question_text = Column(Text, nullable=False)
    statements = Column(JSON, nullable=True)    # list of statement strings (for multi_statement / how_many)
    pairs = Column(JSON, nullable=True)          # [{item, match}] for match_following
    options = Column(JSON, nullable=False)       # [{"label": "a", "text": "..."}]
    correct_option = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)
    topic = Column(String(200), nullable=True)
    difficulty = Column(String(50), default="moderate")  # easy | moderate | hard
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("MCQDocument", back_populates="mcq_questions")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")


class TopperAnswer(Base):
    __tablename__ = "topper_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    file_path = Column(String(500), nullable=True)
    ocr_text = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    exam_type = Column(String(50), default="HCS")
    subject = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)       # list of tags
    source = Column(String(200), nullable=True)  # "InsightsIAS", "DrishtiIAS", "LLM Generated", etc.
    is_anonymized = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    question = relationship("Question", back_populates="topper_answers")
