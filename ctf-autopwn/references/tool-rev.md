# 逆向工程工具速查

<!-- 目录 -->
<!-- 1. Ghidra -->
<!-- 2. radare2 -->
<!-- 3. strings -->
<!-- 4. objdump -->
<!-- 5. ltrace/strace -->
<!-- 6. 常用反编译技术 -->

---

## 1. Ghidra

Ghidra 是 NSA 开发的免费逆向工程框架,支持反编译。

### 安装与启动

```bash
# 下载
https://github.com/NationalSecurityAgency/ghidra/releases

# 解压运行
./ghidraRun

# 或命令行
java -jar ghidra_xxx.jar
```

### 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| G | 跳转地址 |
| / | 搜索 |
| Ctrl+Shift+E | 字符串搜索 |
| Ctrl+F | 搜索当前函数 |
| Tab | 切换反汇编/反编译视图 |
| ; | 添加注释 |
| Ctrl+; | 添加 EEPROM |
| N | 重命名 |
| O | 跳转到交叉引用 |
| X | 跳转到交叉引用的引用 |
| P | 将数据转换为函数 |
| D | 将数据转换为字节/word/dword |
| U | 取消定义 |

### 反编译代码分析

```c
// 常用函数识别

// main 函数特征
int main(int argc, char** argv) { }

// 输入函数
scanf("%s", buf);
gets(buf);           // 危险: 无边界检查
fgets(buf, size, fp);

// 输出函数
printf();
puts();
putsn();

// 字符串操作
strcpy(dst, src);     // 危险: 无边界检查
strncpy(dst, src, n);
strcat(dst, src);    // 危险
strlen(s);

// 内存操作
memcpy(dst, src, n);
memset(s, c, n);

// 文件操作
fopen("file", "r");
fread(buf, size, n, fp);
fwrite(buf, size, n, fp);

// 数学运算
abs(), labs();
atoi(), atol(), atof();
```

### 常用脚本 (Java/Python)

```java
// 查找 main 函数
import ghidra.app.script.GhidraScript;

void run() throws Exception {
    // 查找 main
    Function main = getFunction("main");
    if (main != null) {
        println("main @ " + main.getEntryPoint());
    }
}
```

```python
# Ghidra Python 脚本
# 需要安装 ghidra_bridge

from ghidra_bridge import GhidraBridge

# 创建 bridge
bridge = GhidraBridge()

# 获取当前程序
program = bridge.getCurrentProgram()

# 查找函数
func = program.listing.getFunctionContaining(0x00401000)

# 获取反编译
decompiler = program.getDecompiler()
```

---

## 2. radare2

radare2 是开源的逆向工程框架,功能强大。

### 安装

```bash
# macOS
brew install radare2

# Ubuntu/Debian
sudo apt install radare2

# 或从源码编译
git clone https://github.com/radareorg/radare2
cd radare2
sys/install.sh
```

### 常用命令

```bash
# 打开文件
r2 ./binary
r2 -d ./binary          # 调试模式
r2 -A ./binary          # 自动分析
r2 -AA ./binary         # 深度分析

# 退出
q        # 退出
q!       # 强制退出
```

### 分析命令

| 命令 | 功能 |
|------|------|
| `aaa` | 分析所有 (等价于 -A) |
| `aac` | 分析函数调用 |
| `aaf` | 分析函数 |
| `aar` | 分析 references |
| `afl` | 列出函数 |
| `afll` | 列出函数(详细信息) |
| `afi` | 显示函数信息 |
| `afn <name> <addr>` | 重命名函数 |
| `ax <addr>` | 列出交叉引用 |
| `axt <addr>` | 查找谁引用了这个地址 |

### 显示命令

| 命令 | 功能 |
|------|------|
| `pdf` | 反汇编当前函数 |
| `pdc` | 反汇编(伪C) |
| `pd <n>` | 反汇编 n 条指令 |
| `px <n>` | 显示 hexdump n 字节 |
| `pxw` | 显示 32-bit words |
| `ps` | 显示字符串 |
| `pxq` | 显示 qword (64-bit) |
| `/ <pattern>` | 搜索 |
| `/R <pattern>` | 搜索ROP gadget |
| `/x <hex>` | 搜索十六进制 |
| `/c <cmd>` | 搜索命令 |

### 调试命令

| 命令 | 功能 |
|------|------|
| `dc` | 继续执行 |
| `dc <signal>` | 发送信号继续 |
| `ds` | 单步执行 (step) |
| `dsi` | 单步执行(跳过call) |
| `dso` | 单步执行(执行完函数) |
| `dr` | 显示寄存器 |
| `dr <reg>=<val>` | 修改寄存器 |
| `db <addr>` | 设置断点 |
| `db- <addr>` | 删除断点 |
| `dbt` | 显示栈帧 |
| `dmm` | 显示内存映射 |
| `dmp <addr> <size> <file>` | dump 内存 |

