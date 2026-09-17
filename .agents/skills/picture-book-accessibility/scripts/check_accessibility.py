#!/usr/bin/env python3
"""Mechanical lint tool for picture-book accessibility ledger (accessibility.md) and EPUB files."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


def parse_accessibility_ledger(path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing accessibility ledger: {path}")
    content = path.read_text(encoding="utf-8")
    issues: list[str] = []

    # Check for process-state header
    if not re.search(r"<!--\s*process-state", content):
        issues.append("WARNING: accessibility.md lacks standard process-state metadata header")

    entries: dict[str, dict[str, str]] = {}
    # Look for table specifically in the page descriptions section
    section2_match = re.search(r"##\s*2[^\n]*\n([\s\S]*?)(?:\n##|\Z)", content)
    table_src = section2_match.group(1) if section2_match else content

    table_lines = [line.strip() for line in table_src.splitlines() if line.strip().startswith("|")]
    if len(table_lines) >= 3:
        raw_headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
        headers = [h.lower() for h in raw_headers]
        
        def find_col(keys: tuple[str, ...]) -> int:
            for idx, h in enumerate(headers):
                if any(k in h for k in keys):
                    return idx
            return -1

        id_col = find_col(("頁", "ページ", "page", "id"))
        alt_col = find_col(("代替テキスト", "img_alt", "alt"))
        body_col = find_col(("本文", "body_text"))
        vis_col = find_col(("情景", "描写", "visual_description"))
        dec_col = find_col(("装飾", "decorative"))

        if id_col != -1 and alt_col != -1:
            for row in table_lines[2:]:
                cells = [c.strip() for c in row.split("|")[1:-1]]
                if len(cells) > max(id_col, alt_col):
                    page_id = cells[id_col]
                    if not page_id or page_id.startswith("---") or page_id.startswith(":-"):
                        continue
                    entry = {
                        "img_alt": cells[alt_col],
                        "body_text": cells[body_col] if body_col != -1 and len(cells) > body_col else "",
                        "visual_description": cells[vis_col] if vis_col != -1 and len(cells) > vis_col else "",
                        "decorative": cells[dec_col].lower() if dec_col != -1 and len(cells) > dec_col else "no",
                    }
                    entries[page_id] = entry

    if not entries:
        issues.append("ERROR: No structured page rows found in accessibility.md table")

    return entries, issues


def check_ledger(entries: dict[str, dict[str, str]], expected_pages: int | None) -> list[str]:
    issues: list[str] = []
    if not entries:
        issues.append("ERROR: No page accessibility entries found in accessibility.md")
        return issues

    for page_id, data in entries.items():
        alt = data.get("img_alt", "")
        dec = data.get("decorative", "no")
        is_decorative = dec in {"yes", "true", "y"}

        if is_decorative:
            if alt and alt != '""':
                issues.append(f"WARNING: Decorative image for '{page_id}' has non-empty alt text '{alt}' (should be empty)")
            continue

        if not alt:
            issues.append(f"ERROR: Page '{page_id}' has empty img_alt")
            continue

        if len(alt) < 10:
            issues.append(f"WARNING: Page '{page_id}' alt text is very short ({len(alt)} chars): '{alt}'")
        elif len(alt) > 300:
            issues.append(f"NOTE: Page '{page_id}' alt text is detailed ({len(alt)} chars); ensure read-aloud rhythm remains comfortable")

        if alt in {"1ページ", "挿絵", "表紙", "イラスト", "画像"}:
            issues.append(f"ERROR: Page '{page_id}' has non-descriptive generic alt text: '{alt}'")

    if expected_pages:
        missing = []
        for i in range(1, expected_pages + 1):
            candidates = [f"{i}", f"p{i:02d}", f"p_{i:02d}", f"{i}ページ", f"Page {i}"]
            if not any(c in entries for c in candidates):
                missing.append(f"p{i:02d}")
        if missing:
            issues.append(f"ERROR: Missing accessibility descriptions for pages: {', '.join(missing)}")

    return issues


def check_epub(epub_path: Path) -> list[str]:
    issues: list[str] = []
    if not epub_path.exists():
        issues.append(f"ERROR: EPUB file does not exist: {epub_path}")
        return issues

    try:
        archive = zipfile.ZipFile(epub_path)
    except Exception as e:
        issues.append(f"ERROR: Failed to open EPUB archive: {e}")
        return issues

    with archive:
        # Resolve OPF from container.xml
        if "META-INF/container.xml" not in archive.namelist():
            issues.append("ERROR: Missing META-INF/container.xml in EPUB")
            return issues

        try:
            container_xml = archive.read("META-INF/container.xml")
            container_tree = ET.fromstring(container_xml)
            rootfile = container_tree.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
            if rootfile is None or not rootfile.attrib.get("full-path"):
                issues.append("ERROR: Could not locate OPF path in container.xml")
                return issues
            opf_path = rootfile.attrib["full-path"]
        except Exception as e:
            issues.append(f"ERROR: Failed to parse container.xml: {e}")
            return issues

        if opf_path not in archive.namelist():
            issues.append(f"ERROR: OPF file specified in container.xml not found in archive: {opf_path}")
            return issues

        opf_content = archive.read(opf_path).decode("utf-8")

        # Check W3C EPUB Accessibility 1.1 MUST metadata properties
        for meta in ("schema:accessMode", "schema:accessibilityFeature", "schema:accessibilityHazard"):
            if meta not in opf_content:
                issues.append(f"ERROR: EPUB package metadata lacks W3C MUST property '{meta}'")

        # Check SHOULD metadata properties
        for meta in ("schema:accessibilitySummary", "schema:accessModeSufficient"):
            if meta not in opf_content:
                issues.append(f"WARNING: EPUB package metadata lacks W3C SHOULD property '{meta}'")

        # Check all XHTML content documents
        content_files = [n for n in archive.namelist() if n.endswith((".xhtml", ".html")) and not n.endswith("nav.xhtml")]
        if not content_files:
            issues.append("WARNING: No XHTML content documents found in EPUB")

        for file_name in content_files:
            try:
                xml_data = archive.read(file_name)
                tree = ET.fromstring(xml_data)
                # Find all img tags in any namespace
                for elem in tree.iter():
                    if elem.tag.split("}")[-1] == "img":
                        alt = elem.attrib.get("alt")
                        if alt is None:
                            issues.append(f"ERROR: <img> in '{file_name}' has no alt attribute")
                        elif not alt.strip() and elem.attrib.get("role") != "presentation":
                            # Empty alt is valid if role="presentation" or decorative
                            pass
                        elif len(alt.strip()) < 5:
                            issues.append(f"WARNING: <img> in '{file_name}' has very short alt text: '{alt}'")
            except Exception as e:
                issues.append(f"ERROR: XML parsing failed for '{file_name}': {e}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Project directory, accessibility.md, or .epub file")
    parser.add_argument("--pages", type=int, help="Expected page count")
    parser.add_argument("--strict", action="store_true", help="Fail with exit code 1 on warnings as well as errors")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    all_issues: list[str] = []

    if target_path.suffix.lower() == ".epub":
        print(f"Linting EPUB accessibility: {target_path}")
        all_issues.extend(check_epub(target_path))
    elif target_path.is_file() and target_path.name == "accessibility.md":
        print(f"Linting accessibility ledger: {target_path}")
        entries, parse_issues = parse_accessibility_ledger(target_path)
        all_issues.extend(parse_issues)
        print(f"Found {len(entries)} structured page descriptions.")
        all_issues.extend(check_ledger(entries, args.pages))
    elif target_path.is_dir():
        ledger = target_path / "accessibility.md"
        if ledger.exists():
            print(f"Linting accessibility ledger: {ledger}")
            entries, parse_issues = parse_accessibility_ledger(ledger)
            all_issues.extend(parse_issues)
            print(f"Found {len(entries)} structured page descriptions.")
            all_issues.extend(check_ledger(entries, args.pages))
        else:
            all_issues.append(f"WARNING: No accessibility.md found in project directory {target_path}")

        dist_epubs = list((target_path / "dist").glob("*.epub")) if (target_path / "dist").exists() else []
        for epub in dist_epubs:
            print(f"Linting output EPUB: {epub}")
            all_issues.extend(check_epub(epub))
    else:
        print(f"Target not found: {target_path}", file=sys.stderr)
        return 1

    if not all_issues:
        print("✓ All accessibility lint checks passed! No issues found.")
        return 0

    print(f"\nAccessibility lint findings ({len(all_issues)} items):")
    has_error = False
    has_warning = False
    for issue in all_issues:
        print(f" - {issue}")
        if issue.startswith("ERROR"):
            has_error = True
        elif issue.startswith("WARNING"):
            has_warning = True

    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
