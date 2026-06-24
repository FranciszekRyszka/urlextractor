"""Reusable widget composition and layout for the URL Extractor TUI.

Keeping the layout here lets ``app.py`` focus on behaviour and event
handling. Widget IDs are the contract between the two modules.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    Select,
)

SORT_OPTIONS = [
    ("Original order", "original"),
    ("A → Z", "az"),
    ("Z → A", "za"),
    ("By domain", "domain"),
    ("By frequency", "frequency"),
]

FORMAT_OPTIONS = [
    ("Text (.txt)", "txt"),
    ("CSV (.csv)", "csv"),
    ("JSON (.json)", "json"),
    ("Markdown (.md)", "md"),
]


def compose_layout() -> ComposeResult:
    """Yield the full widget tree for the main screen."""
    yield Header()
    with Vertical(id="main"):
        # --- File input ------------------------------------------------
        with Vertical(id="file-section"):
            yield Label("Input files, folders, or globs (.txt, .md)")
            with Horizontal(id="file-input-row"):
                yield Input(
                    placeholder="Path / folder / *.md — or drag a file here…",
                    id="path-input",
                )
                yield Button("Add", id="add", variant="primary")
                yield Button("Browse", id="browse")
            yield Label("No files added yet.", id="file-list")

        # --- Options ---------------------------------------------------
        with Horizontal(id="options-section"):
            yield Checkbox("Deduplicate URLs", value=True, id="dedupe")
            yield Checkbox("Skip empty lines", value=True, id="skip-empty")

        # --- View / export options ------------------------------------
        with Horizontal(id="view-section"):
            yield Label("Sort:", classes="field-label")
            yield Select(
                SORT_OPTIONS, value="original", allow_blank=False, id="sort"
            )
            yield Label("Format:", classes="field-label")
            yield Select(
                FORMAT_OPTIONS, value="txt", allow_blank=False, id="format"
            )

        # --- Output ----------------------------------------------------
        with Horizontal(id="output-section"):
            yield Input(placeholder="Output path (e.g. urls.txt)…", id="output-input")
            yield Checkbox("Overwrite", value=False, id="overwrite")

        # --- Progress --------------------------------------------------
        yield ProgressBar(id="progress", show_eta=False)

        # --- Results preview ------------------------------------------
        with VerticalScroll(id="results-section"):
            yield DataTable(id="results")

        # --- Actions ---------------------------------------------------
        with Horizontal(id="action-row"):
            yield Button("Scan", id="scan", variant="success")
            yield Button("Export", id="export", variant="primary")
            yield Button("Clear", id="clear", variant="warning")

        yield Label("Ready.", id="status")
    yield Footer()
