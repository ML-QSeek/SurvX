# -*- coding: utf-8 -*-
"""
trade_executor_futures.py - 期货交易执行模块

与股票版的差异：
    1. 合约代码格式不同
    2. 最小交易单位 = 1手（按合约乘数）
    3. 支持开多/开空/平多/平空
    4. 保证金计算
    5. 夜盘时段支持
    6. T+0（不需要考虑持仓过夜，但需要考虑换月）
"""

import time
import datetime
import math
from typing import List, Dict, Optional, Union, Any
from enum import Enum


# ============================================================
# 配置区
# ============================================================

DEFAULT_CONFIG = {
    'wait_seconds': 30,
    'stop_abs': 1,               # 期货最小单位是手，停止阈值设1手
    'stop_ratio': 0.05,
    'close_minutes': 5,
    'first_ratio': 0.9,
    'final_wait': 10,
    'single_ratio': 0.02,
    'min_trim_amount': 5000,
    'default_price_type': '1',
    'default_limit_price': 0,
}

# T0策略专用配置（期货天然T+0，T0更顺手）
T0_CONFIG = {
    'wait_seconds': 3,
    'stop_abs': 0,
    'stop_ratio': 0,
    'close_minutes': 5,
    'first_ratio': 1.0,
    'final_wait': 3,
    'default_price_type': '1',
    'default_limit_price': 0,
}

# 品种乘数表（按实际交易所规则）
CONTRACT_MULTIPLIER = {
    # 上期所
    'CU': 5, 'AL': 5, 'ZN': 5, 'PB': 5, 'NI': 1, 'SN': 1,
    'AU': 1000, 'AG': 15, 'RB': 10, 'WR': 10, 'HC': 10,
    'SS': 5, 'BU': 10, 'RU': 10, 'SP': 10, 'FU': 10,
    # 大商所
    'A': 10, 'B': 10, 'M': 10, 'Y': 10, 'P': 10,
    'C': 10, 'CS': 10, 'JD': 10, 'LH': 16, 'RR': 10,
    'L': 5, 'V': 5, 'PP': 5, 'J': 100, 'JM': 100,
    'I': 100, 'EG': 10, 'EB': 5, 'PG': 20,
    # 郑商所
    'SR': 10, 'TA': 5, 'MA': 10, 'FG': 20, 'ZC': 100,
    'CF': 5, 'CY': 5, 'RM': 10, 'OI': 10, 'WH': 20,
    'PM': 50, 'RI': 20, 'JR': 20, 'LR': 20, 'RS': 10,
    'CJ': 5, 'AP': 10, 'UR': 20, 'SA': 20, 'PF': 5,
    'PK': 5, 'SH': 100,
    # 中金所
    'IF': 300, 'IC': 200, 'IH': 300, 'IM': 200,
    'T': 10000, 'TF': 10000, 'TS': 20000, 'TL': 10000,
    # 能源中心
    'SC': 1000, 'LU': 10, 'NR': 10, 'BC': 5,
}

# 保证金比例（简化，实际应从账户查询）
MARGIN_RATE = 0.10  # 默认10%


# ============================================================
# 期货专用辅助函数
# ============================================================

def parse_futures_code(full_code: str) -> Dict:
    """
    解析期货合约代码
    输入: 'rb2410.SHFE' 或 'RB2410' 或 'IF2412.CFFEX'
    返回: {'symbol': 'RB', 'month': '2410', 'exchange': 'SHFE'}
    """
    # 去除可能的点号后缀
    if '.' in full_code:
        code, exchange = full_code.split('.')
    else:
        code = full_code
        exchange = ''

    # 提取品种字母和月份
    # 品种字母通常是1-2个字母，月份是4位数字
    import re
    match = re.match(r'([A-Z]+)(\d{4})', code)
    if match:
        symbol = match.group(1)
        month = match.group(2)
    else:
        symbol = code
        month = ''

    return {'symbol': symbol, 'month': month, 'exchange': exchange}


def get_contract_multiplier(symbol: str) -> int:
    """获取合约乘数"""
    return CONTRACT_MULTIPLIER.get(symbol.upper(), 1)


def calculate_margin(price: float, volume: int, symbol: str) -> float:
    """
    计算保证金
    保证金 = 价格 × 数量 × 合约乘数 × 保证金比例
    """
    multiplier = get_contract_multiplier(symbol)
    return price * volume * multiplier * MARGIN_RATE


