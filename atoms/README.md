# Atom Store v1.1

`atoms/` 是当前工作区唯一的 atom store。所有 atom 平铺保存，不按主题或层级分目录。

唯一机器契约见 [`../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md`](../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md)。

## Atom 是知识函数

每个 atom 都必须能独立表达：

```text
输入 -> 操作 -> 输出
触发条件 -> 中介机制 -> 可观察结果 -> 适用边界
```

词语、人物、文章标题、一次性建议和只有领域标签的节点不单独进入 store。

## 唯一 Frontmatter

```yaml
id: 机制短名称
status: draft
source:
  - docs/00-system-brief.md
tags:
  - N94/系统科学
aliases:
  - 常见别名一
  - 常见别名二
depends_on: []
components: []
```

- `source`：可解析的工作区路径、绝对路径或直接 URL 列表；优先使用稳定的工作区相对路径。URL 只供 draft 追溯，stable 必须至少有两个路径 identity 与内容哈希都不同、且本地可解析的来源文件。
- `tags`：先扫描 CLC 22 个基本大类，再从 [`../skills/nix-knowledge-compiler/references/classification.md`](../skills/nix-knowledge-compiler/references/classification.md) 选择 1–3 个 `CODE/CLC正式类名`；不接受裸学科词，不决定本体、粒度、地基或真值。
- `aliases`：填写 2–6 个真实检索入口，至少包含一种普通人会说或输入的口语。
- `depends_on`：理解或调用当前函数必须先掌握的 atom。
- `components`：共同执行当前复合函数的下层 atom。

不要添加 `type`、`level`、`used_by`、`part_of`、`related`、`closure` 等字段。

## 基础机制与复合系统

- 一个机制已经是完整、不可再拆的知识函数时，可以 `components: []`。
- 只有组件组合后产生单个组件不具备的新能力时，才创建复合系统，并令 `components` 非空。
- 不采用严格 L0-L5。是否继续展开由任务和函数完整性决定。

## 正文

所有处于 `draft` 或 `stable` 的新 atom 使用固定 15 个中文 H2 机器键；文件名、ID、H1、别名和章节内容跟随来源主语言：

```text
场景用途 / CLC方向 / 定义 / 边界 / 机制核心 / 参与角色 / 成立条件 /
迁移边界 / 复用价值 / 领域绑定 / 脱域说明 / 区分说明 / 必要说明 / 依赖 / 组件
```

不适用的章节仍保留，并明确写出“不适用”的理由，避免不同类型产生不同解析结构。`deprecated` 或 `merged` 历史记录可按唯一机器契约省略机制四段，但必须保留身份、来源、去向和迁移理由。

机器解析章节与标签时忽略 fenced code 和 HTML comment，示例或注释不能充当正式结构。

“必要说明”必须包含：证据状态、来源支持、编译器推导、待验证、学术线索、命名依据、常见别名、独立语义复核；八个标签各且仅出现一次。命名依据按“精确学科术语＞通俗用语＞描述性命名＞编译器造词”说明。`独立语义复核` 只有未参与成稿的 subagent 可以标记“通过”。

领域绑定中 `来源支持` 与 `独立材料验证` 行的证据定位必须以精确 frontmatter source locator 或无歧义 basename 开头，并解析到路径 identity 与内容哈希都不同的来源。

## 状态

- `draft`：结构可读，但仍有证据、复用、迁移或关系待验证。
- `stable`：至少两个路径 identity 与内容哈希都不同、且本地可解析的来源文件、合格定位的实际验证绑定、未参与成稿的 subagent 独立语义复核和硬校验均通过，可被默认调用；URL 不计来源硬门。
- `deprecated`：保留追溯，不再建议新调用。
- `merged`：已并入另一个 atom，正文说明去向和理由；去向链必须无环，并最终终止于 `draft` 或 `stable` 活动 atom。

AI 自动维护状态。用户不需要审批候选或手工维护关系。
