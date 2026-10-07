#!/usr/bin/env python3
"""Claude Docs の Markdown 書き出し（base64）をエッセイとして取り込む。

使い方:
    python3 scripts/import_docs.py <base64 ファイル> --bytes <申告バイト数> \\
        --slug <slug> --tags <タグ1,タグ2> --source <ドキュメントの URL>

- base64 をデコードし、export が申告したバイト数と UTF-8 として正しいかを検証する
- 先頭の `# タイトル` と `Oct 7, 2026 · @名前` の署名行から title / date / collaborators を決める
- 署名行を除き、frontmatter を付けて essays/YYYY/YYYY-MM-DD-<slug>.md に書き出す
- 図（`[embedded content: ...]`）は書き出しから落ちるので、残っている箇所を警告する
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BYLINE = re.compile(r"^([A-Z][a-z]{2} \d{1,2}, \d{4}) · @(\S+)\s*$")
EMBED = re.compile(r"^&#91;embedded content: (.+?)\\?\]$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("b64", type=Path)
    parser.add_argument("--bytes", type=int, required=True, help="export の data.bytes")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--tags", required=True, help="カンマ区切り")
    parser.add_argument("--source", required=True, help="ドキュメントの URL")
    parser.add_argument("--force", action="store_true", help="既存ファイルを上書きする")
    args = parser.parse_args()

    raw = base64.b64decode("".join(args.b64.read_text().split()), validate=True)
    if len(raw) != args.bytes:
        print(f"ERROR バイト数が一致しない: {len(raw)} != {args.bytes}（base64 の写し間違い）", file=sys.stderr)
        return 1
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"ERROR UTF-8 として不正: {e}（base64 の写し間違い）", file=sys.stderr)
        return 1

    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        print("ERROR 先頭行が `# タイトル` ではない", file=sys.stderr)
        return 1
    title = lines[0][2:].strip()

    date, author, body = None, None, []
    for line in lines[1:]:
        m = BYLINE.match(line)
        if m and date is None:
            date = datetime.strptime(m[1], "%b %d, %Y").strftime("%Y-%m-%d")
            author = m[2]
            continue
        body.append(line)
    if date is None:
        print("ERROR 署名行（例: Oct 7, 2026 · @名前）が見つからない", file=sys.stderr)
        return 1

    body_text = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip("\n")
    tags = ", ".join(t.strip() for t in args.tags.split(",") if t.strip())
    title_yaml = title.replace('"', '\\"')
    out = ROOT / "essays" / date[:4] / f"{date}-{args.slug}.md"
    if out.exists() and not args.force:
        print(f"ERROR 既に存在する: {out.relative_to(ROOT)}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "---\n"
        f'title: "{title_yaml}"\n'
        f"date: {date}\n"
        f"tags: [{tags}]\n"
        f"collaborators: [{author}, claude]\n"
        f"source: {args.source}\n"
        "extracted: false\n"
        "wisdom: []\n"
        "---\n\n"
        f"# {title}\n\n{body_text}\n",
        encoding="utf-8",
    )
    print(f"OK {out.relative_to(ROOT)}（{len(raw)} bytes）")
    for n, line in enumerate(out.read_text(encoding="utf-8").splitlines(), 1):
        m = EMBED.match(line)
        if m:
            print(f"WARN {out.relative_to(ROOT)}:{n} 図が落ちている: {m[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
