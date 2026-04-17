# CTF AutoPwn

当前架构：

- `backend`：纯 FastAPI（无 MCP），提供容器管理、Kali 执行、callback API
- `frontend`：React 面板
- `plugin`：`plugins/ctf-autopwn-orchestrator`，统一编排本机 tmpfiles/bore + 远端 Kali API

## 启动

```bash
cd /Users/zuens2020/Documents/CTF-mcp
docker compose up -d --build
```

访问：
- 前端: [http://localhost:5173](http://localhost:5173)
- 后端健康检查: [http://localhost:8000/healthz](http://localhost:8000/healthz)

## 纯 API 接口

- `GET /healthz`
- `GET/POST/DELETE/PUT /api/containers...`
- `POST /api/kali/exec`：在 active Kali 容器里执行命令
- `POST /api/kali/read`：读取 active Kali 容器 `/tmp/workspace` 文件
- `GET/DELETE /api/callbacks`
- `POST /callback/{token}`

## 传输与穿透（命令行标准）

上传本地文件到 tmpfiles：

```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

打开 bore 隧道：

```bash
bore local --to bore.pub <LOCAL_PORT>
```

## Plugin 入口

插件目录：
- `/Users/zuens2020/Documents/CTF-mcp/plugins/ctf-autopwn-orchestrator`

插件内 skill：
- `/Users/zuens2020/Documents/CTF-mcp/plugins/ctf-autopwn-orchestrator/skills/ctf-kali-api/SKILL.md`

插件脚本：
- `scripts/local_tmpfiles_upload.sh`
- `scripts/local_bore_open.sh`
- `scripts/kali_api_exec.py`
- `scripts/kali_api_read.py`

## E2E 验证

```bash
cd /Users/zuens2020/Documents/CTF-mcp
python3 backend/scripts/e2e_phase06.py
```