### 打印命令

| 命令 | 功能 |
|------|------|
| `px` | hexdump |
| `px 16` | 16 字节 hexdump |
| `pxw` | 32-bit word hexdump |
| `pxq` | 64-bit qword hexdump |
| `pd 10` | 反汇编 10 条指令 |
| `pdb 10` | 反汇编 10 条指令(basic block) |
| `pdf` | 反汇编当前函数 |
| `pdc` | 伪 C 代码 |

### 搜索

```bash
# 搜索字符串
/S "password"
/Si "Password"    # 忽略大小写

# 搜索十六进制
/x 414243         # 搜索 ABC

# 搜索二进制
/x 90 90          # 搜索 NOP NOP

# 搜索地址
/b <pattern>      # 搜索 asm

# 搜索ROP
/R pop            # 搜索 pop 指令
/R ret            # 搜索 ret 指令
```

### 写入

```bash
# 修改字节
wx <hex>          # 写入 hex
wa nop            # 写入 asm
wa jmp 0x8048...  # 写入 jmp

# 写入字符串
"w hello"         # 写入字符串

# 保存
w                 # 写入磁盘
```

### 附加

```bash
# 附加到进程
r2 -d pid

# 使用 gdb server
r2 -g 1234 ./binary  # 等价于 -d ./binary -g 1234
```

---

## 3. strings

strings 显示文件中的可打印字符串。

### 基本使用

```bash
# 基本用法
strings ./binary

# 显示字符串及其偏移
strings -t x ./binary    # 显示十六进制偏移
strings -t d ./binary    # 显示十进制偏移

# 最小长度
strings -n 8 ./binary    # 只显示长度 >= 8 的字符串

# 全部字符
strings -e s ./binary    # 7-bit
strings -e S ./binary    # 8-bit (默认)
strings -e l ./binary    # 16-bit little-endian
strings -e b ./binary    # 16-bit big-endian
strings -e L ./binary    # 32-bit

# 编码检测
strings -e ISO-8859-1 ./binary

# 在特定段中搜索
objdump -s -j .rodata ./binary
```

### 结合其他工具

```bash
# 过滤敏感关键词
strings ./binary | grep -i "password\|passwd\|secret\|key"

# 查找 URL
strings ./binary | grep -E "http://|https://|ftp://"

# 查找函数名
strings ./binary | grep -E "^_|^[a-zA-Z_][a-zA-Z0-9_]*$"

# 排序去重
strings ./binary | sort | uniq

# 统计出现次数
strings ./binary | sort | uniq -c | sort -rn | head
```

---

## 4. objdump

objdump 显示二进制文件信息。

### 基本使用

```bash
# 显示文件头
objdump -f ./binary

# 显示所有头
objdump -x ./binary

# 反汇编
objdump -d ./binary           # 反汇编所有
objdump -d ./binary -M intel  # Intel 语法

# 反汇编特定函数
objdump -d ./binary --start-address=0x8048... --stop-address=0x8049...

# 显示符号表
objdump -t ./binary

# 显示字符串
objdump -s -j .rodata ./binary

# 显示特定段
objdump -s -j .text ./binary

# 显示程序头
objdump -p ./binary

# 显示动态段
objdump -p ./binary | grep -A 20 "DYNAMIC"

# 检查保护
objdump -d ./binary | grep -i "exec\|stack\|reloc"
```

### 常用参数

| 参数 | 功能 |
|------|------|
| `-f` | 文件头 |
| `-h` | 节头 |
| `-x` | 所有头 |
| `-d` | 反汇编 |
| `-D` | 反汇编所有 |
| `-t` | 符号表 |
| `-T` | 动态符号表 |
| `-s` | 十六进制内容 |
| `-p` | 程序头 |
| `-M intel` | Intel 语法 |
| `-M att` | AT&T 语法 |
| `-C` | demangle C++ |

---

## 5. ltrace / strace

### ltrace (库调用追踪)

```bash
# 追踪库函数调用
ltrace ./program

# 指定函数
ltrace -e malloc+free ./program
ltrace -e "@libc.so*:+read+write" ./program

# 排除函数
ltrace -i ./program          # 显示指令指针
ltrace -f ./program          # 追踪 fork 的子进程
ltrace -t ./program          # 显示时间戳

# 统计调用次数
ltrace -c ./program

# 输出到文件
ltrace -o output.txt ./program

# 追踪参数
ltrace -S ./program          # 显示系统调用

# 附加到进程
ltrace -p PID
```

