---
name: picture-book-pagination
description: >-
  Use this after synopsis lock to build a page table: what the art shows, whether
  text exists, and page-turn timing — human-owned pacing; may iterate with prose/rough.
---

# 工程3: ページ表

状態は `_shared/process-state.md` に従う。

## 担当

- **人:** 全頁の絵／文／めくりの設計（必須）
- **AI:** 頁割り候補の提案は可。採用は人

## 前提

`synopsis.md` 確定済み。brief の総頁・数え方・表紙扱いに従う。

## 手順

1. 総頁を brief に合わせる（数え方・表紙を再確認）。
2. 各頁に書く: 頁番号、絵で見せること、文の有無、めくりの効き。
   brief の一貫性ポリシーで可変にした舞台・人物配置・小道具は、変更内容と理由も頁へ割り当てる。
3. 文なし頁を意図的に残してよいか確認する。
4. 説明過多の頁を削る／分割する。
5. 本文とは別にカバーが必要なら、タイトル安全域、サムネイルで読める主役、本文頁との数え分けを記録する。
6. prose・rough で破綻したらここへ戻り、状態を `要再確認` → 再確定する。

## 完了条件

- `pagination.md` に全頁が埋まり、あらすじの拍と対応している
- 「文量で埋めただけ」の頁がない
- 可変項目と意図した例外が該当頁に割り当てられている
- カバーが必要な案件では本文と別のカバー枠がある
- 人が確定したことが記録されている（prose/rough 反復中は `下書き` でも開始可）

## やらないこと

- 本文完成前に本番彩色に入る
- pagination を凍結したまま prose/rough の矛盾を放置する
