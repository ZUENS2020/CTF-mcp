# CTF-mcp 项目介绍（中文）

## 1. 项目定位

`CTF-mcp` 当前是一个“纯 API 后端 + 前端面板 + Kali 容器执行环境”的 CTF 自动化系统。

核心目标：
- 让 AI/自动化流程通过统一 API 管理隔离容器。
- 在指定 Kali 容器中执行命令、读取结果文件。
- 通过回调接口接收外部服务回传数据。

## 2. 架构总览

- `backend`：FastAPI 服务（纯 API，不内置 MCP Server）。
- `frontend`：React 面板（通过 nginx 反代到 backend）。
- `kali-base`：Kali 基础镜像（`ctf-kali:latest`），用于创建题目容器。
- `SQLite`：后端内置 DB（`backend/data/app.db`），存配置和回调记录。

## 3. 主要能力

- 容器管理：
  - 列表、创建、删除容器。
- 远端执行：
  - 在指定容器执行 shell 命令。
  - 读取容器工作区文件内容。
- 配置管理：
  - 读写 `cf_token`、`cf_domain`。
- 回调收集：
  - 接收任意 body + headers 并持久化。
  - 支持按时间过滤查询、清空。

## 4. 典型调用流程

1. `GET /healthz` 检查服务状态。
2. `POST /api/containers` 创建容器（建议传唯一 `name`）。
3. `POST /api/kali/exec` 执行命令（如下载题目、工具检查）。
4. `POST /api/kali/read` 读取容器内文件（默认约束在工作区内）。
5. 需要外部回传时，使用 `POST /callback/{token}` 收集结果。
6. 任务结束 `DELETE /api/containers/{name}` 清理容器。

## 5. 运行与部署

```bash
cd /path/to/CTF-mcp
docker compose up -d --build
```

默认访问：
- 前端：`http://localhost:5173`
- 后端健康检查：`http://localhost:8000/healthz`

## 6. 关键配置（环境变量，前缀 `CTF_`）

后端读取 `backend/.env` 或环境变量：

- `CTF_DOCKER_BASE_IMAGE`（默认 `ctf-kali:latest`）
- `CTF_CONTAINER_PLATFORM`（默认 `linux/amd64`）
- `CTF_WORKSPACE_DIR`（默认 `/tmp/workspace`）
- `CTF_COMMAND_TIMEOUT_SECONDS`（默认 `30`）
- `CTF_DOCKER_API_TIMEOUT_SECONDS`（默认 `15`）
- `CTF_DOCKER_OPERATION_TIMEOUT_SECONDS`（默认 `20`）
- `CTF_CONTAINER_MEM_LIMIT`（默认 `32g`）
- `CTF_CONTAINER_NANO_CPUS`（默认 `8000000000`）
- `CTF_CONTAINER_PIDS_LIMIT`（默认 `32768`）
- `CTF_CONTAINER_SHM_SIZE`（默认 `8g`）

## 7. 安全与边界（当前实现）

- `kali exec` 有简单黑名单：`rm -rf /`、`docker`、`shutdown`、`reboot`、`mkfs`。
- `kali read` 强制路径在工作区（默认 `/tmp/workspace`）内，禁止目录穿越读取任意文件。
- 当前 API 默认无鉴权、CORS 允许全部来源（`*`），生产环境应在网关层加鉴权与访问控制。

## 8. 数据持久化

- SQLite 路径：`backend/data/app.db`
- 表：
  - `CallbackRecord`：回调事件（token、headers、body、时间）
  - `ConfigEntry`：配置项（key/value）

## 9. 运维建议

- 定期清理不再使用的容器。
- 给 API 增加鉴权（如 API Key/JWT + 网关白名单）。
- 对 `exec` 增加更细粒度策略（命令 allowlist + 审计）。
- 对回调数据启用保留期策略，防止数据库无限增长。

