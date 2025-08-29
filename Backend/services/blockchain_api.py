import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests

# Providers
BLOCKCHAIR_BASE = "https://api.blockchair.com/bitcoin/dashboards/address/"
BLOCKSTREAM_BASE = "https://blockstream.info/api"


@dataclass
class BlockchainAPIError(Exception):
    message: str
    status_code: Optional[int] = None

    def __str__(self) -> str:
        if self.status_code:
            return f"{self.message} (status={self.status_code})"
        return self.message


def _fetch_from_blockchair(address: str) -> Dict[str, Any]:
    key = os.getenv("BLOCKCHAIR_API_KEY") or os.getenv("BLOCKCHAIN_API_KEY")
    url = f"{BLOCKCHAIR_BASE}{address}"
    params = {"limit": 100}
    if key:
        params["key"] = key

    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        raise BlockchainAPIError(f"network error: {e}") from e

    if not resp.ok:
        # 429/430 indicate rate limiting/blacklisting without a key
        raise BlockchainAPIError(
            f"blockchair error: {resp.text[:200]}", status_code=resp.status_code
        )

    try:
        payload = resp.json()
        data = payload["data"][address]
        balance_sats = data["address"].get("balance", 0)
        tx_hashes: List[str] = data.get("transactions", [])
    except Exception as e:  # noqa: BLE001 keep simple
        raise BlockchainAPIError("unexpected response from Blockchair") from e

    balance = (balance_sats or 0) / 1e8
    transactions = [
        {
            "tx_hash": h,
            "amount": 0.0,
            "timestamp": datetime.utcnow(),
            "type": "incoming",
        }
        for h in tx_hashes
    ]
    return {"balance": balance, "transactions": transactions}


def _fetch_from_blockstream(address: str) -> Dict[str, Any]:
    # Address info (balance)
    try:
        info = requests.get(f"{BLOCKSTREAM_BASE}/address/{address}", timeout=10)
    except requests.RequestException as e:
        raise BlockchainAPIError(f"network error: {e}") from e
    if not info.ok:
        raise BlockchainAPIError(
            f"blockstream error: {info.text[:200]}", status_code=info.status_code
        )
    try:
        j = info.json()
        chain = j.get("chain_stats", {})
        mempool = j.get("mempool_stats", {})
        funded = (chain.get("funded_txo_sum", 0) or 0) + (mempool.get("funded_txo_sum", 0) or 0)
        spent = (chain.get("spent_txo_sum", 0) or 0) + (mempool.get("spent_txo_sum", 0) or 0)
        balance_sats = funded - spent
    except Exception as e:
        raise BlockchainAPIError("unexpected response from Blockstream (info)") from e

    # Recent transactions (first page, up to 25)
    try:
        txs_resp = requests.get(f"{BLOCKSTREAM_BASE}/address/{address}/txs", timeout=10)
    except requests.RequestException as e:
        raise BlockchainAPIError(f"network error: {e}") from e
    if not txs_resp.ok:
        raise BlockchainAPIError(
            f"blockstream error: {txs_resp.text[:200]}", status_code=txs_resp.status_code
        )
    try:
        txs_json = txs_resp.json()
        transactions = []
        for tx in txs_json:
            txid = tx.get("txid")
            if not txid:
                continue

            # Compute net amount relative to this address in satoshis
            received_sats = sum(
                (vout.get("value") or 0)
                for vout in (tx.get("vout") or [])
                if vout.get("scriptpubkey_address") == address
            )
            spent_sats = 0
            for vin in (tx.get("vin") or []):
                prev = vin.get("prevout") or {}
                if prev.get("scriptpubkey_address") == address:
                    spent_sats += prev.get("value") or 0

            net_sats = (received_sats or 0) - (spent_sats or 0)
            direction = "incoming" if net_sats >= 0 else "outgoing"
            amount_btc = abs(net_sats) / 1e8

            block_time = (tx.get("status") or {}).get("block_time")
            ts = datetime.utcfromtimestamp(block_time) if block_time else datetime.utcnow()

            transactions.append(
                {
                    "tx_hash": txid,
                    "amount": amount_btc,
                    "timestamp": ts,
                    "type": direction,
                }
            )
    except Exception as e:
        raise BlockchainAPIError("unexpected response from Blockstream (txs)") from e

    return {"balance": (balance_sats or 0) / 1e8, "transactions": transactions}


def fetch_wallet_data(address: str) -> Dict[str, Any]:
    """Fetch wallet data using Blockchair when possible; fallback to Blockstream.

    - If BLOCKCHAIR_API_KEY is set, try Blockchair first.
    - On rate limiting (429/430) or any Blockchair failure, fallback to Blockstream.
    - If no key is set, use Blockstream directly to avoid blacklisting.
    """
    has_blockchair_key = bool(os.getenv("BLOCKCHAIR_API_KEY") or os.getenv("BLOCKCHAIN_API_KEY"))

    if has_blockchair_key:
        try:
            return _fetch_from_blockchair(address)
        except BlockchainAPIError as e:
            # Fallback on rate limiting or upstream failure
            if e.status_code in (429, 430) or e.status_code is None:
                return _fetch_from_blockstream(address)
            # For other HTTP errors, still attempt fallback as a best effort
            return _fetch_from_blockstream(address)
    else:
        # No key: prefer Blockstream to avoid Blockchair blacklisting
        return _fetch_from_blockstream(address)
