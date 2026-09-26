# Claude Code 向け

スキル本体はリポジトリ直下の [`.agents/skills/`](../.agents/skills/) にあります。

ZIP 展開環境（ChromeOS の Files など）ではシンボリックリンクが解凍失敗の原因になるため、ここにはリンクを置いていません。

使うときは次のどちらかです。

- エージェントに `.agents/skills/`（またはリポジトリ本体）を渡す
- 必要なら `.agents/skills` をこのディレクトリへコピーする: `cp -R ../.agents/skills ./skills`
