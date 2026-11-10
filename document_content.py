#!/usr/bin/env python3
"""Conservative document text extraction. No investment stance is validated here."""
import hashlib
import io
import re
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

MAX_PDF_BYTES = 5_000_000
MAX_PDF_PAGES = 12

def extract_pdf(url):
    from pypdf import PdfReader
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; GlobalOutlookResearch/3.4)",
                                "Accept":"application/pdf"})
    with urlopen(req, timeout=12) as response:
        final = response.geturl()
        p = urlsplit(final)
        if p.scheme != "https" or not p.hostname or p.username or p.password:
            return ("unsafe_redirect", "", "", "")
        mime = response.headers.get("Content-Type", "").lower()
        raw = response.read(MAX_PDF_BYTES+1)
    if len(raw)>MAX_PDF_BYTES:
        return ("pdf_too_large", "", "", "")
    if not raw.startswith(b"%PDF-") or ("pdf" not in mime and not p.path.lower().endswith(".pdf")):
        return ("not_pdf", "", "", "")
    try:
        reader = PdfReader(io.BytesIO(raw), strict=False)
        if reader.is_encrypted:
            return ("pdf_encrypted", "", "", "")
        parts=[]
        for page in reader.pages[:MAX_PDF_PAGES]:
            parts.append(page.extract_text() or "")
        text=re.sub(r"\s+", " ", " ".join(parts)).strip()
        if not text:
            return ("pdf_no_extractable_text", "", "", "")
        return ("pdf_read", "", "", text[:6000])
    except Exception:
        return ("pdf_parse_error", "", "", "")
