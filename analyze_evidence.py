#!/usr/bin/env python3
"""Extract auditable topic-linked passages; NEVER approve or infer investment stances."""
import argparse
import csv
import re
from pathlib import Path

TOPICS = {
    "Equity": r"\b(equit(?:y|ies)|stocks?|azion(?:i|ario)|shares?)\b",
    "Government bonds": r"\b(treasur(?:y|ies)|sovereign bonds?|government bonds?|titoli di stato|bunds?)\b",
    "Credit": r"\b(credit|corporate bonds?|high.yield|investment.grade|obbligazion(?:i|ario))\b",
    "Emerging markets": r"\b(emerging markets?|mercati emergenti|EM equities)\b",
    "Currencies": r"\b(currencies|currency|foreign exchange|dollar|euro|valute|fx)\b",
    "Commodities": r"\b(commodit(?:y|ies)|gold|oil|oro|petrolio|materie prime)\b",
}
FIELDS = ["institution_name","document_url","asset_class","evidence_excerpt",
          "extraction_status","proposed_stance","review_status","checked_at_utc"]

def evidence_rows(source):
    text = " ".join((source.get("text_excerpt") or "").split())
    if source.get("fetch_status") not in ("html_read","pdf_read") or len(text)<40:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out=[]
    for topic,pattern in TOPICS.items():
        sentence = next((s for s in sentences if re.search(pattern,s,re.I) and 35<=len(s)<=650),None)
        if sentence:
            out.append({"institution_name":source.get("institution_name",""),
                        "document_url":source.get("document_url",""),"asset_class":topic,
                        "evidence_excerpt":sentence[:650],
                        "extraction_status":"topic_sentence_unverified",
                        "proposed_stance":"","review_status":"pending_human_interpretation",
                        "checked_at_utc":source.get("checked_at_utc","")})
    return out

def run(root):
    src=root/"document_evidence.csv"
    with src.open(newline="",encoding="utf-8-sig") as f:
        evidence=list(csv.DictReader(f))
    records={}
    for item in evidence:
        for row in evidence_rows(item):
            records[(row["document_url"],row["asset_class"])]=row
    with (root/"document_topic_evidence.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(records.values(),key=lambda r:(r["institution_name"],r["asset_class"],r["document_url"])))
    print(f"Extracted {len(records)} topic-linked passages from {len(evidence)} archived document records; zero investment stances approved.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dir",default=".")
    args=p.parse_args()
    run(Path(args.dir))
