# Phase 06 E2E

## 前置

先起全栈 Docker：

```bash
cd /Users/zuens2020/Documents/CTF-mcp
docker compose up -d --build
```

## 运行端到端脚本

```bash
cd /Users/zuens2020/Documents/CTF-mcp
python3 backend/scripts/e2e_phase06.py
```

可选参数：

- `--require-bore`: bore 启动失败时直接判定失败
- `--keep-container`: 测试结束后保留容器
- `--base-url http://127.0.0.1:8000`: 指定后端地址

示例：

```bash
python3 backend/scripts/e2e_phase06.py --require-bore --bore-port 4444
```
