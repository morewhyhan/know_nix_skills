# Skill v0.1 规格入口

状态：**已实现并通过 v0.1 回归测试。**

这一版完全从 [黄金样本 001](../../golden-cases/001-shenxiu-huineng/README.md) 反向提炼，不继承旧 NIX 的目录、本体、字段或工作流。

## 文件

- [PRODUCT-CONTRACT.md](PRODUCT-CONTRACT.md)：产品目标、输入输出、行为边界与完成定义。
- [KNOWLEDGE-MODEL.md](KNOWLEDGE-MODEL.md)：机制卡、系统卡、关系、证据和生命周期。
- [WORKFLOW.md](WORKFLOW.md)：一次处理从读入到事务写入的完整流程。
- [QUALITY-GATES.md](QUALITY-GATES.md)：一票否决项、语义验收与回归测试。
- [GOLDEN-MAPPING.md](GOLDEN-MAPPING.md)：黄金样本已经证明什么、距离新契约还缺什么。
- [COMPLETION-AUDIT.md](COMPLETION-AUDIT.md)：v0.1 每项完成条件的实现与验证证据。
- `templates/`：Skill 实际写入 Markdown 时使用的规范模板；发布副本位于 `skills/mechanism-network-builder/assets/`。

## v0.1 的一句话

> 把零散文本变成可读、可追溯、可迁移、可组合的机制知识网络，并让不同领域的机制组合出能够解决新问题的系统。

## 实现状态

1. 黄金样本 001 已按新模板规范化并迁入正式知识库。
2. 与反脆弱无关的洪水分流价值冲突样本已通过。
3. “没有合格机制，所以不建卡”的负例已通过。
4. 正式 Skill、结构校验器、语义回归和事务回滚脚本均已建立。
5. 组合设计仍按 `draft` 管理，真实效果需要在后续材料和应用中持续验证。
