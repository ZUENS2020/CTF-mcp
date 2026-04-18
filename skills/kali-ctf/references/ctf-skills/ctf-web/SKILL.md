---
name: ctf-web
description: Web 题专项方法。用于 HTTP/API/模板/鉴权类题目（XSS、SQLi、SSTI、SSRF、JWT、上传链等），并要求在 CTF-mcp 项目中仅通过远端 Kali API 执行所有测试与利用。
---

# Web 解题（项目版）

## 执行约束

1. 所有 Web 侦察与利用在远端 Kali 执行。
2. 本地不运行 `sqlmap/ffuf/nmap` 等解题工具。
3. 若题目入口在本地端口，先用 frpc 暴露后再由远端访问。

## 并发容器约定

1. 统一使用主技能已初始化的 `CONTAINER_NAME`（如 `ai-a-web-001`）。
2. 所有 `/api/kali/exec`、`/api/kali/read` 请求必须显式携带 `container=$CONTAINER_NAME`。
3. 禁止在子技能中硬编码容器名（如 `ctf-kali-base`）。

## 工具准备（远端执行）

通过 `/api/kali/exec`（`container=$CONTAINER_NAME`）安装或校验：

```bash
apt-get update && apt-get install -y curl jq
python3 -m pip install --upgrade requests sqlmap flask-unsign
```

## 快速流程

1. 基线探测：状态码、目录、接口、认证方式。
2. 建立最小可复现请求：记录 headers/cookie/body。
3. 漏洞分类：注入、鉴权、文件处理、模板执行、服务端请求链。
4. 先拿原语：信息泄露、权限绕过、文件读取、内部请求。
5. 再做链路：原语拼接到 flag 读取路径。

## 常见路径

1. SQL 注入：先布尔/报错，再盲注脚本化。
2. SSTI：先探测表达式，再对象探针，再命令执行。
3. SSRF：先回显能力，再内网面探测，再高价值目标。
4. JWT：检查 `alg`、签名验证、密钥来源、时效逻辑。
5. 上传链：校验后缀、MIME、解析器差异、执行触发点。

## 内置参考

1. `sql-injection.md`
2. `server-side.md`
3. `server-side-exec.md`
4. `auth-jwt.md`
5. `client-side.md`
