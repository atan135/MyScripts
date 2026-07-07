#!/usr/bin/env python3
from __future__ import annotations

import csv
import fnmatch
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


VALID_OUTPUT_FORMATS = {"table", "csv", "json"}

DEFAULT_CODE_EXTENSIONS = {
    ".bat",
    ".c",
    ".cc",
    ".clj",
    ".cljs",
    ".cmake",
    ".cpp",
    ".cs",
    ".css",
    ".dart",
    ".dockerfile",
    ".erl",
    ".ex",
    ".exs",
    ".fs",
    ".go",
    ".h",
    ".hpp",
    ".hs",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".lua",
    ".m",
    ".mm",
    ".php",
    ".pl",
    ".ps1",
    ".py",
    ".r",
    ".rb",
    ".rs",
    ".scala",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".svelte",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
    ".zig",
}

DEFAULT_CODE_FILENAMES = {
    "BUILD",
    "CMakeLists.txt",
    "Dockerfile",
    "Gemfile",
    "Jenkinsfile",
    "Makefile",
    "Rakefile",
    "WORKSPACE",
    "justfile",
}

DEFAULT_EXCLUDE_DIRS = {
    ".cache",
    ".git",
    ".gradle",
    ".idea",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".svn",
    ".tox",
    ".venv",
    ".vscode",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
    "venv",
    "__pycache__",
}


@dataclass
class CodeLinesConfig:
    project_dir: Path
    min_lines: int
    exclude_dirs: set[str]
    code_extensions: set[str]
    gitignore_matcher: GitIgnoreMatcher
    output_format: str
    output_file: Path | None


@dataclass
class GitIgnoreRule:
    pattern: str
    negated: bool
    directory_only: bool
    basename_only: bool

    @property
    def pattern_parts(self) -> list[str]:
        return [part for part in self.pattern.split("/") if part]

    def matches(self, relative_path: str, is_dir: bool) -> bool:
        path_parts = [part for part in relative_path.split("/") if part]
        if not path_parts:
            return False

        if self.basename_only:
            parts_to_check = path_parts if is_dir else path_parts[:-1]
            if any(fnmatch.fnmatchcase(part, self.pattern) for part in parts_to_check):
                return True

            return not self.directory_only and fnmatch.fnmatchcase(path_parts[-1], self.pattern)

        if matches_full_path(self.pattern_parts, path_parts):
            return True

        return any(
            matches_full_path(self.pattern_parts, path_parts[:index])
            for index in range(1, len(path_parts))
        )


def matches_full_path(pattern_parts: list[str], path_parts: list[str]) -> bool:
    return match_path_segments(pattern_parts, path_parts)


class GitIgnoreMatcher:
    def __init__(self, rules: list[GitIgnoreRule]) -> None:
        self.rules = rules

    @classmethod
    def from_file(cls, gitignore_path: Path) -> GitIgnoreMatcher:
        if not gitignore_path.exists():
            return cls([])

        rules: list[GitIgnoreRule] = []
        for raw_line in gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines():
            rule = parse_gitignore_rule(raw_line)
            if rule:
                rules.append(rule)

        return cls(rules)

    def is_ignored(self, relative_path: str, is_dir: bool) -> bool:
        ignored = False
        normalized_path = relative_path.replace("\\", "/").strip("/")

        for rule in self.rules:
            if rule.matches(normalized_path, is_dir):
                ignored = not rule.negated

        return ignored

    def has_negation_under(self, relative_path: str) -> bool:
        normalized_path = relative_path.replace("\\", "/").strip("/")
        if not normalized_path:
            return False

        for rule in self.rules:
            if not rule.negated:
                continue

            pattern = rule.pattern.strip("/")
            if not pattern or rule.basename_only:
                continue

            if pattern == normalized_path or pattern.startswith(f"{normalized_path}/"):
                return True

        return False


@dataclass
class FileLineCount:
    path: Path
    relative_path: str
    lines: int

    def to_row(self) -> dict[str, str | int]:
        return asdict(self) | {"path": str(self.path)}


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists() or (path / ".env").exists() or (path / ".env.example").exists():
            return path
    return current


