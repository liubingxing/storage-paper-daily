#!/usr/bin/env python3
"""
论文抓取工具 — 从 USENIX FAST 官网抓取论文列表，补充到 papers 数据库中。
用法: python scripts/fetch_papers.py [year]
例如: python scripts/fetch_papers.py 2024
"""

import json
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PAPERS_FILE = ROOT / "data" / "fast_papers.json"

# USENIX FAST 论文列表页面 URL 模板
FAST_URL_TEMPLATE = "https://www.usenix.org/conference/fast{year_short}/technical-sessions"


def load_existing_papers() -> list[dict]:
    if PAPERS_FILE.exists():
        with open(PAPERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_papers(papers: list[dict]):
    PAPERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)


def fetch_fast_page(year: int) -> str:
    """获取 FAST 会议页面 HTML"""
    year_short = str(year)[2:]  # 2024 -> 24
    url = FAST_URL_TEMPLATE.format(year_short=year_short)
    print(f"正在获取: {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_papers_from_html(html: str, year: int) -> list[dict]:
    """
    从 USENIX 页面 HTML 中提取论文信息。
    这是一个简单的正则解析，可能需要根据页面结构调整。
    """
    papers = []
    # USENIX 页面通常用 <h2 class="node-title"> 或类似结构
    # 这里用一个宽泛的模式匹配论文标题
    pattern = r'<h[23][^>]*class="[^"]*title[^"]*"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)

    year_short = str(year)[2:]
    for href, title in matches:
        title = title.strip()
        if not title or len(title) < 10:
            continue

        paper_id = f"fast{year_short}-{re.sub(r'[^a-z0-9]+', '-', title.lower())[:50].strip('-')}"
        pdf_url = ""
        if href.startswith("/"):
            pdf_url = f"https://www.usenix.org{href}"

        papers.append({
            "id": paper_id,
            "title": title,
            "conference": f"FAST'{year_short}",
            "year": year,
            "authors": "",
            "pdf_url": pdf_url,
            "abstract": "",
            "tags": [],
            "picked": False,
        })

    return papers


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fetch_papers.py <year>")
        print("例如: python scripts/fetch_papers.py 2024")
        sys.exit(1)

    year = int(sys.argv[1])
    existing = load_existing_papers()
    existing_ids = {p["id"] for p in existing}

    try:
        html = fetch_fast_page(year)
        new_papers = parse_papers_from_html(html, year)
    except Exception as e:
        print(f"抓取失败: {e}", file=sys.stderr)
        print("提示: 你也可以手动编辑 data/fast_papers.json 添加论文")
        sys.exit(1)

    added = 0
    for paper in new_papers:
        if paper["id"] not in existing_ids:
            existing.append(paper)
            existing_ids.add(paper["id"])
            added += 1
            print(f"  + {paper['title']}")

    save_papers(existing)
    print(f"\n完成! 新增 {added} 篇论文，总计 {len(existing)} 篇。")


if __name__ == "__main__":
    main()
