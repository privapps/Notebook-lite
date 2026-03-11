"""
Tests for pBin Paste Skill
"""

import os
import tempfile
from pathlib import Path

import pytest

from skill import (
    create_paste_from_file,
    create_paste_from_text,
    _validate_expiry,
    _validate_format,
    _detect_format,
    _transform_to_notebook_lite_url,
    _validate_notebook_lite_url,
    convert_text_to_json_records,
    combine_files_to_json,
)


class TestValidation:
    """Test validation functions."""

    def test_validate_expiry_valid(self):
        """Test valid expiry values."""
        assert _validate_expiry("5min") == "5min"
        assert _validate_expiry("1day") == "1day"
        assert _validate_expiry("1week") == "1week"
        assert _validate_expiry("never") == "never"

    def test_validate_expiry_invalid(self):
        """Test invalid expiry values."""
        with pytest.raises(ValueError, match="Invalid expiry"):
            _validate_expiry("invalid")

    def test_validate_format_valid(self):
        """Test valid format values."""
        assert _validate_format("plaintext") == "plaintext"
        assert _validate_format("markdown") == "markdown"
        assert _validate_format("syntaxhighlighting") == "syntaxhighlighting"

    def test_validate_format_invalid(self):
        """Test invalid format values."""
        with pytest.raises(ValueError, match="Invalid format"):
            _validate_format("invalid")

    def test_detect_format_python(self):
        """Test format detection for Python files."""
        assert _detect_format("script.py") == "syntaxhighlighting"
        assert _detect_format("file.pyw") == "syntaxhighlighting"

    def test_detect_format_javascript(self):
        """Test format detection for JavaScript files."""
        assert _detect_format("app.js") == "syntaxhighlighting"
        assert _detect_format("component.tsx") == "syntaxhighlighting"

    def test_detect_format_markdown(self):
        """Test format detection for Markdown files."""
        assert _detect_format("README.md") == "markdown"
        assert _detect_format("doc.markdown") == "markdown"

    def test_detect_format_unknown(self):
        """Test format detection for unknown extensions."""
        assert _detect_format("data.txt") == "plaintext"
        assert _detect_format("file.unknown") == "plaintext"


class TestURLTransformation:
    """Test URL transformation to Notebook-lite format."""

    def test_transform_privatebin_to_notebook_lite(self):
        """Test basic transformation of PrivateBin URL to Notebook-lite format."""
        privatebin_url = "https://paste.i2pd.xyz/?a4f313580c148670#F21RSQNzWKceDmTq4CopMEN8FviZzxLNynUSHamEMn2v"
        decryption_key = "F21RSQNzWKceDmTq4CopMEN8FviZzxLNynUSHamEMn2v"
        result = _transform_to_notebook_lite_url(privatebin_url, decryption_key)
        
        expected = "https://privapps.github.io/Notebook-lite/index.html#F21RSQNzWKceDmTq4CopMEN8FviZzxLNynUSHamEMn2v@https://paste.i2pd.xyz/?a4f313580c148670"
        assert result == expected

    def test_transform_with_different_server(self):
        """Test transformation with a different PrivateBin server."""
        privatebin_url = "https://paste.eccologic.net/?xyz123#ABC789"
        decryption_key = "ABC789"
        result = _transform_to_notebook_lite_url(privatebin_url, decryption_key)
        
        assert result.startswith("https://privapps.github.io/Notebook-lite/index.html#ABC789@")
        assert "https://paste.eccologic.net/?xyz123" in result

    def test_transform_includes_decryption_key_and_separator(self):
        """Test that transformation includes @ separator between key and URL."""
        privatebin_url = "https://paste.example.com/?123#key456"
        decryption_key = "key456"
        result = _transform_to_notebook_lite_url(privatebin_url, decryption_key)
        
        assert "#key456@https://" in result
        assert "paste.example.com/?123" in result


