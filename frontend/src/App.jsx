import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import MatchDashboard from "./components/MatchDashboard";
import LearningPath from "./components/LearningPath";
import ResumeImprover from "./components/ResumeImprover";

const TABS = [
  { id: "input",   label: "1 · Input" },
  { id: "match",   label: "2 · Match Analysis" },
  { id: "courses", label: "3 · Learning Path" },
  { id: "improve", label: "4 · Improve Resume" },
];

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [tab, setTab]     = useState("input");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  async function handleAnalyze({ resumeText, jdText }) {
    setLoading(true);
    setError("");
    try {
      // 1. Match score + gap report
      const matchRes = await fetch(`${API}/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, jd_text: jdText }),
      });
      if (!matchRes.ok) {
        const e = await matchRes.json();
        throw new Error(e.detail || "Match API error");
      }
      const matchData = await matchRes.json();
      const gaps = matchData.top_missing_skills || [];

      // 2. Course recommendations
      let courses = { learning_path: {}, total_courses: 0 };
      if (gaps.length) {
        const cRes = await fetch(`${API}/recommend/courses`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ gap_skills: gaps }),
        });
        if (cRes.ok) courses = await cRes.json();
      }

      // 3. STAR improvements
      let improvements = { star_improvements: [] };
      if (gaps.length) {
        const iRes = await fetch(`${API}/improve/resume`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resume_text: resumeText, jd_text: jdText, gap_skills: gaps }),
        });
        if (iRes.ok) improvements = await iRes.json();
      }

      setResult({ ...matchData, courses, improvements, resume_text: resumeText, jd_text: jdText });
      setTab("match");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <div className="logo-icon">⚡</div>
            <div>
              <h1>Resume Match AI</h1>
              <p>Semantic gap analysis &amp; learning path recommender</p>
            </div>
          </div>
          {result && (
            <div className="score-badge" style={{
              background: result.match_score >= 70 ? "#059669" : result.match_score >= 45 ? "#d97706" : "#dc2626"
            }}>
              <span className="score-num">{result.match_score}%</span>
              <span className="score-lbl">match score</span>
            </div>
          )}
        </div>
      </header>

      {/* ── Tabs ── */}
      <nav className="tab-nav">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? "active" : ""} ${t.id !== "input" && !result ? "disabled" : ""}`}
            onClick={() => (t.id === "input" || result) && setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* ── Main ── */}
      <main className="main-content">
        {error && <div className="error-banner">⚠ {error}</div>}
        {loading && tab === "input" ? (
          <div className="loading-row">
            <div className="spinner" />
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>Analyzing your resume…</div>
              <div style={{ fontSize: 13, marginTop: 4 }}>This takes 20–60 seconds as we scrape live course data.</div>
            </div>
          </div>
        ) : null}
        {tab === "input"   && <UploadPanel   onAnalyze={handleAnalyze} loading={loading} />}
        {tab === "match"   && result && <MatchDashboard data={result} />}
        {tab === "courses" && result && <LearningPath   data={result.courses} missingSkills={result.top_missing_skills} />}
        {tab === "improve" && result && <ResumeImprover data={result.improvements} />}
      </main>
    </div>
  );
}
