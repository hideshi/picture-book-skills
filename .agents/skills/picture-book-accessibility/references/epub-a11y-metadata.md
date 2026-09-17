# EPUBアクセシビリティメタデータ規約

W3C EPUB Accessibility 1.1 および Schema.org に準拠したメタデータを EPUB の `package.opf` に付与することで、書店、配信プラットフォーム、読書支援機器が作品のアクセシビリティ対応状況を正確に認識できます。

---

## 1. W3C EPUB Accessibility 1.1 仕様区分

| プロパティ | 区分 | 固定絵本での標準値・記述例 | 補足 |
| :--- | :--- | :--- | :--- |
| `schema:accessMode` | **MUST** | `textual`<br>`visual` | 本書を認知・受容するために必要な知覚モード。絵本は原則として視覚とテキストの両方。 |
| `schema:accessibilityFeature` | **MUST** | 実装済みの機能のみ列挙：<br>`alternativeText`（画像代替テキスト）<br>`readingOrder`（論理的読み順）<br>`tableOfContents`（目次ナビ）<br>`pageNavigation`（ページリスト） | 未実装の機能（例: 音声同期がないのに `synchronizedAudioText`）を記載してはならない。 |
| `schema:accessibilityHazard` | **MUST** | `none` | 光の点滅（`flashing`）、激しい動的変化（`motionSimulation`）、不快音（`sound`）がない場合は `none` を明記。 |
| `schema:accessModeSufficient` | **SHOULD** | `textual,visual`<br>`textual`（詳細な代替テキストのみで完全理解できると評価した場合） | 完読に必要な知覚モードの組み合わせ。 |
| `schema:accessibilitySummary` | **SHOULD** | （平易な日本語で作成。下記参照） | 全体的な対応状況、固定レイアウトとしての特性や制約を簡潔に説明。 |
| `dcterms:conformsTo` | **条件付** | `https://www.w3.org/TR/epub-a11y-11/#wcag-2.1-aa` 等 | 正式な適合評価を行った場合のみ指定。評価未了の場合は付与しない。 |
| `a11y:certifiedBy` | **条件付** | 評価を行った個人名、組織名、または認証機関名 | `dcterms:conformsTo` を付与した場合に必須。 |

---

## 2. 日本語アクセシビリティ要約（`accessibilitySummary`）の文案テンプレート

固定レイアウト絵本において、代替テキストが付与されている場合の標準的な記述例です。自動断定ではなく、実際の対応状況に合わせて記述します。

```text
本作品は固定レイアウト形式の絵本です。すべての挿絵ページに、本文テキストおよび情景・登場人物の表情・動作を解説した代替テキスト（alt属性）が付与されており、スクリーンリーダー等の音声読み上げ技術による通読が可能です。文字サイズの拡大・リフローには対応していません。光の点滅等の視覚的危険性はありません。
```

---

## 3. `package.opf` への組み込み例

```xml
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
  <!-- 基本書誌情報 -->
  <dc:identifier id="pub-id">urn:uuid:00000000-0000-0000-0000-000000000000</dc:identifier>
  <dc:title>[作品タイトル]</dc:title>
  <dc:creator>[著者名]</dc:creator>
  <dc:language>ja</dc:language>
  <meta property="dcterms:modified">2026-09-17T00:00:00Z</meta>

  <!-- W3C EPUB Accessibility 1.1 メタデータ -->
  <!-- 1. 必須項目 (MUST) -->
  <meta property="schema:accessMode">textual</meta>
  <meta property="schema:accessMode">visual</meta>
  <meta property="schema:accessibilityFeature">alternativeText</meta>
  <meta property="schema:accessibilityFeature">readingOrder</meta>
  <meta property="schema:accessibilityFeature">tableOfContents</meta>
  <meta property="schema:accessibilityFeature">pageNavigation</meta>
  <meta property="schema:accessibilityHazard">none</meta>

  <!-- 2. 推奨項目 (SHOULD) -->
  <meta property="schema:accessModeSufficient">textual,visual</meta>
  <meta property="schema:accessModeSufficient">textual</meta>
  <meta property="schema:accessibilitySummary">本作品は固定レイアウト形式の絵本です。すべての挿絵ページに、本文および情景・表情・動作を解説した代替テキストが付与されており、スクリーンリーダーによる通読が可能です。文字拡大・リフローには対応していません。</meta>

  <!-- 3. 適合評価を行った場合のみ付与 (Optional / Conditional) -->
  <!--
  <meta property="dcterms:conformsTo" id="a11y-conf">https://www.w3.org/TR/epub-a11y-11/#wcag-2.1-aa</meta>
  <meta property="a11y:certifiedBy" refines="#a11y-conf">[評価者・認証組織名]</meta>
  -->
</metadata>
```
