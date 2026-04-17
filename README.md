# CTF AutoPwn

用 Claude Code / Codex / OpenCode 驱动 Kali 容器自动解 CTF 题目的平台。

## 架构

```
Mac 本地
  ├── React 前端（容器管理、回调查看）
  └── MCP 客户端（Claude Code / Codex / OpenCode）
           │ HTTPS（CF Tunnel）
           ▼
学校服务器
  ├── FastAPI 控制层（:8000）
  │     ├── /api/*           REST 接口（前端用）
  │     ├── /mcp             标准 MCP Streamable HTTP（AI 客户端用）
  │     └── /callback/{tok}  靶机回调收件箱
  ├── Kali 容器 1、2…（Docker，按需创建）
  ├── bore 进程（TCP 穿透 → bore.pub）
  └── CF Tunnel（HTTPS 穿透 → callback.zuens2020.work）
```

---

## 一、服务器端部署

### 1.1 前置条件

| 软件 | 最低版本 | 说明 |
|------|----------|------|
| Docker | 24+ | 容器运行时 |
| Docker Compose | 2.20+ | 服务编排 |
| Python | 3.12+ | 仅裸机跑时需要 |
| bore | 0.5+ | TCP 穿透二进制 |

#### 安装 bore

```bash
# 下载预编译二进制（替换架构名）
curl -L https://github.com/ekzhang/bore/releases/latest/download/bore-x86_64-unknown-linux-musl.tar.gz \
  | tar xz -C /usr/local/bin
chmod +x /usr/local/bin/bore
bore --version
```

#### 安装 Cloudflare Tunnel（可选，用于 HTTP 回调）

```bash
curl -L -o cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

---

### 1.2 用 Docker Compose 部署（推荐）

```bash
git clone <your-repo> ctf-autopwn
cd ctf-autopwn/backend

# 可选：创建 .env 覆盖默认值（见 1.3）
cp .env.example .env   # 若有的话，或直接编辑 docker-compose.yml

docker compose up -d --build
```

验证：

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

查看日志：

```bash
docker compose logs -f ctf-backend
```

---

### 1.3 环境变量

所有变量均以 `CTF_` 为前缀，可放在 `.env` 文件或 `docker-compose.yml` 的 `environment` 块中。

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CTF_APP_ENV` | `dev` | 环境标识 |
| `CTF_DOCKER_BASE_IMAGE` | `kalilinux/kali-rolling:latest` | 新容器默认镜像 |
| `CTF_WORKSPACE_DIR` | `/tmp/workspace` | 容器内工作目录 |
| `CTF_COMMAND_TIMEOUT_SECONDS` | `30` | shell_exec 单命令超时（秒） |
| `CTF_BORE_BINARY` | `bore` | bore 可执行文件路径 |
| `CTF_BORE_SERVER` | `bore.pub` | bore 服务器地址 |
| `CTF_BORE_RESTART_BACKOFF_SECONDS` | `2` | bore 崩溃后重启等待时间 |

**注意**：`docker-compose.yml` 中的服务已将 Docker socket（`/var/run/docker.sock`）挂载进容器，这是控制层操作 Docker 的必要条件。

---

### 1.4 裸机运行（不用 Docker Compose）

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 数据目录
mkdir -p data

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### 1.5 配置 Cloudflare Tunnel（HTTP 回调穿透）

CF Tunnel 将 HTTPS 流量从公网域名转发到服务器 :8000，靶机用 HTTP 请求 `https://callback.zuens2020.work/callback/<token>` 即可外带数据。

```bash
# 登录并创建 Tunnel
cloudflared tunnel login
cloudflared tunnel create ctf-autopwn

# 运行（前台测试）
cloudflared tunnel --url http://localhost:8000 run ctf-autopwn

# 或配置为 systemd 服务
cloudflared service install
```

配置文件示例 `~/.cloudflared/config.yml`：

```yaml
tunnel: ctf-autopwn
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: callback.zuens2020.work
    service: http://localhost:8000
  - service: http_status:404
```

---

## 二、本地前端启动

前端只读 `VITE_API_BASE` 环境变量来定位后端，不需要任何后端依赖。

```bash
cd frontend
npm install

# 开发模式（指向 CF Tunnel 域名，或 SSH 转发后的本地地址）
VITE_API_BASE=https://callback.zuens2020.work npm run dev
# 打开 http://localhost:5173

# 或生产构建（静态文件可任意托管）
npm run build
# 产物在 dist/
```

**SSH 端口转发（替代 CF Tunnel 访问前端 API）**：

```bash
# 把服务器 8000 转发到本地 8000
ssh -L 8000:localhost:8000 user@school-server
# 此时 VITE_API_BASE=http://localhost:8000 即可
```

---

## 三、MCP 客户端接入

MCP 端点：`https://<CF域名>/mcp`（或 SSH 转发后 `http://localhost:8000/mcp`）

### Claude Code

`~/.claude/mcp.json` 或项目根 `.mcp.json`：

```json
{
  "mcpServers": {
    "ctf-autopwn": {
      "type": "http",
      "url": "https://callback.zuens2020.work/mcp"
    }
  }
}
```

验证连接：

```bash
claude mcp list
claude mcp get ctf-autopwn
```

### Codex CLI

`~/.codex/config.toml`：

```toml
[[mcp_servers]]
name = "ctf-autopwn"
type = "http"
url  = "https://callback.zuens2020.work/mcp"
```

### OpenCode

`~/.config/opencode/config.json`：

```json
{
  "mcp": {
    "ctf-autopwn": {
      "type": "http",
      "url": "https://callback.zuens2020.work/mcp"
    }
  }
}
```

---

