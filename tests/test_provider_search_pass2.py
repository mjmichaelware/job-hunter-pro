import unittest
from unittest.mock import patch, MagicMock
from providers.search.adzuna import adzuna_provider
from providers.search.usajobs import usajobs_provider
from providers.search.jooble import jooble_provider
from providers.search.careerjet import careerjet_provider
from models import SearchResult

class TestProviderSearchPass2(unittest.TestCase):
    
    @patch('core.http_session.get')
    def test_adzuna_search_success(self, mock_get):
        with patch('core.Config.ADZUNA_APP_ID', 'fake_id'), patch('core.Config.ADZUNA_APP_KEY', 'fake_key'):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Adzuna Job",
                        "description": "Description here",
                        "redirect_url": "https://adzuna.com/job/1",
                        "company": {"display_name": "Adzuna Corp"},
                        "created": "2026-06-07T00:00:00Z"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            results = adzuna_provider.search("Adzuna")
            self.assertEqual(len(results), 1)
            self.assertIsInstance(results[0], SearchResult)
            self.assertEqual(results[0].provider, "adzuna")
            self.assertEqual(results[0].url, "https://adzuna.com/job/1")

    @patch('core.http_session.get')
    def test_usajobs_search_success(self, mock_get):
        with patch('core.Config.USAJOBS_API_KEY', 'fake_key'), patch('core.Config.USAJOBS_EMAIL', 'test@example.com'):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "SearchResult": {
                    "SearchResultItems": [
                        {
                            "MatchedObjectDescriptor": {
                                "PositionTitle": "Federal Job",
                                "PositionURI": "https://usajobs.gov/job/1",
                                "QualificationSummary": "Qualification",
                                "OrganizationName": "US Gov",
                                "PublicationStartdate": "2026-06-07"
                            }
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            results = usajobs_provider.search("Federal")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, "usajobs")
            self.assertEqual(results[0].url, "https://usajobs.gov/job/1")

    @patch('core.http_session.post')
    def test_jooble_search_success(self, mock_post):
        with patch('core.Config.JOOBLE_API_KEY', 'fake_key'):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jobs": [
                    {
                        "title": "Jooble Job",
                        "link": "https://jooble.org/job/1",
                        "snippet": "Snippet",
                        "company": "Jooble Corp",
                        "updated": "2026-06-07"
                    }
                ]
            }
            mock_post.return_value = mock_response
            
            results = jooble_provider.search("Jooble")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, "jooble")
            self.assertEqual(results[0].url, "https://jooble.org/job/1")

    @patch('core.http_session.get')
    def test_careerjet_search_success(self, mock_get):
        with patch('core.Config.CAREERJET_AFFID', 'fake_id'):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jobs": [
                    {
                        "title": "Careerjet Job",
                        "url": "https://careerjet.com/job/1",
                        "description": "Description",
                        "company": "Careerjet Corp",
                        "date": "2026-06-07"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            results = careerjet_provider.search("Careerjet")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, "careerjet")
            self.assertEqual(results[0].url, "https://careerjet.com/job/1")

    def test_missing_keys_return_empty(self):
        with patch('core.Config.ADZUNA_APP_ID', ''), patch('core.Config.ADZUNA_APP_KEY', ''):
            self.assertEqual(adzuna_provider.search("q"), [])
        with patch('core.Config.USAJOBS_API_KEY', ''):
            self.assertEqual(usajobs_provider.search("q"), [])
        with patch('core.Config.JOOBLE_API_KEY', ''):
            self.assertEqual(jooble_provider.search("q"), [])
        with patch('core.Config.CAREERJET_AFFID', ''):
            self.assertEqual(careerjet_provider.search("q"), [])

    @patch('core.http_session.get')
    def test_error_handling_returns_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response
        
        with patch('core.Config.ADZUNA_APP_ID', 'id'), patch('core.Config.ADZUNA_APP_KEY', 'key'):
            self.assertEqual(adzuna_provider.search("q"), [])

if __name__ == "__main__":
    unittest.main()
