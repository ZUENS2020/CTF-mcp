---
name: solve-challenge
description: 统一 CTF 调度入口。用于题型未明确时的首轮研判与分流，在 CTF-mcp 项目中将题目附件/URL 从本地输入转为远端 Kali 可执行任务，并把执行路由到 ctf-web、ctf-pwn、ctf-reverse、ctf-crypto、ctf-forensics、ctf-misc。
---

# 题目总调度（项目版）

## 项目执行模型

1. 本地仅做输入、上传与隧道控制，不做解题执行。
2. 所有分析与利用都通过 `setting.md` 的 `Api_Base` 在远端 Kali 完成。
3. 题型明确后再进入对应分类技能。
4. 若设备判定目标不是后端云服务器，必须停机交接并等待用户执行结果。

## 设备选择与停机交接（强制）

可选设备：
1. `backend-cloud`（默认）：后端 API 对应 Kali 容器。
2. `i9-12900k`：本地高性能工作站。
3. `gpu-cloud`：高性能 GPU 云（固定环境：`CUDA 13.0` + `Python 3.12` + `Ubuntu 22.04`）。

判定规则：
1. 常规 CTF 分析与利用：`backend-cloud`。
2. 明显 GPU 密集任务（大规模爆破/模型推理）：`gpu-cloud`。
3. 依赖本地专有环境且后端无法满足：`i9-12900k`。

停机交接规则：
1. 若目标设备不是 `backend-cloud`，AI 不继续自动求解。
2. AI 仅执行：
- 生成完整交接脚本（必须包含环境安装与前置检查）；
- 打包并上传交接文件到 `File_Base`；
- 输出一键后台运行命令（防 SSH 不稳中断）与监控命令；
- 明确需要用户回传的结果文件。
3. 完成交接后立即停止，等待用户返回执行产物。

后台运行参考模板（必须使用）：

```bash
chmod +x run_task.sh
nohup bash run_task.sh > run.log 2>&1 & echo $! > run.pid
ps -fp $(cat run.pid)
tail -f run.log
```

## 配置来源

统一读取：
- `./setting.md`（当前工作区）

字段：
1. `Api_Base`
2. `FRP_Address`
3. `FRP_token`
4. `File_Base`

## 本地动作（仅控制面）

### 文件上传

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

下载直链格式：
- `<File_Base>/<文件名>`

清理要求（强制）：
1. 远端下载并校验成功后，立即删除 `/srv/ctf-files/${FILE_NAME}`。
2. 删除命令（本地控制面允许）：

```bash
ssh "root@${FRP_ADDRESS}" "rm -f /srv/ctf-files/${FILE_NAME}"
```

### 隧道穿透（按需）

```bash
cat > /tmp/frpc-ctf.toml <<'EOF'
serverAddr = "<FRP_Address from setting.md>"
serverPort = 7000
transport.tcpMux = false
auth.method = "token"
auth.token = "<FRP_token from setting.md>"
EOF
frpc -c /tmp/frpc-ctf.toml
```

## 本机禁令（强制）

1. 本机仅允许执行：`nginx 文件服务器上传` + `frpc` 穿透。
2. 严禁在本机执行任何解题命令（扫描、调试、利用、逆向、取证脚本）。
3. 首轮研判阶段的 `file/strings/checksec/curl/nc` 等侦察动作也必须放到远端容器执行。
4. 若误在本机执行了解题命令，必须立即停止并记录违规条目，然后改为远端 API 执行。

## 远端 API 基线

基础地址：`setting.md` 的 `Api_Base`

并发约束：
- 不使用 active 容器；每个请求独立指定 `container`。

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

1. 创建容器：`POST /api/containers`
2. 执行命令：`POST /api/kali/exec`（请求体必须带 `container`）
3. 读取文件：`POST /api/kali/read`（请求体必须带 `container`）
4. 回调收件箱：`GET /api/callbacks`

## 强制自检环节（调度前必须通过）

任一检查失败时，停止调度，不得继续题型判定与利用。

