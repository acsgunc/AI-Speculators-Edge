"""
Mock data source for testing without hitting real API rate limits.

Usage in code:
  source = MockStockSource()
  candles = source.fetch_history_sync("AAPL", "1d")
"""

import sys
sys.path.insert(0, '.')

from app.models import Candle
from datetime import datetime, timedelta
import random


class MockStockSource:
    """Returns mock OHLCV data for testing."""
    
    def fetch_history_sync(self, symbol: str, interval: str, limit: int | None = None) -> list[Candle]:
        """Generate mock candles for testing."""
        if limit is None:
            limit = 100
            
        candles = []
        now = datetime.now()
        base_price = {
            'AAPL': 150.0,
            'MSFT': 420.0,
            'GOOGL': 140.0,
            'AMZN': 180.0,
            'RELIANCE.NS': 2500.0,
        }.get(symbol, 100.0)
        
        for i in range(limit):
            # Generate realistic OHLCV data
            days_ago = (limit - i) * self._interval_to_days(interval)
            timestamp = int((now - timedelta(days=days_ago)).timestamp())
            
            # Add realistic price movement
            open_price = base_price + random.uniform(-5, 5)
            close_price = open_price + random.uniform(-3, 3)
            high_price = max(open_price, close_price) + random.uniform(0, 2)
            low_price = min(open_price, close_price) - random.uniform(0, 2)
            volume = random.randint(1000000, 100000000)
            
            candle = Candle(
                time=timestamp,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=volume,
            )
            candles.append(candle)
            
            # Update base price for next candle
            base_price = close_price
        
        return sorted(candles, key=lambda c: c.time)
    
    @staticmethod
    def _interval_to_days(interval: str) -> float:
        """Convert interval string to days for mock data generation."""
        mapping = {
            '1m': 1/1440,      # 1 minute
            '5m': 5/1440,      # 5 minutes
            '15m': 15/1440,    # 15 minutes
            '1h': 1/24,        # 1 hour
            '1d': 1.0,         # 1 day
        }
        return mapping.get(interval, 1.0)


if __name__ == '__main__':
    # Test the mock source
    mock = MockStockSource()
    candles = mock.fetch_history_sync('AAPL', '1d', limit=5)
    
    print(f"Generated {len(candles)} mock candles for AAPL:")
    for candle in candles:
        print(f"  {datetime.fromtimestamp(candle.time).strftime('%Y-%m-%d')} - "
              f"O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close} V:{candle.volume}")