### strace (系统调用追踪)

```bash
# 追踪系统调用
strace ./program

# 常用选项
strace -i ./program          # 显示指令指针
strace -t ./program          # 显示时间戳
strace -T ./program          # 显示每次调用耗时
strace -f ./program          # 追踪子进程
strace -F ./program          # 也追踪 vfork

# 过滤
strace -e trace=read,write ./program    # 只跟踪 read/write
strace -e trace=file ./program         # 文件相关
strace -e trace=network ./program      # 网络相关
strace -e trace=signal ./program      # 信号相关
strace -e trace=ipc ./program         # 进程通信

# 输出
strace -o output.txt ./program        # 输出到文件
strace -s 1024 ./program              # 字符串最大长度

# 统计
strace -c ./program                   # 统计系统调用

# 附加到进程
strace -p PID

# 修改返回值
strace -E VAR=VAL ./program           # 设置环境变量
```

### 常用过滤表达式

```bash
# 系统调用
strace -e trace=execve ./program

# 文件操作
strace -e trace=open,openat,read,write,close ./program

# 网络
strace -e trace=socket,connect,send,recv ./program

# 内存
strace -e trace=brk,mmap,mprotect ./program

# 进程
strace -e trace=fork,execve,wait,exit ./program
```

---

## 6. 常用反编译技术

### x86/x64 寄存器约定

| 寄存器 | 用途 (cdecl) | 用途 (stdcall) |
|--------|--------------|----------------|
| eax | 返回值 | 返回值 |
| ebx | 通用 | 通用 |
| ecx | 通用 | 通用 |
| edx | 通用 | 通用 |
| esi | 源索引 | 通用 |
| edi | 目的索引 | 通用 |
| ebp | 帧指针 | 帧指针 |
| esp | 栈指针 | 栈指针 |

| amd64 寄存器 | 用途 |
|--------------|------|
| rax | 返回值, syscall number |
| rdi | 第1个参数 |
| rsi | 第2个参数 |
| rdx | 第3个参数 |
| r10 | 第4个参数 |
| r8 | 第5个参数 |
| r9 | 第6个参数 |
| rbx, r12-r15 | 通用 |

### 栈帧分析

```assembly
# 典型函数 prologue
push   ebp
mov    ebp, esp
sub    esp, 0x20        ; 分配栈空间

# 典型函数 epilogue
mov    esp, ebp
pop    ebp
ret

# 调用约定
# cdecl: 参数从右到左入栈,调用者清理栈
# stdcall: 参数从右到左入栈,被调用者清理栈
# fastcall: 参数在寄存器中传递

# amd64 调用约定 (System V)
# 参数顺序: rdi, rsi, rdx, rcx, r8, r9, 然后栈
```

### 常见反调试技术

```c
// 1. 检测调试器
if (ptrace(PTRACE_TRACEME, 0, 1, 0) == -1) {
    // 被调试
    exit(1);
}

// 2. 时间检测
time1 = get_time();
some_operation();
time2 = get_time();
if (time2 - time1 > threshold) {
    // 被单步或断点
}

// 3. 自检
code_segment_checksum();
if (checksum != expected) {
    // 被修改
}

// 4. 断点检测
// 检查 INT3 (0xCC)
for (i = 0; i < code_len; i++) {
    if (code[i] == 0xCC) {
        // 可能有断点
    }
}
```

### 常用混淆与解混淆

```python
# XOR 解密
def xor_decrypt(data, key):
    result = bytearray()
    for i, b in enumerate(data):
        result.append(b ^ key[i % len(key)])
    return bytes(result)

# Base64
import base64
decoded = base64.b64decode(data)

# ROT13
def rot13(s):
    result = []
    for c in s:
        if 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(c)
    return ''.join(result)
```

### 常用补丁技术

```assembly
# NOP 替换 (禁用指令)
90                ; x86 NOP
90 90 90 90 90    ; x86 多字节 NOP

# 跳转修改
# JZ -> JNZ
# 74 -> 75 (opcode 差 1)

# 修改返回值
# XOR EAX, EAX (使返回值为 0)
# 或 MOV EAX, 1 (使返回值为 1)
```

---

## 常用逆向分析流程

1. **信息收集**
   - `file` - 查看文件类型
   - `checksec` - 检查保护
   - `strings` - 查看字符串
   - `objdump -d` - 初步反汇编

2. **详细分析**
   - `radare2` / `Ghidra` - 深度分析
   - `strace` / `ltrace` - 动态追踪

3. **漏洞利用**
   - `ROPgadget` - 查找 gadgets
   - `one_gadget` - 查找 one_gadget
   - `pwntools` - 构建利用

4. **验证**
   - 动态调试
   - 编写 exploit
