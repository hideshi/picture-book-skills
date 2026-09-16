#!/usr/bin/env python3
"""Build the image-page fixed-layout EPUB profile used by picture-book-epub.

This builder keeps the adopted prose as a separate source file, renders a
compatibility-first page image, and records the prose in image alternatives.
It does not by itself prove store compatibility; run the target-reader checks
required by the skill.
"""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
import uuid
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw, ImageFont


DEFAULT_WIDTH = 1440
DEFAULT_HEIGHT = 1920
BACKGROUND = (250, 248, 245)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_prose(path: Path) -> dict[int, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing adopted prose: {path}")
    content = read_text(path)
    heading = re.search(r"^##\s*採用本文[^\n]*$", content, re.MULTILINE)
    if not heading:
        raise ValueError(f"Could not find '## 採用本文' in {path}")
    section = content[heading.end() :]
    next_h2 = re.search(r"^##\s+", section, re.MULTILINE)
    if next_h2:
        section = section[: next_h2.start()]

    pages: dict[int, list[str]] = {}
    blocks = re.split(r"^###\s*(\d+)(?:[^\n]*)$", section, flags=re.MULTILINE)
    for index in range(1, len(blocks), 2):
        page_number = int(blocks[index])
        lines = []
        for raw in blocks[index + 1].splitlines():
            line = raw.strip()
            if not line or line.startswith("<!--") or line.startswith("（拍"):
                continue
            if line in {"（文なし）", "(文なし)"}:
                continue
            lines.append(line)
        pages[page_number] = lines
    if not pages:
        raise ValueError(f"No numbered adopted-prose pages found in {path}")
    return pages


def parse_brief(path: Path) -> tuple[str | None, str | None, int | None]:
    if not path.exists():
        return None, None, None
    content = read_text(path)
    title_match = re.search(r"仮題:\s*([^\n\r]+)", content)
    credited_author_match = re.search(
        r"^(?:著者(?:名|・クレジット名)?|creator)\s*:\s*([^\n\r]+)",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    decision_maker_match = re.search(
        r"^##\s*7\.\s*答え責任[^\n]*\n+(?:\s*\n)*([^\n\r#]+)",
        content,
        re.MULTILINE,
    )
    pages_match = re.search(r"本文\s*[*_]*(\d+)\s*頁", content)
    return (
        title_match.group(1).strip() if title_match else None,
        (
            credited_author_match.group(1).strip()
            if credited_author_match
            else decision_maker_match.group(1).strip()
            if decision_maker_match
            else None
        ),
        int(pages_match.group(1)) if pages_match else None,
    )


def select_art_dir(project_dir: Path, requested: str | None) -> Path:
    if requested:
        candidate = Path(requested)
        if not candidate.is_absolute():
            candidate = project_dir / candidate
        if not candidate.is_dir():
            raise FileNotFoundError(f"Art directory does not exist: {candidate}")
        return candidate
    for name in ("final-art", "final_art", "art", "rough"):
        candidate = project_dir / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "No art directory found. Use --art-dir or create final-art/, art/, or rough/."
    )


def infer_page_count(
    requested: int | None,
    brief_pages: int | None,
    prose: dict[int, list[str]],
    art_dir: Path,
) -> int:
    if requested:
        return requested
    if brief_pages:
        return brief_pages
    art_pages = [
        int(match.group(1))
        for path in art_dir.iterdir()
        if (match := re.fullmatch(r"p(\d+)\.(?:png|jpe?g)", path.name, re.I))
    ]
    candidates = list(prose)
    candidates.extend(art_pages)
    if not candidates:
        raise ValueError("Could not infer page count; pass --pages.")
    return max(candidates)


def locate_page_art(art_dir: Path, page_number: int) -> Path:
    for suffix in (".png", ".jpg", ".jpeg"):
        path = art_dir / f"p{page_number:02d}{suffix}"
        if path.exists():
            return path
    raise FileNotFoundError(f"Missing art for page {page_number}: {art_dir}/pNN.(png|jpg)")


def locate_cover(project_dir: Path, art_dir: Path, requested: str | None) -> Path:
    if requested:
        path = Path(requested)
        if not path.is_absolute():
            path = project_dir / path
    else:
        path = art_dir / "cover.png"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing dedicated cover image: {path}. Pass --cover; body-page fallback is disabled."
        )
    return path


