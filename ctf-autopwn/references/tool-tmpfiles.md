# tmpfiles.org 用法

免注册的临时文件托管,上限 100 MB / 文件,保留 60 分钟(上传方)。用于在用户物理机 ↔ Kali 容器之间传附件。

## API

### 上传

```bash
curl -fsS -F "file=@/path/to/local.bin" https://tmpfiles.org/api/v1/upload
```

返回:
```json
{"status":"success","data":{"url":"https://tmpfiles.org/4294967/local.bin"}}
```

### 下载(注意:URL 要换成直链)

上面返回的 URL 是**展示页**,不是直接下载链接。直链需要把 `tmpfiles.org/` 替换成 `tmpfiles.org/dl/`:

```
展示页: https://tmpfiles.org/4294967/local.bin
直链:   https://tmpfiles.org/dl/4294967/local.bin
```

下载:
```bash
curl -fsSL 'https://tmpfiles.org/dl/4294967/local.bin' -o /tmp/workspace/current/artifacts/local.bin
```

## 典型流程

### 场景 A:用户把题目附件传给 AI
1. 用户在物理机上:`curl -F "file=@chall.bin" https://tmpfiles.org/api/v1/upload`
2. 把返回的 URL 发给 AI
3. AI 在 Kali 里:`bash scripts/tf_get.sh '<用户给的URL>' artifacts/chall.bin`

### 场景 B:AI 把结果回传给用户
AI 在 Kali 里:
```
bash scripts/tf_up.sh /tmp/workspace/current/output.txt
```
脚本会打印直链,告诉用户在物理机 `curl -O <URL>` 取回。

## 注意事项

- 返回的 JSON 里的 URL 是**展示页**,脚本 `tf_get.sh` 已自动处理 `/dl/` 替换,直接粘用户给的原始 URL 就行
- 大文件(>100 MB):分割 + 多文件上传,或换 `0x0.st` / `transfer.sh` —— 见 `tool-misc.md`
- 包含 flag 或敏感数据的产物**不要**上传 tmpfiles(公开可访问),改用 bore + 本地 http 服务器
