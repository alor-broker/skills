# Video upload workflow

Use this workflow for video requests. Python only uploads an already prepared MP4. The agent handles conversion through the FFmpeg CLI and coordinates draft creation, review, and publication. The uploader contains no FFmpeg calls, post editing, publication, deletion, journal, or credential-file storage.

## 1. Prepare MP4 through the shell

Follow the MOV conversion instructions in `SKILL.md`. Check/install FFmpeg when needed, preserve the source, choose a new output filename, use `-n`, and verify the converted video with a playable preview. Do not pass MOV to the uploader. The agent must inspect codecs/duration; the uploader only checks MP4 filename/header and the 2 GiB client size ceiling. The server may impose a lower limit.

Inspect the streams first. When the selected video/audio streams are already MP4-playback compatible, remux without re-encoding:

```text
ffmpeg -nostdin -hide_banner -n -loglevel warning -stats_period 5 -progress <new-progress-log> -i <input.mov> -map 0:v:0 -map 0:a? -c copy -movflags +faststart <new-output.mp4>
```

Adapt argument quoting to the host shell (especially the optional `0:a?` mapping). Choose unique output/log paths. Verify orientation, duration, and playable audio/video; stream copy does not apply visual filters. If only audio is incompatible, use `-c:v copy -c:a aac` instead of `-c copy`. If video actually needs encoding, choose a suitable H.264 preset such as `veryfast`; do not re-encode purely because the source extension is MOV.

Track the exact process and read the progress log at least every 30–60 seconds. The `speed` and `out_time` values distinguish slow encoding from a stalled operation. Check CPU allocation/throttling and storage if progress stalls, and check whether the process has already exited before blaming FFmpeg. Do not wait silently for many minutes or start duplicate encodes. Preserve partial outputs. These are shell instructions, not Python conversion code. [FFmpeg stream copy and progress documentation](https://ffmpeg.org/ffmpeg.html).

## 2. Prepare an unpublished draft

Video jobs require an existing post ID. Reuse the intended draft or create one once with `blog.py`:

```json
{"title":"Video title","content":"","status":"draft","image_media_ids":[]}
```

```text
python <skill-dir>/scripts/blog.py --config <active-config> create --payload <draft.json> --execute
```

Include the intended final title/body/images at draft creation. Empty body is supported for author-app drafts. Retain the returned ID; do not create another draft after an ambiguous response. Draft creation and uploads must be authorized by the user's task, while public publication requires the separate final confirmation.

Tell the user that this creates an unpublished draft, not a public blog entry. Do not offer its returned `?p=<id>` permalink as a public preview: it can show “not found” to a logged-out reader. Follow the explicit status and usable-link rules in `SKILL.md` throughout the workflow.

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

This only reads and displays the post. Lead the user-facing response with **Draft ready — NOT PUBLISHED; awaiting your confirmation** and explain that it is not in the public blog feed. Automatically include the direct video URL returned in `video.url` as a clickable **Watch video** link (and a playable preview if supported), then present the complete title, body, and all media, identify the blog, and ask whether to publish that exact version. The user must not have to request a link. An uploaded video's direct URL can work while the post is still a draft.

Do not substitute the draft permalink for the full review. Only include a draft editor/preview link when verified and label it as requiring WordPress login. If such a preview is unavailable, say the complete review is provided here in chat with the video link. Follow `SKILL.md`; never infer confirmation from the initial task. If the content changes, show and confirm the changed version again.

## 6. Publish the same draft

Only after the user's affirmative reply:

```text
python <skill-dir>/scripts/blog.py --config <active-config> publish --post-id <draft-id> --execute --confirmed
```

This sends only `status: publish`, preserving attached video and other fields, then reads the post back. It uses PATCH for author-app and POST for standard WordPress. An already published post is reported without another write. `--confirmed` records the caller's assertion; the program cannot inspect chat consent or lock out concurrent edits by someone using WordPress. The agent must check that the current draft still matches the confirmed version.

After success, automatically return **Published: [post title](the actual public permalink from read-back)** and **Watch video** linked to the actual media URL. Check the public page when possible and clearly distinguish unverified visibility from confirmed publication. Do not leave the user with a draft URL or wait for them to ask where to view the result.

No live upload or publication was performed while implementing this workflow.
