#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  1) 本机一键下发到远端（推荐）
     ./scripts/setup_ctf_server.sh \
       --host 14.1.99.251 \
       --password '你的root密码' \
       --token 'frp-token' \
       --api-base 'https://api.example.com' \
       --update-setting

  2) 直接在远端服务器本机执行
     sudo bash ./scripts/setup_ctf_server.sh \
       --local \
       --token 'frp-token'

参数：
  --host <ip_or_domain>        远端主机（本机下发模式必填）
  --ssh-user <user>            SSH 用户，默认 root
  --password <password>        SSH 密码（本机下发模式必填）
  --token <token>              frps token（必填）
  --frps-port <port>           frps 监听端口，默认 7000
  --file-port <port>           nginx 文件服务端口，默认 80
  --file-root <path>           文件根目录，默认 /srv/ctf-files
  --api-base <url>             可选，回写 setting.md 的 Api_Base
  --update-setting             将 FRP_Address/FRP_token/File_Base/Api_Base 回写到项目 setting.md
  --local                      在服务器本机直接执行，不走 ssh/expect
  -h, --help                   显示帮助
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "缺少命令: $1" >&2
    exit 1
  }
}

HOST=""
SSH_USER="root"
PASSWORD=""
TOKEN=""
FRPS_PORT="7000"
FILE_PORT="80"
FILE_ROOT="/srv/ctf-files"
API_BASE=""
UPDATE_SETTING="0"
LOCAL_MODE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --ssh-user) SSH_USER="${2:-}"; shift 2 ;;
    --password) PASSWORD="${2:-}"; shift 2 ;;
    --token) TOKEN="${2:-}"; shift 2 ;;
    --frps-port) FRPS_PORT="${2:-}"; shift 2 ;;
    --file-port) FILE_PORT="${2:-}"; shift 2 ;;
    --file-root) FILE_ROOT="${2:-}"; shift 2 ;;
    --api-base) API_BASE="${2:-}"; shift 2 ;;
    --update-setting) UPDATE_SETTING="1"; shift 1 ;;
    --local) LOCAL_MODE="1"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$TOKEN" ]] || { echo "--token 必填" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SETTING_FILE="$REPO_ROOT/setting.md"

run_remote_install() {
  local target_host="$1"
  local ssh_user="$2"
  local ssh_password="$3"
  local token="$4"
  local frps_port="$5"
  local file_port="$6"
  local file_root="$7"

  require_cmd expect

  local local_tmp
  local remote_tmp="/tmp/ctf_server_setup.$$.$RANDOM.sh"
  local_tmp="$(mktemp)"

  cat >"$local_tmp" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y --no-install-recommends nginx curl ca-certificates tar

FRP_VER=0.61.1
ARCH=linux_amd64
TMP_DIR=\$(mktemp -d)
cd "\$TMP_DIR"
curl -fsSL -o frp.tar.gz "https://github.com/fatedier/frp/releases/download/v\${FRP_VER}/frp_\${FRP_VER}_\${ARCH}.tar.gz"
tar -xzf frp.tar.gz
install -m 0755 "frp_\${FRP_VER}_\${ARCH}/frps" /usr/local/bin/frps

mkdir -p /etc/frp
cat >/etc/frp/frps.toml <<'TOML'
bindPort = ${frps_port}

auth.method = "token"
auth.token = "${token}"

transport.tcpMux = false
TOML

cat >/etc/systemd/system/frps.service <<'UNIT'
[Unit]
Description=frp server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable frps
systemctl restart frps

mkdir -p "${file_root}"
chmod 755 "${file_root}"

cat >/etc/nginx/sites-available/ctf-files <<'NGINX'
server {
    listen ${file_port} default_server;
    listen [::]:${file_port} default_server;
    server_name _;

    location = /healthz_files {
        add_header Content-Type text/plain;
        return 200 'ok';
    }

    location /files/ {
        alias ${file_root}/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        add_header Cache-Control "no-store";
    }
}
NGINX

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/ctf-files /etc/nginx/sites-enabled/ctf-files
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "===PORTS==="
ss -lntp | egrep ":(22|${file_port}|${frps_port})\\b" || true
echo "===FRPS==="
systemctl --no-pager --full status frps | sed -n '1,20p'
echo "===NGINX==="
systemctl --no-pager --full status nginx | sed -n '1,20p'
echo "===HEALTH==="
curl -fsS "http://127.0.0.1:${file_port}/healthz_files" && echo

rm -rf "\$TMP_DIR"
EOF
  chmod +x "$local_tmp"

  expect <<EOF
set timeout 300
spawn scp -o StrictHostKeyChecking=accept-new "$local_tmp" ${ssh_user}@${target_host}:${remote_tmp}
expect "password:"
send "${ssh_password}\r"
expect eof

spawn ssh -o StrictHostKeyChecking=accept-new ${ssh_user}@${target_host} "bash ${remote_tmp} && rm -f ${remote_tmp}"
expect "password:"
send "${ssh_password}\r"
expect eof
EOF

  rm -f "$local_tmp"
}

