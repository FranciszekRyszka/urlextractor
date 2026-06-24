# URL Extractor TUI

A terminal app, built with [Textual](https://textual.textualize.io/), that
extracts URLs from `.txt` and `.md` files and exports them to a plain-text
file with one URL per line.

## Features

- Add inputs as **files, folders (scanned recursively), or glob patterns**
  (e.g. `docs/*.md`).
- **Drag-and-drop**: drag a file onto the input box (then Add/Enter), or drop
  it while the box is unfocused to add it automatically.
- **File picker**: a `Browse` button opens a directory-tree modal.
- Extract all `http://` and `https://` links with a regex-based parser.
- Optional order-preserving deduplication, with per-URL occurrence counts.
- **Sort** results: original order, A→Z, Z→A, by domain, or by frequency.
- Preview results (with counts) in a scrollable table before exporting.
- **Progress bar** while scanning.
- **Multiple export formats**: plain text, CSV, JSON, or Markdown.
- Inline status messages and error reporting (no crashes on bad input).

## Requirements

- Python 3.9+
- Textual (installed via the steps below)

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e .          # runtime only
pip install -e ".[dev]"   # adds textual-dev for development
```

Or just install the dependency directly:

```bash
pip install textual
```

## Usage

Launch the TUI:

```bash
python app.py
```

Or, if installed as a package, use the console script:

```bash
url-extractor
```

### Command-line options

The app is a TUI but accepts arguments to pre-fill the form for automation:

```bash
python app.py notes.txt docs/ "blog/*.md" --output urls.csv --format csv --sort frequency --overwrite
```

| Option           | Effect                                                  |
| ---------------- | ------------------------------------------------------- |
| `paths...`       | Initial inputs: files, folders, or globs.               |
| `-o`, `--output` | Default output path.                                    |
| `--dedupe`       | Enable deduplication by default (already the default).  |
| `--no-dedupe`    | Disable deduplication by default.                       |
| `--overwrite`    | Allow overwriting an existing output file.              |
| `--sort`         | Default ordering: `original`, `az`, `za`, `domain`, `frequency`. |
| `--format`       | Default export format: `txt`, `csv`, `json`, `md`.      |

The output file's extension is normalized to match the chosen format.

### In-app controls

- **Add** — resolve the input box (file, folder, or glob) and add the files.
- **Browse** — open the file-picker modal (Esc cancels).
- **Sort / Format** — choose result ordering and export format.
- **Scan** — read all added files and populate the results table.
- **Export** — write the current results to the output path.
- **Clear** — reset files and results.
- **Ctrl+Q** — quit.

## Project structure

```text
.
├── app.py        # Textual app, event handlers, CLI entry point
├── ui.py         # Reusable widget composition / layout
├── screens.py    # File-picker modal screen
├── extractor.py  # URL regex, cleaning, deduplication, sorting
├── io_utils.py   # Input resolution, safe reading, multi-format export
├── app.tcss      # TUI styling (App.CSS_PATH)
├── pyproject.toml
└── README.md
```

## Development

With `textual-dev` installed you can run the app in dev mode and use the
console for live logs:

```bash
textual run --dev app.py
```
