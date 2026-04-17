# CTF AutoPwn

CTF 自动化平台（FastAPI + MCP + React），当前已改为全容器化运行：

- `backend`：API + MCP + callback receiver + bore manager
- `frontend`：React 构建后由 Nginx 提供页面
- `kali-base`：基于 `kalilinux/kali-rolling:latest` 构建并安装 `kali-linux-headless` 的容器（供后台动态创建题目容器）

## 一键启动

```bash
cd /Users/zuens2020/Documents/CTF-mcp
docker compose up -d --build
```

网络受限时（例如 npm/crates 访问不稳定），先设置构建参数再启动：

```bash
cd /Users/zuens2020/Documents/CTF-mcp
export NPM_REGISTRY=https://registry.npmmirror.com
# 可选：自定义 bore 二进制下载地址
# export BORE_DOWNLOAD_URL=https://<your-mirror>/bore-x86_64-unknown-linux-musl.tar.gz
# 可选：代理
# export HTTP_PROXY=http://127.0.0.1:7890
# export HTTPS_PROXY=http://127.0.0.1:7890
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
- 新建题目容器默认镜像：`ctf-kali:latest`（由 `kali-base` 服务构建提供，包含 `kali-linux-headless`）。

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

## tmpfiles 上传命令

统一使用本机命令进行传输：

```bash
curl -F "file=@/Users/myuser/test.jpg" https://tmpfiles.org/api/v1/upload
```


## Skill

- Local-tools CTF skill: `/Users/zuens2020/Documents/CTF-mcp/ctf-autopwn/SKILL.md`
- 触发建议：在会话里写 `使用 ctf-autopwn-local-tools skill`。
