# 🧩 PropositionClusterEngine (GenLayer Intelligent Contract)

![GenLayer](https://img.shields.io/badge/Network-GenLayer_Studio-blueviolet?style=for-the-badge)
![Smart Contract](https://img.shields.io/badge/Contract-Python_GenVM-blue?style=for-the-badge&logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Pytest-Passing-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

**PropositionClusterEngine** is an autonomous GenLayer Intelligent Contract that performs pairwise bidirectional entailment analysis over pinned GitHub datasets and constructs verified equivalence clusters on-chain.

Rather than relying on fuzzy embedding similarity scores, the contract evaluates every statement pair via LLM consensus (`SYNONYMOUS`, `DIVERGENT`, `AMBIGUOUS`) and enforces strict mathematical transitivity before indexing canonical cluster anchors.

---

## ✨ Key Architectural Features

* **Canonical Input Ordering (`parse_claim_bundle`):** Automatically sorts incoming entries by `id` so publishers cannot manipulate cluster anchor selection through row ordering.
* **Transitivity & Contradiction Firewall (`build_equivalence_clusters`):** Rejects non-transitive LLM graphs (`TRANSITIVITY_VIOLATION`) and identical-statement mismatches (`IDENTICAL_STATEMENT_MISMATCH`) instead of chaining noisy merges.
* **Cryptographic Source Pinning:** Verifies exact SHA-256 digests of raw GitHub JSON payloads (`payload_sha256`) prior to executing LLM evaluation.
* **Chained Audit Trail (`audit_trail`):** Every job registration, clustering execution, and expiration event is appended to an immutable hash-chained log.

---

## 📂 Dataset Schema Format

Pinned GitHub JSON files must contain between 2 and 6 entries matching the following schema:

```json
{
  "entries": [
    {
      "id": "prop_01",
      "statement": "Validator unbonding requires a strict 14-day cooldown period."
    },
    {
      "id": "prop_02",
      "statement": "Staked tokens remain locked for exactly two weeks after unbonding begins."
    },
    {
      "id": "prop_03",
      "statement": "Slashing penalties burn 5 percent of the offending validator stake."
    }
  ]
}
```

---

## 🚀 Contract Lifecycle & Methods

1. **`submit_job`**: Registers a clustering job with pinned GitHub coordinates (`gh_user`, `gh_repo`, `commit_sha`, `file_path`, `payload_sha256`) and an `expires_at` timestamp.
2. **`execute_clustering(job_id, run_index)`**: Fetches the pinned JSON bundle, runs pairwise semantic evaluation via `gl.vm.run_nondet_unsafe`, verifies graph transitivity, and indexes canonical equivalence clusters if `CLUSTERED`.
3. **`resolve_entry(job_id, entry_id)`**: Resolves any member `entry_id` to its canonical cluster `anchor_id` along with the cryptographic `registry_hash`.
4. **`get_job` / `get_registry` / `get_audit_entry`**: View methods for inspecting clustering state and hash-chained audit logs.

---

## 🧪 Running Local Tests

```bash
pip install -r requirements.txt
pytest test_cluster_engine.py -v
```

---

<div align="center">
  <p><i>Built for Decentralized AI & GenLayer Intelligent Contract Infrastructure</i></p>
</div>
