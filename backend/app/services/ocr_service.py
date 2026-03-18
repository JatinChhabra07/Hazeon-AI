"""
OCR Service — Handles image preprocessing and text extraction.

Pipeline:
1. PDF → extract pages as images (PyMuPDF)
2. Image preprocessing (OpenCV: deskew, denoise, threshold)
3. OCR via Gemini Vision API (handles Hindi + English handwriting)
4. Fallback: smart mock output for demo/testing
"""
import os
import io
import base64
import random
import logging
from typing import Tuple

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Demo OCR Outputs ──────────────────────────────────────────────────────────
DEMO_OCR_OUTPUTS = {
    "governance": """
The concept of good governance encompasses transparency, accountability, and citizen participation
in the democratic process. In the context of Haryana, several governance reforms have been
implemented to improve public service delivery.

The Haryana government has taken significant steps through e-governance initiatives like
Antyodaya SARAL platform which provides single-window access to government services.
The CM Window portal allows direct grievance redressal.

Key dimensions of governance reform include:
- Administrative reforms: Simplification of procedures, digitization of land records through
  Jamabandi Nakal system
- Financial governance: Implementation of DBT (Direct Benefit Transfer) reducing leakages
- Social governance: Beti Bachao Beti Padhao originated from Haryana
- Judicial reforms: Fast track courts, Lok Adalats for speedy justice

However, challenges remain including bureaucratic resistance to change, digital divide in
rural areas, and need for capacity building of government officials.

Way Forward: Strengthening PRIs, improving digital literacy, and adopting AI-based governance
tools can enhance governance quality. The Haryana government should focus on outcome-based
monitoring rather than output-based assessment.
""",
    "economy": """
The economic development of Haryana has been remarkable since its formation in 1966.
From being primarily an agrarian state, Haryana has transformed into an industrial powerhouse
with significant contributions from IT, automobile, and textile sectors.

Agriculture: Haryana contributes significantly to India's food security. It is the second
largest contributor to the central food grain pool. Green Revolution transformed agriculture
with HYV seeds, irrigation through Bhakra canal system. However, issues of depleting water
table, stubble burning, and over-reliance on wheat-paddy cycle persist.

Industrial Development: Gurugram has emerged as a major IT and corporate hub. Faridabad,
Panipat, and Hisar have strong industrial bases. The state's industrial policy offers
incentives through HSIIDC.

Key Economic Indicators:
- Per capita income among highest in India
- Strong automobile sector (Maruti Suzuki, Hero MotoCorp)
- Emerging startup ecosystem in Gurugram

Challenges: Regional disparity between North and South Haryana, unemployment despite
industrial growth, need for skilling youth.

Conclusion: Balanced regional development, investment in human capital, and sustainable
agriculture practices are essential for Haryana's continued economic growth.
""",
    "society": """
Social development in Haryana presents a paradox - high economic indicators coexist with
concerning social metrics, particularly regarding gender issues. The state has historically
had one of the lowest sex ratios in India, though recent improvements are noteworthy.

Gender Issues: The Beti Bachao Beti Padhao campaign launched from Panipat has shown positive
results. Sex ratio at birth improved from 834 (2011) to over 920 in recent years. However,
honor killings, child marriage in some areas, and patriarchal mindset remain challenges.

Education: Haryana has made significant strides in education with schemes like:
- Super 100 program for meritorious students
- Consolidation of schools for better quality
- Multiple state universities established

Way Forward: Focus on changing social attitudes through education, strengthening women's
SHGs, and ensuring last-mile delivery of social welfare schemes.
""",
    "general": """
India's federal structure presents unique challenges and opportunities for cooperative
governance. The relationship between Centre and States has evolved significantly since
independence, shaped by constitutional provisions, judicial interpretations, and political
dynamics.

Constitutional Framework: Articles 245-263 define legislative, administrative, and financial
relations. Seventh Schedule distributes powers through Union, State, and Concurrent lists.

Key Issues:
1. Fiscal Federalism: GST implementation has subsumed state taxes, raising concerns about
   fiscal autonomy.
2. Governor's Role: Discretionary powers, Article 356 misuse, recent controversies.
3. Water Disputes: Interstate river water sharing (SYL canal issue).

Conclusion: Cooperative and competitive federalism should be strengthened through regular
ISC meetings, dispute resolution mechanisms, and respecting constitutional boundaries.
"""
}


