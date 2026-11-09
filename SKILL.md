---
name: htmlput
description: Publish single-file HTML pages and zip sites to htmlput.com and manage them, or add server-side per-page data (Page KV) for polls, guestbooks and forms, including optional Page Accounts authorize for private per-user rows. Use when the user wants to host a web page, share an HTML file through a public link, update or delete a hosted page, or give a static page a shared data backend without writing one.
---

# htmlput

htmlput (https://www.htmlput.com) is free static hosting for single-file HTML pages and zip sites.
Every page gets a public share link like `https://share.htmlput.com/p/<id>`.

Full API reference: https://www.htmlput.com/help/hosting/agent-api

## Setup

1. Sign up at https://www.htmlput.com (free, no credit card).
2. Open https://www.htmlput.com/account and create an API key (`hp_live_…`).
3. Export it in your shell:
   `export HP_API_KEY="hp_live_…"`

The CLI (`scripts/hp.py`) reads `HP_API_KEY`. Never ask the user to paste the key
in chat; if it is missing, send them to step 2.

## CLI

`python3 scripts/hp.py <command>` — every command prints JSON.

### Pages

```
hp.py pages list [--page N] [--page-size N]
hp.py pages read PAGE_ID
hp.py pages paste --title TITLE --file index.html [--access public|password|claim --password SECRET]
hp.py pages update PAGE_ID --title TITLE --file index.html [--access public|password|claim --password SECRET]  # Plus+
hp.py pages delete PAGE_ID                                                            # Plus+
hp.py pages claim-credits                                                             # how many cl_… codes left
hp.py pages claim-codes PAGE_ID [--count N] [--batch LABEL] [--channel LABEL]         # mint codes (page must be claim)
```

`--access` is `public` (default), `password`, or `claim`. `password` requires `--password`. `claim` is one-code-per-person access (visitors redeem `cl_…` on `/p/…`); no password.

After `paste`/`update` with `--access claim`, mint codes with `claim-codes` (or check `claim-credits` first). Save the returned `cl_…` strings — they are shown only once. Visitors redeem on the share URL.

`paste` returns JSON containing `data.shareUrl` and `data.pageId`.
Always open `shareUrl` and confirm it renders before telling the user it is live.

### Zip sites (bundles)

```
hp.py bundle upload --title TITLE --zip site.zip [--access public|password|claim --password SECRET]  # Pro+
hp.py bundle reupload PAGE_ID --zip site.zip --title TITLE                  # Pro+, in-place
```

Re-upload keeps the same share link. Web-built bundle pages that reject
`bundle reupload` with `HOST_BUNDLE_NOT_EDITABLE` can be updated with
`pages update` instead when the page is a single HTML file.

### Page KV (per-page key-value data)

Give a static page a shared data backend: polls, guestbooks, signup forms,
quizzes. No server code needed.

```
hp.py kv enable FILEKEY [--require-review]
# → prints {"writeToken": "hp_pwt_…"} — SAVE IT. Shown only here (and on rotate).

hp.py kv write FILEKEY --token WRITE_TOKEN --key vote_abc123 --value '{"option":"a"}'
hp.py kv list FILEKEY [--cursor CURSOR] [--limit N]   # owner view; follow nextCursor
hp.py kv public FILEKEY               # what visitors can read (no auth)
hp.py kv review FILEKEY --key KEY --status approved|rejected
hp.py kv rotate-token FILEKEY         # new write token, old one dies immediately
```

`FILEKEY` is the `<id>` in the page's share URL (`share.htmlput.com/p/<id>`).

**In the browser**, pages call the same API directly (CORS is open for share-link origins):

```js
// visitor write (write-token is public by design — it is "pocket money", not a password)
await fetch(`https://www.htmlput.com/api/v1/pages/${FILEKEY}/kv`, {
  method: "POST",
  headers: {"Content-Type": "application/json", "Authorization": `Bearer ${WRITE_TOKEN}`},
  body: JSON.stringify({ key: "vote_" + crypto.randomUUID().slice(0,8), value: { option: "a" } })
});
// public read (no auth) — only approved rows
const { items } = await (await fetch(`https://www.htmlput.com/api/v1/pages/${FILEKEY}/kv/public`)).json();
```

Conventions that keep demos working:

- One row per submission: `key` = prefix + random id (e.g. `vote_`, `msg_`, `sub_`).
- With `--require-review`, new rows are `pending` and invisible to `kv public`
  until approved via `kv review`. Use it for guestbooks / comment walls.
- Key quota (public + private rows) is lifetime for the whole account, shared
  across pages (Free 100, Plus 10,000, Pro 100,000, Ultra 1,000,000). One value
  is plan-tiered (Free 10KB · Plus 32KB · Pro 64KB · Ultra 128KB UTF-8 of
  `JSON.stringify(value)`). Deleting a key does not free quota. **Every new
  key** (public or private) counts as one Data replies unit.

### Two visibility layers (do not conflate)

Page data has **two** independent controls:

1. **Row** `visibility`: `"public"` (default) \| `"private"`.
   - `public` → eligible for `GET …/kv/public` (if Shown / approved).
   - `private` → **never** on `/kv/public`; owner Data shows **Private** /
     **非公开**. Anonymous private rows keep `owner_user_id = null`.
2. **Field** `guestVisible` (schema `fields[]`): on a **public** row, which
   keys appear in the public projection. `guestVisible: false` → owner still
   sees the field in Data (column marked Private / 非公开); visitors’ 
   `/kv/public` omits it. DIY pages with **no** field schema expose the full
   value object on public read.

**Prefer field-level for mixed forms** (personality quiz, check-in): one
`visibility: "public"` row; nick / result / matchScore → `guestVisible: true`;
phone / answers → `false`. Matching that needs secret answers should be
computed by the creator (or their backend) and only public fields written back.

```js
// settings (owner): schema with guestVisible mix
await fetch(`https://www.htmlput.com/api/v1/pages/${FILEKEY}/kv/settings`, {
  method: "PUT",
  headers: {"Content-Type": "application/json", "Authorization": `Bearer ${API_KEY}`},
  body: JSON.stringify({
    enabled: true,
    schema: {
      requireReview: false,
      fields: [
        { id: "nick", type: "text", label: "Nick", guestVisible: true },
        { id: "phone", type: "text", label: "Phone", guestVisible: false },
        { id: "result", type: "text", label: "Result", guestVisible: true },
      ],
    },
  }),
});
// guest write: public row, mixed fields in value
await fetch(`https://www.htmlput.com/api/v1/pages/${FILEKEY}/kv`, {
  method: "POST",
  headers: {"Content-Type": "application/json", "Authorization": `Bearer ${WRITE_TOKEN}`},
  body: JSON.stringify({
    key: "card_" + crypto.randomUUID().slice(0, 8),
    visibility: "public",
    value: { nick: "Ada", phone: "…", result: "INTJ" },
  }),
});
```

### Whole-row private (`visibility: "private"`)

Use when the **entire** submission must stay off the public list (one-way
quotes, medical leads, internal feedback with no public wall). Same `POST …/kv`;
pass `visibility: "private"`. Owner reads full value in History → Data.

```
hp.py kv write FILEKEY --token WRITE_TOKEN --key lead_abc --value '{"phone":"…"}' --visibility private
```

Browser (write-token; **Require authorize must be off** — otherwise
`KV_ANON_WRITE_DISABLED`; use page session instead):

```js
await fetch(`https://www.htmlput.com/api/v1/pages/${FILEKEY}/kv`, {
  method: "POST",
  headers: {"Content-Type": "application/json", "Authorization": `Bearer ${WRITE_TOKEN}`},
  body: JSON.stringify({
    key: "lead_" + crypto.randomUUID().slice(0,8),
    value: { phone: "…" },
    visibility: "private",
  })
});
```

**Which approach to use**

| Need | Write | Read |
|------|-------|------|
| Mixed card (nick public, phone/answers hidden) | `POST …/kv` **public** row + schema `guestVisible` | `/kv/public` (projected); owner Data (full) |
| Poll / guestbook / leaderboard | `POST …/kv` public (omit visibility) | `GET …/kv/public` |
| Entire lead off the wall | `POST …/kv` + `visibility: "private"` | Owner Data / `GET …/kv` only |
| Per-user progress / wrong-answer book | `visibility: "private"` + page session when authorize on | `GET …/kv/mine`; owner `GET …/kv` |

Multi-submit vs overwrite is the Creator’s **key** strategy; the platform does
not add business rules. Require authorize stays Creator choice (UI or
`PUT …/kv/settings` + `schema.login`).

### Page Accounts (authorize + private rows)

Optional. Turn on in the owner's Data dialog (**Require authorize**) or via settings
schema `login: { enabled: true, defaultVisibility: "private", maxEntriesPerUser: 500 }`.

Visitor flow on the hosted page (same `fileKey` only — no cross-page private reads):

1. On load: `POST …/auth/silent` with `credentials: "include"`. If the user already
   authorized this page, you get `{ token: "hp_pst_…", user: { id, name } }`.
2. Otherwise show an Authorize button → same-tab navigate to
   `https://www.htmlput.com/auth/page?fileKey=…&return=…&state=…`.
   Unauthenticated users hit login first; return uses `autoGrant=1` so they are not
   asked to click Authorize again. Success redirects to `return` with `#hp_code=`
   (clear with `history.replaceState` after reading).
