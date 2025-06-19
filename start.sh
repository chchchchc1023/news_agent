#!/bin/bash

# 新闻代理系统启动脚本

echo "🚀 新闻代理系统启动脚本"
echo "========================"

# 检查conda环境
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到conda命令"
    exit 1
fi

# 激活conda环境
echo "📦 激活conda环境: news_agent"
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate news_agent

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到python命令"
    exit 1
fi

echo "✅ 环境检查完成"
echo ""

# 显示菜单
echo "请选择操作:"
echo "1) 测试所有组件"
echo "2) 执行一次任务"
echo "3) 启动定时调度器"
echo "4) 启动调度器并立即执行"
echo "5) 显示系统信息"
echo "6) 退出"
echo ""

read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        echo "🔧 开始测试所有组件..."
        uv run python main.py --test
        ;;
    2)
        echo "🏃 执行一次任务..."
        uv run python main.py --run-once
        ;;
    3)
        echo "⏰ 启动定时调度器..."
        uv run python main.py --start
        ;;
    4)
        echo "🚀 启动调度器并立即执行..."
        uv run python main.py --start-now
        ;;
    5)
        echo "ℹ️ 显示系统信息..."
        uv run python main.py --info
        ;;
    6)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
