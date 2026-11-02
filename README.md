# Green-Claims Checker

Find environmental ("green") claims in marketing copy and sustainability reports, rate each one for greenwashing risk, and get compliant rewrites, before a regulator does.


> **Prototype.** Built for demonstration and research. Not legal advice.

## Why

From **27 September 2026**, EU Directive 2024/825 bans vague environmental claims such as "eco-friendly" unless they are backed by recognised evidence. In the UK, the DMCC Act 2024 lets the CMA fine companies up to **10% of global turnover** for misleading claims. Companies have already been fined for claims like these:

| Claim | Company | Outcome |
|---|---|---|
| "50% ocean plastic" bags | Glad (Clorox), Australia | A$8.25 million penalty |
| Pods "can be effectively recycled" | Keurig, US | US$1.5 million SEC penalty |
| "Clean Diesel" | Volkswagen | Over €25 billion in costs |
| ESG "integrated" across investing | DWS | US$19 million (SEC) + €25 million (Germany) |

Checking claims with a lawyer costs £295–£579 an hour, so most small brands don't. This tool gives a first review in seconds.

## How it works

1. **Find.** A language model reads the text and extracts each sentence that makes an environmental claim.
2. **Answer.** For each claim it answers ten yes/no questions: does it give a number, state its scope, name evidence, rely on offsets, make a future promise, and so on.
3. **Rate.** **Fixed rules in code** turn those answers into a rating, so the model never decides the rating itself. The same answers always give the same rating, so every result can be audited.

| Rating | Rule |
|---|---|
| **0 · High risk** | Relies on carbon offsets, *or* uses a broad or absolute term ("sustainable", "recyclable", "net zero") with no evidence named, *or* is a future target with no plan or evidence |
| **2 · Supported** | No high-risk flag, and it gives a number, says what it covers, names evidence, and states a baseline for any comparison and a plan for any target |
| **1 · Needs work** | Everything else |

Each problem is linked to the rule behind it (EU Directive 2024/825, UK CMA Green Claims Code). See [docs/SCORING.md](docs/SCORING.md).


## What's in this repository

```
app/index.html                 Web app (single file: HTML, CSS, JavaScript)
python/green_claims_checker.py Command-line version for whole PDFs → CSV
python/requirements.txt        Python dependencies
examples/regulator_cases.txt   Sample input: four penalised claims and one good one
docs/TUTORIAL.md               Step-by-step guide
docs/SCORING.md                Rating rules and legal sources
docs/screenshots/              Images used in the docs
```


## Quick start

### Web app

Open `app/index.html` in a browser. Sample reviews (H&M Group, EQS Group, Shell plc, regulator cases) load straight away and work offline.

Live reviews of new text or uploaded PDFs use the claude.ai artifact runtime, so they work when the page is published as a Claude artifact. When the page is opened anywhere else, the **Run review** button explains that live reviews are unavailable.

To host the saved-review demo on **GitHub Pages**: Settings → Pages → Deploy from branch → `main`, folder `/ (root)`, then open `https://<your-username>.github.io/green-claims-checker/app/`.

### Python (whole reports)

Needs Python 3.10+ and an [Anthropic API key](https://console.anthropic.com).

```bash
cd python
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."        # Windows: set ANTHROPIC_API_KEY=sk-ant-...

python green_claims_checker.py ../examples/regulator_cases.txt
python green_claims_checker.py report.pdf --pages 336-400 --out results.csv
python green_claims_checker.py report.pdf --dry-run      # free: lists the sentences that would be sent
```

Settings you're likely to change are marked `# EDIT ME` in the script: model, batch size, keyword filter, rule text, and the rating rules in `assess()`.

## Test reports

The prototype was tested on three public reports with different styles:

- [H&M Group Annual and Sustainability Report 2024](https://hmgroup.com/wp-content/uploads/2025/03/HM-Group-Annual-and-sustainability-report-2024.pdf): retail, PR-heavy
- [EQS Group Sustainability Report 2023](https://www.eqs.com/assets/2024/05/EQS_Sustainability_Report_2023_EN.pdf): small software company, a control case
- [Shell plc Annual Report and Accounts 2025](https://www.shell.com/investors/results-and-reporting/annual-report.html): heavy industry

The PDFs are not included; download them from the links.

## Limitations

- The model can miss or misread claims. Check every result against the source.
- It judges **wording**, one sentence at a time. Evidence printed elsewhere in a report is not counted unless it is included, and it cannot detect fraud.
- The EU rules cited apply to consumer marketing. For investor reports they are used as a benchmark.
- Scanned PDFs (images of pages) have no text to read.

## Roadmap

- [ ] Published accuracy benchmark against expert-labelled claims
- [ ] Evidence matching: link each claim to supporting documents
- [ ] Rule packs for more countries
- [ ] Browser extension and Google Docs add-on
- [ ] Monitoring agent that re-checks websites and drafts supplier evidence requests, with human approval

## License

[MIT](LICENSE) © 2026 Handy Dermawan

---

<sub>Powered by Claude Opus 5.5</sub>
