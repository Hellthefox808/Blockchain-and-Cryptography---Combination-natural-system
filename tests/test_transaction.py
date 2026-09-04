"""Unit tests for transaction logic and cryptographic signing."""

from src.core.crypto import (
    export_private_key_pem,
    export_public_key_pem,
    generate_keypair,
    get_address_from_public_key,
)
from src.core.transaction import Transaction


def test_coinbase_transaction():
    tx = Transaction(
        sender="SYSTEM",
        recipient="0x1234567890123456789012345678901234567890",
        amount=50.0,
    )
    assert tx.is_coinbase() is True
    assert tx.is_valid() is True


def test_valid_signed_transaction():
    priv, pub = generate_keypair()
    priv_pem = export_private_key_pem(priv)
    pub_pem = export_public_key_pem(pub)
    sender_addr = get_address_from_public_key(pub)
    recipient_addr = "0x2222222222222222222222222222222222222222"

    tx = Transaction(
        sender=sender_addr,
        recipient=recipient_addr,
        amount=15.0,
        fee=0.5,
        sender_public_key=pub_pem,
    )
    tx.sign(priv_pem)

    assert tx.is_valid() is True
    assert tx.signature is not None


def test_invalid_amount():
    tx = Transaction(
        sender="0x1111111111111111111111111111111111111111",
        recipient="0x2222222222222222222222222222222222222222",
        amount=-5.0,
    )
    assert tx.is_valid() is False


def test_tampered_transaction():
    priv, pub = generate_keypair()
    priv_pem = export_private_key_pem(priv)
    pub_pem = export_public_key_pem(pub)
    sender_addr = get_address_from_public_key(pub)

    tx = Transaction(
        sender=sender_addr,
        recipient="0x2222222222222222222222222222222222222222",
        amount=10.0,
        sender_public_key=pub_pem,
    )
    tx.sign(priv_pem)
    assert tx.is_valid() is True

    # Tamper with recipient
    tx.recipient = "0xAttackerAddress00000000000000000000000000"
    assert tx.is_valid() is False


def test_transaction_dict_roundtrip():
    priv, pub = generate_keypair()
    priv_pem = export_private_key_pem(priv)
    pub_pem = export_public_key_pem(pub)
    sender_addr = get_address_from_public_key(pub)

    tx = Transaction(
        sender=sender_addr,
        recipient="0x3333333333333333333333333333333333333333",
        amount=42.0,
        fee=1.0,
        sender_public_key=pub_pem,
    )
    tx.sign(priv_pem)

    d = tx.to_dict()
    reconstructed = Transaction.from_dict(d)
    assert reconstructed.tx_id == tx.tx_id
    assert reconstructed.amount == tx.amount
    assert reconstructed.signature == tx.signature
    assert reconstructed.is_valid() is True
