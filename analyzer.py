# analyzer.py — Keyword-based skill extraction from resume text

import json
import os
import re


# Path to the skills database
SKILLS_FILE = os.path.join(os.path.dirname(__file__), "data", "skills.json")


def load_skills():
    """Load the skills database from skills.json."""
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["categories"]


def extract_skills(resume_text: str) -> dict:
    """
    Match skills from resume text against the skills database.

    Args:
        resume_text (str): Full text extracted from the resume.

    Returns:
        dict: {
            "skills": [list of matched skill names],
            "categorized": {category: [matched skills], ...},
            "total": int
        }
    """
    categories = load_skills()
    text_lower = resume_text.lower()

    matched_skills = []          # flat list (no duplicates)
    categorized = {}             # grouped by category

    for category, skills_list in categories.items():
        found_in_category = []
        for skill in skills_list:
            # Use word-boundary matching so "C" doesn't match inside "Communication"
            # For short skills (<=2 chars), require exact standalone match
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                if skill not in matched_skills:
                    matched_skills.append(skill)
                found_in_category.append(skill)

        if found_in_category:
            # Pretty-print category name: "data_science_and_ai" -> "Data Science And Ai"
            nice_name = category.replace("_", " ").title()
            categorized[nice_name] = found_in_category

    return {
        "skills": matched_skills,
        "categorized": categorized,
        "total": len(matched_skills),
    }


def calculate_score(skill_results: dict) -> dict:
    """
    Calculate a resume score (0-100) based on detected skills.

    Scoring breakdown:
        - Base score from skill count (0-70 pts)
        - Category diversity bonus  (0-30 pts)

    Args:
        skill_results (dict): Output from extract_skills().

    Returns:
        dict: {
            "score": int,
            "level": str,
            "reason": str,
            "breakdown": dict
        }
    """
    total = skill_results["total"]
    num_categories = len(skill_results["categorized"])

    # --- Base score from skill count (max 70) ---
    if total == 0:
        base = 0
    elif total <= 2:
        base = 15 + (total * 5)       # 20-25
    elif total <= 5:
        base = 25 + (total * 5)       # 40-50
    elif total <= 9:
        base = 35 + (total * 4)       # 59-71  →  cap at 70
    else:
        base = min(50 + (total * 2), 70)
    base = min(base, 70)

    # --- Category diversity bonus (max 30) ---
    diversity = min(num_categories * 5, 30)

    score = min(base + diversity, 100)

    # --- Level ---
    if score <= 35:
        level = "Low"
    elif score <= 60:
        level = "Medium"
    elif score <= 80:
        level = "High"
    else:
        level = "Excellent"

    # --- Explainable reason ---
    reasons = []
    reasons.append(f"Your resume mentions {total} recognised skill(s).")
    reasons.append(f"Skills span {num_categories} categor{'y' if num_categories == 1 else 'ies'}.")

    if total <= 2:
        reasons.append("Consider adding more technical and soft skills to strengthen your profile.")
    elif total <= 5:
        reasons.append("Decent skill set — adding more domain-specific skills could boost your score.")
    elif total <= 9:
        reasons.append("Strong skill coverage. Try diversifying across more categories for an even higher score.")
    else:
        reasons.append("Excellent breadth of skills across multiple domains!")

    if num_categories <= 2:
        reasons.append("Tip: Broaden your skill categories (e.g., add cloud, databases, or soft skills).")
    elif num_categories >= 5:
        reasons.append("Great diversity — your profile covers multiple technology areas.")

    return {
        "score": score,
        "level": level,
        "reason": " ".join(reasons),
        "breakdown": {
            "skill_score": base,
            "diversity_bonus": diversity,
            "skills_detected": total,
            "categories_covered": num_categories,
        },
    }


