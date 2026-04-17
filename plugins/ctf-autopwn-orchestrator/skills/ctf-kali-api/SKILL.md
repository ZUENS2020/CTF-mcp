---
name: ctf-kali-api
description: Solve CTF tasks with strict remote execution. Challenge files and challenge URLs are local inputs, but AI must transfer via tmpfiles and use bore for tunneling, then solve entirely in remote Kali through https://api.zuens2020.work APIs.
---

# CTF Kali API

## Hard constraints

1. Local machine is only transfer/tunnel control plane.
2. Full solving (analysis/exploit/flag retrieval) runs remotely in Kali.
3. Do not run checksec/gdb/pwntools/sqlmap/nmap/exploit scripts on local machine.
4. Do not cheat by searching public writeups/official solutions/exploit repositories for the same challenge.
5. Derive solution from provided artifacts and runtime behavior only.

## Local command standards

### tmpfiles upload

```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

Convert URL:
- page: `https://tmpfiles.org/<id>/<name>`
- direct: `https://tmpfiles.org/dl/<id>/<name>`

### bore tunnel

```bash
bore local --to bore.pub <LOCAL_PORT>
```

## Remote API standards

Base URL: `https://api.zuens2020.work`

1. Container lifecycle
- `POST /api/containers`
- `PUT /api/containers/{name}/activate`

2. Kali execution
- `POST /api/kali/exec` with `{ "cmd": "...", "timeout": 30 }`

3. Read artifact
- `POST /api/kali/read` with `{ "path": "relative/path" }`

4. Callback inbox
- `GET /api/callbacks`

## Execution template

1. `本地传输` - upload local attachment via tmpfiles.
2. `Kali落地` - use `/api/kali/exec` to pull file into `/tmp/workspace/current`.
3. `Kali解题` - execute complete chain in remote Kali only.
4. `穿透` - use bore command when reverse channel is required.
5. `结果` - read artifacts via `/api/kali/read`, report flag evidence.
