import os
import re
import time
import json
from uuid import uuid4
import logging
from io import BytesIO
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   send_file, session, redirect, url_for, flash)
from werkzeug.utils import secure_filename
from resume_parser import extract_text_from_pdf
from analyzer import (extract_skills, calculate_score, risk_analysis,
                      career_prediction, skill_gap_analysis,
                      simulate_evolution, get_all_skills)
from report_generator import generate_report

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "careerforge-dev-secret-key-2026")

# ---------- Logging Configuration ----------
LOG_FILE = os.path.join(os.path.dirname(__file__), "system.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("CareerForge")
logger.info("CareerForge AI server starting up...")

# ---------- Configuration ----------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users.json")

# Create uploads/ folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Validation Config ----------
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
RESUME_KEYWORDS = re.compile(
    r"\b(education|experience|skills|summary|objective|projects|certifications|achievements|work\s*history)\b",
    re.IGNORECASE,
)

def validate_resume_content(text):
    """Return True if extracted text looks like a resume (>= 2 keyword matches)."""
    matches = set(RESUME_KEYWORDS.findall(text.lower()))
    return len(matches) >= 2

# ---------- In-memory stores ----------
all_candidates = []          # admin analytics
shortlisted_candidates = []  # recruiter decisions
rejected_candidates = []     # recruiter decisions


# ---------- User helpers ----------

def load_users():
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_users(users):
    """Save users dictionary to the JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """Decorator to restrict access to specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                flash("Please login to access this page.", "error")
                return redirect(url_for("login"))
            user_role = session.get("role", "")
            if user_role not in allowed_roles:
                return redirect(url_for("access_denied"))
            return f(*args, **kwargs)
        return decorated
    return decorator


def allowed_file(filename):
    """Return True if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Auth Routes ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "Student")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("register"))

        users = load_users()

        if email in users:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("register"))

        users[email] = {"password": password, "role": role}
        save_users(users)
        logger.info("New user registered: %s (role=%s)", email, role)

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("login"))

        users = load_users()

        if email not in users or users[email]["password"] != password:
            logger.warning("Failed login attempt for: %s", email)
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # Set session
        session["user"] = email
        session["role"] = users[email]["role"]
        logger.info("User logged in: %s (role=%s)", email, users[email]["role"])

        flash(f"Welcome back, {email}!", "success")

        # Role-based redirect
        user_role = users[email]["role"]
        if user_role == "Recruiter":
            return redirect(url_for("recruiter_page"))
        elif user_role == "Admin":
            return redirect(url_for("admin_page"))
        return redirect(url_for("student_dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and redirect to login."""
    session.clear()
    logger.info("User logged out")
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/access-denied")
@login_required
def access_denied():
    """Show access denied page."""
    return render_template("access_denied.html",
                           user=session.get("user"),
                           role=session.get("role"))


# ---------- Main Routes ----------

@app.route("/")
def landing():
    """Render the landing page."""
    return render_template("landing.html")



@app.route("/student")
def student_dashboard():
    """Render the student dashboard (role-guarded, demo bypass)."""
    demo_mode = request.args.get("demo") == "1"
    if not demo_mode:
        if "user" not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for("login"))
        if session.get("role") not in ("Student", "Admin"):
            return redirect(url_for("access_denied"))
    return render_template("index.html",
                           user=session.get("user", "demo@careerforge.com"),
                           role=session.get("role", "Student"),
                           demo_mode=demo_mode)


