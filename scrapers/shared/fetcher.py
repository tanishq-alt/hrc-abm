"""Shared page/PDF fetcher for all HR Intel scrapers."""
import requests
from bs4 import BeautifulSoup

try:
    from pdfminer.high_level import extract_text as pdf_extract
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LeadIntel/1.0)"}


def fetch_text(url: str, timeout: int = 12) -> str:
    """Fetch a URL and return cleaned text (up to 5000 chars).

    Handles HTML pages and PDFs. Returns empty string on error.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code != 200:
            return ""
        ct = r.headers.get("content-type", "")
        if "pdf" in ct and HAS_PDF:
            import io
            return pdf_extract(io.BytesIO(r.content))[:5000]
        if "html" in ct or url.lower().endswith(".html") or url.lower().endswith(".htm"):
            soup = BeautifulSoup(r.text, "lxml")
            for t in soup(["script", "style", "nav", "footer"]):
                t.decompose()
            return soup.get_text(" ", strip=True)[:5000]
        # Generic fallback (plain text, etc.)
        return r.text[:3000]
    except Exception:
        return ""
