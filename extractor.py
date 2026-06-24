"""URL extraction, cleaning, and deduplication.

The regex lives here, in one place, so it can be improved later without
touching the rest of the app.
"""
from __future__ import annotations

import re
from typing import Iterable

# Match http(s) URLs, stopping at whitespace and a few obvious delimiters.
# Trailing punctuation is handled separately by ``clean_url``.
URL_PATTERN = re.compile(r'https?://[^\s<>"]+')

# Characters that commonly cling to the end of a URL in prose but are not
# part of it (sentence punctuation, closing brackets, quotes).
_TRAILING_PUNCT = ".,;:!?)]}>\"'"


def clean_url(url: str) -> str:
    """Strip trailing punctuation that regularly clings to URLs in prose."""
    return url.rstrip(_TRAILING_PUNCT)


def extract_urls(text: str) -> list[str]:
    """Return all URLs found in *text*, cleaned of trailing punctuation."""
    return [clean_url(match) for match in URL_PATTERN.findall(text)]


def dedupe(urls: Iterable[str], *, preserve_order: bool = True) -> list[str]:
    """Remove duplicate URLs.

    With *preserve_order* (the default) the first occurrence wins and the
    original ordering is kept; otherwise the result is sorted.
    """
    if not preserve_order:
        return sorted(set(urls))
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result
