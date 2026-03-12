#!/usr/bin/env python3
"""
import_shinobi.py - 忍者ブログ (orangeness.blog.shinobi.jp) の全記事をクロールして
orange-wks/portal の articles/ に保存するスクリプト。

保存先:
  E:/orange-wks/portal/articles/shinobi-NNN/
  C:/Users/orang/AppData/Local/Temp/blog-init/articles/shinobi-NNN/

使い方:
  python3 scripts/import_shinobi.py
"""

import sys
import os
import re
import json
import time
import urllib.request
import urllib.parse
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "https://orangeness.blog.shinobi.jp"
BLOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = "C:/Users/orang/AppData/Local/Temp/blog-init"

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
    .article-body iframe { max-width: 100%; }
    .article-meta { color: #888; font-size: 0.85rem; margin-bottom: 2rem;
        display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
    .article-tag { color: var(--accent); font-weight: 600; }
    .source-link { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #ddd;
        font-size: 0.85rem; color: #888; }
    .source-link a { color: var(--accent); }
    .nav-links { display: flex; margin: 1.5rem 0; }
    .nav-links a { color: var(--accent); text-decoration: none; font-weight: 600; font-size: 0.9rem; }
"""



def fetch(url, sleep_sec=1.0):
    """URL を取得して UTF-8 文字列を返す。"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    time.sleep(sleep_sec)
    return raw.decode("utf-8", errors="replace")


def strip_tags(html):
    """HTMLタグを除去してテキストを返す。"""
    return re.sub(r"<[^>]+>", "", html)


def clean_body_html(raw_html):
    """
    記事本文の生HTMLを整形する。
    - PR広告ブロック (ninja-blog-inactive) を除去
    - NinjaClap 以降を除去
    - script/style タグを除去
    - iframe は保持（ニコニコ動画埋め込みなど）
    """
    # NinjaClap 以降を除去
    html = re.split(r'<p class="NinjaClap"', raw_html, maxsplit=1)[0]

    # ninja-blog-inactive ブロック除去
    html = re.sub(
        r'<div id="ninja-blog-inactive".*?</div>\s*</div>\s*<script[^>]*>.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )

    # script タグ除去
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)

    # style タグ除去
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

    # NinjaEntryCommercial 除去
    html = re.sub(
        r'<div class="NinjaEntryCommercial"[^>]*>.*?</div>',
        "",
        html,
        flags=re.DOTALL,
    )

    return html.strip()


SITE_URL = "https://orange-wks.github.io/portal"

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

def build_article_html(title, date, tags, body_html, source_url, slug):
    tags_html = "".join(f'<span class="article-tag">{t}</span>' for t in tags)
    import html as html_lib
    source_html = (
        f'<div class="source-link">初出: '
        f'<a href="{source_url}" target="_blank" rel="noopener">'
        f"Shinobiブログ (orangeness)</a></div>"
    )
    cover = "assets/ogp.jpg"
    og_image = f"{SITE_URL}/{cover}"
    cover_src = f"../../{cover}"
    desc_text = strip_tags(body_html).strip().replace("\n", " ")
    desc_text = re.sub(r"\s+", " ", desc_text)[:80] + "..."
    article_url = f"{SITE_URL}/articles/{slug}/"
    share_html = _build_share_html(article_url, title)
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="ja">',
            "<head>",
            '  <meta charset="UTF-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"  <title>{html_lib.escape(title)}</title>",
            f'  <meta property="og:title" content="{html_lib.escape(title)}">',
            f'  <meta property="og:description" content="{html_lib.escape(desc_text)}">',
            f'  <meta property="og:image" content="{og_image}">',
            f'  <meta property="og:url" content="{article_url}">',
            f'  <meta property="og:type" content="article">',
            f'  <meta name="twitter:image" content="{og_image}">',
            f'  <meta name="twitter:card" content="summary_large_image">',
            '  <link rel="stylesheet" href="../../assets/article.css">',
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
            f'    <img class="article-cover" src="{cover_src}" alt="{html_lib.escape(title)}">',
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
        ]
    )


