#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import posixpath
import re
import shutil
import unicodedata
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath
from typing import Any

from bs4 import BeautifulSoup
from lxml import etree
from markdownify import MarkdownConverter
from rapidfuzz.fuzz import ratio as fuzz_ratio

V4_EPUB = Path('/mnt/data/高善文文集V4.0.epub')
V2_EPUB = Path('/mnt/data/高善文文集V2.epub')
PACK = Path('/mnt/data/work_gaobo_v4/gaoshanwen_ai_knowledge_pack_v4_0')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def non_ws_len(text: str) -> int:
    return len(re.sub(r'\s+', '', text))


def cjk_text(text: str) -> str:
    return ''.join(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]', text))


def clean_title_key(text: str) -> str:
    text = unicodedata.normalize('NFKC', text).lower()
    text = re.sub(r'^\s*\d{4}[-年]\d{1,2}(?:[-月]\d{1,2}日?)?\s*', '', text)
    return re.sub(r'[\W_]+', '', text, flags=re.UNICODE)


def clean_body_key(text: str) -> str:
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))


def resolve_href(base: str, href: str) -> str:
    if not href:
        return ''
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), href.split('#', 1)[0]))


def yaml_scalar(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def safe_filename(text: str, max_len: int = 110) -> str:
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', text)
    text = re.sub(r'\s+', '_', text).strip('._ ')
    text = re.sub(r'_+', '_', text)
    return (text[:max_len].rstrip('._ ') or 'untitled')


class EpubMarkdownConverter(MarkdownConverter):
    """Markdown converter that preserves visible text and records image paths as comments.

    Image alt text is indexed separately and is not duplicated in the visible article body.
    """

    def __init__(self, source_xhtml: str, **options: Any):
        self.source_xhtml = source_xhtml
        super().__init__(**options)

    def convert_img(self, el, text, parent_tags):  # type: ignore[override]
        src = el.get('src', '')
        resolved = resolve_href(self.source_xhtml, src)
        alt = (el.get('alt') or '').replace('--', '—').strip()
        payload = f'epub://{resolved}' if resolved else src
        return f'\n<!-- EPUB_IMAGE src="{payload}" alt="{alt}" -->\n'


def is_heading_candidate(line: str) -> tuple[bool, int]:
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return False, 0
    if stripped.startswith(('#', '|', '>', '<!--', '- ', '* ')):
        return False, 0
    plain = stripped
    if plain.startswith('**') and plain.endswith('**') and plain.count('**') == 2:
        plain = plain[2:-2].strip()
    if plain.endswith(('。', '；', ';', '，', ',')) and len(plain) > 18:
        return False, 0
    top_patterns = [
        r'^(内容提要|提要|摘要|摘\s*要|引言|前言|绪论|目录|结论|结语|总结|说明|附录|关键词)\s*[:：]?',
        r'^第[一二三四五六七八九十百0-9]+[章节部分篇]\b',
        r'^[一二三四五六七八九十百]+[、．.]\s*\S+',
        r'^第[一二三四五六七八九十百0-9]+个(?:特征|事实|问题|方面|原因|阶段|结论)\s*[:：]?',
    ]
    sub_patterns = [
        r'^[（(][一二三四五六七八九十百0-9]+[）)]\s*\S+',
        r'^\d{1,2}\s*[、．.]\s*\S+',
        r'^\d{1,2}\.\d{1,2}\s*\S+',
    ]
    if any(re.match(p, plain) for p in top_patterns):
        return True, 2
    if any(re.match(p, plain) for p in sub_patterns):
        return True, 3
    if stripped.startswith('**') and stripped.endswith('**') and 2 <= len(plain) <= 40 and not re.search(r'[。！？!?]$', plain):
        return True, 3
    return False, 0


def promote_headings(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith('```'):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence:
            ok, level = is_heading_candidate(line)
            if ok:
                text = line.strip()
                if text.startswith('**') and text.endswith('**') and text.count('**') == 2:
                    text = text[2:-2].strip()
                line = '#' * level + ' ' + text
        out.append(line.rstrip())
    text = '\n'.join(out)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip() + '\n'


def markdown_visible_cjk(markdown: str) -> str:
    text = re.sub(r'<!--.*?-->', '', markdown, flags=re.S)
    text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    return cjk_text(text)


@dataclass
class Article:
    id: str
    title: str
    category: str
    internal_type: str
    date: str
    date_precision: str
    minutes: str
    excerpt: str
    source_xhtml: str
    source_plain: str
    markdown_body: str
    source_non_ws_chars: int
    source_cjk_chars: int
    source_body_sha256: str
    image_count: int
    image_alts: list[str]
    heading_count: int
    table_count: int
    chart_table_count: int
    filename: str = ''
    legacy_v3_ids: list[str] | None = None
    update_status: str = ''


def epub_metadata(z: zipfile.ZipFile) -> dict[str, str]:
    container = etree.fromstring(z.read('META-INF/container.xml'))
    cns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
    opf_path = container.xpath('string(//c:rootfile/@full-path)', namespaces=cns)
    opf = etree.fromstring(z.read(opf_path))
    ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
    return {
        'opf_path': opf_path,
        'identifier': opf.xpath('string(opf:metadata/dc:identifier)', namespaces=ns),
        'title': opf.xpath('string(opf:metadata/dc:title)', namespaces=ns),
        'language': opf.xpath('string(opf:metadata/dc:language)', namespaces=ns),
        'creator': opf.xpath('string(opf:metadata/dc:creator)', namespaces=ns),
        'contributor': opf.xpath('string(opf:metadata/dc:contributor)', namespaces=ns),
        'publisher': opf.xpath('string(opf:metadata/dc:publisher)', namespaces=ns),
        'description': opf.xpath('string(opf:metadata/dc:description)', namespaces=ns),
        'modified': opf.xpath('string(opf:metadata/opf:meta[@property="dcterms:modified"])', namespaces=ns),
        'package_version': opf.get('version', ''),
    }


def parse_articles(epub: Path, convert_markdown: bool = True) -> tuple[list[Article], dict[str, str]]:
    articles: list[Article] = []
    with zipfile.ZipFile(epub) as z:
        meta = epub_metadata(z)
        paths = sorted(
            [n for n in z.namelist() if re.match(r'OEBPS/text/article-\d+.*\.xhtml$', n)],
            key=lambda n: int(re.search(r'article-(\d+)-', PurePosixPath(n).name).group(1)),
        )
        for source_xhtml in paths:
            raw = z.read(source_xhtml)
            soup = BeautifulSoup(raw, 'xml')
            fm = re.search(r'article-(\d+)-([^-]+)-([^/]+?)\.xhtml$', PurePosixPath(source_xhtml).name)
            if not fm:
                raise ValueError(f'Cannot parse article path: {source_xhtml}')
            aid, internal_type = fm.group(1), fm.group(2)
            title_node = soup.find('h1') or soup.find('title')
            title = title_node.get_text(' ', strip=True) if title_node else f'Article {aid}'
            kicker = soup.find('p', class_='kicker')
            category = kicker.get_text(' ', strip=True) if kicker else internal_type
            meta_node = soup.find('p', class_='meta')
            meta_text = meta_node.get_text(' ', strip=True) if meta_node else ''
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', meta_text)
            date = date_match.group(1) if date_match else ''
            minutes_match = re.search(r'(\d+)\s*分钟', meta_text)
            minutes = minutes_match.group(1) if minutes_match else ''
            date_precision = 'day' if date else 'unknown'
            excerpt_node = soup.find('p', class_='excerpt')
            excerpt = excerpt_node.get_text(' ', strip=True) if excerpt_node else ''
            sec = soup.select_one('section.article-content')
            if sec is None:
                raise ValueError(f'No article-content section: {source_xhtml}')
            source_plain = sec.get_text('\n', strip=True)
            images = sec.find_all('img')
            image_alts = [(img.get('alt') or '').strip() for img in images if (img.get('alt') or '').strip()]
            if convert_markdown:
                converter = EpubMarkdownConverter(
                    source_xhtml,
                    heading_style='ATX',
                    bullets='-',
                    strip=['section'],
                    newline_style='BACKSLASH',
                )
                md_body = converter.convert(str(sec))
                md_body = promote_headings(md_body)
            else:
                md_body = ''
            articles.append(Article(
                id=f'{int(aid):03d}',
                title=title,
                category=category,
                internal_type=internal_type,
                date=date,
                date_precision=date_precision,
                minutes=minutes,
                excerpt=excerpt,
                source_xhtml=source_xhtml,
                source_plain=source_plain,
                markdown_body=md_body,
                source_non_ws_chars=non_ws_len(source_plain),
                source_cjk_chars=len(cjk_text(source_plain)),
                source_body_sha256=sha256_text(clean_body_key(source_plain)),
                image_count=len(images),
                image_alts=image_alts,
                heading_count=len(sec.find_all(re.compile('^h[2-6]$'))),
                table_count=len(sec.find_all('table')),
                chart_table_count=len(sec.find_all('table', class_='article-chart-table')),
            ))
    return articles, meta


def build_crosswalk(old_articles: list[Article], new_articles: list[Article]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    old_removed = {'011', '029', '037', '070'}
    manual_map = {
        '013': '051',
        '017': '012',
        '039': '074',
        '052': '079',
        '053': '079',
        '054': '080',
        '081': '127',
        '088': '092',
        '101': '040',
        '107': '047',
    }
    by_id = {a.id: a for a in new_articles}
    by_text: dict[str, list[Article]] = defaultdict(list)
    by_title: dict[str, list[Article]] = defaultdict(list)
    for a in new_articles:
        by_text[clean_body_key(a.source_plain)].append(a)
        by_title[clean_title_key(a.title)].append(a)

    rows: list[dict[str, Any]] = []
    by_v4: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for old in old_articles:
        target: Article | None = None
        relationship = ''
        note = ''
        if old.id in old_removed:
            relationship = 'removed_from_v4'
            note = 'V4.0 未收录该旧版条目。'
        elif old.id in manual_map:
            target = by_id[manual_map[old.id]]
        else:
            exact = by_text.get(clean_body_key(old.source_plain), [])
            if exact:
                target = max(exact, key=lambda a: fuzz_ratio(clean_title_key(old.title), clean_title_key(a.title)))
            else:
                same_title = by_title.get(clean_title_key(old.title), [])
                if same_title:
                    target = max(same_title, key=lambda a: fuzz_ratio(clean_body_key(old.source_plain), clean_body_key(a.source_plain)))
                else:
                    candidates = sorted(new_articles, key=lambda a: fuzz_ratio(clean_title_key(old.title), clean_title_key(a.title)), reverse=True)[:10]
                    best: tuple[float, Article, float, float] | None = None
                    for cand in candidates:
                        title_sim = fuzz_ratio(clean_title_key(old.title), clean_title_key(cand.title))
                        body_sim = fuzz_ratio(clean_body_key(old.source_plain)[:10000], clean_body_key(cand.source_plain)[:10000])
                        score = title_sim * 0.4 + body_sim * 0.6
                        if best is None or score > best[0]:
                            best = (score, cand, title_sim, body_sim)
                    if best and (best[2] >= 70 and best[3] >= 70):
                        target = best[1]
        if target is not None:
            title_sim = fuzz_ratio(clean_title_key(old.title), clean_title_key(target.title))
            body_sim = fuzz_ratio(clean_body_key(old.source_plain), clean_body_key(target.source_plain))
            exact_body = clean_body_key(old.source_plain) == clean_body_key(target.source_plain)
            if old.id == '052':
                relationship = 'legacy_abridged_consolidated'
                note = '旧版短稿/会议稿在 V4.0 中合并到完整稿。'
            elif exact_body:
                relationship = 'retained_exact'
            elif body_sim >= 97:
                relationship = 'retained_minor_revision'
            elif body_sim >= 80:
                relationship = 'retained_revised'
            else:
                relationship = 'legacy_version_consolidated'
            row = {
                'legacy_v3_id': old.id,
                'legacy_title': old.title,
                'v4_id': target.id,
                'v4_title': target.title,
                'relationship': relationship,
                'title_similarity_pct': f'{title_sim:.2f}',
                'body_similarity_pct': f'{body_sim:.2f}',
                'note': note,
            }
            rows.append(row)
            by_v4[target.id].append(row)
        else:
            rows.append({
                'legacy_v3_id': old.id,
                'legacy_title': old.title,
                'v4_id': '',
                'v4_title': '',
                'relationship': relationship or 'removed_from_v4',
                'title_similarity_pct': '',
                'body_similarity_pct': '',
                'note': note or '未找到足够可靠的 V4.0 对应条目。',
            })
    return rows, by_v4


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def write_articles(articles: list[Article], meta: dict[str, str], by_v4: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out_dir = PACK / '02_markdown_articles'
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    source_sha = sha256_file(V4_EPUB)
    index_rows: list[dict[str, Any]] = []
    combined_parts = [
        '# 高善文文集 V4.0｜全文合并',
        '',
        '> 来源：高善文文集V4.0.epub。文章顺序与 V4.0 EPUB 原生编号一致。汇编分类、摘要、阅读时间等属于 EPUB 汇编层元数据；正文保留源文可见文字。',
        '',
    ]
    for art in articles:
        legacy_rows = by_v4.get(art.id, [])
        legacy_ids = sorted({r['legacy_v3_id'] for r in legacy_rows})
        art.legacy_v3_ids = legacy_ids
        if not legacy_rows:
            status = 'new_in_v4'
        elif len(legacy_rows) > 1:
            status = 'consolidated_from_v3'
        elif legacy_rows[0]['relationship'] == 'retained_exact':
            status = 'retained_exact'
        else:
            status = 'retained_revised'
        art.update_status = status
        date_part = f'_{art.date}' if art.date else ''
        filename = f'{art.id}{date_part}_{safe_filename(art.title)}.md'
        art.filename = filename
        front = {
            'id': art.id,
            'title': art.title,
            'thematic_category': art.category,
            'content_type': art.internal_type,
            'date': art.date,
            'date_precision': art.date_precision,
            'minutes': art.minutes,
            'source_file': art.source_xhtml,
            'source_epub': V4_EPUB.name,
            'source_epub_sha256': source_sha,
            'source_epub_modified': meta.get('modified', ''),
            'source_body_sha256': art.source_body_sha256,
            'non_ws_chars': art.source_non_ws_chars,
            'cjk_chars': art.source_cjk_chars,
            'image_count': art.image_count,
            'legacy_v3_ids': legacy_ids,
            'update_status': status,
        }
        yaml_lines = ['---'] + [f'{k}: {yaml_scalar(v)}' for k, v in front.items()] + ['---', '']
        date_display = art.date or '未注明'
        minutes_display = f'{art.minutes} 分钟' if art.minutes else '未注明'
        doc = '\n'.join(yaml_lines)
        doc += f'# {art.title}\n\n'
        doc += f'> 主题分类：{art.category}；内容类型：{art.internal_type}；日期：{date_display}；阅读时间：{minutes_display}；V4文章ID：{art.id}\n\n'
        if art.excerpt:
            doc += '## EPUB 摘要/引文\n\n' + art.excerpt.strip() + '\n\n'
        doc += '## 正文\n\n' + art.markdown_body.strip() + '\n'
        path = out_dir / filename
        path.write_text(doc, encoding='utf-8')
        md_cjk = markdown_visible_cjk(art.markdown_body)
        src_cjk = cjk_text(art.source_plain)
        sim = SequenceMatcher(None, src_cjk, md_cjk).ratio() if src_cjk or md_cjk else 1.0
        index_rows.append({
            'id': art.id,
            'title': art.title,
            'category': art.category,
            'content_type': art.internal_type,
            'date': art.date,
            'date_precision': art.date_precision,
            'minutes': art.minutes,
            'file': f'02_markdown_articles/{filename}',
            'source_file': art.source_xhtml,
            'source_epub': V4_EPUB.name,
            'source_epub_sha256': source_sha,
            'non_ws_chars': art.source_non_ws_chars,
            'cjk_chars': art.source_cjk_chars,
            'image_count': art.image_count,
            'image_alts': ' | '.join(art.image_alts),
            'excerpt': art.excerpt,
            'legacy_v3_ids': ';'.join(legacy_ids),
            'update_status': status,
            'source_body_sha256': art.source_body_sha256,
            'markdown_file_sha256': sha256_file(path),
            'markdown_body_cjk_similarity': f'{sim:.8f}',
            'heading_count_source': art.heading_count,
            'table_count_source': art.table_count,
            'chart_table_count_source': art.chart_table_count,
        })
        combined_parts.extend([
            '',
            '---',
            '',
            f'# {art.id}｜{date_display}｜{art.title}',
            '',
            f'> 主题分类：{art.category}；内容类型：{art.internal_type}；源文件：{art.source_xhtml}',
            '',
        ])
        if art.excerpt:
            combined_parts.extend(['## EPUB 摘要/引文', '', art.excerpt.strip(), ''])
        combined_parts.extend(['## 正文', '', art.markdown_body.strip(), ''])
    combined = '\n'.join(combined_parts).rstrip() + '\n'
    (out_dir / '00_高善文文集V4.0_全文合并.md').write_text(combined, encoding='utf-8')
    return index_rows


def main() -> int:
    print('Parsing V4.0 EPUB...')
    v4_articles, v4_meta = parse_articles(V4_EPUB, convert_markdown=True)
    print('Parsing V2 EPUB for crosswalk...')
    v2_articles, _ = parse_articles(V2_EPUB, convert_markdown=False)
    crosswalk, by_v4 = build_crosswalk(v2_articles, v4_articles)
    index_rows = write_articles(v4_articles, v4_meta, by_v4)

    idx_dir = PACK / '05_indexes'
    qual_dir = PACK / '06_quality'
    idx_dir.mkdir(exist_ok=True)
    qual_dir.mkdir(exist_ok=True)
    base_fields = [
        'id','title','category','content_type','date','date_precision','minutes','file','source_file',
        'source_epub','source_epub_sha256','non_ws_chars','cjk_chars','image_count','image_alts','excerpt',
        'legacy_v3_ids','update_status','source_body_sha256','markdown_file_sha256',
        'markdown_body_cjk_similarity','heading_count_source','table_count_source','chart_table_count_source',
    ]
    write_csv(idx_dir / 'article_index.csv', index_rows, base_fields)
    write_csv(idx_dir / 'legacy_v3_to_v4_map.csv', crosswalk, [
        'legacy_v3_id','legacy_title','v4_id','v4_title','relationship','title_similarity_pct','body_similarity_pct','note',
    ])

    fidelity_rows = []
    for r in index_rows:
        fidelity_rows.append({
            'article_id': r['id'],
            'title': r['title'],
            'source_cjk_chars': r['cjk_chars'],
            'markdown_body_cjk_similarity': r['markdown_body_cjk_similarity'],
            'passes_0_99': str(float(r['markdown_body_cjk_similarity']) >= 0.99).lower(),
            'source_body_sha256': r['source_body_sha256'],
            'markdown_file_sha256': r['markdown_file_sha256'],
        })
    write_csv(qual_dir / 'epub_text_fidelity.csv', fidelity_rows, list(fidelity_rows[0].keys()))

    status_counts: dict[str, int] = defaultdict(int)
    for r in index_rows:
        status_counts[r['update_status']] += 1
    rel_counts: dict[str, int] = defaultdict(int)
    for r in crosswalk:
        rel_counts[r['relationship']] += 1
    summary = {
        'source_epub': V4_EPUB.name,
        'source_epub_sha256': sha256_file(V4_EPUB),
        'source_epub_size_bytes': V4_EPUB.stat().st_size,
        'source_epub_metadata': v4_meta,
        'v4_article_count': len(v4_articles),
        'legacy_v3_article_count': len(v2_articles),
        'v4_status_counts': dict(status_counts),
        'legacy_relationship_counts': dict(rel_counts),
        'v4_categories': dict(sorted({a.category: sum(x.category == a.category for x in v4_articles) for a in v4_articles}.items())),
        'date_min': min(a.date for a in v4_articles if a.date),
        'date_max': max(a.date for a in v4_articles if a.date),
        'dated_article_count': sum(bool(a.date) for a in v4_articles),
        'undated_article_count': sum(not a.date for a in v4_articles),
        'source_non_ws_chars': sum(a.source_non_ws_chars for a in v4_articles),
        'source_cjk_chars': sum(a.source_cjk_chars for a in v4_articles),
        'articles_with_images': sum(a.image_count > 0 for a in v4_articles),
        'image_reference_count': sum(a.image_count for a in v4_articles),
        'minimum_markdown_body_cjk_similarity': min(float(r['markdown_body_cjk_similarity']) for r in index_rows),
        'average_markdown_body_cjk_similarity': sum(float(r['markdown_body_cjk_similarity']) for r in index_rows) / len(index_rows),
    }
    (qual_dir / 'source_update_diff_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
