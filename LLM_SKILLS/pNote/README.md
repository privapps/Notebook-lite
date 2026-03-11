# pNote Skill - Setup & Usage Guide

## Quick Start with uv

This project uses [uv](https://docs.astral.sh/uv/) for Python package management. It's fast, reliable, and handles everything you need.

### Installation

1. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and navigate to the project**:
   ```bash
   cd CURRENT_FOLDER/skills/pNote
   ```

3. **Sync dependencies**:
   ```bash
   uv sync
   ```

### Running the CLI

```bash
# Create paste from text
uv run cli.py text "Your secret content"

# Create paste from file
uv run cli.py file path/to/file.txt

# With options
uv run cli.py text "Secret" --expiry 1week --burn-after-read

# Enable debug logging
PNOTE_DEBUG=1 uv run cli.py text "Test"
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test class
uv run pytest test_skill.py::TestURLTransformation -v

# With coverage
uv run pytest --cov=skill test_skill.py
```

### Project Structure

- `skill.py` - Core paste creation logic
- `cli.py` - Command-line interface
- `test_skill.py` - Test suite
- `pyproject.toml` - Project configuration (managed by uv)
- `uv.lock` - Locked dependency versions (auto-generated)

### Features

- ✅ Creates PrivateBin pastes from text or files
- ✅ Auto-detects file format (Python, JS, Markdown, etc.)
- ✅ Transforms URLs to Notebook-lite format
- ✅ Supports all PrivateBin options (expiry, burn-after-read, etc.)
- ✅ Comprehensive error handling and validation

### Output Format

Success:
```json
{
  "success": true,
  "url": "https://privapps.github.io/Notebook-lite/index.html#<key>@<server>/?<id>",
  "error": null
}
```

Error:
```json
{
  "success": false,
  "url": null,
  "error": "Error message explaining what went wrong"
}
```

### Debug Mode

Enable debug logging to see intermediate steps:
```bash
PNOTE_DEBUG=1 uv run cli.py text "test"
```

Shows:
- Server being used
- API version
- Paste ID received
- Raw PrivateBin URL
- Transformed Notebook-lite URL

### Requirements

- Python 3.11+
- uv package manager
- pbincli >= 0.3.7 (auto-installed by uv)

For more details, see [SKILL.md](SKILL.md)
