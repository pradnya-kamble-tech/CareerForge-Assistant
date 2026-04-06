# database.py — Supabase persistence layer for CareerForge AI

import json
from supabase import create_client, Client

# ---------- Supabase Configuration ----------
SUPABASE_URL = "https://vlwougjxmsjmmurbfjdl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZsd291Z2p4bXNqbW11cmJmamRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwMzMzNzgsImV4cCI6MjA5MDYwOTM3OH0.Ak0zZDSGmT4vL-d7J-Wdzy4IaQvOchWKdaChpla8BsQ"

_supabase: Client = None


def _get_client() -> Client:
    """Lazy-initialise and return the Supabase client."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def init_db():
    """Verify Supabase connection (tables already created via SQL Editor)."""
    try:
        sb = _get_client()
        sb.table("users").select("id").limit(1).execute()
        print("✅ Supabase connected successfully.")
    except Exception as e:
        print(f"⚠️  Supabase connection check failed: {e}")


# ──────────────────── USERS ────────────────────

def db_add_user(email: str, password: str, role: str = "Student"):
    sb = _get_client()
    sb.table("users").insert({
        "email": email.lower(),
        "password": password,
        "role": role,
    }).execute()


def db_get_user(email: str):
    """Return user dict or None."""
    sb = _get_client()
    result = sb.table("users").select("*").eq("email", email.lower()).limit(1).execute()
    if result.data:
        row = result.data[0]
        return {"email": row["email"], "password": row["password"], "role": row["role"]}
    return None


def db_user_exists(email: str) -> bool:
    return db_get_user(email) is not None


def db_count_users():
    sb = _get_client()
    result = sb.table("users").select("id", count="exact").execute()
    return result.count or 0


# ──────────────────── RESUMES ────────────────────

def db_add_resume(data):
    """Insert a resume record. `data` is a dict with candidate fields."""
    sb = _get_client()
    sb.table("resumes").insert({
        "filename": data.get("filename", ""),
        "score": data.get("score", 0),
        "score_level": data.get("score_level", ""),
        "risk_level": data.get("risk_level", ""),
        "risk_icon": data.get("risk_icon", ""),
        "skills": json.dumps(data.get("skills", [])),
        "skills_total": data.get("skills_total", 0),
        "career_preds": json.dumps(data.get("career_predictions", [])),
        "insight": data.get("insight", ""),
        "owner": data.get("owner", ""),
    }).execute()


def db_get_resumes(owner=None):
    """Return list of resume dicts. If owner given, filter by it."""
    sb = _get_client()
    query = sb.table("resumes").select("*").order("score", desc=True)
    if owner:
        query = query.eq("owner", owner)
    result = query.execute()
    results = []
    for r in result.data:
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
    sb = _get_client()
    result = sb.table("resumes").select("id", count="exact").execute()
    return result.count or 0


# ──────────────────── DECISIONS ────────────────────

def db_add_decision(data):
    """Upsert a shortlist/reject decision for a candidate."""
    sb = _get_client()
    # Remove any previous decision for this file by this owner
    sb.table("decisions").delete().eq(
        "filename", data.get("filename", "")
    ).eq(
        "owner", data.get("owner", "")
    ).execute()

    sb.table("decisions").insert({
        "filename": data.get("filename", ""),
        "score": data.get("score", 0),
        "risk_level": data.get("risk_level", ""),
        "insight": data.get("insight", ""),
        "owner": data.get("owner", ""),
        "decision": data.get("decision", "pending"),
    }).execute()


def db_get_decisions(owner, decision_type=None):
    """Return decisions for an owner, optionally filtered by type."""
    sb = _get_client()
    query = sb.table("decisions").select("*").eq("owner", owner).order("id", desc=True)
    if decision_type:
        query = query.eq("decision", decision_type)
    result = query.execute()
    return result.data


# ──────────────────── LOGS ────────────────────

def db_add_log(action, user="system", detail=""):
    """Insert a log entry."""
    try:
        sb = _get_client()
        sb.table("logs").insert({
            "action": action,
            "user": user,
            "detail": detail,
        }).execute()
    except Exception:
        pass  # Don't crash the app if logging fails


def db_get_logs(limit=50):
    """Return recent log entries."""
    sb = _get_client()
    result = sb.table("logs").select("*").order("id", desc=True).limit(limit).execute()
    return result.data


def db_count_logs():
    sb = _get_client()
    result = sb.table("logs").select("id", count="exact").execute()
    return result.count or 0


# ──────────────────── ADMIN STATS ────────────────────

def db_get_admin_stats():
    """Return aggregated stats for the admin dashboard."""
    sb = _get_client()

    # Get all resumes
    all_resumes = sb.table("resumes").select("score,risk_level,skills").execute().data

    total = len(all_resumes)
    scores = [r["score"] for r in all_resumes]
    avg_score = round(sum(scores) / total, 1) if total else 0
    highest = max(scores) if scores else 0
    lowest = min(scores) if scores else 0

    # Score distribution
    low = sum(1 for s in scores if s < 40)
    mid = sum(1 for s in scores if 40 <= s < 70)
    high = sum(1 for s in scores if s >= 70)

    # Risk distribution
    risk_low = sum(1 for r in all_resumes if r.get("risk_level") == "Low")
    risk_med = sum(1 for r in all_resumes if r.get("risk_level") == "Medium")
    risk_high = sum(1 for r in all_resumes if r.get("risk_level") == "High")

    # Skill counts
    from collections import Counter
    skill_counts = Counter()
    for r in all_resumes:
        try:
            skill_counts.update(json.loads(r["skills"]))
        except Exception:
            pass

    total_users = db_count_users()
    total_logs = db_count_logs()

    return {
        "total": total,
        "avg_score": avg_score,
        "highest_score": highest,
        "lowest_score": lowest,
        "score_dist": {"0-39": low, "40-69": mid, "70-100": high},
        "risk_dist": {"Low": risk_low, "Medium": risk_med, "High": risk_high},
        "unique_skills": len(skill_counts),
        "top_skills": skill_counts.most_common(10),
        "total_users": total_users,
        "total_logs": total_logs,
    }


# ──────────────────── RECRUITER STATS ────────────────────

def db_get_recruiter_stats(owner):
    """Return recruiter-specific dashboard stats."""
    sb = _get_client()

    # All resumes by this recruiter
    resumes = sb.table("resumes").select("score,risk_level,created_at").eq("owner", owner).execute().data
    total = len(resumes)
    scores = [r["score"] for r in resumes]
    avg_score = round(sum(scores) / total, 1) if total else 0
    top_matches = sum(1 for s in scores if s >= 80)

    # Decisions by this recruiter
    decisions = sb.table("decisions").select("decision").eq("owner", owner).execute().data
    shortlisted = sum(1 for d in decisions if d["decision"] == "shortlisted")
    rejected = sum(1 for d in decisions if d["decision"] == "rejected")
    pending = total - shortlisted - rejected
    if pending < 0:
        pending = 0

    # Hiring success rate
    success_rate = round(shortlisted / total * 100, 1) if total else 0

    # Risk distribution for attrition
    risk_high = sum(1 for r in resumes if r.get("risk_level") == "High")
    attrition_pct = round(risk_high / total * 100, 1) if total else 0

    return {
        "total": total,
        "avg_score": avg_score,
        "top_matches": top_matches,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "pending": pending,
        "success_rate": success_rate,
        "quality_of_hire": avg_score,
        "attrition_risk": attrition_pct,
    }


def db_get_top_candidates(owner, limit=5):
    """Return top N candidates by score for a recruiter."""
    sb = _get_client()
    result = sb.table("resumes").select("filename,score,risk_level,skills_total,created_at").eq(
        "owner", owner
    ).order("score", desc=True).limit(limit).execute()
    return result.data


def db_get_recent_activity(owner, limit=5):
    """Return recent log entries for a recruiter."""
    sb = _get_client()
    result = sb.table("logs").select("*").eq("user", owner).order("id", desc=True).limit(limit).execute()
    return result.data


# ──────────────────── ADMIN EXTENDED ────────────────────

def db_get_all_users():
    """Return all users for admin user management."""
    sb = _get_client()
    result = sb.table("users").select("email,role,created_at").order("id", desc=True).execute()
    return result.data


def db_get_logs_filtered(action_filter=None, limit=50):
    """Return logs optionally filtered by action type."""
    sb = _get_client()
    query = sb.table("logs").select("*").order("id", desc=True).limit(limit)
    if action_filter and action_filter != "all":
        query = query.eq("action", action_filter)
    return query.execute().data

