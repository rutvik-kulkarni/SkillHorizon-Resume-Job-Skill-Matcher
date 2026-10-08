"""
NLP Pipeline — Resume Match & Learning Path Recommender

Features:
  - Resume & JD parsing (rule-based NER + regex)
  - Semantic similarity (sentence-transformers or TF-IDF fallback)
  - Skill gap detection with synonym/paraphrase matching
  - Competency-level inference from resume bullet context
  - Bias detection (rule-based)
  - STAR-style improvement suggestions
  - Course / learning-path recommendations
"""

import re
import math
import os
import json
from typing import Optional
from dotenv import load_dotenv

from knowledge_graph import COURSE_KG
from course_scraper import scrape_courses_for_skill
from rapidfuzz import fuzz
import esco_onet

load_dotenv()
try:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        _LLM_ENABLED = True
    else:
        _LLM_ENABLED = False
except ImportError:
    _LLM_ENABLED = False

# ---------------------------------------------------------------------------
# Optional: sentence-transformers for real semantic embeddings.
# Falls back to TF-IDF cosine similarity if not installed.
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    # Try loading JobBERT (jjzha/jobbert-base-cased) or CareerBERT (lwolfrum2/careerbert-jg) for career matching
    try:
        _MODEL = SentenceTransformer("jjzha/jobbert-base-cased")
        print("[NLP] Using JobBERT (jjzha/jobbert-base-cased) for domain-specific matching")
    except Exception:
        try:
            _MODEL = SentenceTransformer("lwolfrum2/careerbert-jg")
            print("[NLP] Using CareerBERT (lwolfrum2/careerbert-jg) for domain-specific matching")
        except Exception:
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            print("[NLP] Using sentence-transformers fallback (all-MiniLM-L6-v2)")
    USE_EMBEDDINGS = True
except ImportError:
    USE_EMBEDDINGS = False
    print("[NLP] sentence-transformers not installed -> using TF-IDF cosine similarity")


# ---------------------------------------------------------------------------
# Skill vocabulary
# ---------------------------------------------------------------------------
TECH_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "ruby", "golang", "go", "rust",
    "c++", "c#", "php", "kotlin", "swift", "scala", "r", "matlab", "perl", "bash",
    "powershell", "shell", "dart", "elixir", "clojure", "haskell", "objective-c",
    "fortran", "cobol", "sql", "pl/sql", "t-sql",
    # Frontend
    "react", "angular", "vue", "svelte", "solidjs", "solid.js", "ember", "jquery",
    "bootstrap", "tailwind", "tailwindcss", "material ui", "mui", "next.js", "nextjs",
    "nuxt.js", "nuxtjs", "gatsby", "redux", "mobx", "zustand", "recoil", "vite",
    "webpack", "babel", "gulp", "grunt", "npm", "yarn", "pnpm", "sass", "css", "html",
    # Backend / Frameworks
    "express", "nodejs", "node.js", "django", "flask", "fastapi", "spring", "spring boot",
    "rails", "ruby on rails", "laravel", "symfony", "codeigniter", "nest.js", "nestjs",
    "koa", "hapi", "asp.net", "net core", "fastify",
    # Databases & Caching
    "postgresql", "postgres", "mysql", "sqlite", "oracle", "sql server", "mssql",
    "mongodb", "redis", "memcached", "elasticsearch", "cassandra", "dynamodb",
    "mariadb", "firebase", "firestore", "supabase", "prisma", "sequelize", "mongoose",
    "hibernate", "neo4j", "influxdb", "couchdb",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "google cloud platform",
    "terraform", "ansible", "jenkins", "kubernetes", "k8s", "docker", "docker compose",
    "github actions", "gitlab ci", "circleci", "travis ci", "ci/cd", "continuous integration",
    "continuous deployment", "argocd", "helm", "istio", "prometheus", "grafana",
    "elk stack", "splunk", "datadog", "nginx", "apache", "caddy", "linux", "unix",
    "ubuntu", "debian", "centos", "redhat", "aws lambda", "serverless", "cloudformation",
    "ec2", "s3", "rds", "route 53", "iam",
    # AI / ML / CV
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "cv", "image recognition", "object detection",
    "image segmentation", "image processing", "opencv", "yolo",
    "convolutional neural network", "cnn", "transformer", "bert", "llm",
    "generative ai", "stable diffusion", "diffusion model",
    "tensorflow", "keras", "pytorch", "scikit-learn", "sklearn", "pandas", "numpy",
    "hugging face", "langchain", "llamaindex", "rag", "vector database", "pinecone",
    "chromadb", "milvus", "qdrant", "weaviate", "gpt", "large language models",
    # Data & Streaming
    "spark", "kafka", "rabbitmq", "activemq", "sqs", "sns", "hadoop", "flink",
    "hive", "dbt", "airflow", "apache airflow", "presto", "snowflake", "bigquery",
    "redshift",
    # Testing & QA
    "jest", "cypress", "playwright", "selenium", "puppeteer", "mocha", "chai",
    "junit", "pytest", "testing library", "postman", "supertest", "k6", "jmeter",
    # Mobile
    "react native", "flutter", "swiftui", "kotlin multiplatform", "xamarin", "ionic",
    "cordova",
    # System Design & Architecture
    "microservices", "service mesh", "rest", "restful", "rest api", "graphql", "grpc",
    "soap", "trpc", "websockets", "socket.io", "web3", "solidity", "ethers.js",
    "system design", "design patterns", "mvc", "mvvm", "event-driven architecture",
    # Others & Tools
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "trello", "slack",
    "agile", "scrum", "kanban", "figma", "sketch", "adobe xd", "swagger", "openapi",
    "eslint", "prettier", "embedded systems", "rtos", "arduino", "raspberry pi",
    "fpga", "ros", "data structures", "algorithms", "data engineering", "data science",
    "statistics", "linear algebra", "calculus"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "time management", "adaptability",
    "collaboration", "mentoring", "project management",
]

COMPETENCY_SIGNALS = {
    "advanced": [
        "expert", "expert-level", "senior", "lead", "architect", "designed",
        "optimized", "scaled", "built from scratch", "deep", "extensive",
    ],
    "intermediate": [
        "developed", "implemented", "built", "managed", "worked with",
        "experience with", "proficient", "solid", "good knowledge",
    ],
    "basic": [
        "familiar", "basic", "exposure", "learning", "some experience",
        "introduced", "beginner", "junior", "coursework",
    ],
}

EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s*[-–]\s*\d+\s*years?\s+(?:of\s+)?(?:work\s+)?experience",  # "2-3 years experience" → take lower
    r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:work\s+)?experience",
    r"minimum\s+(?:of\s+)?(\d+)\s*years?",
    r"at\s+least\s+(\d+)\s*years?",
    r"(\d+)\+?\s*yrs",
]

