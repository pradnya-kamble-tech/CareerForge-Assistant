import os
import time
import json
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

# Store latest analysis for PDF report download
last_analysis = {}

# Store all processed candidates for admin dashboard stats
all_candidates = []


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
        return redirect(url_for("home"))

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
@login_required
def home():
    """Render the homepage."""
    return render_template("index.html",
                           user=session.get("user"),
                           role=session.get("role"))


@app.route("/upload", methods=["POST"])
@login_required
def upload_resume():
    """Handle PDF resume upload."""
    # Check if a file was included in the request
    if "resume" not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files["resume"]

    # Check if user actually selected a file
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    # Validate extension
    if not allowed_file(file.filename):
        logger.warning("Invalid file type rejected: %s (user=%s)", file.filename, session.get("user"))
        return jsonify({"success": False, "message": "Only PDF files are allowed."}), 400

    # Save the file
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)
    logger.info("Student resume uploaded: %s (user=%s)", filename, session.get("user"))

    try:
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(save_path)

        # Extract skills from the text
        skill_results = extract_skills(extracted_text)

        # Calculate resume score
        score_results = calculate_score(skill_results)

        # Risk analysis
        risk_results = risk_analysis(score_results["score"], skill_results["skills"])

        # Career trajectory prediction
        career_results = career_prediction(skill_results["skills"])

        # Skill gap analysis
        gap_results = skill_gap_analysis(skill_results["skills"])

        result = {
            "success": True,
            "message": f"✅ '{filename}' uploaded and analysed successfully!",
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

        # Store for PDF download
        last_analysis.update(result)
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
    if not last_analysis:
        return jsonify({"success": False, "message": "No analysis available. Upload a resume first."}), 400

    pdf_bytes = generate_report(last_analysis)
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)

    filename = last_analysis.get("filename", "resume").rsplit(".", 1)[0]
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
    """Handle multiple PDF resume uploads and analyse each one.

    - Accepts files from <input name="resumes" multiple>
    - Validates & saves each PDF (with timestamp deduplication)
    - Runs the EXISTING analysis pipeline on every resume
    - Passes a candidates[] list to recruiter.html for display
    """
    files = request.files.getlist("resumes")

    # Guard: no files submitted at all
    if not files or all(f.filename == "" for f in files):
        flash("No files selected. Please choose at least one PDF resume.", "error")
        return render_template("recruiter.html",
                               user=session.get("user"),
                               role=session.get("role"))

    saved_paths = []

    for file in files:
        if file.filename == "":
            continue
        if not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)

        # Avoid overwriting: append timestamp if file already exists
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(save_path):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(time.time())}{ext}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(save_path)
        saved_paths.append((filename, save_path))

    # ---------- Step 3: Analyse each resume ----------
    candidates = []

    for filename, path in saved_paths:
        try:
            # 1. Extract text (parser.py)
            text = extract_text_from_pdf(path)

            # 2. Extract skills (analyzer.py)
            skill_results = extract_skills(text)

            # 3. Score
            score_results = calculate_score(skill_results)

            # 4. Risk
            risk_results = risk_analysis(score_results["score"], skill_results["skills"])

            # 5. Career prediction
            career_results = career_prediction(skill_results["skills"])

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
            })
            logger.info("Recruiter analysis: %s | score=%d", filename, score_results["score"])
        except Exception as e:
            logger.error("Error processing %s: %s", filename, str(e))
            continue  # skip bad files gracefully

    count = len(candidates)
    if count == 0:
        flash("No valid PDF files were found in your selection.", "error")
    else:
        # ---------- Step 4: Rank candidates by score (highest first) ----------
        candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)
        for rank, candidate in enumerate(candidates, start=1):
            candidate["rank"] = rank

        flash(f"{count} resume{'s' if count != 1 else ''} uploaded and analysed!", "success")
        logger.info("Recruiter batch complete: %d resumes (user=%s)", count, session.get("user"))

        # Persist for admin dashboard stats
        all_candidates.extend(candidates)

    return render_template("recruiter.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           uploaded_count=count,
                           candidates=candidates)


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

@app.route("/logs")
@role_required("Admin")
def view_logs():
    """Show the last 100 log entries."""
    lines = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]
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
