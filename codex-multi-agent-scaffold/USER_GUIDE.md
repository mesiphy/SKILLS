# Codex Multi-Agent Scaffold 使用流程与功能介绍

## 总览：这个 skill 如何工作

`codex-multi-agent-scaffold` 是一个用于把普通软件项目升级为“多 agent 可协作开发环境”的 Codex skill。

它的核心不是简单复制一组模板，而是帮助 agent 在目标项目中完成一套可追踪、可校验、可交接的工作流：

1. 初始化目标项目的 `.ai/` 工作区。
2. 扫描真实项目结构，生成 repo scan 报告。
3. 基于扫描证据生成项目上下文和项目专属规则。
4. 根据用户目标生成 action plan 和 current task。
5. 由 development agent 只执行当前任务。
6. 由 review agent 独立审查任务结果。
7. 由 flow-control agent 在用户确认后推进下一任务。
8. 如审查失败，由 fix-planning agent 创建返工任务。
9. 阶段完成后，由 phase-close agent 归档 active 工作区并生成 handoff。
10. 任意阶段都可以运行 validate mode 检查 `.ai/` 状态是否合法。

整体流程可以理解为：

```text
初始化项目
  -> 扫描项目
  -> 生成项目上下文与规则
  -> 制定计划
  -> 用户确认计划
  -> 执行当前任务
  -> 审查当前任务
  -> 用户确认审查结果
  -> 推进下一任务 / 创建返工任务
  -> 阶段完成后归档
```

这个 skill 的重点是“让 agent 有边界地协作”。所有角色都围绕 `.ai/` 文件系统工作，避免一个 agent 同时承担规划、开发、审查、推进和归档职责。

## 一、初始化：让项目具备多 agent 工作区

初始化阶段的目标是在目标项目根目录创建或补齐 `.ai/` 文件夹。

典型用户指令：

```text
Use the codex-multi-agent-scaffold skill to initialize this project.
Scan the repository, create the .ai scaffold, generate project-context.md,
project-specific-rules.md, status.md, status.json, and validate the result.
Do not modify business code.
```

初始化会创建或补齐：

- `.ai/rules.md`
- `.ai/project-context.md`
- `.ai/project-specific-rules.md`
- `.ai/active/action-plan.md`
- `.ai/active/status.md`
- `.ai/active/status.json`
- `.ai/active/current-task/`
- `.ai/active/dev-log/`
- `.ai/active/review/`
- `.ai/archive/`
- `.ai/handoff/latest-summary.md`
- `.ai/templates/`
- `.ai/prompts/`

初始化默认不覆盖已有 `.ai/` 文件。只有用户明确要求 force 时，才允许覆盖已有 scaffold 文件。

可直接运行的脚本：

```bash
python scripts/init_scaffold.py --target /path/to/project
python scripts/init_scaffold.py --target /path/to/project --dry-run
python scripts/init_scaffold.py --target /path/to/project --force
```

## 二、项目扫描：把真实项目结构转成证据报告

项目扫描阶段会读取目标项目中的真实文件，生成：

```text
.ai/repo-scan-report.md
```

扫描内容包括：

- 项目根目录证据
- 顶层目录结构
- 主要语言
- 包管理器
- 框架识别
- 前端入口
- 后端入口
- 测试设置
- 配置文件
- 数据库相关文件
- API 路由相关文件
- build / lint / typecheck / test 命令候选
- 高风险目录
- Unknowns

扫描原则是保守的：不能确定的信息不会被写成事实，而是进入 Unknowns。

可直接运行：

```bash
python scripts/scan_project.py --target /path/to/project
```

## 三、项目上下文：只记录已验证事实

`.ai/project-context.md` 是项目长期事实源。

它记录：

- 项目摘要
- 已验证技术栈
- 已验证目录结构
- 已验证入口文件
- 已验证命令
- 已验证数据库 / 存储结构
- 已验证 API 结构
- 已验证测试设置
- 已验证编码约定
- 高风险区域
- Unknowns
- Evidence Index

它不记录：

- 当前开发目标
- 临时任务状态
- 没有证据的猜测

开发目标属于：

```text
.ai/active/action-plan.md
```

任务状态属于：

```text
.ai/active/status.json
.ai/active/status.md
```

## 四、项目专属规则：补充通用 rules

`.ai/project-specific-rules.md` 用来记录当前项目特有的约束。

它补充 `.ai/rules.md`，但不替代 `.ai/rules.md`。

它可以包含：

- 项目类型
- 主要语言
- 框架
- runtime
- package manager
- database
- frontend / backend 边界
- 必须运行的命令
- 文件所有权规则
- 高风险区域
- 不同变更类型必须同步更新的文件
- Unknowns

development agent 和 review agent 都必须读取它。

## 五、规划：把用户目标拆成可执行任务

当用户给出开发目标时，进入 plan mode。

典型用户指令：

```text
My development goal is:
...

Use planning mode to generate action-plan.md and current-task files.
Stop after the plan and wait for my confirmation.
```

planning agent 会生成：

- `.ai/active/action-plan.md`
- `.ai/active/current-task/001-task.md`
- 可能的后续任务文件
- 更新后的 `.ai/active/status.json`
- 更新后的 `.ai/active/status.md`

每个 task 必须包含：

- 目标
- 输入上下文
- allowed scope
- forbidden scope
- 执行步骤
- 验收标准
- 测试要求
- 输出要求

规划完成后必须停止，等待用户确认，不能自动进入开发。

## 六、执行：development agent 只做当前任务

用户确认计划后，可以要求执行当前任务。

典型用户指令：

