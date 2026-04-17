#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================
# 工具名称: session_init.py - 初始化 CTF 挑战会话
# 使用方法: python3 session_init.py "challenge_name" [--category pwn|web|crypto|rev|forensics|misc]
# 说明:     在 /tmp/workspace/current 创建标准化的 CTF 工作目录结构
# 创建内容:
#   - session.md: 标题、类别、描述、产物列表、时间戳
#   - facts.md: 空模板
#   - hypotheses.md: 空模板
#   - attempts.md: 空模板
#   - artifacts/: 下载的文件
#   - tries/: 漏洞利用尝试
#   - notes/: 笔记
#   - tunnels.log: 空日志文件
# ===============================================================================

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# 颜色输出 (ANSI)
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def cprint(msg: str, color: str = NC):
    """打印带颜色的消息"""
    print(f"{color}{msg}{NC}")


def create_directory_structure(base_path: Path):
    """创建目录结构"""
    directories = ["artifacts", "tries", "notes"]
    created = []
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
    return created


def create_session_md(base_path: Path, challenge_name: str, category: str):
    """创建 session.md 主会话文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# CTF Challenge Session

## 基本信息

- **挑战名称**: {challenge_name}
- **类别**: {category}
- **创建时间**: {timestamp}
- **状态**: 🔵 进行中

---

## 挑战描述

<!-- 在此填写挑战描述 -->



## 产物列表 (Artifacts)

| 文件名 | 说明 | 来源 |
|--------|------|------|
|        |      |      |

---

## 部署信息

| 项目 | 值 |
|------|---|
| 靶机地址 | |
| 开放端口 | |
| Flag 格式 | |
| 提示信息 | |

---

## 环境变量

```bash

```

---

## 相关链接

- Challenge URL:
- Writeup 参考:
- 相关工具文档:

---

## 会话状态

- [ ] 信息收集完成
- [ ] 初步分析完成
- [ ] 漏洞点识别
- [ ] Exploit 开发
- [ ] Flag 获取
- [ ] 清理痕迹

---

*此文件由 session_init.py 自动生成*
"""

    file_path = base_path / "session.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return str(file_path)


def create_template_md(base_path: Path, filename: str, title: str):
    """创建模板 markdown 文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# {title}

<!-- 在此记录您的 {title.lower().replace("# ", "")} -->



---

*最后更新: {timestamp}*
"""

    file_path = base_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return str(file_path)


def create_empty_file(file_path: Path):
    """创建空文件"""
    file_path.touch()
    return str(file_path)


def main():
    parser = argparse.ArgumentParser(
        description="初始化 CTF 挑战会话",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 session_init.py babyheap --category pwn
  python3 session_init.py "SQL Injection" --category web
        """,
    )

    parser.add_argument("challenge_name", help="挑战名称")
    parser.add_argument(
        "--category",
        "-c",
        choices=["pwn", "web", "crypto", "rev", "forensics", "misc"],
        default="misc",
        help="挑战类别 (默认: misc)",
    )

    args = parser.parse_args()

    challenge_name = args.challenge_name.strip()
    category = args.category

    # 工作目录路径
    workspace_path = Path("/tmp/workspace/current")

    # 检查工作目录是否存在
    if workspace_path.exists() and any(workspace_path.iterdir()):
        cprint(f"警告: 工作目录 {workspace_path} 已存在且非空", YELLOW)
        response = input("是否继续? 这可能会覆盖现有文件 (y/N): ").strip().lower()
        if response != "y":
            cprint("操作已取消", RED)
            sys.exit(0)

    # 创建目录结构
    try:
        cprint(f"创建目录结构...", BLUE)
        directories = create_directory_structure(workspace_path)
        for d in directories:
            cprint(f"  ✓ 创建: {d}", GREEN)

        # 创建 session.md
        cprint(f"\n创建主会话文件...", BLUE)
        session_md = create_session_md(workspace_path, challenge_name, category)
        cprint(f"  ✓ 创建: {session_md}", GREEN)

        # 创建模板文件
        cprint(f"\n创建模板文件...", BLUE)
        templates = [
            ("facts.md", "已知事实 (Facts)"),
            ("hypotheses.md", "假设与推测 (Hypotheses)"),
            ("attempts.md", "尝试记录 (Attempts)"),
        ]
        for filename, title in templates:
            file_path = create_template_md(workspace_path, filename, title)
            cprint(f"  ✓ 创建: {file_path}", GREEN)

        # 创建 tunnels.log
        cprint(f"\n创建日志文件...", BLUE)
        tunnels_log = create_empty_file(workspace_path / "tunnels.log")
        cprint(f"  ✓ 创建: {tunnels_log}", GREEN)

        # 输出摘要
        cprint(f"\n{'=' * 50}", GREEN)
        cprint(f"会话初始化完成!", GREEN)
        cprint(f"{'=' * 50}", GREEN)
        cprint(f"\n挑战: {challenge_name}", BLUE)
        cprint(f"类别: {category}", BLUE)
        cprint(f"工作目录: {workspace_path}", BLUE)
        cprint(f"\n创建的文件:", BLUE)
        print(f"  - session.md (主会话文件)")
        print(f"  - facts.md (已知事实)")
        print(f"  - hypotheses.md (假设推测)")
        print(f"  - attempts.md (尝试记录)")
        print(f"  - tunnels.log (隧道日志)")
        print(f"\n创建的目录:", BLUE)
        for d in directories:
            print(f"  - {d}/")

        cprint(f"\n下一步操作:", YELLOW)
        print(f"  1. 编辑 session.md 填写挑战描述")
        print(f"  2. 使用 bore_open.sh 打开隧道(如需要)")
        print(f"  3. 使用 attempt_add.py 记录每次尝试")

    except Exception as e:
        cprint(f"错误: 创建会话失败 - {e}", RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
