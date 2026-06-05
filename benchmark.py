"""
Benchmark Module for the Custom Distributed Web Crawler.

Role in Master-Worker Architecture:
This module is executed by the Master Process. It acts as the benchmarking and
performance evaluation engine. Its responsibilities are:
1. Running the sequential crawler baseline (`run_sequential_baseline`) on target URLs
   to serve as a performance comparator.
2. Calculating metrics comparing sequential time (T_seq) to parallel time (T_par).
3. Computing actual Speedup (S) and Parallel Efficiency (E).
4. Evaluating Amdahl's Law for theoretical maximum speedup given a serial fraction
   (f = 0.1) representing overhead from URL loading, chunking, and merging.
5. Evaluating average duration per URL between sequential and parallel modes.
"""

import time
import multiprocessing
from typing import List, Dict, Any, Tuple
from crawler import crawl_url


def run_sequential_baseline(urls: List[str]) -> Tuple[List[Dict[str, Any]], float]:
    """
    Executes the crawl sequentially on all URLs in a simple loop.
    Records the total elapsed baseline time.
    """
    start_time = time.perf_counter()
    results = []
    
    for url in urls:
        result = crawl_url(url)
        results.append(result)
        
    sequential_time = time.perf_counter() - start_time
    return results, round(sequential_time, 4)


def calculate_metrics(t_seq: float, t_par: float, num_cores: int, num_urls: int) -> Dict[str, Any]:
    """
    Calculates execution speedups, efficiencies, and compares against Amdahl's Law.
    
    Equations:
      - Speedup (S) = T_seq / T_par
      - Parallel Efficiency (E) = (S / N) * 100 % (where N is the core count)
      - Serial Fraction (f) = 0.1 (URL parsing, file ingestion, result merging)
      - Amdahl's Theoretical Max Speedup = 1 / (f + (1 - f) / N)
      - Average time per URL (sequential) = T_seq / num_urls
      - Average time per URL (parallel) = T_par / num_urls
    """
    # Prevent division by zero
    t_par_safe = max(t_par, 0.0001)
    num_cores_safe = max(num_cores, 1)
    num_urls_safe = max(num_urls, 1)
    
    speedup = t_seq / t_par_safe
    efficiency = (speedup / num_cores_safe) * 100.0
    
    # Amdahl's Law
    serial_fraction = 0.1
    amdahl_max = 1.0 / (serial_fraction + (1.0 - serial_fraction) / num_cores_safe)
    
    avg_time_seq = t_seq / num_urls_safe
    avg_time_par = t_par_safe / num_urls_safe
    
    return {
        "t_seq": round(t_seq, 4),
        "t_par": round(t_par, 4),
        "speedup": round(speedup, 2),
        "efficiency": round(efficiency, 2),
        "amdahl_max": round(amdahl_max, 2),
        "avg_time_seq": round(avg_time_seq, 4),
        "avg_time_par": round(avg_time_par, 4),
        "cores_used": num_cores_safe,
        "num_urls": num_urls_safe
    }
