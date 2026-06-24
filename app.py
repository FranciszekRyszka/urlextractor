"""Textual TUI entry point for the URL Extractor.

Launches the app, wires UI actions (Add / Scan / Export / Clear) to the
``extractor`` and ``io_utils`` modules, and supports a small command-line
interface for automation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button, Checkbox, DataTable, Input, Label

from extractor import dedupe, extract_urls
from io_utils import InputFileError, read_text_file, validate_input_file, write_urls
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
    ) -> None:
        super().__init__()
        self._initial_paths = list(initial_paths or [])
        self._initial_output = output_path
        self._dedupe_default = dedupe_default
        self._overwrite_default = overwrite_default
        self.files: list[Path] = []
        self.results: list[str] = []

    # -- Composition ----------------------------------------------------
    def compose(self) -> ComposeResult:
        yield from compose_layout()

    def on_mount(self) -> None:
        table = self.query_one("#results", DataTable)
        table.add_columns("#", "URL")
        table.cursor_type = "row"
        table.zebra_stripes = True

        self.query_one("#dedupe", Checkbox).value = self._dedupe_default
        self.query_one("#overwrite", Checkbox).value = self._overwrite_default
        if self._initial_output:
            self.query_one("#output-input", Input).value = self._initial_output

        for path in self._initial_paths:
            self._add_file(path)
        self._refresh_file_list()
        if self.files:
            self._set_status(f"{len(self.files)} file(s) ready. Press Scan.")

    # -- Helpers --------------------------------------------------------
    def _set_status(self, message: str) -> None:
        self.query_one("#status", Label).update(message)

    def _add_file(self, raw_path) -> bool:
        try:
            path = validate_input_file(raw_path)
        except InputFileError as exc:
            self._set_status(f"[red]{exc}[/red]")
            return False
        if path in self.files:
            self._set_status(f"Already added: {path.name}")
            return False
        self.files.append(path)
        return True

    def _refresh_file_list(self) -> None:
        label = self.query_one("#file-list", Label)
        if not self.files:
            label.update("No files added yet.")
        else:
            label.update("\n".join(f"• {p}" for p in self.files))

    def _populate_results(self, urls: Sequence[str]) -> None:
        table = self.query_one("#results", DataTable)
        table.clear()
        for index, url in enumerate(urls, start=1):
            table.add_row(str(index), url)

    # -- Event handlers -------------------------------------------------
    @on(Input.Submitted, "#path-input")
    @on(Button.Pressed, "#add")
    def handle_add(self) -> None:
        input_widget = self.query_one("#path-input", Input)
        raw = input_widget.value.strip()
        if not raw:
            self._set_status("Enter a file path first.")
            return
        if self._add_file(raw):
            self._set_status(f"Added {Path(raw).name}.")
            input_widget.value = ""
            self._refresh_file_list()

    @on(Button.Pressed, "#scan")
    def handle_scan(self) -> None:
        if not self.files:
            self._set_status("Add at least one file before scanning.")
            return

        all_urls: list[str] = []
        errors: list[str] = []
        scanned = 0
        for path in self.files:
            try:
                text = read_text_file(path)
            except InputFileError as exc:
                errors.append(str(exc))
                continue
            all_urls.extend(extract_urls(text))
            scanned += 1

        if self.query_one("#skip-empty", Checkbox).value:
            all_urls = [u for u in all_urls if u.strip()]
        if self.query_one("#dedupe", Checkbox).value:
            all_urls = dedupe(all_urls)

        self.results = all_urls
        self._populate_results(all_urls)

        if not all_urls:
            message = f"No URLs found in {scanned} file(s)."
        else:
            message = f"{len(all_urls)} URLs found in {scanned} file(s)."
        if errors:
            message += f" [red]{len(errors)} error(s).[/red]"
        self._set_status(message)

    @on(Button.Pressed, "#export")
    def handle_export(self) -> None:
        if not self.results:
            self._set_status("Nothing to export — scan some files first.")
            return
        out = self.query_one("#output-input", Input).value.strip()
        if not out:
            self._set_status("Choose an output path before exporting.")
            return
        overwrite = self.query_one("#overwrite", Checkbox).value
        try:
            written = write_urls(out, self.results, overwrite=overwrite)
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
        self.query_one("#results", DataTable).clear()
        self._refresh_file_list()
        self._set_status("Cleared.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract URLs from .txt and .md files in a Textual TUI."
    )
    parser.add_argument("paths", nargs="*", help="Initial input files (.txt, .md).")
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
    args = parser.parse_args(argv)

    dedupe_default = not args.no_dedupe  # --dedupe is the default; --no-dedupe wins

    app = URLExtractorApp(
        initial_paths=args.paths,
        output_path=args.output,
        dedupe_default=dedupe_default,
        overwrite_default=args.overwrite,
    )
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
