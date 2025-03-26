"""
Simple tests for AI utility functions.
"""

import sys
import os
import unittest

# Add the lambda directory to the Python path for imports to work correctly
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../lambda"))
)

# Import functions to test
from utils.ai_utils import Prompts, get_prompt, extract_structured_data


class TestAiUtils(unittest.TestCase):
    """
    Test AI utilities for prompt generation and response processing.
    """

    def test_get_prompt(self):
        """Test that prompts are successfully created with proper variables"""
        # Create a simple query
        query = "What is the business model of TechCompany?"

        # Create a sample company list
        companies = [
            {
                "Company": "Campus",
                "Sector": "Real Estate",
                "Fund": "EQT IX",
                "Market": "Spain",
                "Entry": "2021",
                "Link": "https://eqtgroup.com/about/current-portfolio/campus",
                "company_website": "https://nodis.es/en/home-nodis-student-residences/",
            },
            {
                "Company": "Candela",
                "Sector": "Sustainability",
                "Fund": "EQT Ventures III",
                "Market": "Sweden",
                "Entry": "2021",
                "Link": "https://eqtgroup.com/about/current-portfolio/candela",
                "company_website": "https://candela.com/",
            },
        ]

        # Create the prompt with above variables
        identify_company_prompt = get_prompt(
            Prompts.IDENTIFY_COMPANY,
            query=query,
            companies_list=companies,
        )

        # Verify variables successfully injected
        self.assertIsNotNone(identify_company_prompt, "Failed to generate prompt")
        self.assertTrue(len(identify_company_prompt) > 0, "Empty prompt generated")
        self.assertTrue(
            query in identify_company_prompt, "User query not found in generated prompt"
        )
        self.assertTrue(
            "Campus" in identify_company_prompt
            and "Candela" in identify_company_prompt,
            "Company data not found in generated prompt",
        )

        # Test query reformulation prompt
        reformulation_prompt = get_prompt(
            Prompts.QUERY_REFORMULATION,
            query=query,
        )

        # Verify the reformulation prompt
        self.assertIsNotNone(
            reformulation_prompt, "Failed to generate reformulation prompt"
        )
        self.assertTrue(
            len(reformulation_prompt) > 0, "Empty reformulation prompt generated"
        )
        self.assertTrue(
            query in reformulation_prompt,
            "User query not found in reformulation prompt",
        )
        self.assertTrue(
            "reformulated_queries" in reformulation_prompt,
            "Expected output format not found in reformulation prompt",
        )

    def test_extract_structured_data(self):
        """Test extracting JSON data from AI responses"""
        # Sample JSON response with code block markers
        json_response = """
        Here's the information you requested:
        
        ```json
        {
          "name": "TestCompany",
          "sector": "Technology"
        }
        ```
        """

        # Extract the data
        extracted = extract_structured_data(json_response)

        # Verify extraction
        self.assertIsNotNone(extracted, "Failed to extract JSON data")
        self.assertEqual(
            extracted.get("name"), "TestCompany", "Wrong company name extracted"
        )
        self.assertEqual(
            extracted.get("sector"), "Technology", "Wrong sector extracted"
        )

    def test_extract_reformulated_queries(self):
        """Test extracting reformulated queries from JSON response"""
        # Sample query reformulation response
        reformulation_response = """
        ```json
        {
          "reformulated_queries": [
            "TechCompany revenue business model",
            "TechCompany monetization strategy analysis"
          ]
        }
        ```
        """

        # Extract the data
        extracted = extract_structured_data(
            reformulation_response, expected_format="query reformulation"
        )

        # Verify extraction
        self.assertIsNotNone(extracted, "Failed to extract reformulated queries")
        self.assertTrue(
            "reformulated_queries" in extracted, "Missing reformulated_queries key"
        )
        self.assertEqual(
            len(extracted["reformulated_queries"]), 2, "Should have two queries"
        )
        self.assertEqual(
            extracted["reformulated_queries"][0],
            "TechCompany revenue business model",
            "First reformulated query incorrect",
        )
        self.assertEqual(
            extracted["reformulated_queries"][1],
            "TechCompany monetization strategy analysis",
            "Second reformulated query incorrect",
        )


if __name__ == "__main__":
    unittest.main()
