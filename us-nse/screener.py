"""Core stock screening logic: data fetching, RSI, volume spike, P/E filtering."""

import time
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st


def compute_rsi(closes: pd.Series, period: int = 14) -> float:
    """Compute RSI using Wilder's smoothing method."""
    if len(closes) < period + 1:
        return np.nan
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.iloc[1 : period + 1].mean()
    avg_loss = loss.iloc[1 : period + 1].mean()

    for i in range(period + 1, len(gain)):
        avg_gain = (avg_gain * (period - 1) + gain.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss.iloc[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def batch_download_history(tickers: list[str], period: str = "2mo") -> dict[str, pd.DataFrame]:
    """Download historical data for all tickers in a single batch call."""
    if not tickers:
        return {}

    result = {}
    # Process in chunks to avoid URL length limits
    chunk_size = 100
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i : i + chunk_size]
        try:
            data = yf.download(
                chunk,
                period=period,
                group_by="ticker",
                threads=True,
                progress=False,
            )
            if data.empty:
                continue

            if len(chunk) == 1:
                # Single ticker: data is not grouped
                ticker = chunk[0]
                if not data.empty and "Close" in data.columns:
                    result[ticker] = data[["Close", "Volume"]].dropna()
            else:
                for ticker in chunk:
                    try:
                        ticker_data = data[ticker][["Close", "Volume"]].dropna()
                        if not ticker_data.empty:
                            result[ticker] = ticker_data
                    except (KeyError, TypeError):
                        continue
        except Exception:
            continue

        # Small delay between chunks to respect rate limits
        if i + chunk_size < len(tickers):
            time.sleep(0.5)

    return result


def compute_volume_spike(df: pd.DataFrame) -> float:
    """Compute volume spike as ratio of latest volume to 20-day avg."""
    if len(df) < 21 or "Volume" not in df.columns:
        return np.nan
    avg_vol = df["Volume"].iloc[-21:-1].mean()
    if avg_vol == 0:
        return np.nan
    return df["Volume"].iloc[-1] / avg_vol


def first_pass_filter(
    history: dict[str, pd.DataFrame],
    min_rsi: float = 50.0,
    min_volume_spike: float = 2.0,
) -> pd.DataFrame:
    """Filter tickers by RSI > threshold and volume spike > threshold.
    Returns DataFrame with ticker, RSI, volume_spike, current_price.
    """
    rows = []
    for ticker, df in history.items():
        if len(df) < 21:
            continue
        rsi = compute_rsi(df["Close"])
        vol_spike = compute_volume_spike(df)
        if np.isnan(rsi) or np.isnan(vol_spike):
            continue
        if rsi > min_rsi and vol_spike > min_volume_spike:
            rows.append({
                "Ticker": ticker,
                "Price": round(df["Close"].iloc[-1], 2),
                "RSI": round(rsi, 2),
                "Volume Ratio": round(vol_spike, 2),
            })
    return pd.DataFrame(rows)


def fetch_pe_ratios(tickers: list[str], progress_callback=None) -> dict[str, float]:
    """Fetch P/E ratios for a list of tickers with rate limiting."""
    pe_map = {}
    batch_size = 10
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        for ticker in batch:
            try:
                info = yf.Ticker(ticker).info
                pe = info.get("trailingPE") or info.get("forwardPE")
                if pe is not None:
                    pe_map[ticker] = round(float(pe), 2)
            except Exception:
                continue
        if progress_callback:
            progress_callback(min((i + batch_size) / len(tickers), 1.0))
        # Rate limit: pause between batches
        if i + batch_size < len(tickers):
            time.sleep(1.0)
    return pe_map


def run_screen(
    tickers: list[str],
    max_pe: float = 20.0,
    min_rsi: float = 50.0,
    min_volume_spike: float = 2.0,
    top_n: int = 50,
    progress_bar=None,
) -> pd.DataFrame:
    """Run the full screening pipeline.

    1. Batch download historical data (1 call per 100-ticker chunk)
    2. Filter by RSI and volume spike
    3. Fetch P/E only for survivors
    4. Filter by P/E
    5. Rank by volume spike descending
    """
    # Step 1: Batch download
    if progress_bar:
        progress_bar.progress(0.1, "Downloading price & volume data...")
    history = batch_download_history(tickers)

    if not history:
        return pd.DataFrame()

    # Step 2: First pass filter (RSI + volume spike)
    if progress_bar:
        progress_bar.progress(0.4, "Computing RSI & volume spikes...")
    candidates = first_pass_filter(history, min_rsi, min_volume_spike)

    if candidates.empty:
        return candidates

    # Step 3: Fetch P/E for survivors only
    survivor_tickers = candidates["Ticker"].tolist()
    if progress_bar:
        progress_bar.progress(0.6, f"Fetching P/E for {len(survivor_tickers)} candidates...")

    def pe_progress(pct):
        if progress_bar:
            progress_bar.progress(0.6 + pct * 0.3, "Fetching P/E ratios...")

    pe_map = fetch_pe_ratios(survivor_tickers, progress_callback=pe_progress)

    # Step 4: Apply P/E filter
    candidates["P/E"] = candidates["Ticker"].map(pe_map)
    candidates = candidates.dropna(subset=["P/E"])
    candidates = candidates[candidates["P/E"] < max_pe]
    candidates = candidates[candidates["P/E"] > 0]  # Exclude negative P/E

    if candidates.empty:
        return candidates

    # Step 5: Rank by volume spike descending
    candidates = candidates.sort_values("Volume Ratio", ascending=False).head(top_n)
    candidates = candidates.reset_index(drop=True)
    candidates.index = candidates.index + 1  # 1-based ranking
    candidates.index.name = "Rank"

    # Reorder columns
    candidates = candidates[["Ticker", "Price", "P/E", "Volume Ratio", "RSI"]]

    if progress_bar:
        progress_bar.progress(1.0, "Done!")

    return candidates
