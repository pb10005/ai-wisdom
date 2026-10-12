#!/usr/bin/env python3
"""lessons/*.md から、人が読むための教訓かるた（lessons/index.html）と一覧表（lessons/README.md）を生成する。

使い方:
    python3 scripts/build_lessons.py          # lessons/index.html を書き出す
    python3 scripts/build_lessons.py --check  # index.html が最新かを確かめる（古ければ終了コード 1）
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "lessons"
OUT = LESSONS / "index.html"
README = LESSONS / "README.md"
REPO_URL = "https://github.com/pb10005/ai-wisdom/blob/main/"
THEMES = [  # (ファイル名, 表示名) 並び順
    ("problem-solving.md", "問題解決"),
    ("strategy.md", "戦略"),
    ("collaboration.md", "協働"),
    ("judgment.md", "判断と評価"),
]
HEADING = re.compile(r"^### (W-\d{4}) (.+)$")
FIELD = re.compile(r"^- ([^:]+): ?(.*)$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def parse_file(path: Path, theme: str) -> list[dict]:
    lessons, cur, key = [], None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = HEADING.match(line)
        if m:
            cur = {"id": m[1], "maxim": m[2], "theme": theme, "fable_title": "",
                   "fable": [], "lesson": "", "questions": [], "source": None}
            lessons.append(cur)
            key = None
            continue
        if cur is None:
            continue
        if line.startswith("> "):
            cur["fable"].append(line[2:].strip())
            continue
        if line.startswith("  - ") and key == "問い":
            cur["questions"].append(line[4:].strip())
            continue
        f = FIELD.match(line)
        if not f:
            continue
        key, value = f[1].strip(), f[2].strip()
        if key == "寓話":
            cur["fable_title"] = value
        elif key == "教訓":
            cur["lesson"] = value
        elif key == "出典":
            link = LINK.search(value)
            if link:
                target = (path.parent / link[2]).resolve().relative_to(ROOT).as_posix()
                cur["source"] = {"title": link[1], "url": REPO_URL + target}
    return lessons


def load() -> list[dict]:
    items = []
    for name, theme in THEMES:
        items += parse_file(LESSONS / name, theme)
    return items


def render(items: list[dict]) -> str:
    data = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    themes = json.dumps([t for _, t in THEMES], ensure_ascii=False)
    return TEMPLATE.replace("__DATA__", data).replace("__THEMES__", themes).replace(
        "__COUNT__", str(len(items))).replace("__NOSCRIPT__", "".join(
            f"<li>{html.escape(i['id'])} {html.escape(i['maxim'])}</li>" for i in items))


def render_readme(items: list[dict]) -> str:
    """lessons/README.md の一覧表（| テーマ | 番号 | 格言 |）を作り直した全文を返す。"""
    text = README.read_text(encoding="utf-8")
    files = {theme: name for name, theme in THEMES}
    rows = "\n".join(f"| [{i['theme']}]({files[i['theme']]}) | {i['id']} | {i['maxim']} |" for i in items)
    return re.sub(r"(\| テーマ \| 番号 \| 格言 \|\n\| --- \| --- \| --- \|\n)(?:\|.*\n)*", lambda m: m[1] + rows + "\n", text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    items = load()
    out, readme = render(items), render_readme(items)
    if args.check:
        stale = [p.name for p, new in ((OUT, out), (README, readme))
                 if not p.exists() or p.read_text(encoding="utf-8") != new]
        if stale:
            print(f"ERROR lessons/{', '.join(stale)} が古い。python3 scripts/build_lessons.py を実行する", file=sys.stderr)
            return 1
        print("OK lessons/index.html と README.md は最新")
        return 0
    OUT.write_text(out, encoding="utf-8")
    README.write_text(readme, encoding="utf-8")
    print(f"OK lessons/index.html を書き出した（{out.count(chr(10))} 行）")
    return 0


TEMPLATE = r"""<title>教訓かるた</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@500;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* 配置: かるたの取り札を並べた卓。札の表は縦書きの格言、選ぶと寓話・教訓・問いを開く */
:root {
  --paper: #e9ece8;      /* 卓（灰がかった和紙） */
  --card: #fbfbf8;       /* 札 */
  --ink: #1d2733;        /* 本文の墨 */
  --muted: #5d6874;      /* 添え書き */
  --ai: #24466e;         /* 藍：札の縁と見出し */
  --shu: #b8432c;        /* 朱：判と強調 */
  --line: #cfd5d2;
  --veil: rgba(29, 39, 51, .45);
  --display: "Shippori Mincho B1", "Hiragino Mincho ProN", "Yu Mincho", serif;
  --body: "Zen Kaku Gothic New", "Hiragino Sans", "Yu Gothic", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #12171e; --card: #1b222c; --ink: #e5e8ec; --muted: #9aa6b2;
    --ai: #9db7da; --shu: #e1765f; --line: #2c3540; --veil: rgba(0, 0, 0, .6); color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --paper: #12171e; --card: #1b222c; --ink: #e5e8ec; --muted: #9aa6b2;
  --ai: #9db7da; --shu: #e1765f; --line: #2c3540; --veil: rgba(0, 0, 0, .6); color-scheme: dark;
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { background: var(--paper); color: var(--ink); font-family: var(--body); font-size: 15px; line-height: 1.8; }
.wrap { max-width: 1120px; margin: 0 auto; padding-inline: 16px; padding-block: 40px 64px; }
header { display: grid; gap: 12px; margin-bottom: 28px; }
h1 { font-family: var(--display); font-weight: 800; font-size: clamp(34px, 6vw, 52px); line-height: 1.15; margin: 0; letter-spacing: .06em; color: var(--ai); }
h1 .seal { display: inline-grid; place-items: center; width: 1.05em; height: 1.05em; margin-left: .25em; border: 3px solid var(--shu); border-radius: 6px; color: var(--shu); font-size: .5em; vertical-align: .55em; letter-spacing: 0; transform: rotate(-6deg); }
.lead { margin: 0; max-width: 62ch; color: var(--muted); }
.bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 24px; }
.chip, .draw { font: 500 14px/1 var(--body); border-radius: 999px; padding: 9px 16px; cursor: pointer; border: 1px solid var(--line); background: var(--card); color: var(--ink); }
.chip[aria-pressed="true"] { background: var(--ai); border-color: var(--ai); color: var(--card); }
.draw { margin-left: auto; border-color: var(--shu); color: var(--shu); background: transparent; }
.chip:focus-visible, .draw:focus-visible, .card:focus-visible, .close:focus-visible, .nav button:focus-visible { outline: 3px solid var(--shu); outline-offset: 2px; }
.count { font: 500 12px var(--mono); color: var(--muted); letter-spacing: .04em; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 18px; }
.card { position: relative; display: grid; grid-template-rows: auto 1fr auto; gap: 10px; min-height: 300px; padding: 14px; text-align: left; cursor: pointer;
  background: var(--card); color: var(--ink); border: 1px solid var(--line); border-radius: 6px; box-shadow: inset 0 0 0 5px var(--card), inset 0 0 0 6px var(--ai); font: inherit; transition: transform .15s ease; }
