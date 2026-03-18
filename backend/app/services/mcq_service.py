"""
UPSC-Style MCQ Generation Service
===================================
Generates authentic UPSC Prelims-style MCQs from uploaded documents/books.

Based on 40-year UPSC pattern analysis (1985-2025):
  - 60%+ questions are statement-based
  - Multi-statement ("Consider the following statements")
  - Statement I & II (cause-effect / assertion-reason)
  - Match the Following (pair matching)
  - "How many statements are correct?" (post-2020 trend)
  - Direct single-answer factual questions
  - Negative framing ("Which is NOT correct?")

Pipeline:
  1. extract_text()   — PDF/text extraction using PyMuPDF
  2. chunk_text()     — split into ~1500-char chunks for context window
  3. generate_mcqs()  — LLM (Groq → Gemini → Mock) generates structured MCQs
"""

import json
import math
import re
import logging
import random
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ── LLM (reuses same priority logic as evaluation_service) ────────────────────
_mcq_llm = None


def get_mcq_llm():
    global _mcq_llm
    if _mcq_llm is not None:
        return _mcq_llm

    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            _mcq_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=settings.GROQ_API_KEY,
                temperature=0.5,
                max_tokens=8192,
            )
            logger.info("MCQ LLM: Groq (llama-3.3-70b)")
            return _mcq_llm
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _mcq_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=gemini_key,
                temperature=0.5,
            )
            logger.info("MCQ LLM: Gemini (gemini-2.0-flash)")
            return _mcq_llm
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    logger.warning("MCQ LLM: No API key — using mock generator")
    return None


# ── Text Extraction ────────────────────────────────────────────────────────────

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract raw text from PDF, TXT, or other supported formats.

    For scanned/image-only PDFs, falls back to OCR via Gemini if available,
    otherwise returns a placeholder so mock MCQs can still be generated.
    """
    try:
        if file_type == "pdf":
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            pages = []
            for page in doc:
                pages.append(page.get_text())
            doc.close()
            text = "\n".join(pages).strip()

            # Scanned PDF — very little text extracted
            if len(text) < 100:
                logger.warning(f"PDF appears to be scanned/image-based: {file_path}")
                # Try Gemini Vision OCR as fallback
                gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
                if gemini_key:
                    text = _ocr_pdf_with_gemini(file_path, gemini_key) or text
                # If still empty, return a signal so caller can use mock
                if len(text) < 100:
                    return "__SCANNED_PDF__"
            return text

        if file_type in ("txt", "text"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
    return ""


def _ocr_pdf_with_gemini(file_path: str, api_key: str) -> str:
    """Use Gemini Vision to OCR the first few pages of a scanned PDF."""
    try:
        import fitz
        import base64
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        doc = fitz.open(file_path)
        all_text = []
        # Process up to 5 pages to avoid rate limits
        for i, page in enumerate(doc):
            if i >= 5:
                break
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode()
            response = model.generate_content([
                {"mime_type": "image/png", "data": img_b64},
                "Extract all text from this page. Return only the text content, no commentary.",
            ])
            all_text.append(response.text)
        doc.close()
        return "\n".join(all_text)
    except Exception as e:
        logger.warning(f"Gemini OCR fallback failed: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for MCQ generation."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Try to break at a sentence boundary
        last_period = chunk.rfind(". ")
        if last_period > chunk_size // 2:
            chunk = chunk[: last_period + 1]
        chunks.append(chunk.strip())
        advance = len(chunk) - overlap
        if advance <= 0:
            break  # remaining text is smaller than overlap — we're done
        start += advance
    return chunks


# ── UPSC MCQ Generation Prompt ─────────────────────────────────────────────────

UPSC_MCQ_SYSTEM_PROMPT = """You are an expert UPSC question paper setter with 40+ years of experience designing UPSC Civil Services Prelims questions.

You must generate AUTHENTIC UPSC-style MCQs strictly following these proven patterns from UPSC history:

## UPSC QUESTION TYPES (use these exact formats):

### Type 1: MULTI_STATEMENT ("Consider the following statements")
Question format:
"Consider the following statements regarding [TOPIC]:
1. [Statement A]
2. [Statement B]
3. [Statement C - optional]
Which of the statements given above is/are correct?"

Options MUST be one of these standard sets:
- For 2 statements: (a) 1 only  (b) 2 only  (c) Both 1 and 2  (d) Neither 1 nor 2
- For 3 statements: (a) 1 only  (b) 2 and 3 only  (c) 1 and 3 only  (d) 1, 2 and 3

### Type 2: ASSERTION_REASON ("Statement I and Statement II")
Question format:
"Consider the following two statements:
Statement I: [Main assertion]
Statement II: [Reason/explanation]
Which one of the following is correct in respect of the above statements?"

