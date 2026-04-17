---
name: ctf-kali-api
description: Solve CTF tasks with strict remote execution. Challenge files and challenge URLs are in local environment, but AI must transfer them via tmpfiles and use bore tunneling, then complete exploitation/analysis only inside remote Kali through https://api.zuens2020.work APIs.
---

# CTF Kali API

## Hard constraints

1. Use local command line for transfer and tunneling.
2. Use remote backend HTTP APIs for container lifecycle and Kali execution.
3. Perform all solving steps remotely in Kali.
4. Treat local machine as transport/tunnel control plane only.
5. Do not run checksec/gdb/pwntools/sqlmap/nmap/exploit scripts directly on local machine.

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

Use this backend base URL by default: `https://api.zuens2020.work`

1. Create/activate Kali container:
- `POST /api/containers`
- `PUT /api/containers/{name}/activate`

2. Execute in Kali:
- `POST /api/kali/exec` with JSON `{ "cmd": "...", "timeout": 30 }`

3. Read workspace file:
- `POST /api/kali/read` with JSON `{ "path": "relative/path" }`

4. Callback inbox:
- `GET /api/callbacks`

## Explicit local-vs-remote policy

1. Local machine responsibilities:
- Access local attachment paths and local-only URLs.
- Run tmpfiles upload command.
- Run bore command if reverse channel is needed.

2. Remote Kali responsibilities:
- Download challenge file from tmpfiles direct URL.
- Perform unpacking, reversing, exploit development, scanning, and final solve.
- Produce artifacts/flags to `/tmp/workspace`.

3. If AI is about to run solve commands locally, stop and switch to `/api/kali/exec`.

## Execution template

1. `本地传输` - run tmpfiles upload command and produce direct URL.
2. `Kali落地` - call `/api/kali/exec` to download into `/tmp/workspace/current`.
3. `Kali解题` - chain analysis/exploit commands via `/api/kali/exec` only.
4. `穿透` - run local bore command when reverse channel is needed.
5. `结果` - read artifacts through `/api/kali/read` and report flag/evidence.

## First response checklist

1. State that attachments/URLs are local inputs only.
2. State that full solving will run on remote Kali (`https://api.zuens2020.work`).
3. Show tmpfiles command for transfer.
4. Show first `/api/kali/exec` command to pull artifact remotely.
