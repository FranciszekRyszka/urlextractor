# URL Extractor TUI

A terminal app, built with [Textual](https://textual.textualize.io/), that
extracts URLs from `.txt` and `.md` files and exports them to a plain-text
file with one URL per line.

## Features

- Add one or more `.txt` / `.md` files.
- Extract all `http://` and `https://` links with a regex-based parser.
- Optional order-preserving deduplication.
- Preview results in a scrollable table before exporting.
- Inline status messages and error reporting (no crashes on bad input).
- Export to a UTF-8 text file, one URL per line.

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
python app.py notes.txt README.md --output urls.txt --dedupe --overwrite
```

| Option           | Effect                                              |
| ---------------- | --------------------------------------------------- |
| `paths...`       | Initial input files to load on startup.             |
| `-o`, `--output` | Default output path.                                |
| `--dedupe`       | Enable deduplication by default (already the default). |
| `--no-dedupe`    | Disable deduplication by default.                   |
| `--overwrite`    | Allow overwriting an existing output file.          |

### In-app controls

- **Add file** — validate and add the path in the input box.
- **Scan** — read all added files and populate the results table.
- **Export** — write the current results to the output path.
- **Clear** — reset files and results.
- **Ctrl+Q** — quit.

## Project structure

```text
.
├── app.py        # Textual app, event handlers, CLI entry point
├── ui.py         # Reusable widget composition / layout
├── extractor.py  # URL regex, cleaning, deduplication
├── io_utils.py   # Safe file reading and writing
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
