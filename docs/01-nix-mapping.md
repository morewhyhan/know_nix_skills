# Nix 到知识系统的映射

这份映射只保留对当前工程有用的部分。目标不是完整复刻 Nix，而是借用 Nix 的可靠构建思想。

| Nix 概念 | 在 Nix 中的作用 | 在本工程中的映射 |
|---|---|---|
| input/source | 构建输入 | atom 的 `source` 指针 |
| derivation | 构建规则和输入输出说明 | skill 的构建规则，不单独建文件 |
| store path | 稳定定位构建结果 | atom 的稳定 `id` |
| store object | 构建结果及其 references | Markdown atom 文件 |
| references | store object 指向其他对象 | `depends_on` 和 `components` |
| closure | 一个对象的完整依赖集合 | 从 `depends_on` 递归计算，不手写 |
| referrers | 谁引用了当前对象 | 从全库反查，不写 `used_by` |

## 最重要的迁移

### 1. 原文不是 atom

原文、引用、对话、摘录只是输入。它们可以被记录为 `source` 指针，但不直接成为知识资产。

atom 是经过压缩、边界校准、依赖声明后的构建结果。

### 2. 系统也是 atom

不单独保留 `systems/` 作为核心结构。一个系统级知识函数仍然是 atom，只是它有 `components`。

这更符合递归组合：小 atom 组成大 atom，大 atom 继续参与更大的 atom。

### 3. 能由图算出来的不要手写

Nix 不要求一个对象自己写“谁使用了我”。它保存正向 references，反向引用和 closure 从图里算。

本工程同样如此：

- 写 `depends_on`，不写 `closure`。
- 写 `components`，不写 `part_of`。
- 写正向引用，不写 `used_by`。
- 写关系，不写 `reuse_count`。

### 4. 复用优先是复利核心

Nix 能复用已有构建结果就不重新构建。

知识系统也一样：输入材料进来后，先查是否已有 atom 能准确承载。能复用就复用；旧 atom 不够精准时，才创建新 atom 或升级旧 atom。

## 当前不映射的 Nix 概念

这些概念不进入 v0.3 核心：

- flake
- profile
- overlay
- binary cache
- module
- separate derivation file
- garbage collection

删除原因：它们不能直接提高 atom 的稳定身份、来源追溯、依赖显式、递归组合或复用优先，进入 v0 只会让系统过度工程化。

## 一句话

本工程只保留 Nix 的骨架思想：稳定身份、来源可追溯、正向依赖、递归组合、图上计算、复用优先。
