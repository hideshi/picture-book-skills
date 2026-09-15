---
name: picture-book-orchestrator
description: >-
  Use this when starting or resuming a picture-book project to pick the next
  process-stage skill and keep human/AI roles consistent across stages.
---

# 絵本制作オーケストレータ

工程技能を正しい順で選ぶ。作業そのものは各工程の `SKILL.md` に委譲する。

## 手順

1. 入力の有無を確認する（対象年齢、一言主題、禁止線、頁数目安、絵のトーン、AIに任せる範囲）。
2. 未確定なら `picture-book-brief` から始める。
3. 確定済みの成果物に応じて次を選ぶ:
   - brief 済 → `picture-book-synopsis`
   - synopsis 済 → `picture-book-pagination`
   - pagination 済 → `picture-book-prose` と `picture-book-character`（並行可、ラフ前に両方）
   - prose+character 済 → `picture-book-rough`
   - rough 済 → 必要なら `picture-book-visual-refs`、なければ `picture-book-final-art`
   - final-art 済 → `picture-book-readthrough`
   - readthrough 済 → `picture-book-rights-export`
4. 各工程の完了条件を満たすまで次へ進まない。
5. 答え責任（最終判断者）がメモに無ければ brief に戻して書く。

## 成果物の置き場（提案）

リポジトリまたは案件フォルダに `projects/<slug>/` を切り、工程成果を置く:

- `brief.md`
- `synopsis.md`
- `pagination.md`
- `prose.md`
- `character.md`
- `rough-notes.md`
- `visual-refs/`（任意）
- `readthrough.md`
- `rights.md`

## やらないこと

- 工程を飛ばして本文や絵を一気に生成する
- このファイルに個別案件の固有名詞を焼き込む