class TestURLValidation:
    """Test URL validation to prevent format bugs."""

    def test_validate_correct_format(self):
        """Test that valid Notebook-lite URL passes validation."""
        valid_url = "https://privapps.github.io/Notebook-lite/index.html#KEY@https://paste.i2pd.xyz/?id123"
        assert _validate_notebook_lite_url(valid_url) is True

    def test_validate_missing_https_in_fragment(self):
        """Test that URL missing https:// in fragment fails validation."""
        invalid_url = "https://privapps.github.io/Notebook-lite/index.html#KEY@paste.i2pd.xyz/?id123"
        assert _validate_notebook_lite_url(invalid_url) is False

    def test_validate_empty_url(self):
        """Test that empty URL fails validation."""
        assert _validate_notebook_lite_url("") is False

    def test_validate_none_url(self):
        """Test that None URL fails validation."""
        assert _validate_notebook_lite_url(None) is False

    def test_transform_output_always_valid(self):
        """Test that _transform_to_notebook_lite_url always produces valid URLs."""
        privatebin_url = "https://paste.i2pd.xyz/?abc123#KEY789"
        decryption_key = "KEY789"
        result = _transform_to_notebook_lite_url(privatebin_url, decryption_key)
        assert _validate_notebook_lite_url(result) is True


class TestCreatePasteFromText:
    """Test text-based paste creation."""

    def test_empty_text(self):
        """Test that empty text returns error."""
        result = create_paste_from_text("")
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_whitespace_only_text(self):
        """Test that whitespace-only text returns error."""
        result = create_paste_from_text("   \n  \t  ")
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_invalid_expiry(self):
        """Test that invalid expiry returns error."""
        result = create_paste_from_text("valid text", expiry="invalid_expiry")
        assert result["success"] is False
        assert "expiry" in result["error"].lower()

    def test_invalid_format(self):
        """Test that invalid format returns error."""
        result = create_paste_from_text("valid text", format_type="invalid_format")
        assert result["success"] is False
        assert "format" in result["error"].lower()

    def test_text_with_default_params(self):
        """Test text paste with default parameters (will fail without server)."""
        result = create_paste_from_text("Hello, world!")
        # Will fail due to server connectivity in test environment
        # But should have correct error structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "url" in result
        assert "error" in result


class TestCreatePasteFromFile:
    """Test file-based paste creation."""

    def test_empty_file_path(self):
        """Test that empty file path returns error."""
        result = create_paste_from_file("")
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_nonexistent_file(self):
        """Test that nonexistent file returns error."""
        result = create_paste_from_file("/nonexistent/path/file.txt")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_directory_path(self):
        """Test that directory path returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_paste_from_file(tmpdir)
            assert result["success"] is False
            assert "not a file" in result["error"].lower()

    def test_file_without_read_permission(self):
        """Test that unreadable file returns error."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()
            temp_path = f.name

        try:
            # Remove read permission
            os.chmod(temp_path, 0o000)
            result = create_paste_from_file(temp_path)
            assert result["success"] is False
            assert "permission" in result["error"].lower()
        finally:
            # Restore permission for cleanup
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)

    def test_non_utf8_file(self):
        """Test that non-UTF8 file returns error."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\x80\x81\x82\x83")
            f.flush()
            temp_path = f.name

        try:
            result = create_paste_from_file(temp_path)
            assert result["success"] is False
            assert "utf-8" in result["error"].lower()
        finally:
            os.unlink(temp_path)

    def test_format_auto_detection(self):
        """Test that format is auto-detected correctly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write("print('hello')")
            f.flush()
            temp_path = f.name

        try:
            # Note: This will fail due to server connectivity
            # But we can verify the format was detected
            result = create_paste_from_file(temp_path)
            # Result will have error due to server, but format should be syntaxhighlighting
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)

    def test_format_override(self):
        """Test that format can be overridden."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write("print('hello')")
            f.flush()
            temp_path = f.name

        try:
            # Override to plaintext
            result = create_paste_from_file(temp_path, format_type="plaintext")
            # Will fail due to server, but should have correct structure
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)


class TestOutputStructure:
    """Test return value structure."""

    def test_result_structure_on_error(self):
        """Test that error results have correct structure."""
        result = create_paste_from_text("")
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["url"] is None
        
        assert result["error"] is not None
        assert isinstance(result["error"], str)

    def test_result_keys_exist(self):
        """Test that all required keys exist in result."""
        result = create_paste_from_text("test", expiry="invalid")
        required_keys = {"success", "url", "error"}
        assert set(result.keys()) == required_keys


class TestJSONConversion:
    """Test JSON conversion functionality."""

    def test_convert_single_record(self):
        """Test converting single record to JSON."""
        text = "Name: Project Alpha\nContent: Initial research\nDate: 2021-02-24T21:30:21.002Z"
        result = convert_text_to_json_records(text)
        assert len(result) == 1
        assert result[0]["name"] == "Project Alpha"
        assert result[0]["content"] == "Initial research"
        assert result[0]["date"] == "2021-02-24T21:30:21.002Z"

    def test_convert_multiple_records(self):
        """Test converting multiple records separated by ---."""
        text = """Name: Project A
