#!/usr/bin/env python3
"""
Chapter Generator for A Likely Story

Usage:
    python generate_chapter.py <day_number> "<title>" "<content>"
    python generate_chapter.py today "<title>" "<content>"
    python generate_chapter.py --rebuild-index

Examples:
    python generate_chapter.py 1 "The Beginning" "<p>It all started on a cold January morning...</p>"
    python generate_chapter.py today "A New Dawn" "<p>The sun rose slowly...</p>"
    python generate_chapter.py --rebuild-index
"""

import os
import sys
import json
from datetime import date, timedelta
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).parent
CHAPTERS_DIR = PROJECT_DIR / "chapters"
CHAPTERS_JSON = PROJECT_DIR / "chapters.json"

# Story start date
START_DATE = date(2026, 1, 1)

CHAPTER_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>{title} - A Likely Story</title>
	<meta name="description" content="Chapter {num}: {title}. {date_formatted}.">

	<!-- Fonts -->
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap" rel="stylesheet">

	<!-- Styles -->
	<link rel="stylesheet" href="../css/design-tokens.css">
	<link rel="stylesheet" href="../css/style.css">
</head>
<body>
	<nav>
		<div class="nav-inner">
			<a href="../index.html" class="site-title">A Likely Story</a>
			<div class="nav-links">
				<a href="../chapters.html">Chapters</a>
				<a href="../about.html">About</a>
				<button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
					<span class="theme-icon">&#9790;</span>
				</button>
			</div>
		</div>
	</nav>

	<div class="reading-progress">
		<div class="progress-bar" id="progressBar"></div>
	</div>

	<article class="container">
		<header class="chapter-header">
			<p class="chapter-number">Chapter {num} of 365</p>
			<h1>{title}</h1>
			<p class="chapter-date">{date_formatted}</p>
		</header>

		<div class="chapter-content">
{content}
		</div>

		<nav class="chapter-nav">
			<a href="{prev_link}" class="{prev_class}">&larr; Previous</a>
			<a href="../chapters.html">All Chapters</a>
			<a href="{next_link}" class="{next_class}">Next &rarr;</a>
		</nav>
	</article>

	<footer>
		<p>Written by AI &middot; A Likely Story &middot; 2026</p>
	</footer>

	<script>
		// Theme toggle
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

		// Reading progress
		const progressBar = document.getElementById('progressBar');
		window.addEventListener('scroll', () => {{
			const scrollTop = window.scrollY;
			const docHeight = document.documentElement.scrollHeight - window.innerHeight;
			const progress = (scrollTop / docHeight) * 100;
			progressBar.style.width = progress + '%';
		}});
	</script>
