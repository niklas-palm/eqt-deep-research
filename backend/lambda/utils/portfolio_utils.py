"""Utility functions for portfolio company data"""

import json
import os
from typing import List
from .types import PortfolioCompany
from . import logger


def fetch_portfolio_companies() -> List[PortfolioCompany]:
    """
    Load portfolio companies from the local portfolio JSON file.

    Returns:
        List[PortfolioCompany]: A list of portfolio company models
    """
    try:
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the JSON file in the assets directory
        json_file_path = os.path.join(current_dir, "assets", "eqt_portfolio.json")
        logger.info(f"Loading portfolio data from {json_file_path}")

        # Open and read the JSON file
        with open(json_file_path, "r") as file:
            portfolio_data = json.load(file)

        # Transform to Pydantic models
        transformed_data = []
        for company in portfolio_data:
            company_model = PortfolioCompany(
                name=company.get("Company", ""),
                sector=company.get("Sector", ""),
                fund=company.get("Fund", ""),
                country=company.get("Market", ""),
                entry_year=company.get("Entry", ""),
                link=company.get("Link", ""),
                website=company.get("company_website", "")
            )
            transformed_data.append(company_model)

        logger.info(f"Loaded {len(transformed_data)} portfolio companies")
        return transformed_data
    except Exception as e:
        logger.error(f"Error fetching portfolio companies: {str(e)}")
        return []
