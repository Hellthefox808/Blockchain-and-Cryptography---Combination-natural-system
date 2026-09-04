"""FastAPI router implementing all endpoints for the Combo Nature System."""

from __future__ import annotations

import time
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from src.api.models import (
    AvalancheRequest,
    AvalancheResponse,
    BalanceResponse,
    ChainValidationResponse,
    MineBlockRequest,
    MineBlockResponse,
    SignatureVerifyRequest,
    SignatureVerifyResponse,
    SystemStatsResponse,
    TamperRequest,
    TamperResponse,
    TransactionCreateRequest,
    TransactionResponse,
    WalletCreateResponse,
)
from src.core.blockchain import Blockchain
from src.core.crypto import (
    calculate_avalanche_effect,
    export_private_key_pem,
    export_public_key_pem,
    generate_keypair,
    get_address_from_public_key,
    load_private_key,
    verify_signature,
)
from src.core.transaction import Transaction

router = APIRouter(prefix="/api", tags=["Blockchain & Cryptography"])

# Global in-memory blockchain instance (can be injected or reloaded)
blockchain = Blockchain(difficulty=2, mining_reward=25.0)


@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats() -> Dict[str, Any]:
    """Retrieve system health, block metrics, difficulty, and consensus status."""
    return blockchain.get_stats()


@router.post("/wallet/create", response_model=WalletCreateResponse)
def create_wallet() -> Dict[str, Any]:
    """Generate a new ECDSA SECP256k1 keypair and cryptographic wallet address."""
    priv, pub = generate_keypair()
    priv_pem = export_private_key_pem(priv)
    pub_pem = export_public_key_pem(pub)
    address = get_address_from_public_key(pub)

    return {
        "address": address,
        "public_key_pem": pub_pem,
        "private_key_pem": priv_pem,
        "created_at": time.time(),
    }


@router.get("/wallet/{address}/balance", response_model=BalanceResponse)
def get_wallet_balance(address: str) -> Dict[str, Any]:
    """Query confirmed and spendable balance for an address."""
    balance = blockchain.get_balance(address)
    confirmed_count = 0
    address_lower = address.lower()

    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.sender.lower() == address_lower or tx.recipient.lower() == address_lower:
                confirmed_count += 1

    pending_count = sum(
        1
        for tx in blockchain.pending_transactions
        if tx.sender.lower() == address_lower or tx.recipient.lower() == address_lower
    )

    return {
        "address": address,
        "balance": balance,
        "confirmed_tx_count": confirmed_count,
        "pending_tx_count": pending_count,
    }


@router.get("/wallet/{address}/transactions")
def get_wallet_transactions(address: str) -> List[Dict[str, Any]]:
    """Retrieve full transaction history for an address."""
    txs: List[Dict[str, Any]] = []
    address_lower = address.lower()

    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.sender.lower() == address_lower or tx.recipient.lower() == address_lower:
                tx_dict = tx.to_dict()
                tx_dict["block_index"] = block.index
                tx_dict["block_hash"] = block.hash
                txs.append(tx_dict)

    return txs


@router.post("/transaction/new", response_model=TransactionResponse)
def create_transaction(req: TransactionCreateRequest) -> Dict[str, Any]:
    """Submit a cryptographically signed transaction to the mempool."""
    sender_public_key = req.sender_public_key
    signature = req.signature

    # If user provided a private key, sign transaction automatically
    if req.private_key:
        priv_obj = load_private_key(req.private_key)
        pub_obj = priv_obj.public_key()
        sender_public_key = export_public_key_pem(pub_obj)
        sender_address = get_address_from_public_key(pub_obj)

        if sender_address.lower() != req.sender.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided private key does not match sender address.",
            )

        tx = Transaction(
            sender=req.sender,
            recipient=req.recipient,
            amount=req.amount,
            fee=req.fee,
            sender_public_key=sender_public_key,
        )
        signature = tx.sign(priv_obj)
    else:
        if not sender_public_key or not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either (sender_public_key and signature) or private_key.",
            )
        tx = Transaction(
            sender=req.sender,
            recipient=req.recipient,
            amount=req.amount,
            fee=req.fee,
            sender_public_key=sender_public_key,
            signature=signature,
        )

    success, msg = blockchain.add_transaction(tx)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return tx.to_dict()


@router.get("/transaction/pending")
def get_pending_transactions() -> List[Dict[str, Any]]:
    """Inspect all pending transactions currently waiting in the mempool."""
    return [tx.to_dict() for tx in blockchain.pending_transactions]


@router.post("/mine", response_model=MineBlockResponse)
def mine_block(req: MineBlockRequest) -> Dict[str, Any]:
    """Mine all pending transactions into a new block using Proof-of-Work."""
    if not req.miner_address or len(req.miner_address) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid miner address required to receive coinbase block reward.",
        )

    mined_block = blockchain.mine_pending_transactions(miner_address=req.miner_address)
    return {
        "message": f"Block #{mined_block.index} successfully mined!",
        "block_index": mined_block.index,
        "block_hash": mined_block.hash or "",
        "merkle_root": mined_block.merkle_root or "",
        "nonce": mined_block.nonce,
        "transactions_count": len(mined_block.transactions),
        "difficulty": mined_block.difficulty,
    }


@router.get("/chain")
def get_chain() -> Dict[str, Any]:
    """Return the entire blockchain ledger."""
    return blockchain.to_dict()


@router.get("/block/{index}")
def get_block(index: int) -> Dict[str, Any]:
    """Fetch a single block with Merkle tree details."""
    if index < 0 or index >= len(blockchain.chain):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Block index #{index} not found.",
        )
    block = blockchain.chain[index]
    data = block.to_dict()

    # Calculate Merkle tree visualization
    from src.core.merkle import MerkleTree
    leaves = [tx.tx_id or tx.compute_hash() for tx in block.transactions]
    tree = MerkleTree(leaves)
    data["merkle_tree"] = tree.to_dict()
    return data


@router.get("/validate", response_model=ChainValidationResponse)
def validate_chain() -> Dict[str, Any]:
    """Audit and verify cryptographic integrity of the entire chain."""
    is_valid, msg, broken_idx = blockchain.is_chain_valid()
    return {
        "is_valid": is_valid,
        "message": msg,
        "broken_block_index": broken_idx,
    }


@router.post("/crypto/avalanche", response_model=AvalancheResponse)
def test_avalanche_effect(req: AvalancheRequest) -> Dict[str, Any]:
    """Calculate bit-level avalanche effect between two inputs under SHA-256."""
    return calculate_avalanche_effect(req.input1, req.input2)


@router.post("/crypto/verify-signature", response_model=SignatureVerifyResponse)
def test_verify_signature(req: SignatureVerifyRequest) -> Dict[str, Any]:
    """Verify an ECDSA digital signature for a message and public key."""
    is_valid = verify_signature(req.public_key, req.signature, req.message)
    msg = "Digital signature is VALID." if is_valid else "Digital signature is INVALID or corrupted."
    return {"is_valid": is_valid, "message": msg}


@router.post("/tamper", response_model=TamperResponse)
def tamper_block_endpoint(req: TamperRequest) -> Dict[str, Any]:
    """Deliberately modify a block's transaction to demonstrate tamper detection."""
    success, msg = blockchain.tamper_block(req.block_index, req.new_amount)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"success": success, "message": msg}


@router.post("/reset")
def reset_blockchain() -> Dict[str, str]:
    """Reset blockchain back to clean Genesis state."""
    global blockchain
    blockchain = Blockchain(difficulty=2, mining_reward=25.0)
    return {"message": "Blockchain reset to initial Genesis state."}
