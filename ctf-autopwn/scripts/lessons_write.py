#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================
# 工具名称: lessons_write.py - 在 LESSONS.md 追加经验条目
# 使用方法: python3 lessons_write.py --category <pwn|web|crypto|rev|forensics|misc> --signal "<text>" --technique "<text>" --pitfall "<text>" --title "<optional_title>"
# 说明:     在宿主机构建并追加经验条目到 LESSONS.md
#           LESSONS.md 位于 ~/.claude/skills/ctf-autopwn/LESSONS.md 或项目目录
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
NC = "\033[0m"

# LESSONS.md 可能的路径
LESSONS_PATHS = [
    Path("~/.claude/skills/ctf-autopwn/LESSONS.md").expanduser(),
    Path("/Users/zuens2020/Documents/CTF-mcp/ctf-autopwn/references/LESSONS.md"),
    Path("./LESSONS.md"),
]


def cprint(msg: str, color: str = NC):
    """打印带颜色的消息"""
    print(f"{color}{msg}{NC}")


def find_lessons_file() -> Path:
    """查找 LESSONS.md 文件"""
    for path in LESSONS_PATHS:
        expanded = path.expanduser()
        if expanded.exists():
            return expanded

    # 如果都不存在,使用第一个路径
    default_path = LESSONS_PATHS[0].expanduser()
    return default_path


def create_lessons_template(file_path: Path):
    """创建 LESSONS.md 模板(如果不存在)"""
    if file_path.exists():
        return False  # 文件已存在

    template = """# CTF 经验池 (Lessons Learned)

<!--
本文件用于记录 CTF 比赛和练习中获得的经验和技巧。
每个条目应包含: 类别、信号/触发点、使用的技术、踩过的坑。

格式:
## [类别] 经验标题
- **信号/触发点**: 什么情况下会用到
- **技术/方法**: 使用的技术或方法
- **踩坑记录**: 遇到的问题和解决方案
- **相关题目**: 相关的 CTF 题目
- **参考资料**: 相关的文档或链接
-->

---

*最后更新: """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template += timestamp + "*\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)

    return True  # 新创建


def parse_category(category: str) -> tuple:
    """解析类别,返回中文和英文"""
    category_map = {
        "pwn": ("Pwn", "二进制漏洞利用"),
        "web": ("Web", "Web 安全"),
        "crypto": ("Crypto", "密码学"),
        "rev": ("Rev", "逆向工程"),
        "forensics": ("Forensics", "数字取证"),
        "misc": ("Misc", "杂项"),
    }

    if category.lower() in category_map:
        en, zh = category_map[category.lower()]
        return en, zh
    else:
        return category, category


def escape_brackets(text: str) -> str:
    """转义中括号"""
    return text.replace("[", "\\[").replace("]", "\\]")


def main():
    parser = argparse.ArgumentParser(
        description="在 LESSONS.md 追加经验条目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 lessons_write.py -c pwn -s "格式化字符串泄露" -t "利用 %%x %%s 泄露信息" -p "忘记 %%n 写入长度"
  python3 lessons_write.py --category web --signal "SQL注入万能钥匙" --technique "OR 1=1 --" --pitfall "需要注释后续SQL"
  python3 lessons_write.py -c misc -s "流量包分析" -t "用 strings grep 关键字" -p "Unicode 编码" --title "流量分析技巧"

参数说明:
  --category  类别: pwn|web|crypto|rev|forensics|misc
  --signal    信号/触发点: 在什么情况下会用到这个技术
  --technique 技术/方法: 具体使用的技术
  --pitfall   踩坑记录: 遇到的问题和解决方案
  --title     经验标题 (可选,默认使用技术关键词)
        """,
    )

    parser.add_argument(
        "-c",
        "--category",
        required=True,
        choices=["pwn", "web", "crypto", "rev", "forensics", "misc"],
        help="经验类别",
    )

    parser.add_argument(
        "-s", "--signal", required=True, help="信号/触发点 (什么情况下会用到)"
    )

    parser.add_argument(
        "-t", "--technique", required=True, help="技术/方法 (具体使用的技术)"
    )

    parser.add_argument(
        "-p", "--pitfall", required=True, help="踩坑记录 (遇到的问题和解决方案)"
    )

    parser.add_argument("-T", "--title", default=None, help="经验标题 (可选)")

    parser.add_argument(
        "-f", "--file", default=None, help="LESSONS.md 文件路径 (可选,默认自动查找)"
    )

    args = parser.parse_args()

    # 查找或创建 LESSONS.md
    if args.file:
        lessons_path = Path(args.file).expanduser()
    else:
        lessons_path = find_lessons_file()

    # 确保目录存在
    lessons_path.parent.mkdir(parents=True, exist_ok=True)

    # 如果文件不存在,创建模板
    is_new = create_lessons_template(lessons_path)
    if is_new:
        cprint(f"✓ 创建新 LESSONS.md: {lessons_path}", GREEN)

    # 解析类别
    cat_en, cat_zh = parse_category(args.category)

    # 生成标题
    if args.title:
        title = args.title.strip()
    else:
        # 从 technique 提取前几个词作为标题
        technique_words = args.technique.strip().split()[:3]
        title = "".join(technique_words)
        if len(args.technique.strip().split()) > 3:
            title += "..."

    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 转义内容中的特殊字符
    signal_escaped = escape_brackets(args.signal.strip())
    technique_escaped = escape_brackets(args.technique.strip())
    pitfall_escaped = escape_brackets(args.pitfall.strip())
    title_escaped = escape_brackets(title)

    # 构造条目
    entry = f"""
## [{cat_zh}] {title_escaped}

- **类别**: {cat_en} ({cat_zh})
- **信号/触发点**: {signal_escaped}
- **技术/方法**: {technique_escaped}
- **踩坑记录**: {pitfall_escaped}
- **相关题目**: 
- **参考资料**: 
- **记录时间**: {timestamp}

---
"""

    # 追加到文件
    # 在最后一个 "---" 之前插入新条目
    try:
        with open(lessons_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找最后一个 ---
        last_separator = content.rfind("---")
        if last_separator != -1:
            # 在最后一个 --- 之前插入(保留最后的 timestamp 行)
            before = content[:last_separator].rstrip()
            after = content[last_separator:].lstrip()

            # 更新 timestamp
            after_lines = after.split("\n", 1)
            if after_lines[0] == "---":
                after = f"---\n*最后更新: {timestamp}*\n"

            new_content = before + "\n\n" + entry.strip() + "\n\n" + after
        else:
            # 没有找到分隔符,直接追加
            new_content = content + "\n" + entry

        with open(lessons_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        cprint(f"✓ 经验已追加到 LESSONS.md", GREEN)
        print(f"\n文件: {lessons_path}")
        print(f"类别: {cat_en} ({cat_zh})")
        print(f"标题: {title}")
        print(f"时间: {timestamp}")
        print(f"\n提示: 使用 grep 搜索经验: grep -i '关键字' {lessons_path}")

    except Exception as e:
        cprint(f"错误: 写入文件失败 - {e}", RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
