"""Command line interface for rendering thumbnail templates."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable

from thumbnail_automatic import ThumbnailTemplate, load_config


def default_config_path() -> Path:
    """Return the bundled sample configuration path."""

    return Path(__file__).resolve().parent / "config" / "sample_thumbnail.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a thumbnail from a JSON configuration. If you do not pass a file, "
            "the bundled sample template will be used so you can test things quickly."
        )
    )
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        default=default_config_path(),
        help="Path to the JSON configuration file. Defaults to the sample template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Overrides the path defined inside the configuration file.",
    )
    parser.add_argument(
        "--text",
        action="append",
        default=[],
        metavar="ID=VALUE",
        help="Override the text for a block with the matching 'id' field in the configuration.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for new text values in the terminal instead of passing --text overrides.",
    )
    return parser.parse_args()


def apply_text_overrides(config: Dict, overrides: Iterable[str]) -> None:
    if not overrides:
        return
    blocks = config.get("blocks", [])
    lookup = {block.get("id"): block for block in blocks if isinstance(block, dict) and block.get("id")}

    for pair in overrides:
        if "=" not in pair:
            raise ValueError(f"Invalid override '{pair}'. Expected format ID=VALUE")
        key, value = pair.split("=", 1)
        key = key.strip()
        if key not in lookup:
            raise KeyError(f"No block with id '{key}' defined in configuration")
        lookup[key]["text"] = value


def prompt_for_text(config: Dict) -> None:
    """Interactively ask the user for new copy for each block that has an id."""

    blocks = config.get("blocks", [])
    if not blocks:
        return

    print("Nhập nội dung mới cho từng phần (ấn Enter để giữ nguyên văn bản cũ):")
    for block in blocks:
        block_id = block.get("id")
        if not block_id:
            continue
        current_text = str(block.get("text", ""))
        prompt = f"  {block_id} [{current_text}]: "
        try:
            response = input(prompt)
        except EOFError:
            response = ""
        if response.strip():
            block["text"] = response
    print()


def main() -> None:
    args = parse_args()
    config_path = args.config
    if not config_path.exists():
        raise SystemExit(f"Config file '{config_path}' not found")

    config = load_config(config_path)
    if args.interactive:
        prompt_for_text(config)
    try:
        apply_text_overrides(config, args.text)
    except (ValueError, KeyError) as exc:
        raise SystemExit(str(exc)) from exc

    output_path = args.output or config.get("output_path")
    if not output_path:
        output_path = Path("output/thumbnail.png")
    else:
        output_path = Path(output_path)

    template = ThumbnailTemplate(config)
    template.save(output_path)
    print(f"Thumbnail saved to {output_path}")


if __name__ == "__main__":
    main()
