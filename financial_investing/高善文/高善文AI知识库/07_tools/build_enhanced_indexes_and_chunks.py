#!/usr/bin/env python3
"""Build V4.0 indexes and RAG chunks for the Gao Shanwen AI knowledge pack."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SEM_TARGET = 900
SEM_OVERLAP = 120
SEM_MAX = 1250
SEM_MIN = 260
FIXED_TARGET = 1200
FIXED_OVERLAP = 160
FIXED_MAX = 1500
FIXED_MIN = 350

TOPIC_RULES: dict[str, list[str]] = {
    "研究方法与证据": [r"研究方法", r"逻辑", r"因果", r"相关关系", r"证伪", r"预测", r"横断面", r"经验事实", r"理论", r"反证", r"排除"],
    "潜在增长与人口": [r"潜在(?:经济|GDP)?增速", r"人口红利", r"人口负债", r"刘易斯拐点", r"劳动力", r"老龄化", r"资本系数", r"全要素生产率", r"长期资本回报"],
    "增长与总需求": [r"总需求", r"内需", r"经济增长", r"GDP", r"经济景气", r"经济周期", r"名义增长", r"产出缺口"],
    "消费收入与就业": [r"消费", r"居民收入", r"可支配收入", r"储蓄率", r"就业", r"工资", r"失业", r"工时", r"农民工", r"收入分配"],
    "通胀与价格": [r"通货膨胀", r"通胀", r"CPI", r"PPI", r"食品价格", r"核心CPI", r"价格粘性", r"生产资料价格", r"贸易条件"],
    "货币与流动性": [r"货币政策", r"货币供应", r"M1", r"M2", r"央行", r"流动性", r"广谱利率", r"银行间", r"同业", r"存款准备金", r"信贷需求"],
    "利率与债券市场": [r"债券", r"债市", r"国债", r"国开债", r"收益率曲线", r"长端利率", r"短端利率", r"利率市场化", r"债券收益率", r"政策利率"],
    "信用债务与金融风险": [r"债务", r"杠杆", r"信用风险", r"信用利差", r"违约", r"清偿力", r"影子银行", r"理财", r"期限错配", r"刚性兑付", r"金融风险", r"债务重组"],
    "财政与地方政府": [r"财政政策", r"财政支出", r"财政收入", r"地方政府", r"地方债", r"城投", r"基础设施", r"基建", r"土地财政", r"政府债", r"税收", r"社保"],
    "房地产与城市化": [r"房地产", r"房价", r"住宅", r"商品房", r"土地供应", r"购房", r"按揭", r"房租", r"租金", r"新开工", r"竣工", r"开发商", r"城市化"],
    "汇率与国际收支": [r"人民币汇率", r"汇率", r"美元", r"国际收支", r"外汇储备", r"资本流出", r"资本流入", r"外汇占款", r"经常账户", r"直接投资"],
    "贸易与全球经济": [r"出口", r"进口", r"贸易盈余", r"贸易顺差", r"外需", r"中美贸易", r"贸易摩擦", r"全球化", r"关税", r"可贸易部门", r"海外需求", r"全球经济"],
    "产能库存与工业周期": [r"产能", r"产能利用率", r"库存", r"补库", r"去库", r"工业增加值", r"制造业投资", r"工业周期", r"供给侧", r"生产资料"],
    "产业升级与制造业": [r"产业升级", r"技术进步", r"科技", r"电子制造", r"创新", r"制造业", r"产业结构", r"新兴产业", r"生产率", r"竞争力"],
    "能源资源与碳转型": [r"大宗商品", r"原油", r"煤炭", r"钢铁", r"有色", r"资源品", r"能源", r"碳中和", r"碳达峰", r"雾霾"],
    "股票与资本市场": [r"股市", r"股票", r"A股", r"资本市场", r"股灾", r"牛市", r"熊市", r"估值", r"IPO", r"创业板", r"风险偏好", r"筹码", r"市盈率"],
    "企业盈利与资产负债表": [r"工业利润", r"企业利润", r"利润率", r"ROA", r"ROE", r"资产周转率", r"企业部门杠杆", r"上市公司", r"现金流", r"资产负债表", r"资本回报率"],
    "金融制度与监管": [r"金融监管", r"监管", r"制度", r"存贷比", r"资本约束", r"预售资金", r"保证金", r"涨跌停", r"停牌", r"注册制", r"金融改革", r"道德风险"],
    "疫情冲击与宏观应对": [r"疫情", r"新冠", r"封控", r"疤痕效应", r"灾后重建", r"救济", r"补贴", r"政策干预", r"公共卫生"],
}

ASSET_RULES: dict[str, list[str]] = {
    "权益": [r"股市", r"股票", r"A股", r"资本市场", r"估值", r"牛市", r"创业板", r"筹码"],
    "利率债": [r"国债", r"债券收益率", r"收益率曲线", r"长端利率", r"短端利率", r"债市"],
    "信用债": [r"信用利差", r"信用风险", r"违约", r"企业债", r"城投", r"信用债"],
    "外汇": [r"汇率", r"人民币", r"美元", r"外汇", r"资本流动"],
    "大宗商品": [r"大宗商品", r"原油", r"煤炭", r"钢铁", r"有色", r"商品价格", r"工业品"],
    "房地产": [r"房地产", r"房价", r"住宅", r"商品房", r"土地", r"按揭", r"租金"],
}

POLICY_RULES: dict[str, list[str]] = {
    "货币政策": [r"货币政策", r"央行", r"存款准备金", r"逆回购", r"MLF", r"政策利率", r"信贷投放"],
    "财政政策": [r"财政政策", r"财政支出", r"财政赤字", r"政府债", r"地方债", r"基建", r"税收", r"社保"],
    "房地产政策": [r"限购", r"限贷", r"按揭", r"土地供应", r"房地产调控", r"预售资金", r"保交楼", r"止跌回稳"],
    "金融监管": [r"监管", r"去杠杆", r"资本约束", r"存贷比", r"刚性兑付", r"影子银行", r"注册制"],
    "产业与贸易政策": [r"产业政策", r"供给侧", r"关税", r"贸易摩擦", r"出口退税", r"补贴", r"产能过剩"],
    "能源与环境政策": [r"碳中和", r"碳达峰", r"能源政策", r"环保", r"去产能", r"排放"],
    "汇率与资本流动政策": [r"汇率政策", r"中间价", r"外汇管理", r"资本管制", r"人民币国际化", r"汇率形成机制"],
    "金融稳定政策": [r"维稳", r"流动性危机", r"金融稳定", r"救市", r"债务重组", r"风险处置"],
    "疫情救助与收入补贴": [r"疫情", r"救济", r"定向补贴", r"现金补贴", r"灾后重建", r"疤痕效应"],
}

METHOD_RULES: dict[str, list[str]] = {
    "可证伪假说": [r"证伪", r"命题", r"预言", r"理论.{0,8}预测", r"如果.{0,20}那么"],
    "竞争性假说": [r"竞争性", r"第一种可能", r"第二种可能", r"备选解释", r"另一种解释", r"可能的原因", r"一种解释"],
    "排他性证据": [r"反证", r"排除", r"不支持", r"相悖", r"说不通", r"不应该", r"只有.{0,20}才能", r"区别在于"],
    "广谱横断面观察": [r"横断面", r"横向比对", r"不同行业", r"不同城市", r"不同地区", r"不同品类", r"不同产品", r"所有制", r"企业规模", r"分组", r"资产谱"],
    "因果与相关区分": [r"因果关系", r"相关关系", r"第三变量", r"共同原因", r"隔离"],
    "价格—数量联合验证": [r"量升价落", r"量跌价升", r"量价", r"价格.{0,16}产量", r"数量.{0,16}价格", r"产出.{0,16}价格"],
    "名义—实际拆分": [r"名义.{0,12}实际", r"实际.{0,12}名义", r"贸易条件", r"价格因素", r"剔除价格"],
    "总量—结构拆分": [r"总量.{0,12}结构", r"结构性", r"分行业", r"分地区", r"分部门", r"分品类", r"不对称"],
    "存量—流量与会计闭合": [r"存量", r"流量", r"会计恒等", r"储蓄.{0,10}投资", r"收入.{0,10}支出", r"融资.{0,10}存款"],
    "资产负债表分析": [r"资产负债表", r"现金流", r"杠杆", r"期限错配", r"偿债", r"抵押品"],
    "广谱利率与流动性": [r"广谱利率", r"流动性", r"资金成本", r"资金面", r"融资成本", r"银行间.{0,12}贷款"],
    "跨市场与跨资产验证": [r"股票.{0,20}债券", r"股市.{0,20}房地产", r"汇率.{0,20}贸易", r"资产价格", r"大类资产", r"不同资产"],
    "自然实验与政策识别": [r"自然实验", r"政策冲击", r"制度变化", r"监管变化", r"疫情冲击", r"事件研究"],
    "左侧—右侧判断": [r"左侧", r"右侧", r"拐点", r"均值回归"],
    "国际与历史对标": [r"国际比较", r"日本", r"韩国", r"美国", r"欧洲", r"历史经验", r"对比"],
    "情景与预测复盘": [r"情景", r"预测", r"误差", r"复盘", r"扰动因素", r"概率"],
}

BROAD_OBSERVATION_RULES: dict[str, list[str]] = {
    "行业横断面": [r"不同行业", r"行业之间", r"分行业", r"行业分化", r"工业行业", r"上游", r"中游", r"下游"],
    "地区与城市横断面": [r"不同城市", r"分城市", r"城市之间", r"一线城市", r"二线城市", r"三四线", r"不同地区", r"区域"],
    "产品与品类横断面": [r"不同产品", r"不同品类", r"食品", r"服务价格", r"耐用品", r"可贸易品", r"不可贸易品", r"商品和服务"],
    "所有制与企业类型": [r"国有企业", r"民营企业", r"所有制", r"国有资本", r"私营", r"大型企业", r"中小企业"],
    "主体资产负债表": [r"居民部门", r"企业部门", r"政府部门", r"银行", r"非银", r"资产负债表", r"现金流"],
    "期限评级与信用层级": [r"不同期限", r"期限结构", r"评级", r"高等级", r"低等级", r"信用利差", r"期限错配"],
    "收入年龄与家庭分组": [r"收入组", r"高收入", r"低收入", r"年龄结构", r"家庭", r"居民", r"农民工", r"劳动年龄"],
    "量价与名实组合": [r"量价", r"价格.{0,16}数量", r"产量.{0,16}价格", r"名义.{0,12}实际", r"贸易条件"],
    "国内国际与资本流动": [r"国内.{0,16}国外", r"中国.{0,16}美国", r"全球", r"国际收支", r"资本流动", r"汇率"],
    "跨资产与市场谱系": [r"资产谱", r"大类资产", r"股票.{0,16}房地产", r"债券.{0,16}股票", r"纪念币", r"商品.{0,16}股市"],
}

EXCLUSIVE_EVIDENCE_RULES: dict[str, list[str]] = {
    "符号与量价组合": [r"量升价落", r"量跌价升", r"量价同", r"价格下降", r"价格上涨", r"供应能力收缩", r"需求扩张"],
    "横断面梯度": [r"横断面", r"不同行业", r"不同城市", r"不同产品", r"所有制", r"越.{0,10}越"],
    "时序与领先滞后": [r"领先", r"滞后", r"先于", r"随后", r"拐点", r"时间顺序", r"阶段"],
    "反证与不相容事实": [r"反证", r"相悖", r"说不通", r"难以解释", r"不支持", r"排除", r"不应该"],
    "会计与存量流量约束": [r"会计恒等", r"储蓄率", r"贸易盈余", r"存量", r"流量", r"资产负债表", r"资金来源"],
    "自然实验与制度冲击": [r"政策冲击", r"制度变化", r"监管", r"疫情", r"去产能", r"汇率制度", r"事件"],
    "多市场一致性": [r"股票.{0,20}房地产", r"汇率.{0,20}顺差", r"债券.{0,20}信贷", r"大类资产", r"同步", r"背离"],
    "负向预测与证伪阈值": [r"如果.{0,30}应该", r"如果.{0,30}不会", r"一旦", r"推翻", r"证伪", r"预言"],
}

CORE_SOURCE_IDS = {
    "001", "003", "013", "014", "015", "018", "019", "024", "025", "028", "038", "040", "047",
    "051", "053", "056", "070", "071", "072", "074", "075", "079", "080", "082", "087", "088",
    "091", "092", "093", "097", "103", "105", "106", "107", "108", "111", "112", "114", "116",
    "118", "121", "127", "130", "133", "135", "145", "148", "150", "154", "159", "160",
}

CATEGORY_PRIMARY_TOPIC = {
    "成长、追忆与评论": "研究方法与证据",
    "代表作与研究方法": "研究方法与证据",
    "周期、通胀与人口": "增长与总需求",
    "流动性、利率与汇率": "货币与流动性",
    "资本市场与金融风险": "股票与资本市场",
    "房地产、城市化与消费": "房地产与城市化",
    "产业、产能与能源转型": "产能库存与工业周期",
    "贸易、国际收支与全球经济": "贸易与全球经济",
    "财政、疫情及宏观应对": "疫情冲击与宏观应对",
}


def non_ws_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def cjk_len(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return {}, raw
    fm_raw = raw[4:end]
    body = raw[end + 5:]
    meta: dict[str, object] = {}
    for line in fm_raw.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        try:
            meta[key] = json.loads(val)
        except Exception:
            meta[key] = val.strip('"\'')
    return meta, body


def extract_article_body(raw: str) -> str:
    _, rest = parse_frontmatter(raw)
    marker = "\n## 正文\n"
    body = rest.split(marker, 1)[1] if marker in rest else rest
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return body.strip()


def extract_headings(body: str) -> list[str]:
    return [x.strip() for x in re.findall(r"^#{1,6}[ \t]+(.+)$", body, flags=re.M)]


def score_rule_set(title: str, headings: str, body: str, rules: dict[str, list[str]]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for label, patterns in rules.items():
        score = 0
        for pat in patterns:
            score += min(len(re.findall(pat, title, flags=re.I)), 2) * 8
            score += min(len(re.findall(pat, headings, flags=re.I)), 3) * 4
            score += min(len(re.findall(pat, body, flags=re.I)), 7)
        if score:
            scores[label] = score
    return scores


def select_labels(scores: dict[str, int], threshold: int, max_count: int) -> list[str]:
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    selected = [k for k, v in ranked if v >= threshold][:max_count]
    if not selected and ranked:
        selected = [ranked[0][0]]
    return selected


@dataclass
class Unit:
    text: str
    section_path: tuple[str, ...]
    index: int


def split_long_block(text: str, max_chars: int) -> list[str]:
    if non_ws_len(text) <= max_chars:
        return [text]
    pieces = re.split(r"(?<=[。！？；!?;])", text)
    out: list[str] = []
    buf = ""
    for piece in pieces:
        if not piece:
            continue
        if buf and non_ws_len(buf + piece) > max_chars:
            out.append(buf.strip())
            buf = piece
        else:
            buf += piece
        while non_ws_len(buf) > max_chars:
            cut = min(len(buf), max_chars)
            left = buf[:cut]
            candidates = [left.rfind(x) for x in ("。", "；", "！", "？", "\n")]
            best = max(candidates)
            if best >= int(cut * 0.55):
                cut = best + 1
            out.append(buf[:cut].strip())
            buf = buf[cut:]
    if buf.strip():
        out.append(buf.strip())
    return out


def parse_units(body: str, max_chars: int) -> list[Unit]:
    lines = body.splitlines()
    path: list[str] = []
    blocks: list[tuple[str, tuple[str, ...]]] = []
    buf: list[str] = []
    buf_path: tuple[str, ...] = tuple()

    def flush() -> None:
        nonlocal buf
        if buf:
            text = "\n".join(buf).strip()
            if text:
                blocks.append((text, buf_path))
            buf = []

    for line in lines:
        hm = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if hm:
            flush()
            level = len(hm.group(1))
            heading = hm.group(2).strip()
            while len(path) >= level:
                path.pop()
            while len(path) < level - 1:
                path.append("")
            path.append(heading)
            buf_path = tuple(x for x in path if x)
        elif not line.strip():
            flush()
            buf_path = tuple(x for x in path if x)
        else:
            if not buf:
                buf_path = tuple(x for x in path if x)
            buf.append(line.rstrip())
    flush()

    units: list[Unit] = []
    idx = 0
    for text, section_path in blocks:
        for piece in split_long_block(text, max_chars):
            idx += 1
            units.append(Unit(piece, section_path, idx))
    return units


def build_chunks(units: list[Unit], target: int, max_chars: int, min_chars: int) -> list[dict]:
    if not units:
        return []
    chunks: list[dict] = []
    i = 0
    while i < len(units):
        selected: list[Unit] = []
        size = 0
        start_section = units[i].section_path
        while i < len(units):
            u = units[i]
            ulen = non_ws_len(u.text)
            section_changed = bool(selected) and u.section_path != start_section and size >= min_chars
            if section_changed or (selected and size + ulen > max_chars):
                break
            selected.append(u)
            size += ulen
            i += 1
            if size >= target:
                break
        if not selected:
            selected = [units[i]]
            i += 1
        content = "\n\n".join(u.text for u in selected).strip()
        section = next((u.section_path for u in selected if u.section_path), tuple())
        chunks.append({
            "content": content,
            "section_path": list(section),
            "source_unit_start": selected[0].index,
            "source_unit_end": selected[-1].index,
            "non_ws_chars": non_ws_len(content),
            "cjk_chars": cjk_len(content),
        })
    merged: list[dict] = []
    for ch in chunks:
        if ch["non_ws_chars"] < min_chars and merged and merged[-1]["non_ws_chars"] + ch["non_ws_chars"] <= max_chars:
            prev = merged[-1]
            prev["content"] = (prev["content"] + "\n\n" + ch["content"]).strip()
            prev["source_unit_end"] = ch["source_unit_end"]
            prev["non_ws_chars"] = non_ws_len(prev["content"])
            prev["cjk_chars"] = cjk_len(prev["content"])
        else:
            merged.append(ch)
    return merged


def tail_context(text: str, target_non_ws: int) -> str:
    if non_ws_len(text) <= target_non_ws:
        return text.strip()
    raw_window = max(target_non_ws * 3, 300)
    snippet = text[-raw_window:]
    positions = [snippet.find(x) for x in ("\n\n", "。", "；", "！", "？") if snippet.find(x) >= 0]
    if positions:
        cut = min(positions)
        snippet = snippet[cut + (2 if snippet[cut:cut+2] == "\n\n" else 1):]
    while non_ws_len(snippet) > target_non_ws * 1.8 and len(snippet) > target_non_ws:
        snippet = snippet[max(1, len(snippet)//10):]
    return snippet.strip()


def safe_date_key(date_str: str) -> tuple[int, int, int]:
    if not date_str:
        return (9999, 12, 31)
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", date_str)
    if not m:
        return (9999, 12, 31)
    return int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def make_map(title: str, intro: str, members: dict[str, list[tuple[int, dict]]]) -> str:
    lines = [f"# {title}", "", intro, ""]
    for label in sorted(members):
        rows = sorted(members[label], key=lambda x: (-x[0], safe_date_key(x[1].get("date", "")), x[1]["id"]))
        lines += [f"## {label}（{len(rows)} 篇）", ""]
        for score, r in rows:
            lines.append(f"- {r['id']}｜{r.get('date') or '未注明'}｜{r['title']}｜相关度 {score}｜`{r['file']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_dir", type=Path)
    args = parser.parse_args()
    root = args.pack_dir
    with (root / "05_indexes/article_index.csv").open(encoding="utf-8-sig", newline="") as f:
        base_rows = list(csv.DictReader(f))

    enhanced_rows: list[dict] = []
    semantic_chunks: list[dict] = []
    fixed_chunks: list[dict] = []
    topic_members: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    method_members: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    broad_members: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    exclusive_members: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    asset_members: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    policy_members: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    category_members: dict[str, list[dict]] = defaultdict(list)
    figures_rows: list[dict] = []

    for base in base_rows:
        aid = str(base["id"]).zfill(3)
        raw = (root / base["file"]).read_text("utf-8")
        body = extract_article_body(raw)
        headings_list = extract_headings(body)
        headings = "\n".join(headings_list)
        title = base["title"]
        category = base["category"]
        date = (base.get("date") or "").strip()

        topic_scores = score_rule_set(title, headings, body, TOPIC_RULES)
        topics = select_labels(topic_scores, 5, 8)
        category_default = CATEGORY_PRIMARY_TOPIC.get(category)
        if category_default and category_default not in topics:
            topics = ([category_default] + topics)[:8]
        primary_topic = topics[0] if topics else category_default or "综合宏观"
        asset_scores = score_rule_set(title, headings, body, ASSET_RULES)
        assets = select_labels(asset_scores, 5, 6)
        policy_scores = score_rule_set(title, headings, body, POLICY_RULES)
        policies = select_labels(policy_scores, 5, 7)
        method_scores = score_rule_set(title, headings, body, METHOD_RULES)
        methods = select_labels(method_scores, 5, 10)
        broad_scores = score_rule_set(title, headings, body, BROAD_OBSERVATION_RULES)
        broad_dims = select_labels(broad_scores, 4, 8)
        exclusive_scores = score_rule_set(title, headings, body, EXCLUSIVE_EVIDENCE_RULES)
        exclusive_methods = select_labels(exclusive_scores, 4, 8)

        year = date[:4] if re.match(r"^\d{4}", date) else ""
        decade = f"{year[:3]}0s" if year else "未注明"
        retrieval_priority = 100 + (35 if aid in CORE_SOURCE_IDS else 0) + (15 if base.get("content_type") == "representative" else 0)
        if "广谱横断面观察" in methods:
            retrieval_priority += 10
        if "排他性证据" in methods:
            retrieval_priority += 10

        enhanced = dict(base)
        enhanced.update({
            "year": year,
            "decade": decade,
            "canonical_id": aid,
            "duplicate_group": "",
            "duplicate_relation": "unique",
            "is_preferred_version": "true",
            "retrieval_suppress_default": "false",
            "primary_topic": primary_topic,
            "topics_v2": ";".join(topics),
            "topic_scores": json.dumps(topic_scores, ensure_ascii=False, sort_keys=True),
            "asset_classes": ";".join(assets),
            "policy_dimensions": ";".join(policies),
            "methodology_concepts": ";".join(methods),
            "broad_observation_dimensions": ";".join(broad_dims),
            "exclusive_evidence_methods": ";".join(exclusive_methods),
            "heading_outline": json.dumps(headings_list, ensure_ascii=False),
            "retrieval_priority": retrieval_priority,
            "file_sha256": sha256_text(raw),
            "body_sha256": sha256_text(body),
            "body_non_ws_chars": non_ws_len(body),
            "body_cjk_chars": cjk_len(body),
        })
        enhanced_rows.append(enhanced)
        category_members[category].append(enhanced)

        for label, score in topic_scores.items():
            if label in topics:
                topic_members[label].append((score, enhanced))
        for label, score in method_scores.items():
            if label in methods:
                method_members[label].append((score, enhanced))
        for label, score in broad_scores.items():
            if label in broad_dims:
                broad_members[label].append((score, enhanced))
        for label, score in exclusive_scores.items():
            if label in exclusive_methods:
                exclusive_members[label].append((score, enhanced))
        for label, score in asset_scores.items():
            if label in assets:
                asset_members[label].append((score, enhanced))
        for label, score in policy_scores.items():
            if label in policies:
                policy_members[label].append((score, enhanced))

        if int(base.get("image_count") or 0) > 0:
            figures_rows.append({
                "article_id": aid,
                "title": title,
                "date": date,
                "category": category,
                "image_count": base.get("image_count", ""),
                "image_alts": base.get("image_alts", ""),
                "article_md": base["file"],
                "note": "正文保留图题、来源与 EPUB 图像路径注释；原始图像仍在源 EPUB 中。",
            })

        sem_units = parse_units(body, SEM_MAX)
        sem_parts = build_chunks(sem_units, SEM_TARGET, SEM_MAX, SEM_MIN)
        article_sem: list[dict] = []
        for i, part in enumerate(sem_parts, 1):
            cid = f"{aid}-s{i:03d}"
            section_display = " > ".join(part["section_path"]) if part["section_path"] else "正文"
            overlap_prefix = tail_context(sem_parts[i-2]["content"], SEM_OVERLAP) if i > 1 else ""
            bridge = f"[上文衔接]\n{overlap_prefix}\n\n[本段]\n" if overlap_prefix else ""
            retrieval_text = (
                f"# {title}\n\n文章ID：{aid}；日期：{date or '未注明'}；主题分类：{category}；章节：{section_display}\n"
                f"研究标签：{';'.join(methods)}；广谱维度：{';'.join(broad_dims)}；排他性证据：{';'.join(exclusive_methods)}\n\n"
                f"{bridge}{part['content']}"
            )
            ch = {
                "chunk_id": cid,
                "article_id": aid,
                "canonical_article_id": aid,
                "title": title,
                "thematic_category": category,
                "content_type": base.get("content_type", ""),
                "date": date,
                "year": year,
                "primary_topic": primary_topic,
                "topics": topics,
                "asset_classes": assets,
                "policy_dimensions": policies,
                "methodology_concepts": methods,
                "broad_observation_dimensions": broad_dims,
                "exclusive_evidence_methods": exclusive_methods,
                "legacy_v3_ids": [x for x in (base.get("legacy_v3_ids") or "").split(";") if x],
                "update_status": base.get("update_status", ""),
                "source_file": base["source_file"],
                "article_md": base["file"],
                "chunk_index": i,
                "section_path": part["section_path"],
                "source_unit_start": part["source_unit_start"],
                "source_unit_end": part["source_unit_end"],
                "content": part["content"],
                "overlap_prefix": overlap_prefix,
                "overlap_non_ws_chars": non_ws_len(overlap_prefix),
                "retrieval_text": retrieval_text,
                "non_ws_chars": part["non_ws_chars"],
                "cjk_chars": part["cjk_chars"],
                "content_sha256": sha256_text(part["content"]),
                "prev_chunk_id": "",
                "next_chunk_id": "",
            }
            article_sem.append(ch)
            semantic_chunks.append(ch)
        for i, ch in enumerate(article_sem):
            ch["prev_chunk_id"] = article_sem[i-1]["chunk_id"] if i > 0 else ""
            ch["next_chunk_id"] = article_sem[i+1]["chunk_id"] if i + 1 < len(article_sem) else ""

        fixed_units = parse_units(body, FIXED_MAX)
        fixed_parts = build_chunks(fixed_units, FIXED_TARGET, FIXED_MAX, FIXED_MIN)
        article_fixed: list[dict] = []
        for i, part in enumerate(fixed_parts, 1):
            cid = f"{aid}-c{i:03d}"
            overlap = tail_context(fixed_parts[i-2]["content"], FIXED_OVERLAP) if i > 1 else ""
            content = (overlap + "\n\n" + part["content"]).strip() if overlap else part["content"]
            ch = {
                "chunk_id": cid,
                "article_id": aid,
                "title": title,
                "category": category,
                "date": date,
                "chunk_index": i,
                "content": content,
                "core_content": part["content"],
                "overlap_prefix": overlap,
                "overlap_non_ws_chars": non_ws_len(overlap),
                "non_ws_chars": non_ws_len(content),
                "source_file": base["source_file"],
                "article_md": base["file"],
                "prev_chunk_id": "",
                "next_chunk_id": "",
                "content_sha256": sha256_text(content),
            }
            article_fixed.append(ch)
            fixed_chunks.append(ch)
        for i, ch in enumerate(article_fixed):
            ch["prev_chunk_id"] = article_fixed[i-1]["chunk_id"] if i > 0 else ""
            ch["next_chunk_id"] = article_fixed[i+1]["chunk_id"] if i + 1 < len(article_fixed) else ""

    extra_fields = [
        "year", "decade", "canonical_id", "duplicate_group", "duplicate_relation", "is_preferred_version",
        "retrieval_suppress_default", "primary_topic", "topics_v2", "topic_scores", "asset_classes",
        "policy_dimensions", "methodology_concepts", "broad_observation_dimensions", "exclusive_evidence_methods",
        "heading_outline", "retrieval_priority", "file_sha256", "body_sha256", "body_non_ws_chars", "body_cjk_chars",
    ]
    write_csv(root / "05_indexes/article_index_v2.csv", enhanced_rows, list(base_rows[0].keys()) + extra_fields)
    write_csv(root / "05_indexes/duplicate_map.csv", [], [
        "group_id", "article_id", "title", "date", "canonical_id", "relation", "retrieval_suppress_default", "note"
    ])
    write_csv(root / "05_indexes/figures_index.csv", figures_rows, [
        "article_id", "title", "date", "category", "image_count", "image_alts", "article_md", "note"
    ])

    rag_dir = root / "03_rag_chunks"
    rag_dir.mkdir(exist_ok=True)
    with (rag_dir / "chunks_semantic_900_120.jsonl").open("w", encoding="utf-8") as f:
        for ch in semantic_chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")
    semantic_index_rows = [{
        "chunk_id": ch["chunk_id"], "article_id": ch["article_id"], "title": ch["title"], "date": ch["date"],
        "thematic_category": ch["thematic_category"], "chunk_index": ch["chunk_index"],
        "section_path": " > ".join(ch["section_path"]) if ch["section_path"] else "正文",
        "primary_topic": ch["primary_topic"], "topics": ";".join(ch["topics"]),
        "methodology_concepts": ";".join(ch["methodology_concepts"]),
        "broad_observation_dimensions": ";".join(ch["broad_observation_dimensions"]),
        "exclusive_evidence_methods": ";".join(ch["exclusive_evidence_methods"]),
        "non_ws_chars": ch["non_ws_chars"], "overlap_non_ws_chars": ch["overlap_non_ws_chars"],
        "prev_chunk_id": ch["prev_chunk_id"], "next_chunk_id": ch["next_chunk_id"],
        "article_md": ch["article_md"], "content_sha256": ch["content_sha256"],
    } for ch in semantic_chunks]
    write_csv(rag_dir / "chunks_semantic_index.csv", semantic_index_rows, list(semantic_index_rows[0].keys()))

    with (rag_dir / "chunks_1200_160.jsonl").open("w", encoding="utf-8") as f:
        for ch in fixed_chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")
    fixed_index_rows = [{k: ch[k] for k in [
        "chunk_id", "article_id", "title", "category", "date", "chunk_index", "non_ws_chars",
        "overlap_non_ws_chars", "prev_chunk_id", "next_chunk_id", "article_md", "content_sha256"
    ]} for ch in fixed_chunks]
    write_csv(rag_dir / "chunks_index.csv", fixed_index_rows, list(fixed_index_rows[0].keys()))

    (root / "05_indexes/topic_map_v2.md").write_text(make_map(
        "主题索引 V4.0", "按标题、章节与正文关键词加权打标，用于召回与重排；不替代人工核对。", topic_members), "utf-8")
    (root / "05_indexes/topic_map.md").write_text((root / "05_indexes/topic_map_v2.md").read_text("utf-8"), "utf-8")
    (root / "05_indexes/methodology_concept_map.md").write_text(make_map(
        "方法论概念索引", "把可证伪、竞争性假说、广谱观察、排他性证据等方法映射到文章。", method_members), "utf-8")
    (root / "05_indexes/broad_observation_dimension_map.md").write_text(make_map(
        "广谱观察维度索引", "按行业、地区、品类、所有制、主体资产负债表、期限评级、量价名实和跨资产等横断面维度组织文章。广谱不是堆数据，而是寻找不同驱动因子应产生的差异化截面。", broad_members), "utf-8")
    (root / "05_indexes/exclusive_evidence_method_map.md").write_text(make_map(
        "排他性证据方法索引", "按符号组合、横断面梯度、时序、反证、会计约束、自然实验和多市场一致性组织文章。证据只有在能够改变竞争假说的相对权重时，才具有较强排他性。", exclusive_members), "utf-8")
    (root / "05_indexes/asset_map.md").write_text(make_map(
        "大类资产索引", "按权益、利率债、信用债、外汇、商品和房地产整理。历史文章提供机制，不替代当前定价验证。", asset_members), "utf-8")
    (root / "05_indexes/policy_map.md").write_text(make_map(
        "政策工具索引", "按货币、财政、地产、监管、产业贸易、能源环境、汇率资本流动和疫情救助整理。", policy_members), "utf-8")

    cat_lines = ["# V4.0 主题分类索引", "", "以下九类来自 EPUB V4.0 的汇编分类。", ""]
    for cat, rows in category_members.items():
        cat_lines += [f"## {cat}（{len(rows)} 篇）", ""]
        for r in rows:
            cat_lines.append(f"- {r['id']}｜{r.get('date') or '未注明'}｜{r['title']}｜`{r['file']}`")
        cat_lines.append("")
    (root / "05_indexes/category_map.md").write_text("\n".join(cat_lines).rstrip() + "\n", "utf-8")

    timeline_rows = sorted(enhanced_rows, key=lambda r: (safe_date_key(r.get("date", "")), r["id"]))
    lines = ["# 文章时间轴 V4.0", "", "未注明日期的文章列在末尾。V4.0 已合并旧版重复稿；旧编号见 `legacy_v3_to_v4_map.csv`。", ""]
    current_year = None
    for r in timeline_rows:
        year = r["year"] or "未注明"
        if year != current_year:
            lines += [f"## {year}", ""]
            current_year = year
        lines.append(f"- {r.get('date') or '未注明'}｜{r['id']}｜{r['title']}｜{r['category']}｜{r['primary_topic']}｜`{r['file']}`")
    (root / "05_indexes/timeline.md").write_text("\n".join(lines) + "\n", "utf-8")

    coverage_rows = []
    sem_by_article: dict[str, list[dict]] = defaultdict(list)
    fixed_by_article: dict[str, list[dict]] = defaultdict(list)
    for ch in semantic_chunks: sem_by_article[ch["article_id"]].append(ch)
    for ch in fixed_chunks: fixed_by_article[ch["article_id"]].append(ch)
    for r in enhanced_rows:
        aid = r["id"]
        coverage_rows.append({
            "article_id": aid, "title": r["title"], "body_non_ws_chars": r["body_non_ws_chars"],
            "semantic_chunk_count": len(sem_by_article[aid]),
            "semantic_core_non_ws_chars": sum(ch["non_ws_chars"] for ch in sem_by_article[aid]),
            "fixed_chunk_count": len(fixed_by_article[aid]),
            "has_semantic_chunks": str(bool(sem_by_article[aid])).lower(),
            "has_fixed_chunks": str(bool(fixed_by_article[aid])).lower(),
        })
    write_csv(root / "06_quality/semantic_chunk_coverage.csv", coverage_rows, list(coverage_rows[0].keys()))

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "article_count": len(enhanced_rows),
        "semantic_chunk_count": len(semantic_chunks),
        "fixed_chunk_count": len(fixed_chunks),
        "semantic_chunk_non_ws_min": min(ch["non_ws_chars"] for ch in semantic_chunks),
        "semantic_chunk_non_ws_median": sorted(ch["non_ws_chars"] for ch in semantic_chunks)[len(semantic_chunks)//2],
        "semantic_chunk_non_ws_max": max(ch["non_ws_chars"] for ch in semantic_chunks),
        "fixed_chunk_non_ws_min": min(ch["non_ws_chars"] for ch in fixed_chunks),
        "fixed_chunk_non_ws_median": sorted(ch["non_ws_chars"] for ch in fixed_chunks)[len(fixed_chunks)//2],
        "fixed_chunk_non_ws_max": max(ch["non_ws_chars"] for ch in fixed_chunks),
        "duplicate_groups": 0,
        "figure_article_count": len(figures_rows),
        "topic_count": len(topic_members),
        "methodology_concept_count": len(method_members),
        "broad_observation_dimension_count": len(broad_members),
        "exclusive_evidence_method_count": len(exclusive_members),
    }
    (root / "06_quality/build_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (rag_dir / "README.md").write_text(
        "# RAG 切片说明\n\n"
        "- `chunks_semantic_900_120.jsonl`：章节感知切片，正文核心约 900 个非空白字符，检索文本含约 120 字上文衔接。\n"
        "- `chunks_1200_160.jsonl`：兼容固定切片，核心约 1200 字，正文内容显式包含约 160 字重叠。\n"
        "- V4.0 切片元数据新增 `broad_observation_dimensions` 与 `exclusive_evidence_methods`，用于优先召回横断面和排他性检验材料。\n"
        "- 回答前仍应回到单篇 Markdown 核对上下文；涉及图表时回到源 EPUB。\n",
        "utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
