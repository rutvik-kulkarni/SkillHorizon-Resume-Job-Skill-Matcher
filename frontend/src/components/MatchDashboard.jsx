import { useState, useEffect } from "react";

/* ── Helpers ─────────────────────────────────────────────────────────── */
function barColor(v) {
  return v >= 70 ? "#059669" : v >= 45 ? "#d97706" : "#dc2626";
}
function levelPct(lvl) {
  return { basic: 33, intermediate: 66, advanced: 100 }[lvl?.toLowerCase()] ?? 0;
}

/* ── Score Ring ──────────────────────────────────────────────────────── */
function ScoreRing({ score }) {
  const r = 52, circ = 2 * Math.PI * r;
  const color = score >= 70 ? "#059669" : score >= 45 ? "#d97706" : "#dc2626";
  const label = score >= 70 ? "Strong fit" : score >= 45 ? "Moderate fit" : "Weak fit";
  const [animated, setAnimated] = useState(0);
  useEffect(() => { const t = setTimeout(() => setAnimated(score), 200); return () => clearTimeout(t); }, [score]);
  return (
    <div className="score-ring-wrap">
      <div style={{ position: "relative", width: 128, height: 128, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="128" height="128" viewBox="0 0 128 128" style={{ position: "absolute", transform: "rotate(-90deg)" }}>
          <circle cx="64" cy="64" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
          <circle cx="64" cy="64" r={r} fill="none" stroke={color} strokeWidth="10"
            strokeDasharray={`${(animated / 100) * circ} ${circ}`} strokeLinecap="round"
            style={{ transition: "stroke-dasharray 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)" }} />
        </svg>
        <div style={{ textAlign: "center", zIndex: 1 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{score}%</div>
          <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 3, fontWeight: 600 }}>{label}</div>
        </div>
      </div>
    </div>
  );
}

/* ── Skill Gap Visual (pill grid) ────────────────────────────────────── */
function SkillGapVisual({ matched, weak, missing, taxonomy = {} }) {
  const [section, setSection] = useState("missing");
  const tabs = [
    { key: "missing", label: "Missing", color: "#dc2626", icon: "✕", items: missing },
    { key: "weak",    label: "Weak",    color: "#d97706", icon: "⚠", items: weak    },
    { key: "matched", label: "Matched", color: "#059669", icon: "✓", items: matched },
  ];
  const total = matched.length + weak.length + missing.length || 1;
  const active = tabs.find(t => t.key === section);

  // Helper to render ESCO badge if taxonomy is available
  const renderEscoBadge = (skillName) => {
    const escoData = taxonomy?.esco_skills?.[skillName];
    if (escoData && escoData.esco_uri) {
      return (
        <a href={escoData.esco_uri} target="_blank" rel="noreferrer" title={`ESCO Normalized: ${escoData.preferred_label}`} 
           style={{ marginLeft: 6, fontSize: 10, textDecoration: "none", opacity: 0.6, cursor: "pointer" }}>
          🔗
        </a>
      );
    }
    return null;
  };

  return (
    <div>
      {/* Proportion bar */}
      <div className="skill-prop-bar">
        {tabs.map(t => (
          <div key={t.key} style={{
            flex: t.items.length / total, background: t.color,
            opacity: section === t.key ? 1 : 0.2, minWidth: t.items.length ? 4 : 0
          }} />
        ))}
      </div>

      {/* Tab buttons */}
      <div className="skill-tab-bar">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setSection(t.key)}
            className={`skill-tab tab-${t.key} ${section === t.key ? "active" : ""}`}>
            <span>{t.icon}</span>
            {t.label}
            <span className="tab-count">{t.items.length}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      {active.items.length === 0 ? (
        <div style={{ textAlign: "center", padding: "20px 0", color: "#94a3b8", fontSize: 13 }}>
          No {active.label.toLowerCase()} skills 🎉
        </div>
      ) : active.key === "missing" ? (
        <div className="skill-pill-grid">
          {missing.map((s, i) => (
            <span key={i} className="skill-pill skill-pill-missing" style={{ display: 'inline-flex', alignItems: 'center' }}>
              <span className="skill-pill-icon">✕</span>
              {s.skill || s}
              {renderEscoBadge(s.skill || s)}
            </span>
          ))}
        </div>
      ) : active.key === "weak" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {weak.map((s, i) => {
            const hp = levelPct(s.resume_level), np = levelPct(s.jd_expected);
            return (
              <div key={i} className="weak-skill-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#92400e", display: 'inline-flex', alignItems: 'center' }}>
                    {s.skill}
                    {renderEscoBadge(s.skill)}
                  </span>
                  <span style={{ fontSize: 11, color: "#d97706", fontWeight: 700 }}>
                    {s.resume_level?.toUpperCase()} → {s.jd_expected?.toUpperCase()}
                  </span>
                </div>
                <div className="weak-skill-bar-track">
                  <div className="weak-skill-bar-need" style={{ width: `${np}%` }} />
                  <div className="weak-skill-bar-have" style={{ width: `${hp}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="skill-pill-grid">
          {matched.map((s, i) => (
            <span key={i} className="skill-pill skill-pill-matched" style={{ display: 'inline-flex', alignItems: 'center' }}>
              <span className="skill-pill-icon">✓</span>
              {s.skill}
              {s.confidence != null && <span style={{ fontSize: 10, opacity: 0.7, marginLeft: 4 }}>{s.confidence}%</span>}
              {/* Note: we don't normalize matched skills right now in backend to save time, but if we did we'd show badge here */}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Skill Comparison Grid ────────────────────────────────────────────── */
function SkillComparison({ skills }) {
  const [filter, setFilter] = useState("all");
  if (!skills || skills.length === 0)
    return <div style={{ fontSize: 13, color: "#94a3b8" }}>No skill comparison data available.</div>;

  const filtered = filter === "all" ? skills : skills.filter(s => s.status === filter);
  const counts = { all: skills.length, matched: 0, weak: 0, missing: 0 };
  skills.forEach(s => { if (counts[s.status] !== undefined) counts[s.status]++; });

  const badgeClass = { matched: "badge-matched", weak: "badge-weak", missing: "badge-missing" };

  return (
    <div>
      {/* Filter tabs */}
      <div className="filter-row" style={{ marginBottom: "1.25rem" }}>
        {[["all", "All", counts.all], ["matched", "Matched ✓", counts.matched], ["weak", "Weak ⚠", counts.weak], ["missing", "Missing ✕", counts.missing]].map(([k, l, c]) => (
          <button key={k} className={`filter-btn ${filter === k ? "active" : ""}`} onClick={() => setFilter(k)}>
            {l} <span style={{ opacity: 0.65, marginLeft: 3 }}>({c})</span>
          </button>
        ))}
      </div>

      <div className="grid-auto">
        {filtered.map((s, idx) => {
          const reqPct = levelPct(s.expected_level);
          const candPct = levelPct(s.candidate_level);
          const hasGap = candPct < reqPct;
          const gapPct = reqPct - candPct;
          const barColor = s.status === "matched" ? "#059669" : s.status === "weak" ? "#d97706" : "#e2e8f0";

          return (
            <div key={idx} className="skill-cmp-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 13.5, fontWeight: 700, color: "#0f172a" }}>{s.skill}</span>
                  <span className={`badge ${s.required_status === "Required" ? "badge-required" : "badge-preferred"}`}>
                    {s.required_status}
                  </span>
                </div>
                <span className={`badge ${badgeClass[s.status] || "badge-missing"}`}>
                  {s.status === "matched" ? "✓ Matched" : s.status === "weak" ? "⚠ Level Gap" : "✕ Missing"}
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#64748b", marginBottom: 6 }}>
                <span>You: <strong style={{ color: s.status === "missing" ? "#dc2626" : "#475569" }}>
                  {s.candidate_level === "none" ? "Not detected" : `${s.candidate_level?.toUpperCase()} (${candPct}%)`}
                </strong></span>
                <span>Required: <strong style={{ color: "#4f46e5" }}>{s.expected_level?.toUpperCase()} ({reqPct}%)</strong></span>
              </div>

              <div className="skill-cmp-bar-track">
                {candPct > 0 && (
                  <div style={{
                    position: "absolute", left: 0, top: 0, height: "100%", width: `${candPct}%`,
                    background: barColor, borderRadius: hasGap ? "6px 0 0 6px" : "6px",
                    transition: "width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)"
                  }} />
                )}
                {hasGap && (
                  <div style={{
                    position: "absolute", left: `${candPct}%`, top: 0, height: "100%", width: `${gapPct}%`,
                    background: "repeating-linear-gradient(45deg,rgba(220,38,38,.06),rgba(220,38,38,.06) 5px,rgba(220,38,38,.15) 5px,rgba(220,38,38,.15) 10px)"
                  }} />
                )}
                <div style={{ position: "absolute", left: `calc(${reqPct}% - 1.5px)`, top: 0, width: 3, height: "100%", background: "#4f46e5", zIndex: 2, borderRadius: 2 }} />
              </div>
              {hasGap && (
                <div style={{ fontSize: 10.5, color: "#dc2626", marginTop: 4, textAlign: "right", fontWeight: 600 }}>
                  ⚠ {gapPct}% gap to close
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Interview Prep ───────────────────────────────────────────────────── */
function InterviewPrepSection({ initialQuestions, data }) {
  const [questions, setQuestions] = useState(initialQuestions || []);
  const [openIdx, setOpenIdx] = useState({ 0: true });
  const [loading, setLoading] = useState(false);

  const toggle = (i) => setOpenIdx(p => ({ ...p, [i]: !p[i] }));

  const getCatMeta = (cat) => {
    if (cat?.startsWith("Technical")) return { icon: "⚙️", color: "#1d4ed8", bg: "#eff6ff" };
    if (cat?.startsWith("Experience")) return { icon: "⏱️", color: "#dc2626", bg: "#fef2f2" };
    return { icon: "🧠", color: "#6d28d9", bg: "#f5f3ff" };
  };

  const DIFF = ["Medium", "Hard", "Hard", "Medium", "Easy", "Medium", "Hard"];
  const diffColor = (d) => d === "Easy" ? "#059669" : d === "Medium" ? "#d97706" : "#dc2626";

  const loadMore = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/interview-prep/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: data.resume_text || "",
          jd_text: data.jd_text || "",
          missing_skills: (data.skill_analysis?.missing || []).map(s => s.skill || s),
          weak_skills: data.skill_analysis?.weak || [],
          experience_gap: data.experience_gap || null,
          existing_questions: questions,
          count: 3
        })
      });
      if (res.ok) {
        const newQs = await res.json();
        if (Array.isArray(newQs) && newQs.length > 0) {
          setQuestions(prev => [...prev, ...newQs]);
        }
      }
    } catch (err) {
      console.error("Failed to load more questions", err);
    } finally {
      setLoading(false);
    }
  };

  if (!questions || questions.length === 0)
    return <div style={{ fontSize: 13, color: "#94a3b8" }}>No prep questions generated.</div>;

  return (
    <div>
      {questions.map((q, idx) => {
        const meta = getCatMeta(q.category);
        const diff = DIFF[idx % DIFF.length];
        const dc = diffColor(diff);
        const isOpen = !!openIdx[idx];
        return (
          <div key={idx} className={`interview-card ${isOpen ? "interview-card-open" : ""}`}
            style={{ borderColor: isOpen ? meta.color + "55" : "var(--border)", ...(isOpen ? { background: meta.bg } : {}) }}>
            <div className="interview-card-header" onClick={() => toggle(idx)}>
              <div style={{ flex: 1 }}>
                <div className="interview-card-meta">
                  <span className="interview-icon">{meta.icon}</span>
                  <span className="interview-cat-badge"
                    style={{ background: meta.color + "22", color: meta.color }}>
                    {q.category}
                  </span>
                  <span className="interview-diff-badge"
                    style={{ background: dc + "22", color: dc }}>
                    {diff}
                  </span>
                </div>
                <div className="interview-q-text">
                  Q{idx + 1}. {q.question}
                </div>
              </div>
              <span className="interview-chevron">{isOpen ? "▴" : "▾"}</span>
            </div>
            {isOpen && (
              <div className="interview-answer" style={{ borderTopColor: meta.color + "33" }}>
                <div className="interview-hint" style={{ borderLeftColor: meta.color, background: "rgba(255,255,255,0.85)" }}>
                  <strong style={{ color: meta.color }}>💡 Answer Strategy: </strong>
                  {q.hint}
                </div>
              </div>
            )}
          </div>
        );
      })}

      <button className="load-more-btn" onClick={loadMore} disabled={loading}>
        {loading ? (
          <><span className="spinner" style={{ borderTopColor: "#4f46e5", width: 16, height: 16, borderWidth: 2 }} /> Generating more questions…</>
        ) : (
          <><span>🤖</span> Load More Questions</>
        )}
      </button>
    </div>
  );
}

/* ── Main Dashboard ──────────────────────────────────────────────────── */
export default function MatchDashboard({ data }) {
  const {
    match_score, score_breakdown = {}, skill_analysis = {},
    synonym_matches = [], competency_levels = [],
    interview_prep = [], skill_gaps_summary,
    experience_gap = null, skill_comparison = [],
    taxonomy = {}
  } = data;

  const metrics = [
    { label: "Skills match",       val: score_breakdown.skills_match    ?? 0, icon: "🎯" },
    { label: "Experience",         val: score_breakdown.experience_match ?? 0, icon: "⏳" },
    { label: "Education",          val: score_breakdown.education_match  ?? 0, icon: "🎓" },
    { label: "Keyword / Semantic", val: score_breakdown.keywords_match   ?? 0, icon: "🔍" },
  ];
  const matched = skill_analysis.matched || [];
  const weak    = skill_analysis.weak    || [];
  const missing = skill_analysis.missing || [];

  return (
    <div>

      {/* ── Top Stats ── */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-num" style={{ color: barColor(match_score) }}>{match_score}%</div>
          <div className="stat-lbl">Overall Match</div>
        </div>
        <div className="stat-card">
          <div className="stat-num" style={{ color: "#059669" }}>{matched.length}</div>
          <div className="stat-lbl">Skills Matched</div>
        </div>
        <div className="stat-card">
          <div className="stat-num" style={{ color: "#d97706" }}>{weak.length}</div>
          <div className="stat-lbl">Level Gaps</div>
        </div>
        <div className="stat-card">
          <div className="stat-num" style={{ color: "#dc2626" }}>{missing.length}</div>
          <div className="stat-lbl">Missing Skills</div>
        </div>
        <div className="stat-card">
          <div className="stat-num" style={{ color: "#4f46e5" }}>{skill_comparison.length}</div>
          <div className="stat-lbl">Skills Analyzed</div>
        </div>
      </div>

      {/* ── Score + Gap ── */}
      <div className="grid-2" style={{ alignItems: "flex-start" }}>
        {/* Left: score ring + breakdown */}
        <div className="card">
          <div className="card-title">Match Score Breakdown</div>
          <ScoreRing score={match_score} />
          {metrics.map(m => (
            <div key={m.label} className="metric-row">
              <span style={{ fontSize: 14 }}>{m.icon}</span>
              <span className="metric-label">{m.label}</span>
              <div className="metric-bar">
                <div className="metric-fill" style={{ width: `${m.val}%`, background: barColor(m.val) }} />
              </div>
              <span className="metric-val" style={{ color: barColor(m.val) }}>{m.val}%</span>
            </div>
          ))}
          {skill_gaps_summary && <div className="gap-summary">{skill_gaps_summary}</div>}
        </div>

        {/* Right: Skill gap visual */}
        <div className="card">
          <div className="card-title">Skill Gap Overview</div>
          <SkillGapVisual matched={matched} weak={weak} missing={missing} taxonomy={taxonomy} />
        </div>
      </div>

      {/* ── Experience Gap Banner ── */}
      {experience_gap && (
        <div className="exp-gap-banner">
          <span style={{ fontSize: 32 }}>⏱️</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 3 }}>Experience Gap Detected</div>
            <div style={{ fontSize: 13, opacity: 0.92 }}>
              This role requires <strong>{experience_gap.required_years}+ years</strong> of experience.
              Your resume shows <strong>{experience_gap.resume_years} year(s)</strong> —
              you are <strong>{experience_gap.shortfall_years} year(s) short</strong>.
            </div>
          </div>
        </div>
      )}

      {/* ── Implicit O*NET Gaps ── */}
      {taxonomy?.implicit_gaps && taxonomy.implicit_gaps.length > 0 && (
        <div className="card" style={{ background: "rgba(255,247,237,0.5)", borderColor: "#fed7aa" }}>
          <div className="card-title" style={{ color: "#c2410c", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>🕵️</span> 
            Hidden Requirements (O*NET Benchmark)
          </div>
          <div style={{ fontSize: 13, color: "#9a3412", marginBottom: 12 }}>
            Based on the detected occupation (<strong>{taxonomy.onet_occupation?.title}</strong>), 
            O*NET considers these skills critical, but they were not explicitly mentioned in the Job Description or your resume.
          </div>
          <div className="grid-auto">
            {taxonomy.implicit_gaps.map((g, i) => (
              <div key={i} className="skill-cmp-card" style={{ borderColor: "#fdba74", background: "#fff" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                  <span style={{ fontSize: 13.5, fontWeight: 700, color: "#9a3412" }}>{g.name}</span>
                  <span className="badge" style={{ background: "#ffedd5", color: "#c2410c", border: "1px solid #fed7aa" }}>
                    ⭐ {g.importance} / 5
                  </span>
                </div>
                <div style={{ fontSize: 11, color: "#78350f" }}>
                  <em>{g.reason}</em>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Skill Comparison Grid ── */}
      <div className="section-title">
        <div className="section-title-icon">📊</div>
        Required Skills vs. Your Proficiency
      </div>
      <div className="card">
        <SkillComparison skills={skill_comparison} />
      </div>

      {/* ── Competency ── */}
      {competency_levels.length > 0 && (
        <>
          <div className="section-title">
            <div className="section-title-icon">🧩</div>
            Competency Level Inference
          </div>
          <div className="card">
            <div className="comp-grid">
              {competency_levels.slice(0, 18).map(c => {
                const order = ["basic", "intermediate", "advanced"];
                const idx = order.indexOf(c.inferred_level);
                const cls = idx === 0 ? "on-basic" : idx === 1 ? "on-mid" : "on-adv";
                return (
                  <div key={c.skill} className="comp-row">
                    <span className="comp-name">{c.skill}</span>
                    <div className="level-dots">
                      {[0, 1, 2].map(i => (
                        <div key={i} className={`level-dot ${i <= idx ? cls : ""}`} />
                      ))}
                    </div>
                    <span className="level-lbl">{c.inferred_level}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* ── Synonym Matches ── */}
      {synonym_matches.length > 0 && (
        <>
          <div className="section-title">
            <div className="section-title-icon">🔗</div>
            Skill Paraphrase &amp; Synonym Matches
          </div>
          <div className="card">
            <div className="syn-grid">
              {synonym_matches.map((s, i) => (
                <div key={i} className="syn-pair">
                  <span className="syn-a">{s.resume_term}</span>
                  <span className="syn-arrow">↔</span>
                  <span className="syn-b">{s.jd_term}</span>
                  <span className="syn-rel">{s.relationship}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ── Interview Prep ── */}
      <div className="section-title">
        <div className="section-title-icon">🎤</div>
        Interview Prep Q&amp;A Coach
      </div>
      <div className="card" style={{ background: "rgba(239,246,255,0.6)", borderColor: "#c7d2fe" }}>
        <div style={{
          padding: "12px 16px", borderRadius: 10, marginBottom: 18,
          background: "linear-gradient(135deg, #eff6ff, #f5f3ff)",
          border: "1px solid #c7d2fe", fontSize: 13, color: "#312e81", lineHeight: 1.6,
          display: "flex", alignItems: "center", gap: 10
        }}>
          <span style={{ fontSize: 20 }}>💡</span>
          <span>
            <strong>{interview_prep.length} custom questions</strong> generated for your specific gaps.
            Click any question to reveal the answer strategy.
          </span>
        </div>
        <InterviewPrepSection initialQuestions={interview_prep} data={data} />
      </div>
    </div>
  );
}
