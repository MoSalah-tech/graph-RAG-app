import os
from pathlib import Path
from edgar import Company, set_identity
from app.core.config import settings

set_identity(settings.SEC_IDENTITY)

CACHE_DIR = Path("data/filings")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_10k_text(ticker: str, use_cache: bool = True) -> str | None:
    """
    Fetch the latest 10-K text for a ticker.
    Caches the result to data/filings/{ticker}_10k.txt.
    """
    cache_file = CACHE_DIR / f"{ticker}_10k.txt"

    if use_cache and cache_file.exists():
        print(f"  [cache] {ticker}")
        return cache_file.read_text(encoding="utf-8")

    try:
        company = Company(ticker)
        filings = company.get_filings(form="10-K")
        if not filings:
            print(f"  [skip] no 10-K for {ticker}")
            return None

        latest = filings[0]
        print(f"  [fetch] {ticker} — filed {latest.filing_date}")
        text = latest.text()

        cache_file.write_text(text, encoding="utf-8")
        return text

    except Exception as e:
        print(f"  [error] {ticker}: {e}")
        return None