import requests
from datetime import datetime

# Example with Blockchair API
BASE_URL = "https://api.blockchair.com/bitcoin/dashboards/address/"

def fetch_wallet_data(address: str):
    url = f"{BASE_URL}{address}"
    resp = requests.get(url)
    data = resp.json()["data"][address]

    balance = data["address"]["balance"] / 1e8  # Satoshi to BTC
    transactions = []

    for tx_hash in data["transactions"]:
        transactions.append({
            "tx_hash": tx_hash,
            "amount": 0.0,  # Placeholder, would fetch detailed tx info
            "timestamp": datetime.utcnow(),
            "type": "incoming"  # Simplified
        })

    return {
        "balance": balance,
        "transactions": transactions
    }