@app.route("/upload", methods=["POST"])
@login_required
def upload_resume():
    """Handle PDF resume upload with validation."""
    if "resume" not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    # --- Validation 1: Extension ---
    if not allowed_file(file.filename):
        logger.warning("Invalid file type rejected: %s (user=%s)", file.filename, session.get("user"))
        return jsonify({"success": False, "message": "Only PDF files are allowed."}), 400

    # --- Validation 2: File size (2 MB) ---
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        logger.warning("File too large (%d bytes): %s", size, file.filename)
        return jsonify({"success": False, "message": "File exceeds 2 MB limit."}), 400

    # --- Save with UUID prefix for uniqueness ---
    raw_name = secure_filename(file.filename)
    filename = f"{uuid4().hex[:8]}_{raw_name}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)
    logger.info("Student resume uploaded: %s (user=%s)", filename, session.get("user"))

    try:
        extracted_text = extract_text_from_pdf(save_path)

        # --- Validation 3: Resume content heuristic ---
        if not validate_resume_content(extracted_text):
            os.remove(save_path)
            logger.warning("Rejected non-resume PDF: %s", filename)
            return jsonify({"success": False, "message": "This file does not appear to be a resume. Please upload a PDF containing sections like Education, Skills, and Experience."}), 400

        skill_results = extract_skills(extracted_text)
        score_results = calculate_score(skill_results)
        risk_results = risk_analysis(score_results["score"], skill_results["skills"])
        career_results = career_prediction(skill_results["skills"])
        gap_results = skill_gap_analysis(skill_results["skills"])

        result = {
            "success": True,
            "message": f"'{raw_name}' uploaded and analysed successfully!",
            "filename": filename,
            "size_kb": round(os.path.getsize(save_path) / 1024, 1),
            "extracted_text": extracted_text,
            "skills": skill_results["skills"],
            "skills_categorized": skill_results["categorized"],
            "skills_total": skill_results["total"],
            "score": score_results["score"],
            "score_level": score_results["level"],
            "score_reason": score_results["reason"],
            "score_breakdown": score_results["breakdown"],
            "risk_level": risk_results["risk_level"],
            "risk_icon": risk_results["risk_icon"],
            "risk_reason": risk_results["reason"],
            "risk_suggestions": risk_results["suggestions"],
            "career_predictions": career_results,
            "skill_gap": gap_results,
        }

        session['last_analysis'] = result
        logger.info("Student analysis complete: %s | score=%d | skills=%d",
                    filename, score_results["score"], skill_results["total"])
        return jsonify(result)

    except Exception as e:
        logger.error("Error analysing resume %s: %s", filename, str(e))
        return jsonify({"success": False, "message": "Error processing resume. Please ensure it is a valid PDF."}), 500


@app.route("/api/status")
def status():
    """Simple API endpoint to verify the server is running."""
    return jsonify({"status": "ok", "project": "CareerForge AI"})


@app.route("/api/demo-data")
def demo_data():
    """Return pre-analysed sample resume data for demo mode."""
    sample_text = """
    PRIYA SHARMA
    Full Stack Developer | Mumbai, India
    Email: priya.sharma@email.com | LinkedIn: linkedin.com/in/priyasharma

    SUMMARY
    Passionate computer science graduate with hands-on experience in web development
    and data analysis. Seeking a challenging role to leverage my skills in Python,
    machine learning, and cloud computing.

    EDUCATION
    B.E. Computer Science, University of Mumbai (2022-2026) – CGPA: 8.5/10

    SKILLS
    Python, Java, JavaScript, HTML, CSS, SQL, React, Node.js, Flask, Git,
    Machine Learning, Data Analysis, REST API, MongoDB, Docker, AWS, Linux

    EXPERIENCE
    Software Development Intern – TechSolutions Pvt. Ltd. (June 2025 - Dec 2025)
    - Developed RESTful APIs using Flask and Node.js
    - Built responsive frontends with React and JavaScript
    - Implemented CI/CD pipelines using Docker and AWS

    PROJECTS
    1. AI Resume Analyzer – Python, Flask, NLP
    2. E-Commerce Dashboard – React, Node.js, MongoDB
    3. Weather Prediction System – Python, Machine Learning, Data Analysis

    CERTIFICATIONS
    - AWS Cloud Practitioner
    - Google Data Analytics Certificate
    """

    try:
        skill_results = extract_skills(sample_text)
        score_results = calculate_score(skill_results)
        risk_results = risk_analysis(score_results["score"], skill_results["skills"])
        career_results = career_prediction(skill_results["skills"])
        gap_results = skill_gap_analysis(skill_results["skills"])

        result = {
            "success": True,
            "message": "Demo resume analysed successfully!",
            "filename": "demo_resume_priya_sharma.pdf",
            "size_kb": 142.5,
            "extracted_text": sample_text.strip(),
            "skills": skill_results["skills"],
            "skills_categorized": skill_results["categorized"],
            "skills_total": skill_results["total"],
            "score": score_results["score"],
            "score_level": score_results["level"],
            "score_reason": score_results["reason"],
            "score_breakdown": score_results["breakdown"],
            "risk_level": risk_results["risk_level"],
            "risk_icon": risk_results["risk_icon"],
            "risk_reason": risk_results["reason"],
            "risk_suggestions": risk_results["suggestions"],
            "career_predictions": career_results,
            "skill_gap": gap_results,
        }

        # Store for PDF download in demo mode too — per-user session
        session['last_analysis'] = result

        logger.info("Demo mode analysis served")
        return jsonify(result)

    except Exception as e:
        logger.error("Demo data generation failed: %s", str(e))
        return jsonify({"success": False, "message": "Demo data unavailable."}), 500


