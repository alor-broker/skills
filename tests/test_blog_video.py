"""Offline video contract checks. No server, credentials, or FFmpeg required."""

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "blog" / "scripts"
sys.path.insert(0, str(SCRIPTS))
video = importlib.import_module("upload_video")
blog = importlib.import_module("blog")

JOB = "566b841a-7eaa-4b47-aa6d-35a57cd09d1b"
BASE = "https://blog.example/wp-json/author-app/v1"
SIGNED_URL = "https://direct-uploads-oci-us-ashburn-1-vop1.mux.com/upload/example?token=private-upload-token"


def files(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"skills": {"entries": {"blog": {"config": {
        "username": "author", "blogUrl": "https://blog.example", "apiBaseUrl": BASE,
    }}}}}), encoding="utf-8")
    mp4 = tmp_path / "clip.mp4"
    mp4.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"data" * 100)
    return config, mp4


def post(status="draft"):
    return {"id": 42, "title": "Video", "content": "", "status": status,
            "videos_media": [{"id": 43, "url": f"https://blog.example/uploads/{JOB}-video.mp4"}]}


def test_upload_streams_file_then_verifies_attachment(tmp_path, monkeypatch, capsys):
    config, mp4 = files(tmp_path)
    calls, transfers = [], []

    def api(base, method, path, **kwargs):
        calls.append((method, path, kwargs))
        assert base == BASE and kwargs["username"] == "author"
        if path == "/posts/42":
            return post()
        if path == "/video-jobs":
            assert kwargs["json"] == {"filename": "clip.mp4", "mime_type": "video/mp4", "post_id": 42, "cors_origin": "https://studio.example"}
            assert "Idempotency-Key" in kwargs["headers"]
            return {"id": JOB, "status": "pending_client_upload", "upload": {"method": "PUT", "url": SIGNED_URL}}
        assert path == f"/video-jobs/{JOB}" and method == "GET"
        return {"id": JOB, "status": "completed"}

    def put(request):
        transfers.append(request)
        assert request.method == "PUT" and str(request.url) == SIGNED_URL
        assert "authorization" not in request.headers and "cookie" not in request.headers
        assert request.headers["content-type"] == "video/mp4"
        assert int(request.headers["content-length"]) == mp4.stat().st_size
        assert request.content == mp4.read_bytes()
        return httpx.Response(200)

    real_client = httpx.Client

    def client(**kwargs):
        assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        return real_client(transport=httpx.MockTransport(put), **kwargs)

    monkeypatch.setattr(video, "request", api)
    monkeypatch.setattr(video.httpx, "Client", client)
    assert video.main(["--config", str(config), "--post-id", "42", "--file", str(mp4),
                       "--cors-origin", "https://studio.example", "--execute", "--wait-seconds", "0"]) == 0
    output = capsys.readouterr().out
    result = json.loads(output.splitlines()[-1])
    assert result["status"] == "completed" and result["video"]["id"] == 43
    assert result["post_status"] == "draft"
    assert "private-upload-token" not in output
    assert len(transfers) == 1
    assert [(m, p) for m, p, _ in calls if m != "GET"] == [("POST", "/video-jobs")]
    assert mp4.exists()


def test_resume_only_polls_existing_job(tmp_path, monkeypatch, capsys):
    config, _ = files(tmp_path)
    calls = []

    def api(base, method, path, **kwargs):
        calls.append((method, path))
        return {"id": JOB, "status": "processing"}

    monkeypatch.setattr(video, "request", api)
    assert video.main(["--config", str(config), "--post-id", "42", "--job-id", JOB, "--wait-seconds", "0"]) == 0
    assert calls == [("GET", f"/video-jobs/{JOB}")]
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["status"] == "processing"


def test_preview_does_not_connect(tmp_path, monkeypatch, capsys):
    config, mp4 = files(tmp_path)
    monkeypatch.setattr(video, "request", lambda *a, **k: pytest.fail("Preview connected"))
    assert video.main(["--config", str(config), "--post-id", "42", "--file", str(mp4), "--cors-origin", "https://studio.example"]) == 0
    assert json.loads(capsys.readouterr().out)["preview"] is True


@pytest.mark.parametrize("url", ["http://direct-uploads.mux.com/upload/x", "https://127.0.0.1/upload/x", "https://direct-uploads.mux.com.evil.example/upload/x", "https://user:pass@direct-uploads.mux.com/upload/x", "https://direct-uploads.mux.com:444/upload/x"])
def test_rejects_untrusted_upload_destination(url):
    with pytest.raises(blog.BlogError):
        video.mux_url(url)


