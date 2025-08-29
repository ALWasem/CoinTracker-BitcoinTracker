import os
import sys
import unittest
from datetime import datetime
from pathlib import Path


class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure Backend/ is importable
        repo_root = Path(__file__).resolve().parents[1]
        backend_dir = repo_root / "Backend"
        sys.path.insert(0, str(backend_dir))

        # Use in-memory SQLite for tests
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

        # Lazy import after env is set
        from app import app as flask_app  # type: ignore
        from extensions import db  # type: ignore

        cls.app = flask_app
        cls.db = db

        with cls.app.app_context():
            cls.db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            cls.db.drop_all()

    def setUp(self):
        self.client = self.app.test_client()
        # Clean tables between tests
        from models import Address, Transaction  # type: ignore
        with self.app.app_context():
            self.db.session.query(Transaction).delete()
            self.db.session.query(Address).delete()
            self.db.session.commit()

    def test_add_and_list_addresses(self):
        # Missing address
        resp = self.client.post("/addresses", json={})
        self.assertEqual(resp.status_code, 400)

        # Add address
        addr = "test_addr_1"
        resp = self.client.post("/addresses", json={"address": addr})
        self.assertEqual(resp.status_code, 201)

        # Duplicate should fail
        resp = self.client.post("/addresses", json={"address": addr})
        self.assertEqual(resp.status_code, 400)

        # List
        resp = self.client.get("/addresses")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["address"], addr)
        self.assertEqual(data[0]["balance"], "0.00000000")

    def test_transactions_format_and_remove(self):
        from models import Address, Transaction  # type: ignore

        with self.app.app_context():
            addr = Address(address="seed_addr")
            self.db.session.add(addr)
            self.db.session.commit()

            tx = Transaction(
                address_id=addr.id,
                tx_hash="seed_tx_hash",
                amount=0.0001,
                timestamp=datetime.utcnow(),
                tx_type="incoming",
            )
            self.db.session.add(tx)
            self.db.session.commit()

        # Verify amount formatting
        resp = self.client.get("/transactions/seed_addr")
        self.assertEqual(resp.status_code, 200)
        txs = resp.get_json()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["tx_hash"], "seed_tx_hash")
        self.assertEqual(txs[0]["amount"], "0.00010000")

        # Remove address and ensure cascade
        resp = self.client.delete("/addresses/seed_addr")
        self.assertEqual(resp.status_code, 200)

        with self.app.app_context():
            self.assertIsNone(Address.query.filter_by(address="seed_addr").first())
            self.assertIsNone(Transaction.query.filter_by(tx_hash="seed_tx_hash").first())

    def test_sync_missing_address(self):
        resp = self.client.post("/sync/not_added_addr")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()

