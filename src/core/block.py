"""Block data structure and Proof-of-Work (PoW) consensus engine.

Provides:
- Block header and body representation
- Integration with Merkle Tree root calculation
- SHA-256 Proof-of-Work mining algorithm
- Cryptographic integrity validation
- Serialization and deserialization
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, List, Optional

from src.core.crypto import sha256_hex
from src.core.merkle import MerkleTree
from src.core.transaction import Transaction


@dataclass
class Block:
    """Represents a single block in the cryptographic blockchain."""

    index: int
    transactions: List[Transaction]
    previous_hash: str
    timestamp: float = field(default_factory=lambda: time.time())
    nonce: int = 0
    difficulty: int = 2
    merkle_root: Optional[str] = None
    hash: Optional[str] = None

    def __post_init__(self) -> None:
        if self.merkle_root is None:
            self.merkle_root = self.compute_merkle_root()
        if self.hash is None:
            self.hash = self.compute_hash()

    def compute_merkle_root(self) -> str:
        """Compute the Merkle root of all transactions contained in this block."""
        tx_hashes = [tx.tx_id or tx.compute_hash() for tx in self.transactions]
        tree = MerkleTree(tx_hashes)
        return tree.get_root()

    def get_header_payload(self) -> dict[str, Any]:
        """Produce the canonical block header data used for block hashing."""
        return {
            "index": self.index,
            "timestamp": round(float(self.timestamp), 6),
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root or self.compute_merkle_root(),
            "nonce": self.nonce,
            "difficulty": self.difficulty,
        }

    def compute_hash(self) -> str:
        """Calculate the SHA-256 cryptographic hash of the block header."""
        header_payload = self.get_header_payload()
        return sha256_hex(header_payload)

    def mine_block(self, difficulty: Optional[int] = None, max_nonce: int = 10_000_000) -> tuple[str, int]:
        """Perform Proof-of-Work mining until block hash meets difficulty target."""
        if difficulty is not None:
            self.difficulty = difficulty

        target_prefix = "0" * self.difficulty
        self.merkle_root = self.compute_merkle_root()

        start_time = time.time()
        while self.nonce < max_nonce:
            current_hash = self.compute_hash()
            if current_hash.startswith(target_prefix):
                self.hash = current_hash
                return current_hash, self.nonce
            self.nonce += 1

        # Fallback if max_nonce reached without finding match
        self.hash = self.compute_hash()
        return self.hash, self.nonce

    def is_valid(self, expected_previous_hash: Optional[str] = None) -> bool:
        """Verify internal consistency, Proof-of-Work target, and transaction signatures."""
        # 1. Verify previous hash link if provided
        if expected_previous_hash is not None and self.previous_hash != expected_previous_hash:
            return False

        # 2. Verify Merkle root matches transactions
        calculated_root = self.compute_merkle_root()
        if self.merkle_root != calculated_root:
            return False

        # 3. Verify block hash matches header computation
        if self.hash != self.compute_hash():
            return False

        # 4. Verify Proof of Work difficulty constraint (except genesis block if difficulty 0)
        target_prefix = "0" * self.difficulty
        if not self.hash.startswith(target_prefix):
            return False

        # 5. Verify all transactions inside the block are cryptographically valid
        for tx in self.transactions:
            if not tx.is_valid():
                return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert block to dictionary representation."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Block:
        """Construct a Block instance from dictionary."""
        transactions = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        block = cls(
            index=int(data["index"]),
            transactions=transactions,
            previous_hash=data["previous_hash"],
            timestamp=float(data["timestamp"]),
            nonce=int(data.get("nonce", 0)),
            difficulty=int(data.get("difficulty", 2)),
            merkle_root=data.get("merkle_root"),
            hash=data.get("hash"),
        )
        return block
