# 📚 存储论文每日精读 (Storage Paper Daily)

> 每天一篇 FAST 会议论文，AI 辅助分析 + 分布式存储工程师的实践思考

## 🏗️ 项目架构

```
storage-paper-daily/
├── .github/workflows/
│   ├── daily_paper.yml     # 每日自动生成论文分析 (GitHub Actions)
│   └── deploy.yml          # 自动部署博客到 GitHub Pages
├── data/
│   └── fast_papers.json    # FAST 会议论文数据库
├── docs/
│   ├── index.md            # 博客首页
│   └── posts/              # 博客文章（自动生成 + 手动补充）
├── scripts/
│   ├── generate_daily.py   # 核心：每日论文 AI 分析生成
│   └── fetch_papers.py     # 工具：从 USENIX 抓取论文列表
├── mkdocs.yml              # MkDocs Material 博客配置
└── requirements.txt
```

## 🚀 快速开始

### 1. 配置环境

```bash
# 克隆仓库
git clone <your-repo-url>
cd storage-paper-daily

# 安装依赖
pip install -r requirements.txt

# 配置 GitHub Token（GitHub Copilot 订阅用户可直接使用 GitHub Models）
# 获取 PAT: https://github.com/settings/tokens → Generate new token (classic) → 无需勾选任何 scope
export GITHUB_TOKEN="ghp_your-token-here"

# (可选) 自定义模型，默认为 openai/gpt-4o
export API_MODEL="openai/gpt-4o"
```

### 2. 手动生成一篇论文分析

```bash
# 随机选一篇
python scripts/generate_daily.py

# 指定论文 ID
python scripts/generate_daily.py fast24-fifo-queues
```

### 3. 本地预览博客

```bash
mkdocs serve
# 打开 http://127.0.0.1:8000
```

### 4. 补充个人见解

生成的 Markdown 文件中有 `TODO` 标记，搜索并补充你的：
- 与 HDFS 的对比经验
- 与 CubeFS 的对比经验
- 生产环境可行性评估

### 5. 启用自动化

#### GitHub Secrets 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 | 必需 |
|--------|------|------|
| `GH_PAT` | GitHub Personal Access Token | ✅ |
| `API_MODEL` | 模型名称（默认 `openai/gpt-4o`） | ❌ |

> **获取 PAT**: [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)** → 无需勾选任何 scope，直接生成即可。只要你的账号有 Copilot 订阅就能访问 GitHub Models。

#### GitHub Pages 配置

1. 仓库 Settings → Pages → Source 选择 **GitHub Actions**
2. 确保 `.github/workflows/deploy.yml` 存在

### 6. 日常工作流

自动化配好后，你的日常工作变成：

1. ☀️ **早上** — 收到 GitHub PR 通知，AI 已选好论文并生成分析
2. 📖 **阅读** — Review PR 中的 AI 分析，同时翻阅原论文
3. ✍️ **补充** — 在 PR 中编辑，补充你的 HDFS/CubeFS 对比和实践思考
4. ✅ **发布** — Merge PR，博客自动部署更新

## 📋 管理论文库

### 添加新论文

手动编辑 `data/fast_papers.json`，或者用抓取工具：

```bash
# 抓取 FAST'24 论文列表
python scripts/fetch_papers.py 2024
```

### 论文数据格式

```json
{
  "id": "fast24-unique-slug",
  "title": "Paper Full Title",
  "conference": "FAST'24",
  "year": 2024,
  "authors": "Author1, Author2",
  "pdf_url": "https://...",
  "abstract": "Paper abstract...",
  "tags": ["distributed storage", "metadata"],
  "picked": false
}
```

> 💡 **提示**: `abstract` 字段如果填写了，AI 分析会更准确。可以从论文 PDF 中复制摘要填入。

## 🔧 自定义

### 修改 AI 分析模板

编辑 `scripts/generate_daily.py` 中的 `ANALYSIS_PROMPT_TEMPLATE`，调整分析结构。

### 修改博客样式

编辑 `mkdocs.yml` 自定义主题、导航等。参考 [MkDocs Material 文档](https://squidfunk.github.io/mkdocs-material/)。

### 更换模型

默认使用 [GitHub Models](https://github.com/marketplace/models) API（GitHub Copilot 订阅用户免费）。

可用模型包括：
- `openai/gpt-4o`（默认）
- `openai/gpt-4o-mini`（更快更便宜）
- `meta-llama/llama-3-70b-instruct`
- `mistralai/mistral-large`
- 更多模型见 [GitHub Models Marketplace](https://github.com/marketplace/models)

通过 `API_MODEL` 环境变量切换。也支持其他 OpenAI 兼容 API，设置 `API_BASE_URL` 即可。

## 📄 License

MIT
