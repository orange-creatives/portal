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

def _build_share_html(url, title):
    from urllib.parse import quote
    encoded_url = quote(url, safe='')
    encoded_title = quote(title, safe='')
    return f'''    <div class="share-buttons">
      <a class="share-btn" href="https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}" target="_blank" rel="noopener" title="X">
        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a class="share-btn" href="https://b.hatena.ne.jp/entry/{url}" target="_blank" rel="noopener" title="はてなブックマーク">
        <svg viewBox="0 0 24 24"><path d="M20.47 2H3.53A1.45 1.45 0 002 3.38v17.24A1.45 1.45 0 003.53 22h16.94A1.45 1.45 0 0022 20.62V3.38A1.45 1.45 0 0020.47 2zM8.8 17.04H5.8V6.96h2.87a3.2 3.2 0 012.27.73 2.46 2.46 0 01.77 1.91 2.35 2.35 0 01-1.48 2.29 2.65 2.65 0 011.78 2.62 2.71 2.71 0 01-.87 2.07 3.44 3.44 0 01-2.34.46zm.16-7.14H7.53v2.28h1.4a1.37 1.37 0 001-.34 1.23 1.23 0 00.35-.92 1.17 1.17 0 00-.36-.88 1.34 1.34 0 00-.96-.14zm.2 3.9H7.53v2.36h1.65a1.48 1.48 0 001.05-.37 1.28 1.28 0 00.39-1 1.22 1.22 0 00-.4-.95 1.55 1.55 0 00-1.06-.04zm8.22.52a2.83 2.83 0 01-.83 2.12 3.22 3.22 0 01-2.3.76h-3.1V6.96h2.96a3.14 3.14 0 012.17.71 2.39 2.39 0 01.75 1.84 2.33 2.33 0 01-1.43 2.24 2.6 2.6 0 011.78 2.57zm-3.34-4.42h-1.51v2.28h1.48a1.39 1.39 0 001-.34 1.21 1.21 0 00.36-.91 1.17 1.17 0 00-.36-.89 1.36 1.36 0 00-.97-.14zm.24 3.9h-1.75v2.36h1.72a1.49 1.49 0 001.05-.37 1.27 1.27 0 00.39-1 1.22 1.22 0 00-.4-.95 1.54 1.54 0 00-1.01-.04z"/></svg>
      </a>
      <a class="share-btn" href="https://social-plugins.line.me/lineit/share?url={encoded_url}" target="_blank" rel="noopener" title="LINE">
        <svg viewBox="0 0 24 24"><path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
      </a>
      <button class="share-btn" onclick="navigator.clipboard.writeText(\'{url}\').then(function(){{var b=this;b.classList.add(\'share-btn--copied\');b.title=\'コピーしました\';setTimeout(function(){{b.classList.remove(\'share-btn--copied\');b.title=\'リンクをコピー\'}},2000)}}.bind(this))" title="リンクをコピー">
        <svg viewBox="0 0 24 24"><path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>'''

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
    share_html = _build_share_html(article_url, title)
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
        f'  <meta name="twitter:card" content="summary_large_image">',
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
        share_html,
        '    <div class="bottom-nav"><a href="../../">&larr; orange-wks</a></div>',
        "  </div>",
        "</main>",
        "",
        "<footer><p>orange</p></footer>",
        "",
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
    desc = re.sub(r"<[^>]+>", "", body_html).strip().replace("\n", " ")[:80] + "..."
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
