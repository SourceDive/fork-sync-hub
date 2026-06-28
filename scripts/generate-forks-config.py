#!/usr/bin/env python3
"""从 GitHub API 生成 forks.json，供 sync-all-forks workflow 使用。"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ORG = "SourceDive"
API = "https://api.github.com"
OUTPUT = Path(__file__).resolve().parent.parent / "forks.json"


def get_json(url: str) -> list | dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "sync-fork-config-generator",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def load_all_forks() -> list[dict]:
    forks: list[dict] = []
    for page in range(1, 20):
        data = get_json(f"{API}/orgs/{ORG}/repos?per_page=100&type=forks&page={page}")
        if not data:
            break
        forks.extend(data)
        if len(data) < 100:
            break
    return forks


def main() -> int:
    configs: list[dict] = []
    skipped: list[str] = []

    for repo in sorted(load_all_forks(), key=lambda item: item["name"].lower()):
        full_name = repo["full_name"]
        try:
            detail = get_json(f"{API}/repos/{full_name}")
            parent = detail.get("parent")
            if not parent:
                skipped.append(full_name)
                continue
            configs.append(
                {
                    "fork": full_name,
                    "upstream": parent["full_name"],
                    "target_branch": parent.get("default_branch", "main"),
                }
            )
            time.sleep(0.05)
        except urllib.error.HTTPError as error:
            skipped.append(f"{full_name} ({error.code})")

    OUTPUT.write_text(json.dumps(configs, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {len(configs)} 条配置到 {OUTPUT}")
    if skipped:
        print(f"跳过 {len(skipped)} 个仓库:", ", ".join(skipped), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
