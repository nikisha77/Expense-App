# Splitzy — Expense Splitter Spec

## 1. Overview
Splitzy lets a group of people (roommates, trip friends, a couple) track shared
expenses and see who owes whom, so nobody has to do the math by hand.

## 2. Core entities
- **Group** — a named collection of people sharing expenses (e.g. "Goa Trip").
- **Member** — a person belonging to a group (just a name, no login/auth for v1).
- **Expense** — an amount paid by one member on behalf of the group, on a date,
  with a description, split among some or all members.
- **Split** — how an expense is divided: **equal** (default) or **custom amounts**
  per member that must sum to the expense total.

## 3. User flows
1. Create a group, add members by name.
2. Add an expense: description, amount, who paid, who it's split between,
   and how (equal / custom).
3. View a running list of expenses for the group.
4. View **Balances**: net position of every member (+ = owed money, − = owes money).
5. View **Settle up**: a minimal list of "A pays B ₹X" transactions that would
   zero out all balances.
6. Data persists across refreshes and is shared across browsers/tabs (real DB,
   not local-only state).

## 4. Out of scope for v1
- Authentication / user accounts.
- Multi-currency support (single currency, unformatted number).
- Editing/deleting expenses after creation (can be a stretch goal).
- Notifications, receipts/images, recurring expenses.

## 5. Data model (high level)
- `Group(id, name, created_at)`
- `Member(id, group_id, name)`
- `Expense(id, group_id, description, amount, paid_by_member_id, created_at)`
- `ExpenseShare(id, expense_id, member_id, share_amount)` — one row per member
  who owes part of that expense.

## 6. API surface (contract between frontend & backend)
- `POST   /groups` — create group
- `GET    /groups` — list groups
- `GET    /groups/{id}` — group detail (incl. members)
- `POST   /groups/{id}/members` — add member
- `POST   /groups/{id}/expenses` — add expense (with split info)
- `GET    /groups/{id}/expenses` — list expenses
- `GET    /groups/{id}/balances` — net balance per member
- `GET    /groups/{id}/settle-up` — minimal set of settling transactions

## 7. Tech stack
- **Frontend:** Vite + vanilla JS/HTML/CSS (single-page app), all backend calls
  centralized in `src/api.js` so they're easy to mock, then point at the real API.
- **Backend:** Python, FastAPI, `uv` for package management. Mock in-memory
  store first, then swapped for SQLite via SQLAlchemy (kept DB-agnostic).
- **Tests:** pytest, written against the API contract before implementation.

## 8. Name
**Splitzy**
