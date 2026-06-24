"""Safe reading of input files, input resolution, and multi-format export."""
from __future__ import annotations

import csv
import glob as globmod
import json
from io import StringIO
from pathlib import Path
from typing import Iterable, Mapping, Optional, Union

SUPPORTED_EXTENSIONS = {".txt", ".md"}

# Export formats and the extension each one expects.
EXPORT_FORMATS = {"txt", "csv", "json", "md"}
_FORMAT_EXT = {"txt": ".txt", "csv": ".csv", "json": ".json", "md": ".md"}

_GLOB_CHARS = set("*?[")

PathLike = Union[str, Path]


class InputFileError(Exception):
    """Raised when an input/output path is missing or has an invalid type."""


def validate_input_file(path: PathLike) -> Path:
    """Validate that *path* exists and is a supported text file.

    Returns the :class:`Path` or raises :class:`InputFileError`.
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


def resolve_inputs(raw: PathLike) -> list[Path]:
    """Expand *raw* into a list of supported input files.

    Handles three cases:

    - a **directory** -> all supported files found recursively inside it;
    - a **glob pattern** (contains ``*``, ``?`` or ``[``) -> matching files;
    - a single **file** -> validated and returned as a one-item list.

    Surrounding quotes (as added by terminals on drag-and-drop) are stripped.
    Raises :class:`InputFileError` if nothing usable is found.
    """
    text = str(raw).strip().strip('"').strip("'").strip()
    if not text:
        raise InputFileError("Empty path.")

    p = Path(text)
    if p.is_dir():
        files = sorted(
            f
            for f in p.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            raise InputFileError(f"No .txt or .md files in directory: {p}")
        return files

    if any(c in text for c in _GLOB_CHARS):
        matches = sorted(Path(m) for m in globmod.glob(text, recursive=True))
        files = [
            m
            for m in matches
            if m.is_file() and m.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        if not files:
            raise InputFileError(f"No .txt or .md files match: {text}")
        return files

    return [validate_input_file(p)]


def read_text_file(path: PathLike) -> str:
    """Read a validated input file as UTF-8 text.

    Decoding errors are replaced rather than raised so a single stray byte
    never aborts a scan.
    """
    p = validate_input_file(path)
    return p.read_text(encoding="utf-8", errors="replace")


def ensure_extension(path: PathLike, fmt: str) -> Path:
    """Return *path* with the extension matching export format *fmt*."""
    p = Path(path)
    want = _FORMAT_EXT.get(fmt, ".txt")
    if p.suffix.lower() != want:
        p = p.with_suffix(want)
    return p


def _render(urls: list[str], fmt: str, counts: Mapping[str, int]) -> str:
    """Serialize *urls* to a string in the requested *fmt*."""
    if fmt == "txt":
        body = "\n".join(urls)
        return body + "\n" if urls else ""
    if fmt == "md":
        body = "\n".join(f"- [{u}]({u})" for u in urls)
        return body + "\n" if urls else ""
    if fmt == "csv":
        buf = StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["url", "count"])
        for u in urls:
            writer.writerow([u, counts.get(u, 1)])
        return buf.getvalue()
    if fmt == "json":
        data = [{"url": u, "count": counts.get(u, 1)} for u in urls]
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    raise InputFileError(f"Unknown export format: {fmt}")


def write_output(
    path: PathLike,
    urls: Iterable[str],
    *,
    fmt: str = "txt",
    counts: Optional[Mapping[str, int]] = None,
    overwrite: bool = False,
) -> Path:
    """Write *urls* to *path* in format *fmt*, encoded as UTF-8.

    The output extension is normalized to match *fmt*. Raises
    :class:`InputFileError` if the target exists and *overwrite* is false.
    """
    if fmt not in EXPORT_FORMATS:
        raise InputFileError(f"Unknown export format: {fmt}")

    urls = list(urls)
    counts = counts or {}
    p = ensure_extension(path, fmt)
    if p.exists() and not overwrite:
        raise InputFileError(f"Output file already exists: {p} (enable overwrite)")
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    p.write_text(_render(urls, fmt, counts), encoding="utf-8")
    return p