def save_article(slug, title, date, tags, body_html, source_url):
    """
    BLOG_DIR/articles/<slug>/ と TEMP_DIR/articles/<slug>/ の両方に保存する。
    """
    cover = "assets/ogp.jpg"
    desc_text = strip_tags(body_html).strip().replace("\n", " ")
    desc_text = re.sub(r"\s+", " ", desc_text)[:80] + "..."

    meta = {
        "title": title,
        "description": desc_text,
        "date": date,
        "tags": tags[:3],
        "cover": cover,
        "platform": "Shinobi",
        "source_url": source_url,
        "section": "archive",
    }

    html_content = build_article_html(title, date, tags, body_html, source_url, slug)

    for base in [BLOG_DIR, TEMP_DIR]:
        out_dir = os.path.join(base, "articles", slug)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Saved: {slug}  [{date}] {title[:50]}")


def collect_article_urls_from_page(page_html):
    """
    一覧ページから記事URLのリストを返す（[PR]エントリは除外）。
    EntryTitle の href を収集する。
    """
    urls = []
    titles_raw = re.findall(
        r'class="EntryTitle">\s*<a href="([^"]+)">', page_html
    )
    for href in titles_raw:
        if not href:  # 空 href は PR 広告
            continue
        full_url = BASE_URL + href
        urls.append(full_url)
    return urls


def has_next_page(page_html):
    # 実際のパターン: <a href="/Page/N/">NEXT&nbsp;&gt;&gt;</a>
    return bool(re.search(r'href="/Page/\d+/">NEXT', page_html))


def parse_article_page(html, url):
    """
    記事個別ページから (title, date, category, body_html) を返す。
    忍者ブログは EntryInnerBlock が複数ある（PR + 本記事）。
    EntryInnerBlock の開始位置を列挙し、次の EntryInnerBlock か EntryFooter までを各ブロックとする。
    """
    # EntryInnerBlock の開始位置を全て取得
    starts = [m.start() for m in re.finditer(r'<div class="EntryInnerBlock">', html)]
    footer_positions = [m.start() for m in re.finditer(r'<div class="EntryFooter">', html)]

    blocks = []
    for i, start in enumerate(starts):
        # このブロックの終端: 次のEntryInnerBlockの開始 or 対応するEntryFooterの開始
        # EntryFooter はブロックの外にある（ブロックの次のdivがEntryFooter）
        if i + 1 < len(starts):
            # 次のEntryInnerBlock手前までが対象
            # ただし、対応するEntryFooterを使う（startより後の最初のEntryFooter）
            foot_candidates = [p for p in footer_positions if p > start and p < starts[i + 1]]
            end = foot_candidates[0] if foot_candidates else starts[i + 1]
        else:
            # 最後のEntryInnerBlock: start以降の最初のEntryFooter
            foot_candidates = [p for p in footer_positions if p > start]
            end = foot_candidates[0] if foot_candidates else len(html)
        blocks.append(html[start + len('<div class="EntryInnerBlock">'):end])

    # PR を除く（EntryTitleFont が "[PR]" のブロックをスキップ）
    article_block = None
    for block in blocks:
        title_m = re.search(r'class="EntryTitleFont">(.*?)</span>', block)
        if title_m and title_m.group(1).strip() == "[PR]":
            continue
        article_block = block
        break

    if not article_block:
        return None

    # タイトル取得
    title_m = re.search(r'class="EntryTitleFont">(.*?)</span>', article_block)
    title = title_m.group(1).strip() if title_m else "無題"

    # EntryText 内容取得
    body_m = re.search(r'<div class="EntryText">(.*)', article_block, re.DOTALL)
    body_raw = body_m.group(1) if body_m else ""
    body_html = clean_body_html(body_raw)

    # EntryFooter から日付・カテゴリを取得
    # PR広告フッター（/Date/20260307/）を除き、最初の有効なフッターを使う
    # 構造: EntryData[0]=日付, EntryData[1]=カテゴリ(/カテゴリ名/ へのリンク)
    footers = re.findall(r'<div class="EntryFooter">(.*?)</div>', html, re.DOTALL)
    date_str = ""
    category = ""
    PR_DATE = "20260307"  # 忍者ブログのPR広告フッターの日付
    for footer in footers:
        date_m = re.search(r'href="/Date/(\d{8})/"', footer)
        if not date_m:
            continue
        d = date_m.group(1)
        if d == PR_DATE:
            continue  # PR広告フッターをスキップ
        date_str = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        # EntryData スパンを順番に取得: [0]=日付, [1]=カテゴリ
        entry_data = re.findall(r'<span class="EntryData">(.*?)</span>', footer, re.DOTALL)
        if len(entry_data) >= 2:
            cat_m = re.search(r'href="([^"#]*)">(.*?)</a>', entry_data[1])
            if cat_m and cat_m.group(2).strip() and cat_m.group(2).strip() != "▲Top":
                category = cat_m.group(2).strip()
        break

    return title, date_str, category, body_html


