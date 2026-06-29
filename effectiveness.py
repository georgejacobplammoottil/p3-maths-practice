#!/usr/bin/env python3
"""
effectiveness.py — Intervention effectiveness analysis
======================================================
Run from the project root:
    python effectiveness.py

Reads sessions.db (local or Render path) and taxonomy.json.
Prints three tables:
  1. Per-abstract-misconception-type: N, mean pre/post/retention, mean lift, mean retention lift
  2. Per-structure-id: same metrics, for debugging individual question types
  3. Students needing attention: anyone with a pending intervention older than 7 days
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = pathlib.Path(__file__).parent
_render_data = pathlib.Path("/opt/render/project/src/data")
DB_PATH      = (_render_data if _render_data.exists() else BASE / "data") / "sessions.db"
TAXONOMY_PATH = BASE / "question_banks" / "P3" / "taxonomy.json"

# ── Load taxonomy ─────────────────────────────────────────────────────────────
if not TAXONOMY_PATH.exists():
    print(f"ERROR: taxonomy not found at {TAXONOMY_PATH}")
    sys.exit(1)

tx = json.loads(TAXONOMY_PATH.read_text())
STRUCTURE_ID_MAP = tx.get("structure_id_map", {})
ABSTRACT_TYPES   = tx.get("abstract_misconception_types", {})

# ── DB connection ─────────────────────────────────────────────────────────────
if not DB_PATH.exists():
    print(f"ERROR: database not found at {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# ── Pull all completed interventions ──────────────────────────────────────────
rows = conn.execute(
    """SELECT i.structure_id, i.pre_score, i.post_score, i.retention_score,
              i.created_at, i.completed_at, s.name AS student_name
       FROM interventions i
       JOIN students s ON s.id = i.student_id
       WHERE i.completed_at IS NOT NULL"""
).fetchall()

pending = conn.execute(
    """SELECT i.structure_id, i.pre_score, i.created_at, s.name AS student_name
       FROM interventions i
       JOIN students s ON s.id = i.student_id
       WHERE i.completed_at IS NULL
       ORDER BY i.created_at"""
).fetchall()

conn.close()

# ── Aggregate ─────────────────────────────────────────────────────────────────
def mean(vals):
    clean = [v for v in vals if v is not None]
    return sum(clean) / len(clean) if clean else None

def fmt(v, pct=True):
    if v is None: return "  —  "
    if pct: return f"{v*100:5.1f}%"
    return f"{v:5.2f}"

by_abstract: dict[str, list] = defaultdict(list)
by_structure: dict[str, list] = defaultdict(list)

for r in rows:
    sid = r["structure_id"]
    entry = dict(r)
    abstract_type = STRUCTURE_ID_MAP.get(sid, {}).get("abstract_type", "UNMAPPED")
    by_abstract[abstract_type or "UNMAPPED"].append(entry)
    by_structure[sid].append(entry)

# ── Table printer ─────────────────────────────────────────────────────────────
def print_table(title: str, groups: dict[str, list], label_fn):
    print(f"\n{'='*90}")
    print(f"  {title}")
    print(f"{'='*90}")
    print(f"  {'Label':<38} {'N':>3}  {'Pre':>6}  {'Post':>6}  {'Lift':>6}  {'Retain':>6}  {'RetLift':>7}")
    print(f"  {'-'*38} {'-'*3}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*7}")

    for key, entries in sorted(groups.items()):
        pre_vals  = [e["pre_score"]       for e in entries]
        post_vals = [e["post_score"]      for e in entries]
        ret_vals  = [e["retention_score"] for e in entries]
        mp = mean(pre_vals)
        mpo = mean(post_vals)
        mr  = mean(ret_vals)
        lift = (mpo - mp) if (mp is not None and mpo is not None) else None
        ret_lift = (mr - mp) if (mp is not None and mr is not None) else None
        label = label_fn(key)[:38]
        flag = " ⚠" if (mpo is not None and mpo < 0.6) else ""
        print(f"  {label:<38} {len(entries):>3}  {fmt(mp)}  {fmt(mpo)}  {fmt(lift)}  {fmt(mr)}  {fmt(ret_lift)}{flag}")

    print()

print_table(
    "BY ABSTRACT MISCONCEPTION TYPE  (⚠ = post_score < 60%, intervention may need redesign)",
    by_abstract,
    lambda k: ABSTRACT_TYPES.get(k, {}).get("label", k),
)

print_table(
    "BY STRUCTURE ID",
    by_structure,
    lambda k: k,
)

# ── Pending interventions ─────────────────────────────────────────────────────
print(f"\n{'='*90}")
print(f"  PENDING INTERVENTIONS  (not yet completed)")
print(f"{'='*90}")
if not pending:
    print("  None — all triggered interventions have been completed.\n")
else:
    now = datetime.now(timezone.utc)
    print(f"  {'Student':<16} {'Structure ID':<40} {'Pre':>6}  {'Created'}")
    print(f"  {'-'*16} {'-'*40} {'-'*6}  {'-'*20}")
    for p in pending:
        created = p["created_at"]
        print(f"  {p['student_name']:<16} {p['structure_id']:<40} {fmt(p['pre_score'])}  {created}")
    print()

# ── Summary ───────────────────────────────────────────────────────────────────
n_completed = len(rows)
n_with_retention = sum(1 for r in rows if r["retention_score"] is not None)
print(f"  Completed interventions : {n_completed}")
print(f"  With retention data     : {n_with_retention}")
print(f"  Pending                 : {len(pending)}")
print(f"  DB path                 : {DB_PATH}\n")

if n_completed < 20:
    print(f"  NOTE: Only {n_completed} completed interventions — statistics are not yet reliable.")
    print(f"  Aim for ≥20 per abstract_type before re-ranking intervention_types_ranked in taxonomy.json.\n")