def load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        values[key] = value

    return values


def env_value(env_file_values: dict[str, str], key: str, default: str = "") -> str:
    return os.environ.get(key, env_file_values.get(key, default)).strip()


def resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def split_env_list(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(";") if item.strip()]


def strip_unescaped_trailing_spaces(value: str) -> str:
    while value.endswith(" "):
        backslash_count = 0
        index = len(value) - 2
        while index >= 0 and value[index] == "\\":
            backslash_count += 1
            index -= 1

        if backslash_count % 2 == 1:
            break

        value = value[:-1]

    return value


def parse_gitignore_rule(raw_line: str) -> GitIgnoreRule | None:
    line = strip_unescaped_trailing_spaces(raw_line)
    if not line:
        return None

    if line.startswith("#"):
        return None

    escaped_leading_bang = line.startswith("\\!")
    if line.startswith("\\#") or escaped_leading_bang:
        line = line[1:]

    negated = False if escaped_leading_bang else line.startswith("!")
    if negated:
        line = line[1:]

    if not line:
        return None

    directory_only = line.endswith("/")
    anchored = line.startswith("/")
    line = line.rstrip("/")
    line = line.lstrip("/")
    if not line:
        return None

    line = re.sub(r"\\([#! ])", r"\1", line)

    return GitIgnoreRule(
        pattern=line,
        negated=negated,
        directory_only=directory_only,
        basename_only=not anchored and "/" not in line,
    )


def match_path_segments(pattern_parts: list[str], path_parts: list[str]) -> bool:
    if not pattern_parts:
        return not path_parts

    pattern_part = pattern_parts[0]
    if pattern_part == "**":
        if len(pattern_parts) == 1:
            return True

        return any(
            match_path_segments(pattern_parts[1:], path_parts[index:])
            for index in range(len(path_parts) + 1)
        )

    if not path_parts:
        return False

    if not fnmatch.fnmatchcase(path_parts[0], pattern_part):
        return False

    return match_path_segments(pattern_parts[1:], path_parts[1:])


def normalize_extensions(raw_extensions: str) -> set[str]:
    if not raw_extensions:
        return DEFAULT_CODE_EXTENSIONS

    extensions: set[str] = set()
    for extension in split_env_list(raw_extensions):
        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"
        extensions.add(extension)

    return extensions


