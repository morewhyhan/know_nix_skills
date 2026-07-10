# 关系语义 v1.1

唯一机器契约见 [`../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md`](../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md)。

## 机器可读关系

核心图只使用两个 frontmatter 字段：

### `depends_on`

理解或调用当前知识函数所必需的前置 atom。删除该依赖后，当前函数将无法被正确解释或执行。

### `components`

共同执行当前复合函数的组成 atom。删除关键组件后，复合系统将失去结构或能力。

基础机制 atom 可以 `components: []`。只有真正的复合系统才必须非空。系统不使用严格层级编号，关系合法性由函数职责和无环性判断。

## 正文语义标注

正文“依赖”“组件”“区分说明”使用：

```markdown
- [[atom-id]] - 关系类型：具体理由
```

推荐关系类型：

- 组件：`composed_of`、`implements`、`instantiates`
- 前提：`prerequisite`、`defined_by`、`grounded_in`
- 逻辑：`supports`、`constrains`、`explains`、`contrasts_with`

语义标注不能替代 frontmatter。属于依赖或组件的链接必须同时出现在对应列表和正文中；只作区分、支持或对照的链接不必塞入核心图。

## 关系判定

每条边都必须回答：

> 删除这条关系后，当前 atom 会失去什么具体理解或能力？

答不出来就不建立核心边。相似、同主题、同领域或能互相启发，都不足以成为 `depends_on` 或 `components`。

## 跨领域绑定

跨领域关系写在“领域绑定”表，不新增 frontmatter 字段。每行必须包含证据标签：

| 证据标签 | 含义 |
|---|---|
| 来源支持 | 输入材料直接支持该绑定；定位以精确 frontmatter source locator 或无歧义 basename 开头 |
| 独立材料验证 | 独立于输入的材料验证了角色、条件和结果；定位以精确 locator 或无歧义 basename 开头 |
| 机制推演 | 编译器按结构映射提出，尚未验证 |

`来源支持` 与 `独立材料验证` 必须解析到路径 identity 与内容哈希都不同的来源。`机制推演` 不算验证。跨领域绑定只有在参与角色、成立条件、中介机制和函数输出保持同构时才成立；若输出从“吸引”变成“谨慎、服从、学习”等不同结果，默认判为假迁移或另一个机制族。`instantiates` 只用于目标确实作为当前系统 atom 下层组件的关系，不能仅因绑定获得验证就写入 `components`。

## 图约束

- `depends_on` 与 `components` 指向的 atom 必须存在。
- 两者不得形成循环。
- 正文与 frontmatter 必须一致。
- 反向引用、闭包和使用次数由图计算，不手写。
- 合并或废弃后，AI 自动修复受影响的正向关系。
- `merged` 去向链必须无环，并最终终止于 `draft` 或 `stable` 活动 atom。
