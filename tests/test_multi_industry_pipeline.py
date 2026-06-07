import unittest
from pipeline.run import run_pipeline
from models import SearchResult

class TestMultiIndustryPipeline(unittest.TestCase):
    
    def test_full_pipeline_multi_industry(self):
        # Create fake results for different industries
        raw_results = [
            # Food Service
            SearchResult(provider="p1", query="q", title="Line Cook", url="u1", snippet="Good restaurant", raw_json={}),
            # Hospitality
            SearchResult(provider="p1", query="q", title="Hotel Front Desk", url="u2", snippet="Grand America", raw_json={}),
            # Care & Social
            SearchResult(provider="p1", query="q", title="Peer Support", url="u3", snippet="Recovery center", raw_json={}),
            # Sales
            SearchResult(provider="p1", query="q", title="Sales Representative", url="u4", snippet="Commission", raw_json={}),
            # Customer Service
            SearchResult(provider="p1", query="q", title="Call Center Agent", url="u5", snippet="Support", raw_json={}),
            # Retail
            SearchResult(provider="p1", query="q", title="Retail Cashier", url="u6", snippet="Stocking", raw_json={}),
            # Unknown / Rejected
            SearchResult(provider="p1", query="q", title="Software Engineer", url="u7", snippet="Python", raw_json={}),
        ]
        
        output = run_pipeline(raw_results)
        
        accepted = output["accepted"]
        rejected = output["rejected"]
        counts = output["counts"]
        
        # 6 should be accepted (one for each supported industry)
        # 1 should be rejected (software engineer is not mapped in our core industries)
        self.assertEqual(len(accepted), 6)
        self.assertEqual(len(rejected), 1)
        
        industries = [j["industry"] for j in accepted]
        self.assertIn("food_service", industries)
        self.assertIn("hospitality", industries)
        self.assertIn("care_social", industries)
        self.assertIn("sales", industries)
        self.assertIn("customer_service", industries)
        self.assertIn("retail_ops", industries)
        
        # Check rejection reason
        self.assertEqual(rejected[0]["rejection"]["reason"], "not_mapped_to_industry")

    def test_pipeline_dedupe(self):
        raw_results = [
            SearchResult(provider="p1", query="q", title="Cook", url="dup", raw_json={}),
            SearchResult(provider="p2", query="q", title="Cook", url="dup", raw_json={}),
        ]
        output = run_pipeline(raw_results)
        self.assertEqual(len(output["accepted"]), 1)
        self.assertEqual(output["counts"]["raw"], 2)

if __name__ == "__main__":
    unittest.main()