def risk_analysis(score: int, skills: list) -> dict:
    """
    Determine the risk level of a resume based on score and detected skills.

    Args:
        score  (int):  Resume score out of 100.
        skills (list): List of matched skill names.

    Returns:
        dict: {
            "risk_level": str,
            "risk_icon": str,
            "reason": str,
            "suggestions": list[str]
        }
    """
    total = len(skills)

    # --- Risk level ---
    if score < 40:
        risk_level = "High"
        risk_icon = "high"
    elif score <= 70:
        risk_level = "Medium"
        risk_icon = "medium"
    else:
        risk_level = "Low"
        risk_icon = "low"

    # --- Explanation ---
    reasons = []
    reasons.append(f"Resume score is {score}/100 with {total} skill(s) detected.")

    if risk_level == "High":
        reasons.append("This indicates a significant gap between your profile and industry expectations.")
    elif risk_level == "Medium":
        reasons.append("Your profile meets basic requirements but has room for improvement.")
    else:
        reasons.append("Your profile demonstrates strong alignment with industry skill demands.")

    # --- Actionable suggestions ---
    suggestions = []
    if total <= 3:
        suggestions.append("Add more technical skills (e.g., Python, SQL, cloud platforms).")
    if total <= 6:
        suggestions.append("Include relevant certifications or project experience.")
    if score < 60:
        suggestions.append("Diversify skills across multiple categories for a stronger profile.")
    if score >= 70:
        suggestions.append("Consider tailoring skills to specific job descriptions for even better results.")
    if not suggestions:
        suggestions.append("Your resume looks well-rounded - keep it updated with new skills!")

    return {
        "risk_level": risk_level,
        "risk_icon": risk_icon,
        "reason": " ".join(reasons),
        "suggestions": suggestions,
    }


# ---------- Career role mappings ----------
ROLE_MAP = [
    {
        "role": "Data Scientist",
        "icon": "DS",
        "skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow",
                   "PyTorch", "Pandas", "NumPy", "Scikit-learn", "Data Analysis",
                   "Data Visualization", "R", "MATLAB"],
    },
    {
        "role": "Frontend Developer",
        "icon": "FE",
        "skills": ["HTML", "CSS", "JavaScript", "React", "Angular", "Vue.js",
                   "TypeScript", "Bootstrap", "Tailwind CSS", "SASS", "Next.js"],
    },
    {
        "role": "Backend Developer",
        "icon": "BE",
        "skills": ["Python", "Java", "Node.js", "Flask", "Django", "Spring Boot",
                   "Express.js", "SQL", "REST API", "GraphQL", "Go", "PHP"],
    },
    {
        "role": "Full-Stack Developer",
        "icon": "FS",
        "skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Python",
                   "Flask", "Django", "SQL", "MongoDB", "REST API", "Git"],
    },
    {
        "role": "Data Analyst",
        "icon": "DA",
        "skills": ["Python", "SQL", "Pandas", "Data Analysis", "Data Visualization",
                   "Matplotlib", "Seaborn", "Excel", "R", "MySQL", "PostgreSQL"],
    },
    {
        "role": "DevOps Engineer",
        "icon": "DO",
        "skills": ["Docker", "Kubernetes", "AWS", "Azure", "Google Cloud",
                   "CI/CD", "Jenkins", "Linux", "Git", "Terraform", "Nginx"],
    },
    {
        "role": "Mobile App Developer",
        "icon": "MA",
        "skills": ["Android", "iOS", "React Native", "Flutter", "Kotlin",
                   "Swift", "Dart", "Java", "Firebase"],
    },
    {
        "role": "AI / ML Engineer",
        "icon": "ML",
        "skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow",
                   "PyTorch", "Keras", "Natural Language Processing",
                   "Computer Vision", "Neural Networks", "OpenCV"],
    },
    {
        "role": "Database Administrator",
        "icon": "DB",
        "skills": ["SQL", "MySQL", "PostgreSQL", "MongoDB", "Oracle", "Redis",
                   "SQLite", "Firebase", "Cassandra", "DynamoDB"],
    },
    {
        "role": "Cloud Engineer",
        "icon": "CE",
        "skills": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
                   "Terraform", "Linux", "CI/CD", "Heroku", "Netlify"],
    },
]


