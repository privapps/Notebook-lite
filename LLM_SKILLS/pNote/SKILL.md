---
name: pNote
description: Share secrets or config files as PrivateBin pastes with transformed Notebook-lite URL via agent. Returns JSON output.
license: MIT
compatibility: Requires pbincli >= 0.3.7, Python 3.11+
metadata:
  author: ai-opencode
  version: "1.1"
---

# pNote Skill

This skill securely creates PrivateBin pastes from file or text and always returns a structured JSON result. The URL is transformed for Notebook-lite use:

    https://privapps.github.io/Notebook-lite/index.html#<decryption_key>@https://<paste_server>/?<paste_id>

## Features

- **Text/file pastes**: Share text/raw files instantly
- **Notebook-lite URL transformation**: Extracts decryption key and creates shareable link
- **Configurable expiry and burn-after-read**: All PrivateBin options supported
- **Structured JSON output**: Output is ready for programmatic use

## Installation

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- pbincli >= 0.3.7 (managed by uv)

## Usage

### Via CLI (Recommended)

```bash
# Basic text sharing
uv run cli.py text "Your secret content"

# Share single file
uv run cli.py file path/to/file.txt

# Combine multiple files into single JSON paste
uv run cli.py combine file1.md file2.md file3.md

# With custom options
uv run cli.py text "Secret" --expiry 1week --burn-after-read
uv run cli.py combine file1.md file2.md --expiry 1week --burn-after-read
```

### File Combination (Multiple Files to Single JSON)

Combine multiple files into one JSON paste where each file becomes a record:

**Command:**
```bash
uv run cli.py combine p.md p1.md w.md
```

**Output format:**
```json
[
  [
    {
      "name": "p.md",
      "content": "... file content ...",
      "date": "2021-02-24T21:30:21.002Z"
    },
    {
      "name": "p1.md",
      "content": "... file content ...",
      "date": "2021-02-24T21:30:21.002Z"
    },
    {
      "name": "w.md",
      "content": "... file content ...",
      "date": "2021-02-24T21:30:21.002Z"
    }
  ],
  {
    "name": "Combined Files",
    "description": "3 files combined"
  }
]
```

Each file becomes a JSON record with:
- `name`: Filename
- `content`: Full file content
- `date`: File modification time in ISO 8601 format

The output array has two elements:
1. Array of file records
2. Metadata object with combined description

### Text to JSON Records Conversion

For parsing structured text into JSON records, use `--json-format` flag:

**Input format (text file with structured records):**
```
Name: Project Alpha
Content: Initial research phase completed
Date: 2021-02-24T21:30:21.002Z
---
Name: Project Beta
Content: Design documents ready
Date: 2021-02-25T10:15:30.000Z
```

**Command (read from file):**
```bash
cat input.txt | uv run cli.py text "$(cat input.txt)" --json-format
```

**Output:**
```json
[
  [
    {
      "name": "Project Alpha",
      "content": "Initial research phase completed",
      "date": "2021-02-24T21:30:21.002Z"
    },
    {
      "name": "Project Beta",
      "content": "Design documents ready",
      "date": "2021-02-25T10:15:30.000Z"
    }
  ],
  {
    "name": "Metadata",
    "description": "Converted 2 records from text"
  }
]
```

### Required Setup

Before first use, install dependencies:
```bash
cd CURRENT_FOLDER/skills/pNote
uv sync
```

## Output

Agent returns structured JSON:

```json
{
  "success": true,
  "url": "https://privapps.github.io/Notebook-lite/index.html#F21RSQNzWKceDmTq4CopMEN8FviZzxLNynUSHamEMn2v@paste.i2pd.xyz/?a4f313580c148670",
  "error": null
}
```

If an error:

```json
{
  "success": false,
  "url": null,
  "error": "File not found: /path/to/file.txt"
}
```

## Examples

### Example 1: Simple Text Sharing
```bash
$ uv run cli.py text "My secret password: xyz123"

{
  "success": true,
  "url": "https://privapps.github.io/Notebook-lite/index.html#...@paste.i2pd.xyz/?...",
  "error": null
}
```

### Example 2: JSON Conversion
```bash
$ cat data.txt
Name: Database Backup
Content: Backup of production database
Date: 2024-03-10T15:30:00.000Z
---
Name: Config Files
Content: Server configuration backup
Date: 2024-03-10T16:00:00.000Z

$ uv run cli.py text "$(cat data.txt)" --json-format

{
  "success": true,
  "url": "...",
  "error": null
}
```

### Example 3: File with Options
```bash
$ uv run cli.py file config.py --expiry 1week --burn-after-read

{
  "success": true,
  "url": "...",
  "error": null
}
```

## What NOT to Do

### ❌ Don't use pbincli directly
```bash
# WRONG - This doesn't create Notebook-lite URLs
pbincli send -f file.txt
```

### ❌ Don't look for cli.py before running uv sync
```bash
# WRONG - cli.py won't be in PATH yet
cd ~/.venv/bin && ./cli.py
```

### ✅ DO use the pNote skill with uv
```bash
# RIGHT - Use uv to run CLI
uv run cli.py text "content"
```

### URL Transformation Logic
- Takes PrivateBin URL in form: `https://paste.i2pd.xyz/?<pasteid>#<decryption_key>`
- Extracts `<decryption_key>` from URL fragment and `<paste_url>` (without fragment).
- Combines as: `https://privapps.github.io/Notebook-lite/index.html#<decryption_key>@<paste_url>`

## Supported File Formats

| Extension               | Format           |
|-------------------------|------------------|
| .py .js .java .go .rs   | syntaxhighlighting|
| .md .markdown           | markdown         |
| All others              | plaintext        |

## Expiry Options

- 5min, 10min, 1hour, 1day (default), 1week, 1month, 1year, never

## API Reference

**Input:**
- `file_path` (str): file to share
- `text` (str): text to share
- `expiry` (str, optional): Expiration time (default: "1day")
- `burn_after_read` (bool, optional): Delete after first read
- `format` (str, optional): Force format type
- `discussions` (bool, optional): Enable discussions
- `server` (str, optional): PrivateBin server URL
- `json_format` (bool, optional): Convert text to JSON records (default: false)

**JSON Format Fields (when json_format=true):**
- `name` (str): Record name
- `content` (str): Record content
- `date` (str): Record date (ISO 8601 format)
- `description` (str): Record description (optional)

Records are separated by `---` in input text.

**Output JSON:**
- `success` (bool)
- `url` (str): Transformed Notebook-lite URL
- `error` (str): Error message

## Server Compatibility
- API/CLI server support required. Default: https://paste.eccologic.net
- Test your server if custom.

## Troubleshooting
- File not found, permission, connection, argument errors reported in output.
- Enable debug logging: `PNOTE_DEBUG=1` to see intermediate transformation steps
- **URL format issue**: Ensure the generated URL includes `https://` before the server name in the fragment (e.g., `#KEY@https://paste.server.com/?id`). Missing `https://` will cause Notebook-lite to fail to parse the URL.
- If URLs don't work, verify the PrivateBin server is accessible

## Security Considerations
- Notebook-lite URL contains decryption key and server endpoint. Share only via secure channels.
- Use burn-after-read for sensitive shares.
- Do not commit server URLs or paste IDs in version control

## License
MIT
