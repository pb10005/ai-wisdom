#!/usr/bin/env python3
"""知恵袋の整合性チェック。

使い方:
    python3 scripts/check.py            # 全体を検証（エラーがあれば終了コード 1）
    python3 scripts/check.py --pending  # 未抽出（extracted: false）のエッセイを一覧
    python3 scripts/check.py --next-id  # 次に振る知恵 ID を表示

外部ライブラリには依存しない。frontmatter は「key: value」と「[a, b]」形式のリストのみ扱う。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ESSAYS = ROOT / "essays"
SKILL_DIR = ROOT / "skills" / "ai-wisdom"
REFERENCES = SKILL_DIR / "references"

ESSAY_NAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
CARD_HEADING = re.compile(r"^### (W-\d{4}) (.+)$")
CARD_FIELD = re.compile(r"^- ([^:]+): ?(.*)$")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ESSAY_KEYS = ("title", "date", "tags", "extracted", "wisdom")
CARD_KEYS = ("status", "tags", "使う場面", "指針", "理由", "出典")


def parse_value(raw: str):
    raw = raw.split(" #", 1)[0].strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [v.strip() for v in raw[1:-1].split(",") if v.strip()]
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def parse_frontmatter(path: Path) -> dict | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None
    meta = {}
    for line in lines[1:]:
        if line == "---":
            return meta
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            meta[key.strip()] = parse_value(value)
    return None


def essay_files() -> list[Path]:
    return sorted(p for p in ESSAYS.rglob("*.md") if p.name != "_template.md")


def parse_cards() -> list[dict]:
    cards = []
    for path in sorted(REFERENCES.glob("*.md")):
        card = None
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            heading = CARD_HEADING.match(line)
            if heading:
                card = {"id": heading[1], "title": heading[2], "file": path,
                        "line": lineno, "fields": {}, "sources": []}
                cards.append(card)
                continue
            if line.startswith("#"):
                card = None
                continue
            if card is None:
                continue
            field = CARD_FIELD.match(line)
            if field:
                key = field[1].strip()
                card["fields"][key] = field[2].strip()
                current = key
            elif line.startswith("  ") and card["fields"]:
                current = list(card["fields"])[-1]
            else:
                continue
            if current == "出典":
                card["sources"] += LINK.findall(line)
    return cards


def check() -> list[str]:
    errors: list[str] = []
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731

    # エッセイ
    essays: dict[Path, dict] = {}
    for path in essay_files():
        name = ESSAY_NAME.match(path.name)
        if not name or path.parent.parent != ESSAYS or path.parent.name != name[1]:
            errors.append(f"{rel(path)}: パスは essays/YYYY/YYYY-MM-DD-<slug>.md にする")
        meta = parse_frontmatter(path)
        if meta is None:
            errors.append(f"{rel(path)}: frontmatter がない")
            continue
        essays[path.resolve()] = meta
        for key in ESSAY_KEYS:
            if key not in meta:
                errors.append(f"{rel(path)}: frontmatter に {key} がない")
        if name and meta.get("date") != f"{name[1]}-{name[2]}-{name[3]}":
            errors.append(f"{rel(path)}: date がファイル名の日付と一致しない")
        if not isinstance(meta.get("extracted"), bool):
            errors.append(f"{rel(path)}: extracted は true / false にする")
        if not isinstance(meta.get("wisdom", []), list):
            errors.append(f"{rel(path)}: wisdom はリストにする")
        if meta.get("wisdom") and meta.get("extracted") is False:
            errors.append(f"{rel(path)}: wisdom があるのに extracted: false")
        local = LINK.findall(path.read_text(encoding="utf-8"))
        if isinstance(meta.get("source"), str):
            local.append(meta["source"])
        for link in local:
            if "://" in link or link.startswith("#"):
                continue
            if not (path.parent / link.split("#", 1)[0]).exists():
                errors.append(f"{rel(path)}: リンク先のファイルがない: {link}")

    # 知恵カード
    cards = parse_cards()
    seen: dict[str, str] = {}
    cited: dict[Path, set[str]] = {}
    for card in cards:
        where = f"{rel(card['file'])}:{card['line']} {card['id']}"
        if card["id"] in seen:
            errors.append(f"{where}: ID が重複（{seen[card['id']]}）")
        seen[card["id"]] = where
        for key in CARD_KEYS:
            if key not in card["fields"]:
                errors.append(f"{where}: 「{key}」がない")
        if card["fields"].get("status") not in (None, "active", "retired"):
            errors.append(f"{where}: status は active / retired にする")
        if "出典" in card["fields"] and not card["sources"]:
            errors.append(f"{where}: 出典にエッセイへのリンクがない")
        for link in card["sources"]:
            target = (card["file"].parent / link.split("#", 1)[0]).resolve()
            if target not in essays:
                errors.append(f"{where}: 出典リンク先のエッセイがない: {link}")
                continue
            cited.setdefault(target, set()).add(card["id"])
            if card["id"] not in essays[target].get("wisdom", []):
                errors.append(f"{where}: 出典エッセイ {rel(target)} の wisdom にこの ID がない")

    # エッセイ → カードの逆参照
    for path, meta in essays.items():
        for wid in meta.get("wisdom", []) if isinstance(meta.get("wisdom"), list) else []:
            if wid not in seen:
                errors.append(f"{rel(path)}: wisdom の {wid} に対応するカードがない")
            elif wid not in cited.get(path, set()):
                errors.append(f"{rel(path)}: {wid} のカードの出典にこのエッセイがない")

    # 索引
    index = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for path in sorted(REFERENCES.glob("*.md")):
        if f"references/{path.name}" not in index:
            errors.append(f"skills/ai-wisdom/SKILL.md: 索引に references/{path.name} がない")
    for card in cards:
        if card["id"] not in index:
            errors.append(f"skills/ai-wisdom/SKILL.md: 索引に {card['id']} がない")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pending", action="store_true", help="未抽出のエッセイを一覧")
    parser.add_argument("--next-id", action="store_true", help="次に振る知恵 ID を表示")
    args = parser.parse_args()

    if args.pending:
        for path in essay_files():
            meta = parse_frontmatter(path) or {}
            if meta.get("extracted") is not True:
                print(f"{path.relative_to(ROOT).as_posix()}\t{meta.get('title', '')}")
        return 0
    if args.next_id:
        numbers = [int(c["id"][2:]) for c in parse_cards()]
        print(f"W-{max(numbers, default=0) + 1:04d}")
        return 0

    errors = check()
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} 件のエラー", file=sys.stderr)
        return 1
    print(f"OK: エッセイ {len(essay_files())} 本 / 知恵 {len(parse_cards())} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
