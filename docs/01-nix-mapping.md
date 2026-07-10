# Nix 思想到机制知识系统的映射 v1.1

本项目只借用 Nix 的构建纪律，不声称复制 Nix 的软件构建模型。唯一机器契约见 [`../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md`](../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md)。

## 保留的映射

| Nix 思想 | 本系统中的实现 |
|---|---|
| 明确输入 | `source` 保存可解析路径或 URL 列表 |
| 稳定身份 | `id` 与文件名一致，非破坏性更新保持 ID |
| 正向引用 | `depends_on` 与 `components` 明确保存 |
| 复用优先 | 新建前执行名称、别名、签名、机制、角色、条件和跨域检索 |
| 事务写入 | 快照旧文件原始字节，以同目录临时文件校验后原子替换；失败恢复旧字节并删除新增 |
| 构建校验 | 写入后自动执行未参与成稿的 subagent 独立语义复核、硬校验和整批验收 |
| 生命周期 | `draft`、`stable`、`deprecated`、`merged` 由 AI 维护 |

## 不做的映射

- 不把文件路径当内容哈希。
- 不建立 derivation、profile、overlay、binary cache 等目录。
- 不把所有语义变化都强制生成新版本。
- 不用严格 L0-L5 模拟依赖层级。

## 图上计算

系统只手写正向关系：

- 理解前提写 `depends_on`。
- 结构组成写 `components`。
- 反向引用、闭包和被使用关系由检索计算，不写冗余字段。

基础机制可以没有 components。复合系统只有在组合产生新能力时才建立，且必须能沿 components 展开。

## 证据与可复现边界

`source` 的每一项都必须能被再次解析；独立复核使用的来源也进入列表。URL 只供 draft 追溯，stable 至少需要两个路径 identity 与内容哈希都不同、且本地可解析的来源文件；同一文件的不同写法或同内容副本不能凑数。当前没有任何可解析来源时不得新写 atom；既有 atom 的来源后来失效时，AI 将其降为 draft、记录缺口并寻找替代来源，不能把失效地址继续当成可复核输入。

Nix 启发的是“输入清楚、关系显式、复用优先、失败自动返工”，项目的知识内核仍然是机制提取、证据裁决和跨领域迁移验证。
