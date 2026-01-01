# A Likely Story

A Likely Story is a **365-chapter** cozy serial published daily for the year **2026**.

- Plain static HTML/CSS site (GitHub Pages friendly)
- Chapters are authored in **markdown** and published as generated HTML
- RSS feed at `rss.xml`

## Repo quick tour

- `index.html`, `chapters.html`, `about.html` — site pages
- `chapters/` — generated chapter pages (`001.html`, `002.html`, ...)
- `manuscript/` — markdown source chapters (**canonical content**)
- `scripts/publish.py` — markdown → HTML + updates archive + RSS
- `story/` — character card + continuity state

## Setup (project-local Python env via uv)

```bash
cd ~/Code/HTML5/ALikelyStory
uv venv
uv pip install "Markdown>=3.6" "PyYAML>=6.0"
```

## Write + publish a chapter

1) Create a markdown file:

- Preferred: `manuscript/YYYY-MM-DD.md`
- Accepted: `manuscript/NNN.md`

Example:
```md
---
title: "Day 001: The Fog and the Milk Run"
excerpt: "He steps outside and the fog makes the lane feel like a secret."
---

(Chapter text...)
```

2) Publish (generates `chapters/NNN.html`, updates `chapters.html`, `chapters.json`, `rss.xml`):

```bash
uv run python scripts/publish.py 1
```

Dry run:
```bash
uv run python scripts/publish.py 1 --dry-run
```

## GitHub Pages + custom domain

- This repo can be served via GitHub Pages.
- Add/update `CNAME` at repo root with your final domain.
- Update `SITE_URL` in `scripts/publish.py` so RSS item links are correct.

## Operating procedure

See `AGENTS.md` for the daily workflow and guardrails.