EDU_MAP = {
    "phd": 3, "ph.d": 3, "doctorate": 3,
    "master": 2, "m.sc": 2, "m.tech": 2, "mba": 2, "m.s.": 2,
    "bachelor": 1, "b.sc": 1, "b.tech": 1, "b.s.": 1, "undergraduate": 1,
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _tfidf_cosine(a: str, b: str) -> float:
    """Lightweight TF-IDF cosine similarity (no dependencies)."""
    def tf(text):
        words = re.findall(r"[a-z][a-z0-9]*", text.lower())
        d: dict = {}
        for w in words:
            d[w] = d.get(w, 0) + 1
        return d

    va, vb = tf(a), tf(b)
    vocab = set(va) | set(vb)
    dot = sum(va.get(w, 0) * vb.get(w, 0) for w in vocab)
    mag_a = math.sqrt(sum(v ** 2 for v in va.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vb.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _semantic_sim(a: str, b: str) -> float:
    if USE_EMBEDDINGS:
        ea = _MODEL.encode(a, convert_to_tensor=True)
        eb = _MODEL.encode(b, convert_to_tensor=True)
        return float(st_util.cos_sim(ea, eb)[0][0])
    return _tfidf_cosine(a, b)


SYNONYM_MAP = {
    "aws": {"amazon web services", "aws cloud", "amazon cloud"},
    "gcp": {"google cloud", "google cloud platform", "gcp cloud"},
    "k8s": {"kubernetes", "k8s cluster"},
    "ci/cd": {"continuous integration", "continuous delivery", "continuous deployment", "cicd", "ci-cd", "ci/cd pipeline", "ci/cd pipelines"},
    "js": {"javascript"},
    "ts": {"typescript"},
    "c#": {"csharp", "c sharp"},
    "c++": {"cpp", "c plus plus"},
    "db": {"database", "databases"},
    "ml": {"machine learning"},
    "dl": {"deep learning"},
    "nlp": {"natural language processing"},
    "cv": {"computer vision"},
    "qa": {"quality assurance", "testing", "software testing"},
    "rest": {"restful", "rest api", "rest apis", "restful api", "restful apis"},
    "docker": {"docker container", "docker containers", "dockerization", "dockerised", "dockerized"},
    "next.js": {"nextjs", "next.js framework"},
    "react": {"reactjs", "react.js", "react framework"},
    "node.js": {"nodejs", "node.js runtime", "node"},
    "vue": {"vuejs", "vue.js", "vue framework"},
    "angular": {"angularjs", "angular.js"},
    "ror": {"ruby on rails", "rails"},
}

def _are_synonyms(a: str, b: str) -> bool:
    a_lower, b_lower = a.lower(), b.lower()
    if a_lower == b_lower:
        return True
    for key, synonyms in SYNONYM_MAP.items():
        all_syns = {key} | synonyms
        if a_lower in all_syns and b_lower in all_syns:
            return True
    return False

def _is_valid_skill_context(skill: str, text: str) -> bool:
    skill_lower = skill.lower()
    text_lower = text.lower()
    
    if skill_lower not in ["go", "r", "c", "rest", "swift", "spring", "agile", "run", "git"]:
        return True
        
    if skill_lower == "go":
        if "golang" in text_lower:
            return True
        matches = list(re.finditer(r"\bGo\b", text))
        for m in matches:
            start, end = m.span()
            post_context = text[end:end+15].strip().lower()
            if not any(post_context.startswith(w) for w in ["to ", "through", "out", "on", "in", "for", "with", "ahead", "back", "away"]):
                return True
        return False
        
    if skill_lower == "r":
        if not re.search(r"\b[rR]\b", text):
            return False
        if any(w in text_lower for w in ["python", "sql", "pandas", "numpy", "statistics", "data science", "r programming", "r language", "r-programming"]):
            return True
        return False
        
    if skill_lower == "c":
        if not re.search(r"\bC\b", text):
            return False
        if any(w in text_lower for w in ["c++", "c#", "java", "python", "assembly", "c programming", "c language", "embedded", "gcc", "clang"]):
            return True
        return False
        
    if skill_lower == "rest":
        return any(w in text_lower for w in ["restful", "rest api", "rest apis", "rest web", "representational state transfer"])
        
    if skill_lower == "swift":
        if "swiftui" in text_lower or "swift programming" in text_lower or "apple swift" in text_lower:
            return True
        if re.search(r"\bSwift\b", text) and any(w in text_lower for w in ["ios", "xcode", "objective-c", "cocoa", "macos", "app store"]):
            return True
        return False
        
    if skill_lower == "spring":
        if any(w in text_lower for w in ["spring boot", "spring framework", "spring mvc", "spring security", "spring data", "spring cloud"]):
            return True
        if re.search(r"\bSpring\b", text) and "java" in text_lower:
            return True
        return False

    if skill_lower == "git":
        return re.search(r"\b[gG]it\b", text) is not None

    return True

def _is_standalone_skill(skill: str, text: str) -> bool:
    skill_lower = skill.lower()
    text_lower = text.lower()
    skill_len = len(skill_lower)
    text_len = len(text_lower)
    
    start = 0
    while True:
        pos = text_lower.find(skill_lower, start)
        if pos == -1:
            return False
            
        # Check character before
        before_ok = True
        if pos > 0:
            char_before = text_lower[pos - 1]
            if char_before.isalnum() or char_before in {'+', '#', '.', '/', '-'}:
                before_ok = False
                
        # Check character after
        after_ok = True
        if pos + skill_len < text_len:
            char_after = text_lower[pos + skill_len]
            if char_after.isalnum() or char_after in {'+', '#', '.', '/', '-'}:
                after_ok = False
                
        if before_ok and after_ok:
            return True
            
        start = pos + 1

# Extended exclusion set — words that are NEVER valid skills
_DYNAMIC_SKILL_EXCLUSIONS = {
    # Pronouns / articles / conjunctions
    "we","you","our","us","they","them","he","she","it","his","her","their",
    "this","that","these","those","here","there","when","where","why","how",
    "what","who","which","whose","whom","then","once","first","second","third",
    "last","next","each","every","some","any","no","not","only","own","same",
    "both","either","neither","also","too","very","much","more","most","less",
    "least","few","many","other","another","such","than","as","like","so",
    "just","even","still","yet","already","never","always","often","sometimes",
    "about","above","across","after","against","along","amid","among","around",
    "at","before","behind","below","beneath","beside","between","beyond","but",
    "by","concerning","considering","despite","down","during","except","for",
    "from","in","inside","into","minus","near","of","off","on","onto",
    "opposite","out","outside","over","past","per","plus","regarding","since",
    "through","throughout","till","to","toward","towards","under","underneath",
    "unlike","until","up","upon","versus","via","with","within","without",
    # Days / months
    "monday","tuesday","wednesday","thursday","friday","saturday","sunday",
    "january","february","march","april","may","june","july","august","september",
    "october","november","december",
    # Geography — countries, cities, states, regions (common false positives)
    "london","new york","san francisco","california","texas","india","mumbai","delhi",
    "bangalore","bengaluru","hyderabad","chennai","pune","kolkata","ahmedabad",
    "romania","bulgaria","poland","ukraine","germany","france","canada",
    "australia","brazil","china","japan","korea","singapore","dubai","uae",
    "usa","united states","united kingdom","uk","europe","asia","africa",
    "new","york","san","francisco","angeles","chicago","boston","seattle",
    "remote","onsite","hybrid","nationwide","worldwide","globally",
    # University / college / institution keywords that appear in resume headers
    "university","college","institute","institution","school","academy","faculty",
    "iit","nit","bits","mit","stanford","harvard","oxford","cambridge",
    "vit","srm","manipal","amity","lpu","du","mumbai university","pune university",
    "anna university","osmania","bhu","jnu","amu","upes",
    # Degree / education labels that look like proper nouns
    "bachelor","bachelors","b.tech","b.sc","b.e","b.com","bca","bba",
    "master","masters","m.tech","m.sc","m.e","mba","mca","m.s",
    "phd","ph.d","doctorate","diploma","associate","undergraduate","postgraduate",
    "gpa","cgpa","grade","grades","honors","honours","distinction",
    # Company type suffixes (often extracted near company names)
    "inc","ltd","llc","pvt","corp","co","solutions","technologies","systems",
    "services","labs","group","global","international","enterprises",
    # Contact / header info that leaks into resume text
    "linkedin","github","portfolio","website","email","phone","mobile","address",
    "http","https","www","com","org","net","io",
    # Common nouns that appear in JDs but are NOT skills
    "application","applications","project","projects","role","roles","team","teams",
    "candidate","candidates","resume","resumes","job","jobs","company","companies",
    "office","salary","benefits","contract","work","worker",
    "engineering","engineer","engineers","developer","developers","development",
    "manager","managers","management","leader","leaders","leadership",
    "architect","architects","architecture","designer","designers","design",
    "analyst","analysts","analysis","specialist","specialists","expertise",
    "experience","experiences","expert","experts","senior","junior","staff",
    "principal","director","vice","president","executive","officer","board",
    "member","members","client","clients","customer","customers","partner",
    "partners","vendor","vendors","stakeholder","stakeholders","user","users",
    "product","products","service","solution","platform","platforms",
    "tool","tools","technology","technologies","framework","frameworks",
    "library","libraries","language","languages",
    "code","codes","coding","program","programs","programming","software",
    "hardware","infrastructure","data","database","databases","server","servers",
    "network","networks","networking","cloud","clouds","security","testing",
    "test","tests","quality","assurance","deployment","deployments","integration",
    "integrations","delivery","deliveries","release","releases","ops","operation",
    "operations","support","maintenance","troubleshooting","monitoring","analytics",
    "report","reports","reporting","dashboard","dashboards","metric","metrics",
    "key","performance","indicator","indicators","target","targets","goal","goals",
    "objective","objectives","strategy","strategies","strategic","tactical",
    "business","market","industry","industries","field","fields","domain","domains",
    "process","processes","method","methods","methodology","methodologies",
    "practice","practices","standard","standards","policy","policies","compliance",
    "audit","audits","risk","risks","control","controls","governance","legal",
    "education","training","course","courses","certification","certifications",
    "degree","degrees","diploma",
    "science","sciences","arts","humanities","mathematics","math","stats",
    "communication","collaborate","collaboration","teamwork","problem","solving",
    "decision","making","time","organization","organizational",
    "written","verbal","oral","presentation","presentations","writing","documentation",
    "requirement","requirements","qualification","qualifications","skill","skills",
    "ability","abilities","knowledge","understanding","competency","competencies",
    "capability","capabilities","capacity","potential","strength","strengths",
    "weakness","weaknesses","opportunity","opportunities","challenge","challenges",
    "success","successful","failure","fail","fails","failed","bug","bugs",
    "defect","defects","issue","issues","error","errors","incident","incidents",
    "event","events","log","logs","track","record",
    "strong","excellent","highly","interpersonal","proven","demonstrated",
    "fast-paced","environment",
    # Location-type words often in contact/address lines
    "street","avenue","road","lane","drive","place","block","sector","district",
    "state","country","city","town","village","zip","pincode","postal",
    # Verbs and action words — these are NOT skills
    "contribute","contributes","contributing","contributed","contributor","contributors",
    "build","builds","building","built","create","creates","creating","created",
    "develop","develops","developing","developed","implement","implements","implementing",
    "design","designs","designing","designed","deliver","delivers","delivering","delivered",
    "manage","manages","managing","managed","lead","leads","leading","led",
    "drive","drives","driving","drove","ensure","ensures","ensuring","ensured",
    "maintain","maintains","maintaining","maintained","improve","improves","improving",
    "collaborate","collaborates","collaborating","collaborated",
    "communicate","communicates","communicating","communicated",
    "identify","identifies","identifying","identified",
    "define","defines","defining","defined","support","supports","supporting",
    "use","uses","using","used","apply","applies","applying","applied",
    "work","works","working","worked","join","joins","joining","joined",
    "help","helps","helping","helped","provide","provides","providing","provided",
    "enable","enables","enabling","enabled","scale","scales","scaling","scaled",
    "own","owns","owning","owned","review","reviews","reviewing","reviewed",
    # Adjectives that appear in JDs but are NOT skills
    "individual","individuals","artificial","natural","general","specific","special",
    "critical","essential","important","relevant","required","preferred","desired",
    "additional","multiple","various","complex","large","small","high","low",
    "modern","current","latest","proven","demonstrated","strong","excellent",
    "robust","reliable","efficient","effective","innovative","dynamic","diverse",
    "local","internal","external","technical","non-technical","cross-functional",
    # Misc false positives from real JDs
    "date","dates","day","days","week","weeks","month","months","year","years",
    "cloud-scale","at-scale","large-scale","small-scale","full-stack","full-time","part-time",
    "open-source","end-to-end","day-to-day","real-time","up-to-date","hands-on",
    "well-versed","well-defined","well-documented","fast-paced","self-motivated",
    "detail-oriented","results-driven","team-player","team-oriented",
    # Hyphenated adjectives / adverbs that look like skills but aren't
    "real-world","well-tested","production-ready","state-of-the-art","cutting-edge",
    "cross-platform","high-performance","mission-critical","fault-tolerant",
    "open-ended","forward-thinking","industry-leading","best-in-class",
    # Common plain verbs that end up capitalized in JDs
    "train","trains","trained","write","writes","written","conduct","conducts","conducted",
    "deploy","deploys","deployed","overview","overviews","research","researches",
    "areas","area","looks","look","typical","deep","deeper","vision","visions",
    "fundamentals","fundamental","responsible","responsibility","responsibilities",
    "pipeline","pipelines","algebra","algebras","linear","distributed","conduct",
    "describe","describes","understand","understands",
    "demonstrate","demonstrates","model","models","feature","features",
    "dataset","datasets","benchmark","benchmarks",
    # Words that look like skills but are just nouns
    "intuition","intuitions","pattern","patterns","approach","approaches",
    "insight","insights","scenario","scenarios","workflow","workflows",
    "output","outputs","input","inputs","baseline","baselines","tradeoff","tradeoffs",
    "aspect","aspects","component","components","module","modules","layer","layers",
    "stage","stages","phase","phases","step","steps","loop","loops","node","nodes",
    "graph","graphs","edge","edges","vertex","vertices","point","points","space","spaces",
    "class","classes","instance","instances","object","objects","variable","variables",
    "function","functions","parameter","parameters","argument","arguments",
    "epoch","batch","iteration","iterations","convergence","gradient","gradients",
    # Generic descriptors often extracted from ML/AI JDs
    "mle","dsa","ml/dl","gpus/tpus","gputpus","generative",
    # Internship / work section header words
    "intern","internship","internships","trainee","apprentice","fellowship",
    "volunteer","freelance","contractor","part-time",
    # Personal info words common in resume headers
    "name","dob","gender","nationality","marital","status","language","languages",
    "hobbies","interests","objective","summary","profile","about",
}

def _is_valid_dynamic_skill(w: str) -> bool:
    common_exclusions = _DYNAMIC_SKILL_EXCLUSIONS
    # Also exclude words matching known JD filler patterns
    extra_exclusion_patterns = [
        r"^\d+$",                      # pure numbers
        r"^[a-z]{1,2}$",               # single/double lowercase letters
        r"ing$",                        # gerunds (building, working, etc.)
        r"tion$",                       # abstract nouns (integration, etc.)
        r"ment$",                       # abstract nouns (management, etc.)
        r"ness$",                       # abstract nouns
        r"ility$",                      # abstract nouns (scalability, etc.)
        r"ance$",                       # abstract nouns (compliance, etc.)
        r"ence$",                       # abstract nouns (experience, etc.)
        r"ship$",                       # abstract nouns (leadership, etc.)
        r"ware$",                       # software, hardware
        r"wide$",                       # company-wide etc.
    ]
    # Exceptions — known real skills that match the suffix patterns above
    _suffix_exceptions = {
        "spring", "golang", "nestjs", "kubernetes", "jenkins", "engineering",
        "programming", "testing", "networking", "monitoring", "reporting",
        "kafka", "flink", "databricks", "databricks", "snowflake",
    }
    w_clean = w.strip(".,;:()[]{}'\"")
    w_lower = w_clean.lower()

    if len(w_clean) < 2:
        return False
    if not re.search(r"[a-zA-Z]", w_clean):
        return False
    if w_lower in common_exclusions:
        return False
    # Apply suffix exclusion patterns (unless it's a known exception)
    if w_lower not in _suffix_exceptions:
        for pat in extra_exclusion_patterns:
            if re.search(pat, w_lower):
                return False

    # Heuristics for tech/specialized terms:
    # 1. Contains special skill chars (e.g. C++, C#, Node.js, CI/CD)
    if any(c in w_clean for c in ['+', '#', '.', '/']):
        return True
    # Hyphenated: only allow if BOTH parts are non-trivial (e.g. scikit-learn, well-NOT)
    if '-' in w_clean:
        parts = w_clean.split('-')
        if all(len(p) >= 3 and p.lower() not in common_exclusions for p in parts):
            return True
        return False

    # 2. Mixed case (e.g. NestJS, PyTorch, MongoDB)
    if re.search(r"[a-z]+[A-Z]+", w_clean) or re.search(r"[A-Z]+[a-z]+[A-Z]+", w_clean):
        return True

    # 3. All uppercase 2-6 chars (acronyms like AWS, GCP, REST, SQL)
    if w_clean.isupper() and 2 <= len(w_clean) <= 6:
        return True

    # 4. Capitalized word >= 4 chars that passes suffix filters (e.g. Docker, Django, Redis)
    if w_clean[0].isupper() and w_clean[1:].islower() and len(w_clean) >= 4:
        return True

    return False

def _extract_dynamic_skills(jd_text: str) -> list:
    words = re.findall(r"\b[a-zA-Z0-9+#/.-]+\b", jd_text)
    candidates = set()
    for w in words:
        if _is_valid_dynamic_skill(w):
            candidates.add(w.strip(".,;:()[]{}'\"")
    )
    # Capture capitalized two-word phrases (e.g. "Google Cloud", "Deep Learning")
    phrases = re.findall(r"\b([A-Z][a-zA-Z0-9+#/.-]{2,}\s+[A-Z][a-zA-Z0-9+#/.-]{2,})\b", jd_text)
    for p in phrases:
        parts = p.split()
        if all(_is_valid_dynamic_skill(part) for part in parts):
            candidates.add(p.strip())

    return list(candidates)

def _extract_skills(text: str, custom_vocabulary: list = None) -> list:
    text_lower = text.lower()
    found = []
    
    # Extract words/n-grams from clean text (preserving +, #, /, .)
    words = re.findall(r"\b[a-z0-9+#/.⁃-]+\b", text_lower)
    
    ngrams = []
    n = len(words)
    for i in range(n):
        ngrams.append(words[i])
        if i < n - 1:
            ngrams.append(f"{words[i]} {words[i+1]}")
        if i < n - 2:
            ngrams.append(f"{words[i]} {words[i+1]} {words[i+2]}")
            
    ngrams = list(set(ngrams))
    
    vocab = list(TECH_SKILLS + SOFT_SKILLS)
    if custom_vocabulary:
        for cv in custom_vocabulary:
            if cv.lower() not in [v.lower() for v in vocab]:
                vocab.append(cv)
    
    for skill in vocab:
        skill_lower = skill.lower()
        
        # 1. Standalone exact match check
        if _is_standalone_skill(skill_lower, text_lower):
            if _is_valid_skill_context(skill, text):
                found.append(skill)
            continue
            
        # 2. Fuzzy match fallback
        if len(skill_lower) > 4:
            best_score = 0
            for ngram in ngrams:
                # Manual alias alignments
                if skill_lower == "ci/cd" and ngram in ["ci-cd", "cicd", "ci/cd"]:
                    best_score = 100
                    break
                if skill_lower == "c++" and ngram in ["cpp", "cplusplus"]:
                    best_score = 100
                    break
                if skill_lower == "c#" and ngram in ["csharp", "c-sharp"]:
                    best_score = 100
                    break
                if skill_lower == "node.js" and ngram in ["nodejs", "node"]:
                    best_score = 100
                    break
                if skill_lower == "devops" and ngram in ["dev ops", "dev-ops"]:
                    best_score = 100
                    break
                if skill_lower == "next.js" and ngram in ["nextjs"]:
                    best_score = 100
                    break
                
                score = fuzz.ratio(skill_lower, ngram)
                if score > best_score:
                    best_score = score

            threshold = 85
            if best_score >= threshold:
                if _is_valid_skill_context(skill, text):
                    found.append(skill)
            
    return list(set(found))


def _extract_years(text: str) -> int:
    years = []
    for pat in EXPERIENCE_PATTERNS:
        for m in re.finditer(pat, text.lower()):
            years.append(int(m.group(1)))
    return max(years) if years else 0


def _extract_education(text: str) -> str:
    text_lower = text.lower()
    best = 0
    label = "Not specified"
    for kw, level in EDU_MAP.items():
        if kw in text_lower and level > best:
            best = level
            label = {1: "Bachelor's degree", 2: "Master's degree", 3: "PhD"}[level]
    return label


def _infer_competency(skill: str, text: str) -> str:
    sentences = [s for s in re.split(r"[.\n]", text.lower()) if skill.lower() in s]
    context = " ".join(sentences)
    for level in ("advanced", "intermediate", "basic"):
        if any(kw in context for kw in COMPETENCY_SIGNALS[level]):
            return level
    if re.search(r"\d\+?\s*years?", context):
        return "intermediate"
    return "basic"


def _find_synonyms(resume_skills: list, jd_skills: list) -> list:
    matches = []
    seen = set()
    for rs in resume_skills:
        for js in jd_skills:
            if rs.lower() == js.lower():
                continue
            pair = tuple(sorted([rs.lower(), js.lower()]))
            if pair in seen:
                continue

            # 1. Check explicit synonym map first
            if _are_synonyms(rs, js):
                seen.add(pair)
                matches.append({"resume_term": rs, "jd_term": js, "relationship": "mapped alias"})
                continue

            # 2. General fallback for longer terms
            if len(rs) <= 3 or len(js) <= 3:
                continue

            lexical_score = fuzz.WRatio(rs.lower(), js.lower())
            semantic_score = _semantic_sim(rs.lower(), js.lower()) * 100

            if lexical_score > 90 or semantic_score > 82:
                seen.add(pair)
                rel_type = "lexical synonym" if lexical_score > 90 else "semantic match"
                matches.append({"resume_term": rs, "jd_term": js, "relationship": rel_type})
    return matches


_INTERVIEW_TECH_LIBRARY = {
    "azure": {
        "question": "How would you design a highly available and secure application using Azure services? What key components would you use?",
        "hint": "Discuss Azure App Service / AKS for hosting, Azure SQL / Cosmos DB for data, Azure Active Directory for auth, Azure CDN, and Azure Monitor for observability. Mention ARM templates or Bicep for IaC."
    },
    "azure storage": {
        "question": "Explain the difference between Azure Blob Storage, Table Storage, Queue Storage, and File Storage. When would you choose each?",
        "hint": "Blob = unstructured data (images/videos); Table = NoSQL key-value; Queue = async message passing; File = SMB-compatible shared drive. Mention tiers (Hot/Cool/Archive) and lifecycle management policies."
    },
    "docker": {
        "question": "What are multi-stage Docker builds and how do they reduce image size in production?",
        "hint": "Explain using a build stage (heavy SDK image) and a runtime stage (slim/alpine), copying only the compiled artifact. Mention layer caching strategies and .dockerignore to speed up builds."
    },
    "terraform": {
        "question": "What is Terraform state, and how do you manage it safely in a team environment?",
        "hint": "Explain remote backends (S3 + DynamoDB locking), state file encryption, workspace isolation for environments, and preventing drift with automated plan-on-PR CI checks."
    },
    "microservices": {
        "question": "What are the key challenges of a microservices architecture and how do you handle distributed transactions?",
        "hint": "Cover service discovery, network latency, data consistency (Saga pattern vs 2PC), circuit breakers (Resilience4j/Hystrix), and observability with distributed tracing (Jaeger/Zipkin)."
    },
    "mongodb": {
        "question": "When would you choose MongoDB over a relational database? How do you handle data consistency in MongoDB?",
        "hint": "Discuss schema flexibility, horizontal scaling (sharding), denormalization trade-offs. Cover write concerns, read preferences, and transactions (multi-document ACID since v4.0)."
    },
    "redis": {
        "question": "Describe a caching strategy using Redis. How do you handle cache invalidation and thundering herd problems?",
        "hint": "Discuss TTL-based expiry, cache-aside vs write-through patterns. For thundering herd: use mutex/lock on cache miss, or probabilistic early expiration. Mention Redis Cluster for scale."
    },
    "machine learning": {
        "question": "Walk through the full ML model lifecycle — from data collection to production monitoring. What can go wrong at each stage?",
        "hint": "Cover data quality/bias, feature engineering, train/val/test splits, hyperparameter tuning, model versioning (MLflow), serving (REST API / batch), and monitoring for data drift and model degradation."
    },
    "python": {
        "question": "Explain Python's GIL and when you would use multiprocessing vs multithreading vs asyncio.",
        "hint": "GIL limits true CPU parallelism for threads. Use threading for I/O-bound (network calls), multiprocessing for CPU-bound tasks, and asyncio for high-concurrency I/O (web scraping, APIs) with minimal overhead."
    },
    "react": {
        "question": "How do you optimize a React application that is experiencing slow renders and poor performance?",
        "hint": "Profile with React DevTools. Use React.memo, useMemo, useCallback to prevent unnecessary re-renders. Implement code-splitting (React.lazy + Suspense), virtualization (react-window) for long lists, and avoid prop drilling with context."
    },
    "node.js": {
        "question": "How does Node.js handle concurrency given it is single-threaded? What are its limitations for CPU-intensive tasks?",
        "hint": "Explain the event loop, libuv, and async I/O. CPU-heavy tasks block the loop — offload to Worker Threads or child_process. Cluster module to use all CPU cores. Mention when to choose Go/Rust instead."
    },
    "postgresql": {
        "question": "How would you diagnose and fix a slow PostgreSQL query that is running against a large table?",
        "hint": "Use EXPLAIN ANALYZE to check seq scans vs index scans. Add composite indexes matching query predicates. Check for N+1 patterns, missing vacuums, lock contention. Consider partitioning for very large tables."
    },
    "system design": {
        "question": "Design a URL shortening service like bit.ly that handles 1 billion URLs and 100k requests/second.",
        "hint": "Cover: hash generation (Base62 + collision handling), distributed ID generation (Snowflake), read-heavy caching (Redis), DB sharding strategy, CDN for redirect latency, and analytics pipeline."
    },
    "kafka": {
        "question": "How does Kafka ensure message durability and at-least-once vs exactly-once delivery semantics?",
        "hint": "Discuss replication factor, ISR (In-Sync Replicas), producer acks (0/1/all), consumer offset commits, idempotent producers, and transactional APIs for exactly-once. Contrast with RabbitMQ."
    },

    "aws": {
        "question": "How would you design a scalable, secure, and fault-tolerant multi-tier web application on AWS?",
        "hint": "Mention AWS VPC, public/private subnets, Auto Scaling Groups (ASG), Application Load Balancers (ALB), Multi-AZ RDS for databases, and S3 for assets."
    },
    "kubernetes": {
        "question": "Explain the lifecycle of a Kubernetes Pod and how you would configure rolling updates without downtime.",
        "hint": "Discuss Pod states, readiness and liveness probes, deployment strategy 'RollingUpdate', and configuring maxSurge and maxUnavailable to ensure seamless handoffs."
    },
    "ci/cd": {
        "question": "What are the key stages of a robust CI/CD pipeline, and how do you ensure security vulnerabilities are caught before merging code?",
        "hint": "Explain Build, Test, Static Analysis (SAST), Dependency Scanning, Dockerize, and Deploy stages. Mention tools like GitHub Actions, SonarQube, Snyk, and automated container scanning."
    },
    "graphql": {
        "question": "How does GraphQL handle the 'N+1 query problem', and what strategy would you implement to solve it?",
        "hint": "Discuss how GraphQL executes resolvers independently. Explain using a batching and caching utility like DataLoader to consolidate database queries."
    },
    "typescript": {
        "question": "What are the advantages of TypeScript interfaces and generics, and how do you handle API response validation at runtime?",
        "hint": "Explain how interfaces define structure and generics enable reusable types. Since TS types are erased at runtime, discuss using schemas like Zod or Yup to validate API boundaries."
    },
    "security": {
        "question": "Describe the OWASP Top 10 vulnerabilities and explain how you prevent SQL Injection and Cross-Site Scripting (XSS) in a web application.",
        "hint": "Detail SQL Injection (use parameterized queries/ORMs) and XSS (sanitize/escape user inputs, implement Content Security Policy headers). Mention secure JWT handling."
    },
    "communication": {
        "question": "Describe a scenario where you had to explain a complex technical decision to non-technical stakeholders. How did you structure your communication?",
        "hint": "Use the STAR format. Explain how you focused on business value, trade-offs, and outcomes (costs/speeds) rather than raw implementation details, using analogies."
    },
    "devops": {
        "question": "What is 'Infrastructure as Code' (IaC) and how does Terraform manage state files securely in a collaborative team setting?",
        "hint": "Discuss how IaC treats infra config as code. Explain storing Terraform state files in a remote backend (e.g. AWS S3) with state locking (e.g. DynamoDB) to prevent concurrent changes."
    }
}

def _generate_interview_questions(resume_text: str, jd_text: str, missing_skills: list, weak_skills: list, experience_gap: dict, count: int = 5) -> list:
    all_gaps = list(set(missing_skills + [w["skill"] for w in weak_skills]))
    
    # Extract role name from JD (first non-blank line often has the title)
    job_title_line = next((l.strip() for l in jd_text.splitlines() if l.strip()), "this role")
    job_title = job_title_line[:120]

    if _LLM_ENABLED:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
You are a senior hiring manager conducting a technical interview for the following role:
"{job_title}"

The candidate's background (from their resume):
{resume_text[:1500] if resume_text else "Not provided"}

The candidate's SKILL GAPS (missing or below required level): {all_gaps}
Experience Gap: {experience_gap if experience_gap else 'None'}

Generate {count} targeted, role-specific interview questions that:
1. Are directly relevant to the specific job role and its real-world responsibilities
2. Probe the candidate's skill gaps in a way that reveals depth of knowledge
3. Mix technical depth questions with situational/behavioral questions
4. Reference realistic scenarios a person in this role would face day-to-day
5. Are NOT generic — they should feel like they come from someone who actually works in this field

For each question, provide a detailed "hint" with a specific, structured answer strategy including any relevant frameworks, tools, or numbers the candidate should mention.

Return ONLY a valid JSON array:
[
  {{
    "category": "Technical (SkillName) OR Role-Specific OR Behavioral OR System Design",
    "question": "The specific interview question",
    "hint": "Detailed answer strategy with specific technical details, frameworks, and metrics to mention"
  }}
]

Output raw JSON only. No markdown code fences.
"""
            response = model.generate_content(prompt)
            text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            questions = json.loads(text)
            return questions[:count]
        except Exception as e:
            print(f"[LLM] Error generating questions, falling back to static library: {e}")


    # Fallback to static library
    questions = []
    
    # 1. Experience Gap question if applicable
    if experience_gap:
        req = experience_gap.get("required_years", 3)
        res = experience_gap.get("resume_years", 1)
        questions.append({
            "category": "Experience Gap",
            "question": f"The job description specifies a preference for {req}+ years of experience, but your resume highlights {res} year(s). How would you address the question: 'You seem slightly junior for this position based on your years of experience'?",
            "hint": "Pivot the conversation from time-based metrics to impact. Highlight specific complex projects you owned, your fast learning curve, and how your current skills directly align with the core challenges the team faces."
        })
        
    # 2. Technical questions for missing / weak skills
    added_tech_count = 0
    for skill in all_gaps:
        key = skill.lower().replace(".", "").replace("+", "plus").replace("#", "sharp").replace(" ", "")
        lib_entry = next((v for k, v in _INTERVIEW_TECH_LIBRARY.items() if k in key or key in k), None)
        if lib_entry:
            questions.append({
                "category": f"Technical ({skill.title()})",
                "question": lib_entry["question"],
                "hint": lib_entry["hint"]
            })
            added_tech_count += 1
        if added_tech_count >= max(0, count - len(questions) - 1):
            break
            
    # If we have too few technical questions, add a generic one
    if added_tech_count < max(1, count - 2) and all_gaps:
        skill = all_gaps[0]
        questions.append({
            "category": f"Technical ({skill.title()})",
            "question": f"In your past work, what was the most challenging engineering issue you faced when working with {skill}, and how did you diagnose and fix it?",
            "hint": "Structure your answer using the STAR method: describe the system context, the performance metric or bug, your diagnostic steps (logs, profiling, experiments), and the final quantitative resolution (e.g., latency reduction, bug-free deploy)."
        })
        
    # 3. Behavioral question
    if len(questions) < count:
        questions.append({
            "category": "Behavioral",
            "question": "Can you describe a time when you had to work on a feature with highly ambiguous or shifting requirements? How did you ensure success?",
            "hint": "Focus on your adaptability, collaborative communication with product owners, iterative MVP prototyping, and how you managed scope creep to deliver on time."
        })
    
    return questions[:count]

def generate_more_interview_questions(resume_text: str, jd_text: str, missing_skills: list, weak_skills: list, experience_gap: dict, count: int = 3, existing_questions: list = None) -> list:
    all_gaps = list(set(missing_skills + [w["skill"] for w in weak_skills]))
    existing_qs = existing_questions or []
    existing_qs_text = "\n".join([q.get("question", "") for q in existing_qs])

    if _LLM_ENABLED:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            You are an expert technical interviewer. Generate {count} MORE tailored interview questions to probe a candidate's skill gaps.
            They have already been asked the following questions, DO NOT repeat them:
            {existing_qs_text}
            
            Candidate's Skill Gaps: {all_gaps}
            Experience Gap: {experience_gap if experience_gap else 'None'}
            
            Return ONLY a valid JSON array of objects with the following schema:
            [
              {{
                "category": "e.g., Technical (Skill Name), Experience Gap, or Behavioral",
                "question": "The interview question",
                "hint": "Detailed strategy or answer hint"
              }}
            ]
            
            Do not include any markdown formatting like ```json, just output the raw JSON array.
            """
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            questions = json.loads(text.strip())
            return questions[:count]
        except Exception as e:
            print(f"[LLM] Error generating more questions: {e}")
            return []
    
    # Fallback if no LLM: return a variety of behavioral questions, avoiding duplicates
    _BEHAVIORAL_POOL = [
        {"category": "Behavioral", "question": "Tell me about a time you made a significant mistake at work. How did you handle it?", "hint": "Focus on ownership and learning. Describe the mistake honestly, explain how you fixed it, and what systems you put in place to ensure it never happens again."},
        {"category": "Behavioral", "question": "Describe a situation where you had to quickly learn a new technology to complete a project. What was your approach?", "hint": "Emphasize your structured learning strategy, the resources you used, how you applied the learning in practice, and the timeline from zero knowledge to productive output."},
        {"category": "Behavioral", "question": "Tell me about a time you disagreed with a technical decision made by your team. What did you do?", "hint": "Show that you can advocate for your ideas respectfully using data and logic, accept decisions gracefully, and commit to the team's direction even when you disagree."},
        {"category": "Behavioral", "question": "Describe a project where you had to deliver under tight time constraints. How did you prioritize?", "hint": "Explain your triage process: MoSCoW method or similar. Show how you cut scope without compromising core value, and how you communicated trade-offs to stakeholders."},
        {"category": "Behavioral", "question": "Give an example of when you proactively identified a problem before it became critical. What did you do?", "hint": "Demonstrate technical intuition and initiative. Explain the signals you noticed, the investigation you conducted, and the proactive steps you took to prevent an incident."},
        {"category": "Behavioral", "question": "How have you helped onboard or mentor a junior team member?", "hint": "Show leadership and communication skills. Describe the specific guidance you provided, how you made yourself approachable, and the measurable improvement in the new member's productivity."},
        {"category": "Behavioral", "question": "Tell me about a time you had to work with a difficult stakeholder or cross-functional team. How did you handle it?", "hint": "Focus on empathy and communication. Describe how you found common ground, aligned on priorities, and built trust to move the project forward despite friction."},
    ]
    existing_qs_text_set = {q.get("question", "").strip().lower() for q in existing_qs}
    novel = [q for q in _BEHAVIORAL_POOL if q["question"].strip().lower() not in existing_qs_text_set]
    return novel[:count] if novel else []


# ---------------------------------------------------------------------------
# Experience / Internship extraction
# ---------------------------------------------------------------------------

# Patterns that mark the start of a work/experience/internship section
_EXP_SECTION_HEADERS = re.compile(
    r"^\s*(?:work\s+)?experience|internship|employment\s+history|"
    r"professional\s+experience|work\s+history|career\s+history|positions?\s+held",
    re.IGNORECASE | re.MULTILINE
)

# Date range patterns used to detect experience entries
_DATE_RANGE_PAT = re.compile(
    r"(?:"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}"  # Mar 2022
    r"|\d{4}"  # bare year
    r")"
    r"(?:\s*[-–—]\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|present|current|now|\d{4}))?",
    re.IGNORECASE
)

_INTERN_KEYWORDS = re.compile(
    r"\b(intern|internship|trainee|apprentice|co-op|coop|fellowship)\b",
    re.IGNORECASE
)


def _extract_experience_sections(text: str) -> list:
    """
    Parse structured work/internship entries from a resume.
    Returns a list of dicts with keys:
      - role, company, date_range, duration_months, is_internship, bullets, skills_mentioned
    """
    lines = text.split("\n")
    entries = []
    in_exp_section = False
    current_entry = None
    exp_skills_vocab = list(TECH_SKILLS + SOFT_SKILLS)

    def _flush(entry):
        if entry and (entry.get("role") or entry.get("company")):
            # Extract skills mentioned in this entry's bullets
            bullet_text = " ".join(entry.get("bullets", []))
            entry["skills_mentioned"] = _extract_skills(bullet_text)
            # Estimate duration from date range string
            entry["duration_months"] = _estimate_duration_months(entry.get("date_range", ""))
            entries.append(entry)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect section header
        if _EXP_SECTION_HEADERS.match(stripped):
            _flush(current_entry)
            current_entry = None
            in_exp_section = True
            continue

        # Stop at other major section headers (education, skills, projects, etc.)
        if re.match(
            r"^\s*(?:education|skills|technical\s+skills|projects?|certifications?|awards?|"
            r"publications?|references?|languages?|hobbies|interests|summary|objective|profile)",
            stripped, re.IGNORECASE
        ) and len(stripped) < 60:
            if in_exp_section:
                _flush(current_entry)
                current_entry = None
                in_exp_section = False
            continue

        if not in_exp_section:
            continue

        # Detect a new role line: has a date range OR looks like "Role — Company"
        date_match = _DATE_RANGE_PAT.search(stripped)
        role_company_match = re.search(r"[-–—|@]\s*", stripped)

        if date_match and len(stripped) < 120:
            # Likely a new entry header line
            _flush(current_entry)
            date_range_str = date_match.group(0).strip()
            # Remove date part, split remainder on delimiters
            remainder = stripped[:date_match.start()].strip().rstrip("|-–—, ")
            parts = re.split(r"[-–—|@]", remainder, maxsplit=1)
            role = parts[0].strip() if parts else remainder
            company = parts[1].strip() if len(parts) > 1 else ""
            is_intern = bool(_INTERN_KEYWORDS.search(role) or _INTERN_KEYWORDS.search(company))
            current_entry = {
                "role": role,
                "company": company,
                "date_range": date_range_str,
                "is_internship": is_intern,
                "bullets": [],
                "skills_mentioned": [],
                "duration_months": 0,
            }
        elif current_entry is not None and re.match(r"^[-•*▪◦>]", stripped):
            # Bullet point under current entry
            current_entry["bullets"].append(stripped.lstrip("-•*▪◦> ").strip())
        elif current_entry is not None and stripped and not date_match:
            # Could be a continuation line for company name or role title
            if not current_entry["company"] and len(stripped) < 80:
                current_entry["company"] = stripped

    _flush(current_entry)
    return entries


def _estimate_duration_months(date_range: str) -> int:
    """Rough estimate of months from a date-range string like '2022 - 2024' or 'Jun 2021 - Dec 2021'."""
    if not date_range:
        return 0
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", date_range)
    if len(years) >= 2:
        return max(0, (int(years[-1]) - int(years[0])) * 12)
    if re.search(r"present|current|now", date_range, re.IGNORECASE) and years:
        import datetime
        return max(0, (datetime.datetime.now().year - int(years[0])) * 12)
    if len(years) == 1:
        # Single year — assume ~12 months
        return 12
    return 0


def _compute_experience_years_from_sections(sections: list) -> float:
    """
    Sum up experience from extracted sections.
    Internships count at 0.5× weight of full-time experience.
    """
    total_months = 0.0
    for s in sections:
        months = s.get("duration_months", 0) or 0
        if s.get("is_internship"):
            total_months += months * 0.5
        else:
            total_months += months
    return round(total_months / 12, 1)


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------

def parse_resume_text(text: str, custom_vocabulary: list = None) -> dict:
    skills = _extract_skills(text, custom_vocabulary=custom_vocabulary)
    competency_levels = [
        {
            "skill": s,
            "inferred_level": _infer_competency(s, text),
            "evidence": "inferred from resume context",
        }
        for s in skills[:16]
    ]
    certs = re.findall(r"(?:certified?|certification|certificate)[^\n]{0,80}", text, re.IGNORECASE)
    certs += re.findall(r"\b(?:AWS|GCP|Azure|PMP|CISSP|CKA|CPA|CFA)\s+\w+", text)
    projects = re.findall(r"(?:project|built|developed|created)[^\n]{0,100}", text, re.IGNORECASE)[:5]

    # Extract structured experience/internship sections
    experience_sections = _extract_experience_sections(text)
    internships = [e for e in experience_sections if e["is_internship"]]
    work_experience = [e for e in experience_sections if not e["is_internship"]]

    # Derive experience years: prefer regex-extracted number, supplement with section-based calc
    regex_years = _extract_years(text)
    section_years = _compute_experience_years_from_sections(experience_sections)
    # Use whichever is higher (regex captures stated years, sections capture implicit duration)
    effective_years = max(regex_years, section_years)

    return {
        "skills": skills,
        "experience_years": effective_years,
        "education": _extract_education(text),
        "certifications": list(set(c.strip() for c in certs))[:6],
        "projects": projects,
        "competency_levels": competency_levels,
        "experience_sections": work_experience[:8],
        "internships": internships[:6],
        "total_experience_entries": len(experience_sections),
    }


# ---------------------------------------------------------------------------
# JD parsing
# ---------------------------------------------------------------------------

def parse_jd_text(text: str, custom_vocabulary: list = None) -> dict:
    lower = text.lower()
    split_idx = -1
    for marker in ["nice to have", "nice-to-have", "preferred", "bonus", "plus if"]:
        idx = lower.find(marker)
        if idx != -1:
            split_idx = idx
            break

    required_text = text[:split_idx] if split_idx != -1 else text
    optional_text = text[split_idx:] if split_idx != -1 else ""

    required = _extract_skills(required_text, custom_vocabulary=custom_vocabulary)
    nice = [s for s in _extract_skills(optional_text, custom_vocabulary=custom_vocabulary) if s not in required] if optional_text else []

    return {
        "required_skills": required,
        "nice_to_have": nice,
        "experience_required_years": _extract_years(text),
        "education_required": _extract_education(text),
        "responsibilities": re.findall(r"[-•*]\s*(.+)", text)[:10],
    }


# ---------------------------------------------------------------------------
# Match computation
# ---------------------------------------------------------------------------

def compute_match(resume_text: str, jd_text: str) -> dict:
    # 1. Extract dynamic skills from JD first
    dynamic_skills = _extract_dynamic_skills(jd_text)

    # 2. Parse both texts using the dynamically expanded vocabulary
    rp = parse_resume_text(resume_text, custom_vocabulary=dynamic_skills)
    jp = parse_jd_text(jd_text, custom_vocabulary=dynamic_skills)

    r_skills = set(s.lower() for s in rp["skills"])
    j_skills = set(s.lower() for s in jp["required_skills"])
    nice_skills = set(s.lower() for s in jp["nice_to_have"])
    all_j_skills = j_skills | nice_skills

    synonym_matches = _find_synonyms(list(r_skills), list(all_j_skills))
    synonym_jd_terms = {m["jd_term"].lower() for m in synonym_matches}

    # Matched skills
    matched = []
    for s in j_skills:
        if s in r_skills:
            matched.append({"skill": s, "confidence": 95, "resume_term": s, "jd_term": s})
        elif s in synonym_jd_terms:
            r_term = next((m["resume_term"] for m in synonym_matches if m["jd_term"].lower() == s), s)
            matched.append({"skill": s, "confidence": 75, "resume_term": r_term, "jd_term": s})

    matched_set = {m["skill"] for m in matched}

    # Weak skills (present but below expected level)
    is_senior = bool(re.search(r"\b(senior|sr\.?|lead|principal|staff)\b", jd_text, re.I))
    jd_expected = "advanced" if is_senior else "intermediate"
    levels_order = ["basic", "intermediate", "advanced"]

    weak = []
    for s in j_skills & r_skills:
        lvl = _infer_competency(s, resume_text)
        if levels_order.index(lvl) < levels_order.index(jd_expected):
            weak.append({"skill": s, "resume_level": lvl, "jd_expected": jd_expected, "confidence": 70})

    # Missing skills (not on resume at all, not covered by synonym)
    weak_set = {w["skill"] for w in weak}
    missing = [s for s in j_skills if s not in matched_set and s not in weak_set]

    # Compilation of comparative skill analysis
    skill_comparison = []

    def get_candidate_level(skill_name):
        skill_name_lower = skill_name.lower()
        # Check matched
        for m in matched:
            if m["skill"].lower() == skill_name_lower:
                return _infer_competency(skill_name, resume_text)
        # Check weak
        for w in weak:
            if w["skill"].lower() == skill_name_lower:
                return w["resume_level"]
        return "none"

    for s in jp["required_skills"]:
        cand_level = get_candidate_level(s)
        skill_comparison.append({
            "skill": s,
            "required_status": "Required",
            "expected_level": jd_expected,
            "candidate_level": cand_level,
            "status": "matched" if cand_level != "none" and cand_level in ["intermediate", "advanced"] else ("weak" if cand_level != "none" else "missing")
        })

    for s in jp["nice_to_have"]:
        cand_level = get_candidate_level(s)
        skill_comparison.append({
            "skill": s,
            "required_status": "Preferred",
            "expected_level": "intermediate",
            "candidate_level": cand_level,
            "status": "matched" if cand_level != "none" else "missing"
        })

    # -----------------------------------------------------------------------
    # Experience gap — surface explicitly if resume falls short
    # Uses both regex-stated years AND structured section-based calculation
    # Internships count at 0.5× weight in section-based scoring
    # -----------------------------------------------------------------------
    r_exp = rp["experience_years"]  # already max(regex, section-based)
    j_exp = jp["experience_required_years"]

    # Also collect internship-specific info for display
    internship_count = len(rp.get("internships", []))
    internship_months = sum(
        e.get("duration_months", 0) or 0
        for e in rp.get("internships", [])
    )
    has_internships = internship_count > 0

    experience_gap = None
    if j_exp > 0 and r_exp < j_exp:
        shortfall = round(j_exp - r_exp, 1)
        intern_note = (
            f" ({internship_count} internship(s) totalling ~{internship_months // 12} yr(s) counted at 0.5×)"
            if has_internships else ""
        )
        experience_gap = {
            "required_years": j_exp,
            "resume_years": r_exp,
            "shortfall_years": shortfall,
            "internship_count": internship_count,
            "internship_months": internship_months,
            "message": (
                f"JD requires {j_exp}+ years of experience; "
                f"resume shows {r_exp} year(s){intern_note}. "
                f"You are {shortfall} year(s) short."
            ),
        }

    # Score breakdown
    skills_score = int(100 * len(matched) / max(len(j_skills), 1))

    if j_exp == 0:
        exp_score = 85
    elif r_exp >= j_exp:
        exp_score = 100
    elif r_exp >= j_exp - 1:
        exp_score = 78
    elif r_exp >= j_exp - 2:
        exp_score = 58
    else:
        exp_score = max(20, int(100 * r_exp / max(j_exp, 1)))

    edu_rank = {"Not specified": 0, "Bachelor's degree": 1, "Master's degree": 2, "PhD": 3}
    edu_score = (
        100
        if edu_rank.get(rp["education"], 0) >= edu_rank.get(jp["education_required"], 0)
        else max(40, int(100 * edu_rank.get(rp["education"], 0) / max(edu_rank.get(jp["education_required"], 1), 1)))
    )

    sem = _semantic_sim(resume_text, jd_text)
    kw_score = int(min(100, sem * 130))

    overall = int(0.40 * skills_score + 0.25 * exp_score + 0.15 * edu_score + 0.20 * kw_score)

    # Human-readable summary
    fit = "strong" if overall >= 70 else "moderate" if overall >= 45 else "weak"
    summary = (
        f"Overall this is a {fit} match ({overall}%). "
        f"The resume directly covers {len(matched)} of {len(j_skills)} required skills. "
    )
    if experience_gap:
        summary += f"⚠️ Experience gap: {experience_gap['message']} "
    if missing:
        summary += f"Key missing skills: {', '.join(missing[:4])}. "
    if weak:
        summary += f"{len(weak)} skill(s) present but below expected level. "
    if not missing and not weak and not experience_gap:
        summary += "No critical gaps — focus on quantifying impact in your resume."

    # -----------------------------------------------------------------------
    # Taxonomy Integration (ESCO + O*NET)
    # -----------------------------------------------------------------------
    # 1. Normalize Skill Gaps via ESCO
    all_gaps_for_esco = missing + [w["skill"] for w in weak]
    esco_normalized_skills = esco_onet.batch_normalize_skills(all_gaps_for_esco, max_skills=10)

    # 2. Extract job title from JD and fetch O*NET occupation
    job_title = next((l.strip() for l in jd_text.splitlines() if l.strip()), "Unknown Role")[:120]
    onet_occupation = esco_onet.get_onet_occupation_skills(job_title)

    # 3. Compute implicit gaps (skills O*NET says are needed, but missing in JD & Resume)
    implicit_gaps = esco_onet.compute_implicit_gaps(onet_occupation, r_skills, j_skills)

    return {
        "match_score": overall,
        "score_breakdown": {
            "skills_match": skills_score,
            "experience_match": exp_score,
            "education_match": edu_score,
            "keywords_match": kw_score,
        },
        "resume_profile": rp,
        "jd_profile": jp,
        "skill_analysis": {"matched": matched, "weak": weak, "missing": missing},
        "skill_comparison": skill_comparison,
        "experience_gap": experience_gap,
        "synonym_matches": synonym_matches,
        "competency_levels": rp["competency_levels"],
        "interview_prep": _generate_interview_questions(resume_text, jd_text, missing, weak, experience_gap),
        "skill_gaps_summary": summary,
        "top_missing_skills": missing[:8],
        "taxonomy": {
            "esco_skills": esco_normalized_skills,
            "onet_occupation": onet_occupation,
            "implicit_gaps": implicit_gaps
        }
    }


# ---------------------------------------------------------------------------
# Course recommendations
# ---------------------------------------------------------------------------

def recommend_courses(
    gap_skills: list,
    free_only: bool = False,
    platform: Optional[str] = None,
    max_duration_hours: Optional[int] = None,
) -> dict:
    path: dict = {"foundational": [], "intermediate": [], "advanced": []}

    for skill in gap_skills:
        # 1. Fetch pre-populated courses from our offline COURSE_KG database first
        slug = skill.lower().replace(" ", "_").replace(".", "")
        courses = list(COURSE_KG.get(slug, []))
        
        # Also check direct lowercase match of the skill string
        if not courses and skill.lower() in COURSE_KG:
            courses = list(COURSE_KG[skill.lower()])

        # 2. Try scraping additional courses dynamically
        scraped = scrape_courses_for_skill(skill)
        existing_urls = {c["url"] for c in courses}
        for s_course in scraped:
            if s_course["url"] not in existing_urls:
                courses.append(s_course)
                existing_urls.add(s_course["url"])

        # 3. Fallback: If no courses were found, dynamically generate high-quality fallback courses
        if not courses:
            courses = [
                {
                    "title": f"Introduction to {skill.title()} Fundamentals",
                    "platform": "YouTube",
                    "url": f"https://www.youtube.com/results?search_query={skill}+tutorial",
                    "duration": "4 hours",
                    "duration_hours": 4,
                    "free": True,
                    "level": "foundational",
                    "description": f"Learn the core concepts of {skill} from top industry experts in this free crash course."
                },
                {
                    "title": f"{skill.title()} Masterclass: Zero to Hero",
                    "platform": "Udemy",
                    "url": f"https://www.udemy.com/courses/search/?q={skill}",
                    "duration": "12 hours",
                    "duration_hours": 12,
                    "free": False,
                    "level": "intermediate",
                    "description": f"Deep dive into intermediate and advanced patterns of {skill} with practical hands-on exercises."
                }
            ]

        for course in courses:
            if free_only and not course.get("free"):
                continue
            if platform and course.get("platform", "").lower() != platform.lower():
                continue
            if max_duration_hours and isinstance(course.get("duration_hours"), int):
                if course["duration_hours"] > max_duration_hours:
                    continue
            level = course.get("level", "intermediate")
            path[level].append({**course, "skill": skill})

    return {
        "learning_path": path,
        "total_courses": sum(len(v) for v in path.values()),
        "filters_applied": {
            "free_only": free_only,
            "platform": platform,
            "max_duration_hours": max_duration_hours,
        },
    }


# ---------------------------------------------------------------------------
# STAR-style resume improvement suggestions
# ---------------------------------------------------------------------------

_STAR_LIBRARY = {
    "aws": {
        "situation": "Our team needed to migrate a monolithic application to the cloud to improve scalability and reduce hardware costs.",
        "task": "I was responsible for evaluating cloud providers and leading the infrastructure migration.",
        "action": "Designed the AWS architecture using EC2, S3, RDS, and Lambda; authored CloudFormation templates and set up auto-scaling groups.",
        "result": "Reduced infrastructure costs by 35% and improved system uptime from 99.5% to 99.9%.",
        "bullet": "Led AWS cloud migration (EC2, S3, RDS, Lambda + CloudFormation), cutting infra costs 35% and achieving 99.9% uptime.",
    },
    "docker": {
        "situation": "Development and production environments were inconsistent, causing weekly deployment failures.",
        "task": "Standardize the environment setup across the engineering team and CI/CD pipeline.",
        "action": "Containerized all services using Docker and Docker Compose; created Dockerfiles for each microservice and integrated them into the CI pipeline.",
        "result": "Eliminated environment inconsistencies and reduced deployment failures by 80% within the first month.",
        "bullet": "Containerized 8 microservices with Docker/Compose, eliminating environment drift and reducing deployment failures by 80%.",
    },
    "kubernetes": {
        "situation": "Our growing microservices architecture needed better orchestration to handle traffic spikes without manual intervention.",
        "task": "Implement container orchestration to ensure high availability and elastic scaling.",
        "action": "Deployed and managed a Kubernetes cluster on AWS EKS; implemented HPA, rolling deployments, Helm charts, and liveness probes.",
        "result": "Achieved zero-downtime deployments and automatically handled 3× traffic spikes during peak events.",
        "bullet": "Managed Kubernetes (EKS) with HPA and Helm, enabling zero-downtime deploys and 3× elastic traffic scaling.",
    },
    "postgresql": {
        "situation": "Core application queries were timing out under load, violating our SLA.",
        "task": "Diagnose and fix database performance bottlenecks.",
        "action": "Used EXPLAIN ANALYZE to profile slow queries, added composite indexes, refactored N+1 query patterns, and set up PgBouncer connection pooling.",
        "result": "Reduced average query latency by 70% and eliminated all SLA violations within two sprints.",
        "bullet": "Optimized PostgreSQL performance (indexes, query rewrite, PgBouncer), reducing avg query time by 70% and eliminating SLA breaches.",
    },
    "typescript": {
        "situation": "Our growing JavaScript front-end was producing frequent runtime type errors in production.",
        "task": "Improve code reliability and developer experience by migrating to TypeScript.",
        "action": "Led a gradual TypeScript adoption: defined interfaces and generics for shared modules, enforced strict mode, and updated the CI linting pipeline.",
        "result": "Reduced production type errors by 90% and cut new-developer onboarding time from 3 days to 1 day.",
        "bullet": "Migrated front-end codebase to TypeScript (strict mode), reducing runtime type errors 90% and onboarding time by 66%.",
    },
    "graphql": {
        "situation": "Multiple REST endpoints were causing over-fetching and under-fetching, slowing our mobile clients.",
        "task": "Design a unified API layer that lets clients request exactly the data they need.",
        "action": "Designed and implemented a GraphQL API with Apollo Server; migrated 12 REST endpoints, added DataLoader for batching, and wrote resolver tests.",
        "result": "Reduced mobile payload size by 45% and cut average API response time from 320 ms to 110 ms.",
        "bullet": "Built GraphQL API (Apollo Server, DataLoader) replacing 12 REST endpoints, reducing payload by 45% and latency by 66%.",
    },
    "terraform": {
        "situation": "Our infrastructure was manually provisioned, making environment replication error-prone and slow.",
        "task": "Introduce infrastructure-as-code to enable reproducible, version-controlled environments.",
        "action": "Authored Terraform modules for all AWS resources; integrated plan/apply into the CI/CD pipeline with automated drift detection.",
        "result": "Reduced environment setup time from 2 days to 20 minutes and eliminated configuration drift across staging and production.",
        "bullet": "Implemented Terraform IaC for all AWS resources, cutting environment setup from 2 days to 20 min and eliminating config drift.",
    },
    "kafka": {
        "situation": "Real-time data from 15 microservices needed reliable, decoupled event streaming at scale.",
        "task": "Design and implement an event-driven messaging backbone.",
        "action": "Set up Apache Kafka clusters with topic partitioning, consumer groups, and Kafka Streams for stateful processing; implemented dead-letter queues.",
        "result": "Achieved sub-100 ms event delivery at 50,000 msg/s with zero message loss during failover.",
        "bullet": "Built Kafka event-streaming backbone (50k msg/s), delivering sub-100ms latency and zero message loss across 15 microservices.",
    },
}

_DEFAULT_STAR = {
    "situation": "Our team identified a critical gap in our technical capabilities that was impacting project velocity.",
    "task": "I took ownership of bridging the gap by learning and applying {skill} in a production context.",
    "action": "Completed targeted training on {skill}, built a proof-of-concept, gathered team feedback, and integrated the solution into our workflow.",
    "result": "Delivered the feature on schedule, which improved team velocity by 20% and received positive stakeholder feedback.",
    "bullet": "Applied {skill} to deliver a key project feature, improving team velocity by 20% and earning stakeholder recognition.",
}


def generate_star_improvements(resume_text: str, jd_text: str, gap_skills: list) -> dict:
    """
    Generate personalized STAR-format resume bullets and overall resume improvement
    suggestions using Gemini LLM. Falls back to static library if LLM is unavailable.
    """
    if _LLM_ENABLED:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')

            # --- 1. STAR bullets ---
            star_prompt = f"""
You are an expert resume writer helping a candidate improve their resume for a specific job application.

The candidate's resume:
{resume_text[:3000]}

The job description they are applying for:
{jd_text[:2000]}

The candidate is MISSING or WEAK in the following skills: {gap_skills[:5]}

For EACH skill, write a realistic, specific, quantified STAR-format story as if the candidate HAD worked on a project involving that skill. Make it believable based on the candidate's existing background and the role they are targeting. DO NOT be generic — reference the role, the domain (e.g., ML, fintech, e-commerce), and realistic metrics.

Return ONLY a valid JSON array with exactly {min(len(gap_skills[:5]), 5)} objects, each with this schema:
[
  {{
    "gap_skill": "the skill name",
    "situation": "1-2 sentences describing the business context and the problem",
    "task": "1 sentence: what the candidate specifically owned or was responsible for",
    "action": "2-3 sentences: specific technical steps taken, tools used, decisions made",
    "result": "1-2 sentences with quantified business impact (%, time saved, users served, latency, cost)",
    "bullet_suggestion": "one polished resume bullet in past tense, action verb first, quantified result at end"
  }}
]

Do not include any markdown formatting or code fences. Output raw JSON only.
"""
            resp = model.generate_content(star_prompt)
            text = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            star_list = json.loads(text)

            # --- 2. Resume improvement suggestions ---
            suggest_prompt = f"""
You are a professional resume coach and career advisor. Analyze this resume against the job description and provide highly personalized, actionable improvement suggestions.

Resume:
{resume_text[:3000]}

Job Description:
{jd_text[:2000]}

Provide 6 specific, personalized suggestions to improve the resume for this role. These should be concrete and reference actual content from the resume. Focus on: missing quantification, weak phrasing, missing keywords, structural improvements, skills highlighting.

Return ONLY a valid JSON array of 6 objects:
[
  {{
    "category": "one of: Quantification | Keywords | Phrasing | Structure | Skills | Impact",
    "title": "Short title for this suggestion (5-7 words)",
    "current": "What the resume currently does (or lacks) - be specific, quote/reference actual resume content if possible",
    "suggestion": "Specific, actionable advice on how to fix it",
    "priority": "one of: High | Medium | Low",
    "example": "A concrete example of the improved version (e.g., a rewritten bullet or section)"
  }}
]

Do not include markdown formatting. Output raw JSON only.
"""
            resp2 = model.generate_content(suggest_prompt)
            text2 = resp2.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            suggestions = json.loads(text2)

            return {
                "star_improvements": star_list,
                "resume_suggestions": suggestions,
                "total": len(star_list),
                "ai_powered": True
            }
        except Exception as e:
            print(f"[LLM] STAR improvement error: {e}")

    # Fallback: use static library
    improvements = []
    for skill in gap_skills[:6]:
        key = skill.lower().replace(".", "").replace("+", "plus").replace("#", "sharp").replace(" ", "")
        template = next((v for k, v in _STAR_LIBRARY.items() if k in key or key in k), None)
        if not template:
            template = {k: v.replace("{skill}", skill) for k, v in _DEFAULT_STAR.items()}
        improvements.append({
            "gap_skill": skill,
            "situation": template["situation"],
            "task": template["task"],
            "action": template["action"],
            "result": template["result"],
            "bullet_suggestion": template["bullet"],
        })
    return {"star_improvements": improvements, "resume_suggestions": [], "total": len(improvements), "ai_powered": False}

