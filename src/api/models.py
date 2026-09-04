"""Pydantic schemas and request/response models for the REST API."""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class WalletCreateResponse(BaseModel):
    address: str
    public_key_pem: str
    private_key_pem: str
    created_at: float


class BalanceResponse(BaseModel):
    address: str
    balance: float
    confirmed_tx_count: int
    pending_tx_count: int


class TransactionCreateRequest(BaseModel):
    sender: str
    recipient: str
    amount: float = Field(..., gt=0)
    fee: float = Field(default=0.0, ge=0)
    sender_public_key: Optional[str] = None
    signature: Optional[str] = None
    private_key: Optional[str] = None  # Helper for browser UI signing


class TransactionResponse(BaseModel):
    tx_id: str
    sender: str
    recipient: str
    amount: float
    fee: float
    timestamp: float
    signature: Optional[str] = None


class MineBlockRequest(BaseModel):
    miner_address: str


class MineBlockResponse(BaseModel):
    message: str
    block_index: int
    block_hash: str
    merkle_root: str
    nonce: int
    transactions_count: int
    difficulty: int


class AvalancheRequest(BaseModel):
    input1: str = Field(..., min_length=1)
    input2: str = Field(..., min_length=1)


class AvalancheResponse(BaseModel):
    input1: str
    input2: str
    hash1_hex: str
    hash2_hex: str
    hash1_binary: str
    hash2_binary: str
    differing_bits: int
    total_bits: int
    percentage_divergence: float
    diff_mask: str
    is_avalanche_ideal: bool


class SignatureVerifyRequest(BaseModel):
    public_key: str
    message: str
    signature: str


class SignatureVerifyResponse(BaseModel):
    is_valid: bool
    message: str


class TamperRequest(BaseModel):
    block_index: int = Field(..., ge=0)
    new_amount: float = Field(default=99999.0)


class TamperResponse(BaseModel):
    success: bool
    message: str


class ChainValidationResponse(BaseModel):
    is_valid: bool
    message: str
    broken_block_index: Optional[int] = None


class SystemStatsResponse(BaseModel):
    chain_length: int
    latest_block_index: int
    latest_block_hash: str
    difficulty: int
    mining_reward: float
    pending_transactions_count: int
    total_transactions_count: int
    is_valid: bool
    validation_message: str
    broken_block_index: Optional[int] = None