def round_to_lot_futures(volume: int) -> int:
    """期货最小交易单位 = 1手"""
    return max(1, int(volume))  # 期货不能买0.几手，直接取整


def is_futures_trading_hours() -> bool:
    """
    判断是否在期货交易时段
    期货有夜盘，需要特殊处理
    """
    now = datetime.datetime.now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute

    # 周末休市
    if weekday >= 5:
        return False

    # 上午：9:00 - 11:30
    if 9 <= hour < 11:
        return True
    if hour == 11 and minute <= 30:
        return True

    # 下午：13:30 - 15:00
    if 13 <= hour < 15:
        return True
    if hour == 15 and minute == 0:
        return True

    # 夜盘：21:00 - 次日2:30（不同品种不同）
    # 简化：21:00 - 23:00
    if hour >= 21 or hour < 2:
        return True

    return False


def get_futures_close_time() -> datetime:
    """
    获取期货收盘时间
    不同品种收盘时间不同，简化处理
    """
    now = datetime.datetime.now()
    if now.hour >= 21:
        # 夜盘，次日凌晨收盘
        return now.replace(hour=23, minute=0, second=0, microsecond=0)
    else:
        # 日盘 15:00
        return now.replace(hour=15, minute=0, second=0, microsecond=0)


def is_market_close_soon_futures(minutes: int = 5) -> bool:
    """判断是否即将收盘（期货版）"""
    if not is_futures_trading_hours():
        return True

    close_time = get_futures_close_time()
    now = datetime.datetime.now()
    diff = (close_time - now).total_seconds() / 60
    return diff <= minutes


# ============================================================
# 底层下单函数（期货版）
# ============================================================

def place_order_futures(stock_code: str, volume: int, direction: str,
                        price_type: str = '1', limit_price: float = 0) -> bool:
    """
    期货下单

    参数:
        stock_code: 合约代码
        volume: 手数
        direction: 'open_long' / 'open_short' / 'close_long' / 'close_short'
        price_type: '1'-最新价, '2'-对手价, '3'-指定价
        limit_price: 指定价

    返回:
        bool: 是否下单成功
    """
    global mqsaccount

    if volume <= 0:
        print(f"[期货下单] 数量无效: {volume}")
        return False

    if price_type == '3' and limit_price <= 0:
        print(f"[期货下单] 指定价模式但价格无效，降级为最新价")
        price_type = '1'

    # 期货下单类型映射
    order_type_map = {
        'open_long': ('50', '买入开仓'),
        'open_short': ('51', '卖出开仓'),
        'close_long': ('52', '卖出平仓'),
        'close_short': ('53', '买入平仓'),
    }

    if direction not in order_type_map:
        print(f"[期货下单] 未知方向: {direction}")
        return False

    order_type, desc = order_type_map[direction]
    orderset = (order_type, price_type, str(limit_price), stock_code,
                str(volume), mqsaccount, '49', '2')

    # TODO: 替换为实际的期货下单
    # from main import place_order
    # place_order(orderset)
    print(f"[期货下单] {desc} {stock_code} {volume}手 price_type={price_type} limit_price={limit_price}")
    return True


def all_cancel_order_futures() -> bool:
    """全部撤单（期货版）"""
    print("[期货撤单] 全部撤单")
    return True


# ============================================================
# 行情获取（期货版）
# ============================================================

def get_futures_price(stock_code: str) -> Optional[float]:
    """
    获取期货合约最新价
    TODO: 替换为实际的ZMQ调用
    """
    # 临时返回示例价格
    return 3500.0


def get_futures_position() -> Dict[str, Dict]:
    """
    获取期货持仓
    返回: {
        'rb2410': {'long': 5, 'short': 0, 'long_cost': 3500, 'short_cost': 0},
        'IF2412': {'long': 0, 'short': 2, 'long_cost': 0, 'short_cost': 3800}
    }
    """
    # TODO: 替换为实际持仓查询
    return {}


def get_futures_available() -> float:
    """获取期货可用资金"""
    # TODO: 替换为实际资金查询
    return 1000000.0


def get_futures_margin() -> float:
    """获取占用保证金"""
    # TODO: 替换为实际查询
    return 0.0


# ============================================================
# 基础执行层（期货版）
# ============================================================

