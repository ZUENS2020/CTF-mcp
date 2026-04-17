#!/bin/bash
#===============================================================================
# 工具名称: bore_close.sh - 关闭 bore 隧道
# 使用方法:
#   bash bore_close.sh --port <PORT>    # 按本地端口关闭
#   bash bore_close.sh --pid <PID>      # 按 PID 关闭
#   bash bore_close.sh --all            # 关闭所有隧道
# 说明:     通过 PID 或端口号杀死 bore 进程
#           更新 tunnels.log 标记为已关闭
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

# 使用说明
usage() {
    echo "使用方法: $0 --port <PORT> | --pid <PID> | --all"
    echo ""
    echo "选项:"
    echo "  --port <PORT>   按本地端口关闭隧道"
    echo "  --pid <PID>     按 PID 关闭隧道"
    echo "  --all           关闭所有活跃隧道"
    echo ""
    echo "示例:"
    echo "  $0 --pid 12345"
    echo "  $0 --port 8080"
    echo "  $0 --all"
}

# 杀死进程并验证
kill_process() {
    local pid="$1"
    local pid_info="PID $pid"

    # 检查进程是否存在
    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}进程 $pid 不存在或已结束${NC}"
        return 1
    fi

    # 杀死进程
    # 首先尝试 SIGTERM(优雅终止)
    if kill -TERM "$pid" 2>/dev/null; then
        # 等待进程结束(最多 5 秒)
        for i in {1..10}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}已终止 $pid_info${NC}"
                return 0
            fi
            sleep 0.5
        done

        # 如果还没结束,强制杀死
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}进程未响应,强制杀死...${NC}"
            kill -9 "$pid" 2>/dev/null || true
            sleep 0.5
        fi

        if ! kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}已强制终止 $pid_info${NC}"
            return 0
        else
            echo -e "${RED}无法终止 $pid_info${NC}"
            return 1
        fi
    else
        echo -e "${RED}无法发送信号到 $pid_info${NC}"
        return 1
    fi
}

# 检查日志文件是否存在
if [[ ! -f "$TUNNELS_LOG" ]]; then
    echo -e "${RED}错误: 隧道日志文件不存在: $TUNNELS_LOG${NC}" >&2
    echo "请先运行 bore_open.sh 创建隧道" >&2
    exit 1
fi

# 解析参数
MODE=""
VALUE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            MODE="port"
            VALUE="$2"
            shift 2
            ;;
        --pid)
            MODE="pid"
            VALUE="$2"
            shift 2
            ;;
        --all)
            MODE="all"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

# 检查模式
if [[ -z "$MODE" ]]; then
    echo -e "${RED}错误: 未指定操作模式${NC}" >&2
    usage
    exit 1
fi

# 临时文件用于更新日志
TEMP_LOG=$(mktemp)

# 根据模式执行操作
CLOSED_COUNT=0
FAILED_COUNT=0

if [[ "$MODE" == "all" ]]; then
    echo -e "${GREEN}关闭所有活跃隧道...${NC}"
    echo ""

    while IFS='|' read -r timestamp pid local_port remote_url purpose; do
        [[ -z "$pid" ]] && continue

        # 只处理还在运行的进程
        if kill -0 "$pid" 2>/dev/null; then
            if kill_process "$pid"; then
                # 标记为已关闭
                echo "${timestamp}|${pid}|${local_port}|${remote_url}|closed" >> "$TEMP_LOG"
                CLOSED_COUNT=$((CLOSED_COUNT + 1))
            else
                # 保留原记录
                echo "${timestamp}|${pid}|${local_port}|${remote_url}|${purpose}" >> "$TEMP_LOG"
                FAILED_COUNT=$((FAILED_COUNT + 1))
            fi
        else
            # 进程已结束,标记为已关闭
            echo "${timestamp}|${pid}|${local_port}|${remote_url}|closed" >> "$TEMP_LOG"
        fi
    done < "$TUNNELS_LOG"

elif [[ "$MODE" == "pid" ]]; then
    echo -e "${GREEN}关闭 PID $VALUE ...${NC}"
    echo ""

    PID_TO_KILL="$VALUE"

    # 验证 PID 格式
    if ! [[ "$PID_TO_KILL" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 无效的 PID: $PID_TO_KILL${NC}" >&2
        exit 1
    fi

    # 在日志中查找对应的隧道
    FOUND=false
    while IFS='|' read -r timestamp pid local_port remote_url purpose; do
        [[ -z "$pid" ]] && continue

        if [[ "$pid" == "$PID_TO_KILL" ]]; then
            FOUND=true
            if kill_process "$pid"; then
                echo "${timestamp}|${pid}|${local_port}|${remote_url}|closed" >> "$TEMP_LOG"
                CLOSED_COUNT=$((CLOSED_COUNT + 1))
            else
                echo "${timestamp}|${pid}|${local_port}|${remote_url}|${purpose}" >> "$TEMP_LOG"
                FAILED_COUNT=$((FAILED_COUNT + 1))
            fi
        else
            echo "${timestamp}|${pid}|${local_port}|${remote_url}|${purpose}" >> "$TEMP_LOG"
        fi
    done < "$TUNNELS_LOG"

    if ! $FOUND; then
        echo -e "${YELLOW}在日志中未找到 PID $PID_TO_KILL${NC}"
        echo "尝试直接终止该进程..."
        if kill_process "$PID_TO_KILL"; then
            CLOSED_COUNT=1
        else
            FAILED_COUNT=1
        fi
    fi

elif [[ "$MODE" == "port" ]]; then
    echo -e "${GREEN}关闭本地端口 $VALUE 的隧道...${NC}"
    echo ""

    PORT_TO_CLOSE="$VALUE"

    # 验证端口格式
    if ! [[ "$PORT_TO_CLOSE" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 无效的端口号: $PORT_TO_CLOSE${NC}" >&2
        exit 1
    fi

    # 在日志中查找对应的隧道
    while IFS='|' read -r timestamp pid local_port remote_url purpose; do
        [[ -z "$pid" ]] && continue

        if [[ "$local_port" == "$PORT_TO_CLOSE" ]]; then
            if kill_process "$pid"; then
                echo "${timestamp}|${pid}|${local_port}|${remote_url}|closed" >> "$TEMP_LOG"
                CLOSED_COUNT=$((CLOSED_COUNT + 1))
            else
                echo "${timestamp}|${pid}|${local_port}|${remote_url}|${purpose}" >> "$TEMP_LOG"
                FAILED_COUNT=$((FAILED_COUNT + 1))
            fi
        else
            echo "${timestamp}|${pid}|${local_port}|${remote_url}|${purpose}" >> "$TEMP_LOG"
        fi
    done < "$TUNNELS_LOG"

    if [[ $CLOSED_COUNT -eq 0 ]]; then
        echo -e "${YELLOW}在日志中未找到端口 $PORT_TO_CLOSE 对应的隧道${NC}"
    fi
fi

# 更新日志文件
mv "$TEMP_LOG" "$TUNNELS_LOG"

# 输出结果
echo ""
echo "=== 操作结果 ==="
echo "关闭成功: $CLOSED_COUNT"
echo "关闭失败: $FAILED_COUNT"

if [[ $CLOSED_COUNT -gt 0 ]]; then
    echo ""
    echo -e "${GREEN}隧道已关闭${NC}"
    echo "提示: 使用 bore_list.sh 查看剩余隧道"
fi

if [[ $FAILED_COUNT -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}部分隧道可能需要手动清理,使用 bore_list.sh 查看状态${NC}"
fi
