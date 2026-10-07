# ai-wisdom リポジトリでの作業ルール

このリポジトリは「エッセイ → 知恵 → skill」というパイプラインで成り立っている。詳細は README.md。

- エッセイ（`essays/`）は一次資料。保存後に本文の意味を書き換えない（誤字修正・frontmatter 更新は可）。
- エッセイの追加は `add-essay` skill、知恵の抽出は `extract-wisdom` skill の手順に従う。
- 知恵カード（`skills/ai-wisdom/references/*.md`）には必ず出典エッセイへの相対リンクを付ける。
- 知恵 ID（`W-0001` 形式）は一度振ったら変えない・再利用しない。廃止する場合は `status: retired` にする。
- `skills/ai-wisdom/SKILL.md` は短く保つ（索引と使い方のみ）。本文はテーマ別 references に置く。
- 変更後は `python3 scripts/check.py` を実行して通ることを確認する。
- 文書は日本語で書く。
