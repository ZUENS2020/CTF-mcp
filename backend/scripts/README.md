# Phase 06 E2E

## 1) 启动后端

```bash
cd /Users/zuens2020/Documents/CTF-mcp/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 2) 运行端到端脚本

另开一个终端：

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
