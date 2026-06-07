import unittest
from unittest.mock import patch, MagicMock
from providers.search.themuse import themuse_provider
from providers.search.serpapi_jobs import serpapi_jobs_provider
from providers.search.serpapi_organic import serpapi_organic_provider
from models import SearchResult
from core import Config

class TestProviderSearchPass1(unittest.TestCase):
    
    @patch('core.http_session.get')
    def test_themuse_search_success(self, mock_get):
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "name": "Software Engineer",
                    "contents": "Develop great things.",
                    "refs": {"landing_page": "https://www.themuse.com/jobs/1"},
                    "company": {"name": "Tech Corp"},
                    "publication_date": "2026-06-07T00:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        results = themuse_provider.search("Software")
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results[0].provider, "themuse")
        self.assertEqual(results[0].title, "Software Engineer")
        self.assertEqual(results[0].url, "https://www.themuse.com/jobs/1")

    @patch('core.http_session.get')
    def test_themuse_search_filter(self, mock_get):
        # Mock Response with mismatch
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"name": "Baker", "contents": "Bake cakes."}]
        }
        mock_get.return_value = mock_response
        
        results = themuse_provider.search("Software")
        self.assertEqual(len(results), 0)

    @patch('core.http_session.get')
    def test_serpapi_jobs_success(self, mock_get):
        # Ensure key is present for test
        with patch('core.Config.SERPAPI_KEY', 'fake_key'):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jobs_results": [
                    {
                        "title": "Google Jobs Post",
                        "company_name": "Google",
                        "description": "Work at Google.",
                        "apply_options": [{"link": "https://google.com/apply"}]
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            results = serpapi_jobs_provider.search("Google")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, "serpapi_jobs")
            self.assertEqual(results[0].url, "https://google.com/apply")

    @patch('core.http_session.get')
    def test_serpapi_jobs_missing_key(self, mock_get):
        with patch('core.Config.SERPAPI_KEY', ''):
            results = serpapi_jobs_provider.search("Google")
            self.assertEqual(len(results), 0)
            mock_get.assert_not_called()

    @patch('core.http_session.get')
    def test_serpapi_organic_success(self, mock_get):
        with patch('core.Config.SERPAPI_KEY', 'fake_key'):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "organic_results": [
                    {
                        "title": "Organic Result",
                        "link": "https://example.com",
                        "snippet": "Snippet here",
                        "displayed_link": "example.com"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            results = serpapi_organic_provider.search("Example")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, "serpapi_organic")
            self.assertEqual(results[0].url, "https://example.com")

    @patch('core.http_session.get')
    def test_provider_error_handling(self, mock_get):
        # Test HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response
        
        results = themuse_provider.search("Any")
        self.assertEqual(results, [])
        
        with patch('core.Config.SERPAPI_KEY', 'fake_key'):
            results = serpapi_jobs_provider.search("Any")
            self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
