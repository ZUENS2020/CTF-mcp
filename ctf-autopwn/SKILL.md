---
name: ctf-autopwn-local-tools
description: 在本地题目环境中，先用本机命令完成文件传输和穿透，再在 Kali MCP 内完成全部解题执行。
---

# CTF AutoPwn (Local Tools First)

本 skill 用于以下场景：
- 题目文件在用户本机路径（例如 `/Users/.../chall.zip`）。
- 题目 URL 只能在本机访问（例如本地地址、内网地址、浏览器可开但 Kali 容器不可直连）。

## 强制约束

1. 传输与穿透必须使用本机命令，不使用 tmpfiles/bore 的 MCP 工具。
2. 解题执行必须在 Kali MCP 内完成（`shell_exec`）。
3. 不在宿主机直接跑利用链、爆破、逆向主流程。

## 两个本机工具（固定用法）

### A. 传输工具（tmpfiles）

上传：
```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

说明：返回 JSON 中 `data.url` 是展示页，下载时要改成直链：
- 展示页：`https://tmpfiles.org/<id>/<name>`
- 直链：`https://tmpfiles.org/dl/<id>/<name>`

### B. 穿透工具（bore）

```bash
bore local --to bore.pub <LOCAL_PORT>
```

说明：该命令在本机启动；拿到公网 `host:port` 后，给题目回连/外带使用。

## 标准工作流

1. 判断输入类型。
- 本地文件路径：先用 tmpfiles 上传，拿到直链。
- 本地 URL：先在本机下载成文件，再用 tmpfiles 上传，拿到直链。

2. 将题目送入 Kali。
- 在 Kali MCP 中用 `shell_exec` 执行下载，例如：
```bash
curl -fsSL '<TMPFILES_DL_URL>' -o /tmp/workspace/chall.bin
```

3. 在 Kali 内完成全部分析与利用。
- 仅使用 Kali MCP 的 `shell_exec` 执行：解压、checksec、调试、脚本利用、提交。

4. 需要回连/外带时。
- 在本机运行：
```bash
bore local --to bore.pub <LOCAL_PORT>
```
- 将返回的公网地址用于 payload（回连地址/外带地址）。
- Kali 内继续用 `shell_exec` 完成监听、触发和拿结果。

## AI 执行模板

当用户给出“本地文件或本地 URL”时，按此顺序输出并执行：

1. `本机传输步骤`：给出并执行 tmpfiles 上传命令。
2. `Kali 拉取步骤`：在 Kali 里下载到 `/tmp/workspace/`。
3. `Kali 解题步骤`：只在 Kali 里跑完整解题链。
4. `本机穿透步骤(如需要)`：给出并执行 `bore local --to bore.pub <port>`。

