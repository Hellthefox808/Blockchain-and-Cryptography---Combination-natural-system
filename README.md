# Blockchain & Cryptography: Combo Nature System

[![CI Test & Build Pipeline](https://github.com/Hellthefox808/Blockchain-and-Cryptography---Combination-natural-system/actions/workflows/ci.yml/badge.svg)](https://github.com/Hellthefox808/Blockchain-and-Cryptography---Combination-natural-system/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

An end-to-end engineered, cryptographically validated blockchain platform demonstrating the combination of distributed ledger technology with modern asymmetric and hash-based cryptography.

Originally initiated as an academic project concept, this codebase was inherited and subsequently re-architected, implemented, hardened, tested, and packaged into a production-ready system as part of my engineering responsibility.

---

## Table of Contents

- [1. System Architecture](#1-system-architecture)
- [2. Cryptographic Foundations](#2-cryptographic-foundations)
  - [SHA-256 & The Avalanche Effect](#sha-256--the-avalanche-effect)
  - [Asymmetric Cryptography (ECDSA SECP256k1)](#asymmetric-cryptography-ecdsa-secp256k1)
  - [Merkle Trees & Inclusion Proofs](#merkle-trees--inclusion-proofs)
- [3. Blockchain & Consensus Engine](#3-blockchain--consensus-engine)
  - [Block Structure](#block-structure)
  - [Proof-of-Work (PoW) Mining](#proof-of-work-pow-mining)
  - [Tamper Detection & Avalanche Resistance](#tamper-detection--avalanche-resistance)
- [4. Interactive Web Dashboard](#4-interactive-web-dashboard)
- [5. Engineering Provenance & Contributions](#5-engineering-provenance--contributions)
- [6. Installation & Quick Start](#6-installation--quick-start)
- [7. REST API Documentation](#7-rest-api-documentation)
- [8. Automated Test Suite](#8-automated-test-suite)
- [9. Docker & Production Deployment](#9-docker--production-deployment)
- [10. License & Attribution](#10-license--attribution)

---

## 1. System Architecture

```text
+-------------------------------------------------------------------------------+
|                           INTERACTIVE WEB CLIENT                             |
|    (Vanilla CSS Glassmorphism + Dynamic State Engine + Cryptographic Lab)    |
+-------------------------------------------------------------------------------+
                                      |
                                      | REST / JSON (HTTP)
                                      v
+-------------------------------------------------------------------------------+
|                            FASTAPI REST BACKEND                              |
|   /api/wallet  |  /api/transaction  |  /api/mine  |  /api/chain  |  /crypto  |
+-------------------------------------------------------------------------------+
                                      |
       +------------------------------+-------------------------------+
       |                                                              |
       v                                                              v
+-----------------------------+                       +-----------------------------+
|    CRYPTOGRAPHIC ENGINE     |                       |      BLOCKCHAIN ENGINE      |
|  * SHA-256 Hashing          |                       |  * Genesis Block            |
|  * Avalanche Calculator     |<--------------------->|  * Proof-of-Work Mining     |
|  * ECDSA SECP256k1 Keypairs |                       |  * Merkle Root Computation  |
|  * DER Digital Signatures   |                       |  * Mempool & Double-Spend   |
|  * Public Key Addresses     |                       |  * Full Chain Validation    |
+-----------------------------+                       +-----------------------------+
                                                              |
                                                              v
                                              +-------------------------------+
                                              |       PERSISTENCE LAYER       |
                                              |    JSON State Serialization   |
                                              +-------------------------------+
```

---

## 2. Cryptographic Foundations

### SHA-256 & The Avalanche Effect

A cornerstone requirement outlined in the project synopsis is demonstrating how cryptographic hash functions establish blockchain immutability via the **avalanche effect**.

Under SHA-256:

- Every unique input produces a deterministic 256-bit (64-hexadecimal character) output.
- **Strict Sensitivity**: Altering a single input character causes approximately 50% of the output bits to flip, making prediction or reverse-engineering impossible.

$$\text{Hamming Distance} = \sum_{i=0}^{255} (b_{1, i} \oplus b_{2, i}) \approx 128 \text{ bits}$$

### Asymmetric Cryptography (ECDSA SECP256k1)

All peer-to-peer transactions utilize Elliptic Curve Digital Signature Algorithm (ECDSA) with the **SECP256k1** curve (identical to Bitcoin and Ethereum):

- **Private Key**: 256-bit scalar stored securely in PKCS#8 PEM format.
- **Public Key**: Uncompressed elliptic curve point $(x, y)$ exported in SubjectPublicKeyInfo PEM format.
- **Wallet Address**: Formatted as `0x` followed by the first 40 hex characters of the SHA-256 digest of the uncompressed public key.
- **Digital Signatures**: Transaction payloads are hashed and signed producing DER-encoded digital signatures, ensuring **non-repudiation** and **data integrity**.

### Merkle Trees & Inclusion Proofs

Transactions within each block are organized into a binary **Merkle Tree**:

- Every transaction hash forms a leaf node.
- Nodes are hashed pairwise: $H_{parent} = \text{SHA256}(H_{left} + H_{right})$.
- If a level has an odd number of elements, the last element is duplicated per standard Bitcoin rules.
- The single resulting **Merkle Root** is stored in the block header.
- Enables Simplified Payment Verification (SPV) inclusion proofs with $O(\log N)$ complexity without downloading the entire block payload.

---

## 3. Blockchain & Consensus Engine

### Block Structure

Each block consists of a cryptographically validated header and a transaction list:

```json
{
  "index": 1,
  "timestamp": 1700000100.0,
  "previous_hash": "000a1b2c...",
  "merkle_root": "8f3e2d1c...",
  "nonce": 4218,
  "difficulty": 2,
  "hash": "00a4b7f9...",
  "transactions": [...]
}
```

### Proof-of-Work (PoW) Mining

Blocks are sealed through Proof of Work:

$$\text{SHA256}(\text{BlockHeader}) < \text{Target}$$

The mining engine iterates the `nonce` integer until the block header hash begins with the required number of leading hexadecimal zeros (difficulty target). Successful mining awards a configurable coinbase reward (default: 25.0 tokens) to the miner's address.

### Tamper Detection & Avalanche Resistance

If an adversary attempts to modify transaction data in any historical block:

1. The transaction hash changes.
2. The block's calculated Merkle root fails to match the header `merkle_root`.
3. The block hash fails verification.
4. Because the block hash changed, the subsequent block's `previous_hash` link is broken.
5. The `is_chain_valid()` engine instantly halts consensus and pinpoints the exact corrupted block.

---

## 4. Interactive Web Dashboard

The application provides a built-in Single Page Application dashboard served directly from the backend:

- **Ledger Timeline**: Horizontally scrolling visual block explorer displaying block height, hashes, nonces, timestamps, and Merkle tree breakdowns.
- **Wallet Studio**: Generate new SECP256k1 keypairs, copy private keys, and query real-time spendable balances. Includes preset test wallets (Vinny, Kinny, Miner) from the project synopsis.
- **Transaction Hub**: Compose transfers, attach private keys for client-side signing, and broadcast to the mempool.
- **Mining Center**: Real-time Proof-of-Work mining simulator with live telemetry console.
- **Cryptographic Lab**:
  - **Avalanche Effect Visualizer**: Interactive 256-bit heatmap grid comparing two inputs with exact bit divergence percentages.
  - **Digital Signature Verifier**: Independent cryptographic validation tool.
  - **Consensus Attack Simulator**: Deliberately alter any confirmed block to watch the security engine detect tampering in real time.

---

## 5. Engineering Provenance & Contributions

### Inherited Baseline

- **Inherited Artifacts**: A conceptual 6-page project synopsis (`Blockchain+Crypto Synopsis .pdf`) and an unfinished Google Colab notebook stub (`BlockchainProject_D.ipynb`) containing basic hash functions and promotional marketing text.
- **Original Authorship**: Conceptual project design and synopsis created by original contributors.

### Engineering Contributions

- **Full Cryptographic Core**: Built pure-Python implementation of SHA-256 bitwise analysis, ECDSA SECP256k1 key generation, digital signing, and address derivation using `cryptography`.
- **Merkle Tree Engine**: Implemented complete binary Merkle tree with root generation and SPV audit proofs.
- **Consensus & Ledger**: Engineered Proof-of-Work mining loop, genesis block generation, mempool queue, balance accounting with double-spend prevention, and chain validation.
- **REST API**: Developed FastAPI web service with complete OpenAPI documentation covering all blockchain operations.
- **Interactive UI**: Built responsive, dark-mode glassmorphic frontend with live visualizations and cryptographic testing labs.
- **Notebook Overhaul**: Reconstructed `BlockchainProject_D.ipynb` into a 100% executable, educational Colab/Jupyter notebook covering all 9 modules with zero broken stubs.
- **Automated Testing**: Created comprehensive pytest suite with 27 unit, integration, and API tests.
- **Production Packaging**: Containerized with Docker and Docker Compose, and configured automated multi-version Python CI via GitHub Actions.

---

## 6. Installation & Quick Start

### Prerequisites

- Python 3.9+ installed
- Git

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/Hellthefox808/Blockchain-and-Cryptography---Combination-natural-system.git
cd Blockchain-and-Cryptography---Combination-natural-system

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to:

- **Interactive Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI (Swagger) Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Redoc API Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 7. REST API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check |
| `GET` | `/api/stats` | Blockchain height, difficulty, validity, and mempool counts |
| `POST` | `/api/wallet/create` | Generate new ECDSA keypair and address |
| `GET` | `/api/wallet/{address}/balance` | Query balance and confirmed transaction count |
| `GET` | `/api/wallet/{address}/transactions` | Retrieve complete transaction history for an address |
| `POST` | `/api/transaction/new` | Broadcast signed transaction to mempool |
| `GET` | `/api/transaction/pending` | Inspect unconfirmed transactions in mempool |
| `POST` | `/api/mine` | Trigger Proof-of-Work mining of pending transactions |
| `GET` | `/api/chain` | Retrieve full blockchain ledger |
| `GET` | `/api/block/{index}` | Inspect specific block and its Merkle tree |
| `GET` | `/api/validate` | Audit cryptographic validity of the chain |
| `POST` | `/api/crypto/avalanche` | Calculate bit-level avalanche divergence for two inputs |
| `POST` | `/api/crypto/verify-signature` | Verify arbitrary ECDSA digital signature |
| `POST` | `/api/tamper` | Deliberately alter block data to test consensus defenses |
| `POST` | `/api/reset` | Reset blockchain state to clean Genesis block |

---

## 8. Automated Test Suite

The test suite covers unit logic, cryptographic primitives, Merkle trees, consensus rules, balance checks, tampering detection, and REST API routes.

```bash
# Run all automated tests
pytest -v tests/
```

Test coverage includes:

- `tests/test_crypto.py`: SHA-256 determinism, binary conversions, avalanche Hamming distance (40%-60%), ECDSA key generation, valid/tampered digital signature checks.
- `tests/test_merkle.py`: Empty trees, odd/even transaction lists, Merkle root verification, SPV inclusion proofs.
- `tests/test_transaction.py`: Coinbase rewards, digital signing, tamper detection, and JSON roundtripping.
- `tests/test_blockchain.py`: Genesis block, PoW mining, balance tracking, insufficient funds rejection, double-spend prevention, and persistence.
- `tests/test_api.py`: FastAPI endpoints, wallet creation, mining flows, transactions, and tamper recovery.

---

## 9. Docker & Production Deployment

### Running with Docker

```bash
# Build Docker image
docker build -t combo-nature-blockchain .

# Run container on port 8000
docker run -d -p 8000:8000 --name blockchain-node combo-nature-blockchain
```

### Running with Docker Compose

```bash
docker-compose up -d
```

---

## 10. License & Attribution

This project is licensed under the [MIT License](LICENSE).

- Theoretical foundations and project synopsis: Preserved from original academic project specification (`Blockchain+Crypto Synopsis .pdf`).
- Engineering architecture, cryptographic implementations, REST API, web dashboard, notebook reconstruction, and test suite: Maintained and authored by Ravi Ranjan Singh.