3. `POST …/auth/exchange` with `{ code }` → page session token.
4. Writes while authorize is on: `POST …/kv` with `Authorization: Bearer hp_pst_…`
   (optional `visibility: "public"` for walls/leaderboards, or `"private"` for
   personal rows). `GET …/kv/mine` lists the caller's rows. Use `user.name` in
   forms if you want; API does not force it.

When `login.enabled` is true, anonymous `writeToken` (`hp_pwt_…`) POSTs are
rejected (`KV_ANON_WRITE_DISABLED` + `message`). Turn authorize off to allow
write-token again. Never put the Agent API key (`hp_live_…`) in page HTML.

Browser helpers and OpenAPI: History → Data → Wire snippet; OpenAPI at
`/openapi.json` (tag **Page accounts**). Paths/errors also in [reference.md](reference.md).
Example stub: [examples/authorize-mine-snippet.html](examples/authorize-mine-snippet.html).

Raw HTTP routes, bodies, and the required `User-Agent` are in [reference.md](reference.md).

## Quirks

- `writeToken` is returned only on the first `kv enable` and on `rotate-token`.
  Save it immediately — it is embedded in the page's own frontend code.
- Zip upload: the multipart file part MUST be named `file` (singular);
  `files`+`relpaths` is folder-mode only and returns 400 with a zip.
