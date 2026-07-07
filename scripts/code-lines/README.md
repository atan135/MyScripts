# code-lines

Finds code files whose line count is greater than the configured threshold, sorted by line count descending.

## Configuration

Configure the script in the project-level `.env` file.

```env
CODE_LINES_PROJECT_DIR=D:\Projects\project-a
CODE_LINES_MIN_LINES=1000
CODE_LINES_EXCLUDE_DIRS=
CODE_LINES_EXTENSIONS=
CODE_LINES_OUTPUT_FORMAT=table
CODE_LINES_OUTPUT_FILE=
```

`CODE_LINES_PROJECT_DIR` is required. Relative paths are resolved from the script collection root.

`CODE_LINES_MIN_LINES` defaults to `1000`. Files must be greater than this value to appear in the result.

`CODE_LINES_EXCLUDE_DIRS` is optional. Add extra directory names separated by semicolons. Common dependency, build, cache, and VCS directories are already excluded by default.

If `CODE_LINES_PROJECT_DIR` contains a `.gitignore` file, matching files and directories are excluded from the line-count scan.

`CODE_LINES_EXTENSIONS` is optional. Leave empty to scan common code file extensions, or provide a semicolon-separated list such as `.py;.ts;.tsx;.rs`.

## Run

Requires Python 3.

Shortcut from the project root:

```powershell
npm run code-lines
```

Windows:

```powershell
.\scripts\code-lines\run.ps1
```

Linux/macOS:

```bash
./scripts/code-lines/run.sh
```

## Output Fields

| Field | Description |
| --- | --- |
| `lines` | Physical line count for the file. |
| `relative_path` | File path relative to `CODE_LINES_PROJECT_DIR`. |
| `path` | Absolute file path. Included in CSV and JSON output. |
