#!/usr/bin/env python3
"""
Entrez Search - поиск в базах данных NCBI через E-utilities.
"""
import argparse
import json
import os
import sys
import time

import requests


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_TOOL = "veles-entrez-search"
REQUEST_TIMEOUT_SECONDS = 20

DB_ALIASES = {
    "nucleotide": "nuccore",
    "pubchem": "pccompound",
    "chem": "pccompound",
    "disease": "clinvar",
}


def normalize_db(db):
    """Return the E-utilities database name for a user-facing alias."""
    return DB_ALIASES.get(db.lower(), db.lower())


def request_eutils(endpoint, params, email=None, api_key=None, tool=DEFAULT_TOOL):
    """Call an E-utilities endpoint with common identity and safety parameters."""
    request_params = dict(params)
    if email:
        request_params["email"] = email
    if api_key:
        request_params["api_key"] = api_key
    if tool:
        request_params["tool"] = tool

    url = f"{BASE_URL}/{endpoint}"
    headers = {"User-Agent": f"{tool or DEFAULT_TOOL}/1.0"}
    try:
        response = requests.get(
            url,
            params=request_params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:500].replace("\n", " ")
        raise RuntimeError(f"NCBI {endpoint} failed with HTTP {response.status_code}: {detail}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"NCBI {endpoint} request failed: {exc}") from exc
    return response


def parse_json_response(response, endpoint):
    try:
        return response.json()
    except ValueError as exc:
        detail = response.text[:500].replace("\n", " ")
        raise RuntimeError(f"NCBI {endpoint} returned non-JSON response: {detail}") from exc


def search(db, term, retmax=10, retstart=0, sort=None, email=None, api_key=None, tool=DEFAULT_TOOL):
    """Поиск ID статей/генов/белков"""
    params = {
        "db": db,
        "term": term,
        "retmax": retmax,
        "retstart": retstart,
        "retmode": "json",
    }
    if sort:
        params["sort"] = sort

    response = request_eutils("esearch.fcgi", params, email=email, api_key=api_key, tool=tool)
    data = parse_json_response(response, "esearch.fcgi")
    
    id_list = data.get("esearchresult", {}).get("idlist", [])
    count = data.get("esearchresult", {}).get("Count", "0")
    query_translation = data.get("esearchresult", {}).get("querytranslation")
    
    return {"idlist": id_list, "count": count, "querytranslation": query_translation}


def summary(db, ids, email=None, api_key=None, tool=DEFAULT_TOOL):
    """Получение сводки по ID"""
    if not ids:
        return {"error": "No IDs provided"}
    
    params = {
        "db": db,
        "id": ",".join(ids),
        "retmode": "json",
    }
    
    response = request_eutils("esummary.fcgi", params, email=email, api_key=api_key, tool=tool)
    return parse_json_response(response, "esummary.fcgi")


def fetch_abstracts(db, ids, rettype="abstract", email=None, api_key=None, tool=DEFAULT_TOOL):
    """Получение абстрактов для PubMed"""
    if not ids or db != "pubmed":
        return {"error": "Abstracts only available for pubmed"}
    
    params = {
        "db": db,
        "id": ",".join(ids),
        "rettype": rettype,
        "retmode": "text",
    }
    
    response = request_eutils("efetch.fcgi", params, email=email, api_key=api_key, tool=tool)
    return {"text": response.text}


def main():
    parser = argparse.ArgumentParser(description="Entrez Search")
    parser.add_argument(
        "--db",
        default="pubmed",
        help="База данных: pubmed, pmc, gene, protein, nuccore, clinvar, pccompound, pcsubstance, pcassay, mesh, snp",
    )
    parser.add_argument("--term", required=True, help="Поисковый запрос")
    parser.add_argument("--retmax", type=int, default=10, help="Максимум результатов")
    parser.add_argument("--retstart", type=int, default=0, help="Смещение результатов")
    parser.add_argument("--sort", default=None, help="Порядок сортировки, например relevance или date")
    parser.add_argument("--email", default=os.environ.get("NCBI_EMAIL"), help="Email для NCBI (опционально)")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("NCBI_API_KEY"),
        help="NCBI API key (опционально; можно хранить как секрет NCBI_API_KEY)",
    )
    parser.add_argument(
        "--tool",
        default=os.environ.get("NCBI_TOOL", DEFAULT_TOOL),
        help="Имя инструмента для NCBI requests",
    )
    parser.add_argument("--rettype", default="abstract", help="EFetch rettype для --abstracts")
    parser.add_argument("--summary", action="store_true", help="Показать сводку")
    parser.add_argument("--abstracts", action="store_true", help="Получить абстракты (только pubmed)")
    
    args = parser.parse_args()
    db = normalize_db(args.db)
    
    # Поиск
    print(f"Поиск: {args.term} в {db}...")
    search_result = search(
        db,
        args.term,
        retmax=args.retmax,
        retstart=args.retstart,
        sort=args.sort,
        email=args.email,
        api_key=args.api_key,
        tool=args.tool,
    )
    
    print(f"Найдено: {search_result.get('count', 0)} результатов")
    print(f"ID: {', '.join(search_result.get('idlist', []))}")
    if search_result.get("querytranslation"):
        print(f"Query translation: {search_result['querytranslation']}")
    
    if args.summary and search_result.get("idlist"):
        time.sleep(0.34 if args.api_key else 0.5)  # Rate limiting
        print("\nСводка:")
        summ = summary(db, search_result["idlist"], email=args.email, api_key=args.api_key, tool=args.tool)
        print(json.dumps(summ, indent=2, ensure_ascii=False))
    
    if args.abstracts and search_result.get("idlist"):
        time.sleep(0.34 if args.api_key else 0.5)
        print("\nАбстракты:")
        abstracts = fetch_abstracts(
            db,
            search_result["idlist"],
            rettype=args.rettype,
            email=args.email,
            api_key=args.api_key,
            tool=args.tool,
        )
        print(abstracts.get("text") or abstracts.get("error", ""))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        sys.exit(1)
