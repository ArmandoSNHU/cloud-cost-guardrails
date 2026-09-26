import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cloud_guardrails import Resource, evaluate_inventory
from cloud_guardrails.cli import main


class InventoryValidationTests(unittest.TestCase):
    def record(self, **changes):
        return dict(id="fictional-1", provider="aws", type="storage", **changes)

    def test_invalid_fields_rejected_for_dict_and_resource(self):
        invalid = {
            "public": ["false", 0, None],
            "monthly_cost": [float("nan"), float("inf"), -1, True, "12", None, 10**1000],
            "open_ports": [[True], [0], [65536], [22.5], ["22"], "22"],
            "age_days": [-1, True, 1.5, "1"],
            "state": [None, "  ", 3],
            "tags": [[], {"owner": 3}, {1: "x"}],
        }
        for field, values in invalid.items():
            for value in values:
                for typed in (False, True):
                    with self.subTest(field=field, value=value, typed=typed):
                        raw = self.record(**{field: value})
                        with self.assertRaises(ValueError):
                            evaluate_inventory([Resource(**raw) if typed else raw])

    def test_required_strings(self):
        for field in ("id", "provider", "type"):
            for value in (None, "", "  ", 4):
                for typed in (False, True):
                    raw = self.record()
                    raw[field] = value
                    with self.subTest(field=field, value=value, typed=typed):
                        with self.assertRaises(ValueError):
                            evaluate_inventory([Resource(**raw) if typed else raw])
            raw = self.record()
            del raw[field]
            with self.assertRaises(ValueError):
                evaluate_inventory([raw])

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_inventory([self.record(publicly=True)])

    def test_invalid_inventory_and_entries(self):
        for raw in (None, {}, "inventory", 42, [None], ["secret"]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                evaluate_inventory(raw)

    def test_blank_tags_reported_missing(self):
        result = evaluate_inventory([self.record(tags={"owner": " ", "environment": ""})])
        self.assertEqual(len(result), 1)
        self.assertIn("environment, owner", result[0]["message"])

    def test_boundaries_and_private_storage(self):
        raw = self.record(public=False, monthly_cost=0, open_ports=[1, 65535], age_days=0,
                          tags={"owner": "team", "environment": "test"})
        self.assertEqual(evaluate_inventory([raw]), [])
        self.assertEqual(evaluate_inventory([Resource(**raw)]), [])
        self.assertEqual(evaluate_inventory(iter([raw])), [])

    def test_cli_invalid_input_is_sanitized_and_atomic(self):
        for content in ('[{"id": "SECRET"}]', '[{"id":"demo","provider":"aws","type":"storage"},null]', '[NaN]', '{SECRET', '{}', 'null'):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inventory.json"
                path.write_text(content, encoding="utf-8")
                out, err = io.StringIO(), io.StringIO()
                with patch("sys.argv", ["cloud_guardrails", str(path)]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = main()
                self.assertEqual(code, 2)
                self.assertEqual(out.getvalue(), "")
                self.assertEqual(json.loads(err.getvalue())["error"], "Invalid inventory: expected resources matching the inventory contract.")
                self.assertNotIn("SECRET", err.getvalue())

    def test_cli_missing_file_is_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            out, err = io.StringIO(), io.StringIO()
            with patch("sys.argv", ["cloud_guardrails", str(Path(directory) / "SECRET.json")]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(main(), 2)
            self.assertEqual(out.getvalue(), "")
            self.assertNotIn("SECRET", err.getvalue())
