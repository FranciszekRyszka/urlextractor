"""URL extraction, cleaning, deduplication, and sorting.

The regex lives here, in one place, so it can be improved later without
touching the rest of the app.
"""
from __future__ import annotations

import re
from typing import Iterable, Mapping, Optional
from urllib.parse import urlparse

# Match http(s) URLs, stopping at whitespace and a few obvious delimiters.
# Trailing punctuation is handled separately by ``clean_url``.
URL_PATTERN = re.compile(r'https?://[^\s<>"]+')

# Characters that commonly cling to the end of a URL in prose but are not
# part of it (sentence punctuation, closing brackets, quotes).
_TRAILING_PUNCT = ".,;:!?)]}>\"'"

# Sort keys accepted by ``sort_urls`` / the ``--sort`` CLI option.
SORT_KEYS = ("original", "az", "za", "domain", "frequency")


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


def domain_of(url: str) -> str:
    """Return the lowercased host of *url* (empty string if unparseable)."""
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


def sort_urls(
    urls: Iterable[str],
    key: str = "original",
    *,
    counts: Optional[Mapping[str, int]] = None,
) -> list[str]:
    """Return *urls* ordered according to *key*.

    Keys: ``original`` (as given), ``az`` / ``za`` (alphabetical), ``domain``
    (grouped by host), ``frequency`` (most-seen first, needs *counts*).
    """
    urls = list(urls)
    if key == "az":
        return sorted(urls, key=str.lower)
    if key == "za":
        return sorted(urls, key=str.lower, reverse=True)
    if key == "domain":
        return sorted(urls, key=lambda u: (domain_of(u), u.lower()))
    if key == "frequency":
        counts = counts or {}
        return sorted(urls, key=lambda u: (-counts.get(u, 1), u.lower()))
    return urls  # "original" or unknown -> unchanged
