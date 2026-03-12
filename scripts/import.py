#!/usr/bin/env python3
"""
orange-wks/portal - 記事インポートスクリプト

使い方:
  python scripts/import.py zenn <slug>        # zenn-content/ のローカルまたはZenn APIから
  python scripts/import.py qiita <item-id>    # Qiita API から取得

オプション:
  --section recent|archive    セクション指定（デフォルト: recent）
  --date YYYY-MM-DD           日付を上書き
"""
import sys, os, json, re, html as html_lib, urllib.request, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BLOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZENN_DIR = os.path.join(os.path.dirname(BLOG_DIR), "zenn-content", "articles")
ZENN_USERNAME = "orangewk"
SITE_URL = "https://orange-wks.github.io/portal"

ARTICLE_CSS_LINK = '  <link rel="stylesheet" href="../../assets/article.css">'

try:
    import markdown as md_lib
    def md2html(text):
        return md_lib.markdown(text, extensions=["fenced_code", "tables"])
except ImportError:
    def md2html(text):
        return "<pre>" + html_lib.escape(text) + "</pre>"

def build_article_html(title, date, tags, body_html, slug, description, source_url=None, source_name=None, cover=None):
    tags_html = "".join(f'<span class="article-tag">{t}</span>' for t in tags)
    source_html = ""
    if source_url:
        source_html = (f'<div class="source-link">初出: '
                       f'<a href="{source_url}" target="_blank" rel="noopener">'
                       f'{source_name or source_url}</a></div>')
    if cover and cover.startswith("assets/"):
        og_image = f"{SITE_URL}/{cover}"
        cover_src = f"../../{cover}"
    elif cover:
        og_image = f"{SITE_URL}/articles/{slug}/{cover}"
        cover_src = cover
    else:
        og_image = f"{SITE_URL}/assets/orange.png"
        cover_src = None
    cover_tag = f'    <img class="article-cover" src="{cover_src}" alt="{html_lib.escape(title)}">' if cover_src else ""
    article_url = f"{SITE_URL}/articles/{slug}/"
    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"  <title>{html_lib.escape(title)}</title>",
        f'  <meta property="og:title" content="{html_lib.escape(title)}">',
        f'  <meta property="og:description" content="{html_lib.escape(description)}">',
        f'  <meta property="og:image" content="{og_image}">',
        f'  <meta property="og:url" content="{article_url}">',
        f'  <meta property="og:type" content="article">',
        f'  <meta name="twitter:image" content="{og_image}">',
        f'  <meta name="twitter:card" content="summary">',
        ARTICLE_CSS_LINK,
        "</head>",
        "<body>",
        "",
        "<header>",
        f"  <h1>{html_lib.escape(title)}</h1>",
        "</header>",
        "",
        "<main>",
        '  <div class="nav-links"><a href="../../">&larr; orange-wks</a></div>',
        '  <div class="article-body">',
        f'    <div class="article-meta">{tags_html}<span>{date}</span></div>',
        cover_tag,
        f"    {body_html}",
        f"    {source_html}",
        '    <div class="bottom-nav"><a href="../../">&larr; orange-wks</a></div>',
        "  </div>",
        "</main>",
        "",
        "<footer><p>orange</p></footer>",
        "",
        '<script src="../../assets/share.js"></script>',
        "</body>",
        "</html>",
    ])

def parse_zenn_fm(content):
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}, content
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w+):\s*(.+)", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"')
    topics_m = re.search(r"topics:\s*\[([^\]]+)\]", m.group(1))
    if topics_m:
        fm["topics"] = [t.strip().strip('"') for t in topics_m.group(1).split(",")]
    return fm, content[m.end():]

def fetch_zenn_api(slug):
    url = f"https://zenn.dev/api/articles/{slug}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))["article"]

def fetch_qiita(item_id):
    url = f"https://qiita.com/api/v2/items/{item_id}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

def save_article(slug, title, date, tags, body_html, section, source_url, source_name, cover):
    out_dir = os.path.join(BLOG_DIR, "articles", slug)
    os.makedirs(out_dir, exist_ok=True)
    desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", body_html)).strip()[:150] + "..."
    html = build_article_html(title, date, tags, body_html, slug, desc, source_url, source_name, cover)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    meta = {
        "title": title, "description": desc, "date": date,
        "tags": tags[:2], "cover": cover, "platform": source_name,
        "source_url": source_url, "section": section
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Saved: articles/{slug}/  [{date}] {title[:50]}")

def cmd_zenn(slug, section, date_override):
    local_path = os.path.join(ZENN_DIR, f"{slug}.md")
    if os.path.exists(local_path):
        with open(local_path, encoding="utf-8") as f:
            content = f.read()
        fm, body_md = parse_zenn_fm(content)
        title = fm.get("title", slug)
        topics = fm.get("topics", [])
        if isinstance(topics, str):
            topics = [topics]
        body_html = md2html(body_md)
    else:
        print(f"No local file, fetching from Zenn API...")
        data = fetch_zenn_api(slug)
        title = data["title"]
        topics = [t["display_name"] for t in data.get("topics", [])]
        body_html = data.get("body_html") or md2html(data.get("body_markdown") or "")

    data_api = fetch_zenn_api(slug)
    date = date_override or data_api["published_at"][:10]
    save_article(slug, title, date, topics, body_html, section,
                 f"https://zenn.dev/{ZENN_USERNAME}/articles/{slug}",
                 "Zenn", "assets/ogp.jpg")

def cmd_qiita(item_id, section, date_override):
    data = fetch_qiita(item_id)
    title = data["title"]
    tags = [t["name"] for t in data.get("tags", [])]
    body_html = md2html(data["body"])
    date = date_override or data["created_at"][:10]
    save_article(f"qiita-{item_id}", title, date, tags, body_html, section,
                 data["url"], "Qiita", "assets/ogp.jpg")

def main():
    parser = argparse.ArgumentParser(description="Import article to orange-wks/portal")
    parser.add_argument("platform", choices=["zenn", "qiita"])
    parser.add_argument("slug_or_id", help="Zenn slug or Qiita item ID")
    parser.add_argument("--section", default="recent", choices=["featured", "recent", "archive"])
    parser.add_argument("--date", help="Override date (YYYY-MM-DD)")
    args = parser.parse_args()
    if args.platform == "zenn":
        cmd_zenn(args.slug_or_id, args.section, args.date)
    elif args.platform == "qiita":
        cmd_qiita(args.slug_or_id, args.section, args.date)
    print("Done. Run 'python build.py' to rebuild index.html")

if __name__ == "__main__":
    main()
