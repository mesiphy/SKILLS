# .ai Multi-Agent Scaffold

本目录是项目内的多 agent 工作流控制台。

## 使用顺序

1. 填写 `project-context.md`。
2. 用 planning agent 生成 `active/action-plan.md`、`active/status.md` 和当前任务文件。
3. 用 development agent 执行当前任务。
4. 用 review agent 审查当前任务。
5. 审查后暂停，用户确认后由 flow-control agent 推进。
6. 阶段完成后归档 `active/`，更新 `handoff/latest-summary.md`。

## 默认读取边界

新阶段默认读取：

- `rules.md`
- `project-context.md`
- `handoff/latest-summary.md`
- `active/action-plan.md`
- `active/status.md`
- `active/current-task/<当前任务>.md`

不要默认读取 `archive/**`。
