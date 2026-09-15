---
name: picture-book-orchestrator
description: >-
  Use this when starting or resuming a picture-book project to pick the next
  process-stage skill and keep human/AI roles consistent across stages.
---

# 絵本制作オーケストレータ

工程技能を正しい順で選ぶ。作業そのものは各工程の `SKILL.md` に委譲する。
状態語彙・版・承認捏造禁止は `_shared/process-state.md` に従う。

## 担当

- **AI:** 次工程の提案、開始条件／確定条件の区別の確認
- **人:** 工程の確定判断と答え責任

## 前提

案件フォルダまたは同等の置き場がある（なければ提案して切る）。

## 手順

1. 入力の有無を確認する（対象年齢、一言主題、禁止線、頁数目安、絵のトーン、AIに任せる範囲、買い手／納品の型）。
2. 未確定なら `picture-book-brief` から始める。
3. **開始条件**と**確定条件**を分けて次を選ぶ（下表）。反復してよいループを直線に強制しない。
4. 上流を直したら下流を `要再確認` にする（`process-state.md`）。
5. 答え責任（最終判断者）がメモに無ければ brief に戻して書く。

### 開始条件 vs 確定条件

| 工程 | 開始してよい条件 | 確定して次の本番系へ進む条件 |
| --- | --- | --- |
| synopsis | brief が人の確認可能な核を持つ | synopsis **確定** |
| pagination | synopsis 確定 | pagination 確定（ただし prose/rough と反復可） |
| prose | pagination の下書き以上がある | prose **確定**（final-art 前） |
| character | brief 以降いつでも可 | character **確定**（final-art 前。キャラ無しは N/A） |
| rough | prose・character の下書き以上で開始可 | rough **確定**（final-art 前）。途中で visual-refs 可 |
| visual-refs | rough 作業中でも可（任意） | 使ったなら方針メモ。スキップ可 |
| final-art | **prose・character・rough がすべて確定**（character は N/A 可） | 本番全頁＋チェックログ |
| readthrough (A) | rough＋仮文が揃う | A 相の記録。致命的は差し戻し |
| readthrough (B) | final-art＋本文確定 | B 相通過、致命的未解決なし |
| rights-export | readthrough B 通過 | 素材リスト証拠付き・書き出し実ファイル検証 |
| epub（任意） | rights-export 済かつ brief で Kindle/EPUB | EPUB 実ファイル＋人のメタ/目次/権利確認 |
| youtube（任意） | rights-export 済かつ brief で YouTube | 音声付き動画＋ページ同期確認＋人の公開判断 |

### 基本順と戻り先（要約）

- brief 済 → synopsis
- synopsis 済 → pagination
- pagination ⇄ prose ⇄ rough（反復可）。character は rough と並行可
- rough 途中 → visual-refs（任意）
- prose+character+rough **確定** → final-art
- final-art 前または後 → readthrough の相を選ぶ（A＝ラフ段階、B＝本番後）
- readthrough B 済 → rights-export
- rights-export 済 → brief の公開チャネルに応じて `picture-book-epub` および／または `picture-book-youtube`（どちらも任意。選ばれていなければここで打ち切り可）

## 完了条件（オーケストレータ自身）

- 次に開く工程と、それが開始条件を満たす理由を一文で示せる
- 飛ばした工程があれば、意図的スキップか未達かを区別してメモにある
- どの成果物が `確定`／`要再確認` かを `process-state.md` の語彙で言える

## 成果物の置き場（提案）

リポジトリまたは案件フォルダに `projects/<slug>/` を切り、工程成果を置く:

- `brief.md`
- `synopsis.md`
- `pagination.md`
- `prose.md`
- `character.md`（または N/A 記録）
- `rough-notes.md`
- `visual-refs/`（任意）
- `readthrough.md`
- `rights.md`（権利追跡＋書き出しチェック）
- `epub/` または EPUB ファイル参照（任意）
- `youtube/` または動画・読み上げ稿参照（任意）

## やらないこと

- 工程を飛ばして本文や絵を一気に生成する
- 開始条件と確定条件を混同する（例: rough 開始できる＝final-art してよい、とみなす）
- 人の承認を捏造して「確定」と書く
- このファイルに個別案件の固有名詞を焼き込む
