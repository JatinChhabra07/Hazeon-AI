"""
Hazeon AI — UPSC/HCS Mains Answer Evaluation Platform
Main FastAPI Application

Powered by: LangChain + LangGraph + ChromaDB + FastAPI
"""
import os
import logging
import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import auth, upload, dashboard, topper
from app.routers import mcq

# ── Centralized logging ───────────────────────────────────────────────────────
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    # Silence noisy third-party loggers
    "loggers": {
        "httpx": {"level": "WARNING"},
        "httpcore": {"level": "WARNING"},
        "chromadb": {"level": "WARNING"},
        "langchain": {"level": "WARNING"},
        "opentelemetry": {"level": "ERROR"},
    },
})


def seed_questions(db):
    """Ensure question bank is always populated — runs independently of full demo seed."""
    from app.models.models import Question

    if db.query(Question).count() > 0:
        return  # questions already exist

    print("📚 Seeding question bank...")
    questions = [
        Question(
            text="Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency at the district level.",
            subject="GS2 - Governance", topic="Good Governance", year=2025, exam_type="HCS",
            marks=15, word_limit=250, difficulty="moderate",
            model_answer_points=["Define good governance pillars", "Cite SARAL, CM Window", "District admin challenges", "e-governance initiatives", "Way Forward with recommendations"],
        ),
        Question(
            text="Analyze the impact of Green Revolution on agriculture in Haryana. What are the emerging challenges and how can sustainable agriculture be promoted?",
            subject="GS3 - Economy", topic="Agriculture", year=2025, exam_type="HCS",
            marks=15, word_limit=250, difficulty="moderate",
            model_answer_points=["Green Revolution impact with data", "Water depletion crisis", "Stubble burning", "MSP dependency", "Crop diversification", "Natural farming initiatives"],
        ),
        Question(
            text="Examine the changing sex ratio in Haryana. Evaluate the effectiveness of Beti Bachao Beti Padhao campaign.",
            subject="GS1 - Society", topic="Gender Issues", year=2024, exam_type="HCS",
            marks=15, word_limit=250, difficulty="moderate",
            model_answer_points=["Census data on sex ratio", "BBBP scheme details", "Outcomes and improvements", "Remaining challenges", "Multi-stakeholder approach"],
        ),
        Question(
            text="'Cooperative federalism is the need of the hour for India.' Discuss with reference to recent Centre-State relations.",
            subject="GS2 - Polity", topic="Federalism", year=2025, exam_type="HCS",
            marks=20, word_limit=300, difficulty="hard",
            model_answer_points=["Constitutional provisions Art 245-263", "GST impact on fiscal federalism", "NITI Aayog role", "Recent disputes", "ISC meetings", "Way Forward"],
        ),
        Question(
            text="What are the ethical challenges faced by civil servants in India? Discuss with examples from Haryana context.",
            subject="GS4 - Ethics", topic="Ethics in Governance", year=2025, exam_type="HCS",
            marks=15, word_limit=250, difficulty="moderate",
            model_answer_points=["Define ethical governance", "Common dilemmas", "Conflict of interest", "Haryana-specific examples", "ARC recommendations", "Code of conduct"],
        ),
        Question(
            text="Critically analyze the industrial development of Haryana with special focus on the IT corridor of Gurugram and its socio-economic impact.",
            subject="GS3 - Economy", topic="Industrial Development", year=2024, exam_type="HCS",
            marks=15, word_limit=250, difficulty="moderate",
            model_answer_points=["Industrial policy overview", "Gurugram IT sector", "HSIIDC role", "Employment generation", "Urban challenges", "Regional imbalance"],
        ),
        Question(
            text="Discuss the significance of Panchayati Raj Institutions in Haryana for grassroots democracy. What reforms are needed?",
            subject="GS2 - Governance", topic="Local Governance", year=2024, exam_type="HCS",
            marks=15, word_limit=250, difficulty="easy",
            model_answer_points=["73rd Amendment", "Haryana Panchayati Raj Act", "Women reservation", "Gram Sabha empowerment", "Financial autonomy", "Capacity building"],
        ),
        Question(
            text="Examine the water crisis in Haryana and suggest a comprehensive water management strategy.",
            subject="GS3 - Environment", topic="Water Management", year=2025, exam_type="HCS",
            marks=15, word_limit=250, difficulty="moderate",
            model_answer_points=["Groundwater depletion data", "SYL canal issue", "Paddy cultivation impact", "Micro-irrigation", "Jal Jeevan Mission", "Policy recommendations"],
        ),
        Question(
            text="Discuss the role of education in social transformation of Haryana. Evaluate recent education policies.",
            subject="GS1 - Society", topic="Education", year=2024, exam_type="HCS",
            marks=15, word_limit=250, difficulty="easy",
            model_answer_points=["Literacy rates progression", "NEP 2020 implementation", "Super 100 scheme", "School consolidation", "Higher education", "Skill development"],
        ),
        Question(
            text="Analyze India's neighborhood first policy and its implications for regional stability in South Asia.",
            subject="GS2 - IR", topic="Foreign Policy", year=2025, exam_type="UPSC",
            marks=15, word_limit=250, difficulty="hard",
            model_answer_points=["Neighborhood first policy evolution", "Bilateral relations", "SAGAR doctrine", "BRI challenge", "Connectivity projects", "Way Forward"],
        ),
    ]
    db.add_all(questions)
    db.commit()
    print(f"✅ {len(questions)} questions seeded into question bank.")
    return questions


