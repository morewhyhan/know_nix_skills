---
name: nix-knowledge-compiler
description: Autonomously compile articles, conversations, excerpts, and thought fragments into source reconstructions plus a reusable, traceable, composable Markdown mechanism-atom store. Use when Codex should preserve enough source meaning to replace rereading, extract or name mechanisms, search the full CLC space, maintain atoms without user curation, reuse or refactor existing atoms, validate cross-domain transfer, query the store, or repair its dependency and evidence structure.
---

# Autonomous Mechanism Atom Compiler

把材料同时编译成可替代原文的还原稿和可复用的知识函数，并由 AI 全自动维护。用户只提供材料或任务；不要要求用户筛候选、审稿、选关系、补字段、决定是否入库或维护状态。

## 模式

- `compile`：读取材料，自动生成或更新 `reconstructions/`，并复用、创建、更新、合并和验证 atom。
- `reuse`：只检索并解释已有 atom，不写入。
- `query`：调用已有 atom 回答问题，不写入。
- `validate`：运行语义检查与确定性校验，自动修复授权范围内的问题。
- `refactor`：自动拆分、合并、升级或废弃 atom。

意图不明确时用 `reuse` 或 `query`；只有明确要求处理或沉淀材料时进入 `compile`。

## 必读资源

- 执行 `compile`、`validate` 或 `refactor` 前，完整读取 [references/nix-knowledge-compiler-v1.1.md](references/nix-knowledge-compiler-v1.1.md)。
- 任何检索、命名或 `tags` 分配都完整读取 [references/classification.md](references/classification.md)，先扫描 CLC 22 个基本大类，再展开相关正式类号；不能只列几个常用方向。
- 写 atom 时使用 [assets/knowledge-atom.md](assets/knowledge-atom.md)。
- 写来源还原稿时使用 [assets/article-reconstruction.md](assets/article-reconstruction.md)。
- 写入后，从当前 `SKILL.md` 的绝对目录定位 validator。Windows PowerShell 运行 `& <skill-dir>/scripts/validate_store.ps1 -Root <workspace-root>`；其他环境用可用的 Python 3 运行绝对路径 `<skill-dir>/scripts/validate_store.py --root <workspace-root>`。AI 自动选择可用 runtime，不把安装或选择 Python 交给用户。

## 核心本体

atom 是可复用知识函数，不是标题、概念标签、文章观点、方法清单或漂亮摘要。每个有效 atom 必须能写成：

```text
输入 -> 操作 -> 输出
触发条件 -> 中介机制 -> 可观察结果 -> 适用边界
```

- 基础 atom：已经是完整的最小知识函数；再拆会失去输入、操作或输出。`components: []`。
- 系统 atom：多个下层 atom 组合后产生单个组件不具备的新能力。`components` 非空。
- `depends_on` 只放理解或调用当前 atom 真正必需的前置知识函数。
- 学科名、普通术语和正文中已自足定义的词，不自动变成地基 atom。
- 不使用 L0-L5 硬编码层级；层级从依赖图推导。
- 所有 atom 的 15 个机器章节名固定为中文；ID、标题、别名和章节内容跟随来源主语言。

## 双层产物

- `reconstructions/` 保存理解来源所必需的核心结论、论证链、关键概念、建议、适用范围、证据风险和 atom 映射；读者应能不看原文回答核心问题。
- `atoms/` 只保存跨来源可复用的机制函数。文章观点、修辞、案例和只有建议没有结果证据的内容留在还原稿，不污染 atom。
- compile 只有在还原覆盖与 atom 复用两条质量门都通过后才结束。

## 命名与 CLC

- 先按 CLC 全表路由，再在入选与邻接学科核验术语。
- ID 优先级固定为：与机制精确一致的既有学科术语 > 已有通俗口语 > 清楚的描述性短语 > 编译器自造词。
- 只有“相关”但不完全同构的专业词不能冒充 ID；应拆分、作为近邻说明，或使用下一优先级。
- aliases 同时保留专业近义词、来源原话和普通人会搜索的口语；不能全部是 ID 的技术改写。
- `tags` 只使用 `CODE/CLC正式类名`，专业词不能以裸标签冒充 CLC。

## AI 内部编译闭环

下面各阶段全部由 AI 完成。中间候选、独立复核和争议裁决是内部状态，不交给用户维护。

### 1. 来源预检

完整读取来源，记录可解析的绝对路径、workspace 相对路径或 URL。发现转写残缺、内部矛盾、事实断言和观点性语言时标记证据风险；不得静默补全或把作者断言当事实。

### 2. 来源还原

先生成来源还原稿，覆盖核心结论、完整论证顺序、关键概念、建议与适用范围、作者断言、证据缺口和文本问题。不得因某项内容不能成为 atom 就从还原稿删除。

### 3. 独立提取

