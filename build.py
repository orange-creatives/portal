"""
orange-creatives/portal build script v3
- meta.json の section フィールドで3セクションに振り分け
- section: "featured" / "recent" (default) / "archive"
- featured: トップに大カードグリッド
- recent: トップにコンパクトリスト
- archive: 別ページ (archive.html)
"""
import json, glob, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BLOG_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://orange-creatives.github.io/portal"

def load_articles():
    articles = []
    for meta_path in glob.glob(os.path.join(BLOG_DIR, 'articles', '*', 'meta.json')):
        with open(meta_path, encoding='utf-8') as f:
            meta = json.load(f)
        dir_name = os.path.basename(os.path.dirname(meta_path))
        meta['_dir'] = dir_name
        articles.append(meta)
    articles.sort(key=lambda a: a.get('date', '0000-00-00'), reverse=True)
    return articles

def render_card(article):
    tags_html = ''.join(f'<span class="card-tag">{t}</span>' for t in article.get('tags', []))
    href = article.get('url') or f"articles/{article['_dir']}/"
    target = ' target="_blank" rel="noopener"' if article.get('url') else ''
    platform = article.get('platform', '')
    badge = f'<span class="card-badge card-badge--{platform.lower()}">{platform}</span>' if platform else ''
    cover_src = article['cover'] if article['cover'].startswith('assets/') else f"articles/{article['_dir']}/{article['cover']}"
    return f'''    <a class="card" href="{href}"{target}>
      <img class="card-image" src="{cover_src}" alt="{article['title']}">
      <div class="card-body">
        <div class="card-meta">
          {tags_html}
          {badge}
          <span>{article['date']}</span>
        </div>
        <div class="card-title">{article['title']}</div>
        <div class="card-desc">{article['description']}</div>
      </div>
    </a>'''

def render_compact_item(article):
    tags_html = ''.join(f'<span class="card-tag">{t}</span>' for t in article.get('tags', []))
    href = article.get('url') or f"articles/{article['_dir']}/"
    target = ' target="_blank" rel="noopener"' if article.get('url') else ''
    platform = article.get('platform', '')
    badge = f'<span class="card-badge card-badge--{platform.lower()}">{platform}</span>' if platform else ''
    return f'''    <a class="compact-item" href="{href}"{target}>
      <span class="compact-date">{article['date']}</span>
      <span class="compact-title">{article['title']}</span>
      <span class="compact-meta">
        {tags_html}
        {badge}
      </span>
    </a>'''

PORTAL_CSS = """
    :root {
      --bg: #f9f9f7;
      --surface: #fff;
      --text: #1a1a1a;
      --muted: #888;
      --border: #e5e5e5;
      --accent: #e8622a;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }
    header {
      padding: 3rem 2rem 2rem;
      max-width: 960px;
      margin: 0 auto;
      border-bottom: 1px solid var(--border);
    }
    header h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
    header p { margin-top: 0.4rem; color: var(--muted); font-size: 0.9rem; }
    main { max-width: 960px; margin: 0 auto; padding: 2.5rem 2rem 4rem; }
    .section-title {
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin: 3rem 0 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }
    .section-title:first-child { margin-top: 0; }

    /* Featured: card grid */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.5rem;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      text-decoration: none;
      color: inherit;
      display: flex;
      flex-direction: column;
      transition: box-shadow 0.2s, transform 0.2s;
    }
    .card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); transform: translateY(-2px); }
    .card-image { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; background: #f0ede8; }
    .card-body { padding: 1.2rem 1.3rem 1.4rem; flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
    .card-meta { font-size: 0.78rem; color: var(--muted); display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
    .card-tag { color: var(--accent); font-weight: 600; }
    .card-badge { font-size: 0.7rem; font-weight: 700; padding: 0.1em 0.5em; border-radius: 3px; letter-spacing: 0.03em; }
    .card-badge--zenn { background: #3ea8ff22; color: #3ea8ff; }
    .card-badge--qiita { background: #55c500aa; color: #2d6a00; }
    .card-title { font-size: 1rem; font-weight: 700; line-height: 1.5; }
    .card-desc { font-size: 0.85rem; color: var(--muted); line-height: 1.6; margin-top: auto; padding-top: 0.4rem; }

    /* Recent: compact list */
    .compact-list {
      display: flex;
      flex-direction: column;
    }
    .compact-item {
      display: flex;
      align-items: baseline;
      gap: 1rem;
      padding: 0.7rem 0;
      border-bottom: 1px solid var(--border);
      text-decoration: none;
      color: inherit;
      transition: background 0.15s;
    }
    .compact-item:hover { background: rgba(0,0,0,0.02); }
    .compact-date { font-size: 0.8rem; color: var(--muted); flex-shrink: 0; min-width: 6rem; }
    .compact-title { font-size: 0.95rem; font-weight: 600; flex: 1; min-width: 0; }
    .compact-meta { font-size: 0.75rem; display: flex; gap: 0.4rem; align-items: center; flex-shrink: 0; }

    /* Archive link */
    .archive-link {
      display: inline-block;
      margin-top: 1.5rem;
      color: var(--accent);
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
    }
    .archive-link:hover { text-decoration: underline; }

    /* Nav */
    .nav-back {
      display: inline-block;
      margin-bottom: 1.5rem;
      color: var(--accent);
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
    }
    .nav-back:hover { text-decoration: underline; }

    footer { text-align: center; padding: 2rem; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 2rem; }
    .header-inner { display: flex; align-items: center; gap: 1rem; }
    .header-logo { width: 48px; height: 48px; border-radius: 6px; flex-shrink: 0; }
    @media (prefers-color-scheme: dark) {
      :root { --bg: #1a1a1a; --surface: #222; --text: #d4d4d8; --muted: #666; --border: #333; }
      .compact-item:hover { background: rgba(255,255,255,0.03); }
    }
"""