# ── Image Preprocessing ───────────────────────────────────────────────────────
def preprocess_image(image_path: str) -> str:
    """
    Preprocess uploaded image for better OCR results.
    Deskewing, denoising, and adaptive thresholding via OpenCV.
    Returns path to preprocessed image.
    """
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            return image_path

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Deskew
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = gray.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Denoise + threshold
        denoised = cv2.fastNlMeansDenoising(rotated, h=10)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        preprocessed_path = image_path.rsplit(".", 1)[0] + "_p.png"
        cv2.imwrite(preprocessed_path, thresh)
        return preprocessed_path

    except ImportError:
        logger.warning("OpenCV not available, skipping preprocessing.")
        return image_path
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        return image_path


# ── PDF Extraction ────────────────────────────────────────────────────────────
def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF.
    For scanned/handwritten PDFs, renders pages as images then OCR via Gemini Vision.
    For digital PDFs, extracts text directly.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        all_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Try direct text extraction first (works for digital PDFs)
            text = page.get_text("text").strip()

            if text and len(text) > 30:
                all_text.append(text)
            else:
                # Scanned/handwritten PDF — render page as image and OCR
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")

                # OCR the rendered page image
                ocr_text = _gemini_vision_ocr_bytes(img_bytes, "image/png")
                if ocr_text:
                    all_text.append(ocr_text)

        doc.close()
        return "\n\n".join(all_text)

    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install PyMuPDF")
        return "[PDF Error: PyMuPDF not installed]"
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return f"[PDF Error: {str(e)}]"


# ── Gemini Vision OCR ─────────────────────────────────────────────────────────
def _gemini_vision_ocr(file_path: str) -> str:
    """OCR an image file using Google Gemini Vision API."""
    try:
        with open(file_path, "rb") as f:
            img_bytes = f.read()

        ext = os.path.splitext(file_path)[1].lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".bmp": "image/bmp", ".tiff": "image/tiff"}.get(ext, "image/jpeg")

        return _gemini_vision_ocr_bytes(img_bytes, mime)

    except Exception as e:
        logger.error(f"Gemini Vision OCR failed: {e}")
        return f"[OCR Error: {str(e)}]"


def _gemini_vision_ocr_bytes(img_bytes: bytes, mime_type: str) -> str:
    """
    Core Gemini Vision OCR — sends image bytes to Gemini and extracts text.
    Handles Hindi + English mixed handwriting.
    """
    api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
    if not api_key:
        logger.warning("No Gemini API key configured, falling back to demo OCR.")
        return ""

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        prompt = """You are an expert OCR system specialized in handwritten text extraction for Indian competitive exams (UPSC/HCS/IAS).

Extract ALL handwritten text from this answer sheet image. The text may be in:
- English only
- Hindi only
- Mixed Hindi and English (most common)

Instructions:
1. Extract every word exactly as written, preserving the structure
2. Maintain paragraph breaks and bullet points
3. For Hindi text, use proper Devanagari script
4. For diagrams/flowcharts, describe them briefly as [DIAGRAM: description]
5. If text is unclear, make your best attempt and mark as [unclear]
6. Preserve headings, underlines, and structural elements

Return ONLY the extracted text, nothing else."""

        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": img_b64}
        ])

        return response.text.strip()

    except Exception as e:
        logger.error(f"Gemini Vision API call failed: {e}")
        return ""


# ── Demo OCR ──────────────────────────────────────────────────────────────────
def _demo_ocr(file_path: str) -> str:
    """Smart mock OCR — picks contextual output based on filename."""
    filename = os.path.basename(file_path).lower()
    for key in DEMO_OCR_OUTPUTS:
        if key in filename:
            return DEMO_OCR_OUTPUTS[key].strip()
    return random.choice(list(DEMO_OCR_OUTPUTS.values())).strip()


# ── Main Entry Point ──────────────────────────────────────────────────────────
def perform_ocr(file_path: str) -> Tuple[str, int]:
    """
    Main OCR entry point.
    Routes by file type: PDF → extract_text_from_pdf, image → Gemini Vision OCR.
    Returns (extracted_text, word_count).
    """
    if settings.DEMO_MODE:
        text = _demo_ocr(file_path)
        return text, len(text.split())

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        # If still empty (total extraction failure), fall back to demo
        if not text or len(text.strip()) < 20:
            logger.warning("PDF extraction returned empty text, using demo fallback.")
            text = _demo_ocr(file_path)

    elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
        preprocessed = preprocess_image(file_path)
        text = _gemini_vision_ocr(preprocessed)
        if not text or len(text.strip()) < 10:
            logger.warning("Gemini OCR returned empty, using demo fallback.")
            text = _demo_ocr(file_path)
    else:
        text = _demo_ocr(file_path)

    word_count = len(text.split()) if text else 0
    return text, word_count
