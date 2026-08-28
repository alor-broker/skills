"""Regression coverage for Entrez credential redaction."""

from __future__ import annotations

import importlib.util
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "entrez_search.py"
SPEC = importlib.util.spec_from_file_location("entrez_search", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
ENTREZ = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENTREZ)


class EntrezCredentialRedactionTests(unittest.TestCase):
    def test_request_exception_chain_does_not_render_email_or_api_key(self) -> None:
        email = "private-medical@example.invalid"
        api_key = "ncbi-secret-value"
        prepared = requests.Request(
            "GET",
            f"{ENTREZ.BASE_URL}/esearch.fcgi",
            params={"email": email, "api_key": api_key},
        ).prepare()
        source_error = requests.ConnectionError(f"connection failed for {prepared.url}")

        with patch.object(ENTREZ.requests, "get", side_effect=source_error):
            with self.assertRaises(RuntimeError) as raised:
                ENTREZ.request_eutils(
                    "esearch.fcgi",
                    {"db": "pubmed", "term": "asthma"},
                    email=email,
                    api_key=api_key,
                )

        rendered = "".join(traceback.format_exception(raised.exception))
        self.assertNotIn(email, rendered)
        self.assertNotIn(api_key, rendered)
        self.assertNotIn(str(prepared.url), rendered)
        self.assertIsNone(raised.exception.__cause__)


if __name__ == "__main__":
    unittest.main()
