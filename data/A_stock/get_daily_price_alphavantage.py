import os
import requests
from dotenv import load_dotenv
from typing import List
import sys

# Add parent directory to path to import DataManager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import DataManager

load_dotenv()
import json
import datetime
from collections import OrderedDict
sse_50_codes = [
    "600519.SHH",
    "601318.SHH",
    "600036.SHH",
    "601899.SHH",
    "600900.SHH",
    "601166.SHH",
    "600276.SHH",
    "600030.SHH",
    "603259.SHH",
    "688981.SHH",
    "688256.SHH",
    "601398.SHH",
    "688041.SHH",
    "601211.SHH",
    "601288.SHH",
    "601328.SHH",
    "688008.SHH",
    "600887.SHH",
    "600150.SHH",
    "601816.SHH",
    "601127.SHH",
    "600031.SHH",
    "688012.SHH",
    "603501.SHH",
    "601088.SHH",
    "600309.SHH",
    "601601.SHH",
    "601668.SHH",
    "603993.SHH",
    "601012.SHH",
    "601728.SHH",
    "600690.SHH",
    "600809.SHH",
    "600941.SHH",
    "600406.SHH",
    "601857.SHH",
    "601766.SHH",
    "601919.SHH",
    "600050.SHH",
    "600760.SHH",
    "601225.SHH",
    "600028.SHH",
    "601988.SHH",
    "688111.SHH",
    "601985.SHH",
    "601888.SHH",
    "601628.SHH",
    "601600.SHH",
    "601658.SHH",
    "600048.SHH"
]

def filter_data(data: dict,after_date: str):
    data_filtered = {}
    for date in data["Time Series (Daily)"]:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        after_date_obj = datetime.datetime.strptime(after_date, "%Y-%m-%d")
        if date_obj > after_date_obj:
            data_filtered[date] = data["Time Series (Daily)"][date]
    data["Time Series (Daily)"] = data_filtered
    return data

def merge_data(existing_data: dict, new_data: dict):
    """合并数据：保留已存在的日期，只添加新日期"""
    if existing_data is None or "Time Series (Daily)" not in existing_data:
        return new_data
    
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
    if sorted_dates:
        merged_data["Meta Data"]["3. Last Refreshed"] = list(sorted_dates.keys())[0]
    
    return merged_data

def load_existing_data(filepath: str):
    """加载已存在的数据文件"""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

def get_daily_price(SYMBOL: str, force_update: bool = False, verbose: bool = True):
    """
    获取A股日价格数据，支持智能缓存和增量更新

    Args:
        SYMBOL: A股代码
        force_update: 是否强制更新，忽略本地数据检查
        verbose: 是否显示详细信息
    """
    data_manager = DataManager()

    # 确保数据目录存在
    os.makedirs("./A_stock_data", exist_ok=True)
    output_file = f"./A_stock_data/daily_prices_{SYMBOL}.json"

    # 检查是否需要更新数据
    if not data_manager.should_update_data(output_file, force_update):
        if verbose:
            summary = data_manager.get_update_summary(SYMBOL, output_file, False)
            print(summary)
        return

    # 需要更新数据，调用API
    FUNCTION = "TIME_SERIES_DAILY"
    OUTPUTSIZE = "compact"
    APIKEY = os.getenv("ALPHAADVANTAGE_API_KEY")

    if not APIKEY:
        print(f"❌ Error: ALPHAADVANTAGE_API_KEY not found in environment variables")
        return

    url = (
        f"https://www.alphavantage.co/query?function={FUNCTION}&symbol={SYMBOL}&entitlement=delayed&outputsize={OUTPUTSIZE}&apikey={APIKEY}"
    )

    try:
        if verbose:
            print(f"📡 Fetching data for {SYMBOL}...")

        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        # 检查API响应中的错误信息
        if data.get("Note") is not None:
            if verbose:
                print(f"⚠️  {SYMBOL}: API call limit reached - {data.get('Note')}")
            return
        if data.get("Information") is not None:
            if verbose:
                print(f"⚠️  {SYMBOL}: API information - {data.get('Information')}")
            return
        if data.get("Error Message") is not None:
            if verbose:
                print(f"❌ {SYMBOL}: API error - {data.get('Error Message')}")
            return

        # 检查是否有有效数据
        if "Meta Data" not in data or "Time Series (Daily)" not in data:
            if verbose:
                print(f"❌ {SYMBOL}: Invalid data structure received")
            return

        stock_name = data.get("Meta Data", {}).get("2. Symbol", SYMBOL)

        # 获取最新日期用于摘要
        latest_date = data_manager.get_latest_data_date(data)

        # 过滤数据（如果需要）
        if OUTPUTSIZE == "full":
            data = filter_data(data, "2025-10-01")

        # 合并数据：保留已存在的日期，只添加新日期
        existing_data = data_manager.load_existing_data(output_file)
        merged_data = data_manager.merge_time_series_data(existing_data, data)

        # 保存数据
        data_manager.save_data(merged_data, output_file)

        if verbose:
            summary = data_manager.get_update_summary(SYMBOL, output_file, True, latest_date)
            print(summary)

        # 特殊处理上证50指数
        if SYMBOL == "000016.SHH":
            handle_index_file(data_manager, data, verbose)

    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"❌ {SYMBOL}: Network error - {e}")
    except Exception as e:
        if verbose:
            print(f"❌ {SYMBOL}: Unexpected error - {e}")


