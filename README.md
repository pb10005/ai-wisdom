# ai-wisdom（知恵袋）

AI と一緒に書いたエッセイを蓄積し、そこから抽出した「知恵」を AI エージェント用の
skill として配布するためのリポジトリ。

```
エッセイ (essays/)  ──抽出──▶  知恵 skill (skills/ai-wisdom/)  ──読み込み──▶  AI エージェント
```

## ディレクトリ構成

| パス | 役割 |
| --- | --- |
| `essays/YYYY/YYYY-MM-DD-<slug>.md` | エッセイ本体（一次資料）。frontmatter 付き Markdown |
| `essays/YYYY/assets/<エッセイ名>/` | 取り込んだ原本（PDF など）と図 |
| `essays/_template.md` | エッセイのテンプレート |
| `skills/ai-wisdom/SKILL.md` | エージェントが読み込む知恵 skill の入口（索引） |
| `skills/ai-wisdom/references/<theme>.md` | テーマ別の知恵カード |
| `.claude/skills/add-essay/` | エッセイを保存するためのワークフロー skill（このリポジトリ作業用） |
| `.claude/skills/extract-wisdom/` | エッセイから知恵を抽出するワークフロー skill（このリポジトリ作業用） |
| `.claude-plugin/` | このリポジトリを Claude Code プラグインとして配布するための定義 |
| `scripts/check.py` | エッセイと知恵カードの整合性チェック |
| `scripts/import_docs.py` | Claude Docs の Markdown 書き出しをエッセイとして保存 |

## ワークフロー

### 1. エッセイを置く

AI との対話で書いたエッセイを `essays/<年>/<日付>-<slug>.md` に保存する。
Claude Code 上なら「このエッセイを知恵袋に追加して」と頼むと `add-essay` skill が
テンプレートに沿って保存する。

新しいエッセイの frontmatter は `extracted: false` にしておく。

Claude Docs で書いたエッセイは「Claude Docs の〇〇を知恵袋に取り込んで」と頼めばよい。
`add-essay` skill が文書を Markdown で書き出し、`scripts/import_docs.py` で検証・保存し、図を SVG に起こして戻す。

PDF で渡す場合も「この PDF を知恵袋に取り込んで」と頼めばよい。原本と図を `assets/` に保存し、
ページ画像と照合しながら Markdown に起こす（Claude Docs からの取り込みより手間がかかり、劣化しやすい）。

### 2. 知恵を抽出する

「未抽出のエッセイから知恵を抽出して」と頼むと `extract-wisdom` skill が動き、

1. `extracted: false` のエッセイを探す
2. 再利用可能な原則（知恵）を取り出し、知恵カードの形式にする
3. 既存カードと重複・矛盾がないか確認し、`skills/ai-wisdom/references/` に追記・統合する
4. `SKILL.md` の索引を更新する
5. エッセイの frontmatter を `extracted: true` にし、生まれた知恵の ID を記録する

### 3. 検証する

```sh
python3 scripts/check.py
```

PR / push 時にも GitHub Actions で同じチェックが走る。

## 知恵 skill をエージェントに読み込ませる

### Claude Code プラグインとして入れる

```
/plugin marketplace add pb10005/ai-wisdom
/plugin install ai-wisdom@ai-wisdom
```

### skill ディレクトリをコピー / シンボリックリンクする

```sh
# 個人スコープ
ln -s "$(pwd)/skills/ai-wisdom" ~/.claude/skills/ai-wisdom
# 特定プロジェクト
cp -r skills/ai-wisdom <project>/.claude/skills/
```

`SKILL.md` は Agent Skills の標準形式（YAML frontmatter + Markdown）なので、
同形式に対応した他のエージェントでもそのまま使える。
