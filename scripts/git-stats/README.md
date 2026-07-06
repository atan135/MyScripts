# git-stats

Summarizes commit count and changed lines by day across all configured Git repositories.

## Configuration

Configure the script in the project-level `.env` file.

```env
GIT_STATS_REPOS=D:\Projects\project-a;D:\Projects\project-b
GIT_STATS_DATE_FROM=
GIT_STATS_DATE_TO=
GIT_STATS_AUTHOR=
GIT_STATS_OUTPUT_FORMAT=table
GIT_STATS_OUTPUT_FILE=
```

`GIT_STATS_REPOS` accepts multiple paths separated by semicolons. Relative paths are resolved from the project root.

`GIT_STATS_DATE_FROM` and `GIT_STATS_DATE_TO` are optional. Leave both empty to scan all history. `GIT_STATS_DATE_TO` includes the full configured day.

## Run

Requires Git and Python 3.

Shortcut from the project root:

```powershell
npm run git-stats
```

Windows:

```powershell
.\scripts\git-stats\run.ps1
```

Linux/macOS:

```bash
./scripts/git-stats/run.sh
```

## Output Fields

| Field | Description |
| --- | --- |
| `date` | Commit date in `YYYY-MM-DD` format. |
| `commit_count` | Total commits from all configured repositories on that date. |
| `lines_added` | Total added lines from all configured repositories on that date. |
| `lines_deleted` | Total deleted lines from all configured repositories on that date. |
| `lines_changed` | Added plus deleted lines. |
