---
name: ctf-kali-api
description: Solve CTF tasks by combining local shell commands (tmpfiles and bore) with remote pure HTTP APIs for Kali container execution. Use when challenge files/URLs are local but exploitation and analysis must run inside remote Kali.
---

# CTF Kali API

## Required flow

1. Use local command line for transfer and tunneling.
2. Use remote backend HTTP APIs for container lifecycle and Kali execution.
3. Keep exploit workflow inside Kali API execution, not on host shell.

## Local command standards

### Upload local file to tmpfiles

```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

Convert result URL:
- page URL: `https://tmpfiles.org/<id>/<name>`
- direct URL: `https://tmpfiles.org/dl/<id>/<name>`

### Open tunnel with bore

```bash
bore local --to bore.pub <LOCAL_PORT>
```

## Remote API standards

Assume backend base URL: `http://<remote-host>:8000`

1. Create/activate Kali container:
- `POST /api/containers`
- `PUT /api/containers/{name}/activate`

2. Execute in Kali:
- `POST /api/kali/exec` with JSON `{ "cmd": "...", "timeout": 30 }`

3. Read workspace file:
- `POST /api/kali/read` with JSON `{ "path": "relative/path" }`

4. Callback inbox:
- `GET /api/callbacks`

## Execution template

1. `本地传输` - run tmpfiles upload command and produce direct URL.
2. `Kali落地` - call `/api/kali/exec` to download into `/tmp/workspace/current`.
3. `Kali解题` - chain analysis/exploit commands via `/api/kali/exec` only.
4. `穿透` - run local bore command when reverse channel is needed.
5. `结果` - read artifacts through `/api/kali/read` and report flag/evidence.
