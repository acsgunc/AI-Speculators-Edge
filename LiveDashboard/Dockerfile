# Multi-stage build: compile the Angular SPA, then serve it from FastAPI as a
# single unified web service. Suitable for Render, Railway, Fly.io and
# Hugging Face Spaces free tiers.

# ---- Stage 1: build the Angular frontend ----
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend + compiled frontend ----
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install backend dependencies first for better layer caching.
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source.
COPY backend/ ./backend/

# Copy the compiled Angular build into the location FastAPI serves from.
COPY --from=frontend /app/frontend/dist/live-dashboard/browser ./frontend/dist/live-dashboard/browser

ENV HOST=0.0.0.0 \
    PORT=8000 \
    RELOAD=0 \
    FRONTEND_DIST=/app/frontend/dist/live-dashboard/browser

EXPOSE 8000
WORKDIR /app/backend

# Cloud platforms inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
