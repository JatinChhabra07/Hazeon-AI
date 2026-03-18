"""
Topper Answer Scraper Service — Hazeon AI

Scrapes publicly available UPSC/HCS model answers and topper answer summaries
from InsightsIAS, DrishtiIAS, CivilsDaily, Mrunal, and structured UPSC archives.

Pipeline:
  1. Fetch HTML from public model-answer pages (respectful rate-limited crawl)
  2. Parse & clean text with BeautifulSoup
  3. Structure into TopperAnswerRecord objects
  4. Caller stores to SQLite + ChromaDB via populate_topper_db.py
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TopperAnswerRecord:
    question_text: str
    answer_text: str
    subject: str           # GS1, GS2, GS3, GS4, Essay
    topic: str
    year: int
    exam_type: str         # UPSC, HCS
    source: str
    score: Optional[float] = None
    rank: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    marks: int = 15
    word_limit: int = 250


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE CONFIGS
# Each entry: (url, subject, topic, year, marks)
# ══════════════════════════════════════════════════════════════════════════════

# ── InsightsIAS ── Real topper answer copies + model answers
INSIGHTS_TOPPER_URLS = [
    "https://www.insightsonindia.com/upsc-toppers-answer-copies-download-ias-topper-mains-copies-by-insightsonindia/",
    "https://www.insightsonindia.com/category/toppers-answer-scripts/",
    "https://www.insightsonindia.com/category/upsc-mains-model-answers/",
    "https://www.insightsonindia.com/category/upsc-mains-model-answers/gs-1-model-answers/",
    "https://www.insightsonindia.com/category/upsc-mains-model-answers/gs-2-model-answers/",
    "https://www.insightsonindia.com/category/upsc-mains-model-answers/gs-3-model-answers/",
    "https://www.insightsonindia.com/category/upsc-mains-model-answers/gs-4-model-answers/",
]
INSIGHTS_MODEL_ANSWER_URLS = INSIGHTS_TOPPER_URLS  # backward compat

# ── DrishtiIAS ── Free topper copies + model answers
DRISHTI_MODEL_ANSWER_URLS = [
    "https://www.drishtiias.com/free-downloads/toppers-copy/",
    "https://www.drishtiias.com/free-downloads/toppers-copy-ravi-raj",
    "https://www.drishtiias.com/mains-practice-question",
]

# ── ForumIAS ── Rank 1-50 topper pages (each has answer copy PDFs)
FORUMIAS_TOPPER_BASE = "https://forumias.com/blog/testimonials/"
FORUMIAS_KNOWN_TOPPERS = [
    # 2024 toppers
    "https://forumias.com/blog/komal-punia-upsc-ias-2024-topper-air-6-biography-state-marksheet-and-answer-copy/",
    "https://forumias.com/blog/saumya-mishra-upsc-ias-2024-topper-air-18-biography-state-marksheet-and-answer-copy/",
    # 2022 toppers
    "https://forumias.com/blog/ishita-kishore-ias-topper-rank-1-upsc-cse-2022-mgp-test-copies/",
]
FORUMIAS_URLS = [FORUMIAS_TOPPER_BASE] + FORUMIAS_KNOWN_TOPPERS

# ── GS Score / IASScore ── Year-wise topper copies (2015–2024)
GSSCORE_TOPPER_URLS = [
    f"https://iasscore.in/toppers-copy/{year}" for year in range(2015, 2025)
]

# ── CivilsDaily ── Post-mains model solutions
CIVILSDAILY_URLS = [
    "https://www.civilsdaily.com/upsc-mains-2024-gs-model-solutions-gs1-gs2-gs3-gs4/",
    "https://www.civilsdaily.com/upsc-2024-gs1-model-answers/",
    "https://www.civilsdaily.com/upsc-2024-gs2-model-answers/",
    "https://www.civilsdaily.com/upsc-2024-gs3-model-answers/",
    "https://www.civilsdaily.com/mains-model-answers/",
]

# ── Mrunal ── Topicwise compilations + model answers
MRUNAL_URLS = [
    "https://mrunal.org/mains",
    "https://mrunal.org/category/mains-answer-writing",
]

# ── VisionIAS ── Topper answer copy viewer
VISIONIAS_URLS = [
    "https://www.visionias.in/resources/toppers-answer-copy/",
]

# ── Vajiramandravi ── Model answers
VAJIRA_URLS = [
    "https://vajiramandravi.com/upsc-exam/model-answers-for-upsc-mains/",
]

# ── UPSC Official ── Question papers (1995–2024)
UPSC_OFFICIAL_QP = "https://upsc.gov.in/examinations/previous-question-papers"

# ── HPSC Official ── HCS Haryana question papers
HPSC_OFFICIAL_QP = "https://hpsc.gov.in/en-us/Previous-Question-Papers"


# ══════════════════════════════════════════════════════════════════════════════
# HTTP HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Synchronous HTTP fetch with a browser-like UA. Returns HTML or None."""
    try:
        import httpx
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"HTTP {resp.status_code} for {url}")
    except Exception as e:
        logger.warning(f"Fetch failed {url}: {e}")
    return None


