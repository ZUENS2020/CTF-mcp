# Phase 06 E2E (Pure API)

## 前置

```bash
cd /Users/zuens2020/Documents/CTF-mcp
docker compose up -d --build
```

## 运行

```bash
cd /Users/zuens2020/Documents/CTF-mcp
python3 backend/scripts/e2e_phase06.py
```

可选参数：

- `--base-url http://127.0.0.1:8000`
- `--container phase06-kali-xxx`
- `--image kalilinux/kali-rolling:latest`
- `--callback-token phase06-token-xxx`
- `--keep-container`
