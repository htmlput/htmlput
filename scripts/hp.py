#!/usr/bin/env python3
"""htmlput CLI — publish pages to htmlput.com and manage Page KV data.

Auth: export HP_API_KEY="hp_live_…" (create one at https://www.htmlput.com/account).

Usage:
    hp.py pages list [--page N] [--page-size N]
    hp.py pages read PAGE_ID
    hp.py pages paste --title TITLE --file index.html [--access public|password|claim --password SECRET]
    hp.py pages update PAGE_ID --title TITLE --file index.html [--access public|password|claim --password SECRET]  # Plus+
    hp.py pages delete PAGE_ID                                                            # Plus+
    hp.py bundle upload --title TITLE --zip site.zip [--access public|password|claim --password SECRET]  # Pro+
    hp.py bundle reupload PAGE_ID --zip site.zip --title TITLE                            # Pro+
    hp.py kv enable FILEKEY [--require-review]
    hp.py kv write FILEKEY --token WRITE_TOKEN --key KEY --value '{"a":1}'
    hp.py kv list FILEKEY [--cursor CURSOR] [--limit N]
    hp.py kv public FILEKEY
    hp.py kv review FILEKEY --key KEY --status approved|rejected
    hp.py kv rotate-token FILEKEY
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import quote

BASE = "https://www.htmlput.com"
UA = "htmlput-agent-cli/1.0"


def api_key() -> str:
    key = os.environ.get("HP_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "HP_API_KEY is not set.\n"
            "  1. Sign up at https://www.htmlput.com\n"
            "  2. Create an API key at https://www.htmlput.com/account\n"
            "  3. export HP_API_KEY=\"hp_live_…\""
        )
    return key


def request(method, path, payload=None, files=None, token=None):
    if files:
        boundary, body = encode_multipart(files)
        data = body
        ctype = f"multipart/form-data; boundary={boundary}"
    else:
        data = json.dumps(payload).encode() if payload is not None else None
        ctype = "application/json" if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("User-Agent", UA)
    if ctype:
        req.add_header("Content-Type", ctype)
    req.add_header("Authorization", "Bearer " + (token or api_key()))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise SystemExit(f"HTTP {e.code}: {body[:800]}")


def encode_multipart(files):
    import uuid
    boundary = uuid.uuid4().hex
    body = b""
    for name, value, filename, mimetype in files:
        body += f"--{boundary}\r\n".encode()
        if filename:
            body += (
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {mimetype}\r\n\r\n"
            ).encode()
            body += value + b"\r\n"
        else:
            body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            body += str(value).encode() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return boundary, body


# ---- pages ----

def cmd_pages_list(a):
    print(json.dumps(request("GET", f"/api/v1/hosting/pages?page={a.page}&pageSize={a.page_size}"),
                     indent=2, ensure_ascii=False))


def cmd_pages_read(a):
    print(json.dumps(request("GET", f"/api/v1/hosting/pages/{a.page_id}"),
                     indent=2, ensure_ascii=False))


def page_body(a, html):
    body = {"title": a.title, "htmlContent": html, "accessType": a.access}
    if a.access == "password":
        if not a.password:
            raise SystemExit("--password is required when --access password")
        body["accessPassword"] = a.password
    return body


def cmd_pages_paste(a):
    with open(a.file, encoding="utf-8") as f:
        html = f.read()
    out = request("POST", "/api/v1/hosting/pages", page_body(a, html))
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_pages_delete(a):
    print(json.dumps(request("DELETE", f"/api/v1/hosting/pages/{a.page_id}"),
                     indent=2, ensure_ascii=False))


def cmd_pages_update(a):
    with open(a.file, encoding="utf-8") as f:
        html = f.read()
    out = request("PUT", f"/api/v1/hosting/pages/{a.page_id}", page_body(a, html))
    print(json.dumps(out, indent=2, ensure_ascii=False))


# ---- bundles ----

def cmd_bundle_upload(a):
    with open(a.zip, "rb") as f:
        data = f.read()
    files = [("mode", "zip", None, None), ("title", a.title, None, None),
             ("accessType", a.access, None, None)]
    if a.access == "password":
        if not a.password:
            raise SystemExit("--password is required when --access password")
        files.append(("accessPassword", a.password, None, None))
    files.append(("file", data, "site.zip", "application/zip"))
    print(json.dumps(request("POST", "/api/v1/hosting/pages/bundle", files=files),
                     indent=2, ensure_ascii=False))


def cmd_bundle_reupload(a):
    with open(a.zip, "rb") as f:
        data = f.read()
    files = [("mode", "zip", None, None), ("title", a.title, None, None),
             ("file", data, "site.zip", "application/zip")]
    print(json.dumps(request("PUT", f"/api/v1/hosting/pages/{a.page_id}/bundle", files=files),
                     indent=2, ensure_ascii=False))


# ---- kv ----

def cmd_kv_enable(a):
    body = {"enabled": True}
    if a.require_review:
        body["schema"] = {"requireReview": True, "fields": []}
    out = request("PUT", f"/api/v1/pages/{a.filekey}/kv/settings", body)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if out.get("writeToken"):
        print("\n>>> SAVE THIS WRITE TOKEN — it is shown only here and on rotate-token.",
              file=sys.stderr)


def cmd_kv_write(a):
    try:
        value = json.loads(a.value)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--value must be valid JSON: {e}")
    out = request("POST", f"/api/v1/pages/{a.filekey}/kv",
                  {"key": a.key, "value": value}, token=a.token)
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_kv_list(a):
    qs = f"limit={a.limit}"
    if a.cursor:
        qs += "&cursor=" + quote(a.cursor, safe="")
    print(json.dumps(
        request("GET", f"/api/v1/pages/{a.filekey}/kv?{qs}"),
        indent=2, ensure_ascii=False))


def cmd_kv_public(a):
    print(json.dumps(request("GET", f"/api/v1/pages/{a.filekey}/kv/public"),
                     indent=2, ensure_ascii=False))


def cmd_kv_review(a):
    print(json.dumps(
        request("POST", f"/api/v1/pages/{a.filekey}/kv/{a.key}/review",
                {"status": a.status}), indent=2, ensure_ascii=False))


def cmd_kv_rotate(a):
    out = request("POST", f"/api/v1/pages/{a.filekey}/kv/rotate-token")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\n>>> Old write token is dead. Update the page's frontend code with the new one.",
          file=sys.stderr)


def main():
    p = argparse.ArgumentParser(prog="hp.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("pages")
    psub = pp.add_subparsers(dest="op", required=True)
    l = psub.add_parser("list")
    l.add_argument("--page", type=int, default=1)
    l.add_argument("--page-size", type=int, default=20)
    l.set_defaults(fn=cmd_pages_list)
    r = psub.add_parser("read")
    r.add_argument("page_id")
    r.set_defaults(fn=cmd_pages_read)
    c = psub.add_parser("paste")
    c.add_argument("--title", required=True)
    c.add_argument("--file", required=True)
    c.add_argument(
        "--access",
        default="public",
        choices=["public", "password", "claim"],
        help="public | password | claim (one code per person; no --password)",
    )
    c.add_argument("--password", default=None, help="Required when --access password")
    c.set_defaults(fn=cmd_pages_paste)
    d = psub.add_parser("delete")
    d.add_argument("page_id")
    d.set_defaults(fn=cmd_pages_delete)
    u = psub.add_parser("update")
    u.add_argument("page_id")
    u.add_argument("--title", required=True)
    u.add_argument("--file", required=True)
    u.add_argument(
        "--access",
        default="public",
        choices=["public", "password", "claim"],
        help="public | password | claim (one code per person; no --password)",
    )
    u.add_argument("--password", default=None, help="Required when --access password")
    u.set_defaults(fn=cmd_pages_update)

    bp = sub.add_parser("bundle")
    bsub = bp.add_subparsers(dest="op", required=True)
    bu = bsub.add_parser("upload")
    bu.add_argument("--title", required=True)
    bu.add_argument("--zip", required=True)
    bu.add_argument(
        "--access",
        default="public",
        choices=["public", "password", "claim"],
        help="public | password | claim (one code per person; no --password)",
    )
    bu.add_argument("--password", default=None, help="Required when --access password")
    bu.set_defaults(fn=cmd_bundle_upload)
    br = bsub.add_parser("reupload")
    br.add_argument("page_id")
    br.add_argument("--zip", required=True)
    br.add_argument("--title", required=True)
    br.set_defaults(fn=cmd_bundle_reupload)

    kp = sub.add_parser("kv")
    ksub = kp.add_subparsers(dest="op", required=True)
    ke = ksub.add_parser("enable")
    ke.add_argument("filekey")
    ke.add_argument("--require-review", action="store_true")
    ke.set_defaults(fn=cmd_kv_enable)
    kw = ksub.add_parser("write")
    kw.add_argument("filekey")
    kw.add_argument("--token", required=True)
    kw.add_argument("--key", required=True)
    kw.add_argument("--value", required=True, help="JSON value, e.g. '{\"option\":\"a\"}'")
    kw.set_defaults(fn=cmd_kv_write)
    kl = ksub.add_parser("list")
    kl.add_argument("filekey")
    kl.add_argument("--cursor", default=None, help="nextCursor from the previous page")
    kl.add_argument("--limit", type=int, default=100)
    kl.set_defaults(fn=cmd_kv_list)
    kpu = ksub.add_parser("public")
    kpu.add_argument("filekey")
    kpu.set_defaults(fn=cmd_kv_public)
    kr = ksub.add_parser("review")
    kr.add_argument("filekey")
    kr.add_argument("--key", required=True)
    kr.add_argument("--status", required=True, choices=["approved", "rejected"])
    kr.set_defaults(fn=cmd_kv_review)
    krt = ksub.add_parser("rotate-token")
    krt.add_argument("filekey")
    krt.set_defaults(fn=cmd_kv_rotate)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
