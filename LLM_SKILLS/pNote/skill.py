"""
pBin Paste Skill - Create PrivateBin pastes from text or files
"""

from __future__ import annotations

import json as json_module
import os
import pathlib
import sys
from datetime import datetime
from typing import List, Literal, TypedDict
from urllib.parse import urlparse

from pbincli.api import PrivateBin
from pbincli.format import Paste


DEFAULT_SERVER = "https://paste.i2pd.xyz/"

VALID_EXPIRY = {"5min", "10min", "1hour", "1day", "1week", "1month", "1year", "never"}
VALID_FORMATS = {"plaintext", "markdown", "syntaxhighlighting"}

# Enable intermediate step logging via environment variable
DEBUG_MODE = os.getenv("PNOTE_DEBUG", "").lower() in ("1", "true", "yes")


def _debug_log(message: str) -> None:
    """Log intermediate steps when DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(f"[pNote DEBUG] {message}", file=sys.stderr)


def _validate_notebook_lite_url(url: str) -> bool:
    """
    Validate that the Notebook-lite URL has the correct format.
    
    The URL fragment should include https:// before the server URL, otherwise
    Notebook-lite cannot properly parse the server and paste ID.
    
    Expected format: https://privapps.github.io/Notebook-lite/index.html#<KEY>@https://<server>/?<id>
    
    Returns: True if valid, False if missing https:// in fragment
    """
    if not url:
        return False
    
    # Check for common issues
    if "@https://" not in url:
        # Fragment is missing https:// before server URL
        return False
    
    return True

# Extension to format mapping for auto-detection
EXTENSION_TO_FORMAT = {
    # Python
    ".py": "syntaxhighlighting",
    ".pyw": "syntaxhighlighting",
    ".pyi": "syntaxhighlighting",
    # JavaScript/TypeScript
    ".js": "syntaxhighlighting",
    ".jsx": "syntaxhighlighting",
    ".ts": "syntaxhighlighting",
    ".tsx": "syntaxhighlighting",
    # Java
    ".java": "syntaxhighlighting",
    ".class": "syntaxhighlighting",
    ".jar": "syntaxhighlighting",
    # Go
    ".go": "syntaxhighlighting",
    # Rust
    ".rs": "syntaxhighlighting",
    ".rlib": "syntaxhighlighting",
    # C/C++
    ".c": "syntaxhighlighting",
    ".h": "syntaxhighlighting",
    ".cpp": "syntaxhighlighting",
    ".cc": "syntaxhighlighting",
    ".cxx": "syntaxhighlighting",
    # Ruby
    ".rb": "syntaxhighlighting",
    ".rbw": "syntaxhighlighting",
    # PHP
    ".php": "syntaxhighlighting",
    # Shell
    ".sh": "syntaxhighlighting",
    ".bash": "syntaxhighlighting",
    ".zsh": "syntaxhighlighting",
    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",
}


class PasteResult(TypedDict):
    """Result from paste creation."""

    success: bool
    url: str | None
    error: str | None


def _validate_server_url(url: str) -> str:
    """Validate and normalize the server URL."""
    if not url:
        return DEFAULT_SERVER
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid server URL: {url}. Must be http:// or https://")
    return url if url.endswith("/") else url + "/"


def _validate_expiry(expiry: str) -> str:
    """Validate expiry value."""
    if expiry not in VALID_EXPIRY:
        raise ValueError(
            f"Invalid expiry: {expiry}. Must be one of: {', '.join(sorted(VALID_EXPIRY))}"
        )
    return expiry


def _validate_format(format_type: str) -> str:
    """Validate format value."""
    if format_type not in VALID_FORMATS:
        raise ValueError(
            f"Invalid format: {format_type}. Must be one of: {', '.join(sorted(VALID_FORMATS))}"
        )
    return format_type


def _detect_format(file_path: str) -> str:
    """Auto-detect format from file extension."""
    ext = pathlib.Path(file_path).suffix.lower()
    return EXTENSION_TO_FORMAT.get(ext, "plaintext")


def _transform_to_notebook_lite_url(privatebin_url: str, decryption_key: str) -> str:
    """
    Transform a PrivateBin URL to Notebook-lite format.

    PrivateBin URL format: https://server/?<paste_id>#<decryption_key>
    Notebook-lite URL format: https://privapps.github.io/Notebook-lite/index.html#<decryption_key>@https://<server>/?<paste_id>

    Args:
        privatebin_url: Full PrivateBin URL with fragment
        decryption_key: Decryption key extracted from paste

    Returns:
        Transformed Notebook-lite URL with https:// in fragment for proper parsing
    """
    parsed = urlparse(privatebin_url)
    # Notebook-lite expects fragment to contain: <key>@https://<server>/?<paste_id>
    # Include scheme (https://) so Notebook-lite can properly parse the server URL
    paste_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{parsed.query}"
    result = f"https://privapps.github.io/Notebook-lite/index.html#{decryption_key}@{paste_url}"
    
    # Validate the output to catch potential bugs
    if not _validate_notebook_lite_url(result):
        _debug_log(f"WARNING: Generated URL may not work properly: {result}")
    
    return result


def convert_text_to_json_records(text: str, include_metadata: bool = False) -> list:
    """
    Convert plain text to structured JSON records.
    
    Parses text in format:
        Name: value
        Content: value
        Date: value
        ---
        Name: value
        ...
    
    Args:
        text: Text content with key-value pairs separated by ---
        include_metadata: Whether to include metadata object at end
    
    Returns:
        List of JSON records with name, content, date fields
        
    Example:
        >>> text = "Name: Project A\\nContent: Details\\nDate: 2021-02-24T21:30:21Z\\n---\\nName: Project B\\nContent: More details\\nDate: 2021-02-25T10:15:30Z"
        >>> records = convert_text_to_json_records(text)
        >>> print(len(records))  # 2
    """
    records = []
    
    # Split by --- to get individual records
    sections = text.split("---")
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.strip().split("\n")
        record = {}
        
        for line in lines:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            # Map common field names
            if key == "name":
                record["name"] = value
            elif key == "content":
                record["content"] = value
            elif key == "date":
                record["date"] = value
            elif key == "description":
                record["description"] = value
        
        if record:
            records.append(record)
    
    # Return with optional metadata
    if include_metadata and records:
        metadata = {
            "name": "Metadata",
            "description": f"Converted {len(records)} records from text"
        }
        return [records, metadata]
    
    return records


def create_paste_from_text(
    text: str,
    *,
    expiry: str = "1day",
    burn_after_read: bool = False,
    format_type: str = "plaintext",
    discussions: bool = False,
    server: str | None = None,
    json_format: bool = False,
) -> PasteResult:
    """
    Create a paste from text content.

    Args:
        text: Text content to paste (required, cannot be empty)
        expiry: Expiration duration (default: "1day")
        burn_after_read: Delete paste after first read (default: False)
        format_type: Format type (default: "plaintext")
        discussions: Enable discussions (default: False)
        server: PrivateBin server URL (default: DEFAULT_SERVER)
        json_format: Convert text to JSON records (default: False)

    Returns:
        PasteResult with success, url, and error fields
    """
    try:
        # Convert to JSON if requested
        if json_format:
            records = convert_text_to_json_records(text, include_metadata=True)
            text = json_module.dumps(records, indent=2)
            format_type = "plaintext"
            _debug_log(f"Converted text to JSON format ({len(records)} records)")
        # Validate inputs
        if not text or not text.strip():
            return PasteResult(
                success=False,
                url=None,
                error="Error: Text cannot be empty.",
            )

        server_url = _validate_server_url(server or DEFAULT_SERVER)
        _debug_log(f"Using server: {server_url}")
        _validate_expiry(expiry)
        _validate_format(format_type)

        # Create paste via pbincli
        api = PrivateBin(settings={"server": server_url})
        version = api.getVersion()
        _debug_log(f"PrivateBin API version: {version}")

        paste = Paste()
        paste.setVersion(version)
        if version == 2:
            paste.setCompression("zlib")
        paste.setText(text)
        paste.encrypt(
            formatter=format_type,
            burnafterreading=burn_after_read,
            discussion=discussions,
            expiration=expiry,
        )

        result = api.post(paste.getJSON())
        if result.get("status") != 0:
            error_msg = result.get("message", "Unknown error from server")
            return PasteResult(
                success=False,
                url=None,
                error=f"Error: {error_msg}",
            )

        # Format response
        passphrase = paste.getHash()
        privatebin_url = f"{server_url}?{result['id']}#{passphrase}"
        _debug_log(f"Paste ID: {result['id']}")
        _debug_log(f"PrivateBin URL: {privatebin_url}")
        
        transformed_url = _transform_to_notebook_lite_url(privatebin_url, passphrase)
        _debug_log(f"Transformed URL: {transformed_url}")

        return PasteResult(
            success=True,
            url=transformed_url,
            error=None,
        )

    except ValueError as e:
        return PasteResult(
            success=False,
            url=None,
            error=f"Error: {str(e)}",
        )
    except Exception as e:
        return PasteResult(
            success=False,
            url=None,
            error=f"Error: {str(e)}",
        )


def create_paste_from_file(
    file_path: str,
    *,
    expiry: str = "1day",
    burn_after_read: bool = False,
    format_type: str | None = None,
    discussions: bool = False,
    server: str | None = None,
) -> PasteResult:
    """
    Create a paste from a file with auto-format detection.

    Args:
        file_path: Path to file to paste (required)
        expiry: Expiration duration (default: "1day")
        burn_after_read: Delete paste after first read (default: False)
        format_type: Format type override (optional, auto-detected if None)
        discussions: Enable discussions (default: False)
        server: PrivateBin server URL (default: DEFAULT_SERVER)

    Returns:
        PasteResult with success, url, and error fields
    """
    try:
        # Validate file
        if not file_path or not file_path.strip():
            return PasteResult(
                success=False,
                url=None,
                
                error="Error: File path cannot be empty.",
            )

        file_obj = pathlib.Path(file_path)
        if not file_obj.exists():
            return PasteResult(
                success=False,
                url=None,
                
                error=f"Error: File not found: {file_path}",
            )

        if not file_obj.is_file():
            return PasteResult(
                success=False,
                url=None,
                
                error=f"Error: Not a file: {file_path}",
            )

        # Check read permissions
        if not os.access(file_obj, os.R_OK):
            return PasteResult(
                success=False,
                url=None,
                
                error=f"Error: Permission denied reading: {file_path}",
            )

        # Read file
        try:
            text = file_obj.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return PasteResult(
                success=False,
                url=None,
                
                error=f"Error: File is not valid UTF-8 text: {file_path}",
            )

        # Auto-detect format if not overridden
        if format_type is None:
            format_type = _detect_format(file_path)
        else:
            _validate_format(format_type)

        # Use text-based creation with detected format
        return create_paste_from_text(
            text,
            expiry=expiry,
            burn_after_read=burn_after_read,
            format_type=format_type,
            discussions=discussions,
            server=server,
        )

    except ValueError as e:
        return PasteResult(
            success=False,
            url=None,
            
            error=f"Error: {str(e)}",
        )
    except Exception as e:
        return PasteResult(
            success=False,
            url=None,
            
            error=f"Error: {str(e)}",
        )


def combine_files_to_json(file_paths: List[str], include_metadata: bool = True) -> list:
    """
    Combine multiple files into a JSON structure with records and metadata.
    
    Args:
        file_paths: List of file paths to combine
        include_metadata: Whether to include metadata object (default: True)
    
    Returns:
        List with structure: [[file_records], metadata] or [file_records] without metadata
        Each file record: {"name": filename, "content": content, "date": iso_date}
    
    Raises:
        FileNotFoundError: If any file doesn't exist
        IOError: If file cannot be read
    """
    if not file_paths:
        return []
    
    records = []
    
    for file_path in file_paths:
        try:
            path = pathlib.Path(file_path)
            
            # Verify file exists and is readable
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if not path.is_file():
                raise IOError(f"Not a file: {file_path}")
            
            # Read file content
            content = path.read_text(encoding="utf-8")
            
            # Get file modification time in ISO 8601 format
            mtime = path.stat().st_mtime
            date_str = datetime.fromtimestamp(mtime).isoformat() + "Z"
            
            # Get filename
            filename = path.name
            
            # Create record
            record = {
                "name": filename,
                "content": content,
                "date": date_str
            }
            records.append(record)
            
        except (FileNotFoundError, IOError) as e:
            _debug_log(f"Error reading file {file_path}: {str(e)}")
            raise
    
    # Return with optional metadata
    if include_metadata and records:
        metadata = {
            "name": "Combined Files",
            "description": f"{len(records)} files combined"
        }
        return [records, metadata]
    
    return [records] if records else []
