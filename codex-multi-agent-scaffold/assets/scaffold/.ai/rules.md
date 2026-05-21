# AI Development Rules / AI 开发规则

本文档是所有 agent 的最高优先级规则。除非用户明确修改本文件，否则规划、开发、审查、流程控制、返工和归档都必须遵守。

## 1. File Priority / 文件优先级

开发与审查时按以下优先级解释冲突：

```text
rules.md > active/status.json > active/status.md > active/current-task/*.md > active/action-plan.md > project-specific-rules.md > project-context.md > handoff/latest-summary.md
```

如果冲突无法判断，必须暂停并记录阻塞原因。

## 2. Active vs Archive / 当前区与归档区

- `active/` 只保存当前阶段的运行状态、任务、dev-log、review。
- `archive/` 保存历史阶段完整记录。
- `handoff/latest-summary.md` 是下一阶段默认读取的历史压缩摘要。
- 除非用户明确要求追溯历史，否则任何 agent 不得读取 `.ai/archive/**`。
- 新阶段规划只能基于 `project-context.md`、`handoff/latest-summary.md` 和用户目标。

## 3. State Machine / 状态机

`.ai/active/status.json` 是机器可读状态源，`.ai/active/status.md` 是人类可读状态镜像。任何 agent 修改状态时必须同步更新两个文件。

如果 `status.md` 与 `status.json` 冲突，必须暂停并输出 `FAIL`，不得继续推进任务。

`status.json` 必须使用以下字段：

```json
{
  "phase": "planning",
  "current_task_id": null,
  "current_task_file": null,
  "task_status": "pending",
  "dev_log_file": null,
  "review_file": null,
  "last_human_confirmation": null,
  "tasks": [],
  "blocked_reason": null,
  "updated_at": null
}
```

允许的流程阶段：

- `planning`：正在规划目标、任务和状态文件
- `ready`：任务已拆分，等待开发
- `developing`：正在开发当前任务
- `reviewing`：当前任务开发完成，等待或正在审查
- `fixing`：审查失败后，正在创建或执行返工任务
- `paused`：等待用户确认
- `blocked`：流程阻塞
- `completed`：全部任务完成

允许的任务状态：

- `pending`
- `in-progress`
- `done`
- `review-pass`
- `review-failed`
- `need-human-review`
- `blocked`

正常流转：

```text
planning/pending -> ready/pending -> developing/in-progress -> reviewing/done -> paused/review-pass -> ready/pending -> completed/review-pass
```

失败流转：

```text
reviewing/done -> fixing/review-failed -> fixing/pending -> developing/in-progress -> reviewing/done
```

人工确认规则：

- `last_human_confirmation` 只能在用户明确确认后写入。
- 模糊回复、沉默、自动推断都不能作为确认。
- flow-control agent 只有在 `task_status = review-pass` 且存在明确人工确认时才能推进下一任务。

状态文件引用规则：

- `current_task_file` 非空时必须指向 `.ai/active/current-task/` 下存在的任务文件。
- `dev_log_file` 非空时必须指向 `.ai/active/dev-log/` 下存在的 dev-log 文件。
- `review_file` 非空时必须指向 `.ai/active/review/` 下存在的 review 文件。
- `review-pass` 状态必须有 review 文件。
- `review-failed` 状态必须创建或等待创建 fix task。
- `completed` 状态必须有 `.ai/active/final-report.md`。

## 4. Role Permissions / 角色权限

### Orchestrator agent / 主控 agent

- 可以读取 status 并决定调用哪个角色。
- 不直接修改业务代码。
- 每次 review 后必须暂停，等待用户确认是否推进。

### Planning agent / 规划 agent

可以：

- 创建或更新 `active/action-plan.md`
- 创建 `active/current-task/*.md`
- 初始化 `active/status.md`

不得：

- 修改业务代码
- 创建 dev-log 或 review
- 将任务标记为 done 或 review-pass

