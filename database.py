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
# database.py — SQLite persistence layer for CareerForge AI
import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "careerforge.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        score INTEGER,
        risk_level TEXT,
        insight TEXT,
        owner TEXT,
        decision TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        user TEXT,
        detail TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
    print("✅ SQLite database initialised.")

def db_add_user(email, password, role="Student"):
    try:
        conn = get_db()
        conn.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                     (email.lower(), password, role))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass

def db_get_user(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    conn.close()
    if row:
        return {"email": row["email"], "password": row["password"], "role": row["role"]}
    return None

def db_user_exists(email):
    return db_get_user(email) is not None

def db_count_users():
    conn = get_db()
    c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return c

def db_add_resume(data):
    conn = get_db()
    conn.execute('''INSERT INTO resumes 
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
    conn.commit()
    conn.close()

def db_get_resumes(owner=None):
    conn = get_db()
    if owner:
        rows = conn.execute("SELECT * FROM resumes WHERE owner = ? ORDER BY score DESC", (owner,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM resumes ORDER BY score DESC").fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "filename": r["filename"],
            "score": r["score"],
            "score_level": r["score_level"],
            "risk_level": r["risk_level"],
            "risk_icon": r["risk_icon"],
            "skills": json.loads(r["skills"]) if r["skills"] else [],
            "skills_total": r["skills_total"],
            "career_predictions": json.loads(r["career_preds"]) if r["career_preds"] else [],
            "insight": r["insight"],
            "owner": r["owner"],
            "created_at": r["created_at"],
        })
    return results

def db_count_resumes():
    conn = get_db()
    c = conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
    conn.close()
    return c

def db_add_decision(data):
    conn = get_db()
    conn.execute("DELETE FROM decisions WHERE filename = ? AND owner = ?", 
                 (data.get("filename", ""), data.get("owner", "")))
    conn.execute('''INSERT INTO decisions 
        (filename, score, risk_level, insight, owner, decision)
        VALUES (?, ?, ?, ?, ?, ?)''', (
            data.get("filename", ""),
            data.get("score", 0),
            data.get("risk_level", ""),
            data.get("insight", ""),
            data.get("owner", ""),
            data.get("decision", "pending")
        ))
    conn.commit()
    conn.close()

def db_get_decisions(owner, decision_type=None):
    conn = get_db()
    if decision_type:
        rows = conn.execute("SELECT * FROM decisions WHERE owner = ? AND decision = ? ORDER BY id DESC", 
                            (owner, decision_type)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM decisions WHERE owner = ? ORDER BY id DESC", (owner,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_add_log(action, user="system", detail=""):
    try:
        conn = get_db()
        conn.execute("INSERT INTO logs (action, user, detail) VALUES (?, ?, ?)",
                     (action, user, detail))
        conn.commit()
        conn.close()
    except Exception:
        pass

def db_get_logs(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_count_logs():
    conn = get_db()
    c = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    conn.close()
    return c

def db_get_admin_stats():
    conn = get_db()
    rows = conn.execute("SELECT score, risk_level, skills FROM resumes").fetchall()
    
    
    total = len(rows)
    scores = [r["score"] for r in rows]
    avg_score = round(sum(scores) / total, 1) if total else 0
    highest = max(scores) if scores else 0
    lowest = min(scores) if scores else 0
    
    low = sum(1 for s in scores if s < 40)
    mid = sum(1 for s in scores if 40 <= s < 70)
    high = sum(1 for s in scores if s >= 70)
    
    risk_low = sum(1 for r in rows if r["risk_level"] == "Low")
    risk_med = sum(1 for r in rows if r["risk_level"] == "Medium")
    risk_high = sum(1 for r in rows if r["risk_level"] == "High")
    
    from collections import Counter
    skill_counts = Counter()
    for r in rows:
        try:
            skill_counts.update(json.loads(r["skills"]))
        except Exception:
            pass
            
    # Trend Data (Last 7 days)
    trend_counts = {}
    c = conn.cursor()
    # Count resumes by day
    rows_trend = c.execute("SELECT date(created_at) as d, COUNT(*) as c FROM resumes GROUP BY d ORDER BY d DESC LIMIT 7").fetchall()
    for tr in reversed(rows_trend):
        trend_counts[tr["d"]] = tr["c"]
    
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in trend_counts:
        trend_counts[today] = 0
        
    conn.close()
    return {
        "total": total,
        "avg_score": avg_score,
        "highest_score": highest,
        "lowest_score": lowest,
        "score_dist": {"0-39": low, "40-69": mid, "70-100": high},
        "risk_dist": {"Low": risk_low, "Medium": risk_med, "High": risk_high},
        "unique_skills": len(skill_counts),
        "top_skills": skill_counts.most_common(10),
        "total_users": db_count_users(),
        "total_logs": db_count_logs(),
        "trend_labels": list(trend_counts.keys()),
        "trend_data": list(trend_counts.values())
>>>>>>> f762ae921504b26acced84762f0240253af6bb27
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
