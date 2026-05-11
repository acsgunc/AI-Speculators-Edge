# 📈 Speculator's Edge — Stock Threshold Calculator

A Python/Streamlit app that fetches real-time stock prices and calculates **Buy** (dip) and **Sell** (gain) target prices based on percentage offsets.

---

## Features

- **Ticker Lookup** — Enter any stock symbol and fetch the current Last Traded Price via `yfinance`.
- **Standard Targets** — Automatically shows price targets at **-10 %**, **-20 %**, **+10 %**, **+20 %**.
- **Custom Percentage** — Add your own percentage from the sidebar and it merges into the results.
- **Clean Table** — Results rendered as a Pandas DataFrame for easy reading.

---

## Project Structure

```
A/
├── app.py                   # Thin orchestrator — wires layers together
├── config.py                # App-wide constants
├── requirements.txt         # Python dependencies
├── services/
│   ├── calculator.py        # Pure business logic (threshold math + parsing)
│   └── price_service.py     # Data access layer (yfinance)
└── ui/
    ├── inputs.py            # Main-area & sidebar input widgets
    └── results.py           # Output rendering
```

---

## Prerequisites

- **Python 3.10+**

---

## Installation & Running

```bash
# 1. Clone the repo
git clone <repo-url> && cd A

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
streamlit run app.py
```

The app opens at **http://localhost:8501**.

---

## How to Use

1. Type a **Stock Ticker** (e.g. `AAPL`, `TSLA`) in the main input.
2. Click **Fetch Current Price** — the last traded price is retrieved.
3. A table appears with dip/gain targets at the standard **10 %** and **20 %** levels.
4. Open the **sidebar** and enter a **Custom Percentage** (e.g. `15`) to add that level to the table.

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Web UI | [Streamlit](https://streamlit.io/) |
| Market Data | [yfinance](https://github.com/ranaroussi/yfinance) |
| Data Tables | [Pandas](https://pandas.pydata.org/) |
