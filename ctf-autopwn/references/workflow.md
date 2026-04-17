# CTF 七阶段 SOP 详解

这份文件把 `SKILL.md` 里的表格展开成可执行的指令。**每一道题都走完整七步**(第 5 阶段可跳过),不要截弯取直。

---

## 阶段 1 — BRIEF(审题)

**目标**:把题目变成结构化 session。

### 输入
- 用户告知:题目分类、文件路径(本地 / URL / tmpfiles)、题目描述、平台、可能的 hint
- 用户告诉 AI 附件是哪个文件(本 skill 不猜)

### 动作

1. 在容器里建 session 目录:
   ```bash
   shell_exec: mkdir -p /tmp/workspace/current && cd /tmp/workspace/current && \
               mkdir -p artifacts tries notes
   ```

2. 用 `scripts/session_init.py` 生成 `session.md` 骨架(标题、分类、描述、附件清单、时间戳)

3. **grep 本地 LESSONS.md 找相似题**(在 AI 这端,不在容器):
   - 按题目关键词 / 分类 / 特征字符串搜
   - 命中的 Signal 要摘抄到 `session.md` 的 "相关经验" 段

4. 如果用户给的是 **tmpfiles.org URL**:
   ```bash
   shell_exec: bash scripts/tf_get.sh '<url>' /tmp/workspace/current/artifacts/<name>
   ```
   详见 [`tool-tmpfiles.md`](tool-tmpfiles.md)。

5. 如果用户直接给了公网 URL(GitHub、题目平台静态资源),直接 `curl -fsSL -o` 下来

### 产出
- `/tmp/workspace/current/session.md` — 题目档案
- `/tmp/workspace/current/artifacts/` — 题目原始附件
- 相关 LESSONS 摘要(写在 session.md 里)

### 禁止
- 跳过 LESSONS 查询。**多数中档题有历史经验可抄**。

---

## 阶段 2 — CHARACTERIZE(摸底)

**目标**:采集所有事实,不做任何猜测。

### 为什么重要
新手的典型错误:看到题目分类是 "pwn" 就立刻 `pwntools` 上去写 payload。结果后来发现二进制是 32-bit static,没 PIE,有栈保护,白忙了一下午。**先观察后动手** 永远更快。

### 分类侦察清单

**二进制类(pwn / rev)**:
```bash
file <binary>                          # 架构、链接方式、stripped?
checksec --file=<binary>               # NX/PIE/Canary/RELRO
strings -n 8 <binary> | head -50       # 字面量,有时直接藏 flag
nm <binary> 2>/dev/null | head -30     # 符号表
ldd <binary>                           # 动态库
./<binary> < /dev/null 2>&1 | head     # 观察正常行为
```

**Web 类(远程 URL 已知)**:
```bash
curl -sI <url>                         # Headers: Server、X-Powered-By、CSP、cookies
curl -s <url> | head -100              # 源码
curl -sL <url>/robots.txt
curl -sL <url>/sitemap.xml
# 登录页?找默认凭证?静态资源路径?
ffuf -u <url>/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302,401,403
# (需要先 apt install ffuf)
```

**Crypto**:
```bash
# 看附件是 PEM 公钥?RSA 参数 JSON?密文是 base64/hex?
file <artifact>
cat <artifact> | head
# RSA 参数:RsaCtfTool.py -n N -e E --uncipher C
# Hash:hashid '<hash>'
```

**Forensics**:
```bash
file <artifact>
exiftool <artifact>                    # 需要 apt install libimage-exiftool-perl
binwalk <artifact>                     # 需要 apt install binwalk
strings -n 8 <artifact> | grep -iE 'flag|ctf|key|pass'
```

### 事实写进 `facts.md`

