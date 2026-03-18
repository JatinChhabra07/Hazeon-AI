"""
Live end-to-end test of the Hazeon AI evaluation pipeline.
Tests: Groq LLM + ChromaDB RAG + anti-hallucination evaluation
Run: cd backend && python test_evaluation_live.py
"""
import json
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("HAZEON AI — Live Evaluation Pipeline Test")
print("=" * 60)

# ── Test 1: Config ────────────────────────────────────────
print("\n[1/4] Loading config...")
from app.config import settings
print(f"  App: {settings.APP_NAME}")
print(f"  Groq key: {'[OK]' if settings.GROQ_API_KEY else '[MISSING]'}")
print(f"  Gemini key: {'[OK]' if settings.GEMINI_API_KEY else '[MISSING]'}")

# ── Test 2: LLM init ──────────────────────────────────────
print("\n[2/4] Initialising LLM...")
from app.services.evaluation_service import get_llm
llm = get_llm()
if llm:
    print(f"  LLM: [OK] {type(llm).__name__}")
else:
    print("  LLM: [MISSING] No LLM — will use smart mock")

# ── Test 3: ChromaDB RAG ──────────────────────────────────
print("\n[3/4] Testing ChromaDB RAG retrieval...")
try:
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    col = client.get_or_create_collection("topper_answers")
    total = col.count()
    print(f"  ChromaDB: [OK] {total} topper answers indexed")
    if total > 0:
        results = col.query(
            query_texts=["good governance Haryana district administration"],
            n_results=2,
        )
        docs = results["documents"][0] if results["documents"] else []
        print(f"  RAG test query returned {len(docs)} results")
        if docs:
            print(f"  Top result preview: {docs[0][:120]}...")
except Exception as e:
    print(f"  ChromaDB: [FAILED] {e}")

# ── Test 4: Full evaluation ───────────────────────────────
print("\n[4/4] Running full evaluation (Groq + RAG)...")
print("  Question: Good governance challenges in Haryana")
print("  Sending student answer to LLM...")

from app.services.evaluation_service import run_evaluation

STUDENT_ANSWER = """
Good governance is essential for development and welfare of citizens. In Haryana,
the government has launched several initiatives like SARAL platform which provides
single window access to government services. The CM Window portal helps in grievance
redressal. However, challenges remain in terms of administrative efficiency,
corruption at lower levels, and digital divide in rural areas.

Way Forward:
1. Strengthen e-governance initiatives at district level
2. Regular training of government staff
3. Citizen feedback mechanism
4. Use of technology for transparent service delivery
5. Accountability frameworks for officials
"""

try:
    result = run_evaluation(
        ocr_text=STUDENT_ANSWER,
        question_text="Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency at the district level.",
        question_subject="GS2 - Governance",
        question_marks=15,
        question_word_limit=250,
        model_answer_points=["Define good governance pillars", "Cite SARAL, CM Window", "District admin challenges", "Way Forward with recommendations"],
    )

    print("\n" + "=" * 60)
    print("EVALUATION RESULT")
    print("=" * 60)
    print(f"  Overall Score:     {result['overall_score']}/10")
    print(f"  Marks Obtained:    {result['marks_obtained']}/15")
    print(f"  Relevance:         {result['relevance_score']}/10")
    print(f"  Structure:         {result['structure_score']}/10")
    print(f"  Keywords Found:    {result['keywords_found']}")
    print(f"  Keywords Missed:   {result['keywords_missed'][:5]}")
    print(f"\n  Feedback: {result['feedback_summary']}")
    print(f"\n  Strengths:")
    for s in result['strengths']:
        print(f"    + {s}")
    print(f"\n  Improvements:")
    for i in result['improvements'][:3]:
        print(f"    → {i}")
    print(f"\n  Topper Benchmark: {result['topper_benchmark']}")
    print(f"\n  Dimensions covered: {result['dimension_analysis']}")
    print("\n[PASS] PIPELINE TEST PASSED")

except Exception as e:
    print(f"\n[FAIL] Evaluation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
