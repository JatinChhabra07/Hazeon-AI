"""
AI Evaluation Engine — LangGraph powered answer evaluation pipeline.

Pipeline (3 nodes):
  1. analyze_text       → structural analysis of the answer
  2. retrieve_topper    → RAG from ChromaDB topper database
  3. evaluate_with_llm  → Groq LLM scores + detailed feedback JSON

LLM Priority: Groq (llama-3.3-70b) → Gemini → Mock
"""
import json
import os
import random
import logging
from typing import TypedDict, Optional, List

from app.config import settings

logger = logging.getLogger(__name__)

# ── LLM Initialization ────────────────────────────────────────────────────────
_llm = None


def get_llm():
    """
    Return configured LLM.
    Priority: Fine-tuned Hazeon model → Groq → Gemini → None
    """
    global _llm
    if _llm is not None:
        return _llm

    # 0. Fine-tuned Hazeon UPSC evaluator (trained on topper answers)
    finetuned_path = getattr(settings, "FINETUNED_MODEL_PATH", "") or os.environ.get("FINETUNED_MODEL_PATH", "")
    use_finetuned = getattr(settings, "USE_FINETUNED_MODEL", False) or os.environ.get("USE_FINETUNED_MODEL", "").lower() == "true"

    if finetuned_path and use_finetuned and os.path.exists(finetuned_path):
        try:
            from langchain_community.llms import HuggingFacePipeline
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            logger.info(f"LLM: Loading fine-tuned Hazeon model from {finetuned_path}")
            tokenizer = AutoTokenizer.from_pretrained(finetuned_path)
            model = AutoModelForCausalLM.from_pretrained(
                finetuned_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
            )
            pipe = pipeline(
                "text-generation", model=model, tokenizer=tokenizer,
                max_new_tokens=2048, temperature=0.1, do_sample=False,
            )
            _llm = HuggingFacePipeline(pipeline=pipe)
            logger.info("LLM: Using fine-tuned Hazeon UPSC evaluator ✅")
            return _llm
        except Exception as e:
            logger.warning(f"Fine-tuned model load failed: {e} — falling back to API")

    # 1. Groq — fast, free tier, llama-3.3-70b
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            _llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=settings.GROQ_API_KEY,
                temperature=0.1,
                max_tokens=4096,
                request_timeout=25,  # fail fast, don't hang — triggers mock fallback
            )
            logger.info("LLM: Using Groq (llama-3.3-70b-versatile)")
            return _llm
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    # 2. Gemini fallback
    gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=gemini_key,
                temperature=0.3,
                request_timeout=25,
            )
            logger.info("LLM: Using Gemini (gemini-2.0-flash)")
            return _llm
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    logger.warning("No LLM configured — using smart mock evaluation.")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH STATE
# ══════════════════════════════════════════════════════════════════════════════
class EvaluationState(TypedDict):
    # Inputs
    ocr_text: str
    question_text: str
    question_subject: str
    question_marks: int
    question_word_limit: int
    model_answer_points: Optional[List[str]]

    # Intermediate
    text_structure: Optional[dict]
    word_count: int
    has_introduction: bool
    has_conclusion: bool
    has_diagrams: bool
    detected_language: str
    topper_examples: Optional[List[str]]

    # Scores (0-10)
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
    overall_score: float

    # Feedback
    feedback_summary: str
    strengths: List[str]
    weaknesses: List[str]
    improvements: List[str]
    model_answer: str
    keywords_found: List[str]
    keywords_missed: List[str]
    topper_benchmark: str
    dimension_analysis: dict
    marks_obtained: float


