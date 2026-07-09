# code-lines

查找行数大于配置阈值的代码文件，并按行数递减排序。

## 配置

在项目根目录的 `.env` 文件中配置脚本。

```env
CODE_LINES_PROJECT_DIR=D:\Projects\project-a
CODE_LINES_MIN_LINES=1000
CODE_LINES_EXCLUDE_DIRS=
CODE_LINES_EXTENSIONS=
CODE_LINES_OUTPUT_FORMAT=table
CODE_LINES_OUTPUT_FILE=
```

`CODE_LINES_PROJECT_DIR` 是必填配置。相对路径会从脚本集合根目录解析。

`CODE_LINES_MIN_LINES` 默认值为 `1000`。只有行数大于该值的文件才会出现在结果中。

`CODE_LINES_EXCLUDE_DIRS` 是可选配置。可以用分号分隔额外要排除的目录名。常见依赖、构建、缓存和版本控制目录已经默认排除。

如果 `CODE_LINES_PROJECT_DIR` 目录下存在 `.gitignore` 文件，匹配的文件和目录会从行数统计中排除。

`CODE_LINES_EXTENSIONS` 是可选配置。留空时会扫描常见代码文件扩展名，也可以提供分号分隔的扩展名列表，例如 `.py;.ts;.tsx;.rs`。

## 运行

需要安装 Python 3。

在项目根目录运行快捷命令：

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

## 输出字段

| 字段 | 说明 |
| --- | --- |
| `lines` | 文件的物理行数。 |
| `relative_path` | 相对于 `CODE_LINES_PROJECT_DIR` 的文件路径。 |
| `path` | 文件绝对路径。仅在 CSV 和 JSON 输出中包含。 |