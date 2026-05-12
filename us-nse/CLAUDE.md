# US-NSE Stock Screener

## Project Overview
A real-time stock screener that filters Indian NSE (Nifty 500) or US NYSE (S&P 500) stocks based on technical and fundamental criteria, displayed in a Streamlit dashboard.

## Tech Stack
- **Language**: Python 3.10+
- **UI**: Streamlit (port 8601)
- **Data Source**: yfinance
- **Key Libraries**: pandas, numpy, yfinance, streamlit

## Architecture
- `app.py` — Streamlit UI with auto-refresh (60s interval)
- `screener.py` — Core screening logic (data fetch, RSI calc, volume spike, P/E filtering)
- `stock_lists.py` — Fetches Nifty 500 / S&P 500 ticker lists from Wikipedia

## Screening Criteria
1. **P/E Ratio** < 20
2. **Volume Spike** > 2x the 20-day average volume
3. **RSI (14-period)** > 50

## Ranking
Results ranked by **Volume Spike** (highest first), top 50 displayed.

## Rate Limit Strategy
- yfinance rate limit: ~2000 req/hour
- **Two-pass approach**: Batch download price/volume for all tickers first (1 API call), then fetch P/E only for stocks passing RSI + volume filters (minimizes individual info calls)
- 60-second refresh interval with caching to avoid redundant fetches
- Batch size of 50 tickers for info calls with 1s delay between batches

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py --server.port 8601
```

## Key Decisions
- Nifty 500 tickers sourced from Wikipedia, suffixed with `.NS` for yfinance
- S&P 500 used as proxy for NYSE-listed stocks
- RSI calculated using 14-period Wilder's smoothing method
- Results cached with `@st.cache_data(ttl=55)` to avoid redundant fetches within refresh cycle
