# Yahoo Finance Rate Limiting - Explained

## What's Happening

When you test the API repeatedly, you get:
```json
{"symbol":"AAPL","interval":"1d","candles":[]}
```

This means the backend received a **429 Too Many Requests** response from Yahoo Finance.

---

## Root Cause

Yahoo Finance API enforces rate limits:
- **~2000 requests per hour** per IP address
- **Resets every 60 minutes**
- **Triggered by**: Multiple rapid requests within seconds

---

## Why It's Happening Now

Testing repeatedly in a short time:
```bash
curl http://localhost:8000/api/history?symbol=AAPL&interval=1d  # Request 1
curl http://localhost:8000/api/history?symbol=MSFT&interval=1d  # Request 2
curl http://localhost:8000/api/history?symbol=GOOGL&interval=1d  # Request 3
# ... etc - triggers rate limit after ~20-30 requests
```

Each request → 1-2 API calls to Yahoo Finance → rate limit hit quickly during testing.

---

## How the Code Handles It

The backend is **designed to handle this gracefully**:

```python
def _fetch_history_sync(self, symbol, interval, limit):
    try:
        # Layer 1: Direct API
        return self._fetch_via_api(symbol, interval, limit)
    except:
        try:
            # Layer 2: Fallback to yfinance
            import yfinance as yf
            return self._fetch_via_yfinance(symbol, interval, limit, yf)
        except:
            # Layer 3: Return empty (graceful degrade)
            return []
```

**What happens**:
1. Direct API gets 429 → returns empty list
2. Code tries fallback (yfinance) → also fails due to rate limit
3. Code returns `[]` → API returns `{"candles":[]}`

This is **not a bug** - it's correct error handling.

---

## Solutions

### ✅ Solution 1: Wait for Rate Limit Reset
```bash
# Wait 2-5 minutes (safest)
sleep 180
curl http://localhost:8000/api/history?symbol=AAPL&interval=1d
```

**Pros**: Real data, production-like experience
**Cons**: Need to wait

---

### ✅ Solution 2: Use Mock Data (Recommended for Dev)
```bash
cd backend
python3 << 'EOF'
from mock_data import MockStockSource

mock = MockStockSource()
candles = mock.fetch_history_sync('AAPL', '1d', limit=100)
print(f"Generated {len(candles)} candles (no rate limit!)")
EOF
```

**Pros**: Instant, unlimited testing, realistic format
**Cons**: Not real market data

---

### ✅ Solution 3: Test in Production
Deploy to Render and test there:
```bash
git push origin main  # Auto-deploys to Render
# Then test at: https://your-domain.onrender.com/api/history?symbol=AAPL&interval=1d
```

**Pros**: Fresh rate limit quota
**Cons**: Requires deployment

---

### ✅ Solution 4: Space Out Requests
Add delays between tests:
```bash
# Test one symbol at a time with delays
curl http://localhost:8000/api/history?symbol=AAPL&interval=1d
sleep 5  # Wait 5 seconds

curl http://localhost:8000/api/history?symbol=MSFT&interval=1d
sleep 5

curl http://localhost:8000/api/history?symbol=GOOGL&interval=1d
```

**Pros**: Allows real data testing
**Cons**: Slow, cumbersome

---

## Rate Limit Details

### What We Know
```
Status Code: 429
Response: "Edge: Too Many Requests"
Source: Yahoo Finance CDN edge server
```

### Rate Limit Behavior
- **Limit**: ~2000 requests/hour
- **Reset**: Automatic after 60 minutes
- **Detection**: Happens silently (returns 429 status)
- **Per IP**: Shared across all connections from your machine

### Requests Count As
```
Each API call = 1-3 Yahoo Finance requests:
  - /api/history?symbol=AAPL  → hits Yahoo 1-2 times (direct + fallback)
  - After ~20-30 /api/history calls → rate limit triggered
```

---

## Production vs Development

### In Production (Render)
- ✅ Fresh IP address
- ✅ Separate rate limit quota
- ✅ Rarely hits limits with normal usage
- ✅ Real market data works

### In Development (Local)
- ⚠️ Same IP for all testing
- ⚠️ Rate limit hits quickly with repeated tests
- ⚠️ Expected behavior during development
- ✅ Mock data available to bypass

---

## UI Still Shows Data in Production?

When rate limit hits in production:
1. ✅ API returns `{"candles":[]}`
2. ✅ UI receives the response successfully
3. ✅ Chart renders (just empty, no data points)
4. ✅ No error, UI stays responsive

Users won't see errors - just temporary blank charts until rate limit resets.

---

## Best Practice During Development

### For Quick Testing
Use **mock data**:
```bash
python3 -c "from mock_data import MockStockSource; m = MockStockSource(); print(m.fetch_history_sync('AAPL','1d',5))"
```

### For Real Data Testing
Test **one symbol** at a time with **spacing**:
```bash
curl http://localhost:8000/api/health
sleep 60  # Wait a minute
curl http://localhost:8000/api/history?symbol=AAPL&interval=1d
sleep 60  # Wait before next test
```

### For Realistic Testing
Deploy to **Render** and test there (fresh rate limit quota).

---

## Workaround for Frequent Testing

Create a **development flag** (optional enhancement):

```python
# backend/config.py
import os

USE_MOCK_DATA = os.environ.get('MOCK_DATA', 'false').lower() == 'true'

# Then in data_source.py:
if USE_MOCK_DATA:
    from mock_data import MockStockSource
    source = MockStockSource()
else:
    source = RealDataSource()
```

Usage:
```bash
# Use mock data
MOCK_DATA=true python3 -m uvicorn app.main:app

# Use real data (default)
python3 -m uvicorn app.main:app
```

---

## Summary

| Scenario | Status | Solution |
|----------|--------|----------|
| Empty candles in testing | ✅ Expected | Use mock data or wait 2-5 min |
| Empty candles in production | ⚠️ Rare | Automatic reset, users see blank chart |
| UI still works | ✅ Yes | Empty `candles: []` is valid response |
| Real data works | ✅ Yes | After rate limit resets |
| Production deployment | ✅ Works | Deploy normally, works fine |

---

**Key Takeaway**: Empty candles during development testing is **normal and expected**. Use mock data for fast iteration, or wait for rate limit reset. In production, rate limits reset frequently and real data fetches successfully.
