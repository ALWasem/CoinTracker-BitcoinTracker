# CoinTracker — Bitcoin Tracker (Prototype)

A small app that lets you:
- Add/remove Bitcoin addresses
- Sync balances and recent transactions from a public API
- See balances and transactions in a simple web page

Defaults to SQLite, so it runs locally without installing a database.

Quick Start
- Install requirements:
  - If you see an “externally-managed-environment” error, use a virtual environment.
  - macOS/Linux:
    - `python3 -m venv .venv && source .venv/bin/activate`
    - `python3 -m pip install -r requirements.txt`
  - Windows (PowerShell):
    - `python -m venv .venv; .\.venv\Scripts\Activate.ps1`
    - `python -m pip install -r requirements.txt`
- Run the app: `python3 Backend/app.py`
- Open your browser: `http://127.0.0.1:5000/`

Use The App
- Enter a Bitcoin address and click Add.
- Click Sync to pull balance and recent transactions.
- Click View Transaction to see the latest transactions for that address.
- Remove deletes the address and its saved transactions.

Try the API (optional)
- Add: `curl -X POST http://127.0.0.1:5000/addresses -H 'Content-Type: application/json' -d '{"address":"3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd"}'`
- List: `curl http://127.0.0.1:5000/addresses`
- Sync: `curl -X POST http://127.0.0.1:5000/sync/3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd`
- Transactions: `curl http://127.0.0.1:5000/transactions/3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd`
- Remove: `curl -X DELETE http://127.0.0.1:5000/addresses/3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd`

Troubleshooting
- If installs fail, make sure your virtualenv is active (your prompt should show `.venv`).
- If the page looks unstyled, hard refresh (Cmd/Ctrl+Shift+R). The CSS and JS are served at `/static/...`.
- Data is stored in `Backend/cointracker.db` (created automatically).

Testing
- Make sure dependencies are installed (ideally in a virtualenv):
  - `python3 -m pip install -r requirements.txt`
- Run the tests from the repo root:
  - `python3 -m unittest discover -s tests -p "test_*.py" -q`
- If you see “Ran 0 tests”, ensure you are in the project root and used the exact command above.
- Tests use an in‑memory SQLite database and do not call external APIs.

Architecture (What’s inside)
- Backend (Flask)
  - Files: `Backend/app.py` (bootstrap), `Backend/routes.py` (endpoints), `Backend/models.py` (tables), `Backend/services/blockchain_api.py` (blockchain client), `Backend/extensions.py` (shared db object).
  - Storage: SQLite via SQLAlchemy. One table for `addresses`, one for `transactions` (linked to an address). Deleting an address removes its transactions.
- Frontend (React, minimal)
  - Files: `Frontend/index.html` (served at `/`), `Frontend/app.jsx` (logic/UI), `Frontend/styles.css` (a few styles). Uses Tailwind via CDN for utility classes.
- Tests
  - File: `tests/test_api_unittest.py`. Uses an in-memory SQLite DB. Run with `python3 -m unittest -q`.

System Design Decisions
- Database: SQLite by default to make setup trivial. Postgres is supported via `DATABASE_URL` if you want to point to a server later.
- Sync provider: Uses Blockstream’s public API by default (no key required). If `BLOCKCHAIR_API_KEY` is set, tries Blockchair first and automatically falls back to Blockstream on rate‑limit/errors.
- Transaction amounts: Computed from Blockstream per transaction by netting outputs to the address minus inputs from the address. Amounts are returned as 8‑decimal strings (BTC) to preserve display precision.
- Sync model: Clicking Sync for an address fetches its latest balance and the most recent 25 transactions from the provider. For each transaction, the app computes the net amount (incoming/outgoing) for that address and saves it. Existing transactions are updated; new ones are inserted. There are no background jobs or continuous polling in this prototype.
- API schema: A small set of simple endpoints. An OpenAPI stub lives at `Backend/openapi.yaml` (ignored by Git) for reference.

Assumptions
- Local, single‑user demo running on your machine (no auth or multi‑user state).
- You provide valid Bitcoin addresses; server‑side validation is minimal.
- Showing recent history (last 25 transactions) is enough for the demo (no full archival sync).
- Public network access is available to reach Blockstream/Blockchair; if both fail, sync returns an error.
- Display precision is 8 decimals (BTC). For a prototype, float storage is acceptable; production would use integer satoshis or fixed‑precision decimals.
- All timestamps use UTC.
- No fiat conversion; amounts are shown in BTC only.
- SQLite file can be created in `Backend/` (write permission assumed).

Limitations (Prototype scope)
- Only the recent page of transactions is fetched for speed; very large wallets aren’t paged fully.
- Internally, amounts are stored as floats for brevity (sufficient for a demo). A production version would store satoshis as integers or fixed‑precision decimals.
- No auth/rate limiting since this is for local demo use.

Configuration (Optional)
- Use Postgres instead of SQLite:
  - macOS/Linux: `DATABASE_URL=postgresql://user:pass@localhost/db python3 Backend/app.py`
  - Windows (PowerShell): `$env:DATABASE_URL='postgresql://user:pass@localhost/db'; python3 Backend/app.py`
- Use a Blockchair API key: set `BLOCKCHAIR_API_KEY` or `BLOCKCHAIN_API_KEY` in your environment.
