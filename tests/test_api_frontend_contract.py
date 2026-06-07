import unittest
import json
from app import app

class TestAPIFrontendContract(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_surface_endpoint(self):
        response = self.client.get('/api/_surface')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["api_index_proxy_routes"], "enabled")
        self.assertFalse(data["placeholder_blueprint_registered"])

    def test_health_endpoint_rich(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("maps_enabled", data)
        self.assertIn("serpapi_enabled", data)
        self.assertIn("batch_bucket", data)

    def test_usage_endpoint_rich(self):
        response = self.client.get('/api/usage')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("serpapi", data)
        self.assertIn("storage", data)
        self.assertIn("batch_bucket", data["storage"])

    def test_providers_endpoint_modular(self):
        response = self.client.get('/api/providers')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("providers", data)
        # Should have both search and reasoning providers
        keys = [p["key"] for p in data["providers"]]
        self.assertIn("openai", keys)
        self.assertIn("adzuna", keys)

    def test_industries_endpoint_modular(self):
        response = self.client.get('/api/industries')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("industries", data)
        self.assertEqual(len(data["industries"]), 6)

    def test_applications_endpoint_modular(self):
        # Even if empty, it should return the structure
        response = self.client.get('/api/applications')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("applications", data)
        self.assertIsInstance(data["applications"], list)

    def test_history_endpoint_rich(self):
        response = self.client.get('/api/history')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("batch_count", data)
        self.assertIn("data", data)

    def test_jobs_dry_run_rich(self):
        response = self.client.get('/api/jobs?dry_run=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["dry_run"])

    def test_why_three_endpoint_rich(self):
        response = self.client.get('/api/why-three')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "explained")
        self.assertIn("main_reason", data)

if __name__ == '__main__':
    unittest.main()