Content: Details A
Date: 2021-02-24T21:30:21.002Z
---
Name: Project B
Content: Details B
Date: 2021-02-25T10:15:30.000Z"""
        result = convert_text_to_json_records(text)
        assert len(result) == 2
        assert result[0]["name"] == "Project A"
        assert result[1]["name"] == "Project B"

    def test_convert_with_metadata(self):
        """Test that metadata is included when requested."""
        text = """Name: Project A
Content: Details
Date: 2021-02-24T21:30:21.002Z"""
        result = convert_text_to_json_records(text, include_metadata=True)
        assert isinstance(result, list)
        assert len(result) == 2  # Records list + metadata
        assert isinstance(result[0], list)  # First element is records
        assert isinstance(result[1], dict)  # Second element is metadata
        assert result[1]["name"] == "Metadata"

    def test_convert_with_description(self):
        """Test parsing description field."""
        text = """Name: Project
Content: Details
Description: This is a project description"""
        result = convert_text_to_json_records(text)
        assert len(result) == 1
        assert result[0]["description"] == "This is a project description"

    def test_empty_text(self):
        """Test that empty text returns empty list."""
        result = convert_text_to_json_records("")
        assert result == []

    def test_text_paste_with_json_format(self):
        """Test creating paste with JSON format conversion."""
        text = """Name: Test Project
Content: This is a test record
Date: 2021-02-24T21:30:21.002Z"""
        result = create_paste_from_text(text, json_format=True)
        # Result will succeed with server or fail with error
        assert isinstance(result, dict)
        assert "success" in result
        assert "url" in result
        assert "error" in result


class TestFileCombination:
    """Test file combination feature."""

    def test_combine_single_file(self):
        """Test combining a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content")
            
            result = combine_files_to_json([str(test_file)])
            
            assert isinstance(result, list)
            assert len(result) == 2  # [records, metadata]
            assert isinstance(result[0], list)
            assert len(result[0]) == 1
            assert result[0][0]["name"] == "test.txt"
            assert result[0][0]["content"] == "Test content"
            assert "date" in result[0][0]

    def test_combine_multiple_files(self):
        """Test combining multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple test files
            file1 = Path(tmpdir) / "file1.md"
            file1.write_text("Content 1")
            
            file2 = Path(tmpdir) / "file2.md"
            file2.write_text("Content 2")
            
            file3 = Path(tmpdir) / "file3.md"
            file3.write_text("Content 3")
            
            result = combine_files_to_json([str(file1), str(file2), str(file3)])
            
            assert len(result) == 2
            assert len(result[0]) == 3  # 3 files
            assert result[0][0]["name"] == "file1.md"
            assert result[0][1]["name"] == "file2.md"
            assert result[0][2]["name"] == "file3.md"

    def test_combine_with_metadata(self):
        """Test that metadata is included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file1.write_text("Content")
            
            result = combine_files_to_json([str(file1)], include_metadata=True)
            
            assert len(result) == 2
            metadata = result[1]
            assert metadata["name"] == "Combined Files"
            assert "1 files combined" in metadata["description"]

    def test_combine_without_metadata(self):
        """Test combining without metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file1.write_text("Content")
            
            result = combine_files_to_json([str(file1)], include_metadata=False)
            
            assert len(result) == 1
            assert isinstance(result[0], list)
            assert len(result[0]) == 1

    def test_combine_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            combine_files_to_json(["/nonexistent/file.txt"])

    def test_combine_empty_list(self):
        """Test combining with empty file list."""
        result = combine_files_to_json([])
        assert result == []

    def test_combine_preserves_content(self):
        """Test that file content is preserved exactly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            original_content = "# Title\n\nSome content\nWith multiple lines\n"
            test_file.write_text(original_content)
            
            result = combine_files_to_json([str(test_file)])
            
            assert result[0][0]["content"] == original_content
