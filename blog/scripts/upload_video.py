"""Upload a prepared MP4 to an existing draft through author-app video jobs.

No conversion, post creation, publication, deletion, or credential files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from blog import BlogError, load_settings, positive_id, request, validate_url

MAX_VIDEO = 2 * 1024 * 1024 * 1024
PENDING = {"pending_client_upload", "processing", "ready_for_archive", "archiving_to_wp"}


def uuid_arg(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except ValueError:
        raise argparse.ArgumentTypeError("Expected a UUID.") from None


def wait_arg(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Wait must be 0-60 seconds.") from None
    if not 0 <= number <= 60:
        raise argparse.ArgumentTypeError("Wait must be 0-60 seconds.")
    return number


def emit(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False), flush=True)


def validate_mp4(stream, path: Path) -> int:
    size = os.fstat(stream.fileno()).st_size
    header = stream.read(12)
    stream.seek(0)
    if path.suffix.lower() != ".mp4" or len(header) < 12 or header[4:8] != b"ftyp" or header[8:12] == b"qt  ":
        raise BlogError("Provide a prepared MP4. Convert MOV with FFmpeg CLI according to SKILL.md first.")
    if not 0 < size <= MAX_VIDEO:
        raise BlogError("MP4 exceeds the 2 GiB client limit or is empty.")
    return size


def mux_url(value) -> str:
    try:
        parts = urlsplit(value) if isinstance(value, str) else None
        if (not parts or parts.scheme != "https" or parts.username is not None or parts.password is not None
                or parts.port not in (None, 443) or parts.fragment or "\\" in value
                or any(c.isspace() or ord(c) < 32 for c in value)
                or not re.fullmatch(r"direct-uploads(?:-[a-z0-9]+)*\.mux\.com", parts.hostname or "")
                or not parts.path.startswith("/upload/")):
            raise ValueError
    except ValueError:
        raise BlogError("The job returned an unsupported upload destination. No file bytes were sent.") from None
    return value


def transfer(stream, size: int, url: str) -> None:
    """One bounded-memory PUT; a separate client has no WordPress credentials."""
    url = mux_url(url)
    before = os.fstat(stream.fileno())
    if before.st_size != size:
        raise BlogError("MP4 changed before upload. Check the existing job before continuing.")
    sent = 0

    def chunks():
        nonlocal sent
        while block := stream.read(1024 * 1024):
            sent += len(block)
            if sent > size:
                raise BlogError("MP4 changed during upload. No retry was made.")
            yield block
        after = os.fstat(stream.fileno())
        if sent != size or after.st_size != size or after.st_mtime_ns != before.st_mtime_ns:
            raise BlogError("MP4 changed during upload. Check the existing job; no retry was made.")

    try:
        with httpx.Client(timeout=httpx.Timeout(60, connect=15), follow_redirects=False, trust_env=False) as client:
            with client.stream("PUT", url, headers={"Content-Type": "video/mp4", "Content-Length": str(size)}, content=chunks()) as response:
                if not 200 <= response.status_code < 300:
                    raise BlogError(f"Mux returned HTTP {response.status_code}. Check the existing job; no upload retry was made.")
        if sent != size:
            raise BlogError("Upload did not consume the whole file. Check the existing job.")
    except (httpx.HTTPError, OSError):
        raise BlogError("MP4 transfer failed. The signed URL is hidden. Check the existing job before any further upload.") from None


def poll(api_base: str, username: str, job_id: str, post_id: int, wait_seconds: int) -> dict:
    deadline = time.monotonic() + wait_seconds
    delay = 5
    while True:
        job = request(api_base, "GET", f"/video-jobs/{job_id}", username=username)
        if not isinstance(job, dict) or job.get("id") != job_id:
            raise BlogError("Unexpected job response; keep the saved job ID.")
        status = job.get("status")
        if status == "completed":
            post = request(api_base, "GET", f"/posts/{post_id}", username=username)
            if not isinstance(post, dict) or post.get("id") != post_id:
                raise BlogError("Job completed, but post read-back could not be verified.")
            videos = post.get("videos_media", [])
            if not isinstance(videos, list):
                videos = []
            if isinstance(post.get("video_media"), dict):
                videos = videos + [post["video_media"]]
            for video in videos:
                if (isinstance(video, dict) and type(video.get("id")) is int and video["id"] > 0
                        and job_id in str(video.get("url", ""))):
                    return {"status": "completed", "job_id": job_id, "post_id": post_id,
                            "post_status": post.get("status"), "video": video,
                            "next": "Read the complete draft, show it with the video, and obtain publication confirmation."}
            return {"status": "attachment_unverified", "job_id": job_id, "post_id": post_id,
                    "next": "Do not publish yet. Check the same job/post again; do not upload another copy."}
        if status == "failed":
            return {"status": "failed", "job_id": job_id, "post_id": post_id,
                    "next": "Inspect this job in Writer Studio. No files or posts were deleted."}
        if status not in PENDING:
            raise BlogError("Unknown video-job status. No further write was made.")
        emit({"status": status, "job_id": job_id, "post_id": post_id})
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"status": status, "job_id": job_id, "post_id": post_id,
                    "next": "Resume with --job-id and the same --post-id; this does not upload again."}
        time.sleep(min(delay, remaining))
        delay = min(delay * 2, 15)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--post-id", type=positive_id, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--file", type=Path, help="Prepared MP4; preview unless --execute is supplied.")
    mode.add_argument("--job-id", type=uuid_arg, help="Check an existing job without creating or uploading anything.")
    parser.add_argument("--cors-origin", help="Writer Studio HTTPS origin, required for a new upload.")
    parser.add_argument("--idempotency-key", type=uuid_arg)
    parser.add_argument("--wait-seconds", type=wait_arg, default=60)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    job_id = args.job_id
    try:
        _, api_base, username = load_settings(args.config)
        if not urlsplit(api_base).path.endswith("/author-app/v1"):
            raise BlogError("MP4 video jobs require an explicitly configured author-app/v1 API.")
        if not job_id:
            if not args.cors_origin:
                raise BlogError("Provide --cors-origin with the site's Writer Studio HTTPS origin for a new upload.")
            origin = validate_url(args.cors_origin)
            if urlsplit(origin).path:
                raise BlogError("--cors-origin must be an HTTPS origin without a path.")
            if not args.file.is_file():
                raise BlogError("MP4 must be an existing regular file.")
            with args.file.open("rb") as stream:
                size = validate_mp4(stream, args.file)
                if not args.execute:
                    emit({"preview": True, "file": str(args.file.resolve()), "bytes": size,
                          "post_id": args.post_id, "api_base": api_base, "username": username,
                          "cors_origin": origin})
                    return 0
                post = request(api_base, "GET", f"/posts/{args.post_id}", username=username)
                if not isinstance(post, dict) or post.get("id") != args.post_id or post.get("status") != "draft":
                    raise BlogError("Upload requires an existing draft; no video job was created.")
                key = args.idempotency_key or str(uuid.uuid4())
                emit({"status": "creating_job", "post_id": args.post_id, "idempotency_key": key})
                job = request(api_base, "POST", "/video-jobs", username=username,
                              headers={"Idempotency-Key": key}, json={"filename": args.file.name,
                                  "mime_type": "video/mp4", "post_id": args.post_id, "cors_origin": origin})
                try:
                    job_id = str(uuid.UUID(job["id"]))
                except (KeyError, TypeError, ValueError, AttributeError):
                    raise BlogError("Job response lacks a valid ID. Reconcile with the saved idempotency key before retrying.") from None
                emit({"status": "job_created", "job_id": job_id, "post_id": args.post_id, "idempotency_key": key})
                upload = job.get("upload", {})
                if not isinstance(upload, dict) or upload.get("method") != "PUT":
                    raise BlogError("Job has no supported upload instruction. Keep its ID; do not create another.")
                transfer(stream, size, upload.get("url"))
                emit({"status": "uploaded", "job_id": job_id, "post_id": args.post_id})
        result = poll(api_base, username, job_id, args.post_id, args.wait_seconds)
        emit(result)
        return 1 if result["status"] == "failed" else 0
    except (BlogError, OSError) as error:
        message = str(error) if isinstance(error, BlogError) else "Cannot read the MP4 file. No automatic retry was made."
        emit({"error": message, **(error.details if isinstance(error, BlogError) else {}),
              "job_id": job_id, "post_id": args.post_id})
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
