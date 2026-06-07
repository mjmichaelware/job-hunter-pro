import unittest
from flask import Flask
from api import api_bp
import json

class TestAPIFrontendContract(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.client = self.app.test_client()

    def test_providers_endpoint(self):
        response = self.client.get('/api/providers')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("providers", data)
        self.assertTrue(len(data["providers"]) > 0)
        self.assertIn("key", data["providers"][0])
        self.assertIn("is_available", data["providers"][0])

    def test_industries_endpoint(self):
        response = self.client.get('/api/industries')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("industries", data)
        self.assertTrue(len(data["industries"]) > 0)
        self.assertIn("key", data["industries"][0])

    def test_usage_endpoint(self):
        response = self.client.get('/api/usage')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("monthly_usage", data)
        self.assertIn("status", data)

    def test_history_endpoint(self):
        response = self.client.get('/api/history')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("batches", data)

    def test_jobs_dry_run(self):
        response = self.client.get('/api/jobs?dry_run=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["mode"], "dry_run")
        self.assertIn("jobs", data)

    def test_why_three_endpoint(self):
        response = self.client.get('/api/why-three')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("top3", data)

if __name__ == '__main__':
    unittest.main()
