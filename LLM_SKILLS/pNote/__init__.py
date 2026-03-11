"""
pBin Paste Skill - Public API
"""

from skill import (
    create_paste_from_file,
    create_paste_from_text,
    PasteResult,
)

__all__ = [
    "create_paste_from_text",
    "create_paste_from_file",
    "PasteResult",
]
