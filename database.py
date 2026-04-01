# database.py — SQLite persistence layer for CareerForge AI

import os
import json
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.db")
USERS_JSON = os.path.join(os.path.dirname(__file__), "data", "users.json")


def _connect():
    """Return a new SQLite connection with row-factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ──────────────────── INIT ────────────────────

def init_db():
    """Create tables if they don't exist, then migrate users.json."""
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL DEFAULT 'Student',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT    NOT NULL,
            score       INTEGER DEFAULT 0,
            score_level TEXT    DEFAULT '',
            risk_level  TEXT    DEFAULT '',
            risk_icon   TEXT    DEFAULT '',
            skills      TEXT    DEFAULT '[]',
            skills_total INTEGER DEFAULT 0,
            career_preds TEXT   DEFAULT '[]',
            insight     TEXT    DEFAULT '',
            owner       TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            filename   TEXT    NOT NULL,
            score      INTEGER DEFAULT 0,
            risk_level TEXT    DEFAULT '',
            insight    TEXT    DEFAULT '',
            owner      TEXT    DEFAULT '',
            decision   TEXT    DEFAULT 'pending',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            action     TEXT    NOT NULL,
            user       TEXT    DEFAULT '',
            detail     TEXT    DEFAULT '',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()

    # ── Migrate users.json → SQLite (one-time) ──
    if os.path.exists(USERS_JSON):
        try:
            with open(USERS_JSON, "r", encoding="utf-8") as f:
                users_data = json.load(f)
            for email, info in users_data.items():
                try:
                    cur.execute(
                        "INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)",
                        (email.lower(), info["password"], info.get("role", "Student")),
                    )
                except Exception:
                    pass
            conn.commit()
            # Rename old file so migration doesn't repeat
            os.rename(USERS_JSON, USERS_JSON + ".migrated")
        except Exception:
            pass

    conn.close()


# ──────────────────── USERS ────────────────────

def db_add_user(email, password, role="Student"):
    conn = _connect()
    conn.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email.lower(), password, role),
    )
    conn.commit()
    conn.close()


def db_get_user(email):
    """Return user dict or None."""
    conn = _connect()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    conn.close()
    if row:
        return {"email": row["email"], "password": row["password"], "role": row["role"]}
    return None


def db_user_exists(email):
    return db_get_user(email) is not None


def db_count_users():
    conn = _connect()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


# ──────────────────── RESUMES ────────────────────

def db_add_resume(data):
    """Insert a resume record. `data` is a dict with candidate fields."""
    conn = _connect()
    conn.execute(
        """INSERT INTO resumes
           (filename, score, score_level, risk_level, risk_icon,
            skills, skills_total, career_preds, insight, owner)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("filename", ""),
            data.get("score", 0),
            data.get("score_level", ""),
            data.get("risk_level", ""),
            data.get("risk_icon", ""),
            json.dumps(data.get("skills", [])),
            data.get("skills_total", 0),
            json.dumps(data.get("career_predictions", [])),
            data.get("insight", ""),
            data.get("owner", ""),
        ),
    )
    conn.commit()
    conn.close()


def db_get_resumes(owner=None):
    """Return list of resume dicts. If owner given, filter by it."""
    conn = _connect()
    if owner:
        rows = conn.execute(
            "SELECT * FROM resumes WHERE owner = ? ORDER BY score DESC", (owner,)
        ).fetchall()
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
    conn = _connect()
    count = conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
    conn.close()
    return count


# ──────────────────── DECISIONS ────────────────────

def db_add_decision(data):
    """Upsert a shortlist/reject decision for a candidate."""
    conn = _connect()
    # Remove any previous decision for this file by this owner
    conn.execute(
        "DELETE FROM decisions WHERE filename = ? AND owner = ?",
        (data.get("filename", ""), data.get("owner", "")),
    )
    conn.execute(
        """INSERT INTO decisions (filename, score, risk_level, insight, owner, decision)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data.get("filename", ""),
            data.get("score", 0),
            data.get("risk_level", ""),
            data.get("insight", ""),
            data.get("owner", ""),
            data.get("decision", "pending"),
        ),
    )
    conn.commit()
    conn.close()


def db_get_decisions(owner, decision_type=None):
    """Return decisions for an owner, optionally filtered by type."""
    conn = _connect()
    if decision_type:
        rows = conn.execute(
            "SELECT * FROM decisions WHERE owner = ? AND decision = ? ORDER BY id DESC",
            (owner, decision_type),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM decisions WHERE owner = ? ORDER BY id DESC", (owner,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────── LOGS ────────────────────

def db_add_log(action, user="system", detail=""):
    """Insert a log entry."""
    conn = _connect()
    conn.execute(
        "INSERT INTO logs (action, user, detail) VALUES (?, ?, ?)",
        (action, user, detail),
    )
    conn.commit()
    conn.close()


def db_get_logs(limit=50):
    """Return recent log entries."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_count_logs():
    conn = _connect()
    count = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    conn.close()
    return count


# ──────────────────── ADMIN STATS ────────────────────

def db_get_admin_stats():
    """Return aggregated stats for the admin dashboard."""
    conn = _connect()
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
    avg_score = cur.execute("SELECT COALESCE(AVG(score), 0) FROM resumes").fetchone()[0]
    highest = cur.execute("SELECT COALESCE(MAX(score), 0) FROM resumes").fetchone()[0]
    lowest = cur.execute("SELECT COALESCE(MIN(score), 0) FROM resumes").fetchone()[0]

    # Score distribution
    low = cur.execute("SELECT COUNT(*) FROM resumes WHERE score < 40").fetchone()[0]
    mid = cur.execute("SELECT COUNT(*) FROM resumes WHERE score >= 40 AND score < 70").fetchone()[0]
    high = cur.execute("SELECT COUNT(*) FROM resumes WHERE score >= 70").fetchone()[0]

    # Risk distribution
    risk_low = cur.execute("SELECT COUNT(*) FROM resumes WHERE risk_level = 'Low'").fetchone()[0]
    risk_med = cur.execute("SELECT COUNT(*) FROM resumes WHERE risk_level = 'Medium'").fetchone()[0]
    risk_high = cur.execute("SELECT COUNT(*) FROM resumes WHERE risk_level = 'High'").fetchone()[0]

    # Skill counts
    rows = cur.execute("SELECT skills FROM resumes").fetchall()
    from collections import Counter
    skill_counts = Counter()
    for r in rows:
        try:
            skill_counts.update(json.loads(r["skills"]))
        except Exception:
            pass

    total_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_logs = cur.execute("SELECT COUNT(*) FROM logs").fetchone()[0]

    conn.close()

    return {
        "total": total,
        "avg_score": round(avg_score, 1),
        "highest_score": highest,
        "lowest_score": lowest,
        "score_dist": {"0-39": low, "40-69": mid, "70-100": high},
        "risk_dist": {"Low": risk_low, "Medium": risk_med, "High": risk_high},
        "unique_skills": len(skill_counts),
        "top_skills": skill_counts.most_common(10),
        "total_users": total_users,
        "total_logs": total_logs,
    }
