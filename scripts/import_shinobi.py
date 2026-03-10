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
import shutil
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

def build_article_html(title, date, tags, body_html, source_url, slug):
    tags_html = "".join(f'<span class="article-tag">{t}</span>' for t in tags)
    import html as html_lib
    source_html = (
        f'<div class="source-link">初出: '
        f'<a href="{source_url}" target="_blank" rel="noopener">'
        f"Shinobiブログ (orangeness)</a></div>"
    )
    cover = "assets/covers/shinobi-default.png"
    og_image = f"{SITE_URL}/{cover}"
    cover_src = f"../../{cover}"
    desc_text = strip_tags(body_html).strip().replace("\n", " ")
    desc_text = re.sub(r"\s+", " ", desc_text)[:80] + "..."
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
            f'  <meta property="og:url" content="{SITE_URL}/articles/{slug}/">',
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
    cover = "assets/covers/shinobi-default.png"
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

    # カバー画像の準備
    cover_src = os.path.join(BLOG_DIR, "assets", "covers", "qiita-default.png")
    cover_dst = os.path.join(BLOG_DIR, "assets", "covers", "shinobi-default.png")
    cover_dst_temp = os.path.join(TEMP_DIR, "assets", "covers", "shinobi-default.png")

    if not os.path.exists(cover_dst):
        if os.path.exists(cover_src):
            shutil.copy2(cover_src, cover_dst)
            print(f"カバー画像コピー: {cover_dst}")
        else:
            print(f"警告: カバー画像ソースが見つかりません: {cover_src}")

    if not os.path.exists(cover_dst_temp):
        os.makedirs(os.path.dirname(cover_dst_temp), exist_ok=True)
        if os.path.exists(cover_src):
            shutil.copy2(cover_src, cover_dst_temp)
            print(f"カバー画像コピー (temp): {cover_dst_temp}")

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
