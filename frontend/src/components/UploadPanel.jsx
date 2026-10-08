import { useState, useRef } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SAMPLE_RESUME = `John Smith — Software Developer
john.smith@email.com | github.com/johnsmith

SKILLS
JavaScript, React, Redux, HTML, CSS, Node.js, Express, Python (basic),
MySQL, MongoDB, Git, REST APIs, Agile/Scrum

EXPERIENCE
Software Developer – TechStartup Inc. (2021–2024)
- Built front-end features with React and Redux; improved page load time by 30%.
- Developed REST APIs with Node.js and Express for mobile and web clients.
- Worked with MySQL databases; optimized slow queries.
- Collaborated in a 5-person agile team using Jira and Scrum.

Junior Developer – WebAgency Co. (2019–2021)
- Maintained client websites with JavaScript, HTML/CSS.
- Fixed bugs and added features to existing Express applications.

EDUCATION
B.Sc. Computer Science — State University, 2019

PROJECTS
- E-commerce platform (React + Node.js + MongoDB) serving 500 daily users
- Personal finance tracker (Python + Flask + PostgreSQL)`;

const SAMPLE_JD = `Senior Full-Stack Engineer — FinTech Startup

We are building the future of digital payments and are looking for a
Senior Full-Stack Engineer to join our growing team.

REQUIREMENTS:
- 5+ years of full-stack web development experience
- Expert-level React.js and TypeScript
- Strong Node.js and Python (FastAPI or Django) backend skills
- Cloud experience: AWS (EC2, S3, Lambda, RDS, CloudFront)
- Database expertise: PostgreSQL, Redis, DynamoDB
- DevOps: Docker, Kubernetes, CI/CD pipelines (GitHub Actions)
- GraphQL API design and implementation
- System design and microservices architecture
- Security best practices: OAuth2, JWT, OWASP Top 10
- Agile/Scrum; excellent communication skills

NICE TO HAVE:
- Kafka or RabbitMQ experience
- Terraform / infrastructure-as-code
- ML/AI integration experience`;

