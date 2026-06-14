# Quick Testing & Deployment Guide

## Problem Summary
UI was not displaying Indian and US stock data, even though the backend API was configured to serve them.

**Root Causes Fixed**:
1. Frontend type system didn't include `us_stock` asset class
2. Symbol label lookup (chart-pane) only searched crypto + indian_stock
3. Error fallback was incomplete (missing us_stock)
4. UI header didn't mention US stocks

---

## Quick Start (Development)

### 1️⃣ Start Backend API
```bash
cd backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload
# Server running on http://localhost:8000
```

### 2️⃣ Verify API is Serving All Symbols
```bash
# In another terminal
curl http://localhost:8000/api/symbols | python3 -m json.tool

# Expected: Three keys with arrays
{
  "crypto": [...8 symbols...],
  "indian_stock": [...8 symbols...],
  "us_stock": [...13 symbols...]
}
```

### 3️⃣ Build & Start Frontend
```bash
cd frontend
npm install  # if needed
npm start    # starts dev server on http://localhost:4200
```

### 4️⃣ Open UI
```bash
# Open in browser
http://localhost:4200
```

### 5️⃣ Verify US Stocks Appear
- ✅ Header should say "Crypto · Indian Equities · US Stocks"
- ✅ Symbol dropdowns should include AAPL, MSFT, GOOGL, etc.
- ✅ Selecting US stock should show friendly name (e.g., "Apple" for AAPL)

---

## Production Deployment

### Option 1: Render.com (Current Setup)
```bash
# Changes are automatically deployed when pushed to main
git add -A
git commit -m "Fix: Add US stocks support to UI"
git push origin main

# Render will:
# 1. Build backend (Python 3.13.3 with requirements.txt)
# 2. Build frontend (npm install + npm run build)
# 3. Start server (uvicorn + FastAPI)
```

**Verify Deployment**:
```bash
# Replace with your Render domain
curl https://live-trading-dashboard.onrender.com/api/symbols | jq '.us_stock | length'
# Should output: 13
```

### Option 2: Local Production Test
```bash
# Build frontend for production
cd frontend
npm run build

# The backend serves the built frontend
cd ../backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Access on http://localhost:8000
```

---

## Testing Checklist

### API Testing
```bash
# 1. Check health
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}

# 2. Check symbols are grouped correctly
curl http://localhost:8000/api/symbols | jq '.us_stock | map(.symbol)'
# Expected: ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ", "^GSPC", "^IXIC", "^DJI"]

# 3. Check history endpoint (may be empty in sandbox, works in production)
curl "http://localhost:8000/api/history?symbol=AAPL&interval=1d"
# Expected: {"symbol":"AAPL","interval":"1d","candles":[...]}

# NOTE: If you get {"candles":[]} - Yahoo Finance is rate limiting (429 error)
# This is normal during testing. Wait 2-5 minutes and retry, or use mock data (see below)
```

### Mock Data for Testing (No Rate Limits)
If real data hits rate limits, use mock data for development:
```bash
cd backend

# Test with mock data
python3 << 'EOF'
from mock_data import MockStockSource

mock = MockStockSource()
candles = mock.fetch_history_sync('AAPL', '1d', limit=10)
print(f"Mock data: {len(candles)} candles for AAPL")
for candle in candles[-3:]:
    print(f"  {candle}")
EOF
```
```

### Frontend Testing
```bash
# 1. Open browser DevTools (F12)
# 2. Go to Network tab
# 3. Refresh page
# 4. Verify API calls:
#    - GET /api/symbols → 200 status
#    - Response includes us_stock array

# 5. Go to Console tab
# 6. Look for any JavaScript errors

# 7. In Application, check Symbol dropdowns show US stocks
```

### Data Fetching Test (Advanced)
```bash
cd backend
python3 debug_data_fetch.py

# Output will show:
# ✓ Symbol resolution working
# ✓ Direct API status (may fail in sandbox)
# ✓ Fallback yfinance status
# ✓ Network diagnostics
```

---

## If US Stocks Still Don't Appear

### Issue: Empty Candles Array `{"candles":[]}`

**Cause**: Yahoo Finance rate limiting (429 error)

**Why this happens**: Testing repeatedly or running multiple requests triggers rate limiting. This is **normal and expected** during development.

**Solutions**:

**Option 1: Wait for Rate Limit Reset** (2-5 minutes)
```bash
# Just wait and retry
sleep 180
curl "http://localhost:8000/api/history?symbol=AAPL&interval=1d"
```

**Option 2: Use Mock Data** (Instant, No Rate Limits)
```bash
cd backend

# Create mock data provider
python3 << 'EOF'
from mock_data import MockStockSource

mock = MockStockSource()
candles = mock.fetch_history_sync('AAPL', '1d', limit=20)
print(f"✅ Generated {len(candles)} candles (no rate limit!)")
EOF
```

**Option 3: Test in Production** (Where Rate Limits Reset Faster)
Deploy to Render and test there - the rate limit should reset within minutes.

---

### Step 1: Check API is Running
```bash
curl http://localhost:8000/api/health
# If fails: Backend is not running, start it
```

### Step 2: Check API Returns US Stocks
```bash
curl http://localhost:8000/api/symbols | python3 -m json.tool | head -100
# If us_stock key is missing: Backend code not updated correctly
```

### Step 3: Check Frontend is Calling API
```bash
# Open DevTools Network tab, refresh page
# Look for GET request to /api/symbols
# If not present: Frontend not running or misconfigured
```

### Step 4: Check Frontend Built Correctly
```bash
cd frontend
npm run build
# Check for compilation errors
```

### Step 5: Check Browser Console
```bash
# Open DevTools Console tab
# Look for JavaScript errors
# Check for API response parsing errors
```

### Step 6: Clear Browser Cache
```bash
# Hard refresh (Ctrl+Shift+R on Windows/Linux, Cmd+Shift+R on Mac)
# Or clear cache in DevTools Settings
```

---

## File Locations

### Key Files Modified
```
frontend/src/app/models/market.ts
  └─ AssetClass type, SymbolGroups interface

frontend/src/app/components/dashboard/dashboard.ts
  └─ Error fallback handler

frontend/src/app/components/dashboard/dashboard.html
  └─ Header text

frontend/src/app/components/chart-pane/chart-pane.ts
  └─ Symbol label computation

backend/app/models.py
  └─ AssetClass enum (US_STOCK value)

backend/app/data_source.py
  └─ USStockSource class, registry update
```

### Documentation
```
docs/13-us-stocks-ui-fix.md
  └─ Complete technical documentation

docs/12-yahoo-finance-api-fix.md
  └─ Backend data fetching explanation

backend/debug_data_fetch.py
  └─ Diagnostic script
```

---

## Environment Variables (If Needed)

```bash
# Frontend (usually auto-detected)
export API_BASE_URL=http://localhost:8000

# Backend (if not using default port)
export PORT=8000
export HOST=0.0.0.0
```

---

## Rollback (If Issues)

If you need to revert the changes:
```bash
git log --oneline | head -5
# Find the commit before these changes

git revert <commit-hash>
git push origin main
```

---

## Success Indicators

After deployment, verify:
1. ✅ Header mentions "US Stocks"
2. ✅ Symbol dropdown includes AAPL, MSFT, GOOGL, etc.
3. ✅ Selecting US stock shows friendly name
4. ✅ Browser Network tab shows /api/symbols with us_stock data
5. ✅ No JavaScript errors in Console
6. ✅ API returns data for /api/history endpoint

---

**Last Updated**: 2025
**Status**: Ready to Deploy ✅