# ══════════════════════════════════════════════════════════════════════════════
# NODE 1: TEXT STRUCTURE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
def analyze_text(state: EvaluationState) -> dict:
    """Node 1: Analyze text structure."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    llm = get_llm()
    text = state["ocr_text"]
    word_count = len(text.split())

    if llm:
        try:
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert UPSC/HCS answer evaluator. Analyze the student answer and extract structural metadata.

Return a JSON object with:
- has_introduction: boolean
- has_conclusion: boolean
- has_diagrams: boolean
- detected_language: "english" | "hindi" | "mixed"
- covered_dimensions: list of dimensions covered (political, economic, social, environmental, ethical, legal)
- structure_quality: "poor" | "average" | "good" | "excellent"
- analytical_depth: "descriptive" | "moderate_analysis" | "deep_analysis"
"""),
                ("human", "Question: {question}\nSubject: {subject}\n\nStudent Answer:\n{answer}\n\nReturn ONLY valid JSON.")
            ])
            chain = analysis_prompt | llm | JsonOutputParser()
            result = chain.invoke({
                "question": state["question_text"],
                "subject": state["question_subject"],
                "answer": text[:3000],  # cap to avoid token overflow
            })
            return {
                "text_structure": result,
                "word_count": word_count,
                "has_introduction": result.get("has_introduction", False),
                "has_conclusion": result.get("has_conclusion", False),
                "has_diagrams": result.get("has_diagrams", False),
                "detected_language": result.get("detected_language", "english"),
            }
        except Exception as e:
            logger.warning(f"Text analysis LLM call failed: {e}")

    # Heuristic fallback
    tl = text.lower()
    return {
        "text_structure": {},
        "word_count": word_count,
        "has_introduction": any(kw in tl[:200] for kw in [
            "introduction", "the concept", "in the context", "refers to", "is defined"
        ]),
        "has_conclusion": any(kw in tl[-300:] for kw in [
            "conclusion", "way forward", "thus,", "therefore,", "to conclude", "hence,"
        ]),
        "has_diagrams": any(kw in tl for kw in ["diagram", "flowchart", "figure", "chart"]),
        "detected_language": "english",
    }


# ══════════════════════════════════════════════════════════════════════════════
# NODE 2: RAG — RETRIEVE TOPPER EXAMPLES
# ══════════════════════════════════════════════════════════════════════════════
def retrieve_topper_examples(state: EvaluationState) -> dict:
    """Node 2: Retrieve similar topper answers from ChromaDB."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection(
            name="topper_answers",
            metadata={"hnsw:space": "cosine"}
        )
        if collection.count() > 0:
            results = collection.query(
                query_texts=[state["question_text"]],
                n_results=3,
            )
            if results and results["documents"]:
                return {"topper_examples": results["documents"][0]}
    except Exception as e:
        logger.warning(f"ChromaDB retrieval failed: {e}")

    return {"topper_examples": []}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 3: LLM EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
def evaluate_with_llm(state: EvaluationState) -> dict:
    """Node 3: Core LLM evaluation."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    llm = get_llm()

    topper_context = ""
    if state.get("topper_examples"):
        topper_context = "TOPPER REFERENCE ANSWERS (use for benchmarking):\n"
        for i, ex in enumerate(state["topper_examples"][:2], 1):
            topper_context += f"\n--- Topper Answer {i} ---\n{ex[:500]}\n"

    model_answer_context = ""
    if state.get("model_answer_points"):
        model_answer_context = "MODEL ANSWER KEY POINTS:\n" + "\n".join(
            f"- {p}" for p in state["model_answer_points"]
        )

    if llm:
        try:
            evaluation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a senior UPSC/HCS Mains answer evaluator with 20+ years of experience.

CRITICAL — ANTI-HALLUCINATION RULES (follow strictly):
1. Base evaluation ONLY on the topper reference answer provided below — do NOT add external facts
2. keywords_found must contain ONLY terms that literally appear in the student answer
3. keywords_missed must reference ONLY keywords present in the topper reference
4. Scores must reflect ACTUAL content in the student answer — do not inflate or deflate arbitrarily
5. strengths must cite specific phrases from the student answer
6. topper_benchmark must compare against the PROVIDED topper reference, not general knowledge
7. Return ONLY valid JSON — no markdown fences, no text before or after

SCORING RUBRIC — score each 0-10:
1. relevance_score: Does the answer address the specific question demand?
2. intro_score: Introduction quality — defines terms, sets context
3. body_score: Multi-dimensional coverage (political/economic/social/environmental/ethical)
4. keyword_score: Density of subject-specific terms from the topper reference
5. structure_score: Headings, bullet points, logical flow
6. factual_score: Accuracy of facts vs topper reference; penalise invented data
7. conclusion_score: Quality of Way Forward — concrete, forward-looking
8. word_limit_score: Adherence to word limit ({word_limit} words; student wrote {word_count})
9. analysis_score: Depth of analysis vs mere description
10. diagram_score: Use of diagrams/flowcharts (0 if not attempted)
11. multidimensional_score: Coverage across multiple dimensions

{topper_context}
{model_answer_context}

Return JSON with ALL these fields:
relevance_score, intro_score, body_score, keyword_score, structure_score,
factual_score, conclusion_score, word_limit_score, analysis_score,
diagram_score, multidimensional_score (floats 0-10),
overall_score (weighted average 0-10), marks_obtained (float out of {total_marks}),
feedback_summary (2-3 sentences), strengths (list 3-5), weaknesses (list 3-5),
improvements (list 4-6), model_answer (ideal outline 150-200 words),
keywords_found (list — ONLY from student answer), keywords_missed (list — ONLY from topper reference),
topper_benchmark (2-3 sentences comparing to PROVIDED reference),
dimension_analysis (object: political/economic/social/environmental/ethical/legal as booleans)"""),
                ("human", """Question ({subject}, {marks} marks, {word_limit} word limit):
{question}

