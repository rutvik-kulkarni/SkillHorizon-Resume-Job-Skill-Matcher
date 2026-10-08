import { useState } from "react";

/* ── Copy Button ──────────────────────────────────────────────────────── */
function CopyButton({ text, small = false }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(text); }
    catch { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); document.body.removeChild(t); }
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };
  return (
    <button onClick={handleCopy} style={{
      padding: small ? "4px 10px" : "7px 14px",
      borderRadius: 8, border: "1px solid",
      borderColor: copied ? "#6ee7b7" : "#e2e8f0",
      background: copied ? "#d1fae5" : "#f8fafc",
      color: copied ? "#065f46" : "#475569",
      fontSize: 12, fontWeight: 700, cursor: "pointer",
      display: "flex", alignItems: "center", gap: 5,
      transition: "all .2s", fontFamily: "inherit", whiteSpace: "nowrap"
    }}>
      {copied ? "✓ Copied!" : "⎘ Copy"}
    </button>
  );
}

/* ── Priority Badge ───────────────────────────────────────────────────── */
function PriorityBadge({ priority }) {
  const cfg = {
    High:   { bg: "#fee2e2", color: "#dc2626", icon: "🔴" },
    Medium: { bg: "#fef3c7", color: "#d97706", icon: "🟡" },
    Low:    { bg: "#d1fae5", color: "#059669", icon: "🟢" },
  }[priority] || { bg: "#f1f5f9", color: "#64748b", icon: "⚪" };
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      fontSize: 10, fontWeight: 800, padding: "2px 8px", borderRadius: 99,
      background: cfg.bg, color: cfg.color, textTransform: "uppercase", letterSpacing: "0.05em"
    }}>
      {cfg.icon} {priority}
    </span>
  );
}

/* ── Category Badge ───────────────────────────────────────────────────── */
function CategoryBadge({ category }) {
  const colors = {
    Quantification: { bg: "#ede9fe", color: "#6d28d9" },
    Keywords:       { bg: "#dbeafe", color: "#1d4ed8" },
    Phrasing:       { bg: "#fce7f3", color: "#9d174d" },
    Structure:      { bg: "#d1fae5", color: "#065f46" },
    Skills:         { bg: "#fef3c7", color: "#92400e" },
    Impact:         { bg: "#fee2e2", color: "#991b1b" },
  };
  const cfg = colors[category] || { bg: "#f1f5f9", color: "#475569" };
  return (
    <span style={{
      fontSize: 10, fontWeight: 800, padding: "2px 9px", borderRadius: 99,
      background: cfg.bg, color: cfg.color,
      textTransform: "uppercase", letterSpacing: "0.05em"
    }}>{category}</span>
  );
}

