import { useState } from "react";

const LEVELS = ["foundational", "intermediate", "advanced"];
const LEVEL_LABEL = { foundational: "Start here", intermediate: "Build depth", advanced: "Reach mastery" };
const ICONS = { Coursera: "📚", Udemy: "🎓", edX: "🏛", "LinkedIn Learning": "💼",
                YouTube: "▶", Google: "🔍", "AWS Training": "☁" };

export default function LearningPath({ data, missingSkills }) {
  const [costFilter, setCostFilter]     = useState("all");
  const [platFilter, setPlatFilter]     = useState("all");

  const lp = data?.learning_path || {};
  const all = LEVELS.flatMap(lvl => (lp[lvl] || []).map(c => ({ ...c, level: lvl })));
  const platforms = ["all", ...new Set(all.map(c => c.platform))];

  const visible = all.filter(c => {
    if (costFilter === "free" && !c.free) return false;
    if (costFilter === "paid" && c.free)  return false;
    if (platFilter !== "all" && c.platform !== platFilter) return false;
    return true;
  });

  if (all.length === 0) return (
    <div className="card empty-state">
      No courses found. Ensure the backend knowledge graph has entries for your gap skills:
      {missingSkills?.length ? <p style={{ marginTop: 8, fontSize: 12 }}>{missingSkills.join(", ")}</p> : null}
    </div>
  );

  return (
    <div>
      <div className="alert alert-info">
        Personalized learning path for <strong>{missingSkills?.length ?? 0}</strong> gap skill(s).
        Ordered: foundational → intermediate → advanced.
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: "1rem" }}>
        <div>
          <span style={{ fontSize: 12, color: "#888", marginRight: 8 }}>Cost:</span>
          {["all","free","paid"].map(f => (
            <button key={f} style={{ marginRight: 4 }}
              className={`filter-btn ${costFilter === f ? "active" : ""}`}
              onClick={() => setCostFilter(f)}>
              {f === "all" ? "All" : f === "free" ? "Free only" : "Paid"}
            </button>
          ))}
        </div>
        <div>
          <span style={{ fontSize: 12, color: "#888", marginRight: 8 }}>Platform:</span>
          {platforms.map(p => (
            <button key={p} style={{ marginRight: 4 }}
              className={`filter-btn ${platFilter === p ? "active" : ""}`}
              onClick={() => setPlatFilter(p)}>
              {p === "all" ? "All" : p}
            </button>
          ))}
        </div>
      </div>

      {LEVELS.map(lvl => {
        const items = visible.filter(c => c.level === lvl);
        if (!items.length) return null;
        return (
          <div key={lvl}>
            <div className="level-header">
              <span className={`level-badge level-${lvl}`}>{lvl}</span>
              <span className="level-title">{LEVEL_LABEL[lvl]}</span>
              <span className="level-count">{items.length} course{items.length !== 1 ? "s" : ""}</span>
            </div>
            {items.map((c, i) => {
              const icon  = ICONS[c.platform] || "📖";
              const iconBg = c.free ? "#e8f5e9" : "#e3f2fd";
              return (
                <div key={i} className="course-card">
                  <div className="course-icon" style={{ background: iconBg }}>{icon}</div>
                  <div className="course-meta">
                    <div className="course-title">{c.title}</div>
                    <div className="course-desc">{c.description}</div>
                    <div className="course-tags">
                      <span className={`tag tag-${c.free ? "free" : "paid"}`}>{c.free ? "Free" : "Paid"}</span>
                      <span className="tag tag-neutral">{c.platform}</span>
                      <span className="tag tag-neutral">{c.duration}</span>
                      {c.skill && <span className="tag tag-neutral">For: {c.skill}</span>}
                    </div>
                  </div>
                  <a href={c.url || "#"} target="_blank" rel="noopener noreferrer" className="course-link">View →</a>
                </div>
              );
            })}
          </div>
        );
      })}

      {visible.length === 0 && <div className="empty-state">No courses match the selected filters.</div>}
    </div>
  );
}
