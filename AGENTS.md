# Agent instructions for this repo

- Spec lives at `_docs/specs.md`. Treat it as the source of truth; update it
  if the app's behavior intentionally changes.
- Backend: Python + FastAPI + SQLAlchemy, dependency management via `uv`
  (never `pip install` directly — use `uv add`). Keep DB access abstracted
  behind SQLAlchemy so the storage engine can change without touching route
  handlers.
- Frontend: plain JS + Vite, no framework. All HTTP calls to the backend must
  go through `frontend/src/api.js` — never call `fetch` directly from UI code.
- Write/update pytest tests in `backend/tests/` alongside any endpoint change;
  run `uv run pytest` before considering a backend change done.
- Keep commits small and scoped to one step of the workflow (spec, frontend
  prototype, backend, wiring, DB swap).
