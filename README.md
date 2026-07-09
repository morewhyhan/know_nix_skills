# Nix Knowledge Compiler

这是一个 Nix 哲学启发的知识原子化工程。

最终目标不是整理文章，而是把文章、对话、摘录、想法等输入材料，编译成可以长期复用、组合、依赖和演化的 Markdown 知识原子。这个仓库的核心不是“分类”，而是 **可复用知识函数 + 依赖图 + 组件闭包 + 复用优先**。

## 当前结论

这是一个 Codex skill 驱动的本地工作区系统。你在哪个项目根目录打开 Agent，它就只在那个根目录下创建和维护知识库文件。

核心结构先收敛为一个文件夹：

```text
atoms/
```

这里的 `atoms/`、`docs/`、`templates/`、`schemas/`、`skills/` 都是相对于当前工作区根目录的路径，不是全局目录。

每个 atom 都可以是基础原子，也可以是由其他 atom 组成的大原子。所谓“系统”，不是另一类文件；系统只是 `components` 不为空的高层级 atom。

原始材料不单独建文件。只保留来源指针，写进 atom 的 `source` 字段。原文、对话、摘录只是输入，不是知识资产。

## 最小字段

每个 atom 最少保留：

```yaml
id:
status:
source:
depends_on:
components:
```

- `id`：稳定身份，不能靠标题引用。
- `status`：维护状态，支持草稿、稳定、废弃、合并。
- `source`：来源指针，不必保存全文。
- `depends_on`：理解或使用当前 atom 需要哪些前置 atom。
- `components`：当前 atom 由哪些下层 atom 组成。

能从依赖图推出来的东西不手写：`used_by`、`reuse_count`、`closure`、`part_of`、`system_scope` 都不保留。

## 必要规则

字段足够少，但系统必须有一组运行规则。

1. **构建规则**：输入材料进入后，AI 必须按统一标准判断候选内容是否值得成为 atom，太大则拆，太碎则并入说明，不够复用则不建。
2. **复用优先**：创建新 atom 前，必须先查旧 atom。能被旧 atom 准确承载，就复用旧 atom，不新建。
3. **写入安全**：新 atom 默认是 `draft`，通过质量门、硬校验和整批验收后才能 `stable`。
4. **失败不入库**：不合格候选直接丢弃或并入正文说明，不创建 `rejected` atom，也不为失败候选建文件。
5. **地基补齐**：新建上层 atom 前，必须确认它的前置原理已存在；缺少底层学科原理时，先补齐地基 atom，再创建上层 atom。
6. **AI 调用协议**：未来任务先检索相关 atom，再按需要展开 `depends_on` 或 `components`，避免读取无关图谱。

复利来自第二条：旧 atom 降低新知识的处理成本，并被未来任务反复组合调用。

## 文档入口

- `docs/00-system-brief.md`：最小系统说明。
- `docs/01-nix-mapping.md`：Nix 思想如何映射到本工程。
- `docs/02-atom-standard.md`：什么内容有资格成为 atom。
- `docs/03-relation-semantics.md`：保留哪些正向关系。
- `docs/04-compile-workflow.md`：输入材料如何编译成 atom。
- `docs/05-quality-gates.md`：质量检查规则。
- `docs/06-build-decision-rules.md`：复用、新建、升级、拆分、合并、丢弃的判定规则。
- `docs/07-operation-modes-and-safety.md`：skill 模式、写入安全、硬校验、事务规则。
- `docs/08-reuse-search.md`：旧 atom 检索、复用判断、别名、来源保存边界。
- `docs/09-id-lifecycle-iteration.md`：ID、版本、生命周期、可观察、迭代、冲突、循环规则。
- `docs/10-usage-experience-and-validation.md`：AI 调用、整批验收、系统 atom、Obsidian 展示。
- `docs/11-goal-contract.md`：最终目标、v0 交付物、成功标准和失败标准。
- `docs/12-foundation-grounding.md`：底层学科地基、前置依赖补齐和逐层追溯规则。
- `templates/knowledge-atom.md`：最小 atom 模板。
- `schemas/atom-frontmatter.yaml`：最小 frontmatter schema。
- `skills/nix-knowledge-compiler/`：Codex skill 文件。

## 一句话

最终只保留 atom。每个 atom 有 ID、状态、来源、依赖、组成。其他能从图里推出来的东西都不写。失败候选不进入 atom store。