格式:
```markdown
# Facts

## 文件信息
- binary: ELF 64-bit, dynamically linked, not stripped
- checksec: NX enabled, PIE disabled, no canary, partial RELRO

## 运行观察
- 打印 "Welcome", 读一行输入, strcmp 后退出
- 输入 >= 32 字节时 crash(SIGSEGV at 0x400723)

## 字符串里的线索
- "admin:Sup3rS3cret" 疑似后门
- 发现函数 win() 在 0x400650
```

**不要在这一步写攻击方案**。攻击方案是下一步的事。

---

## 阶段 3 — HYPOTHESIZE(假设生成)

**目标**:把事实翻译成 ≥2 条可尝试的攻击路径。

### 为什么需要显式化
如果没有显式列出候选,AI 容易死抓一条路不放。把它们写成列表后,失败时能**明确切到下一条**,而不是"再试一下这个参数"。

### `hypotheses.md` 模板

```markdown
# Hypotheses

Last updated: 2026-04-17 14:30

## H1 (rank: 1, cost: low, confidence: medium) — ret2win via win()
- 依据:win() 在 0x400650,NX on 但无 canary,32 字节溢出已复现
- 实验:send 40 bytes junk + p64(0x400650) → 看 stdout 有没有 flag
- 证伪条件:输出无 flag 且 retaddr 没到 0x400650

## H2 (rank: 2, cost: low, confidence: medium) — 后门凭证 "admin:Sup3rS3cret"
- 依据:strings 里的疑似凭证
- 实验:把这串作为输入喂进去
- 证伪条件:程序拒绝或无变化

## H3 (rank: 3, cost: high, confidence: low) — format string
- 依据:输入直接进 printf?未验证
- 实验:送 %x%x%x 看栈泄露
- 证伪条件:无泄露迹象
```

### 排序规则

- **Cost**:需要多少时间 / 网络 / 外部依赖
- **Confidence**:事实支持度(几个证据指向它?)
- **Rank 1 = Confidence / Cost 最大化**

先试第 1 个。失败了再回来更新排名,再试下一个。

---

## 阶段 4 — EXECUTE(实验)

**目标**:试当前 H1,把过程日志化。

### 执行循环

```
while 还有未证伪的假设:
    取 rank 1
    执行实验
    attempt_add.py 记录命令 + 输出 + 结论
    if 证伪:
        从 hypotheses.md 划掉
        if 产生了新事实:
            更新 facts.md
            回阶段 3 重排假设
        else:
            直接取下一个 rank
    elif 验证成功:
        break → 阶段 6
```

### 写 `attempts.md`(用 `scripts/attempt_add.py`)

每条 entry 四字段:
- `hypothesis` — 对应哪个 H
- `command` — 精确命令(复制粘贴就能重现)
- `result` — 输出 / 现象(截取关键部分)
- `conclusion` — ✅ 验证 / ❌ 证伪 / 🔶 未结论 + 下一步

```
python3 /tmp/workspace/current/scripts/attempt_add.py \
    --hypothesis H1 \
    --command "python3 -c \"print('A'*40 + '\x50\x06\x40\x00...')\" | ./chall" \
    --result "Segfault at 0x4006xx, no flag output" \
    --conclusion "❌ offset 有误,栈上位置不是 40;回炉测偏移"
```

### 如果连着 3 个假设全证伪

- 重新跑一遍 CHARACTERIZE,看有没有漏掉的事实
- 搜 LESSONS.md 同类题的 Pitfall 段
- 如果还是没辙 → 停下来告诉用户,不要编答案

---

## 阶段 5 — PIVOT(条件触发:开隧道)

**这一步不是每道题都要做**。触发场景:

- 需要接收远程靶机 / 题目平台的回连(reverse shell、OOB exfil)
- 需要把 Kali 里跑的服务暴露到公网(比如让题目平台的爬虫 / SSRF 访问)
- 需要把**用户物理机上**的本地服务暴露到公网(比如本地跑的 fake SMTP 服务器,让远程靶机来连)

### 在 Kali 容器里起 bore