def seed_demo_data():
    """Populate database with realistic HCS demo data for impressive presentation."""
    from app.models.models import Institute, User, Question, Submission, Evaluation, TopperAnswer
    from app.routers.auth import hash_password
    import datetime
    import random

    db = SessionLocal()

    # Always ensure question bank is populated first
    seed_questions(db)

    # Skip full demo seed if already seeded
    if db.query(Institute).count() > 0:
        db.close()
        return

    print("🌱 Seeding demo data...")

    # ── Institutes ────────────────────────────────────
    institutes = [
        Institute(name="Drishti IAS Chandigarh", code="DRISHTI-CHD", city="Chandigarh", state="Punjab/Haryana", plan_type="premium"),
        Institute(name="Vision HCS Academy", code="VISION-HCS", city="Rohtak", state="Haryana", plan_type="basic"),
        Institute(name="Lakshya IAS Gurugram", code="LAKSHYA-GGN", city="Gurugram", state="Haryana", plan_type="pilot"),
    ]
    db.add_all(institutes)
    db.flush()

    # ── Users ─────────────────────────────────────────
    admin = User(
        email="admin@hazeon.com", password_hash=hash_password("admin123"),
        full_name="Dr. Rajesh Kumar", role="institute_admin", institute_id=institutes[0].id,
    )
    students = [
        User(email="priya@student.com", password_hash=hash_password("student123"),
             full_name="Priya Sharma", role="student", institute_id=institutes[0].id),
        User(email="aman@student.com", password_hash=hash_password("student123"),
             full_name="Aman Verma", role="student", institute_id=institutes[0].id),
        User(email="neha@student.com", password_hash=hash_password("student123"),
             full_name="Neha Gupta", role="student", institute_id=institutes[0].id),
        User(email="rohit@student.com", password_hash=hash_password("student123"),
             full_name="Rohit Singh", role="student", institute_id=institutes[0].id),
        User(email="kavita@student.com", password_hash=hash_password("student123"),
             full_name="Kavita Yadav", role="student", institute_id=institutes[0].id),
    ]
    db.add(admin)
    db.add_all(students)
    db.flush()

    # ── Questions (already seeded by seed_questions) ──
    questions = db.query(Question).order_by(Question.id).all()

    # ── Sample Submissions & Evaluations ──────────────
    sample_texts = [
        "Good governance is fundamental to the development of any state. In Haryana, several initiatives have been taken to improve governance quality. The SARAL platform provides single-window access to 500+ government services. The CM Window portal enables direct grievance redressal. However, challenges remain including bureaucratic resistance, digital divide, and capacity constraints. E-governance initiatives need to be complemented with administrative reforms at the district level. Way Forward: Strengthen district administration through training, improve digital literacy, and adopt outcome-based monitoring.",
        "The Green Revolution transformed Haryana's agriculture, making it India's breadbasket. High-yielding varieties, chemical fertilizers, and irrigation through Bhakra canal system boosted food production dramatically. However, this has created serious challenges: depleting water table (falling 1-2m annually), soil degradation, stubble burning crisis, and over-reliance on wheat-paddy cycle. The state government has launched initiatives like Mera Pani Meri Virasat for crop diversification. Natural farming is being promoted. Sustainable agriculture requires micro-irrigation, organic farming incentives, and MSP reforms.",
        "Haryana's sex ratio has historically been among India's lowest, reflecting deep-rooted patriarchal mindsets. The Beti Bachao Beti Padhao campaign, launched from Panipat in 2015, has shown remarkable results. Sex ratio at birth improved from 834 in 2011 to over 920 recently. Key interventions include strict enforcement of PC-PNDT Act, awareness campaigns, and incentives for girl child education. However, honor killings, domestic violence, and glass ceiling in professional spaces remain concerns.",
        "The ethical challenges faced by civil servants require careful balancing of competing interests. In Haryana, officials face dilemmas related to political interference in transfers, caste-based pressures, and corruption. Integrity, impartiality, and dedication to public service are essential values. The Second ARC recommended a comprehensive code of ethics for civil servants.",
        "Industrial development in Haryana, particularly the IT corridor in Gurugram, has transformed the state's economic landscape. From being primarily agrarian, Haryana now has a robust industrial base with automobile, IT, and textile sectors. However, this development has been concentrated in southern Haryana, creating significant regional imbalance.",
    ]

    days_offsets = [30, 25, 20, 15, 10, 7, 5, 3, 2, 1]
    eval_idx = 0
    for i, student in enumerate(students):
        num_subs = random.randint(3, 6)
        for j in range(num_subs):
            q_idx = (i * 2 + j) % len(questions)
            text = sample_texts[(i + j) % len(sample_texts)]

            sub = Submission(
                student_id=student.id,
                question_id=questions[q_idx].id,
                file_path=f"demo/sample_{eval_idx}.pdf",
                file_type="pdf",
                ocr_text=text,
                status="evaluated",
                word_count=len(text.split()),
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=days_offsets[eval_idx % len(days_offsets)]),
            )
            db.add(sub)
            db.flush()

            # Generate varied scores
            base = random.uniform(5.0, 8.5)
            evaluation = Evaluation(
                submission_id=sub.id,
                overall_score=round(base, 1),
                relevance_score=round(base + random.uniform(-1.5, 1.5), 1),
                intro_score=round(base + random.uniform(-2, 1), 1),
                body_score=round(base + random.uniform(-1, 1.5), 1),
                keyword_score=round(base + random.uniform(-1.5, 1), 1),
                structure_score=round(base + random.uniform(-1, 2), 1),
                factual_score=round(base + random.uniform(-2, 1), 1),
                conclusion_score=round(base + random.uniform(-2, 0.5), 1),
                word_limit_score=round(random.uniform(7, 9.5), 1),
                analysis_score=round(base + random.uniform(-2, 0.5), 1),
                diagram_score=round(random.uniform(1, 4), 1),
                multidimensional_score=round(base + random.uniform(-1.5, 1), 1),
                feedback_summary=f"The answer demonstrates {'good' if base > 6.5 else 'moderate'} understanding of the topic.",
                strengths=["Clear structure", "Good use of examples", "Relevant keywords used"],
                weaknesses=["Could add more dimensions", "Needs stronger conclusion"],
                improvements=["Add diagrams", "Include more data points", "Strengthen Way Forward"],
                model_answer="A comprehensive answer should cover all dimensions...",
                keywords_found=["governance", "reform", "development"],
                keywords_missed=["constitutional", "ARC", "accountability"],
                topper_benchmark="A topper would structure this answer with clear headings...",
                dimension_analysis={"political": True, "economic": True, "social": bool(j % 2), "environmental": False, "ethical": False, "legal": bool(j % 3)},
                marks_obtained=round(base / 10 * questions[q_idx].marks, 1),
            )
            db.add(evaluation)
            eval_idx += 1

    # ── Topper Answers ────────────────────────────────
    topper_texts = [
        "Good governance ensures transparency, accountability, and efficient public service delivery. Haryana has pioneered several governance reforms...",
        "The Green Revolution, while transforming Haryana into India's granary, has created an unsustainable agricultural model...",
        "The declining sex ratio in Haryana is a manifestation of deep-rooted socio-cultural factors...",
    ]
    for i, text in enumerate(topper_texts):
        topper = TopperAnswer(
            question_id=questions[i].id, ocr_text=text,
            score=round(random.uniform(8.0, 9.5), 1), rank=random.randint(1, 20),
            year=2024, exam_type="HCS", subject=questions[i].subject,
            tags=["model answer", "topper", questions[i].topic or ""],
        )
        db.add(topper)

    db.commit()
    db.close()
    print("✅ Demo data seeded successfully!")


