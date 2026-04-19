---
name: ctf-forensics
description: Forensics 题专项方法。用于磁盘、内存、流量、日志、隐写取证等任务，并要求在 CTF-mcp 项目中仅通过远端 Kali API 完成分析、提取和验证。
---

# Forensics 解题（项目版）

## 执行约束

1. 提取、解包、解析、恢复全部在远端 Kali 执行。
2. 本地不直接运行取证工具链。
3. 每个关键结论保留证据文件路径与命令记录。

## 并发容器约定

1. 统一使用主技能已初始化的 `CONTAINER_NAME`（如 `ai-c-forensics-001`）。
2. 所有 `/api/kali/exec`、`/api/kali/read` 请求必须显式携带 `container=$CONTAINER_NAME`。
3. 禁止在子技能中硬编码容器名。

## 本机禁令（强制）

1. 本机仅允许执行 `nginx 文件服务器上传` 与 `frpc` 穿透，不允许任何取证分析命令。
2. 本机禁止执行 `binwalk`、`strings`、`exiftool`、`scapy`、本地提取脚本。
3. 所有提取、解析、恢复动作必须通过远端 `/api/kali/exec` 执行。

## 工具准备（远端执行）

```bash
apt-get update && apt-get install -y binwalk exiftool foremost strings
python3 -m pip install --upgrade scapy
```

## 标准流程

1. 识别介质：文件系统、镜像、流量、日志、多媒体。
2. 批量提取：元数据、可疑片段、隐藏内容。
3. 关联验证：时间线、来源、编码层、完整性。
4. 结果固化：输出可复现提取脚本与证据路径。

## 常见分支

1. 流量题：会话重组 -> 协议字段提取 -> 明文恢复。
2. 磁盘题：分区识别 -> 文件恢复 -> 关键路径定位。
3. 隐写题：元数据异常 -> 信道假设 -> payload 解码。
4. 内存题：进程与字符串关联 -> 凭据/flag 抽取。

## 内置参考

1. `disk-and-memory.md`
2. `network.md`
3. `steganography.md`
4. `linux-forensics.md`
5. `windows.md`
