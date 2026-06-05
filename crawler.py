"""
Crawler Worker Module for the Custom Distributed Web Crawler.

Role in Master-Worker Architecture:
This module represents the Worker Process execution layer. It contains:
1. `crawl_url(url: str) -> dict`: Crawls a single URL, scrapes HTML, extracts metadata,
   and handles any network/parsing exceptions safely.
2. `crawl_chunk(chunk: list[str]) -> list[dict]`: Sequentially crawls a chunk of URLs,
   returning a consolidated list of crawler results.

Both are defined as top-level functions (not enclosed inside any classes) to ensure
they are fully picklable by the multiprocessing pool across all supported platforms
(especially Windows which uses the 'spawn' start method).
"""

import time
from urllib.parse import urlparse
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup


def crawl_url(url: str) -> Dict[str, Any]:
    """
    Crawls a single URL.
    Fetches the URL, parses HTML, extracts relevant statistics,
    and handles specific requests exceptions gracefully.
    
    Ensures response_time is always calculated and returned even on failure.
    """
    start_time = time.perf_counter()
    domain = ""
    try:
        parsed_uri = urlparse(url)
        domain = parsed_uri.netloc or parsed_uri.hostname or ""
    except Exception:
        pass

    # Initialize standard result dictionary template
    result = {
        "url": url,
        "domain": domain,
        "status": "error",
        "status_code": None,
        "title": None,
        "links_count": 0,
        "size_bytes": 0,
        "response_time": 0.0,
        "error_msg": None
    }

    # Desktop Chrome User-Agent header to avoid basic crawler blocks (403 Forbidden)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    try:
        # Fetch target URL with 5 seconds connection timeout and 10 seconds read timeout
        response = requests.get(url, headers=headers, timeout=(5, 10))
        
        # Calculate response time immediately after the response completes
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status_code"] = response.status_code
        
        # Triggers HTTPError if the response code is 4xx or 5xx
        response.raise_for_status()
        
        # Parse document metadata
        content = response.content
        result["size_bytes"] = len(content)
        
        # Parse elements
        soup = BeautifulSoup(content, "html.parser")
        
        # Extract title tag (limit to 50 characters max)
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()
            result["title"] = title_text[:50]
        else:
            result["title"] = None
            
        # Count all <a href> link tags
        links = soup.find_all("a", href=True)
        result["links_count"] = len(links)
        
        result["status"] = "success"

    except requests.exceptions.InvalidURL as e:
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "error"
        result["error_msg"] = "InvalidURL"
        
    except requests.exceptions.SSLError as e:
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "error"
        result["error_msg"] = "SSLError"
        
    except requests.exceptions.ConnectionError as e:
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "error"
        result["error_msg"] = "ConnectionError"
        
    except requests.exceptions.TooManyRedirects as e:
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "error"
        result["error_msg"] = "TooManyRedirects"
        
    except requests.exceptions.Timeout as e:
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "error"
        result["error_msg"] = "ReadTimeout"
        
    except requests.exceptions.HTTPError as e:
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "failed"
        result["error_msg"] = "HTTPError"
        
    except Exception as e:
        # Fallback catch-all error handler to avoid crashing pool workers
        elapsed = time.perf_counter() - start_time
        result["response_time"] = round(elapsed, 4)
        result["status"] = "error"
        result["error_msg"] = type(e).__name__

    return result


def crawl_chunk(chunk: List[str]) -> List[Dict[str, Any]]:
    """
    Crawls a partitioned list of URLs sequentially.
    Called inside a worker process mapping slice.
    """
    chunk_results = []
    for url in chunk:
        chunk_results.append(crawl_url(url))
    return chunk_results
