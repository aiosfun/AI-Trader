#!/bin/bash

# A股数据准备 - 支持智能更新

# 获取项目根目录（scripts/ 的父目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

cd data/A_stock

echo "🚀 Starting A-stock data update with smart caching..."

# 使用Tushare获取数据（支持智能跳过）
python get_daily_price_tushare.py

# 合并数据到JSONL格式
python merge_jsonl_tushare.py

echo "✅ A-stock data preparation completed!"

cd ..