def buy_futures_with_retry(contract: str, target_volume: int,
                           price_type: str = '1', limit_price: float = 0,
                           wait_seconds: int = 30, stop_abs: int = 1,
                           stop_ratio: float = 0.05, close_minutes: int = 5,
                           first_ratio: float = 0.9, final_wait: int = 10) -> Dict:
    """
    期货开多，带重试和兜底
    target_volume: 目标手数
    stop_abs: 停止阈值（手），默认1手
    """
    if target_volume <= 0:
        return wrap_result(0, 0, 0, 0, 'invalid')

    stop_rel = max(1, int(target_volume * stop_ratio))
    print(f"[期货开多] {contract} 目标:{target_volume}手, 停止: ≤{stop_abs}手 或 ≤{stop_rel}手({stop_ratio*100:.0f}%)")

    cum_filled = 0
    cum_cost = 0
    rounds = 0
    is_first = True

    while True:
        if is_market_close_soon_futures(close_minutes):
            print(f"[期货开多] {contract} 临近收盘，强制停止")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'timeout')

        rounds += 1

        if is_first:
            order_volume = int(target_volume * first_ratio)
            order_volume = max(1, order_volume)
            is_first = False
        else:
            order_volume = target_volume - cum_filled

        if order_volume <= 0:
            print(f"[期货开多] {contract} 第{rounds}轮: 下单量≤0，结束")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')

        print(f"[期货开多] {contract} 第{rounds}轮: 挂单 {order_volume}手")

        price = get_futures_price(contract)
        if not price or price <= 0:
            print(f"[期货开多] {contract} 获取价格失败")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'error')

        place_order_futures(contract, order_volume, 'open_long', price_type, limit_price)
        time.sleep(wait_seconds)
        all_cancel_order_futures()
        time.sleep(1)

        round_filled, round_cost = query_today_filled_futures(contract)
        if round_filled > 0:
            cum_filled += round_filled
            cum_cost += round_cost
            print(f"[期货开多] {contract} 第{rounds}轮: 成交 {round_filled}手, 累计 {cum_filled}手")
        else:
            print(f"[期货开多] {contract} 第{rounds}轮: 无成交")

        remain = target_volume - cum_filled

        if remain <= stop_abs or remain <= stop_rel:
            print(f"[期货开多] {contract} 剩余 {remain}手, 进入兜底")
            if remain > 0:
                print(f"[期货开多] {contract} 兜底: 挂单 {remain}手")
                price = get_futures_price(contract)
                if price and price > 0:
                    place_order_futures(contract, remain, 'open_long', price_type, limit_price)
                    time.sleep(final_wait)
                    all_cancel_order_futures()
                    time.sleep(1)
                    final_filled, final_cost = query_today_filled_futures(contract)
                    if final_filled > 0:
                        cum_filled += final_filled
                        cum_cost += final_cost
                        print(f"[期货开多] {contract} 兜底成交: {final_filled}手")
            break

    return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')


def sell_futures_with_retry(contract: str, target_volume: int,
                            price_type: str = '1', limit_price: float = 0,
                            wait_seconds: int = 30, stop_abs: int = 1,
                            stop_ratio: float = 0.05, close_minutes: int = 5,
                            final_wait: int = 10) -> Dict:
    """
    期货平多，带重试和兜底
    """
    if target_volume <= 0:
        return wrap_result(0, 0, 0, 0, 'invalid')

    stop_rel = max(1, int(target_volume * stop_ratio))
    print(f"[期货平多] {contract} 目标:{target_volume}手, 停止: ≤{stop_abs}手 或 ≤{stop_rel}手")

    cum_filled = 0
    cum_cost = 0
    rounds = 0

    while True:
        if is_market_close_soon_futures(close_minutes):
            print(f"[期货平多] {contract} 临近收盘，强制停止")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'timeout')

        rounds += 1
        order_volume = target_volume - cum_filled

        if order_volume <= 0:
            print(f"[期货平多] {contract} 第{rounds}轮: 下单量≤0，结束")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')

        print(f"[期货平多] {contract} 第{rounds}轮: 挂单 {order_volume}手")

        price = get_futures_price(contract)
        if not price or price <= 0:
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'error')

        place_order_futures(contract, order_volume, 'close_long', price_type, limit_price)
        time.sleep(wait_seconds)
        all_cancel_order_futures()
        time.sleep(1)

        round_filled, round_cost = query_today_filled_futures(contract)
        if round_filled > 0:
            cum_filled += round_filled
            cum_cost += round_cost
            print(f"[期货平多] {contract} 第{rounds}轮: 成交 {round_filled}手, 累计 {cum_filled}手")
        else:
            print(f"[期货平多] {contract} 第{rounds}轮: 无成交")

        remain = target_volume - cum_filled

        if remain <= stop_abs or remain <= stop_rel:
            print(f"[期货平多] {contract} 剩余 {remain}手, 进入兜底")
            if remain > 0:
                print(f"[期货平多] {contract} 兜底: 挂单 {remain}手")
                price = get_futures_price(contract)
                if price and price > 0:
                    place_order_futures(contract, remain, 'close_long', price_type, limit_price)
                    time.sleep(final_wait)
                    all_cancel_order_futures()
                    time.sleep(1)
                    final_filled, final_cost = query_today_filled_futures(contract)
                    if final_filled > 0:
                        cum_filled += final_filled
                        cum_cost += final_cost
                        print(f"[期货平多] {contract} 兜底成交: {final_filled}手")
            break

    return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')


