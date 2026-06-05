# 🕷️ Custom Distributed Web Crawler for Parallel Domain Analysis

> **Course:** Parallel & Distributed Computing (SDC-504)  
> **Language:** Python 3.10+  
> **Architecture:** Master-Worker using `multiprocessing.Pool`

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Performance Benchmarking](#performance-benchmarking)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Output & Dashboard](#output--dashboard)
- [Configuration](#configuration)
- [Dependencies](#dependencies)

---

## Overview

A multi-process web crawler that distributes URL crawling across all available CPU cores using Python's `multiprocessing` module. It fetches page metadata (title, link count, size, response time) from a list of target URLs and benchmarks parallel performance against a sequential baseline — measuring real speedup, parallel efficiency, and Amdahl's Law theoretical limits.

---

## Architecture

```
Master Process (main.py / master.py)
│
├── url_loader.py     → Loads, validates, and partitions URLs into chunks
├── benchmark.py      → Runs sequential baseline (T_seq) and calculates metrics
├── master.py         → Spawns multiprocessing.Pool and dispatches chunks to workers
│
└── Worker Processes (crawler.py)
    ├── crawl_chunk() → Crawls assigned URL slice sequentially
    └── crawl_url()   → Fetches a single URL and extracts metadata
```

The **Master Process** handles orchestration, benchmarking, and result aggregation. **Worker Processes** are stateless and only execute `crawl_chunk()` on their assigned URL slices.

---

## Project Structure

```
.
├── main.py           # Entry point — orchestrates the full pipeline
├── master.py         # ParallelCrawlerManager — pool lifecycle & chunk dispatch
├── crawler.py        # Worker functions: crawl_url() and crawl_chunk()
├── benchmark.py      # Sequential baseline runner and metric calculations
├── dashboard.py      # Rich terminal dashboard renderer
├── url_loader.py     # URL loading, validation, and partitioning
├── urls.txt          # Target URLs (one per line)
├── results.json      # Output — parallel crawl results (auto-generated)
└── requirements.txt  # Python dependencies
```

---

## How It Works

1. **Load URLs** — `url_loader.py` reads `urls.txt`, validates each URL (must start with `http://` or `https://`), and falls back to 10 safe default URLs if the file is missing or empty.
2. **Sequential Baseline** — `benchmark.py` crawls all URLs one-by-one and records total time `T_seq`.
3. **Parallel Crawl** — `master.py` partitions URLs into N chunks (one per CPU core) and dispatches them to a `multiprocessing.Pool`. Each worker runs `crawl_chunk()`.
4. **Metrics** — Speedup, parallel efficiency, and Amdahl's Law comparison are calculated.
5. **Dashboard** — A color-coded terminal dashboard is rendered via the `rich` library.
6. **Save Results** — All parallel crawl results are saved to `results.json`.

---

## Performance Benchmarking

The benchmark module computes the following metrics:

| Metric | Formula |
|---|---|
| Speedup (S) | `T_seq / T_par` |
| Parallel Efficiency (E) | `(S / N) × 100%` |
| Amdahl's Max Speedup | `1 / (f + (1 - f) / N)` |
| Avg Time/URL (Seq) | `T_seq / num_urls` |
| Avg Time/URL (Par) | `T_par / num_urls` |

> **Serial Fraction (f):** Set to `0.1` — representing overhead from URL loading, chunking, and result merging.

---

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**2. (Optional) Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## Usage

**Run the crawler:**
```bash
python main.py
```

To crawl custom URLs, edit `urls.txt` — add one URL per line:
```
https://www.example.com
https://www.python.org
https://news.ycombinator.com
```

> ⚠️ **Windows users:** The `if __name__ == '__main__':` guard in `main.py` is required for `multiprocessing` to work correctly on Windows. Do not remove it.

---

## Output & Dashboard

After execution, the terminal renders a live dashboard with:

- **System Information** — core count, URL count, chunk count, pool type
- **Execution Timing** — `T_seq`, `T_par`, average time per URL for both modes
- **Performance Evaluation** — Speedup, efficiency %, Amdahl's max, color-coded rating (Excellent / Moderate / Degraded)
- **Crawl Results Table** — domain, status, HTTP code, response time, page size, link count, title
- **Consolidated Summary** — success/failure/error totals, fastest & slowest URLs, highest link density

Results are also saved to **`results.json`** in the project root.

---

## Configuration

| Parameter | Location | Default | Description |
|---|---|---|---|
| `num_workers` | `master.py` | `cpu_count()` | Number of parallel worker processes |
| `serial_fraction` | `benchmark.py` | `0.1` | Serial overhead fraction for Amdahl's Law |
| Request timeout | `crawler.py` | `(5, 10)` | Connection timeout / read timeout in seconds |
| Title max length | `crawler.py` | `50` chars | Maximum characters stored for page titles |
| Fallback URLs | `url_loader.py` | 10 URLs | Used when `urls.txt` is missing or empty |

---

## Dependencies

```
requests>=2.28.0
beautifulsoup4>=4.11.0
rich>=13.0.0
```

Install with:
```bash
pip install -r requirements.txt
```
