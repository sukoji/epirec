<div align="center">

# EpiRec

**用于记忆增强智能体的情绪唤回与事实检索的情景回忆基准**

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

**12 personas | 168 episodes | 504 retrieval probes | English | synthetic**

</div>

EpiRec 分别评估记忆增强智能体的两种检索能力。

| 能力 | 示例问题 | 评估目标 |
|---|---|---|
| 事实检索 | "我在拉面店点了什么？" | 找回某段经历中的具体事实。 |
| 情绪唤回 | "水边的那个夜晚仍然会回到我的脑海。" | 从间接的反思性表述中找回情绪上重要的过往经历。 |

LoCoMo 等长期记忆基准擅长评估事实检索，但没有情绪显著性标签。EpiRec 是一个小型、完全披露的 synthetic evaluation benchmark，用于补充这一缺口。它不能用于支持关于真实人类记忆、情绪或心理健康效果的结论。

<p align="center"><img src="docs/epirec_overview.png" width="96%" alt="EpiRec v1.0 benchmark overview"></p>

## 数据与任务

12 个虚构 persona 各有 14 条带日期的第一人称 journal episode；每条 episode 都有以下三种 probe 各一条。

| Probe | 构造规则 |
|---|---|
| `factual` | 直接询问具体事实，允许词汇重叠。 |
| `reflective_explicit` | 明确提及情绪或近义词的第一人称反思。 |
| `reflective_implicit` | 不使用独立情绪词表中的词，也不复用目标 episode content-word stem 的间接反思。 |

Release artifact 为 [`data/epirec_v1.json`](data/epirec_v1.json)。每个 probe 的 target 是包含它的 episode；时间戳为 ISO-8601 UTC。评估时应为每个 persona 建立一个 retrieval store，并使用 `reference_now` 进行 time-aware scoring。

## 评估协议

[GENERATION_SPEC.md](GENERATION_SPEC.md) 定义了固定协议：

- 每个 persona 的 14 条 episode 构成一个 store。
- 对全部 504 条 probe 进行评估，primary metric 为 recall@3。
- 同时报告 recall@1 和 MRR。
- 分别按 probe type、authored intensity band 与 age range 报告结果。
- 不应将 `factual`、`reflective_explicit` 与 `reflective_implicit` 合并为单一 headline score。

该数据集没有训练集，仅用于 evaluation。

## 复现

```bash
python scripts/validate.py            # 验证 schema、protocol、release 与 checksum
python scripts/build.py --check       # 确认 release artifact 是最新版本
python scripts/baseline_retrieval.py  # hashing baseline；安装 MiniLM 后会额外运行
```

[`data/SHA256SUMS`](data/SHA256SUMS) 固定 release JSON 的准确 checksum。GitHub Actions 会在每次 push 和 pull request 时检查 source、release 与 manifest 是否一致。

## 完整性与限制

- 所有 persona、episode 和 probe 均为 fictional synthetic data，由 Claude (Anthropic) 在 supervised session 中协助编写。
- validator 会检查 ID 与 text/query 重复、时区、长度、session span、label 分布、temporal coverage、probe 完整性和 implicit probe lexical leakage。
- [`human_validation/`](human_validation/) 中提供了 60 条 episode 的独立 human label audit 流程，但 v1.0 仍为 pending。因此目前应将 authored intensity/valence 解释为 design label。
- 本数据集仅有英语、single-target、人工编写且规模较小；它不能证明 ecological validity。

完整数据记录见 [DATASHEET.md](DATASHEET.md)，生成规则见 [GENERATION_SPEC.md](GENERATION_SPEC.md)。

## License and Citation

Data 采用 [CC BY 4.0](LICENSE)，code 采用 [MIT](LICENSE)。请使用 [English README](README.md) 中的 Citation。