run_local_install() {
  local token="$1"
  local frps_port="$2"
  local file_port="$3"
  local file_root="$4"

  [[ "$(id -u)" -eq 0 ]] || { echo "--local 模式需 root 执行" >&2; exit 1; }

  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends nginx curl ca-certificates tar

  local frp_ver="0.61.1"
  local arch="linux_amd64"
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  cd "$tmp_dir"
  curl -fsSL -o frp.tar.gz "https://github.com/fatedier/frp/releases/download/v${frp_ver}/frp_${frp_ver}_${arch}.tar.gz"
  tar -xzf frp.tar.gz
  install -m 0755 "frp_${frp_ver}_${arch}/frps" /usr/local/bin/frps

  mkdir -p /etc/frp
  cat >/etc/frp/frps.toml <<EOF
bindPort = ${frps_port}

auth.method = "token"
auth.token = "${token}"

transport.tcpMux = false
EOF

  cat >/etc/systemd/system/frps.service <<'EOF'
[Unit]
Description=frp server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable frps
  systemctl restart frps

  mkdir -p "$file_root"
  chmod 755 "$file_root"
  cat >/etc/nginx/sites-available/ctf-files <<EOF
server {
    listen ${file_port} default_server;
    listen [::]:${file_port} default_server;
    server_name _;

    location = /healthz_files {
        add_header Content-Type text/plain;
        return 200 'ok';
    }

    location /files/ {
        alias ${file_root}/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        add_header Cache-Control "no-store";
    }
}
EOF
  rm -f /etc/nginx/sites-enabled/default
  ln -sf /etc/nginx/sites-available/ctf-files /etc/nginx/sites-enabled/ctf-files
  nginx -t
  systemctl enable nginx
  systemctl restart nginx

  rm -rf "$tmp_dir"
}

update_setting_file() {
  local host="$1"
  local token="$2"
  local file_port="$3"
  local api_base="$4"
  local file_base=""

  if [[ "$file_port" == "80" ]]; then
    file_base="http://${host}/files"
  else
    file_base="http://${host}:${file_port}/files"
  fi

  [[ -f "$SETTING_FILE" ]] || touch "$SETTING_FILE"

  _sed_inplace() {
    local expr="$1"
    local file="$2"
    if sed --version >/dev/null 2>&1; then
      sed -i "$expr" "$file"
    else
      sed -i '' "$expr" "$file"
    fi
  }

  if grep -q '^FRP_Address:' "$SETTING_FILE"; then
    _sed_inplace "s#^FRP_Address:.*#FRP_Address: ${host}#" "$SETTING_FILE"
  else
    echo "FRP_Address: ${host}" >>"$SETTING_FILE"
  fi

  if grep -q '^FRP_token:' "$SETTING_FILE"; then
    _sed_inplace "s#^FRP_token:.*#FRP_token: ${token}#" "$SETTING_FILE"
  else
    echo "FRP_token: ${token}" >>"$SETTING_FILE"
  fi

  if grep -q '^File_Base:' "$SETTING_FILE"; then
    _sed_inplace "s#^File_Base:.*#File_Base: ${file_base}#" "$SETTING_FILE"
  else
    echo "File_Base: ${file_base}" >>"$SETTING_FILE"
  fi

  if [[ -n "$api_base" ]]; then
    if grep -q '^Api_Base:' "$SETTING_FILE"; then
      _sed_inplace "s#^Api_Base:.*#Api_Base: ${api_base}#" "$SETTING_FILE"
    else
      echo "Api_Base: ${api_base}" >>"$SETTING_FILE"
    fi
  fi
}

if [[ "$LOCAL_MODE" == "1" ]]; then
  run_local_install "$TOKEN" "$FRPS_PORT" "$FILE_PORT" "$FILE_ROOT"
  echo "本机模式配置完成。"
  exit 0
fi

[[ -n "$HOST" ]] || { echo "--host 必填（非 --local 模式）" >&2; exit 1; }
[[ -n "$PASSWORD" ]] || { echo "--password 必填（非 --local 模式）" >&2; exit 1; }

run_remote_install "$HOST" "$SSH_USER" "$PASSWORD" "$TOKEN" "$FRPS_PORT" "$FILE_PORT" "$FILE_ROOT"

if [[ "$UPDATE_SETTING" == "1" ]]; then
  update_setting_file "$HOST" "$TOKEN" "$FILE_PORT" "$API_BASE"
  echo "已更新 setting.md: $SETTING_FILE"
fi

echo "完成。"
echo "FRPS: ${HOST}:${FRPS_PORT}"
echo "文件服务: http://${HOST}:${FILE_PORT}/files/"