## 四、首次使用流程

### 4.1 在前端创建并激活容器

1. 打开前端 → **Containers** 页
2. 点击 **New Container**，输入名称（如 `kali-pwn-01`），镜像留空（用默认 kali-rolling）
3. 等待容器变为 `running`
4. 点击 **Activate** — 此后所有 MCP shell 命令都在这个容器里执行

### 4.2 让 Claude Code 开始解题

打开新的 Claude Code 会话，给出题目信息即可：

```
这道 pwn 题目的附件在 /Users/me/Downloads/pwn100
帮我分析漏洞并尝试获取 shell
```

Claude Code 会自动调用：
- `shell_exec` — 在 Kali 容器里跑命令（checksec / gdb / pwntools 等）
- `upload_file` — 把题目文件上传到容器 `/tmp/workspace/`
- `start_bore` — 开 TCP 隧道等待反弹 shell
- `get_callbacks` — 等待靶机 HTTP 回调（SSRF / XSS 外带）

### 4.3 上传题目文件（手动方式）

```bash
# base64 编码后通过 MCP 上传
b64=$(base64 < pwn100)
# 或直接在 Claude Code 里说"帮我上传 pwn100 这个文件"
```

### 4.4 查看回调

- 前端 **Callbacks** 页实时展示靶机发来的请求
- 或在 Claude Code 里说"查一下最近的回调"

---

## 五、MCP 工具参考

AI 客户端通过这些工具操作平台，无需了解底层实现。

### `shell_exec`

在当前 active 容器里执行 shell 命令，返回 `exit_code` 和 stdout+stderr 合并输出。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cmd` | string | ✅ | 要执行的命令 |
| `timeout` | int | ❌ | 超时秒数，默认 30 |

```
# 示例
shell_exec(cmd="nmap -sV 10.0.0.1")
shell_exec(cmd="python3 exploit.py", timeout=60)
```

**命令黑名单**：`rm -rf /`、`docker`、`shutdown`、`reboot`、`mkfs`

---

### `upload_file`

将文件上传到容器 `/tmp/workspace/`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 目标文件名（不含路径） |
| `b64` | string | ✅ | 文件内容的 Base64 编码 |

---

### `read_file`

读取容器 `/tmp/workspace/` 内的文件，返回文本内容。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | ✅ | 相对于 `/tmp/workspace/` 的路径 |

---

### `start_bore`

开启 bore TCP 隧道，将容器本地端口映射到 bore.pub 公网。返回 `remote_host:remote_port`，靶机可以直接连接。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `local_port` | int | ✅ | 容器本地监听端口（1–65535） |
| `server` | string | ❌ | bore 服务器，默认 `bore.pub` |

---

### `stop_bore`

停止指定端口的 bore 隧道。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `local_port` | int | ✅ | 之前 `start_bore` 传入的端口 |

---

### `list_bore_tunnels`

列出所有 bore 隧道状态（运行中、公网地址、重启次数等）。无参数。

---

### `get_callbacks`

查询靶机发来的 HTTP 回调记录（存储在 SQLite）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `since` | string | ❌ | ISO 8601 时间过滤，如 `2026-04-17T12:00:00Z` |
| `limit` | int | ❌ | 最大返回条数，默认 100，上限 1000 |

---

## 六、REST API 参考（前端用）

### 容器管理

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/containers` | 容器列表（含状态） |
| `POST` | `/api/containers` | 创建容器 `{"name":"...", "image":"..."}` |
| `DELETE` | `/api/containers/{name}` | 删除容器 |
| `PUT` | `/api/containers/{name}/activate` | 设置 active 容器 |
| `GET` | `/api/containers/active` | 查当前 active |

### 配置

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/config` | 读取 CF token 等配置 |
| `PUT` | `/api/config` | 保存配置 `{"cf_token":"...", "cf_domain":"..."}` |

### Callback

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/callbacks` | 查询回调记录 |
| `DELETE` | `/api/callbacks` | 清空记录 |
| `POST` | `/callback/{token}` | 靶机回调入口（任意 HTTP 方法均可） |

### 系统

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/healthz` | 健康检查 |

---

## 七、常见问题

**Q: MCP 连接失败，报 connection refused**

检查 CF Tunnel 是否在运行：`cloudflared tunnel info ctf-autopwn`；或者 SSH 端口转发是否存活。

**Q: `shell_exec` 返回 "no active container set"**

在前端 Containers 页点击 **Activate** 激活一个容器。active 状态存在内存里，服务重启后需要重新激活。

**Q: Kali 容器缺少某个工具**

```bash
shell_exec(cmd="apt-get update && apt-get install -y <tool>")
```

或修改 `Dockerfile.kali` 重新构建镜像：

```bash
cd backend
docker build -f Dockerfile.kali -t ctf-kali:local .
# 创建容器时 image 填 ctf-kali:local
```

**Q: bore 隧道断了靶机连不上**

bore 有自动重连逻辑。用 `list_bore_tunnels` 检查 `running` 和 `restart_count` 字段。若 `last_error` 显示 `bore binary not found`，确认服务器上 `bore` 在 PATH 里。

**Q: 多个 AI 会话并发冲突**

active container 是全局状态，多个 AI 会话共用同一个容器。建议每个会话独立创建并激活各自的容器。

---

## 八、端到端验证

运行脚本验证所有 REST 接口和 MCP 工具：

```bash
cd backend
python3 scripts/e2e_phase06.py

# 可选参数
python3 scripts/e2e_phase06.py \
  --base-url http://127.0.0.1:8000 \
  --require-bore \        # bore 启动失败直接报错
  --bore-port 4444 \
  --keep-container        # 测完保留容器便于调试
```
