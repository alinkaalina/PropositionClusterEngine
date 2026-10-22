"""
Unit test suite for PropositionClusterEngine deterministic helper functions.
Validates schema parsing, canonical ordering, transitive graph clustering, and contradiction guards.
"""
import json
import re
import pytest

VERDICTS = ("SYNONYMOUS", "DIVERGENT", "AMBIGUOUS")


def no_duplicate_keys(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate JSON key detected")
        out[k] = v
    return out


def parse_claim_bundle(raw_text):
    try:
        parsed = json.loads(raw_text, object_pairs_hook=no_duplicate_keys)
    except (ValueError, TypeError):
        return None
    if type(parsed) is not dict or set(parsed) != {"entries"} or type(parsed["entries"]) is not list:
        return None
    items = parsed["entries"]
    if not 2 <= len(items) <= 6:
        return None
    seen_ids = set()
    for item in items:
        if (type(item) is not dict or set(item) != {"id", "statement"} or type(item["id"]) is not str
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}", item["id"]) is None
                or item["id"] in seen_ids or type(item["statement"]) is not str
                or not 8 <= len(item["statement"]) <= 600 or item["statement"] != item["statement"].strip()
                or "\x00" in item["statement"]):
            return None
        seen_ids.add(item["id"])
    return sorted(items, key=lambda x: x["id"])


def parse_pair_verdicts(raw_val, expected_len):
    if type(raw_val) is str:
        try:
            raw_val = json.loads(raw_val, object_pairs_hook=no_duplicate_keys)
        except (ValueError, TypeError):
            return None
    if type(raw_val) is not dict or set(raw_val) != {"verdicts"}:
        return None
    verdicts = raw_val["verdicts"]
    if (type(verdicts) is not list or len(verdicts) != expected_len
            or any(type(v) is not str or v not in VERDICTS for v in verdicts)):
        return None
    return verdicts


def build_equivalence_clusters(items, verdicts):
    n = len(items)
    if parse_pair_verdicts({"verdicts": verdicts}, n * (n - 1) // 2) is None:
        raise ValueError("malformed pairwise verdict array")
    if "AMBIGUOUS" in verdicts:
        return {"state": "ISOLATED", "clusters": [], "anchor_map": {}, "reason": "AMBIGUOUS_PAIR"}

    adj = [[i == j for j in range(n)] for i in range(n)]
    cursor = 0
    for i in range(n):
        for j in range(i + 1, n):
            adj[i][j] = adj[j][i] = verdicts[cursor] == "SYNONYMOUS"
            cursor += 1
            if items[i]["statement"] == items[j]["statement"] and not adj[i][j]:
                return {"state": "CONTRADICTORY", "clusters": [], "anchor_map": {}, "reason": "IDENTICAL_STATEMENT_MISMATCH"}

    for i in range(n):
        for j in range(n):
            for k in range(n):
                if adj[i][j] and adj[j][k] and not adj[i][k]:
                    return {"state": "CONTRADICTORY", "clusters": [], "anchor_map": {}, "reason": "TRANSITIVITY_VIOLATION"}

    clusters, anchor_map = [], {}
    for i, item in enumerate(items):
        if item["id"] in anchor_map:
            continue
        member_ids = [items[j]["id"] for j in range(n) if adj[i][j]]
        cluster = {
            "anchor_id": item["id"],
            "member_ids": member_ids,
            "size": len(member_ids),
            "statement": item["statement"],
        }
        clusters.append(cluster)
        for mid in member_ids:
            anchor_map[mid] = item["id"]

    return {"state": "CLUSTERED", "clusters": clusters, "anchor_map": anchor_map, "reason": "TRANSITIVE_EQUIVALENCE"}


def test_canonical_sorting_on_parse():
    payload = json.dumps({
        "entries": [
            {"id": "claim_b", "statement": "Protocol fee is capped at 30 basis points."},
            {"id": "claim_a", "statement": "Maximum protocol fee equals 0.30 percent."},
        ]
    })
    parsed = parse_claim_bundle(payload)
    assert parsed is not None
    assert [x["id"] for x in parsed] == ["claim_a", "claim_b"]


def test_transitive_clustering_success():
    items = [
        {"id": "c1", "statement": "Staking lockup lasts 14 days."},
        {"id": "c2", "statement": "Validators must lock tokens for two weeks."},
        {"id": "c3", "statement": "Governance quorum is 5 percent."},
    ]
    # Pairs: (c1,c2)=SYNONYMOUS, (c1,c3)=DIVERGENT, (c2,c3)=DIVERGENT
    verdicts = ["SYNONYMOUS", "DIVERGENT", "DIVERGENT"]
    res = build_equivalence_clusters(items, verdicts)
    assert res["state"] == "CLUSTERED"
    assert len(res["clusters"]) == 2
    assert res["anchor_map"]["c2"] == "c1"
    assert res["anchor_map"]["c3"] == "c3"


def test_non_transitive_rejected():
    items = [
        {"id": "c1", "statement": "Statement A is valid here."},
        {"id": "c2", "statement": "Statement B is valid here."},
        {"id": "c3", "statement": "Statement C is valid here."},
    ]
    # (c1,c2)=SYNONYMOUS, (c1,c3)=DIVERGENT, (c2,c3)=SYNONYMOUS -> Violates transitivity
    verdicts = ["SYNONYMOUS", "DIVERGENT", "SYNONYMOUS"]
    res = build_equivalence_clusters(items, verdicts)
    assert res["state"] == "CONTRADICTORY"
    assert res["reason"] == "TRANSITIVITY_VIOLATION"


def test_ambiguous_pair_isolates_job():
    items = [
        {"id": "c1", "statement": "The settlement window closes at midnight UTC."},
        {"id": "c2", "statement": "It closes at 00:00 UTC sharp."},
    ]
    res = build_equivalence_clusters(items, ["AMBIGUOUS"])
    assert res["state"] == "ISOLATED"
    assert res["reason"] == "AMBIGUOUS_PAIR"
