"""Textual TUI entry point for the URL Extractor.

Launches the app, wires UI actions (Add / Browse / Scan / Export / Clear) to
the ``extractor`` and ``io_utils`` modules, and supports a small command-line
interface for automation.
"""
from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
from collections import Counter
from pathlib import Path
from typing import Optional, Sequence

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Input,
    Label,
    ProgressBar,
    Select,
)

from extractor import SORT_KEYS, dedupe, extract_urls, sort_urls
from io_utils import (
    EXPORT_FORMATS,
    InputFileError,
    read_text_file,
    resolve_inputs,
    write_output,
)
from screens import FilePickerScreen
from ui import compose_layout


class URLExtractorApp(App):
    """Interactive URL extractor for ``.txt`` and ``.md`` files."""

    CSS_PATH = "app.tcss"
    TITLE = "URL Extractor"
    SUB_TITLE = "Extract URLs from .txt and .md files"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(
        self,
        initial_paths: Optional[Sequence[str]] = None,
        output_path: Optional[str] = None,
        dedupe_default: bool = True,
        overwrite_default: bool = False,
        sort_default: str = "original",
        format_default: str = "txt",
    ) -> None:
        super().__init__()
        self._initial_paths = list(initial_paths or [])
        self._initial_output = output_path
        self._dedupe_default = dedupe_default
        self._overwrite_default = overwrite_default
        self._sort_default = sort_default
        self._format_default = format_default
        self.files: list[Path] = []
        self.results: list[str] = []  # canonical scan-order list
        self._counts: Counter[str] = Counter()  # occurrences across all files

    # -- Composition ----------------------------------------------------
    def compose(self) -> ComposeResult:
        yield from compose_layout()

    def on_mount(self) -> None:
        table = self.query_one("#results", DataTable)
        table.add_columns("#", "URL", "Count")
        table.cursor_type = "row"
        table.zebra_stripes = True

        self.query_one("#dedupe", Checkbox).value = self._dedupe_default
        self.query_one("#overwrite", Checkbox).value = self._overwrite_default
        self.query_one("#sort", Select).value = self._sort_default
        self.query_one("#format", Select).value = self._format_default
        if self._initial_output:
            self.query_one("#output-input", Input).value = self._initial_output

        self.query_one("#progress", ProgressBar).display = False

        for raw in self._initial_paths:
            self._add_inputs(raw)
        self._refresh_file_list()
        if self.files:
            self._set_status(f"{len(self.files)} file(s) ready. Press Scan.")

    # -- Helpers --------------------------------------------------------
    def _set_status(self, message: str) -> None:
        self.query_one("#status", Label).update(message)

    def _add_file_path(self, path: Path) -> bool:
        """Add a resolved path to the file list, skipping duplicates."""
        if path in self.files:
            return False
        self.files.append(path)
        return True

    def _add_inputs(self, raw) -> tuple[int, Optional[str]]:
        """Resolve *raw* (file/dir/glob, possibly several quoted paths).

        Returns ``(added_count, last_error_message)``.
        """
        try:
            tokens = shlex.split(str(raw), posix=False)
        except ValueError:
            tokens = [str(raw)]
        if not tokens:
            tokens = [str(raw)]

        added = 0
        error: Optional[str] = None
        for token in tokens:
            try:
                for path in resolve_inputs(token):
                    if self._add_file_path(path):
                        added += 1
            except InputFileError as exc:
                error = str(exc)
        return added, error

    def _refresh_file_list(self) -> None:
        label = self.query_one("#file-list", Label)
        if not self.files:
            label.update("No files added yet.")
        else:
            label.update("\n".join(f"• {p}" for p in self.files))

    def _sorted_results(self) -> list[str]:
        key = self.query_one("#sort", Select).value
        return sort_urls(self.results, str(key), counts=self._counts)

    def _populate_results(self, urls: Sequence[str]) -> None:
        table = self.query_one("#results", DataTable)
        table.clear()
        for index, url in enumerate(urls, start=1):
            table.add_row(str(index), url, str(self._counts.get(url, 1)))

    # -- Event handlers -------------------------------------------------
    @on(Input.Submitted, "#path-input")
    @on(Button.Pressed, "#add")
    def handle_add(self) -> None:
        input_widget = self.query_one("#path-input", Input)
        raw = input_widget.value.strip()
        if not raw:
            self._set_status("Enter a file path, folder, or glob first.")
            return
        added, error = self._add_inputs(raw)
        if added:
            input_widget.value = ""
            self._refresh_file_list()
            self._set_status(f"Added {added} file(s).")
        elif error:
            self._set_status(f"[red]{error}[/red]")
        else:
            self._set_status("No new files added.")

    @on(Button.Pressed, "#browse")
    def handle_browse(self) -> None:
        self.push_screen(FilePickerScreen("."), self._on_picked)

    def _on_picked(self, path: Optional[str]) -> None:
        if not path:
            return
        added, error = self._add_inputs(path)
        if added:
            self._refresh_file_list()
            self._set_status(f"Added {Path(path).name}.")
        elif error:
            self._set_status(f"[red]{error}[/red]")

    def on_paste(self, event) -> None:
        """Treat pasted/dropped file paths as an Add action.

        Many terminals deliver a drag-and-dropped file as pasted text. If the
        paste resolves to real input files we add them and consume the event;
        otherwise we let it fall through to the focused widget as normal text.
        """
        text = getattr(event, "text", "").strip()
        if not text:
            return
        added, _ = self._add_inputs(text)
        if added:
            self._refresh_file_list()
            self._set_status(f"Added {added} file(s) (dropped).")
            event.stop()

    @on(Button.Pressed, "#scan")
    def handle_scan(self) -> None:
        if not self.files:
            self._set_status("Add at least one file before scanning.")
            return
        self._scan()

    @work(exclusive=True)
    async def _scan(self) -> None:
        progress = self.query_one("#progress", ProgressBar)
        progress.display = True
        progress.update(total=len(self.files), progress=0)
        self._set_status("Scanning…")

        raw_urls: list[str] = []
        errors: list[str] = []
        scanned = 0
        for path in self.files:
            try:
                text = await asyncio.to_thread(read_text_file, path)
            except InputFileError as exc:
                errors.append(str(exc))
            else:
                raw_urls.extend(extract_urls(text))
                scanned += 1
            progress.advance(1)
            await asyncio.sleep(0)  # yield so the bar repaints

        if self.query_one("#skip-empty", Checkbox).value:
            raw_urls = [u for u in raw_urls if u.strip()]

        self._counts = Counter(raw_urls)
        if self.query_one("#dedupe", Checkbox).value:
            self.results = dedupe(raw_urls)
        else:
            self.results = raw_urls

        self._populate_results(self._sorted_results())
        progress.display = False

        if not self.results:
            message = f"No URLs found in {scanned} file(s)."
        else:
            message = f"{len(self.results)} URLs found in {scanned} file(s)."
        if errors:
            message += f" [red]{len(errors)} error(s).[/red]"
        self._set_status(message)

    @on(Select.Changed, "#sort")
    def handle_sort_changed(self) -> None:
        if self.results:
            self._populate_results(self._sorted_results())

    @on(Button.Pressed, "#export")
    def handle_export(self) -> None:
        if not self.results:
            self._set_status("Nothing to export — scan some files first.")
            return
        out = self.query_one("#output-input", Input).value.strip()
        if not out:
            self._set_status("Choose an output path before exporting.")
            return
        fmt = str(self.query_one("#format", Select).value)
        overwrite = self.query_one("#overwrite", Checkbox).value
        try:
            written = write_output(
                out,
                self._sorted_results(),
                fmt=fmt,
                counts=self._counts,
                overwrite=overwrite,
            )
        except InputFileError as exc:
            self._set_status(f"[red]{exc}[/red]")
            return
        except OSError as exc:
            self._set_status(f"[red]Could not write file: {exc}[/red]")
            return
        self._set_status(f"Exported {len(self.results)} URLs to {written}.")

    @on(Button.Pressed, "#clear")
    def handle_clear(self) -> None:
        self.files.clear()
        self.results.clear()
        self._counts.clear()
        self.query_one("#results", DataTable).clear()
        self.query_one("#progress", ProgressBar).display = False
        self._refresh_file_list()
        self._set_status("Cleared.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract URLs from .txt and .md files in a Textual TUI."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Initial inputs: files, folders, or globs (.txt, .md).",
    )
    parser.add_argument("-o", "--output", help="Default output path.")
    parser.add_argument(
        "--dedupe", action="store_true", help="Enable deduplication by default."
    )
    parser.add_argument(
        "--no-dedupe", action="store_true", help="Disable deduplication by default."
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Allow overwriting the output file."
    )
    parser.add_argument(
        "--sort",
        choices=list(SORT_KEYS),
        default="original",
        help="Default result ordering.",
    )
    parser.add_argument(
        "--format",
        choices=sorted(EXPORT_FORMATS),
        default="txt",
        help="Default export format.",
    )
    args = parser.parse_args(argv)

    dedupe_default = not args.no_dedupe  # --dedupe is the default; --no-dedupe wins

    app = URLExtractorApp(
        initial_paths=args.paths,
        output_path=args.output,
        dedupe_default=dedupe_default,
        overwrite_default=args.overwrite,
        sort_default=args.sort,
        format_default=args.format,
    )
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
