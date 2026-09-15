---
name: picture-book-synopsis
description: >-
  Use this after the picture-book brief is fixed to draft a 3–5 beat synopsis:
  human gives theme/desired scenes/feeling, AI may propose beats, human adopts.
---

# 工程2: あらすじ

状態は `_shared/process-state.md` に従う。

## 担当

- **人:** 主題・欲しい場面・感触（核）と最終採用
- **AI:** 人が核を出した**後**に、3–5 拍の構造候補を提案してよい。主題変更禁止。採用は人

## 前提

`brief.md` が完了条件を満たしている（少なくとも主題・禁止線・対象が人の手にある）こと。

## 手順

1. 人が次を出す（長文の「背骨」全文を一人で先に書く必要はない）:
   - 主題（brief と一致）
   - 欲しい場面・イメージ（箇条で可）
   - 読後の感触
2. AI が同じ禁止線のまま 3–5 拍の構造候補を 2–3 案出してよい。
3. 人が 1 案を採用（または自分で書き直し）し、不採用理由を一言残す。
4. 確定あらすじを `synopsis.md` に書き、状態を人が `確定` にする。

## 完了条件

- 確定あらすじが `synopsis.md` にある
- brief の主題・禁止線と矛盾しない
- 採用者が人として記録されている

## やらないこと

- 人の核（主題・欲しい場面・感触）なしに AI が物語をゼロから決める
- AI 案をそのまま「決定稿」扱いにする
- ページ表より先に長文本文を書き始める
