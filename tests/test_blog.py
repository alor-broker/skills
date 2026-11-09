"""Offline checks: no live API or encrypted user storage is accessed."""

import base64
import importlib.util
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

SPEC = importlib.util.spec_from_file_location(
    "blog_skill", Path(__file__).resolve().parents[1] / "blog/scripts/blog.py"
)
blog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blog)


def setup_files(tmp_path, settings=None):
    config = tmp_path / "config.json"
    settings = {"username": "test-user", **(settings or {
        "blogUrl": "https://public.example", "apiBaseUrl": "https://author.example/wp-json/wp/v2",
    })}
    config.write_text(json.dumps({"skills": {"entries": {"blog": {"config": settings}}}}), encoding="utf-8")
    payload = tmp_path / "post.json"
    payload.write_text(json.dumps({"title": "Статья", "content": "<p>Текст</p>", "status": "publish"}), encoding="utf-8")
    return config, payload


def mock_client(monkeypatch, handler):
    original = httpx.Client

    def factory(**kwargs):
        assert kwargs["follow_redirects"] is False
        assert kwargs["trust_env"] is False
        return original(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(blog.httpx, "Client", factory)
    # A stale encrypted/environment login must never override config.username.
    monkeypatch.setenv("BLOG_USERNAME", "wrong-legacy-login")
    monkeypatch.setenv("BLOG_APP_PASSWORD", "test only secret")


def test_preview_is_local_without_credentials(tmp_path, monkeypatch, capsys):
    config, payload = setup_files(tmp_path)
    monkeypatch.delenv("BLOG_USERNAME", raising=False)
    monkeypatch.delenv("BLOG_APP_PASSWORD", raising=False)
    monkeypatch.setattr(blog, "request", lambda *a, **k: pytest.fail("Preview made a request"))
    assert blog.main(["--config", str(config), "create", "--payload", str(payload)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["preview"] is True
    assert result["blog"] == "https://public.example"
    assert result["destination"] == "https://author.example/wp-json/wp/v2/posts"
    assert result["payload"]["title"] == "Статья"


def test_configured_api_and_real_multipart_bytes(tmp_path, monkeypatch, capsys):
    config, _ = setup_files(tmp_path)
    photo = tmp_path / "photo.png"
    Image.new("RGB", (2, 2), "red").save(photo)
    seen = []

    def handle(request):
        seen.append(request)
        assert str(request.url) == "https://author.example/wp-json/wp/v2/media"
        assert base64.b64decode(request.headers["authorization"].removeprefix("Basic ")) == b"test-user:testonlysecret"
        assert "multipart/form-data; boundary=" in request.headers["content-type"]
        assert photo.read_bytes() in request.content
        assert b'name="title"' in request.content
        assert b'name="alt_text"' in request.content
        assert "Описание".encode() in request.content
        return httpx.Response(201, json={"id": 123})

    mock_client(monkeypatch, handle)
    assert blog.main(["--config", str(config), "upload", "--file", str(photo), "--alt-text", "Описание", "--execute"]) == 0
    assert len(seen) == 1
    assert json.loads(capsys.readouterr().out)["id"] == 123


@pytest.mark.parametrize("kind", ["redirect", "timeout", "server-error", "invalid-json", "too-large"])
def test_uncertain_writes_are_never_retried(monkeypatch, kind):
    calls = []

    def handle(request):
        calls.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout("private server details", request=request)
        if kind == "redirect":
            return httpx.Response(307, headers={"location": "https://other.example/stolen"})
        if kind == "server-error":
            return httpx.Response(500, text="test-only-secret")
        if kind == "too-large":
            return httpx.Response(200, content=b"x" * (blog.MAX_RESPONSE + 1))
        return httpx.Response(200, text="not json")

    mock_client(monkeypatch, handle)
    with pytest.raises(blog.BlogError, match="may already have succeeded") as error:
        blog.request("https://author.example", "POST", "/posts", username="test-user", json={})
    assert len(calls) == 1
    assert "test-only-secret" not in str(error.value)
    assert "private server details" not in str(error.value)


def test_publish_readback_and_secret_redaction(tmp_path, monkeypatch, capsys):
    config, payload = setup_files(tmp_path)
    calls = []

    def handle(request):
        calls.append(request)
        if request.method == "POST":
            assert json.loads(request.content)["status"] == "publish"
        return httpx.Response(200, json={"id": 42, "status": "publish", "token": "another-secret", "echo": request.headers["authorization"], "raw": "test only secret", "normalized": "testonlysecret", "encoded": request.headers["authorization"].split(" ", 1)[1]})

    mock_client(monkeypatch, handle)
    assert blog.main(["--config", str(config), "create", "--payload", str(payload), "--execute", "--confirmed"]) == 0
    assert blog.main(["--config", str(config), "get", "--post-id", "42"]) == 0
    output = capsys.readouterr().out
    assert all(secret not in output for secret in ("test only secret", "testonlysecret", "another-secret", base64.b64encode(b"test-user:testonlysecret").decode()))
    assert [request.method for request in calls] == ["POST", "GET"]
    assert calls[1].url.path.endswith("/posts/42")
    assert calls[1].url.params["context"] == "edit"


def test_default_endpoint_preserves_subdirectory(tmp_path):
    config, _ = setup_files(tmp_path, {"blogUrl": "https://public.example/blog/"})
    assert blog.load_settings(config) == ("https://public.example/blog", "https://public.example/blog/wp-json/wp/v2", "test-user")


@pytest.mark.parametrize("url", ["http://example.com", "https://user:pass@example.com", "https://example.com/?token=x", "https://example.com/#fragment"])
def test_rejects_unsafe_destination_urls(url):
    with pytest.raises(blog.BlogError):
        blog.validate_url(url)


@pytest.mark.parametrize("featured", [True, -1, "1", [1]], ids=["boolean", "negative", "string", "list"])
def test_rejects_invalid_featured_media(tmp_path, featured):
    payload = tmp_path / "post.json"
    payload.write_text(json.dumps({"title": "Title", "content": "Body", "status": "publish", "featured_media": featured}), encoding="utf-8")
    with pytest.raises(blog.BlogError):
        blog.load_payload(payload)


def test_rejects_legacy_image_list(tmp_path):
    payload = tmp_path / "post.json"
    payload.write_text(json.dumps({"title": "Title", "content": "Body", "status": "publish", "image_media_ids": [123]}), encoding="utf-8")
    with pytest.raises(blog.BlogError, match="image_media_ids"):
        blog.load_payload(payload)


@pytest.mark.parametrize("status", ["draft", "publish"])
def test_standard_payload_preserves_content_and_cover(tmp_path, monkeypatch, status):
    config, payload = setup_files(tmp_path)
    expected = {"title": "Title", "content": '<p>Text</p><img src="https://public.example/uploads/photo.png" alt="Photo">', "status": status, "featured_media": 123}
    payload.write_text(json.dumps(expected), encoding="utf-8")
    seen = []

    def handle(request):
        seen.append(request)
        assert json.loads(request.content) == expected
        assert request.url.path == "/wp-json/wp/v2/posts"
        return httpx.Response(201, json={"id": 42, "status": status})

    mock_client(monkeypatch, handle)
    assert blog.main(["--config", str(config), "create", "--payload", str(payload), "--execute", "--confirmed"]) == 0
    assert len(seen) == 1


def test_read_only_auth_check(tmp_path, monkeypatch):
    config, _ = setup_files(tmp_path)
    calls = []

    def handle(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.path == "/wp-json/wp/v2/users/me"
        assert request.url.params["context"] == "edit"
        assert request.url.params["_fields"] == "id,name,slug,roles,capabilities"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(200, json={"id": 5, "name": "Test User"})

    mock_client(monkeypatch, handle)
    assert blog.main(["--config", str(config), "check-auth"]) == 0
    assert len(calls) == 1


@pytest.mark.parametrize("status,code", [(401, "incorrect_password"), (403, "rest_cannot_create")])
def test_wordpress_error_details_reach_cli_without_secrets(tmp_path, monkeypatch, capsys, status, code):
    config, _ = setup_files(tmp_path)
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={
            "code": code,
            "message": "<strong>Доступ запрещён</strong> test only secret " + request.headers["authorization"],
            "data": {"debug": "private server data"},
            "extra": "private details",
        })

    mock_client(monkeypatch, handle)
    assert blog.main(["--config", str(config), "check-auth"]) == 1
    output = capsys.readouterr()
    assert not output.out
    details = json.loads(output.err)
    assert details["http_status"] == status
    assert details["wp_code"] == code
    assert "Доступ запрещён" in details["wp_message"]
    assert "<strong>" not in details["wp_message"]
    assert all(value not in output.err for value in (
        "test only secret", "testonlysecret", "private server data", "private details",
        base64.b64encode(b"test-user:testonlysecret").decode(),
    ))
    assert len(calls) == 1


@pytest.mark.parametrize("kind", ["html", "oversized", "malformed", "long-message"])
def test_error_diagnostics_are_bounded_and_do_not_dump_bodies(monkeypatch, kind):
    def handle(request):
        if kind == "html":
            return httpx.Response(403, text="<html>private firewall page</html>")
        if kind == "oversized":
            return httpx.Response(403, content=b"x" * (blog.MAX_ERROR_RESPONSE + 1))
        if kind == "malformed":
            return httpx.Response(403, json={"code": {"bad": "shape"}, "message": ["private"]})
        return httpx.Response(403, json={"code": "rest_cannot_create", "message": "x" * 795 + "testonlysecret" + "y" * 1000})

    mock_client(monkeypatch, handle)
    with pytest.raises(blog.BlogError) as error:
        blog.request("https://public.example/wp-json/wp/v2", "POST", "/posts", username="test-user", json={})
    details = error.value.details
    assert details["http_status"] == 403
    if kind == "html":
        assert details["response_kind"] == "non_json"
    elif kind == "oversized":
        assert details["response_kind"] == "oversized"
    elif kind == "malformed":
        assert "wp_message" not in details and "wp_code" not in details
    else:
        assert len(details["wp_message"]) == 800
        assert "test" not in details["wp_message"]
    assert "private" not in json.dumps(details)


def test_unknown_endpoint_rejected_before_request(tmp_path, monkeypatch, capsys):
    config, _ = setup_files(tmp_path, {"blogUrl": "https://public.example", "apiBaseUrl": "https://author.example/wp-json/unknown/v1"})
    monkeypatch.setattr(blog, "request", lambda *a, **k: pytest.fail("Legacy API received credentials"))
    assert blog.main(["--config", str(config), "check-auth"]) == 1
    assert "apiBaseUrl must end" in capsys.readouterr().err


def test_bearer_token_is_not_a_fallback(monkeypatch):
    monkeypatch.setenv("BLOG_TOKEN", "unused-old-token")
    monkeypatch.delenv("BLOG_USERNAME", raising=False)
    monkeypatch.delenv("BLOG_APP_PASSWORD", raising=False)
    monkeypatch.setattr(blog.httpx, "Client", lambda **k: pytest.fail("Missing credentials made a request"))
    with pytest.raises(blog.BlogError, match="BLOG_APP_PASSWORD"):
        blog.request("https://public.example/wp-json/wp/v2", "GET", "/users/me", username="test-user")


@pytest.mark.parametrize("status", [401, 403])
def test_auth_failures_do_not_expose_response_or_retry(monkeypatch, status):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, text="testonlysecret")

    mock_client(monkeypatch, handle)
    with pytest.raises(blog.BlogError, match="Application Password") as error:
        blog.request("https://public.example/wp-json/wp/v2", "GET", "/users/me", username="test-user")
    assert "testonlysecret" not in str(error.value)
    assert len(calls) == 1

@pytest.mark.parametrize("command", ["check-auth", "create", "get", "upload"])
def test_author_app_exchanges_application_password_then_uses_bearer(tmp_path, monkeypatch, capsys, command):
    config, payload = setup_files(tmp_path, {"blogUrl": "https://public.example", "apiBaseUrl": "https://author.example/wp-json/author-app/v1"})
    payload.write_text(json.dumps({"title": "Test", "content": "Body", "status": "publish", "image_media_ids": [123]}), encoding="utf-8")
    photo = tmp_path / "photo.png"
    Image.new("RGB", (2, 2), "red").save(photo)
    calls = []

    def handle(request):
        calls.append(request)
        if len(calls) == 1:
            assert request.method == "POST"
            assert request.url.path == "/wp-json/author-app/v1/auth/session"
            assert "authorization" not in request.headers
            assert json.loads(request.content) == {"username": "test-user", "password": "testonlysecret"}
            return httpx.Response(200, json={"access_token": "fake-access-token", "refresh_token": "fake-refresh-token"})
        assert request.headers["authorization"] == "Bearer fake-access-token"
        if command == "check-auth":
            assert request.url.path.endswith("/config") and request.method == "GET"
        elif command == "create":
            assert request.url.path.endswith("/posts") and request.method == "POST"
            assert json.loads(request.content)["image_media_ids"] == [123]
        elif command == "upload":
            assert request.url.path.endswith("/media") and request.method == "POST"
            assert photo.read_bytes() in request.content
        else:
            assert request.url.path.endswith("/posts/42") and not request.url.query
        return httpx.Response(200, json={"id": 42, "echo": "fake-access-token fake-refresh-token testonlysecret"})

    mock_client(monkeypatch, handle)
    args = ["--config", str(config), command]
    if command == "create":
        args += ["--payload", str(payload), "--execute", "--confirmed"]
    if command == "get":
        args += ["--post-id", "42"]
    if command == "upload":
        args += ["--file", str(photo), "--execute"]
    assert blog.main(args) == 0
    assert len(calls) == 2
    output = capsys.readouterr().out
    assert all(secret not in output for secret in ("fake-access-token", "fake-refresh-token", "testonlysecret"))


@pytest.mark.parametrize("failure", ["denied", "redirect", "missing-token", "timeout"])
def test_failed_session_never_sends_post_or_retries(monkeypatch, failure):
    calls = []

    def handle(request):
        calls.append(request)
        assert request.url.path.endswith("/auth/session")
        if failure == "timeout":
            raise httpx.ReadTimeout("private detail", request=request)
        if failure == "redirect":
            return httpx.Response(307, headers={"Location": "https://other.example/"})
        if failure == "denied":
            return httpx.Response(401, json={"code": "invalid_credentials", "message": "testonlysecret"})
        return httpx.Response(200, json={"refresh_token": "private-refresh"})

    mock_client(monkeypatch, handle)
    with pytest.raises(blog.BlogError) as error:
        blog.request("https://author.example/wp-json/author-app/v1", "POST", "/posts", username="test-user", json={})
    assert error.value.details["phase"] == "authentication"
    assert "no content request was sent" in str(error.value)
    assert len(calls) == 1
    assert "testonlysecret" not in json.dumps(error.value.details)


def test_author_app_preview_needs_no_credentials_or_session(tmp_path, monkeypatch, capsys):
    config, payload = setup_files(tmp_path, {"blogUrl": "https://public.example", "apiBaseUrl": "https://author.example/wp-json/author-app/v1"})
    monkeypatch.delenv("BLOG_USERNAME", raising=False)
    monkeypatch.delenv("BLOG_APP_PASSWORD", raising=False)
    monkeypatch.setattr(blog, "request", lambda *a, **k: pytest.fail("Preview started authentication"))
    assert blog.main(["--config", str(config), "create", "--payload", str(payload)]) == 0
    assert json.loads(capsys.readouterr().out)["preview"] is True

@pytest.mark.parametrize("username", [None, "", "   ", 123, "user:password", "bad\nlogin"], ids=["missing", "empty", "blank", "number", "colon", "newline"])
def test_bad_config_username_never_uses_legacy_secret_or_network(tmp_path, monkeypatch, capsys, username):
    config, _ = setup_files(tmp_path)
    source = json.loads(config.read_text(encoding="utf-8"))
    settings = source["skills"]["entries"]["blog"]["config"]
    if username is None:
        del settings["username"]
    else:
        settings["username"] = username
    config.write_text(json.dumps(source), encoding="utf-8")
    monkeypatch.setenv("BLOG_USERNAME", "legacy-login")
    monkeypatch.setenv("BLOG_APP_PASSWORD", "test only secret")
    monkeypatch.setattr(blog, "request", lambda *a, **k: pytest.fail("Invalid login reached the network"))
    assert blog.main(["--config", str(config), "check-auth"]) == 1
    output = capsys.readouterr()
    assert "skills.entries.blog.config.username" in output.err
    assert "test only secret" not in output.err


def test_preview_displays_configured_login(tmp_path, monkeypatch, capsys):
    config, payload = setup_files(tmp_path, {"blogUrl": "https://public.example", "username": " configured-login "})
    monkeypatch.setenv("BLOG_USERNAME", "wrong-legacy-login")
    monkeypatch.setattr(blog, "request", lambda *a, **k: pytest.fail("Preview made a request"))
    assert blog.main(["--config", str(config), "create", "--payload", str(payload)]) == 0
    assert json.loads(capsys.readouterr().out)["username"] == "configured-login"