def career_prediction(skills):
    """
    Predict suitable career roles based on detected skills.

    Args:
        skills (list): List of matched skill names from the resume.

    Returns:
        list[dict]: Sorted list of role predictions, each with:
            role, icon, match_percentage, matched_skills, reason
    """
    skills_set = {s.lower() for s in skills}
    predictions = []

    for role_def in ROLE_MAP:
        role_skills = {s.lower() for s in role_def["skills"]}
        matched = skills_set & role_skills
        if not matched:
            continue

        pct = round((len(matched) / len(role_skills)) * 100)

        # Get original-case names for display
        matched_display = [s for s in role_def["skills"] if s.lower() in matched]

        reason = (
            f"Based on your skills: {', '.join(matched_display)}. "
            f"You match {len(matched)} of {len(role_skills)} key skills for this role."
        )

        predictions.append({
            "role": role_def["role"],
            "icon": role_def["icon"],
            "match_percentage": pct,
            "matched_skills": matched_display,
            "reason": reason,
        })

    # Sort by match percentage descending
    predictions.sort(key=lambda x: x["match_percentage"], reverse=True)
    return predictions


def skill_gap_analysis(current_skills):
    """
    Identify important skills missing from the user's resume by comparing
    detected skills against the ideal skill sets defined in ROLE_MAP.

    Args:
        current_skills (list): List of matched skill names from the resume.

    Returns:
        dict: {
            "target_role": str,
            "target_icon": str,
            "missing_skills": list[dict],
            "recommended_skills": list[dict],
            "summary": str,
            "gap_percentage": int
        }
    """
    skills_lower = {s.lower() for s in current_skills}

    # --- Find the best-matched role (highest overlap) ---
    best_role = None
    best_matched = 0
    for role_def in ROLE_MAP:
        role_skills = {s.lower() for s in role_def["skills"]}
        overlap = len(skills_lower & role_skills)
        if overlap > best_matched:
            best_matched = overlap
            best_role = role_def

    # Fallback to Full-Stack Developer if no role matches at all
    if best_role is None:
        best_role = ROLE_MAP[3]  # Full-Stack Developer

    # --- Missing skills for the target role ---
    role_skills_lower = {s.lower() for s in best_role["skills"]}
    missing_lower = role_skills_lower - skills_lower
    missing_skills = [s for s in best_role["skills"] if s.lower() in missing_lower]

    # Gap percentage = how far the user is from completing the ideal set
    total_role_skills = len(best_role["skills"])
    matched_count = total_role_skills - len(missing_skills)
    gap_pct = round((len(missing_skills) / total_role_skills) * 100) if total_role_skills else 0

    # --- Recommended skills from *other* top roles ---
    # Gather missing skills from the top-3 matched roles for broader suggestions
    recommendations = {}
    for role_def in ROLE_MAP:
        if role_def["role"] == best_role["role"]:
            continue
        role_skills = {s.lower() for s in role_def["skills"]}
        overlap = len(skills_lower & role_skills)
        if overlap == 0:
            continue
        for skill in role_def["skills"]:
            if skill.lower() not in skills_lower and skill not in missing_skills:
                if skill not in recommendations:
                    recommendations[skill] = {
                        "skill": skill,
                        "reason": f"Important for {role_def['role']} role",
                        "from_role": role_def["role"],
                        "icon": role_def["icon"],
                    }

    # Sort by role relevance, take top 6
    recommended_list = list(recommendations.values())[:6]

    # --- Build missing_skills with explanations ---
    missing_with_reasons = []
    for skill in missing_skills:
        priority = "High" if skill.lower() in {"python", "javascript", "sql", "git",
                                                 "html", "css", "react", "node.js",
                                                 "docker", "aws", "machine learning"} else "Medium"
        missing_with_reasons.append({
            "skill": skill,
            "priority": priority,
            "reason": f"Core requirement for {best_role['role']}",
        })

    # Sort: High priority first
    missing_with_reasons.sort(key=lambda x: 0 if x["priority"] == "High" else 1)

    # --- Summary explanation ---
    parts = []
    parts.append(f"Your resume best aligns with the **{best_role['role']}** role "
                 f"({matched_count}/{total_role_skills} skills matched).")
    if missing_skills:
        parts.append(f"You are missing {len(missing_skills)} key skill(s): "
                     f"{', '.join(missing_skills[:5])}"
                     f"{'...' if len(missing_skills) > 5 else ''}.")
    else:
        parts.append("You have all the core skills for this role!")
    if recommended_list:
        parts.append(f"We also recommend learning {', '.join(r['skill'] for r in recommended_list[:3])} "
                     f"to broaden your career options.")

    return {
        "target_role": best_role["role"],
        "target_icon": best_role["icon"],
        "missing_skills": missing_with_reasons,
        "recommended_skills": recommended_list,
        "summary": " ".join(parts),
        "gap_percentage": gap_pct,
        "matched_count": matched_count,
        "total_role_skills": total_role_skills,
    }


