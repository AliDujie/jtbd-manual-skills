# jtbd-manual-skills

配合《JTBD 实战手册》做的一套 JTBD 实战 skill，共 19 件，随公众号连载「心法记」逐步放开。

每个 skill 对应书里的一个关卡：文章讲"为什么这么做、现场长什么样"，skill 装"每一步怎么做、做到什么算合格、怎么自检"。两者配套用，单用也可以——每个 skill 都写了触发条件和边界，不缺上下文，也不需要其他任何 skill 配合。

## 现在有哪些

已放开 5 件，覆盖连载第 01–06 篇（手册关卡 0–3）：

| 目录 | 对应篇目 | 关卡 | skill | 干什么用 |
|------|---------|------|-------|---------|
| `01-jtbd-manual` | 01 序言 | 总入口 | jtbd-manual | JTBD 全流程路由：判断任务该走哪一关 |
| `02-jtbd-boundary-check` | 02 | 关卡 0 | jtbd-boundary-check | 五问自检：这个问题该不该用 JTBD |
| `03-04-jtbd-hypothesis-decompose` | 03、04 | 关卡 1 | jtbd-hypothesis-decompose | 把业务方一句话拆成 6 个可证伪假设 |
| `05-jtbd-sampling-design` | 05 | 关卡 2 | jtbd-sampling-design | 访谁、访多少、怎么招、翻车了怎么补 |
| `06-jtbd-interview-guide` | 06 | 关卡 3 | jtbd-interview-guide | Switch/ODI/Churn 三型访谈提纲生成 |

第 07–20 篇对应的 14 件随连载节奏逐步放开，对应表见 [docs/skill-手册对应表.md](docs/skill-手册对应表.md)。

## 怎么用

每个 skill 是一个独立目录，核心是 `SKILL.md`（字段定义、评分标准、自检清单、prompt 骨架）。支持 skill 机制的 AI Agent 把整个目录放进它的 skills 目录即可被自动唤起；不支持的话，直接把 `SKILL.md` 粘进任何长上下文对话当工作手册用，效果一样。

**安装时去掉目录名的数字前缀**，让目录名与 `SKILL.md` 里的 `name` 一致：

```bash
# 例：安装 05 号 skill（目标路径换成你 Agent 的 skills 目录）
cp -R 05-jtbd-sampling-design /path/to/skills/jtbd-sampling-design
```

目录名带编号是为了跟连载篇目一一对应，方便查找；`name` 保持原名是因为 Agent 按它识别和调用。

随连载放开，部分 skill 还会随包附带 `scripts/`、`references/` 等文件（如格式校验器、字段规范），用法写在各自 `SKILL.md` 里。

## 版本与打磨

每个 skill 头部有版本号，新增放开与修订记在 [CHANGELOG.md](CHANGELOG.md)。

这套 skill 来自真实项目的实战拆解，不是实验室产物。它会在连载反馈里持续打磨：某个评分标准在实践中被证伪、某条自检清单漏了场景，都会修订换版。如果你在使用过程中发现"按它做但结果不对"的地方，欢迎开 issue 说清当时的输入和预期——每一条具体反馈都是下一轮修订的弹药。

## 许可

MIT，见 [LICENSE](LICENSE)。
