#!/usr/bin/env python3
"""
CLI entry point for pBin Paste Skill
"""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser

from skill import create_paste_from_file, create_paste_from_text, combine_files_to_json


def main() -> None:
    """Main entry point for CLI."""
    parser = ArgumentParser(
        prog="create-pbin-paste",
        description="Create PrivateBin pastes from files or text",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Text subcommand
    text_parser = subparsers.add_parser("text", help="Create paste from text")
    text_parser.add_argument("text", help="Text content to paste")
    text_parser.add_argument(
        "--expiry",
        default="1day",
        help="Expiration duration (default: 1day)",
    )
    text_parser.add_argument(
        "--burn-after-read",
        action="store_true",
        help="Delete after first read",
    )
    text_parser.add_argument(
        "--format",
        default="plaintext",
        help="Format type (default: plaintext)",
    )
    text_parser.add_argument(
        "--discussions",
        action="store_true",
        help="Enable discussions",
    )
    text_parser.add_argument(
        "--server",
        help="PrivateBin server URL",
    )
    text_parser.add_argument(
        "--json-format",
        action="store_true",
        help="Convert text to JSON records (parse Name/Content/Date fields)",
    )

    # File subcommand
    file_parser = subparsers.add_parser("file", help="Create paste from file")
    file_parser.add_argument("file_path", help="Path to file to paste")
    file_parser.add_argument(
        "--expiry",
        default="1day",
        help="Expiration duration (default: 1day)",
    )
    file_parser.add_argument(
        "--burn-after-read",
        action="store_true",
        help="Delete after first read",
    )
    file_parser.add_argument(
        "--format",
        help="Format type (overrides auto-detection)",
    )
    file_parser.add_argument(
        "--discussions",
        action="store_true",
        help="Enable discussions",
    )
    file_parser.add_argument(
        "--server",
        help="PrivateBin server URL",
    )

    # Combine subcommand
    combine_parser = subparsers.add_parser("combine", help="Combine multiple files into JSON paste")
    combine_parser.add_argument("files", nargs="+", help="File paths to combine")
    combine_parser.add_argument(
        "--expiry",
        default="1day",
        help="Expiration duration (default: 1day)",
    )
    combine_parser.add_argument(
        "--burn-after-read",
        action="store_true",
        help="Delete after first read",
    )
    combine_parser.add_argument(
        "--discussions",
        action="store_true",
        help="Enable discussions",
    )
    combine_parser.add_argument(
        "--server",
        help="PrivateBin server URL",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "text":
            result = create_paste_from_text(
                args.text,
                expiry=args.expiry,
                burn_after_read=args.burn_after_read,
                format_type=args.format,
                discussions=args.discussions,
                server=args.server,
                json_format=getattr(args, 'json_format', False),
            )
        elif args.command == "file":
            result = create_paste_from_file(
                args.file_path,
                expiry=args.expiry,
                burn_after_read=args.burn_after_read,
                format_type=args.format,
                discussions=args.discussions,
                server=args.server,
            )
        elif args.command == "combine":
            # Combine multiple files into JSON
            combined_data = combine_files_to_json(args.files, include_metadata=True)
            json_content = json.dumps(combined_data, indent=2)
            result = create_paste_from_text(
                json_content,
                expiry=args.expiry,
                burn_after_read=args.burn_after_read,
                format_type="plaintext",
                discussions=args.discussions,
                server=args.server,
            )
        else:
            parser.print_help()
            sys.exit(1)

        # Output result as JSON
        print(json.dumps(result, indent=2))

        # Exit with status code based on success
        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
