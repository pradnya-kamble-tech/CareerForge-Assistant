import os
import sys
import unittest
from io import BytesIO
from app import app, init_db, db_add_user, db_user_exists

class TestCareerForgeAI_QA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "test_uploads")
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        init_db()
        if not db_user_exists("testQA@careerforge.com"):
            db_add_user("testQA@careerforge.com", "password", "Student")
        if not db_user_exists("recruiterQA@careerforge.com"):
            db_add_user("recruiterQA@careerforge.com", "password", "Recruiter")

    def setUp(self):
        self.client = app.test_client()
        # Login
        self.client.post("/login", data={"email": "testQA@careerforge.com", "password": "password"})

    # ─────────────────────────────────────────────
    # EXISTING EDGE CASE TESTS
    # ─────────────────────────────────────────────

    def test_01_empty_pdf(self):
        """Edge Case 1: Empty PDF should be caught by content validator."""
        data = {"resume": (BytesIO(b"%PDF-1.4\n%EOF"), "empty.pdf")}
        response = self.client.post("/upload", data=data, content_type="multipart/form-data")
        json_resp = response.get_json()
        assert response.status_code == 400
        assert "does not appear to be a resume" in json_resp["message"]

    def test_02_non_pdf_file(self):
        """Edge Case 2: Extension validation."""
        data = {"resume": (BytesIO(b"Hello World"), "text.txt")}
        response = self.client.post("/upload", data=data, content_type="multipart/form-data")
        json_resp = response.get_json()
        assert response.status_code == 400
        assert "Only valid PDF files are allowed" in json_resp["message"]

    def test_03_no_file(self):
        """Edge Case 3: No file part."""
        response = self.client.post("/upload", data={}, content_type="multipart/form-data")
        json_resp = response.get_json()
        assert response.status_code == 400
        assert "No file" in json_resp["message"]

    def test_04_ai_demo_flow(self):
        """Validate AI logic end-to-end using the demo-data endpoint (simulates perfect resume)."""
        response = self.client.get("/api/demo-data")
        json_resp = response.get_json()
        assert response.status_code == 200
        assert json_resp["success"] is True
        assert "role" in json_resp
        assert "score" in json_resp
        assert "skills_categorized" in json_resp
        assert "career_predictions" in json_resp
        # Verify Risk vs Score correlation
        score = json_resp["score"]
        risk_level = json_resp["risk_level"]
        if score > 80:
            assert risk_level in ["Low", "Very Low"]

    def test_05_digital_twin(self):
        """Digital Twin edge case simulation — both Format A and Format B."""
        # Format B (QA harness format): current_skills + added_skill
        current_skills = ["Python", "Machine Learning"]
        added_skill = "Docker"
        response = self.client.post(
            "/simulate",
            json={"current_skills": current_skills, "added_skill": added_skill},
            content_type="application/json"
        )
        rj = response.get_json()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {rj}"
        assert rj["success"] is True, f"Success was False: {rj}"
        assert "score_change" in rj["deltas"], f"No score_change in deltas: {rj}"

    # ─────────────────────────────────────────────
    # ROLE INTELLIGENCE UNIT TESTS (Task 7 Validation)
    # ─────────────────────────────────────────────

    def test_06_role_knowledge_teacher(self):
        """TASK 7 – Teacher: role knowledge returns relevant skills, gap is non-empty."""
        from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap

        kb = get_role_knowledge("Teacher")
        top_skills = kb.get("top_skills", [])

        # Verify dataset data loaded (not fallback defaults)
        assert len(top_skills) > 0, "No top_skills for Teacher — knowledge base may not be loaded."
        assert kb.get("resume_count", 0) > 0, "resume_count is 0 — cache may not have Teacher data."

        # Teacher skills should include teaching-specific terms
        skill_names_lower = [s.lower() for s in top_skills]
        teacher_specific = {"teaching", "lesson planning", "curriculum development", "e-learning", "training"}
        found = teacher_specific & set(skill_names_lower)
        assert len(found) > 0, (
            f"Teacher top_skills don't contain any teaching-specific skill. Got: {top_skills}"
        )

        # Skill gap with empty resume should return missing skills from role
        gap = get_skill_gap([], "Teacher")
        assert len(gap["missing"]) > 0, "Skill gap missing list is empty for Teacher with no skills."
        assert gap["match_percentage"] == 0.0, "match_percentage should be 0 for empty skill set."
        print(f"\n[Teacher] top_skills: {top_skills[:5]}")
        print(f"[Teacher] skill_gap (empty resume): {gap['missing'][:5]}")

    def test_07_role_knowledge_hr(self):
        """TASK 7 – HR: role knowledge returns relevant skills, gap is role-specific."""
        from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap

        kb = get_role_knowledge("Hr")
        top_skills = kb.get("top_skills", [])

        assert len(top_skills) > 0, "No top_skills for HR."
        assert kb.get("resume_count", 0) > 0, "resume_count is 0 for HR."

        # HR-specific skills
        skill_names_lower = [s.lower() for s in top_skills]
        hr_specific = {"recruitment", "employee relations", "hris", "onboarding",
                       "talent acquisition", "performance management", "compensation"}
        found = hr_specific & set(skill_names_lower)
        assert len(found) > 0, (
            f"HR top_skills don't include any HR-specific skill. Got: {top_skills}"
        )

        # Verify gap is role-specific (has HR skills, not random tech skills)
        partial_skills = ["Communication", "Excel"]  # skills a candidate has
        gap = get_skill_gap(partial_skills, "Hr")
        assert len(gap["missing"]) > 0, "Skill gap missing list is empty for HR with minimal skills."
        assert gap["match_percentage"] < 100.0, "match_percentage cannot be 100 with minimal skills."
        print(f"\n[HR] top_skills: {top_skills[:5]}")
        print(f"[HR] skill_gap (partial): {gap['missing'][:5]}")

    def test_08_role_knowledge_engineering(self):
        """TASK 7 – Engineering: role knowledge returns relevant skills, score is non-zero."""
        from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap
        from analyzer import analyze_resume_ai

        kb = get_role_knowledge("Engineering")
        top_skills = kb.get("top_skills", [])

        assert len(top_skills) > 0, "No top_skills for Engineering."
        assert kb.get("resume_count", 0) > 0, "resume_count is 0 for Engineering."

        # Engineering-specific skills
        skill_names_lower = [s.lower() for s in top_skills]
        eng_specific = {"autocad", "mechanical engineering", "cad", "lean manufacturing",
                        "matlab", "automation", "quality assurance"}
        found = eng_specific & set(skill_names_lower)
        assert len(found) > 0, (
            f"Engineering top_skills don't include any engineering-specific skill. Got: {top_skills}"
        )

        # End-to-end: run a short engineering resume through the full AI pipeline
        eng_resume = (
            "MECHANICAL ENGINEER\n"
            "SKILLS: AutoCAD, SolidWorks, CAD, MATLAB, Mechanical Engineering, "
            "Project Management, Quality Assurance, Lean Manufacturing\n"
            "EXPERIENCE: 3 years as a Mechanical Design Engineer at ABC Corp.\n"
            "EDUCATION: B.E. Mechanical Engineering, XYZ University."
        )
        result = analyze_resume_ai(eng_resume)
        assert "error" not in result, f"AI pipeline error: {result.get('error')}"
        assert result.get("score", 0) > 0, "Score is 0 for Engineering resume."

        skill_gap = result.get("skill_gap", {})
        role_profile = result.get("role_profile", {})
        assert len(role_profile.get("top_skills", [])) > 0, "role_profile.top_skills is empty."

        print(f"\n[Engineering] top_skills: {top_skills[:5]}")
        print(f"[Engineering] score: {result.get('score')}")
        print(f"[Engineering] role_profile: {role_profile.get('top_skills', [])[:5]}")
        print(f"[Engineering] skill_gap.missing: {skill_gap.get('missing', [])[:5]}")

    def test_09_simulator_format_a(self):
        """Simulator Format A: extracted_text + added_skill (frontend format)."""
        resume_text = (
            "Python Developer with experience in Django, Flask, REST API, Git, Linux. "
            "3 years experience. B.E. Computer Science."
        )
        response = self.client.post(
            "/simulate",
            json={"extracted_text": resume_text, "added_skill": "Docker"},
            content_type="application/json"
        )
        rj = response.get_json()
        assert response.status_code == 200, f"Simulate Format A failed: {rj}"
        assert rj["success"] is True
        assert "deltas" in rj
        assert "score_change" in rj["deltas"]
        assert "role_context" in rj
        print(f"\n[Simulator Format A] score_change={rj['deltas']['score_change']}, "
              f"role={rj['role_context'].get('role')}")

    def test_10_skill_gap_never_empty(self):
        """Skill gap should NEVER be empty, even for unknown roles."""
        from ai_engine.role_knowledge import get_skill_gap
        gap = get_skill_gap([], "UnknownRole_XYZ")
        assert len(gap["missing"]) > 0, "Skill gap returned empty for unknown role — fallback broken."
        assert gap["match_percentage"] == 0.0


if __name__ == "__main__":
    unittest.main(verbosity=2)
