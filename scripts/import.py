#!/usr/bin/env python3
"""
orange-creatives/portal - 記事インポートスクリプト

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

ARTICLE_CSS = """
    .article-body { max-width: 720px; margin: 0 auto; }
    .article-body h2 { color: var(--heading-color); font-size: 1.4rem; margin: 2.5rem 0 1rem;
        padding-bottom: 0.3rem; border-bottom: 2px solid var(--accent); }
    .article-body h3 { color: #37474f; font-size: 1.15rem; margin: 2rem 0 0.8rem;
        padding-left: 0.5rem; border-left: 4px solid var(--accent); }
    .article-body p { margin: 0.8rem 0; }
    .article-body ul, .article-body ol { padding-left: 1.5rem; margin: 0.8rem 0; }
    .article-body li { margin: 0.4rem 0; }
    .article-body code { background: var(--code-bg); padding: 0.2em 0.4em;
        border-radius: 3px; font-family: monospace; font-size: 0.9em; }
    .article-body pre { background: var(--code-bg); padding: 1rem;
        border-radius: 6px; overflow-x: auto; margin: 1rem 0; }
    .article-body pre code { padding: 0; background: none; }
    .article-body blockquote { border-left: 4px solid #ddd; padding: 0.5rem 1rem;
        color: #666; margin: 1rem 0; }
    .article-body img { max-width: 100%; border-radius: 6px; }
    .article-body table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    .article-body th, .article-body td { border: 1px solid #ddd; padding: 0.6rem; }
    .article-body th { background: #f5f5f5; }
    .article-meta { color: #888; font-size: 0.85rem; margin-bottom: 2rem;
        display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
    .article-tag { color: var(--accent); font-weight: 600; }
    .source-link { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #ddd;
        font-size: 0.85rem; color: #888; }
    .source-link a { color: var(--accent); }
    .nav-links { display: flex; margin: 1.5rem 0; }
    .nav-links a { color: var(--accent); text-decoration: none; font-weight: 600; font-size: 0.9rem; }
"""

def get_base_css():
    path = os.path.join(BLOG_DIR, "articles", "llm-mechanism", "index.html")
    with open(path, encoding="utf-8") as f:
        m = re.search(r"<style>(.*?)</style>", f.read(), re.DOTALL)
    return m.group(1) if m else ""

try:
    import markdown as md_lib
    def md2html(text):
        return md_lib.markdown(text, extensions=["fenced_code", "tables"])
except ImportError:
    def md2html(text):
        return "<pre>" + html_lib.escape(text) + "</pre>"

def build_article_html(title, date, tags, body_html, source_url=None, source_name=None):
    base_css = get_base_css()
    tags_html = "".join(f'<span class="article-tag">{t}</span>' for t in tags)
    source_html = ""
    if source_url:
        source_html = (f'<div class="source-link">初出: '
                       f'<a href="{source_url}" target="_blank" rel="noopener">'
                       f'{source_name or source_url}</a></div>')
    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"  <title>{html_lib.escape(title)}</title>",
        f"  <style>{base_css}{ARTICLE_CSS}  </style>",
        "</head>",
        "<body>",
        "",
        "<header>",
        f"  <h1>{html_lib.escape(title)}</h1>",
        "</header>",
        "",
        "<main>",
        '  <div class="nav-links"><a href="../../">&larr; orange creatives</a></div>',
        '  <div class="article-body">',
        f'    <div class="article-meta">{tags_html}<span>{date}</span></div>',
        f"    {body_html}",
        f"    {source_html}",
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
    html = build_article_html(title, date, tags, body_html, source_url, source_name)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    desc = re.sub(r"<[^>]+>", "", body_html).strip().replace("\n", " ")[:80] + "..."
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
                 "Zenn", "assets/covers/zenn-default.png")

def cmd_qiita(item_id, section, date_override):
    data = fetch_qiita(item_id)
    title = data["title"]
    tags = [t["name"] for t in data.get("tags", [])]
    body_html = md2html(data["body"])
    date = date_override or data["created_at"][:10]
    save_article(f"qiita-{item_id}", title, date, tags, body_html, section,
                 data["url"], "Qiita", "assets/covers/qiita-default.png")

def main():
    parser = argparse.ArgumentParser(description="Import article to orange-creatives/portal")
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
