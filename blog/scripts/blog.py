"""WordPress REST API publishing with encrypted Application Password credentials."""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from PIL import Image

USERNAME_ENV = "BLOG_USERNAME"
PASSWORD_ENV = "BLOG_APP_PASSWORD"
MAX_PAYLOAD = 2 * 1024 * 1024
MAX_RESPONSE = 2 * 1024 * 1024
MAX_IMAGE = 20 * 1024 * 1024
IMAGE_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}


class BlogError(Exception):
    """A safe, credential-free message for the caller."""


def validate_url(value: Any) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() or ord(char) < 32 for char in value):
        raise BlogError("Blog URLs must be nonempty HTTPS URLs without whitespace.")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        raise BlogError("Invalid blog URL.") from None
    if (
        parts.scheme != "https" or not parts.hostname or parts.username is not None
        or parts.password is not None or parts.query or parts.fragment or "\\" in value
        or (port is not None and port <= 0)
    ):
        raise BlogError("Blog URLs must use HTTPS without credentials, queries, or fragments.")
    return urlunsplit(parts).rstrip("/")


def load_settings(path: Path) -> tuple[str, str]:
    """Read only non-secret settings from the explicitly selected Veles config."""
    try:
        source = json.loads(read_bounded(path, 4 * 1024 * 1024).decode("utf-8-sig"))
        entry = source["skills"]["entries"]["blog"]
        if entry.get("enabled") is False:
            raise BlogError("The blog skill is disabled in the selected Veles configuration.")
        settings = entry["config"]
        blog_url = validate_url(settings["blogUrl"])
        api_base = validate_url(settings.get("apiBaseUrl", blog_url + "/wp-json/wp/v2"))
        if not urlsplit(api_base).path.endswith("/wp/v2"):
            raise BlogError("apiBaseUrl must end in /wp/v2. Remove the old author-app/v1 override or configure the WordPress REST API URL.")
        return blog_url, api_base
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
        raise BlogError("Set skills.entries.blog.config.blogUrl in the selected Veles config.json; set apiBaseUrl only if the WordPress REST API uses a different address.") from None


def read_bounded(path: Path, limit: int) -> bytes:
    try:
        with path.open("rb") as source:
            data = source.read(limit + 1)
    except OSError:
        raise BlogError("Cannot read the selected local file.") from None
    if not data or len(data) > limit:
        raise BlogError(f"File must contain between 1 and {limit} bytes.")
    return data


def load_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(read_bounded(path, MAX_PAYLOAD).decode("utf-8-sig"))
    except (ValueError, RecursionError):
        raise BlogError("Payload must be valid UTF-8 JSON.") from None
    allowed = {"title", "content", "status", "featured_media"}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise BlogError("Payload accepts only title, content, status, and featured_media. For multiple images, embed their uploaded URLs in content; image_media_ids is not a WordPress core field.")
    for key in ("title", "content"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise BlogError(f"Payload requires a nonempty {key} string.")
    if payload.get("status") not in ("draft", "publish"):
        raise BlogError("Set an explicit status of draft or publish; preview is local by default.")
    featured = payload.get("featured_media", 0)
    if type(featured) is not int or featured < 0:
        raise BlogError("featured_media must be a nonnegative integer (0 means no featured image).")
    return payload


def load_image(path: Path) -> tuple[bytes, str]:
    data = read_bounded(path, MAX_IMAGE)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as picture:
                mime = IMAGE_TYPES.get(picture.format)
                if mime is None:
                    raise BlogError("Only PNG, JPEG, GIF, and WebP images are supported.")
                picture.verify()
    except BlogError:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise BlogError("Image is invalid or exceeds safe image dimensions.") from None
    return data, mime


def redact(value: Any, secrets: tuple[str, ...]) -> Any:
    """Do not echo an authorization value even if a server reflects it."""
    if isinstance(value, str):
        for secret in sorted(set(secrets), key=len, reverse=True):
            if secret:
                value = value.replace(secret, "[redacted]")
        return value
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, dict):
        return {
            redact(key, secrets): (
                "[redacted]" if any(part in key.lower() for part in ("token", "authorization", "password", "secret", "cookie"))
                else redact(item, secrets)
            )
            for key, item in value.items()
        }
    return value


