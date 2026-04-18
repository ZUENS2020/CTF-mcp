---
name: ctf-pwn
description: Pwn 题专项方法。用于栈溢出、格式化字符串、堆利用、ROP、沙箱绕过等内存破坏类题目，并要求在 CTF-mcp 项目中仅通过远端 Kali API 执行分析和利用。
---

# Pwn 解题（项目版）

## 执行约束

1. 二进制分析、调试、exp 运行全部在远端 Kali。
2. 本地只做附件上传与端口穿透，不执行 pwn 工具链。
3. 所有脚本通过 `/api/kali/exec`（带 `container`）执行并回收输出。

## 并发容器约定

1. 统一使用主技能已初始化的 `CONTAINER_NAME`（如 `ai-b-pwn-001`）。
2. 所有 `/api/kali/exec`、`/api/kali/read` 请求必须显式携带 `container=$CONTAINER_NAME`。
3. 禁止在子技能中硬编码容器名。

## 本机禁令（强制）

1. 本机仅允许执行 `tmpfiles` 上传与 `frpc` 穿透，不允许任何 Pwn 解题命令。
2. 本机禁止执行 `gdb`、`checksec`、`pwntools`、`ropper`、本地 exp。
3. 所有分析、调试、利用动作必须通过远端 `/api/kali/exec` 执行。

## 工具准备（远端执行）

```bash
apt-get update && apt-get install -y gdb binutils
python3 -m pip install --upgrade pwntools ropper
```

## 标准流程

1. 保护分析：`file`、`checksec`、架构与 libc 关系。
2. 原语识别：任意读/写、栈控制、格式化写、UAF。
3. 泄露阶段：地址泄露与基址计算。
4. 利用阶段：ROP/ret2libc/hook/堆链构造。
5. 稳定化：重试机制、超时与交互同步。

## 远端命令样式

```bash
checksec --file /tmp/workspace/current/chall
python3 /tmp/workspace/current/exp.py
```

## 常见分支

1. 栈溢出：偏移 -> 控制 RIP -> 构造调用链。
2. 格式化字符串：偏移确认 -> 泄露 -> 定点写入。
3. 堆利用：分配器版本识别 -> chunk 布局 -> 原语升级。
4. 沙箱限制：syscall 面分析 -> 替代链或旁路。

## 内置参考

1. `overflow-basics.md`
2. `rop-and-shellcode.md`
3. `format-string.md`
4. `heap-techniques.md`
5. `sandbox-escape.md`
