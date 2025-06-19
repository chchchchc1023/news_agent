#!/bin/bash
# Render启动脚本

echo "=== 检查当前目录 ==="
pwd
ls -la

echo "=== 检查Python文件 ==="
ls -la *.py

echo "=== 启动Web服务 ==="
python web_main.py
