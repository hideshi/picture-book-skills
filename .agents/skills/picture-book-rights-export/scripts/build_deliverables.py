#!/usr/bin/env python3
"""Build EPUB, standalone HTML, and spread PDF into a project's dist directory."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from export_common import load_project, safe_filename


SCRIPT_DIR = Path(__file__).resolve().parent
EPUB_BUILDER = (
    Path(__file__).resolve().parents[2]
    / "picture-book-epub"
    / "scripts"
    / "build_fixed_layout.py"
)


def add_common_options(command: list[str], args) -> None:
    if args.art_dir:
        command.extend(["--art-dir", args.art_dir])
    if args.cover:
        command.extend(["--cover", args.cover])
    if args.title:
        command.extend(["--title", args.title])
    if args.author:
        command.extend(["--author", args.author])
    if args.pages:
        command.extend(["--pages", str(args.pages)])


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("project_dir", nargs="?", default=".")
    result.add_argument("--art-dir")
    result.add_argument("--cover")
    result.add_argument("--cover-text-mode", choices=("overlay", "embedded", "none"), default="overlay")
    result.add_argument("--output-dir")
    result.add_argument("--title")
    result.add_argument("--author")
    result.add_argument("--pages", type=int)
    result.add_argument(
        "--formats",
        default="epub,html,pdf",
        help="Comma-separated subset of epub,html,pdf",
    )
    result.add_argument("--disclosure", action="append", default=[])
    result.add_argument("--allow-missing-epubcheck", action="store_true")
    result.add_argument("--embed-html-images", action="store_true", help="Make HTML outputs standalone by embedding images")
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
    formats = {value.strip().lower() for value in args.formats.split(",") if value.strip()}
    unknown = formats - {"epub", "html", "pdf"}
    if unknown or not formats:
        raise ValueError(f"Invalid --formats value: {args.formats}")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else project.root / "dist"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(project.title)
    final_paths = {
        "epub": output_dir / f"{stem}_固定レイアウト版.epub",
        "viewer_html": output_dir / f"{stem}_通し読みビューアー.html",
        "spread_html": output_dir / f"{stem}_見開き冊子.html",
        "pdf": output_dir / f"{stem}_通し読み見開き冊子.pdf",
    }
    tasks: list[str] = []
    if "epub" in formats:
        tasks.append("epub")
    if "html" in formats:
        tasks.extend(["viewer_html", "spread_html"])
    if "pdf" in formats:
        tasks.append("pdf")

    with tempfile.TemporaryDirectory(prefix=".deliverables-", dir=output_dir) as directory:
        staging = Path(directory)
        commands: dict[str, list[str]] = {
            "epub": [
                sys.executable,
                str(EPUB_BUILDER),
                str(project.root),
                "--output",
                str(staging / final_paths["epub"].name),
                "--rendered-dir",
                str(project.root / "rendered_pages"),
            ],
            "viewer_html": [
                sys.executable,
                str(SCRIPT_DIR / "build_html_viewer.py"),
                str(project.root),
                "--output",
                str(staging / final_paths["viewer_html"].name),
                "--relative-to",
                str(output_dir),
            ],
            "spread_html": [
                sys.executable,
                str(SCRIPT_DIR / "build_spread_html.py"),
                str(project.root),
                "--output",
                str(staging / final_paths["spread_html"].name),
                "--relative-to",
                str(output_dir),
            ],
            "pdf": [
                sys.executable,
                str(SCRIPT_DIR / "build_spread_pdf.py"),
                str(project.root),
                "--output",
                str(staging / final_paths["pdf"].name),
            ],
        }
        for command in commands.values():
            add_common_options(command, args)
        commands["epub"].extend(["--cover-text-mode", args.cover_text_mode])
        if args.embed_html_images:
            commands["viewer_html"].append("--embed-images")
            commands["spread_html"].append("--embed-images")
        for disclosure in args.disclosure:
            commands["epub"].extend(["--disclosure", disclosure])
        if "epub" in formats and not args.allow_missing_epubcheck:
            commands["epub"].append("--require-epubcheck")

        for task in tasks:
            subprocess.run(commands[task], check=True)
        for task in tasks:
            staged = staging / final_paths[task].name
            if not staged.exists() or staged.stat().st_size == 0:
                raise RuntimeError(f"Missing staged {task} output: {staged}")
        for task in tasks:
            (staging / final_paths[task].name).replace(final_paths[task])

    print("Deliverables created:")
    for task in tasks:
        size = final_paths[task].stat().st_size / (1024 * 1024)
        print(f" - {final_paths[task]} ({size:.2f} MiB)")


if __name__ == "__main__":
    main()
