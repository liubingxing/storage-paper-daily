#!/usr/bin/env python3
"""
每日论文挑选与AI分析脚本
从 FAST 会议论文列表中挑选一篇，调用 GitHub Models API 生成总结与分析，
输出 Markdown 格式的博客草稿。

GitHub Copilot 订阅用户可直接使用 GitHub Models API。
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

from openai import OpenAI

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
PAPERS_FILE = ROOT / "data" / "fast_papers.json"
POSTS_DIR = ROOT / "docs" / "posts"

SYSTEM_PROMPT = """你是一位资深的分布式存储系统专家。
你的任务是对存储领域的学术论文进行深度、详尽的技术分析，面向有一定存储系统经验的工程师。

要求：
- 用中文输出，关键技术术语保留英文
- 分析要非常详细和深入，不要泛泛而谈
- 对于核心设计部分，需要详细解释每个技术点的原理、实现方式和设计权衡
- 内容丰富度相当于一篇 3000-5000 字的技术博客"""

ANALYSIS_PROMPT_TEMPLATE = """请对以下 FAST 会议论文进行深度分析：

论文标题: {title}
会议: {conference}
标签: {tags}
{abstract_section}

请按以下结构输出分析（Markdown 格式），每个部分都要详细展开：

## 论文基本信息

简要介绍论文的 conference、年份、研究方向。

## 研究背景与动机

- 这篇论文要解决什么问题？问题的具体表现是什么？
- 为什么这个问题重要？对实际系统有什么影响？
- 现有方案有哪些？各自有什么不足？请逐一分析
- 论文的核心 insight 是什么？

## 架构设计图

用 Mermaid 语法画出论文的核心架构图，要求：
- 使用 flowchart 或 graph 类型
- 展示系统的主要组件和数据流
- 用中文标注组件名，关键英文术语保留
- 用 subgraph 对组件进行分组，层次清晰
- 节点使用圆角矩形、圆柱形等多种形状区分不同类型的组件
- 连接线用不同样式（实线、虚线、粗线）区分数据流和控制流
- 如有必要，再画一个流程图展示关键操作流程（对比传统方案 vs 论文方案）

## 核心设计与技术贡献

**请非常详细地展开这一部分**，对每个关键技术点都要说清楚：

### 整体架构
- 系统由哪些核心组件构成？各组件的职责是什么？
- 组件之间如何交互？数据流和控制流是怎样的？

### 关键技术点（逐一详解）
对论文中的每个关键技术设计，都需要详细说明：
1. **要解决的子问题**：这个技术点针对什么具体挑战？
2. **设计方案**：具体怎么做的？算法或机制是什么？
3. **设计权衡（trade-off）**：为什么选择这种方案？放弃了什么？获得了什么？
4. **与现有技术的区别**：和之前的做法有什么本质区别？

### 创新点总结
- 论文最核心的创新是什么？
- 为什么这种设计之前没人做？

## 实验评估亮点

- 实验环境和基准（benchmarks）是什么？
- 对比了哪些 baseline 系统？
- 关键的性能数据（具体数字和提升比例）
- 实验结论说明了什么问题？

## 与工业界的关联

- 这篇论文的思路在工业界有哪些类似实践？
- 这些思路是否可以借鉴到生产系统中？
- 落地可能面临哪些工程挑战？

## 个人思考启发

- 这篇论文最值得学习的点是什么？
- 有哪些潜在的局限性或可改进之处？
- 对存储系统从业者有什么启示？
"""


def load_papers() -> list[dict]:
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_papers(papers: list[dict]):
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)


def pick_paper(papers: list[dict]) -> dict | None:
    """从未选过的论文中随机挑一篇"""
    unpicked = [p for p in papers if not p.get("picked", False)]
    if not unpicked:
        # 全部选过了，重置
        for p in papers:
            p["picked"] = False
        unpicked = papers
    return random.choice(unpicked) if unpicked else None


def generate_analysis(paper: dict) -> str:
    """调用 GitHub Models API 生成论文分析"""
    api_key = os.environ.get("GITHUB_TOKEN")
    if not api_key:
        print("错误: 请设置 GITHUB_TOKEN 环境变量", file=sys.stderr)
        print("获取方式: https://github.com/settings/tokens → Generate new token (classic)", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get("API_BASE_URL") or "https://models.inference.ai.azure.com"
    model = os.environ.get("API_MODEL") or "gpt-4o"

    client = OpenAI(api_key=api_key, base_url=base_url)

    abstract_section = ""
    if paper.get("abstract"):
        abstract_section = f"摘要: {paper['abstract']}"

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        title=paper["title"],
        conference=paper["conference"],
        tags=", ".join(paper.get("tags", [])),
        abstract_section=abstract_section,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=8000,
    )

    return response.choices[0].message.content


def generate_post(paper: dict, analysis: str) -> str:
    """生成博客 Markdown 文件内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    tags_str = "\n".join(f"  - {tag}" for tag in paper.get("tags", []))

    post = f"""---
date: {today}
categories:
  - 论文精读
  - {paper['conference']}
tags:
{tags_str}
---

# 【论文精读】{paper['title']}

> **会议**: {paper['conference']} | **日期**: {today}
> **标签**: {', '.join(paper.get('tags', []))}

{analysis}
"""
    return post


def main():
    papers = load_papers()

    # 支持通过命令行参数指定论文 ID
    if len(sys.argv) > 1:
        paper_id = sys.argv[1]
        paper = next((p for p in papers if p["id"] == paper_id), None)
        if not paper:
            print(f"错误: 找不到论文 ID '{paper_id}'", file=sys.stderr)
            sys.exit(1)
    else:
        paper = pick_paper(papers)

    if not paper:
        print("没有可选的论文了！", file=sys.stderr)
        sys.exit(1)

    print(f"📄 今日论文: {paper['title']}")
    print(f"📂 会议: {paper['conference']}")
    print(f"🏷️  标签: {', '.join(paper.get('tags', []))}")
    print()

    print("🤖 正在调用 AI 生成分析...")
    analysis = generate_analysis(paper)
    print("✅ 分析生成完成！")

    # 生成文件名
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = paper["id"].replace("/", "-")
    filename = f"{today}-{safe_title}.md"

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_path = POSTS_DIR / filename
    post_content = generate_post(paper, analysis)

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(post_content)

    # 标记已选
    paper["picked"] = True
    paper["picked_date"] = today
    save_papers(papers)

    # 输出论文信息供 CI 使用
    metadata_path = ROOT / "paper_metadata.txt"
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(f"PAPER_TITLE={paper['title']}\n")
        f.write(f"PAPER_CONF={paper['conference']}\n")
        f.write(f"PAPER_TAGS={', '.join(paper.get('tags', []))}\n")

    print(f"📝 博客草稿已生成: {post_path}")
    return str(post_path)


if __name__ == "__main__":
    main()
