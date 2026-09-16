#!/usr/bin/env python3
"""Build an A4-landscape spread PDF from a picture-book project."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from export_common import body_groups, image_uri, load_project, page_panel, safe_filename


def render_print_html(project, *, embed_images: bool = False, relative_to: Path | None = None) -> str:
    cover_uri = image_uri(project.cover, embed=embed_images, relative_to=relative_to)
    sheets = [
        f"""<section class="sheet cover-sheet">
  <div class="cover-title"><h1>{html.escape(project.title)}</h1><p>作・構成　{html.escape(project.author)}</p></div>
  <img src="{cover_uri}" alt="{html.escape(project.title)}の表紙"/>
</section>"""
    ]
    for left, right in body_groups(project.page_count):
        sheets.append(
            f"""<section class="sheet spread">
          {page_panel(project, left, embed=embed_images, side="left", relative_to=relative_to)}
          {page_panel(project, right, embed=embed_images, side="right", relative_to=relative_to)}
</section>"""
        )
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<title>{html.escape(project.title)} — 通し読み見開き冊子</title>
<style>
@page {{ size:A4 landscape; margin:0; }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; padding:0; font-family:"Noto Serif CJK JP","Yu Mincho",serif; color:#222; }}
.sheet {{ width:297mm; height:210mm; page-break-after:always; background:#faf8f5; overflow:hidden; }}
.sheet:last-child {{ page-break-after:auto; }}
.spread {{ display:grid; grid-template-columns:1fr 1fr; }}
.page {{ position:relative; min-width:0; height:210mm; padding:9mm 12mm 10mm; display:grid; grid-template-rows:136mm auto; }}
.page.left {{ border-right:.2mm dashed #0002; }}
.art {{ display:flex; align-items:center; justify-content:center; min-height:0; }}
.art img {{ max-width:100%; max-height:136mm; object-fit:contain; }}
.prose {{ display:flex; align-items:center; justify-content:center; text-align:center; font-size:13.5pt; line-height:1.75; padding-top:4mm; }}
.no-text {{ color:#999; font-size:10pt; font-style:italic; }}
.page-number {{ position:absolute; bottom:4mm; color:#888; font:8pt sans-serif; }}
.left .page-number {{ left:10mm; }} .right .page-number {{ right:10mm; }}
.blank {{ background:#f7f4ee; }}
.cover-sheet {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:5mm; }}
.cover-title {{ width:100%; text-align:center; }}
.cover-title h1 {{ margin:0; font-size:28pt; font-weight:700; }}
.cover-title p {{ margin:3mm 0 0; font-size:14pt; color:#444; }}
.cover-sheet img {{ max-width:90%; max-height:160mm; object-fit:contain; }}
</style>
</head>
<body>{"".join(sheets)}</body>
</html>"""


def pdf_page_count(path: Path) -> int | None:
    executable = shutil.which("pdfinfo")
    if not executable:
        return None
    result = subprocess.run(
        [executable, str(path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    match = re.search(r"^Pages:\s*(\d+)", result.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("project_dir", nargs="?", default=".")
    result.add_argument("--art-dir")
    result.add_argument("--cover")
    result.add_argument("--output")
    result.add_argument("--title")
    result.add_argument("--author")
    result.add_argument("--pages", type=int)
    result.add_argument("--weasyprint", default="weasyprint")
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
    executable = shutil.which(args.weasyprint)
    if not executable:
        raise FileNotFoundError(f"WeasyPrint executable not found: {args.weasyprint}")
    output = (
        Path(args.output).resolve()
        if args.output
        else project.root / "dist" / f"{safe_filename(project.title)}_通し読み見開き冊子.pdf"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="picture-book-pdf-") as directory:
        html_path = Path(directory) / "spreads.html"
        html_path.write_text(render_print_html(project), encoding="utf-8")
        temporary_output = output.with_suffix(".pdf.tmp")
        if temporary_output.exists():
            temporary_output.unlink()
        subprocess.run([executable, str(html_path), str(temporary_output)], check=True)
        if not temporary_output.read_bytes().startswith(b"%PDF-"):
            raise RuntimeError(f"WeasyPrint did not produce a PDF: {temporary_output}")
        temporary_output.replace(output)

    expected = 1 + len(body_groups(project.page_count))
    actual = pdf_page_count(output)
    if actual is not None and actual != expected:
        raise RuntimeError(f"PDF page count mismatch: expected {expected}, got {actual}")
    print(f"Spread PDF created: {output}")
    print(f"Sheets: {actual if actual is not None else expected}; body pages: {project.page_count}")
    print(f"Art source: {project.art_dir}; renderer: {executable}")


if __name__ == "__main__":
    main()