def parse_positive_int(raw_value: str, key: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer, got: {raw_value}") from exc

    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0, got: {raw_value}")

    return value


def load_config(project_root: Path) -> CodeLinesConfig:
    env_file_values = load_env_file(project_root / ".env")

    raw_project_dir = env_value(env_file_values, "CODE_LINES_PROJECT_DIR")
    if not raw_project_dir:
        raise ValueError("CODE_LINES_PROJECT_DIR is required.")

    project_dir = resolve_path(project_root, raw_project_dir)
    if not project_dir.exists():
        raise ValueError(f"CODE_LINES_PROJECT_DIR does not exist: {project_dir}")
    if not project_dir.is_dir():
        raise ValueError(f"CODE_LINES_PROJECT_DIR must be a directory: {project_dir}")

    min_lines = parse_positive_int(env_value(env_file_values, "CODE_LINES_MIN_LINES", "1000"), "CODE_LINES_MIN_LINES")

    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    exclude_dirs.update(split_env_list(env_value(env_file_values, "CODE_LINES_EXCLUDE_DIRS")))

    output_format = env_value(env_file_values, "CODE_LINES_OUTPUT_FORMAT", "table").lower()
    if output_format not in VALID_OUTPUT_FORMATS:
        valid = ", ".join(sorted(VALID_OUTPUT_FORMATS))
        raise ValueError(f"CODE_LINES_OUTPUT_FORMAT must be one of: {valid}")

    raw_output_file = env_value(env_file_values, "CODE_LINES_OUTPUT_FILE")
    output_file = resolve_path(project_root, raw_output_file) if raw_output_file else None

    return CodeLinesConfig(
        project_dir=project_dir,
        min_lines=min_lines,
        exclude_dirs=exclude_dirs,
        code_extensions=normalize_extensions(env_value(env_file_values, "CODE_LINES_EXTENSIONS")),
        gitignore_matcher=GitIgnoreMatcher.from_file(project_dir / ".gitignore"),
        output_format=output_format,
        output_file=output_file,
    )


def is_code_file(path: Path, code_extensions: set[str]) -> bool:
    if path.name in DEFAULT_CODE_FILENAMES:
        return True
    return path.suffix.lower() in code_extensions


def has_binary_marker(path: Path) -> bool:
    try:
        with path.open("rb") as file:
            return b"\0" in file.read(4096)
    except OSError:
        return True


def count_lines(path: Path) -> int:
    lines = 0
    last_byte = b""

    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            lines += chunk.count(b"\n")
            last_byte = chunk[-1:]

    if last_byte and last_byte != b"\n":
        lines += 1

    return lines


def iter_code_files(config: CodeLinesConfig) -> list[Path]:
    files: list[Path] = []

    for root, dir_names, file_names in os.walk(config.project_dir):
        root_path = Path(root)
        dir_names[:] = [
            dir_name
            for dir_name in dir_names
            if dir_name not in config.exclude_dirs
            and (
                not config.gitignore_matcher.is_ignored(
                    (root_path / dir_name).relative_to(config.project_dir).as_posix(),
                    is_dir=True,
                )
                or config.gitignore_matcher.has_negation_under(
                    (root_path / dir_name).relative_to(config.project_dir).as_posix()
                )
            )
        ]

        for file_name in file_names:
            path = root_path / file_name
            if config.gitignore_matcher.is_ignored(
                path.relative_to(config.project_dir).as_posix(),
                is_dir=False,
            ):
                continue

            if is_code_file(path, config.code_extensions):
                files.append(path)

    return files


def collect_file_line_counts(config: CodeLinesConfig) -> list[FileLineCount]:
    results: list[FileLineCount] = []

    for path in iter_code_files(config):
        if has_binary_marker(path):
            continue

        try:
            lines = count_lines(path)
        except OSError as exc:
            print(f"Warning: skipped unreadable file {path}: {exc}", file=sys.stderr)
            continue

        if lines <= config.min_lines:
            continue

        results.append(
            FileLineCount(
                path=path,
                relative_path=str(path.relative_to(config.project_dir)),
                lines=lines,
            )
        )

    return sorted(results, key=lambda item: (-item.lines, item.relative_path.lower()))


def format_table(rows: list[dict[str, str | int]]) -> str:
    columns = ["lines", "relative_path"]
    if not rows:
        return "No code files matched the configured line threshold."

    widths = {
        column: max(len(column), *(len(str(row[column])) for row in rows))
        for column in columns
    }

    header = "  ".join(column.ljust(widths[column]) for column in columns)
    separator = "  ".join("-" * widths[column] for column in columns)
    body = [
        "  ".join(str(row[column]).ljust(widths[column]) for column in columns)
        for row in rows
    ]

    return "\n".join([header, separator, *body])


def write_csv(output_file: Path, rows: list[dict[str, str | int]]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fields = ["lines", "relative_path", "path"]
    with output_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(output_file: Path, rows: list[dict[str, str | int]]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def output_results(config: CodeLinesConfig, rows: list[dict[str, str | int]]) -> None:
    if config.output_format == "table":
        table = format_table(rows)
        if config.output_file:
            config.output_file.parent.mkdir(parents=True, exist_ok=True)
            config.output_file.write_text(table + "\n", encoding="utf-8")
            print(f"Wrote table output to {config.output_file}")
        else:
            print(table)
        return

    if not config.output_file:
        raise ValueError(f"CODE_LINES_OUTPUT_FILE is required for {config.output_format} output.")

    if config.output_format == "csv":
        write_csv(config.output_file, rows)
    elif config.output_format == "json":
        write_json(config.output_file, rows)

    print(f"Wrote {config.output_format} output to {config.output_file}")


def main() -> int:
    project_root = find_project_root(Path(__file__).parents[3])

    try:
        config = load_config(project_root)
        file_line_counts = collect_file_line_counts(config)
        rows = [item.to_row() for item in file_line_counts]
        output_results(config, rows)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
