---
name: kali-ctf
description: "CTF-mcp 项目的统一 Kali CTF 技能。用于任何 CTF 题目求解：将本地题目附件和题目 URL 作为输入，仅在本地执行 nginx 文件服务器上传与 frpc 穿透，所有侦察、分析、利用和取 flag 全程通过远端 Kali API 执行；并使用技能内置的 ctf-skills 参考库完成分类型解题。运行前先读取当前工作区的 setting.md。"
---

# Kali CTF（统一技能）

## 核心目标

将 `ctf-kali-api` 的远端执行规范与 `ctf-skills` 的分类解题方法合并为一个工作流，确保：

1. 本地只负责传输与隧道控制。
2. 远端 Kali 负责完整解题链路。
3. 解题方法按题型复用本技能内置 `ctf-skills` 资料。

## 配置来源（强制）

所有环境参数必须从以下文件读取，不在技能内硬编码：

- `./setting.md`（当前工作区）

字段定义：

1. `Api_Base`：远端 API 基础地址
2. `FRP_Address`：frps 地址
3. `FRP_token`：frp 认证 token
4. `File_Base`：附件下载基地址（例如 `http://14.1.99.251/files`）

## 强约束

1. 本地机器仅作为控制面，不在本地直接解题。
2. 仅允许本地执行：`nginx 文件服务器上传` 与 `frpc` 隧道命令。
3. 禁止本地执行 `checksec`、`gdb`、`pwntools`、`sqlmap`、`nmap`、exploit 脚本等解题动作。
4. 侦察、利用、提权、读 flag、证据收集全部在远端 Kali 完成。
5. 禁止检索该题公开题解、官方解答或现成 exploit 仓库。
6. 每条利用路径都必须记录尝试日志，不允许只保留成功路径。
7. 当单一路径连续失败时必须转向，不允许长时间死磕同一方法。

## 本机命令白名单与禁令（强制）

本机只允许两类命令：
1. `nginx` 文件服务器上传命令（如 `scp`/`rsync` 上传到 `/srv/ctf-files/`）
2. `frpc` 穿透命令（含生成/读取 frpc 配置）

除上述白名单外，其余本机命令一律视为违规，尤其禁止：
1. 本机漏洞利用与分析：`python exploit.py`、`pwntools`、`gdb`、`checksec`
2. 本机 Web 安全扫描：`sqlmap`、`ffuf`、`nmap`、`nikto`
3. 本机逆向/取证分析：`strings`、`binwalk`、`radare2`、`ghidra`、`volatility`
4. 本机直连题目服务进行解题交互（除上传与穿透验证外）

执行规则：
1. 任何解题动作必须改写为 `/api/kali/exec` 远端执行。
2. 如误在本机执行了解题命令，必须立即停止并在 `attempts.log` 记录“违规动作 + 回滚措施 + 后续改正路径”。

## 本地标准动作

### 1) 附件上传（nginx 文件服务器）

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing $SETTINGS_FILE"; exit 1; }
FRP_ADDRESS="$(awk -F': *' '/^FRP_Address:/{print $2}' "$SETTINGS_FILE")"
FILE_BASE="$(awk -F': *' '/^File_Base:/{print $2}' "$SETTINGS_FILE")"
[ -n "$FILE_BASE" ] || FILE_BASE="http://${FRP_ADDRESS}/files"
LOCAL_FILE="/ABS/PATH/TO/FILE"
FILE_NAME="$(basename "$LOCAL_FILE")"

scp "$LOCAL_FILE" "root@${FRP_ADDRESS}:/srv/ctf-files/${FILE_NAME}"
echo "${FILE_BASE%/}/${FILE_NAME}"
```

说明：
- 上传后下载地址统一为：`<File_Base>/<文件名>`
- 远端 Kali 直接用该 URL 下载到 `/tmp/workspace/current`

### 2) 穿透（frpc）

```bash
cat > /tmp/frpc-ctf.toml <<'EOF'
serverAddr = "<FRP_Address from setting.md>"
serverPort = 7000
transport.tcpMux = false
auth.method = "token"
auth.token = "<FRP_token from setting.md>"

