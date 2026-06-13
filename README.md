# md2image - Markdown 自动转图片插件

AstrBot 插件，自动检测 AI 回复中的 Markdown 格式，使用 Playwright + Chromium 渲染为高清手账风格图片，解决 QQ 等平台无法渲染 Markdown 的问题。

## ✨ 功能特性

- **自动检测**：AI 回复中包含列表、加粗、表格、代码块等 Markdown 语法时，自动转换为图片发送
- **手动转换**：支持 `/md2img` 命令手动将文本转为图片
- **四套主题**：绿野 🌿 / 晴蓝 ◈ / 绯红 ♡ / 金典 ❖，随机切换
- **移动端友好**：viewport 480px + 17px 字号，手机端阅读清晰不费力
- **代码高亮**：支持代码块语法高亮（基于 Pygments）
- **智能裁剪**：根据内容高度自动裁剪，无多余空白

## 📦 安装

### 前置依赖

需要安装 Chromium 浏览器：

```bash
python -m playwright install chromium
```

### 安装插件

在 AstrBot 插件目录中克隆本仓库：

```bash
git clone https://github.com/Nelson-Zeng/md2image.git
```

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

## 🚀 使用方法

### 自动模式

无需任何操作，AI 回复中若包含 Markdown 格式（至少匹配 2 种语法，且内容超过 60 字），插件会自动将其渲染为图片。

### 手动模式

```
/md2img <Markdown 内容>
```

或直接发送 `/md2img`，然后在 30 秒内发送要转换的 Markdown 文本。

## 🎨 主题预览

| 绿野 | 晴蓝 | 绯红 | 金典 |
|:---:|:---:|:---:|:---:|
| 🌿 | ◈ | ♡ | ❖ |
| 清新草绿 | 天空蓝 | 樱花粉 | 复古金 |

主题随机切换，每次渲染自动应用。

## ⚙️ 配置参数

在插件类中可调整以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `min_length` | 60 | 触发自动转换的最小字符数 |
| `viewport_width` | 480 | 渲染视口宽度（px） |
| `device_scale_factor` | 2.0 | 设备像素比，2.0 即 2x 高清 |

## 📋 支持的 Markdown 语法

- `# 标题`（h1~h6）
- `**加粗**` / `*斜体*`
- `- 无序列表` / `1. 有序列表`
- `` `行内代码` `` / ` ```代码块``` `
- `> 引用`
- `| 表格 |`
- `~~删除线~~`
- `---` 分割线
- `![图片](url)`

## 🛠️ 技术栈

- **Playwright** - 无头 Chromium 浏览器渲染
- **Python-Markdown** - Markdown 解析
- **Pygments** - 代码语法高亮
- **AstrBot** - 插件运行平台

## 📄 许可证

MIT License
