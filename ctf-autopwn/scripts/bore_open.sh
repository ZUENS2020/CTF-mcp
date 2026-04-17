#!/bin/bash
#===============================================================================
# 工具名称: bore_open.sh - 在 Kali 容器内打开 bore 隧道
# 使用方法: bash bore_open.sh <本地端口> [--port <远程端口>]
# 说明:     在后台启动 bore,解析输出 "listening at bore.pub:XXXXX"
#           写入日志: /tmp/workspace/current/tunnels.log
#           格式: timestamp|PID|local_port|remote_url|purpose
# 语法:     bore local <LOCAL_PORT> --to bore.pub [--port <REMOTE_PORT>]
# 返回:     pid=<PID> remote=<bore.pub:PORT> local=<PORT>
#===============================================================================

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志文件路径
TUNNELS_LOG="/tmp/workspace/current/tunnels.log"
WORKSPACE_DIR="/tmp/workspace/current"

# 检查是否为 root 用户运行 (bore 需要监听特权端口时可能需要)
# if [[ $EUID -ne 0 ]]; then
#     echo -e "${YELLOW}警告: 建议使用 root 用户运行以监听端口 < 1024${NC}" >&2
# fi

# 检查参数
if [[ $# -lt 1 ]]; then
    echo -e "${RED}错误: 缺少本地端口参数${NC}" >&2
    echo "使用方法: $0 <本地端口> [--port <远程端口>]" >&2
    exit 1
fi

LOCAL_PORT="$1"
REMOTE_PORT="${2:-}"  # 可选,指定远程 bore 服务器端口

# 验证端口号
if ! [[ "$LOCAL_PORT" =~ ^[0-9]+$ ]] || [[ "$LOCAL_PORT" -lt 1 ]] || [[ "$LOCAL_PORT" -gt 65535 ]]; then
    echo -e "${RED}错误: 无效的端口号: $LOCAL_PORT${NC}" >&2
    exit 1
fi

if [[ -n "$REMOTE_PORT" ]]; then
    if ! [[ "$REMOTE_PORT" =~ ^[0-9]+$ ]] || [[ "$REMOTE_PORT" -lt 1 ]] || [[ "$REMOTE_PORT" -gt 65535 ]]; then
        echo -e "${RED}错误: 无效的远程端口号: $REMOTE_PORT${NC}" >&2
        exit 1
    fi
fi

# 确保工作目录存在
mkdir -p "$WORKSPACE_DIR"

# 确保日志文件存在
touch "$TUNNELS_LOG"

# 检查 bore 是否安装
if ! command -v bore &> /dev/null; then
    echo -e "${RED}错误: bore 未安装或不在 PATH 中${NC}" >&2
    echo "请先安装 bore: cargo install bore-cli" >&2
    exit 1
fi

# 构造 bore 命令
# 语法: bore local <LOCAL_PORT> --to <BORE_SERVER> [--port <REMOTE_PORT>]
# 示例: bore local 4444 --to bore.pub
#       bore local 4444 --to bore.pub --port 42000
BORE_CMD=(bore local "$LOCAL_PORT" --to bore.pub)
if [[ -n "$REMOTE_PORT" ]]; then
    BORE_CMD+=(--port "$REMOTE_PORT")
fi

# 启动 bore (后台运行)
# 使用临时文件捕获输出
OUTPUT_FILE=$(mktemp)
BORE_PID=""

# 启动 bore 并后台运行
# 2>&1: 重定向 stderr 到 stdout
# | tee: 同时输出到文件和控制台
# disown: 从当前 shell 分离
nohup "${BORE_CMD[@]}" > "$OUTPUT_FILE" 2>&1 &
BORE_PID=$!
echo "Bore PID: $BORE_PID"

# 等待 bore 启动并解析输出
# 最多等待 30 秒
TIMEOUT=30
ELAPSED=0
INTERVAL=0.5
REMOTE_URL=""
BORE_LOCAL_PORT=""

while [[ $ELAPSED -lt $TIMEOUT ]]; do
    # 检查进程是否还在运行
    if ! kill -0 "$BORE_PID" 2>/dev/null; then
        # 进程已退出
        echo -e "${RED}错误: bore 进程意外退出${NC}" >&2
        echo "输出:" >&2
        cat "$OUTPUT_FILE" >&2
        rm -f "$OUTPUT_FILE"
        exit 1
    fi

    # 检查输出文件是否有新的监听信息
    # 期望格式: "listening at bore.pub:XXXXX"
    if grep -q "listening at" "$OUTPUT_FILE"; then
        # 解析远程 URL
        # 支持两种格式:
        # 1. listening at bore.pub:XXXXX
        # 2. listening at [::1]:XXXXX  (IPv6 本地)
        REMOTE_URL=$(grep "listening at" "$OUTPUT_FILE" | head -1 | sed -n 's/.*listening at \([^ ]*\).*/\1/p')

        # 检查是否是 bore.pub 地址
        if [[ "$REMOTE_URL" == "bore.pub:"* ]] || echo "$REMOTE_URL" | grep -qE 'bore\.pub:[0-9]+'; then
            # 格式已经是正确的
            :
        elif echo "$REMOTE_URL" | grep -qE ':[0-9]+$'; then
            # 可能是 IPv6 或其他格式,保持原样
            :
        fi

        # 从输出中提取 bore 实际监听的本地端口(如果可用)
        # 这个端口可能与指定的本地端口不同(如果端口被占用)
        break
    fi

    sleep $INTERVAL
    ELAPSED=$(echo "$ELAPSED + $INTERVAL" | bc)
done

# 再次检查进程状态
if ! kill -0 "$BORE_PID" 2>/dev/null; then
    echo -e "${RED}错误: bore 进程意外退出${NC}" >&2
    echo "输出:" >&2
    cat "$OUTPUT_FILE" >&2
    rm -f "$OUTPUT_FILE"
    exit 1
fi

# 如果还没获取到远程 URL,超时
if [[ -z "$REMOTE_URL" ]]; then
    echo -e "${RED}错误: 等待 bore 启动超时(${TIMEOUT}秒)${NC}" >&2
    echo "输出:" >&2
    cat "$OUTPUT_FILE" >&2
    # 清理进程
    kill "$BORE_PID" 2>/dev/null || true
    rm -f "$OUTPUT_FILE"
    exit 1
fi

# 从 REMOTE_URL 提取端口号
BORE_PORT=$(echo "$REMOTE_URL" | sed -n 's/.*:\([0-9]*\)$/\1/p')

# 获取当前时间戳
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 写入日志文件
# 格式: timestamp|PID|local_port|remote_url|purpose
echo "${TIMESTAMP}|${BORE_PID}|${LOCAL_PORT}|${REMOTE_URL}|pending" >> "$TUNNELS_LOG"

# 清理临时文件
rm -f "$OUTPUT_FILE"

# 输出结果
echo -e "${GREEN}bore 隧道已打开${NC}"
echo ""
echo -e "pid=${BORE_PID}"
echo -e "remote=${REMOTE_URL}"
echo -e "local=${LOCAL_PORT}"
echo ""
echo -e "${YELLOW}日志已写入: $TUNNELS_LOG${NC}"
echo ""
echo "提示: 使用 bore_list.sh 查看所有活跃隧道"
echo "      使用 bore_close.sh --pid $BORE_PID 关闭此隧道"
