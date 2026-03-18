"""
Quick Groq API test — no heavy imports, runs in ~5 seconds.
Tests: anti-hallucination evaluation prompt with real Groq call.
Run: cd backend && python test_quick.py
"""
import json, os, sys

# Load .env manually (no pydantic needed)
env = {}
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path, encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

GROQ_KEY = env.get("GROQ_API_KEY", "")
if not GROQ_KEY:
    print("[FAIL] GROQ_API_KEY not found in .env")
    sys.exit(1)

print("=" * 60)
print("HAZEON AI — Quick Groq Evaluation Test")
print("=" * 60)
print(f"  Groq key: {GROQ_KEY[:8]}...{GROQ_KEY[-4:]}")

# Direct Groq API call using urllib (no langchain needed)
import httpx

TOPPER_ANSWER = """Good governance (UN ESCAP 8 pillars: transparency, accountability,
responsiveness, equitability, inclusiveness, effectiveness, rule of law, participation)
requires structural reforms. Haryana Achievements: SARAL platform 550+ services with
1 crore annual transactions; CM Window resolved 50 lakh grievances (94% resolution rate);
CCTNS 100% FIR digitization. Challenges: 30% admin vacancy; political transfers
(Ashok Khemka 53 transfers in 32 years); digital divide rural 45% vs urban 72%;
8 lakh pending court cases. Way Forward (ARC2): 2-year posting security (Rec 7.15),
District Performance Index, Gram Sachivalaya strengthening, Haryana Ombudsman 30-day resolution."""

STUDENT_ANSWER = """Good governance is essential for development and welfare of citizens.
In Haryana, the government has launched several initiatives like SARAL platform which
provides single window access to government services. The CM Window portal helps in
grievance redressal. However, challenges remain in terms of administrative efficiency,
corruption at lower levels, and digital divide in rural areas.
Way Forward:
1. Strengthen e-governance initiatives at district level
2. Regular training of government staff
3. Citizen feedback mechanism
4. Use of technology for transparent service delivery"""

SYSTEM = """You are a senior UPSC/HCS Mains answer evaluator with 20+ years of experience.

CRITICAL ANTI-HALLUCINATION RULES:
1. Base evaluation ONLY on the topper reference answer provided — do NOT add external facts
2. keywords_found must contain ONLY terms that literally appear in the student answer
3. keywords_missed must reference ONLY keywords present in the topper reference
4. Scores must reflect ACTUAL content in the student answer
5. Return ONLY valid JSON — no markdown, no text before or after

Score 0-10 for: relevance_score, intro_score, body_score, keyword_score, structure_score,
factual_score, conclusion_score, word_limit_score, analysis_score, diagram_score, multidimensional_score,
overall_score. Also return: marks_obtained (out of 15), feedback_summary (2-3 sentences),
strengths (list 3), weaknesses (list 3), improvements (list 3),
keywords_found (only from student answer), keywords_missed (only from topper reference),
topper_benchmark (comparing to the PROVIDED topper reference)."""

USER_MSG = f"""Question (GS2 - Governance, 15 marks, 250 words, 2025 HCS):
Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency.

Topper Reference Answer (Score 9.0/10):
{TOPPER_ANSWER}

Student Answer ({len(STUDENT_ANSWER.split())} words):
{STUDENT_ANSWER}

Return ONLY valid JSON."""

payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_MSG},
    ],
    "temperature": 0.1,
    "max_tokens": 1500,
    "response_format": {"type": "json_object"},
}

print("\n  Calling Groq API (llama-3.3-70b)...")
try:
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    result = json.loads(content)

    print("\n" + "=" * 60)
    print("EVALUATION RESULT")
    print("=" * 60)
    print(f"  Overall Score  : {result.get('overall_score')}/10")
    print(f"  Marks Obtained : {result.get('marks_obtained')}/15")
    print(f"  Relevance      : {result.get('relevance_score')}/10")
    print(f"  Structure      : {result.get('structure_score')}/10")
    print(f"  Analysis       : {result.get('analysis_score')}/10")
    print(f"  Keywords Found : {result.get('keywords_found')}")
    print(f"  Keywords Missed: {result.get('keywords_missed', [])[:5]}")
    print(f"\n  Feedback: {result.get('feedback_summary')}")
    print(f"\n  Strengths:")
    for s in result.get("strengths", []):
        print(f"    + {s}")
    print(f"\n  Weaknesses:")
    for w in result.get("weaknesses", []):
        print(f"    - {w}")
    print(f"\n  Topper Benchmark:")
    print(f"    {result.get('topper_benchmark')}")
    print("\n" + "=" * 60)
    print("[PASS] Anti-hallucination evaluation pipeline working!")
    print("=" * 60)

except httpx.HTTPStatusError as e:
    print(f"[FAIL] HTTP {e.response.status_code}: {e.response.text[:300]}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
