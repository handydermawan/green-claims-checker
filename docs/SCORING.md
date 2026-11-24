# Rating rules

The language model only answers yes/no questions about each claim. The verdict is computed in code (`assess()` in `app/index.html` and `python/green_claims_checker.py`), so it is deterministic and auditable.

## The questions

| Field | True when the claim… |
|---|---|
| `generic_term` | relies on a broad term (eco-friendly, green, sustainable, clean, climate neutral, net zero, lower-carbon…) without defining it |
| `absolute_claim` | claims a full benefit (recyclable, plastic-free, zero, 100%, carbon neutral) without limits or conditions |
| `quantified` | gives a number or percentage |
| `comparative` | compares with the past, a target or alternatives |
| `baseline_stated` | names the baseline of a comparison (a year or reference) |
| `scope_stated` | says what it covers (products, sites, countries, emission scopes, materials) |
| `evidence_cited` | names verification, assurance, a certification, a standard or a data source |
| `offset_based` | claims neutral or reduced impact through offsets or compensation |
| `future_target` | is a commitment or target about the future |
| `plan_stated` | gives interim milestones, actions or budget for a target |

## Rules

**Not approved** if any of these apply:

| Flag | Condition | Source |
|---|---|---|
| Relies on offsets | `offset_based` | EU Directive 2024/825, Annex I point 4c |
| Broad term, no evidence | `generic_term` and not `evidence_cited` | EU Directive 2024/825, Annex I point 4a; CMA Green Claims Code (clear and unambiguous) |
| Absolute claim, no evidence | `absolute_claim` and not `evidence_cited` | CMA Green Claims Code (must not omit or hide important information) |
| Target, no plan or evidence | `future_target` and not `plan_stated` and not `evidence_cited` | EU Directive 2024/825, Article 6(2)(d) |

**Approved** if there is no red flag and all of these hold: `quantified`, `scope_stated`, `evidence_cited`, a baseline for any comparison, and a plan for any target.

**Moderately approved** otherwise. The reasons list whichever is missing: number, scope, baseline or evidence (CMA Green Claims Code).

## Sources

- [Directive (EU) 2024/825, Empowering Consumers for the Green Transition](https://eur-lex.europa.eu/eli/dir/2024/825/oj): applies from 27 September 2026
- [UK CMA Green Claims Code](https://www.gov.uk/government/publications/green-claims-code-making-environmental-claims)

These rules are a simplified screening model, not a legal test.
