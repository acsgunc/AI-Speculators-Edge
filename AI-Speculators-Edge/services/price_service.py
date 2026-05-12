from dataclasses import dataclass

import yfinance as yf


@dataclass
class PriceResult:
    price: float
    label: str


class PriceFetchError(Exception):
    pass


def fetch_last_price(ticker: str) -> PriceResult:
    try:
        stock = yf.Ticker(ticker)
        ltp = getattr(stock.fast_info, "last_price", None)
    except Exception as exc:
        raise PriceFetchError(
            f"Failed to fetch data for {ticker}. "
            "Please verify the ticker symbol is correct."
        ) from exc

    if ltp is None or ltp <= 0:
        raise PriceFetchError(
            f"Could not retrieve a valid price for {ticker}. "
            "Please check the ticker symbol and try again."
        )

    return PriceResult(
        price=round(ltp, 2),
        label=f"{ticker} (Last Traded Price)",
    )
