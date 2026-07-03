import unittest
import urllib.request
import json

class TestBackendAPI(unittest.TestCase):
    BASE_URL = "http://127.0.0.1:8000"

    def test_health_endpoint(self):
        """
        Verify that GET /health returns {'status': 'running'}.
        """
        try:
            response = urllib.request.urlopen(f"{self.BASE_URL}/health")
            self.assertEqual(response.status, 200)
            
            data = json.loads(response.read().decode())
            self.assertEqual(data.get("status"), "running")
        except Exception as e:
            self.fail(f"Health check endpoint request failed: {e}")

if __name__ == "__main__":
    unittest.main()
