import unittest
from industries import (
    get_all_routes,
    get_route,
    list_industries,
    classify_text
)
from industries.base import term_present

class TestIndustriesRegistry(unittest.TestCase):
    def test_registry_count(self):
        """Registry must load exactly 6 routes."""
        routes = get_all_routes()
        self.assertEqual(len(routes), 6)
        
        keys = list_industries()
        self.assertEqual(len(keys), 6)
        self.assertIn("food_service", keys)
        self.assertIn("hospitality", keys)
        self.assertIn("care_social", keys)
        self.assertIn("sales", keys)
        self.assertIn("customer_service", keys)
        self.assertIn("retail_ops", keys)

    def test_food_service_classification(self):
        """Tests that food service titles are correctly classified."""
        self.assertEqual(classify_text("Line Cook at Urban Hill"), "food_service")
        self.assertEqual(classify_text("Server for high-end restaurant"), "food_service")
        self.assertEqual(classify_text("Dishwasher / Kitchen Utility"), "food_service")
        
    def test_rn_substring_bug(self):
        """Tests that 'rn' in normal words does not trigger rejection or misclassification."""
        # 'morning' contains 'rn' but should not be rejected by negative 'rn' if using \b
        self.assertTrue(term_present("cook", "morning cook"))
        # If 'rn' is a negative term, it shouldn't match 'morning'
        self.assertFalse(term_present("rn", "morning cook"))
        # Should classify as food_service despite 'rn' in 'morning'
        self.assertEqual(classify_text("morning cook"), "food_service")
        
    def test_registered_nurse_exclusion(self):
        """Tests that Registered Nurse does NOT become food_service."""
        # 'registered nurse' is a negative term for food_service
        self.assertNotEqual(classify_text("Registered Nurse"), "food_service")

    def test_hospitality_classification(self):
        """Tests that hospitality titles are correctly classified."""
        self.assertEqual(classify_text("Hotel Front Desk Agent"), "hospitality")
        self.assertEqual(classify_text("Banquet Server for Grand America"), "hospitality")
        
    def test_care_social_classification(self):
        """Tests that care and social service titles are correctly classified."""
        self.assertEqual(classify_text("Peer Support Specialist"), "care_social")
        self.assertEqual(classify_text("Case Aide"), "care_social")
        self.assertEqual(classify_text("Behavioral Health Technician (BHT)"), "care_social")
        
    def test_customer_service_classification(self):
        """Tests that customer service titles are correctly classified."""
        self.assertEqual(classify_text("Inbound Call Center Representative"), "customer_service")
        self.assertEqual(classify_text("Customer Support Agent"), "customer_service")
        
    def test_sales_classification(self):
        """Tests that sales titles are correctly classified."""
        self.assertEqual(classify_text("Sales Representative"), "sales")
        self.assertEqual(classify_text("Account Executive"), "sales")
        
    def test_retail_ops_classification(self):
        """Tests that retail titles are correctly classified."""
        self.assertEqual(classify_text("Retail Cashier"), "retail_ops")
        self.assertEqual(classify_text("Stocking Associate"), "retail_ops")
        self.assertEqual(classify_text("Inventory Specialist"), "retail_ops")

if __name__ == "__main__":
    unittest.main()
