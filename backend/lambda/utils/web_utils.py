"""Web utilities for scraping and processing website content"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Optional

from . import logger

def scrape_website(url: str, max_depth: int = 2) -> str:
    """
    Scrape a website and its relative links up to a specified depth.
    
    Args:
        url: The starting URL to scrape
        max_depth: Maximum depth of links to follow (default: 2)
        
    Returns:
        A string containing all the extracted text content
    """
    visited_urls: Set[str] = set()
    all_text: List[str] = []
    
    def extract_text_and_links(url: str, depth: int) -> List[str]:
        """
        Recursively extract text and follow links up to specified depth.
        
        Args:
            url: Current URL to scrape
            depth: Current depth level
            
        Returns:
            List of relative URLs found on the page
        """
        if depth > max_depth or url in visited_urls:
            return []
        
        visited_urls.add(url)
        relative_links = []
        
        try:
            logger.info(f"Scraping URL: {url} (depth: {depth})")
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract and add text content
            text_content = soup.get_text(separator=' ', strip=True)
            all_text.append(text_content)
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Skip fragment links, javascript, mailto, etc.
                if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                    continue
                
                # Handle relative URLs
                full_url = urljoin(url, href)
                parsed_url = urlparse(full_url)
                
                # Only follow links to the same site (relative links)
                if parsed_url.netloc == urlparse(url).netloc and full_url not in visited_urls:
                    relative_links.append(full_url)
            
            return relative_links
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error processing {url}: {str(e)}")
            return []
    
    # Start the recursive scraping process
    links_to_visit = [url]
    current_depth = 1
    
    # Add URL validation check
    if not url or not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL: {url}")
        return ""
    
    logger.info(f"Starting to scrape {url} with max depth {max_depth}")
    
    while current_depth <= max_depth and links_to_visit:
        new_links = []
        
        for link in links_to_visit:
            found_links = extract_text_and_links(link, current_depth)
            new_links.extend(found_links)
        
        links_to_visit = new_links
        current_depth += 1
    
    result = "\n\n".join(all_text)
    logger.info(f"Scraped {len(visited_urls)} pages, extracted {len(result)} characters")
    
    return result