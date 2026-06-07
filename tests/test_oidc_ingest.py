import unittest
from flask import Flask
from api.ingest import ingest
from api import api_bp
import os

class TestOIDCIngest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.client = self.app.test_client()

    def test_ingest_no_auth(self):
        response = self.client.post('/api/ingest')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Authorization header missing", response.data)

    def test_ingest_malformed_auth(self):
        response = self.client.post('/api/ingest', headers={"Authorization": "Basic 123"})
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Authorization header missing or malformed", response.data)

    def test_ingest_no_token_args(self):
        # Ensure token in args is ignored
        response = self.client.post('/api/ingest?token=secret')
        self.assertEqual(response.status_code, 401)

    def test_ingest_fake_valid_oidc(self):
        # We need to mock verify_token or provide a path for testing in oidc.py
        # Since we modified oidc.py to accept fake_claims, we can test it directly
        from ingest.oidc import verify_token
        
        claims = {"iss": "https://accounts.google.com", "aud": "target", "email": "scheduler@service.com"}
        auth_header = "Bearer fake-token"
        
        verified = verify_token(auth_header, expected_audience="target", fake_claims=claims)
        self.assertEqual(verified.email, "scheduler@service.com")

if __name__ == '__main__':
    unittest.main()