/* ── Resume Suggestion Card ───────────────────────────────────────────── */
function SuggestionCard({ item, index }) {
  const [open, setOpen] = useState(index < 2);
  return (
    <div style={{
      border: "1px solid var(--border)", borderRadius: "var(--radius)",
      overflow: "hidden", marginBottom: 10,
      background: "var(--surface-solid)",
      transition: "all .2s ease",
      boxShadow: open ? "var(--shadow)" : "var(--shadow-sm)"
    }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          padding: "14px 18px", cursor: "pointer",
          display: "flex", alignItems: "center", gap: 12,
          background: open ? "linear-gradient(135deg, #f8f4ff, #eff6ff)" : "var(--surface-solid)",
          transition: "background .2s"
        }}
      >
        <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <CategoryBadge category={item.category} />
          <span style={{ fontSize: 13.5, fontWeight: 700, color: "var(--text-primary)" }}>{item.title}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <PriorityBadge priority={item.priority} />
          <span style={{ fontSize: 13, color: "var(--text-muted)" }}>{open ? "▴" : "▾"}</span>
        </div>
      </div>

      {open && (
        <div style={{ padding: "16px 18px", borderTop: "1px solid var(--border)" }}>
          {/* Current state */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "#dc2626", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 5 }}>
              📍 Current Issue
            </div>
            <div style={{
              padding: "10px 14px", borderRadius: 8,
              background: "#fff5f5", border: "1px solid #fecaca",
              fontSize: 13, color: "#7f1d1d", lineHeight: 1.6
            }}>{item.current}</div>
          </div>

          {/* Suggestion */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "#059669", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 5 }}>
              ✅ How to Fix It
            </div>
            <div style={{
              padding: "10px 14px", borderRadius: 8,
              background: "#f0fdf4", border: "1px solid #bbf7d0",
              fontSize: 13, color: "#14532d", lineHeight: 1.6
            }}>{item.suggestion}</div>
          </div>

          {/* Example */}
          {item.example && (
            <div>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#4f46e5", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 5 }}>
                ✦ Improved Example
              </div>
              <div style={{
                padding: "10px 14px", borderRadius: 8,
                background: "linear-gradient(135deg, #f8f4ff, #eff6ff)",
                border: "1px solid #c4b5fd",
                fontSize: 13, color: "#3730a3", lineHeight: 1.65, fontStyle: "italic"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                  <span>"{item.example}"</span>
                  <CopyButton text={item.example} small />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── STAR Card ────────────────────────────────────────────────────────── */
const STAR_CFG = {
  S: { bg: "#ede9fe", color: "#6d28d9", border: "#c4b5fd", label: "Situation" },
  T: { bg: "#dbeafe", color: "#1d4ed8", border: "#bfdbfe", label: "Task" },
  A: { bg: "#d1fae5", color: "#065f46", border: "#6ee7b7", label: "Action" },
  R: { bg: "#fef9c3", color: "#854d0e", border: "#fde047", label: "Result" },
};

function StarCard({ item, index }) {
  const [expanded, setExpanded] = useState(index === 0);
  const steps = [
    { key: "S", text: item.situation },
    { key: "T", text: item.task },
    { key: "A", text: item.action },
    { key: "R", text: item.result },
  ];
  const isTemplate = !item.situation || item.situation.includes("critical gap");

  return (
    <div style={{
      border: isTemplate ? "1.5px dashed #cbd5e1" : "1px solid var(--border)",
      borderRadius: "var(--radius)", overflow: "hidden", marginBottom: 14,
      background: "var(--surface-solid)",
      boxShadow: isTemplate ? "none" : "var(--shadow-sm)",
      opacity: isTemplate ? 0.75 : 1,
      transition: "all .25s ease"
    }}>
      {/* Header */}
      <div
        onClick={() => setExpanded(e => !e)}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "14px 18px", cursor: "pointer",
          background: isTemplate
            ? "linear-gradient(135deg, #f1f5f9, #e2e8f0)"
            : "linear-gradient(135deg, #4f46e5, #7c3aed)",
          color: isTemplate ? "#64748b" : "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{
            fontSize: 10, fontWeight: 800, padding: "2px 9px", borderRadius: 99,
            textTransform: "uppercase", letterSpacing: "0.06em",
            background: isTemplate ? "#e2e8f0" : "rgba(255,255,255,0.22)",
          }}>Skill Gap</span>
          <span style={{ fontSize: 14.5, fontWeight: 700 }}>{item.gap_skill}</span>
          {isTemplate && (
            <span style={{ fontSize: 11, fontStyle: "italic", opacity: 0.7 }}>— generic template</span>
          )}
        </div>
        <span style={{ fontSize: 14, opacity: 0.8 }}>{expanded ? "▴" : "▾"}</span>
      </div>

      {expanded && (
        <div style={{ padding: "18px 20px" }}>
          {/* STAR grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
            {steps.map(({ key, text }) => {
              const cfg = STAR_CFG[key];
              return (
                <div key={key} style={{
                  padding: "12px 14px", borderRadius: 10,
                  background: cfg.bg, border: `1px solid ${cfg.border}`,
                }}>
                  <div style={{
                    fontSize: 10, fontWeight: 800, color: cfg.color,
                    textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 6
                  }}>{cfg.label}</div>
                  <div style={{ fontSize: 13, color: "#334155", lineHeight: 1.6 }}>{text}</div>
                </div>
              );
            })}
          </div>

          {/* Resume bullet */}
          <div style={{
            background: "linear-gradient(135deg, #f8f4ff, #eff6ff)",
            border: "1px solid #c4b5fd", borderRadius: 10, padding: "14px 16px",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 8 }}>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#7c3aed", textTransform: "uppercase", letterSpacing: ".08em" }}>
                ✦ Polished Resume Bullet
              </div>
              <CopyButton text={item.bullet_suggestion} small />
            </div>
            <div style={{ fontSize: 13.5, color: "#1e293b", lineHeight: 1.65, fontStyle: "italic" }}>
              "{item.bullet_suggestion}"
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────────────────── */
export default function ResumeImprover({ data }) {
  const stars = data?.star_improvements || [];
  const suggestions = data?.resume_suggestions || [];
  const aiPowered = data?.ai_powered ?? false;
  const [activeTab, setActiveTab] = useState("suggestions");

  if (!stars.length && !suggestions.length) return (
    <div className="card empty-state" style={{ padding: "4rem 2rem" }}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>📝</div>
      <div style={{ fontWeight: 700, color: "#374151", marginBottom: 6 }}>No improvement suggestions yet</div>
      <div style={{ fontSize: 13, color: "#9ca3af" }}>Run the analysis first — suggestions are generated from your skill gaps.</div>
    </div>
  );

  const highCount = suggestions.filter(s => s.priority === "High").length;

  return (
    <div>
      {/* Header Banner */}
      <div style={{
        background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
        borderRadius: "var(--radius-lg)", padding: "24px 28px", marginBottom: 24,
        color: "#fff", display: "flex", alignItems: "flex-start", gap: 18,
        boxShadow: "0 12px 40px rgba(79,70,229,0.35)"
      }}>
        <span style={{ fontSize: 38, lineHeight: 1 }}>🚀</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 6, letterSpacing: "-0.3px" }}>
            AI Resume Coach
            {aiPowered && (
              <span style={{ fontSize: 11, fontWeight: 700, marginLeft: 10, padding: "2px 9px", borderRadius: 99, background: "rgba(255,255,255,0.2)" }}>
                ✨ Gemini Powered
              </span>
            )}
          </div>
          <div style={{ fontSize: 13.5, opacity: 0.9, lineHeight: 1.65 }}>
            {aiPowered
              ? "Your resume has been analyzed against this specific job description. Each suggestion references your actual experience and the role's requirements."
              : "STAR-format resume bullets tailored to your skill gaps. Customize with your real metrics for best results."}
          </div>
          {suggestions.length > 0 && (
            <div style={{ marginTop: 12, display: "flex", gap: 12, flexWrap: "wrap" }}>
              <div style={{ background: "rgba(255,255,255,0.15)", borderRadius: 10, padding: "8px 14px", textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800 }}>{suggestions.length}</div>
                <div style={{ fontSize: 10, opacity: 0.8, textTransform: "uppercase" }}>Personalized Tips</div>
              </div>
              {highCount > 0 && (
                <div style={{ background: "rgba(239,68,68,0.25)", borderRadius: 10, padding: "8px 14px", textAlign: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 800 }}>{highCount}</div>
                  <div style={{ fontSize: 10, opacity: 0.8, textTransform: "uppercase" }}>High Priority</div>
                </div>
              )}
              <div style={{ background: "rgba(255,255,255,0.15)", borderRadius: 10, padding: "8px 14px", textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800 }}>{stars.length}</div>
                <div style={{ fontSize: 10, opacity: 0.8, textTransform: "uppercase" }}>STAR Bullets</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      {suggestions.length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          {[
            { id: "suggestions", label: "📋 Resume Suggestions", count: suggestions.length },
            { id: "bullets", label: "✦ STAR Bullets", count: stars.length },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "10px 18px", borderRadius: "var(--radius-sm)",
                border: activeTab === tab.id ? "1.5px solid #4f46e5" : "1.5px solid var(--border)",
                background: activeTab === tab.id ? "#eff6ff" : "var(--surface-solid)",
                color: activeTab === tab.id ? "#4f46e5" : "var(--text-secondary)",
                fontWeight: 700, fontSize: 13, cursor: "pointer",
                display: "flex", alignItems: "center", gap: 8,
                fontFamily: "inherit", transition: "all .18s"
              }}
            >
              {tab.label}
              <span style={{
                fontSize: 11, padding: "1px 7px", borderRadius: 99,
                background: activeTab === tab.id ? "#c7d2fe" : "#f1f5f9",
                color: activeTab === tab.id ? "#4338ca" : "var(--text-muted)",
                fontWeight: 800
              }}>{tab.count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Resume Suggestions Panel */}
      {(activeTab === "suggestions" && suggestions.length > 0) && (
        <div>
          <div style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "12px 16px", borderRadius: "var(--radius-sm)",
            background: "#fffbeb", border: "1px solid #fde68a",
            marginBottom: 16, fontSize: 13, color: "#92400e"
          }}>
            <span style={{ fontSize: 18 }}>💡</span>
            <span>These suggestions are <strong>personalized to your resume</strong> and this specific job description. Apply the high-priority ones first.</span>
          </div>
          {suggestions.map((s, i) => <SuggestionCard key={i} item={s} index={i} />)}
        </div>
      )}

      {/* STAR Bullets Panel */}
      {(activeTab === "bullets" || suggestions.length === 0) && (
        <div>
          {!aiPowered && (
            <div style={{
              padding: "12px 16px", borderRadius: "var(--radius-sm)",
              background: "#fffbeb", border: "1px solid #fde68a",
              fontSize: 13, color: "#92400e", marginBottom: 16, lineHeight: 1.6
            }}>
              <strong>💡 Pro tip:</strong> These are template stories. Replace the placeholder metrics with your real numbers — team size, latency reduction %, cost saved, etc. Quantified bullets are 3× more likely to get noticed by recruiters.
            </div>
          )}
          {aiPowered && (
            <div style={{
              padding: "12px 16px", borderRadius: "var(--radius-sm)",
              background: "#eff6ff", border: "1px solid #bfdbfe",
              fontSize: 13, color: "#1e40af", marginBottom: 16, lineHeight: 1.6
            }}>
              <strong>✨ AI-generated:</strong> These STAR bullets are tailored to your background and the target role. Still review and personalize with your actual numbers before use.
            </div>
          )}
          {stars.map((s, i) => <StarCard key={i} item={s} index={i} />)}
        </div>
      )}

      {/* Pro tip footer */}
      <div style={{
        marginTop: 20, padding: "14px 18px", borderRadius: 10,
        background: "#f8f4ff", border: "1px solid #c4b5fd",
        fontSize: 13, color: "#6d28d9", lineHeight: 1.65
      }}>
        <strong>🎯 Action Plan:</strong> Apply high-priority suggestions to your resume before you apply. Paste each STAR bullet into the relevant experience section, then customize with your real project metrics to make it uniquely yours.
      </div>
    </div>
  );
}
