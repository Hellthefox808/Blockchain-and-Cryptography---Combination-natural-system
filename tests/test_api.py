"""Integration tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "chain_length" in data
    assert "difficulty" in data
    assert "is_valid" in data


def test_avalanche_endpoint():
    res = client.post(
        "/api/crypto/avalanche",
        json={"input1": "Blockchain at myfort", "input2": "Blockchain at Myfort"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_bits"] == 256
    assert data["differing_bits"] > 80
    assert 40.0 <= data["percentage_divergence"] <= 60.0


def test_wallet_creation_and_balance():
    res = client.post("/api/wallet/create")
    assert res.status_code == 200
    wallet = res.json()
    assert wallet["address"].startswith("0x")
    assert "BEGIN PUBLIC KEY" in wallet["public_key_pem"]
    assert "BEGIN PRIVATE KEY" in wallet["private_key_pem"]

    bal_res = client.get(f"/api/wallet/{wallet['address']}/balance")
    assert bal_res.status_code == 200
    assert bal_res.json()["balance"] == 0.0


def test_mining_and_transaction_flow():
    # 1. Reset chain to clean state
    client.post("/api/reset")

    # 2. Create wallets
    sender_wallet = client.post("/api/wallet/create").json()
    recipient_wallet = client.post("/api/wallet/create").json()

    # 3. Mine a block to award sender tokens
    mine_res = client.post("/api/mine", json={"miner_address": sender_wallet["address"]})
    assert mine_res.status_code == 200

    sender_bal = client.get(f"/api/wallet/{sender_wallet['address']}/balance").json()["balance"]
    assert sender_bal == 25.0

    # 4. Submit transaction with automatic signing helper
    tx_res = client.post(
        "/api/transaction/new",
        json={
            "sender": sender_wallet["address"],
            "recipient": recipient_wallet["address"],
            "amount": 10.0,
            "fee": 0.5,
            "private_key": sender_wallet["private_key_pem"],
        },
    )
    assert tx_res.status_code == 200
    assert tx_res.json()["amount"] == 10.0

    # 5. Check pending mempool
    pending_res = client.get("/api/transaction/pending")
    assert pending_res.status_code == 200
    assert len(pending_res.json()) == 1

    # 6. Mine pending transactions
    client.post("/api/mine", json={"miner_address": sender_wallet["address"]})

    # 7. Check recipient received funds
    recip_bal = client.get(f"/api/wallet/{recipient_wallet['address']}/balance").json()["balance"]
    assert recip_bal == 10.0

    # 8. Check chain validity
    val_res = client.get("/api/validate")
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True


def test_tamper_and_reset():
    # Reset and ensure at least 2 blocks exist
    client.post("/api/reset")
    client.post("/api/mine", json={"miner_address": "0xMinerNode0000000000000000000000000000000"})

    # Tamper Block 1
    tamper_res = client.post("/api/tamper", json={"block_index": 1, "new_amount": 77777.0})
    assert tamper_res.status_code == 200

    val_res = client.get("/api/validate")
    assert val_res.json()["is_valid"] is False
    assert val_res.json()["broken_block_index"] == 1

    # Reset
    reset_res = client.post("/api/reset")
    assert reset_res.status_code == 200
    assert client.get("/api/validate").json()["is_valid"] is True