def short_futures_with_retry(contract: str, target_volume: int,
                             price_type: str = '1', limit_price: float = 0,
                             wait_seconds: int = 30, stop_abs: int = 1,
                             stop_ratio: float = 0.05, close_minutes: int = 5,
                             first_ratio: float = 0.9, final_wait: int = 10) -> Dict:
    """
    期货开空，带重试和兜底
    """
    if target_volume <= 0:
        return wrap_result(0, 0, 0, 0, 'invalid')

    stop_rel = max(1, int(target_volume * stop_ratio))
    print(f"[期货开空] {contract} 目标:{target_volume}手, 停止: ≤{stop_abs}手 或 ≤{stop_rel}手")

    cum_filled = 0
    cum_cost = 0
    rounds = 0
    is_first = True

    while True:
        if is_market_close_soon_futures(close_minutes):
            print(f"[期货开空] {contract} 临近收盘，强制停止")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'timeout')

        rounds += 1

        if is_first:
            order_volume = int(target_volume * first_ratio)
            order_volume = max(1, order_volume)
            is_first = False
        else:
            order_volume = target_volume - cum_filled

        if order_volume <= 0:
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')

        print(f"[期货开空] {contract} 第{rounds}轮: 挂单 {order_volume}手")

        price = get_futures_price(contract)
        if not price or price <= 0:
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'error')

        place_order_futures(contract, order_volume, 'open_short', price_type, limit_price)
        time.sleep(wait_seconds)
        all_cancel_order_futures()
        time.sleep(1)

        round_filled, round_cost = query_today_filled_futures(contract)
        if round_filled > 0:
            cum_filled += round_filled
            cum_cost += round_cost
            print(f"[期货开空] {contract} 第{rounds}轮: 成交 {round_filled}手, 累计 {cum_filled}手")
        else:
            print(f"[期货开空] {contract} 第{rounds}轮: 无成交")

        remain = target_volume - cum_filled

        if remain <= stop_abs or remain <= stop_rel:
            print(f"[期货开空] {contract} 剩余 {remain}手, 进入兜底")
            if remain > 0:
                print(f"[期货开空] {contract} 兜底: 挂单 {remain}手")
                price = get_futures_price(contract)
                if price and price > 0:
                    place_order_futures(contract, remain, 'open_short', price_type, limit_price)
                    time.sleep(final_wait)
                    all_cancel_order_futures()
                    time.sleep(1)
                    final_filled, final_cost = query_today_filled_futures(contract)
                    if final_filled > 0:
                        cum_filled += final_filled
                        cum_cost += final_cost
                        print(f"[期货开空] {contract} 兜底成交: {final_filled}手")
            break

    return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')


