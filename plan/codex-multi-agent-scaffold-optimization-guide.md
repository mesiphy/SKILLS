
# Codex Multi-Agent Scaffold Skill 优化行动指南

## 1. 当前结论

当前 `codex-multi-agent-scaffold` Skill 已经从一个简单的 `.ai/` 文件夹模板，进化为一个较完整的“文件驱动多 agent 工作流模板”。

它已经具备以下能力：

- 创建 `.ai/` 工作流目录
- 提供 `active/` 当前工作区
- 提供 `archive/` 历史归档区
- 提供 `handoff/latest-summary.md` 阶段交接摘要
- 提供 planning、development、review、flow-control、fix-planning、explorer、orchestrator 等角色提示词
- 提供 `rules.md` 作为工作流规则文件
- 提供 `status.md`、`action-plan.md`、`current-task/`、`dev-log/`、`review/` 等协作文件

但是，当前 Skill 还没有真正升级为“Codex 原生多 agent 脚手架生成器”。

当前最核心的问题是：

```text
它创建了协作文件，但没有完整创建 Codex 会自动读取和执行的原生项目规则、原生 agent 配置和确定性状态推进脚本。
````

换句话说，当前工作流仍然主要依赖：

```text
用户手动复制 prompt
↓
用户手动指定角色
↓
agent 手动修改 status.md
↓
用户手动推进下一阶段
```

优化后的目标应该是：

```text
安装 AGENTS.md + .codex/agents + .ai + scripts
↓
Codex 自动读取项目规则
↓
用户用一句话触发 orchestrator
↓
orchestrator 根据 status.json/status.md 调用角色 agent
↓
脚本校验和推进状态
```

---

## 2. 当前仓库的主要变化

### 2.1 SKILL.md 已经扩展为工作流管理说明

当前 `SKILL.md` 已经不再只是说明“复制 `.ai/` 模板”，而是开始描述：

* 初始化 file-driven multi-agent Codex development workflow
* 管理 `.ai` scaffolding
* 管理 agent roles
* 管理 task planning
* 管理 dev logs
* 管理 reviews
* 管理 status flow
* 管理 phase archiving
* 管理 handoff summaries

这说明 Skill 的定位已经开始从“模板”转向“工作流”。

但是，`SKILL.md` 目前仍然没有充分要求生成：

* `AGENTS.md`
* `.codex/agents/*.toml`
* `.ai/scripts/*.py`
* `.ai/active/status.json`
* `.ai/workflow-config.yaml`

因此，它还没有真正进入 Codex 原生工作流层面。

---

### 2.2 .ai/rules.md 已经比较成熟

当前 `.ai/rules.md` 已经定义了较完整的工作流规则，包括：

* 文件优先级
* active/archive 边界
* 状态机
* 角色权限
* 任务范围控制
* dev-log 规则
* review 规则
* git 规则
* 阶段归档规则

其中比较重要的一点是，它已经定义了规则优先级：

```text
.ai/rules.md
> .ai/active/status.md
> .ai/active/current-task/*.md
> .ai/active/action-plan.md
> .ai/project-context.md
> .ai/handoff/latest-summary.md
```

这套规则是有价值的。

但是问题在于：

```text
.ai/rules.md 不是 Codex 默认自动读取的入口文件。
```

Codex 默认更应该通过项目根目录的 `AGENTS.md` 获得长期规则。因此，`.ai/rules.md` 应该作为详细规则库，而 `AGENTS.md` 应该作为 Codex 的项目入口。

---

### 2.3 prompts 已经形成角色协议，但还不是 Codex 原生 agent

当前 `.ai/prompts/` 下已经包含多个角色提示词，例如：

```text
00_orchestrator-agent.md
01_planning-agent.md
02_development-agent.md
03_review-agent.md
04_flow-control-agent.md
05_fix-planning-agent.md
06_explorer-agent.md
```

这些 prompt 已经具备比较明确的职责边界。

例如，orchestrator agent 已经能够区分：

* init mode
* plan mode
* run mode
* validate mode

并要求读取：

```text
.ai/rules.md
.ai/project-context.md
.ai/project-specific-rules.md
.ai/handoff/latest-summary.md
.ai/active/status.json
.ai/active/status.md
.ai/active/action-plan.md
```

但是，这些仍然只是 Markdown prompt 文件。

它们的问题是：

```text
需要用户手动复制或手动要求 Codex 读取。
```

更好的方式是将它们升级为 Codex 原生自定义 agent：

```text
.codex/agents/orchestrator.toml
.codex/agents/planner.toml
.codex/agents/explorer.toml
.codex/agents/developer.toml
.codex/agents/reviewer.toml
.codex/agents/flow-controller.toml
.codex/agents/fix-planner.toml
```

这样 Codex 才能在 subagent 工作流中直接调用这些角色。

---

### 2.4 status.json 被引用，但当前模板缺失

当前 prompt 和 `status.md` 中都已经提到：

```text
机器可读状态以 .ai/active/status.json 为准
```

但是当前 `.ai/active/` 下实际只有：

```text
current-task/
dev-log/
review/
action-plan.md
status.md
```

缺少：

```text
.ai/active/status.json
```

这是当前仓库中最明显的不一致之一。

这会导致 orchestrator 进入项目后试图读取一个不存在的关键状态文件，从而影响自动推进能力。

---

## 3. 优化总目标

当前 Skill 应该从：

```text
多 agent 工作流模板
```

升级为：

```text
Codex 原生多 agent 脚手架生成器
```

再进一步升级为：

```text
文件状态机驱动的半自动开发控制器
```

优化后的理想效果是：

```text
一次安装，长期可用
一句目标，生成计划
一句继续，按状态机推进
审查失败，自动生成返工任务
阶段完成，自动归档并生成 handoff
```

---

## 4. 目标文件结构

建议将 Skill 生成的目标项目结构升级为：

```text
项目根目录/
├── AGENTS.md
├── .codex/
│   ├── config.toml
│   └── agents/
│       ├── orchestrator.toml
│       ├── planner.toml
│       ├── explorer.toml
│       ├── developer.toml
│       ├── reviewer.toml
│       ├── flow-controller.toml
│       └── fix-planner.toml
├── .ai/
│   ├── README.md
│   ├── rules.md
│   ├── project-context.md
│   ├── project-specific-rules.md
│   ├── repo-scan-report.md
│   ├── workflow-config.yaml
│   ├── active/
│   │   ├── action-plan.md
│   │   ├── status.json
│   │   ├── status.md
│   │   ├── current-task/
│   │   ├── dev-log/
│   │   └── review/
│   ├── archive/
│   ├── handoff/
│   │   └── latest-summary.md
│   ├── prompts/
│   ├── templates/
│   └── scripts/
│       ├── init_goal.py
│       ├── validate_state.py
│       ├── sync_status_md.py
│       ├── next_task.py
│       ├── create_fix_task.py
│       ├── archive_phase.py
│       └── summarize_handoff.py
```

---

## 5. 优化行动指南

## 5.1 第一阶段：让 Codex 自动感知工作流

### 5.1.1 新增 `assets/scaffold/AGENTS.md`

当前 `.ai/rules.md` 写得比较完整，但 Codex 不会天然把它当作项目入口。

因此，必须新增：

```text
assets/scaffold/AGENTS.md
```

该文件在安装 Skill 时应复制到目标项目根目录：

```text
项目根目录/AGENTS.md
```

建议内容：

```md
# AGENTS.md

This repository uses a file-driven multi-agent Codex workflow.

Before doing any planning, coding, review, testing, or flow-control work, read:

1. `.ai/rules.md`
2. `.ai/project-context.md`
3. `.ai/project-specific-rules.md` if it exists
4. `.ai/handoff/latest-summary.md`
5. `.ai/active/status.json` if it exists
6. `.ai/active/status.md`
7. `.ai/active/action-plan.md`
8. The current task file referenced by status

`.ai/rules.md` is the workflow rule source.
`AGENTS.md` is the Codex entrypoint.

Do not read `.ai/archive/**` unless the user explicitly asks for historical context.

Do not modify business code unless acting as the development agent on the current task.

Do not commit automatically.

After every review, pause unless workflow config explicitly allows auto-advance.
```

---

### 5.1.2 修改 README 的安装方式

当前 README 中如果仍然只写：

```bash
cp -R assets/scaffold/.ai /path/to/your-project/.ai
```

需要改成：

```bash
cp -R assets/scaffold/.ai /path/to/your-project/.ai
cp assets/scaffold/AGENTS.md /path/to/your-project/AGENTS.md
cp -R assets/scaffold/.codex /path/to/your-project/.codex
```

这样 Skill 才不只是复制 `.ai/`，而是安装完整的 Codex 原生工作流。

---

## 5.2 第二阶段：将 prompt 升级为 Codex 原生自定义 agent

### 5.2.1 新增 `.codex/agents/*.toml`

当前 `.ai/prompts/*.md` 是角色提示词，但不是 Codex 原生 subagent。

建议新增：

```text
assets/scaffold/.codex/agents/
├── orchestrator.toml
├── planner.toml
├── explorer.toml
├── developer.toml
├── reviewer.toml
├── flow-controller.toml
└── fix-planner.toml
```

---

### 5.2.2 developer.toml 示例

```toml
name = "developer"
description = "Implement exactly the current task from .ai/active/status.json or status.md, write dev-log, and stop before review."
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"

developer_instructions = """
You are the development agent.

Before editing code, read:
- AGENTS.md
- .ai/rules.md
- .ai/project-context.md
- .ai/active/status.json if present
- .ai/active/status.md
- the current task file

You may:
- change the current task from pending to in-progress
- modify only files allowed by the current task
- write the matching dev-log
- mark development output as done

You must not:
- create review files
- mark review-pass
- select the next task
- read .ai/archive/**
- commit automatically
"""
```

---

### 5.2.3 reviewer.toml 示例

```toml
name = "reviewer"
description = "Review the current dev-done task, diff, logs, and tests. Does not modify product code."
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
You are the review agent.

Read:
- AGENTS.md
- .ai/rules.md
- .ai/project-context.md
- .ai/active/status.json if present
- .ai/active/status.md
- the current task file
- the matching dev-log
- git diff

Review for:
- correctness
- scope compliance
- regressions
- missing tests
- risky assumptions
- documentation mismatch

Write:
- .ai/active/review/<task-id>-review.md

Return one decision:
- review-pass
- review-failed

Do not modify product code.
Do not select the next task.
Do not commit automatically.
"""
```

---

### 5.2.4 orchestrator.toml 示例

```toml
name = "orchestrator"
description = "Coordinate the file-driven multi-agent workflow according to AGENTS.md, .ai/rules.md, and .ai/active/status.json."
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"

developer_instructions = """
You are the workflow orchestrator.

Your job is to decide the next valid workflow action.

Before acting, read:
- AGENTS.md
- .ai/rules.md
- .ai/project-context.md
- .ai/project-specific-rules.md if present
- .ai/workflow-config.yaml if present
- .ai/handoff/latest-summary.md
- .ai/active/status.json if present
- .ai/active/status.md
- .ai/active/action-plan.md

You may:
- invoke planner, explorer, developer, reviewer, tester, flow-controller, or fix-planner agents when appropriate
- run .ai/scripts/validate_state.py
- run .ai/scripts/next_task.py when allowed
- summarize the current workflow state for the user

You must not:
- directly implement product code unless explicitly acting as developer
- skip review
- advance after review-failed
- read .ai/archive/** unless the user asks for historical context
- commit automatically

Stop when:
- review fails
- tests fail
- scope is unclear
- workflow config requires pause
- human confirmation is required
- max_tasks_per_run is reached
"""
```

---

## 5.3 第三阶段：补齐机器可读状态文件

### 5.3.1 新增 `status.json`

当前 prompt 已经引用 `status.json`，但模板中缺少该文件。

必须新增：

```text
assets/scaffold/.ai/active/status.json
```

建议初始内容：

```json
{
  "schema_version": "1.0",
  "goal": {
    "name": "TODO",
    "description": "TODO"
  },
  "phase": "planning",
  "current_task": {
    "id": null,
    "name": null,
    "file": null,
    "status": "pending",
    "dev_log": null,
    "review": null
  },
  "tasks": [],
  "blockers": [],
  "human_confirmations": [],
  "last_updated": null,
  "last_updated_by": "planning-agent"
}
```

---

### 5.3.2 调整 status.md 的定位

`status.md` 不应该再作为唯一状态源。

建议将其定位为：

```text
人类可读状态镜像
```

状态权威来源应改为：

```text
.ai/active/status.json
```

推荐规则：

```text
脚本更新 status.json
↓
sync_status_md.py 根据 status.json 生成 status.md
```

不要让不同 agent 同时手动编辑 `status.json` 和 `status.md`。

---

## 5.4 第四阶段：新增脚本化状态推进能力

### 5.4.1 新增 `.ai/scripts/`

当前工作流推进主要依赖 agent 手动修改 Markdown，这容易产生：

* 状态跳步
* 状态名不一致
* 忘记写 review
* 忘记写 dev-log
* `status.md` 和 `status.json` 不一致
* archive 被误读或误写

因此建议新增：

```text
assets/scaffold/.ai/scripts/
├── init_goal.py
├── validate_state.py
├── sync_status_md.py
├── next_task.py
├── create_fix_task.py
├── archive_phase.py
└── summarize_handoff.py
```

所有脚本尽量只使用 Python 标准库，不引入复杂外部依赖。

---

### 5.4.2 validate_state.py 的职责

`validate_state.py` 应检查：

```text
status.json 是否存在
status.json 是否是合法 JSON
phase 是否在允许枚举内
current_task.file 是否存在
当前任务状态和 phase 是否匹配
review-pass 是否有 review 文件
dev-done 是否有 dev-log 文件
done 是否有完整 review-pass 记录
status.md 是否和 status.json 一致
prompts 中引用的文件是否存在
AGENTS.md 是否存在
.codex/agents/*.toml 是否存在
```

---

### 5.4.3 next_task.py 的职责

`next_task.py` 应只允许在满足条件时推进：

```text
当前任务 review-pass
用户确认通过，或者 workflow-config 允许自动推进
存在下一个 pending task
```

执行流程：

```text
当前任务标记完成
↓
选择下一个 pending task
↓
更新 current_task
↓
phase = ready
↓
同步 status.md
```

禁止行为：

```text
review-failed 时推进
测试失败时推进
无 review 文件时推进
无 dev-log 文件时推进
超出 max_tasks_per_run 时推进
```

---

### 5.4.4 sync_status_md.py 的职责

`sync_status_md.py` 根据 `status.json` 自动生成或更新 `status.md`。

建议生成内容包括：

```text
当前目标
当前阶段
当前任务
任务列表
阻塞项
最近更新时间
下一步建议
```

---

### 5.4.5 archive_phase.py 的职责

`archive_phase.py` 用于阶段结束后归档当前工作区。

执行流程：

```text
检查当前 phase 是否 completed
↓
检查所有任务是否 review-pass 或明确跳过
↓
生成 handoff/latest-summary.md
↓
复制 active/ 到 archive/YYYY-MM-DD-goal-name/
↓
重置 active/ 为下一阶段准备状态
```

禁止行为：

```text
任务未完成时归档
review-failed 时归档
没有 handoff summary 时归档
覆盖已有 archive
```

---

## 5.5 第五阶段：修正状态机语义

### 5.5.1 当前问题

当前状态中包含：

```text
pending
in-progress
done
review-pass
review-failed
need-human-review
blocked
```

问题是：

```text
done 容易被误解为整个任务已经完成。
```

但在当前流程中，`done` 更像是“开发完成，等待审查”。

---

### 5.5.2 建议改为 dev-done

建议状态改为：

```text
pending
in-progress
dev-done
review-pass
review-failed
need-human-review
blocked
```

推荐状态流转：

```text
planning/pending
-> ready/pending
-> developing/in-progress
-> reviewing/dev-done
-> paused/review-pass
-> ready/pending
-> completed/review-pass
```

这样可以避免 developer agent 把 `done` 误认为任务最终完成。

---

## 5.6 第六阶段：新增 workflow-config.yaml

当前规则中“review 后必须暂停”是写死的。

这很安全，但会导致流程永远偏手动。

建议新增：

```text
assets/scaffold/.ai/workflow-config.yaml
```

初始内容：

```yaml
review:
  pause_after_each_review: true
  auto_advance_on_review_pass: false

execution:
  max_tasks_per_run: 1
  stop_on_test_failure: true
  stop_on_scope_exception: true

git:
  auto_commit: false

archive:
  auto_archive_when_completed: false
```

这样用户可以根据需要切换为更自动化的模式：

```yaml
review:
  pause_after_each_review: false
  auto_advance_on_review_pass: true

execution:
  max_tasks_per_run: 3
```

---

## 5.7 第七阶段：补齐被 prompt 引用但模板缺失的文件

当前 prompts 中引用了一些文件，但模板中可能不存在。

建议补齐：

```text
assets/scaffold/.ai/project-specific-rules.md
assets/scaffold/.ai/repo-scan-report.md
```

---

### 5.7.1 project-specific-rules.md

用途：

```text
记录当前项目特有规则。
```

内容可以包括：

```text
项目技术栈
禁止修改的目录
数据库规则
测试规则
代码风格
模块边界
性能要求
安全要求
```

---

### 5.7.2 repo-scan-report.md

用途：

```text
记录 explorer/init agent 对项目结构的扫描结果。
```

内容可以包括：

```text
项目语言
包管理器
入口文件
测试命令
lint 命令
核心模块
关键配置文件
数据库结构
潜在风险区
```

---

## 5.8 第八阶段：新增升级旧脚手架能力

当前 Skill 应该同时支持：

```text
初始化新项目
升级旧脚手架
```

建议新增：

```text
assets/scaffold/.ai/scripts/upgrade_scaffold.py
```

该脚本职责：

```text
检测是否存在 .ai/
检测是否存在 AGENTS.md
检测是否存在 .codex/agents/
检测是否存在 status.json
检测是否存在 workflow-config.yaml
检测是否存在 .ai/scripts/
检测 prompts 中引用但不存在的文件
```

升级原则：

```text
只补缺失文件
不覆盖 active/dev-log/review/archive
不覆盖用户已有 project-context.md
不覆盖用户已有 action-plan.md
不覆盖用户已有 status.md
生成 upgrade-report.md
```

建议输出：

```text
.ai/upgrade-report.md
```

内容包括：

```text
本次新增了哪些文件
本次跳过了哪些已有文件
发现了哪些不一致
需要用户手动确认哪些内容
```

---

## 5.9 第九阶段：更新 SKILL.md

当前 `SKILL.md` 应明确：

```text
这个 Skill 不只是复制 .ai，而是安装或升级 Codex 原生多 agent 工作流。
```

建议新增或修改为：

```md
## Mandatory outputs

When initializing or upgrading a repository, this skill must create or update:

1. `AGENTS.md`
2. `.codex/agents/*.toml`
3. `.ai/rules.md`
4. `.ai/project-context.md`
5. `.ai/project-specific-rules.md`
6. `.ai/repo-scan-report.md`
7. `.ai/workflow-config.yaml`
8. `.ai/active/status.json`
9. `.ai/active/status.md`
10. `.ai/active/action-plan.md`
11. `.ai/templates/*`
12. `.ai/scripts/*`

Do not overwrite existing active logs, reviews, archive records, or user project files.
```

还应加入：

```md
## Initialization behavior

The skill must inspect the repository structure before generating project-context.md and repo-scan-report.md.

The skill must detect:

- language
- package manager
- test commands
- lint commands
- main source directories
- configuration files
- database or migration directories
- existing AGENTS.md or .codex configuration
```

以及：

```md
## Upgrade behavior

If the target repository already contains a .ai directory, do not overwrite existing workflow history.

Instead:

1. Detect missing scaffold files.
2. Add missing files.
3. Preserve active logs, reviews, archive records, and project-specific context.
4. Generate `.ai/upgrade-report.md`.
```

---

## 5.10 第十阶段：更新 README.md

README 应从“如何复制模板”升级为“如何安装、规划、推进、归档”。

建议 README 至少包含四种使用场景。

---

### 场景一：初始化项目

```text
使用 codex-multi-agent-scaffold 初始化当前项目。
请创建 AGENTS.md、.codex/agents、.ai 文件体系，并根据仓库结构生成 project-context、repo-scan-report 和初始 status.json。
```

---

### 场景二：基于目标生成计划

```text
请调用 planner，根据目标“XXX”生成 .ai/active/action-plan.md、status.json、status.md 和 current-task/*.md。
规划完成后停止，不要进入开发。
```

---

### 场景三：继续当前任务

```text
请调用 orchestrator，根据 .ai/active/status.json 推进当前任务。
最多推进 1 个任务；review 后暂停；不得自动 commit。
```

---

### 场景四：阶段完成后归档

```text
请调用 flow-controller 检查当前阶段是否完成。
如果所有任务都已 review-pass，请生成 handoff/latest-summary.md，并运行 archive_phase.py 归档当前 active 工作区。
```

---

## 6. 优先级排序

## 6.1 第一批：最高优先级

优先完成下面 5 个文件：

```text
assets/scaffold/AGENTS.md
assets/scaffold/.codex/agents/orchestrator.toml
assets/scaffold/.codex/agents/developer.toml
assets/scaffold/.ai/active/status.json
assets/scaffold/.ai/scripts/validate_state.py
```

原因：

```text
AGENTS.md 让 Codex 自动知道工作流
orchestrator.toml 让流程有统一调度入口
developer.toml 让开发角色有明确边界
status.json 让状态机器可读
validate_state.py 让状态可以被校验
```

---

## 6.2 第二批：中高优先级

然后完成：

```text
assets/scaffold/.ai/scripts/next_task.py
assets/scaffold/.ai/scripts/sync_status_md.py
assets/scaffold/.ai/workflow-config.yaml
assets/scaffold/.ai/repo-scan-report.md
assets/scaffold/.ai/project-specific-rules.md
```

原因：

```text
next_task.py 解决手动推进问题
sync_status_md.py 解决状态文件不一致问题
workflow-config.yaml 解决自动化程度不可配置问题
repo-scan-report.md 解决项目结构扫描记录问题
project-specific-rules.md 解决项目差异化规则问题
```

---

## 6.3 第三批：完善体验

最后完成：

```text
assets/scaffold/.codex/agents/planner.toml
assets/scaffold/.codex/agents/explorer.toml
assets/scaffold/.codex/agents/reviewer.toml
assets/scaffold/.codex/agents/flow-controller.toml
assets/scaffold/.codex/agents/fix-planner.toml
assets/scaffold/.ai/scripts/archive_phase.py
assets/scaffold/.ai/scripts/create_fix_task.py
assets/scaffold/.ai/scripts/summarize_handoff.py
assets/scaffold/.ai/scripts/upgrade_scaffold.py
README.md
SKILL.md
```

---

## 7. 给 Codex 执行的完整行动指令

可以直接把下面这段交给 Codex 执行。

```text
请优化当前 codex-multi-agent-scaffold Skill。

目标：把它从“只复制 .ai 文件夹的多 agent 工作流模板”升级为“Codex 原生多 agent 脚手架生成器”。

必须完成：

1. 在 assets/scaffold/ 下新增 AGENTS.md，作为目标项目的 Codex 自动读取入口。
2. 在 assets/scaffold/.codex/agents/ 下新增 orchestrator、planner、explorer、developer、reviewer、flow-controller、fix-planner 的 TOML 自定义 agent 配置。
3. 在 assets/scaffold/.ai/active/ 下新增 status.json，并使 status.md 明确作为人类可读镜像。
4. 在 assets/scaffold/.ai/scripts/ 下新增 validate_state.py、sync_status_md.py、next_task.py、archive_phase.py。
5. 新增 .ai/workflow-config.yaml，让 review 后是否暂停、是否自动进入下一任务、每次最多推进几个任务可配置。
6. 补齐 prompts 中引用但模板中缺失的 .ai/project-specific-rules.md 和 .ai/repo-scan-report.md。
7. 修改 SKILL.md，把 Mandatory outputs 从只复制 .ai 改成必须创建/升级 AGENTS.md、.codex/agents、.ai、scripts。
8. 修改 README.md，更新快速使用方式，说明初始化、规划、继续当前任务、归档四种用法。
9. 保持向后兼容：不得覆盖已有 active/dev-log/review/archive 内容；如需升级旧结构，生成 upgrade-report.md。
10. 完成后运行一次自检：确认所有被 prompts 引用的文件都存在，status.json 和 status.md 的初始状态一致，README/SKILL.md 与实际目录一致。

注意：
- 不要修改仓库中与 codex-multi-agent-scaffold 无关的 Skill。
- 不要引入复杂外部依赖，脚本只用 Python 标准库。
- 默认不自动 commit。
```

---

## 8. 验收标准

优化完成后，应满足以下标准。

### 8.1 文件完整性

目标项目中应存在：

```text
AGENTS.md
.codex/agents/orchestrator.toml
.codex/agents/planner.toml
.codex/agents/explorer.toml
.codex/agents/developer.toml
.codex/agents/reviewer.toml
.codex/agents/flow-controller.toml
.codex/agents/fix-planner.toml
.ai/active/status.json
.ai/active/status.md
.ai/workflow-config.yaml
.ai/project-specific-rules.md
.ai/repo-scan-report.md
.ai/scripts/validate_state.py
.ai/scripts/sync_status_md.py
.ai/scripts/next_task.py
.ai/scripts/archive_phase.py
```

---

### 8.2 规则一致性

应满足：

```text
AGENTS.md 指向 .ai/rules.md
prompts 中引用的文件都实际存在
status.md 不再是唯一状态源
status.json 是机器可读状态源
status.md 是人类可读镜像
```

---

### 8.3 状态机一致性

应使用：

```text
pending
in-progress
dev-done
review-pass
review-failed
need-human-review
blocked
```

避免继续使用容易混淆的：

```text
done
```

作为“开发完成”的状态。

---

### 8.4 自动推进能力

至少应支持：

```text
validate_state.py 校验当前状态
sync_status_md.py 同步 status.md
next_task.py 推进到下一个任务
archive_phase.py 归档已完成阶段
```

---

### 8.5 向后兼容

如果目标项目已经存在旧版 `.ai/`，不得覆盖：

```text
.ai/active/dev-log/
.ai/active/review/
.ai/archive/
.ai/project-context.md
.ai/active/action-plan.md
.ai/active/status.md
```

应优先补齐缺失文件，并生成：

```text
.ai/upgrade-report.md
```

---

## 9. 最终使用方式示例

### 9.1 初始化

```text
使用 codex-multi-agent-scaffold 初始化当前项目。
创建 AGENTS.md、.codex/agents 和 .ai 工作流文件。
扫描当前仓库结构，生成 project-context.md、repo-scan-report.md 和初始 status.json。
```

---

### 9.2 生成计划

```text
请调用 planner agent，为目标“完成量化项目因子计算模块重构”生成 action-plan、status.json、status.md 和 current-task/*.md。
规划完成后停止，不要进入开发。
```

---

### 9.3 继续当前任务

```text
请调用 orchestrator，根据 .ai/active/status.json 继续当前任务。
最多推进 1 个任务，review 后暂停，不要自动 commit。
```

---

### 9.4 半自动推进多个任务

```text
请调用 orchestrator，根据 .ai/active/status.json 推进当前阶段。
review-pass 后可以自动进入下一个任务，最多推进 3 个任务。
如果 review-failed、测试失败、范围不清楚或需要人工确认，立即停止。
不要自动 commit。
```

---

### 9.5 阶段归档

```text
请调用 flow-controller 检查当前阶段是否已经完成。
如果所有任务都已 review-pass，请生成 handoff/latest-summary.md，并运行 archive_phase.py 归档当前 active 工作区。
```

---

## 10. 总结

当前 Skill 的核心价值已经具备：

```text
多 agent 角色意识
文件驱动协作
active/archive 分层
dev-log/review 留痕
handoff 阶段交接
```

但它还缺少真正自动化所需的关键部件：

```text
AGENTS.md
.codex/agents/*.toml
status.json
workflow-config.yaml
.ai/scripts/*.py
upgrade_scaffold.py
```

因此，下一步优化的核心不是继续增加更多 Markdown 文档，而是把已有的 Markdown 工作流升级为：

```text
Codex 可感知
状态可验证
流程可推进
历史可归档
旧版可升级
```

最终目标是让用户从：

```text
手动管理 agent 工作流
```

变成：

```text
用 orchestrator 管理 agent 工作流
```

```
```
