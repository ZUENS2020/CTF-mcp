#!/bin/bash
#===============================================================================
# 工具名称: bore_list.sh - 列出所有活跃 bore 隧道
# 使用方法: bash bore_list.sh
# 说明:     读取 /tmp/workspace/current/tunnels.log 和 ps aux 获取 bore 进程状态
# 输出格式: 每行显示 pid|local_port|remote|bore_process_status
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

# 确保工作目录和日志文件存在
if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo -e "${YELLOW}工作目录不存在: $WORKSPACE_DIR${NC}" >&2
    echo "请先运行 bore_open.sh 创建隧道"
    exit 0
fi

if [[ ! -f "$TUNNELS_LOG" ]]; then
    echo -e "${YELLOW}隧道日志文件不存在: $TUNNELS_LOG${NC}" >&2
    echo "还没有活跃的隧道"
    exit 0
fi

# 检查日志文件是否为空
if [[ ! -s "$TUNNELS_LOG" ]]; then
    echo -e "${YELLOW}没有活跃的隧道${NC}"
    exit 0
fi

# 获取所有 bore 进程
# 使用 ps 获取 PID 和命令信息
# 格式: PID, COMMAND
declare -A BORE_PROCESSES
while IFS= read -r line; do
    # 解析 ps 输出
    # ps aux 格式: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
    PID=$(echo "$line" | awk '{print $2}')
    # 检查是否是 bore 进程(排除 grep 自身)
    if echo "$line" | grep -q "bore local"; then
        BORE_PROCESSES["$PID"]="running"
    fi
done < <(ps aux | grep -E "[b]ore local" || true)

# 读取日志并显示隧道列表
echo -e "${GREEN}=== 活跃 Bore 隧道列表 ===${NC}"
echo ""
printf "%-10s %-12s %-25s %-10s\n" "PID" "LOCAL_PORT" "REMOTE" "STATUS"
printf "%-10s %-12s %-25s %-10s\n" "---" "----------" "------" "------"

# 临时文件存储已处理的 PID
PROCESSED_PIDS=()

while IFS='|' read -r timestamp pid local_port remote_url purpose; do
    # 跳过空行
    [[ -z "$pid" ]] && continue

    # 检查进程是否还在运行
    RUNNING=false
    for procpid in "${!BORE_PROCESSES[@]}"; do
        if [[ "$procpid" == "$pid" ]]; then
            RUNNING=true
            unset BORE_PROCESSES["$procpid"]
            break
        fi
    done

    if $RUNNING; then
        STATUS="${GREEN}running${NC}"
    else
        if kill -0 "$pid" 2>/dev/null; then
            STATUS="${GREEN}running${NC}"
        else
            STATUS="${RED}stopped${NC}"
        fi
    fi

    printf "%-10s %-12s %-25s %-10b\n" "$pid" "$local_port" "$remote_url" "$STATUS"

    PROCESSED_PIDS+=("$pid")
done < "$TUNNELS_LOG"

# 检查是否有孤儿 bore 进程(不在日志中但仍在运行)
ORPHAN_COUNT=0
for pid in "${!BORE_PROCESSES[@]}"; do
    if [[ "${BORE_PROCESSES[$pid]}" == "running" ]]; then
        ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
        # 尝试获取进程信息
        LOCAL_PORT=$(ps aux | grep -E "[b]ore local" | grep "$pid" | awk '{print $NF}' || echo "unknown")
        printf "%-10s %-12s %-25s %-10b\n" "$pid" "$LOCAL_PORT" "unknown" "${YELLOW}orphan${NC}"
    fi
done

echo ""
if [[ $ORPHAN_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}警告: 发现 $ORPHAN_COUNT 个不在日志中的孤儿 bore 进程${NC}"
    echo ""
fi

# 显示日志中的历史记录统计
TOTAL=$(wc -l < "$TUNNELS_LOG")
echo "日志中共有 $TOTAL 条隧道记录"

# 统计活跃数量
ACTIVE_COUNT=0
while IFS='|' read -r timestamp pid local_port remote_url purpose; do
    [[ -z "$pid" ]] && continue
    if kill -0 "$pid" 2>/dev/null; then
        ACTIVE_COUNT=$((ACTIVE_COUNT + 1))
    fi
done < "$TUNNELS_LOG"

echo "当前活跃: $ACTIVE_COUNT 条"

echo ""
echo "提示: 使用 bore_close.sh --pid <PID> 关闭指定隧道"
echo "      使用 bore_close.sh --all 关闭所有隧道"
