#!/usr/bin/env python3
"""
picture-book-epub: Fixed-Layout EPUB3 Builder for Picture Books
Complies with IDPF EPUB3, Kindle Fixed-Layout, and Google Play Books specifications.
Renders high-resolution pages (1440x1920) with upper white margin text and lower illustration.
"""

import os
import sys
import shutil
import zipfile
import uuid
import re
from PIL import Image, ImageDraw, ImageFont

PAGE_W = 1440
PAGE_H = 1920
BG_COLOR = (250, 248, 245) # Warm paper #faf8f5

def find_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",
        "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
        "/usr/share/fonts/opentype/ipaexfont-mincho/ipaexm.ttf",
    ]
    bold_candidates = [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ]
    reg = None
    bold = None
    for c in candidates:
        if os.path.exists(c):
            reg = c
            break
    for c in bold_candidates:
        if os.path.exists(c):
            bold = c
            break
    return reg, (bold or reg)

def parse_prose(prose_path):
    pages = {}
    if not os.path.exists(prose_path):
        return pages
    with open(prose_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find section "## 採用本文（頁対応"
    m = re.search(r"##\s*採用本文.*?###\s*1\b", content, re.DOTALL)
    section_text = content
    if m:
        start_idx = content.find("### 1")
        # stop before "## 不採用"
        stop_idx = content.find("## 不採用", start_idx)
        if stop_idx != -1:
            section_text = content[start_idx:stop_idx]
        else:
            section_text = content[start_idx:]

    blocks = re.split(r"###\s*(\d+)", section_text)
    for i in range(1, len(blocks), 2):
        p_num = int(blocks[i])
        body = blocks[i+1].strip()
        lines = [line.strip() for line in body.split("\n") if line.strip() and not line.startswith("（拍") and not line.startswith("<!--")]
        # Filter out (文なし)
        filtered = [l for l in lines if l != "（文なし）"]
        pages[p_num] = filtered
    return pages

def parse_brief_meta(brief_path, project_dir):
    title = "絵本"
    author = "作者"
    total_pages = 0
    if os.path.exists(brief_path):
        with open(brief_path, "r", encoding="utf-8") as f:
            txt = f.read()
        m_title = re.search(r"仮題:\s*([^\n\r]+)", txt)
        if m_title:
            title = m_title.group(1).strip()
        m_auth = re.search(r"##\s*7\.\s*答え責任[^\n]*\n+([^\n\r#]+)", txt)
        if m_auth:
            author = m_auth.group(1).strip()
        m_pages = re.search(r"本文\s*[\*]*(\d+)\s*頁", txt)
        if m_pages:
            total_pages = int(m_pages.group(1))

    # Fallback: check max page in rough/ or prose.md
    if total_pages == 0:
        rough_dir = os.path.join(project_dir, "rough")
        if os.path.exists(rough_dir):
            p_files = [f for f in os.listdir(rough_dir) if re.match(r"^p\d+\.png$", f)]
            if p_files:
                nums = [int(re.search(r"\d+", f).group(0)) for f in p_files]
                total_pages = max(nums)
    if total_pages == 0:
        total_pages = 14

    return title, author, total_pages

def render_pages_to_dir(project_dir, rendered_dir, title, author, total_pages):
    os.makedirs(rendered_dir, exist_ok=True)
    font_reg_path, font_bold_path = find_font()
    font_text = ImageFont.truetype(font_reg_path, 54)
    font_num = ImageFont.truetype(font_reg_path, 32)
    font_cov_title = ImageFont.truetype(font_bold_path, 88)
    font_cov_author = ImageFont.truetype(font_reg_path, 42)

    prose_path = os.path.join(project_dir, "prose.md")
    pages_text = parse_prose(prose_path)

    rough_dir = os.path.join(project_dir, "rough")

    # 1. Cover
    # Prefer cover.png, or fallback to p11.png / p14.png / p01.png
    cov_img_name = None
    for cand in ["cover.png", "p11.png", "p14.png", "p01.png"]:
        if os.path.exists(os.path.join(rough_dir, cand)):
            cov_img_name = cand
            break

    cov_canvas = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
    draw_cov = ImageDraw.Draw(cov_canvas)

    # Title text
    c_chars = list(title)
    c_spacing = int(88 * 0.25)
    total_tw = sum((font_cov_title.getbbox(ch)[2] - font_cov_title.getbbox(ch)[0]) for ch in c_chars) + c_spacing * (len(c_chars) - 1)
    start_tx = (PAGE_W - total_tw) // 2
    title_y = 160
    curr_tx = start_tx
    for ch in c_chars:
        draw_cov.text((curr_tx, title_y), ch, font=font_cov_title, fill=(24, 24, 24))
        w = font_cov_title.getbbox(ch)[2] - font_cov_title.getbbox(ch)[0]
        curr_tx += w + c_spacing

    author_str = f"作・構成　{author}"
    a_bbox = font_cov_author.getbbox(author_str)
    a_w = a_bbox[2] - a_bbox[0]
    draw_cov.text(((PAGE_W - a_w) // 2, title_y + 130), author_str, font=font_cov_author, fill=(70, 70, 70))

    if cov_img_name:
        c_raw = Image.open(os.path.join(rough_dir, cov_img_name)).convert("RGB")
        max_box_w, max_box_h = 1360, 1150
        scale = min(max_box_w / c_raw.width, max_box_h / c_raw.height)
        fit_w = int(c_raw.width * scale)
        fit_h = int(c_raw.height * scale)
        c_resized = c_raw.resize((fit_w, fit_h), Image.Resampling.LANCZOS)
        cov_canvas.paste(c_resized, ((PAGE_W - fit_w) // 2, 560 + (max_box_h - fit_h) // 2))

    cov_canvas.save(os.path.join(rendered_dir, "page_cover.png"), quality=95)

    # 2. Body Pages
    for p in range(1, total_pages + 1):
        canvas = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
        draw = ImageDraw.Draw(canvas)
        text_lines = pages_text.get(p, [])

        if text_lines:
            line_height = 96
            total_th = len(text_lines) * line_height
            start_y = 80 + (440 - total_th) // 2
            for i, line in enumerate(text_lines):
                bbox = font_text.getbbox(line)
                tw = bbox[2] - bbox[0]
                draw.text(((PAGE_W - tw) // 2, start_y + i * line_height), line, font=font_text, fill=(28, 28, 28))

        # Image
        p_img_path = os.path.join(rough_dir, f"p{p:02d}.png")
        if os.path.exists(p_img_path):
            p_raw = Image.open(p_img_path).convert("RGB")
            max_box_w, max_box_h = 1360, 1150
            scale = min(max_box_w / p_raw.width, max_box_h / p_raw.height)
            fit_w = int(p_raw.width * scale)
            fit_h = int(p_raw.height * scale)
            p_resized = p_raw.resize((fit_w, fit_h), Image.Resampling.LANCZOS)
            canvas.paste(p_resized, ((PAGE_W - fit_w) // 2, 560 + (max_box_h - fit_h) // 2))

        # Page number
        is_left = (p % 2 == 0)
        p_str = str(p)
        if is_left:
            num_x = 100
        else:
            num_w = font_num.getbbox(p_str)[2] - font_num.getbbox(p_str)[0]
            num_x = PAGE_W - 100 - num_w
        draw.text((num_x, 1820), p_str, font=font_num, fill=(140, 140, 140))

        canvas.save(os.path.join(rendered_dir, f"page_{p:02d}.png"), quality=95)

    # 3. Colophon Page
    col_canvas = Image.new("RGB", (PAGE_W, PAGE_H), (250, 247, 242))
    draw_c = ImageDraw.Draw(col_canvas)
    draw_c.text((200, 600), title, font=ImageFont.truetype(font_bold_path, 52), fill=(30, 30, 30))
    draw_c.line((200, 680, 1240, 680), fill=(200, 200, 200), width=2)
    draw_c.text((200, 740), f"作・構成: {author}", font=ImageFont.truetype(font_reg_path, 32), fill=(50, 50, 50))
    draw_c.text((200, 810), f"企画・制作: {author}", font=ImageFont.truetype(font_reg_path, 32), fill=(50, 50, 50))
    draw_c.text((200, 880), "発行: 初版発行", font=ImageFont.truetype(font_reg_path, 32), fill=(50, 50, 50))
    draw_c.text((200, 1050), "※ 本作の画像ラフ構想および文の構成には、AIアシスト（Gemini）を活用しています。", font=ImageFont.truetype(font_reg_path, 24), fill=(120, 120, 120))
    draw_c.text((200, 1095), "※ 最終的な演出、文言、画面構成の採否および監修責任は作者に帰属します。", font=ImageFont.truetype(font_reg_path, 24), fill=(120, 120, 120))
    col_canvas.save(os.path.join(rendered_dir, "page_colophon.png"), quality=95)

def build_epub_package(rendered_dir, output_epub, title, author, total_pages=14):
    temp_dir = "/tmp/epub_build_pkg"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(f"{temp_dir}/META-INF")
    os.makedirs(f"{temp_dir}/OEBPS/images")
    os.makedirs(f"{temp_dir}/OEBPS/css")

    with open(f"{temp_dir}/mimetype", "w", encoding="ascii") as f:
        f.write("application/epub+zip")

    with open(f"{temp_dir}/META-INF/container.xml", "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")

    with open(f"{temp_dir}/OEBPS/css/style.css", "w", encoding="utf-8") as f:
        f.write(f"""@charset "utf-8";
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {PAGE_W}px; height: {PAGE_H}px; background-color: #faf8f5; overflow: hidden; }}
.page-full {{ width: {PAGE_W}px; height: {PAGE_H}px; display: block; }}
.page-full img {{ width: 100%; height: 100%; display: block; }}
""")

    page_files = [("cover", "page_cover.png", "page-spread-left", "表紙")]
    for p in range(1, total_pages + 1):
        spread = "page-spread-left" if (p % 2 == 0) else "page-spread-right"
        page_files.append((f"p_{p:02d}", f"page_{p:02d}.png", spread, f"{p}ページ"))
    page_files.append(("colophon", "page_colophon.png", "page-spread-right", "奥付"))

    for p_id, p_img, _, _ in page_files:
        shutil.copyfile(os.path.join(rendered_dir, p_img), f"{temp_dir}/OEBPS/images/{p_img}")

    for p_id, p_img, _, title_desc in page_files:
        is_cover = (p_id == "cover")
        epub_type = ' epub:type="cover"' if is_cover else ''
        xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ja" lang="ja">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width={PAGE_W}, height={PAGE_H}"/>
  <title>{title} - {title_desc}</title>
  <link rel="stylesheet" type="text/css" href="css/style.css"/>
</head>
<body{epub_type}>
  <div class="page-full"{epub_type}>
    <img src="images/{p_img}" alt="{title_desc}"/>
  </div>
</body>
</html>"""
        with open(f"{temp_dir}/OEBPS/{p_id}.xhtml", "w", encoding="utf-8") as f:
            f.write(xhtml)

    with open(f"{temp_dir}/OEBPS/nav.xhtml", "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ja" lang="ja">
<head><meta charset="utf-8"/><title>目次</title><link rel="stylesheet" type="text/css" href="css/style.css"/></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>目次</h1>
    <ol>
      <li><a href="cover.xhtml">表紙</a></li>
      <li><a href="p_01.xhtml">本編（1〜{total_pages}ページ）</a></li>
      <li><a href="colophon.xhtml">奥付</a></li>
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="">
    <h2>ランドマーク</h2>
    <ol>
      <li><a epub:type="cover" href="cover.xhtml">表紙</a></li>
      <li><a epub:type="bodymatter" href="cover.xhtml">本編開始</a></li>
    </ol>
  </nav>
</body>
</html>""")

    book_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{title}.picture-book.local"))
    manifest_items = [
        '<item id="style" href="css/style.css" media-type="text/css"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="cover-img" href="images/page_cover.png" media-type="image/png" properties="cover-image"/>',
    ]
    for p_id, p_img, _, _ in page_files:
        manifest_items.append(f'<item id="{p_id}" href="{p_id}.xhtml" media-type="application/xhtml+xml"/>')
        if p_img != "page_cover.png":
            manifest_items.append(f'<item id="img_{p_id}" href="images/{p_img}" media-type="image/png"/>')

    spine_items = [f'<itemref idref="{p_id}" properties="{spread}"/>' for p_id, _, spread, _ in page_files]

    manifest_xml = "\n    ".join(manifest_items)
    spine_xml = "\n    ".join(spine_items)

    package_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:uuid:{book_uuid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">2026-09-16T14:30:00Z</meta>
    <meta name="cover" content="cover-img"/>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">auto</meta>
    <meta name="fixed-layout" content="true"/>
    <meta name="original-resolution" content="{PAGE_W}x{PAGE_H}"/>
    <meta name="book-type" content="children"/>
    <meta name="orientation-lock" content="none"/>
  </metadata>
  <manifest>
    {manifest_xml}
  </manifest>
  <spine page-progression-direction="ltr">
    {spine_xml}
  </spine>
  <guide>
    <reference type="cover" title="表紙" href="cover.xhtml"/>
    <reference type="text" title="本編" href="cover.xhtml"/>
  </guide>
</package>"""

    with open(f"{temp_dir}/OEBPS/package.opf", "w", encoding="utf-8") as f:
        f.write(package_opf)

    os.makedirs(os.path.dirname(os.path.abspath(output_epub)), exist_ok=True)
    if os.path.exists(output_epub):
        os.remove(output_epub)

    with zipfile.ZipFile(output_epub, "w") as zf:
        zf.write(f"{temp_dir}/mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(f"{temp_dir}/META-INF"):
            for file in files:
                p = os.path.join(root, file)
                zf.write(p, os.path.relpath(p, temp_dir), compress_type=zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(f"{temp_dir}/OEBPS"):
            for file in files:
                p = os.path.join(root, file)
                zf.write(p, os.path.relpath(p, temp_dir), compress_type=zipfile.ZIP_DEFLATED)

    print(f"EPUB created successfully: {output_epub}")

def main():
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    project_dir = os.path.abspath(project_dir)

    brief_path = os.path.join(project_dir, "brief.md")
    title, author, total_pages = parse_brief_meta(brief_path, project_dir)

    rendered_dir = os.path.join(project_dir, "rendered_pages")
    dist_dir = os.path.join(project_dir, "dist")
    out_epub = os.path.join(dist_dir, f"{title}_固定レイアウト版.epub")

    print(f"=== Rendering Fixed-Layout Pages for '{title}' (by {author}, {total_pages} pages) ===")
    render_pages_to_dir(project_dir, rendered_dir, title, author, total_pages)

    print(f"=== Packing EPUB3 ===")
    build_epub_package(rendered_dir, out_epub, title, author, total_pages)

if __name__ == "__main__":
    main()