@app.route("/api/all-skills")
@login_required
def all_skills():
    """Return every skill in the database for the simulator dropdown."""
    return jsonify({"skills": get_all_skills()})


@app.route("/simulate", methods=["POST"])
@login_required
def simulate():
    """Simulate adding a new skill and return before/after comparison."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request."}), 400

    current_skills = data.get("current_skills", [])
    added_skill = data.get("added_skill", "")

    if not added_skill:
        return jsonify({"success": False, "message": "No skill selected."}), 400

    result = simulate_evolution(current_skills, added_skill)
    return jsonify({"success": True, **result})


@app.route("/download-report")
@login_required
def download_report():
    """Generate and download a PDF report of the latest analysis."""
    analysis = session.get('last_analysis')
    if not analysis:
        return jsonify({"success": False, "message": "No analysis available. Upload a resume first."}), 400

    pdf_bytes = generate_report(analysis)
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)

    filename = analysis.get("filename", "resume").rsplit(".", 1)[0]
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{filename}_CareerForge_Report.pdf",
    )


# ---------- Recruiter Routes ----------

@app.route("/recruiter")
@role_required("Recruiter", "Admin")
def recruiter_page():
    """Render the recruiter dashboard."""
    return render_template("recruiter.html",
                           user=session.get("user"),
                           role=session.get("role"))


@app.route("/recruiter-upload", methods=["POST"])
@role_required("Recruiter", "Admin")
def recruiter_upload():
    """Handle multiple PDF resume uploads with validation."""
    files = request.files.getlist("resumes")

    if not files or all(f.filename == "" for f in files):
        flash("No files selected. Please choose at least one PDF resume.", "error")
        return render_template("recruiter.html",
                               user=session.get("user"),
                               role=session.get("role"))

    saved_paths = []
    skipped = 0

    for file in files:
        if file.filename == "" or not allowed_file(file.filename):
            skipped += 1
            continue

        # Size check
        file.seek(0, os.SEEK_END)
        if file.tell() > MAX_FILE_SIZE:
            logger.warning("Recruiter: file too large, skipped: %s", file.filename)
            skipped += 1
            file.seek(0)
            continue
        file.seek(0)

        # UUID-based unique filename
        raw_name = secure_filename(file.filename)
        filename = f"{uuid4().hex[:8]}_{raw_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        saved_paths.append((filename, save_path))

    candidates = []

    for filename, path in saved_paths:
        try:
            text = extract_text_from_pdf(path)

            # Resume content heuristic
            if not validate_resume_content(text):
                logger.warning("Recruiter: rejected non-resume: %s", filename)
                os.remove(path)
                skipped += 1
                continue

            skill_results = extract_skills(text)
            score_results = calculate_score(skill_results)
            risk_results = risk_analysis(score_results["score"], skill_results["skills"])
            career_results = career_prediction(skill_results["skills"])

            # Insight tag based on score
            if score_results["score"] >= 80:
                insight = "Top Candidate"
            elif score_results["score"] >= 50:
                insight = "Strong Match"
            else:
                insight = "Needs Improvement"

            candidates.append({
                "filename": filename,
                "size_kb": round(os.path.getsize(path) / 1024, 1),
                "skills": skill_results["skills"],
                "skills_total": skill_results["total"],
                "score": score_results["score"],
                "score_level": score_results["level"],
                "risk_level": risk_results["risk_level"],
                "risk_icon": risk_results["risk_icon"],
                "career_predictions": career_results,
                "insight": insight,
            })
            logger.info("Recruiter analysis: %s | score=%d", filename, score_results["score"])
        except Exception as e:
            logger.error("Error processing %s: %s", filename, str(e))
            skipped += 1
            continue

    count = len(candidates)
    if count == 0:
        flash("No valid resume PDFs were found in your selection.", "error")
    else:
        candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)
        for rank, candidate in enumerate(candidates, start=1):
            candidate["rank"] = rank

        msg = f"{count} resume{'s' if count != 1 else ''} uploaded and analysed!"
        if skipped:
            msg += f" ({skipped} file{'s' if skipped != 1 else ''} skipped)"
        flash(msg, "success")
        logger.info("Recruiter batch complete: %d resumes (user=%s)", count, session.get("user"))
        all_candidates.extend(candidates)

    return render_template("recruiter.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           uploaded_count=count,
                           candidates=candidates)


@app.route("/recruiter-decision", methods=["POST"])
@role_required("Recruiter", "Admin")
def recruiter_decision():
    """Track shortlist/reject decisions from the recruiter."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False}), 400

    candidate = {
        "filename": data.get("filename", "unknown"),
        "score": data.get("score", 0),
        "risk_level": data.get("risk_level", "unknown"),
        "insight": data.get("insight", ""),
    }
    decision = data.get("decision", "")

    if decision == "shortlisted":
        # Remove from rejected if previously there
        rejected_candidates[:] = [c for c in rejected_candidates if c["filename"] != candidate["filename"]]
        if not any(c["filename"] == candidate["filename"] for c in shortlisted_candidates):
            shortlisted_candidates.append(candidate)
        logger.info("Recruiter shortlisted: %s", candidate["filename"])
    elif decision == "rejected":
        shortlisted_candidates[:] = [c for c in shortlisted_candidates if c["filename"] != candidate["filename"]]
        if not any(c["filename"] == candidate["filename"] for c in rejected_candidates):
            rejected_candidates.append(candidate)
        logger.info("Recruiter rejected: %s", candidate["filename"])

    return jsonify({"success": True, "decision": decision})


