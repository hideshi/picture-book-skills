---
name: picture-book-prose
description: >-
  Use this after pagination to draft page text with AI candidates, then human
  read-aloud editing for rhythm, age vocabulary, and final wording.
---

# 工程4: 本文

## 担当

- **AI:** 頁番号つき本文候補（各頁 1–3 案まで）
- **人:** 音読、語彙、優しさ、最終文言の署名

## 前提

`pagination.md` 完了。`brief.md` の年齢・禁止線を守る。

## AI への制約

- 1 頁あたり短文、音読で息が続く長さ
- 主題を変えない、頁数を勝手に増減しない
- 説教くさい締めを強制しない

## 手順

1. ページ表と確定あらすじを渡して候補生成。
2. 人が音読して直す（子どもがつまずく箇所を優先）。
3. 頁の文と絵の主役分担をメモする（絵が主役なら文は最小）。

## 完了条件

- `prose.md` がページ表と一致
- 人が通しで音読して詰まらない

## やらないこと

- AI 出力を読み上げずに確定する
