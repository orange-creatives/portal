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
    with open(BASE_CSS_PATH, encoding='utf-8') as f:
        base = f.read()
    css_match = re.search(r'<style>(.*?)</style>', base, re.DOTALL)
    base_css = css_match.group(1) if css_match else ''

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
  <h1>orange creatives</h1>
  <p>apps, music, words, and whatever catches my eye</p>
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
