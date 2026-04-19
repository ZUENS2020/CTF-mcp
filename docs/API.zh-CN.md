# CTF-mcp API 接口文档（中文）

## 1. 基本信息

- 后端框架：FastAPI
- 默认基址：`http://127.0.0.1:8000`
- 数据格式：JSON（`/callback/{token}` 可接收任意原始 body）
- 鉴权：当前版本默认无鉴权

## 2. 通用错误说明

常见状态码：
- `400` 参数错误、Docker API 报错（部分场景）
- `404` 资源不存在（如容器不存在、文件不存在）
- `500` 服务器内部错误（如未捕获异常）
- `503` Docker 不可用
- `504` Docker 调用超时

## 3. 健康检查

### `GET /healthz`

用途：检查服务是否存活。

成功响应：

```json
{
  "status": "ok"
}
```

---

## 4. 容器管理

路由前缀：`/api/containers`

### `GET /api/containers`

用途：列出所有容器（含停止状态）。

成功响应示例：

```json
[
  {
    "id": "abcd1234",
    "name": "ai-a-web-001",
    "status": "running",
    "image": "ctf-kali:latest"
  }
]
```

### `POST /api/containers`

用途：创建容器并启动（默认命令 `sleep infinity`）。

请求体：

```json
{
  "name": "ai-a-web-001",
  "image": "ctf-kali:latest"
}
```

字段说明：
- `name`：必填，容器名。
- `image`：可选；未提供时使用服务端默认镜像（`CTF_DOCKER_BASE_IMAGE`）。

成功响应示例：

```json
{
  "message": "created",
  "id": "abcd1234",
  "name": "ai-a-web-001",
  "status": "created"
}
```

### `DELETE /api/containers/{name}`

用途：强制删除指定容器。

成功响应示例：

```json
{
  "message": "deleted",
  "name": "ai-a-web-001"
}
```

错误：
- `404` 容器不存在

---

## 5. Kali 执行与读取

路由前缀：`/api/kali`

### `POST /api/kali/exec`

用途：在指定容器内执行命令。

请求体：

```json
{
  "container": "ai-a-web-001",
  "cmd": "id && pwd",
  "timeout": 30
}
```

字段约束：
- `container`：必填，非空字符串。
- `cmd`：必填，非空字符串。
- `timeout`：可选，`1~3600` 秒；不传则用后端默认值（`CTF_COMMAND_TIMEOUT_SECONDS`）。

执行机制：
- 服务端会包装为：`timeout <N>s /bin/bash -lc '<cmd>'`

成功响应：

```json
{
  "container": "ai-a-web-001",
  "exit_code": 0,
  "output": "uid=0(root) gid=0(root) groups=0(root)\n/tmp/workspace\n"
}
```

错误：
- `404` 容器不存在
- `500` Docker 执行报错
- `503` Docker 不可用
- `504` Docker 操作超时

说明：
- 有命令黑名单（`rm -rf /`、`docker`、`shutdown`、`reboot`、`mkfs`）。命中时会失败（当前实现可能表现为 `500`）。

### `POST /api/kali/read`

用途：读取容器内文件（UTF-8 文本）。

请求体：

```json
{
  "container": "ai-a-web-001",
  "path": "current/result.txt"
}
```

路径规则：
- 服务端会将 `path` 解析到工作区（默认 `/tmp/workspace`）下。
- 禁止越界到工作区外（目录穿越会被拒绝）。

成功响应示例：

```json
{
  "container": "ai-a-web-001",
  "path": "/tmp/workspace/current/result.txt",
  "content": "flag{...}\n"
}
```

错误：
- `400` 路径越界（`path must stay within workspace`）
- `404` 文件或容器不存在
- `500` Docker 读取报错

---

## 6. 配置管理

路由前缀：`/api/config`

### `GET /api/config`

用途：读取当前配置（DB 中的 `cf_token`、`cf_domain`）。

成功响应：

```json
{
  "cf_token": "xxxxx",
  "cf_domain": "example.com"
}
```

### `PUT /api/config`

用途：更新配置（支持部分更新）。

请求体（字段可选）：

```json
{
  "cf_token": "xxxxx",
  "cf_domain": "example.com"
}
```

成功响应：

```json
{
  "message": "config updated"
}
```

---

## 7. 回调接口

### `POST /callback/{token}`

用途：接收外部回调并写入数据库。

特性：
- `token` 来自路径参数。
- 请求 body 原样读取并以 UTF-8（替换非法字符）存储。
- 请求 headers 会序列化后存储。

成功响应：

```json
{
  "message": "received"
}
```

### `GET /api/callbacks`

用途：查询回调记录，按时间倒序。

查询参数：
- `since`（可选，ISO 时间，如 `2026-04-19T00:00:00`）

成功响应示例：

```json
[
  {
    "id": 12,
    "token": "demo-token",
    "source_ip": "1.2.3.4",
    "headers_json": "{\"user-agent\":\"curl/8.0\"}",
    "body": "hello",
    "created_at": "2026-04-19T04:00:00.000000"
  }
]
```

### `DELETE /api/callbacks`

用途：清空所有回调记录。

成功响应：

```json
{
  "message": "callbacks cleared"
}
```

---

## 8. 最小可用调用序列（示例）

```bash
# 1) 健康检查
curl -sS http://127.0.0.1:8000/healthz

# 2) 创建容器
curl -sS -X POST http://127.0.0.1:8000/api/containers \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo-kali-001","image":"ctf-kali:latest"}'

# 3) 执行命令
curl -sS -X POST http://127.0.0.1:8000/api/kali/exec \
  -H 'Content-Type: application/json' \
  -d '{"container":"demo-kali-001","cmd":"id && pwd","timeout":30}'

# 4) 删除容器
curl -sS -X DELETE http://127.0.0.1:8000/api/containers/demo-kali-001
```

