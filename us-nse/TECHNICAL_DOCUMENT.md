# Technical Document — Stock Screener

**Version:** 1.0  
**Date:** May 11, 2026  
**Language:** Python 3.10+  
**UI Framework:** Streamlit  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Module Reference](#3-module-reference)
   - 3.1 [stock_lists.py](#31-stock_listspy)
   - 3.2 [screener.py](#32-screenerpy)
   - 3.3 [app.py](#33-apppy)
4. [Data Flow](#4-data-flow)
5. [Screening Criteria & Algorithms](#5-screening-criteria--algorithms)
   - 5.1 [Relative Strength Index (RSI)](#51-relative-strength-index-rsi)
   - 5.2 [Volume Spike](#52-volume-spike)
   - 5.3 [P/E Ratio](#53-pe-ratio)
6. [Rate Limit Strategy](#6-rate-limit-strategy)
7. [Caching Strategy](#7-caching-strategy)
8. [UI Design](#8-ui-design)
9. [Configuration & Defaults](#9-configuration--defaults)
10. [Dependencies](#10-dependencies)
11. [Setup & Running](#11-setup--running)
12. [Limitations & Known Constraints](#12-limitations--known-constraints)

---

## 1. Project Overview

This application is a near-real-time stock screener that scans either the **Indian NSE (Nifty 500)** or **US NYSE (S&P 500)** universe of stocks and surfaces candidates satisfying a combination of value, momentum, and volume criteria. Results are displayed through an interactive Streamlit dashboard that auto-refreshes on a user-configurable interval.

### Primary Use Case

Identify stocks that are:
- **Undervalued** relative to earnings (low P/E)
- **Gaining momentum** (RSI trending upward)
- **Attracting unusual attention** (abnormal volume activity)

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        app.py                           │
│              (Streamlit UI / Orchestrator)               │
│                                                         │
│  ┌─────────────┐        ┌────────────────────────────┐  │
│  │ stock_lists │        │        screener.py         │  │
│  │    .py      │        │                            │  │
│  │             │        │  batch_download_history()  │  │
│  │ get_nifty   │──────▶ │  first_pass_filter()       │  │
│  │ 500_tickers │        │  fetch_pe_ratios()         │  │
│  │             │        │  run_screen()              │  │
│  │ get_sp500   │        │                            │  │
│  │ _tickers    │        └────────────┬───────────────┘  │
│  └─────────────┘                     │                  │
│                                      ▼                  │
│                              yfinance API               │
│                         (Yahoo Finance backend)         │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| `app.py` | Streamlit UI, session state management, refresh logic, result rendering |
| `screener.py` | All data fetching, indicator calculation, multi-pass filtering, ranking |
| `stock_lists.py` | Ticker universe management with Wikipedia scraping and hardcoded fallbacks |
| `yfinance` | External data source — OHLCV history and fundamental info |

---

## 3. Module Reference

### 3.1 `stock_lists.py`

Responsible for providing the universe of tickers to screen. Both functions are decorated with `@st.cache_data(ttl=86400)`, meaning the ticker list is re-fetched at most once per 24 hours.

#### `get_nifty500_tickers() → list[str]`

Scrapes the [NIFTY 500 Wikipedia page](https://en.wikipedia.org/wiki/NIFTY_500) using `pandas.read_html()`. It searches all tables for a column named `symbol`, `ticker`, `nse symbol`, or `company`. Tickers are suffixed with `.NS` (required by yfinance for NSE-listed securities).

**Fallback behaviour:** If Wikipedia scraping fails (network error, page structure change), returns a hardcoded list of ~50 large-cap Nifty stocks.

#### `get_sp500_tickers() → list[str]`

Scrapes the [S&P 500 Wikipedia page](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies), reading the `Symbol` column from the first table. Dot notation in tickers is converted to hyphens (e.g. `BRK.B` → `BRK-B`) for yfinance compatibility.

**Fallback behaviour:** Returns a hardcoded list of ~50 large-cap S&P 500 stocks.

---

### 3.2 `screener.py`

Contains all quantitative logic. No UI code. Operates purely on DataFrames and returns structured data to the caller.

#### `compute_rsi(closes: pd.Series, period: int = 14) → float`

Implements RSI using **Wilder's Smoothing Method** (exponential moving average variant). Returns `NaN` if fewer than `period + 1` data points are available.

**Algorithm:** See [Section 5.1](#51-relative-strength-index-rsi).

---

#### `batch_download_history(tickers: list[str], period: str = "2mo") → dict[str, pd.DataFrame]`

Downloads OHLCV history for all tickers in a single batched `yf.download()` call per 100-ticker chunk. Uses `group_by="ticker"` and `threads=True` for parallelism within yfinance.

Returns a dict mapping `ticker → DataFrame[Close, Volume]`.

**Chunk size:** 100 tickers per API call (avoids HTTP URL length limits).  
**Delay:** 0.5s between chunks.  
**Single-ticker edge case:** When the chunk has exactly 1 ticker, yfinance returns an un-grouped DataFrame — handled explicitly.

---

#### `compute_volume_spike(df: pd.DataFrame) → float`

Computes the ratio of the most recent day's volume to the 20-day simple average of preceding volume:

$$\text{Volume Spike} = \frac{V_{\text{today}}}{\bar{V}_{20}}$$

where $\bar{V}_{20} = \frac{1}{20} \sum_{i=-21}^{-2} V_i$ (excludes today from the average).

Returns `NaN` if fewer than 21 data points exist or if average volume is zero.

---

#### `first_pass_filter(history, min_rsi, min_volume_spike) → pd.DataFrame`

Iterates over all downloaded tickers, computes RSI and volume spike for each, and retains only those passing both thresholds. Returns a DataFrame with columns: `Ticker`, `Price`, `RSI`, `Volume Ratio`.

This is the **cheap pass** — no individual API calls, only math on already-downloaded data.

---

#### `fetch_pe_ratios(tickers: list[str], progress_callback=None) → dict[str, float]`

Fetches `trailingPE` (falling back to `forwardPE`) from `yf.Ticker(ticker).info` for each surviving ticker. Processes tickers in batches of 10 with a 1-second delay between batches to respect yfinance rate limits.

This is the **expensive pass** — one HTTP request per ticker. It is intentionally deferred to after the first-pass filter to minimise API usage.

---

#### `run_screen(tickers, max_pe, min_rsi, min_volume_spike, top_n, progress_bar) → pd.DataFrame`

Orchestrates the full pipeline:

```
tickers (500)
    │
    ▼
batch_download_history()          ← ~5–10 API calls (batches of 100)
    │
    ▼
first_pass_filter()               ← pure computation, 0 API calls
    │  (survivors: typically 5–30)
    ▼
fetch_pe_ratios()                 ← 1 API call per survivor
    │
    ▼
P/E filter (< max_pe, > 0)
    │
    ▼
sort by Volume Ratio desc → head(top_n)
    │
    ▼
DataFrame[Rank, Ticker, Price, P/E, Volume Ratio, RSI]
```

Updates a Streamlit progress bar at each stage if provided.

---

### 3.3 `app.py`

Streamlit application entry point. Manages the UI lifecycle and orchestrates calls to `screener.py`.

#### Session State Variables

| Key | Type | Purpose |
|---|---|---|
| `last_run` | `float` | Unix timestamp of last successful screen run |
| `results` | `pd.DataFrame \| None` | Cached result set from last run |
| `last_market` | `str \| None` | Market selected at last run (to detect market switches) |

#### Refresh Logic

A fetch is triggered when **any** of the following is true:

```python
should_fetch = (
    manual_refresh           # user clicked "Refresh Now"
    or market_changed        # user switched NSE ↔ NYSE
    or (auto_refresh and elapsed >= 55)  # 60s interval elapsed
)
```

The 55-second threshold (vs. 60s sleep) provides a small overlap buffer to account for Streamlit's rerun latency.

#### Auto-Refresh Mechanism

Implemented via `time.sleep(60)` followed by `st.rerun()` at the bottom of the script. Streamlit's execution model reruns the entire script on each interaction; the sleep-then-rerun pattern is the standard approach for timer-based refreshes in Streamlit.

---

## 4. Data Flow

```
Wikipedia (HTML tables)
        │
        │ pandas.read_html()
        ▼
  Ticker Universe
  (500 symbols)
        │
        │ yf.download(batch, period="2mo")
        ▼
  OHLCV DataFrames
  per ticker (2 months)
        │
        │ compute_rsi() + compute_volume_spike()
        ▼
  Candidates
  (pass RSI > 50, Vol > 2x)
        │
        │ yf.Ticker(t).info  [per survivor]
        ▼
  P/E Ratios
        │
        │ filter P/E < 20, sort by Vol Spike desc
        ▼
  Final Results DataFrame
        │
        │ Streamlit st.dataframe()
        ▼
  Browser UI
```

---

## 5. Screening Criteria & Algorithms

### 5.1 Relative Strength Index (RSI)

RSI is a momentum oscillator that measures the speed and magnitude of price changes. It oscillates between 0 and 100.

**Wilder's Smoothing Method:**

1. Compute daily price changes: $\Delta_i = C_i - C_{i-1}$
2. Separate gains and losses:
   $$G_i = \max(\Delta_i, 0), \quad L_i = \max(-\Delta_i, 0)$$
3. Seed with simple averages over the first `period` days:
   $$\overline{G}_0 = \frac{1}{n}\sum_{i=1}^{n} G_i, \quad \overline{L}_0 = \frac{1}{n}\sum_{i=1}^{n} L_i$$
4. Apply Wilder's EMA for subsequent days:
   $$\overline{G}_t = \frac{\overline{G}_{t-1} \cdot (n-1) + G_t}{n}, \quad \overline{L}_t = \frac{\overline{L}_{t-1} \cdot (n-1) + L_t}{n}$$
5. Compute Relative Strength and RSI:
   $$RS = \frac{\overline{G}}{\overline{L}}, \quad RSI = 100 - \frac{100}{1 + RS}$$

**Threshold used:** RSI > 50 (indicating net bullish momentum).

**Period:** 14 days (Wilder's standard).

**Data requirement:** Minimum 15 trading days (`period + 1`).

---

### 5.2 Volume Spike

Measures abnormal trading activity relative to recent history.

$$\text{Volume Spike Ratio} = \frac{V_{\text{today}}}{\bar{V}_{20\text{-day}}}$$

where $\bar{V}_{20\text{-day}}$ is the simple moving average of the 20 trading days preceding today (today is excluded to avoid look-ahead bias).

**Threshold used:** Ratio > 2.0 (today's volume is more than twice the recent average).

**Data requirement:** Minimum 21 trading days.

---

### 5.3 P/E Ratio

Price-to-Earnings ratio sourced from yfinance's `Ticker.info` dictionary:

- Primary field: `trailingPE` (based on last 12 months of actual earnings)
- Fallback field: `forwardPE` (based on analyst estimates for next 12 months)

**Threshold used:** P/E < 20 and P/E > 0 (negative P/E stocks, which imply losses, are excluded).

P/E is fetched **only for stocks that have already passed** the RSI and volume spike filters, minimising total API calls.

---

## 6. Rate Limit Strategy

yfinance connects to Yahoo Finance, which imposes informal rate limits of approximately **2,000 requests per hour** for unauthenticated access. Exceeding this results in `429 Too Many Requests` errors and temporary IP-level throttling.

### Two-Pass Approach

| Pass | What | API Calls | Per Run |
|---|---|---|---|
| Pass 1 | Batch OHLCV download | `ceil(N / 100)` calls | ~5–6 calls for 500 tickers |
| Pass 2 | Individual `.info` for P/E | 1 call per survivor | Typically 5–30 calls |
| **Total** | | | **~10–36 calls per run** |

Compared to a naive approach (1 `.info` call per ticker = 500 calls per run), this is a **10–50× reduction** in API usage.

### Delays

| Location | Delay | Reason |
|---|---|---|
| Between 100-ticker download chunks | 0.5s | Avoid bursting batch requests |
| Between 10-ticker P/E batches | 1.0s | Throttle individual info calls |

### Refresh Interval

60 seconds between full runs. At maximum, this produces ~36 API calls/minute = ~2,160 calls/hour, which approaches the limit. In practice, far fewer stocks pass the first-pass filter, so typical usage is well within limits.

---

## 7. Caching Strategy

| Cache | TTL | Scope | What is cached |
|---|---|---|---|
| `get_nifty500_tickers` | 24 hours | Streamlit `@st.cache_data` | List of ~500 NSE tickers |
| `get_sp500_tickers` | 24 hours | Streamlit `@st.cache_data` | List of ~500 NYSE tickers |
| `st.session_state.results` | Until next refresh | Streamlit session state | Last screen result DataFrame |
| `st.session_state.last_run` | Session lifetime | Streamlit session state | Timestamp for refresh logic |

The ticker lists are scraped from Wikipedia once per day. The screen results persist in session state and are only recomputed when the 60-second interval elapses, the user clicks Refresh, or the selected market changes.

---

## 8. UI Design

### Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  📈 Stock Screener                                                  │
│  Filter stocks by P/E, Volume Spike & RSI — auto-refreshes 60s    │
├──────────────┬─────────────────────────────────────────────────────┤
│  SIDEBAR     │  MAIN AREA                                          │
│              │                                                     │
│  Market      │  [Stocks Found] [Avg P/E] [Top Vol] [Avg RSI]      │
│  radio       │                                                     │
│              │  ─────────────────────────────────────────          │
│  Filters     │                                                     │
│  ─ P/E       │  Rank │ Ticker │ Price │ P/E │ Vol Spike │ RSI     │
│  ─ Vol Spike │   1   │  XYZ   │ $...  │ ... │   ...x    │  ...   │
│  ─ RSI       │   2   │  ...   │  ...  │ ... │   ...x    │  ...   │
│  ─ Top N     │   ⋮   │   ⋮    │   ⋮   │  ⋮  │    ⋮      │   ⋮   │
│              │                                                     │
│  Auto-       │  Last updated: 2026-05-11 00:59:47                 │
│  refresh     │                                                     │
│  Refresh Now │                                                     │
└──────────────┴─────────────────────────────────────────────────────┘
```

### Summary Metric Cards

Four cards displayed above the table provide at-a-glance statistics:
- **Stocks Found** — count of results passing all filters
- **Avg P/E** — mean P/E across results
- **Top Vol Spike** — highest volume ratio among results
- **Avg RSI** — mean RSI across results

### Results Table

Rendered using `st.dataframe()` with typed column configurations:

| Column | Type | Format |
|---|---|---|
| Ticker | Text | Plain string |
| Price | Text | `₹1,234.56` or `$1,234.56` |
| P/E | Number | `%.2f` |
| Vol Spike | Number | `%.2fx` |
| RSI (14) | Number | `%.1f` |

Table height is dynamically calculated as `min(rows × 38 + 40, 800)` pixels, capped at 800px with scrolling.

---

## 9. Configuration & Defaults

All thresholds are adjustable at runtime via the sidebar. Defaults:

| Parameter | Default | Sidebar Range |
|---|---|---|
| Max P/E | 20.0 | 5.0 – 50.0 (step 0.5) |
| Min Volume Spike | 2.0x | 1.0 – 10.0 (step 0.1) |
| Min RSI | 50.0 | 30.0 – 80.0 (step 1.0) |
| Top N Results | 50 | 10 – 100 (step 5) |
| Refresh Interval | 60s | Toggle on/off |
| RSI Period | 14 | Hardcoded |
| History Period | 2 months | Hardcoded |
| Batch Download Chunk Size | 100 tickers | Hardcoded |
| P/E Fetch Batch Size | 10 tickers | Hardcoded |

---

## 10. Dependencies

| Package | Minimum Version | Purpose |
|---|---|---|
| `streamlit` | 1.30.0 | Web UI framework |
| `yfinance` | 0.2.36 | Yahoo Finance data access |
| `pandas` | 2.0.0 | DataFrame operations, Wikipedia scraping |
| `numpy` | 1.24.0 | Numerical RSI computation |
| `lxml` | 4.9.0 | HTML parsing backend for `pandas.read_html` |
| `html5lib` | 1.1 | Fallback HTML parser |

---

## 11. Setup & Running

### Installation

```bash
# Clone or place project files in a directory
cd d:\cs\Devlop\us-nse

# Install all dependencies
pip install -r requirements.txt
```

### Running

```bash
streamlit run app.py --server.port 8601
```

Access at: `http://localhost:8601`

### Stopping

Press `Ctrl+C` in the terminal where Streamlit is running.

### File Structure

```
us-nse/
├── app.py                  # Streamlit UI entry point
├── screener.py             # Screening logic (RSI, volume, P/E)
├── stock_lists.py          # Ticker universe fetcher
├── requirements.txt        # Python dependencies
├── CLAUDE.md               # Project summary
└── TECHNICAL_DOCUMENT.md   # This document
```

---

## 12. Limitations & Known Constraints

### Data Source

- **yfinance is unofficial.** It scrapes Yahoo Finance and is not a licensed market data feed. Data may be delayed, incorrect, or unavailable during Yahoo Finance outages.
- **P/E data availability:** Not all tickers have `trailingPE` or `forwardPE` in yfinance's `.info`. Such tickers are dropped from results.
- **NSE ticker accuracy:** The Wikipedia Nifty 500 page structure may change, causing scraping to fail and falling back to the hardcoded ~50-ticker list. Full 500-ticker coverage requires a stable scrape.

### Rate Limits

- Running the screener on the full 500-ticker universe multiple times per minute will approach or exceed Yahoo Finance's informal rate limits (~2,000 req/hr), potentially resulting in temporary blocks.
- The 60-second refresh interval is the minimum recommended interval for reliable operation.

### RSI Computation

- RSI is computed on **daily close prices**. It reflects daily momentum, not intraday momentum. A stock that has been rising for 14+ days but is falling intraday may still show high RSI.
- Minimum 15 daily data points are required; tickers with shorter histories (e.g. recently listed stocks) are excluded.

### Volume Spike

- Volume is compared against a simple 20-day average, not an exponential or weighted average. This may produce high ratios for tickers with historically thin volume.
- Pre-market and after-hours volume is not considered.

### Auto-Refresh

- Streamlit's `time.sleep(60)` + `st.rerun()` approach blocks the server-side thread during the sleep. With multiple concurrent users, this can degrade server responsiveness. For production use, consider `streamlit-autorefresh` or a query-parameter-based refresh approach.

### No Persistence

- Results are not stored to disk. Restarting the app clears all cached results and session state. There is no historical data or alerting capability.
