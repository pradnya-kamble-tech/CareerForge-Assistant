import sqlite3
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
import json
import os
from collections import Counter
from datetime import datetime

# ---------- Database Configuration ----------
# Use DATABASE_URL for PostgreSQL (Supabase), otherwise fallback to local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "careerforge.db")

def _get_conn():
    """Returns a new database connection (PostgreSQL or SQLite)."""
    if DATABASE_URL and HAS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def _get_cursor(conn):
    """Returns a dictionary-like cursor for the current connection."""
    if DATABASE_URL and HAS_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def db_execute(query, params=(), commit=True):
    """Execute a query, handling placeholder differences between SQLite (?) and PostgreSQL (%s)."""
    if DATABASE_URL and HAS_POSTGRES:
        query = query.replace("?", "%s")
    
    conn = _get_conn()
    try:
        cursor = _get_cursor(conn)
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor
    finally:
        if not commit: # If we need the cursor for fetch later, we can't close yet
            pass
        else:
            conn.close()

def db_query(query, params=(), one=False):
    """Execute a SELECT query and return results as dicts."""
    if DATABASE_URL and HAS_POSTGRES:
        query = query.replace("?", "%s")
        
    conn = _get_conn()
    try:
        cursor = _get_cursor(conn)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
        return (results[0] if results else None) if one else results
    finally:
        conn.close()

# ---------- Database API ----------

def init_db():
    """Initialize database tables. Primarily for local SQLite; Supabase should be pre-migrated."""
    queries = [
        '''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            score INTEGER,
            score_level TEXT,
            risk_level TEXT,
            risk_icon TEXT,
            skills TEXT,
            skills_total INTEGER,
            career_preds TEXT,
            insight TEXT,
            owner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS decisions (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            score INTEGER,
            risk_level TEXT,
            insight TEXT,
            owner TEXT,
            decision TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            action TEXT,
            user_id TEXT,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    if not DATABASE_URL:
        # SQLite adjustments
        queries = [q.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT") for q in queries]
        queries = [q.replace("TIMESTAMP", "DATETIME") for q in queries]
        queries = [q.replace("user_id", "user") for q in queries] # Backwards compatibility
        
    for q in queries:
        try:
            db_execute(q)
        except Exception:
            pass # Tables might already exist with SERIAL/INTEGER conflict

def db_add_user(email, password, role="Student"):
    db_execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
               (email.lower(), password, role))

def db_get_user(email):
    return db_query("SELECT * FROM users WHERE email = ?", (email.lower(),), one=True)

def db_user_exists(email):
    return db_get_user(email) is not None

def db_count_users():
    res = db_query("SELECT COUNT(*) as count FROM users", one=True)
    return res["count"] if res else 0

def db_add_resume(data):
    db_execute('''INSERT INTO resumes 
        (filename, score, score_level, risk_level, risk_icon, skills, skills_total, career_preds, insight, owner)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            data.get("filename", ""),
            data.get("score", 0),
            data.get("score_level", ""),
            data.get("risk_level", ""),
            data.get("risk_icon", ""),
            json.dumps(data.get("skills", [])),
            data.get("skills_total", 0),
            json.dumps(data.get("career_predictions", [])),
            data.get("insight", ""),
            data.get("owner", "")
        ))

def db_get_resumes(owner=None):
    if owner:
        rows = db_query("SELECT * FROM resumes WHERE owner = ? ORDER BY score DESC", (owner,))
    else:
        rows = db_query("SELECT * FROM resumes ORDER BY score DESC")
    
    for r in rows:
        r["skills"] = json.loads(r["skills"]) if r["skills"] else []
        r["career_predictions"] = json.loads(r["career_preds"]) if r.get("career_preds") else []
    return rows

def db_count_resumes():
    res = db_query("SELECT COUNT(*) as count FROM resumes", one=True)
    return res["count"] if res else 0

