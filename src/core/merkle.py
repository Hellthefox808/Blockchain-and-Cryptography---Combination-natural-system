"""Merkle Tree implementation for transaction integrity and inclusion proofs in blocks.

Provides:
- Pairwise SHA-256 tree aggregation
- Empty tree and odd-length leaf handling (Bitcoin-style last-node replication)
- Merkle root computation
- Cryptographic Merkle inclusion proof generation (SPV)
- Merkle proof verification against a known root
"""

from __future__ import annotations

from typing import Any, List, Optional
from src.core.crypto import sha256_hex


class MerkleTree:
    """Binary Merkle Tree for transaction integrity verification."""

    def __init__(self, leaves: Optional[List[str]] = None) -> None:
        self.leaves: List[str] = leaves or []
        self.levels: List[List[str]] = []
        self.root: str = "0" * 64
        if self.leaves:
            self.build_tree()

    def build_tree(self) -> str:
        """Construct the Merkle tree levels from the current leaf hashes."""
        if not self.leaves:
            self.root = "0" * 64
            self.levels = []
            return self.root

        # Ensure all leaves are hashed strings
        current_level = [
            leaf if len(leaf) == 64 and all(c in "0123456789abcdefABCDEF" for c in leaf) else sha256_hex(leaf)
            for leaf in self.leaves
        ]
        self.levels = [current_level]

        while len(current_level) > 1:
            next_level: List[str] = []
            # If odd count, duplicate last item per standard Bitcoin Merkle tree rules
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent_hash = sha256_hex(left + right)
                next_level.append(parent_hash)

            current_level = next_level
            self.levels.append(current_level)

        self.root = self.levels[-1][0] if self.levels else "0" * 64
        return self.root

    def get_root(self) -> str:
        """Return the current 64-character hexadecimal Merkle root."""
        return self.root

    def get_proof(self, tx_index: int) -> List[dict[str, str]]:
        """Generate a Merkle inclusion proof (audit path) for a leaf at tx_index.

        Each element in the proof indicates:
        - hash: The sibling's hash value
        - position: 'left' if the sibling is on the left, 'right' if on the right
        """
        if not self.levels or tx_index < 0 or tx_index >= len(self.leaves):
            return []

        proof: List[dict[str, str]] = []
        idx = tx_index

        for level_idx in range(len(self.levels) - 1):
            level = self.levels[level_idx]
            # Sibling index
            if idx % 2 == 0:
                sibling_idx = idx + 1 if idx + 1 < len(level) else idx
                position = "right"
            else:
                sibling_idx = idx - 1
                position = "left"

            sibling_hash = level[sibling_idx]
            proof.append({"hash": sibling_hash, "position": position})
            idx = idx // 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[dict[str, str]], expected_root: str) -> bool:
        """Verify an inclusion proof against an expected Merkle root."""
        current_hash = leaf_hash
        for item in proof:
            sibling_hash = item["hash"]
            position = item["position"]

            if position == "right":
                current_hash = sha256_hex(current_hash + sibling_hash)
            else:
                current_hash = sha256_hex(sibling_hash + current_hash)

        return current_hash.lower() == expected_root.lower()

    def to_dict(self) -> dict[str, Any]:
        """Serialize tree structure for API visualization."""
        return {
            "root": self.root,
            "leaf_count": len(self.leaves),
            "leaves": self.leaves,
            "depth": len(self.levels),
            "levels": self.levels,
        }
