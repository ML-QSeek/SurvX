# -*- coding: utf-8 -*-
"""
迅投QMT股票版交易脚本 - 适配进程池版本 - 修复版
继承自ScriptMain接口
支持前端消息推送
修复多进程环境下的线程启动问题
"""

import os
import requests
import socketio
import json
import time
import datetime
import copy
import threading
import dbf
from dbfread import DBF
import logging
import traceback
import math
import sqlite3
from typing import List, Dict, Any, Optional, Callable

# 交易所代码
M_CODE_DICT = {
    "上交所": "SHSE", "深交所": "SZSE", "大商所": "DCE",
    "郑商所": "CZCE", "中金所": "CFFEX", "上期所": "SHFE",
    "能源交易中心": "INE", "广期所": "GFEX", "上金所": "SGE"
}

# 默认交易配置
DEFAULT_CONFIG = {
    'wait_seconds': 30,
    'stop_abs': 100,
    'stop_ratio': 0.05,
    'close_minutes': 5,
    'first_ratio': 0.95,
    'final_wait': 10,
}


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_now(TimeItem=None):
    if TimeItem == "Stamp":
        tvar = int(time.time())
    elif TimeItem == "DateTime":
        tvar = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif TimeItem == "Date":
        tvar = datetime.datetime.now().strftime("%Y-%m-%d")
    elif TimeItem == "YMDHMS":
        tvar = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return tvar


def check_authority(User, item, server_url):
    tempflag = 0
    Today = get_now(TimeItem="Date")
    Sub_Field = {
        'sflag': 'auth',
        'sid': '_04',
        'username': User,
        'Authority': item,
        'date': Today,
    }
    r = requests.post(server_url, data=Sub_Field)
    rtext = r.text.strip()[1:]
    rtext = json.loads(rtext)
    if rtext != 0:
        tempflag = 1
    return tempflag


##############交易#############
# 单笔委托（原版平移）
def place_order(stock_code: str, volume: int, direction: str,
                mq_dir: str, account_id: str,
                price_type: str = '1', limit_price: float = 0,
                send_func: Optional[Callable] = None) -> bool:
    if volume <= 0:
        return False
    volume = (volume // 100) * 100
    if volume <= 0:
        return False
    order_type = '23' if direction == 'buy' else '24'
    orderset = (order_type, price_type, str(limit_price), stock_code,
                str(volume), account_id, '49', '2')
    order_file = os.path.join(mq_dir, 'XT_DBF_ORDER.dbf')
    if not os.path.exists(order_file):
        msg = f"委托文件不存在: {order_file}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "error",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        return False
    rORDER = dbf.Table(order_file).open(mode=dbf.READ_WRITE)
    rORDER.append(orderset)
    rORDER.close()
    msg = f"[下单] {direction} {stock_code} {volume}股"
    print(msg)
    if send_func:
        send_func({
            "type": "trade",
            "level": "info",
            "message": msg,
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {"stock_code": stock_code, "volume": volume, "direction": direction}
        })
    return True


# 撤销委托（原版平移）
def cancel_order(orderid, mq_dir, account_id, send_func: Optional[Callable] = None):
    order_file = os.path.join(mq_dir, 'XT_DBF_ORDER.dbf')
    if os.path.exists(order_file):
        rORDER = dbf.Table(order_file).open(mode=dbf.READ_WRITE)
        corderset = ('cancel_order', account_id, orderid)
        rORDER.append(corderset)
        rORDER.close()
        msg = f"[撤单] 合同编号: {orderid}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "info",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"order_id": orderid}
            })
    else:
        msg = f"委托文件不存在: {order_file}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "error",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
    return None


# 全部撤单（原版平移）
def all_cancel_order(mq_dir, account_id, out_dir, send_func: Optional[Callable] = None):
    try:
        tdate0 = datetime.datetime.now().strftime("%Y%m%d")
        wwtcxlist = get_wtcx(out_dir, account_id, tdate0)
        cancelled_count = 0
        for item in wwtcxlist:
            if item['委托状态'] != '已成':
                cancel_order(item['合同编号'], mq_dir, account_id, send_func)
                cancelled_count += 1
        msg = f"[撤单] 全部撤单完成，共撤销 {cancelled_count} 笔"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "success",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"cancelled_count": cancelled_count}
            })
    except Exception as e:
        msg = f"[撤单] 失败: {e}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "error",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e)
            })


def get_order(n, out_dir, account_id):
    order_file = os.path.join(out_dir, 'XT_DBF_ORDER.dbf')
    orderlist = []
    if os.path.exists(order_file):
        ORDER = DBF(order_file, load=True, encoding='gbk')
        fn = 0
        for record in ORDER:
            if fn == n:
                tdict = {'order_type': record['order_type'], 'price_type': record['price_type'],
                        'stock_code': record['stock_code'], 'volume': record['volume'],
                        'account_id': record['account_id']}
                orderlist.append(tdict)
                break
            else:
                fn += 1
    return orderlist


def get_orderresult(n, out_dir, account_id):
    order_result_file = os.path.join(out_dir, 'XT_DBF_ORDER_result.dbf')
    orderresultlist = []
    if os.path.exists(order_result_file):
        ORDERResult = DBF(order_result_file, load=True, encoding='gbk')
        fn = 0
        for record in ORDERResult:
            if fn == n:
                tdict = {'orderId': record['orderId'], 'message': record['message'],
                        'status': record['status'], 'taskMsg': record['taskMsg'],
                        'orderNum': record['orderNum']}
                orderresultlist.append(tdict)
                break
            else:
                fn += 1
    return orderresultlist


def get_cctj(out_dir, account_id, date_str):
    cctj_file = os.path.join(out_dir, f'XT_CCTJ_Stock_{date_str}.dbf')
    cctjlist = []
    if os.path.exists(cctj_file):
        CCTJ = DBF(cctj_file, load=True, encoding='gbk')
        for record in CCTJ:
            tdict = {'市场代码': record['市场代码'], '市场名称': record['市场名称'],
                    '证券代码': record['证券代码'], '证券名称': record['证券名称'],
                    '当前拥股': record['当前拥股'], '持仓成本': record['持仓成本'],
                    '成本价': record['成本价'], '市值': record['市值'],
                    '可用数量': record['可用数量'], '当日涨幅': record['当日涨幅'],
                    '昨夜拥股': record['昨夜拥股'], '最新价': record['最新价']}
            cctjlist.append(tdict)
    return cctjlist