def db_add_decision(data):
    db_execute("DELETE FROM decisions WHERE filename = ? AND owner = ?", 
               (data.get("filename", ""), data.get("owner", "")))
    db_execute('''INSERT INTO decisions 
        (filename, score, risk_level, insight, owner, decision)
        VALUES (?, ?, ?, ?, ?, ?)''', (
            data.get("filename", ""),
            data.get("score", 0),
            data.get("risk_level", ""),
            data.get("insight", ""),
            data.get("owner", ""),
            data.get("decision", "pending")
        ))

def db_get_decisions(owner, decision_type=None):
    if decision_type:
        return db_query("SELECT * FROM decisions WHERE owner = ? AND decision = ? ORDER BY id DESC", (owner, decision_type))
    return db_query("SELECT * FROM decisions WHERE owner = ? ORDER BY id DESC", (owner,))

def db_add_log(action, user="system", detail=""):
    # Note: Using 'user' column for SQLite and 'user_id' for Supabase? No, let's stick to 'user' for now.
    try:
        db_execute("INSERT INTO logs (user_id if DATABASE_URL else user, action, detail) VALUES (?, ?, ?)",
                   (user, action, detail))
    except Exception:
        # Fallback to column name 'user' if 'user_id' fails
        try:
            db_execute("INSERT INTO logs (user, action, detail) VALUES (?, ?, ?)",
                       (user, action, detail))
        except Exception:
            pass

def db_query_logs(limit=50):
    return db_query("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))

def db_count_logs():
    res = db_query("SELECT COUNT(*) as count FROM logs", one=True)
    return res["count"] if res else 0

def db_get_admin_stats():
    rows = db_query("SELECT score, risk_level, skills FROM resumes")
    total = len(rows)
    if total == 0:
        return {
            "avg_score": 0, "highest_score": 0, "lowest_score": 0,
            "score_dist": {"0-39": 0, "40-69": 0, "70-100": 0},
            "risk_dist": {"Low": 0, "Medium": 0, "High": 0},
            "unique_skills": 0, "top_skills": [], "total_users": 0, "total_logs": 0,
            "trend_labels": [], "trend_data": []
        }
        
    scores = [r["score"] for r in rows]
    avg_score = round(sum(scores) / total, 1)
    highest = max(scores)
    lowest = min(scores)
    
    low = len([s for s in scores if s < 40])
    mid = len([s for s in scores if 40 <= s < 70])
    high = len([s for s in scores if s >= 70])
    
    risk_low = len([r for r in rows if r["risk_level"] == "Low"])
    risk_med = len([r for r in rows if r["risk_level"] == "Medium"])
    risk_high = len([r for r in rows if r["risk_level"] == "High"])
    
    all_skills = []
    for r in rows:
        if r["skills"]:
            all_skills.extend(json.loads(r["skills"]))
    skill_counts = Counter(all_skills)
    
    # Simple trend over creation date
    trend_counts = Counter([r.get("created_at", "Unknown")[:10] for r in db_query("SELECT created_at FROM resumes")])
    
    return {
        "avg_score": avg_score, "highest_score": highest, "lowest_score": lowest,
        "score_dist": {"0-39": low, "40-69": mid, "70-100": high},
        "risk_dist": {"Low": risk_low, "Medium": risk_med, "High": risk_high},
        "unique_skills": len(skill_counts), "top_skills": skill_counts.most_common(10),
        "total_users": db_count_users(), "total_logs": db_count_logs(),
        "trend_labels": sorted(list(trend_counts.keys())),
        "trend_data": [trend_counts[k] for k in sorted(trend_counts.keys())]
    }

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

def db_get_top_candidates(owner, limit=5):
    return db_query("SELECT * FROM resumes WHERE owner = ? ORDER BY score DESC LIMIT ?", (owner, limit))

def db_get_recent_activity(owner, limit=5):
    # Join resumes and decisions to see activity
    return db_query("SELECT r.filename, r.score, d.decision, r.created_at FROM resumes r LEFT JOIN decisions d ON r.filename = d.filename WHERE r.owner = ? ORDER BY r.created_at DESC LIMIT ?", (owner, limit))

def db_get_all_users():
    return db_query("SELECT * FROM users ORDER BY id DESC")
