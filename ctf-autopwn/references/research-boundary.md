# 信息收集的边界 — 什么能查,什么不能查

## 核心判据

> **去掉题目里的专有名词后,这个搜索词还能帮别人学同类技术吗?**
> 能 → 可以搜(技术原理 / 工具文档 / 漏洞原理)
> 不能 → 禁止(这道题的 writeup / 答案)

## ✅ 允许查

| 类型 | 例子 |
|---|---|
| 工具文档 / man page | `man sqlmap`, sqlmap README, pwntools docs |
| 技术原理 / 通用手法 | "Jinja2 SSTI sandbox escape techniques", "ret2dlresolve principle", "AES-ECB 明文重放原理" |
| CVE 描述 + PoC 原理(非涉题) | "CVE-2021-44228 log4shell details" |
| 协议规范 / RFC | RFC 2616, TLS 1.3 handshake |
| 官方源码 | Linux kernel git blame, PHP source |
| 标准密码学论文 / 公式 | Wiener's attack on low private exponent RSA |
| Kali / 工具安装与使用 | "how to install gef on kali" |

## ❌ 禁止查

| 类型 | 例子 |
|---|---|
| 这道题的 writeup | "picoCTF 2024 babygame writeup", "HTB Bashed walkthrough" |
| 题目专属答案 | "CCS2023 crypto_warmup flag", "某校赛 week3 逆向答案" |
| flag 泄露 / 数据库 | 任何声称"flag 集合"的站 |
| 比赛期间的 Discord / Reddit 讨论 | 即使标题看起来是技术讨论 |

## 灰色区域判断

**场景 A**:题目是 SQLi,你想搜 "PostgreSQL WAF bypass 2024"
- ✅ 这是通用技术,不绑定这道题

**场景 B**:题目是 SQLi,题目环境里看到 `powered by shopMVC 3.2`,你想搜 "shopMVC 3.2 CVE"
- ✅ 这是真实的漏洞情报收集,现实 pentesting 也这么干

**场景 C**:题目是 SQLi,你想搜 "shopMVC 3.2 CTF"
- ❌ 意图已经是找这道题的答案

**场景 D**:你搜到一个 writeup,里面**恰好**提到了这道题
- 立刻关闭页面,不要看内容
- 告诉用户:"在搜 X 时意外搜到本题 writeup,已避开,建议换用户角度提示"

## 实操准则

- 搜之前先在脑子里把题目特有信息替换成占位符。如果替换后还有用,才搜。
- 看到 writeup 标题含赛题名 / 赛事名 + 题目名,**不要点进去**。
- `grep LESSONS.md` 不算联网搜索,鼓励优先做。
- 向用户问 hint 不算作弊,但要说清你目前卡在哪。

## 红线一旦越过怎么办

- 坦白告诉用户"我不小心看了这道题的 writeup"
- 本次解题**不再写 LESSON**(经验会污染)
- 题目请用户换一道
