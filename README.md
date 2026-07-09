# MyScripts

按任务组织的个人脚本集合。每个脚本放在 `scripts/<script-name>` 目录下，可以根据任务选择最合适的语言实现。

## 初始化

1. 复制 `.env.example` 为 `.env`。
2. 根据需要更新对应脚本的配置项。
3. 确认本机已安装 Git 和 Python 3。
4. 通过 npm 快捷命令，或脚本自己的 `run.ps1` / `run.sh` 入口运行。

## 脚本

查看 [脚本索引](docs/脚本索引.md)。

## git-stats

`git-stats` 按提交日期汇总所有配置的 Git 仓库。

快捷命令：

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

## code-lines

`code-lines` 扫描配置的项目目录，列出超过 1000 行的代码文件，并遵守该目录下的 `.gitignore`。

快捷命令：

```powershell
npm run code-lines
```

Windows：

```powershell
.\scripts\code-lines\run.ps1
```

Linux/macOS：

```bash
./scripts/code-lines/run.sh
```