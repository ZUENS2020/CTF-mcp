#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /abs/path/to/file" >&2
  exit 1
fi

file="$1"
if [[ ! -f "$file" ]]; then
  echo "file not found: $file" >&2
  exit 1
fi

curl -fsSL -F "file=@${file}" https://tmpfiles.org/api/v1/upload
