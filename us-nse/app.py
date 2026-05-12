"""Stock Screener Dashboard — Streamlit UI."""

import time
import streamlit as st
from stock_lists import get_nifty500_tickers, get_sp500_tickers
from screener import run_screen

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Screener",
    page_icon="📈",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #888;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
    }
    div[data-testid="stDataFrame"] {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">📈 Stock Screener</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Filter stocks by P/E, Volume Spike & RSI — auto-refreshes every 60s</p>',
    unsafe_allow_html=True,
)

# ── Sidebar Controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    market = st.radio(
        "Market",
        options=["NSE (Nifty 500)", "NYSE (S&P 500)"],
        index=0,
        help="Select Indian NSE or US NYSE stocks",
    )

    st.divider()
    st.subheader("Filter Thresholds")

    max_pe = st.slider("Max P/E Ratio", 5.0, 50.0, 20.0, 0.5)
    min_volume_spike = st.slider("Min Volume Spike (x avg)", 1.0, 10.0, 2.0, 0.1)
    min_rsi = st.slider("Min RSI", 30.0, 80.0, 50.0, 1.0)
    top_n = st.slider("Top N Results", 10, 100, 50, 5)

    st.divider()
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=True)
    manual_refresh = st.button("🔄 Refresh Now", use_container_width=True)

    st.divider()
    st.caption(
        "**Rate Limits:** yfinance ~2000 req/hr. "
        "This app uses batch downloads and two-pass filtering to minimize API calls."
    )

# ── Session State ─────────────────────────────────────────────────────────────
if "last_run" not in st.session_state:
    st.session_state.last_run = 0
if "results" not in st.session_state:
    st.session_state.results = None
if "last_market" not in st.session_state:
    st.session_state.last_market = None

# ── Determine if we need to fetch ────────────────────────────────────────────
now = time.time()
market_changed = st.session_state.last_market != market
elapsed = now - st.session_state.last_run
should_fetch = manual_refresh or market_changed or (auto_refresh and elapsed >= 55)

# ── Main Area ─────────────────────────────────────────────────────────────────
if should_fetch:
    # Get ticker list
    with st.spinner("Loading ticker list..."):
        if "NSE" in market:
            tickers = get_nifty500_tickers()
            currency = "₹"
        else:
            tickers = get_sp500_tickers()
            currency = "$"

    st.info(f"Screening **{len(tickers)}** tickers from **{market}**...")

    progress_bar = st.progress(0, "Starting...")

    results = run_screen(
        tickers=tickers,
        max_pe=max_pe,
        min_rsi=min_rsi,
        min_volume_spike=min_volume_spike,
        top_n=top_n,
        progress_bar=progress_bar,
    )

    progress_bar.empty()

    st.session_state.results = results
    st.session_state.last_run = time.time()
    st.session_state.last_market = market

results = st.session_state.results

# ── Display Results ───────────────────────────────────────────────────────────
if results is not None and not results.empty:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{len(results)}</div>'
            f'<div class="metric-label">Stocks Found</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        avg_pe = results["P/E"].mean()
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{avg_pe:.1f}</div>'
            f'<div class="metric-label">Avg P/E</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        max_vol = results["Volume Ratio"].max()
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{max_vol:.1f}x</div>'
            f'<div class="metric-label">Top Vol Spike</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        avg_rsi = results["RSI"].mean()
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{avg_rsi:.1f}</div>'
            f'<div class="metric-label">Avg RSI</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Format price column with currency
    display_df = results.copy()
    currency = "₹" if "NSE" in market else "$"
    display_df["Price"] = display_df["Price"].apply(lambda x: f"{currency}{x:,.2f}")

    # Results table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(len(display_df) * 38 + 40, 800),
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="medium"),
            "Price": st.column_config.TextColumn("Price", width="small"),
            "P/E": st.column_config.NumberColumn("P/E", format="%.2f", width="small"),
            "Volume Ratio": st.column_config.NumberColumn(
                "Vol Spike", format="%.2fx", width="small",
                help="Current volume / 20-day average volume",
            ),
            "RSI": st.column_config.NumberColumn("RSI (14)", format="%.1f", width="small"),
        },
    )

    # Last updated timestamp
    import datetime
    last_update = datetime.datetime.fromtimestamp(st.session_state.last_run)
    st.caption(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

elif results is not None:
    st.warning("No stocks matched the current filter criteria. Try relaxing the thresholds.")
else:
    st.info("Click **Refresh Now** or wait for auto-refresh to load data.")

# ── Auto-refresh via rerun ────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
