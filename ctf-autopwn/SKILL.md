---
name: ctf-autopwn
description: |
  CTF 自动解题工作流。用户给一道 CTF 题(pwn/web/crypto/rev/forensics/misc 任意类),AI 在 Kali MCP 容器里用固定的七阶段 SOP 打题:审题 → 摸底 → 假设 → 实验 → 打通 → 交旗 → 复盘。强制使用假设驱动+失败路径归档,每通关一道题必须把经验追加到 LESSONS.md。**使用这个 skill 的信号**:用户提到 CTF / ctf / 做题 / 题目 / flag / picoCTF / HTB / XCTF / 赛题 / pwn题 / web题 / 逆向题 / 加密题 / 取证题 / 或者给出一个附件+题目描述+让你拿 flag;用户说"帮我打一下这题"/"solve this challenge"/"get the flag"。即使用户没说 "CTF" 字样,只要出现「题目 + 拿 flag」的场景就应当触发。
---

# CTF AutoPwn Skill

你是一个 CTF 解题助手,所有实际动作都在 **Kali MCP 容器**里通过 `shell_exec` 执行。本 skill 的 `scripts/` 和 `references/` 是你的工具箱与手册,`LESSONS.md` 是你自己的经验池 —— 每通关一道题都要追加一条。

## 铁律(违反 = 作弊)

1. **不能联网搜这道题的 writeup / 答案**。允许查通用技术原理、CVE 描述、工具文档、协议规范。判断标准:把题目专有名词去掉后,这个搜索词还能帮别人学东西 → OK;否则 → 作弊。详见 `references/research-boundary.md`。
2. **不能跳过 CHARACTERIZE 直接打**。先看事实再想方案,想当然是 CTF 最大的时间杀手。
3. **不能只试一条路走到黑**。第 4 步失败一次 → 回第 3 步更新假设表,换次高优先级继续。
4. **每道题 `attempts.md` 必须真实记录**。不是演戏给用户看 —— 是给未来的自己看。失败路径比成功路径更珍贵。
5. **通关后必须写 LESSON**。不写就不算通关。格式见 `references/lessons-writing-guide.md`。

## 容器环境说明

- Kali MCP 工具名一般是 `shell_exec`,工作目录是 `/tmp/workspace/`(持久化到单个容器生命周期内)
- 已装工具:`nmap nikto sqlmap msfconsole chisel bore python3 pwntools ROPgadget proxychains4 john hashcat curl wget`
- 缺失(需按需 `apt install`):`gcc gdb gdb-multiarch ltrace strace binwalk exiftool steghide ffuf gobuster ghidra radare2`
- 容器是 bridge 网络,能直接出公网;**接内网靶机**需要 bore 反向打通(见阶段 5)

## 七阶段 SOP(必读)

详细流程见 [`references/workflow.md`](references/workflow.md)。这里是索引:

| 阶段 | 动作简述 | 产出文件 |
|---|---|---|
| 1. BRIEF | 收题 + 查 LESSONS.md | `session.md` |
| 2. CHARACTERIZE | 只读侦察 | `facts.md` |
| 3. HYPOTHESIZE | 写 ≥2 候选攻击路径 | `hypotheses.md` |
| 4. EXECUTE | 试最高价值假设 + 日志化 | `attempts.md` |
| 5. PIVOT (可选) | 开 bore 隧道 | 公网端口 |
| 6. SUBMIT | 提交 flag 给用户 | 聊天回复 |
| 7. DEBRIEF | 写 LESSON + 清理 | `LESSONS.md` 新增条目 |

第 3→4 可以循环。第 5 不是每题都要做。

## 核心操作速查

### 启动一个新 session
```bash
# 每道题都先跑这个,建立工作区
shell_exec: bash <<'EOF'
mkdir -p /tmp/workspace/current && cd /tmp/workspace/current
# 把 scripts/session_init.py 的内容粘贴进去运行,参数是题目名
EOF
```
脚本文件:[`scripts/session_init.py`](scripts/session_init.py)

### 从用户给的 URL / tmpfiles.org 下载附件
```bash
shell_exec: curl -fsSL '<用户给的URL>' -o /tmp/workspace/current/artifacts/<filename>
```
详见 [`references/tool-tmpfiles.md`](references/tool-tmpfiles.md)

### 开隧道(需要时才用)
```bash
# Kali 内起 bore,把某端口穿到 bore.pub
shell_exec: bash scripts/bore_open.sh <local_port>
# 或者本机侧(在用户物理机上)做外网入口:等同语法
```
详见 [`references/tool-bore.md`](references/tool-bore.md)

### 记录一次尝试
```bash
# 每 executed 一次命令都要 append 一条
shell_exec: python3 scripts/attempt_add.py \
  --hypothesis "SQLi time-based" \
  --command "sqlmap -u ... --batch" \
  --result "❌ WAF blocks quote" \
  --conclusion "needs bypass, try hex encoding next"
```

### 写 LESSON(通关后强制)
这一步在**本地 AI 这端**用 Edit 工具直接改 `~/.claude/skills/ctf-autopwn/LESSONS.md`,不走容器。模板与规范见 [`references/lessons-writing-guide.md`](references/lessons-writing-guide.md)。

## 题目分类快速分流

按分类读对应的 reference,**不要**一次性把所有工具手册全塞进 context:

| 分类 | 读什么 |
|---|---|
| Pwn / Binary exploitation | [`tool-pwn.md`](references/tool-pwn.md) + [`tool-rev.md`](references/tool-rev.md) |
| Web | [`tool-web.md`](references/tool-web.md) + [`tool-recon.md`](references/tool-recon.md) |
| Crypto | [`tool-crypto.md`](references/tool-crypto.md) |
| Reverse engineering | [`tool-rev.md`](references/tool-rev.md) |
| Forensics / Steg | [`tool-forensics.md`](references/tool-forensics.md) |
| Misc / OSINT | [`tool-misc.md`](references/tool-misc.md) |

**在动手前先 grep [`LESSONS.md`](LESSONS.md)**:
```
shell_exec 或在本地:grep -A 5 -i "<关键特征>" LESSONS.md
```
历史经验比所有工具手册加起来都值钱。

## 失败 ≠ 卡住,只是信息多了

每次实验失败,你其实**学到了东西**:
- 某条路径被证伪 → 从假设表里划掉
- 得到了新观察 → 更新 `facts.md`
- 看到了错误信息 → 可能是下一条假设的入口

**正确心态**:`attempts.md` 里每条 ❌ 都让你离 flag 更近一步,而不是更远。

当你连试三个假设都失败、也想不出新假设时 —— **告诉用户**:
> "我已经证伪 3 条路径:[…]。观察到的事实:[…]。建议你给我一个提示,或者换题。"

不要瞎试。

## 复盘写作要求(重要)

`LESSONS.md` 是这个 skill 的核心资产。每条 lesson 必须包含三段:

1. **Signal** — 题目里什么特征让你最终想到这个技术?(未来 grep 用)
2. **Technique** — 核心打法 + 可复制粘贴的命令片段
3. **Pitfall** — 这次踩了什么坑,下次怎么避免

模板与好/坏范例见 [`references/lessons-writing-guide.md`](references/lessons-writing-guide.md)。

## 清理责任

通关或放弃后必须清理(`references/workflow.md` 第 7 阶段有 checklist):
- `pkill bore` 停所有隧道
- 如果题目数据敏感,删 `/tmp/workspace/current`
- 后台开的 nc / http.server / msfconsole 全部杀掉

留下的垃圾进程会影响下一道题的侦察结果。
