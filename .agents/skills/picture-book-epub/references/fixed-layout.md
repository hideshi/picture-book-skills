# 固定レイアウト実装・検証

固定レイアウトは、レイアウト自体が作品の意味に関わるときに選ぶ。対象ストアの
仕様は変更されるため、制作時に公式仕様を確認し、確認日と対象端末を案件記録に残す。

## 共通パッケージ

- EPUB 3 の `rendition:layout=pre-paginated` と各XHTMLの viewport を設定する。
- カバー画像に manifest の `cover-image` を付ける。旧環境用 `meta name="cover"`
  や `guide` は対象環境で必要な場合に併記する。
- spine は表紙から始め、本文開始ランドマークは最初の本文頁へ向ける。
- 一頁一XHTMLを基本とし、綴じ方向、左右頁、見開き表示を作品の設計と合わせる。
- nav に目次、本文開始等のlandmark、必要に応じpage-listを入れる。

## 固定＋独立HTML文字

- 文字はDOM上の読み順と視覚上の読み順を一致させる。
- 領域拡大や文字ポップアップを使う場合は対象リーダーの公式方式に従う。
- CSSの位置、フォント、行送りを対象端末で確認する。透過帯や画像上配置そのものを
  一律禁止にはせず、重なりと可読性で判定する。

## 固定＋焼き込み文字

- 「上部文字領域＋下部挿絵」は互換性優先の一プロファイルとして使える。
- 解像度や比率は案件で決める。1440×1920は固定要件ではない。
- 採用本文の独立テキスト正本を保持し、画像の代替情報へ本文と絵の意味を反映する。
- 文字拡大・検索・読み上げの制約、小画面での可読性を人が確認する。
- 見開きを一枚にする場合は、頁をまたぐ読み順が一枚の中で完結する設計にする。

## 検証記録

| 種別 | 記録する内容 |
| --- | --- |
| 構造 | EPUBCheck版・結果、manifest/spine/nav、リンク、頁数 |
| 汎用表示 | ビューア名・版、表紙、頁送り、見開き、回転、欠け |
| Kindle | Previewer／実機、文字拡大方式、表紙、開始位置、頁送り |
| Google Play Books | Web Reader／Android等、アップロード処理、表紙、見開き、開始位置 |
| アクセシビリティ | 読み順、代替文、言語、landmark、page-list、既知の制約 |

構造合格は表示合格を意味しない。対象ストアへ出す前に、そのストアのプレビューまたは
実機で確認する。

## 制作時の公式確認先

- EPUB 3.3: <https://www.w3.org/TR/epub-33/>
- W3C Fixed Layout Accessibility: <https://www.w3.org/TR/epub-fxl-a11y/>
- Google Play Books EPUB files: <https://support.google.com/books/partner/answer/3316879>
- Amazon KDP Fixed-Layout Books with Text Pop-Ups: <https://kdp.amazon.com/help/topic/GFFHCXVPHRZW8SJ5>
