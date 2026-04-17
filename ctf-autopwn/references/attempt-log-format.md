# CTF 尝试日志格式

本文档定义了在 CTF 挑战中记录尝试的标准格式。

---

## 基本原则

1. **每次尝试都要记录** - 即使是失败的尝试也有价值
2. **及时记录** - 不要依赖记忆,在尝试后立即记录
3. **清晰简洁** - 使用固定格式便于快速浏览和检索
4. **包含关键信息** - 命令、输出、结论都要有

---

## 文件结构

### 工作目录

```
/tmp/workspace/current/
├── session.md        # 主会话文件
├── facts.md          # 已知事实
├── hypotheses.md     # 假设与推测
├── attempts.md       # 尝试记录 (本文档定义)
├── notes/            # 额外笔记
├── artifacts/        # 下载的文件
└── tries/            # Exploit 尝试脚本
```

---

## attempts.md 格式

### 条目格式

```markdown
## Attempt @ YYYY-MM-DD HH:MM:SS

- **Hypothesis**: H1 / H2 / H3...
- **Command**: `实际执行的命令`
- **Result**: <关键输出或观察结果>
- **Conclusion**: ✅/❌/🔶 <从这次尝试中学到了什么>

---

```

### 字段说明

| 字段 | 说明 |
|------|------|
| `Hypothesis` | 对应的假设编号 (如 H1, H2) |
| `Command` | 实际执行的命令,使用反引号包裹 |
| `Result` | 命令的关键输出或观察结果 |
| `Conclusion` | 结论标记 + 学到的内容 |

### 结论标记

| 标记 | 含义 | 使用场景 |
|------|------|----------|
| ✅ | 成功 | 得到了预期结果,利用成功 |
| ❌ | 失败 | 操作未成功,方法不可行 |
| 🔶 | 部分成功/新发现 | 有进展但未完全成功,或发现新线索 |

---

## 示例条目

### 成功示例

```markdown
## Attempt @ 2024-03-15 14:30:22

- **Hypothesis**: H1 - 格式化字符串漏洞
- **Command**: `python3 exploit.py`
- **Result**: `Got libc address: 0x7ffff7a5a000`
- **Conclusion**: ✅ 成功泄露 libc 地址,可以使用onegadget

---
```

### 失败示例

```markdown
## Attempt @ 2024-03-15 14:35:10

- **Hypothesis**: H1 - 格式化字符串漏洞
- **Command**: `%p.%p.%p.%p.%p.%p.%p.%p.%p.%p`
- **Result**: `0x7ffeb5c9a2a0 0x7ffeb5c9a270 0x401a6 0x7ffeb5c9a540...`
- **Conclusion**: ❌ 程序没有格式化字符串漏洞,输出只是普通指针

---
```

### 部分成功示例

```markdown
## Attempt @ 2024-03-15 15:00:00

- **Hypothesis**: H2 - 栈溢出 + ROP
- **Command**: `python3 exploit.py DEBUG`
- **Result**: `EIP controlled: 0x42424242`
- **Conclusion**: 🔶 控制到 EIP,但 gadge 地址不对,需要重新计算偏移

---
```

---

## Hypotheses (假设) 格式

### hypotheses.md 格式

```markdown
# 假设与推测

## H1 - [简短描述]
- **问题**: 什么导致了这个现象?
- **假设**: 我的假设是什么?
- **验证方法**: 如何验证这个假设?
- **状态**: 🔵 待验证 / 🔶 验证中 / ✅ 已确认 / ❌ 已否定

---

## H2 - [简短描述]
- **问题**: ...
- **假设**: ...
- **验证方法**: ...
- **状态**: ...

---
```

### 示例

```markdown
## H1 - 格式化字符串可泄露内存
- **问题**: 输入 `%s` 时程序行为异常
- **假设**: 程序使用 printf(user_input) 没有格式化参数
- **验证方法**: 尝试输入 %p 或 %x
- **状态**: 🔶 验证中

---

## H2 - 存在栈溢出
- **问题**: 函数返回地址被覆盖
- **假设**: gets() 或 strcpy() 没有边界检查
- **验证方法**: 发送超长输入观察是否崩溃
- **状态**: ✅ 已确认
```

---

## Facts (事实) 格式

### facts.md 格式

```markdown
# 已知事实

## 环境信息
- **系统**: Ubuntu 20.04 x64
- **libc**: libc-2.31.so
- **架构**: x86-64

## 发现的信息
- **保护**: NX enabled, PIE enabled, Canary found
- **函数**: main, vuln, win
- **偏移**: libc leak @ 0x7f..., canary offset = 0x28

---
```

---

## 会话状态追踪

在 session.md 中维护状态:

```markdown
## 会话状态

- [ ] 信息收集完成
- [x] 初步分析完成
- [x] 漏洞点识别
- [ ] Exploit 开发
- [ ] Flag 获取
- [ ] 清理痕迹
```

---

## 最佳实践

1. **使用时间戳** - 便于追溯
2. **关联假设** - 每条记录关联到 H#
3. **记录关键输出** - 不要复制全部输出,只记录关键部分
4. **定期整理** - 完成一个阶段后回顾和总结
5. **备份** - 重要记录定期备份

---

## 快速添加尝试

使用 `attempt_add.py` 脚本快速添加:

```bash
python3 attempt_add.py \
    --hypothesis H1 \
    --command "python3 exploit.py" \
    --result "Got shell!" \
    --conclusion "✅ 成功"
```

---

## 日志审查清单

在结束会话前检查:

- [ ] 所有尝试都已记录
- [ ] 每条尝试都有 Hypothesis 关联
- [ ] 失败尝试也记录了学到的教训
- [ ] Facts 反映了最新的分析结果
- [ ] Hypotheses 状态已更新
