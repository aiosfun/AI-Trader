import os
import json
import datetime
from typing import Dict, Any, Optional, List
from collections import OrderedDict


class DataManager:
    """通用数据管理工具，支持本地数据检查和增量更新"""

    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def load_existing_data(self, filepath: str) -> Optional[Dict[str, Any]]:
        """加载已存在的数据文件"""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 检查数据是否包含错误信息
                if data.get("Error Message") or data.get("Information"):
                    return None
                return data
            except (json.JSONDecodeError, FileNotFoundError):
                return None
        return None

    def get_latest_data_date(self, data: Dict[str, Any]) -> Optional[str]:
        """获取数据中最新的日期"""
        if not data or "Time Series (Daily)" not in data:
            return None

        time_series = data["Time Series (Daily)"]
        if not time_series:
            return None

        # 时间序列数据通常是按日期降序排列的，第一个就是最新的
        return list(time_series.keys())[0] if isinstance(time_series, dict) else None

    def is_data_fresh(self, filepath: str, max_days_old: int = 1) -> bool:
        """
        检查本地数据是否足够新鲜

        Args:
            filepath: 数据文件路径
            max_days_old: 允许的最大天数差，超过此天数需要更新

        Returns:
            bool: True表示数据足够新鲜，False表示需要更新
        """
        data = self.load_existing_data(filepath)
        if not data:
            return False

        latest_date_str = self.get_latest_data_date(data)
        if not latest_date_str:
            return False

        try:
            # 解析最新日期
            latest_date = datetime.datetime.strptime(latest_date_str, "%Y-%m-%d")

            # 获取当前日期（忽略时间部分）
            now = datetime.datetime.now()

            # 计算日期差
            date_diff = (now - latest_date).days

            # 如果是今天的数据，或者日期差在允许范围内，则认为数据是新鲜的
            return date_diff <= max_days_old

        except ValueError:
            # 如果日期格式不正确，认为数据无效，需要更新
            return False

    def is_trading_day(self, date: datetime.datetime = None) -> bool:
        """
        检查给定日期是否是交易日（简单判断：周一到周五）

        Args:
            date: 要检查的日期，默认为当前日期

        Returns:
            bool: True表示是交易日，False表示不是交易日
        """
        if date is None:
            date = datetime.datetime.now()

        # 周一到周五是交易日 (0-4)
        return date.weekday() < 5

    def should_update_data(self, filepath: str, force_update: bool = False) -> bool:
        """
        判断是否需要更新数据

        Args:
            filepath: 数据文件路径
            force_update: 是否强制更新

        Returns:
            bool: True表示需要更新，False表示跳过更新
        """
        if force_update:
            return True

        # 如果文件不存在，需要更新
        if not os.path.exists(filepath):
            return True

        # 如果数据不新鲜，需要更新（但只在交易日检查）
        if self.is_trading_day() and not self.is_data_fresh(filepath):
            return True

        return False

    def merge_time_series_data(self, existing_data: Optional[Dict[str, Any]],
                              new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并时间序列数据：保留已存在的日期，只添加新日期

        Args:
            existing_data: 已存在的数据
            new_data: 新获取的数据

        Returns:
            合并后的数据
        """
        if existing_data is None or "Time Series (Daily)" not in existing_data:
            return new_data

        if "Time Series (Daily)" not in new_data:
            return existing_data

        existing_dates = existing_data["Time Series (Daily)"]
        new_dates = new_data["Time Series (Daily)"]

        # 合并：保留已存在的日期，添加新日期
        merged_dates = existing_dates.copy()
        for date in new_dates:
            if date not in merged_dates:
                merged_dates[date] = new_dates[date]

        # 按日期排序（降序，最新的在前）
        sorted_dates = OrderedDict(sorted(merged_dates.items(), key=lambda x: x[0], reverse=True))

        # 更新数据：保留 existing_data 的 Meta Data，但更新 Last Refreshed
        merged_data = existing_data.copy()
        merged_data["Time Series (Daily)"] = sorted_dates

        # 更新 Meta Data 中的 Last Refreshed（使用最新的日期）
        if sorted_dates and "Meta Data" in merged_data:
            merged_data["Meta Data"]["3. Last Refreshed"] = list(sorted_dates.keys())[0]

        return merged_data

    def save_data(self, data: Dict[str, Any], filepath: str) -> None:
        """保存数据到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_update_summary(self, symbol: str, filepath: str, was_updated: bool,
                          latest_date: Optional[str] = None) -> str:
        """
        生成更新摘要信息

        Args:
            symbol: 股票/加密货币代码
            filepath: 数据文件路径
            was_updated: 是否进行了更新
            latest_date: 最新日期

        Returns:
            摘要信息字符串
        """
        status = "✅ UPDATED" if was_updated else "⏭️  SKIPPED"

        if was_updated and latest_date:
            return f"{status} {symbol}: Latest data {latest_date}"
        elif not was_updated:
            if os.path.exists(filepath):
                data = self.load_existing_data(filepath)
                if data:
                    latest_date = self.get_latest_data_date(data)
                    return f"{status} {symbol}: Data already fresh until {latest_date}"
            return f"{status} {symbol}: No existing data or file not found"

        return f"{status} {symbol}"