"""
Main Entry Module for the Custom Distributed Web Crawler.

Course: Parallel & Distributed Computing (SDC-504)
Language: Python 3.10+
Role in Master-Worker Architecture:
This is the main orchestrator (the core master execution path).
Its execution flow:
1. Clears the console screen.
2. Displays project metadata headers.
3. Loads target domains from urls.txt (or uses fallback if missing/empty).
4. Validates each URL (starts with http:// or https://), skipping invalid ones with warnings.
5. Informs the user of the initial status and core counts.
6. Conducts a sequential baseline crawl to record sequential time (T_seq).
7. Conducts a parallel distributed crawl using ParallelCrawlerManager to record parallel time (T_par).
8. Compiles benchmarks comparing speedup, efficiency, and Amdahl's Law calculations.
9. Displays the rich ANSI terminal dashboard.
10. Saves parallel crawler records into a formatted results.json.
11. Outputs a final confirmation of execution completion.

Crucial Instruction:
Includes the required `if __name__ == '__main__':` guard, which is mandatory
for the multiprocessing library to function under Windows without spawning infinite
nested subprocesses.
"""

import os
import json
import multiprocessing
from typing import List, Dict, Any

from url_loader import load_urls, validate_urls
from benchmark import run_sequential_baseline, calculate_metrics
from master import ParallelCrawlerManager
from dashboard import render_dashboard, console


def clear_screen():
    """
    Clears the terminal screen for a clean dashboard display.
    """
    os.system("cls" if os.name == "nt" else "clear")


def save_results(results: List[Dict[str, Any]], filename: str = "results.json"):
    """
    Serializes crawl results to a JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        console.print(f"[bold green][OK] Parallel results successfully saved to '{filename}'[/bold green]")
    except Exception as e:
        console.print(f"[bold red][ERROR] Failed to save results to '{filename}': {e}[/bold red]")


def main():
    # 1. Clear terminal screen
    clear_screen()

    # 2. Print project header
    console.print("=" * 70, style="bold blue")
    console.print("  CUSTOM DISTRIBUTED WEB CRAWLER FOR PARALLEL DOMAIN ANALYSIS", style="bold white")
    console.print("  COURSE: Parallel & Distributed Computing (SDC-504)", style="bold cyan")
    console.print("=" * 70, style="bold blue")
    console.print()

    # 3. Load and validate URLs
    url_file = "urls.txt"
    console.print(f"[cyan][i] Loading URLs from '{url_file}'...[/cyan]")
    raw_urls = load_urls(url_file)
    valid_urls = validate_urls(raw_urls)
    
    total_loaded = len(raw_urls)
    total_valid = len(valid_urls)
    
    # Check if we have URLs to crawl
    if not valid_urls:
        console.print("[bold red][ERROR] No valid URLs to crawl. Exiting.[/bold red]")
        return
        
    num_cores = multiprocessing.cpu_count()
    console.print(f"[green][OK] Total URLs loaded: {total_loaded}[/green]")
    console.print(f"[green][OK] Valid URLs to crawl: {total_valid}[/green]")
    console.print(f"[green][OK] Available CPU cores detected: {num_cores}[/green]")
    console.print()

    # 4. Run sequential crawl baseline
    console.print("[yellow][RUNNING] Initiating Sequential Crawl (T_seq) baseline...[/yellow]")
    seq_results, t_seq = run_sequential_baseline(valid_urls)
    console.print(f"[green][OK] Sequential baseline completed in {t_seq:.4f} seconds.[/green]")
    console.print()

    # 5. Run parallel crawl via Master Crawler Manager
    console.print("[yellow][RUNNING] Initiating Parallel Distributed Crawl (T_par) via worker pool...[/yellow]")
    try:
        manager = ParallelCrawlerManager(valid_urls)
        num_chunks = len(manager.chunks)
        par_results, t_par = manager.run_parallel()
        console.print(f"[green][OK] Parallel crawl completed in {t_par:.4f} seconds using {manager.num_workers} processes.[/green]")
        console.print()
    except Exception as e:
        console.print(f"[bold red][ERROR] Parallel crawl encountered a critical failure: {e}[/bold red]")
        return

    # 6. Calculate execution and speedup metrics
    metrics = calculate_metrics(t_seq, t_par, manager.num_workers, total_valid)

    # 7. Clear screen for the final Dashboard render
    clear_screen()
    
    # 8. Print header and dashboard panels
    console.print("=" * 80, style="bold blue")
    console.print("  SDC-504: PARALLEL & DISTRIBUTED WEB CRAWLER DASHBOARD", style="bold white")
    console.print("=" * 80, style="bold blue")
    console.print()

    render_dashboard(metrics, par_results, num_chunks)
    console.print()

    # 9. Save parallel crawl outcomes to results.json
    save_results(par_results, "results.json")
    console.print()

    # 10. Print final confirmation message
    console.print("=" * 80, style="bold blue")
    console.print("  [SUCCESS] Distributed analysis completed successfully. Master-Worker run finished.", style="bold green")
    console.print("=" * 80, style="bold blue")


if __name__ == "__main__":
    main()
