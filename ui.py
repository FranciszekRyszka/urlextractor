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
)


def compose_layout() -> ComposeResult:
    """Yield the full widget tree for the main screen.

    Layout zones: a ``Header`` on top, a vertical main area (file input,
    options, output, results, actions, status), and a ``Footer`` at the
    bottom.
    """
    yield Header()
    with Vertical(id="main"):
        # --- File input ------------------------------------------------
        with Vertical(id="file-section"):
            yield Label("Input files (.txt, .md)")
            with Horizontal(id="file-input-row"):
                yield Input(placeholder="Path to a .txt or .md file…", id="path-input")
                yield Button("Add file", id="add", variant="primary")
            yield Label("No files added yet.", id="file-list")

        # --- Options ---------------------------------------------------
        with Horizontal(id="options-section"):
            yield Checkbox("Deduplicate URLs", value=True, id="dedupe")
            yield Checkbox("Skip empty lines", value=True, id="skip-empty")

        # --- Output ----------------------------------------------------
        with Horizontal(id="output-section"):
            yield Input(placeholder="Output path (e.g. urls.txt)…", id="output-input")
            yield Checkbox("Overwrite", value=False, id="overwrite")

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
