import time
import re
from duckduckgo_search import DDGS

# ---------------------------------------------------------------------------
# Platform registry — domain fragment → (display name, free_by_default)
# ---------------------------------------------------------------------------
PLATFORMS = {
    "udemy.com":                    ("Udemy",              False),
    "coursera.org":                 ("Coursera",           False),
    "edx.org":                      ("edX",                False),
    "youtube.com/watch":            ("YouTube",            True),
    "youtu.be":                     ("YouTube",            True),
    "linkedin.com/learning":        ("LinkedIn Learning",  False),
    "skillsbuild.org":              ("IBM SkillsBuild",    True),
    "nptel.ac.in":                  ("NPTEL",              True),
    "onlinecourses.nptel.ac.in":    ("NPTEL",              True),
    "freecodecamp.org":             ("freeCodeCamp",       True),
    "ocw.mit.edu":                  ("MIT OpenCourseWare", True),
    "learn.google":                 ("Google",             True),
    "developers.google.com":        ("Google",             True),
    "cloud.google.com/learn":       ("Google",             True),
    "pluralsight.com":              ("Pluralsight",        False),
    "datacamp.com":                 ("DataCamp",           False),
    "udacity.com":                  ("Udacity",            False),
    "codecademy.com":               ("Codecademy",         False),
    "educative.io":                 ("Educative",          False),
    "khanacademy.org":              ("Khan Academy",       True),
    "skillshare.com":               ("Skillshare",         False),
    "simplilearn.com":              ("Simplilearn",        False),
    "alison.com":                   ("Alison",             True),
    "mygreatlearning.com":          ("Great Learning",     True),
}

# Site lists for targeted search query (split to avoid very long queries)
_PLATFORM_DOMAINS = list(set(d.split('/')[0] for d in PLATFORMS.keys()))
_SITE_LIST_1 = " OR ".join(f"site:{d}" for d in _PLATFORM_DOMAINS[:10])
_SITE_LIST_2 = " OR ".join(f"site:{d}" for d in _PLATFORM_DOMAINS[10:])


def _classify(url: str):
    """Return (platform_name, free) for a URL, or (None, None) if unknown."""
    url_lower = url.lower()
    for domain, (name, free) in PLATFORMS.items():
        if domain in url_lower:
            return name, free
    return None, None


def _infer_level(title: str) -> str:
    t = title.lower()
    if any(kw in t for kw in ["beginner", "intro", "introduction", "foundation",
                               "basics", "101", "start", "getting started", "fundamentals"]):
        return "foundational"
    if any(kw in t for kw in ["advanced", "masterclass", "expert",
                               "deep dive", "professional", "mastery"]):
        return "advanced"
    return "intermediate"


def _build_course(res: dict, platform: str, free: bool, skill: str) -> dict:
    title = res.get("title", "")
    snippet = res.get("body", "")
    level = _infer_level(title)
    duration_hours = 5 if level == "foundational" else (20 if level == "advanced" else 10)
    clean_title = re.sub(
        r"(\s*[-|]\s*(Coursera|Udemy|edX|IBM SkillsBuild|NPTEL|YouTube|LinkedIn Learning"
        r"|freeCodeCamp|MIT OpenCourseWare|Google|Online Courses|Free Online)).*$",
        "", title, flags=re.IGNORECASE,
    ).strip()
    return {
        "title": (clean_title[:70] + "...") if len(clean_title) > 70 else clean_title,
        "platform": platform,
        "url": res.get("href", ""),
        "duration": f"{duration_hours} hours",
        "duration_hours": duration_hours,
        "free": free,
        "level": level,
        "description": (snippet[:150] + "...") if len(snippet) > 150 else snippet,
    }


def scrape_courses_for_skill(skill: str) -> list:
    """
    Fetches courses from 20+ edtech platforms using DuckDuckGo search.
    Multiple query passes are run for better coverage and to avoid long query limits.
    """
    queries = [
        # Pass 1 — targeted site search part 1
        f'"{skill}" course tutorial ({_SITE_LIST_1})',
        # Pass 2 — targeted site search part 2
        f'"{skill}" course tutorial ({_SITE_LIST_2})',
        # Pass 3 — broader phrasing to catch edge cases
        f'learn "{skill}" online course free site:youtube.com OR site:freecodecamp.org OR site:coursera.org',
    ]

    seen_urls: set = set()
    results: list = []

    try:
        with DDGS() as ddgs:
            for query in queries:
                time.sleep(0.8)  # polite rate-limit
                try:
                    search_results = list(ddgs.text(query, max_results=12))
                except Exception as inner_e:
                    print(f"[Scraper] Query failed for '{skill}': {inner_e}")
                    continue

                for res in search_results:
                    url = res.get("href", "")
                    if not url or url in seen_urls:
                        continue
                    platform, free = _classify(url)
                    if platform is None:
                        continue
                    seen_urls.add(url)
                    results.append(_build_course(res, platform, free, skill))

                # Stop early if we already have enough results
                if len(results) >= 10:
                    break

    except Exception as e:
        print(f"[Scraper] Error scraping courses for '{skill}': {e}")

    return results