def get_cjcx(out_dir, account_id, date_str):
    cjcx_file = os.path.join(out_dir, f'XT_CJCX_Stock_{date_str}.dbf')
    cjcxlist = []
    if os.path.exists(cjcx_file):
        CJCX = DBF(cjcx_file, load=True, encoding='gbk')
        for record in CJCX:
            tdict = {'资金名称': record['资金账号'], '任务编号': record['任务编号'],
                    '合同编号': record['合同编号'], '成交编号': record['成交编号'],
                    '证券代码': record['证券代码'], '成交数量': record['成交数量'],
                    '成交价格': record['成交价格'], '成交金额': record['成交金额'],
                    '手续费': record['手续费'], '订单编号': record['订单编号'],
                    '市场名称': record.get('证券市场', '')}
            cjcxlist.append(tdict)
    return cjcxlist


def get_wtcx(out_dir, account_id, date_str):
    wtcx_file = os.path.join(out_dir, f'XT_WTCX_Stock_{date_str}.dbf')
    wtcxlist = []
    if os.path.exists(wtcx_file):
        WTCX = DBF(wtcx_file, load=True, encoding='gbk')
        for record in WTCX:
            tdict = {'资金账号': record['资金账号'], '合同编号': record['合同编号'],
                    '证券代码': record['证券代码'], '委托量': record['委托量'],
                    '委托状态': record['委托状态'], '成交数量': record['成交数量'],
                    '委托剩余量': record['委托剩余量'], '成交均价': record['成交均价'],
                    '订单编号': record['订单编号'], '任务编号': record['任务编号']}
            wtcxlist.append(tdict)
    return wtcxlist


def get_zjcx(out_dir, account_id, date_str):
    zjcx_file = os.path.join(out_dir, f'XT_ZJCX_Stock_{date_str}.dbf')
    zjcxdict = {}
    if os.path.exists(zjcx_file):
        ZJCX = DBF(zjcx_file, load=True, encoding='gbk')
        for record in ZJCX:
            accid = record['资金账号']
            if str(accid) == str(account_id):
                tdict = {'总资产': record['总资产'], '可用金额': record['可用金额'],
                        '手续费': record['手续费'], '盈亏': record['盈亏'],
                        '总市值': record['总市值']}
                zjcxdict[accid] = tdict
    return zjcxdict


