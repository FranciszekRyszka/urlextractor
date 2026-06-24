"""Safe reading of input files and writing of the extracted URL list."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

SUPPORTED_EXTENSIONS = {".txt", ".md"}

PathLike = Union[str, Path]


class InputFileError(Exception):
    """Raised when an input/output file is missing or has an invalid type."""


def validate_input_file(path: PathLike) -> Path:
    """Validate that *path* exists and is a supported text file.

    Returns the resolved :class:`Path` or raises :class:`InputFileError`.
    """
    p = Path(path)
    if not p.exists():
        raise InputFileError(f"File not found: {p}")
    if not p.is_file():
        raise InputFileError(f"Not a file: {p}")
    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        expected = " or ".join(sorted(SUPPORTED_EXTENSIONS))
        raise InputFileError(
            f"Unsupported file type '{p.suffix}': {p.name} (expected {expected})"
        )
    return p


def read_text_file(path: PathLike) -> str:
    """Read a validated input file as UTF-8 text.

    Decoding errors are replaced rather than raised so a single stray byte
    never aborts a scan.
    """
    p = validate_input_file(path)
    return p.read_text(encoding="utf-8", errors="replace")


def write_urls(path: PathLike, urls: Iterable[str], *, overwrite: bool = False) -> Path:
    """Write *urls* to *path*, one per line, encoded as UTF-8.

    Raises :class:`InputFileError` if the file already exists and *overwrite*
    is false.
    """
    p = Path(path)
    if p.exists() and not overwrite:
        raise InputFileError(f"Output file already exists: {p} (enable overwrite)")
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    urls = list(urls)
    content = "\n".join(urls)
    if urls:
        content += "\n"  # trailing newline so the file ends cleanly
    p.write_text(content, encoding="utf-8")
    return p
