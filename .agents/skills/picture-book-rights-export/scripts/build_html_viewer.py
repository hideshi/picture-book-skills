#!/usr/bin/env python3
"""Build a self-contained, responsive picture-book HTML viewer."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from export_common import body_groups, image_uri, load_project, page_panel, safe_filename


def render_viewer(project, *, embed_images: bool, relative_to: Path | None = None) -> str:
    cover_uri = image_uri(project.cover, embed=embed_images, relative_to=relative_to)
    sections = [
        f"""<article class="spread cover">
  <header><strong>表紙</strong><span>作・構成: {html.escape(project.author)}</span></header>
  <div class="cover-body"><img src="{cover_uri}" alt="{html.escape(project.title)}の表紙"/></div>
</article>"""
    ]
    for index, (left, right) in enumerate(body_groups(project.page_count), start=1):
        label = (
            f"p.{right}（単独）"
            if left is None and right is not None
            else f"p.{left}–p.{right}"
            if right is not None
            else f"p.{left}（単独）"
        )
        sections.append(
            f"""<article class="spread">
  <header><strong>{label}</strong><span>見開き {index}</span></header>
  <div class="spread-body">
    {page_panel(project, left, embed=embed_images, side="left", relative_to=relative_to)}
    {page_panel(project, right, embed=embed_images, side="right", relative_to=relative_to)}
  </div>
</article>"""
        )

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(project.title)} — 通し読みビューアー</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:32px 18px 64px; background:#18191f; color:#e8edf5; }}
.book {{ width:min(1180px,100%); margin:auto; display:grid; gap:42px; }}
.book-title {{ text-align:center; }}
.book-title h1 {{ margin:0 0 8px; font-size:clamp(24px,4vw,40px); }}
.book-title p {{ margin:0; color:#aeb7c5; }}
.spread {{ background:#282a34; border-radius:14px; padding:18px; box-shadow:0 12px 36px #0006; }}
.spread header {{ display:flex; justify-content:space-between; gap:16px; padding:0 4px 12px; color:#a9cfff; }}
.spread-body {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; background:#efece6; padding:12px; border-radius:9px; }}
.page {{ position:relative; min-width:0; aspect-ratio:3/4; background:#faf8f5; color:#222; padding:5% 5% 7%; display:grid; grid-template-rows:minmax(0,1fr) auto; }}
.page.left {{ border-right:1px solid #0001; }}
.art {{ min-height:0; display:flex; align-items:center; justify-content:center; }}
.art img {{ max-width:100%; max-height:100%; object-fit:contain; }}
.prose {{ min-height:5.5em; padding-top:3%; display:flex; align-items:center; justify-content:center; text-align:center; font-family:"Noto Serif CJK JP","Yu Mincho",serif; font-size:clamp(12px,1.55vw,21px); line-height:1.75; }}
.no-text {{ color:#999; font-size:.8em; font-style:italic; }}
.page-number {{ position:absolute; bottom:2%; color:#888; font-size:12px; }}
.left .page-number {{ left:4%; }} .right .page-number {{ right:4%; }}
.blank {{ background:#f5f2ec; }}
.cover-body {{ background:#faf8f5; border-radius:9px; padding:18px; display:flex; justify-content:center; }}
.cover-body img {{ display:block; max-width:min(520px,100%); max-height:78vh; object-fit:contain; }}
@media (max-width:720px) {{
  body {{ padding:18px 8px 40px; }}
  .book {{ gap:24px; }}
  .spread {{ padding:10px; }}
  .spread-body {{ gap:5px; padding:5px; }}
  .page {{ padding:4% 3% 8%; }}
  .prose {{ font-size:clamp(9px,2.4vw,14px); }}
}}
</style>
</head>
<body>
<main class="book">
  <div class="book-title"><h1>『{html.escape(project.title)}』</h1><p>通し読み見開きビューアー・本文{project.page_count}頁</p></div>
  {"".join(sections)}
</main>
</body>
</html>"""


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
        else project.root / "dist" / f"{safe_filename(project.title)}_通し読みビューアー.html"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    relative_to = Path(args.relative_to).resolve() if args.relative_to else output.parent
    output.write_text(
        render_viewer(project, embed_images=args.embed_images, relative_to=None if args.embed_images else relative_to),
        encoding="utf-8",
    )
    if output.stat().st_size == 0:
        raise RuntimeError(f"Empty HTML output: {output}")
    print(f"HTML viewer created: {output}")
    print(f"Pages: {project.page_count}; art source: {project.art_dir}")
    print("Images: embedded (standalone)" if args.embed_images else f"Images: linked relative to {relative_to}")


if __name__ == "__main__":
    main()
