# CoinTracker — Bitcoin Tracker (Prototype)

A minimal Flask backend that lets you:
- Add/remove Bitcoin addresses
- Sync an address' balance and transactions from a public API
- Retrieve balances and transactions per address

The app defaults to SQLite for easy local setup and supports Postgres via `DATABASE_URL`.

## Quickstart

Prereqs: Python 3.9+ recommended.

1) Install deps
```
python3 -m pip install -r requirements.txt
```

2) Run the API (SQLite by default)
```
python3 Backend/app.py
```
Server starts on http://127.0.0.1:5000

3) Try the endpoints

Add address
```
curl -X POST http://127.0.0.1:5000/addresses \
  -H 'Content-Type: application/json' \
  -d '{"address": "3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd"}'
```

List addresses
```
curl http://127.0.0.1:5000/addresses
```

Sync an address (fetches from Blockchair)
```
curl -X POST http://127.0.0.1:5000/sync/3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd
```

Get transactions
```
curl http://127.0.0.1:5000/transactions/3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd
```

Remove address
```
curl -X DELETE http://127.0.0.1:5000/addresses/3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd
```

## Configuration

- Database: Defaults to SQLite at `Backend/cointracker.db`.
  - Override via `DATABASE_URL` (e.g., Postgres):
    - macOS/Linux: `DATABASE_URL=postgresql://user:pass@localhost/db python3 Backend/app.py`
    - Windows (PowerShell): `$env:DATABASE_URL='postgresql://user:pass@localhost/db'; python3 Backend/app.py`

- Blockchain API provider:
  - The app uses Blockstream's public API by default to avoid rate limits without a key.
  - If you have a Blockchair API key, set `BLOCKCHAIR_API_KEY` (or `BLOCKCHAIN_API_KEY`) to use Blockchair.
  - On Blockchair rate-limit errors (429/430), the app falls back to Blockstream automatically.

## API Notes

- Endpoints are defined in `Backend/routes.py`.
- Data models are in `Backend/models.py` (tables: `addresses`, `transactions`).
- Sync logic uses `Backend/services/blockchain_api.py` (Blockchair). For simplicity:
  - Transaction amounts are placeholders (0.0) and type is simplified.
  - Consider enhancing to fetch per-tx details and direction.

An OpenAPI spec is provided at `Backend/openapi.yaml` (basic schema of current endpoints).

## Assumptions & Decisions

- SQLite default to minimize setup friction; swap to Postgres with `DATABASE_URL`.
- Simplified sync: one-shot HTTP call; no background jobs.
- Minimal error handling around external API; recommended follow-ups below.

## Recommended Improvements (Next Iterations)

- Harden external API client (timeouts, retries, rate limits, pagination, amount/direction logic).
- Background sync job + last block height checkpointing.
- AuthN/AuthZ if exposed beyond localhost.
- OpenAPI-first development and auto-generated client.
- Simple web UI or Postman collection for demoing.
