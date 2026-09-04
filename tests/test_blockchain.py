"""Unit tests for Blockchain ledger, Proof of Work mining, and tamper detection."""

import os
import tempfile
from src.core.blockchain import Blockchain
from src.core.crypto import (
    export_private_key_pem,
    export_public_key_pem,
    generate_keypair,
    get_address_from_public_key,
)
from src.core.transaction import Transaction


def test_genesis_block():
    bc = Blockchain(difficulty=2)
    assert len(bc.chain) == 1
    genesis = bc.chain[0]
    assert genesis.index == 0
    assert genesis.previous_hash == "0" * 64
    assert genesis.hash.startswith("00")
    assert bc.is_chain_valid()[0] is True


def test_mining_and_balance():
    bc = Blockchain(difficulty=2, mining_reward=50.0)
    miner_addr = "0xMiner111111111111111111111111111111111111"

    # Mine 2 blocks
    bc.mine_pending_transactions(miner_addr)
    bc.mine_pending_transactions(miner_addr)

    assert len(bc.chain) == 3
    assert bc.get_balance(miner_addr) == 100.0
    assert bc.is_chain_valid()[0] is True


def test_transaction_and_transfer():
    bc = Blockchain(difficulty=2, mining_reward=100.0)
    priv_a, pub_a = generate_keypair()
    addr_a = get_address_from_public_key(pub_a)
    pem_priv_a = export_private_key_pem(priv_a)
    pem_pub_a = export_public_key_pem(pub_a)

    priv_b, pub_b = generate_keypair()
    addr_b = get_address_from_public_key(pub_b)

    # Fund account A via mining
    bc.mine_pending_transactions(addr_a)
    assert bc.get_balance(addr_a) == 100.0

    # A sends 40 to B
    tx = Transaction(
        sender=addr_a,
        recipient=addr_b,
        amount=40.0,
        fee=2.0,
        sender_public_key=pem_pub_a,
    )
    tx.sign(pem_priv_a)

    success, msg = bc.add_transaction(tx)
    assert success is True
    # Available balance should reflect pending deduction
    assert bc.get_balance(addr_a) == 58.0

    # Mine block to confirm transaction
    miner_addr = "0xMinerNode0000000000000000000000000000000"
    bc.mine_pending_transactions(miner_addr)

    assert bc.get_balance(addr_a) == 58.0
    assert bc.get_balance(addr_b) == 40.0
    assert bc.is_chain_valid()[0] is True


def test_insufficient_balance_rejected():
    bc = Blockchain(difficulty=2)
    priv, pub = generate_keypair()
    addr = get_address_from_public_key(pub)
    pem_priv = export_private_key_pem(priv)
    pem_pub = export_public_key_pem(pub)

    # Empty balance attempting to send 10 tokens
    tx = Transaction(
        sender=addr,
        recipient="0xRecipient000000000000000000000000000000",
        amount=10.0,
        sender_public_key=pem_pub,
    )
    tx.sign(pem_priv)

    success, msg = bc.add_transaction(tx)
    assert success is False
    assert "Insufficient funds" in msg


def test_tamper_detection_pinpoints_corrupted_block():
    bc = Blockchain(difficulty=2, mining_reward=25.0)
    miner_addr = "0xMinerNode0000000000000000000000000000000"

    bc.mine_pending_transactions(miner_addr)
    bc.mine_pending_transactions(miner_addr)
    assert bc.is_chain_valid()[0] is True

    # Tamper with Block 1
    success, _ = bc.tamper_block(1, 888888.0)
    assert success is True

    is_valid, msg, broken_idx = bc.is_chain_valid()
    assert is_valid is False
    assert broken_idx == 1


def test_blockchain_persistence():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        bc1 = Blockchain(difficulty=2, mining_reward=50.0, storage_path=tmp_path)
        miner = "0xMiner111111111111111111111111111111111111"
        bc1.mine_pending_transactions(miner)
        bc1.save_to_disk(tmp_path)

        # Reload in new instance
        bc2 = Blockchain(difficulty=2, storage_path=tmp_path)
        assert len(bc2.chain) == 2
        assert bc2.get_balance(miner) == 50.0
        assert bc2.is_chain_valid()[0] is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
