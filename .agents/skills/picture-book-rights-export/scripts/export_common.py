#!/usr/bin/env python3
"""Shared project loading and HTML helpers for picture-book exports."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import html
import importlib.util
import mimetypes
import os
from pathlib import Path
from types import ModuleType


@dataclass(frozen=True)
class Project:
    root: Path
    title: str
    author: str
    page_count: int
    prose: dict[int, list[str]]
    art_dir: Path
    cover: Path
    pages: dict[int, Path]


def load_epub_builder() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[2]
        / "picture-book-epub"
        / "scripts"
        / "build_fixed_layout.py"
    )
    spec = importlib.util.spec_from_file_location("picture_book_epub_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load shared EPUB builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project(
    project_dir: str,
    *,
    art_dir: str | None = None,
    cover: str | None = None,
    title: str | None = None,
    author: str | None = None,
    pages: int | None = None,
) -> Project:
    root = Path(project_dir).resolve()
    builder = load_epub_builder()
    brief_title, brief_author, brief_pages = builder.parse_brief(root / "brief.md")
    selected_title = title or brief_title
    selected_author = author or brief_author
    if not selected_title or not selected_author:
        raise ValueError("Title and author are required in brief.md or command options")
    prose = builder.parse_prose(root / "prose.md")
    selected_art = builder.select_art_dir(root, art_dir)
    selected_cover = builder.locate_cover(root, selected_art, cover)
    page_count = builder.infer_page_count(pages, brief_pages, prose, selected_art)
    page_art = {
        number: builder.locate_page_art(selected_art, number)
        for number in range(1, page_count + 1)
    }
    return Project(
        root=root,
        title=selected_title,
        author=selected_author,
        page_count=page_count,
        prose=prose,
        art_dir=selected_art,
        cover=selected_cover,
        pages=page_art,
    )


def safe_filename(value: str) -> str:
    return load_epub_builder().safe_filename(value)


def image_uri(path: Path, *, embed: bool, relative_to: Path | None = None) -> str:
    if not embed:
        if relative_to:
            return os.path.relpath(path.resolve(), relative_to.resolve()).replace(os.sep, "/")
        return path.resolve().as_uri()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def page_text(project: Project, number: int) -> str:
    lines = project.prose.get(number, [])
    if not lines:
        return '<span class="no-text">（文なし）</span>'
    return "<br/>".join(html.escape(line) for line in lines)


def body_groups(page_count: int) -> list[tuple[int | None, int | None]]:
    groups: list[tuple[int | None, int | None]] = [(None, 1)]
    number = 2
    while number <= page_count:
        groups.append((number, number + 1 if number + 1 <= page_count else None))
        number += 2
    return groups


def page_panel(
    project: Project,
    number: int | None,
    *,
    embed: bool,
    side: str,
    relative_to: Path | None = None,
) -> str:
    if number is None:
        return f'<section class="page blank {side}" aria-label="空白ページ"></section>'
    source = image_uri(project.pages[number], embed=embed, relative_to=relative_to)
    return f"""<section class="page {side}" aria-label="{number}ページ">
  <div class="art"><img src="{source}" alt="{number}ページの挿絵"/></div>
  <div class="prose">{page_text(project, number)}</div>
  <div class="page-number">{number}</div>
</section>"""
