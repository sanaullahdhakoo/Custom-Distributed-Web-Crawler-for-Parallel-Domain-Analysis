"""
Dashboard Module for the Custom Distributed Web Crawler.

Role in Master-Worker Architecture:
This module is executed exclusively by the Master Process. It handles:
1. Collecting timing, benchmarking, and crawl results from memory.
2. Rendering a beautiful, color-coded ANSI terminal dashboard using the `rich` library.
3. Constructing distinct panels for System Info, Execution Timing, Performance
   Evaluation, the Results Table (top 20 crawled items), and consolidated Summary Stats.
"""

from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.box import ROUNDED, HEAVY_EDGE

console = Console()


def render_dashboard(metrics: Dict[str, Any], results: List[Dict[str, Any]], num_chunks: int):
    """
    Renders the rich ANSI terminal dashboard.
    Outputs system specs, performance ratings, crawled results, and summaries.
    """
    # ----------------------------------------------------
    # PANEL 1: System Info
    # ----------------------------------------------------
    sys_info_text = Text()
    sys_info_text.append(" Active CPU Cores : ", style="bold cyan")
    sys_info_text.append(f"{metrics['cores_used']}\n", style="white")
    sys_info_text.append(" URLs Ingested    : ", style="bold cyan")
    sys_info_text.append(f"{metrics['num_urls']}\n", style="white")
    sys_info_text.append(" Chunks Created   : ", style="bold cyan")
    sys_info_text.append(f"{num_chunks}\n", style="white")
    sys_info_text.append(" Worker Pool Type : ", style="bold cyan")
    sys_info_text.append("multiprocessing.Pool", style="white")
    
    panel_sys_info = Panel(
        sys_info_text,
        title="[bold cyan]System Information[/bold cyan]",
        border_style="cyan",
        box=ROUNDED,
        expand=True
    )

    # ----------------------------------------------------
    # PANEL 2: Execution Timing
    # ----------------------------------------------------
    timing_text = Text()
    timing_text.append(" Seq. Time (T_seq)  : ", style="bold magenta")
    timing_text.append(f"{metrics['t_seq']:.4f} s\n", style="white")
    timing_text.append(" Par. Time (T_par)  : ", style="bold magenta")
    timing_text.append(f"{metrics['t_par']:.4f} s\n", style="white")
    timing_text.append(" Avg. Time/URL (Seq): ", style="bold magenta")
    timing_text.append(f"{metrics['avg_time_seq']:.4f} s\n", style="white")
    timing_text.append(" Avg. Time/URL (Par): ", style="bold magenta")
    timing_text.append(f"{metrics['avg_time_par']:.4f} s", style="white")
    
    panel_timing = Panel(
        timing_text,
        title="[bold magenta]Execution Timing[/bold magenta]",
        border_style="magenta",
        box=ROUNDED,
        expand=True
    )

    # ----------------------------------------------------
    # PANEL 3: Performance Evaluation (Color-coded)
    # ----------------------------------------------------
    speedup = metrics["speedup"]
    if speedup > 1.5:
        perf_style = "green"
        perf_emoji = "Excellent"
    elif speedup > 1.0:
        perf_style = "yellow"
        perf_emoji = "Moderate"
    else:
        perf_style = "red"
        perf_emoji = "Degraded"
        
    perf_text = Text()
    perf_text.append(" Speedup (S)       : ", style=f"bold {perf_style}")
    perf_text.append(f"{metrics['speedup']}x\n", style="white")
    perf_text.append(" Par. Efficiency   : ", style=f"bold {perf_style}")
    perf_text.append(f"{metrics['efficiency']}%\n", style="white")
    perf_text.append(" Amdahl Max Speedup: ", style="bold blue")
    perf_text.append(f"{metrics['amdahl_max']}x\n", style="white")
    perf_text.append(" Rating            : ", style=f"bold {perf_style}")
    perf_text.append(perf_emoji, style=f"bold {perf_style}")

    panel_perf = Panel(
        perf_text,
        title=f"[bold {perf_style}]Performance ({perf_style.upper()})[/bold {perf_style}]",
        border_style=perf_style,
        box=ROUNDED,
        expand=True
    )

    # Output row of top stats
    console.print(Columns([panel_sys_info, panel_timing, panel_perf]))

    # ----------------------------------------------------
    # PANEL 4: Results Table (Top 20 rows)
    # ----------------------------------------------------
    table = Table(
        title="[bold white]Crawl Results Table [/bold white]",
        title_justify="left",
        border_style="white",
        box=HEAVY_EDGE,
        show_header=True,
        header_style="bold bold"
    )
    table.add_column("Domain", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Code", justify="center")
    table.add_column("Time (s)", justify="right")
    table.add_column("Size (B)", justify="right")
    table.add_column("Links", justify="right")
    table.add_column("Title", style="italic")

    # Select top 20 rows
    top_results = results
    
    for r in top_results:
        status = r["status"]
        code = str(r["status_code"]) if r["status_code"] is not None else "-"
        time_s = f"{r['response_time']:.4f}"
        size_b = f"{r['size_bytes']:,}"
        links = str(r["links_count"])
        title = r["title"] or "-"
        
        # Color code row by status
        if status == "success":
            row_style = "green"
            status_text = "[bold green]Success[/bold green]"
        elif status == "failed":
            row_style = "yellow"
            status_text = f"[bold yellow]Failed[/bold yellow]"
        else:
            row_style = "red"
            status_text = f"[bold red]Error ({r['error_msg']})[/bold red]"
            
        table.add_row(
            r["domain"] or r["url"],
            status_text,
            code,
            time_s,
            size_b,
            links,
            title,
            style=row_style
        )
        
    console.print(table)
    console.print()

    # ----------------------------------------------------
    # PANEL 5: Summary Stats
    # ----------------------------------------------------
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    # Calculate extreme stats
    # Filter for non-zero responses to avoid counting errors as "fastest" if response time was 0,
    # but since response_time is set even on failure, we can search overall.
    fastest_url = "-"
    fastest_time = float("inf")
    slowest_url = "-"
    slowest_time = -1.0
    most_links_url = "-"
    most_links_count = -1
    
    for r in results:
        t = r["response_time"]
        l_cnt = r["links_count"]
        
        # Fastest
        if t < fastest_time:
            fastest_time = t
            fastest_url = r["url"]
            
        # Slowest
        if t > slowest_time:
            slowest_time = t
            slowest_url = r["url"]
            
        # Most links
        if l_cnt > most_links_count:
            most_links_count = l_cnt
            most_links_url = r["url"]
            
    summary_table = Table.grid(padding=(0, 2))
    summary_table.add_column(style="bold yellow")
    summary_table.add_column()
    
    summary_table.add_row("Total Successes :", f"[bold green]{success_count}[/bold green]")
    summary_table.add_row("Total Failures  :", f"[bold yellow]{failed_count}[/bold yellow] (e.g. 4xx/5xx responses)")
    summary_table.add_row("Total Errors    :", f"[bold red]{error_count}[/bold red] (network issues, redirects, SSL)")
    summary_table.add_row("Fastest Run     :", f"[green]{fastest_time:.4f} s[/green] -> {fastest_url}")
    summary_table.add_row("Slowest Run     :", f"[red]{slowest_time:.4f} s[/red] -> {slowest_url}")
    summary_table.add_row("Link Density Max:", f"[cyan]{most_links_count} links[/cyan] -> {most_links_url}")
    
    panel_summary = Panel(
        summary_table,
        title="[bold yellow]Consolidated Crawl Summary[/bold yellow]",
        border_style="yellow",
        box=ROUNDED,
        expand=True
    )
    
    console.print(panel_summary)
