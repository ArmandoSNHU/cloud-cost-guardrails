# Cloud Cost Guardrails

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Cloud](https://img.shields.io/badge/Cloud-AWS%20%7C%20Azure%20%7C%20GCP-2563eb)](#supported-guardrails)
[![Policy](https://img.shields.io/badge/Policy-as--Code-success)](#supported-guardrails)

Cloud Cost Guardrails is a policy-as-code analyzer for cloud inventory exports. It scans JSON inventory data for cost waste, tagging gaps, public exposure, stale compute, unattached storage, and risky network rules.

The project is intentionally provider-neutral. It models the kind of guardrail logic a cloud engineer would use before wiring checks into AWS Config, Azure Policy, GCP Asset Inventory, CI pipelines, or scheduled FinOps reports.

## Supported Guardrails

| Guardrail | Why it matters |
| --- | --- |
| Missing owner or environment tag | Weak accountability and cost allocation |
| Public storage bucket | Security exposure risk |
| Open administrative port | High-risk access path |
| Oversized compute instance | Potential monthly spend waste |
| Stale stopped compute | Unused attached resources still costing money |
| Unattached disk | Direct storage waste |

## Quick Start

```powershell
python -m cloud_guardrails examples\sample_inventory.json --pretty
```

Run tests:

```powershell
python -m unittest discover
```

## Example Finding

```json
{
  "resource_id": "i-prod-001",
  "provider": "aws",
  "severity": "high",
  "rule": "oversized_compute",
  "message": "Compute resource is above the approved monthly cost threshold.",
  "estimated_monthly_waste": 315.0
}
```

## Inventory Contract

Input is a JSON array of cloud resources:

```json
{
  "id": "i-prod-001",
  "provider": "aws",
  "type": "compute",
  "state": "running",
  "monthly_cost": 420.0,
  "public": false,
  "open_ports": [443],
  "tags": {
    "owner": "platform",
    "environment": "prod"
  }
}
```

## Repository Structure

```text
cloud-cost-guardrails/
├── cloud_guardrails/
│   ├── cli.py
│   └── policies.py
├── examples/
│   └── sample_inventory.json
├── tests/
│   └── test_policies.py
├── pyproject.toml
├── README.md
└── codex.md
```

## Verification

```powershell
python -m unittest discover
python -m cloud_guardrails examples\sample_inventory.json --pretty
```

## Responsible Use

Use sanitized cloud inventory only. Do not commit account IDs, subscription IDs, public IPs, hostnames, internal tags, secrets, or production architecture data.


## Strict Validation and Error Handling

The CLI requires a JSON array of resource objects. The Python API also accepts iterables of dictionaries or `Resource` instances; both follow the same validation rules.

| Field | Contract |
| --- | --- |
| `id`, `provider`, `type` | Required strings containing non-whitespace characters |
| `state` | Nonblank string; defaults to `unknown` |
| `public` | Actual boolean only; defaults to `false`; strings such as `"false"` are rejected |
| `monthly_cost` | Finite, nonnegative integer or float, excluding booleans; defaults to zero |
| `open_ports` | List (or Python tuple) of integers 1–65535, excluding booleans; defaults to empty |
| `age_days` | Nonnegative integer, excluding booleans; defaults to zero |
| `tags` | String-to-string object or null; absent/null means no tags; blank required values count as missing |

Unknown resource fields are rejected. Strings are not normalized; policy type names are case-sensitive. Invalid input raises `ValueError` in the API. The CLI returns exit 2 with a sanitized JSON error on stderr and no partial findings on stdout, including malformed JSON and unreadable files. Valid reports return exit 0 even when they contain critical findings.

Cost thresholds are review signals, not verified waste. Findings can overlap on a resource; do not sum their estimates as unique savings. Currency, utilization, billing accuracy, and exporter-provided ages are not verified.

See [Armando Gomez's contribution evidence](docs/CONTRIBUTION.md) for before/after behavior, executable examples, test results, and TechOps relevance.
