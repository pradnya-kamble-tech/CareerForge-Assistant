import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from collections import Counter

# ---------- Database Configuration ----------
# Use DATABASE_URL for PostgreSQL (Supabase), otherwise fallback to local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "careerforge.db")

def _get_conn():
    """Returns a new database connection (PostgreSQL or SQLite)."""
    if DATABASE_URL:
        # Connect to PostgreSQL (Supabase)
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # Fallback to SQLite
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def _get_cursor(conn):
    """Returns a dictionary-like cursor for the current connection."""
    if DATABASE_URL:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def db_execute(query, params=(), commit=True):
    """Execute a query, handling placeholder differences between SQLite (?) and PostgreSQL (%s)."""
    if DATABASE_URL:
        query = query.replace("?", "%s")
    
    with _get_conn() as conn:
        cursor = _get_cursor(conn)
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor

def db_query(query, params=(), one=False):
    """Execute a SELECT query and return results as dicts."""
    if DATABASE_URL:
        query = query.replace("?", "%s")
        
    with _get_conn() as conn:
        cursor = _get_cursor(conn)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
        if one:
            return results[0] if results else None
        return results

def init_db():
    """Initialise database tables. Handles SQLite and PostgreSQL syntax differences."""
    pk_type = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    if not DATABASE_URL:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    queries = [
        f"CREATE TABLE IF NOT EXISTS users (id {pk_type}, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        f"CREATE TABLE IF NOT EXISTS resumes (id {pk_type}, filename TEXT NOT NULL, score INTEGER DEFAULT 0, score_level TEXT, risk_level TEXT, risk_icon TEXT, skills TEXT, skills_total INTEGER DEFAULT 0, career_preds TEXT, insight TEXT, owner TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        f"CREATE TABLE IF NOT EXISTS decisions (id {pk_type}, filename TEXT NOT NULL, score INTEGER DEFAULT 0, risk_level TEXT, insight TEXT, owner TEXT NOT NULL, decision TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        f"CREATE TABLE IF NOT EXISTS logs (id {pk_type}, action TEXT, \"user\" TEXT, detail TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ]
    
    for q in queries:
        db_execute(q)
    print(f"Database initialised ({'PostgreSQL' if DATABASE_URL else 'SQLite'}).")

# ──────────────────── USERS ────────────────────

def db_add_user(email: str, password: str, role: str = "Student"):
    db_execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email.lower(), password, role))

def db_get_user(email: str):
    return db_query("SELECT * FROM users WHERE email = ? LIMIT 1", (email.lower(),), one=True)

def db_user_exists(email: str) -> bool:
    return db_get_user(email) is not None

def db_count_users():
    result = db_query("SELECT COUNT(id) as count FROM users", one=True)
    return result['count'] if result else 0

# ──────────────────── RESUMES ────────────────────

def db_add_resume(data):
    db_execute(
        "INSERT INTO resumes (filename, score, score_level, risk_level, risk_icon, skills, skills_total, career_preds, insight, owner) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data['filename'], data['score'], data['score_level'], data['risk_level'], data['risk_icon'], json.dumps(data['skills']), data['skills_total'], json.dumps(data['career_preds']), data['insight'], data['owner'])
    )

def db_get_resumes(owner=None):
    if owner:
        rows = db_query("SELECT * FROM resumes WHERE owner = ? ORDER BY id DESC", (owner,))
    else:
        rows = db_query("SELECT * FROM resumes ORDER BY id DESC")
    for r in rows:
        r['skills'] = json.loads(r['skills']) if r.get('skills') else []
        r['career_preds'] = json.loads(r['career_preds']) if r.get('career_preds') else []
    return rows

def db_count_resumes():
    result = db_query("SELECT COUNT(id) as count FROM resumes", one=True)
    return result['count'] if result else 0

# ──────────────────── DECISIONS ────────────────────

def db_add_decision(data):
    db_execute(
        "INSERT INTO decisions (filename, score, risk_level, insight, owner, decision) VALUES (?, ?, ?, ?, ?, ?)",
        (data['filename'], data['score'], data['risk_level'], data['insight'], data['owner'], data['decision'])
    )

def db_get_decisions(owner, decision_type=None):
    if decision_type:
        return db_query("SELECT * FROM decisions WHERE owner = ? AND decision = ? ORDER BY id DESC", (owner, decision_type))
    return db_query("SELECT * FROM decisions WHERE owner = ? ORDER BY id DESC", (owner,))

# ──────────────────── LOGS ────────────────────

def db_add_log(action, user="system", detail=""):
    db_execute("INSERT INTO logs (action, \"user\", detail) VALUES (?, ?, ?)", (action, user, detail))

def db_get_logs(limit=50):
    return db_query("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))

def db_count_logs():
    result = db_query("SELECT COUNT(id) as count FROM logs", one=True)
    return result['count'] if result else 0

# ──────────────────── ADMIN STATS ────────────────────

def db_get_admin_stats():
    resumes = db_get_resumes()
    total = len(resumes)
    if total == 0:
        return {"total_resumes": 0, "avg_score": 0, "score_dist": {}, "skill_counts": [], "risk_dist": {}, "total_users": db_count_users(), "total_logs": db_count_logs()}
    
    scores = [r['score'] for r in resumes]
    avg_score = round(sum(scores) / total, 1)
    
    # Score dist
    dist = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in scores:
        if s <= 20: dist["0-20"] += 1
        elif s <= 40: dist["21-40"] += 1
        elif s <= 60: dist["41-60"] += 1
        elif s <= 80: dist["61-80"] += 1
        else: dist["81-100"] += 1
    
    # Top skills
    all_skills = []
    for r in resumes: all_skills.extend(r['skills'])
    skill_counts = Counter(all_skills).most_common(10)
    
    # Risk dist
    risk_counts = Counter(r['risk_level'] for r in resumes)
    
    return {
        "total_resumes": total, "avg_score": avg_score, "score_dist": dist,
        "skill_counts": skill_counts, "risk_dist": dict(risk_counts),
        "total_users": db_count_users(), "total_logs": db_count_logs()
    }

# ──────────────────── RECRUITER STATS ────────────────────

def db_get_recruiter_stats(owner):
    resumes = db_get_resumes(owner)
    total = len(resumes)
    if total == 0:
        return {"total_resumes": 0, "shortlisted": 0, "rejected": 0, "pending": 0, "success_rate": 0, "quality_of_hire": 0, "attrition_risk": 0}
    
    decisions = db_get_decisions(owner)
    shortlisted = len([d for d in decisions if d['decision'] == 'shortlist'])
    rejected = len([d for d in decisions if d['decision'] == 'reject'])
    pending = total - len(decisions)
    
    success_rate = round((shortlisted / total * 100)) if total > 0 else 0
    avg_score = round(sum(r['score'] for r in resumes) / total, 1)
    high_risk = len([r for r in resumes if r['risk_level'] == 'High'])
    attrition_pct = round((high_risk / total * 100)) if total > 0 else 0
    
    return {
        "total_resumes": total, "shortlisted": shortlisted, "rejected": rejected,
        "pending": max(0, pending), "success_rate": success_rate,
        "quality_of_hire": avg_score, "attrition_risk": attrition_pct
    }

def db_get_all_users():
    return db_query("SELECT email, role, created_at FROM users ORDER BY id DESC")

def db_get_logs_filtered(action_filter=None, limit=50):
    if action_filter and action_filter != "all":
        return db_query("SELECT * FROM logs WHERE action = ? ORDER BY id DESC LIMIT ?", (action_filter, limit))
    return db_get_logs(limit)

def db_get_top_candidates(owner, limit=5):
    return db_query("SELECT filename, score, risk_level, skills_total, created_at FROM resumes WHERE owner = ? ORDER BY score DESC LIMIT ?", (owner, limit))

def db_get_recent_activity(owner, limit=5):
    return db_query("SELECT * FROM logs WHERE \"user\" = ? ORDER BY id DESC LIMIT ?", (owner, limit))
