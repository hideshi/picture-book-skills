---
name: picture-book-visual-refs
description: >-
  Use optionally during or after roughs when AI reference images may help;
  check brief AI scope before image generation; human selects adoption policy.
---

# 工程7: ビジュアル参照（任意）

状態は `_shared/process-state.md` に従う。

## 担当

- **AI:** 構図・小物・光の参照候補（**brief の AI 範囲内のみ**）
- **人:** 採用／不採用、トレース方針のメモ

## 前提

### 開始条件

rough 作業中でも、rough 後でも呼んでよい。必須工程ではない。

### 画像生成の前に

`brief.md` の **AI に任せる範囲** を確認する。画像生成・参照生成が範囲外なら、この工程で生成しない（言葉の構図案に留めるかスキップ）。

## 手順

1. brief の AI 範囲を読み、生成してよいか判定する。範囲外なら理由を残してスキップ。
2. 必要な頁・不足（構図、小物、背景）を特定する。
3. AI で候補を出し、人が選ぶ。
4. 採用したものの利用方針（参照のみ／部分トレース不可、など）を書く。
5. ファイルを `visual-refs/` に置き、ページ番号と紐づける。character / final-art のベースラインになりうるならその旨を書く。

## 完了条件

- 使ったなら方針メモと brief AI 範囲の確認記録がある
- 使わなければこの工程スキップでよい

## やらないこと

- brief の AI 範囲を確認せずに画像生成する
- 参照を最終イラストとして納品する（別方針を brief で明示した場合を除く）
