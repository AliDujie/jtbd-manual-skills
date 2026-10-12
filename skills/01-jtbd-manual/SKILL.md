---
name: jtbd-manual
description: JTBD 实战手册总入口（路由 skill）。当用户提及 JTBD、Jobs to Be Done、用户研究、访谈拆解、场景库构建、四力分析、补偿行为、创新机会识别、机会评分、优先级排序、洞察落地时使用。根据用户意图分派到对应的子 skill（0-16 号，共 17 个）；也支持全流程编排——串起某几关跑完整项目。
version: 1.0.0
---

# JTBD 实战手册 · 总入口

《JTBD 实战手册：AI 助力 JTBD 全流程》配套 skill 集合的总路由。整个手册按项目流程组织为 16 关 + 自序（共 17 个单元），对应 17 个执行子 skill（jtbd-boundary-check 至 jtbd-pitfall-library）。本 skill 作为总入口，承担两个职责：

## 一、意图识别与分派

用户描述任务时，识别其位于全流程的哪一步，分派给对应子 skill：

| 用户意图关键词 | 分派至 |
|---|---|
| 判断该不该用 JTBD / 划边界 / 项目边界感 | jtbd-boundary-check |
| 拆需求 / 拆假设 / 六板斧 / 可证伪 | jtbd-hypothesis-decompose |
| 选样本 / 招募 / 样本量 | jtbd-sampling-design |
| 写访谈提纲 / Switch/ODI/Churn | jtbd-interview-guide |
| 现场跑偏 / 主动被动识别 / 临场话术 | jtbd-interview-execution |
| 转录纠错 / 关键原话筛选 | jtbd-transcript-refine |
| 场景库抽取 / 35 列 / 补偿行为标注 | jtbd-scene-extract |
| L1/L2 分层 / 场景合并 / 分类粒度 | jtbd-hierarchy-cluster |
| 四力分析 / 净推动力 / 田字格 | jtbd-forces-analysis |
| 洞察质量 / So What / 反直觉发现 | jtbd-insight-quality |
| 创新信号 / 五种金矿 / S/A/B/C 分级 | jtbd-innovation-signal |
| 补偿行为产品化 / 收编赋能颠覆 | jtbd-compensation-productize |
| OST / Opportunity Solution Experiment | jtbd-ost-loop |
| 洞察落地 / 推动 PRD/OKR | jtbd-insight-adoption |
| 业务约束 / 战略权重 / 供给能力 | jtbd-constraint-dialog |
| AI 分工 / prompt 骨架 / 幻觉识别 | jtbd-ai-forge |
| 避坑 / 踩过的坑 / 免疫记忆 | jtbd-pitfall-library |

## 二、全流程编排

当用户说"跑一个完整 JTBD 项目"、"从头到尾走一遍"、"启动新研究"时，按以下顺序串联：

```
0 边界 → 1 拆假设 → 2 样本 → 3 提纲 → 4 现场 → 5 转录 → 6 场景库
→ 7 分层 → 8 四力 → 9 洞察 → 10 创新识别 → 11 补偿产品化
→ 12 OST → 13 落地 → 14 约束 → 15 AI 作坊 → 16 避坑复盘
```

每一步产出可作为下一步输入。中间任何一步都可以跳过或返工。

## 三、底层能力库

18 个 skill 是业务视角的包装层，底层复用两个基础 skill 的能力：

- **jtbd-scene-library**（35 列场景库两遍式抽取）
- **scenario-library**（HTML 分析报告流水线）

上层 skill 不重写底层能力，只做业务视角的编排和调用。

## 四、使用方式

- **单关调用**：用户直接指名某关，如"帮我做六板斧拆解" → 分派 jtbd-hypothesis-decompose
- **全流程调用**：用户说"跑一遍完整流程" → 按顺序执行 0-16 号
- **反向查找**：用户描述症状不确定属于哪一步，本 skill 通过问几个诊断问题（"你在哪一步？访谈还没做？还是场景库出来了？"）定位到具体 skill

## 五、书稿对应关系

本 skill 集合与《JTBD 实战手册》一书完全对应——每关一个 skill，每个 skill 承载该关的执行能力。读书遇到问题→跳到对应 skill 执行→不懂原理再翻书。
