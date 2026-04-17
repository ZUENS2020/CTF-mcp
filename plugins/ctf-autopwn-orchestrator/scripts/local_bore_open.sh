#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <local_port>" >&2
  exit 1
fi

port="$1"
exec bore local --to bore.pub "$port"
