"""
esco_onet.py — Hybrid Taxonomy Integration Module
=================================================
Provides:
  - ESCO skill normalization (EU Skills Taxonomy, free public API)
  - O*NET occupation lookup + standard skill requirements (US Labor Dept, free API with credentials)
  - SQLite-backed persistent caching to avoid repeated API calls
  - Graceful fallback when APIs are unavailable
"""

import sqlite3
import json
import os
import time
import re
from pathlib import Path
from typing import Optional

try:
    import requests as _requests
    _HTTP_AVAILABLE = True
except ImportError:
    _HTTP_AVAILABLE = False
    print("[TAXONOMY] 'requests' not installed — ESCO/O*NET lookups disabled")

_CACHE_DB = Path(__file__).parent / "taxonomy_cache.db"
_ESCO_BASE = "https://esco.ec.europa.eu/api"
_ONET_BASE = "https://services.onetcenter.org/ws"

# O*NET credentials from .env (optional)
_ONET_USER = os.getenv("ONET_USERNAME", "")
_ONET_PASS = os.getenv("ONET_PASSWORD", "")

# ---------------------------------------------------------------------------
# SQLite Cache Setup
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_CACHE_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS esco_skills (
            term        TEXT PRIMARY KEY,
            uri         TEXT,
            pref_label  TEXT,
            alt_labels  TEXT,
            broader     TEXT,
            fetched_at  INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS esco_occupations (
            job_title   TEXT PRIMARY KEY,
            uri         TEXT,
            pref_label  TEXT,
            isco_group  TEXT,
            fetched_at  INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS onet_occupations (
            job_title    TEXT PRIMARY KEY,
            onet_code    TEXT,
            title        TEXT,
            skills_json  TEXT,
            tasks_json   TEXT,
            fetched_at   INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def _cache_fresh(fetched_at: int, max_age_days: int = 30) -> bool:
    """Return True if cached value was fetched within max_age_days."""
    return (time.time() - fetched_at) < (max_age_days * 86400)


# ---------------------------------------------------------------------------
# ESCO Skill Normalization
# ---------------------------------------------------------------------------

def normalize_skill_esco(term: str) -> dict:
    """
    Map a raw skill string to its ESCO canonical URI + labels.
    Returns a dict with keys: term, esco_uri, preferred_label, alt_labels, from_cache.
    Returns the term unchanged if ESCO lookup fails.
    """
    key = term.strip().lower()
    if not key:
        return _empty_esco(term)

    # Check cache first
    try:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM esco_skills WHERE term = ?", (key,)).fetchone()
        if row and _cache_fresh(row["fetched_at"]):
            return {
                "term": term,
                "esco_uri": row["uri"],
                "preferred_label": row["pref_label"] or term,
                "alt_labels": json.loads(row["alt_labels"] or "[]"),
                "broader": row["broader"] or "",
                "from_cache": True
            }
        conn.close()
    except Exception:
        pass

    if not _HTTP_AVAILABLE:
        return _empty_esco(term)

    try:
        resp = _requests.get(
            f"{_ESCO_BASE}/search",
            params={"language": "en", "type": "skill", "text": key, "offset": 0, "limit": 3},
            timeout=6,
            headers={"Accept": "application/json"}
        )
        if not resp.ok:
            return _empty_esco(term)

        data = resp.json()
        results = data.get("_embedded", {}).get("results", [])
        if not results:
            _cache_esco_miss(key)
            return _empty_esco(term)

        top = results[0]
        uri = top.get("uri", "")
        pref = top.get("preferredLabel", {})
        if isinstance(pref, dict):
            pref = pref.get("en", term)
        elif not isinstance(pref, str):
            pref = term

        alts = top.get("altLabels", {})
        if isinstance(alts, dict):
            alts = alts.get("en", [])
        if isinstance(alts, str):
            alts = [alts]

        _cache_esco_skill(key, uri, pref, alts)
        return {
            "term": term,
            "esco_uri": uri,
            "preferred_label": pref,
            "alt_labels": alts if isinstance(alts, list) else [],
            "broader": "",
            "from_cache": False
        }
    except Exception as e:
        print(f"[ESCO] Error normalizing '{term}': {e}")
        return _empty_esco(term)


def _empty_esco(term: str) -> dict:
    return {"term": term, "esco_uri": None, "preferred_label": term, "alt_labels": [], "broader": "", "from_cache": False}


def _cache_esco_skill(key, uri, pref, alts):
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO esco_skills (term, uri, pref_label, alt_labels, broader, fetched_at) VALUES (?,?,?,?,?,?)",
            (key, uri, pref, json.dumps(alts), "", int(time.time()))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _cache_esco_miss(key):
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO esco_skills (term, uri, pref_label, alt_labels, broader, fetched_at) VALUES (?,?,?,?,?,?)",
            (key, "", key, "[]", "", int(time.time()))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ESCO Occupation Lookup
# ---------------------------------------------------------------------------

def find_esco_occupation(job_title: str) -> dict:
    """
    Map a job title string to its ESCO occupation classification.
    Returns uri, preferred_label, isco_group.
    """
    key = job_title.strip().lower()[:200]
    if not key:
        return {"uri": None, "preferred_label": job_title, "isco_group": ""}

    try:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM esco_occupations WHERE job_title = ?", (key,)).fetchone()
        if row and _cache_fresh(row["fetched_at"]):
            return {
                "uri": row["uri"],
                "preferred_label": row["pref_label"] or job_title,
                "isco_group": row["isco_group"] or "",
                "from_cache": True
            }
        conn.close()
    except Exception:
        pass

    if not _HTTP_AVAILABLE:
        return {"uri": None, "preferred_label": job_title, "isco_group": ""}

    try:
        resp = _requests.get(
            f"{_ESCO_BASE}/search",
            params={"language": "en", "type": "occupation", "text": key, "offset": 0, "limit": 3},
            timeout=6,
            headers={"Accept": "application/json"}
        )
        if not resp.ok:
            return {"uri": None, "preferred_label": job_title, "isco_group": ""}

        data = resp.json()
        results = data.get("_embedded", {}).get("results", [])
        if not results:
            return {"uri": None, "preferred_label": job_title, "isco_group": ""}

        top = results[0]
        uri = top.get("uri", "")
        pref = top.get("preferredLabel", {})
        if isinstance(pref, dict):
            pref = pref.get("en", job_title)
        isco = top.get("iscoGroup", {})
        if isinstance(isco, dict):
            isco = isco.get("preferredLabel", {}).get("en", "")

        try:
            conn = _get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO esco_occupations (job_title, uri, pref_label, isco_group, fetched_at) VALUES (?,?,?,?,?)",
                (key, uri, pref, isco, int(time.time()))
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return {"uri": uri, "preferred_label": pref, "isco_group": isco, "from_cache": False}
    except Exception as e:
        print(f"[ESCO] Error finding occupation '{job_title}': {e}")
        return {"uri": None, "preferred_label": job_title, "isco_group": ""}


# ---------------------------------------------------------------------------
# O*NET Occupation + Skills Lookup
# ---------------------------------------------------------------------------

def get_onet_occupation_skills(job_title: str) -> dict:
    """
    Look up a job title in O*NET and return the standard skill requirements
    with importance/level scores.
    Requires ONET_USERNAME and ONET_PASSWORD in .env.
    Returns empty result gracefully if credentials are not set.
    """
    if not _ONET_USER or not _ONET_PASS:
        return {
            "onet_code": None,
            "title": job_title,
            "standard_skills": [],
            "knowledge_areas": [],
            "configured": False
        }

    key = job_title.strip().lower()[:200]

    # Check cache
    try:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM onet_occupations WHERE job_title = ?", (key,)).fetchone()
        if row and _cache_fresh(row["fetched_at"]):
            return {
                "onet_code": row["onet_code"],
                "title": row["title"] or job_title,
                "standard_skills": json.loads(row["skills_json"] or "[]"),
                "knowledge_areas": json.loads(row["tasks_json"] or "[]"),
                "configured": True,
                "from_cache": True
            }
        conn.close()
    except Exception:
        pass

    if not _HTTP_AVAILABLE:
        return {"onet_code": None, "title": job_title, "standard_skills": [], "knowledge_areas": [], "configured": True}

    auth = (_ONET_USER, _ONET_PASS)
    headers = {"Accept": "application/json"}

    try:
        # 1. Search for the occupation
        search_resp = _requests.get(
            f"{_ONET_BASE}/search",
            params={"keyword": job_title, "client": "true"},
            auth=auth, headers=headers, timeout=8
        )
        if not search_resp.ok:
            return {"onet_code": None, "title": job_title, "standard_skills": [], "knowledge_areas": [], "configured": True}

        occupations = search_resp.json().get("occupation", [])
        if not occupations:
            return {"onet_code": None, "title": job_title, "standard_skills": [], "knowledge_areas": [], "configured": True}

        top = occupations[0]
        code = top.get("code", "")
        title = top.get("title", job_title)

        # 2. Get skills for the occupation
        skills_resp = _requests.get(
            f"{_ONET_BASE}/online/occupations/{code}/summary/skills",
            auth=auth, headers=headers, timeout=8
        )
        standard_skills = []
        if skills_resp.ok:
            for el in skills_resp.json().get("element", []):
                name = el.get("name", "")
                score = el.get("score", {})
                standard_skills.append({
                    "name": name,
                    "importance": round(float(score.get("value", 0)), 1),
                    "level": round(float(score.get("level", 0)), 1)
                })

        # 3. Get knowledge areas
        know_resp = _requests.get(
            f"{_ONET_BASE}/online/occupations/{code}/summary/knowledge",
            auth=auth, headers=headers, timeout=8
        )
        knowledge = []
        if know_resp.ok:
            for el in know_resp.json().get("element", []):
                name = el.get("name", "")
                score = el.get("score", {})
                knowledge.append({
                    "name": name,
                    "importance": round(float(score.get("value", 0)), 1),
                })

        # Cache results
        try:
            conn = _get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO onet_occupations (job_title, onet_code, title, skills_json, tasks_json, fetched_at) VALUES (?,?,?,?,?,?)",
                (key, code, title, json.dumps(standard_skills), json.dumps(knowledge), int(time.time()))
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return {
            "onet_code": code,
            "title": title,
            "standard_skills": standard_skills,
            "knowledge_areas": knowledge,
            "configured": True,
            "from_cache": False
        }

    except Exception as e:
        print(f"[ONET] Error fetching occupation skills for '{job_title}': {e}")
        return {"onet_code": None, "title": job_title, "standard_skills": [], "knowledge_areas": [], "configured": True}


# ---------------------------------------------------------------------------
# Batch skill normalization (for a list)
# ---------------------------------------------------------------------------

def batch_normalize_skills(skills: list, max_skills: int = 20) -> dict:
    """
    Normalize a list of skill strings through ESCO.
    Returns a dict: {raw_term: esco_result}
    Limits to max_skills to avoid rate limiting.
    """
    results = {}
    for skill in skills[:max_skills]:
        term = skill.get("skill", skill) if isinstance(skill, dict) else str(skill)
        results[term] = normalize_skill_esco(term)
        time.sleep(0.05)  # Small delay to be respectful to ESCO servers
    return results


# ---------------------------------------------------------------------------
# Compute implicit gaps from O*NET
# ---------------------------------------------------------------------------

def compute_implicit_gaps(onet_data: dict, resume_skills: list, jd_skills: list) -> list:
    """
    Find skills that O*NET considers important for this occupation but that
    are NOT explicitly mentioned in the resume OR the job description.
    These are the 'hidden' gaps — skills a good hiring manager would assume.
    """
    if not onet_data.get("standard_skills"):
        return []

    all_known = set()
    for s in resume_skills:
        t = s.get("skill", s) if isinstance(s, dict) else str(s)
        all_known.add(t.lower())
    for s in jd_skills:
        t = s.lower() if isinstance(s, str) else s.get("skill", "").lower()
        all_known.add(t)

    implicit = []
    for onet_skill in onet_data["standard_skills"]:
        name = onet_skill.get("name", "")
        importance = onet_skill.get("importance", 0)

        if importance < 3.5:  # Only surface highly important skills
            continue

        # Check if this skill is already known (fuzzy match)
        name_lower = name.lower()
        already_covered = False
        for known in all_known:
            # Simple substring overlap check
            if known in name_lower or name_lower in known or (
                len(known) > 4 and any(w in name_lower.split() for w in known.split())
            ):
                already_covered = True
                break

        if not already_covered:
            implicit.append({
                "name": name,
                "importance": importance,
                "level": onet_skill.get("level", 0),
                "source": "onet",
                "onet_code": onet_data.get("onet_code"),
                "occupation_title": onet_data.get("title", ""),
                "reason": f"Standard requirement for {onet_data.get('title', 'this occupation')} per O*NET (importance: {importance}/5)"
            })

    # Sort by importance descending, return top 10
    implicit.sort(key=lambda x: x["importance"], reverse=True)
    return implicit[:10]
