#!/bin/bash
# エラーが発生したら即座に終了する設定
set -e

cd /Users/solle/development/github/Tasker/
export PYTHONPATH=$PYTHONPATH:.

# 仮想環境のPythonを実行
./.venv/bin/python3.12 src/main.py "$@"