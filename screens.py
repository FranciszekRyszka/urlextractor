"""Modal screens for the URL Extractor TUI."""
from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Label


class FilePickerScreen(ModalScreen[Optional[str]]):
    """A modal directory tree for picking a single input file.

    Dismisses with the selected file path (str) or ``None`` if cancelled.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, start_path: str = ".") -> None:
        super().__init__()
        self._start_path = start_path

    def compose(self) -> ComposeResult:
        with Vertical(id="picker"):
            yield Label("Select a file (.txt or .md) — Enter to choose, Esc to cancel")
            yield DirectoryTree(self._start_path, id="tree")
            yield Button("Cancel", id="cancel-pick")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        self.dismiss(str(event.path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-pick":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
