#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


VALID_OUTPUT_FORMATS = {"table", "csv", "json"}


@dataclass
class GitStatsConfig:
    repos: list[Path]
    date_from: str
    date_to: str
    author: str
    output_format: str
    output_file: Path | None


@dataclass
class DailyStats:
    date: str
    commit_count: int
    lines_added: int
    lines_deleted: int

    @property
    def lines_changed(self) -> int:
        return self.lines_added + self.lines_deleted

    def to_row(self) -> dict[str, str | int]:
        data = asdict(self)
        data["lines_changed"] = self.lines_changed
        return data


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


def validate_date(value: str, key: str) -> None:
    if not value:
        return
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{key} must use YYYY-MM-DD format, got: {value}") from exc


def split_repos(raw_repos: str) -> list[str]:
    return [repo.strip() for repo in raw_repos.split(";") if repo.strip()]


def resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def load_config(project_root: Path) -> GitStatsConfig:
    env_file_values = load_env_file(project_root / ".env")

    raw_repos = env_value(env_file_values, "GIT_STATS_REPOS")
    if not raw_repos:
        raise ValueError("GIT_STATS_REPOS is required. Separate multiple paths with semicolons.")

    date_from = env_value(env_file_values, "GIT_STATS_DATE_FROM")
    date_to = env_value(env_file_values, "GIT_STATS_DATE_TO")
    validate_date(date_from, "GIT_STATS_DATE_FROM")
    validate_date(date_to, "GIT_STATS_DATE_TO")

    output_format = env_value(env_file_values, "GIT_STATS_OUTPUT_FORMAT", "table").lower()
    if output_format not in VALID_OUTPUT_FORMATS:
        valid = ", ".join(sorted(VALID_OUTPUT_FORMATS))
        raise ValueError(f"GIT_STATS_OUTPUT_FORMAT must be one of: {valid}")

    raw_output_file = env_value(env_file_values, "GIT_STATS_OUTPUT_FILE")
    output_file = resolve_path(project_root, raw_output_file) if raw_output_file else None

    return GitStatsConfig(
        repos=[resolve_path(project_root, repo) for repo in split_repos(raw_repos)],
        date_from=date_from,
        date_to=date_to,
        author=env_value(env_file_values, "GIT_STATS_AUTHOR"),
        output_format=output_format,
        output_file=output_file,
    )


def run_git(repo: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git executable was not found in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else str(exc)
        raise RuntimeError(f"Git command failed for {repo}: {stderr}") from exc

    return result.stdout


def is_git_repository(repo: Path) -> bool:
    if not repo.exists() or not repo.is_dir():
        return False

    try:
        output = run_git(repo, ["rev-parse", "--is-inside-work-tree"]).strip().lower()
    except RuntimeError:
        return False

    return output == "true"


def has_commits(repo: Path) -> bool:
    try:
        run_git(repo, ["rev-parse", "--verify", "HEAD"])
    except RuntimeError:
        return False

    return True


def build_log_filters(config: GitStatsConfig) -> list[str]:
    filters: list[str] = []
    if config.date_from:
        filters.append(f"--since={config.date_from}")
    if config.date_to:
        filters.append(f"--until={config.date_to} 23:59:59")
    if config.author:
        filters.append(f"--author={config.author}")
    return filters


def parse_daily_numstat(output: str) -> dict[str, DailyStats]:
    daily = defaultdict(lambda: {"commit_count": 0, "lines_added": 0, "lines_deleted": 0})
    current_date = ""

    for line in output.splitlines():
        if not line:
            continue

        if line.startswith("--COMMIT--"):
            parts = line[len("--COMMIT--") :].split("\t")
            if len(parts) < 2:
                current_date = ""
                continue

            current_date = parts[1].strip()
            if current_date:
                daily[current_date]["commit_count"] += 1
            continue

        if not current_date:
            continue

        parts = line.split("\t")
        if len(parts) < 3:
            continue

        added, deleted = parts[0], parts[1]
        if added == "-" or deleted == "-":
            continue

        try:
            daily[current_date]["lines_added"] += int(added)
            daily[current_date]["lines_deleted"] += int(deleted)
        except ValueError:
            continue

    return {
        date: DailyStats(
            date=date,
            commit_count=values["commit_count"],
            lines_added=values["lines_added"],
            lines_deleted=values["lines_deleted"],
        )
        for date, values in daily.items()
    }


def collect_repo_daily_stats(repo: Path, config: GitStatsConfig) -> dict[str, DailyStats]:
    if not is_git_repository(repo):
        raise RuntimeError(f"Not a Git repository: {repo}")

    if not has_commits(repo):
        return {}

    filters = build_log_filters(config)
    log_output = run_git(
        repo,
        [
            "log",
            "--date=short",
            "--numstat",
            "--pretty=format:--COMMIT--%H%x09%cd",
            *filters,
        ],
    )

    return parse_daily_numstat(log_output)


def collect_daily_stats(config: GitStatsConfig) -> list[DailyStats]:
    totals: dict[str, DailyStats] = {}

    for repo in config.repos:
        repo_daily_stats = collect_repo_daily_stats(repo, config)
        for date, stats in repo_daily_stats.items():
            if date not in totals:
                totals[date] = DailyStats(
                    date=date,
                    commit_count=0,
                    lines_added=0,
                    lines_deleted=0,
                )

            totals[date].commit_count += stats.commit_count
            totals[date].lines_added += stats.lines_added
            totals[date].lines_deleted += stats.lines_deleted

    return [totals[date] for date in sorted(totals)]


def format_table(rows: list[dict[str, str | int]]) -> str:
    columns = ["date", "commit_count", "lines_added", "lines_deleted", "lines_changed"]
    if not rows:
        return "No commits found."

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
    fields = [
        "date",
        "commit_count",
        "lines_added",
        "lines_deleted",
        "lines_changed",
    ]
    with output_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(output_file: Path, rows: list[dict[str, str | int]]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def output_results(config: GitStatsConfig, rows: list[dict[str, str | int]]) -> None:
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
        raise ValueError(f"GIT_STATS_OUTPUT_FILE is required for {config.output_format} output.")

    if config.output_format == "csv":
        write_csv(config.output_file, rows)
    elif config.output_format == "json":
        write_json(config.output_file, rows)

    print(f"Wrote {config.output_format} output to {config.output_file}")


def main() -> int:
    project_root = find_project_root(Path(__file__).parents[3])

    try:
        config = load_config(project_root)
        stats = collect_daily_stats(config)
        rows = [item.to_row() for item in stats]
        output_results(config, rows)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
