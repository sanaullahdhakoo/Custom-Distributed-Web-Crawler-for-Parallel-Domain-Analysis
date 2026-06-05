"""
Master Process Module for the Custom Distributed Web Crawler.

Role in Master-Worker Architecture:
This module represents the Master Process coordination layer. It contains:
1. `ParallelCrawlerManager`: A high-level orchestration class that takes a list of URLs,
   calculates process counts, partitions the URLs using `url_loader.partition_urls`,
   manages the lifecycle of a `multiprocessing.Pool`, dispatches tasks, catches pool-level
   failures, and merges the returned records.
"""

import time
import multiprocessing
from typing import List, Dict, Any, Tuple
from url_loader import partition_urls
from crawler import crawl_chunk


class ParallelCrawlerManager:
    """
    Manages process-level parallel crawling.
    Spawns workers in a Pool, distributes partitioned URL chunks,
    aggregates final responses, and measures overall parallel duration.
    """

    def __init__(self, urls: List[str], num_workers: int = None):
        """
        Initializes the manager. If num_workers is not specified, it defaults
        to the machine's active CPU core count.
        """
        self.urls = urls
        
        # Determine number of processes to allocate
        try:
            self.num_workers = num_workers or multiprocessing.cpu_count()
        except Exception:
            self.num_workers = 4  # Fallback core count if cpu_count is unsupported
            
        # Guarantee at least 1 worker process
        self.num_workers = max(1, self.num_workers)
        
        # Partition URLs into equal slices based on worker count
        self.chunks = partition_urls(self.urls, self.num_workers)
        
        # Actual chunks might be less than num_workers if we have very few URLs
        self.actual_worker_count = len(self.chunks)

    def run_parallel(self) -> Tuple[List[Dict[str, Any]], float]:
        """
        Orchestrates parallel crawling by executing worker processes via Pool.map.
        Wraps operations in exception handlers and ensures resources are closed.
        
        Returns:
            A tuple of (aggregated results list, parallel execution time in seconds)
        """
        if not self.chunks:
            return [], 0.0

        start_time = time.perf_counter()
        aggregated_results: List[Dict[str, Any]] = []
        
        # Create multiprocessing Pool
        # On Windows, using the 'spawn' context is standard for Python 3.10+
        # Passing crawl_chunk as a top-level picklable reference.
        pool = multiprocessing.Pool(processes=self.num_workers)
        
        try:
            # Dispatch partitioned URL slices to worker processes
            # We use pool.map to execute crawl_chunk on each slice in parallel
            chunk_results = pool.map(crawl_chunk, self.chunks)
            
            # Aggregate individual worker chunk outputs
            for result_list in chunk_results:
                aggregated_results.extend(result_list)
                
        except Exception as e:
            print(f"[ERROR] Multiprocessing Pool map failed: {e}")
            # Re-raise to let master or benchmark handle it or fail gracefully
            raise e
        finally:
            # Guarantee that Pool is closed and joined to prevent resource/zombie leaks
            pool.close()
            pool.join()
            
        parallel_time = time.perf_counter() - start_time
        return aggregated_results, round(parallel_time, 4)