def _warmup_chromadb():
    """Pre-import ChromaDB at startup to avoid first-request hang on Windows (Defender .pyd scan)."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        client.get_or_create_collection("topper_answers", metadata={"hnsw:space": "cosine"})
        print("✅ ChromaDB warmed up")
    except Exception as e:
        print(f"⚠️  ChromaDB warmup skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    init_db()
    seed_demo_data()
    _warmup_chromadb()
    yield


# ── Create FastAPI App ────────────────────────────────
app = FastAPI(
    title="Hazeon AI — Answer Evaluation Platform",
    description="AI-powered UPSC/HCS Mains answer evaluation using LangChain + LangGraph",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Production Middlewares ───────────────────────────
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"DEBUG: {request.method} {request.url.path} processed in {process_time:.4f}s")
    return response

# ── Error Handlers ────────────────────────────────────
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support.", "error": str(exc)},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error in your request.", "errors": exc.errors()},
    )

# ── Routers ───────────────────────────────────────────
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(topper.router)
app.include_router(mcq.router)

# ── Serve uploads ─────────────────────────────────────
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {
        "name": "Hazeon AI",
        "version": settings.APP_VERSION,
        "description": "Premium UPSC/HCS Mains Answer Evaluation Platform",
        "status": "online",
        "powered_by": ["LangChain", "LangGraph", "ChromaDB", "FastAPI"],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}