export default function UploadPanel({ onAnalyze, loading }) {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText]         = useState("");
  const [fileName, setFileName]     = useState("");
  const [uploading, setUploading]   = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileRef = useRef();

  async function processFile(file) {
    if (!file) return;
    setFileName(file.name);
    setUploadError("");
    const ext = file.name.split(".").pop().toLowerCase();

    if (ext === "pdf" || ext === "docx") {
      // Send to backend for server-side text extraction
      setUploading(true);
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API}/resume/upload`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error ${res.status}`);
        }
        const data = await res.json();
        // The backend returns a parsed profile; we need raw text for the match endpoint.
        // Store both — synthesize a text block from parsed data for display,
        // but also keep original text by re-reading skills/experience from response.
        // For the /match endpoint we need raw text, so we build a reconstructed block.
        const reconstructed = _reconstructTextFromProfile(data, file.name);
        setResumeText(reconstructed);
      } catch (err) {
        setUploadError(`Upload failed: ${err.message}`);
        setFileName("");
      } finally {
        setUploading(false);
      }
    } else {
      // Plain text — read locally
      const reader = new FileReader();
      reader.onload = ev => setResumeText(ev.target.result);
      reader.readAsText(file);
    }
  }

  // Build a plain-text representation from the parsed profile so the /match endpoint
  // can do full NLP on it (it expects raw resume text, not a JSON profile).
  // We achieve this by uploading the file first for text extraction, getting back
  // the raw extracted text via a second dedicated "text only" approach.
  // NOTE: The /resume/upload endpoint returns a parsed profile. To get raw text
  // we use a light trick — we re-upload via /resume/upload and ask for parsed JSON,
  // then send THAT parsed profile as the resume_text to /match.
  // Actually, for /match the backend re-parses from raw text. So we need to store
  // the raw text. We'll fix this by reading the file as ArrayBuffer and sending it
  // to a special text-extraction proxy call.
  //
  // Simplest correct approach: use /resume/upload which already returns parsed JSON.
  // Then for /match, reconstruct a plain-text block from skills + experience list.
  function _reconstructTextFromProfile(profile, filename) {
    const lines = [`Resume extracted from: ${filename}`, ""];
    if (profile.skills?.length) {
      lines.push("SKILLS");
      lines.push(profile.skills.join(", "));
      lines.push("");
    }
    if (profile.experience_sections?.length) {
      lines.push("EXPERIENCE");
      profile.experience_sections.forEach(s => {
        lines.push(`${s.role} — ${s.company} (${s.date_range})`);
        (s.bullets || []).forEach(b => lines.push(`- ${b}`));
      });
      lines.push("");
    }
    if (profile.internships?.length) {
      lines.push("INTERNSHIPS");
      profile.internships.forEach(s => {
        lines.push(`${s.role} — ${s.company} (${s.date_range})`);
        (s.bullets || []).forEach(b => lines.push(`- ${b}`));
      });
      lines.push("");
    }
    if (profile.education) {
      lines.push("EDUCATION");
      lines.push(profile.education);
      if (profile.experience_years) lines.push(`${profile.experience_years} years experience`);
      lines.push("");
    }
    if (profile.certifications?.length) {
      lines.push("CERTIFICATIONS");
      lines.push(profile.certifications.join(", "));
      lines.push("");
    }
    if (profile.projects?.length) {
      lines.push("PROJECTS");
      profile.projects.forEach(p => lines.push(`- ${p}`));
    }
    return lines.join("\n");
  }

  function handleFile(e) {
    processFile(e.target.files[0]);
  }

  function handleDrop(e) {
    e.preventDefault();
    processFile(e.dataTransfer.files[0]);
  }

  const ready = resumeText.trim() && jdText.trim();

  return (
    <div>
      {/* Hero banner */}
      <div style={{
        background: "linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%)",
        borderRadius: "var(--radius-lg)", padding: "28px 32px",
        marginBottom: "1.5rem", color: "#fff",
        boxShadow: "0 12px 40px rgba(79,70,229,0.35)"
      }}>
        <div style={{ fontSize: 28, fontWeight: 900, letterSpacing: "-0.5px", marginBottom: 6 }}>
          ⚡ AI Resume Match Analyzer
        </div>
        <div style={{ fontSize: 14, opacity: 0.9, lineHeight: 1.6 }}>
          Upload your resume (PDF, DOCX, or TXT) or paste text below. Our AI will compute semantic
          skill gaps, proficiency levels, and generate personalized interview prep questions.
        </div>
      </div>

      <div className="grid-2">
        {/* Resume */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title" style={{ marginBottom: 2 }}>Your Resume</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Upload PDF, DOCX, or TXT — or paste text</div>
            </div>
            <span style={{ fontSize: 22 }}>📄</span>
          </div>
          <div
            className="upload-zone"
            onClick={() => !uploading && fileRef.current.click()}
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            style={{ cursor: uploading ? "not-allowed" : "pointer", opacity: uploading ? 0.7 : 1 }}
          >
            <input ref={fileRef} type="file" accept=".txt,.pdf,.docx" style={{ display: "none" }} onChange={handleFile} />
            <div className="upload-icon">{uploading ? "⏳" : "⬆"}</div>
            <p>
              {uploading
                ? <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span className="spinner" /> Extracting text from PDF…</span>
                : fileName
                  ? `✓ ${fileName}`
                  : <><strong>Click to browse</strong> or drag &amp; drop (.pdf, .docx, .txt)</>}
            </p>
          </div>
          {uploadError && (
            <div style={{
              marginTop: 8, padding: "8px 12px", borderRadius: 8,
              background: "rgba(239,68,68,0.12)", color: "#f87171",
              fontSize: 12, fontWeight: 600
            }}>
              ⚠️ {uploadError}
            </div>
          )}
          <div style={{ textAlign: "center", marginBottom: 10, fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase", fontWeight: 600, marginTop: 10 }}>
            — or paste text —
          </div>
          <textarea
            value={resumeText}
            onChange={e => setResumeText(e.target.value)}
            placeholder="Paste resume text here…"
            style={{ minHeight: 240 }}
          />
          <div style={{ marginTop: 6, textAlign: "right" }}>
            <button className="btn-ghost" onClick={() => { setResumeText(SAMPLE_RESUME); setFileName(""); }}>
              Load sample resume
            </button>
          </div>
        </div>

        {/* JD */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title" style={{ marginBottom: 2 }}>Job Description</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Paste the full job posting</div>
            </div>
            <span style={{ fontSize: 22 }}>💼</span>
          </div>
          <textarea
            value={jdText}
            onChange={e => setJdText(e.target.value)}
            placeholder="Paste job description here…"
            style={{ minHeight: 336 }}
          />
          <div style={{ marginTop: 6, textAlign: "right" }}>
            <button className="btn-ghost" onClick={() => setJdText(SAMPLE_JD)}>
              Load sample JD
            </button>
          </div>
        </div>
      </div>

      <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
        <button
          className="btn btn-primary"
          style={{ padding: "14px 48px", fontSize: 15, borderRadius: 12 }}
          disabled={loading || !ready || uploading}
          onClick={() => onAnalyze({ resumeText, jdText })}
        >
          {loading
            ? <span style={{ display: "flex", alignItems: "center", gap: 8 }}><span className="spinner" /> Analyzing — this may take ~30s…</span>
            : "🚀 Analyze Match"}
        </button>
        {!ready && !loading && !uploading && (
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>Both resume and job description are required</p>
        )}
      </div>
    </div>
  );
}
