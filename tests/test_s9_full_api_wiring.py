import unittest
import sys
import os

# Ensure the root of the project is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class TestS9ApiWiring(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_routes_exist(self):
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        expected_routes = [
            "/api/health",
            "/api/usage",
            "/api/jobs",
            "/api/opportunities",
            "/api/history",
            "/api/research",
            "/api/providers",
            "/api/industries",
            "/api/applications",
            "/api/ingest",
            "/api/why-three"
        ]
        
        for r in expected_routes:
            self.assertIn(r, routes, f"Route {r} is missing from app.url_map")

    def test_route_methods(self):
        # We test HTTP methods
        # Most are GET except /api/ingest is POST
        
        get_routes = [
            "/api/health", "/api/usage", "/api/jobs", 
            "/api/opportunities", "/api/history", "/api/research",
            "/api/providers", "/api/industries", "/api/applications",
            "/api/why-three"
        ]
        
        for route in get_routes:
            resp = self.client.get(route)
            self.assertIn(resp.status_code, [200, 201], f"GET {route} failed with {resp.status_code}")
            
        resp = self.client.post("/api/ingest")
        self.assertIn(resp.status_code, [200, 201], f"POST /api/ingest failed with {resp.status_code}")

if __name__ == '__main__':
    unittest.main()
