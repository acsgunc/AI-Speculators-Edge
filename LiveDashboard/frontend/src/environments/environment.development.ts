/**
 * Development environment.
 *
 * The Angular dev server (http://localhost:4200) talks to the FastAPI backend
 * running separately on http://localhost:8000.
 */
export const environment = {
  production: false,
  apiBase: 'http://localhost:8000',
  wsBase: 'ws://localhost:8000',
};
