# CTF AutoPwn

CTF 自动化平台（FastAPI + MCP + React），当前已改为全容器化运行：

- `backend`：API + MCP + callback receiver + bore manager
- `frontend`：React 构建后由 Nginx 提供页面
- `kali-base`：预装 CTF 工具镜像（供后台动态创建题目容器）

## 一键启动

```bash
cd /Users/zuens2020/Documents/CTF-mcp
docker compose up -d --build
```

访问地址：

- 前端: [http://localhost:5173](http://localhost:5173)
- 后端健康检查: [http://localhost:8000/healthz](http://localhost:8000/healthz)
- MCP 端点: `http://localhost:8000/mcp`

## 关键说明

- `bore` 已内置在 `backend` 镜像中，不需要宿主机单独安装。
- 前端也在 Docker 内运行，不需要宿主机 `npm run dev`。
- 后台通过挂载 `/var/run/docker.sock` 控制 Docker 来创建题目容器。
- 新建题目容器默认镜像：`ctf-kali:latest`（由 `kali-base` 服务构建提供）。

## 停止与清理

```bash
cd /Users/zuens2020/Documents/CTF-mcp
docker compose down
```

如需连同构建缓存和匿名卷一起清理：

```bash
docker compose down --rmi local --volumes
```

## Phase 06 端到端验收

先确保 compose 已启动，然后在宿主机执行：

```bash
cd /Users/zuens2020/Documents/CTF-mcp
python3 backend/scripts/e2e_phase06.py
```

严格要求 bore 成功：

```bash
python3 backend/scripts/e2e_phase06.py --require-bore
```