def url_to_slug(url, idx):
    """URLから slug を生成する。shinobi-<連番3桁> 形式。"""
    return f"shinobi-{idx:03d}"


def main():
    print("=== 忍者ブログ クローラー開始 ===")
    print(f"保存先1: {BLOG_DIR}/articles/")
    print(f"保存先2: {TEMP_DIR}/articles/")
    print()

    # 全記事URLを収集（Page/1/ から Page/25/ まで）
    all_article_urls = []
    page = 1

    while True:
        list_url = f"{BASE_URL}/Page/{page}/"
        print(f"ページ収集中: {list_url}")
        try:
            page_html = fetch(list_url, sleep_sec=1.0)
        except Exception as e:
            print(f"  エラー: {e}")
            break

        urls = collect_article_urls_from_page(page_html)
        print(f"  記事URL: {len(urls)} 件")
        all_article_urls.extend(urls)

        if not has_next_page(page_html):
            print(f"  最終ページ (Page/{page}/)")
            break

        page += 1
        if page > 30:  # 安全上限
            print("警告: ページ数が30を超えました。中断します。")
            break

    # 重複除去（順序保持）
    seen = set()
    unique_urls = []
    for u in all_article_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    print(f"\n合計 {len(unique_urls)} 件の記事URLを収集しました。")
    print("各記事ページを取得します...\n")

    saved = 0
    skipped = 0
    errors = []

    for idx, art_url in enumerate(unique_urls, start=1):
        slug = url_to_slug(art_url, idx)

        # 既に保存済みならスキップ
        out_dir = os.path.join(BLOG_DIR, "articles", slug)
        if os.path.exists(os.path.join(out_dir, "meta.json")):
            print(f"スキップ (既存): {slug}")
            skipped += 1
            continue

        try:
            html = fetch(art_url, sleep_sec=1.0)
        except Exception as e:
            print(f"エラー (fetch): {art_url} - {e}")
            errors.append((art_url, str(e)))
            continue

        result = parse_article_page(html, art_url)
        if not result:
            print(f"エラー (parse): {art_url}")
            errors.append((art_url, "parse failed"))
            continue

        title, date_str, category, body_html = result
        tags = [category] if category else []

        if not date_str:
            print(f"警告: 日付が取得できませんでした: {art_url}")
            date_str = "2000-01-01"

        save_article(slug, title, date_str, tags, body_html, art_url)
        saved += 1

    print(f"\n=== 完了 ===")
    print(f"保存: {saved} 件")
    print(f"スキップ: {skipped} 件")
    if errors:
        print(f"エラー: {len(errors)} 件")
        for url, msg in errors:
            print(f"  {url}: {msg}")


if __name__ == "__main__":
    main()
