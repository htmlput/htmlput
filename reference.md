# htmlput HTTP reference

Base `https://www.htmlput.com`. Owner calls use `Authorization: Bearer $HP_API_KEY`.
Always send `User-Agent: htmlput-agent-cli/1.0` — Cloudflare blocks default
Python/Java user agents.

`accessType` is `public` or `password`. `password` requires `accessPassword`.

| Method | Path | Notes |
|---|---|---|
| GET | /api/v1/hosting/pages | list (`page`, `pageSize`) |
| GET | /api/v1/hosting/pages/{id} | read |
| POST | /api/v1/hosting/pages | `{title, htmlContent, accessType, accessPassword?}` |
| PUT | /api/v1/hosting/pages/{id} | same body as create |
| DELETE | /api/v1/hosting/pages/{id} | |
| POST | /api/v1/hosting/pages/bundle | multipart, `mode=zip`, file part named `file`; optional `accessPassword` |
| PUT | /api/v1/hosting/pages/{id}/bundle | multipart, same as above |
| PUT | /api/v1/pages/{fileKey}/kv/settings | `{"enabled":true}` → returns `writeToken`; review: `{"enabled":true,"schema":{"requireReview":true,"fields":[]}}` |
| GET | /api/v1/pages/{fileKey}/kv | owner list; query `cursor`, `limit` (max 100). Response `nextCursor` |
| GET | /api/v1/pages/{fileKey}/kv/public | visitor read, approved rows only, no auth |
| POST | /api/v1/pages/{fileKey}/kv | visitor write, `Authorization: Bearer <writeToken>`, `{key, value}` |
| POST | /api/v1/pages/{fileKey}/kv/{key}/review | `{"status":"approved"\|"rejected"}` |
| POST | /api/v1/pages/{fileKey}/kv/rotate-token | new write token |

Key quota is an account lifetime cap shared by every page (Free 100, Plus 1,000, Pro 10,000, Ultra 100,000). One value ≤ 10 KB.
