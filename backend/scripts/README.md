# e2e_phase06.py

端到端验证脚本，测试所有 REST 接口和 MCP 工具（使用标准 MCP Streamable HTTP / JSON-RPC 2.0 协议）。

## 启动后端

```bash
cd /path/to/ctf-autopwn/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 运行脚本

```bash
python3 backend/scripts/e2e_phase06.py
```

可选参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--base-url` | `http://127.0.0.1:8000` | 后端地址 |
| `--container` | `phase06-kali-<ts>` | 测试用容器名 |
| `--image` | `kalilinux/kali-rolling:latest` | 容器镜像 |
| `--bore-port` | `4444` | bore 测试端口 |
| `--callback-token` | `phase06-token-<ts>` | 回调测试 token |
| `--require-bore` | false | bore 启动失败时直接判定失败 |
| `--keep-container` | false | 测试结束后保留容器 |

示例：

```bash
python3 backend/scripts/e2e_phase06.py \
  --base-url http://10.0.0.1:8000 \
  --require-bore \
  --bore-port 4444 \
  --keep-container
```