[[proxies]]
name = "ctf-rev"
type = "tcp"
localIP = "127.0.0.1"
localPort = <LOCAL_PORT>
remotePort = <REMOTE_PORT>
EOF
frpc -c /tmp/frpc-ctf.toml
```

## 远端 API 约定

基础地址：读取 `setting.md` 的 `Api_Base`

并发约束：
- 不存在“active 容器”概念。
- 每次调用 `/api/kali/exec` 或 `/api/kali/read` 必须显式携带 `container` 字段。

多容器并发命名规范（必须遵守）：
1. 命名格式：`ai-<agent>-<cat>-<seq>`
2. 字段含义：
- `<agent>`：AI 实例代号（如 `a`、`b`、`c`）
- `<cat>`：题型代号（`web` / `pwn` / `rev` / `crypto` / `forensics` / `misc`）
- `<seq>`：三位递增编号（`001`、`002`...）
3. 示例：
- `ai-a-web-001`
- `ai-b-pwn-001`
- `ai-c-rev-002`
4. 冲突规避：
- 同一 AI 同一题目禁止复用旧容器名，必须递增 `seq`
- 新建容器前先 `GET /api/containers`，若同名已存在则递增编号重试

1. 容器生命周期
- `POST /api/containers`

2. 远端命令执行
- `POST /api/kali/exec`，参数：`{ "container": "<name>", "cmd": "...", "timeout": 30 }`

3. 远端文件读取
- `POST /api/kali/read`，参数：`{ "container": "<name>", "path": "relative/path" }`

4. 回调收件箱
- `GET /api/callbacks`

## 并发会话初始化模板（建议先执行）

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing $SETTINGS_FILE"; exit 1; }

API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' "$SETTINGS_FILE")"
AGENT_TAG="a"         # a/b/c...
CAT_TAG="web"         # web/pwn/rev/crypto/forensics/misc
SEQ="001"             # 三位编号,冲突时递增
CONTAINER_NAME="ai-${AGENT_TAG}-${CAT_TAG}-${SEQ}"
WORKDIR="/tmp/workspace/current"
```

## 执行前自检（每次开题前必须口头确认）

1. “接下来除 nginx 文件上传/frpc 外，本机不再执行任何解题命令。”
2. “所有侦察、分析、利用、取证、读 flag 统一走远端 Kali API。”
3. “若命令无法在远端执行，先修远端环境，不回退到本机解题。”

## 统一执行流程

1. `本地输入`：读取题目附件路径、题目 URL、端口信息。
2. `本地传输`：上传附件到 nginx 文件服务器并得到 `File_Base/文件名` 直链。
3. `远端落地`：通过 `/api/kali/exec` 在 Kali 下载到 `/tmp/workspace/current`。
4. `题型判定`：判断为 Web/Pwn/Reverse/Crypto/Forensics/Misc。
5. `远端解题`：仅通过 `/api/kali/exec` 执行完整分析与利用。
6. `按需穿透`：需要反连或端口映射时，在本地使用 frpc。
7. `结果回收`：通过 `/api/kali/read` 和 `/api/callbacks` 读取证据与 flag。

## 前置连通性检查（建议）

在正式解题前先做一次最小检查，避免把网络/容器问题误判为题目问题：

1. `GET /healthz` 应返回 `{"status":"ok"}`
2. `POST /api/containers` 创建目标容器（使用并发命名）
3. `POST /api/kali/exec` 执行 `id && pwd` 验证执行链路
4. 再开始附件下载与题型探测

## 尝试日志（必须执行）

每次尝试后都记录一条日志，至少包含：

1. `假设`：当前漏洞假设或利用路径。
2. `动作`：实际执行的命令/API 调用。
3. `结果`：关键输出、错误信息、是否推进。
4. `结论`：该路径是继续、暂挂还是放弃。
5. `下一步`：下一条待验证路径。

