from extensions import db
from datetime import datetime

class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    last_synced = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship(
        "Transaction",
        backref="address",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    address_id = db.Column(
        db.Integer,
        db.ForeignKey("addresses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tx_hash = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    tx_type = db.Column(db.String(10))  # "incoming" or "outgoing"
