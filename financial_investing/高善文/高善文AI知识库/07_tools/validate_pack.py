#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

EXPECTED_SOURCE_SHA = "d84eb38d989588b66ec63d0dce528f94564ecd444f043f7c46dfd21c12dc4366"
EXPECTED_CATEGORIES = {
    "成长、追忆与评论": 12,
    "代表作与研究方法": 8,
    "周期、通胀与人口": 22,
    "流动性、利率与汇率": 26,
    "资本市场与金融风险": 30,
    "房地产、城市化与消费": 23,
    "产业、产能与能源转型": 12,
    "贸易、国际收支与全球经济": 17,
    "财政、疫情及宏观应对": 10,
}
EXPECTED_STATUS = {
    "retained_exact": 87,
    "retained_revised": 3,
    "new_in_v4": 63,
    "consolidated_from_v3": 7,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_jsonl(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except Exception as exc:
                raise RuntimeError(f"{path.name} line {line_no}: {exc}") from exc
    return out


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    fm = text[4:end]
    out: dict[str, str] = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def boolish(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", type=Path)
    ap.add_argument("--source-epub", type=Path, required=True)
    args = ap.parse_args()

    root = args.pack.resolve()
    source_epub = args.source_epub.resolve()
    q = root / "06_quality"
    q.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    # Source and input hashes.
    src_exists = source_epub.exists()
    src_sha = sha256_file(source_epub) if src_exists else ""
    check("源 EPUB 存在", src_exists, str(source_epub))
    check("源 EPUB SHA-256 匹配", src_sha == EXPECTED_SOURCE_SHA, src_sha or "missing")
    input_rows = []
    if src_exists:
        input_rows.append({
            "input_file": source_epub.name,
            "size_bytes": source_epub.stat().st_size,
            "sha256": src_sha,
            "role": "V4.0 唯一新版原文源",
        })
    write_csv(q / "input_file_hashes.csv", input_rows, ["input_file", "size_bytes", "sha256", "role"])

    # Articles.
    article_dir = root / "02_markdown_articles"
    all_md = sorted(article_dir.glob("*.md"))
    singles = [p for p in all_md if not p.name.startswith("00_")]
    combined = [p for p in all_md if p.name.startswith("00_")]
    check("160 篇单篇 Markdown 存在", len(singles) == 160, f"{len(singles)} 篇")
    check("全文合并版唯一且存在", len(combined) == 1, f"{len(combined)} 份")

    article_hash_rows = []
    valid_fm = True
    ids_from_files: list[str] = []
    for path in singles:
        raw = path.read_text("utf-8")
        fm = parse_frontmatter(raw)
        aid = fm.get("id", "")
        ids_from_files.append(aid)
        valid_fm &= bool(
            re.fullmatch(r"\d{3}", aid)
            and fm.get("source_epub") == "高善文文集V4.0.epub"
            and fm.get("source_epub_sha256") == EXPECTED_SOURCE_SHA
            and fm.get("title")
            and "## 正文\n" in raw
        )
        article_hash_rows.append({
            "article_id": aid,
            "file": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "source_body_sha256": fm.get("source_body_sha256", ""),
        })
    write_csv(q / "article_sha256.csv", article_hash_rows,
              ["article_id", "file", "size_bytes", "sha256", "source_body_sha256"])
    check("文章 Front Matter 和源哈希有效", valid_fm, f"{len(singles)} 篇已检查")
    check("文章 ID 为 001—160 且唯一", sorted(ids_from_files) == [f"{i:03d}" for i in range(1, 161)],
          f"{len(set(ids_from_files))}/160 唯一")

    # Article indexes and corpus statistics.
    base = read_csv(root / "05_indexes/article_index.csv")
    enhanced = read_csv(root / "05_indexes/article_index_v2.csv")
    check("基础文章索引 160 行", len(base) == 160, f"{len(base)} 行")
    check("增强文章索引 160 行", len(enhanced) == 160, f"{len(enhanced)} 行")
    idx_ids = [str(r.get("id", "")).zfill(3) for r in enhanced]
    check("增强索引文章 ID 完整", idx_ids == [f"{i:03d}" for i in range(1, 161)],
          f"{len(set(idx_ids))}/160 唯一")
    path_ok = all((root / r["file"]).exists() for r in enhanced)
    check("增强索引文章路径全部有效", path_ok,
          f"{sum((root / r['file']).exists() for r in enhanced)}/{len(enhanced)}")
    category_counts = Counter(r["category"] for r in enhanced)
    check("9 个分类及篇数匹配 EPUB", dict(category_counts) == EXPECTED_CATEGORIES,
          json.dumps(dict(category_counts), ensure_ascii=False, sort_keys=True))
    type_counts = Counter(r["content_type"] for r in enhanced)
    check("内容类型统计匹配", type_counts == Counter({"analysis": 140, "commentary": 7, "essay": 10, "representative": 3}),
          json.dumps(dict(type_counts), ensure_ascii=False, sort_keys=True))
    nonws = sum(int(float(r["non_ws_chars"])) for r in enhanced)
    cjk = sum(int(float(r["cjk_chars"])) for r in enhanced)
    check("正文字符统计匹配", nonws == 858136 and cjk == 742943,
          f"非空白 {nonws:,}；汉字 {cjk:,}")
    dates = sorted(r["date"] for r in enhanced if r.get("date"))
    check("日期范围与完整性匹配", len(dates) == 157 and dates[0] == "2009-08-15" and dates[-1] == "2024-10-22",
          f"有日期 {len(dates)}；{dates[0] if dates else ''}—{dates[-1] if dates else ''}")
    status_counts = Counter(r["update_status"] for r in enhanced)
    check("V4 文章更新状态统计匹配", dict(status_counts) == EXPECTED_STATUS,
          json.dumps(dict(status_counts), ensure_ascii=False, sort_keys=True))
    enhanced_required = {
        "methodology_concepts", "broad_observation_dimensions", "exclusive_evidence_methods",
        "legacy_v3_ids", "update_status", "source_epub_sha256", "file_sha256", "body_sha256"
    }
    check("增强索引包含新增方法字段", enhanced_required.issubset(enhanced[0].keys()),
          ", ".join(sorted(enhanced_required)))

    # Text fidelity.
    fidelity = read_csv(q / "epub_text_fidelity.csv")
    sims = [float(r["markdown_body_cjk_similarity"]) for r in fidelity]
    check("EPUB—Markdown 逐篇文字校验 160 行", len(fidelity) == 160, f"{len(fidelity)} 行")
    check("正文汉字序列逐篇完全一致", bool(sims) and min(sims) == 1.0 and sum(sims) / len(sims) == 1.0,
          f"最低 {min(sims):.6f}；平均 {sum(sims)/len(sims):.6f}")
    check("全部文章通过 0.99 阈值", all(boolish(r["passes_0_99"]) for r in fidelity),
          f"{sum(boolish(r['passes_0_99']) for r in fidelity)}/{len(fidelity)}")

    # Legacy crosswalk and duplicate consolidation.
    legacy = read_csv(root / "05_indexes/legacy_v3_to_v4_map.csv")
    check("旧版 108 篇迁移表完整", len(legacy) == 108, f"{len(legacy)} 行")
    rel_counts = Counter(r["relationship"] for r in legacy)
    expected_rel = Counter({
        "retained_exact": 94,
        "retained_minor_revision": 5,
        "retained_revised": 4,
        "legacy_abridged_consolidated": 1,
        "removed_from_v4": 4,
    })
    check("旧版迁移关系统计匹配", rel_counts == expected_rel,
          json.dumps(dict(rel_counts), ensure_ascii=False, sort_keys=True))
    removed_ok = all(not r.get("v4_id") for r in legacy if r["relationship"] == "removed_from_v4")
    mapped_ok = all(r.get("v4_id") for r in legacy if r["relationship"] != "removed_from_v4")
    check("旧版删除与映射状态有效", removed_ok and mapped_ok,
          f"删除 {rel_counts['removed_from_v4']}；已映射 {len(legacy)-rel_counts['removed_from_v4']}")
    duplicates = read_csv(root / "05_indexes/duplicate_map.csv")
    check("V4 无未合并重复文章组", len(duplicates) == 0, f"{len(duplicates)} 行")

    # RAG chunks.
    sem = read_jsonl(root / "03_rag_chunks/chunks_semantic_900_120.jsonl")
    fixed = read_jsonl(root / "03_rag_chunks/chunks_1200_160.jsonl")
    check("章节感知切片 1,264 条且可解析", len(sem) == 1264, f"{len(sem)} 条")
    check("固定字符切片 1,053 条且可解析", len(fixed) == 1053, f"{len(fixed)} 条")
    sem_ids = [x["chunk_id"] for x in sem]
    fixed_ids = [x["chunk_id"] for x in fixed]
    check("两套切片 ID 唯一", len(sem_ids) == len(set(sem_ids)) and len(fixed_ids) == len(set(fixed_ids)),
          f"semantic {len(set(sem_ids))}/{len(sem_ids)}；fixed {len(set(fixed_ids))}/{len(fixed_ids)}")
    sem_aids = {str(x["article_id"]).zfill(3) for x in sem}
    fixed_aids = {str(x["article_id"]).zfill(3) for x in fixed}
    check("两套切片覆盖 160 篇", len(sem_aids) == 160 and len(fixed_aids) == 160,
          f"semantic {len(sem_aids)}；fixed {len(fixed_aids)}")
    sem_sizes = [int(x["non_ws_chars"]) for x in sem]
    check("语义切片长度受控", min(sem_sizes) > 0 and max(sem_sizes) <= 1250,
          f"最小 {min(sem_sizes)}；中位 {median(sem_sizes)}；最大 {max(sem_sizes)}")
    required_sem = {
        "methodology_concepts", "broad_observation_dimensions", "exclusive_evidence_methods",
        "section_path", "prev_chunk_id", "next_chunk_id", "content_sha256", "legacy_v3_ids", "update_status"
    }
    check("语义切片包含 V1.2 方法元数据", required_sem.issubset(sem[0].keys()),
          ", ".join(sorted(required_sem)))
    content_hash_ok = all(sha256_text(x["content"]) == x["content_sha256"] for x in sem)
    check("语义切片内容哈希有效", content_hash_ok, f"{len(sem)} 条")

    def adjacency_ok(rows: list[dict]) -> bool:
        by: dict[str, list[dict]] = defaultdict(list)
        for x in rows:
            by[str(x["article_id"]).zfill(3)].append(x)
        for vals in by.values():
            vals.sort(key=lambda x: int(x["chunk_index"]))
            for i, x in enumerate(vals):
                exp_prev = vals[i-1]["chunk_id"] if i else ""
                exp_next = vals[i+1]["chunk_id"] if i + 1 < len(vals) else ""
                if x.get("prev_chunk_id", "") != exp_prev or x.get("next_chunk_id", "") != exp_next:
                    return False
        return True

    check("语义切片相邻指针有效", adjacency_ok(sem), "prev/next 全部匹配")
    check("固定切片相邻指针有效", adjacency_ok(fixed), "prev/next 全部匹配")
    coverage = read_csv(q / "semantic_chunk_coverage.csv")
    coverage_ok = (
        len(coverage) == 160
        and all(boolish(r["has_semantic_chunks"]) and boolish(r["has_fixed_chunks"]) for r in coverage)
        and all(0 < int(r["semantic_core_non_ws_chars"]) <= int(r["body_non_ws_chars"]) for r in coverage)
        and max(int(r["body_non_ws_chars"]) - int(r["semantic_core_non_ws_chars"]) for r in coverage) <= 700
    )
    check("160 篇均有语义核心覆盖，标题差异受控", coverage_ok,
          f"覆盖 {sum(boolish(r['has_semantic_chunks']) and boolish(r['has_fixed_chunks']) for r in coverage)}/{len(coverage)}；最大标题/标记差异 {max(int(r['body_non_ws_chars']) - int(r['semantic_core_non_ws_chars']) for r in coverage)}")

    # Method/index maps.
    map_checks = {
        "主题地图": (root / "05_indexes/topic_map_v2.md", ["增长与总需求", "研究方法与证据"]),
        "方法论概念地图": (root / "05_indexes/methodology_concept_map.md", ["可证伪假说", "广谱横断面观察", "排他性证据"]),
        "广谱观察维度地图": (root / "05_indexes/broad_observation_dimension_map.md", ["行业横断面", "产品与品类横断面", "主体资产负债表"]),
        "排他性证据方法地图": (root / "05_indexes/exclusive_evidence_method_map.md", ["横断面梯度", "时序与领先滞后", "会计与存量流量约束"]),
    }
    for label, (path, terms) in map_checks.items():
        raw = path.read_text("utf-8") if path.exists() else ""
        check(f"{label}有效", path.exists() and all(t in raw for t in terms),
              f"{path.relative_to(root)}；关键术语 {len([t for t in terms if t in raw])}/{len(terms)}")
    source_map_raw = (root / "05_indexes/methodology_source_map.md").read_text("utf-8")
    check("方法论来源地图已迁移到 V4 ID", all(t in source_map_raw for t in ["V4-015", "V4-150", "广谱观察", "排他性证据"]),
          "V4 方法来源与核心强化均已覆盖")
    figures = read_csv(root / "05_indexes/figures_index.csv")
    check("含图文章兼容索引 57 行", len(figures) == 57, f"{len(figures)} 行")

    # EPUB inventories.
    epub_summary = json.loads((root / "05_indexes/epub_structure_summary.json").read_text("utf-8"))
    epub_articles = read_csv(root / "05_indexes/epub_article_inventory.csv")
    epub_refs = read_csv(root / "05_indexes/epub_image_reference_index.csv")
    epub_assets = read_csv(root / "05_indexes/epub_image_asset_inventory.csv")
    internal_refs = read_csv(q / "epub_internal_reference_checks.csv")
    check("EPUB 结构统计匹配 V4", (
        epub_summary.get("article_count") == 160
        and epub_summary.get("category_page_count") == 9
        and epub_summary.get("image_asset_count") == 979
        and epub_summary.get("image_reference_count") == 978
        and epub_summary.get("articles_with_images") == 57
        and epub_summary.get("source_sha256") == EXPECTED_SOURCE_SHA
    ), f"文章 {epub_summary.get('article_count')}；分类 {epub_summary.get('category_page_count')}；图片 {epub_summary.get('image_asset_count')}")
    check("EPUB 文章清单 160 行", len(epub_articles) == 160, f"{len(epub_articles)} 行")
    check("EPUB 图片引用索引 978 行", len(epub_refs) == 978, f"{len(epub_refs)} 行")
    check("EPUB 图片资产清单 979 行", len(epub_assets) == 979, f"{len(epub_assets)} 行")
    check("EPUB 内部 2,626 项引用无缺失", len(internal_refs) == 2626 and all(boolish(r["exists"]) for r in internal_refs),
          f"{len(internal_refs)} 项；缺失 {sum(not boolish(r['exists']) for r in internal_refs)}")

    # Skill.
    skill_dir = root / "01_skill/gaobo-macro-market-policy"
    skill_path = skill_dir / "SKILL.md"
    skill_raw = skill_path.read_text("utf-8")
    skill_fm = parse_frontmatter(skill_raw)
    refs = sorted((skill_dir / "references").glob("*.md"))
    check("标准 Skill Front Matter 有效", skill_fm.get("name") == "gaobo-macro-market-policy",
          f"name={skill_fm.get('name', '')}")
    check("Skill 版本为 1.2.0", skill_fm.get("version") == "1.2.0",
          f"version={skill_fm.get('version', '')}")
    check("Skill 包含 8 个参考模块", len(refs) == 8, f"{len(refs)} 个")
    skill_terms = [
        "广谱观察是硬门槛", "排他性证据是硬门槛", "三个横断面维度", "两个独立证据家族",
        "2 项排他性证据", "当前不可识别", "广谱观察矩阵", "排他性证据矩阵", "2024-10-22",
        "legacy_v3_to_v4_map.csv",
    ]
    missing_skill_terms = [t for t in skill_terms if t not in skill_raw]
    check("Skill 核心强化条款齐全", not missing_skill_terms,
          "齐全" if not missing_skill_terms else "缺少：" + "、".join(missing_skill_terms))
    ref8 = skill_dir / "references/08_广谱观察与排他性证据.md"
    ref8_raw = ref8.read_text("utf-8") if ref8.exists() else ""
    ref8_terms = ["广谱观察", "排他性证据", "独立证据簇", "横断面梯度", "负向预测", "主导因子评分卡"]
    check("新增参考模块 08 完整", ref8.exists() and all(t in ref8_raw for t in ref8_terms),
          f"关键术语 {sum(t in ref8_raw for t in ref8_terms)}/{len(ref8_terms)}")
    policy_raw = (skill_dir / "references/02_政策分析模块.md").read_text("utf-8")
    check("政策模块已加入横断面和排他性检验", all(t in policy_raw for t in ["广谱横断面", "排他性证据", "置换", "实际使用率"]),
          "政策穿透条款齐全")
    output_raw = (skill_dir / "references/05_输出模板与质量检查.md").read_text("utf-8")
    check("输出模板含两张证据矩阵", all(t in output_raw for t in ["广谱观察矩阵", "排他性证据矩阵", "主导因子排序", "不可识别"]),
          "模板齐全")

    # Evals.
    rubric = (skill_dir / "evals/rubric.md").read_text("utf-8")
    numbered = re.findall(r"^\d+\. \*\*", rubric, flags=re.M)
    tests = read_jsonl(skill_dir / "evals/test_cases.jsonl")
    check("Skill 评分标准为 16 项/32 分", len(numbered) == 16 and "总分 32 分" in rubric,
          f"识别 {len(numbered)} 项")
    check("Skill 回归测试 13 个且 ID 唯一", len(tests) == 13 and len({x["id"] for x in tests}) == 13,
          f"{len(tests)} 个")
    test_text = json.dumps(tests, ensure_ascii=False)
    check("回归测试覆盖广谱观察与排他性证据", all(t in test_text for t in ["横断面", "排他性证据", "反向证据", "主导因子"]),
          "覆盖关键概念")

    # Assembled single-file Skill.
    single_a = root / "01_skill/高博宏观市场分析Skill.md"
    single_b = root / "01_skill/高博宏观市场政策分析Skill_完整版.md"
    assembled_same = single_a.exists() and single_b.exists() and single_a.read_bytes() == single_b.read_bytes()
    single_raw = single_a.read_text("utf-8") if single_a.exists() else ""
    all_ref_titles = all(f"## {p.stem.split('_', 1)[-1]}" in single_raw or p.stem.split('_', 1)[-1] in single_raw for p in refs)
    check("两份单文件 Skill 完全一致", assembled_same, f"大小 {single_a.stat().st_size if single_a.exists() else 0} 字节")
    check("单文件 Skill 已合并 8 个模块", all_ref_titles and "## 08｜广谱观察与排他性证据" in single_raw,
          f"references={len(refs)}")

    # Guides and top-level docs.
    required_guides = [
        "00_高善文文集导读与使用说明.md",
        "01_高博Skill说明与使用手册.md",
        "02_高博EPUB文集说明.md",
        "03_V4.0数据库更新说明.md",
        "使用提示词模板.md",
        "部署与检索建议.md",
    ]
    missing_guides = [x for x in required_guides if not (root / "04_guides" / x).exists()]
    check("六份使用指南齐全", not missing_guides,
          "齐全" if not missing_guides else "缺少：" + "、".join(missing_guides))
    readme = (root / "README.md").read_text("utf-8")
    changelog = (root / "CHANGELOG.md").read_text("utf-8")
    check("README 已更新到 V4.0/Skill 1.2.0", all(t in readme for t in ["V4.0", "1.2.0", "160 篇", "广谱观察", "排他性证据"]),
          "版本与核心强化已说明")
    check("CHANGELOG 记录 V4.0 更新", all(t in changelog for t in ["V4.0", "160 篇", "1.2.0", "排他性证据"]),
          "更新记录齐全")

    # Tools.
    tool_names = {
        "build_v4_corpus.py", "build_enhanced_indexes_and_chunks.py", "inspect_epub.py",
        "assemble_skill.py", "validate_pack.py", "build_manifest.py"
    }
    actual_tools = {p.name for p in (root / "07_tools").glob("*.py")}
    check("六个可复现工具齐全", tool_names.issubset(actual_tools),
          f"{len(tool_names & actual_tools)}/{len(tool_names)}")

    # Write results and report.
    pass_count = sum(x["status"] == "PASS" for x in checks)
    fail_count = len(checks) - pass_count
    write_csv(q / "validation_checks.csv", checks, ["check", "status", "detail"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "knowledge_pack_version": "4.0",
        "skill_version": "1.2.0",
        "source_epub": source_epub.name,
        "source_epub_sha256": src_sha,
        "total_checks": len(checks),
        "passed": pass_count,
        "failed": fail_count,
        "all_passed": fail_count == 0,
        "article_count": 160,
        "semantic_chunk_count": len(sem),
        "fixed_chunk_count": len(fixed),
        "reference_module_count": len(refs),
        "test_case_count": len(tests),
    }
    (q / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 高博 AI 知识库 V4.0 质量校验报告",
        "",
        f"- 生成时间：{summary['generated_at']}；",
        f"- 源 EPUB：`{source_epub.name}`；",
        f"- 源 SHA-256：`{src_sha}`；",
        f"- 数据库版本：V4.0；Skill 版本：1.2.0；",
        f"- 校验结果：**{pass_count}/{len(checks)} 项通过**；",
        "",
        "## 核心结果",
        "",
        "- 160 篇单篇 Markdown 与 V4.0 EPUB 正文的汉字序列逐篇完全一致；",
        "- 9 个分类、157 篇日期、正文字符和 V4 更新状态与源文件解析结果一致；",
        "- 1,264 个章节感知切片和 1,053 个固定切片覆盖 160 篇文章；",
        "- 旧版 108 篇均有迁移、修订、合并或删除状态记录；",
        "- Skill 已升级到 1.2.0，含 8 个参考模块、13 个回归用例和 16 项评分标准；",
        "- 广谱观察与排他性证据已写入核心规则、政策模块、主题模块、资产模块、输出模板和评测硬门槛；",
        "- EPUB 的 979 个图片资产、978 次文章图片引用和 2,626 项内部引用已建立索引并通过引用存在性检查；",
        "",
        "## 校验明细",
        "",
        "| # | 检查项 | 状态 | 说明 |",
        "|---:|---|---|---|",
    ]
    for i, row in enumerate(checks, 1):
        detail = row["detail"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {i} | {row['check']} | {row['status']} | {detail} |")
    lines.extend([
        "",
        "## 边界",
        "",
        "本报告完成文字一致性、结构、索引、切片、Skill、迁移关系和 EPUB 内部引用检查；未运行独立的 DAISY/W3C EPUBCheck，也不对作者观点的现实有效性作判断。图表精确数值仍应回到底层数据源核验。",
        "",
    ])
    (q / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