# ============================================================
# 数据库管理（原版平移）
# ============================================================
def init_trade_db(account_id):
    """初始化交易数据库，如果不存在则创建"""
    data_dir = '../../data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    db_path = os.path.join(data_dir, f'{account_id}.db')
    
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS note (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                item TEXT NOT NULL,
                note TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print(f"数据库创建成功: {db_path}")
    else:
        print(f"数据库已存在: {db_path}")
    
    return db_path


def save_record(account_id, litem, lnote):
    """保存持仓记录到数据库"""
    db_path = os.path.join('../../data', f'{account_id}.db')
    
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        current_time = get_now(TimeItem="DateTime")
        
        if litem in ['result', 'position']:
            xnote = json.dumps(lnote, ensure_ascii=False)
        else:
            xnote = lnote
        
        cursor.execute(
            'INSERT INTO note (datetime, item, note) VALUES (?, ?, ?)',
            (current_time, litem, xnote)
        )
        conn.commit()
        conn.close()
        print(f"持仓记录已保存: {current_time}")
        return True
    except Exception as e:
        print(f"保存持仓记录失败: {e}")
        return False


# ============================================================
# 行情相关（原版平移）
# ============================================================
def get_price(stock_code: str) -> float:
    """获取行情最新报价，失败返回0"""
    try:
        response = requests.get(
            'http://10.10.98.51:3215/quote',
            params={'type': 'stock', 'symbol': stock_code},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        price = float(data['price'])
        if price <= 0:
            print(f"[行情] {stock_code} 价格异常: {price}")
            return 0
        return price
    except requests.exceptions.Timeout:
        print(f"[行情] {stock_code} 请求超时")
        return 0
    except requests.exceptions.RequestException as e:
        print(f"[行情] {stock_code} 请求失败: {e}")
        return 0
    except (KeyError, ValueError, TypeError) as e:
        print(f"[行情] {stock_code} 解析失败: {e}")
        return 0


def _is_limit_up(stock_code: str) -> bool:
    """是否涨停"""
    price = get_price(stock_code)
    if price <= 0:
        return False
    # TODO: 获取昨日收盘价，计算涨停价
    # 涨停价 = 昨日收盘价 * 1.1（近似，实际要取整）
    return False


def _is_limit_down(stock_code: str) -> bool:
    """是否跌停"""
    price = get_price(stock_code)
    if price <= 0:
        return False
    # TODO: 获取昨日收盘价，计算跌停价
    return False


def is_close_soon(minutes: int = 5) -> bool:
    """是否临近收盘"""
    now = datetime.datetime.now()
    close_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return now >= close_time or (close_time - now).total_seconds() <= minutes * 60


def round_lot(vol: int) -> int:
    """取整手数"""
    return max(0, (int(vol) // 100) * 100)


def get_holdings(out_dir, account_id, date_str) -> dict:
    """获取当前持仓 {stock_code: 可用数量}"""
    try:
        positions = get_cctj(out_dir, account_id, date_str)
        result = {}
        for item in positions:
            code = item['市场代码'] + item['证券代码']
            available = int(item['可用数量'])
            if available > 0:
                result[code] = available
        return result
    except Exception as e:
        print(f"[持仓] 查询失败: {e}")
        return {}


# ============================================================
# 执行层（原版平移）
# ============================================================
def execute_round(tasks: dict, mq_dir: str, account_id: str, out_dir: str,
                  price_type: str, limit_price: float, wait_seconds: int,
                  send_func: Optional[Callable] = None) -> dict:
    """执行一轮：下单 -> 等待 -> 全撤 -> 查询成交"""
    if not tasks:
        return {}

    # 下单
    for code, task in tasks.items():
        vol = round_lot(task['volume'])
        if vol > 0:
            place_order(code, vol, task['direction'], mq_dir, account_id, 
                       price_type, limit_price, send_func)

    # 等待
    wait_msg = f"[执行] 等待 {wait_seconds} 秒..."
    print(wait_msg)
    if send_func:
        send_func({
            "type": "trade",
            "level": "info",
            "message": wait_msg,
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {"wait_seconds": wait_seconds}
        })
    time.sleep(wait_seconds)
    
    # 全部撤单
    all_cancel_order(mq_dir, account_id, out_dir, send_func)
    time.sleep(1)

    # 查询成交
    result = {}
    try:
        TDate0 = datetime.datetime.now().strftime("%Y%m%d")
        cjcxlist = get_cjcx(out_dir, account_id, TDate0)
        for item in cjcxlist:
            code = item.get('市场名称', '') + item['证券代码']
            if code not in tasks:
                continue
            if code not in result:
                result[code] = {'filled': 0, 'cost': 0}
            result[code]['filled'] += int(item['成交数量'])
            result[code]['cost'] += float(item['成交金额'])
        
        if result:
            msg = f"[执行] 本轮成交 {len(result)} 只股票"
            print(msg)
            if send_func:
                send_func({
                    "type": "trade",
                    "level": "success",
                    "message": msg,
                    "timestamp": get_now(TimeItem="DateTime"),
                    "data": {"result": result}
                })
    except Exception as e:
        msg = f"[成交] 查询失败: {e}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "error",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e)
            })

    return {k: v for k, v in result.items() if v['filled'] > 0}


def execute_mixed(sell_targets: dict, buy_targets: dict,
                  mq_dir: str, account_id: str, out_dir: str,
                  price_type: str, limit_price: float, config: dict,
                  candidates: list = None,
                  send_func: Optional[Callable] = None) -> dict:
    """
    卖和买每轮同时进行，卖出回款滚入下一轮可用资金
    涨停买不到跳过，用候选池替换
    跌停卖不掉跳过
    """
    wait_seconds = config.get('wait_seconds', 30)
    stop_abs = config.get('stop_abs', 100)
    stop_ratio = config.get('stop_ratio', 0.05)
    close_minutes = config.get('close_minutes', 5)
    first_ratio = config.get('first_ratio', 0.95)
    final_wait = config.get('final_wait', 10)

    TDate0 = datetime.datetime.now().strftime("%Y%m%d")

    sell_cum = {code: 0 for code in sell_targets}
    sell_cum_cost = {code: 0 for code in sell_targets}
    buy_cum = {code: 0 for code in buy_targets}
    buy_cum_cost = {code: 0 for code in buy_targets}

    abandoned_sells = set()
    abandoned_buys = set()
    cand_idx = 0

    initial_cash = 0
    try:
        wzjcxdict = get_zjcx(out_dir, account_id, TDate0)
        if account_id in wzjcxdict:
            initial_cash = float(wzjcxdict[account_id]['可用金额'])
    except:
        pass

    total_sell_proceeds = 0
    is_first_round = True
    round_num = 0

    while True:
        round_num += 1
        if is_close_soon(close_minutes):
            msg = f"[执行] 收盘前{close_minutes}分钟，强制停止"
            print(msg)
            if send_func:
                send_func({
                    "type": "trade",
                    "level": "warning",
                    "message": msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
            break

        # ---- 本轮卖单 ----
        round_sells = {}
        sell_final_list = []

        for code, target in sell_targets.items():
            if code in abandoned_sells:
                continue
            remain = target - sell_cum[code]
            if remain <= 0:
                continue
            stop_rel = target * stop_ratio
            if remain <= stop_abs or remain <= stop_rel:
                sell_final_list.append(code)
                continue

            if _is_limit_down(code):
                msg = f"[卖] {code} 跌停，跳过"
                print(msg)
                if send_func:
                    send_func({
                        "type": "trade",
                        "level": "warning",
                        "message": msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {"stock_code": code}
                    })
                abandoned_sells.add(code)
                continue

            vol = round_lot(remain)
            if vol > 0:
                round_sells[code] = {'direction': 'sell', 'volume': vol}

        # ---- 可用资金 ----
        available_cash = initial_cash + total_sell_proceeds - sum(buy_cum_cost.values())

        # ---- 本轮买单 ----
        round_buys = {}
        buy_final_list = []

        if available_cash > 0 and buy_targets:
            buy_need = {}
            total_need = 0
            for code, target in buy_targets.items():
                if code in abandoned_buys:
                    continue
                remain = target - buy_cum[code]
                if remain <= 0:
                    continue
                stop_rel = target * stop_ratio
                if remain <= stop_abs or remain <= stop_rel:
                    buy_final_list.append(code)
                    continue

                price = get_price(code)
                if _is_limit_up(code):
                    skipped_amount = remain * price if price > 0 else 0
                    if skipped_amount > 0:
                        total_need += skipped_amount
                        buy_need[code] = {'vol': 0, 'need': skipped_amount, 'skipped': True}
                    abandoned_buys.add(code)
                    msg = f"[买] {code} 涨停，跳过，剩余{remain}股约{skipped_amount:.2f}元转候选"
                    print(msg)
                    if send_func:
                        send_func({
                            "type": "trade",
                            "level": "warning",
                            "message": msg,
                            "timestamp": get_now(TimeItem="DateTime"),
                            "data": {"stock_code": code, "remain": remain, "amount": skipped_amount}
                        })
                    continue

                if price <= 0:
                    continue
                
                order_vol = round_lot(int(remain * first_ratio)) if is_first_round else round_lot(remain)
                if order_vol <= 0:
                    continue

                need = order_vol * price
                buy_need[code] = {'vol': order_vol, 'need': need, 'skipped': False}
                total_need += need

            if total_need > available_cash and total_need > 0:
                ratio = available_cash / total_need
                for code, info in buy_need.items():
                    if info.get('skipped'):
                        continue
                    scaled = round_lot(int(info['vol'] * ratio))
                    if scaled > 0:
                        round_buys[code] = {'direction': 'buy', 'volume': scaled}
            else:
                for code, info in buy_need.items():
                    if not info.get('skipped') and info['vol'] > 0:
                        round_buys[code] = {'direction': 'buy', 'volume': info['vol']}

        # ---- 候选替换 ----
        if candidates and abandoned_buys:
            for code in list(abandoned_buys):
                remain = buy_targets[code] - buy_cum[code]
                if remain <= 0:
                    continue
                price = get_price(code)
                if price <= 0:
                    continue
                replace_amount = remain * price

                while replace_amount > 0 and cand_idx < len(candidates):
                    cand_code = candidates[cand_idx]
                    if _is_limit_up(cand_code):
                        msg = f"[候选] {cand_code} 也涨停，换下一个"
                        print(msg)
                        if send_func:
                            send_func({
                                "type": "trade",
                                "level": "warning",
                                "message": msg,
                                "timestamp": get_now(TimeItem="DateTime"),
                                "data": {"stock_code": cand_code}
                            })
                        cand_idx += 1
                        continue

                    cand_price = get_price(cand_code)
                    if cand_price <= 0:
                        cand_idx += 1
                        continue

                    cand_vol = round_lot(int(replace_amount / cand_price))
                    if cand_vol <= 0:
                        cand_idx += 1
                        continue

                    cand_need = cand_vol * cand_price
                    if cand_code not in round_buys:
                        round_buys[cand_code] = {'direction': 'buy', 'volume': 0}
                    round_buys[cand_code]['volume'] += cand_vol
                    msg = f"[候选] {code} → {cand_code} {cand_vol}股 ({cand_need:.2f}元)"
                    print(msg)
                    if send_func:
                        send_func({
                            "type": "trade",
                            "level": "info",
                            "message": msg,
                            "timestamp": get_now(TimeItem="DateTime"),
                            "data": {"from": code, "to": cand_code, "volume": cand_vol, "amount": cand_need}
                        })
                    replace_amount -= cand_need
                    if replace_amount <= 0:
                        break
                    cand_idx += 1

        # ---- 合并本轮 ----
        round_tasks = {}
        round_tasks.update(round_sells)
        round_tasks.update(round_buys)

        if not round_tasks and not sell_final_list and not buy_final_list:
            if abandoned_sells == set(sell_targets.keys()) and abandoned_buys == set(buy_targets.keys()):
                break
            if not any(code not in abandoned_sells and sell_cum[code] < sell_targets[code]
                       for code in sell_targets) and \
               not any(code not in abandoned_buys and buy_cum[code] < buy_targets[code]
                       for code in buy_targets) and \
               not candidates:
                break

        if not round_tasks:
            break

        n_sell = len(round_sells)
        n_buy = len(round_buys)
        round_label = '首' if is_first_round else '续'
        msg = f"\n[执行] 第{round_label}{round_num}轮: 卖{n_sell}只 买{n_buy}只, 可用{available_cash:.2f}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "info",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"round": round_num, "sell_count": n_sell, "buy_count": n_buy, 
                        "available_cash": available_cash, "is_first": is_first_round}
            })
        is_first_round = False

        round_result = execute_round(round_tasks, mq_dir, account_id, out_dir,
                                     price_type, limit_price, wait_seconds, send_func)

        for code, res in round_result.items():
            if code in sell_targets:
                sell_cum[code] += res['filled']
                sell_cum_cost[code] += res['cost']
                total_sell_proceeds += res['cost']
                msg = f"[卖] {code} 本轮{res['filled']}股, 累计{sell_cum[code]}/{sell_targets[code]}"
                print(msg)
                if send_func:
                    send_func({
                        "type": "trade",
                        "level": "info",
                        "message": msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {"stock_code": code, "filled": res['filled'], 
                                "cumulative": sell_cum[code], "target": sell_targets[code]}
                    })
            elif code in buy_targets or (candidates and code in candidates):
                if code not in buy_cum:
                    buy_cum[code] = 0
                    buy_cum_cost[code] = 0
                buy_cum[code] += res['filled']
                buy_cum_cost[code] += res['cost']
                msg = f"[买] {code} 本轮{res['filled']}股, 累计{buy_cum[code]}"
                print(msg)
                if send_func:
                    send_func({
                        "type": "trade",
                        "level": "info",
                        "message": msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {"stock_code": code, "filled": res['filled'], 
                                "cumulative": buy_cum[code]}
                    })

    # ---- 兜底 ----
    final_tasks = {}

    for code in sell_final_list:
        if code in abandoned_sells:
            continue
        remain = sell_targets[code] - sell_cum[code]
        vol = round_lot(remain)
        if vol > 0 and not _is_limit_down(code):
            final_tasks[code] = {'direction': 'sell', 'volume': vol}

    available_cash = initial_cash + total_sell_proceeds - sum(buy_cum_cost.values())
    for code in buy_final_list:
        if code in abandoned_buys:
            continue
        remain = buy_targets[code] - buy_cum[code]
        price = get_price(code)
        if price > 0 and not _is_limit_up(code):
            max_vol = int(available_cash / price)
            vol = round_lot(min(remain, max_vol))
            if vol > 0:
                final_tasks[code] = {'direction': 'buy', 'volume': vol}
                available_cash -= vol * price

    if final_tasks:
        msg = f"\n[执行] 兜底: {len(final_tasks)}只"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "info",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"task_count": len(final_tasks)}
            })
        final_result = execute_round(final_tasks, mq_dir, account_id, out_dir,
                                     price_type, limit_price, final_wait, send_func)
        for code, res in final_result.items():
            if code in sell_targets:
                sell_cum[code] += res['filled']
                sell_cum_cost[code] += res['cost']
            elif code in buy_targets or (candidates and code in candidates):
                if code not in buy_cum:
                    buy_cum[code] = 0
                    buy_cum_cost[code] = 0
                buy_cum[code] += res['filled']
                buy_cum_cost[code] += res['cost']

    # 汇总结果
    msg = f"[执行] 交易完成！卖出{len(sell_targets)}只，买入{len(buy_targets)}只"
    print(msg)
    if send_func:
        send_func({
            "type": "trade",
            "level": "success",
            "message": msg,
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {
                "sell_count": len(sell_targets),
                "buy_count": len(buy_targets),
                "sell_details": sell_cum,
                "buy_details": buy_cum
            }
        })

    sell_result = {code: {'target': sell_targets[code], 'filled': sell_cum[code],
                           'cost': sell_cum_cost[code]} for code in sell_targets}
    buy_result = {code: {'target': buy_targets.get(code, 0), 'filled': buy_cum.get(code, 0),
                          'cost': buy_cum_cost.get(code, 0)} for code in
                  set(list(buy_targets.keys()) + list(buy_cum.keys()))}

    return {'sell': sell_result, 'buy': buy_result}