Student's Answer ({word_count} words):
{answer}

Return ONLY valid JSON.""")
            ])
            chain = evaluation_prompt | llm | JsonOutputParser()
            result = chain.invoke({
                "question": state["question_text"],
                "subject": state["question_subject"],
                "marks": state["question_marks"],
                "word_limit": state["question_word_limit"],
                "word_count": state["word_count"],
                "answer": state["ocr_text"][:4000],
                "topper_context": topper_context,
                "model_answer_context": model_answer_context,
                "total_marks": state["question_marks"],
            })
            parsed = _parse_llm_result(result, state)
            logger.info(f"LLM evaluation complete — overall: {parsed['overall_score']}/10")
            return parsed
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")

    return _generate_smart_mock_evaluation(state)


def _parse_llm_result(result: dict, state: EvaluationState) -> dict:
    def _f(key, default=5.0):
        try:
            return min(max(float(result.get(key, default)), 0.0), 10.0)
        except (TypeError, ValueError):
            return default

    return {
        "relevance_score": _f("relevance_score"),
        "intro_score": _f("intro_score"),
        "body_score": _f("body_score"),
        "keyword_score": _f("keyword_score"),
        "structure_score": _f("structure_score"),
        "factual_score": _f("factual_score"),
        "conclusion_score": _f("conclusion_score"),
        "word_limit_score": _f("word_limit_score"),
        "analysis_score": _f("analysis_score"),
        "diagram_score": _f("diagram_score", 0.0),
        "multidimensional_score": _f("multidimensional_score"),
        "overall_score": _f("overall_score"),
        "marks_obtained": _f("marks_obtained", 0.0),
        "feedback_summary": result.get("feedback_summary", ""),
        "strengths": result.get("strengths", []),
        "weaknesses": result.get("weaknesses", []),
        "improvements": result.get("improvements", []),
        "model_answer": result.get("model_answer", ""),
        "keywords_found": result.get("keywords_found", []),
        "keywords_missed": result.get("keywords_missed", []),
        "topper_benchmark": result.get("topper_benchmark", ""),
        "dimension_analysis": result.get("dimension_analysis", {}),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SMART MOCK EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
HCS_KEYWORDS = {
    "governance": ["transparency", "accountability", "e-governance", "SARAL", "decentralization",
                   "RTI", "citizen charter", "PRIs", "CM Window", "digital", "reforms"],
    "economy": ["GDP", "agriculture", "industrial", "MSMEs", "fiscal", "GST", "FDI",
                "employment", "infrastructure", "HSIIDC", "green revolution"],
    "society": ["sex ratio", "education", "health", "caste", "women empowerment", "Beti Bachao",
                "poverty", "HDI", "literacy"],
    "polity": ["federalism", "constitution", "fundamental rights", "DPSP", "amendment",
               "judiciary", "parliament", "Article", "legislature"],
    "environment": ["climate change", "pollution", "biodiversity", "sustainable", "renewable",
                    "water table", "stubble burning", "NGT", "EIA"],
    "ethics": ["integrity", "impartiality", "empathy", "moral", "conflict of interest",
               "accountability", "public service", "values"],
}

MODEL_ANSWERS = {
    "governance": "An ideal governance answer should: (1) Define governance pillars — transparency, accountability, participation; (2) Cite Haryana-specific initiatives like SARAL, CM Window with outcomes; (3) Cover administrative, financial, social, judicial dimensions; (4) Include ARC recommendations; (5) End with actionable Way Forward.",
    "economy": "An ideal economy answer should: (1) Provide macro data — GDP, growth rates; (2) Cover primary/secondary/tertiary sectors with Haryana examples; (3) Discuss successes and challenges; (4) Include government schemes; (5) End with evidence-based recommendations.",
    "society": "A strong social answer must: (1) Lead with NFHS/Census data; (2) Analyze root causes; (3) Critically evaluate government interventions; (4) Reference SC judgments/reports; (5) Propose a nuanced Way Forward.",
    "general": "A comprehensive answer should: (1) Open with definition or context; (2) Present arguments with evidence; (3) Show multi-dimensional analysis; (4) Cite constitutional provisions or reports; (5) Conclude with balanced, forward-looking perspective.",
}

TOPPER_BENCHMARKS = {
    "governance": "A topper would open with a crisp governance definition, immediately cite 2-3 Haryana-specific initiatives with outcomes data, use a structured framework with diagram, and end with a powerful Way Forward citing ARC recommendations.",
    "economy": "A topper would anchor their answer with latest economic data, use headings for each sector, include a comparative table, cite NITI Aayog/Economic Survey findings, and connect all sectors in an integrated development vision.",
    "society": "A topper would lead with NFHS-5/Census data, analyze through intersectional lens (gender×caste×geography), evaluate schemes against outcomes, cite SC judgments, and propose a phased implementation framework.",
    "general": "A topper would connect the topic to current affairs, cite constitutional provisions precisely (with Article numbers), use national and international examples, present counter-arguments fairly, and offer an original synthesis.",
}


def _generate_smart_mock_evaluation(state: EvaluationState) -> dict:
    text = state["ocr_text"].lower()
    word_count = state["word_count"]
    word_limit = state["question_word_limit"]
    subject = state.get("question_subject", "general").lower()

    category = "general"
    for cat in HCS_KEYWORDS:
        if cat in subject or any(kw in text for kw in HCS_KEYWORDS[cat][:4]):
            category = cat
            break

    cat_kws = HCS_KEYWORDS.get(category, list(HCS_KEYWORDS["governance"]))
    keywords_found = [kw for kw in cat_kws if kw in text]
    keywords_missed = [kw for kw in cat_kws if kw not in text]
    kw_ratio = len(keywords_found) / max(len(cat_kws), 1)

    # Word limit score
    deviation = abs(word_count - word_limit) / max(word_limit, 1)
    wl_score = round(max(9.5 - deviation * 10, 1.0), 1)

    has_bullets = any(c in text for c in ["•", "-", "1.", "2.", "key ", "challenges"])
    has_headings = any(h in text for h in ["introduction", "conclusion", "way forward"])
    struct_score = round(min(5.5 + (1.5 if has_bullets else 0) + (1.5 if has_headings else 0) + random.uniform(-0.3, 0.3), 10), 1)

    intro_score = round((random.uniform(7.0, 9.0) if state.get("has_introduction") else random.uniform(3.5, 5.5)), 1)
    conclusion_score = round((random.uniform(7.0, 9.0) if state.get("has_conclusion") else random.uniform(3.0, 5.0)), 1)
    keyword_score = round(min(4.0 + kw_ratio * 5.5, 10), 1)
    relevance_score = round(min(6.0 + kw_ratio * 3.0, 10), 1)
    body_score = round(min(5.5 + kw_ratio * 2.5 + (0.5 if word_count > 150 else 0), 10), 1)
    factual_score = round(min(5.0 + kw_ratio * 3.5, 10), 1)
    analysis_score = round(min(4.5 + kw_ratio * 2.5 + (1.0 if "however" in text or "although" in text else 0), 10), 1)
    diagram_score = round((random.uniform(6.0, 8.0) if state.get("has_diagrams") else random.uniform(1.0, 3.0)), 1)
    multi_score = round(min(5.0 + kw_ratio * 3.5, 10), 1)

    weights = {
        "relevance": (relevance_score, 0.15), "intro": (intro_score, 0.08),
        "body": (body_score, 0.15), "keyword": (keyword_score, 0.10),
        "structure": (struct_score, 0.10), "factual": (factual_score, 0.12),
        "conclusion": (conclusion_score, 0.08), "word_limit": (wl_score, 0.05),
        "analysis": (analysis_score, 0.10), "diagram": (diagram_score, 0.02),
        "multi": (multi_score, 0.05),
    }
    overall = sum(s * w for s, w in weights.values())
    overall = round(overall, 1)

    dimension_analysis = {
        "political": any(kw in text for kw in ["government", "policy", "political", "legislature"]),
        "economic": any(kw in text for kw in ["economic", "gdp", "fiscal", "industry", "agriculture"]),
        "social": any(kw in text for kw in ["social", "education", "health", "gender", "poverty"]),
        "environmental": any(kw in text for kw in ["environment", "climate", "pollution", "sustainable"]),
        "ethical": any(kw in text for kw in ["ethical", "moral", "integrity", "values"]),
        "legal": any(kw in text for kw in ["law", "act", "constitution", "article", "supreme court"]),
    }

    strengths, weaknesses, improvements = [], [], []
    if state.get("has_introduction"):
        strengths.append("Good introduction sets context effectively")
    else:
        weaknesses.append("Missing a proper introduction — define key terms and set context")
        improvements.append("Begin with 2-3 lines defining the core concept and its significance")

    if state.get("has_conclusion"):
        strengths.append("Conclusion/Way Forward demonstrates maturity of thought")
    else:
        weaknesses.append("No Way Forward — essential for scoring well in Mains")
        improvements.append("Always end with 3-4 concrete, actionable Way Forward recommendations")

    if kw_ratio > 0.5:
        strengths.append(f"Good keyword usage — {len(keywords_found)} relevant terms used")
    else:
        weaknesses.append(f"Low keyword density — only {len(keywords_found)}/{len(cat_kws)} expected terms")
        improvements.append(f"Include key terms: {', '.join(keywords_missed[:5])}")

    covered = sum(1 for v in dimension_analysis.values() if v)
    if covered >= 4:
        strengths.append(f"Multi-dimensional analysis covering {covered}/6 dimensions")
    else:
        missing_dims = [k for k, v in dimension_analysis.items() if not v]
        improvements.append(f"Add {', '.join(missing_dims[:2])} dimensions to strengthen the answer")

    improvements.append("Add 2-3 specific data points or case studies to strengthen arguments")
    improvements.append("Consider a diagram or flowchart to visually represent key relationships")

    return {
        "relevance_score": relevance_score,
        "intro_score": intro_score,
        "body_score": body_score,
        "keyword_score": keyword_score,
        "structure_score": struct_score,
        "factual_score": factual_score,
        "conclusion_score": conclusion_score,
        "word_limit_score": wl_score,
        "analysis_score": analysis_score,
        "diagram_score": diagram_score,
        "multidimensional_score": multi_score,
        "overall_score": overall,
        "marks_obtained": round(overall / 10 * state["question_marks"], 1),
        "feedback_summary": f"The answer shows {'strong' if overall > 7 else 'good' if overall > 5.5 else 'basic'} understanding with {'rich' if kw_ratio > 0.5 else 'limited'} subject-specific terminology. {'Well-structured with clear sections.' if has_headings else 'Could benefit from clearer structure with headings.'} Overall: {overall}/10.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
        "model_answer": MODEL_ANSWERS.get(category, MODEL_ANSWERS["general"]),
        "keywords_found": keywords_found[:10],
        "keywords_missed": keywords_missed[:8],
        "topper_benchmark": TOPPER_BENCHMARKS.get(category, TOPPER_BENCHMARKS["general"]),
        "dimension_analysis": dimension_analysis,
    }


# ══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH WORKFLOW
# ══════════════════════════════════════════════════════════════════════════════
def build_evaluation_graph():
    from langgraph.graph import StateGraph, END, START
    workflow = StateGraph(EvaluationState)
    workflow.add_node("analyze_text", analyze_text)
    workflow.add_node("retrieve_topper_examples", retrieve_topper_examples)
    workflow.add_node("evaluate_with_llm", evaluate_with_llm)
    workflow.add_edge(START, "analyze_text")
    workflow.add_edge("analyze_text", "retrieve_topper_examples")
    workflow.add_edge("retrieve_topper_examples", "evaluate_with_llm")
    workflow.add_edge("evaluate_with_llm", END)
    return workflow.compile()


_evaluation_pipeline = None


def _get_pipeline():
    global _evaluation_pipeline
    if _evaluation_pipeline is None:
        _evaluation_pipeline = build_evaluation_graph()
    return _evaluation_pipeline


def run_evaluation(
    ocr_text: str,
    question_text: str,
    question_subject: str = "General Studies",
    question_marks: int = 15,
    question_word_limit: int = 250,
    model_answer_points: Optional[List[str]] = None,
) -> dict:
    """Run the full LangGraph evaluation pipeline."""
    initial_state: EvaluationState = {
        "ocr_text": ocr_text,
        "question_text": question_text,
        "question_subject": question_subject,
        "question_marks": question_marks,
        "question_word_limit": question_word_limit,
        "model_answer_points": model_answer_points or [],
        "text_structure": None,
        "word_count": len(ocr_text.split()),
        "has_introduction": False,
        "has_conclusion": False,
        "has_diagrams": False,
        "detected_language": "english",
        "topper_examples": [],
        "relevance_score": 0.0, "intro_score": 0.0, "body_score": 0.0,
        "keyword_score": 0.0, "structure_score": 0.0, "factual_score": 0.0,
        "conclusion_score": 0.0, "word_limit_score": 0.0, "analysis_score": 0.0,
        "diagram_score": 0.0, "multidimensional_score": 0.0, "overall_score": 0.0,
        "feedback_summary": "", "strengths": [], "weaknesses": [], "improvements": [],
        "model_answer": "", "keywords_found": [], "keywords_missed": [],
        "topper_benchmark": "", "dimension_analysis": {}, "marks_obtained": 0.0,
    }
    return _get_pipeline().invoke(initial_state)
