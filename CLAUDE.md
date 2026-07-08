# CLAUDE.md

本文件面向 AI 编程助手，说明 `MyScripts` 仓库的项目背景、目录约定、开发流程和文档规范。执行任务前请先阅读本文件，再结合当前请求和现有代码做最小必要改动。

## 项目概览

`MyScripts` 是个人脚本集合仓库。每个脚本按任务独立放在 `scripts/<script-name>` 目录下，可以根据任务选择合适语言实现。当前脚本主要通过根目录 `package.json` 中的 npm shortcut、Windows `run.ps1` 和 Linux/macOS `run.sh` 运行。

当前已有脚本：

- `git-stats`：按日期汇总多个 Git 仓库的提交数和代码变更行数。
- `code-lines`：扫描配置的项目目录，列出超过阈值的代码文件，并遵守目标项目根目录的 `.gitignore`。

## 目录约定

- `scripts/<script-name>/`：单个脚本的完整实现目录。
- `scripts/<script-name>/src/`：脚本源码。
- `scripts/<script-name>/run.ps1`：Windows 入口。
- `scripts/<script-name>/run.sh`：Linux/macOS 入口。
- `scripts/<script-name>/README.md`：脚本使用说明。
- `scripts/<script-name>/outputs/`：脚本局部输出目录，只保留 `.gitkeep`，不要提交生成结果。
- `outputs/`：全局输出目录，只保留必要的 `.gitkeep`，不要提交生成结果。
- `docs/`：跨脚本索引、说明和规范文档。
- `shared/`：可复用工具代码目录。只有确实被多个脚本复用时再放入共享代码。

## 配置约定

- 根目录 `.env.example` 记录所有脚本可用配置项。
- 根目录 `.env` 是本地配置，不要提交。
- 新脚本的环境变量使用脚本名前缀，例如 `CODE_LINES_`、`GIT_STATS_`。
- 相对路径配置应从仓库根目录解析。
- 多值配置优先使用分号分隔，保持与现有脚本风格一致。

## 开发规范

- 优先沿用现有脚本结构：`src/main.py`、`run.ps1`、`run.sh`、脚本 README、根 README 索引说明。
- Python 脚本默认不引入第三方依赖，除非任务收益明显且已更新安装说明。
- 新增脚本时同步更新：
  - `package.json` 的 npm shortcut。
  - `.env.example` 的配置样例。
  - 根目录 `README.md` 的脚本入口说明。
  - `docs/script-index.md` 的脚本索引。
- 不要提交 `.env`、缓存、构建产物、输出文件、日志或临时测试目录。
- 修改已有脚本时保持行为兼容，除非用户明确要求改变默认行为。
- 涉及路径、文件遍历、删除、移动等操作时，必须谨慎处理绝对路径和相对路径，避免误操作仓库外文件。

## 文档规范

- 项目文档内容需要使用中文，除非需要保留命令、变量名、错误信息、API 名称或英文专有名词。
- 除 `README.md` 这类通用入口文档外，其他新增文档文件名尽量使用中文文件名。
- 文档应说明脚本用途、配置项、运行方式、输出字段和注意事项。
- 文档中的命令示例需要能直接复制执行，并区分 Windows PowerShell 与 Linux/macOS shell。
- 修改脚本行为时，同步更新对应文档，不要让 README 和实际行为脱节。

## 验证规范

- Python 脚本至少运行语法检查：

```powershell
py -3 -B -m py_compile <path-to-main.py>
```

- 修改 npm shortcut 或 `package.json` 后，检查 JSON 可解析。
- 对脚本行为变更，优先用临时目录或临时环境变量做最小可复现验证。
- 验证命令不要依赖用户本地 `.env` 的私有路径；可以临时设置环境变量覆盖。
- 验证后清理 `__pycache__`、临时输出和测试目录。

## Git 规范

- 提交前查看：

```powershell
git status --short
git diff --stat
```

- 只暂存当前任务相关文件，不要混入本地配置和无关改动。
- 提交信息使用中文，优先采用 `<type>(<scope>): <summary>` 格式。
- 功能新增使用 `feat`，修复使用 `fix`，文档使用 `docs`，维护配置使用 `chore`。
- 提交前复核暂存区：

```powershell
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
```

## AI 协作注意事项

- 先理解现有脚本模式，再实现改动。
- 保持改动聚焦，避免顺手重构无关脚本。
- 如果发现用户本地有未提交改动，先识别是否相关；不要回滚用户改动。
- 能通过本地上下文判断的问题直接处理，不要频繁要求用户确认。
- 最终回复需要说明改了哪些文件、如何验证，以及是否还有未完成事项。
