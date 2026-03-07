"""
orange-creatives/portal build script v2
- meta.json の section フィールドでセクション分け
- section: "recent" (default) / "archive"
"""
import json, glob, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BLOG_DIR = "C:/Users/orang/AppData/Local/Temp/blog-init"

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
    
    # external link vs internal
    href = article.get('url') or f"articles/{article['_dir']}/"
    target = ' target="_blank" rel="noopener"' if article.get('url') else ''
    
    # platform badge
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
    .card-badge { font-size: 0.7rem; font-weight: 700; padding: 0.1em 0.5em; border-radius: 3px; }
    .card-badge--zenn { background: #3ea8ff22; color: #1a7fd4; }
    .card-badge--qiita { background: #55c50022; color: #2d6a00; }
    .card-title { font-size: 1rem; font-weight: 700; line-height: 1.5; }
    .card-desc { font-size: 0.85rem; color: var(--muted); line-height: 1.6; margin-top: auto; padding-top: 0.4rem; }
    footer { text-align: center; padding: 2rem; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 2rem; }
    .header-inner { display: flex; align-items: center; gap: 1rem; }
    .header-logo { width: 48px; height: 48px; border-radius: 6px; flex-shrink: 0; }
    @media (prefers-color-scheme: dark) {
      :root { --bg: #1a1a1a; --surface: #222; --text: #d4d4d8; --muted: #666; --border: #333; }
    }
"""

def render_section(title, articles):
    if not articles:
        return ''
    cards = '\n\n'.join(render_card(a) for a in articles)
    return f'''  <h2 class="section-title">{title}</h2>
  <div class="grid">

{cards}

  </div>'''

EXTRA_CSS = """
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
    .card-badge {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.1em 0.5em;
      border-radius: 3px;
      letter-spacing: 0.03em;
    }
    .card-badge--zenn { background: #3ea8ff22; color: #3ea8ff; }
    .card-badge--qiita { background: #55c500aa; color: #2d6a00; }
"""

BASE_CSS_PATH = os.path.join(BLOG_DIR, 'articles', 'llm-mechanism', 'index.html')

def build():
    import re
    base_css = PORTAL_CSS

    articles = load_articles()
    recent = [a for a in articles if a.get('section', 'recent') == 'recent']
    archive = [a for a in articles if a.get('section') == 'archive']

    sections_html = render_section('最近の投稿', recent)
    if archive:
        sections_html += '\n' + render_section('過去の活動', archive)

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>orange creatives</title>
  <style>{base_css}{EXTRA_CSS}  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <img class="header-logo" src="assets/orange.png" alt="orange">
    <div>
      <h1>orange creatives</h1>
      <p>apps, music, words, and whatever catches my eye</p>
    </div>
  </div>
</header>

<main>
{sections_html}
</main>

<footer>
  <p>orange</p>
  <p style="margin-top:0.5rem;font-size:0.75rem;opacity:0.45;">まあちらかってるじぶんをまとめるのもいいかなって　きみがいるなら</p>
</footer>

</body>
</html>'''

    out = os.path.join(BLOG_DIR, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Built {len(recent)} recent + {len(archive)} archive cards')

if __name__ == '__main__':
    build()