### Development agent / 开发 agent

可以：

- 将当前任务从 `pending` 改为 `in-progress`
- 修改当前 task 允许范围内的文件
- 创建对应 dev-log
- 将当前任务改为 `done`

不得：

- 创建 review
- 标记 review-pass
- 进入下一任务
- 重置、覆盖或整理与当前任务无关的 git 改动

### Review agent / 审查 agent

可以：

- 创建当前任务 review
- 将任务状态改为 `review-pass`、`review-failed` 或 `need-human-review`

不得：

- 修改业务代码
- 执行返工
- 推进下一任务

### Flow-control agent / 流程控制 agent

可以：

- 在用户确认且当前任务为 `review-pass` 时切换到下一个 pending 任务
- 无下一个任务时标记 completed

不得：

- 修改业务代码
- 跳过未审查任务

### Fix-planning agent / 返工规划 agent

可以：

- 根据 failed review 创建新的 fix task

不得：

- 覆盖原 task、dev-log、review
- 直接修改业务代码

### Explorer agent / 探索 agent

- 只读分析代码、测试、架构和风险。
- 可并行执行。
- 不得修改文件，不得更新 status。

## 5. File Naming Rules / 文件命名规则

### Normal Task / 普通任务

- Task: `.ai/active/current-task/{task_id}-task.md`
- Dev log: `.ai/active/dev-log/{task_id}-dev-log.md`
- Review: `.ai/active/review/{task_id}-review.md`

Examples:

- `.ai/active/current-task/001-task.md`
- `.ai/active/dev-log/001-dev-log.md`
- `.ai/active/review/001-review.md`

### Fix Task / 返工任务

- Fix task: `.ai/active/current-task/{task_id}-fix-{fix_index}-task.md`
- Fix dev log: `.ai/active/dev-log/{task_id}-fix-{fix_index}-dev-log.md`
- Fix review: `.ai/active/review/{task_id}-fix-{fix_index}-review.md`

Examples:

- `.ai/active/current-task/001-fix-01-task.md`
- `.ai/active/dev-log/001-fix-01-dev-log.md`
- `.ai/active/review/001-fix-01-review.md`

## 6. Task Scope / 任务范围

每个 task 必须声明：

- 允许修改范围
- 禁止修改范围
- 验收标准
- 输出要求

开发 agent 只能修改允许范围内的文件。若必须越界，必须在 dev-log 中标记 `scope-exception`，说明原因和不修改的后果。

## 7. Dev Log Rules / 开发记录规则

每个任务必须有对应 dev-log。dev-log 只能记录事实，必须包含：

- 对应任务
- 实际执行内容
- 查看或修改的文件
- 修改原因
- 验收标准逐条对应关系
- 测试、lint、build 结果
- 未完成事项
- 未验证事项
- 风险与疑问

禁止把未验证事项标记为 passed。

## 8. Review Rules / 审查规则

review 结论只能是：

- `pass`
- `failed`
- `need-human-review`

审查必须检查：

- 是否只执行当前任务
- 是否提前做了后续任务
- 是否修改禁止范围
- dev-log 是否真实
- 验收项是否有证据
- 测试失败或未运行是否说明原因

## 9. Git Rules / Git 规则

- 默认不自动 commit。
- 每个开发和审查记录应包含相关 `git status` 或 diff 摘要。
- 不得执行 destructive git 操作，除非用户明确要求。
- 不得重置用户已有改动。

## 10. Phase Archive / 阶段归档

阶段完成后：

1. 生成 `active/final-report.md`。
2. 将 `active/status.md` 标记为 completed。
3. 将本轮 `active/` 产物复制或移动到 `archive/<date-phase-name>/`。
4. 将最终状态保存为 `status.final.md`。
5. 更新 `handoff/latest-summary.md`。
6. 清空 active 下的任务、dev-log、review，为下一阶段准备。
