# CTF AutoPwn

当前架构：

- `backend`：纯 FastAPI（无 MCP），提供容器管理、Kali 执行、callback API
- `frontend`：React 面板
- `plugin`：统一编排本机传输/穿透命令 + 远端 Kali API

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
- `GET/POST/DELETE /api/containers...`
- `POST /api/kali/exec`：在指定容器执行命令（请求体需带 `container`）
- `POST /api/kali/read`：读取指定容器 `/tmp/workspace` 文件（请求体需带 `container`）
- `GET/DELETE /api/callbacks`
- `POST /callback/{token}`

## 传输与穿透（命令行标准）

上传本地文件到 tmpfiles：

```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

## E2E 验证

```bash
cd /Users/zuens2020/Documents/CTF-mcp
python3 backend/scripts/e2e_phase06.py
```
