# Blog API contracts

Both modes read the login only from `skills.entries.blog.config.username` and the Application Password from encrypted `BLOG_APP_PASSWORD`. The old `BLOG_USERNAME` environment secret is ignored. The default API is `<blogUrl>/wp-json/wp/v2`; `apiBaseUrl` explicitly selects another HTTPS base ending in `/wp/v2` or `/author-app/v1`. There is no automatic protocol or host fallback.

## Standard WordPress

Authentication is HTTP Basic with the WordPress login and Application Password.

| Operation | Route relative to base | Fields |
| --- | --- | --- |
| Check access | `GET /users/me?context=edit` | Limited to id, name, slug, roles, capabilities |
| Upload | `POST /media` | Multipart file, title, alt_text; returns id and source_url |
| Create | `POST /posts` | title, HTML content, status draft/publish, optional featured_media integer |
| Read | `GET /posts/{id}?context=edit` | title.raw, content.raw, status, featured_media, id, link |

Additional images belong in HTML content. `image_media_ids` is not a core WordPress field. The helper rejects unsupported fields rather than dropping them.

Official references: [authentication](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/), [Application Passwords](https://developer.wordpress.org/advanced-administration/security/application-passwords/), [posts](https://developer.wordpress.org/rest-api/reference/posts/), [media](https://developer.wordpress.org/rest-api/reference/media/).

## Writer Studio author-app

Observed on 2026-10-19 from the public [API index](https://ag.yourwpcare.com/wp-json/) and the JavaScript served by [Writer Studio](https://lk.yourwpcare.com/) (`/assets/index-CgIaJHhN.js`). The client explicitly describes accepting an Application Password or account password for session exchange. This helper continues to use the configured Application Password only.

- `POST /auth/session`: JSON `{username, password}`. Client reads `access_token`, `refresh_token`, `expires_at` from the response.
- Subsequent requests use `Authorization: Bearer <access_token>`.
- `POST /auth/refresh`: client sends `{refresh_token}` and reads the same token fields. This helper does not persist or refresh tokens: it opens a fresh session per command and discards tokens on exit. Server-side sessions may remain until expiry; the helper does not call logout or revoke sessions.
- `GET /config`: used by the client to check the configured connection. The helper uses it after session exchange for `check-auth`; it does not interpret the result as WordPress roles/capabilities.
- `POST /media`: multipart file with actual image bytes and title, established by the supplied request example. Alt text is not verified here.
- `POST /posts`: title, content, status draft/publish, optional image_media_ids. The supplied video example confirms an empty-content draft returning a post ID.
- `GET /posts/{id}`: read-back without the standard WordPress context parameter.

The route index alone does not describe authentication bodies; those were observed in the served client. These public observations do not prove that a particular saved credential will succeed. The earlier local authentication and simple text publication were verified; no live video upload was performed for this implementation. Never print token responses or send secrets to the Writer Studio HTML frontend instead of the configured API.

## Display template

The supplied Gavrilenko `content.php` renders the title separately, then body, then custom image IDs plus the featured image. In standard mode, avoid duplicating the cover inside the body and embed additional images there. In author-app mode, pass ordered attachment IDs and let the theme render them. The template's custom video metadata does not establish a writable API contract.

## Diagnostics and migration

`BLOG_TOKEN` and `BLOG_USERNAME` secrets are unused. Set the ordinary `config.username` field explicitly when updating. The existing `BLOG_APP_PASSWORD` secret works with either selected mode; never copy its value into settings. Select author-app explicitly with `apiBaseUrl`, and adapt the image payload accordingly.

Error output retains HTTP status plus bounded, redacted code/message fields. Error bodies are limited to 64 KiB; successful content responses to 2 MiB. Login responses are separately bounded and never returned directly. Session failure sends no content request. Write failures after successful authentication may require reconciliation; no automatic retry is performed.

## Video jobs

The supplied captures establish `POST /video-jobs` with `filename`, `mime_type`, `post_id`, `cors_origin`, and an `Idempotency-Key` header. Its response contains `id`, status, and `upload: {url, method: "PUT"}`. The signed URL receives the actual MP4 bytes without WordPress credentials. `GET /video-jobs/{uuid}` reports processing.

The public Writer Studio client confirms terminal `completed`/`failed` and intermediate `pending_client_upload`, `processing`, `ready_for_archive`, `archiving_to_wp`. It reads the post again on completion; the backend attaches the video using `post_id`. The supplied completed post includes `videos_media` with a UUID-based MP4 URL. The uploader verifies that association before reporting success. It does not invent writable video-ID fields.

The final `PATCH /posts/{id}` with `status: "publish"` publishes the same draft. The helper sends only that field, leaving title, body, and attachments intact. See [video.md](video.md) for the complete workflow, bounded polling, and interrupted-upload handling. MOV conversion is an agent instruction, never Python behavior.