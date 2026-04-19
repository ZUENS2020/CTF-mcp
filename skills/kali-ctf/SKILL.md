---
name: kali-ctf
description: "CTF-mcp 项目的统一 Kali CTF 技能。用于任何 CTF 题目求解：将本地题目附件和题目 URL 作为输入，仅在本地执行 nginx 文件服务器上传与 frpc 穿透，所有侦察、分析、利用和取 flag 全程通过远端 Kali API 执行。运行前先读取当前工作区的 setting.md。"
---

# Kali CTF（统一技能）

## 核心目标

确保：

1. 本地只负责传输与隧道控制。
2. 远端 Kali 负责完整解题链路。
3. 解题方法按题型复用技能 `ctf-skills` 。

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
BASE_NAME="$(basename "$LOCAL_FILE")"
FILE_NAME="$(date +%s)-$RANDOM-${BASE_NAME}"

scp "$LOCAL_FILE" "root@${FRP_ADDRESS}:/srv/ctf-files/${FILE_NAME}"
echo "${FILE_BASE%/}/${FILE_NAME}"
```

说明：
- 上传后下载地址统一为：`<File_Base>/<文件名>`
- 远端 Kali 直接用该 URL 下载到 `/tmp/workspace/current`

上传后清理（强制）：
1. 远端 Kali 下载成功并校验后，立即删除文件服务器源文件。
2. 删除命令（本地控制面允许）：

```bash
ssh "root@${FRP_ADDRESS}" "rm -f /srv/ctf-files/${FILE_NAME}"
```

3. 如删除失败，必须记录到 `attempts.log` 并在任务结束前重试删除。

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

## 强制自检环节（开题前必须通过）

未通过任一项时，禁止进入“统一执行流程”。

### A. 配置自检（本地）

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing setting.md"; exit 1; }
for k in Api_Base FRP_Address FRP_token File_Base; do
  v="$(awk -F': *' -v key="$k" '$1==key {print $2}' "$SETTINGS_FILE")"
  [ -n "$v" ] || { echo "missing $k in setting.md"; exit 1; }
done
echo "settings ok"
```

### B. 连通性自检（本地控制面）

```bash
API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' setting.md)"
FILE_BASE="$(awk -F': *' '/^File_Base:/{print $2}' setting.md)"
curl -fsS "${API_BASE%/}/healthz" >/dev/null || { echo "api healthz failed"; exit 1; }
curl -fsS "${FILE_BASE%/}/../healthz_files" >/dev/null || { echo "file server health failed"; exit 1; }
echo "control-plane ok"
```

### C. 远端执行链路自检（Kali API）

```bash
API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' setting.md)"
CONTAINER_NAME="ai-a-web-001"
curl -sS -X POST "${API_BASE%/}/api/containers" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"$CONTAINER_NAME\",\"image\":\"ctf-kali:latest\"}" >/dev/null

curl -sS -X POST "${API_BASE%/}/api/kali/exec" \
  -H 'Content-Type: application/json' \
  -d "{\"container\":\"$CONTAINER_NAME\",\"cmd\":\"id && pwd\",\"timeout\":30}"
```

通过标准：
1. `healthz` 正常；
2. 文件服务健康检查正常；
3. 远端 `id && pwd` 返回非错误结果。

## 统一执行流程

1. `本地输入`：读取题目附件路径、题目 URL、端口信息。
2. `强制自检`：执行并通过“强制自检环节”。
3. `本地传输`：上传附件到 nginx 文件服务器并得到 `File_Base/文件名` 直链。
4. `远端落地`：通过 `/api/kali/exec` 在 Kali 下载到 `/tmp/workspace/current` 并校验。
5. `源文件清理`：下载校验成功后，立即删除 `/srv/ctf-files/<文件名>`。
6. `题型判定`：判断为 Web/Pwn/Reverse/Crypto/Forensics/Misc。
7. `远端解题`：仅通过 `/api/kali/exec` 执行完整分析与利用。
8. `按需穿透`：需要反连或端口映射时，在本地使用 frpc。
9. `结果回收`：通过 `/api/kali/read` 和 `/api/callbacks` 读取证据与 flag。

## 文件区兜底清理（建议）

为避免遗留文件，建议在文件服务器配置定时清理（TTL）：

```bash
sudo crontab -e
*/10 * * * * find /srv/ctf-files -type f -mmin +30 -delete
```

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