@app.route("/recruiter-results")
@role_required("Recruiter", "Admin")
def recruiter_results():
    """Show shortlisted and rejected candidates."""
    return render_template("recruiter_results.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           shortlisted=shortlisted_candidates,
                           rejected=rejected_candidates)


# ---------- Admin Routes ----------

@app.route("/admin")
@role_required("Admin")
def admin_page():
    """Render the admin dashboard with system-wide statistics."""
    total = len(all_candidates)

    # Average score
    avg_score = round(sum(c["score"] for c in all_candidates) / total, 1) if total else 0

    # Top 5 skills across all resumes
    from collections import Counter
    skill_counts = Counter()
    for c in all_candidates:
        skill_counts.update(c["skills"])
    top_skills = skill_counts.most_common(5)

    # Risk distribution
    risk_dist = Counter(c["risk_level"] for c in all_candidates)

    # Score distribution buckets
    score_dist = {"0-39": 0, "40-69": 0, "70-100": 0}
    for c in all_candidates:
        if c["score"] < 40:
            score_dist["0-39"] += 1
        elif c["score"] < 70:
            score_dist["40-69"] += 1
        else:
            score_dist["70-100"] += 1

    # Highest / lowest scores
    highest_score = max((c["score"] for c in all_candidates), default=0)
    lowest_score = min((c["score"] for c in all_candidates), default=0)

    # Total unique skills
    unique_skills = len(skill_counts)

    # Return top 10 skills (enhanced from 5)
    top_skills = skill_counts.most_common(10)

    return render_template("admin.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           total=total,
                           avg_score=avg_score,
                           highest_score=highest_score,
                           lowest_score=lowest_score,
                           unique_skills=unique_skills,
                           top_skills=top_skills,
                           risk_dist=dict(risk_dist),
                           score_dist=score_dist)

# ---------- Logs Route (Admin only) ----------

@app.route("/admin/logs")
@role_required("Admin")
def view_logs():
    """Show the last 50 log entries."""
    lines = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
    return render_template("logs.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           log_lines=lines)


# ---------- Global Error Handlers ----------

@app.errorhandler(404)
def page_not_found(e):
    logger.warning("404 Not Found: %s", request.path)
    return render_template("error.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           error_code=404,
                           error_msg="Page Not Found"), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error("500 Internal Server Error: %s", str(e))
    return render_template("error.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           error_code=500,
                           error_msg="Internal Server Error"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
