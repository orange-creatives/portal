# orange-wks portal

orangeの活動・記事・作品をまとめるポータルサイト。
https://orange-wks.github.io/portal/

## ワークフロー

### 新しい記事を追加する

**Zenn の記事（ローカルファイルあり or なし）**
```bash
python scripts/import.py zenn <slug>
```

**Qiita の記事**
```bash
python scripts/import.py qiita <item-id>
```

**過去記事（archive セクションに入れる）**
```bash
python scripts/import.py zenn <slug> --section archive
python scripts/import.py qiita <item-id> --section archive
```

**日付を手動指定したい場合**
```bash
python scripts/import.py zenn <slug> --date 2026-01-15
```

### ランディングページを更新する

```bash
python build.py
```

記事の追加・削除後は必ず実行する。

### GitHub に push する

```bash
git add .
git commit -m "feat: <記事タイトル> を追加"
git push
```

## ディレクトリ構成

```
portal/
├── index.html              # ランディングページ（build.py が生成）
├── build.py                # index.html ビルドスクリプト
├── scripts/
│   └── import.py           # 記事インポートスクリプト
├── articles/
│   ├── <slug>/
│   │   ├── index.html      # 記事本文
│   │   ├── meta.json       # カード用メタデータ
│   │   └── cover.png       # カバー画像（手動 or Nano Banana で生成）
│   └── ...
└── assets/
    ├── orange.png          # ロゴ画像
    └── covers/
        ├── zenn-default.png
        └── qiita-default.png
```

## meta.json の構造

```json
{
  "title": "記事タイトル",
  "description": "カードに表示する一行説明",
  "date": "2026-03-05",
  "tags": ["AI", "ClaudeCode"],
  "cover": "assets/ogp.jpg",
  "platform": "Zenn",
  "source_url": "https://zenn.dev/orangewk/articles/slug",
  "section": "recent"
}
```

`section` は `"recent"`（最近の投稿）か `"archive"`（過去の活動）。

## カバー画像について

カバー画像がない場合はプラットフォーム別のデフォルト画像が使われる。
記事ごとに画像を用意する場合は `articles/<slug>/cover.png` に置いて
`meta.json` の `"cover"` を `"cover.png"` に変更する。

Nano Banana（Gemini画像生成）で作る場合:
```bash
NODE_PATH=prototype/node_modules npx tsx scripts/art/cli.ts \
  --prompt "..." \
  --output "art/generated/<name>.png" \
  --aspect-ratio "16:9"
```
生成後 `articles/<slug>/cover.png` にコピーして meta.json を更新。
