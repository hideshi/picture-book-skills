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
6. 任意公開工程（epub / youtube）を **明示開始** した場合は、brief の公開チャネル欄へ選択を書き戻す。
7. 短いパスで工程を省略する場合は、対象成果物・スキップした工程・人の判断を残す（`process-state.md`）。記録なしの省略を完了にしない。

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
| rights-export | readthrough B 通過（または短いパス例外の記録あり） | 節Aクローズ＋節B（分岐前書き出し）の実ファイル検証。**最終 EPUB／最終動画そのものではない** |
| epub（任意） | 節A＋節B 済。納品なら prose・本番絵が **確定**。brief で Kindle/EPUB、または明示開始して brief へ書き戻し | EPUB 実ファイル＋形式適合・検証不合格の解消＋人のメタ／読み味確認。公開ステータスは別 |
| youtube（任意） | 節A＋節B 済。納品なら本番絵 **確定**（ラフは brief 例外＋目的記録時のみ）。brief で YouTube、または明示開始して brief へ書き戻し | 音声付き動画＋同期表の合否（書き出し動画上）＋人の声／公開判断。公開ステータスは別 |

プロトタイプ目的の試し変換は、納品用の確定条件を満たさなくても **開始**してよい。成果の目的を分けて記録し、納品 `確定` と混同しない。

### 基本順と戻り先（要約）

- brief 済 → synopsis
- synopsis 済 → pagination
- pagination ⇄ prose ⇄ rough（反復可）。character は rough と並行可
- rough 途中 → visual-refs（任意）
- prose+character+rough **確定** → final-art
- final-art 前または後 → readthrough の相を選ぶ（A＝ラフ段階、B＝本番後）
- readthrough B 済 → rights-export
- rights-export 済 → brief の公開チャネルに応じて `picture-book-epub` および／または `picture-book-youtube`（どちらも任意。選ばれていなければここで打ち切り可）
- 任意工程の不備時の戻り: EPUB レイアウト→epub／TTS・同期→youtube／中身→上流 craft＋要再確認／新規素材権利→rights 節A／チャネル変更→brief

## 完了条件（オーケストレータ自身）

- 次に開く工程と、それが開始条件を満たす理由を一文で示せる
- 飛ばした工程があれば、意図的スキップか未達かを区別し、短いパスなら対象・スキップ・人の判断がメモにある
- どの成果物が `確定`／`要再確認` か、公開ステータスがあるかを `process-state.md` の語彙で言える
- 明示開始した任意パスがあれば brief へのチャネル書き戻し済み

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
- `rights.md`（権利追跡＋書き出しチェック。節Bは分岐前確認）
- `epub/` または EPUB ファイル参照（任意・最終成果はここ）
- `youtube/` または動画・読み上げ稿・同期表参照（任意・最終成果はここ）

## やらないこと

- 工程を飛ばして本文や絵を一気に生成する
- 開始条件と確定条件を混同する（例: rough 開始できる＝final-art してよい、とみなす）
- rights-export 節B の検証を最終 EPUB／最終動画の完了と同一視する
- 「出荷可能」など共有語彙外で完了を宣言する
- 人の承認を捏造して「確定」と書く
- このファイルに個別案件の固有名詞を焼き込む
