# 密码学工具速查

<!-- 目录 -->
<!-- 1. hashcat -->
<!-- 2. john -->
<!-- 3. RsaCtfTool -->
<!-- 4. openssl -->
<!-- 5. factordb -->
<!-- 6. pycryptodome -->
<!-- 7. 常见加密模式 -->
<!-- 8. 编码转换 -->

---

## 1. hashcat

hashcat 是最快的密码恢复工具,支持 GPU 加速。

### 基本使用

```bash
# 查看帮助
hashcat -h

# 查看示例
hashcat --example

# 查看设备
hashcat -I

# 基本语法
hashcat -m <hash_type> -a <attack_mode> <hash_file> <wordlist>
```

### Hash 类型 (-m)

| 类型值 | 算法 | 示例 |
|--------|------|------|
| 0 | MD5 | `8743b52063cd84097a65d1633f5c74fc` |
| 100 | SHA1 | `b89eaac7e614cc573fe9ecc5da463c80c8e4dd67` |
| 1400 | SHA256 | `2c70e12b7f1a6fb2c3a0c8cb1c7b9e3c0c6c7b1a4e8d7f6c5b4a3c2d1e0f9a8b7c` |
| 1700 | SHA512 | (512bit) |
| 3200 | bcrypt | `$2a$...` |
| 10000 | bcrypt | `$2b$...` |
| 13711 | VeraCrypt | 磁盘加密 |
| 99999 | Custom | 自定义 |

### 攻击模式 (-a)

| 模式值 | 名称 | 说明 |
|--------|------|------|
| 0 | Straight | 字典攻击 |
| 1 | Combination | 组合攻击 |
| 3 | Brute-force | 暴力破解 |
| 6 | Hybrid Wordlist + Mask | 字典+掩码 |
| 7 | Hybrid Mask + Wordlist | 掩码+字典 |

### 常用选项

```bash
# 字典攻击
hashcat -m 0 -a 0 hashes.txt wordlist.txt

# 暴力破解 (8位小写字母)
hashcat -m 0 -a 3 hashes.txt ?l?l?l?l?l?l?l?l

# 组合攻击
hashcat -m 0 -a 1 hashes.txt dict1.txt dict2.txt

# 规则攻击
hashcat -m 0 -a 0 hashes.txt wordlist.txt -r rules/best64.rule

# 恢复已停止的任务
hashcat --restore

# 显示结果
hashcat -m 0 -a 0 hashes.txt wordlist.txt --show

# 去除已破解的 hash
hashcat -m 0 -a 0 hashes.txt wordlist.txt --left

# 掩码字符集
# ?l = 小写字母
# ?u = 大写字母
# ?d = 数字
# ?s = 特殊字符
# ?a = 所有字符
# ?b = 0x00-0xff
```

### 常用掩码

```bash
# 8位小写
?l?l?l?l?l?l?l?l

# 8位数字
?d?d?d?d?d?d?d?d

# 8位混合 (小写+数字)
?h?h?h?h?h?h?h?h

# 长度范围 6-8
hashcat -a 3 -i --increment-min 6 --increment-max 8 hash.txt ?a?a?a?a?a?a?a?a

# 特定格式: 小写+数字 开头 + 符号 + 年份
?l?d?l?l?s19?d?d
```

### 状态码

| 状态码 | 含义 |
|--------|------|
| 0 | 全部完成 |
| 1 | 已暂停 |
| 2 | 已继续 |
| 3 | 已停止 |
| 4 | 已破解 |
| 5 | 未破解 |

---

## 2. john

john (John the Ripper) 是另一款流行的密码破解工具。

### 基本使用

```bash
# 查看帮助
john --help

# 查看格式
john --list=formats

# 基本破解
john --format=<format> --wordlist=<wordlist> <hash_file>

# 交互模式
john <hash_file>
# 按 'q' 退出, '空格' 显示状态
```

### 常用格式

```bash
# MD5
john --format=raw-md5 hashes.txt --wordlist=rockyou.txt

# SHA256
john --format=raw-sha256 hashes.txt --wordlist=rockyou.txt

# bcrypt
john --format=bcrypt hashes.txt --wordlist=rockyou.txt

# MySQL
john --format=mysql hashes.txt --wordlist=rockyou.txt

# 尝试自动检测
john hashes.txt --wordlist=rockyou.txt
```

### 显示结果

```bash
# 显示已破解的密码
john --show hashes.txt

# 显示特定格式
john --show --format=raw-md5 hashes.txt

# 显示进度
john --status <session_file>

# 恢复会话
john --restore
```

### 规则文件

```bash
# 使用规则
john --format=raw-md5 hashes.txt --wordlist=rockyou.txt --rules=single

# 常用规则
# single: 基于用户名/盐简单变换
# wordlist: 字典词的各种变形
# jumbo: 更多规则

# 自定义规则
john --format=raw-md5 hashes.txt --wordlist=rockyou.txt --rules=myrules
```

---

## 3. RsaCtfTool

RsaCtfTool 是专门用于 RSA 漏洞利用的工具。

### GitHub

