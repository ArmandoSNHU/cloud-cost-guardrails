# Contribution evidence

Author: Armando Gomez
Date: 2026-09-26
Branch: contribution/techops-reliability

## Problem and result

The former coercion converted `"public": "false"` to Python `True`, producing a false critical public-storage finding. It also accepted NaN, infinity, negative costs, booleans as costs, fractional ages/ports, and blank required tag values. Direct `Resource` objects bypassed all coercion.

Inventory dictionaries and `Resource` instances now pass the same validation before evaluation. Invalid data raises `ValueError`; CLI input failures return exit 2 with one sanitized JSON error on stderr and no findings on stdout. Blank owner/environment tags generate missing-tag findings. Valid policy names and finding shapes remain unchanged.

## Reproduce locally

From the repository root (Python 3.10+; standard library only):

```powershell
python -m unittest discover
python -m cloud_guardrails examples\sample_inventory.json --pretty
python -m cloud_guardrails examples\invalid_inventory.json
$LASTEXITCODE
```

The valid fictional example returns exit 0 and `finding_count: 6`. The invalid fictional example deliberately uses string `"false"` and returns exit 2, empty stdout, and:

```json
{"error": "Invalid inventory: expected resources matching the inventory contract."}
```

To reproduce the earlier false finding in an unmodified checkout, run the invalid example against the baseline revision's CLI: it treated `"false"` as public and emitted `public_storage`. The expression `bool("false")` is independently reproducible as `True`. No real inventory is required.

## Executed verification

Runtime: `D:\TechOpsagent\.venv\Scripts\python.exe`.

- Baseline `-m unittest discover`: `Ran 3 tests in 0.000s`, `OK`.
- New regression tests before implementation: `Ran 10 tests in 0.045s`, `FAILED (failures=62, errors=6)`.
- After implementation: `Ran 11 tests in 0.033s`, `OK`.
- Sample CLI: exit 0, six findings.
- Invalid example CLI: exit 2 and the sanitized error above.

Tests cover dictionary/typed-object parity, string false rejection, nonfinite/negative/nonnumeric costs, port and age boundaries, missing identity fields, malformed entries, blank tags, malformed JSON, absent files, sanitized errors and empty stdout on failure.

## Contract and limits

The README is the inventory contract. Unknown fields are rejected so misspellings cannot silently alter policy inputs. Optional values retain their dataclass defaults; `tags: null` means no tags. The Python API accepts iterables; the CLI requires a JSON array. Required strings must contain non-whitespace characters but are not normalized, and provider/type names are not constrained to a fixed enum.

Cost figures are heuristic review signals. `oversized_compute` means cost exceeds a fixed 300 threshold; it does not prove waste without utilization, pricing, currency, and business context. Findings on one resource may overlap: do not sum `estimated_monthly_waste` as unique savings. `age_days` is supplied by the exporter, not verified against cloud history. This contribution makes no cloud API requests, checks no real credentials or account state, and performs no remediation.

## TechOps relevance

This demonstrates input-contract design, defensive Python validation, FinOps data quality, policy-as-code, regression testing, and operationally safe CLI errors. Rejecting ambiguous public exposure and invalid monetary inputs reduces false escalations and misleading reports before cloud integrations are introduced.