def cover_futures_with_retry(contract: str, target_volume: int,
                             price_type: str = '1', limit_price: float = 0,
                             wait_seconds: int = 30, stop_abs: int = 1,
                             stop_ratio: float = 0.05, close_minutes: int = 5,
                             final_wait: int = 10) -> Dict:
    """
    期货平空，带重试和兜底
    """
    if target_volume <= 0:
        return wrap_result(0, 0, 0, 0, 'invalid')

    stop_rel = max(1, int(target_volume * stop_ratio))
    print(f"[期货平空] {contract} 目标:{target_volume}手, 停止: ≤{stop_abs}手 或 ≤{stop_rel}手")

    cum_filled = 0
    cum_cost = 0
    rounds = 0

    while True:
        if is_market_close_soon_futures(close_minutes):
            print(f"[期货平空] {contract} 临近收盘，强制停止")
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'timeout')

        rounds += 1
        order_volume = target_volume - cum_filled

        if order_volume <= 0:
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')

        print(f"[期货平空] {contract} 第{rounds}轮: 挂单 {order_volume}手")

        price = get_futures_price(contract)
        if not price or price <= 0:
            return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'error')

        place_order_futures(contract, order_volume, 'close_short', price_type, limit_price)
        time.sleep(wait_seconds)
        all_cancel_order_futures()
        time.sleep(1)

        round_filled, round_cost = query_today_filled_futures(contract)
        if round_filled > 0:
            cum_filled += round_filled
            cum_cost += round_cost
            print(f"[期货平空] {contract} 第{rounds}轮: 成交 {round_filled}手, 累计 {cum_filled}手")
        else:
            print(f"[期货平空] {contract} 第{rounds}轮: 无成交")

        remain = target_volume - cum_filled

        if remain <= stop_abs or remain <= stop_rel:
            print(f"[期货平空] {contract} 剩余 {remain}手, 进入兜底")
            if remain > 0:
                print(f"[期货平空] {contract} 兜底: 挂单 {remain}手")
                price = get_futures_price(contract)
                if price and price > 0:
                    place_order_futures(contract, remain, 'close_short', price_type, limit_price)
                    time.sleep(final_wait)
                    all_cancel_order_futures()
                    time.sleep(1)
                    final_filled, final_cost = query_today_filled_futures(contract)
                    if final_filled > 0:
                        cum_filled += final_filled
                        cum_cost += final_cost
                        print(f"[期货平空] {contract} 兜底成交: {final_filled}手")
            break

    return wrap_result(target_volume, cum_filled, cum_cost, rounds, 'done')


def query_today_filled_futures(contract: str) -> tuple:
    """查询期货今日成交"""
    # TODO: 替换为实际成交查询
    return 0, 0


def wrap_result(target: int, filled: int, cost: float, rounds: int, status: str) -> Dict:
    return {
        'target': target,
        'filled': filled,
        'remain': target - filled,
        'rounds': rounds,
        'avg_price': cost / filled if filled > 0 else 0,
        'status': status
    }


# ============================================================
# 算法层（期货版）
# ============================================================

def twap_open_long(contract: str, target_volume: int,
                   price_type: str = '1', limit_price: float = 0,
                   slices: int = 10, interval: int = 60,
                   **kwargs) -> Dict:
    """TWAP开多"""
    print(f"[TWAP开多] {contract} 目标:{target_volume}手, 切片:{slices}, 间隔:{interval}秒")

    slice_volume = target_volume // slices
    remainder = target_volume % slices
    results = []
    cum_filled = 0
    cum_cost = 0

    for i in range(slices):
        if is_market_close_soon_futures(kwargs.get('close_minutes', 5)):
            break

        vol = slice_volume + (remainder if i == slices - 1 else 0)
        if vol <= 0:
            continue

        result = buy_futures_with_retry(contract, vol, price_type, limit_price, **kwargs)
        results.append(result)
        cum_filled += result['filled']
        cum_cost += result['filled'] * result['avg_price'] if result['filled'] > 0 else 0

        if cum_filled >= target_volume:
            break
        if i < slices - 1:
            time.sleep(interval)

    return {
        'target': target_volume,
        'filled': cum_filled,
        'remain': target_volume - cum_filled,
        'rounds': len(results),
        'avg_price': cum_cost / cum_filled if cum_filled > 0 else 0,
        'slices': results,
        'algorithm': 'TWAP',
        'direction': 'open_long',
        'status': 'done' if cum_filled >= target_volume else 'partial'
    }


# ============================================================
# 统一入口层（期货版）
# ============================================================

