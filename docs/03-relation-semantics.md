# 关系语义

v0.3 只保留能支撑复利的最小正向关系。

## 保留的关系

### source

当前 atom 的来源指针。

它可以指向：

- 一篇文章。
- 一段对话。
- 一个书摘。
- 一个外部 URL。
- 一个已有 atom。

`source` 不要求保存原文全文，只要求未来能知道这个 atom 从哪里来、如何回查、如何迭代。

### depends_on

当前 atom 依赖哪些前置 atom。

标准：

> 没有对方，当前 atom 不能被完整理解或使用。

不要把“同主题”“相关”“类似”写成依赖。

### components

当前 atom 由哪些下层 atom 组成。

标准：

> 删除某个 component，会让当前 atom 的结构或能力不完整。

系统级 atom 不单独建文件类型。它只是 `components` 不为空的大 atom。

## 不保留的关系

这些不手写：

- `used_by`
- `part_of`
- `reuse_count`
- `closure`
- `system_scope`
- `related`
- `see_also`

原因：

- `used_by` 可以从全库反向引用算出。
- `part_of` 可以从其他 atom 的 `components` 反查。
- `reuse_count` 可以从反向引用数量统计。
- `closure` 可以从 `depends_on` 递归计算。
- `system_scope` 可以从组件图推断。
- `related` 和 `see_also` 太松，会污染图谱。

## 关系方向

只写正向关系。

```yaml
source:
  title: ...
  locator: ...
depends_on:
  - atom-a
components:
  - atom-b
```

不要写反向关系。反向关系交给工具或 AI 从全库计算。

## 关系质量测试

每条关系都问：

> 如果删除这条关系，系统会失去什么具体能力？

答不上来，就不要写。
