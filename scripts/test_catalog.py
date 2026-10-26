#!/usr/bin/env python3
"""Regression tests for the SniffleShop: BUFT source validator."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_source", ROOT / "scripts" / "validate_source.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class SourceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT / "source.json").read_text(encoding="utf-8"))

    def test_checked_in_catalog_is_valid(self):
        validator.validate(self.source)

    def test_bundle_identifier_must_be_unique(self):
        data = copy.deepcopy(self.source)
        data["apps"].append(copy.deepcopy(data["apps"][0]))
        with self.assertRaisesRegex(validator.ValidationError, "duplicate"):
            validator.validate(data)

    def test_featured_apps_must_reference_existing_bundle_ids(self):
        data = copy.deepcopy(self.source)
        data["featuredApps"] = ["not.a.real.bundle"]
        with self.assertRaisesRegex(validator.ValidationError, "does not match an app"):
            validator.validate(data)

    def test_featured_app_limit_is_five(self):
        data = copy.deepcopy(self.source)
        data["featuredApps"] = [app["bundleIdentifier"] for app in data["apps"][:6]]
        with self.assertRaisesRegex(validator.ValidationError, "at most five"):
            validator.validate(data)

    def test_downloads_must_use_https(self):
        data = copy.deepcopy(self.source)
        data["apps"][0]["versions"][0]["downloadURL"] = "http://example.com/app.ipa"
        with self.assertRaisesRegex(validator.ValidationError, "absolute HTTPS"):
            validator.validate(data)

    def test_version_size_must_be_positive_bytes(self):
        data = copy.deepcopy(self.source)
        data["apps"][0]["versions"][0]["size"] = 0
        with self.assertRaisesRegex(validator.ValidationError, "positive number of bytes"):
            validator.validate(data)

    def test_unknown_metadata_is_rejected_for_review(self):
        data = copy.deepcopy(self.source)
        data["apps"][0]["unreviewedField"] = True
        with self.assertRaisesRegex(validator.ValidationError, "unsupported/unreviewed"):
            validator.validate(data)


if __name__ == "__main__":
    unittest.main()
