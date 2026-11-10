#!/usr/bin/env python3
"""Conservative, auditable stance proposals; not approved views or investment advice."""
import argparse
import csv
import datetime as dt
import re
from pathlib import Path

POS = re.compile(r"\b(overweight|positive|bullish|favor|favour|prefer|constructive|sovrappes(?:o|are)|positiv[io]|rialzist[ao])\b", re.I)
NEG = re.compile(r"\b(underweight|negative|bearish|avoid|cautious|sottopes(?:o|are)|negativ[ao]|ribassist[ao])\b", re.I)
NEU = re.compile(r"\b(neutral|market.weight|in.line|neutrale)\b", re.I)
NEGATION = re.compile(r"\b(not|no|never|non|without|senza)\b",re.I)
FIELDS=["institution_name","document_url","asset_class","evidence_excerpt","proposed_stance",
        "confidence_score","confidence_reason","conflict_status","review_status","checked_at_utc"]

def infer(row):
    text=(row.get("evidence_excerpt") or "").strip()
    hits=[(name,pattern.search(text)) for name,pattern in (("positive",POS),("negative",NEG),("neutral",NEU))]
    found=[(name,m) for name,m in hits if m]
    if not found:
        return "","0","no_explicit_direction","no_direction"
    if len(found)!=1:
        return "","0","contradictory_direction_terms","mixed_terms"
    name,match=found[0]
    prefix=text[max(0,match.start()-30):match.start()]
    if NEGATION.search(prefix.split(",")[-1].split(".")[-1]):
        return "","0","negation_near_direction","negated"
    # Single keyword in a short excerpt is weak evidence, not a verified view.
    return name,"30","single_explicit_keyword_requires_context_review","single_direction"

def run(root):
    with (root/"document_topic_evidence.csv").open(newline="",encoding="utf-8-sig") as f:
        evidence=list(csv.DictReader(f))
    rows=[]
    for item in evidence:
        stance,confidence,reason,signal=infer(item)
        rows.append({**{k:item.get(k,"") for k in FIELDS},
                     "proposed_stance":stance,"confidence_score":confidence,
                     "confidence_reason":reason,"conflict_status":signal,
                     "review_status":"pending_independent_source_review"})
    grouped={}
    for row in rows:
        key=(row["institution_name"],row["asset_class"])
        grouped.setdefault(key,set())
        if row["proposed_stance"]: grouped[key].add(row["proposed_stance"])
    for row in rows:
        if len(grouped[(row["institution_name"],row["asset_class"])])>1:
            row["conflict_status"]="conflicting_documents"
            row["confidence_score"]="0"
            row["review_status"]="manual_conflict_resolution_required"
    with (root/"stance_proposals.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows,key=lambda r:(r["institution_name"],r["asset_class"],r["document_url"])))
    print(f"Stance proposals: {len(rows)} evidence rows; {sum(bool(r['proposed_stance']) for r in rows)} weak directional hypotheses; zero independently approved views.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dir",default=".")
    args=p.parse_args()
    run(Path(args.dir))
