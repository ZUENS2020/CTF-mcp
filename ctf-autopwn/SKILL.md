---
name: ctf-autopwn-local-tools
description: 使用 Kali MCP 解 CTF 题目。题目文件或题目 URL 在本地时，先用命令行 tmpfiles 与 bore 完成传输和穿透，再在 Kali 内执行完整分析与利用。适用于 pwn/web/rev/crypto/misc 的容器化解题流程。
---

# CTF AutoPwn Local Tools

## Rules

1. Use command-line tmpfiles for file transfer.
2. Use command-line bore for tunnel exposure.
3. Run solving workflow inside Kali via MCP `shell_exec`.
4. Use MCP `read_file` only for reading workspace artifacts.
5. Use MCP `get_callbacks` only for callback inbox checks.
6. Do not run the main exploit workflow directly on host unless user explicitly requests it.

## Fixed Commands

### tmpfiles upload

```bash
curl -F "file=@/ABS/PATH/TO/FILE" https://tmpfiles.org/api/v1/upload
```

Convert returned page URL to direct download URL:

- page: `https://tmpfiles.org/<id>/<name>`
- download: `https://tmpfiles.org/dl/<id>/<name>`

### bore tunnel

```bash
bore local --to bore.pub <LOCAL_PORT>
```

Run this on local machine or server shell (same command).

## Workflow

1. Normalize inputs.
- If user gives local file path, upload it with tmpfiles command.
- If user gives local-only URL, fetch it to local file first, then upload with tmpfiles.

2. Pull challenge into Kali workspace.
- Use Kali MCP `shell_exec`:
```bash
mkdir -p /tmp/workspace/current
curl -fsSL '<TMPFILES_DL_URL>' -o /tmp/workspace/current/chall.bin
```

3. Solve inside Kali.
- Use `shell_exec` for extraction, static/dynamic analysis, exploit development, trigger, and flag retrieval.

4. Handle reverse shell or outbound callback.
- Run bore command in local/server shell.
- Use returned public endpoint in payload.
- Continue execution in Kali with `shell_exec`.

5. Return results.
- Return key commands, exploit script path, and flag evidence.

## Response Template

1. `传输` - tmpfiles upload command and resulting direct URL.
2. `落地` - Kali download command to `/tmp/workspace/current`.
3. `解题` - Kali-only execution steps.
4. `穿透` - bore command and endpoint usage (only if needed).
5. `结果` - flag/output and minimal verification.
