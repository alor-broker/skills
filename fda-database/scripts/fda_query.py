#!/usr/bin/env python3
"""Small openFDA query helper for the fda-database skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "https://api.fda.gov"
TIMEOUT_SECONDS = 20
MAX_LIMIT = 1000

ENDPOINTS = {
    "label": "drug/label",
    "event": "drug/event",
    "ndc": "drug/ndc",
    "enforcement": "drug/enforcement",
    "drugsfda": "drug/drugsfda",
    "drugshortages": "drug/shortages",
    "substance": "other/substance",
    "device-event": "device/event",
    "device-enforcement": "device/enforcement",
    "food-enforcement": "food/enforcement",
}

DEFAULT_FIELDS = {
    "label": (
        "openfda.brand_name",
        "openfda.generic_name",
        "openfda.substance_name",
        "indications_and_usage",
        "boxed_warning",
        "warnings",
        "contraindications",
        "drug_interactions",
    ),
    "event": (
        "safetyreportid",
        "receivedate",
        "serious",
        "patient.drug.medicinalproduct",
        "patient.reaction.reactionmeddrapt",
    ),
    "ndc": (
        "product_ndc",
        "brand_name",
        "generic_name",
        "labeler_name",
        "dosage_form",
        "route",
        "marketing_status",
        "active_ingredients",
        "packaging",
    ),
    "enforcement": (
        "recall_number",
        "classification",
        "status",
        "product_description",
        "reason_for_recall",
        "recall_initiation_date",
    ),
    "drugsfda": (
        "application_number",
        "sponsor_name",
        "products.brand_name",
        "products.active_ingredients.name",
        "submissions.submission_status",
        "submissions.submission_status_date",
    ),
    "drugshortages": (
        "generic_name",
        "brand_name",
        "company_name",
        "status",
        "availability",
        "update_type",
        "date_discontinued",
    ),
    "substance": (
        "unii",
        "names.name",
        "substanceClass",
        "codes.code",
        "relationships",
    ),
}


class OpenFDAError(RuntimeError):
    pass


def build_url(endpoint: str, params: dict[str, str | int]) -> str:
    return f"{BASE_URL}/{ENDPOINTS[endpoint]}.json?{urllib.parse.urlencode(params)}"


def query_openfda(
    endpoint: str,
    *,
    search: str | None,
    count: str | None,
    limit: int,
    skip: int,
    api_key: str | None,
) -> dict[str, Any]:
    params: dict[str, str | int] = {}
    if api_key:
        params["api_key"] = api_key
    if search:
        params["search"] = search
    if count:
        params["count"] = count
    else:
        params["limit"] = min(max(limit, 1), MAX_LIMIT)
        if skip:
            params["skip"] = max(skip, 0)

    request = urllib.request.Request(
        build_url(endpoint, params),
        headers={"User-Agent": "veles-fda-database/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise OpenFDAError(f"openFDA returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise OpenFDAError(f"openFDA request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OpenFDAError("openFDA request timed out") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise OpenFDAError(f"openFDA returned non-JSON response: {payload[:500]}") from exc


def get_path(value: Any, path: str) -> Any:
    current = value
    parts = path.split(".")
    for index, part in enumerate(parts):
        if isinstance(current, list):
            remainder = ".".join(parts[index:])
            values = [get_path(item, remainder) for item in current]
            return [item for item in values if item is not None]
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def compact_value(value: Any, max_chars: int) -> Any:
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if len(text) <= max_chars else f"{text[:max_chars]}..."
    if isinstance(value, list):
        return [compact_value(item, max_chars) for item in value[:5]]
    if isinstance(value, dict):
        return {key: compact_value(item, max_chars) for key, item in list(value.items())[:10]}
    return value


def summarize_results(data: dict[str, Any], endpoint: str, fields: list[str] | None, max_chars: int) -> dict[str, Any]:
    meta = data.get("meta", {})
    if "results" not in data:
        return data

    selected_fields = fields or list(DEFAULT_FIELDS.get(endpoint, ()))
    if not selected_fields:
        return data

    return {
        "meta": meta,
        "results": [
            {
                field: compact_value(get_path(result, field), max_chars)
                for field in selected_fields
                if get_path(result, field) is not None
            }
            for result in data.get("results", [])
        ],
    }


def parse_fields(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    fields = [field.strip() for field in raw.split(",") if field.strip()]
    return fields or None


def main() -> int:
    parser = argparse.ArgumentParser(description="Query openFDA endpoints.")
    parser.add_argument("endpoint", choices=sorted(ENDPOINTS), help="openFDA endpoint shortcut")
    parser.add_argument("--search", help="openFDA search expression")
    parser.add_argument("--count", help="Aggregate by field instead of returning records")
    parser.add_argument("--limit", type=int, default=10, help="Number of records to return")
    parser.add_argument("--skip", type=int, default=0, help="Pagination offset")
    parser.add_argument("--fields", help="Comma-separated fields to print from each result")
    parser.add_argument("--raw", action="store_true", help="Print the raw API response")
    parser.add_argument("--max-chars", type=int, default=700, help="Maximum characters per string field")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional delay before request")
    args = parser.parse_args()

    if args.sleep > 0:
        time.sleep(args.sleep)

    try:
        data = query_openfda(
            args.endpoint,
            search=args.search,
            count=args.count,
            limit=args.limit,
            skip=args.skip,
            api_key=os.environ.get("OPENFDA_API_KEY"),
        )
    except OpenFDAError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    output = data if args.raw or args.count else summarize_results(
        data,
        args.endpoint,
        parse_fields(args.fields),
        args.max_chars,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