def test_mov_is_rejected_without_conversion_or_network(tmp_path, monkeypatch, capsys):
    config, mp4 = files(tmp_path)
    mov = tmp_path / "clip.mov"
    mov.write_bytes(mp4.read_bytes())
    monkeypatch.setattr(video, "request", lambda *a, **k: pytest.fail("MOV reached network"))
    assert video.main(["--config", str(config), "--post-id", "42", "--file", str(mov), "--cors-origin", "https://studio.example", "--execute"]) == 1
    assert "FFmpeg CLI" in capsys.readouterr().out
    assert mov.exists()


def test_transfer_failure_keeps_job_id_and_never_retries(tmp_path, monkeypatch, capsys):
    config, mp4 = files(tmp_path)
    writes = []

    def api(base, method, path, **kwargs):
        if method == "GET":
            return post()
        writes.append(path)
        return {"id": JOB, "upload": {"url": SIGNED_URL, "method": "PUT"}}

    def fail(*args):
        raise blog.BlogError("Transfer failed; inspect existing job.")

    monkeypatch.setattr(video, "request", api)
    monkeypatch.setattr(video, "transfer", fail)
    assert video.main(["--config", str(config), "--post-id", "42", "--file", str(mp4), "--cors-origin", "https://studio.example", "--execute"]) == 1
    output = capsys.readouterr().out
    assert json.loads(output.splitlines()[-1])["job_id"] == JOB
    assert writes == ["/video-jobs"] and mp4.exists()
    assert "private-upload-token" not in output


def test_completed_job_without_matching_attachment_is_not_ready(monkeypatch):
    def api(base, method, path, **kwargs):
        return {"id": JOB, "status": "completed"} if "/video-jobs/" in path else {"id": 42, "status": "draft", "videos_media": []}
    monkeypatch.setattr(video, "request", api)
    assert video.poll(BASE, "author", JOB, 42, 0)["status"] == "attachment_unverified"


def test_published_post_cannot_receive_new_video_job(tmp_path, monkeypatch, capsys):
    config, mp4 = files(tmp_path)
    calls = []

    def api(base, method, path, **kwargs):
        calls.append((method, path))
        return post("publish")

    monkeypatch.setattr(video, "request", api)
    assert video.main(["--config", str(config), "--post-id", "42", "--file", str(mp4),
                       "--cors-origin", "https://studio.example", "--execute"]) == 1
    assert calls == [("GET", "/posts/42")]
    assert "existing draft" in capsys.readouterr().out


def test_failed_job_stops_polling(monkeypatch):
    calls = []

    def api(*args, **kwargs):
        calls.append(args)
        return {"id": JOB, "status": "failed"}

    monkeypatch.setattr(video, "request", api)
    monkeypatch.setattr(video, "time", SimpleNamespace(monotonic=lambda: 0, sleep=lambda _: pytest.fail("Failed job kept polling")))
    assert video.poll(BASE, "author", JOB, 42, 60)["status"] == "failed"
    assert len(calls) == 1


def test_draft_creation_and_separate_confirmed_publication(tmp_path, monkeypatch, capsys):
    config, _ = files(tmp_path)
    payload = tmp_path / "draft.json"
    payload.write_text(json.dumps({"title": "Video", "content": "", "status": "draft"}), encoding="utf-8")
    current = post()
    calls = []

    def api(base, method, path, **kwargs):
        calls.append((method, path, kwargs.get("json")))
        if method == "PATCH":
            assert kwargs["json"] == {"status": "publish"}
            current["status"] = "publish"
        return dict(current)

    monkeypatch.setattr(blog, "request", api)
    assert blog.main(["--config", str(config), "create", "--payload", str(payload), "--execute"]) == 0
    assert blog.main(["--config", str(config), "publish", "--post-id", "42", "--execute"]) == 1
    assert not any(m == "PATCH" for m, _, _ in calls)
    assert blog.main(["--config", str(config), "publish", "--post-id", "42", "--execute", "--confirmed"]) == 0
    assert current["status"] == "publish"
    assert sum(m == "PATCH" for m, _, _ in calls) == 1
    assert blog.main(["--config", str(config), "publish", "--post-id", "42", "--execute", "--confirmed"]) == 0
    assert sum(m == "PATCH" for m, _, _ in calls) == 1


def test_delete_is_blocked_before_credentials_or_network(monkeypatch):
    monkeypatch.setattr(blog.httpx, "Client", lambda **k: pytest.fail("Deletion reached network"))
    with pytest.raises(blog.BlogError, match="Deletion"):
        blog.request(BASE, "DELETE", "/posts/42", username="author")
