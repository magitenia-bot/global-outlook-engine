#!/usr/bin/env python3
"""Collect auditable snippets from official HTML candidates, without inferring stances."""
import argparse
import csv
import datetime as dt
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from document_content import extract_pdf

FIELDS = ["institution_name", "document_url", "candidate_title", "publication_date",
          "checked_at_utc", "fetch_status", "page_title", "page_description",
          "text_excerpt", "evidence_status"]
MAX_BYTES = 400_000

class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.title_depth = 0
        self.title = []
        self.text = []
        self.description = ""
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "nav", "footer", "header"):
            self.skip += 1
        if tag == "title":
            self.title_depth += 1
        if tag == "meta":
            a = dict(attrs)
            if (a.get("name", "").lower() == "description" or
                a.get("property", "").lower() == "og:description"):
                self.description = self.description or a.get("content", "")
    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "nav", "footer", "header"):
            self.skip = max(0, self.skip - 1)
        if tag == "title":
            self.title_depth = max(0, self.title_depth - 1)
    def handle_data(self, data):
        s = " ".join(data.split())
        if not s:
            return
        if self.title_depth:
            self.title.append(s)
        if not self.skip and len(" ".join(self.text)) < 6000:
            self.text.append(s)

def safe_url(url):
    p = urlsplit(url)
    return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password

def inspect(url):
    if not safe_url(url):
        return ("invalid_url", "", "", "")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; GlobalOutlookResearch/3.3)", "Accept": "text/html"})
    try:
        with urlopen(req, timeout=6) as res:
            if not safe_url(res.geturl()):
                return ("unsafe_redirect", "", "", "")
            if "html" not in res.headers.get("Content-Type", "").lower():
                return ("non_html", "", "", "")
            raw = res.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return ("too_large", "", "", "")
            p = Extractor()
            p.feed(raw.decode(res.headers.get_content_charset() or "utf-8", errors="replace"))
            return ("html_read", " ".join(p.title)[:250], p.description[:800], " ".join(p.text)[:3000])
    except Exception as exc:
        return ("fetch_error_" + type(exc).__name__, "", "", "")

def run(root, max_checks=12):
    src = root / "view_review_queue.csv"
    if not src.exists():
        raise FileNotFoundError(src)
    with src.open(newline="", encoding="utf-8-sig") as f:
        candidates = list(csv.DictReader(f))
    target = root / "document_evidence.csv"
    old = {}
    if target.exists():
        with target.open(newline="", encoding="utf-8-sig") as f:
            old = {r["document_url"]: r for r in csv.DictReader(f) if r.get("document_url")}
    priority = {"priority_manual_review": 0, "priority_unclassified_review": 1}
    candidates.sort(key=lambda r: (priority.get(r.get("selection_status"), 2),
                                   old.get(r.get("document_url", ""), {}).get("checked_at_utc", ""),
                                   r.get("institution_name", "")))
    count = 0
    for r in candidates:
        url = (r.get("document_url") or "").strip()
        if not url or not safe_url(url) or (r.get("source_status") == "candidate_low_quality_metadata"):
            continue
        if count >= max_checks:
            break
        count += 1
        status, title, desc, excerpt = (extract_pdf(url) if urlsplit(url).path.lower().endswith(".pdf") else inspect(url))
        old[url] = {
            "institution_name": r.get("institution_name", ""),
            "document_url": url,
            "candidate_title": r.get("candidate_title", ""),
            "publication_date": r.get("publication_date", ""),
            "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "fetch_status": status, "page_title": title,
            "page_description": desc, "text_excerpt": excerpt,
            "evidence_status": "unverified_excerpt_requires_review",
        }
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(old[k] for k in sorted(old))
    print(f"Evidence collected/checked: {count}; archived: {len(old)}. No stances approved.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default=".")
    p.add_argument("--max-checks", type=int, default=12)
    a = p.parse_args()
    run(Path(a.dir), max(0, a.max_checks))