Options MUST be:
(a) Both Statement I and Statement II are correct and Statement II explains Statement I
(b) Both Statement I and Statement II are correct but Statement II does NOT explain Statement I
(c) Statement I is correct but Statement II is incorrect
(d) Statement I is incorrect but Statement II is correct

### Type 3: MATCH_FOLLOWING ("Match the following")
Question format:
"Match the following [List I] with [List II]:
List I               List II
A. [Item 1]     1. [Match 1]
B. [Item 2]     2. [Match 2]
C. [Item 3]     3. [Match 3]
D. [Item 4]     4. [Match 4]
Select the correct answer using the codes given below:"

Options MUST be:
(a) A-2, B-3, C-4, D-1
(b) A-3, B-2, C-1, D-4
(c) A-1, B-4, C-3, D-2
(d) [correct matching]

### Type 4: HOW_MANY ("How many of the above statements are correct?")
Question format:
"Consider the following statements:
1. [Statement A]
2. [Statement B]
3. [Statement C]
How many of the above statements are correct?"

Options MUST be:
(a) Only one
(b) Only two
(c) All three
(d) None

### Type 5: DIRECT (Single direct answer)
Question format: "Which one of the following [describes / is correct about] [TOPIC]?"
Standard 4 options (a), (b), (c), (d)

### Type 6: NEGATIVE ("Which is NOT correct?")
Question format: "Which of the following statements about [TOPIC] is NOT correct?"
Standard 4 options where 3 are true and 1 is false (the correct answer)

## CRITICAL RULES:
1. Every question must be DIRECTLY based on content from the provided text
2. Questions must test UNDERSTANDING, not just rote memory
3. Use precise, formal language typical of UPSC
4. Incorrect options must be plausible — not obviously wrong
5. Statements in multi-statement questions: mix true and false thoughtfully
6. Difficulty mix: 30% easy, 45% moderate, 25% hard
7. NEVER repeat information across questions

## OUTPUT FORMAT (strict JSON):
Return a JSON array of MCQ objects. Each object:
{
  "question_type": "multi_statement|assertion_reason|match_following|how_many|direct|negative",
  "question_text": "Full question text including statements/lists if any",
  "statements": ["stmt1", "stmt2", ...] or null,
  "pairs": [{"item": "A. Term", "match": "1. Definition"}, ...] or null,
  "options": [
    {"label": "a", "text": "Option A text"},
    {"label": "b", "text": "Option B text"},
    {"label": "c", "text": "Option C text"},
    {"label": "d", "text": "Option D text"}
  ],
  "correct_option": "a|b|c|d",
  "explanation": "Why this is the correct answer, citing specific facts from the text",
  "topic": "Specific topic name",
  "difficulty": "easy|moderate|hard"
}

Return ONLY valid JSON array. No extra text or markdown."""


def build_mcq_user_prompt(text_chunk: str, num_questions: int, subject_area: str) -> str:
    return f"""Generate exactly {num_questions} UPSC Prelims-style MCQs from the following content.
Subject area: {subject_area or 'General Studies'}

