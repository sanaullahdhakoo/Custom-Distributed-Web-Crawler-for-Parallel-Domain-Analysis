"""
URL Loader Module for the Custom Distributed Web Crawler.

Role in Master-Worker Architecture:
This module is executed exclusively by the Master Process. It is responsible for:
1. Loading the target domain URLs from the filesystem (urls.txt).
2. Applying validation constraints to filter out malformed URLs before crawling.
3. Supplying fallback safe URLs if the source file is missing or empty.
4. Partitioning the validated URLs into equal, balanced chunks based on CPU count
   to be distributed among worker processes, minimizing load imbalance.
"""

import os
import sys
from typing import List

# 10 safe public URLs to fall back on if urls.txt is missing or empty
FALLBACK_URLS = [
    "https://www.python.org",
    "https://httpbin.org/html",
    "http://example.com",
    "https://www.w3.org",
    "https://www.sqlite.org",
    "https://www.debian.org",
    "https://www.php.net",
    "https://www.rust-lang.org",
    "https://go.dev",
    "https://www.gnu.org"
]


def load_urls(file_path: str) -> List[str]:
    """
    Loads URLs from the specified text file. If the file is missing,
    unreadable, or empty, falls back to the hardcoded list of 10 safe URLs.
    """
    if not os.path.exists(file_path):
        print(f"[WARNING] URL source file '{file_path}' not found. Falling back to default list.")
        return FALLBACK_URLS

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            print(f"[WARNING] URL source file '{file_path}' is empty. Falling back to default list.")
            return FALLBACK_URLS
        
        return urls
    except Exception as e:
        print(f"[WARNING] Error reading '{file_path}': {e}. Falling back to default list.")
        return FALLBACK_URLS


def validate_urls(urls: List[str]) -> List[str]:
    """
    Validates each URL. Each URL must start with 'http://' or 'https://'.
    Skipped URLs print a warning message.
    """
    valid_urls = []
    for url in urls:
        if url.startswith("http://") or url.startswith("https://"):
            valid_urls.append(url)
        else:
            print(f"[WARNING] Skipping invalid URL (must start with http:// or https://): '{url}'", file=sys.stderr)
    return valid_urls


def partition_urls(urls: List[str], num_chunks: int) -> List[List[str]]:
    """
    Partitions a list of URLs into equal chunks based on the number of workers.
    Ensures that workloads are distributed as evenly as possible.
    """
    if not urls:
        return []
    
    # If the partition request exceeds the number of URLs, limit chunks to len(urls)
    num_chunks = max(1, min(num_chunks, len(urls)))
    
    chunks: List[List[str]] = [[] for _ in range(num_chunks)]
    for idx, url in enumerate(urls):
        chunks[idx % num_chunks].append(url)
        
    return [c for c in chunks if c]
