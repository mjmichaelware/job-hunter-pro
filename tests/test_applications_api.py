import unittest
import json
from app import create_app
from api.applications import repo

class TestApplicationsAPI(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Reset the repository for each test
        repo._local_storage = {}

    def test_crud_flow(self):
        # 1. Get all (empty)
        response = self.client.get('/api/applications')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data["applications"]), 0)

        # 2. Create one
        payload = {"job_id": "job_123", "notes": "Applied today", "status": "APPLIED"}
        response = self.client.post('/api/applications', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # 3. Get single
        response = self.client.get('/api/applications/job_123')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "APPLIED")

        # 4. Update
        update_payload = {"status": "INTERVIEWING", "notes": "Got a call!"}
        response = self.client.patch('/api/applications/job_123',
                                      data=json.dumps(update_payload),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "INTERVIEWING")
        self.assertEqual(data["notes"], "Got a call!")

    def test_create_duplicate_fails(self):
        payload = {"job_id": "job_dup"}
        self.client.post('/api/applications', data=json.dumps(payload), content_type='application/json')
        response = self.client.post('/api/applications', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 409)

if __name__ == "__main__":
    unittest.main()
