#!/usr/bin/env python3
"""
Debug script to test data fetching for Indian and US stocks.
Run this to diagnose why the API is returning empty candles.
"""

import sys
sys.path.insert(0, '.')

from app.data_source import YFinanceSource, USStockSource, resolve_source
from app.config import Settings
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = Settings()

print("=" * 80)
print("DATA FETCHING DEBUG TEST")
print("=" * 80)

def test_symbol(symbol: str, expected_source: str):
    """Test fetching data for a symbol."""
    print(f"\nTesting: {symbol}")
    print("-" * 40)
    
    try:
        # Resolve source
        source = resolve_source(symbol)
        print(f"✓ Source: {source.name}")
        assert source.name == expected_source, f"Expected {expected_source}, got {source.name}"
        
        # Test direct API
        print(f"  Testing _fetch_via_api()...")
        try:
            candles = source._fetch_via_api(symbol, "1d", limit=5)
            if candles:
                print(f"  ✓ Direct API succeeded: {len(candles)} candles")
                print(f"    Latest: {candles[-1]}")
            else:
                print(f"  ⚠ Direct API returned empty (likely rate limited)")
        except Exception as e:
            print(f"  ✗ Direct API error: {type(e).__name__}: {str(e)[:100]}")
        
        # Test yfinance fallback
        print(f"  Testing _fetch_via_yfinance()...")
        try:
            import yfinance as yf
            candles = source._fetch_via_yfinance(symbol, "1d", limit=5, yf=yf)
            if candles:
                print(f"  ✓ Fallback succeeded: {len(candles)} candles")
                print(f"    Latest: {candles[-1]}")
            else:
                print(f"  ⚠ Fallback returned empty")
        except Exception as e:
            print(f"  ✗ Fallback error: {type(e).__name__}: {str(e)[:100]}")
        
        # Test orchestrated fetch
        print(f"  Testing _fetch_history_sync()...")
        try:
            candles = source._fetch_history_sync(symbol, "1d", limit=5)
            if candles:
                print(f"  ✓ Orchestrated fetch succeeded: {len(candles)} candles")
                print(f"    Latest: {candles[-1]}")
            else:
                print(f"  ✗ Orchestrated fetch returned empty")
        except Exception as e:
            print(f"  ✗ Orchestrated fetch error: {type(e).__name__}: {str(e)[:100]}")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

# Test Indian stock
test_symbol("RELIANCE.NS", "yfinance")

# Test US stock
test_symbol("AAPL", "yfinance_us")

print("\n" + "=" * 80)
print("NETWORK DIAGNOSTICS")
print("=" * 80)

# Test network connectivity
print("\nChecking DNS resolution...")
try:
    import socket
    
    hosts = [
        "query1.finance.yahoo.com",
        "query2.finance.yahoo.com",
        "fc.yahoo.com",
        "8.8.8.8",
    ]
    
    for host in hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✓ {host} → {ip}")
        except socket.gaierror as e:
            print(f"✗ {host} → {e}")
except Exception as e:
    print(f"DNS test error: {e}")

# Test HTTP connectivity
print("\nChecking HTTP connectivity...")
try:
    import requests
    
    session = requests.Session()
    session.trust_env = False
    
    urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&period1=1000000000&period2=2000000000",
        "https://www.google.com",
    ]
    
    for url in urls:
        try:
            resp = session.get(url, timeout=5)
            print(f"✓ {url[:50]}... → {resp.status_code}")
        except Exception as e:
            print(f"✗ {url[:50]}... → {type(e).__name__}: {str(e)[:50]}")
except Exception as e:
    print(f"HTTP test error: {e}")

print("\n" + "=" * 80)
print("ENVIRONMENT INFO")
print("=" * 80)

import os
print(f"\nProxy settings:")
print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not set')}")
print(f"  HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'Not set')}")
print(f"  NO_PROXY: {os.environ.get('NO_PROXY', 'Not set')}")

print(f"\nPython version: {sys.version}")
print(f"Platform: {sys.platform}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)

print("""
If Direct API is rate limited (429):
  - This is expected - the fallback should handle it
  - Fallback should succeed
  
If both fail with DNS error:
  - Environment is offline or has network restrictions
  - This may be expected in sandbox/restricted networks
  - Will work in production
  
If Direct API succeeds but Frontend shows no data:
  - Check if Frontend is calling the correct API endpoint
  - Verify /api/symbols endpoint shows all 29 symbols
  - Check browser console for errors
  - May need to refresh page
  
For testing in restricted networks:
  - Use mock data or pre-recorded responses
  - Or deploy to environment with internet access
""")
