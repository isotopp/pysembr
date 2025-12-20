# pysembr

pysembr is a small command-line filter that wraps long lines of text with simple, punctuation-aware splitting rules. It is intended for piping text through stdin/stdout or for file-to-file processing.

## What it does

- Reads text from stdin or an input file.
- Splits lines that exceed a target width (default 75 characters).
- Prefers splitting at sentence boundaries (".").
- If needed, splits at commas or other punctuation.
- If punctuation is not enough, splits at sentence-break words (English and German).
- If `--extended` is enabled, can also split at conjunctions/prepositions.

## Install

This project is managed by [uv](https://github.com/astral-sh/uv).

```bash
uv venv
uv pip install -e .
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

Force a split at sentence boundaries even when the line is shorter than the width:

```bash
pysembr --force
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

## Planned options

- `--infile` / `-i`: Input file path. If omitted, read from stdin.
- `--outfile` / `-o`: Output file path. If omitted, write to stdout.
- `--width` / `-w`: Target line width (default 75).
- `--force` / `-f`: Split at "." even when lines are shorter than `--width`.
- `--extended` / `-e`: Split at conjunctions/prepositions when needed.
- `--languages` / `-l`: Comma-separated languages to enable, or `all` (default).
- `--list-languages`: List available languages and exit.

## Notes

- If no suitable split point is found and `--extended` is not enabled, long lines may remain longer than the target width.
- When both stdin/stdout and files are provided, file options should take precedence.
