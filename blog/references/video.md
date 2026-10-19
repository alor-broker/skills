# Video upload workflow

Use this workflow for video requests. Python only uploads an already prepared MP4. The agent handles conversion through the FFmpeg CLI and coordinates draft creation, review, and publication. The uploader contains no FFmpeg calls, post editing, publication, deletion, journal, or credential-file storage.

## 1. Prepare MP4 through the shell

Follow the MOV conversion instructions in `SKILL.md`. Check/install FFmpeg when needed, preserve the source, choose a new output filename, use `-n`, and verify the converted video with a playable preview. Do not pass MOV to the uploader. The agent must inspect codecs/duration; the uploader only checks MP4 filename/header and the 2 GiB client size ceiling. The server may impose a lower limit.

## 2. Prepare an unpublished draft

Video jobs require an existing post ID. Reuse the intended draft or create one once with `blog.py`:

```json
{"title":"Video title","content":"","status":"draft","image_media_ids":[]}
```

```text
python <skill-dir>/scripts/blog.py --config <active-config> create --payload <draft.json> --execute
```

Include the intended final title/body/images at draft creation. Empty body is supported for author-app drafts. Retain the returned ID; do not create another draft after an ambiguous response. Draft creation and uploads must be authorized by the user's task, while public publication requires the separate final confirmation.

## 3. Upload the prepared MP4

```text
python <skill-dir>/scripts/upload_video.py --config <active-config> --post-id <draft-id> --file <video.mp4> --cors-origin https://lk.yourwpcare.com --execute
```

Use the site's actual Writer Studio HTTPS origin for `--cors-origin`. The value above comes from the supplied browser capture, not a universal default. It is a job-creation setting, not a destination for credentials. Without `--execute`, this command performs a local preview only.

The uploader verifies that the selected post is a draft, creates one job with an `Idempotency-Key`, streams the file once to the returned Mux URL, then checks processing. It flushes a JSON progress record containing the idempotency key before job creation and another containing `job_id` before transfer. Retain those records in the task context. An optional `--idempotency-key <uuid>` accepts a previously chosen key, but do not assume undocumented replay semantics or retry blindly.

The upload URL is sensitive: it is never printed or saved. Only HTTPS `direct-uploads*.mux.com/upload/…` destinations matching the implementation's host rule are accepted. A separate HTTP client sends the bytes without WordPress authorization or cookies. Redirects and automatic transfer retries are disabled. Data is streamed in 1 MiB chunks, not loaded into model context or a whole-file memory buffer. Give the shell enough time for a large transfer.

## 4. Resume processing checks

The default polling budget is 60 seconds; `--wait-seconds` accepts 0–60. Individual HTTP requests also have their own timeouts. Pending status does not mean failure. Continue with the same ID:

```text
python <skill-dir>/scripts/upload_video.py --config <active-config> --post-id <draft-id> --job-id <job-uuid> --wait-seconds 60
```

This mode never creates a job or uploads bytes. States observed in Writer Studio are `pending_client_upload`, `processing`, `ready_for_archive`, `archiving_to_wp`, `completed`, and `failed`. On completion, the script reads the post and verifies a video URL containing that job UUID, as in the supplied backend output. It returns the media record and current post status. If this association cannot be verified, it returns `attachment_unverified`; do not publish until resolved.

If transfer was interrupted, inspect the existing job. This version resumes status polling, not partially transferred bytes. Do not re-run file mode automatically. If no job ID was returned, reconcile using the emitted idempotency key in the site's logs/interface. Preserve the draft and all files; never clean up through deletion.

## 5. Show the full post and confirm

After the video is attached:

```text
python <skill-dir>/scripts/blog.py --config <active-config> publish --post-id <draft-id>
```

This only reads and displays the post. Present the complete title, body, all media and playable video to the user, identify the blog, and explicitly ask whether to publish that exact version. Follow `SKILL.md`; never infer confirmation from the initial task. If the content changes, show and confirm the changed version again.

## 6. Publish the same draft

Only after the user's affirmative reply:

```text
python <skill-dir>/scripts/blog.py --config <active-config> publish --post-id <draft-id> --execute --confirmed
```

This sends only `status: publish`, preserving attached video and other fields, then reads the post back. It uses PATCH for author-app and POST for standard WordPress. An already published post is reported without another write. `--confirmed` records the caller's assertion; the program cannot inspect chat consent or lock out concurrent edits by someone using WordPress. The agent must check that the current draft still matches the confirmed version.

No live upload or publication was performed while implementing this workflow.
