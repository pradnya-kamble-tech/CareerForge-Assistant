import math
import re

# Backward compatibility imports for app.py
from resume_parser import extract_text_from_pdf

def validate_resume_content(text):
    """
    Fallback validation.
    Returns True if the text looks like a resume.
    """
    return text and len(text.strip()) >= 50

from ai_engine.modules.m5_skill_extractor import extract_skills as extract_skills_ai
from ai_engine.modules.m5_skill_extractor import get_all_skills as get_all_skills_ai
from ai_engine.modules.m6_scoring import calculate_score as calculate_score_ai
from ai_engine.modules.m4_role_classifier import predict_role
from ai_engine.modules.m7_risk import predict_risk as predict_risk_ai
from ai_engine.modules.m9_trajectory import predict_trajectory
from ai_engine.modules.m10_simulator import simulate as simulate_ai
from ai_engine.modules.m11_explainer import explain
from ai_engine.modules.m12_storage import build_output
from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap, preload as _preload_knowledge

# Pre-warm the role knowledge cache at import time (fast after first build)
try:
    _preload_knowledge()
except Exception:
    pass  # Don't crash on import if CSV is unavailable

# ==========================================
# MASTER ENTRY POINT FOR AI PIPELINE
# ==========================================
def analyze_resume_ai(resume_text, jd_text=None):
    """
    Run the full AI pipeline on a resume text.
    Uses dataset-driven role knowledge for skill gap and role profile.
    """
    if not resume_text or len(resume_text.strip()) < 50:
        return {"error": "Resume text too short or empty for AI analysis."}

    # 1. AI Extract Skills
    skills_result = extract_skills_ai(resume_text)

    # 2. AI Predict Role
    role_result = predict_role(resume_text)

    # 3. AI Calculate Score
    score_result = calculate_score_ai(resume_text, skills_result, role_result)

    # 4. AI Predict Risk
    risk_result = predict_risk_ai(score_result, skills_result, resume_text)

    # 5. AI Predict Career Trajectory
    trajectory_result = predict_trajectory(role_result.get("predicted_role"), skills_result)

    # 6. AI Explainability
    explainer_result = explain(resume_text, role_result, score_result, risk_result)

    # 7. (Optional) JD Matching if provided
    jd_match_result = None
    if jd_text:
        from ai_engine.modules.m8_matching import match_resume_to_jd
        jd_match_result = match_resume_to_jd(resume_text, jd_text)

    # 8. Dataset-driven role knowledge and skill gap
    raw_role = role_result.get("raw_role", role_result.get("predicted_role", ""))
    role_knowledge_data = get_role_knowledge(raw_role)
    skill_gap_data = get_skill_gap(skills_result.get("skills", []), raw_role)

    # 9. Standardize Output (pass role knowledge for role_profile)
    output = build_output(
        role_result, skills_result, score_result, risk_result,
        trajectory_result, explainer_result, jd_match_result,
        role_knowledge_data=role_knowledge_data,
        resume_text=resume_text,
    )

    # 10. Attach data-driven skill gap (replaces trajectory-based gap)
    output["skill_gap"] = skill_gap_data

    return output

# ==========================================
# LEGACY WRAPPERS FOR APP.PY COMPATIBILITY
# ==========================================
def extract_skills(text):
    """Legacy wrapper for backward compatibility."""
    return extract_skills_ai(text)

def extract_skills_categorized(text):
    return extract_skills_ai(text)

def get_all_skills():
    return get_all_skills_ai()

def calculate_score(skill_results, text=""):
    """
    Legacy wrapper. In V1, it just took a dict.  
    We mock a full run if only a dict is provided, but ideally 
    app.py should now call analyze_resume_ai directly.
    """
    if isinstance(skill_results, list):
        skill_results = {"skills": skill_results, "total": len(skill_results)}
    
    role = predict_role(text) if text else {"predicted_role": "Unknown", "confidence": 0}
    return calculate_score_ai(text, skill_results, role)

def risk_analysis(score, skills):
    """Legacy wrapper."""
    skill_dict = {"skills": skills, "total": len(skills)} if isinstance(skills, list) else skills
    score_dict = {"total_score": score, "score": score, "dimensions": {}} if isinstance(score, (int, float)) else score
    return predict_risk_ai(score_dict, skill_dict, "")

def career_prediction(skills):
    """Legacy wrapper — derives career predictions from skills list."""
    if not skills:
        return []
    # Build a pseudo-resume text from skills so we can run full AI pipeline
    if isinstance(skills, list):
        skill_text = " ".join(skills)
    elif isinstance(skills, dict):
        all_s = []
        for arr in skills.values():
            if isinstance(arr, list):
                all_s.extend(arr)
        skill_text = " ".join(all_s)
    else:
        skill_text = str(skills)

    pseudo_text = (
        "SKILLS\n" + skill_text + "\n"
        "EXPERIENCE\nSoftware Development\nProjects\nEducation"
    )
    try:
        from ai_engine.modules.m4_role_classifier import predict_role
        from ai_engine.role_knowledge import get_role_knowledge
        role_result = predict_role(pseudo_text)
        # Build career predictions from top_3 roles
        predictions = []
        for entry in role_result.get("top_3", []):
            role_name = entry["role"]
            prob = entry["probability"]
            rk = get_role_knowledge(role_name)
            top_skills = rk.get("top_skills", [])[:5]
            if isinstance(skills, list):
                flat_skills = [s.lower() for s in skills]
            else:
                flat_skills = [s.lower() for arr in (skills.values() if isinstance(skills, dict) else []) for s in (arr if isinstance(arr, list) else [])]
            matched = [s for s in top_skills if s.lower() in flat_skills or any(s.lower() in sk for sk in flat_skills)]
            match_pct = int(prob * 100)
            predictions.append({
                "role": role_name,
                "match_percentage": match_pct,
                "matched_skills": matched,
                "reason": f"{len(matched)} of {len(top_skills)} key skills matched for this role.",
            })
        return predictions
    except Exception:
        return []


def skill_gap_analysis(skills):
    """Legacy wrapper — derives skill gap from skills list."""
    if not skills:
        return {}
    if isinstance(skills, list):
        flat_skills = skills
    elif isinstance(skills, dict):
        flat_skills = [s for arr in skills.values() for s in (arr if isinstance(arr, list) else [])]
    else:
        flat_skills = []
    try:
        from ai_engine.role_knowledge import get_skill_gap
        # Use best-guess role from career prediction
        preds = career_prediction(skills)
        top_role = preds[0]["role"] if preds else ""
        return get_skill_gap(flat_skills, top_role)
    except Exception:
        return {}


def simulate_evolution(current_skills, added_skill=""):
    """Wrapper for digital twin. Accepts (current_skills_list, added_skill_str)."""
    # Build pseudo resume text from the skills list
    if isinstance(current_skills, list):
        skill_text = " ".join(str(s) for s in current_skills)
    elif isinstance(current_skills, str):
        skill_text = current_skills
    else:
        skill_text = ""
    pseudo_resume = (
        "SKILLS\n" + skill_text + "\n"
        "EXPERIENCE\nSoftware Developer\nProjects\nEducation\nCertifications"
    )
    return simulate_ai(pseudo_resume, str(added_skill))

def fetch_skill_data():
    """Legacy wrapper to fetch raw db."""
    import os
    db_path = os.path.join(os.path.dirname(__file__), "ai_engine", "models", "skill_db.json")
    if os.path.exists(db_path):
        import json
        with open(db_path, "r") as f:
            return json.load(f)
    return {}