def request(api_base: str, method: str, path: str, **kwargs: Any) -> Any:
    username = os.environ.get(USERNAME_ENV, "").strip()
    raw_password = os.environ.get(PASSWORD_ENV, "")
    # WordPress displays Application Passwords in space-separated groups.
    password = "".join(raw_password.split())
    if not username or not password:
        raise BlogError(f"Set the encrypted skill secrets {USERNAME_ENV} and {PASSWORD_ENV} in Veles first.")
    if ":" in username or len(username) > 256 or any(ord(char) < 32 or ord(char) == 127 for char in username):
        raise BlogError("The WordPress username has an invalid format.")
    if len(password) > 8192 or any(ord(char) < 33 or ord(char) > 126 for char in password):
        raise BlogError("The Application Password has an invalid format.")
    auth = httpx.BasicAuth(username, password)
    # Also redact reflected Basic credentials, which are reversible base64.
    authorization = next(auth.auth_flow(httpx.Request("GET", api_base))).headers["Authorization"]
    secrets = (raw_password, password, authorization, authorization.split(" ", 1)[1])
    uncertain = " The write may already have succeeded; check the author interface before retrying." if method == "POST" else ""
    try:
        # Explicitly disable redirects, environment proxies, and transport retries.
        with httpx.Client(timeout=httpx.Timeout(60, connect=15), follow_redirects=False, trust_env=False) as client:
            with client.stream(
                method, api_base + path,
                headers={"Accept": "application/json"}, auth=auth,
                **kwargs,
            ) as response:
                if response.status_code in (401, 403):
                    raise BlogError("Authentication or permission denied. Check the WordPress username, Application Password, account permissions, and Application Password availability.")
                if not 200 <= response.status_code < 300:
                    raise BlogError(f"API returned HTTP {response.status_code}; no retry was made." + uncertain)
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    if len(body) + len(chunk) > MAX_RESPONSE:
                        raise BlogError("API response exceeds the 2 MiB client limit." + uncertain)
                    body.extend(chunk)
                try:
                    result = json.loads(body)
                    if not isinstance(result, (dict, list)):
                        raise ValueError
                    return redact(result, secrets)
                except (ValueError, RecursionError):
                    raise BlogError("API returned an unsupported JSON response." + uncertain) from None
    except httpx.HTTPError:
        raise BlogError("API connection failed; no retry was made." + uncertain) from None


def positive_id(value: str) -> int:
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Post ID must be a positive integer.") from None
    if result <= 0:
        raise argparse.ArgumentTypeError("Post ID must be a positive integer.")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Active Veles config.json (ordinary skill settings only).")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Preview locally, or create a draft/published post with --execute.")
    create.add_argument("--payload", type=Path, required=True)
    create.add_argument("--execute", action="store_true")
    upload = commands.add_parser("upload", help="Validate locally, or upload with --execute.")
    upload.add_argument("--file", type=Path, required=True)
    upload.add_argument("--title")
    upload.add_argument("--alt-text", default="", help="Accessible image description.")
    upload.add_argument("--execute", action="store_true")
    get = commands.add_parser("get", help="Read an existing post by ID.")
    get.add_argument("--post-id", type=positive_id, required=True)
    commands.add_parser("check-auth", help="Verify credentials with a read-only users/me request.")
    args = parser.parse_args(argv)
    try:
        blog_url, api_base = load_settings(args.config)
        if args.command == "create":
            payload = load_payload(args.payload)
            result = request(api_base, "POST", "/posts", json=payload) if args.execute else {
                "preview": True, "blog": blog_url, "destination": api_base + "/posts", "payload": payload,
            }
        elif args.command == "upload":
            data, mime = load_image(args.file)
            title = args.title if args.title is not None else args.file.name
            if not title.strip():
                raise BlogError("Image title must not be empty.")
            result = request(
                api_base, "POST", "/media", data={"title": title, "alt_text": args.alt_text},
                files={"file": (args.file.name, data, mime)},
            ) if args.execute else {
                "preview": True, "blog": blog_url, "destination": api_base + "/media",
                "filename": args.file.name, "title": title, "alt_text": args.alt_text, "mime": mime, "bytes": len(data),
            }
        elif args.command == "check-auth":
            result = request(api_base, "GET", "/users/me")
        else:
            result = request(api_base, "GET", f"/posts/{args.post_id}", params={"context": "edit"})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except BlogError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
