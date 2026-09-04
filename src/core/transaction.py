"""Transaction data model and verification engine.

Provides:
- Transaction structure with cryptographic digital signatures
- Payload hashing for transaction IDs
- Digital signature verification against sender's public key
- Protection against transaction tampering and replay
- Support for regular peer-to-peer transfers and coinbase mining rewards
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from src.core.crypto import (
    get_address_from_public_key,
    sha256_hex,
    sign_data,
    verify_signature,
)


@dataclass
class Transaction:
    """Represents a transfer of value on the blockchain."""

    sender: str
    recipient: str
    amount: float
    timestamp: float = field(default_factory=lambda: time.time())
    sender_public_key: Optional[str] = None
    signature: Optional[str] = None
    fee: float = 0.0
    tx_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.tx_id is None:
            self.tx_id = self.compute_hash()

    def get_signing_payload(self) -> str:
        """Create canonical representation of transaction data to be signed."""
        payload_dict = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": round(float(self.amount), 8),
            "timestamp": round(float(self.timestamp), 6),
            "fee": round(float(self.fee), 8),
        }
        return sha256_hex(payload_dict)

    def compute_hash(self) -> str:
        """Calculate transaction unique ID."""
        return self.get_signing_payload()

    def sign(self, private_key: Any) -> str:
        """Sign this transaction using sender's private key."""
        if self.is_coinbase():
            self.signature = "COINBASE_VALID"
            return self.signature

        payload_hash = self.get_signing_payload()
        self.signature = sign_data(private_key, payload_hash)
        return self.signature

    def is_coinbase(self) -> bool:
        """Check if this transaction is a genesis or block reward coinbase transaction."""
        return self.sender.upper() in ("SYSTEM", "COINBASE", "GENESIS", "0X0000000000000000000000000000000000000000")

    def is_valid(self) -> bool:
        """Verify transaction integrity, amount sanity, and digital signature."""
        if self.amount <= 0:
            return False

        if self.tx_id != self.compute_hash():
            return False

        if self.is_coinbase():
            return True

        if not self.signature or not self.sender_public_key:
            return False

        # Validate that sender address matches public key
        derived_address = get_address_from_public_key(self.sender_public_key)
        if derived_address.lower() != self.sender.lower():
            return False

        # Verify cryptographic digital signature
        payload_hash = self.get_signing_payload()
        return verify_signature(self.sender_public_key, self.signature, payload_hash)

    def to_dict(self) -> dict[str, Any]:
        """Convert transaction to dictionary format."""
        return {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "sender_public_key": self.sender_public_key,
            "signature": self.signature,
            "fee": self.fee,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transaction:
        """Construct a Transaction instance from a dictionary."""
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            amount=float(data["amount"]),
            timestamp=float(data.get("timestamp", time.time())),
            sender_public_key=data.get("sender_public_key"),
            signature=data.get("signature"),
            fee=float(data.get("fee", 0.0)),
            tx_id=data.get("tx_id"),
        )
