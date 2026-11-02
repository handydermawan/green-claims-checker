"""
Green-Claims Checker — command-line version
===========================================

Finds environmental ("green") claims in a PDF or text file, asks Claude
yes/no questions about each claim, then scores every claim 0 / 1 / 2 with
FIXED RULES (the same rules as the web prototype). Writes a CSV.

Quick start
-----------
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="sk-ant-..."          # Windows: set ANTHROPIC_API_KEY=...

    # Whole report
    python green_claims_checker.py EQS_Sustainability_Report_2023_EN.pdf

    # Only some pages (e.g. Shell's sustainability statement)
    python green_claims_checker.py shell-annual-report-2025.pdf --pages 336-400

    # See which sentences would be sent, without calling Claude (free)
    python green_claims_checker.py report.pdf --dry-run

Things you will most likely want to edit are marked  # EDIT ME.
Prototype only — not legal advice.
"""

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------- settings
MODEL = "claude-opus-5-5"     # EDIT ME: any Claude model id your account can use
BATCH_SIZE = 40               # EDIT ME: sentences per Claude call
MAX_SENTENCES = 400           # EDIT ME: safety cap per run (cost control)
SHORT_TEXT_CHARS = 4000       # texts shorter than this are sent in full (no keyword filter)

# EDIT ME: words that mark a sentence as "about the environment"
GREEN_WORDS = re.compile(
    r"(sustainab|green|eco[- ]?friendly|\beco\b|climate|carbon|co2|co₂|emission|greenhouse|\bghg\b|"
    r"net[- ]?zero|renewabl|recycl|circular|biodivers|nature|offset|compensat|neutral|environment|"
    r"low[- ]carbon|lower[- ]carbon|decarbon|scope [123]|plastic|organic|biodegrad|compost|clean|"
    r"energy|water|waste|deforest|planet|esg|responsib)",
    re.IGNORECASE,
)

# EDIT ME: the rule text shown next to each problem
RULES = {
    "offset":   "EU Directive 2024/825, Annex I point 4c: claims of neutral, reduced or positive impact based on offsetting are banned for products.",
    "generic":  "EU Directive 2024/825, Annex I point 4a: generic claims are banned without recognised excellent performance. UK CMA Green Claims Code: clear and unambiguous.",
    "absolute": "UK CMA Green Claims Code: must not omit or hide important information, such as limits or conditions.",
    "future":   "EU Directive 2024/825, Article 6(2)(d): future performance claims need a detailed implementation plan, checked by an independent expert.",
    "evidence": "UK CMA Green Claims Code: claims must be substantiated with up-to-date evidence.",
    "baseline": "UK CMA Green Claims Code: comparisons must be fair and meaningful, so the baseline must be clear.",
    "scope":    "UK CMA Green Claims Code: say what the claim covers, considering the full life cycle.",
    "number":   "UK CMA Green Claims Code: claims must be clear; give the figure behind the claim.",
}

FLAGS = ["generic_term", "absolute_claim", "quantified", "comparative", "baseline_stated", "scope_stated",
         "evidence_cited", "offset_based", "future_target", "plan_stated"]
LABEL = {0: "High risk", 1: "Needs work", 2: "Supported"}


# ---------------------------------------------------------------- data
@dataclass
class Sentence:
    page: int | None
    text: str


@dataclass
class Claim:
    quote: str
    page: int | None
    topic: str
    rewrite: str
    flags: dict
    score: int = 1
    reasons: list = field(default_factory=list)


# ---------------------------------------------------------------- 1. read
def read_pdf(path: str, first: int | None, last: int | None) -> str:
    """Return text with a [p.N] marker before each page."""
    from pypdf import PdfReader
    reader = PdfReader(path)
    n = len(reader.pages)
    first = max(1, first or 1)
    last = min(n, last or n)
    parts = []
    for p in range(first, last + 1):
        text = reader.pages[p - 1].extract_text() or ""
        text = re.sub(r"-\n(?=[a-z])", "", text)        # join hyphenated line breaks
        text = re.sub(r"\n(?=[a-z])", " ", text)         # join broken lines
        text = re.sub(r"[ \t]+", " ", text).strip()
        if text:
            parts.append(f"[p.{p}] {text}")
        print(f"  read page {p}/{last}", end="\r", file=sys.stderr)
    print(file=sys.stderr)
    return "\n".join(parts)


