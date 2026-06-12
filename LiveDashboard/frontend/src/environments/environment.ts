/**
 * Production environment.
 *
 * Empty bases mean "same origin": when the FastAPI backend serves the compiled
 * Angular bundle as a single unified service, the API and WebSocket live on the
 * same host, so relative resolution is used at runtime.
 */
export const environment = {
  production: true,
  /** HTTP API base URL. Empty => same origin as the served SPA. */
  apiBase: '',
  /** WebSocket base URL. Empty => derived from window.location at runtime. */
  wsBase: '',
};