推荐保存到远端：

```bash
echo "[2026-04-18 10:00] 假设=JWT伪造 动作=... 结果=签名校验失败 结论=暂挂 下一步=测SSTI" >> /tmp/workspace/current/attempts.log
```

## 转向规则（防止死磕）

满足任一条件立即换方向：

1. 同一路径连续 3 次无有效新信息。
2. 连续 20 分钟只在修同一报错且无进展。
3. 当前方法依赖前提被证伪（如不可控输入、不可达端点）。
4. 题型判定出现更高置信度的新方向。

转向时必须先记录：

1. 为什么放弃当前路径。
2. 下一个路径的验证命令。

## 任务结束清理（建议）

为避免并发任务互相污染，结束时执行：

1. 保留 `attempts.log`、关键脚本、flag 证据到 `current/`
2. 导出必要结果后删除本次临时文件
3. 不再复用本次容器名；下次任务递增 `seq`

## 内置参考库说明

本技能已经内置 `ctf-skills` 到以下路径，不再依赖项目外目录：

- `references/ctf-skills/solve-challenge`
- `references/ctf-skills/ctf-web`
- `references/ctf-skills/ctf-pwn`
- `references/ctf-skills/ctf-reverse`
- `references/ctf-skills/ctf-crypto`
- `references/ctf-skills/ctf-forensics`
- `references/ctf-skills/ctf-misc`

先读取：
- `references/ctf-skills/solve-challenge/SKILL.md`
用于做首轮分流和路线选择。

## 题型方法映射（使用内置 ctf-skills）

当题型明确后，按需读取技能内对应资料：

1. `Web`
- 主入口：`references/ctf-skills/ctf-web/SKILL.md`
- 重点：注入、鉴权、SSTI、SSRF、上传链、业务逻辑链。

2. `Pwn`
- 主入口：`references/ctf-skills/ctf-pwn/SKILL.md`
- 重点：保护分析、原语构造、泄露-计算-利用三阶段。

3. `Reverse`
- 主入口：`references/ctf-skills/ctf-reverse/SKILL.md`
- 重点：伪代码还原、约束提取、自动化求解脚本。

4. `Crypto`
- 主入口：`references/ctf-skills/ctf-crypto/SKILL.md`
- 重点：识别误用模型，优先给出可复现 solver。

5. `Forensics`
- 主入口：`references/ctf-skills/ctf-forensics/SKILL.md`
- 重点：文件/流量/内存分层提取与交叉验证。

6. `Misc`
- 主入口：`references/ctf-skills/ctf-misc/SKILL.md`
- 重点：编码、沙箱、约束题与自动化脚本。

## API 调用模板

### 创建 Kali 容器

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing $SETTINGS_FILE"; exit 1; }
API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' "$SETTINGS_FILE")"
CONTAINER_NAME="ai-a-web-001"
curl -sS -X POST "$API_BASE/api/containers" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"$CONTAINER_NAME\",\"image\":\"ctf-kali:latest\"}"
```

### 在远端执行命令

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing $SETTINGS_FILE"; exit 1; }
API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' "$SETTINGS_FILE")"
CONTAINER_NAME="ai-a-web-001"
curl -sS -X POST "$API_BASE/api/kali/exec" \
  -H 'Content-Type: application/json' \
  -d "{\"container\":\"$CONTAINER_NAME\",\"cmd\":\"id && pwd\",\"timeout\":30}"
```

### 读取远端产物

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing $SETTINGS_FILE"; exit 1; }
API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' "$SETTINGS_FILE")"
CONTAINER_NAME="ai-a-web-001"
curl -sS -X POST "$API_BASE/api/kali/read" \
  -H 'Content-Type: application/json' \
  -d "{\"container\":\"$CONTAINER_NAME\",\"path\":\"current/output.txt\"}"
```
