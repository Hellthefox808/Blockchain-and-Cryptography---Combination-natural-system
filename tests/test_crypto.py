"""Unit tests for cryptographic primitives."""

from src.core.crypto import (
    calculate_avalanche_effect,
    export_private_key_pem,
    export_public_key_pem,
    generate_keypair,
    get_address_from_public_key,
    load_private_key,
    load_public_key,
    sha256_binary,
    sha256_hex,
    sign_data,
    verify_signature,
)


def test_sha256_hex_determinism():
    data = "Blockchain and Cryptography"
    hash1 = sha256_hex(data)
    hash2 = sha256_hex(data)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_sha256_binary():
    data = "test binary hash"
    bin_str = sha256_binary(data)
    assert len(bin_str) == 256
    assert set(bin_str).issubset({"0", "1"})


def test_avalanche_effect():
    # Identical strings from synopsis
    res = calculate_avalanche_effect("Blockchain at myfort", "Blockchain at Myfort")
    assert res["total_bits"] == 256
    assert res["differing_bits"] > 90
    assert 40.0 <= res["percentage_divergence"] <= 60.0
    assert res["is_avalanche_ideal"] is True


def test_ecdsa_keypair_serialization():
    priv, pub = generate_keypair()
    priv_pem = export_private_key_pem(priv)
    pub_pem = export_public_key_pem(pub)

    assert "BEGIN PRIVATE KEY" in priv_pem
    assert "BEGIN PUBLIC KEY" in pub_pem

    # Reload keys from PEM
    reloaded_priv = load_private_key(priv_pem)
    reloaded_pub = load_public_key(pub_pem)
    assert reloaded_priv is not None
    assert reloaded_pub is not None


def test_address_derivation():
    _, pub = generate_keypair()
    addr = get_address_from_public_key(pub)
    assert addr.startswith("0x")
    assert len(addr) == 42


def test_digital_signature_verification():
    priv, pub = generate_keypair()
    priv_pem = export_private_key_pem(priv)
    pub_pem = export_public_key_pem(pub)

    message = "Transfer 25 tokens from Vinny to Kinny"
    signature = sign_data(priv_pem, message)
    assert len(signature) > 60

    # 1. Valid verification
    assert verify_signature(pub_pem, signature, message) is True

    # 2. Tampered message detection
    assert verify_signature(pub_pem, signature, "Transfer 250 tokens from Vinny to Kinny") is False

    # 3. Wrong key detection
    _, wrong_pub = generate_keypair()
    wrong_pub_pem = export_public_key_pem(wrong_pub)
    assert verify_signature(wrong_pub_pem, signature, message) is False
