---
name: nix-knowledge-compiler
description: Compile, query, validate, and refactor a minimal Nix-inspired Markdown knowledge atom store. Use when the user wants to turn articles, AI conversations, excerpts, or thought fragments into reusable knowledge atoms; decompose reusable paradigms into callable atom functions; ensure larger atoms trace through components/depends_on to irreducible foundation atoms from low-level disciplines; extract interaction structures and rule points from social, business, relationship, strategy, or incentive-heavy material; preserve the source language for filenames, IDs, titles, and section headings; search existing atoms before creating new ones; validate atom quality; or merge, split, upgrade, and deprecate atoms.
---

# Nix Knowledge Compiler

把输入材料编译成可复用的 Markdown knowledge atoms。不要做摘要。不要做文章笔记。只沉淀能长期复用、能被依赖、能组合成更大 atom 的知识函数。

## 模式

行动前先选一个模式：

- `compile`：把文章、对话、摘录、想法编译成 draft atoms。
- `reuse`：只检索已有 atom，解释哪些能复用，不写入。
- `validate`：检查 atom 或 store，不新建 atom。
- `query`：用已有 atom 辅助当前思考，不写入。
- `refactor`：合并、拆分、升级、废弃旧 atom。

意图不明确时，不写入；先用 `reuse` 或 `query`。

## 工作区

只在当前 workspace root 内工作。不要默认读取或写入全局知识库。

核心目录只有：

```text
atoms/
```

不要创建 `sources/`、`systems/`、`relations/`、`views/`、`modules/`、`derivations/`、`runs/`、`indexes/`、`maps/` 等目录。source 只是 atom 里的来源指针。系统也是 atom，只是 `components` 不为空。

## 语言规则

atom 的可读部分必须跟随输入材料的主语言。

- 中文输入：文件名、`id`、H1、正文标题、正文都用中文。
- 英文输入：文件名、`id`、H1、正文标题、正文都用英文。
- 混合输入：按主要语言生成，必要术语可以保留原词。
- 不把中文概念翻译成英文 slug，也不优先使用拼音。
- 文件名必须等于 `id + ".md"`。
- ID 必须带版本后缀，如 `关系行为惯性-v1`；文件名对应为 `关系行为惯性-v1.md`。

中文 atom 的正文标题必须使用：

- 定义
- 边界
- 底层机制
- 复用价值
- 区分说明
- 必要说明
- 依赖
- 组件

不要把中文输入生成 `Definition`、`Boundary`、`Underlying mechanism` 等英文标题。

## 最小 Frontmatter

每个 atom 只保留：

```yaml
id:
status:
source:
depends_on:
components:
```

不要写能从图里推出来的字段：

- `used_by`
- `reuse_count`
- `feedback`
- `part_of`
- `closure`
- `system_scope`
- `object_kind`
- `level`
- `content_shape`
- `type`
- `related`
- `see_also`
- `replaces`
- `replaced_by`
- `merge_note`

## 核心本体

atom 是可复用知识函数，不是概念标签。

合格 atom 必须能写成：

```text
输入 -> 操作 -> 输出
```

基础 atom 是不可再拆的最小知识函数，`components: []`。判断标准：再拆下去，就无法得到仍然完整的“输入 -> 操作 -> 输出”。

系统 atom 是函数组合，`components` 必须指向组成它的下层 atom。任何系统 atom 必须能沿 `components` 和 `depends_on` 一层层追溯到底层基础 atom。

底层基础 atom 可以来自逻辑与概念分析、数学与图、概率统计、信息论、微观经济学、博弈论、决策理论、心理学、认知科学、进化心理学、语言学、传播学、社会学、系统论、控制论、复杂性科学、工程设计等底层学科。学科不写成 frontmatter 分类；只在正文“必要说明”里说明来源，并通过 `depends_on` 和正文 `[[atom-id]]` 逐层链接到底层原理 atom。

