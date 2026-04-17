# Recon 工具速查

用于 Web / 网络题的信息收集阶段。**侦察阶段一律只读**,别触发写操作。

## nmap

```bash
# 快速端口探测(Top 1000)
nmap -T4 -Pn -sS <target>

# 全端口 + 版本 + 脚本
nmap -p- -sV -sC -T4 -Pn <target> -oN scan.txt

# UDP(慢,选常用端口)
nmap -sU --top-ports 50 -T4 <target>

# 目标是域名但只想解析不扫描
nmap -sL <target>
```

常用 flag:
- `-Pn` 跳过 ping(很多 CTF 靶机禁 ICMP)
- `-sC` 默认脚本集(含 http-title / smb-os-discovery 等)
- `-sV` 版本探测
- `-oN file` 人读格式,`-oX` XML(给 searchsploit 用)

## gobuster / ffuf(目录爆破)

```bash
# gobuster dir
gobuster dir -u http://target/ -w /usr/share/wordlists/dirb/common.txt \
    -x php,txt,bak,zip -t 40 -o gobuster.out

# ffuf(更快,更灵活)
ffuf -u http://target/FUZZ -w /usr/share/wordlists/dirb/common.txt \
    -mc 200,204,301,302,307,401,403 -t 50 -o ffuf.json

# 子域名
ffuf -u http://FUZZ.target.ctf/ -w /usr/share/wordlists/subdomains-top1million-5000.txt \
    -H "Host: FUZZ.target.ctf"
```

wordlists:
- `/usr/share/wordlists/dirb/common.txt` — 小而快
- `/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt` — 中等
- `/usr/share/seclists/Discovery/Web-Content/raft-medium-*.txt` — 需要 `apt install seclists`

## nikto

```bash
nikto -h http://target -o nikto.txt
```
噪音大但常能扫出 admin.php / .git / phpinfo 这类低挂果。

## whatweb / wappalyzer CLI

```bash
whatweb -a 3 http://target
# 输出:CMS / 框架 / 版本
```

## DNS / WHOIS

```bash
dig <domain> ANY +short
dig <domain> TXT        # 常藏提示
whois <domain>
host -t MX <domain>
```

## 网站基本 recon 组合拳

```bash
curl -sI http://target                     # headers
curl -s http://target/robots.txt
curl -s http://target/sitemap.xml
curl -s http://target/.git/HEAD            # git 泄露?
curl -s http://target/.env
curl -s http://target/server-status
```

## 安装(Kali 里缺的时候)

```bash
apt update && apt install -y gobuster ffuf nikto whatweb seclists dnsutils
```