```bash
SETTINGS_FILE="setting.md"
[ -f "$SETTINGS_FILE" ] || { echo "missing setting.md"; exit 1; }

API_BASE="$(awk -F': *' '/^Api_Base:/{print $2}' "$SETTINGS_FILE" | tr -d '\r' | sed 's/^ *//;s/ *$//' | sed 's/^\"//;s/\"$//')"
FILE_BASE="$(awk -F': *' '/^File_Base:/{print $2}' "$SETTINGS_FILE" | tr -d '\r' | sed 's/^ *//;s/ *$//' | sed 's/^\"//;s/\"$//')"
[ -n "$API_BASE" ] || { echo "missing Api_Base"; exit 1; }
[ -n "$FILE_BASE" ] || { echo "missing File_Base"; exit 1; }

echo "$API_BASE" | grep -Eq '^https?://[^ ]+$' || { echo "Api_Base invalid: $API_BASE"; exit 1; }
echo "$FILE_BASE" | grep -Eq '^https?://[^ ]+$' || { echo "File_Base invalid: $FILE_BASE"; exit 1; }

FILE_SERVER_BASE="$(echo "$FILE_BASE" | sed -E 's#/files/?$##')"
curl -fsS "${API_BASE%/}/healthz" >/dev/null || { echo "api healthz failed: ${API_BASE%/}/healthz"; exit 1; }
curl -fsS "${FILE_SERVER_BASE%/}/healthz_files" >/dev/null || { echo "file server health failed: ${FILE_SERVER_BASE%/}/healthz_files"; exit 1; }
echo "preflight ok"
```

## 首轮流程

1. 收集输入：附件路径、题目 URL、端口、题目描述。
2. 执行“强制自检环节”并确认通过。
3. 设备判定：决定 `backend-cloud` / `i9-12900k` / `gpu-cloud`。
4. 若目标设备不是 `backend-cloud`：执行停机交接并等待用户回传结果。
5. 上传附件：本地上传到 nginx 文件服务器，得到 `File_Base/文件名` 直链。
6. 远端落地：通过 `/api/kali/exec` 在 `/tmp/workspace/current` 下载附件并校验。
7. 源文件清理：下载校验成功后，立即删除文件服务器源文件。
8. 首轮侦察：仅在远端执行 `file/strings/checksec/binwalk/nc/curl` 等。
9. 题型判定：Web/Pwn/Reverse/Crypto/Forensics/Misc。
10. 路由执行：进入对应分类技能。
11. 输出证据：通过 `/api/kali/read` 与 `/api/callbacks` 收集结果与 flag。

## 尝试记录规范

调度层必须维护“已尝试路径”清单，至少记录：

1. 路径名（例如 `Web-SSTI`、`Pwn-格式化字符串`）。
2. 关键命令或 payload。
3. 观察到的结果。
4. 是否产生新信息。
5. 是否继续该路径。

建议在远端维护 `/tmp/workspace/current/attempts.log`，防止重复试错。

## 转向策略

出现以下情况必须转向到下一条候选路径：

1. 同一路径 3 次尝试无新信息。
2. 关键前提被否定（例如注入点不可控、端口不可达）。
3. 题型信号改变（如原判 Web，后续更像 Pwn）。

转向时先写明“放弃原因 + 新路径验证命令”，再执行下一路径。

## 题型判定规则

1. 文件特征
- `pcap/evtx/raw/dd/E01` 倾向 Forensics
- `elf/exe/so/dll` 倾向 Reverse 或 Pwn
- `py/sage/大整数文本` 倾向 Crypto
- Web 代码或 HTTP 服务倾向 Web

2. 描述关键词
- `overflow/ROP/libc/heap` -> Pwn
- `RSA/AES/nonce/lattice/LWE` -> Crypto
- `XSS/SQLi/SSTI/SSRF/JWT` -> Web
- `memory dump/packet capture/stego` -> Forensics
- `jail/encoding/sandbox/game` -> Misc

3. 服务行为
- 交互式端口 + 异常崩溃 -> Pwn
- HTTP/HTTPS -> Web
- 数学或密码问答 -> Crypto

## 路由目标

1. Web：`../ctf-web/SKILL.md`
2. Pwn：`../ctf-pwn/SKILL.md`
3. Reverse：`../ctf-reverse/SKILL.md`
4. Crypto：`../ctf-crypto/SKILL.md`
5. Forensics：`../ctf-forensics/SKILL.md`
6. Misc：`../ctf-misc/SKILL.md`

## 关键约束

1. 不在本地运行解题工具链。
2. 不搜索该题公开题解。
3. 不跨题复用未经验证的 exploit。
4. 不允许在单一路径上无记录地反复尝试。
