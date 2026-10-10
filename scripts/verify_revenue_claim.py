#!/usr/bin/env python3
"""Structural PASS/FAIL for an aegis-analyst revenue claim against its cited sources.

Deterministic half of /verify-revenue-claim: compare claimed numbers with the cited
bev/summary and bev/trajectory excerpts. No network, no guessing.

Input (JSON on stdin or a file path argument):
  {"claim":   {"mrr": 1234.5, "currency": "USD", "paying_subscribers": 7,
               "signups": 3, "not_returned": ["signups"]},
   "sources": {"summary": {...bev/summary excerpt...}, "trajectory": {...}}}

Prints exactly one line, the reply to send back: "PASS: ..." or "FAIL: ...".
"""
from __future__ import annotations

import json
import re
import sys

MISSING = object()


def find(obj, key):
    """First value for `key` anywhere in a nested JSON excerpt (depth-first)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        children = obj.values()
    elif isinstance(obj, list):
        children = obj
    else:
        return MISSING
    for child in children:
        hit = find(child, key)
        if hit is not MISSING:
            return hit
    return MISSING


def number(value):
    if isinstance(value, bool) or value is None or value is MISSING:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(value))
    return float(m.group(0).replace(",", "")) if m else None


def source_mrr(summary):
    """MRR in major units from the summary excerpt: mrr_usd, else mrr_cents/100, else mrr_display."""
    for key, scale in (("mrr_usd", 1), ("mrr_cents", 100), ("mrr_display", 1)):
        n = number(find(summary, key))
        if n is not None:
            return n / scale
    return None


def fmt(n):
    return f"{n:g}" if n is not None else "?"


def check(payload) -> str:
    claim = payload.get("claim") if isinstance(payload, dict) else None
    sources = payload.get("sources") if isinstance(payload, dict) else None
    if not claim or not sources:
        return "FAIL: missing claim or sources"
    summary = sources.get("summary") or {}
    trajectory = sources.get("trajectory") or {}
    not_returned = set(claim.get("not_returned") or [])

    checked = []
    claimed_mrr = number(claim.get("mrr"))
    if claimed_mrr is not None:
        got = source_mrr(summary)
        if got is None:
            return f"FAIL: mrr claimed {fmt(claimed_mrr)} but source shows no MRR field"
        if abs(got - claimed_mrr) > 0.005:
            return f"FAIL: mrr claimed {fmt(claimed_mrr)} but source shows {fmt(got)}"
        currency = claim.get("currency")
        src_currency = find(summary, "currency")
        if currency and src_currency is not MISSING and str(src_currency).upper() != str(currency).upper():
            return f"FAIL: currency claimed {currency} but source shows {src_currency}"
        unit = currency or (src_currency if src_currency is not MISSING else "")
        checked.append(f"MRR {fmt(claimed_mrr)} {unit}".strip())

    for field, where in (("paying_subscribers", summary), ("signups", trajectory)):
        src = find(where, field)
        if field in not_returned:
            if src is not MISSING and src is not None:
                return f"FAIL: {field} claimed not returned by the API but source shows {src}"
            checked.append(f"{field} not returned")
            continue
        claimed = number(claim.get(field))
        if claimed is None:
            continue
        got = number(src) if src is not MISSING else None
        if got is None:
            return f"FAIL: {field} claimed {fmt(claimed)} but source shows no {field} field"
        if got != claimed:
            return f"FAIL: {field} claimed {fmt(claimed)} but source shows {fmt(got)}"
        checked.append(f"{field} {fmt(claimed)}")

    if not checked:
        return "FAIL: missing claim or sources"
    return f"PASS: claim matches cited sources ({', '.join(checked)})"


def main(argv):
    raw = open(argv[1]).read() if len(argv) > 1 else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("FAIL: missing claim or sources")
        return 0
    print(check(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
