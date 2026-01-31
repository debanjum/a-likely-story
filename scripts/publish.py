#!/usr/bin/env python3
"""A Likely Story - Publish Pipeline

This script turns a daily markdown chapter into a published HTML chapter and
updates site artifacts (chapters.json, chapters.html, rss.xml).

Design goals
- No heavy static site generator: plain HTML + CSS.
- GitHub Pages friendly: generated files committed to repo.
- Deterministic builds: markdown source is the canonical chapter content.

Usage
  uv run python scripts/publish.py today
  uv run python scripts/publish.py 1
  uv run python scripts/publish.py 42 --dry-run

Inputs
  manuscript/YYYY-MM-DD.md  (recommended)
  manuscript/NNN.md         (also supported)

Frontmatter (YAML) in markdown is optional but recommended:
---
title: "..."
excerpt: "..."   # optional, used for RSS
---

If title is missing, the script will derive a title from first heading.

"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import markdown as md
import yaml

PROJECT_DIR = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = PROJECT_DIR / "manuscript"
CHAPTERS_DIR = PROJECT_DIR / "chapters"
TEMPLATES_DIR = PROJECT_DIR / "templates"

CHAPTERS_JSON = PROJECT_DIR / "chapters.json"
CHAPTERS_HTML = PROJECT_DIR / "chapters.html"
INDEX_HTML = PROJECT_DIR / "index.html"
RSS_XML = PROJECT_DIR / "rss.xml"

START_DATE = date(2026, 1, 1)
SITE_TITLE = "A Likely Story"
SITE_DESCRIPTION = "A 365-chapter story, one for each day of 2026. Written and published by Pipali."
# On GitHub Pages you will set CNAME to your custom domain.
# Keep SITE_URL updated once domain is finalized.
SITE_URL = "https://alikelystory.org"  # must match CNAME


@dataclass
class Chapter:
    day_num: int
    chapter_date: date
    title: str
    excerpt: str
    markdown_source: str
    html_body: str


def day_number_for_date(d: date) -> Optional[int]:
    if d.year != 2026:
        return None
    delta = d - START_DATE
    n = delta.days + 1
    return n if 1 <= n <= 365 else None


def date_for_day_number(n: int) -> date:
    return START_DATE + timedelta(days=n - 1)


def load_template(name: str) -> str:
    p = TEMPLATES_DIR / name
    return p.read_text(encoding="utf-8")


def load_index() -> Dict[str, Any]:
    if CHAPTERS_JSON.exists():
        return json.loads(CHAPTERS_JSON.read_text(encoding="utf-8"))
    return {"chapters": {}}


def save_index(index: Dict[str, Any]) -> None:
    CHAPTERS_JSON.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)


def parse_frontmatter(markdown_text: str) -> Tuple[Dict[str, Any], str]:
    m = FM_RE.match(markdown_text.strip())
    if not m:
        return {}, markdown_text
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    return fm, body


def derive_title(fm: Dict[str, Any], body_md: str, day_num: int) -> str:
    if isinstance(fm.get("title"), str) and fm["title"].strip():
        return fm["title"].strip()
    # first markdown heading
    for line in body_md.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return f"Chapter {day_num}"


def derive_excerpt(fm: Dict[str, Any], body_md: str) -> str:
    if isinstance(fm.get("excerpt"), str) and fm["excerpt"].strip():
        return fm["excerpt"].strip()
    # Take first non-empty paragraph-ish line
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", body_md)  # strip links
    text = re.sub(r"[#*_>`]", "", text)
    for para in re.split(r"\n\s*\n", text):
        s = " ".join(para.strip().split())
        if len(s) >= 40:
            return s[:200] + ("…" if len(s) > 200 else "")
    return ""


def markdown_to_html(body_md: str) -> str:
    # Keep it simple but pleasant
    return md.markdown(
        body_md,
        extensions=[
            "extra",
            "sane_lists",
            "smarty",
        ],
        output_format="html5",
    )


def chapter_paths(day_num: int) -> Tuple[Path, str]:
    filename = f"{day_num:03d}.html"
    return CHAPTERS_DIR / filename, filename


def find_manuscript_for_day(day_num: int) -> Path:
    d = date_for_day_number(day_num)
    candidates = [
        MANUSCRIPT_DIR / f"{d.isoformat()}.md",
        MANUSCRIPT_DIR / f"{day_num:03d}.md",
        MANUSCRIPT_DIR / f"{day_num}.md",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"No manuscript found for day {day_num}. Expected one of: "
        + ", ".join(str(p.relative_to(PROJECT_DIR)) for p in candidates)
    )


def render_chapter_html(ch: Chapter) -> str:
    template = load_template("chapter_template.html")

    prev_num = ch.day_num - 1
    next_num = ch.day_num + 1
    prev_link = f"{prev_num:03d}.html" if ch.day_num > 1 else "#"
    next_link = f"{next_num:03d}.html" if ch.day_num < 365 else "#"
    prev_class = "" if ch.day_num > 1 else "disabled"
    next_class = "" if ch.day_num < 365 else "disabled"

    date_formatted = ch.chapter_date.strftime("%B %d, %Y")

    # Indent body for nice source output
    body_lines = ch.html_body.strip().splitlines()
    indented = "\n".join("\t\t\t" + ln for ln in body_lines)

    return template.format(
        num=ch.day_num,
        title=ch.title,
        date_formatted=date_formatted,
        content_html=indented,
        prev_link=prev_link,
        next_link=next_link,
        prev_class=prev_class,
        next_class=next_class,
    )


def rebuild_chapters_page(index: Dict[str, Any]) -> None:
    # Reuse the existing generator's HTML structure by importing it? Keep local/simple here.
    chapters = index.get("chapters", {})

    # Group by month
    months: Dict[str, list] = {}
    for day_str, info in sorted(chapters.items(), key=lambda x: int(x[0])):
        day_num = int(day_str)
        d = date_for_day_number(day_num)
        month_key = d.strftime("%B %Y")
        months.setdefault(month_key, []).append((day_num, info))

    sections = []
    for month, items in months.items():
        lis = []
        for day_num, info in items:
            lis.append(
                f'\t\t\t\t<li><a href="chapters/{info["file"]}"><span class="chapter-title">Chapter {day_num}: {info["title"]}</span><span class="chapter-meta">{info["date"]}</span></a></li>'
            )
        sections.append(
            "\n".join(
                [
                    "\t\t<section class=\"archive-section\">",
                    f"\t\t\t<h2>{month}</h2>",
                    "\t\t\t<ul class=\"chapter-list\">",
                    "\n".join(lis),
                    "\t\t\t</ul>",
                    "\t\t</section>",
                ]
            )
        )

    total = len(chapters)

    chapters_list = (
        "\n".join(sections)
        if sections
        else '\n\t\t<section class="archive-section">\n\t\t\t<p style="text-align: center; color: var(--color-text-muted);">No chapters published yet. The story begins January 1, 2026.</p>\n\t\t</section>\n'
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>All Chapters - A Likely Story</title>
	<meta name="description" content="Browse all {total} published chapters of A Likely Story.">

	<!-- Fonts -->
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap" rel="stylesheet">

	<!-- Styles -->
	<link rel="stylesheet" href="css/design-tokens.css">
	<link rel="stylesheet" href="css/style.css">
	<link rel="alternate" type="application/rss+xml" title="A Likely Story RSS" href="rss.xml" />
</head>
<body>
	<nav>
		<div class="nav-inner">
			<a href="index.html" class="site-title">A Likely Story</a>
			<div class="nav-links">
				<a href="chapters.html">Chapters</a>
				<a href="about.html">About</a>
				<a href="rss.xml">RSS</a>
				<button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
					<span class="theme-icon">&#9790;</span>
				</button>
			</div>
		</div>
	</nav>

	<header class="container" style="padding-top: calc(var(--space-16) + 60px);">
		<h1 style="font-size: var(--text-3xl); text-transform: none; letter-spacing: var(--tracking-tight);">All Chapters</h1>
		<p class="subtitle">{total} of 365 chapters published</p>
	</header>

	<main class="container">
{chapters_list}
	</main>

	<footer>
		<p>Written by <a href="https://pipali.ai">Pipali</a> &middot; A Likely Story &middot; 2026</p>
		<p><a href="rss.xml">RSS</a></p>
	</footer>

	<script>
		const themeToggle = document.getElementById('themeToggle');
		const themeIcon = themeToggle.querySelector('.theme-icon');

		function setTheme(theme) {{
			document.documentElement.className = theme;
			localStorage.setItem('theme', theme);
			themeIcon.textContent = theme === 'dark' ? '\\u2600' : '\\u263E';
		}}

		const savedTheme = localStorage.getItem('theme');
		if (savedTheme) {{
			setTheme(savedTheme);
		}} else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {{
			themeIcon.textContent = '\\u2600';
		}}

		themeToggle.addEventListener('click', () => {{
			const currentTheme = document.documentElement.className;
			setTheme(currentTheme === 'dark' ? 'light' : 'dark');
		}});
	</script>
</body>
</html>'''

    CHAPTERS_HTML.write_text(html + "\n", encoding="utf-8")


def rebuild_rss(index: Dict[str, Any]) -> None:
    # Minimal RSS 2.0 feed
    chapters = index.get("chapters", {})
    items = []

    # latest first
    for day_str, info in sorted(chapters.items(), key=lambda x: int(x[0]), reverse=True)[:30]:
        day_num = int(day_str)
        link = f"{SITE_URL}/chapters/{info['file']}"
        guid = link
        pub_date = info.get("rfc2822") or ""
        excerpt = info.get("excerpt", "")
        title = info.get("title", f"Chapter {day_num}")

        # RSS requires escaping
        def esc(s: str) -> str:
            return (
                s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        items.append(
            "\n".join(
                [
                    "  <item>",
                    f"    <title>Chapter {day_num}: {esc(title)}</title>",
                    f"    <link>{esc(link)}</link>",
                    f"    <guid isPermaLink=\"true\">{esc(guid)}</guid>",
                    (f"    <pubDate>{esc(pub_date)}</pubDate>" if pub_date else ""),
                    (f"    <description>{esc(excerpt)}</description>" if excerpt else ""),
                    "  </item>",
                ]
            )
        )

    rss = "\n".join(
        [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<rss version=\"2.0\">",
            "<channel>",
            f"  <title>{SITE_TITLE}</title>",
            f"  <link>{SITE_URL}</link>",
            f"  <description>{SITE_DESCRIPTION}</description>",
            f"  <language>en</language>",
            "\n".join(items),
            "</channel>",
            "</rss>",
            "",
        ]
    )

    RSS_XML.write_text(rss, encoding="utf-8")


def publish(day_num: int, dry_run: bool = False) -> Chapter:
    manuscript_path = find_manuscript_for_day(day_num)
    raw = manuscript_path.read_text(encoding="utf-8")

    fm, body_md = parse_frontmatter(raw)
    title = derive_title(fm, body_md, day_num)
    excerpt = derive_excerpt(fm, body_md)

    body_html = markdown_to_html(body_md)

    ch_date = date_for_day_number(day_num)
    date_formatted = ch_date.strftime("%B %d, %Y")

    chapter = Chapter(
        day_num=day_num,
        chapter_date=ch_date,
        title=title,
        excerpt=excerpt,
        markdown_source=raw,
        html_body=body_html,
    )

    out_path, filename = chapter_paths(day_num)
    html = render_chapter_html(chapter)

    if not dry_run:
        CHAPTERS_DIR.mkdir(exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

        # update chapters.json
        index = load_index()
        index.setdefault("chapters", {})
        index["chapters"][str(day_num)] = {
            "title": title,
            "date": date_formatted,
            "file": filename,
            "excerpt": excerpt,
            # RFC 2822 pubDate; use noon IST to avoid DST weirdness.
            "rfc2822": ch_date.strftime("%a, %d %b %Y 06:30:00 GMT"),
        }
        save_index(index)

        rebuild_chapters_page(index)
        rebuild_rss(index)

    return chapter


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("day", help="1-365 or 'today'")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.day.lower() == "today":
        dn = day_number_for_date(date.today())
        if dn is None:
            raise SystemExit(f"Today ({date.today().isoformat()}) is not in 2026. Use an explicit day number.")
    else:
        dn = int(args.day)
        if not (1 <= dn <= 365):
            raise SystemExit("day must be 1-365 or 'today'")

    ch = publish(dn, dry_run=args.dry_run)
    print(f"Prepared Chapter {ch.day_num:03d}: {ch.title}")


if __name__ == "__main__":
    main()
