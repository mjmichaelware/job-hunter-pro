import unittest
from unittest.mock import patch, MagicMock
from search.federated import FederatedSearch
from models import SearchResult

class TestFederatedSearch(unittest.TestCase):
    
    def setUp(self):
        self.mock_budget = MagicMock()
        self.mock_cache = MagicMock()
        self.fed_search = FederatedSearch(self.mock_budget, self.mock_cache)
        self.mock_cache.generate_key.return_value = "test_key"
        self.mock_cache.get_cached_results.return_value = None

    def test_plan_queries_all_industries(self):
        # Should generate plan for all industries and available providers
        plan = self.fed_search.plan_queries()
        self.assertTrue(len(plan) > 0)
        # Check for free provider The Muse (always available in our setup)
        has_themuse = any(item["provider"] == "themuse" for item in plan)
        self.assertTrue(has_themuse)

    @patch('search.federated.get_providers_by_type')
    def test_execute_plan_merges_and_dedupes(self, mock_get_providers):
        # Setup mock providers
        mock_p1 = MagicMock()
        mock_p1.metadata.key = "p1"
        mock_p1.search.return_value = [
            SearchResult(provider="p1", query="q", title="Job 1", url="http://job1", raw_json={})
        ]
        
        mock_p2 = MagicMock()
        mock_p2.metadata.key = "p2"
        mock_p2.search.return_value = [
            SearchResult(provider="p2", query="q", title="Job 1", url="http://job1", raw_json={}), # Duplicate URL
            SearchResult(provider="p2", query="q", title="Job 2", url="http://job2", raw_json={})
        ]
        
        mock_get_providers.return_value = [mock_p1, mock_p2]
        self.mock_budget.can_afford.return_value = True
        
        plan = [
            {"provider": "p1", "industry": "food", "query": "q"},
            {"provider": "p2", "industry": "food", "query": "q"}
        ]
        
        results = self.fed_search.execute_plan(plan)
        
        # Should have 2 unique jobs
        self.assertEqual(len(results), 2)
        urls = [r.url for r in results]
        self.assertIn("http://job1", urls)
        self.assertIn("http://job2", urls)

    def test_budget_blocking(self):
        # Setup mock providers
        with patch('providers.get_providers_by_type') as mock_get:
            mock_p = MagicMock()
            mock_p.metadata.key = "serpapi_jobs"
            mock_get.return_value = [mock_p]
            
            # Budget blocked
            self.mock_budget.can_afford.return_value = False
            
            plan = [{"provider": "serpapi_jobs", "industry": "food", "query": "q"}]
            results = self.fed_search.execute_plan(plan)
            
            self.assertEqual(len(results), 0)
            mock_p.search.assert_not_called()

if __name__ == "__main__":
    unittest.main()
