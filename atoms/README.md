# Atoms

这是当前知识库的核心目录。

v0.3 只强制保留 atom。基础原子、组合原子、系统级原子都放在这里。

判断方式：

- `components: []`：基础 atom。
- `components` 不为空：由下层 atom 组成的大 atom。

每个 atom 最小 frontmatter：

```yaml
id:
status:
source:
depends_on:
components:
```

不要按 `concept / claim / mechanism / system` 建核心分类。内容形态不是系统骨架。
