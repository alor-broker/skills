#!/usr/bin/env python3
"""Bounded, read-only Open Food Facts client for the Veles skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://world.openfoodfacts.org"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 20
BARCODE_PATTERN = re.compile(r"^[0-9]{8,14}$")
FIELDS = (
    "code,product_name,brands,countries,countries_tags,quantity,serving_size,"
    "nutriments,ingredients_text,allergens,allergens_tags,traces,traces_tags,"
    "additives_n,additives_tags,nutriscore_grade,nova_group,ecoscore_grade,"
    "data_quality_tags,last_modified_t,labels_tags"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def user_agent() -> str:
    contact = os.environ.get("OPEN_FOOD_FACTS_CONTACT_EMAIL", "").strip()
    identity = contact or "https://github.com/PilgrimViis/veles"
    return f"VelesNutritionSkill/1.0 ({identity})"


def emit(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def fail(message: str, exit_code: int = 1) -> None:
    json.dump({"error": message}, sys.stderr, ensure_ascii=False)
    sys.stderr.write("\n")
    raise SystemExit(exit_code)


def bounded_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 120:
        raise argparse.ArgumentTypeError("filter values must contain 1-120 characters")
    return cleaned


def page_size(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("page size must be an integer") from exc
    if not 1 <= parsed <= 10:
        raise argparse.ArgumentTypeError("page size must be between 1 and 10")
    return parsed


def barcode(value: str) -> str:
    if not BARCODE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("barcode must contain 8-14 digits")
    return value


def request_json(path: str, params: dict[str, Any] | None = None) -> Any:
    suffix = f"?{urlencode(params or {})}" if params else ""
    request = Request(
        f"{BASE_URL}{path}{suffix}",
        headers={"Accept": "application/json", "User-Agent": user_agent()},
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        fail(f"Open Food Facts returned HTTP {exc.code}", 3)
    except URLError as exc:
        fail(f"Open Food Facts request failed: {exc.reason}", 3)
    if len(raw) > MAX_RESPONSE_BYTES:
        fail("Open Food Facts response exceeded the 8 MiB safety limit", 3)
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("Open Food Facts returned an invalid JSON response", 3)


def warnings_for(product: dict[str, Any]) -> list[str]:
    warnings = ["Open Food Facts is community-contributed; verify consequential details on the current package label."]
    if not product.get("product_name"):
        warnings.append("Product name is missing.")
    if not product.get("ingredients_text"):
        warnings.append("Ingredient text is missing.")
    if not product.get("nutriments"):
        warnings.append("Nutrient data is missing.")
    if not product.get("allergens_tags"):
        warnings.append("No structured allergen tags are present; this does not prove allergen absence.")
    return warnings


def normalize_product(product: dict[str, Any]) -> dict[str, Any]:
    code = str(product.get("code") or "")
    return {
        "barcode": code,
        "productName": product.get("product_name"),
        "brands": product.get("brands"),
        "quantity": product.get("quantity"),
        "servingSize": product.get("serving_size"),
        "countries": product.get("countries"),
        "countryTags": product.get("countries_tags") or [],
        "labels": product.get("labels_tags") or [],
        "ingredientsText": product.get("ingredients_text"),
        "allergens": product.get("allergens"),
        "allergenTags": product.get("allergens_tags") or [],
        "traces": product.get("traces"),
        "traceTags": product.get("traces_tags") or [],
        "additiveCount": product.get("additives_n"),
        "additiveTags": product.get("additives_tags") or [],
        "nutriments": product.get("nutriments") or {},
        "nutriScoreGrade": product.get("nutriscore_grade"),
        "novaGroup": product.get("nova_group"),
        "ecoScoreGrade": product.get("ecoscore_grade"),
        "dataQualityTags": product.get("data_quality_tags") or [],
        "lastModifiedTimestamp": product.get("last_modified_t"),
        "sourceUrl": f"{BASE_URL}/product/{code}" if code else None,
        "warnings": warnings_for(product),
    }


def fetch_product(code: str) -> dict[str, Any]:
    data = request_json(f"/api/v2/product/{quote(code)}.json", {"fields": FIELDS})
    if not isinstance(data, dict) or data.get("status") != 1 or not isinstance(data.get("product"), dict):
        fail(f"Open Food Facts did not find barcode {code}", 4)
    product = data["product"]
    if not product.get("code"):
        product["code"] = code
    return product


def envelope(payload: dict[str, Any]) -> dict[str, Any]:
    return {"source": "Open Food Facts", "accessedAt": now_iso(), **payload}


def command_product(args: argparse.Namespace) -> None:
    emit(envelope({"product": normalize_product(fetch_product(args.barcode))}))


def command_nutrition(args: argparse.Namespace) -> None:
    product = normalize_product(fetch_product(args.barcode))
    emit(
        envelope(
            {
                "product": {
                    key: product[key]
                    for key in (
                        "barcode",
                        "productName",
                        "brands",
                        "quantity",
                        "servingSize",
                        "countries",
                        "nutriments",
                        "nutriScoreGrade",
                        "novaGroup",
                        "ecoScoreGrade",
                        "dataQualityTags",
                        "sourceUrl",
                        "warnings",
                    )
                }
            }
        )
    )


def command_allergens(args: argparse.Namespace) -> None:
    product = normalize_product(fetch_product(args.barcode))
    emit(
        envelope(
            {
                "product": {
                    key: product[key]
                    for key in (
                        "barcode",
                        "productName",
                        "brands",
                        "countries",
                        "ingredientsText",
                        "allergens",
                        "allergenTags",
                        "traces",
                        "traceTags",
                        "additiveCount",
                        "additiveTags",
                        "dataQualityTags",
                        "sourceUrl",
                        "warnings",
                    )
                }
            }
        )
    )


def command_compare(args: argparse.Namespace) -> None:
    if not 2 <= len(args.barcodes) <= 5:
        fail("Compare requires between two and five barcodes", 2)
    emit(envelope({"products": [normalize_product(fetch_product(code)) for code in args.barcodes]}))


def search_params(args: argparse.Namespace) -> dict[str, Any]:
    mappings = {
        "category": "categories_tags",
        "brand": "brands_tags",
        "country": "countries_tags",
        "label": "labels_tags",
        "grade": "nutrition_grades_tags",
    }
    params: dict[str, Any] = {"fields": FIELDS, "page_size": args.page_size}
    for attribute, parameter in mappings.items():
        value = getattr(args, attribute, None)
        if value:
            params[parameter] = value
    if len(params) == 2:
        fail("Structured search requires at least one category, brand, country, label, or grade filter", 2)
    return params


def command_search(args: argparse.Namespace) -> None:
    params = search_params(args)
    data = request_json("/api/v2/search", params)
    products = data.get("products") if isinstance(data, dict) else None
    if not isinstance(products, list):
        fail("Open Food Facts search response did not contain a products list", 3)
    emit(
        envelope(
            {
                "page": data.get("page"),
                "pageSize": data.get("page_size"),
                "count": data.get("count"),
                "products": [normalize_product(product) for product in products if isinstance(product, dict)],
            }
        )
    )


def command_category(args: argparse.Namespace) -> None:
    args.category = args.category_name
    args.brand = args.country = args.label = args.grade = None
    command_search(args)


def command_doctor(_args: argparse.Namespace) -> None:
    emit(
        {
            "service": "Open Food Facts",
            "endpoint": BASE_URL,
            "authenticationRequired": False,
            "customUserAgentConfigured": bool(os.environ.get("OPEN_FOOD_FACTS_CONTACT_EMAIL", "").strip()),
            "state": "stateless",
            "writes": False,
            "maxProductsPerSearch": 10,
            "maxProductsPerComparison": 5,
            "responseLimitBytes": MAX_RESPONSE_BYTES,
            "timeoutSeconds": TIMEOUT_SECONDS,
        }
    )


def add_search_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--category", type=bounded_text)
    parser.add_argument("--brand", type=bounded_text)
    parser.add_argument("--country", type=bounded_text)
    parser.add_argument("--label", type=bounded_text)
    parser.add_argument("--grade", type=bounded_text)
    parser.add_argument("--page-size", type=page_size, default=5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, handler in (
        ("product", command_product),
        ("nutrition", command_nutrition),
        ("allergens", command_allergens),
    ):
        command = subparsers.add_parser(name)
        command.add_argument("barcode", type=barcode)
        command.set_defaults(handler=handler)

    compare = subparsers.add_parser("compare")
    compare.add_argument("barcodes", nargs="+", type=barcode)
    compare.set_defaults(handler=command_compare)

    search = subparsers.add_parser("search")
    add_search_filters(search)
    search.set_defaults(handler=command_search)

    category = subparsers.add_parser("category")
    category.add_argument("category_name", type=bounded_text)
    category.add_argument("--page-size", type=page_size, default=5)
    category.set_defaults(handler=command_category)

    doctor = subparsers.add_parser("doctor")
    doctor.set_defaults(handler=command_doctor)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()