def execute(orders: list, mq_dir: str, account_id: str, out_dir: str,
            price_type: str = '1', limit_price: float = 0,
            algorithm: str = None, config: dict = None,
            candidates: list = None,
            send_func: Optional[Callable] = None) -> dict:
    """统一执行入口"""
    if config is None:
        config = DEFAULT_CONFIG

    TDate0 = datetime.datetime.now().strftime("%Y%m%d")

    sell_targets = {}
    buy_targets = {}

    for item in orders:
        code = item[0]
        direction = item[1].upper() if isinstance(item[1], str) else item[1]
        vol = item[2]

        if direction in ('S', 'SELL'):
            sell_targets[code] = vol
        else:
            buy_targets[code] = vol

    holdings = get_holdings(out_dir, account_id, TDate0)
    for code in list(sell_targets.keys()):
        available = holdings.get(code, 0)
        if sell_targets[code] > available:
            sell_targets[code] = available
        if sell_targets[code] <= 0:
            del sell_targets[code]

    msg = f"\n[执行] 卖出: {len(sell_targets)}只, 买入: {len(buy_targets)}只"
    print(msg)
    if send_func:
        send_func({
            "type": "trade",
            "level": "info",
            "message": msg,
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {"sell_count": len(sell_targets), "buy_count": len(buy_targets)}
        })
    if candidates:
        msg = f"[执行] 候选池: {candidates}"
        print(msg)
        if send_func:
            send_func({
                "type": "trade",
                "level": "info",
                "message": msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"candidates": candidates}
            })

    return execute_mixed(sell_targets, buy_targets, mq_dir, account_id, out_dir,
                         price_type, limit_price, config, candidates, send_func)


