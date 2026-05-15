# Codex Guide

## Purpose

This repository is a cloud engineering and FinOps portfolio project. It should show policy-as-code thinking, provider-neutral inventory modeling, and testable guardrail logic.

## Commands

```powershell
python -m cloud_guardrails examples\sample_inventory.json --pretty
python -m unittest discover
```

## Editing Rules

- Keep sample inventory sanitized and fictional.
- Do not commit real account IDs, subscription IDs, public IPs, DNS names, cloud tags, or billing exports.
- Each new policy should have at least one unit test.
- Keep findings structured with `resource_id`, `provider`, `severity`, `rule`, `message`, and `estimated_monthly_waste`.
- Update README guardrail tables when policy names change.

