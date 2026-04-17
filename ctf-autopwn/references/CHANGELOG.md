# CHANGELOG - 变更日志

所有重要的变更都应该记录在此文件。

格式:

```markdown
## [版本号] - YYYY-MM-DD

### Added (新增)
- 新增功能描述

### Changed (修改)
- 修改内容描述

### Fixed (修复)
- 问题修复描述

### Deprecated (废弃)
- 即将废弃的功能

### Removed (移除)
- 已移除的功能

### Security (安全)
- 安全相关变更
```

---

## [1.0.0] - 2024-03-15

### Added
- 初始版本发布
- CTF 自动化工具集
- 参考文档集合

### scripts/
- `session_init.py` - 初始化 CTF 挑战会话
- `attempt_add.py` - 记录尝试到 attempts.md
- `bore_open.sh` - 打开 bore 隧道
- `bore_list.sh` - 列出活跃隧道
- `bore_close.sh` - 关闭隧道
- `tf_up.sh` - 上传文件到 tmpfiles.org
- `tf_get.sh` - 从 tmpfiles.org 下载
- `lessons_write.py` - 写入经验到 LESSONS.md

### references/
- `tool-web.md` - Web 渗透工具速查
- `tool-pwn.md` - Pwn 工具速查
- `tool-crypto.md` - 密码学工具速查
- `tool-rev.md` - 逆向工程工具速查
- `tool-forensics.md` - 取证工具速查
- `tool-misc.md` - 杂项工具速查
- `attempt-log-format.md` - 尝试日志格式
- `lessons-writing-guide.md` - 经验写作指南
- `LESSONS.md` - 经验池模板
- `CHANGELOG.md` - 本文件
