"""
Intelligent Resume Match & Learning Path Recommender
FastAPI Backend

Endpoints:
  POST /resume/parse     → structured JSON profile from resume text
  POST /resume/upload    → upload a .txt resume file
  POST /jd/parse         → structured JSON profile from JD text
  POST /match            → match score + full gap report
  POST /recommend/courses → personalized learning path
  POST /improve/resume   → STAR-style improvement bullets
  GET  /kg/skills        → list all KG skills
  GET  /kg/courses/{skill}

Swagger UI: http://localhost:8000/docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import io
import uvicorn

from nlp_pipeline import (
    parse_resume_text,
    parse_jd_text,
    compute_match,
    recommend_courses,
    generate_star_improvements,
    generate_more_interview_questions,
)

# ---------------------------------------------------------------------------
# PDF / DOCX extraction helpers (graceful fallback if libs not installed)
# ---------------------------------------------------------------------------
try:
    import pdfplumber as _pdfplumber
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

try:
    import docx as _docx
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract all text from a PDF byte stream using pdfplumber."""
    if not _PDF_AVAILABLE:
        raise HTTPException(
            status_code=422,
            detail="pdfplumber is not installed on the server. Run: pip install pdfplumber"
        )
    text_parts = []
    with _pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_text_from_docx(content: bytes) -> str:
    """Extract all text from a DOCX byte stream using python-docx."""
    if not _DOCX_AVAILABLE:
        raise HTTPException(
            status_code=422,
            detail="python-docx is not installed on the server. Run: pip install python-docx"
        )
    doc = _docx.Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

# ---------------------------------------------------------------------------
app = FastAPI(
    title="Resume Match & Learning Path API",
    description=(
        "AI-powered resume-to-JD matching, skill gap detection, "
        "personalized course recommendations, and STAR-style resume improvement."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class TextRequest(BaseModel):
    text: str

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str

class CourseRequest(BaseModel):
    gap_skills: List[str]
    free_only: bool = False
    platform: Optional[str] = None
    max_duration_hours: Optional[int] = None

class ImproveRequest(BaseModel):
    resume_text: str
    jd_text: str
    gap_skills: List[str]

class MoreQuestionsRequest(BaseModel):
    resume_text: str
    jd_text: str
    missing_skills: List[str]
    weak_skills: List[dict]
    experience_gap: Optional[dict] = None
    existing_questions: List[dict] = []
    count: int = 3


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "message": "Resume Matcher API is running. Visit /docs for Swagger UI."}


@app.post(
    "/resume/parse",
    summary="Parse resume text → structured JSON profile",
    response_description="Skills, experience, education, certifications, competency levels",
)
def parse_resume(req: TextRequest):
    """
    Send raw resume text (extracted from PDF/DOCX/TXT) and receive
    a structured profile: skills, years of experience, education level,
    certifications, and inferred competency levels.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Resume text is empty")
    return parse_resume_text(req.text)


@app.post(
    "/resume/upload",
    summary="Upload a resume file (.pdf, .docx, .txt) → structured JSON profile",
)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file in PDF, DOCX, or plain-text format.
    The server will extract the text and return a structured profile.
    """
    content = await file.read()
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    # Detect file type and extract text accordingly
    if filename.endswith(".pdf") or "pdf" in content_type:
        text = _extract_text_from_pdf(content)
    elif filename.endswith(".docx") or "openxmlformats" in content_type or "officedocument" in content_type:
        text = _extract_text_from_docx(content)
    else:
        # Try UTF-8 text fallback (covers .txt and other text formats)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Could not decode file. Supported formats: .pdf, .docx, .txt",
                )

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file appears to be empty or has no extractable text")
    return parse_resume_text(text)


@app.post(
    "/jd/parse",
    summary="Parse job description text → structured JSON profile",
)
def parse_jd(req: TextRequest):
    """
    Returns required skills, nice-to-have skills, experience requirement,
    education requirement, responsibilities, and bias flags.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="JD text is empty")
    return parse_jd_text(req.text)


@app.post(
    "/match",
    summary="Compute semantic match score + full gap report",
)
def match(req: MatchRequest):
    """
    Returns:
    - Overall match score (0–100)
    - Score breakdown: skills / experience / education / keyword-semantic
    - Matched, weak, and missing skills
    - Synonym / paraphrase matches
    - Competency level inference
    - Custom interview preparation questions (Technical & Behavioral)
    - Human-readable gap summary
    """
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text is empty")
    if not req.jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text is empty")
    return compute_match(req.resume_text, req.jd_text)


@app.post(
    "/recommend/courses",
    summary="Get personalized course recommendations for skill gaps",
)
def get_courses(req: CourseRequest):
    """
    Given a list of gap skills and optional filters (free_only, platform,
    max_duration_hours), returns a structured learning path:
    foundational → intermediate → advanced.
    """
    if not req.gap_skills:
        raise HTTPException(status_code=400, detail="gap_skills list is empty")
    return recommend_courses(
        req.gap_skills, req.free_only, req.platform, req.max_duration_hours
    )


@app.post(
    "/improve/resume",
    summary="Generate STAR-style resume improvement bullets for skill gaps",
)
def improve_resume(req: ImproveRequest):
    """
    For each identified skill gap, generates a STAR-style bullet
    (Situation, Task, Action, Result) the candidate can adapt for their resume.
    """
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text is empty")
    return generate_star_improvements(req.resume_text, req.jd_text, req.gap_skills)

@app.post(
    "/interview-prep/generate",
    summary="Generate MORE custom interview preparation questions",
)
def get_more_interview_questions(req: MoreQuestionsRequest):
    return generate_more_interview_questions(
        req.resume_text, req.jd_text, req.missing_skills, req.weak_skills, req.experience_gap, req.count, req.existing_questions
    )

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