```bash
shell_exec: bash /tmp/workspace/current/scripts/bore_open.sh 4444
# 输出:PID=123  remote=bore.pub:42137
```
脚本会 daemonize bore 并写 PID + 远程端口到 `tunnels.log`。

### 在用户物理机上起 bore

如果是物理机侧有服务要暴露(比如用户本地跑 `python -m http.server 8080`),让用户在自己物理机执行:
```bash
bore local 8080 --to bore.pub
# 记下输出的 bore.pub:<port>,回传给 AI
```

### 完整语法 / 管理 / 排错

详见 [`tool-bore.md`](tool-bore.md)。

### 产出
- `tunnels.log` 里一行:`timestamp | pid | local_port | bore.pub:remote_port | purpose`
- 记到 `attempts.md` 的上下文里

---

## 阶段 6 — SUBMIT(交旗)

**目标**:告诉用户候选 flag + 推理链 + 置信度。

### 回复模板

```
✅ 候选 flag: `flag{r3t2w1n_1s_fun}`
置信度: 高
推理:
1. 二进制有 win() 在 0x400650
2. 偏移 40 字节时 ret 到 win() 成功(attempts.md#5)
3. win() 直接 cat /flag 打印到 stdout
4. 实测输出里出现该字符串

如果不对,请告诉我平台返回的错误提示。
```

### 置信度标定

| 等级 | 含义 |
|---|---|
| 高 | 直接看到 flag 明文 + 格式正确 |
| 中 | 构造出来但没实机验证(例:exploit 本地 pop shell,远程未测) |
| 低 | 靠猜 / 部分输出拼接 |

**不要虚报置信度**。用户会拿去交,交错受罚。

### 失败了怎么办

用户回「不对」→ 回到阶段 3,把失败的 flag 结构当新事实写进 `facts.md`("平台不接受 X 格式"),重排假设。不要只是换个变体硬塞。

---

## 阶段 7 — DEBRIEF(复盘 + 清理)

### 写 LESSON(强制)

**只有当 flag 被用户确认正确后**才能写 lesson。失败的题也可以写,但标题打 `[UNSOLVED]`。

用 Edit 工具直接追加到 `~/.claude/skills/ctf-autopwn/LESSONS.md`,按 [`lessons-writing-guide.md`](lessons-writing-guide.md) 的格式。

三段内容(Signal / Technique / Pitfall)全要有,每段至少 2 句话。

### 清理 checklist

```bash
# 1) 杀隧道
shell_exec: pkill -f 'bore local' || true

# 2) 杀可能残留的后台服务
shell_exec: pkill -f 'http.server' || true
shell_exec: pkill -x nc || true
shell_exec: pkill -f 'msfconsole' || true

# 3) 如果题目附件敏感,删 workspace
shell_exec: rm -rf /tmp/workspace/current  # 按需

# 4) 确认干净
shell_exec: ps auxf | grep -E 'bore|http.server|nc |msf' | grep -v grep || echo "clean"
```

### 会话结束前回报用户

```
✅ flag 已提交并确认。
- Lesson 已写入(Signal: "二进制 pwn + 暴露 win 函数 + 偏移未知")
- 隧道已关闭
- 背景进程已清理
```

---

## 附:常见陷阱清单

这些是已知会让人浪费时间的地方,动手前扫一眼:

- [ ] 远程靶机和本地 libc 版本不同 → 先泄露 libc 再写 ROP
- [ ] Web 题的 flag 常在 `/flag` 或环境变量 `FLAG`,不一定在数据库
- [ ] Crypto 题的 N 不一定是两个素数乘积,试 `factordb` / `Fermat` / `Wiener`
- [ ] PNG 末尾后的数据,`binwalk -e` 常漏,用 `foremost` 或手动 `dd` 切
- [ ] 有些 jail(pyjail / bash jail)限制导入但可用 `__import__` / `exec` 的字节码
- [ ] 题目描述每个字都是提示,包括赛题标题
