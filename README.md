# pysembr

pysembr is a small command-line filter
that wraps long lines of text with simple,
punctuation-aware splitting rules.
It is intended for piping text through stdin/
stdout or for file-to-file processing.

## What it does

- Reads text from stdin or an input file.
- Splits lines at sentence boundaries (`.`, `!`, `?`) by default.
- If needed, splits at commas or other punctuation.
- If punctuation is not enough, splits at sentence-break words (English and German).
- If `--extended` is enabled, can also split at conjunctions/prepositions.
- Avoids splitting inside Markdown links or images.

## Install

This project is managed by [uv](https://github.com/astral-sh/uv).

1. Have `uv` installed.
2. Clone the repository: `git clone https://github.com/isotopp/pysembr.git`
3. Load the dependencies: `uv sync`
4. Run it with `uv`: `uv run pysembr --help` or install it as a tool: `uv tool install .`

If you run it as a tool, add `uv tool dir --bin` to the PATH in your shell:

```bash
PATH="$PATH:`uv tool dir --bin`"
```

## Run

Filter from stdin to stdout:

```bash
cat input.txt | pysembr
```

Use files instead of stdin/stdout:

```bash
pysembr -i input.txt -o output.txt
```

Adjust the wrapping width:

```bash
pysembr --width 72
```

Disable sentence-boundary splitting for short lines:

```bash
pysembr --no-force
```

Enable conjunction/preposition splitting:

```bash
pysembr --extended
```

Limit to a subset of languages:

```bash
pysembr --languages english,german
```

List available languages:

```bash
pysembr --list-languages
```

Show effective options and config selection:

```bash
pysembr --show-options
```

## Configuration file

Defaults can be set in a configparser file:

- macOS/Linux: `./.sembr`, then `~/.sembr`
- Windows: `.\sembr.ini`, then `%APPDATA%\sembr\sembr.ini`
- Or specify a custom file/section with `--config-file` / `--config-section`.

The first matching section is used, in order, and search stops:

- A path section like `[/Users/kris/Source]` applies to any project under that path.
- `[default]` applies if it appears first or when no path section matches.

Example:

```ini
[/Users/kris/Source]
extended = true
width = 75
force = true
languages = english,german

[default]
width = 75
force = true
languages = english,german
```

## Valid options

- `--infile` / `-i`: Input file path. If omitted, read from stdin.
- `--outfile` / `-o`: Output file path. If omitted, write to stdout.
- `--width` / `-w`: Target line width (default 75).
- `--force` / `-f`: Split at sentence punctuation regardless of line length (default).
- `--no-force`: Disable sentence-boundary splits for short lines.
- `--extended` / `-e`: Split at conjunctions/prepositions when needed.
- `--languages` / `-l`: Comma-separated languages to enable, or `all` (default).
- `--list-languages`: List available languages and exit.
- `--config-file` / `-c`: Config file path (overrides default search).
- `--config-section` / `-s`: Config section name (overrides default selection).
- `--show-options`: Print effective options and exit.

## Use it in IntelliJ/PyCharm/WebStorm

1. Install the 'Shellfilter' Plugin from Marketplace.
2. Open Settings -> Tools -> Shellfilter Settings. 
   In the Commands Section, add a Tool with `[+]`, name it `pysembr` and use the appropriate full path.
3. Use Control+Command+I to run a shellfilter on the current selection. Select `pysembr`.

## Notes

- If no suitable split point is found and `--extended` is not enabled, long lines may remain longer than the target width.
- When both stdin/stdout and files are provided, file options should take precedence.