.card:hover { transform: translateY(-3px); }
.card .top { display: flex; justify-content: space-between; align-items: flex-start; padding: 4px 6px 0; }
.kana { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: var(--shu); color: var(--card); font: 700 21px/1 var(--display); }
.id { font: 500 11px var(--mono); color: var(--muted); letter-spacing: .05em; }
.maxim { writing-mode: vertical-rl; font: 700 21px/1.6 var(--display); letter-spacing: .08em; justify-self: center; max-height: 230px; color: var(--ink); text-wrap: balance; }
.card .foot { display: flex; justify-content: space-between; gap: 8px; padding: 0 6px 4px; font-size: 12px; color: var(--muted); }
.card .foot b { font-weight: 500; color: var(--ai); white-space: nowrap; }
.card .foot span { text-align: right; }
.veil { position: fixed; inset: 0; background: var(--veil); display: grid; place-items: center; padding: 16px; z-index: 10; }
.sheet { position: relative; width: min(720px, 100%); max-height: calc(100% - 32px); overflow-y: auto; background: var(--card); color: var(--ink); border-radius: 8px; padding: 32px clamp(20px, 5vw, 48px); box-shadow: inset 0 0 0 6px var(--card), inset 0 0 0 7px var(--ai); }
.close { position: absolute; top: 14px; right: 14px; width: 36px; height: 36px; border-radius: 50%; border: 1px solid var(--line); background: var(--card); color: var(--ink); font-size: 20px; line-height: 1; cursor: pointer; }
.sheet .meta { font: 500 12px var(--mono); color: var(--muted); letter-spacing: .05em; margin: 0 0 6px; }
.sheet h2 { font: 800 clamp(24px, 4vw, 32px)/1.4 var(--display); margin: 0 0 24px; color: var(--ai); text-wrap: balance; }
.sheet h3 { font: 700 13px var(--body); letter-spacing: .12em; color: var(--muted); margin: 0 0 8px; }
.fable { margin: 0 0 28px; padding: 18px 22px; border-left: 3px solid var(--line); }
.fable h4 { font: 700 18px var(--display); margin: 0 0 10px; }
.fable p { margin: 0 0 .6em; max-width: 60ch; }
.lesson { display: grid; grid-template-columns: auto 1fr; gap: 16px; align-items: start; margin: 0 0 28px; }
.lesson .stamp { display: grid; place-items: center; width: 52px; height: 52px; border: 2px solid var(--shu); border-radius: 6px; color: var(--shu); font: 800 15px/1.1 var(--display); text-align: center; transform: rotate(-4deg); }
.lesson p { margin: 0; font-weight: 500; min-width: 0; }
.questions { margin: 0 0 28px; padding: 0; list-style: none; display: grid; gap: 8px; }
.questions li { padding: 10px 14px; border: 1px dashed var(--line); border-radius: 6px; }
.questions li::before { content: "問 "; color: var(--shu); font-family: var(--display); font-weight: 800; }
.source { font-size: 13px; color: var(--muted); margin: 0 0 20px; }
.source a { color: var(--ai); }
.nav { display: flex; justify-content: space-between; gap: 8px; border-top: 1px solid var(--line); padding-top: 16px; }
.nav button { font: 500 14px var(--body); background: none; border: 0; color: var(--ai); cursor: pointer; padding: 6px 0; }
.note { margin-top: 40px; font-size: 13px; color: var(--muted); max-width: 70ch; }
@media (max-width: 480px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .card { min-height: 250px; }
  .maxim { font-size: 17px; max-height: 190px; }
  .draw { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) { .card { transition: none; } .card:hover { transform: none; } }
</style>

<div class="wrap">
  <header>
    <h1>教訓かるた<span class="seal" aria-hidden="true">知</span></h1>
    <p class="lead">人と AI が一緒に書いたエッセイから取り出した知恵を、格言・寓話・問いの札にしました。札を選ぶと、短い寓話と、明日の自分に投げかける問いが開きます。</p>
  </header>
  <div class="bar" role="toolbar" aria-label="札の絞り込み">
    <div id="chips" style="display:flex;flex-wrap:wrap;gap:8px"></div>
    <span class="count" id="count">__COUNT__ 枚</span>
    <button class="draw" id="draw" type="button">一枚引く</button>
  </div>
  <div class="grid" id="grid"></div>
  <noscript><ul>__NOSCRIPT__</ul></noscript>
  <p class="note">寓話は教訓を伝えるための創作で、出典のエッセイに登場する話ではありません。教訓と問いは、出典のエッセイの主張に沿って書いています。札の番号（W-0001 など）は、AI エージェント向けの知恵 skill のカード番号と対応しています。</p>
</div>

<div class="veil" id="veil" hidden>
  <article class="sheet" id="sheet" role="dialog" aria-modal="true" aria-labelledby="s-title">
    <button class="close" id="close" type="button" aria-label="閉じる">×</button>
    <p class="meta" id="s-meta"></p>
    <h2 id="s-title"></h2>
    <section class="fable"><h3>寓話</h3><h4 id="s-fable-title"></h4><div id="s-fable"></div></section>
    <div class="lesson"><span class="stamp" aria-hidden="true">教<br>訓</span><p id="s-lesson"></p></div>
    <h3>自分に問う</h3>
    <ul class="questions" id="s-questions"></ul>
    <p class="source" id="s-source"></p>
    <div class="nav"><button type="button" id="prev">← 前の札</button><button type="button" id="next">次の札 →</button></div>
  </article>
</div>

<script>
const ITEMS = __DATA__;
const THEMES = __THEMES__;
const $ = (id) => document.getElementById(id);
let filter = "すべて";
let shown = ITEMS;
let current = -1;
let opener = null;

function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

function renderChips() {
  const box = $("chips"); box.textContent = "";
  ["すべて", ...THEMES].forEach((t) => {
    const b = el("button", "chip", t); b.type = "button";
    b.setAttribute("aria-pressed", String(t === filter));
    b.addEventListener("click", () => { filter = t; try { localStorage.setItem("karuta-filter", t); } catch (e) {} renderChips(); renderGrid(); });
    box.append(b);
  });
}

function renderGrid() {
  shown = filter === "すべて" ? ITEMS : ITEMS.filter((i) => i.theme === filter);
  $("count").textContent = shown.length + " 枚";
  const grid = $("grid"); grid.textContent = "";
  shown.forEach((item, idx) => {
    const c = el("button", "card"); c.type = "button";
    c.setAttribute("aria-label", item.id + " " + item.maxim);
    const top = el("div", "top");
    top.append(el("span", "kana", item.maxim.replace(/^[「『（]/, "").charAt(0)), el("span", "id", item.id));
    const foot = el("div", "foot");
    foot.append(el("b", null, item.theme), el("span", null, item.fable_title));
    c.append(top, el("span", "maxim", item.maxim), foot);
    c.addEventListener("click", () => { opener = c; openSheet(idx); });
    grid.append(c);
  });
}

function openSheet(idx) {
  current = (idx + shown.length) % shown.length;
  const item = shown[current];
  $("s-meta").textContent = item.id + " ・ " + item.theme;
  $("s-title").textContent = item.maxim;
  $("s-fable-title").textContent = item.fable_title;
  const fable = $("s-fable"); fable.textContent = "";
  item.fable.forEach((p) => fable.append(el("p", null, p)));
  $("s-lesson").textContent = item.lesson;
  const q = $("s-questions"); q.textContent = "";
  item.questions.forEach((t) => q.append(el("li", null, t)));
  const src = $("s-source"); src.textContent = "";
  if (item.source) {
    src.append("出典: ");
    const a = el("a", null, item.source.title); a.href = item.source.url; a.target = "_blank"; a.rel = "noopener";
    src.append(a);
  }
  $("veil").hidden = false;
  $("sheet").scrollTop = 0;
  $("close").focus();
  try { history.replaceState(null, "", "#" + item.id.toLowerCase()); } catch (e) {}
}

function closeSheet() {
  $("veil").hidden = true;
  try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
  if (opener) opener.focus();
}

$("close").addEventListener("click", closeSheet);
$("veil").addEventListener("click", (e) => { if (e.target === $("veil")) closeSheet(); });
$("prev").addEventListener("click", () => openSheet(current - 1));
$("next").addEventListener("click", () => openSheet(current + 1));
$("draw").addEventListener("click", () => { opener = $("draw"); openSheet(Math.floor(Math.random() * shown.length)); });
document.addEventListener("keydown", (e) => {
  if ($("veil").hidden) return;
  if (e.key === "Escape") closeSheet();
  if (e.key === "ArrowRight") openSheet(current + 1);
  if (e.key === "ArrowLeft") openSheet(current - 1);
});

try { const saved = localStorage.getItem("karuta-filter"); if (saved && (saved === "すべて" || THEMES.includes(saved))) filter = saved; } catch (e) {}
renderChips();
renderGrid();
const hash = location.hash.slice(1).toUpperCase();
if (hash && ITEMS.some((x) => x.id === hash)) {
  if (!shown.some((x) => x.id === hash)) { filter = "すべて"; renderChips(); renderGrid(); }
  openSheet(shown.findIndex((x) => x.id === hash));
}
</script>
"""

if __name__ == "__main__":
    sys.exit(main())