如果一个候选需要底层原理才能成立，但这些底层原理没有被已有 atom 承载，必须先创建或复用相应底层 atom；否则不要把上层候选直接写成孤立 atom。

## 地基补齐

地基 atom 是承载底层学科原理的基础 atom，不是学科标签。

编译上层 atom 前，先追问它的机制为什么成立。缺少前置原理时，先补齐地基 atom，再创建上层 atom。

优先检索或补齐这些地基方向：

- 逻辑与概念分析：定义边界、必要条件、充分条件、因果链、反例检验。
- 概率统计：基率、条件概率、贝叶斯更新、样本偏差、噪声、相关不等于因果。
- 信息论与信号：信息增益、信号噪声分离、压缩损失、代价信号、可伪造信号。
- 微观经济学：稀缺性、机会成本、边际分析、激励、交易成本、外部性、委托代理。
- 博弈论与机制设计：玩家、策略空间、收益函数、均衡、重复博弈、承诺、协调、信息不对称、信号博弈。
- 决策理论与行为经济学：期望值、风险、损失厌恶、时间偏好、权衡、有限理性。
- 心理学与认知科学：注意力、记忆、预测误差、强化、习惯、认知偏差、情绪调节。
- 进化论与进化心理学：选择压力、适应、互惠、亲缘选择、地位竞争、性选择、代价信号。
- 语言学、语用学与传播：语义、语用、言语行为、框架、叙事、共同知识、受众解码。
- 社会学、制度与网络：角色、规范、身份、地位、信任、社会资本、制度约束、扩散。
- 系统论、控制论与复杂性：反馈回路、延迟、瓶颈、涌现、路径依赖、吸引子、非线性。
- 工程、设计与组织：模块化、接口、约束、鲁棒性、冗余、摩擦、可维护性。

这张地图只用于寻找前置原理，不创建目录，不写入 frontmatter。不要预先造完整学科库；只补齐当前材料真正需要的地基 atom。

停止下钻的标准：当前 atom 已经是完整的“输入 -> 操作 -> 输出”，再拆就失去完整函数，且它已经能作为多个上层 atom 的底层原理使用。

## 构建顺序

每个候选按这个顺序处理：

1. 判断候选能否写成“输入 -> 操作 -> 输出”的知识函数。
2. 如果候选是上层函数，先拆 `components`，直到每条链能追溯到不可再拆的基础 atom。
3. 如果候选依赖底层学科原理，先检索或创建承载这些原理的底层 atom；缺地基时先补地基，再写上层 atom。
4. 如果材料涉及多人互动、关系、交易、竞争、合作、权力、承诺、信号或奖惩，再抽互动结构和规则点。
5. 没有独立复用价值，丢弃，不创建 `rejected` atom。
6. 检索已有 atom：名称、别名、函数签名、底层原理、相邻概念、可能的上层 atom。
7. 旧 atom 能准确承载，复用旧 atom，不新建。
8. 旧 atom 机制匹配但边界太窄，优先升级旧 atom。
9. 旧 atom 无法承载且候选有独立复用价值，才新建 atom。
10. 候选混入多个独立函数，先拆分。
11. 已有 atom 实质重复，合并。

不能先新建，再事后考虑复用。

## 互动结构扫描

互动结构不是新字段，也不是 atom 类型。它只是 compile 前的提取步骤，用来把材料中的可复用规则点挖出来。

当材料适用时，先找：

- 玩家：谁在局里。
- 目标：每个玩家想得到什么、避免什么。
- 信息：谁知道什么，谁不知道什么，谁在隐藏什么。
- 策略空间：每个玩家能做什么、不能做什么、能不能退出。
- 规则点：稳定影响选择、信息暴露、成本收益或关系走向的约束和生成机制。
- 奖惩机制：做某动作会获得什么、失去什么、把成本转嫁给谁。
- 信号机制：哪些行为、语言、身体反应、历史记录会泄露隐藏偏好或策略。
- 可能结果：合作、竞争、僵局、退出、背叛、责任转移或稳定均衡。