HEADER_HTML = """<header>
  <div class="header-inner">
    <img class="header-logo" src="assets/orange.png" alt="orange">
    <div>
      <h1>orange creatives</h1>
      <p>apps, music, words, and whatever catches my eye</p>
    </div>
  </div>
</header>"""

FOOTER_HTML = """<footer>
  <p>orange</p>
  <p style="margin-top:0.5rem;font-size:0.75rem;opacity:0.45;">まあちらかってるじぶんをまとめるのもいいかなって　きみがいるなら</p>
</footer>"""

def build():
    articles = load_articles()
    featured = [a for a in articles if a.get('section') == 'featured']
    recent = [a for a in articles if a.get('section', 'recent') == 'recent']
    archive = [a for a in articles if a.get('section') == 'archive']

    # --- index.html ---
    sections_html = ''

    if featured:
        cards = '\n\n'.join(render_card(a) for a in featured)
        sections_html += f'''  <h2 class="section-title">Featured</h2>
  <div class="grid">

{cards}

  </div>'''

    if recent:
        items = '\n'.join(render_compact_item(a) for a in recent)
        sections_html += f'''
  <h2 class="section-title">Recent</h2>
  <div class="compact-list">
{items}
  </div>'''

    if archive:
        sections_html += '\n  <a class="archive-link" href="archive.html">Archive &rarr;</a>'

    index_html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>orange creatives</title>
  <meta property="og:title" content="orange creatives">
  <meta property="og:description" content="apps, music, words, and whatever catches my eye">
  <meta property="og:image" content="{SITE_URL}/assets/orange.png">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <style>{PORTAL_CSS}  </style>
</head>
<body>

{HEADER_HTML}

<main>
{sections_html}
</main>

{FOOTER_HTML}

</body>
</html>'''

    out = os.path.join(BLOG_DIR, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(index_html)

    # --- archive.html ---
    all_articles = sorted(
        featured + recent + archive,
        key=lambda a: a.get('date', '0000-00-00'),
        reverse=True
    )
    archive_items = '\n'.join(render_compact_item(a) for a in all_articles)

    archive_html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Archive - orange creatives</title>
  <meta property="og:title" content="orange creatives">
  <meta property="og:description" content="apps, music, words, and whatever catches my eye">
  <meta property="og:image" content="{SITE_URL}/assets/orange.png">
  <meta property="og:url" content="{SITE_URL}/archive.html">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <style>{PORTAL_CSS}  </style>
</head>
<body>

{HEADER_HTML}

<main>
  <a class="nav-back" href="./">&larr; Back</a>
  <h2 class="section-title">Archive</h2>
  <div class="compact-list">
{archive_items}
  </div>
</main>

{FOOTER_HTML}

</body>
</html>'''

    archive_out = os.path.join(BLOG_DIR, 'archive.html')
    with open(archive_out, 'w', encoding='utf-8') as f:
        f.write(archive_html)

    print(f'Built {len(featured)} featured + {len(recent)} recent + {len(archive)} archive')
    print(f'  -> index.html, archive.html')

if __name__ == '__main__':
    build()
