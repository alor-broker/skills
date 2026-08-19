"""Encrypted secret helpers for the Google Workspace skill."""

from __future__ import annotations

import json
import sys
from typing import Any

from veles.secret_store.crypto import MASTER_KEY_ENV, SecretCryptoError
from veles.secret_store.store import EncryptedValuesStore

CLIENT_SECRET_KEY = "skills.google-workspace.google_client_secret_json"
TOKEN_KEY = "skills.google-workspace.google_token_json"
PENDING_AUTH_KEY = "skills.google-workspace.google_oauth_pending_json"


def _store() -> EncryptedValuesStore:
    return EncryptedValuesStore()


def secret_location() -> str:
    return str(_store().path)


def _handle_secret_error(exc: Exception) -> None:
    print(f"ERROR: Could not access Veles encrypted secrets: {exc}", file=sys.stderr)
    print(f"Set {MASTER_KEY_ENV} for the Veles process and this setup command.", file=sys.stderr)
    sys.exit(1)


def get_json_secret(key: str) -> dict[str, Any] | None:
    try:
        raw = _store().get(key)
    except SecretCryptoError as exc:
        _handle_secret_error(exc)
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Secret {key} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(value, dict):
        print(f"ERROR: Secret {key} must contain a JSON object.", file=sys.stderr)
        sys.exit(1)
    return value


def set_json_secret(key: str, value: dict[str, Any]) -> None:
    try:
        _store().set(key, json.dumps(value, ensure_ascii=False, sort_keys=True))
    except SecretCryptoError as exc:
        _handle_secret_error(exc)


def delete_json_secret(key: str) -> bool:
    try:
        return _store().delete(key)
    except SecretCryptoError as exc:
        _handle_secret_error(exc)
    return False
