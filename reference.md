# htmlput HTTP reference

Base `https://www.htmlput.com`. Owner calls use `Authorization: Bearer $HP_API_KEY`.
Always send `User-Agent: htmlput-agent-cli/1.0` — Cloudflare blocks default
Python/Java user agents.

`accessType` is `public`, `password`, or `claim`. `password` requires `accessPassword`. `claim` is one-code-per-person access (visitors redeem `cl_…`); no password.

| Method | Path | Notes |
|---|---|---|
| GET | /api/v1/hosting/pages | list (`page`, `pageSize`) |
| GET | /api/v1/hosting/pages/{id} | read |
| POST | /api/v1/hosting/pages | `{title, htmlContent, accessType, accessPassword?}` |
| PUT | /api/v1/hosting/pages/{id} | same body as create |
| DELETE | /api/v1/hosting/pages/{id} | |
| POST | /api/v1/hosting/pages/bundle | multipart, `mode=zip`, file part named `file`; optional `accessPassword` |
| PUT | /api/v1/hosting/pages/{id}/bundle | multipart, same as above |
| PUT | /api/v1/pages/{fileKey}/kv/settings | `{"enabled":true}` → returns `writeToken`; review: `{"enabled":true,"schema":{"requireReview":true,"fields":[]}}`; authorize: add `"login":{"enabled":true}` inside `schema` |
| GET | /api/v1/pages/{fileKey}/kv | owner list; query `cursor`, `limit` (max 100). Response `nextCursor`, `privateRowCount` (private values omitted) |
| GET | /api/v1/pages/{fileKey}/kv/public | visitor read, approved **public** rows only, no auth |
| GET | /api/v1/pages/{fileKey}/kv/mine | page session `hp_pst_…`; caller's rows only |
| POST | /api/v1/pages/{fileKey}/kv | writeToken (anonymous; **blocked** when `login.enabled` → `KV_ANON_WRITE_DISABLED`) **or** `hp_pst_…` (owner rows; optional `visibility`) **or** owner `hp_live_…` |
| DELETE | /api/v1/pages/{fileKey}/kv/{key} | page session (own row) or owner |
| POST | /api/v1/pages/{fileKey}/kv/{key}/review | `{"status":"approved"\|"rejected"}` |
| POST | /api/v1/pages/{fileKey}/kv/rotate-token | new write token |
| GET | /api/v1/pages/{fileKey}/kv/users | owner; masked authorizees |
| POST | /api/v1/pages/{fileKey}/kv/users/{userId}/ban | owner; `{ reason? }` — revoke consent + sessions |
| POST | /api/v1/pages/{fileKey}/kv/users/{userId}/unban | owner; delete ban row only |
| POST | /api/v1/pages/{fileKey}/auth/exchange | `{ code }` → `{ token, expiresAt, user:{id,name} }` |
| POST | /api/v1/pages/{fileKey}/auth/silent | cookie `credentials:include`; else `AUTH_SILENT_DENIED` |
| GET | /api/v1/pages/{fileKey}/auth/me | page session → `{ id, name }` |
| POST | /api/v1/pages/{fileKey}/auth/logout | revoke current page session |
| GET | /api/v1/me/page-authorizations | main-site session; History「已授权」 |
| DELETE | /api/v1/me/page-authorizations/{fileKey} | revoke consent + sessions for that page |

Browser authorize UI (not JSON): `GET /auth/page?fileKey&return&state` (same-tab). Unauthenticated → `/login?next=…&autoGrant=1`; success → `#hp_code=` on `return`. Legacy `mode=popup` still served if requested.

Useful `code`s: `KV_DISABLED`, `KV_ANON_WRITE_DISABLED` (write-token while `login.enabled`; response includes `message`), `KV_LOGIN_REQUIRED`, `KV_LOGIN_DISABLED`, `KV_SESSION_EXPIRED`, `KV_NOT_OWNER`, `KV_USER_LIMIT`, `KV_USER_BANNED`, `AUTH_CODE_INVALID`, `AUTH_SILENT_DENIED`, `USE_KV_PUBLIC`.

Key quota is an account lifetime cap shared by every page (Free 100, Plus 1,000, Pro 10,000, Ultra 100,000). One value ≤ 10 KB.
