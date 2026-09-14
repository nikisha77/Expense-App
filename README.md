# Splitzy — Expense Splitter

A small full-stack app to split shared expenses in a group and see who owes
whom. Built as Homework 2 for the AI Dev Tools Zoomcamp: spec → frontend
prototype → FastAPI backend → connect → real database.

See [`_docs/specs.md`](_docs/specs.md) for the full spec.

## Stack
- **Frontend:** Vite + vanilla JS (`frontend/`)
- **Backend:** FastAPI + SQLAlchemy + SQLite, managed with `uv` (`backend/`)

## Running locally

### Backend
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```
API is served at `http://localhost:8000` (docs at `/docs`).

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App is served at `http://localhost:5173` and talks to the backend at
`http://localhost:8000`.

### Tests
```bash
cd backend
uv run pytest
```

## Project structure
```
_docs/specs.md      product spec
backend/             FastAPI app, SQLAlchemy models, tests
frontend/            Vite vanilla-JS single-page app
```
