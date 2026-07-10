# ID、版本与生命周期 v1.1

唯一机器契约见 [`../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md`](../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md)。

## ID

- 文件名、ID、H1、别名和章节内容使用材料主语言，ID 简短但能区分机制；15 个 H2 机器键始终固定为中文。
- 文件名必须等于 `id + ".md"`。
- 初版 ID 不强制 `-v1`；已经存在的 `-v1` ID 可以保留。
- 同名不同机制必须加入能说明函数差异的限定词，不能靠文件夹或 tags 消歧。

## 何时不升版本

以下属于兼容更新，保持原 ID：

- 改善措辞和例子。
- 增加来源、别名或已验证领域绑定。
- 补充边界但不改变既有合法调用。
- 修复断链、关系理由或证据标签。
- 将待验证项验证为支持或否定。

## 破坏性新版本

只有下列变化导致旧调用可能得出不同结果时，才创建 `-v2`：

- 输入、操作或输出发生实质变化。
- 中介机制被替换。
- 关键成立条件或迁移边界改变。
- 依赖或组件结构改变了 atom 的身份。
- 原 atom 实际混合了多个机制，需要保留兼容入口。

AI 自动判断版本并修复引用，不要求用户管理版本号。

## 状态

| status | 含义 |
|---|---|
| `draft` | 结构已进入 store，但有明确证据、迁移或语义待验证，或尚无未参与成稿的独立审查者 |
| `stable` | 至少两个路径 identity 与内容哈希都不同、且本地可解析的来源文件、合格定位的实际验证绑定、独立语义复核和硬校验全部通过 |
| `deprecated` | 保留历史追溯，不建议新调用 |
| `merged` | 已被另一 atom 准确承载，正文写明去向；去向链无环并最终终止于 `draft` 或 `stable` 活动 atom |

stable 不代表永恒真理。新证据出现时，AI 自动复核并可降为 draft、标记 deprecated、合并或创建新版本。

## 自动生命周期

```text
候选 -> draft
draft -> stable
draft -> 自动返工或丢弃
stable -> draft（证据门重新打开）
stable -> deprecated / merged / -v2
```

每次 compile、validate 或 refactor 后，AI 检查受影响 atom 的本地来源 identity 与内容哈希、证据独立性、独立语义复核、`merged` 去向链、关系完整性和状态资格，并自动更新。URL 只供 draft 追溯，不计 stable 来源硬门；只有未参与成稿的 subagent 可以把 `独立语义复核` 标记为“通过”。
