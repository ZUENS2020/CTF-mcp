# bore 隧道用法

bore 是 Rust 写的 TCP 反向隧道(https://github.com/ekzhang/bore),Kali 镜像和用户物理机都建议装。

## 基本语法

### 客户端(在**要暴露服务**的机器上跑)

```bash
bore local <LOCAL_PORT> --to <BORE_SERVER>
```

- `<LOCAL_PORT>` — 本机要暴露的 TCP 端口
- `--to <BORE_SERVER>` — 公共 bore 服务器地址,默认 `bore.pub`

输出:
```
listening at bore.pub:37291
```

这里的 `37291` 是公网端口,任何人访问 `bore.pub:37291` 的 TCP 连接都会被转发到你本地的 `<LOCAL_PORT>`。

### 指定远端端口(可选)

```bash
bore local 4444 --to bore.pub --port 42000
```
失败会自动分配一个随机端口。

### 自建 bore server(可选,稳定性高于 bore.pub)

服务器:
```bash
bore server --min-port 40000 --max-port 42000
```

客户端:
```bash
bore local 4444 --to my.server.ip
```

## Kali 容器内使用

### 起隧道(后台)

使用脚本 `scripts/bore_open.sh`,它会:
1. 后台启动 bore
2. 等几秒解析出 `bore.pub:<remote_port>`
3. 写入 `/tmp/workspace/current/tunnels.log`
4. 返回 PID + 公网地址

```bash
# 在 Kali 容器里
bash /tmp/workspace/current/scripts/bore_open.sh 4444
# 输出: pid=123 public=bore.pub:37291 local=4444
```

### 列表

```bash
bash scripts/bore_list.sh
# 输出所有进行中的 bore,每行: pid local_port remote
```

### 关闭

```bash
bash scripts/bore_close.sh --port 4444      # 按本地端口
bash scripts/bore_close.sh --pid 123         # 按 PID
bash scripts/bore_close.sh --all             # 全杀
```

## 用户物理机使用

用户物理机**没有自动脚本**(skill 不能登陆用户机器),但语法一样:

```bash
# 用户在自己机器上跑
bore local 8080 --to bore.pub
# 把输出的 bore.pub:XXXXX 发给 AI
```

如果用户物理机没有 bore,提示他们安装:

```bash
# Linux / macOS(需要 Rust)
cargo install --locked bore-cli

# 或下 prebuilt(amd64 Linux)
curl -L https://github.com/ekzhang/bore/releases/latest/download/bore-v0.5.3-x86_64-unknown-linux-musl.tar.gz \
  | tar xz -C /usr/local/bin bore

# macOS
brew install ekzhang/tap/bore-cli
```

## 典型场景

### 场景 A — 接收反弹 shell
1. Kali 里起 nc:`nc -lvnp 4444`
2. Kali 里起 bore:`bash scripts/bore_open.sh 4444` → `bore.pub:37291`
3. 让远程靶机反弹到 `bore.pub:37291`(payload 里写这个)

### 场景 B — 暴露本地 HTTP 服务给远程爬虫
1. Kali 里:`python3 -m http.server 8000 &`
2. Kali 里:`bash scripts/bore_open.sh 8000` → `bore.pub:41234`
3. 触发远程靶机请求 `http://bore.pub:41234/payload`

### 场景 C — 把用户物理机的服务暴露到公网
(例:用户本机跑一个 fake SMTP,让远程靶机连进来)

1. 用户在自己机器上:`bore local 25 --to bore.pub`
2. 用户把输出的 `bore.pub:<port>` 发给 AI
3. AI 在 payload 里写这个地址

## 排错

**问题**:bore 说连上了但远程打不通
- 检查本地服务是否真的在监听 `0.0.0.0` 而不是 `127.0.0.1`
- `ss -ltnp | grep <port>` 看 bind 地址

**问题**:`bore local ... : connection refused`
- 本地端口上没服务,bore 本身只做转发不 listen

**问题**:bore.pub 抽风
- 换另一个 bore server,或者自建

**问题**:bore 断连重连,远程端口会变
- 对于长时间任务,写脚本监控 `tunnels.log` + 重启
- 或者自建 server 用 `--port` 固定端口

## 为什么不用 ngrok / cloudflare tunnel

- ngrok 需要注册 + 限连接数,不适合自动化
- cloudflare tunnel 需要托管域名,但我们已经有(见 `backend/app/api/config.py`)—— 如果 bore.pub 挂了,可作为 fallback,后续可扩展
- bore 纯 TCP,能跨任何协议(HTTP/ssh/smtp/custom),最通用
