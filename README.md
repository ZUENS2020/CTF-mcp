# CTF AutoPwn

当前架构：

- `backend`：纯 FastAPI（无 MCP），提供容器管理、Kali 执行、配置与 callback API
- `frontend`：React 面板
- `kali-base`：Kali 基础镜像服务（由 `docker compose` 构建）

## 启动

```bash
cd /path/to/CTF-mcp
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
- `GET/PUT /api/config`
- `GET/DELETE /api/callbacks`
- `POST /callback/{token}`

## 传输与穿透（命令行标准）

上传本地文件到 tmpfiles：

```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

## E2E 验证

```bash
cd /path/to/CTF-mcp
python3 backend/scripts/e2e_phase06.py
```
