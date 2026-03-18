from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

_is_sqlite = "sqlite" in settings.DATABASE_URL

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,      # re-validate connections that went idle (critical for Neon serverless)
    pool_recycle=300,        # recycle connections every 5 min to avoid Neon's idle timeout
    pool_size=10 if not _is_sqlite else 1,       # max persistent connections
    max_overflow=20 if not _is_sqlite else 0,    # burst connections above pool_size
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.models import (
        User, Institute, Question, Submission, Evaluation, TopperAnswer,
        MCQDocument, MCQQuestion, PasswordResetToken,
    )
    Base.metadata.create_all(bind=engine)