def to_sentences(text: str) -> list[Sentence]:
    out, page = [], None
    for part in re.split(r"(\[p\.?\s*\d+\])", text, flags=re.IGNORECASE):
        m = re.fullmatch(r"\[p\.?\s*(\d+)\]", part, flags=re.IGNORECASE)
        if m:
            page = int(m.group(1))
            continue
        for line in re.split(r"\n+", part):
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“(])", line):
                s = re.sub(r"\s+", " ", s).strip()
                if len(s) >= 12:
                    out.append(Sentence(page, s))
    return out


def candidates(text: str) -> list[Sentence]:
    sents = to_sentences(text)
    if len(text) > SHORT_TEXT_CHARS:
        sents = [s for s in sents if GREEN_WORDS.search(s.text) and len(s.text) <= 700]
    seen, unique = set(), []
    for s in sents:
        k = s.text.lower()
        if k not in seen:
            seen.add(k)
            unique.append(s)
    return unique


# ---------------------------------------------------------------- 2. ask Claude
PROMPT = """You are checking environmental ("green") claims for a compliance tool. From the numbered lines below, find each sentence that makes an environmental claim about the company, its products or its operations (materials, emissions, energy, climate, nature, recycling, offsets, targets). Skip sentences that only describe risks, methods, definitions or general context.

For each claim return one object with exactly these fields:
"line": the number of the line it came from,
"quote": the claim copied word for word (max 300 characters),
"topic": one of "emissions","energy","materials","offsets","product","target","other",
"generic_term": true if it relies on a broad term such as eco-friendly, green, sustainable, responsible, clean, climate neutral, net zero, nature positive or lower-carbon without defining it in the same sentence,
"absolute_claim": true if it claims a full benefit (recyclable, plastic-free, zero, 100%, carbon neutral, integrated everywhere) without stating limits or conditions,
"quantified": true if it gives a number or percentage for what is claimed,
"comparative": true if it compares with the past, a target or alternatives (reduced, lower, less, more, cleaner),
"baseline_stated": true if a comparison names its baseline (a year or a named reference),
"scope_stated": true if it says what the claim covers (which products, sites, countries, emission scopes or materials),
"evidence_cited": true if the sentence names verification, assurance, a certification, a standard or a data source,
"offset_based": true if a claim of neutral, reduced or compensated impact relies on carbon offsets or compensation,
"future_target": true if it is a commitment, ambition or target about the future,
"plan_stated": true if a future target comes with interim milestones, named actions or budget in the same sentence,
"rewrite": a clearer, more precise version (max 220 characters) using only facts in the line; put facts the company must add in [square brackets].

Judge only from the text given. Use true/false booleans. Reply with only a JSON array, or [] if there are no claims.

Lines:
{lines}"""


def parse_json_array(text: str) -> list:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    return json.loads(text[start:end + 1])


def ask_claude(client, batch: list[Sentence], model: str) -> list[dict]:
    lines = "\n".join(f"{i+1}. {'[p.%d] ' % s.page if s.page else ''}{s.text}" for i, s in enumerate(batch))
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": PROMPT.format(lines=lines)}],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    return parse_json_array(text)


