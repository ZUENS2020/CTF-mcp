---
name: ctf-reverse
description: Reverse 题专项方法。用于可执行文件、字节码、混淆逻辑、校验器还原等任务，并要求在 CTF-mcp 项目中仅通过远端 Kali API 完成分析与求解。
---

# Reverse 解题（项目版）

## 执行约束

1. 静态/动态分析均在远端 Kali 进行。
2. 本地不运行反汇编、调试与还原脚本。
3. 结论要附带可复现脚本或最小验证步骤。

## 并发容器约定

1. 统一使用主技能已初始化的 `CONTAINER_NAME`（如 `ai-c-rev-001`）。
2. 所有 `/api/kali/exec`、`/api/kali/read` 请求必须显式携带 `container=$CONTAINER_NAME`。
3. 禁止在子技能中硬编码容器名。

## 工具准备（远端执行）

```bash
apt-get update && apt-get install -y file binutils gdb
python3 -m pip install --upgrade capstone
```

## 标准流程

1. 结构识别：文件格式、架构、入口、字符串、段信息。
2. 逻辑抽取：关键分支、校验路径、常量与状态机。
3. 约束建模：把校验逻辑转成可求解约束。
4. 自动还原：输出解码器、求解器或补丁脚本。
5. 结果验证：在远端复现并确认 flag 格式。

## 常见分支

1. 关键算法还原：CRC/哈希/位运算链。
2. 虚拟机题：指令集识别 -> 解释器重建。
3. 混淆题：还原控制流和数据流后再求解。

## 内置参考

1. `tools.md`
2. `patterns.md`
3. `anti-analysis.md`
4. `languages.md`
5. `field-notes.md`
