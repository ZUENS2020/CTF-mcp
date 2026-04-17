#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================
# 工具名称: attempt_add.py - 记录一次尝试到 attempts.md
# 使用方法: python3 attempt_add.py --hypothesis <H#> --command "<cmd>" --result "<output>" --conclusion "<✅|❌|🔶> <notes>"
# 说明:     将尝试追加到 /tmp/workspace/current/attempts.md
# 格式:
#   ## Attempt @ YYYY-MM-DD HH:MM:SS
#   - Hypothesis: H#
#   - Command: <cmd>
#   - Result: <key output>
#   - Conclusion: ✅/❌/🔶 <what was learned>
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


def cprint(msg: str, color: str = NC):
    """打印带颜色的消息"""
    print(f"{color}{msg}{NC}")


def validate_conclusion(conclusion: str) -> bool:
    """验证 conclusion 格式是否正确"""
    # 必须以 ✅ ❌ 🔶 之一开头
    valid_prefixes = ["✅", "❌", "🔶"]
    return any(conclusion.strip().startswith(prefix) for prefix in valid_prefixes)


def format_conclusion(conclusion: str) -> str:
    """格式化 conclusion 确保有 emoji"""
    conclusion = conclusion.strip()

    # 如果没有 emoji 前缀,自动添加
    if not any(
        conclusion.startswith(prefix) for prefix in ["✅", "❌", "🔶", "✔️", "✖️", "⚠️"]
    ):
        # 默认使用问号
        conclusion = f"🔶 {conclusion}"

    return conclusion


def escape_markdown(text: str) -> str:
    """转义 Markdown 特殊字符"""
    # 需要转义的字符
    escape_chars = ["|", "\\", "`", "*", "_", "#", "+", "-", ".", "!"]
    result = text
    for char in escape_chars:
        result = result.replace(char, f"\\{char}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="记录 CTF 尝试到 attempts.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 attempt_add.py -H H1 -c "python3 exploit.py" -r "Got flag!" -C "✅ 成功!"
  python3 attempt_add.py --hypothesis H2 --command "nc target 4444" --result "Connection refused" --conclusion "❌ 服务未开"
  python3 attempt_add.py -H H1 -c "strings binary" -r "password: admin" -C "🔶 发现密码"

结论格式:
  ✅ 或 ✔️ - 成功,得到了预期结果
  ❌ 或 ✖️ - 失败,操作未成功
  🔶 或 ⚠️ - 部分成功或有新发现
        """,
    )

    parser.add_argument(
        "-H", "--hypothesis", required=True, help="假设编号 (如 H1, H2, H3)"
    )

    parser.add_argument("-c", "--command", required=True, help="执行的命令")

    parser.add_argument("-r", "--result", required=True, help="命令输出/结果")

    parser.add_argument(
        "-C", "--conclusion", required=True, help="结论 (格式: <✅|❌|🔶> <说明>)"
    )

    parser.add_argument(
        "--file",
        default="/tmp/workspace/current/attempts.md",
        help="attempts.md 文件路径 (默认: /tmp/workspace/current/attempts.md)",
    )

    args = parser.parse_args()

    hypothesis = args.hypothesis.strip()
    command = args.command.strip()
    result = args.result.strip()
    conclusion = format_conclusion(args.conclusion.strip())
    file_path = Path(args.file)

    # 验证结论格式
    if not validate_conclusion(conclusion):
        cprint(f"警告: 结论应以 ✅ ❌ 🔶 之一开头", YELLOW)

    # 检查文件是否存在
    if not file_path.exists():
        cprint(f"错误: 文件不存在 - {file_path}", RED)
        cprint("请先运行 session_init.py 初始化会话", YELLOW)
        sys.exit(1)

    # 获取时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构造 Markdown 条目
    # 转义特殊字符
    command_escaped = escape_markdown(command)
    result_escaped = escape_markdown(result)
    conclusion_escaped = escape_markdown(conclusion)

    entry = f"""## Attempt @ {timestamp}

- **Hypothesis**: {hypothesis}
- **Command**: `{command_escaped}`
- **Result**: {result_escaped}
- **Conclusion**: {conclusion_escaped}

---

"""

    # 追加到文件
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry)

        cprint(f"✓ 尝试已记录", GREEN)
        print(f"\n文件: {file_path}")
        print(f"时间: {timestamp}")
        print(f"假设: {hypothesis}")
        print(f"命令: {command[:60]}{'...' if len(command) > 60 else ''}")
        print(f"结论: {conclusion}")

    except Exception as e:
        cprint(f"错误: 写入文件失败 - {e}", RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
