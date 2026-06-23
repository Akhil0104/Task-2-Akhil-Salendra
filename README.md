# ⬛ Obsidian Vault - Liquid Democracy EVM Simulator

A zero-dependency, advanced Ethereum Virtual Machine (EVM) simulator built purely in Python. This system upgrades standard governance protocols by implementing **Liquid Proxy Delegation** with integrated O(n) algorithmic loop-detection safeties.

## 🚀 Advanced Architecture
* **Liquid Democracy Engine:** Users can directly vote via the CEI pattern or cryptographically delegate their structural voting weight to trusted proxy identities.
* **Infinite-Loop Protection:** Implements an algorithmic path-traversal safeguard to detect and `REVERT` malicious circular delegation loops (e.g., A -> B -> C -> A) before state execution.
* **Obsidian Data Terminal:** A hyper-technical frontend UI rendering immutable SHA-256 block ledger paths, Gwei/Wei gas burn estimations, and strict hex-enforced Session Identity management.

## ⚙️ Execution
1. Run local EVM Node: `python voting_evm_app.py`
2. Connect Terminal: `http://localhost:8080/`

**Testnet Keys:**
* **Root Admin:** `0xDEC0DE1AB5000000000000000000000000002027`
* **Standard User:** `0xAbC123fE56789dEf0123456789abcdef01234567`
