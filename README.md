# The Working Accord

Ten plain-language rules for how people and AI share work in Canada, with sourced evidence and history. Started by mode40 (Winnipeg).

- Source pages: `src/pages/*.html` (each starts with a `<!--meta {...} -->` block)
- Layout: `src/layout.html`; styles and scripts: `src/assets/`
- Build: `python3 build.py` (production, indexable, canonical https://workingaccord.ca)
- Preview build for GitHub Pages: `STAGING=1 BASE=/working-accord/ python3 build.py` (noindex + preview bar)
- Output: `docs/` (GitHub Pages serves this folder)

The build fails on unreplaced placeholders, em dashes, "Mode40", missing or extra h1 tags, and broken internal links.

Status: concept preview, not launched.
