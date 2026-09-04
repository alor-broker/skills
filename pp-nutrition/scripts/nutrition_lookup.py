#!/usr/bin/env python3
"""Bounded, stateless USDA FoodData Central client for the Veles skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.nal.usda.gov/fdc/v1"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 20
USER_AGENT = "VelesNutritionSkill/1.0 (https://github.com/PilgrimViis/veles)"

SUMMARY_NUTRIENTS = {
    "energy_kcal": ({"energy"}, {"1008", "208"}, "kcal"),
    "protein_g": ({"protein"}, {"1003", "203"}, "g"),
    "fat_g": ({"total lipid (fat)", "total fat"}, {"1004", "204"}, "g"),
    "carbohydrate_g": (
        {"carbohydrate, by difference", "carbohydrate"},
        {"1005", "205"},
        "g",
    ),
    "fiber_g": ({"fiber, total dietary", "dietary fiber"}, {"1079", "291"}, "g"),
    "sugars_g": (
        {"sugars, total including nlea", "sugars, total", "total sugars"},
        {"2000", "269"},
        "g",
    ),
    "sodium_mg": ({"sodium, na", "sodium"}, {"1093", "307"}, "mg"),
    "potassium_mg": ({"potassium, k", "potassium"}, {"1092", "306"}, "mg"),
    "calcium_mg": ({"calcium, ca", "calcium"}, {"1087", "301"}, "mg"),
    "iron_mg": ({"iron, fe", "iron"}, {"1089", "303"}, "mg"),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def emit(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def fail(message: str, exit_code: int = 1) -> None:
    json.dump({"error": message}, sys.stderr, ensure_ascii=False)
    sys.stderr.write("\n")
    raise SystemExit(exit_code)


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def request_json(path: str, params: dict[str, Any] | None = None) -> Any:
    query = dict(params or {})
    query["api_key"] = os.environ.get("FDC_API_KEY") or "DEMO_KEY"
    url = f"{BASE_URL}{path}?{urlencode(query, doseq=True)}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        fail(f"FoodData Central returned HTTP {exc.code}", 3)
    except URLError as exc:
        fail(f"FoodData Central request failed: {exc.reason}", 3)
    if len(raw) > MAX_RESPONSE_BYTES:
        fail("FoodData Central response exceeded the 8 MiB safety limit", 3)
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("FoodData Central returned an invalid JSON response", 3)


def nutrient_rows(food: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in food.get("foodNutrients") or []:
        if not isinstance(item, dict):
            continue
        nutrient = item.get("nutrient") if isinstance(item.get("nutrient"), dict) else {}
        amount = item.get("amount", item.get("value"))
        if not isinstance(amount, (int, float)):
            continue
        name = nutrient.get("name") or item.get("nutrientName")
        unit = nutrient.get("unitName") or item.get("unitName")
        number = nutrient.get("number") or item.get("nutrientNumber")
        nutrient_id = nutrient.get("id") or item.get("nutrientId")
        if not isinstance(name, str) or not isinstance(unit, str):
            continue
        rows.append(
            {
                "id": nutrient_id,
                "number": str(number) if number is not None else None,
                "name": name,
                "unit": unit,
                "amount": round(float(amount), 6),
            }
        )
    return rows


def find_summary_value(rows: list[dict[str, Any]], names: set[str], numbers: set[str], unit: str) -> float | None:
    expected_unit = unit.lower()
    for row in rows:
        row_name = str(row.get("name", "")).lower()
        row_number = str(row.get("number") or "")
        row_unit = str(row.get("unit", "")).lower()
        if row_unit == expected_unit and (row_name in names or row_number in numbers):
            return float(row["amount"])
    return None


def nutrient_summary(food: dict[str, Any]) -> dict[str, float | None]:
    rows = nutrient_rows(food)
    return {
        key: find_summary_value(rows, names, numbers, unit)
        for key, (names, numbers, unit) in SUMMARY_NUTRIENTS.items()
    }


def identity(food: dict[str, Any]) -> dict[str, Any]:
    fdc_id = food.get("fdcId")
    return {
        "fdcId": fdc_id,
        "description": food.get("description"),
        "dataType": food.get("dataType"),
        "brandOwner": food.get("brandOwner"),
        "brandName": food.get("brandName"),
        "publicationDate": food.get("publicationDate"),
        "servingSize": food.get("servingSize"),
        "servingSizeUnit": food.get("servingSizeUnit"),
        "sourceUrl": f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{fdc_id}/nutrients"
        if fdc_id
        else None,
    }


def fetch_food(fdc_id: int) -> dict[str, Any]:
    data = request_json(f"/food/{fdc_id}", {"format": "full"})
    if not isinstance(data, dict) or not data.get("fdcId"):
        fail(f"FoodData Central did not return food {fdc_id}", 4)
    return data


def command_search(args: argparse.Namespace) -> None:
    query = args.query.strip()
    if not query or len(query) > 200:
        fail("Search query must contain 1-200 characters", 2)
    params: dict[str, Any] = {"query": query, "pageSize": args.limit}
    if args.data_type:
        params["dataType"] = ",".join(args.data_type)
    data = request_json("/foods/search", params)
    foods = data.get("foods") if isinstance(data, dict) else None
    if not isinstance(foods, list):
        fail("FoodData Central search response did not contain a foods list", 3)
    emit(
        {
            "source": "USDA FoodData Central",
            "accessedAt": now_iso(),
            "query": query,
            "totalHits": data.get("totalHits"),
            "foods": [
                {**identity(food), "nutrients": nutrient_summary(food)}
                for food in foods
                if isinstance(food, dict)
            ],
        }
    )


def command_food(args: argparse.Namespace) -> None:
    food = fetch_food(args.fdc_id)
    emit(
        {
            "source": "USDA FoodData Central",
            "accessedAt": now_iso(),
            "basis": "Amounts in the FoodData Central foodNutrients record; verify data type and serving context",
            "food": {**identity(food), "summary": nutrient_summary(food), "nutrients": nutrient_rows(food)},
        }
    )


def scaled_summary(food: dict[str, Any], basis: str) -> dict[str, float | None]:
    values = nutrient_summary(food)
    if basis == "100g":
        return values
    energy = values.get("energy_kcal")
    if not energy or energy <= 0:
        return {key: None for key in values}
    factor = 100.0 / energy
    return {key: round(value * factor, 6) if value is not None else None for key, value in values.items()}


def command_compare(args: argparse.Namespace) -> None:
    if not 2 <= len(args.fdc_ids) <= 5:
        fail("Compare requires between two and five FDC IDs", 2)
    foods = [fetch_food(fdc_id) for fdc_id in args.fdc_ids]
    emit(
        {
            "source": "USDA FoodData Central",
            "accessedAt": now_iso(),
            "basis": args.basis,
            "foods": [{**identity(food), "nutrients": scaled_summary(food, args.basis)} for food in foods],
            "warning": "Values depend on the selected records and preparation states; 100kcal values require reported kcal",
        }
    )


def parse_meal_item(value: str) -> tuple[int, float]:
    identifier, separator, grams_text = value.partition(":")
    if not separator:
        raise argparse.ArgumentTypeError("meal items must use FDC_ID:GRAMS")
    try:
        fdc_id = positive_int(identifier)
        grams = float(grams_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("meal grams must be numeric") from exc
    if grams <= 0 or grams > 100_000:
        raise argparse.ArgumentTypeError("meal grams must be greater than 0 and at most 100000")
    return fdc_id, grams


def command_meal(args: argparse.Namespace) -> None:
    if not 1 <= len(args.items) <= 20:
        fail("Meal requires between one and twenty FDC_ID:GRAMS items", 2)
    totals: dict[tuple[str, str], float] = {}
    components: list[dict[str, Any]] = []
    for fdc_id, grams in args.items:
        food = fetch_food(fdc_id)
        components.append({**identity(food), "grams": grams})
        for row in nutrient_rows(food):
            key = (row["name"], row["unit"])
            totals[key] = totals.get(key, 0.0) + float(row["amount"]) * grams / 100.0
    emit(
        {
            "source": "USDA FoodData Central",
            "accessedAt": now_iso(),
            "basis": "Each component scaled from its FoodData Central nutrient record by grams / 100",
            "components": components,
            "totals": [
                {"name": name, "unit": unit, "amount": round(amount, 6)}
                for (name, unit), amount in sorted(totals.items())
            ],
            "warning": "Recipe totals exclude missing ingredients and do not account for unreported cooking yield or nutrient retention",
        }
    )


def command_cite(args: argparse.Namespace) -> None:
    food = fetch_food(args.fdc_id)
    details = identity(food)
    emit(
        {
            "citation": f"U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, FDC ID {args.fdc_id}.",
            "food": details,
            "accessedAt": now_iso(),
        }
    )


def command_doctor(_args: argparse.Namespace) -> None:
    emit(
        {
            "service": "USDA FoodData Central",
            "endpoint": BASE_URL,
            "apiKeySource": "FDC_API_KEY" if os.environ.get("FDC_API_KEY") else "DEMO_KEY",
            "state": "stateless",
            "writes": False,
            "responseLimitBytes": MAX_RESPONSE_BYTES,
            "timeoutSeconds": TIMEOUT_SECONDS,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search FoodData Central")
    search.add_argument("query")
    search.add_argument("--limit", type=positive_int, default=10, choices=range(1, 26))
    search.add_argument("--data-type", action="append")
    search.set_defaults(handler=command_search)

    food = subparsers.add_parser("food", help="Get one food by FDC ID")
    food.add_argument("fdc_id", type=positive_int)
    food.set_defaults(handler=command_food)

    compare = subparsers.add_parser("compare", help="Compare two to five foods")
    compare.add_argument("fdc_ids", nargs="+", type=positive_int)
    compare.add_argument("--basis", choices=("100g", "100kcal"), default="100g")
    compare.set_defaults(handler=command_compare)

    meal = subparsers.add_parser("meal", help="Total FDC_ID:GRAMS components")
    meal.add_argument("items", nargs="+", type=parse_meal_item)
    meal.set_defaults(handler=command_meal)

    cite = subparsers.add_parser("cite", help="Create a source citation")
    cite.add_argument("fdc_id", type=positive_int)
    cite.set_defaults(handler=command_cite)

    doctor = subparsers.add_parser("doctor", help="Show safe runtime configuration")
    doctor.set_defaults(handler=command_doctor)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()

