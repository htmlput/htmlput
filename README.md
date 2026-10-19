# htmlput-skill

An agent skill for [htmlput.com](https://www.htmlput.com) — free static hosting for
single-file HTML pages and zip sites, plus per-page key-value data (Page KV) that
gives static pages a shared backend with no server code.

## Install

```bash
npx skills add htmlput/htmlput
```

Until that repo exists, copy this folder into the agent's skills directory
(for Claude Code: `~/.claude/skills/htmlput`).

## Setup

1. Sign up at https://www.htmlput.com (free).
2. Create an API key at https://www.htmlput.com/account (`hp_live_…`).
3. `export HP_API_KEY="hp_live_…"`

## Quickstart

```bash
# publish a page → returns a shareable link
python3 scripts/hp.py pages paste --title "My page" --file index.html

# update it later (same link)
python3 scripts/hp.py pages update <pageId> --title "My page" --file index.html

# give the page a data backend (polls, guestbooks, forms…)
python3 scripts/hp.py kv enable <fileKey> --require-review
# → save the writeToken it prints, embed it in your page's frontend (see SKILL.md)
```

See [SKILL.md](SKILL.md) for CLI commands, Page KV patterns, and quirks.
HTTP routes are in [reference.md](reference.md).

## Live examples

- Poll — https://share.htmlput.com/p/7vpnexbo0w
- Guestbook with moderation — https://share.htmlput.com/p/ob88j4zgog
- Quiz with leaderboard — https://share.htmlput.com/p/jjros21eoi

## License

MIT
