#!/usr/bin/env python3
"""Scan a project and write a conservative repo-scan report."""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".ai",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}
SKIP_FILES = {".DS_Store"}

SOURCE_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
}

ROOT_EVIDENCE = {
    ".git",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "README.md",
    "readme.md",
}


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def walk_project(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        current_path = Path(current)
        for file_name in sorted(files):
            if file_name in SKIP_FILES:
                continue
            yield current_path / file_name


def list_top_level(root: Path) -> tuple[list[str], list[str]]:
    dirs: list[str] = []
    files: list[str] = []
    try:
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if child.name in SKIP_DIRS or child.name in SKIP_FILES:
                continue
            if child.is_dir():
                dirs.append(child.name + "/")
            elif child.is_file():
                files.append(child.name)
    except OSError:
        pass
    return dirs, files


def detect_root_evidence(root: Path) -> list[str]:
    evidence: list[str] = []
    try:
        actual_names = {path.name for path in root.iterdir()}
    except OSError:
        actual_names = set()
    for name in sorted(ROOT_EVIDENCE):
        if name in actual_names:
            evidence.append(name)
    return evidence


def detect_languages(root: Path, files: list[Path]) -> list[tuple[str, int, list[str]]]:
    counts: Counter[str] = Counter()
    examples: defaultdict[str, list[str]] = defaultdict(list)

    for path in files:
        language = SOURCE_EXTENSIONS.get(path.suffix)
        if not language:
            continue
        counts[language] += 1
        if len(examples[language]) < 5:
            examples[language].append(rel(path, root))

    if (root / "pyproject.toml").exists():
        counts["Python"] += 1
        examples["Python"].append("pyproject.toml")
    if (root / "tsconfig.json").exists():
        counts["TypeScript"] += 1
        examples["TypeScript"].append("tsconfig.json")

    return [(language, count, examples[language]) for language, count in counts.most_common()]


def package_json_data(root: Path) -> dict:
    return load_json(root / "package.json")


def detect_package_managers(root: Path, package_json: dict) -> list[tuple[str, list[str]]]:
    managers: list[tuple[str, list[str]]] = []
    checks = [
        ("npm", ["package.json", "package-lock.json"]),
        ("pnpm", ["pnpm-lock.yaml"]),
        ("Yarn", ["yarn.lock"]),
        ("Bun", ["bun.lockb", "bun.lock"]),
        ("pip", ["requirements.txt"]),
        ("pip-tools", ["requirements.in"]),
        ("Poetry", ["poetry.lock", "pyproject.toml"]),
        ("uv", ["uv.lock", "pyproject.toml"]),
        ("Cargo", ["Cargo.toml"]),
        ("Go modules", ["go.mod"]),
        ("Maven", ["pom.xml"]),
        ("Gradle", ["build.gradle", "build.gradle.kts"]),
    ]
    for manager, names in checks:
        evidence = [name for name in names if (root / name).exists()]
        if evidence:
            managers.append((manager, evidence))

    if package_json and not any(name == "npm" for name, _ in managers):
        managers.append(("npm-compatible", ["package.json"]))

    return managers


def dependencies_from_package_json(package_json: dict) -> set[str]:
    deps: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package_json.get(key)
        if isinstance(value, dict):
            deps.update(value.keys())
    return deps


def detect_frameworks(root: Path, files: list[Path], package_json: dict) -> list[tuple[str, list[str]]]:
    frameworks: list[tuple[str, list[str]]] = []
    deps = dependencies_from_package_json(package_json)

    js_framework_checks = [
        ("React", "react", ["package.json"]),
        ("Next.js", "next", ["package.json"]),
        ("Vue", "vue", ["package.json"]),
        ("Nuxt", "nuxt", ["package.json"]),
        ("Svelte", "svelte", ["package.json"]),
        ("Vite", "vite", ["package.json"]),
        ("Express", "express", ["package.json"]),
        ("NestJS", "@nestjs/core", ["package.json"]),
    ]
    for label, dep, evidence in js_framework_checks:
        if dep in deps:
            frameworks.append((label, evidence))

    config_checks = [
        ("Vite", ["vite.config.ts", "vite.config.js", "vite.config.mjs"]),
        ("Next.js", ["next.config.js", "next.config.mjs", "next.config.ts"]),
        ("Remix", ["remix.config.js"]),
        ("Astro", ["astro.config.mjs", "astro.config.ts"]),
        ("Tailwind CSS", ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"]),
    ]
    for label, names in config_checks:
        evidence = [name for name in names if (root / name).exists()]
        if evidence and not any(existing == label for existing, _ in frameworks):
            frameworks.append((label, evidence))

    python_evidence: defaultdict[str, list[str]] = defaultdict(list)
    for path in files:
        if path.suffix != ".py":
            continue
        relative = rel(path, root)
        imports, calls = python_imports_and_calls(path)
        if "fastapi" in imports or "FastAPI" in calls:
            python_evidence["FastAPI"].append(relative)
        if "flask" in imports or "Flask" in calls:
            python_evidence["Flask"].append(relative)
        if any(name == "django" or name.startswith("django.") for name in imports) or path.name == "manage.py":
            python_evidence["Django"].append(relative)

    for label, evidence in python_evidence.items():
        frameworks.append((label, evidence[:5]))

    return frameworks


def python_imports_and_calls(path: Path) -> tuple[set[str], set[str]]:
    text = read_text(path, limit=200_000)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set(), set()

    imports: set[str] = set()
    calls: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    return imports, calls


def detect_entry_points(root: Path) -> list[tuple[str, str, str]]:
    candidates = [
        ("Backend", "main.py", "Common Python application entry"),
        ("Backend", "app.py", "Common Python application entry"),
        ("Backend", "manage.py", "Django management entry"),
        ("Backend", "server.js", "Common Node server entry"),
        ("Backend", "src/main.py", "Common Python source entry"),
        ("Backend", "src/app.py", "Common Python source entry"),
        ("Frontend", "src/main.tsx", "Common React/Vite entry"),
        ("Frontend", "src/main.ts", "Common Vite entry"),
        ("Frontend", "src/main.jsx", "Common React/Vite entry"),
        ("Frontend", "src/App.tsx", "Common React app root"),
        ("Frontend", "pages/index.tsx", "Common Next.js page"),
        ("Frontend", "app/page.tsx", "Common Next.js app router page"),
        ("CLI / worker", "src/index.ts", "Common TypeScript entry"),
        ("CLI / worker", "index.js", "Common Node entry"),
    ]
    found: list[tuple[str, str, str]] = []
    for kind, relative, reason in candidates:
        if (root / relative).exists():
            found.append((kind, relative, reason))
    return found


def detect_tests(root: Path, files: list[Path], package_json: dict) -> list[tuple[str, list[str]]]:
    findings: list[tuple[str, list[str]]] = []
    test_dirs = [name for name in ("test", "tests", "__tests__", "spec") if (root / name).exists()]
    if test_dirs:
        findings.append(("Test directories", test_dirs))

    test_files = [
        rel(path, root)
        for path in files
        if path.name.startswith("test_")
        or path.name.endswith("_test.py")
        or path.name.endswith(".test.ts")
        or path.name.endswith(".test.tsx")
        or path.name.endswith(".spec.ts")
        or path.name.endswith(".spec.tsx")
    ][:10]
    if test_files:
        findings.append(("Test files", test_files))

    scripts = package_json.get("scripts") if isinstance(package_json.get("scripts"), dict) else {}
    if "test" in scripts:
        findings.append(("npm test script", ["package.json"]))
    if (root / "pytest.ini").exists():
        findings.append(("pytest config", ["pytest.ini"]))

    return findings


def detect_config_files(root: Path) -> list[str]:
    names = [
        ".env.example",
        ".eslintrc",
        ".eslintrc.cjs",
        ".eslintrc.js",
        ".prettierrc",
        "biome.json",
        "docker-compose.yml",
        "Dockerfile",
        "eslint.config.js",
        "jest.config.js",
        "package.json",
        "playwright.config.ts",
        "pyproject.toml",
        "pytest.ini",
        "ruff.toml",
        "tsconfig.json",
        "vite.config.ts",
    ]
    return [name for name in names if (root / name).exists()]


def detect_database_files(root: Path, files: list[Path], package_json: dict) -> list[tuple[str, list[str]]]:
    findings: list[tuple[str, list[str]]] = []
    candidate_dirs = ["migrations", "prisma", "db", "database", "supabase", "alembic"]
    dirs = [name for name in candidate_dirs if (root / name).exists()]
    if dirs:
        findings.append(("Database-related directories", dirs))

    db_files = [
        rel(path, root)
        for path in files
        if path.name in {"schema.prisma", "alembic.ini"}
        or path.suffix in {".sql", ".sqlite", ".db"}
    ][:10]
    if db_files:
        findings.append(("Database-related files", db_files))

    deps = dependencies_from_package_json(package_json)
    db_deps = sorted(deps & {"@prisma/client", "prisma", "pg", "mysql2", "sqlite3", "mongoose"})
    if db_deps:
        findings.append(("Database-related package dependencies", ["package.json: " + ", ".join(db_deps)]))

    return findings


def detect_api_routes(root: Path, files: list[Path]) -> list[tuple[str, list[str]]]:
    findings: list[tuple[str, list[str]]] = []
    route_dirs = [
        rel(path, root)
        for path in (root / "src").glob("**/*")
        if path.is_dir() and path.name in {"api", "routes", "controllers"}
    ] if (root / "src").exists() else []

    top_route_dirs = [name for name in ("api", "routes", "controllers") if (root / name).exists()]
    if top_route_dirs or route_dirs:
        findings.append(("Route directories", top_route_dirs + route_dirs[:10]))

    route_files = []
    for path in files:
        relative = rel(path, root)
        if "/api/" in f"/{relative}/" or "/routes/" in f"/{relative}/" or "/controllers/" in f"/{relative}/":
            route_files.append(relative)
        elif path.name == "route.ts" or path.name == "route.js":
            route_files.append(relative)
        if len(route_files) >= 15:
            break
    if route_files:
        findings.append(("Route files", route_files))

    return findings


def command_candidates(root: Path, package_json: dict) -> dict[str, list[tuple[str, str]]]:
    commands: dict[str, list[tuple[str, str]]] = {
        "Install": [],
        "Test": [],
        "Build": [],
        "Lint": [],
        "Typecheck": [],
    }

    scripts = package_json.get("scripts") if isinstance(package_json.get("scripts"), dict) else {}
    if package_json:
        if (root / "pnpm-lock.yaml").exists():
            commands["Install"].append(("pnpm install", "pnpm-lock.yaml"))
        elif (root / "yarn.lock").exists():
            commands["Install"].append(("yarn install", "yarn.lock"))
        elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
            commands["Install"].append(("bun install", "bun lockfile"))
        else:
            commands["Install"].append(("npm install", "package.json"))

    for script_name, bucket in (
        ("test", "Test"),
        ("build", "Build"),
        ("lint", "Lint"),
        ("typecheck", "Typecheck"),
        ("type-check", "Typecheck"),
    ):
        if script_name in scripts:
            command = package_manager_run_command(root, script_name)
            commands[bucket].append((command, f"package.json scripts.{script_name}"))

    if (root / "requirements.txt").exists():
        commands["Install"].append(("pip install -r requirements.txt", "requirements.txt"))
    if (root / "pyproject.toml").exists():
        commands["Install"].append(("pip install -e .", "pyproject.toml"))
    if (root / "pytest.ini").exists() or (root / "tests").exists():
        commands["Test"].append(("pytest", "pytest.ini or tests/"))
    if (root / "Cargo.toml").exists():
        commands["Build"].append(("cargo build", "Cargo.toml"))
        commands["Test"].append(("cargo test", "Cargo.toml"))
    if (root / "go.mod").exists():
        commands["Build"].append(("go build ./...", "go.mod"))
        commands["Test"].append(("go test ./...", "go.mod"))

    return commands


def package_manager_run_command(root: Path, script_name: str) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return f"pnpm {script_name}"
    if (root / "yarn.lock").exists():
        return f"yarn {script_name}"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return f"bun run {script_name}"
    return f"npm run {script_name}" if script_name != "test" else "npm test"


def detect_high_risk_areas(root: Path) -> list[tuple[str, str]]:
    candidates = [
        ("migrations/", "Database migration directory"),
        ("prisma/", "Database schema or migration directory"),
        ("alembic/", "Database migration directory"),
        ("infra/", "Infrastructure directory"),
        ("terraform/", "Infrastructure as code directory"),
        ("k8s/", "Deployment manifests"),
        ("charts/", "Deployment charts"),
        (".github/workflows/", "CI workflow configuration"),
    ]
    return [(path, reason) for path, reason in candidates if (root / path).exists()]


def markdown_list(items: list[str], empty: str = "Unknown") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- `{item}`" for item in items)


def render_report(root: Path) -> str:
    files = list(walk_project(root))
    package_json = package_json_data(root)
    root_evidence = detect_root_evidence(root)
    top_dirs, top_files = list_top_level(root)
    languages = detect_languages(root, files)
    package_managers = detect_package_managers(root, package_json)
    frameworks = detect_frameworks(root, files, package_json)
    entry_points = detect_entry_points(root)
    tests = detect_tests(root, files, package_json)
    configs = detect_config_files(root)
    database = detect_database_files(root, files, package_json)
    api_routes = detect_api_routes(root, files)
    commands = command_candidates(root, package_json)
    high_risk = detect_high_risk_areas(root)

    unknowns: list[str] = []
    if not root_evidence:
        unknowns.append("Project root could not be confirmed from common root evidence files.")
    if not languages:
        unknowns.append("Primary language not detected.")
    if not frameworks:
        unknowns.append("Framework not detected.")
    if not package_managers:
        unknowns.append("Package manager not detected.")
    if not entry_points:
        unknowns.append("Application entry points not detected.")
    if not tests:
        unknowns.append("Testing setup not detected.")
    if not database:
        unknowns.append("Database or storage setup not detected.")
    if not api_routes:
        unknowns.append("API route structure not detected.")
    if not any(commands[bucket] for bucket in commands):
        unknowns.append("Build, test, lint, and typecheck commands not detected.")

    lines: list[str] = [
        "# Repo Scan Report",
        "",
        "## Scan Metadata",
        "",
        f"- Target project: `{root.as_posix()}`",
        f"- Scan time: `{datetime.now(timezone.utc).isoformat()}`",
        "- Scanner: `scripts/scan_project.py`",
        "- Confidence: `medium` if evidence is listed; `low` for Unknowns",
        "",
        "## Root Evidence",
        "",
        markdown_list(root_evidence, "No common root evidence found"),
        "",
        "## Directory Structure",
        "",
        "Top-level directories:",
        "",
        markdown_list(top_dirs, "No top-level directories found"),
        "",
        "Top-level files:",
        "",
        markdown_list(top_files, "No top-level files found"),
        "",
        "## Language Detection",
        "",
    ]

    if languages:
        for language, count, evidence in languages:
            lines.append(f"- {language}: detected from {count} evidence item(s): " + ", ".join(f"`{item}`" for item in evidence))
    else:
        lines.append("- Unknown")

    lines.extend(["", "## Framework Detection", ""])
    if frameworks:
        for name, evidence in frameworks:
            lines.append(f"- {name}: detected from " + ", ".join(f"`{item}`" for item in evidence))
    else:
        lines.append("- Unknown")

    lines.extend(["", "## Package Managers", ""])
    if package_managers:
        for name, evidence in package_managers:
            lines.append(f"- {name}: detected from " + ", ".join(f"`{item}`" for item in evidence))
    else:
        lines.append("- Unknown")

    lines.extend(["", "## Entry Points", ""])
    if entry_points:
        for kind, path, reason in entry_points:
            lines.append(f"- {kind}: `{path}` ({reason})")
    else:
        lines.append("- Unknown")

    lines.extend(["", "## Database And Storage", ""])
    append_findings(lines, database)

    lines.extend(["", "## API Routes", ""])
    append_findings(lines, api_routes)

    lines.extend(["", "## Test Setup", ""])
    append_findings(lines, tests)

    lines.extend(["", "## Build / Lint / Typecheck Commands", ""])
    for bucket, values in commands.items():
        lines.append(f"### {bucket}")
        lines.append("")
        if values:
            for command, evidence in values:
                lines.append(f"- `{command}` (evidence: `{evidence}`)")
        else:
            lines.append("- Unknown")
        lines.append("")

    lines.extend(["## Configuration Files", ""])
    lines.append(markdown_list(configs, "No common configuration files detected"))

    doc_files = [
        rel(path, root)
        for path in files
        if path.name.lower().startswith("readme") or path.suffix.lower() in {".md", ".rst"}
    ][:20]
    lines.extend(["", "## Documentation Files", ""])
    lines.append(markdown_list(doc_files, "No documentation files detected"))

    lines.extend(["", "## High Risk Areas", ""])
    if high_risk:
        for path, reason in high_risk:
            lines.append(f"- `{path}`: {reason}")
    else:
        lines.append("- Unknown")

    lines.extend(["", "## Unknowns", ""])
    if unknowns:
        lines.extend(f"- {item}" for item in unknowns)
    else:
        lines.append("- None from this scan")

    lines.extend(
        [
            "",
            "## Recommendations For project-context.md",
            "",
            "- Copy only verified facts from this report.",
            "- Keep undetected language, framework, command, database, API, and testing details in Unknowns.",
            "- Include evidence paths for every key fact.",
            "",
            "## Recommendations For project-specific-rules.md",
            "",
            "- Use detected package managers and commands as required commands only when relevant.",
            "- Use detected high risk areas as explicit do-not-modify-without-permission rules.",
            "- Keep ownership boundaries unknown until verified by code structure or user confirmation.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def append_findings(lines: list[str], findings: list[tuple[str, list[str]]]) -> None:
    if not findings:
        lines.append("- Unknown")
        return
    for label, evidence in findings:
        lines.append(f"- {label}: " + ", ".join(f"`{item}`" for item in evidence))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a target project and generate .ai/repo-scan-report.md."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target project directory. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        help="Report output path. Defaults to TARGET/.ai/repo-scan-report.md.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    target = Path(args.target).resolve()

    if not target.exists():
        print(f"Target path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"Target path is not a directory: {target}", file=sys.stderr)
        return 1

    output = Path(args.output).resolve() if args.output else target / ".ai" / "repo-scan-report.md"
    report = render_report(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(output.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
