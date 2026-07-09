# git-stats

按日期汇总所有配置 Git 仓库的提交数量和代码变更行数。

## 配置

在项目根目录的 `.env` 文件中配置脚本。

```env
GIT_STATS_REPOS=D:\Projects\project-a;D:\Projects\project-b
GIT_STATS_DATE_FROM=
GIT_STATS_DATE_TO=
GIT_STATS_AUTHOR=
GIT_STATS_OUTPUT_FORMAT=table
GIT_STATS_OUTPUT_FILE=
```

`GIT_STATS_REPOS` 支持多个仓库路径，使用分号分隔。相对路径会从项目根目录解析。

`GIT_STATS_DATE_FROM` 和 `GIT_STATS_DATE_TO` 都是可选配置。两者都留空时会扫描全部历史记录。`GIT_STATS_DATE_TO` 会包含配置日期当天的完整时间范围。

## 运行

需要安装 Git 和 Python 3。

在项目根目录运行快捷命令：

```powershell
npm run git-stats
```

Windows：

```powershell
.\scripts\git-stats\run.ps1
```

Linux/macOS：

```bash
./scripts/git-stats/run.sh
```

## 输出字段

| 字段 | 说明 |
| --- | --- |
| `date` | 提交日期，格式为 `YYYY-MM-DD`。 |
| `commit_count` | 所有配置仓库在该日期的提交总数。 |
| `lines_added` | 所有配置仓库在该日期的新增行数。 |
| `lines_deleted` | 所有配置仓库在该日期的删除行数。 |
| `lines_changed` | 新增行数与删除行数之和。 |