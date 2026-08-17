#!/usr/bin/env python3
"""Assemble the multi-file Skill into two equivalent single-file Markdown copies."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def demote_headings(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        hashes, rest = match.group(1), match.group(2)
        return (hashes + "#" if len(hashes) < 6 else hashes) + " " + rest
    return re.sub(r"^(#{1,6})\s+(.+)$", repl, text, flags=re.M)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_dir", type=Path)
    args = parser.parse_args()
    pack = args.pack_dir
    skill_dir = pack / "01_skill/gaobo-macro-market-policy"
    core = (skill_dir / "SKILL.md").read_text(encoding="utf-8").rstrip()
    refs = sorted((skill_dir / "references").glob("*.md"))
    appendix = [
        "---",
        "",
        "# 附录：完整版参考模块",
        "",
        "以下内容与标准 Skill 目录中的 `references/` 一致，供不支持多文件 Skill 的知识库一次性上传。",
    ]
    for ref in refs:
        appendix.extend(["", "---", "", demote_headings(ref.read_text(encoding="utf-8").strip())])
    assembled = core + "\n\n" + "\n".join(appendix).rstrip() + "\n"
    for name in ("高博宏观市场分析Skill.md", "高博宏观市场政策分析Skill_完整版.md"):
        (pack / "01_skill" / name).write_text(assembled, encoding="utf-8")
    print(f"assembled {len(refs)} references, {len(assembled)} characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