只有“规则点”能通过原子精度门时，才沉淀为 atom。玩家名单、单个案例、一次性策略、文章里的技巧步骤，不直接成 atom。

规则点可以来自博弈论、心理学、生理学、社会学、经济学、语言学或传播学。学科只是来源，不是 atom 分类。最终只保留可复用知识函数。

## 准确承载

旧 atom 能准确承载新候选，必须同时满足：

- 函数签名兼容：处理同类输入，执行同类操作，产出同类输出。
- 底层机制一致。
- 边界兼容。
- 复用功能一致。
- 依赖结构兼容。

只是例子不同、表达不同、来源不同，不构成新建理由。

## 原子精度门

新建 atom 前，必须通过机制精度检查。

合格 atom 不是“文章观点”，也不是“技巧命名”，而是一个可复用知识函数。它必须先能写清：

```text
输入 -> 操作 -> 输出
```

还必须能说清：

```text
触发条件 -> 中介机制 -> 可观察结果 -> 适用边界
```

如果只能写成“这个方法能帮你做某事”，不新建。

如果只是原文里的一个建议、例子、话术、标签、金句、分类名，不新建；最多并入某个 atom 的“必要说明”。

如果候选是框架或系统，只有在它的 `components` 组合后产生单个组件没有的新能力时，才创建系统 atom。不要把文章目录直接变成系统 atom。系统 atom 必须能通过 `components` 递归追溯到底层基础 atom；依赖底层学科原理时，必须通过 `depends_on` 链接到底层原理 atom。

## 批量去重

一次 compile 中，即使原来的 `atoms/` 为空，也必须先把本批候选互相比较，再写文件。

不要在“区分说明”里写“拆解前 atoms 为空”这种无效理由。区分说明必须写具体检查过哪些旧 atom 或本批候选，以及为什么它们不能承载当前 atom。

## 正文要求

每个 atom 至少写：

- 定义：它是什么。
- 边界：它不是什么，不能用于哪里。
- 底层机制：为什么成立，写清函数签名、因果链或结构约束。
- 复用价值：未来能支持哪些任务或更大 atom，并写清“调用方式”：遇到什么问题时应该引用它。
- 区分说明：为什么不是已有 atom 或本批其他候选。
- 必要说明：别名、例子、限制、来源定位、迭代入口、底层学科来源、上层系统候选。
- 依赖：列出 `depends_on` 对应 atom，空则写“无”；有依赖时用 `[[atom-id]] - 依赖理由`；底层学科原理也通过这里逐层链接，不能只写学科名。
- 组件：列出 `components` 对应 atom，空则写“无”；有组件时用 `[[atom-id]] - 组件职责`；系统 atom 必须能沿组件链追溯到底层基础 atom。

atom 如果不能让未来使用者看出“怎么调用它、它能接入哪个更大系统、它和哪些 atom 有关系”，就不合格，只能保持 `draft` 或不新建。

不要新增 `part_of`、`related`、`see_also` 等 frontmatter 字段。双向链接通过正文 wikilink、Obsidian backlinks、全库搜索和系统 atom 的 `components` 反查获得。

## 状态

只使用：

- `draft`：初次生成，尚未完整检查。
- `stable`：通过质量门、硬校验和整批验收，可以被引用。
- `deprecated`：保留追溯，不建议新引用。
- `merged`：已合并到另一个 atom。

不要使用 `rejected`。失败候选不进入 `atoms/`。

## 安全

新 atom 默认 `draft`。只有通过单 atom 质量门、硬校验和整批验收后，才能标记为 `stable`。

写入或重构后，在最终回复里说明：复用了哪些 atom、新建了哪些 atom、补齐了哪些地基 atom、升级/拆分/合并了哪些 atom、丢弃了哪些候选、还有哪些不确定。不要创建单独日志文件。

不要静默修改、合并、废弃或替换旧 atom；必须说明理由。

## 参考

完整规则见 `references/nix-knowledge-compiler-v0.md`。
