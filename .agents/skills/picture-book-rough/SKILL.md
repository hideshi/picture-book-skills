---
name: picture-book-rough
description: >-
  Use this to rough every page; may start from draft prose/character, iterate
  with pagination/prose, and call visual-refs mid-rough — human-selected thumbnails.
---

# 工程6: ラフ

状態は `_shared/process-state.md` に従う。

## 担当

- **人:** 全頁ラフの採否と構成判断（必須）
- **AI:** brief の画像運用モード内で、構図案、Web用プロンプト、参照／ラフ候補を補助

## 前提

### 開始条件

`prose.md` と `character.md`（または N/A）の **下書き以上** があれば開始してよい。pagination とも反復してよい。

### 確定条件（final-art へ進む前）

prose・character（または N/A）・rough がいずれも **確定**。

## 手順

1. brief の画像運用モードと一貫性ポリシーを読む。人物・場所・小道具の基準参照一覧を作る。
2. 全頁サムネ／ラフを作る。AI候補を許す案件でも、人が頁ごとの採否と修正を記録する。
3. 各頁に「絵主役／文主役」を印する。
4. 舞台・人物配置をbriefの `固定` / `可変` / `N/A` と照合する。可変や例外は pagination の指定と一致させる。
5. キー小道具はプロップ・アンカーと照合し、構造・部品・相対サイズを守る。
6. **製本見開きペアリング確認:** 物理的な製本構造（扉p1単独 → 見開きp2-3, p4-5... → 閉じ単独）を前提に、同時に視界に入る対面ページ同士の調和・呼吸を確認する。
7. キャラシート違反と、意図しない文字・擬音・記号・実在ロゴを潰す。意図的な文字は文字正本と制作方法を確認する。
8. めくりの間が死んでいる頁を直す。
9. 詰まった頁は `picture-book-visual-refs` を **ラフ途中で**呼んでよい。
10. カバーが必要なら本文ラフと別に作り、一覧サムネイルとタイトル安全域を確認する。
11. ページ表・本文と矛盾したら pagination / prose へ戻し、該当成果物を `要再確認` にする。
12. 任意で readthrough **相 A**（ラフ＋仮文）を挟んでよい。

## 完了条件

- 全頁ラフがあり、`rough-notes.md` に頁コメントまたはファイル参照がある
- 固定項目の基準参照、可変項目、意図した例外、AI候補の採否が追跡できる
- 必要な案件ではカバーラフが本文と別にある
- final-art に進むなら状態が `確定`（開始時点では下書きでよい）

## やらないこと

- 人の頁別採否がないAI候補を、そのまま確定ラフとして扱う
- 「rough を開始できた」ことを「prose/character/rough 確定済み」と混同する
