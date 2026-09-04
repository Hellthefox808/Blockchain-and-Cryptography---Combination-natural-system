"""Cryptographic primitives for the Blockchain and Cryptography Combo Nature System.

Provides:
- SHA-256 hashing (hex and binary representations)
- Avalanche effect measurement (Hamming distance and bitwise divergence analysis)
- Asymmetric key generation using ECDSA with curve SECP256k1
- Digital signature generation and verification
- Public key to wallet address derivation
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)


def sha256_hex(data: Union[str, bytes, dict, list]) -> str:
    """Compute standard 256-bit SHA-256 hash returned as 64-character hexadecimal."""
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = str(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_binary(data: Union[str, bytes, dict, list]) -> str:
    """Compute 256-bit SHA-256 hash returned as a 256-character string of 0s and 1s."""
    hex_str = sha256_hex(data)
    # Convert each byte (2 hex chars) to 8-bit binary representation
    return "".join(f"{int(hex_str[i : i + 2], 16):08b}" for i in range(0, len(hex_str), 2))


def calculate_avalanche_effect(input1: str, input2: str) -> dict[str, Any]:
    """Measure the avalanche effect between two input strings under SHA-256.

    Calculates:
    - Hexadecimal hashes of both inputs
    - 256-bit binary streams of both hashes
    - Exact bitwise differences (Hamming distance)
    - Percentage of changed bits (ideal is ~50%)
    """
    hash1_hex = sha256_hex(input1)
    hash2_hex = sha256_hex(input2)

    bin1 = sha256_binary(input1)
    bin2 = sha256_binary(input2)

    differing_bits = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
    total_bits = 256
    percentage_divergence = round((differing_bits / total_bits) * 100, 2)

    # Compute bit-level diff string: '1' if flipped, '0' if matching
    diff_mask = "".join("1" if b1 != b2 else "0" for b1, b2 in zip(bin1, bin2))

    return {
        "input1": input1,
        "input2": input2,
        "hash1_hex": hash1_hex,
        "hash2_hex": hash2_hex,
        "hash1_binary": bin1,
        "hash2_binary": bin2,
        "differing_bits": differing_bits,
        "total_bits": total_bits,
        "percentage_divergence": percentage_divergence,
        "diff_mask": diff_mask,
        "is_avalanche_ideal": 40.0 <= percentage_divergence <= 60.0,
    }


def generate_keypair() -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate a new ECDSA SECP256k1 private and public key pair."""
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()
    return private_key, public_key


def export_private_key_pem(private_key: ec.EllipticCurvePrivateKey) -> str:
    """Export an ECDSA private key to unencrypted PKCS#8 PEM string."""
    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem_bytes.decode("utf-8")


def export_public_key_pem(public_key: ec.EllipticCurvePublicKey) -> str:
    """Export an ECDSA public key to SubjectPublicKeyInfo PEM string."""
    pem_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem_bytes.decode("utf-8")


def export_public_key_hex(public_key: ec.EllipticCurvePublicKey) -> str:
    """Export public key as uncompressed SEC1 hex string."""
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return der_bytes.hex()


def load_private_key(pem_str: str) -> ec.EllipticCurvePrivateKey:
    """Load an ECDSA private key from a PEM string."""
    return serialization.load_pem_private_key(
        pem_str.encode("utf-8") if isinstance(pem_str, str) else pem_str,
        password=None,
    )


def load_public_key(pem_str: str) -> ec.EllipticCurvePublicKey:
    """Load an ECDSA public key from a PEM string."""
    return serialization.load_pem_public_key(
        pem_str.encode("utf-8") if isinstance(pem_str, str) else pem_str,
    )


def get_address_from_public_key(public_key: Union[ec.EllipticCurvePublicKey, str]) -> str:
    """Derive a deterministic wallet address from an ECDSA public key.

    Uses SHA-256 of the uncompressed public key point, taking first 20 bytes (40 hex chars)
    prefixed with '0x' in Ethereum / Crypto standard notation.
    """
    if isinstance(public_key, str):
        if "BEGIN PUBLIC KEY" in public_key:
            pk_obj = load_public_key(public_key)
            uncompressed = pk_obj.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint,
            )
        else:
            # Assume hex string
            uncompressed = bytes.fromhex(public_key)
    else:
        uncompressed = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

    # Double hash or single hash with address prefix
    raw_hash = hashlib.sha256(uncompressed).hexdigest()
    return f"0x{raw_hash[:40]}"


def sign_data(private_key: Union[ec.EllipticCurvePrivateKey, str], message: Union[str, bytes]) -> str:
    """Digitally sign a message with an ECDSA SECP256k1 private key using SHA-256.

    Returns hex-encoded DER signature.
    """
    if isinstance(private_key, str):
        pk = load_private_key(private_key)
    else:
        pk = private_key

    if isinstance(message, str):
        msg_bytes = message.encode("utf-8")
    else:
        msg_bytes = message

    signature_der = pk.sign(msg_bytes, ec.ECDSA(hashes.SHA256()))
    return signature_der.hex()


def verify_signature(
    public_key: Union[ec.EllipticCurvePublicKey, str],
    signature_hex: str,
    message: Union[str, bytes],
) -> bool:
    """Verify an ECDSA DER digital signature against a message and public key.

    Returns True if valid, False if tampered or invalid.
    """
    try:
        if isinstance(public_key, str):
            pk = load_public_key(public_key)
        else:
            pk = public_key

        if isinstance(message, str):
            msg_bytes = message.encode("utf-8")
        else:
            msg_bytes = message

        sig_bytes = bytes.fromhex(signature_hex)
        pk.verify(sig_bytes, msg_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError, TypeError, Exception):
        return False