def handle_index_file(data_manager: DataManager, data: dict, verbose: bool = True):
    """处理上证50指数文件的特殊处理"""
    try:
        # 对于上证50指数，也需要保存 Adaily_prices 文件
        adaily_file = "./A_stock_data/Adaily_prices_000016.SHH.json"
        existing_adaily_data = data_manager.load_existing_data(adaily_file)
        adaily_data = data_manager.merge_time_series_data(existing_adaily_data, data)
        data_manager.save_data(adaily_data, adaily_file)

        # 对于 index_daily_sse_50.json，也需要合并
        index_file = "./A_stock_data/index_daily_sse_50.json"
        existing_index_data = data_manager.load_existing_data(index_file)
        index_data = data.copy()
        if "Meta Data" in index_data:
            index_data["Meta Data"]["2. Symbol"] = "000016.SH"
        index_data = data_manager.merge_time_series_data(existing_index_data, index_data)
        data_manager.save_data(index_data, index_file)

        if verbose:
            print("📊 Updated SSE-50 index files")

    except Exception as e:
        if verbose:
            print(f"⚠️  Error handling index files: {e}")


def get_all_a_stock_prices(symbols: List[str] = None, force_update: bool = False, quiet: bool = False):
    """
    批量获取A股价格数据，支持智能更新

    Args:
        symbols: A股代码列表，默认为SSE-50
        force_update: 是否强制更新所有数据
        quiet: 是否静默运行
    """
    if symbols is None:
        symbols = sse_50_codes

    data_manager = DataManager()

    if not quiet:
        print(f"🚀 Starting A-stock price update for {len(symbols)} symbols...")
        print(f"📅 Trading day: {'Yes' if data_manager.is_trading_day() else 'No'}")
        print(f"🔄 Force update: {'Yes' if force_update else 'No'}")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            if not quiet:
                progress = f"[{i}/{len(symbols)}] "
                print(f"{progress}", end="")

            # 获取文件路径
            output_file = f"./A_stock_data/daily_prices_{symbol}.json"

            # 检查是否需要更新
            should_update = data_manager.should_update_data(output_file, force_update)

            if not should_update:
                skipped_count += 1
                if not quiet:
                    summary = data_manager.get_update_summary(symbol, output_file, False)
                    print(summary)
                continue

            # 需要更新，调用API
            get_daily_price(symbol, force_update, verbose=not quiet)
            updated_count += 1

            # API调用间隔
            if i < len(symbols):
                import time
                time.sleep(12)  # Alpha Vantage免费版频率限制

        except KeyboardInterrupt:
            print(f"\n⏹️  Update interrupted by user at {symbol}")
            break
        except Exception as e:
            error_count += 1
            print(f"❌ Error processing {symbol}: {e}")

    # 显示总结
    if not quiet:
        print(f"\n📋 A-Stock Update Summary:")
        print(f"   ✅ Updated: {updated_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total: {len(symbols)} symbols")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update A-stock (SSE-50) price data with smart caching")
    parser.add_argument("--force", action="store_true", help="Force update all A-stocks")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet mode")
    parser.add_argument("--symbols", nargs="+", help="Specific A-stock symbols to update")
    parser.add_argument("--list", action="store_true", help="List all available A-stock symbols")

    args = parser.parse_args()

    if args.list:
        print("Available SSE-50 A-stock symbols:")
        for i, symbol in enumerate(sse_50_codes, 1):
            print(f"{i:3d}. {symbol}")
        print(f"\nTotal: {len(sse_50_codes)} symbols")
    else:
        get_all_a_stock_prices(
            symbols=args.symbols,
            force_update=args.force,
            quiet=args.quiet
        )