# ---------------------------------------------------------------- 3. score (fixed rules)
def assess(c: Claim) -> None:
    f = c.flags
    red, amber = [], []
    if f["offset_based"]:
        red.append(("Relies on carbon offsets or compensation", RULES["offset"]))
    if f["generic_term"] and not f["evidence_cited"]:
        red.append(("Broad term with no evidence named", RULES["generic"]))
    if f["absolute_claim"] and not f["evidence_cited"]:
        red.append(("Absolute claim with no limits or evidence", RULES["absolute"]))
    if f["future_target"] and not f["plan_stated"] and not f["evidence_cited"]:
        red.append(("Future target with no plan or evidence", RULES["future"]))
    if not f["quantified"]:
        amber.append(("No number given", RULES["number"]))
    if not f["scope_stated"]:
        amber.append(("Doesn't say what it covers", RULES["scope"]))
    if f["comparative"] and not f["baseline_stated"]:
        amber.append(("Comparison with no baseline", RULES["baseline"]))
    if not f["evidence_cited"] and not red:
        amber.append(("No evidence or verification named", RULES["evidence"]))
    if f["future_target"] and not f["plan_stated"] and f["evidence_cited"]:
        amber.append(("Target with no plan or milestones", RULES["future"]))

    if red:
        c.score = 0
    elif (f["quantified"] and f["scope_stated"] and f["evidence_cited"]
          and (not f["comparative"] or f["baseline_stated"])
          and (not f["future_target"] or f["plan_stated"])):
        c.score = 2
    else:
        c.score = 1
    c.reasons = red + amber


# ---------------------------------------------------------------- run
def run(sents: list[Sentence], client, model: str) -> list[Claim]:
    claims, seen = [], set()
    batches = [sents[i:i + BATCH_SIZE] for i in range(0, len(sents), BATCH_SIZE)]
    for b, batch in enumerate(batches, 1):
        print(f"  Claude is reading batch {b} of {len(batches)}…", file=sys.stderr)
        try:
            raw_claims = ask_claude(client, batch, model)
        except Exception as e:  # keep going if one batch fails
            print(f"  batch {b} failed: {e}", file=sys.stderr)
            continue
        for raw in raw_claims:
            if not isinstance(raw, dict) or not raw.get("quote"):
                continue
            quote = str(raw["quote"])[:400]
            if quote.lower() in seen:
                continue
            seen.add(quote.lower())
            line = raw.get("line")
            src = batch[line - 1] if isinstance(line, int) and 0 < line <= len(batch) else None
            c = Claim(quote=quote, page=src.page if src else None, topic=str(raw.get("topic", "other")),
                      rewrite=str(raw.get("rewrite", ""))[:400], flags={k: raw.get(k) is True for k in FLAGS})
            assess(c)
            claims.append(c)
    return claims


def write_csv(claims: list[Claim], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["score", "label", "page", "topic", "quote", "reasons", "rules", "rewrite"] + FLAGS)
        for c in sorted(claims, key=lambda c: (c.score, c.page or 0)):
            w.writerow([c.score, LABEL[c.score], c.page or "", c.topic, c.quote,
                        "; ".join(r[0] for r in c.reasons), " | ".join(r[1] for r in c.reasons), c.rewrite]
                       + [c.flags[k] for k in FLAGS])


def main() -> None:
    ap = argparse.ArgumentParser(description="Find and score green claims in a PDF or text file.")
    ap.add_argument("file", help="PDF or .txt file")
    ap.add_argument("--pages", help="page range for PDFs, e.g. 336-400")
    ap.add_argument("--out", default="green_claims_results.csv", help="CSV file to write")
    ap.add_argument("--model", default=MODEL, help="Claude model id")
    ap.add_argument("--dry-run", action="store_true", help="list the sentences that would be sent, then stop")
    args = ap.parse_args()

    first = last = None
    if args.pages:
        a, _, b = args.pages.partition("-")
        first, last = int(a), int(b or a)

    if args.file.lower().endswith(".pdf"):
        text = read_pdf(args.file, first, last)
    else:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()

    sents = candidates(text)
    print(f"{len(sents)} sentences to check.", file=sys.stderr)
    if len(sents) > MAX_SENTENCES:
        print(f"Only the first {MAX_SENTENCES} will be checked (raise MAX_SENTENCES to change).", file=sys.stderr)
        sents = sents[:MAX_SENTENCES]

    if args.dry_run:
        for s in sents:
            print(f"[p.{s.page}] {s.text}" if s.page else s.text)
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first (see the top of this file).")
    import anthropic
    client = anthropic.Anthropic()

    claims = run(sents, client, args.model)
    write_csv(claims, args.out)
    counts = {s: sum(c.score == s for c in claims) for s in (0, 1, 2)}
    print(f"\n{len(claims)} claims: {counts[0]} high risk, {counts[1]} need work, {counts[2]} supported.")
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