#############收到信息##############
def senddif(BaseDict, username, quant_name, out_dir):
    OrderStatusList = []
    
    try:
        order_status_file = os.path.join(out_dir, 'order_status.csv')
        if os.path.exists(order_status_file):
            with open(order_status_file, 'r', encoding='utf-8') as infile:
                ttxt = infile.read().split('\n')
                i1 = 1
                while i1 < len(ttxt) - 1:
                    tlist = ttxt[i1].split(',')
                    if len(tlist) > 19:
                        OrderStatusList.append([
                            tlist[1], tlist[5], tlist[6], tlist[7], tlist[8], 
                            tlist[11], tlist[12], tlist[13], tlist[18], tlist[19]
                        ])
                    i1 += 1
    except Exception as e:
        print(f"读取交易记录失败: {e}")
    
    if OrderStatusList:
        ttxt = json.dumps(OrderStatusList)
        nnote = f"{username}-{quant_name}-交易记录-{get_now(TimeItem='YMDHMS')}:{ttxt}"
        print(nnote)
    else:
        print("没有成交记录！")
    print("命令执行完毕！")


class ScriptMain:
    """迅投QMT交易脚本主类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        
        self.MQ_USERNAME = config.get("username", "")
        self.MQ_PASSWORD = config.get("password", "")
        self.MQ_QUANT_ID = config.get("quant_id", "")
        self.MQ_QUANT_NAME = config.get("quant_name", "")
        self.MQ_ACCOUNT = config.get("account", "")
        self.MQ_DIR = config.get("mq_dir", "")
        self.OUT_DIR = config.get("out_dir", "")
        self.MQ_ASSETS = config.get("assets", "total")
        self.SERVER_URL = config.get("server_url", "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php")
        self.SOCKETIO_SENDER_URL = config.get("socketio_sender_url", "http://10.10.98.51:3211")
        self.SOCKETIO_RECEIVER_URL = config.get("socketio_receiver_url", "http://10.10.98.51:3210")
        
        self.data_queue = config.get("data_queue", None)
        
        required_params = ["username", "password", "quant_id", "quant_name", "account"]
        missing_params = [p for p in required_params if not self.config.get(p)]
        if missing_params:
            raise ValueError(f"缺少必要参数: {missing_params}")
        
        self.worker_threads = []
        self.sender_thread = None
        self.receiver_thread = None
        self.end_flag = {'endflag': 0}
        
        self.T_DATE_0 = datetime.datetime.now().strftime("%Y%m%d")
        self.T_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
        
        self._in_multiprocess_env = hasattr(self, 'data_queue') and self.data_queue is not None
        self._workers_started = False
        self._init_attempts = 0
        
        self._setup_logging()
        
        if self.OUT_DIR:
            create_directory_if_not_exists(self.OUT_DIR)
        if self.MQ_DIR:
            create_directory_if_not_exists(self.MQ_DIR)
        
        # 初始化数据库
        init_trade_db(self.MQ_ACCOUNT)
        
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": f"初始化迅投QMT交易脚本: {self.MQ_QUANT_NAME}",
            "timestamp": get_now(TimeItem="DateTime"),
            "account": self.MQ_ACCOUNT,
            "strategy": self.MQ_QUANT_NAME,
            "multiprocess_env": self._in_multiprocess_env
        })
        
        self.logger.info(f"初始化迅投QMT交易脚本: {self.MQ_QUANT_NAME}")
        self.logger.info(f"账号: {self.MQ_ACCOUNT}, 用户: {self.MQ_USERNAME}")
    
    def _setup_logging(self):
        script_name = self.config.get("config_name", f"xtqmt_{self.MQ_QUANT_NAME}")
        self.logger = logging.getLogger(f"ScriptMain.{script_name}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            try:
                log_dir = os.path.join("logs", "xtqmt", script_name)
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"{datetime.datetime.now().strftime('%Y%m%d')}.log")
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                console_handler.setFormatter(formatter)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"设置文件日志失败: {e}")
    
    def _send_to_frontend(self, message_dict: Dict[str, Any]):
        if hasattr(self, 'data_queue') and self.data_queue:
            try:
                if 'timestamp' not in message_dict:
                    message_dict['timestamp'] = get_now(TimeItem="DateTime")
                if 'account' not in message_dict:
                    message_dict['account'] = self.MQ_ACCOUNT
                if 'strategy' not in message_dict:
                    message_dict['strategy'] = self.MQ_QUANT_NAME
                message_dict['multiprocess_env'] = self._in_multiprocess_env
                self.data_queue.put(message_dict)
            except Exception as e:
                self.logger.error(f"发送消息到前端失败: {e}")

    # ============================================================
    # 交易执行（交易逻辑来自原版 mqTrader）
    # ============================================================
    def _execute_trade(self, trade_data):
        """执行交易 - 统一入口"""
        self.logger.info("开始执行交易")
        self._send_to_frontend({
            "type": "trade",
            "level": "info",
            "message": "收到交易指令，开始执行",
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        # 保存原始指令到数据库（原版逻辑）
        save_record(self.MQ_ACCOUNT, 'order', trade_data)
        
        try:
            time.sleep(1)
            
            # 获取账户信息
            wzjcxdict = get_zjcx(self.OUT_DIR, self.MQ_ACCOUNT, self.T_DATE_0)
            if self.MQ_ACCOUNT not in wzjcxdict:
                self.logger.error("无法获取账户资金信息")
                self._send_to_frontend({
                    "type": "trade",
                    "level": "error",
                    "message": "无法获取账户资金信息",
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return
            
            totalAssets = float(wzjcxdict[self.MQ_ACCOUNT]['总资产'])
            totalMarketValue = float(wzjcxdict[self.MQ_ACCOUNT]['总市值'])
            
            orderkey, ordervalue = trade_data.split(':', 1)
            #基础策略名称
            bquantname = orderkey.split('-')[0]
            #print(f'基础策略名称:{bquantname}')
            #命令识别字段
            orderfield = orderkey.split('-')[2]
            #print(f'指令识别字段（时间戳）:{orderfield}')
            #拆解ordervalue,命令类型ordertype
            ordertype,temptext0 = ordervalue.split('#', 1)
            #print(f'指令类型:{ordertype}')
            #print(f'指令字段:{temptext0}')
            
            
            self.logger.info(f"指令类型: {ordertype}, 总资产: {totalAssets}")
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": f"指令类型: {ordertype}, 总资产: {totalAssets:.2f}",
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"order_type": ordertype, "total_assets": totalAssets}
            })
            
            # ---- 原版 mqTrader 交易逻辑 ----
            if ordertype == '0':
                # type0: 完整调仓指令
                ordertext = eval(temptext0.replace('#', ','))
                dict0 = {}
                list0 = ordertext['_tqbasket']
                
                for item in list0:
                    dict0[item[0]] = item[1]
                
                HoldTargetList = ordertext['tqbasket']
                houxuan = HoldTargetList.pop(0)
                baoliu = HoldTargetList.pop(0)
                
                BaseDict = {}
                TargetHoldDict = {}
                
                for ix0 in HoldTargetList:
                    fv = ix0[0]
                    fprice = ix0[1]
                    fpos = (ix0[2] / 100) * totalAssets
                    dict0[fv] = fprice
                    TargetHoldDict[fv] = [fprice, fpos]
                    BaseDict[fv] = fprice
                
                holddict = {}
                wcctjlist = get_cctj(self.OUT_DIR, self.MQ_ACCOUNT, self.T_DATE_0)
                
                for tdict in wcctjlist:
                    fv = tdict['市场代码'] + tdict['证券代码']
                    holddict[fv] = [
                        float(tdict['当前拥股']),
                        float(tdict['市值']),
                        float(tdict['最新价']),
                        float(tdict['可用数量'])
                    ]
                    if BaseDict.get(fv) is None:
                        BaseDict[fv] = float(tdict['最新价'])
                
                FList = []
                for (k, v) in TargetHoldDict.items():
                    if k in holddict.keys():
                        Diff = v[1] - holddict.pop(k)[1]
                        if Diff > 0:
                            FList.append([k, "B", math.floor(Diff / v[0] / 100) * 100])
                        elif Diff < 0 and k not in baoliu:
                            FList.append([k, "S", math.floor(-Diff / v[0] / 100) * 100])
                    else:
                        FList.append([k, "B", math.floor(v[1] / v[0] / 100) * 100])
                
                for (k, v) in holddict.items():
                    if k not in baoliu:
                        FList.append([k, "S", math.floor(v[1] / v[2] / 100) * 100])
                
                print('调仓指令：')
                print(FList)
                
                # 保存理论价格
                save_record(self.MQ_ACCOUNT, '调仓理论价格', f'{dict0}')
                
                self._send_to_frontend({
                    "type": "trade",
                    "level": "info",
                    "message": f"生成调仓指令: {len(FList)}条",
                    "timestamp": get_now(TimeItem="DateTime"),
                    "data": {"orders": FList, "candidates": houxuan}
                })
                
                # 传递 send_func 到 execute
                execute(FList, self.MQ_DIR, self.MQ_ACCOUNT, self.OUT_DIR, 
                       candidates=houxuan, send_func=self._send_to_frontend)
                
            elif ordertype == '10':
                # type10: 调仓比例指令
                ordertext = float(temptext0) / 100
                holdratio = float(totalMarketValue / totalAssets) if totalAssets > 0 else 0
                holddiff = holdratio - ordertext
                
                print(f'理论持仓比例:{ordertext}')
                print(f'目前账户持仓比例:{holdratio}')
                
                self._send_to_frontend({
                    "type": "trade",
                    "level": "info",
                    "message": f"调仓比例: 目标{ordertext:.2%}, 当前{holdratio:.2%}",
                    "timestamp": get_now(TimeItem="DateTime")
                })
                
                if holddiff > 0:
                    actual_holdings_list = get_cctj(self.OUT_DIR, self.MQ_ACCOUNT, self.T_DATE_0)
                    selllist = []
                    for item in actual_holdings_list:
                        acode = item['市场代码'] + item['证券代码']
                        gnum = math.floor((float(item['市值']) * holddiff) / float(item['最新价']) / 100) * 100
                        selllist.append([acode, 'S', gnum])
                    
                    # 传递 send_func 到 execute
                    execute(selllist, self.MQ_DIR, self.MQ_ACCOUNT, self.OUT_DIR,
                           send_func=self._send_to_frontend)
                    
            elif ordertype == '20':
                # type20: 简单买卖指令
                ordertext = eval(temptext0.replace('#', ','))
                print(f'收到指令：{ordertext}')
                
                dict0 = {}
                list1 = []
                for text in ordertext:
                    dict0[text[0]] = text[2]
                    lvalue = totalAssets * float(text[3]) / 100
                    lnum = math.floor(lvalue / text[2] / 100) * 100
                    list1.append([text[0], text[1], lnum])
                    print(list1)
                
                # 保存理论价格
                save_record(self.MQ_ACCOUNT, '理论价格',f'{dict0}')
                
                self._send_to_frontend({
                    "type": "trade",
                    "level": "info",
                    "message": f"type20生成指令: {len(list1)}条",
                    "timestamp": get_now(TimeItem="DateTime"),
                    "data": {"orders": list1}
                })
                
                # 传递 send_func 到 execute
                execute(list1, self.MQ_DIR, self.MQ_ACCOUNT, self.OUT_DIR,
                       send_func=self._send_to_frontend)
            
            self.logger.info("交易执行完成")
            self._send_to_frontend({
                "type": "trade",
                "level": "success",
                "message": "交易执行完成",
                "timestamp": get_now(TimeItem="DateTime")
            })
            
        except Exception as e:
            self.logger.error(f"执行交易异常: {e}")
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": f"执行交易异常: {e}",
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            traceback.print_exc()

    def run_iteration(self):
        try:
            if not self._workers_started and self._init_attempts < 3:
                self.logger.info(f"尝试启动工作线程 (尝试次数: {self._init_attempts + 1})")
                self._init_attempts += 1
                
                if self._init_attempts == 1:
                    time.sleep(2)
                    
                if not self.running:
                    self.running = True
                
                self._start_worker_threads()
                self._workers_started = True
                
                self._send_to_frontend({
                    "type": "system",
                    "level": "success",
                    "message": "工作线程已启动",
                    "timestamp": get_now(TimeItem="DateTime")
                })
            
            if self._workers_started:
                dead_threads = []
                for thread in self.worker_threads:
                    if not thread.is_alive():
                        dead_threads.append(thread)
                
                for thread in dead_threads:
                    self.worker_threads.remove(thread)
                    if "Sender" in thread.name:
                        new_thread = threading.Thread(target=self._sender_worker_safe, name=thread.name, daemon=True)
                        new_thread.start()
                        self.worker_threads.append(new_thread)
                    elif "Receiver" in thread.name:
                        new_thread = threading.Thread(target=self._receiver_worker_safe, name=thread.name, daemon=True)
                        new_thread.start()
                        self.worker_threads.append(new_thread)
                    elif "Monitor" in thread.name:
                        new_thread = threading.Thread(target=self._monitor_worker_safe, name=thread.name, daemon=True)
                        new_thread.start()
                        self.worker_threads.append(new_thread)
            
            if self.end_flag['endflag'] == 1:
                self.cleanup()
            
        except Exception as e:
            self.logger.error(f"运行迭代失败: {e}")
    
    def handle_command(self, command: Dict):
        cmd = command.get("command", "")
        data = command.get("data", {})
        
        if cmd == "start":
            return self._start()
        elif cmd == "stop":
            return self._stop()
        elif cmd == "pause":
            return self._pause_trading()
        elif cmd == "resume":
            return self._resume_trading()
        elif cmd == "restart":
            return self._restart()
        elif cmd == "update_config":
            return self._update_config(data)
        elif cmd == "get_status":
            return self._get_status()
        elif cmd == "execute_trade":
            return self._execute_trade_command(data)
        elif cmd == "cancel_all_orders":
            return self._cancel_all_orders()
        else:
            return {"success": False, "message": f"未知命令: {cmd}"}
    
    def _start(self):
        if self.running:
            return {"success": False, "message": "脚本已在运行中"}
        try:
            self.running = True
            self._start_worker_threads()
            self._send_to_frontend({
                "type": "system",
                "level": "success",
                "message": "迅投QMT交易脚本启动成功",
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": True, "message": "启动成功"}
        except Exception as e:
            self.running = False
            return {"success": False, "message": f"启动失败: {str(e)}"}
    
    def _stop(self):
        if not self.running:
            return {"success": False, "message": "脚本未在运行"}
        try:
            self.running = False
            self.end_flag['endflag'] = 1
            for thread in self.worker_threads:
                if thread.is_alive():
                    thread.join(timeout=3)
            self.worker_threads.clear()
            self._send_to_frontend({
                "type": "system",
                "level": "success",
                "message": "迅投QMT交易脚本已停止",
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": True, "message": "已停止"}
        except Exception as e:
            return {"success": False, "message": f"停止失败: {str(e)}"}
    
    def _restart(self):
        self._stop()
        time.sleep(1)
        return self._start()
    
    def _pause_trading(self):
        self.end_flag['endflag'] = 1
        return {"success": True, "message": "交易已暂停"}
    
    def _resume_trading(self):
        self.end_flag['endflag'] = 0
        return {"success": True, "message": "交易已恢复"}
    
    def _cancel_all_orders(self):
        try:
            all_cancel_order(self.MQ_DIR, self.MQ_ACCOUNT, self.OUT_DIR, self._send_to_frontend)
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": "已取消所有订单",
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": True, "message": "已取消所有订单"}
        except Exception as e:
            return {"success": False, "message": f"取消失败: {str(e)}"}
    
    def _execute_trade_command(self, data: Dict):
        trade_data = data.get("trade_data", "")
        if not trade_data:
            return {"success": False, "message": "交易数据为空"}
        self._execute_trade(trade_data)
        return {"success": True, "message": "交易命令已执行"}
    
    def _start_worker_threads(self):
        self.sender_thread = threading.Thread(target=self._sender_worker_safe, name=f"Sender_{self.MQ_QUANT_NAME}", daemon=True)
        self.sender_thread.start()
        self.worker_threads.append(self.sender_thread)
        
        self.receiver_thread = threading.Thread(target=self._receiver_worker_safe, name=f"Receiver_{self.MQ_QUANT_NAME}", daemon=True)
        self.receiver_thread.start()
        self.worker_threads.append(self.receiver_thread)
        
        monitor_thread = threading.Thread(target=self._monitor_worker_safe, name=f"Monitor_{self.MQ_QUANT_NAME}", daemon=True)
        monitor_thread.start()
        self.worker_threads.append(monitor_thread)
    
    def _sender_worker_safe(self):
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries and self.running and self.end_flag['endflag'] == 0:
            try:
                self._sender_worker_impl()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    break
    
    def _sender_worker_impl(self):
        apush = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1, reconnection_delay_max=5)
        
        @apush.event
        def connect():
            self.logger.info('SocketIO连接已建立')
        
        @apush.event
        def disconnect():
            self.logger.info('从服务器断开连接')
        
        @apush.on('exit')
        def handle_exit():
            self.end_flag['endflag'] = 1
        
        apush.connect(self.SOCKETIO_SENDER_URL)
        
        znote = f"{self.MQ_USERNAME}-{self.MQ_QUANT_NAME}-账户注册-{get_now(TimeItem='YMDHMS')}:{self.MQ_QUANT_ID}#{self.MQ_ACCOUNT}#{self.MQ_USERNAME}#{self.MQ_QUANT_NAME}#{self.MQ_ASSETS}"
        apush.emit('fromWebClient', {'mess': znote})
        
        last_send_time = 0
        while self.running and self.end_flag['endflag'] == 0:
            current_time = time.time()
            if current_time - last_send_time >= 5:
                self._send_account_data(apush)
                last_send_time = current_time
            time.sleep(1)
        
        apush.disconnect()
    
    def _send_account_data(self, apush):
        try:
            zjcx_file = os.path.join(self.OUT_DIR, f'XT_ZJCX_Stock_{self.T_DATE_0}.dbf')
            if os.path.exists(zjcx_file):
                ZJCX = DBF(zjcx_file, load=True, encoding='gbk')
                for record in ZJCX:
                    if str(record['资金账号']) == str(self.MQ_ACCOUNT):
                        ageneral = [float(record['总资产']), float(record['可用金额']), float(record['总市值'])]
                        nnote1 = f"{self.MQ_ACCOUNT}-账户总览-{get_now(TimeItem='YMDHMS')}:{json.dumps(ageneral).replace(' ', '')}"
                        apush.emit('fromWebClient', {'mess': nnote1})
        except Exception as e:
            self.logger.error(f"发送账户数据异常: {e}")
    
    def _receiver_worker_safe(self):
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries and self.running and self.end_flag['endflag'] == 0:
            try:
                self._receiver_worker_impl()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    break
    
    def _receiver_worker_impl(self):
        trec = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1, reconnection_delay_max=5)
        
        @trec.event
        def connect():
            self.logger.info('mqReceiver连接已建立')
        
        @trec.event
        def disconnect():
            self.logger.info('从mqReceiver服务器断开连接')
        
        @trec.on(self.MQ_QUANT_NAME)
        def on_message(data):
            print('mqReceiver：', data)
            self.logger.info(f'收到交易指令')
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": "收到新的交易指令",
                "timestamp": get_now(TimeItem="DateTime")
            })
            self._execute_trade(data)
        
        @trec.on('exit')
        def handle_exit():
            self.end_flag['endflag'] = 1
        
        trec.connect(self.SOCKETIO_RECEIVER_URL)
        
        while self.running and self.end_flag['endflag'] == 0:
            time.sleep(1)
        
        trec.disconnect()
    
    def _monitor_worker_safe(self):
        try:
            self._monitor_worker_impl()
        except Exception as e:
            self.logger.error(f"监控线程异常: {e}")
    
    def _monitor_worker_impl(self):
        while self.running:
            try:
                ltime = time.localtime()
                if ltime.tm_hour >= 14 and ltime.tm_min > 59:
                    self.end_flag['endflag'] = 1
                time.sleep(60)
            except Exception as e:
                self.logger.error(f"监控异常: {e}")
                time.sleep(10)
    
    def _update_config(self, new_config: Dict):
        try:
            for key in ['username', 'password', 'quant_id', 'quant_name', 'account', 'mq_dir', 'out_dir', 'socketio_sender_url', 'socketio_receiver_url']:
                if key in new_config:
                    setattr(self, f"MQ_{key.upper()}" if key in ['username', 'password', 'account'] else key.upper(), new_config[key])
            self.T_DATE_0 = datetime.datetime.now().strftime("%Y%m%d")
            self.T_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
            return {"success": True, "message": "配置更新成功"}
        except Exception as e:
            return {"success": False, "message": f"更新失败: {str(e)}"}
    
    def _get_status(self):
        return {
            "running": self.running,
            "thread_count": len(self.worker_threads),
            "alive_threads": sum(1 for t in self.worker_threads if t.is_alive()),
            "account": self.MQ_ACCOUNT,
            "username": self.MQ_USERNAME,
            "strategy": self.MQ_QUANT_NAME,
            "end_flag": self.end_flag['endflag'],
            "current_date": self.T_DATE,
            "timestamp": get_now(TimeItem="DateTime"),
            "multiprocess_env": self._in_multiprocess_env,
            "workers_started": self._workers_started
        }
    
    def cleanup(self):
        self._stop()


def main():
    import sys
    config = {
        "config_name": "xtqmt_trader",
        "username": "quruyi0101",
        "password": "quruyi0101",
        "quant_id": "QI88921489",
        "quant_name": "小市值01",
        "account": "2018134",
        "mq_dir": "D:/迅投模拟盘/export_data/",
        "out_dir": "D:/迅投模拟盘/export_data/",
        "assets": "total",
        "server_url": "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php",
        "socketio_sender_url": "http://10.10.98.51:3211",
        "socketio_receiver_url": "http://10.10.98.51:3210"
    }
    
    if len(sys.argv) > 1:
        try:
            config.update(json.loads(sys.argv[1]))
        except:
            pass
    
    try:
        script = ScriptMain(config)
        result = script._start()
        if result.get("success", False):
            while script.running:
                time.sleep(1)
        script.cleanup()
    except Exception as e:
        print(f"脚本运行异常: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()