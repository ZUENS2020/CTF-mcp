#!/bin/bash
#===============================================================================
# 工具名称: tf_up.sh - 上传文件到 tmpfiles.org
# 使用方法: bash tf_up.sh /path/to/file
# 输出:     打印直接下载链接
# API:      curl -F "file=@<file>" https://tmpfiles.org/api/v1/upload
# 返回JSON: {"status":"success","data":{"url":"https://tmpfiles.org/XXXX/file"}}
# 说明:     返回的URL是展示页面,需要转换为直链:
#           展示页: https://tmpfiles.org/XXXX/file
#           直链:   https://tmpfiles.org/dl/XXXX/file
#===============================================================================

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查参数
if [[ $# -lt 1 ]]; then
    echo -e "${RED}错误: 缺少文件路径参数${NC}" >&2
    echo "使用方法: $0 <文件路径>" >&2
    exit 1
fi

FILE_PATH="$1"

# 检查文件是否存在
if [[ ! -f "$FILE_PATH" ]]; then
    echo -e "${RED}错误: 文件不存在: $FILE_PATH${NC}" >&2
    exit 1
fi

# 检查文件是否可读
if [[ ! -r "$FILE_PATH" ]]; then
    echo -e "${RED}错误: 文件不可读: $FILE_PATH${NC}" >&2
    exit 1
fi

# 调用 tmpfiles.org API 上传文件
# 使用 -F "file=@<file>" 模拟表单上传
# 使用 --max-time 防止挂起
RESPONSE=$(curl -fsSL \
    --max-time 60 \
    -F "file=@${FILE_PATH}" \
    https://tmpfiles.org/api/v1/upload 2>&1)

# 检查 curl 是否出错
if [[ $? -ne 0 ]]; then
    echo -e "${RED}错误: 上传失败,curl返回错误${NC}" >&2
    echo "$RESPONSE" >&2
    exit 1
fi

# 解析 JSON 响应
# 使用 grep 和 sed 提取 URL (避免依赖 jq)
# 期望格式: {"status":"success","data":{"url":"https://tmpfiles.org/XXXX/file"}}

# 检查是否上传成功
if ! echo "$RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${RED}错误: 上传失败,服务器返回错误${NC}" >&2
    echo "响应: $RESPONSE" >&2
    exit 1
fi

# 提取 URL
# 使用 sed 提取 url 字段的值
URL=$(echo "$RESPONSE" | sed -n 's/.*"url":"\([^"]*\)".*/\1/p')

if [[ -z "$URL" ]]; then
    echo -e "${RED}错误: 无法解析响应中的URL${NC}" >&2
    echo "响应: $RESPONSE" >&2
    exit 1
fi

# 从 URL 中提取 ID
# URL 格式: https://tmpfiles.org/XXXX/file
# 需要提取 XXXX 部分
ID=$(echo "$URL" | sed -n 's|https://tmpfiles.org/\([^/]*\)/.*|\1|p')

if [[ -z "$ID" ]]; then
    echo -e "${RED}错误: 无法从URL提取ID${NC}" >&2
    echo "URL: $URL" >&2
    exit 1
fi

# 构造直链 (将路径中的 / 替换为 /dl/)
# 展示页: https://tmpfiles.org/XXXX/file
# 直链:   https://tmpfiles.org/dl/XXXX/file
DIRECT_URL="https://tmpfiles.org/dl/${ID}/$(basename "$FILE_PATH")"

# 输出结果
echo -e "${GREEN}上传成功!${NC}"
echo ""
echo "文件名: $(basename "$FILE_PATH")"
echo "文件大小: $(du -h "$FILE_PATH" | cut -f1)"
echo ""
echo -e "${YELLOW}展示页面:${NC} $URL"
echo -e "${YELLOW}直链下载:${NC} $DIRECT_URL"
echo ""

# 如果需要,也可以只输出直链 (供其他脚本使用)
# echo "$DIRECT_URL"
