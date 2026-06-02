import unittest
import os
import json
from app import app
from database import init_db, db_get_all_users, db_add_user
from resume_parser import extract_text_from_pdf
from analyzer import extract_skills, calculate_score

class CareerForgeSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        init_db()

    
    def test_01_home_page(self):
        """Verify home page loads."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CareerForge', response.data)

    
    def test_02_database_connectivity(self):
        """Verify database connection and user retrieval."""
        users = db_get_all_users()
        self.assertIsInstance(users, list)
        print(f"\n[PASS] Verified DB: Found {len(users)} users.")

    def test_03_skill_extraction_logic(self):
        """Verify skill extraction works on sample text."""
        test_text = "I am a Python developer with experience in SQL, React, and Machine Learning."
        results = extract_skills(test_text)
        self.assertIn('Python', results['skills'])
        self.assertIn('SQL', results['skills'])
        self.assertIn('React', results['skills'])
        self.assertTrue(results['total'] >= 3)
        print(f"[PASS] Verified Analyzer: Extracted {results['total']} skills.")

    def test_04_scoring_logic(self):
        """Verify score calculation is within range."""
        test_text = "Python SQL React"
        results = extract_skills(test_text)
        score_data = calculate_score(results)
        self.assertGreaterEqual(score_data['score'], 0)
        self.assertLessEqual(score_data['score'], 100)
        print(f"[PASS] Verified Scoring: Score is {score_data['score']}/100")

    def test_05_api_demo_data(self):
        """Verify demo data endpoint."""
        response = self.app.get('/api/demo-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['success']) # Corrected key
        self.assertIn('analysis_id', data)
        print("[PASS] Verified API: Demo data retrieval successful.")

    def test_06_resume_parsing(self):
        """Verify parser handles non-existent file gracefully."""
        text = extract_text_from_pdf("non_existent.pdf")
        self.assertIn("Error", text)
        print("[PASS] Verified Parser: Error handling working.")

if __name__ == '__main__':
    unittest.main()
