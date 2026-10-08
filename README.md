# Intelligent Resume Match & Learning Path Recommender

A full-stack AI-powered application that:

- Parses resumes and job descriptions into structured profiles  
- Computes a **semantic match score** (0–100%) with breakdown by skills, experience, education, keywords  
- Identifies **skill gaps** — missing and weak-coverage skills  
- Recommends a **personalized learning path** (foundational → intermediate → advanced)  
- Detects **skill synonyms and paraphrase matches** (e.g. "full-stack" ↔ "MERN")  
- Infers **competency levels** (basic / intermediate / advanced) from resume context  
- Flags **biased or exclusionary language** in job descriptions  
- Generates **STAR-style resume improvement bullets** for each skill gap  

---

## Project Structure

```
resume_matcher/
├── README.md
├── backend/
│   ├── main.py              ← FastAPI app + all API endpoints
│   ├── nlp_pipeline.py      ← NLP: parsing, matching, gap detection, STAR suggestions
│   ├── knowledge_graph.py   ← In-memory course catalog, skill synonyms, bias patterns
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env                 ← VITE_API_URL=http://localhost:8000
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── App.css
        └── components/
            ├── UploadPanel.jsx      ← Resume upload + JD input
            ├── MatchDashboard.jsx   ← Score, skill analysis, synonyms, bias flags
            ├── LearningPath.jsx     ← Course cards with free/paid/platform filters
            └── ResumeImprover.jsx   ← STAR-style improvement bullets
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10 or newer |
| pip | bundled with Python |
| Node.js | 18 or newer |
| npm | bundled with Node.js |

---

## Quickstart — 3 steps

### Step 1 — Backend

```bash
cd resume_matcher/backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
python main.py
```

The backend is now running at **http://localhost:8000**  
Interactive API docs (Swagger UI): **http://localhost:8000/docs**

---

### Step 2 — Frontend

Open a **new terminal** (keep the backend running):

```bash
cd resume_matcher/frontend

npm install
npm run dev
```

The React app is now running at **http://localhost:3000**

---

### Step 3 — Use the app

1. Open **http://localhost:3000** in your browser.  
2. Click **"Load sample resume"** and **"Load sample JD"** to try the demo data.  
3. Click **"Analyze Match →"**.  
4. Explore the four tabs: Match Analysis, Learning Path, Improve Resume.

---

## Enable Real Semantic Embeddings (optional, better accuracy)

By default the backend uses TF-IDF cosine similarity (fast, no GPU required).

To enable sentence-transformer embeddings (~80 MB model download on first run):

```bash
# 1. Edit backend/requirements.txt — uncomment these two lines:
#    sentence-transformers==2.7.0
#    torch==2.3.0

pip install sentence-transformers torch

# Restart the backend — the model downloads automatically on first request.
```

---

## Enable PDF and DOCX File Upload (optional)

The upload endpoint currently parses plain `.txt` files.  
To add PDF/DOCX support:

```bash
pip install pdfplumber python-docx
```

Then update `upload_resume()` in `backend/main.py`:

```python
# For PDF files
import pdfplumber
with pdfplumber.open(tmp_path) as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)

# For DOCX files
from docx import Document
doc = Document(tmp_path)
text = "\n".join(p.text for p in doc.paragraphs)
```

---

## API Reference

All endpoints documented at **http://localhost:8000/docs** (Swagger UI).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/resume/parse` | Parse resume text → structured JSON profile |
| `POST` | `/resume/upload` | Upload .txt resume file → structured JSON profile |
| `POST` | `/jd/parse` | Parse JD text → structured JSON profile |
| `POST` | `/match` | Resume + JD → match score + full gap report |
| `POST` | `/recommend/courses` | Gap skills + filters → learning path |
| `POST` | `/improve/resume` | Resume + JD + gaps → STAR improvement bullets |
| `GET`  | `/kg/skills` | List all skills in the knowledge graph |
| `GET`  | `/kg/courses/{skill}` | Get courses for a specific skill |

### Quick curl example

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer, 3 years React and Node.js ...",
    "jd_text": "Senior engineer, TypeScript, AWS, Docker, Kubernetes ..."
  }'
```

---

## Extending the Course Knowledge Graph

Open `backend/knowledge_graph.py` and add entries to `COURSE_KG`:

```python
COURSE_KG["your_skill_slug"] = [
    {
        "title": "Course Title",
        "platform": "Coursera",         # or Udemy, edX, YouTube, etc.
        "url": "https://...",
        "duration": "10 hours",
        "duration_hours": 10,           # integer — used for filtering
        "free": False,                  # True or False
        "level": "intermediate",        # "foundational" | "intermediate" | "advanced"
        "description": "Short description of what this course covers.",
    }
]
```

---

## Extending Skill Synonym Groups

In `knowledge_graph.py`, add to `SKILL_SYNONYMS`:

```python
SKILL_SYNONYMS["your_term"]   = "shared_group_id"
SKILL_SYNONYMS["alias_term"]  = "shared_group_id"   # same group → treated as synonyms
```

---

## Extending Bias Detection

In `knowledge_graph.py`, add to `BIAS_PATTERNS`:

```python
{
    "regex": r"\bpattern\b",
    "issue": "Human-readable description of the bias",
    "suggestion": "Alternative inclusive wording",
    "category": "gender | age | exclusionary",
}
```

---

## Architecture

```
Browser (React, port 3000)
       │
       │  HTTP / JSON
       ▼
FastAPI Backend (port 8000)
  ├─ POST /match
  │     ├─ parse_resume_text()      regex NER + skill extraction
  │     ├─ parse_jd_text()          skill extraction + bias detection
  │     ├─ _semantic_sim()          sentence-transformers or TF-IDF
  │     ├─ _find_synonyms()         SKILL_SYNONYMS lookup
  │     └─ _infer_competency()      context keyword heuristics
  ├─ POST /recommend/courses
  │     └─ recommend_courses()      COURSE_KG lookup + filters
  └─ POST /improve/resume
        └─ generate_star_improvements()   STAR template library
```

---

## Troubleshooting

**CORS errors in browser**  
The backend allows all origins by default. If you restrict `allow_origins` in `main.py`, add `http://localhost:3000`.

**"Module not found" on backend start**  
Make sure you activated the virtual environment: `source venv/bin/activate`

**Frontend shows "Analysis failed" or network error**  
Check that the backend is running and that `VITE_API_URL` in `frontend/.env` matches the backend port (default `http://localhost:8000`).

**Slow first request with sentence-transformers**  
The model downloads ~80 MB on the first run. Subsequent requests are fast (model is cached in memory).

---

## License

MIT — free to use, modify, and extend.
