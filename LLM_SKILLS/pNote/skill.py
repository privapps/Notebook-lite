#!/usr/bin/env python3
"""
pBin Paste Skill - Create PrivateBin pastes from text or files with robust fallback.
"""

from __future__ import annotations
import json as json_module
import os
import pathlib
import sys
from datetime import datetime
import random
import yaml
from urllib.parse import urlparse
from typing import TypedDict
from pbincli.api import PrivateBin
from pbincli.format import Paste

DEFAULT_SERVER = "https://paste.i2pd.xyz/"
SERVERS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "servers.yaml")
MAX_SERVER_ATTEMPTS = 3
VALID_EXPIRY = {"5min", "10min", "1hour", "1day", "1week", "1month", "1year", "never"}
VALID_FORMATS = {"plaintext", "markdown", "syntaxhighlighting"}
DEBUG_MODE = os.getenv("PNOTE_DEBUG", "").lower() in ("1", "true", "yes")
EXTENSION_TO_FORMAT = {
    ".py": "syntaxhighlighting", ".js": "syntaxhighlighting", ".md": "markdown", ".markdown": "markdown"
}  # Extend as needed

class PasteResult(TypedDict):
    success: bool
    url: str | None
    error: str | None

def _debug_log(message: str) -> None:
    if DEBUG_MODE:
        print(f"[pNote DEBUG] {message}", file=sys.stderr)

def _load_server_list() -> list:
    if not os.path.exists(SERVERS_CONFIG_PATH):
        return [DEFAULT_SERVER]
    try:
        with open(SERVERS_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        servers = config.get("servers", [])
        servers = [s.strip() for s in servers if s.strip()]
        if DEFAULT_SERVER not in servers:
            servers.append(DEFAULT_SERVER)
        random.shuffle(servers)
        return servers
    except Exception as e:
        _debug_log(f"Could not load servers.yaml: {e}")
        return [DEFAULT_SERVER]

def _validate_server_url(url: str) -> str:
    if not url:
        return DEFAULT_SERVER
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid server URL: {url}")
    return url if url.endswith("/") else url + "/"

def _validate_expiry(expiry: str) -> str:
    if expiry not in VALID_EXPIRY:
        raise ValueError(f"Invalid expiry: {expiry}")
    return expiry

def _validate_format(format_type: str) -> str:
    if format_type not in VALID_FORMATS:
        raise ValueError(f"Invalid format: {format_type}")
    return format_type

def _detect_format(file_path: str) -> str:
    ext = pathlib.Path(file_path).suffix.lower()
    return EXTENSION_TO_FORMAT.get(ext, "plaintext")

def _transform_to_notebook_lite_url(privatebin_url: str, decryption_key: str) -> str:
    parsed = urlparse(privatebin_url)
    paste_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{parsed.query}"
    return f"https://privapps.github.io/Notebook-lite/index.html#{decryption_key}@{paste_url}"

def _create_paste_from_text_single_server(
    text: str, *, expiry: str = "1day", burn_after_read: bool = False, format_type: str = "plaintext",
    discussions: bool = False, server: str | None = None, json_format: bool = False,
) -> PasteResult:
    try:
        if json_format:
            records = convert_text_to_json_records(text, include_metadata=True)
            text = json_module.dumps(records, indent=2)
            format_type = "plaintext"
            _debug_log(f"Converted text to JSON format ({len(records)} records)")
        if not text or not text.strip():
            return PasteResult(success=False, url=None, error="Error: Text cannot be empty.")
        server_url = _validate_server_url(server or DEFAULT_SERVER)
        _debug_log(f"Using server: {server_url}")
        _validate_expiry(expiry)
        _validate_format(format_type)
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
            return PasteResult(success=False, url=None, error=f"Error: {error_msg}")
        passphrase = paste.getHash()
        privatebin_url = f"{server_url}?{result['id']}#{passphrase}"
        transformed_url = _transform_to_notebook_lite_url(privatebin_url, passphrase)
        return PasteResult(success=True, url=transformed_url, error=None)
    except Exception as e:
        return PasteResult(success=False, url=None, error=f"Error: {str(e)}")

def create_paste_from_text(
    text: str, *, expiry: str = "1day", burn_after_read: bool = False, format_type: str = "plaintext",
    discussions: bool = False, server: str | None = None, json_format: bool = False,
) -> PasteResult:
    if server:
        return _create_paste_from_text_single_server(
            text, expiry=expiry, burn_after_read=burn_after_read, format_type=format_type,
            discussions=discussions, server=server, json_format=json_format,
        )
    servers = _load_server_list()
    errors = []
    for i, srv in enumerate(servers[:MAX_SERVER_ATTEMPTS]):
        _debug_log(f"Attempt #{i+1} with PrivateBin server: {srv}")
        out = _create_paste_from_text_single_server(
            text, expiry=expiry, burn_after_read=burn_after_read,
            format_type=format_type, discussions=discussions,
            server=srv, json_format=json_format,
        )
        if out["success"]:
            out["error"] = None if i == 0 else f"Took {i+1} tries, succeeded with {srv}"
            return out
        errors.append(f"{srv}: {out['error']}")
    return PasteResult(success=False, url=None, error="All servers failed!\n" + "\n".join(errors))

def create_paste_from_file(
    file_path: str, *, expiry: str = "1day", burn_after_read: bool = False,
    format_type: str | None = None, discussions: bool = False, server: str | None = None,
) -> PasteResult:
    try:
        if not file_path or not file_path.strip():
            return PasteResult(success=False, url=None, error="Error: File path cannot be empty.")
        file_obj = pathlib.Path(file_path)
        if not file_obj.exists():
            return PasteResult(success=False, url=None, error=f"Error: File not found: {file_path}")
        if not file_obj.is_file():
            return PasteResult(success=False, url=None, error=f"Error: Not a file: {file_path}")
        if not os.access(file_obj, os.R_OK):
            return PasteResult(success=False, url=None, error=f"Error: Permission denied reading: {file_path}")
        text = file_obj.read_text(encoding="utf-8")
        if format_type is None:
            format_type = _detect_format(file_path)
        else:
            _validate_format(format_type)
        return create_paste_from_text(
            text, expiry=expiry, burn_after_read=burn_after_read, format_type=format_type,
            discussions=discussions, server=server
        )
    except Exception as e:
        return PasteResult(success=False, url=None, error=f"Error: {str(e)}")

def convert_text_to_json_records(text: str, include_metadata: bool = False) -> list:
    records = []
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
    if include_metadata and records:
        metadata = {
            "name": "Metadata",
            "description": f"Converted {len(records)} records from text"
        }
        return [records, metadata]
    return records

def combine_files_to_json(file_paths, include_metadata: bool = True) -> list:
    if not file_paths:
        return []
    records = []
    for file_path in file_paths:
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise IOError(f"Not a file: {file_path}")
        content = path.read_text(encoding="utf-8")
        mtime = path.stat().st_mtime
        date_str = datetime.fromtimestamp(mtime).isoformat() + "Z"
        filename = path.name
        record = {
            "name": filename,
            "content": content,
            "date": date_str,
        }
        records.append(record)
    if include_metadata and records:
        metadata = {
            "name": "Combined Files",
            "description": f"{len(records)} files combined",
        }
        return [records, metadata]
    return [records] if records else []
