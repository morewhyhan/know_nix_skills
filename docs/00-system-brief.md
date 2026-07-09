# Nix 式知识原子系统 v0.3

## 一句话目标

建立一个 Nix 哲学启发的知识函数库：把输入文字编译成稳定、可复用、可组合、依赖显式的 Markdown atom，让旧 atom 能降低新知识的处理成本，并持续参与更大 atom 的构建。

完整目标契约见 `docs/11-goal-contract.md`。这份系统说明只描述最小结构和运行条件。

## 当前最小结构

这是一个在当前工作区根目录内运行的 skill，不是全局知识库服务。

用户在哪个根目录打开 Agent，skill 就在哪个根目录内读写知识库文件。默认不跨项目、不写到其他仓库、不写到用户全局目录。

核心结构只保留：

```text
atoms/
```

`atoms/` 是相对于当前工作区根目录的路径。

原始材料不单独建 `sources/`。系统级内容不单独建 `systems/`。系统就是一种高层级 atom：它仍然放在 `atoms/`，只是 `components` 不为空。

## 最小 atom

每个 atom 最少包含：

```yaml
id:
status:
source:
depends_on:
components:
```

正文最少包含：

- 定义：它是什么。
- 函数签名：它的输入、操作、输出是什么。
- 边界：它不是什么，容易和什么混淆。
- 底层机制：它为什么成立，写清因果链或结构约束。
- 复用价值：它为什么值得单独保存，未来能支持哪些任务或更大 atom。
- 区分说明：它为什么不是已有 atom 或本批其他候选。
- 必要说明：别名、例子、限制、来源定位、迭代入口。
- 依赖：列出 `depends_on` 对应 atom，空则写“无”。
- 组件：列出 `components` 对应 atom，空则写“无”。

“复用价值”必须写清调用方式：未来遇到什么问题时应该引用这个 atom。看不出怎么使用的节点，不是合格 atom。

基础 atom 是不可再拆的最小知识函数，`components: []`。系统 atom 是多个知识函数组合出的更大函数，`components` 不为空。任何系统 atom 都必须能沿 `components` 和 `depends_on` 追溯到底层基础 atom 或底层学科原理 atom。

## Nix 思想迁移

这个工程只迁移 Nix 中真正必要的思想：

1. **输出有稳定身份**：atom 必须有稳定 `id`，标题不能当身份。
2. **输入可追溯**：atom 必须有 `source` 指针，但不一定保存完整原文。
3. **正向依赖显式**：atom 必须声明 `depends_on`，不能偷偷依赖上下文。
4. **组合关系显式**：大 atom 通过 `components` 声明由哪些下层 atom 组成。
5. **闭包由图计算**：依赖闭包不手写，从 `depends_on` 递归计算。
6. **反向引用由图反查**：`used_by`、`part_of`、`reuse_count` 不手写。
7. **复用优先**：新输入先查旧 atom，能复用就不新建。
8. **机制精度优先**：新 atom 必须能写清“触发条件 -> 中介机制 -> 可观察结果 -> 适用边界”，不要按文章标题、方法步骤或案例建 atom。
9. **互动结构优先于技巧摘录**：互动、关系、商业、策略材料要先抽玩家、目标、信息、策略空间、规则点、奖惩和信号，再把可复用知识函数沉淀为 atom。
10. **链接能力是复用能力的一部分**：正文依赖和组件使用 `[[atom-id]]`，底层学科也通过逐层 atom 链接进入图；反向关系由 Obsidian backlinks、全库搜索和 `components` 反查获得，不新增反向字段。
11. **函数闭包必须可追溯**：上层 atom 必须通过 `components` 和 `depends_on` 追溯到 `components: []` 的基础 atom，以及必要的底层学科原理 atom。
12. **缺地基先补地基**：如果上层 atom 依赖的底层学科原理还没有 atom 承载，先创建或复用地基 atom，再创建上层 atom。

## 不保留什么

以下内容不进入 v0.3 核心：

- `type: concept | claim | mechanism | pattern | system`
- `object_kind`
- `level`
- `content_shape`
- `system_scope`
- `used_by`
- `reuse_count`
- `feedback`
- `part_of`
- `closure`
- 单独的 `relation` 文件
- 单独的 `derivation` 文件
- 单独的 `view` 文件
- 单独的 `module` 文件
- 单独的 `runs/` 目录
- 单独的 `indexes/` 目录
- 单独的 `maps/` 目录
- 单独的 `examples/` 目录
- 单独的 `sources/` 目录

它们要么能从目录或依赖图推出来，要么现在过早，要么会诱导 AI 做无用分类。

## 复利定义

知识复利不是 atom 数量变多，而是：

- 新材料优先复用旧 atom。
- 多个 atom 能组合成更大的 atom。
- 大 atom 还能继续被更大的 atom 引用。
- AI 和人能在任务中调用已有 atom，而不是重新解释。

最小可观察信号是：一个 atom 被其他 atom 的 `depends_on` 或 `components` 引用。

## 充分运转条件

这个系统要正常运转，必须满足：

1. 有 atom store：所有知识函数有统一存放处。
2. 有稳定 ID：每个 atom 可以被稳定引用。
3. 有来源指针：每个 atom 能追溯来源。
4. 有依赖关系：理解当前 atom 需要哪些前置 atom。
5. 有组成关系：大 atom 由哪些下层 atom 组成。
6. 有构建规则：AI 按 `docs/06-build-decision-rules.md` 判断丢弃、复用、升级、新建、拆分、合并。
7. 有复用检索：创建前按 `docs/08-reuse-search.md` 查旧 atom。
8. 有写入安全：新 atom 默认 `draft`，按 `docs/07-operation-modes-and-safety.md` 验收后才能 stable。
9. 有生命周期：ID、版本、合并、废弃按 `docs/09-id-lifecycle-iteration.md` 演化。
10. 有使用协议：AI 调用和整批验收按 `docs/10-usage-experience-and-validation.md` 执行。
11. 有目标契约：用 `docs/11-goal-contract.md` 判断 v0 是否真的完成。
12. 有可调用性：每个 atom 必须说明未来怎么使用，以及能接入哪个上层系统。
13. 有双向链接入口：不手写反向字段，但正文 wikilink 和系统 atom 的 `components` 必须足以让 Obsidian 反查。
14. 有函数闭包：系统 atom 不能是黑箱，必须能一路追溯到底层基础 atom。
15. 有地基补齐规则：缺少底层学科原理 atom 时，先补齐地基，再写上层 atom。

少了前五个，知识库无法形成依赖图。少了后十个，知识库会变成漂亮但不稳定、难以复利的文件堆。

## 参考来源

- Nix manual: https://nix.dev/manual/nix/latest/
- Nix store documentation: https://nix.dev/manual/nix/latest/store/
- Nix derivations: https://nix.dev/manual/nix/latest/language/derivations
- NixOS manual: https://nixos.org/manual/nixos/stable/
- Eelco Dolstra, The Purely Functional Software Deployment Model: https://edolstra.github.io/pubs/phd-thesis.pdf
