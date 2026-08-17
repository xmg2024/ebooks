#!/usr/bin/env python3
"""Inspect the source EPUB and generate reproducible structure/article/image indexes."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, posixpath, re, zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from bs4 import BeautifulSoup
from lxml import etree
from PIL import Image


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def resolve_href(base: str, href: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), href.split('#',1)[0]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('epub', type=Path)
    ap.add_argument('pack', type=Path)
    args = ap.parse_args()
    epub=args.epub; root=args.pack
    idx=root/'05_indexes'; qual=root/'06_quality'
    idx.mkdir(exist_ok=True); qual.mkdir(exist_ok=True)

    with zipfile.ZipFile(epub) as z:
        names=z.namelist(); name_set=set(names); infos=z.infolist()
        container=etree.fromstring(z.read('META-INF/container.xml'))
        cns={'c':'urn:oasis:names:tc:opendocument:xmlns:container'}
        opf_path=container.xpath('string(//c:rootfile/@full-path)',namespaces=cns)
        opf=etree.fromstring(z.read(opf_path))
        ns={'opf':'http://www.idpf.org/2007/opf','dc':'http://purl.org/dc/elements/1.1/'}
        metadata={
            'identifier':opf.xpath('string(opf:metadata/dc:identifier)',namespaces=ns),
            'title':opf.xpath('string(opf:metadata/dc:title)',namespaces=ns),
            'language':opf.xpath('string(opf:metadata/dc:language)',namespaces=ns),
            'creator':opf.xpath('string(opf:metadata/dc:creator)',namespaces=ns),
            'contributor':opf.xpath('string(opf:metadata/dc:contributor)',namespaces=ns),
            'publisher':opf.xpath('string(opf:metadata/dc:publisher)',namespaces=ns),
            'description':opf.xpath('string(opf:metadata/dc:description)',namespaces=ns),
            'modified':opf.xpath('string(opf:metadata/opf:meta[@property="dcterms:modified"])',namespaces=ns),
            'package_version':opf.get('version',''),
        }
        manifest=[]; manifest_by_id={}
        for item in opf.xpath('opf:manifest/opf:item',namespaces=ns):
            row={'id':item.get('id',''),'href':item.get('href',''),'media_type':item.get('media-type',''),'properties':item.get('properties','')}
            manifest.append(row); manifest_by_id[row['id']]=row
        spine_ids=[x.get('idref','') for x in opf.xpath('opf:spine/opf:itemref',namespaces=ns)]
        opf_dir=posixpath.dirname(opf_path)
        spine_paths=[posixpath.normpath(posixpath.join(opf_dir,manifest_by_id[x]['href'])) for x in spine_ids if x in manifest_by_id]

        article_paths=sorted([n for n in names if re.match(r'OEBPS/text/article-\d+.*\.xhtml$',n)])
        category_paths=sorted([n for n in names if re.match(r'OEBPS/text/category-.*\.xhtml$',n)])
        image_paths=sorted([n for n in names if n.startswith('OEBPS/images/') and not n.endswith('/')])

        article_rows=[]; image_ref_rows=[]; internal_ref_rows=[]
        for n in article_paths:
            raw=z.read(n); soup=BeautifulSoup(raw,'xml')
            m=re.search(r'article-(\d+)-([^-]+)-(\d{4}-\d{2}-\d{2}|undated)',PurePosixPath(n).name)
            aid=int(m.group(1)); internal_type=m.group(2); filename_date=m.group(3)
            title=(soup.find('h1') or soup.find('title')).get_text(' ',strip=True)
            kicker=soup.find('p',class_='kicker')
            category_display=kicker.get_text(' ',strip=True) if kicker else internal_type
            meta=soup.find('p',class_='meta'); meta_text=meta.get_text(' ',strip=True) if meta else ''
            dm=re.search(r'(\d{4}-\d{2}-\d{2})',meta_text)
            display_date=dm.group(1) if dm else ''
            rm=re.search(r'(\d+)\s*分钟',meta_text); reading_minutes=int(rm.group(1)) if rm else ''
            excerpt=soup.find('p',class_='excerpt'); excerpt_text=excerpt.get_text(' ',strip=True) if excerpt else ''
            sec=soup.select_one('section.article-content')
            text=sec.get_text('\n',strip=True) if sec else ''
            non_ws=len(re.sub(r'\s+','',text)); cjk=len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]',text))
            headings=soup.find_all(re.compile('^h[2-6]$'))
            tables=soup.find_all('table'); chart_tables=soup.find_all('table',class_='article-chart-table')
            imgs=soup.find_all('img'); unique_src=set()
            footrefs=soup.find_all(attrs={'role':'doc-noteref'})
            # full date precision: filename/display; partial month titles remain partial.
            if display_date or filename_date!='undated': precision='day'
            elif re.search(r'\b\d{4}-\d{2}\b',title): precision='month'
            else: precision='unknown'
            for seq,img in enumerate(imgs,1):
                src=img.get('src',''); resolved=resolve_href(n,src) if src else ''
                unique_src.add(resolved)
                parent_table=img.find_parent('table')
                fig_no=parent_table.get('data-figure-number','') if parent_table else ''
                th=parent_table.find('th') if parent_table else None
                caption=th.get_text(' ',strip=True) if th else ''
                source_text=''
                if parent_table:
                    trs=parent_table.find_all('tr')
                    if len(trs)>=2:
                        candidate=trs[-1].get_text(' ',strip=True)
                        if candidate and candidate!=caption: source_text=candidate
                exists=resolved in name_set
                image_ref_rows.append({
                    'article_id':f'{aid:03d}','title':title,'image_sequence':seq,'source_xhtml':n,
                    'src':src,'resolved_path':resolved,'exists_in_epub':str(exists).lower(),
                    'alt':img.get('alt',''),'figure_number':fig_no,'caption':caption,'source_note':source_text,
                })
                internal_ref_rows.append({'source_file':n,'reference_type':'image','href':src,'resolved_path':resolved,'exists':str(exists).lower()})
            article_rows.append({
                'article_id':f'{aid:03d}','title':title,'category_display':category_display,'internal_type':internal_type,
                'epub_xhtml':n,'filename_date':filename_date if filename_date!='undated' else '',
                'display_date':display_date,'date_precision':precision,'reading_minutes':reading_minutes,
                'excerpt':excerpt_text,'non_ws_chars':non_ws,'cjk_chars':cjk,'heading_count_h2_h6':len(headings),
                'table_count':len(tables),'chart_table_count':len(chart_tables),'image_reference_count':len(imgs),
                'unique_image_file_count':len(unique_src),'footnote_reference_count':len(footrefs),
            })
            # all anchors in article
            for a in soup.find_all('a'):
                href=a.get('href','')
                if href and not href.startswith(('http:','https:','mailto:','#')):
                    resolved=resolve_href(n,href)
                    exists=resolved in name_set
                    internal_ref_rows.append({'source_file':n,'reference_type':'link','href':href,'resolved_path':resolved,'exists':str(exists).lower()})

        image_rows=[]; image_hash_groups=defaultdict(list)
        for n in image_paths:
            data=z.read(n); sha=sha256_bytes(data); image_hash_groups[sha].append(n)
            width=height=mode=fmt=''
            try:
                im=Image.open(io.BytesIO(data)); width=im.width; height=im.height; mode=im.mode; fmt=im.format
            except Exception:
                pass
            image_rows.append({'path':n,'size_bytes':len(data),'sha256':sha,'format':fmt,'mode':mode,'width':width,'height':height})

        # manifest href integrity
        for item in manifest:
            resolved=posixpath.normpath(posixpath.join(opf_dir,item['href']))
            internal_ref_rows.append({'source_file':opf_path,'reference_type':'manifest','href':item['href'],'resolved_path':resolved,'exists':str(resolved in name_set).lower()})
        # spine integrity
        for sid in spine_ids:
            exists=sid in manifest_by_id
            internal_ref_rows.append({'source_file':opf_path,'reference_type':'spine_idref','href':sid,'resolved_path':manifest_by_id.get(sid,{}).get('href',''),'exists':str(exists).lower()})

        write_csv(idx/'epub_article_inventory.csv',article_rows,list(article_rows[0].keys()))
        write_csv(idx/'epub_image_reference_index.csv',image_ref_rows,list(image_ref_rows[0].keys()))
        write_csv(idx/'epub_image_asset_inventory.csv',image_rows,list(image_rows[0].keys()))
        write_csv(qual/'epub_internal_reference_checks.csv',internal_ref_rows,list(internal_ref_rows[0].keys()))

        media_counts=Counter(x['media_type'] for x in manifest)
        category_counts=Counter(x['category_display'] for x in article_rows)
        date_counts=Counter(x['date_precision'] for x in article_rows)
        dup_groups=[v for v in image_hash_groups.values() if len(v)>1]
        summary={
            'source_file':epub.name,'source_size_bytes':epub.stat().st_size,'source_sha256':sha256_file(epub),
            'epub_metadata':metadata,'zip_entry_count':len(names),'manifest_item_count':len(manifest),'spine_item_count':len(spine_ids),
            'spine_paths_all_exist':all(x in name_set for x in spine_paths),
            'mimetype_is_first_entry':bool(infos and infos[0].filename=='mimetype'),
            'mimetype_is_uncompressed':bool(infos and infos[0].compress_type==zipfile.ZIP_STORED),
            'mimetype_value':z.read('mimetype').decode('ascii','replace'),
            'xhtml_count':sum(x['media_type']=='application/xhtml+xml' for x in manifest),
            'article_count':len(article_rows),'category_page_count':len(category_paths),
            'category_article_counts':dict(category_counts),'internal_type_counts':dict(Counter(x['internal_type'] for x in article_rows)),
            'date_precision_counts':dict(date_counts),
            'article_non_ws_chars':sum(x['non_ws_chars'] for x in article_rows),'article_cjk_chars':sum(x['cjk_chars'] for x in article_rows),
            'article_length_non_ws_min':min(x['non_ws_chars'] for x in article_rows),
            'article_length_non_ws_median':sorted(x['non_ws_chars'] for x in article_rows)[len(article_rows)//2],
            'article_length_non_ws_max':max(x['non_ws_chars'] for x in article_rows),
            'article_heading_count_h2_h6':sum(x['heading_count_h2_h6'] for x in article_rows),
            'article_table_count':sum(x['table_count'] for x in article_rows),'article_chart_table_count':sum(x['chart_table_count'] for x in article_rows),
            'image_asset_count':len(image_rows),'image_reference_count':len(image_ref_rows),
            'articles_with_images':sum(x['image_reference_count']>0 for x in article_rows),
            'image_media_counts':dict(Counter(x['format'] for x in image_rows)),
            'image_total_bytes':sum(x['size_bytes'] for x in image_rows),
            'duplicate_image_hash_group_count':len(dup_groups),'files_in_duplicate_image_groups':sum(len(x) for x in dup_groups),
            'manifest_media_type_counts':dict(media_counts),
            'internal_reference_count':len(internal_ref_rows),
            'missing_internal_reference_count':sum(x['exists']!='true' for x in internal_ref_rows),
            'validation_scope_note':'完成 ZIP 完整性、mimetype、manifest、spine、文章链接与图片引用检查；未运行独立的 DAISY/W3C EPUBCheck。',
        }
        (idx/'epub_structure_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
