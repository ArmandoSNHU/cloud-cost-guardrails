import unittest

from cloud_guardrails import evaluate_inventory


class CloudGuardrailTests(unittest.TestCase):
    def test_public_storage_is_critical(self):
        findings = evaluate_inventory(
            [
                {
                    "id": "bucket-1",
                    "provider": "aws",
                    "type": "storage",
                    "public": True,
                    "tags": {"owner": "team", "environment": "prod"},
                }
            ]
        )

        self.assertTrue(any(f["rule"] == "public_storage" for f in findings))
        self.assertTrue(any(f["severity"] == "critical" for f in findings))

    def test_oversized_compute_estimates_waste(self):
        findings = evaluate_inventory(
            [
                {
                    "id": "vm-1",
                    "provider": "azure",
                    "type": "compute",
                    "monthly_cost": 450,
                    "tags": {"owner": "ops", "environment": "prod"},
                }
            ]
        )

        oversized = next(f for f in findings if f["rule"] == "oversized_compute")
        self.assertEqual(oversized["estimated_monthly_waste"], 150.0)

    def test_missing_tags_reports_names(self):
        findings = evaluate_inventory([{"id": "disk-1", "provider": "gcp", "type": "disk", "tags": {}}])

        tag_finding = next(f for f in findings if f["rule"] == "missing_required_tags")
        self.assertIn("environment", tag_finding["message"])
        self.assertIn("owner", tag_finding["message"])


if __name__ == "__main__":
    unittest.main()

