#!/bin/bash
#===============================================================================
# 工具名称: tf_get.sh - 从 tmpfiles.org 下载文件
# 使用方法: bash tf_get.sh <tmpfiles_url> [output_path]
# 说明:     处理 URL 转换: tmpfiles.org/XXXXX/file -> tmpfiles.org/dl/XXXXX/file
# 使用 curl -fsSL 进行下载
#===============================================================================

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查参数
if [[ $# -lt 1 ]]; then
    echo -e "${RED}错误: 缺少URL参数${NC}" >&2
    echo "使用方法: $0 <tmpfiles_url> [output_path]" >&2
    exit 1
fi

TMPFILES_URL="$1"
OUTPUT_PATH="${2:-}"  # 如果未指定,则为空

# 验证 URL 格式
# 期望格式: https://tmpfiles.org/XXXX/file 或 https://tmpfiles.org/dl/XXXX/file
if ! echo "$TMPFILES_URL" | grep -qE 'https://tmpfiles\.org/[^/]+/[^/]+'; then
    echo -e "${RED}错误: 无效的 tmpfiles.org URL 格式${NC}" >&2
    echo "URL: $TMPFILES_URL" >&2
    exit 1
fi

# 将展示页 URL 转换为直链
# 展示页: https://tmpfiles.org/XXXX/file
# 直链:   https://tmpfiles.org/dl/XXXX/file
# 直链格式已经是 dl/ 开头的则不需要转换
if echo "$TMPFILES_URL" | grep -q '/dl/'; then
    # 已经是直链格式
    DOWNLOAD_URL="$TMPFILES_URL"
else
    # 需要转换
    # 从 URL 中提取 ID 和文件名
    # 格式: https://tmpfiles.org/XXXX/file -> https://tmpfiles.org/dl/XXXX/file
    DOWNLOAD_URL=$(echo "$TMPFILES_URL" | sed 's|tmpfiles\.org/|tmpfiles.org/dl/|')
fi

# 确定输出文件名
if [[ -z "$OUTPUT_PATH" ]]; then
    # 从 URL 中提取文件名
    FILENAME=$(basename "$DOWNLOAD_URL")
    OUTPUT_PATH="$FILENAME"
fi

# 如果输出路径是目录,则添加文件名
if [[ -d "$OUTPUT_PATH" ]]; then
    FILENAME=$(basename "$DOWNLOAD_URL")
    OUTPUT_PATH="$OUTPUT_PATH/$FILENAME"
fi

# 获取文件名(用于显示)
FILENAME=$(basename "$OUTPUT_PATH")

# 显示下载信息
echo -e "${GREEN}开始下载...${NC}"
echo "来源: $DOWNLOAD_URL"
echo "目标: $OUTPUT_PATH"
echo ""

# 下载文件
# -f: 失败时返回 HTTP 错误码
# -s: 静默模式
# -S: 显示错误
# -L: follow 重定向
# -o: 输出文件
ERROR_MSG=$(curl -fsSL \
    --max-time 120 \
    -o "$OUTPUT_PATH" \
    "$DOWNLOAD_URL" 2>&1)

if [[ $? -ne 0 ]]; then
    echo -e "${RED}错误: 下载失败${NC}" >&2
    echo "$ERROR_MSG" >&2
    exit 1
fi

# 检查文件是否下载成功
if [[ ! -f "$OUTPUT_PATH" ]]; then
    echo -e "${RED}错误: 文件未创建${NC}" >&2
    exit 1
fi

# 检查文件大小
FILE_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
echo -e "${GREEN}下载完成!${NC}"
echo "文件名: $FILENAME"
echo "文件大小: $FILE_SIZE"
