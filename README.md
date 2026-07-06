# MyScripts

Personal script collection organized by task. Each script lives in `scripts/<script-name>` and can use whichever language is the best fit for that job.

## Setup

1. Copy `.env.example` to `.env`.
2. Update the script-specific configuration values.
3. Make sure Git and Python 3 are available.
4. Run a script through an npm shortcut or its `run.ps1` / `run.sh` entrypoint.

## Scripts

See `docs/script-index.md`.

## Git Stats

`git-stats` aggregates all configured repositories by commit date.

Shortcut:

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