def find_font(requested: str | None, *, bold: bool = False) -> Path:
    if requested:
        path = Path(requested)
        if not path.exists():
            raise FileNotFoundError(f"Font does not exist: {path}")
        return path
    candidates = (
        [
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",
            "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
            "/usr/share/fonts/opentype/ipaexfont-mincho/ipaexm.ttf",
        ]
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    kind = "bold" if bold else "regular"
    raise FileNotFoundError(f"No Japanese {kind} font found; pass --font/--bold-font.")


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        box = draw.textbbox((0, 0), candidate, font=font)
        if current and box[2] - box[0] > width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fit_image(source: Path, max_width: int, max_height: int) -> Image.Image:
    image = Image.open(source).convert("RGB")
    scale = min(max_width / image.width, max_height / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def render_pages(
    rendered_dir: Path,
    art_dir: Path,
    cover_path: Path,
    page_art: dict[int, Path],
    prose: dict[int, list[str]],
    title: str,
    author: str,
    page_count: int,
    width: int,
    height: int,
    regular_font_path: Path,
    bold_font_path: Path,
    disclosure: list[str],
    cover_text_mode: str,
) -> list[tuple[str, Path, str, str, str]]:
    rendered_dir.mkdir(parents=True, exist_ok=True)
    for stale in rendered_dir.glob("page_*.png"):
        stale.unlink()

    scale = width / DEFAULT_WIDTH
    body_font = ImageFont.truetype(str(regular_font_path), max(20, round(54 * scale)))
    number_font = ImageFont.truetype(str(regular_font_path), max(14, round(32 * scale)))
    title_font = ImageFont.truetype(str(bold_font_path), max(32, round(88 * scale)))
    author_font = ImageFont.truetype(str(regular_font_path), max(20, round(42 * scale)))
    colophon_font = ImageFont.truetype(str(regular_font_path), max(16, round(28 * scale)))

    top_height = round(height * 0.26)
    image_top = round(height * 0.292)
    image_box = (round(width * 0.944), round(height * 0.599))
    margin = round(width * 0.055)

    if cover_text_mode == "embedded":
        cover_canvas = fit_image(cover_path, width, height)
        if cover_canvas.size != (width, height):
            page = Image.new("RGB", (width, height), BACKGROUND)
            page.paste(cover_canvas, ((width - cover_canvas.width) // 2, (height - cover_canvas.height) // 2))
            cover_canvas = page
    else:
        cover_canvas = Image.new("RGB", (width, height), BACKGROUND)
        if cover_text_mode == "overlay":
            cover_draw = ImageDraw.Draw(cover_canvas)
            title_lines = wrap_text(cover_draw, title, title_font, width - 2 * margin)
            y = round(height * 0.07)
            for line in title_lines:
                box = cover_draw.textbbox((0, 0), line, font=title_font)
                cover_draw.text(((width - (box[2] - box[0])) / 2, y), line, font=title_font, fill=(24, 24, 24))
                y += round(title_font.size * 1.25)
            author_text = f"作・構成　{author}"
            box = cover_draw.textbbox((0, 0), author_text, font=author_font)
            cover_draw.text(((width - (box[2] - box[0])) / 2, y + round(20 * scale)), author_text, font=author_font, fill=(70, 70, 70))
        cover_art = fit_image(cover_path, *image_box)
        cover_canvas.paste(cover_art, ((width - cover_art.width) // 2, image_top + (image_box[1] - cover_art.height) // 2))
    rendered_cover = rendered_dir / "page_cover.png"
    cover_canvas.save(rendered_cover)

    page_entries: list[tuple[str, Path, str, str, str]] = [
        ("cover", rendered_cover, "", "表紙", f"{title}の表紙")
    ]

    for page_number in range(1, page_count + 1):
        canvas = Image.new("RGB", (width, height), BACKGROUND)
        draw = ImageDraw.Draw(canvas)
        visual_lines: list[str] = []
        for source_line in prose.get(page_number, []):
            visual_lines.extend(wrap_text(draw, source_line, body_font, width - 2 * margin))
        line_height = round(body_font.size * 1.55)
        text_height = len(visual_lines) * line_height
        y = max(round(height * 0.035), (top_height - text_height) // 2)
        for line in visual_lines:
            box = draw.textbbox((0, 0), line, font=body_font)
            draw.text(((width - (box[2] - box[0])) / 2, y), line, font=body_font, fill=(28, 28, 28))
            y += line_height

        page_image = fit_image(page_art[page_number], *image_box)
        canvas.paste(page_image, ((width - page_image.width) // 2, image_top + (image_box[1] - page_image.height) // 2))
        page_label = str(page_number)
        box = draw.textbbox((0, 0), page_label, font=number_font)
        x = margin if page_number % 2 == 0 else width - margin - (box[2] - box[0])
        draw.text((x, round(height * 0.948)), page_label, font=number_font, fill=(140, 140, 140))

        rendered = rendered_dir / f"page_{page_number:02d}.png"
        canvas.save(rendered)
        spread = "page-spread-left" if page_number % 2 == 0 else "page-spread-right"
        spoken = " ".join(prose.get(page_number, []))
        alt = f"{page_number}ページの挿絵。{spoken}" if spoken else f"{page_number}ページの文字のない挿絵"
        page_entries.append((f"p_{page_number:02d}", rendered, spread, f"{page_number}ページ", alt))

    colophon = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(colophon)
    y = round(height * 0.32)
    draw.text((round(width * 0.14), y), title, font=ImageFont.truetype(str(bold_font_path), max(24, round(52 * scale))), fill=(30, 30, 30))
    y += round(140 * scale)
    draw.text((round(width * 0.14), y), f"作・構成: {author}", font=colophon_font, fill=(50, 50, 50))
    for line in disclosure:
        y += round(colophon_font.size * 1.7)
        for wrapped in wrap_text(draw, line, colophon_font, round(width * 0.72)):
            draw.text((round(width * 0.14), y), wrapped, font=colophon_font, fill=(90, 90, 90))
            y += round(colophon_font.size * 1.4)
    rendered_colophon = rendered_dir / "page_colophon.png"
    colophon.save(rendered_colophon)
    next_number = page_count + 1
    colophon_spread = "page-spread-left" if next_number % 2 == 0 else "page-spread-right"
    page_entries.append(("colophon", rendered_colophon, colophon_spread, "奥付", f"{title}の奥付。作・構成 {author}"))
    return page_entries


def modified_timestamp(paths: list[Path], requested: str | None) -> str:
    if requested:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", requested):
            raise ValueError("--modified must be UTC in YYYY-MM-DDTHH:MM:SSZ form")
        return requested
    latest = max(path.stat().st_mtime for path in paths)
    return datetime.fromtimestamp(latest, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def xml(value: str) -> str:
    return html.escape(value, quote=True)


def package_epub(
    entries: list[tuple[str, Path, str, str, str]],
    output: Path,
    title: str,
    author: str,
    language: str,
    identifier: str,
    modified: str,
    width: int,
    height: int,
    progression: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="picture-book-epub-") as temporary:
        root = Path(temporary)
        meta_inf = root / "META-INF"
        oebps = root / "OEBPS"
        images = oebps / "images"
        css = oebps / "css"
        for directory in (meta_inf, images, css):
            directory.mkdir(parents=True, exist_ok=True)

        (root / "mimetype").write_text("application/epub+zip", encoding="ascii")
        (meta_inf / "container.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/package.opf" '
            'media-type="application/oebps-package+xml"/></rootfiles></container>',
            encoding="utf-8",
        )
        (meta_inf / "com.apple.ibooks.display-options.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<display_options><platform name="*"><option name="fixed-layout">true</option>'
            '<option name="orientation-lock">none</option></platform></display_options>',
            encoding="utf-8",
        )
        (css / "style.css").write_text(
            f"* {{ margin:0; padding:0; box-sizing:border-box; }}\n"
            f"html,body,.page-full {{ width:{width}px; height:{height}px; overflow:hidden; }}\n"
            ".page-full img { width:100%; height:100%; display:block; }\n",
            encoding="utf-8",
        )

        for page_id, source, _, description, alt in entries:
            image_name = source.name
            shutil.copyfile(source, images / image_name)
            epub_type = ' epub:type="cover"' if page_id == "cover" else ""
            xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{xml(language)}" lang="{xml(language)}">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width={width}, height={height}"/>
  <title>{xml(title)} - {xml(description)}</title>
  <link rel="stylesheet" type="text/css" href="css/style.css"/>
</head>
<body{epub_type}><div class="page-full"><img src="images/{xml(image_name)}" alt="{xml(alt)}"/></div></body>
</html>"""
            (oebps / f"{page_id}.xhtml").write_text(xhtml, encoding="utf-8")

        body_id = next(page_id for page_id, *_ in entries if page_id.startswith("p_"))
        toc_items = "\n".join(
            f'      <li><a href="{page_id}.xhtml">{xml(description)}</a></li>'
            for page_id, _, _, description, _ in entries
        )
        page_list = "\n".join(
            f'      <li><a href="{page_id}.xhtml">{xml(description)}</a></li>'
            for page_id, _, _, description, _ in entries
            if page_id.startswith("p_")
        )
        nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{xml(language)}" lang="{xml(language)}">
<head><meta charset="utf-8"/><title>目次</title></head>
<body>
  <nav epub:type="toc" id="toc"><h1>目次</h1><ol>
{toc_items}
  </ol></nav>
  <nav epub:type="page-list" hidden=""><h2>ページ一覧</h2><ol>
{page_list}
  </ol></nav>
  <nav epub:type="landmarks" hidden=""><h2>ランドマーク</h2><ol>
    <li><a epub:type="cover" href="cover.xhtml">表紙</a></li>
    <li><a epub:type="bodymatter" href="{body_id}.xhtml">本文開始</a></li>
  </ol></nav>
</body>
</html>"""
        (oebps / "nav.xhtml").write_text(nav, encoding="utf-8")

        manifest = [
            '<item id="style" href="css/style.css" media-type="text/css"/>',
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        ]
        spine: list[str] = []
        for page_id, source, spread, _, _ in entries:
            cover_property = ' properties="cover-image"' if page_id == "cover" else ""
            manifest.append(
                f'<item id="img_{page_id}" href="images/{xml(source.name)}" media-type="image/png"{cover_property}/>'
            )
            manifest.append(
                f'<item id="{page_id}" href="{page_id}.xhtml" media-type="application/xhtml+xml"/>'
            )
            spread_property = f' properties="{spread}"' if spread else ""
            spine.append(f'<itemref idref="{page_id}"{spread_property}/>')

        package = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{xml(identifier)}</dc:identifier>
    <dc:title>{xml(title)}</dc:title>
    <dc:creator>{xml(author)}</dc:creator>
    <dc:language>{xml(language)}</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
    <meta name="cover" content="img_cover"/>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">auto</meta>
    <meta name="fixed-layout" content="true"/>
    <meta name="original-resolution" content="{width}x{height}"/>
    <meta name="book-type" content="children"/>
    <meta name="orientation-lock" content="none"/>
  </metadata>
  <manifest>
    {"".join(manifest)}
  </manifest>
  <spine page-progression-direction="{progression}">
    {"".join(spine)}
  </spine>
  <guide>
    <reference type="cover" title="表紙" href="cover.xhtml"/>
    <reference type="text" title="本文" href="{body_id}.xhtml"/>
  </guide>
</package>"""
        (oebps / "package.opf").write_text(package, encoding="utf-8")

        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = output.with_suffix(output.suffix + ".tmp")
        if temporary_output.exists():
            temporary_output.unlink()
        with zipfile.ZipFile(temporary_output, "w") as archive:
            archive.write(root / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
            for directory in (meta_inf, oebps):
                for path in sorted(directory.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(root), compress_type=zipfile.ZIP_DEFLATED)
        temporary_output.replace(output)


def validate_package(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if not members or members[0].filename != "mimetype":
            raise ValueError("EPUB mimetype must be the first ZIP member")
        if members[0].compress_type != zipfile.ZIP_STORED:
            raise ValueError("EPUB mimetype must be stored without compression")
        if archive.read("mimetype") != b"application/epub+zip":
            raise ValueError("Invalid EPUB mimetype content")
        broken = archive.testzip()
        if broken:
            raise ValueError(f"Corrupt ZIP member: {broken}")
        for member in members:
            if member.filename.endswith((".xml", ".xhtml", ".opf")):
                ET.fromstring(archive.read(member))


def run_epubcheck(path: Path, required: bool, skipped: bool) -> str:
    if skipped:
        return "EPUBCheck: skipped by --skip-epubcheck"
    executable = shutil.which("epubcheck")
    if not executable:
        if required:
            raise RuntimeError("EPUBCheck is required but the epubcheck executable was not found")
        return "EPUBCheck: not installed (internal package/XML validation passed)"
    subprocess.run([executable, str(path)], check=True)
    return f"EPUBCheck: passed ({executable})"


def safe_filename(title: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", title).strip(" .")
    return cleaned or "picture-book"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--art-dir", help="Final-art directory, relative to project by default")
    parser.add_argument("--cover", help="Dedicated cover image, relative to project by default")
    parser.add_argument("--cover-text-mode", choices=("overlay", "embedded", "none"), default="overlay", help="Cover title handling: overlay generated title, preserve embedded cover design, or omit title")
    parser.add_argument("--output", help="Output EPUB; defaults to dist/<title>_固定レイアウト版.epub")
    parser.add_argument("--rendered-dir", help="Intermediate rendered pages; defaults to rendered_pages/")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--pages", type=int)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--font")
    parser.add_argument("--bold-font")
    parser.add_argument("--language", default="ja")
    parser.add_argument("--page-progression", choices=("ltr", "rtl"), default="ltr")
    parser.add_argument("--identifier")
    parser.add_argument("--modified", help="UTC timestamp: YYYY-MM-DDTHH:MM:SSZ")
    parser.add_argument("--disclosure", action="append", default=[])
    parser.add_argument("--disclosure-file")
    parser.add_argument("--require-epubcheck", action="store_true")
    parser.add_argument("--skip-epubcheck", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.width <= 0 or args.height <= 0:
        raise ValueError("--width and --height must be positive")
    if args.require_epubcheck and args.skip_epubcheck:
        raise ValueError("--require-epubcheck and --skip-epubcheck cannot be combined")

    project_dir = Path(args.project_dir).resolve()
    brief_path = project_dir / "brief.md"
    prose_path = project_dir / "prose.md"
    brief_title, brief_author, brief_pages = parse_brief(brief_path)
    title = args.title or brief_title
    author = args.author or brief_author
    if not title or not author:
        raise ValueError("Title and author are required in brief.md or via --title/--author")

    art_dir = select_art_dir(project_dir, args.art_dir)
    cover_path = locate_cover(project_dir, art_dir, args.cover)
    prose = parse_prose(prose_path)
    page_count = infer_page_count(args.pages, brief_pages, prose, art_dir)
    page_art = {number: locate_page_art(art_dir, number) for number in range(1, page_count + 1)}
    regular_font = find_font(args.font)
    bold_font = find_font(args.bold_font, bold=True)
    rendered_dir = Path(args.rendered_dir).resolve() if args.rendered_dir else project_dir / "rendered_pages"
    output = Path(args.output).resolve() if args.output else project_dir / "dist" / f"{safe_filename(title)}_固定レイアウト版.epub"

    disclosure = list(args.disclosure)
    if args.disclosure_file:
        disclosure_path = Path(args.disclosure_file)
        if not disclosure_path.is_absolute():
            disclosure_path = project_dir / disclosure_path
        disclosure.extend(line.strip() for line in read_text(disclosure_path).splitlines() if line.strip())

    inputs = [brief_path, prose_path, cover_path, *page_art.values()]
    modified = modified_timestamp([path for path in inputs if path.exists()], args.modified)
    identifier = args.identifier or f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, title + '|' + author)}"

    entries = render_pages(
        rendered_dir,
        art_dir,
        cover_path,
        page_art,
        prose,
        title,
        author,
        page_count,
        args.width,
        args.height,
        regular_font,
        bold_font,
        disclosure,
        args.cover_text_mode,
    )
    package_epub(
        entries,
        output,
        title,
        author,
        args.language,
        identifier,
        modified,
        args.width,
        args.height,
        args.page_progression,
    )
    validate_package(output)
    epubcheck_result = run_epubcheck(output, args.require_epubcheck, args.skip_epubcheck)
    print(f"EPUB created: {output}")
    print(f"Art source: {art_dir}")
    print(f"Pages: {page_count}; viewport: {args.width}x{args.height}; body start: p_01.xhtml")
    print(epubcheck_result)


if __name__ == "__main__":
    main()
