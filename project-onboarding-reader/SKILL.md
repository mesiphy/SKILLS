---
name: project-onboarding-reader
description: Use when the user wants to understand, learn, or onboard into an unfamiliar codebase, especially an open-source GitHub project. This skill performs read-only repository analysis for programming beginners or new project members, explaining project purpose, tech stack, directory structure, entry points, runtime flow, core modules, key algorithms or business logic, and a practical reading path. Do not use for code review, refactoring, security audit, or implementation unless the user explicitly asks for those after the onboarding analysis.
metadata:
  short-description: Read unfamiliar codebases for newcomers
---

# Project Onboarding Reader

## Mission

Help a programming beginner or new project member build a useful mental model of an unfamiliar repository.

Default to read-only analysis. Explain the project in plain language, grounded in real files and commands from the repository. The goal is orientation, not review or modification.

## Use When

Use this skill when the user asks to:

- understand a downloaded GitHub or open-source project
- explain a repository's architecture, startup flow, request flow, CLI flow, data flow, or algorithm flow
- identify which files a newcomer should read first
- create a beginner-friendly project guide or onboarding note
- explain core modules, key abstractions, or important algorithms in an unfamiliar codebase

Do not use this skill for ordinary code review, bug fixing, refactoring, security audits, or feature implementation unless the user first asks for onboarding and then explicitly extends the task.

## Inputs To Infer

Infer these from the user request and repository context:

- Target repository: default to the current working directory.
- Audience level: default to `beginner`.
- Focus: default to the whole project; honor narrower focuses such as backend API, frontend, data pipeline, core algorithm, CLI, tests, or deployment.
- Output mode: default to chat response only. Create or edit files only when the user explicitly asks for a written artifact.

If the target path is ambiguous or multiple repositories are plausible, ask one concise clarifying question before analysis.

## Read-Only Discovery

Start broad, then narrow. Prefer fast metadata and structure before reading implementation details.

1. Identify the repository root.
   - Use `git rev-parse --show-toplevel` when available.
   - Otherwise infer from manifest files and directory structure.
2. Inspect top-level documentation and manifests.
   - README files
   - `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `vite.config.*`, `next.config.*`
   - `pyproject.toml`, `requirements.txt`, `setup.py`, `uv.lock`
   - `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Makefile`
   - `Dockerfile`, `docker-compose.yml`, `.github/workflows/*`
3. Map the directory structure.
   - Prefer `rg --files` or a shallow directory listing.
   - Ignore dependency, build, cache, and VCS directories such as `.git`, `node_modules`, `.venv`, `dist`, `build`, `.next`, `target`, `__pycache__`, and coverage outputs.
   - Build a concise one-level project structure map for the output. Include top-level directories and important top-level files only; do not recursively expand the whole repository.
4. Identify entry points.
   - Web app: app/router/main files, server files, API route directories, middleware.
   - CLI: command registration, `main`, `__main__`, `bin`, argument parsing.
   - Backend service: server bootstrap, route registration, controller or handler layer.
   - Data or ML project: pipeline scripts, training/inference entry points, notebooks, config files.
   - Library: public exports, package entry, examples, tests.
5. Trace one representative runtime path.
   - Choose the path most aligned with the repository type and user focus.
   - Follow calls from entry point to orchestration layer, domain logic, persistence or external integration, and output.
6. Sample tests and examples.
   - Use tests, examples, demos, or fixtures to confirm how the project expects modules to be used.

Do not run installation, build, database, migration, network, destructive, or long-running commands unless the user asks and the environment permissions allow it.

## Analysis Priorities

Explain facts before judgments.

Focus on:

- what the project does
- how to run or use it, based on repository evidence
- what each important directory is responsible for
- where execution starts
- how the main flow moves through files and modules
- which modules or files are most important for a newcomer
- where key algorithms, business rules, state transitions, or data transformations live
- what concepts a beginner must understand before modifying the project

When evidence is incomplete, label conclusions as static-reading inference.

## Output Template

Use this structure unless the user requests a different format:

````markdown
# Project Onboarding Guide

## 1. What This Project Does

## 2. Tech Stack And How It Runs

## 3. Directory Map

Start this section with a one-level annotated tree. Use the repository root as the first line, then list top-level directories and important top-level files with short comments. Keep it concise and avoid expanding nested folders unless a single second-level folder is essential to understand the project split.

Example style:

```text
/path/to/project
├── app/                  # Main application source
├── packages/             # Internal packages or shared libraries
├── scripts/              # Build, release, migration, or maintenance scripts
├── docs/                 # Project documentation
├── tests/                # Test suite
├── package.json          # JavaScript package metadata and scripts
└── README.md             # Project overview and usage notes
```

## 4. Entry Points

## 5. Main Runtime Flow

## 6. Core Modules

## 7. Key Algorithms Or Business Logic

## 8. Newcomer Reading Path

## 9. Before You Modify Code

## 10. Unknowns And Static-Reading Assumptions
````

Keep the explanation beginner-friendly:

- Define project-specific terms the first time they appear.
- Prefer concrete file paths over abstract descriptions.
- In `Directory Map`, include a one-level annotated file tree before prose explanations.
- Use short call-flow lists for runtime logic.
- Use Mermaid diagrams when a visual map would clarify architecture or flow.
- Include 5-10 "read these first" files with a reason for each.

## Optional Written Artifact

Only when the user asks for a file, create a Markdown guide such as:

```text
docs/PROJECT_ONBOARDING.md
```

Before writing, check whether the target file already exists. If it exists, read it first and update conservatively instead of overwriting it wholesale.

## Quality Checklist

Before finishing, verify that the response includes:

- project purpose and audience
- detected tech stack, with evidence from files
- one-level annotated project structure tree
- top-level directory responsibilities
- real entry points with file paths
- at least one representative runtime flow
- core modules and why they matter
- key algorithm or business logic locations, if present
- a staged reading path for newcomers
- explicit unknowns or assumptions
- no code changes unless the user explicitly requested a written artifact

## Boundaries

- Do not present guesses as facts.
- Do not default to code review findings.
- Do not recommend refactors unless the user asks for improvement advice.
- Do not hide complexity from beginners; layer it from simple overview to deeper detail.
- Do not read every file in a large repository. Use structure, manifests, entry points, tests, and representative flows.
- Do not run project commands just to understand the repository unless the user asks for runtime verification.
