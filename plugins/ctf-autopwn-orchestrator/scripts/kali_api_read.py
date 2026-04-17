#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def call(base_url: str, path: str) -> dict:
    req = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/api/kali/read",
        method="POST",
        data=json.dumps({"path": path}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    parser = argparse.ArgumentParser(description="Read file from active Kali container workspace via API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("path")
    args = parser.parse_args()

    try:
        result = call(args.base_url, args.path)
    except urllib.error.HTTPError as exc:
        print(exc.read().decode(errors="replace"))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