def _clean_text(raw: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"&nbsp;", " ", raw)
    raw = re.sub(r"&amp;", "&", raw)
    raw = re.sub(r"&lt;", "<", raw)
    raw = re.sub(r"&gt;", ">", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def _parse_article_text(html: str) -> str:
    """Extract main article body text from HTML using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Remove nav, footer, sidebar, ads
        for tag in soup.find_all(["nav", "footer", "aside", "script", "style",
                                   "header", "form", "iframe"]):
            tag.decompose()

        # Try common article containers
        for selector in [
            "article .entry-content",
            "article",
            ".post-content",
            ".entry-content",
            ".content-body",
            "main",
        ]:
            el = soup.select_one(selector)
            if el:
                return _clean_text(el.get_text(separator=" "))

        return _clean_text(soup.get_text(separator=" "))
    except ImportError:
        return _clean_text(html)


def _extract_question_answer_pairs(text: str) -> List[dict]:
    """
    Try to split text that contains Q&A patterns into discrete pairs.
    Returns list of {question, answer} dicts.
    """
    pairs = []

    # Pattern: lines starting with "Q." or "Question:" followed by answer
    q_pattern = re.compile(
        r"(?:^|\n)\s*(?:Q\.?\s*\d*\.?|Question\s*\d*\.?|Ques\.?\s*\d*\.?)\s*(.+?)(?=\n\s*(?:Ans|Answer|Sol|Solution|A\.)\s*[:.]?\s*)",
        re.IGNORECASE | re.DOTALL,
    )
    a_pattern = re.compile(
        r"(?:Ans|Answer|Sol|Solution|A\.)\s*[:.]?\s*(.+?)(?=\n\s*(?:Q\.?\s*\d+|Question\s*\d+)|$)",
        re.IGNORECASE | re.DOTALL,
    )

    questions = q_pattern.findall(text)
    answers = a_pattern.findall(text)

    for q, a in zip(questions, answers):
        q_clean = q.strip()
        a_clean = a.strip()
        if len(q_clean) > 20 and len(a_clean) > 50:
            pairs.append({"question": q_clean, "answer": a_clean})

    return pairs


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER: InsightsIAS
# ══════════════════════════════════════════════════════════════════════════════

def scrape_insights_ias(max_pages: int = 5) -> List[TopperAnswerRecord]:
    """
    Scrape model answers from InsightsIAS category pages.
    Follows article links and extracts Q&A pairs.
    """
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return records

    subject_map = {
        "gs-1": "GS1 - History & Society",
        "gs-2": "GS2 - Governance & IR",
        "gs-3": "GS3 - Economy & Environment",
        "gs-4": "GS4 - Ethics",
        "essay": "Essay",
    }

    for base_url in INSIGHTS_MODEL_ANSWER_URLS:
        subject = "GS - General Studies"
        for key, val in subject_map.items():
            if key in base_url:
                subject = val
                break

        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}page/{page}/"
            html = _fetch_url(url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            article_links = []

            # Collect article URLs from listing page
            for a_tag in soup.select("h2.entry-title a, h3.entry-title a, .post-title a"):
                href = a_tag.get("href", "")
                if href and "insightsonindia.com" in href:
                    article_links.append(href)

            logger.info(f"InsightsIAS: found {len(article_links)} articles on {url}")

            for article_url in article_links[:10]:  # max 10 per page
                time.sleep(1.5)  # polite crawl delay
                art_html = _fetch_url(article_url)
                if not art_html:
                    continue

                art_text = _parse_article_text(art_html)
                pairs = _extract_question_answer_pairs(art_text)

                # Extract year from URL or text
                year_match = re.search(r"20(\d{2})", article_url)
                year = int(f"20{year_match.group(1)}") if year_match else 2023

                if pairs:
                    for pair in pairs:
                        rec = TopperAnswerRecord(
                            question_text=pair["question"][:500],
                            answer_text=pair["answer"][:3000],
                            subject=subject,
                            topic=_infer_topic(pair["question"]),
                            year=year,
                            exam_type="UPSC",
                            source="InsightsIAS",
                            score=8.5,
                            tags=["model_answer", "insightsias", subject.lower()],
                        )
                        records.append(rec)
                else:
                    # Store the full article as a model answer context
                    title_match = re.search(r"<title>([^<]+)</title>", art_html)
                    title = title_match.group(1) if title_match else "UPSC Model Answer"
                    if len(art_text) > 200:
                        rec = TopperAnswerRecord(
                            question_text=title[:500],
                            answer_text=art_text[:3000],
                            subject=subject,
                            topic=_infer_topic(title),
                            year=year,
                            exam_type="UPSC",
                            source="InsightsIAS",
                            score=8.0,
                            tags=["model_answer", "insightsias"],
                        )
                        records.append(rec)

            time.sleep(2)  # between pages

    logger.info(f"InsightsIAS scrape complete: {len(records)} records")
    return records


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER: GS Score / IASScore — Year-wise topper copies 2015-2024
# ══════════════════════════════════════════════════════════════════════════════

def scrape_gsscore(years: list = None) -> List[TopperAnswerRecord]:
    """
    Scrape iasscore.in/toppers-copy/[YEAR] pages for topper answer text.
    These pages have scanned copy sections + some HTML text content.
    """
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return records

    if years is None:
        years = list(range(2018, 2025))

    for year in years:
        url = f"https://iasscore.in/toppers-copy/{year}"
        html = _fetch_url(url)
        if not html:
            time.sleep(1)
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Extract topper profiles and their text content
        for section in soup.select(".topper-section, .answer-section, article, .post"):
            text = _clean_text(section.get_text(separator=" "))
            if len(text) < 100:
                continue

            # Try to find associated question
            pairs = _extract_question_answer_pairs(text)
            if pairs:
                for pair in pairs:
                    subject = _infer_subject(pair["question"])
                    rec = TopperAnswerRecord(
                        question_text=pair["question"][:500],
                        answer_text=pair["answer"][:3000],
                        subject=subject,
                        topic=_infer_topic(pair["question"]),
                        year=year,
                        exam_type="UPSC",
                        source="GSScore",
                        score=8.5,
                        tags=["topper_copy", "gsscore", str(year)],
                    )
                    records.append(rec)
            elif len(text) > 200:
                # Store as context block
                rec = TopperAnswerRecord(
                    question_text=f"UPSC Mains {year} — Topper Answer",
                    answer_text=text[:3000],
                    subject=_infer_subject(text),
                    topic=_infer_topic(text),
                    year=year,
                    exam_type="UPSC",
                    source="GSScore",
                    score=8.0,
                    tags=["topper_copy", "gsscore", str(year)],
                )
                records.append(rec)

        # Also collect links to individual topper pages
        topper_links = [
            a["href"] for a in soup.select("a[href*='topper'], a[href*='copy']")
            if "iasscore.in" in a.get("href", "") or a["href"].startswith("/")
        ]
        for link in list(set(topper_links))[:5]:
            if link.startswith("/"):
                link = "https://iasscore.in" + link
            time.sleep(1)
            sub_html = _fetch_url(link)
            if sub_html:
                sub_text = _parse_article_text(sub_html)
                for pair in _extract_question_answer_pairs(sub_text):
                    subject = _infer_subject(pair["question"])
                    rec = TopperAnswerRecord(
                        question_text=pair["question"][:500],
                        answer_text=pair["answer"][:3000],
                        subject=subject,
                        topic=_infer_topic(pair["question"]),
                        year=year,
                        exam_type="UPSC",
                        source="GSScore",
                        score=8.5,
                        tags=["topper_copy", "gsscore", str(year)],
                    )
                    records.append(rec)

        time.sleep(2)

    logger.info(f"GSScore scrape complete: {len(records)} records")
    return records


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER: ForumIAS — Rank 1-50 toppers with individual answer pages
# ══════════════════════════════════════════════════════════════════════════════

def scrape_forumias() -> List[TopperAnswerRecord]:
    """
    Scrape ForumIAS testimonials/topper pages.
    Each topper page links to their GS + Essay answer PDFs (often embedded or linked).
    """
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return records

    # Scrape main testimonials index for all topper links
    html = _fetch_url(FORUMIAS_TOPPER_BASE)
    topper_page_links = list(FORUMIAS_KNOWN_TOPPERS)  # start with known ones

    if html:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href*='topper'], a[href*='air-'], a[href*='rank-']"):
            href = a.get("href", "")
            if "forumias.com/blog/" in href and href not in topper_page_links:
                topper_page_links.append(href)

    logger.info(f"ForumIAS: found {len(topper_page_links)} topper pages to process")

    for page_url in topper_page_links[:20]:  # cap at 20
        time.sleep(1.5)
        html = _fetch_url(page_url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        art_text = _parse_article_text(html)

        # Extract year and rank from URL/title
        year_match = re.search(r"20(\d{2})", page_url)
        year = int(f"20{year_match.group(1)}") if year_match else 2023
        rank_match = re.search(r"air[-_](\d+)|rank[-_](\d+)", page_url, re.I)
        rank = int(rank_match.group(1) or rank_match.group(2)) if rank_match else None

        # Extract Q&A pairs
        pairs = _extract_question_answer_pairs(art_text)
        if pairs:
            for pair in pairs:
                subject = _infer_subject(pair["question"])
                rec = TopperAnswerRecord(
                    question_text=pair["question"][:500],
                    answer_text=pair["answer"][:3000],
                    subject=subject,
                    topic=_infer_topic(pair["question"]),
                    year=year,
                    exam_type="UPSC",
                    source="ForumIAS",
                    score=9.0 if rank and rank <= 10 else 8.5,
                    rank=rank,
                    tags=["topper_copy", "forumias", f"rank_{rank}" if rank else "topper"],
                )
                records.append(rec)
        elif len(art_text) > 300:
            # Store full page as context
            rec = TopperAnswerRecord(
                question_text=f"UPSC {year} Topper Answer" + (f" (Rank {rank})" if rank else ""),
                answer_text=art_text[:3000],
                subject="GS - General Studies",
                topic="General",
                year=year,
                exam_type="UPSC",
                source="ForumIAS",
                score=9.0 if rank and rank <= 10 else 8.5,
                rank=rank,
                tags=["topper_copy", "forumias"],
            )
            records.append(rec)

    logger.info(f"ForumIAS scrape complete: {len(records)} records")
    return records


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER: CivilsDaily — Detailed post-mains model solutions
# ══════════════════════════════════════════════════════════════════════════════

def scrape_civilsdaily(max_urls: int = 10) -> List[TopperAnswerRecord]:
    """Scrape CivilsDaily model answer pages (post-Mains solutions)."""
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return records

    all_urls = list(CIVILSDAILY_URLS)

    # Also discover more pages from the listing
    listing_html = _fetch_url("https://www.civilsdaily.com/mains-model-answers/")
    if listing_html:
        soup = BeautifulSoup(listing_html, "html.parser")
        for a in soup.select("a[href*='model-answer'], a[href*='mains-2']"):
            href = a.get("href", "")
            if "civilsdaily.com" in href and href not in all_urls:
                all_urls.append(href)

    for url in all_urls[:max_urls]:
        time.sleep(1.5)
        html = _fetch_url(url)
        if not html:
            continue

        art_text = _parse_article_text(html)
        year_match = re.search(r"20(\d{2})", url)
        year = int(f"20{year_match.group(1)}") if year_match else 2024

        # Determine subject from URL
        subject = "GS - General Studies"
        if "gs1" in url.lower():
            subject = "GS1 - History & Society"
        elif "gs2" in url.lower():
            subject = "GS2 - Governance & IR"
        elif "gs3" in url.lower():
            subject = "GS3 - Economy & Environment"
        elif "gs4" in url.lower():
            subject = "GS4 - Ethics"

        pairs = _extract_question_answer_pairs(art_text)
        if pairs:
            for pair in pairs:
                if len(pair["answer"]) > 100:
                    rec = TopperAnswerRecord(
                        question_text=pair["question"][:500],
                        answer_text=pair["answer"][:3000],
                        subject=subject if subject != "GS - General Studies" else _infer_subject(pair["question"]),
                        topic=_infer_topic(pair["question"]),
                        year=year,
                        exam_type="UPSC",
                        source="CivilsDaily",
                        score=8.5,
                        tags=["model_answer", "civilsdaily", str(year)],
                    )
                    records.append(rec)
        elif len(art_text) > 200:
            rec = TopperAnswerRecord(
                question_text=f"UPSC Mains {year} — {subject}",
                answer_text=art_text[:3000],
                subject=subject,
                topic="General",
                year=year,
                exam_type="UPSC",
                source="CivilsDaily",
                score=8.0,
                tags=["model_answer", "civilsdaily"],
            )
            records.append(rec)

    logger.info(f"CivilsDaily scrape complete: {len(records)} records")
    return records


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER: Mrunal — Topicwise compilations + model answers
# ══════════════════════════════════════════════════════════════════════════════

def scrape_mrunal(max_pages: int = 3) -> List[TopperAnswerRecord]:
    """Scrape Mrunal.org mains model answers (2011–2024)."""
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return records

    for base_url in MRUNAL_URLS:
        for page in range(1, max_pages + 1):
            url = f"{base_url}/page/{page}" if page > 1 else base_url
            html = _fetch_url(url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            article_links = [
                a["href"] for a in soup.select("h2 a, h3 a, .entry-title a")
                if a.get("href") and "mrunal.org" in a.get("href", "")
            ]

            for link in article_links[:8]:
                time.sleep(1.5)
                art_html = _fetch_url(link)
                if not art_html:
                    continue

                art_text = _parse_article_text(art_html)
                year_match = re.search(r"20(\d{2})", link)
                year = int(f"20{year_match.group(1)}") if year_match else 2023

                pairs = _extract_question_answer_pairs(art_text)
                for pair in pairs:
                    if len(pair["answer"]) > 100:
                        rec = TopperAnswerRecord(
                            question_text=pair["question"][:500],
                            answer_text=pair["answer"][:3000],
                            subject=_infer_subject(pair["question"]),
                            topic=_infer_topic(pair["question"]),
                            year=year,
                            exam_type="UPSC",
                            source="Mrunal",
                            score=8.0,
                            tags=["model_answer", "mrunal", str(year)],
                        )
                        records.append(rec)

            time.sleep(2)

    logger.info(f"Mrunal scrape complete: {len(records)} records")
    return records


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER: DrishtiIAS
# ══════════════════════════════════════════════════════════════════════════════

def scrape_drishti_ias(max_pages: int = 3) -> List[TopperAnswerRecord]:
    """Scrape practice questions and model answers from DrishtiIAS."""
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 not installed.")
        return records

    for base_url in DRISHTI_MODEL_ANSWER_URLS:
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            html = _fetch_url(url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            article_links = [
                a["href"] for a in soup.select("a[href*='drishtiias.com']")
                if "mains" in a.get("href", "") or "question" in a.get("href", "")
            ]
            article_links = list(set(article_links))[:8]

            for link in article_links:
                time.sleep(1.5)
                art_html = _fetch_url(link)
                if not art_html:
                    continue

                art_text = _parse_article_text(art_html)
                pairs = _extract_question_answer_pairs(art_text)
                year_match = re.search(r"20(\d{2})", link)
                year = int(f"20{year_match.group(1)}") if year_match else 2023

                for pair in pairs:
                    subject = _infer_subject(pair["question"])
                    rec = TopperAnswerRecord(
                        question_text=pair["question"][:500],
                        answer_text=pair["answer"][:3000],
                        subject=subject,
                        topic=_infer_topic(pair["question"]),
                        year=year,
                        exam_type="UPSC",
                        source="DrishtiIAS",
                        score=8.5,
                        tags=["model_answer", "drishtiias"],
                    )
                    records.append(rec)

            time.sleep(2)

    logger.info(f"DrishtiIAS scrape complete: {len(records)} records")
    return records


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Infer topic/subject from question text
# ══════════════════════════════════════════════════════════════════════════════

TOPIC_KEYWORDS = {
    "Federalism": ["federalism", "centre-state", "state autonomy", "fiscal federalism", "cooperative federalism"],
    "Good Governance": ["governance", "e-governance", "transparency", "accountability", "saral", "cm window"],
    "Agriculture": ["agriculture", "green revolution", "msp", "farmer", "crop", "irrigation", "food security"],
    "Environment": ["environment", "climate change", "biodiversity", "pollution", "carbon", "ngt", "forest"],
    "Gender Issues": ["women", "gender", "sex ratio", "beti bachao", "maternity", "violence against women"],
    "Economy": ["economy", "gdp", "growth", "inflation", "fiscal deficit", "monetary policy", "banking"],
    "Foreign Policy": ["foreign policy", "neighbourhood", "bilateral", "saarc", "indo-pacific", "china", "pakistan"],
    "Ethics": ["ethics", "integrity", "moral", "corruption", "conflict of interest", "civil servant"],
    "Polity": ["constitution", "fundamental rights", "dpsp", "parliament", "judiciary", "federalism", "article"],
    "Social Issues": ["poverty", "education", "health", "inequality", "caste", "reservation", "tribal"],
    "Science & Technology": ["technology", "ai", "space", "nuclear", "biotechnology", "digital india", "innovation"],
    "Disaster Management": ["disaster", "flood", "earthquake", "cyclone", "ndma", "resilience"],
    "Internal Security": ["terrorism", "naxalism", "insurgency", "border", "security", "extremism"],
    "History": ["ancient india", "medieval", "mughal", "british", "independence", "nationalist", "partition"],
    "Geography": ["geography", "river", "monsoon", "plateau", "coastal", "mineral", "drainage"],
    "Water Management": ["water", "groundwater", "irrigation", "syl canal", "river linking", "jal shakti"],
    "Urban Development": ["urban", "smart city", "slum", "housing", "metro", "infrastructure"],
    "Panchayati Raj": ["panchayat", "local governance", "73rd amendment", "gram sabha", "municipality"],
}

SUBJECT_KEYWORDS = {
    "GS1 - History & Society": ["history", "culture", "society", "geography", "ancient", "medieval", "women", "caste", "tribal", "art", "architecture"],
    "GS2 - Governance & IR": ["governance", "constitution", "polity", "parliament", "federalism", "foreign policy", "bilateral", "international", "rights", "judiciary"],
    "GS3 - Economy & Environment": ["economy", "agriculture", "industry", "technology", "environment", "biodiversity", "disaster", "security", "gdp", "fiscal"],
    "GS4 - Ethics": ["ethics", "integrity", "attitude", "moral", "civil servant", "corruption", "empathy", "values"],
    "Essay": ["essay"],
}


def _infer_topic(text: str) -> str:
    t = text.lower()
    for topic, kws in TOPIC_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return topic
    return "General"


def _infer_subject(text: str) -> str:
    t = text.lower()
    for subject, kws in SUBJECT_KEYWORDS.items():
        if sum(1 for kw in kws if kw in t) >= 2:
            return subject
    return "GS - General Studies"


# ══════════════════════════════════════════════════════════════════════════════
# LLM-BASED TOPPER ANSWER GENERATOR
# Generates high-quality "topper-style" answers for curated questions
# ══════════════════════════════════════════════════════════════════════════════

TOPPER_GENERATION_PROMPT = """You are a UPSC/HCS Mains topper who secured Rank 1-10. Generate a model answer for the following question that would score 13-15/15 marks.

QUESTION ({subject}, {marks} marks, {word_limit} word limit, {year} exam):
{question}

TOPPER ANSWER REQUIREMENTS:
- Start with a crisp 2-line introduction defining the core concept
- Use 3-4 clear headings with bullet points under each
- Cover ALL dimensions: political, economic, social, environmental, ethical, legal
- Include at least 3 specific data points, schemes, or committee names
- Mention constitutional articles / statutory provisions where relevant
- End with a forward-looking "Way Forward" section (3-4 concrete suggestions)
- Use UPSC examiner vocabulary: "multidimensional", "holistic", "paradigm shift"
- Length: exactly {word_limit} words (±10%)
- Do NOT use generic statements — every sentence must add value

Generate the complete answer text ONLY (no meta commentary)."""


# ══════════════════════════════════════════════════════════════════════════════
# PDF DOWNLOADER — fetch and OCR topper copy PDFs
# ══════════════════════════════════════════════════════════════════════════════

# Known IASbaba topper answer copy PDF pages
IASBABA_TOPPER_URLS = [
    "https://iasbaba.com/upsc-topper-answer-copies/",
    "https://iasbaba.com/upsc-mains-model-answers/",
    "https://iasbaba.com/category/mains-answer-writing/",
]

# Vision IAS topper answer copy pages
VISIONIAS_TOPPER_PDFS = [
    "https://www.visionias.in/resources/toppers-answer-copy/",
    "https://www.visionias.in/resources/mains-model-answers/",
]

# PYQ Answer writing resources
IASSCORE_ANSWERS = [
    f"https://iasscore.in/mains-answer-writing/{year}" for year in range(2018, 2025)
]

# Civilsdaily year-wise
CIVILSDAILY_YEAR_URLS = [
    f"https://www.civilsdaily.com/upsc-{year}-mains-model-answers/" for year in range(2015, 2025)
]


def download_and_ocr_pdf(pdf_url: str, save_dir: str = "/tmp/topper_pdfs") -> Optional[str]:
    """
    Download a PDF from url and extract text using pdfplumber or PyMuPDF.
    Returns extracted text or None on failure.
    """
    import os
    os.makedirs(save_dir, exist_ok=True)

    try:
        import httpx
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        resp = httpx.get(pdf_url, headers=headers, timeout=30, follow_redirects=True)
        if resp.status_code != 200:
            logger.warning(f"PDF download failed ({resp.status_code}): {pdf_url}")
            return None

        # Save PDF to temp file
        filename = pdf_url.split("/")[-1].split("?")[0]
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(resp.content)

        # Extract text
        return _extract_pdf_text(filepath)

    except Exception as e:
        logger.warning(f"PDF download/OCR failed for {pdf_url}: {e}")
        return None


def _extract_pdf_text(filepath: str) -> Optional[str]:
    """Extract text from PDF using pdfplumber (preferred) or PyMuPDF fallback."""
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")

    return None


def scrape_pdf_topper_copies(max_pdfs: int = 20) -> List[TopperAnswerRecord]:
    """
    Discover and process PDF topper copies from IASbaba and Vision IAS.
    Extracts text via pdfplumber/PyMuPDF, stores as TopperAnswerRecords.
    """
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return records

    all_sources = IASBABA_TOPPER_URLS + VISIONIAS_TOPPER_PDFS

    for source_url in all_sources:
        html = _fetch_url(source_url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        pdf_links = []

        # Find PDF download links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf") or "pdf" in href.lower():
                if href.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(source_url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                if href not in pdf_links:
                    pdf_links.append(href)

        logger.info(f"Found {len(pdf_links)} PDF links on {source_url}")

        for pdf_url in pdf_links[:max_pdfs]:
            time.sleep(2)
            text = download_and_ocr_pdf(pdf_url)
            if not text or len(text) < 200:
                continue

            year_match = re.search(r"20(\d{2})", pdf_url)
            year = int(f"20{year_match.group(1)}") if year_match else 2023
            subject = _infer_subject(text)

            pairs = _extract_question_answer_pairs(text)
            if pairs:
                for pair in pairs:
                    rec = TopperAnswerRecord(
                        question_text=pair["question"][:500],
                        answer_text=pair["answer"][:3000],
                        subject=subject,
                        topic=_infer_topic(pair["question"]),
                        year=year,
                        exam_type="UPSC",
                        source="PDF_Topper_Copy",
                        score=8.5,
                        tags=["topper_copy", "pdf", str(year)],
                    )
                    records.append(rec)
            else:
                # Store full text as single record
                rec = TopperAnswerRecord(
                    question_text=f"UPSC {year} Topper Answer Copy",
                    answer_text=text[:3000],
                    subject=subject,
                    topic=_infer_topic(text),
                    year=year,
                    exam_type="UPSC",
                    source="PDF_Topper_Copy",
                    score=8.0,
                    tags=["topper_copy", "pdf", str(year)],
                )
                records.append(rec)

    logger.info(f"PDF scrape complete: {len(records)} records")
    return records


# ── IASbaba text-based scraper ─────────────────────────────────────────────────

def scrape_iasbaba(max_pages: int = 3) -> List[TopperAnswerRecord]:
    """Scrape IASbaba model answers and answer writing content."""
    records = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return records

    for base_url in IASBABA_TOPPER_URLS:
        for page in range(1, max_pages + 1):
            url = f"{base_url}page/{page}/" if page > 1 else base_url
            html = _fetch_url(url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            article_links = [
                a["href"] for a in soup.select("h2.entry-title a, .post-title a, h3 a")
                if a.get("href") and "iasbaba.com" in a.get("href", "")
            ]

            for link in article_links[:8]:
                time.sleep(1.5)
                art_html = _fetch_url(link)
                if not art_html:
                    continue
                art_text = _parse_article_text(art_html)
                year_match = re.search(r"20(\d{2})", link)
                year = int(f"20{year_match.group(1)}") if year_match else 2023

                pairs = _extract_question_answer_pairs(art_text)
                for pair in pairs:
                    if len(pair["answer"]) > 100:
                        rec = TopperAnswerRecord(
                            question_text=pair["question"][:500],
                            answer_text=pair["answer"][:3000],
                            subject=_infer_subject(pair["question"]),
                            topic=_infer_topic(pair["question"]),
                            year=year,
                            exam_type="UPSC",
                            source="IASbaba",
                            score=8.5,
                            tags=["model_answer", "iasbaba", str(year)],
                        )
                        records.append(rec)

            time.sleep(2)

    logger.info(f"IASbaba scrape complete: {len(records)} records")
    return records


def generate_topper_answer_with_llm(
    question: str,
    subject: str,
    year: int,
    marks: int = 15,
    word_limit: int = 250,
    llm=None,
) -> Optional[str]:
    """Use Groq/Gemini LLM to generate a topper-quality model answer."""
    if llm is None:
        # Try to import from app config
        try:
            from app.services.evaluation_service import get_llm
            llm = get_llm()
        except Exception:
            pass

    if llm is None:
        return None

    try:
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("human", TOPPER_GENERATION_PROMPT)
        ])
        chain = prompt | llm
        result = chain.invoke({
            "question": question,
            "subject": subject,
            "year": year,
            "marks": marks,
            "word_limit": word_limit,
        })
        text = result.content if hasattr(result, "content") else str(result)
        return text.strip()
    except Exception as e:
        logger.warning(f"LLM answer generation failed: {e}")
        return None