Use a MIX of question types:
- {max(1, num_questions // 3)} multi_statement questions
- {max(1, num_questions // 5)} assertion_reason questions
- {max(1, num_questions // 6)} match_following questions (only if enough distinct facts)
- {max(1, num_questions // 6)} how_many questions
- Remaining: direct and negative questions

CONTENT:
---
{text_chunk}
---

Return ONLY a valid JSON array of {num_questions} MCQ objects."""


# ── Mock Generator (fallback when no API key) ──────────────────────────────────

def _mock_mcqs(num: int, subject_area: str) -> list[dict]:
    """Generate demo UPSC-style MCQs when no LLM API key is configured."""
    templates = [
        {
            "question_type": "multi_statement",
            "question_text": f"Consider the following statements regarding {subject_area or 'Indian Polity'}:\n1. The Constitution of India was adopted on 26th November, 1949.\n2. India became a republic on 26th January, 1950.\nWhich of the statements given above is/are correct?",
            "statements": [
                "The Constitution of India was adopted on 26th November, 1949.",
                "India became a republic on 26th January, 1950.",
            ],
            "pairs": None,
            "options": [
                {"label": "a", "text": "1 only"},
                {"label": "b", "text": "2 only"},
                {"label": "c", "text": "Both 1 and 2"},
                {"label": "d", "text": "Neither 1 nor 2"},
            ],
            "correct_option": "c",
            "explanation": "Both statements are factually correct. The Constituent Assembly adopted the Constitution on 26 November 1949, and it came into force on 26 January 1950, making India a republic.",
            "topic": subject_area or "Indian Polity",
            "difficulty": "easy",
        },
        {
            "question_type": "assertion_reason",
            "question_text": "Consider the following two statements:\nStatement I: Preamble of the Indian Constitution can be amended under Article 368.\nStatement II: The Preamble is not a part of the Constitution and hence not amenable to amendment.\nWhich one of the following is correct in respect of the above statements?",
            "statements": None,
            "pairs": None,
            "options": [
                {"label": "a", "text": "Both Statement I and Statement II are correct and Statement II explains Statement I"},
                {"label": "b", "text": "Both Statement I and Statement II are correct but Statement II does NOT explain Statement I"},
                {"label": "c", "text": "Statement I is correct but Statement II is incorrect"},
                {"label": "d", "text": "Statement I is incorrect but Statement II is correct"},
            ],
            "correct_option": "c",
            "explanation": "In Kesavananda Bharati v. State of Kerala (1973), the Supreme Court held that the Preamble IS a part of the Constitution and can be amended under Article 368, subject to the basic structure doctrine. The Preamble was amended by the 42nd Amendment in 1976.",
            "topic": subject_area or "Constitutional Law",
            "difficulty": "moderate",
        },
        {
            "question_type": "how_many",
            "question_text": "Consider the following statements about Fundamental Rights in India:\n1. Right to property is a Fundamental Right under Part III.\n2. Right to equality includes equality before law and equal protection of laws.\n3. Fundamental Rights are absolute and cannot be restricted.\nHow many of the above statements are correct?",
            "statements": [
                "Right to property is a Fundamental Right under Part III.",
                "Right to equality includes equality before law and equal protection of laws.",
                "Fundamental Rights are absolute and cannot be restricted.",
            ],
            "pairs": None,
            "options": [
                {"label": "a", "text": "Only one"},
                {"label": "b", "text": "Only two"},
                {"label": "c", "text": "All three"},
                {"label": "d", "text": "None"},
            ],
            "correct_option": "a",
            "explanation": "Only Statement 2 is correct. Statement 1 is wrong — Right to Property was removed from Part III by the 44th Amendment (1978) and made a legal right under Article 300A. Statement 3 is wrong — Fundamental Rights can be reasonably restricted.",
            "topic": subject_area or "Fundamental Rights",
            "difficulty": "moderate",
        },
        {
            "question_type": "direct",
            "question_text": "Which one of the following articles of the Indian Constitution deals with the amendment procedure?",
            "statements": None,
            "pairs": None,
            "options": [
                {"label": "a", "text": "Article 352"},
                {"label": "b", "text": "Article 360"},
                {"label": "c", "text": "Article 368"},
                {"label": "d", "text": "Article 370"},
            ],
            "correct_option": "c",
            "explanation": "Article 368 in Part XX of the Constitution deals with 'Power of Parliament to amend the Constitution and procedure therefor'. Articles 352, 360 deal with Emergency provisions, while Article 370 dealt with J&K's special status.",
            "topic": subject_area or "Constitutional Provisions",
            "difficulty": "easy",
        },
        {
            "question_type": "negative",
            "question_text": "Which of the following statements about the Directive Principles of State Policy (DPSP) is NOT correct?",
            "statements": None,
            "pairs": None,
            "options": [
                {"label": "a", "text": "DPSPs are contained in Part IV of the Constitution"},
                {"label": "b", "text": "DPSPs are justiciable in a court of law"},
                {"label": "c", "text": "DPSPs are inspired by the Irish Constitution"},
                {"label": "d", "text": "DPSPs aim to establish a welfare state"},
            ],
            "correct_option": "b",
            "explanation": "DPSPs are NON-justiciable — they cannot be enforced through courts (Article 37). This distinguishes them from Fundamental Rights which are justiciable. All other statements about DPSPs are correct.",
            "topic": subject_area or "Directive Principles",
            "difficulty": "easy",
        },
        {
            "question_type": "match_following",
            "question_text": "Match the following Constitutional Articles with their subjects:\nList I                         List II\nA. Article 17             1. Abolition of untouchability\nB. Article 19             2. Protection of certain rights\nC. Article 21             3. Protection of life and personal liberty\nD. Article 32             4. Right to constitutional remedies\nSelect the correct answer using the codes given below:",
            "statements": None,
            "pairs": [
                {"item": "A. Article 17", "match": "1. Abolition of untouchability"},
                {"item": "B. Article 19", "match": "2. Protection of certain rights"},
                {"item": "C. Article 21", "match": "3. Protection of life and personal liberty"},
                {"item": "D. Article 32", "match": "4. Right to constitutional remedies"},
            ],
            "options": [
                {"label": "a", "text": "A-2, B-1, C-4, D-3"},
                {"label": "b", "text": "A-3, B-4, C-1, D-2"},
                {"label": "c", "text": "A-1, B-2, C-3, D-4"},
                {"label": "d", "text": "A-4, B-3, C-2, D-1"},
            ],
            "correct_option": "c",
            "explanation": "Article 17 = Abolition of untouchability; Article 19 = Protection of certain rights (speech, assembly, etc.); Article 21 = Protection of life and personal liberty; Article 32 = Right to constitutional remedies ('Heart and Soul' of Constitution per Dr. Ambedkar).",
            "topic": subject_area or "Constitutional Articles",
            "difficulty": "moderate",
        },
    ]
    result = []
    for i in range(num):
        result.append(templates[i % len(templates)].copy())
    return result


# ── Core Generation Function ───────────────────────────────────────────────────

def generate_mcqs_from_text(
    text: str,
    num_questions: int = 10,
    subject_area: str = "",
) -> list[dict]:
    """
    Generate UPSC-style MCQs from extracted text.
    Uses smart chunk sampling + parallel LLM calls for speed.
    """
    llm = get_mcq_llm()

    if not llm or not text.strip():
        logger.info("Using mock MCQ generator")
        return _mock_mcqs(num_questions, subject_area)

    # Larger chunks → fewer API calls (5000 chars ≈ 1250 tokens, well within limits)
    chunks = chunk_text(text, chunk_size=5000)

    # Smart sampling: pick at most MAX_CHUNKS evenly distributed across the doc
    # Target ~5 MCQs per LLM call for quality + speed balance
    MAX_CHUNKS = max(1, min(4, math.ceil(num_questions / 5)))
    if len(chunks) > MAX_CHUNKS:
        step = len(chunks) / MAX_CHUNKS
        selected_chunks = [chunks[int(i * step)] for i in range(MAX_CHUNKS)]
    else:
        selected_chunks = chunks

    qs_per_chunk = math.ceil(num_questions / len(selected_chunks))
    logger.info(f"MCQ generation: {len(selected_chunks)} chunks × {qs_per_chunk} questions (parallel)")

    from langchain_core.messages import SystemMessage, HumanMessage
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _call_llm(chunk: str, batch_size: int) -> list[dict]:
        try:
            messages = [
                SystemMessage(content=UPSC_MCQ_SYSTEM_PROMPT),
                HumanMessage(content=build_mcq_user_prompt(chunk, batch_size, subject_area)),
            ]
            response = llm.invoke(messages)
            raw = response.content.strip()
            json_match = re.search(r"\[.*\]", raw, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return [m for m in parsed if _validate_mcq(m)]
        except Exception as e:
            logger.error(f"MCQ LLM call failed: {e}")
        return []

    all_mcqs = []

    # Fire all chunk requests in parallel (max 3 concurrent to respect rate limits)
    with ThreadPoolExecutor(max_workers=min(len(selected_chunks), 3)) as executor:
        futures = [
            executor.submit(_call_llm, chunk, qs_per_chunk)
            for chunk in selected_chunks
        ]
        for future in as_completed(futures):
            all_mcqs.extend(future.result())

    # Deduplicate by question text prefix
    seen: set[str] = set()
    unique_mcqs: list[dict] = []
    for m in all_mcqs:
        key = m["question_text"][:80]
        if key not in seen:
            seen.add(key)
            unique_mcqs.append(m)

    # Top up with mocks if LLM returned fewer than requested
    if len(unique_mcqs) < num_questions:
        logger.warning(f"LLM returned {len(unique_mcqs)}/{num_questions}, padding with mock MCQs")
        unique_mcqs.extend(_mock_mcqs(num_questions - len(unique_mcqs), subject_area))

    return unique_mcqs[:num_questions]


def _validate_mcq(mcq: dict) -> bool:
    """Validate MCQ dict has required fields. Normalizes correct_option to lowercase letter."""
    required = ["question_type", "question_text", "options", "correct_option"]
    if not all(k in mcq for k in required):
        return False
    if not isinstance(mcq.get("options"), list) or len(mcq["options"]) < 4:
        return False
    valid_types = {"multi_statement", "assertion_reason", "match_following", "how_many", "direct", "negative"}
    if mcq.get("question_type") not in valid_types:
        return False
    # Normalize correct_option: LLMs may return "A", "(a)", "option a", "1", etc.
    raw = str(mcq["correct_option"]).strip().lower().strip("(). ")
    # Handle numeric: "1"→"a", "2"→"b", "3"→"c", "4"→"d"
    if raw in ("1", "2", "3", "4"):
        raw = chr(ord("a") + int(raw) - 1)
    # Accept only first character if something like "answer: a"
    if raw and raw[0] in ("a", "b", "c", "d"):
        raw = raw[0]
    if raw not in ("a", "b", "c", "d"):
        return False
    mcq["correct_option"] = raw  # normalize in-place
    return True