def get_all_skills():
    """Return a flat sorted list of every skill in the database."""
    categories = load_skills()
    all_skills = []
    for skill_list in categories.values():
        all_skills.extend(skill_list)
    return sorted(set(all_skills))


def simulate_evolution(current_skills, added_skill):
    """
    Simulate what happens when a new skill is added to the resume.

    Args:
        current_skills (list): Current detected skills.
        added_skill    (str):  The new skill to add.

    Returns:
        dict with before/after comparison and improvement explanation.
    """
    # --- BEFORE ---
    before_skill_results = {
        "skills": list(current_skills),
        "categorized": {},
        "total": len(current_skills),
    }
    # rebuild categorized for before
    categories = load_skills()
    for cat, slist in categories.items():
        found = [s for s in current_skills if s.lower() in {sk.lower() for sk in slist}]
        if found:
            before_skill_results["categorized"][cat.replace("_", " ").title()] = found

    before_score = calculate_score(before_skill_results)
    before_risk  = risk_analysis(before_score["score"], current_skills)
    before_career = career_prediction(current_skills)

    # --- ADD SKILL ---
    updated_skills = list(current_skills)
    already_present = added_skill.lower() in {s.lower() for s in updated_skills}
    if not already_present:
        updated_skills.append(added_skill)

    # --- AFTER ---
    after_skill_results = {
        "skills": updated_skills,
        "categorized": {},
        "total": len(updated_skills),
    }
    for cat, slist in categories.items():
        found = [s for s in updated_skills if s.lower() in {sk.lower() for sk in slist}]
        if found:
            after_skill_results["categorized"][cat.replace("_", " ").title()] = found

    after_score  = calculate_score(after_skill_results)
    after_risk   = risk_analysis(after_score["score"], updated_skills)
    after_career = career_prediction(updated_skills)

    # --- Improvement explanation ---
    score_diff = after_score["score"] - before_score["score"]
    reasons = []
    if already_present:
        reasons.append(f"'{added_skill}' is already in your profile — no change.")
    else:
        reasons.append(f"Adding '{added_skill}' increased your skill count to {len(updated_skills)}.")
        if score_diff > 0:
            reasons.append(f"Score improved by +{score_diff} points ({before_score['score']} -> {after_score['score']}).")
        if before_risk["risk_level"] != after_risk["risk_level"]:
            reasons.append(f"Risk level changed from {before_risk['risk_level']} to {after_risk['risk_level']}.")
        # new career roles
        before_roles = {p["role"] for p in before_career}
        new_roles = [p for p in after_career if p["role"] not in before_roles]
        if new_roles:
            reasons.append(f"New career path unlocked: {', '.join(r['role'] for r in new_roles)}.")

    return {
        "added_skill": added_skill,
        "already_present": already_present,
        "before": {
            "score": before_score["score"],
            "level": before_score["level"],
            "risk": before_risk["risk_level"],
            "risk_icon": before_risk["risk_icon"],
            "careers": len(before_career),
        },
        "after": {
            "score": after_score["score"],
            "level": after_score["level"],
            "risk": after_risk["risk_level"],
            "risk_icon": after_risk["risk_icon"],
            "careers": len(after_career),
            "career_predictions": after_career[:5],
        },
        "improvement": " ".join(reasons),
    }
