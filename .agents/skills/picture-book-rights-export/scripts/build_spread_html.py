#!/usr/bin/env python3
"""Build a self-contained print/spread HTML booklet from a picture-book project."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_spread_pdf import render_print_html
from export_common import body_groups, load_project, safe_filename


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("project_dir", nargs="?", default=".")
    result.add_argument("--art-dir")
    result.add_argument("--cover")
    result.add_argument("--output")
    result.add_argument("--title")
    result.add_argument("--author")
    result.add_argument("--pages", type=int)
    result.add_argument("--embed-images", action="store_true", help="Embed images for a standalone HTML file")
    result.add_argument("--relative-to", help="Directory used for relative image links")
    return result


def main() -> None:
    args = parser().parse_args()
    project = load_project(
        args.project_dir,
        art_dir=args.art_dir,
        cover=args.cover,
        title=args.title,
        author=args.author,
        pages=args.pages,
    )
    output = (
        Path(args.output).resolve()
        if args.output
        else project.root / "dist" / f"{safe_filename(project.title)}_見開き冊子.html"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    relative_to = Path(args.relative_to).resolve() if args.relative_to else output.parent
    output.write_text(
        render_print_html(
            project,
            embed_images=args.embed_images,
            relative_to=None if args.embed_images else relative_to,
        ),
        encoding="utf-8",
    )
    if output.stat().st_size == 0:
        raise RuntimeError(f"Empty spread HTML output: {output}")
    print(f"Spread HTML created: {output}")
    print(f"Sheets: {1 + len(body_groups(project.page_count))}")
    print("Images: embedded (standalone)" if args.embed_images else f"Images: linked relative to {relative_to}")


if __name__ == "__main__":
    main()
