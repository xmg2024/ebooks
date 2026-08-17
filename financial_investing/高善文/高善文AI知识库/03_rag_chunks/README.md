# RAG 切片说明

- `chunks_semantic_900_120.jsonl`：章节感知切片，正文核心约 900 个非空白字符，检索文本含约 120 字上文衔接。
- `chunks_1200_160.jsonl`：兼容固定切片，核心约 1200 字，正文内容显式包含约 160 字重叠。
- V4.0 切片元数据新增 `broad_observation_dimensions` 与 `exclusive_evidence_methods`，用于优先召回横断面和排他性检验材料。
- 回答前仍应回到单篇 Markdown 核对上下文；涉及图表时回到源 EPUB。