</body>
</html>'''


def get_day_number_for_date(target_date):
    """Calculate day number (1-365) for a given date in 2026."""
    if target_date.year != 2026:
        return None
    delta = target_date - START_DATE
    day_num = delta.days + 1
    if 1 <= day_num <= 365:
        return day_num
    return None


def get_date_for_day(day_num):
    """Get the date for a given day number."""
    return START_DATE + timedelta(days=day_num - 1)


def load_chapters_index():
    """Load the chapters index from JSON."""
    if CHAPTERS_JSON.exists():
        with open(CHAPTERS_JSON, 'r') as f:
            return json.load(f)
    return {"chapters": {}}


def save_chapters_index(index):
    """Save the chapters index to JSON."""
    with open(CHAPTERS_JSON, 'w') as f:
        json.dump(index, f, indent=2)


def generate_chapter(day_num, title, content):
    """Generate a chapter HTML file."""
    CHAPTERS_DIR.mkdir(exist_ok=True)

    current_date = get_date_for_day(day_num)
    date_formatted = current_date.strftime("%B %d, %Y")

    # Navigation
    prev_num = f"{day_num - 1:03d}"
    next_num = f"{day_num + 1:03d}"
    prev_link = f"{prev_num}.html" if day_num > 1 else "#"
    next_link = f"{next_num}.html" if day_num < 365 else "#"
    prev_class = "" if day_num > 1 else "disabled"
    next_class = "" if day_num < 365 else "disabled"

    # Indent content for proper HTML formatting
    content_lines = content.strip().split('\n')
    indented_content = '\n'.join('\t\t\t' + line for line in content_lines)

    chapter_html = CHAPTER_TEMPLATE.format(
        num=day_num,
        title=title,
        date_formatted=date_formatted,
        content=indented_content,
        prev_link=prev_link,
        next_link=next_link,
        prev_class=prev_class,
        next_class=next_class
    )

    filename = f"{day_num:03d}.html"
    filepath = CHAPTERS_DIR / filename

    with open(filepath, 'w') as f:
        f.write(chapter_html)

    # Update index
    index = load_chapters_index()
    index["chapters"][str(day_num)] = {
        "title": title,
        "date": date_formatted,
        "file": filename
    }
    save_chapters_index(index)

    print(f"Generated: {filepath}")
    print(f"Chapter {day_num}: {title} ({date_formatted})")
    return filepath


def rebuild_chapters_html():
    """Rebuild the chapters.html page from the index."""
    index = load_chapters_index()
    chapters = index.get("chapters", {})

    # Group by month
    months = {}
    for day_str, info in sorted(chapters.items(), key=lambda x: int(x[0])):
        day_num = int(day_str)
        chapter_date = get_date_for_day(day_num)
        month_key = chapter_date.strftime("%B %Y")
        if month_key not in months:
            months[month_key] = []
        months[month_key].append({
            "day": day_num,
            "title": info["title"],
            "date": info["date"],
            "file": info["file"]
        })

    # Generate chapter list HTML
    chapters_list = ""
    for month, chapter_list in months.items():
        chapters_list += f'\n\t\t<section class="archive-section">\n'
        chapters_list += f'\t\t\t<h2>{month}</h2>\n'
        chapters_list += '\t\t\t<ul class="chapter-list">\n'
        for ch in chapter_list:
            chapters_list += f'\t\t\t\t<li><a href="chapters/{ch["file"]}"><span class="chapter-title">Chapter {ch["day"]}: {ch["title"]}</span><span class="chapter-meta">{ch["date"]}</span></a></li>\n'
        chapters_list += '\t\t\t</ul>\n'
        chapters_list += '\t\t</section>\n'

    if not chapters_list:
        chapters_list = '\n\t\t<section class="archive-section">\n\t\t\t<p style="text-align: center; color: var(--color-text-muted);">No chapters published yet. The story begins January 1, 2026.</p>\n\t\t</section>\n'

    total_chapters = len(chapters)

    chapters_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>All Chapters - A Likely Story</title>
	<meta name="description" content="Browse all {total_chapters} published chapters of A Likely Story.">

	<!-- Fonts -->
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap" rel="stylesheet">

	<!-- Styles -->
	<link rel="stylesheet" href="css/design-tokens.css">
	<link rel="stylesheet" href="css/style.css">
</head>
<body>
	<nav>
		<div class="nav-inner">
			<a href="index.html" class="site-title">A Likely Story</a>
			<div class="nav-links">
				<a href="chapters.html">Chapters</a>
				<a href="about.html">About</a>
				<button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
					<span class="theme-icon">&#9790;</span>
				</button>
			</div>
		</div>
	</nav>

	<header class="container" style="padding-top: calc(var(--space-16) + 60px);">
		<h1 style="font-size: var(--text-3xl); text-transform: none; letter-spacing: var(--tracking-tight);">All Chapters</h1>
		<p class="subtitle">{total_chapters} of 365 chapters published</p>
	</header>

	<main class="container">
{chapters_list}
	</main>

	<footer>
		<p>Written by AI &middot; A Likely Story &middot; 2026</p>
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

    filepath = PROJECT_DIR / "chapters.html"
    with open(filepath, 'w') as f:
        f.write(chapters_html)

    print(f"Rebuilt: {filepath}")
    return filepath


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--rebuild-index":
        rebuild_chapters_html()
        return

    if len(sys.argv) < 4:
        print("Error: Need day_number, title, and content")
        print(__doc__)
        sys.exit(1)

    day_arg = sys.argv[1]
    title = sys.argv[2]
    content = sys.argv[3]

    if day_arg.lower() == "today":
        today = date.today()
        day_num = get_day_number_for_date(today)
        if day_num is None:
            print(f"Error: Today ({today}) is not in 2026")
            sys.exit(1)
    else:
        try:
            day_num = int(day_arg)
            if not 1 <= day_num <= 365:
                raise ValueError
        except ValueError:
            print("Error: day_number must be 1-365 or 'today'")
            sys.exit(1)

    generate_chapter(day_num, title, content)
    rebuild_chapters_html()


if __name__ == "__main__":
    main()
