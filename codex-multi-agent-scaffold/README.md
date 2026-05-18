# Codex Multi-Agent Scaffold

这是一个可复制到任意软件项目的多 agent 开发脚手架。它把需求规划、开发、审查、流程推进、返工、归档和阶段交接都放进 `.ai/` 文件体系里，让 Codex 子 agent 可以围绕同一套状态文件协作。

## 快速使用

```bash
cp -R assets/scaffold/.ai /path/to/your-project/.ai
```

然后在项目根目录开启 Codex，并输入：

```text
请作为规划 agent，读取 .ai/rules.md 和 .ai/project-context.md，基于我的目标初始化 .ai/active/action-plan.md、.ai/active/status.md 和 .ai/active/current-task/*.md。
```

## 推荐节奏

1. 规划 agent 生成当前阶段任务。
2. 开发 agent 执行 `active/status.md` 指定的当前任务。
3. 审查 agent 审查当前任务、dev-log、diff、测试结果。
4. 每轮审查后暂停，等待用户确认。
5. 流程控制 agent 推进到下一个任务。
6. 完成阶段后归档 active，并更新 handoff。

## 目录核心

- `assets/scaffold/.ai/rules.md`：最高优先级规则。
- `assets/scaffold/.ai/project-context.md`：项目事实源模板。
- `assets/scaffold/.ai/active/`：当前阶段运行区。
- `assets/scaffold/.ai/archive/`：历史阶段归档区。
- `assets/scaffold/.ai/handoff/latest-summary.md`：下一阶段默认读取的历史压缩摘要。
- `assets/scaffold/.ai/templates/`：可复制模板。
- `assets/scaffold/.ai/prompts/`：各 agent 提示词。
