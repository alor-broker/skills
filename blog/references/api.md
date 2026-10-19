# WordPress REST API

The helper uses core WordPress REST routes with Application Passwords, not the custom author-app plugin. Base URL defaults to `<blogUrl>/wp-json/wp/v2`. An explicit `apiBaseUrl` may select another user-configured WordPress installation path or host but must end in `/wp/v2`.

Authentication: HTTP Basic with the WordPress login and generated Application Password from encrypted skill secrets. Password grouping spaces are removed. No bearer tokens, cookies, login requests, refresh endpoints, redirects, or automatic write retries are used.

| Operation | Method and path relative to API base | Request / useful response fields |
| --- | --- | --- |
| Verify authentication | `GET /users/me` | Read-only; successful user identity does not guarantee publishing permission |
| Upload image | `POST /media` | Multipart `file` with actual bytes, `title`, `alt_text`; returns `id`, `source_url` |
| Create post | `POST /posts` | `title`, HTML `content`, explicit `status: "draft"` or `"publish"`, optional integer `featured_media`; returns `id`, `link`, `status` |
| Read post | `GET /posts/{id}?context=edit` | Returns raw editable content when the user has permission: `title.raw`, `content.raw`, `featured_media`, `status` |

The helper intentionally accepts only the listed post fields and statuses. It rejects `image_media_ids` instead of silently losing images. A cover uses `featured_media`; multiple inline images are HTML in `content`, built from actual upload responses. Escape attribute values. `featured_media: 0` means no cover.

## Migration from the earlier skill

- Replace `BLOG_TOKEN` with the declared encrypted secrets `BLOG_USERNAME` and `BLOG_APP_PASSWORD`. Do not reuse the old token as a password.
- Remove the old `/author-app/v1` API override or explicitly configure the correct `/wp-json/wp/v2` URL. The helper never automatically rewrites a configured destination.
- Replace custom `image_media_ids` payloads with a cover ID and/or inline image HTML. Do not assume the custom plugin's metadata is writable through the standard API.
- `create` remains a local preview until `--execute` is supplied, even for a draft.

## The supplied theme

The original `content.php` from Gavrilenko's site is a display template, not an API implementation. It renders the title separately from the body, then appends `gav_author_image_ids` and the featured-image ID. Thus a cover embedded in the body may appear twice. New standard-API posts do not populate those custom image lists; embed additional images in the body instead. The same file's custom video and poster metadata does not establish a writable API contract and is not implemented.

These observations are specific to that theme; other WordPress themes may render covers differently. No live authenticated API validation was performed while changing this skill.

## Official references

- [Authentication](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/)
- [Application Passwords](https://developer.wordpress.org/advanced-administration/security/application-passwords/)
- [Posts](https://developer.wordpress.org/rest-api/reference/posts/)
- [Media](https://developer.wordpress.org/rest-api/reference/media/)
