---
name: ctf-misc
description: Misc 题专项方法。用于 jail、编码、脚本陷阱、协议小游戏、杂项自动化等任务，并要求在 CTF-mcp 项目中仅通过远端 Kali API 执行求解流程。
---

# Misc 解题（项目版）

## 执行约束

1. 所有脚本与交互在远端 Kali 执行。
2. 本地仅负责上传附件与 frpc 穿透。
3. 优先最短可复现链路，避免过度复杂化。

## 并发容器约定

1. 统一使用主技能已初始化的 `CONTAINER_NAME`（如 `ai-c-misc-001`）。
2. 所有 `/api/kali/exec`、`/api/kali/read` 请求必须显式携带 `container=$CONTAINER_NAME`。
3. 禁止在子技能中硬编码容器名。

## 本机禁令（强制）

1. 本机仅允许执行 `nginx 文件服务器上传` 与 `frpc` 穿透，不允许任何 Misc 解题命令。
2. 本机禁止执行本地 jail 逃逸脚本、交互脚本、协议自动化脚本。
3. 所有验证与求解动作必须通过远端 `/api/kali/exec` 执行。

## 工具准备（远端执行）

```bash
apt-get update && apt-get install -y jq socat netcat-openbsd
python3 -m pip install --upgrade pwntools
```

## 标准流程

1. 问题建模：识别是编码、约束、交互协议还是 jail。
2. 快速验证：最小输入输出回放，确认可控点。
3. 自动化：把手工步骤脚本化并支持重试。
4. 收敛：输出唯一有效结果与复现步骤。

## 常见分支

1. 编码链：分层识别并逐层解码。
2. Jail：限制分析 -> 可用原语 -> 逃逸 payload。
3. 交互题：状态机建模 -> 会话脚本。
4. 杂项协议：抓包/重放/边界测试。

## 内置参考

1. `encodings.md`
2. `pyjails.md`
3. `bashjails.md`
4. `ctfd-navigation.md`
5. `games-and-vms.md`
