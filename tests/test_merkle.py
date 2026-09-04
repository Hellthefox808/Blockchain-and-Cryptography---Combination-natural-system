"""Unit tests for Merkle Tree computation and inclusion proofs."""

from src.core.crypto import sha256_hex
from src.core.merkle import MerkleTree


def test_empty_merkle_tree():
    tree = MerkleTree([])
    assert tree.get_root() == "0" * 64
    assert tree.get_proof(0) == []


def test_single_leaf_merkle_tree():
    leaf = sha256_hex("tx_0")
    tree = MerkleTree([leaf])
    assert tree.get_root() == leaf


def test_merkle_tree_odd_and_even_counts():
    leaves_even = [sha256_hex(f"tx_{i}") for i in range(4)]
    tree_even = MerkleTree(leaves_even)
    assert len(tree_even.get_root()) == 64
    assert len(tree_even.levels) == 3

    leaves_odd = [sha256_hex(f"tx_{i}") for i in range(5)]
    tree_odd = MerkleTree(leaves_odd)
    assert len(tree_odd.get_root()) == 64
    assert len(tree_odd.levels) == 4


def test_merkle_inclusion_proofs():
    leaves = [sha256_hex(f"tx_{i}") for i in range(7)]
    tree = MerkleTree(leaves)
    root = tree.get_root()

    for idx, leaf in enumerate(leaves):
        proof = tree.get_proof(idx)
        assert len(proof) > 0
        assert MerkleTree.verify_proof(leaf, proof, root) is True

    # Tampered leaf
    tampered_leaf = sha256_hex("tampered_transaction_data")
    assert MerkleTree.verify_proof(tampered_leaf, tree.get_proof(0), root) is False
