from flask import Blueprint, request, jsonify
from extensions import db
from models import Address, Transaction
from services.blockchain_api import fetch_wallet_data, BlockchainAPIError
from datetime import datetime

bp = Blueprint("api", __name__)

# Add new BTC address
@bp.route("/addresses", methods=["POST"])
def add_address():
    data = request.get_json()
    address = data.get("address")
    if not address:
        return jsonify({"error": "Address required"}), 400

    if Address.query.filter_by(address=address).first():
        return jsonify({"error": "Address already exists"}), 400

    new_address = Address(address=address)
    db.session.add(new_address)
    db.session.commit()
    return jsonify({"message": "Address added"}), 201


# Remove BTC address
@bp.route("/addresses/<string:address>", methods=["DELETE"])
def remove_address(address):
    addr = Address.query.filter_by(address=address).first()
    if not addr:
        return jsonify({"error": "Address not found"}), 404

    # Remove related transactions first to satisfy FK constraints in SQLite
    Transaction.query.filter_by(address_id=addr.id).delete(synchronize_session=False)
    db.session.delete(addr)
    db.session.commit()
    return jsonify({"message": "Address removed"}), 200


# List all addresses with balances
@bp.route("/addresses", methods=["GET"])
def list_addresses():
    addresses = Address.query.all()
    return jsonify([
        {
            "address": a.address,
            "balance": f"{float(a.balance):.8f}" if a.balance is not None else "0.00000000",
            "last_synced": a.last_synced.isoformat()
        } for a in addresses
    ])


# Sync BTC address
@bp.route("/sync/<string:address>", methods=["POST"])
def sync_address(address):
    addr = Address.query.filter_by(address=address).first()
    if not addr:
        return jsonify({"error": "Address not found"}), 404

    # Fetch from API (with basic error handling)
    try:
        wallet_data = fetch_wallet_data(address)
    except BlockchainAPIError as e:
        return jsonify({"error": f"sync failed: {e}"}), 502

    # Update balance
    addr.balance = wallet_data["balance"]
    addr.last_synced = datetime.utcnow()

    # Upsert transactions efficiently: single query to find existing, then bulk insert new
    incoming_txs = wallet_data["transactions"]
    tx_hashes = [t["tx_hash"] for t in incoming_txs]
    if tx_hashes:
        existing_rows = Transaction.query.filter(Transaction.tx_hash.in_(tx_hashes)).all()
        existing_by_hash = {row.tx_hash: row for row in existing_rows}

        new_objects = []
        for t in incoming_txs:
            found = existing_by_hash.get(t["tx_hash"])
            if found:
                found.amount = t["amount"]
                found.timestamp = t["timestamp"]
                found.tx_type = t["type"]
            else:
                new_objects.append(
                    Transaction(
                        address_id=addr.id,
                        tx_hash=t["tx_hash"],
                        amount=t["amount"],
                        timestamp=t["timestamp"],
                        tx_type=t["type"],
                    )
                )

        if new_objects:
            db.session.bulk_save_objects(new_objects)

    db.session.commit()
    return jsonify({"message": "Address synced"})


# Get transactions for address
@bp.route("/transactions/<string:address>", methods=["GET"])
def get_transactions(address):
    addr = Address.query.filter_by(address=address).first()
    if not addr:
        return jsonify({"error": "Address not found"}), 404

    # Return the 25 most recent transactions (no pagination)
    q = (
        Transaction.query
        .filter_by(address_id=addr.id)
        .order_by(Transaction.timestamp.desc())
        .limit(25)
    )
    txs = q.all()
    return jsonify([
        {
            "tx_hash": tx.tx_hash,
            "amount": f"{float(tx.amount):.8f}",
            "timestamp": tx.timestamp.isoformat(),
            "type": tx.tx_type
        } for tx in txs
    ])