- `requireReview` must sit inside `schema` together with `fields`
  (`{"schema":{"requireReview":true,"fields":[]}}`); other shapes return 400.
- `login` lives inside the same `schema` object (default off). Enabling authorize
  **disables** anonymous write-token POSTs (`KV_ANON_WRITE_DISABLED`); use page
  session writes instead (see Data → Wire snippet).
- Private **rows** are invisible to `kv public` and to other visitors' `kv/mine`.
  **Page owners** see private `value` on owner `GET …/kv` / `GET …/kv/{key}`
  (tutoring). `privateRowCount` is still returned as a count helper.
  Anonymous private rows (write-token) have `owner_user_id = null`.
- Field `guestVisible: false` only hides keys on `/kv/public` for **public**
  rows; it is not the same as row `visibility: "private"`.
- Plan limits: paste/list/read on Free; edit/delete need Plus; zip bundles need
  Pro. A 403 `API_PLAN_REQUIRED` means the account's plan is too low.
- There is no API signup: new users register at https://www.htmlput.com first.

## Live examples

- Poll: https://share.htmlput.com/p/7vpnexbo0w
- Guestbook with review: https://share.htmlput.com/p/ob88j4zgog
- Quiz with leaderboard: https://share.htmlput.com/p/jjros21eoi
- Page KV intro: https://share.htmlput.com/p/2iasivgyee