```
https://github.com/RsaCtfTool/RsaCtfTool
```

### 安装

```bash
git clone https://github.com/RsaCtfTool/RsaCtfTool.git
cd RsaCtfTool
pip install -r requirements.txt
```

### 基本使用

```bash
# 解密 RSA
python3 RsaCtfTool.py --publickey pub.key --private private.key
python3 RsaCtfTool.py --publickey pub.key --uncipherfile cipher.txt

# 直接从 PEM 文件
python3 RsaCtfTool.py --attack publickey.pem

# 指定输出
python3 RsaCtfTool.py --publickey pub.key --private priv.key
```

### 常用攻击方法

```bash
# 直接求解 (当 e 很大或 d 很小时)
python3 RsaCtfTool.py --publickey pub.key --private priv.key --attack direct

# Wiener's Attack (当 d 很小)
python3 RsaCtfTool.py --publickey pub.key --attack wiener

# Boneh-Durfee Attack (当 d 接近 N^0.25)
python3 RsaCtfTool.py --publickey pub.key --attack boneh_durfee

# 共模攻击
python3 RsaCtfTool.py --publickey pub1.pem pub2.pem --shared

# Franklin-Reiter 相关消息攻击
python3 RsaCtfTool.py --publickey pub.key --attack fermat
```

### 自动攻击

```bash
# 自动尝试所有攻击方法
python3 RsaCtfTool.py --publickey pub.key --attack all

# 常用攻击组合
python3 RsaCtfTool.py --publickey pub.key --attack \
    wiener,boneh_durfee,fermat,factordb
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--publickey` | 公钥文件 |
| `--privatekey` | 私钥文件 |
| `--uncipherfile` | 密文文件 |
| `--uncipher` | 十六进制密文 |
| `--decrypt` | 解密文件 |
| `--attack` | 攻击方法 |
| `--ext` | 导出为其他格式 |

### 常见漏洞场景

```bash
# 1. e 太大 (e >= N)
# 使用 Boneh-Durfee

# 2. 低加密指数
python3 RsaCtfTool.py --publickey pub.key --attack low_exponent

# 3. 低解密指数 (Wiener)
python3 RsaCtfTool.py --publickey pub.key --attack wiener

# 4. 共模攻击
python3 RsaCtfTool.py --publickey key1.pem key2.pem --attack commonmodulus

# 5. 相同因子
python3 RsaCtfTool.py --publickey pub1.pem pub2.pem --attack samefactor

# 6. 模数不互素
python3 RsaCtfTool.py --publickey pub.key --attack nonprime
```

---

## 4. openssl

openssl 是强大的密码学工具集。

### 基本命令

```bash
# 查看版本和帮助
openssl version
openssl help

# 查看可用命令
openssl list -commands
openssl list -digest-commands
openssl list -cipher-commands
```

### Hash 计算

```bash
# MD5
openssl dgst -md5 file.txt
echo -n "text" | openssl dgst -md5

# SHA1
openssl dgst -sha1 file.txt

# SHA256
openssl dgst -sha256 file.txt

# 输出格式
openssl dgst -sha256 -hex file.txt  # 十六进制 (默认)
openssl dgst -sha256 -binary file.txt  # 二进制
```

### AES 加解密

```bash
# AES-128-CBC 加密
openssl enc -aes-128-cbc -in plain.txt -out cipher.bin -pass pass:password

# AES-128-CBC 解密
openssl enc -aes-128-cbc -d -in cipher.bin -out plain.txt -pass pass:password

# 常用参数
# -aes-128-cbc, aes-192-cbc, aes-256-cbc
# -aes-128-ecb, aes-192-ecb, aes-256-ecb
# -bf-cbc, -bf-ecb (Blowfish)
# -des, -des3 (3DES)

# base64 编码
openssl enc -aes-256-cbc -in plain.txt -a -pass pass:password
openssl enc -aes-256-cbc -d -a -in cipher.txt -pass pass:password
```

### RSA 操作

```bash
# 生成 RSA 密钥对
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# 查看公钥
openssl rsa -pubin -in public.pem -text -noout

# 查看私钥
openssl rsa -in private.pem -text -noout

# RSA 签名
openssl dgst -sha256 -sign private.pem -out signature.bin data.txt

# RSA 验证
openssl dgst -sha256 -verify public.pem -signature signature.bin data.txt

# RSA 加密/解密
openssl rsautl -encrypt -pubin -inkey public.pem -in data.txt -out encrypted.bin
openssl rsautl -decrypt -inkey private.pem -in encrypted.bin -out data.txt
```

### 证书操作

```bash
# 生成自签名证书
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365

# 查看证书信息
openssl x509 -in cert.pem -text -noout

# 验证证书
openssl verify -CAfile cert.pem cert.pem
```

---

## 5. factordb

factordb.com 是在线大数分解数据库。

### 在线查询

```
http://factordb.com/
```

### API 使用

```bash
# 查询 n 的分解
curl "http://factordb.com/listfactor.php?q=<number>&type=html"

# 获取已知因子
curl "http://factordb.com/listfactor.php?q=<number>"

# Python 示例
import requests

def factorize(n):
    url = f"http://factordb.com/listfactor.php?q={n}"
    resp = requests.get(url)
    # 解析响应获取因子
    return factors
```