```text
Use development mode to execute the current task.
Follow .ai/active/status.json and the current-task file.
Only modify files allowed by the task.
Create the dev-log and run task scope validation.
Do not create review and do not commit.
```

development agent 必须：

- 读取 `status.json.current_task_file`
- 只执行当前任务
- 只修改 allowed scope 内的文件
- 创建 dev-log
- 更新 status
- 运行 scope 校验

开发完成后生成：

```text
.ai/active/dev-log/001-dev-log.md
```

## 七、审查：review agent 只审查不开发

开发完成后，进入 review mode。

典型用户指令：

```text
Use review mode to review the current task.
Read the task, dev-log, project-specific-rules.md, and git diff.
Check allowed scope, acceptance criteria, and test evidence.
Write the review file only. Do not modify business code.
```

review agent 检查：

- 是否只完成当前任务
- 是否提前做了后续任务
- 是否越过 allowed scope
- 是否修改 forbidden scope
- dev-log 是否真实
- 验收标准是否满足
- 测试是否运行
- 未运行测试是否有说明

审查结果只能是：

- `pass`
- `failed`
- `need-human-review`

生成文件：

```text
.ai/active/review/001-review.md
```

## 八、推进：用户确认后才能进入下一任务

如果 review pass，flow-control agent 不能自动推进，必须等待用户确认。

典型用户指令：

```text
I confirm the review-pass result.
Use flow-control mode to advance to the next pending task.
```

flow-control agent 只有在以下条件都满足时才能推进：

- 当前任务是 `review-pass`
- review 文件存在
- dev-log 文件存在
- 用户明确确认
- `status.json.last_human_confirmation` 已记录

如果还有下一个 pending task，则切换到下一个任务。

如果没有下一个任务，则进入 completed 候选状态，等待 phase-close。

## 九、返工：审查失败后创建 fix task

如果 review failed，不能让 development agent 直接乱改，必须先创建 fix task。

典型用户指令：

```text
Use fix-planning mode to create a fix task from the failed review.
Do not modify business code.
Do not expand allowed scope unless I explicitly approve it.
```

fix task 命名示例：

```text
.ai/active/current-task/001-fix-01-task.md
.ai/active/dev-log/001-fix-01-dev-log.md
.ai/active/review/001-fix-01-review.md
```

fix task 必须引用：

- 原 task
- 原 dev-log
- 原 review

默认 allowed scope 不得超过原 task。

## 十、校验：随时检查 `.ai` 状态是否合法

validate mode 用于检查当前 `.ai/` 是否能继续推进。

典型用户指令：

```text
Use validate mode to check the .ai scaffold and status.
Report PASS, WARN, FAIL, and suggested fixes.
```

可直接运行：

```bash
python scripts/validate_ai_state.py --target /path/to/project
python scripts/validate_ai_state.py --target /path/to/project --strict
```

校验内容包括：

- `.ai/` 目录结构
- 必备文件是否存在
- `status.json` 是否可解析
- phase 是否合法
- task_status 是否合法
- current task 是否存在
- dev-log / review 引用是否存在
- `status.md` 和 `status.json` 是否冲突
- completed 状态是否有 final report

## 十一、范围校验：防止 development agent 越权

`validate_task_scope.py` 会检查 git diff 中的文件是否都在当前 task 的 allowed scope 内。

可直接运行：

```bash
python scripts/validate_task_scope.py --target /path/to/project --task .ai/active/current-task/001-task.md
```

如果项目不是 git 仓库，它会输出 WARN，而不是崩溃。

它不会自动 revert。

## 十二、归档：阶段完成后生成 final report 和 handoff

当所有任务都完成并审查通过后，可以进入 phase-close mode。

典型用户指令：

```text
Use phase-close mode to generate final-report.md,
archive the active phase, update handoff/latest-summary.md,
and mark the phase completed.
Do not modify business code.
```

phase-close agent 会生成或更新：

```text
.ai/active/final-report.md
.ai/archive/YYYY-MM-DD-{phase-name}/
.ai/archive/YYYY-MM-DD-{phase-name}/status.final.md
.ai/handoff/latest-summary.md
```

它不得在任务未完成且无用户豁免时强行归档。

## 角色分工总结

| 角色 | 职责 | 是否能改业务代码 |
|---|---|---|
| init scaffold agent | 初始化 `.ai`、扫描项目、生成上下文和规则 | 否 |
| orchestrator agent | 判断模式和下一角色 | 否 |
| planning agent | 生成 action-plan 和 current-task | 否 |
| development agent | 执行当前任务 | 只能改 allowed scope |
| review agent | 审查 task/dev-log/diff | 否 |
| flow-control agent | 用户确认后推进下一任务 | 否 |
| fix-planning agent | 创建返工任务 | 否 |
| explorer agent | 只读探索和补充证据 | 否 |
| phase-close agent | 总结、归档、更新 handoff | 否 |

## 最小推荐使用节奏

```text
1. Initialize this project with codex-multi-agent-scaffold.
2. Scan the repository and validate .ai state.
3. Use planning mode for my goal.
4. I confirm the action plan.
5. Use development mode for the current task.
6. Use review mode for the current task.
7. I confirm review-pass.
8. Use flow-control mode to advance.
9. Repeat until all tasks are done.
10. Use phase-close mode to archive this phase.
```

## 当前边界

这个 skill 已经具备初始化、扫描、校验和角色协议能力，但还不是完整的自动 runner。

目前仍需要 agent 根据扫描报告生成高质量的 `project-context.md` 和 `project-specific-rules.md`，也需要用户显式确认计划、审查结果和越权范围变更。
