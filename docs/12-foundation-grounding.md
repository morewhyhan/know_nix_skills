# CLC 分类导航 v1.1

本文件只解释检索和 `tags` 选择，不定义 atom 本体，不充当地基词典，不决定依赖、组件、证据或真值。

唯一机器契约见 [`../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md`](../skills/nix-knowledge-compiler/references/nix-knowledge-compiler-v1.1.md)。合法 tag 真源是覆盖 22 个基本大类的 [`../skills/nix-knowledge-compiler/references/classification.md`](../skills/nix-knowledge-compiler/references/classification.md)。[`clc-reference.md`](clc-reference.md) 是历史导航简表，不是完整分类真源。

## 使用规则

- 每次检索先逐一排查 A、B、C、D、E、F、G、H、I、J、K、N、O、P、Q、R、S、T、U、V、X、Z 22 个基本大类，不能从几个常用学科直接起步。
- 对可能相关的大类展开到 `classification.md` 所列最细正式类号；按机制解决的问题分类，不按来源表面词汇分类。
- 每个 atom 使用 1–3 个 `CODE/CLC正式类名`。不确定下位码时回退到真实上位码，禁止猜码或自创码名。
- 组织行为学、社会心理学、博弈论、启发式与认知偏差等仍是重要的术语检索词，但不能作为裸 CLC tag；它们必须映射回正式 CLC 方向。
- `CLC方向` 必须记录 22 大类全表扫描、与 frontmatter 一致的主类，以及展开和排除理由。
- `tags` 不能替代 `depends_on`、`components`、学术依据或证据来源。

## 已纠正的历史错误

- `I04` 是“文学创作论”，不是“叙事学”。
- `Q98` 是“人类学”，不是“进化论与进化心理学”；生物演化应看 `Q11`，心理学应看 `B84`。
- `J0` 是“艺术理论”，美学是 `B83`。
- `V2` 是“航空”，不能改写成“航空安全工程”。
- 任何项目解释词都不能冒充 CLC 官方类名。

CLC 完整版包含数万条深层类目。本地 registry 保证所有知识首先都有 22 大类的通用入口，并覆盖项目随附简表的下位方向；需要更深类号时，AI 必须核对权威表后再补充，不能自行推测。
