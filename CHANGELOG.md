# Changelog

Every version of the Green-Claims Checker. Each is a git tag, so `git checkout <tag>` opens it exactly as it was.

## [0.6.0] — 24 November 2026: clearer verdicts and reports

- Verdicts renamed **Not approved / Moderately approved / Approved** (were High risk / Needs work / Supported), in the app, the Python script, the CSV and the docs.
- Every claim card now explains its verdict in one sentence.
- **Copy report** button: a plain-text summary to paste into an email.
- **Demo mode**: outside claude.ai the app says so clearly and keeps the saved reviews working. Error messages now say what to do next.
- Python: checks several files in one run (`--out-dir`), and writes a readable HTML report next to each CSV.
- Automatic tests for the rules (`tests/test_rules.py`).
- Screenshots refreshed.

## [0.5.0] — 2 November 2026: sustainability colours

- New forest-and-sage palette: pine app bar, sage background, green leaf logo, in light and dark mode.
- Rating colours unchanged: red = high risk, amber = needs work, green = supported.
- Screenshots added to the README and tutorial.

## [0.4.0] — 2 November 2026: wording and model

- Main button renamed **Run review** (was "Run review with Claude").
- Live reviews request Claude Opus 5.5 by name; if a viewer's account can't use it, another Claude model answers.
- "Powered by Claude Opus 5.5" line added at the bottom of the app.
- Python version defaults to `claude-opus-5-5`.

## [0.3.0] — 2 November 2026: corporate redesign and Python version

- Redesigned as a business review workspace: app bar, "Reviews / New review" header, numbered **Source document** and **Review results** panels, document icons for samples, proportional font instead of monospace.
- Renamed controls: Run review with Claude, Show saved review, Export results (CSV), How ratings are decided.
- Added `python/green_claims_checker.py`: reads a whole PDF (with page range), calls the Claude API in batches, applies the same rating rules, writes a CSV. `--dry-run` lists sentences without calling the API.
- Added README, tutorial, rating rules, example input, MIT licence and `.gitignore`.

## [0.2.0] — 2 November 2026: progress state

- While a live review runs, the results panel shows "Waiting for Claude's first answer…" instead of "No green claims found".

## [0.1.0] — 2 November 2026: first MVP

- Paste text or upload a PDF (read in the browser with pdf.js; page range; filtered to environment-related sentences).
- The language model answers ten yes/no questions per claim; fixed rules rate each claim 0 / 1 / 2.
- Reasons linked to EU Directive 2024/825 and the UK CMA Green Claims Code; suggested rewrites with [brackets] for missing facts.
- Saved reviews for H&M Group 2024, EQS Group 2023, Shell plc 2025 and four regulator cases (Glad, Keurig, Volkswagen, DWS) plus one well-supported example.
- Summary counts, filters, copy rewrite, CSV export.
