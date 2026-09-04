"""Blockchain ledger, consensus coordinator, and tamper-resistance engine.

Provides:
- Genesis block construction
- Transaction mempool and double-spend validation
- Balance and state accounting across all confirmed blocks
- Proof-of-Work block mining with difficulty control
- Full cryptographic chain integrity verification
- Educational block tampering simulation
- Ledger serialization and persistence
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from src.core.block import Block
from src.core.crypto import sha256_hex
from src.core.transaction import Transaction


class Blockchain:
    """The central ledger maintaining the chain of cryptographically linked blocks."""

    def __init__(
        self,
        difficulty: int = 2,
        mining_reward: float = 10.0,
        storage_path: Optional[str] = None,
    ) -> None:
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty: int = difficulty
        self.mining_reward: float = mining_reward
        self.storage_path: Optional[str] = storage_path

        if self.storage_path and os.path.exists(self.storage_path) and os.path.getsize(self.storage_path) > 0:
            if not self.load_from_disk(self.storage_path):
                self.create_genesis_block()
        else:
            self.create_genesis_block()

    def create_genesis_block(self) -> Block:
        """Construct and seal the immutable Genesis Block (Height 0)."""
        genesis_tx = Transaction(
            sender="SYSTEM",
            recipient="0xGenesisFaucet00000000000000000000000000",
            amount=10000.0,
            timestamp=1700000000.0,
            signature="GENESIS_COINBASE",
        )
        genesis_block = Block(
            index=0,
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            timestamp=1700000000.0,
            difficulty=self.difficulty,
            nonce=0,
        )
        # Mine genesis with required difficulty
        genesis_block.mine_block(difficulty=self.difficulty)
        self.chain = [genesis_block]
        return genesis_block

    def get_latest_block(self) -> Block:
        """Return the highest block in the active chain."""
        return self.chain[-1]

    def get_balance(self, address: str) -> float:
        """Calculate the current spendable balance for an address.

        Computes net balance from all confirmed transactions, deducting any
        pending outgoing transfers in the mempool to prevent double-spending.
        """
        address_lower = address.lower()
        balance = 0.0

        # Confirmed transactions
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient.lower() == address_lower:
                    balance += tx.amount
                if tx.sender.lower() == address_lower:
                    balance -= (tx.amount + tx.fee)

        # Pending unconfirmed outgoing transactions
        for tx in self.pending_transactions:
            if tx.sender.lower() == address_lower:
                balance -= (tx.amount + tx.fee)

        return round(balance, 8)

    def add_transaction(self, transaction: Transaction) -> Tuple[bool, str]:
        """Validate and add a new transaction to the mempool."""
        if not transaction.is_valid():
            return False, "Invalid transaction format, ID, or cryptographic signature."

        if not transaction.is_coinbase():
            sender_balance = self.get_balance(transaction.sender)
            required_amount = transaction.amount + transaction.fee
            if sender_balance < required_amount:
                return (
                    False,
                    f"Insufficient funds: available {sender_balance}, required {required_amount}.",
                )

        # Check for duplicates in mempool
        if any(tx.tx_id == transaction.tx_id for tx in self.pending_transactions):
            return False, "Transaction already exists in mempool."

        self.pending_transactions.append(transaction)
        return True, "Transaction successfully added to mempool."

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Pack pending transactions, award mining reward, mine PoW, and append block."""
        # 1. Create coinbase mining reward transaction
        reward_tx = Transaction(
            sender="SYSTEM",
            recipient=miner_address,
            amount=self.mining_reward,
            timestamp=time.time(),
            signature="MINING_REWARD",
        )

        # Prepare transactions for this block
        block_transactions = [reward_tx] + self.pending_transactions
        prev_hash = self.get_latest_block().hash or ""

        # Construct new block
        new_block = Block(
            index=len(self.chain),
            transactions=block_transactions,
            previous_hash=prev_hash,
            timestamp=time.time(),
            difficulty=self.difficulty,
        )

        # Mine the block
        new_block.mine_block(difficulty=self.difficulty)

        # Append to chain and clear mempool
        self.chain.append(new_block)
        self.pending_transactions = []

        if self.storage_path:
            self.save_to_disk(self.storage_path)

        return new_block

    def is_chain_valid(self) -> Tuple[bool, str, Optional[int]]:
        """Verify complete cryptographic integrity of the entire blockchain.

        Returns (is_valid, status_message, corrupted_block_index).
        """
        for i in range(len(self.chain)):
            current_block = self.chain[i]

            # 1. Verify genesis block
            if i == 0:
                if current_block.previous_hash != "0" * 64:
                    return False, "Genesis block previous_hash is invalid.", 0
                if current_block.hash != current_block.compute_hash():
                    return False, "Genesis block hash mismatch.", 0
                continue

            prev_block = self.chain[i - 1]

            # 2. Check previous_hash link
            if current_block.previous_hash != prev_block.hash:
                return (
                    False,
                    f"Block #{i} previous_hash '{current_block.previous_hash[:16]}...' does not match Block #{i - 1} hash '{prev_block.hash[:16]}...'.",
                    i,
                )

            # 3. Check block validity (Merkle root, PoW, tx signatures)
            if not current_block.is_valid(prev_block.hash):
                return (
                    False,
                    f"Block #{i} failed internal cryptographic validation (Merkle root, PoW target, or signature).",
                    i,
                )

        return True, "Blockchain is cryptographically secure and fully valid.", None

    def tamper_block(self, block_index: int, new_amount: float = 99999.0) -> Tuple[bool, str]:
        """Educational demonstration: deliberately alter a transaction in a block.

        This demonstrates the avalanche effect: changing a single transaction alters the Merkle root,
        which invalidates the block hash, breaking the link to all subsequent blocks.
        """
        if block_index < 0 or block_index >= len(self.chain):
            return False, f"Block index {block_index} out of range."

        block = self.chain[block_index]
        if not block.transactions:
            return False, f"Block #{block_index} contains no transactions to tamper."

        target_tx = block.transactions[0]
        original_amount = target_tx.amount
        target_tx.amount = new_amount
        # Recalculate transaction hash without valid signature
        target_tx.tx_id = target_tx.compute_hash()

        return (
            True,
            f"Tampered Block #{block_index} Tx #{target_tx.tx_id[:8]}: modified amount from {original_amount} to {new_amount}. Cryptographic verification will now fail.",
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return high-level telemetry and status metrics."""
        is_valid, msg, broken_idx = self.is_chain_valid()
        total_transactions = sum(len(b.transactions) for b in self.chain)
        return {
            "chain_length": len(self.chain),
            "latest_block_index": self.get_latest_block().index,
            "latest_block_hash": self.get_latest_block().hash,
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "pending_transactions_count": len(self.pending_transactions),
            "total_transactions_count": total_transactions,
            "is_valid": is_valid,
            "validation_message": msg,
            "broken_block_index": broken_idx,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete blockchain."""
        return {
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
        }

    def save_to_disk(self, filepath: str) -> None:
        """Persist blockchain state to JSON file."""
        dirname = os.path.dirname(filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def load_from_disk(self, filepath: str) -> bool:
        """Load and reconstruct blockchain state from JSON file."""
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception):
            return False

        self.difficulty = data.get("difficulty", self.difficulty)
        self.mining_reward = data.get("mining_reward", self.mining_reward)
        self.chain = [Block.from_dict(b) for b in data.get("chain", [])]
        self.pending_transactions = [
            Transaction.from_dict(tx) for tx in data.get("pending_transactions", [])
        ]
        return True
