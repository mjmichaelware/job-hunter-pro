import unittest
from providers.reasoning.openai import openai_provider
from providers.reasoning.gemini import gemini_provider
from providers.reasoning.claude import claude_provider
from providers.reasoning.groq import groq_provider
from providers.reasoning.xai import xai_provider
from core import Config

class TestReasoningProviders(unittest.TestCase):
    def setUp(self):
        # Ensure they look available for the test
        Config.OPENAI_API_KEY = "fake"
        Config.GEMINI_API_KEY = "fake"
        Config.ANTHROPIC_API_KEY = "fake"
        Config.GROQ_API_KEY = "fake"
        Config.XAI_API_KEY = "fake"

    def test_providers_structure(self):
        providers = [openai_provider, gemini_provider, claude_provider, groq_provider, xai_provider]
        for p in providers:
            with self.subTest(provider=p.metadata.key):
                res = p.classify("test text", ["cat1", "cat2"])
                self.assertEqual(res["provider"], p.metadata.key)
                self.assertEqual(res["mode"], "classify")
                self.assertIn("confidence", res)
                self.assertTrue(res["evidence_required"])
                self.assertIn("category", res)
                self.assertIn("source_text_hash", res)
                self.assertEqual(res["input_length"], len("test text"))
                self.assertNotIn("provider_stub", res)

                enrich_res = p.enrich("test text")
                self.assertEqual(enrich_res["mode"], "enrich")
                self.assertIn("enrichment", enrich_res)
                self.assertNotIn("provider_stub", enrich_res)

if __name__ == '__main__':
    unittest.main()