先通读，再逐段扫描。只保留能同时写清函数签名和机制链的候选；丢弃标签、修辞、案例、话术、建议步骤和文章目录。

### 4. 独立来源复核

如果可以使用 subagent，委派一个只看原文、不看提取结果的来源审查者，独立给出：核心机制、应丢弃内容、证据不足点和合理粒度上限。不可用 subagent 时，由主 agent 用隔离的第二遍阅读完成来源复查，但这不算“独立语义复核”，本批 atom 只能保持 `draft`。

### 5. CLC 全表、术语与复用审查

先扫描 CLC 22 个基本大类，再展开可能相关的正式类号并核验现成学科术语。如果可以使用 subagent，委派另一个审查者读取原文和 `atoms/`，按 CLC、名称、别名、函数签名、机制、角色、条件和跨领域同构检索。不可只依赖 `depends_on`，也不可因零重叠直接新建。

旧 atom 只有在函数签名、机制、边界、复用功能和依赖结构兼容时才复用。相同结果、相似句式或换了领域词不算复用。

### 6. 主控裁决

主 agent 比较独立结果并自动裁决：

- 有冲突时优先来源忠实、较少 atom、较窄边界和较低证据强度。
- 缺少中介机制或可观察结果的候选不写入。
- 只有建议、没有结果证据的内容保留在来源说明，不建 atom。
- 真正缺少前置知识函数时，AI 自动复用或补齐地基；证据不足时不凭空造地基。

### 7. 证据分层与跨域验证

正文必须区分：

- `来源支持`：来源直接陈述或展示。
- `编译器推导`：AI 从来源抽象出的中介机制。
- `独立材料验证`：另一份独立材料实际支持相同机制。
- `机制推演`：只完成角色替换和逻辑演绎，尚未被独立材料支持。
- `待验证`：事实、因果、学术或边界缺口。

机制推演不能冒充独立验证。只有来源域支持时，保持 `draft`，并在领域绑定中标明其他行是 `机制推演`。

### 8. 事务式写入

在内存中完成整批去重、关系和正文后再写文件。新 atom 默认 `draft`。写前保存所有待修改旧文件的原始字节；先写同目录临时文件并校验，再原子替换目标。

- 精确承载：复用旧 atom，并追加来源与验证信息。
- 机制相同但边界过窄：自动升级旧 atom。
- 机制身份实质变化：创建新版本，旧版本标记 `deprecated` 或 `merged`。
- 失败候选不进入 `atoms/`，不创建 `rejected` 文件。

### 9. 自动验证与返工

写入后执行三类检查：

1. 原文替代盲测：只看原文的审题者出核心问题，只看还原稿的答题者作答，裁判检查核心问题全通过、总体正确率至少 90%、无反向理解、无把作者断言冒充事实、无静默修复原文矛盾。
2. atom 语义检查：来源忠实、术语命名、原子粒度、复用充分、假迁移、证据强度、依赖与组件职责。准备升级 `stable` 时，必须由未参与成稿的 subagent 完成独立语义复核，并把结果与范围写入“必要说明”。
3. 硬校验：运行 bundled validator，检查 atom 与 reconstruction 的结构、来源哈希和链接。

失败时由 AI 自动修复并重跑，最多两轮。仍失败时，恢复所有被修改旧文件的原始字节并删除本轮新增文件；不得留下半批状态。最终只报告未写入及原因，不要求用户修文件。

## 生命周期

- `draft`：单一来源、存在待验证项或尚未独立复核。
- `stable`：硬校验通过，未参与成稿的 subagent 已完成并记录“独立语义复核：通过”，机制身份与边界稳定，并满足以下任一证据条件：
  - 至少两个本地可解析且 identity、内容哈希均不同的来源文件支持同一机制，且来源支持与独立材料验证行精确绑定到两个不同 source；或
  - 权威原理来源支持机制，并有一份实际领域材料验证。
- `deprecated`：保留追溯，不再建议引用。
- `merged`：内容已并入另一个 atom。

每次新材料进入时，AI 自动检查相关 draft 是否获得了新来源、是否应升级为 stable、是否应合并或收窄边界。用户不参与日常维护。

## 用户可见结果

最终只报告：读取了哪些来源；生成或更新了哪些还原稿；复用、新建、更新、合并或丢弃了哪些 atom；原文替代盲测和 validator 是否通过；仍有哪些证据缺口。不要把内部候选清单、盲审流程或维护任务交给用户。

## 安全边界

- 只写当前 workspace 的 `atoms/`、`reconstructions/` 和本 skill 明确授权的维护文件。
- 不修改无法解析的来源文件。
- 不把评论性文章的法律、医疗、金融、制度或科学断言当成已验证事实。
- 不静默覆盖、合并或废弃用户已有 atom；在最终回复中说明自动决策和理由。