---

## 6. pycryptodome

Python 密码学库,是 pycrypto 的分支。

### 安装

```bash
pip install pycryptodome
```

### RSA 示例

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, PKCS1_v1_5
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# 生成 RSA 密钥
key = RSA.generate(2048)
private_key = key.export_key()
public_key = key.publickey().export_key()

# 加载密钥
private_key_obj = RSA.import_key(private_key)
public_key_obj = RSA.import_key(public_key)

# 加密 (OAEP)
cipher = PKCS1_OAEP.new(public_key_obj)
ciphertext = cipher.encrypt(b'plaintext')

# 解密
cipher = PKCS1_OAEP.new(private_key_obj)
plaintext = cipher.decrypt(ciphertext)

# 加密 (v1.5)
cipher = PKCS1_v1_5.new(public_key_obj)
ciphertext, = cipher.encrypt(b'plaintext')

# 解密 (v1.5)
cipher = PKCS1_v1_5.new(private_key_obj)
sentinel = None  # 或 SHA256.new(b'message')
plaintext = cipher.decrypt(ciphertext, sentinel)

# 签名
h = SHA256.new(b'message')
signature = pkcs1_15.new(private_key_obj).sign(h)

# 验证
try:
    pkcs1_15.new(public_key_obj).verify(h, signature)
    print("OK")
except:
    print("FAIL")
```

### AES 示例

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

# 生成随机密钥和 IV
key = get_random_bytes(16)  # 128-bit
iv = get_random_bytes(16)   # 128-bit

# CBC 模式加密
cipher = AES.new(key, AES.MODE_CBC, iv)
ct_bytes = cipher.encrypt(pad(b'plaintext', AES.block_size))

# 解密
cipher = AES.new(key, AES.MODE_CBC, iv)
pt = unpad(cipher.decrypt(ct_bytes), AES.block_size)

# CTR 模式
from Crypto.Cipher import AES
from Crypto.Util.Counter import Counter

counter = Counter.new(128)
cipher = AES.new(key, AES.MODE_CTR, counter=counter)
ct = cipher.encrypt(b'plaintext')
```

### 常用哈希

```python
from Crypto.Hash import MD5, SHA1, SHA256, SHA512

# MD5
h = MD5.new()
h.update(b'Hello')
print(h.hexdigest())

# SHA256
h = SHA256.new()
h.update(b'Hello')
print(h.hexdigest())
```

---

## 7. 常见加密模式

### ECB (Electronic Codebook)

```
明文分成块,每块独立加密
相同明文块 -> 相同密文块
有明显的模式,不安全
```

### CBC (Cipher Block Chaining)

```
IV + 明文块1 XOR -> 加密 -> 密文块1
密文块1 + 明文块2 XOR -> 加密 -> 密文块2
...
需要一个随机 IV
```

### CTR (Counter)

```
计数器值加密 -> keystream
keystream XOR 明文 -> 密文
不需要padding,可并行
```

### GCM (Galois/Counter Mode)

```
CTR 模式 + 认证标签
提供加密和完整性保护
TLS 常用
```

---

## 8. 编码转换

### 进制转换

```bash
# 十六进制
echo "2a" | xxd -r -p     # hex -> binary
echo "2a" | xxd -p -r     # hex -> binary
echo -n "test" | xxd -p  # string -> hex

# Base64
echo -n "test" | base64          # string -> base64
echo -n "dGVzdA==" | base64 -d   # base64 -> string

# 十进制
echo "ibase=16; FF" | bc    # hex -> dec
echo "obase=16; 255" | bc  # dec -> hex
```

### Python 转换

```python
# 字符串转字节
s = "hello"
b = s.encode()           # b'hello'
b = s.encode('utf-8')

# 字节转字符串
b = b'hello'
s = b.decode()           # 'hello'
s = b.decode('utf-8')

# 整数
n = 255
hex_s = hex(n)           # '0xff'
n = int('0xff', 16)      # 255

# 字节组
import struct
# 打包
b = struct.pack('>I', 0x12345678)  # 大端 4 字节
b = struct.pack('<I', 0x12345678)  # 小端 4 字节

# 解包
n = struct.unpack('>I', b)[0]
```

---

## 常见密码学问题

### RSA 基础

```python
# RSA 加密: c = m^e mod n
# RSA 解密: m = c^d mod n
# d = e^-1 mod φ(n)
# φ(n) = (p-1)(q-1)
```

### 低加密指数广播攻击

```python
# 如果使用相同的低 e 和不同的 n 加密相同的消息 m
# 可以用中国剩余定理 (CRT) 解密
from sympy import crt

e = 3
cs = [c1, c2, c3]
ns = [n1, n2, n3]
m = crt(ns, cs)[0]
m = int(pow(m, 1/3, ns[0]*ns[1]*ns[2]))
```

### Coppersmith 定理

```python
# 当已知高位泄露 (d 上的 bits) 时
# 使用 SageMath 或 RsaCtfTool
```