def execute_futures_open_long(contract: str, target_volume: int,
                              algorithm: Optional[str] = None,
                              price_type: str = '1', limit_price: float = 0,
                              **kwargs) -> Dict:
    """
    执行期货开多

    示例:
        execute_futures_open_long('rb2410', 10)                       # 直接开多10手
        execute_futures_open_long('rb2410', 10, algorithm='TWAP')     # TWAP开多
        execute_futures_open_long('rb2410', 10, price_type='3', limit_price=3500)  # 限价
    """
    print(f"\n{'=' * 60}")
    print(f"[执行开多] {contract} 目标:{target_volume}手, 算法:{algorithm or '直通'}")
    print(f"{'=' * 60}")

    if algorithm == 'TWAP':
        return twap_open_long(contract, target_volume, price_type, limit_price, **kwargs)
    else:
        return buy_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)


def execute_futures_close_long(contract: str, target_volume: int,
                               algorithm: Optional[str] = None,
                               price_type: str = '1', limit_price: float = 0,
                               **kwargs) -> Dict:
    """执行期货平多"""
    print(f"\n{'=' * 60}")
    print(f"[执行平多] {contract} 目标:{target_volume}手, 算法:{algorithm or '直通'}")
    print(f"{'=' * 60}")

    if algorithm == 'TWAP':
        # 简化：直接调用，不单独写TWAP平多函数
        return sell_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)
    else:
        return sell_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)


def execute_futures_open_short(contract: str, target_volume: int,
                               algorithm: Optional[str] = None,
                               price_type: str = '1', limit_price: float = 0,
                               **kwargs) -> Dict:
    """执行期货开空"""
    print(f"\n{'=' * 60}")
    print(f"[执行开空] {contract} 目标:{target_volume}手, 算法:{algorithm or '直通'}")
    print(f"{'=' * 60}")

    if algorithm == 'TWAP':
        return short_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)
    else:
        return short_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)


def execute_futures_close_short(contract: str, target_volume: int,
                                algorithm: Optional[str] = None,
                                price_type: str = '1', limit_price: float = 0,
                                **kwargs) -> Dict:
    """执行期货平空"""
    print(f"\n{'=' * 60}")
    print(f"[执行平空] {contract} 目标:{target_volume}手, 算法:{algorithm or '直通'}")
    print(f"{'=' * 60}")

    if algorithm == 'TWAP':
        return cover_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)
    else:
        return cover_futures_with_retry(contract, target_volume, price_type, limit_price, **kwargs)


def execute_futures_spread(contract1: str, contract2: str,
                           volume1: int, volume2: int,
                           direction: str = 'long_short',
                           price_type: str = '1', limit_price: float = 0,
                           **kwargs) -> Dict:
    """
    执行期货套利（开仓）

    参数:
        contract1: 近月合约
        contract2: 远月合约
        volume1: 近月手数
        volume2: 远月手数
        direction: 'long_short'（多近空远）/ 'short_long'（空近多远）

    示例:
        execute_futures_spread('rb2410', 'rb2501', 5, 5, 'long_short')
    """
    print(f"\n{'=' * 60}")
    print(f"[执行套利] {contract1} vs {contract2} {direction}")
    print(f"{'=' * 60}")

    results = {}

    if direction == 'long_short':
        # 多近月，空远月
        results['leg1'] = execute_futures_open_long(contract1, volume1, None, price_type, limit_price, **kwargs)
        results['leg2'] = execute_futures_open_short(contract2, volume2, None, price_type, limit_price, **kwargs)
    elif direction == 'short_long':
        # 空近月，多远月
        results['leg1'] = execute_futures_open_short(contract1, volume1, None, price_type, limit_price, **kwargs)
        results['leg2'] = execute_futures_open_long(contract2, volume2, None, price_type, limit_price, **kwargs)
    else:
        print(f"[执行套利] 未知方向: {direction}")
        return {'status': 'error'}

    return {
        'direction': direction,
        'leg1': results['leg1'],
        'leg2': results['leg2'],
        'status': 'done'
    }


# ============================================================
# 导出清单
# ============================================================

__all__ = [
    'DEFAULT_CONFIG',
    'T0_CONFIG',
    'execute_futures_open_long',
    'execute_futures_close_long',
    'execute_futures_open_short',
    'execute_futures_close_short',
    'execute_futures_spread',
    'buy_futures_with_retry',
    'sell_futures_with_retry',
    'short_futures_with_retry',
    'cover_futures_with_retry',
    'twap_open_long',
    'place_order_futures',
    'get_futures_price',
    'get_futures_position',
    'get_futures_available',
    'is_futures_trading_hours',
    'parse_futures_code',
    'get_contract_multiplier',
]