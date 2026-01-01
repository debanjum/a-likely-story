# Overview

This repository powers **A Likely Story**: a **365‑chapter**, **live‑unfolding** cozy, serial published daily for the year **2026**.

**Author:** *Panini* AI. A human maintains oversight, infrastructure and may occasionally provide small steering notes.

---

## Canonical premise (do not drift)
- Protagonist: A “modal” human — the statistically most likely human to be found in 2026. A reasonable, coherent approximation happens to be an Indian (population mode), 22-year-old (Indian age group mode), living in a semi-urban environment. Female as need more stories with female protagonists. 
- Tone: **cozy, day-in-the-life**, routines, small frictions, small kindnesses, standard dramas, warm human details.
- Reality mode: **mixed reality**
  - Fictional characters and story arc.
  - Real-world events (news, weather, season, holidays) can influence the texture and trajectory of the fictional world.  Use them to ground story or set ambience. Disregard them if they do not add to the story. E.g Earthquake in their town should feature, blast in another city need not.
- Narrative mode: **present tense**, events unfold **as the day happens** (not a retrospective diary).

---

## Project layout

### Static site (served by GitHub Pages)
- `index.html` — home
- `chapters.html` — archive
- `about.html` — disclosure + project description
- `chapters/NNN.html` — published chapter pages (generated)
- `css/` — styling

### Source-of-truth writing inputs
- `manuscript/` — **markdown** source chapters (**canonical text**)
  - Preferred filename: `manuscript/YYYY-MM-DD.md`
  - Accepted filename: `manuscript/NNN.md`

### Story state (continuity)
- `story/character.yaml` — character card (relatively stable)
- `story/bible.json` — facts ledger + open threads (mutable)
- `story/timeline.ndjson` — append‑only daily event log / recaps (mutable)

### Publishing pipeline
- `scripts/publish.py` — converts markdown → HTML chapter, updates:
  - `chapters/NNN.html`
  - `chapters.json`
  - `chapters.html`
  - `rss.xml`
- `templates/chapter_template.html` — HTML template used by publisher
- `pyproject.toml` — python deps (project-local)
- `.venv/` — uv-managed virtualenv (local)

---

## Daily operating procedure (Panini)

### 0) Determine which day we’re writing
- The story calendar is fixed: **Jan 1, 2026 = Chapter 001**.
- Chapter number = NNN format day-of-year in 2026.

### 1) Load context (minimum required)
Read:
- `story/character.yaml`
- `story/bible.json`
- Recent items from `story/timeline.ndjson` (last 7–14 days)
- The previous chapter markdown in `manuscript/` (and/or the generated HTML in `chapters/`)

Optional:
- Any manual steering notes a human drops will be at `story/manual_inputs/YYYY-MM-DD.txt`.
- You can use real-world context (weather, seasonality, local or major news) **for grounding, ambience**. Only include if it weaves in naturally with the story. It can provide good m

### 2) Write today’s chapter (markdown)
Create: `manuscript/YYYY-MM-DD.md`

Recommended frontmatter:
```yaml
---
title: "..."
excerpt: "..."  # optional; used for RSS
---
```

Style checklist:
- Present tense.
- Cozy, grounded; small moments matter.
- Avoid melodrama; no thriller pacing.
- 0–2 short Hindi phrases, gloss in-context.
- Introduce at most 1–2 new named entities per week.

Guardrails:
- No real private individuals.
- No defamatory claims.
- No detailed medical/legal accusations.
- If referencing real news, keep it high-level and non-accusatory.

### 3) Consistency review (before publishing)
- Verify no contradictions with `story/bible.json` facts.
- If we introduced new stable facts (new recurring character/place), update `story/bible.json`.
- Append a new line to `story/timeline.ndjson` with:
  - date, chapter number
  - 5–10 “facts introduced”
  - 3–7 “events”
  - 1–3 “open hooks”

### 4) Publish locally (generate HTML + RSS)
From repo root:
```bash
uv run python scripts/publish.py <day_number>
# or
uv run python scripts/publish.py today
```

Review generated artifacts:
- `chapters/NNN.html` renders correctly
- `chapters.html` updated
- `rss.xml` updated

### 5) Commit + push (GitHub Pages)
- Commit markdown + generated site artifacts.
- Push to the main branch to publish post to https://alikelystory.org (via Github pages)

---

## Roadmap: Panini skill (to be created after pipeline is final)
We will create a Panini skill that:
1) Opens this repo
2) Finds the correct day
3) Reads `story/*` + recent manuscript chapters
4) Drafts today’s markdown chapter
5) Runs `scripts/publish.py`
6) Reviews outputs (HTML + RSS)
7) Prepares the git commit (human can push)

Skill will enforce guardrails and continuity checks as a first-class step.
