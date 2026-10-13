# -*- coding: utf-8 -*-
"""
掘金股票版交易脚本 - 适配进程池版本 - 修复版
继承自ScriptMain接口
遵循迅投QMT模板架构
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
import uuid
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

#默认交易配置
DEFAULT_CONFIG = {
    'wait_seconds': 30,
    'stop_abs': 100,
    'stop_ratio': 0.05,
    'close_minutes': 5,
    'first_ratio': 0.95,
    'final_wait': 10,
}

# 使用os模块来检查一个目录是否存在，如果不存在则创建它
def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# 获取当前日期
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

# 查询权限
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

##############掘金交易相关函数#############
# DBF表对象
table_place_order = None
table_cancel_order = None
table_raw_func = None

class Order(object):
    def __init__(self, account_id: str, symbol: str, volume: int, order_type: int, order_biz: int, price: float = 0,
                 sid: str = '', comment: str = '') -> None:
        """
        报单委托
        """
        self.account_id = account_id
        self.symbol = symbol
        self.volume = volume
        self.order_type = order_type
        self.order_biz = order_biz
        self.price = price
        self.sid = sid if sid != '' else uuid.uuid4().hex
        self.comment = comment

class CancelOrder(object):
    def __init__(self, sid: str, comment: str = '') -> None:
        """
        撤单委托
        """
        self.sid = sid
        self.comment = comment

class RawFunc(object):
    def __init__(self, account_id: str, func_id: str, func_params: str, rid: str = '', comment: str = '') -> None:
        """
        功能号委托对象
        """
        self.account_id = account_id
        self.func_id = func_id
        self.func_params = func_params
        self.rid = rid if rid != '' else uuid.uuid4().hex
        self.comment = comment

def query(dbf_file: str, condition: str) -> List:
    """查询DBF文件"""
    import dbf
    res = []
    table = dbf.Table(dbf_file, codepage='utf8')
    table.open()
    fields = table.field_names
    sql = f'select * from "{dbf_file}" where {condition}'
    rows = table.query(sql)
    if rows is not None and len(rows) > 0:
        for row in rows:
            data = {}
            for field in fields:
                val = row[field]
                if isinstance(val, str):
                    val = str(val).strip()
                data[field] = val
            res.append(data)
    table.close()
    return res

def place_orders(dbf_dir: str, orders: List[Order]) -> List[str]:
    """批量下单"""
    global table_place_order
    import dbf
    
    sids = []
    if table_place_order is None:
        filename = os.path.join(dbf_dir, get_now(TimeItem="YMDHMS")+".order.dbf")
        # 创建表结构
        if not os.path.exists(filename):
            table_place_order = dbf.Table(
                filename=filename,
                field_specs="sid C(64); account_id C(64); symbol C(32); volume N(16,0); order_type N(2,0); order_biz N(8,0); price N(16,2); comment C(255)",
                on_disk=True,
                codepage='utf8',
            )
            table_place_order.open(mode=dbf.READ_WRITE)
        else:
            table_place_order = dbf.Table(filename, codepage='utf8')
            table_place_order.open(mode=dbf.READ_WRITE)

    for order in orders:
        fv = order.symbol
        stock_code = fv[:2]+'SE'+fv[2:]
        ord = (order.sid, order.account_id, stock_code, str(order.volume), order.order_type, order.order_biz, order.price,
               order.comment)
        table_place_order.append(ord)
        sids.append(order.sid)

    return sids

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
    
    orderbiz = 1 if direction == 'buy' else 2
    # 构建掘金订单
    order = Order(
        account_id=account_id, 
        symbol=stock_code[:2]+'SE.'+stock_code[2:], 
        volume=str(volume),
        order_type=2,  # 市价委托
        order_biz=orderbiz,
        price=0,  # 市价委托
        comment='x'
    )
        
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
        
    global table_place_order
    import dbf
    
    if table_place_order is None:
        filename = os.path.join(mq_dir, get_now(TimeItem="YMDHMS")+".order.dbf")
        # 创建表结构
        if not os.path.exists(filename):
            table_place_order = dbf.Table(
                filename=filename,
                field_specs="sid C(64); account_id C(64); symbol C(32); volume N(16,0); order_type N(2,0); order_biz N(8,0); price N(16,2); comment C(255)",
                on_disk=True,
                codepage='utf8',
            )
            table_place_order.open(mode=dbf.READ_WRITE)
        else:
            table_place_order = dbf.Table(filename, codepage='utf8')
            table_place_order.open(mode=dbf.READ_WRITE)

    ord = (order.sid, order.account_id, order.symbol, order.volume, order.order_type, order.order_biz, order.price,
           order.comment)
    table_place_order.append(ord)
    return order.sid

# 撤销委托（原版平移）
def cancel_order(orderid, mq_dir, account_id, send_func: Optional[Callable] = None):
    """撤单"""
    global table_cancel_order
    import dbf
    
    if table_cancel_order is None:
        filename = os.path.join(mq_dir, get_now(TimeItem="YMDHMS")+".cancel_order.dbf")
        # 创建表结构
        if not os.path.exists(filename):
            table_cancel_order = dbf.Table(
                filename=filename,
                field_specs="sid C(64); comment C(255)",
                on_disk=True,
                codepage='utf8',
            )
            table_cancel_order.open(mode=dbf.READ_WRITE)
        else:
            table_cancel_order = dbf.Table(filename, codepage='utf8')
            table_cancel_order.open(mode=dbf.READ_WRITE)

    ord = (orderid, '')
    table_cancel_order.append(ord)
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
    return None
    
# 全部撤单（原版平移）
def all_cancel_order(mq_dir, account_id, out_dir, send_func: Optional[Callable] = None):
    try:
        orders = get_orders(out_dir, account_id, status=[1, 2])  # 获取待成交订单
        if orders:
            print('xxxxx')
            print(orders)
            orderlist = []
            for order in orders:
                orderlist.append(order['sid'])
        cancel_orders(dbf_dir=mq_dir, orders=orderlist)
        cancelled_count = len(orderlist)
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

#掘金批量撤单
def cancel_orders(dbf_dir: str, orders: List[CancelOrder]) -> List[str]:
    """批量撤单"""
    global table_cancel_order
    import dbf
    
    sids = []
    if table_cancel_order is None:
        filename = os.path.join(dbf_dir, get_now(TimeItem="YMDHMS")+".cancel_order.dbf")
        # 创建表结构
        if not os.path.exists(filename):
            table_cancel_order = dbf.Table(
                filename=filename,
                field_specs="sid C(64); comment C(255)",
                on_disk=True,
                codepage='utf8',
            )
            table_cancel_order.open(mode=dbf.READ_WRITE)
        else:
            table_cancel_order = dbf.Table(filename, codepage='utf8')
            table_cancel_order.open(mode=dbf.READ_WRITE)

    for order in orders:
        ord = (order.sid, order.comment)
        table_cancel_order.append(ord)
        sids.append(order.sid)

    return sids

def get_position(out_path: str, account_id: str) -> List:
    """获取持仓"""
    dbf_file = os.path.join(out_path, f'{account_id}/position.dbf')
    if os.path.exists(dbf_file):
        return query(dbf_file, f'account_id.strip() == "{account_id}"')
    return []


def get_cash(out_path: str, account_id: str) -> List:
    """获取资金"""
    dbf_file = os.path.join(out_path, f'{account_id}/cash.dbf')
    if os.path.exists(dbf_file):
        return query(dbf_file, f'account_id.strip() == "{account_id}"')
    return []


def get_orders(out_path: str, account_id: str, sids: List[str] = [], status: List[int] = []) -> List:
    """获取订单状态"""
    dbf_file = os.path.join(out_path, f'{account_id}/order_status.dbf')
    condition = [f'account_id.strip() == "{account_id}"']
    if len(sids) > 0:
        condition.append(f'sid.strip() in {sids}')

    if len(status) > 0:
        condition.append(f'status in {status}')

    if os.path.exists(dbf_file):
        return query(dbf_file, " and ".join(condition))
    return []


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
        positions = get_position(out_dir, account_id)
        result = {}
        for item in positions:
            code = item['SYMBOL'][:2] + item['SYMBOL'][-6:]
            available = float(item.get('AVL_NOW', 0))
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
    
    SidList = []
    # 下单
    for code, task in tasks.items():
        vol = round_lot(task['volume'])
        if vol > 0:
            sid = place_order(code, vol, task['direction'], mq_dir, account_id, 
                       price_type, limit_price, send_func)
            SidList.append(sid)

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
        cjcxlist = get_orders(out_dir, account_id,SidList,status=[1,2,3])
        for item in cjcxlist:
            code = item['SYMBOL'][:2] + item['SYMBOL'][-6:]
            
            if code not in tasks:
                continue
            if code not in result:
                result[code] = {'filled': 0, 'cost': 0}
            result[code]['filled'] += int(item['FILLED_VOL'])
            result[code]['cost'] += float(item['FILLED_AMT'])
        
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

    sell_cum = {code: 0 for code in sell_targets}
    sell_cum_cost = {code: 0 for code in sell_targets}
    buy_cum = {code: 0 for code in buy_targets}
    buy_cum_cost = {code: 0 for code in buy_targets}

    abandoned_sells = set()
    abandoned_buys = set()
    cand_idx = 0

    initial_cash = 0
    try:
        cash_info = get_cash(out_dir, account_id)
        if cash_info:
            cash = cash_info[0]
            initial_cash = float(cash.get('AVAILABLE',0))
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
    """发送交易差异信息"""
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
    """掘金交易脚本主类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        
        # 从配置中读取参数
        self.MQ_USERNAME = config.get("username", "")
        self.MQ_PASSWORD = config.get("password", "")
        self.MQ_QUANT_ID = config.get("quant_id", "")
        self.MQ_QUANT_NAME = config.get("quant_name", "")
        self.MQ_ACCOUNT = config.get("account", "")
        self.MQ_DIR = config.get("mq_dir", "") + "xiaoai/"
        self.OUT_DIR = config.get("out_dir", "")
        self.MQ_ASSETS = config.get("assets", "total")
        self.SERVER_URL = config.get("server_url", "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php")
        self.SOCKETIO_SENDER_URL = config.get("socketio_sender_url", "http://10.10.98.51:3211")
        self.SOCKETIO_RECEIVER_URL = config.get("socketio_receiver_url", "http://10.10.98.51:3210")
        
        # 数据队列（用于向前端发送消息）
        self.data_queue = config.get("data_queue", None)
        
        # 验证必要参数
        required_params = ["username", "password", "quant_id", "quant_name", "account"]
        missing_params = [p for p in required_params if not self.config.get(p)]
        if missing_params:
            raise ValueError(f"缺少必要参数: {missing_params}")
        
        # 工作线程列表
        self.worker_threads = []
                
        # 交易相关变量
        self.sender_thread = None
        self.receiver_thread = None
        self.end_flag = {'endflag': 0}
        
        # 日期字符串
        self.T_DATE_0 = datetime.datetime.now().strftime("%Y%m%d")
        self.T_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # ========== 修复：添加多进程环境特殊处理 ==========
        self._in_multiprocess_env = hasattr(self, 'data_queue') and self.data_queue is not None
        self._workers_started = False
        self._init_attempts = 0
        # ==============================================
        # 初始化日志
        self._setup_logging()
        
        # 创建必要的目录
        if self.OUT_DIR:
            create_directory_if_not_exists(self.OUT_DIR)
        if self.MQ_DIR:
            create_directory_if_not_exists(self.MQ_DIR)
        
        # 初始化数据库
        init_trade_db(self.MQ_ACCOUNT)
        
        # 发送初始化消息到前端
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": f"初始化掘金交易脚本: {self.MQ_QUANT_NAME}",
            "timestamp": get_now(TimeItem="DateTime"),
            "account": self.MQ_ACCOUNT,
            "strategy": self.MQ_QUANT_NAME,
            "multiprocess_env": self._in_multiprocess_env
        })
        
        self.logger.info(f"初始化掘金交易脚本: {self.MQ_QUANT_NAME}")
        self.logger.info(f"账号: {self.MQ_ACCOUNT}, 用户: {self.MQ_USERNAME}")
        self.logger.info(f"数据目录: {self.MQ_DIR}, 输出目录: {self.OUT_DIR}")
        self.logger.info(f"SocketIO发送地址: {self.SOCKETIO_SENDER_URL}")
        self.logger.info(f"SocketIO接收地址: {self.SOCKETIO_RECEIVER_URL}")
        self.logger.info(f"多进程环境: {self._in_multiprocess_env}")
    
    def _setup_logging(self):
        """设置日志"""
        script_name = self.config.get("config_name", f"golden_{self.MQ_QUANT_NAME}")
        # 创建logger
        self.logger = logging.getLogger(f"ScriptMain.{script_name}")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            # 文件handler
            try:
                log_dir = os.path.join("logs", "golden", script_name)
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
                self._send_to_frontend({
                    "type": "system",
                    "level": "error",
                    "message": f"设置文件日志失败: {e}",
                    "timestamp": get_now(TimeItem="DateTime")
                })
                print(f"设置文件日志失败: {e}")
    
    def _send_to_frontend(self, message_dict: Dict[str, Any]):
        """
        发送消息到前端
        
        Args:
            message_dict: 消息字典，应包含:
                - type: 消息类型 (system, trade, account, error, warning, info,command,socket,monitor,status
                - level: 消息级别 (info, warning, error, success)
                - message: 消息内容
                - timestamp: 时间戳
                - data: 附加数据 (可选)
                - account: 账户信息 (可选)
                - strategy: 策略信息 (可选)
        """
        if hasattr(self, 'data_queue') and self.data_queue:
            try:
                # 确保消息包含必要字段
                if 'timestamp' not in message_dict:
                    message_dict['timestamp'] = get_now(TimeItem="DateTime")
                if 'account' not in message_dict:
                    message_dict['account'] = self.MQ_ACCOUNT
                if 'strategy' not in message_dict:
                    message_dict['strategy'] = self.MQ_QUANT_NAME
                # 添加进程环境标识
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
            cash_info = get_cash(self.OUT_DIR, self.MQ_ACCOUNT)
            if not cash_info:
                self.logger.error("无法获取账户资金信息")
                self._send_to_frontend({
                    "type": "trade",
                    "level": "error",
                    "message": "无法获取账户资金信息",
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return
            
            cash = cash_info[0]
            
            totalAssets = float(cash.get('NAV', 0))
            totalMarketValue = float(cash.get('MARKET_VAL', 0))
            
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
                wcctjlist = get_position(self.OUT_DIR, self.MQ_ACCOUNT)
                
                for tdict in wcctjlist:
                    fv = tdict['SYMBOL'][:2] + tdict['SYMBOL'][-6:]
                    holddict[fv] = [
                        float(tdict.get('VOLUME',0)),
                        float(tdict.get('MARKET_VAL',0)),
                        float(tdict.get('PRICE',0)),
                        float(tdict.get('AVL_NOW',0))
                    ]
                    if BaseDict.get(fv) is None:
                        BaseDict[fv] = float(tdict['PRICE'])
                        
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
                    actual_holdings_list = get_position(self.OUT_DIR, self.MQ_ACCOUNT)
                    selllist = []
                    for item in actual_holdings_list:
                        acode = item['SYMBOL'][:2] + item['SYMBOL'][-6:]
                        gnum = math.floor((float(item['MARKET_VAL']) * holddiff) / float(item['PRICE']) / 100) * 100
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
    
    
    # ========== 修复：重写run_iteration方法，实现延迟启动 ==========
    def run_iteration(self):
        """
        运行一次脚本迭代（供进程池调用）
        这是关键修复：确保在多进程环境中线程能正确启动
        """
        try:
            # 如果是第一次运行，启动工作线程
            if not self._workers_started and self._init_attempts < 3:
                self.logger.info(f"尝试启动工作线程 (尝试次数: {self._init_attempts + 1})")
                self._init_attempts += 1
                
                # 延迟启动，避免立即启动导致的SocketIO问题
                if self._init_attempts == 1:
                    time.sleep(2)  # 第一次延迟2秒
                    
                if not self.running:
                    self.logger.info("通过run_iteration设置running=True")
                    self.running = True
                
                
                # 启动工作线程
                self._start_worker_threads()
                self._workers_started = True
                
                self.logger.info("工作线程已通过run_iteration启动")
                self._send_to_frontend({
                    "type": "system",
                    "level": "success",
                    "message": "工作线程已启动",
                    "timestamp": get_now(TimeItem="DateTime"),
                    "data": {
                        "init_attempts": self._init_attempts,
                        "workers_started": self._workers_started
                    }
                })
            
            # 检查工作线程是否存活
            if self._workers_started:
                dead_threads = []
                for thread in self.worker_threads:
                    if not thread.is_alive():
                        dead_threads.append(thread)
                
                # 重启死亡的线程
                for thread in dead_threads:
                    warning_msg = f"检测到线程 {thread.name} 死亡"
                    self.logger.warning(warning_msg)
                    self._send_to_frontend({
                        "type": "system",
                        "level": "warning",
                        "message": warning_msg,
                        "timestamp": get_now(TimeItem="DateTime")
                    })
                    self.worker_threads.remove(thread)
                    
                    # 根据线程类型重启
                    if "Sender" in thread.name:
                        new_thread = threading.Thread(
                            target=self._sender_worker_safe,
                            name=thread.name,
                            daemon=True
                        )
                        new_thread.start()
                        self.worker_threads.append(new_thread)
                        self.logger.info(f"重启发送线程: {thread.name}")
                    elif "Receiver" in thread.name:
                        new_thread = threading.Thread(
                            target=self._receiver_worker_safe,
                            name=thread.name,
                            daemon=True
                        )
                        new_thread.start()
                        self.worker_threads.append(new_thread)
                        self.logger.info(f"重启接收线程: {thread.name}")
                    elif "Monitor" in thread.name:
                        new_thread = threading.Thread(
                            target=self._monitor_worker_safe,
                            name=thread.name,
                            daemon=True
                        )
                        new_thread.start()
                        self.worker_threads.append(new_thread)
                        self.logger.info(f"重启监控线程: {thread.name}")
                
                # 定期检查并发送状态
                current_time = time.time()
                if hasattr(self, '_last_status_check'):
                    if current_time - self._last_status_check > 30:
                        alive_count = sum(1 for t in self.worker_threads if t.is_alive())
                        status_msg = f"系统运行中，存活线程: {alive_count}/{len(self.worker_threads)}"
                        self.logger.info(status_msg)
                        
                        self._send_to_frontend({
                            "type": "monitor",
                            "level": "info",
                            "message": status_msg,
                            "timestamp": get_now(TimeItem="DateTime"),
                            "data": {
                                "alive_threads": alive_count,
                                "total_threads": len(self.worker_threads),
                                "running": self.running,
                                "end_flag": self.end_flag['endflag'],
                                "workers_started": self._workers_started
                            }
                        })
                        self._last_status_check = current_time
                else:
                    self._last_status_check = current_time
            
            # 检查是否收到退出信号
            if self.end_flag['endflag'] == 1:
                self.logger.info("收到退出信号，正在停止...")
                self._send_to_frontend({
                    "type": "system",
                    "level": "info",
                    "message": "收到退出信号，正在停止脚本...",
                    "timestamp": get_now(TimeItem="DateTime")
                })
                self.cleanup()
            
        except Exception as e:
            error_msg = f"运行迭代失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e)
            })
    # ==========================================================
    
    def handle_command(self, command: Dict):
        """
        处理来自外部的命令
        
        Args:
            command: 命令字典，包含 command 和 data 字段
        """
        cmd = command.get("command", "")
        data = command.get("data", {})
        
        self.logger.info(f"收到命令: {cmd}")
        self._send_to_frontend({
            "type": "command",
            "level": "info",
            "message": f"收到命令: {cmd}",
            "timestamp": get_now(TimeItem="DateTime"),
            "command": cmd
        })
        
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
        elif cmd == "test_connection":
            return self._test_connection()
        else:
            warning_msg = f"未知命令: {cmd}"
            self.logger.warning(warning_msg)
            self._send_to_frontend({
                "type": "command",
                "level": "warning",
                "message": warning_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": f"未知命令: {cmd}"}
    
    def _start(self):
        """启动交易脚本"""
        if self.running:
            warning_msg = "脚本已在运行中"
            self.logger.warning(warning_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "warning",
                "message": warning_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": "脚本已在运行中"}
        
        try:
            self.running = True
            
            # 发送启动消息到前端
            self._send_to_frontend({
                "type": "system",
                "level": "info",
                "message": "正在启动掘金交易脚本...",
                "timestamp": get_now(TimeItem="DateTime")
            })
            
            
            # 检查权限（如果是多进程环境，可能需要跳过或延迟检查）
            if not self._in_multiprocess_env:
                if not self._check_authority():
                    warning_msg = "您目前还没有策略,请登录QLens申请！"
                    self.logger.warning(warning_msg)
                    self._send_to_frontend({
                        "type": "system",
                        "level": "warning",
                        "message": warning_msg,
                        "timestamp": get_now(TimeItem="DateTime")
                    })
            
            # 启动工作线程
            self._start_worker_threads()
            
            success_msg = "掘金交易脚本启动成功"
            self.logger.info(success_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "success",
                "message": success_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {
                    "account": self.MQ_ACCOUNT,
                    "strategy": self.MQ_QUANT_NAME,
                    "algorithm": "未初始化",
                    "multiprocess_env": self._in_multiprocess_env
                }
            })
            
            return {"success": True, "message": success_msg}
            
        except Exception as e:
            self.running = False
            error_msg = f"启动失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e)
            })
            return {"success": False, "message": f"启动失败: {str(e)}"}
    
    def _stop(self):
        """停止交易脚本"""
        if not self.running:
            warning_msg = "脚本未在运行"
            self.logger.warning(warning_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "warning",
                "message": warning_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": "脚本未在运行"}
        
        try:
            info_msg = "正在停止掘金交易脚本..."
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            
            self.running = False
            self.end_flag['endflag'] = 1
            
            # 等待工作线程结束
            for thread in self.worker_threads:
                try:
                    if thread.is_alive():
                        thread.join(timeout=3)
                except Exception as e:
                    error_msg = f"等待线程 {thread.name} 结束失败: {e}"
                    self.logger.error(error_msg)
                    self._send_to_frontend({
                        "type": "system",
                        "level": "error",
                        "message": error_msg,
                        "timestamp": get_now(TimeItem="DateTime")
                    })
            
            self.worker_threads.clear()
            
            # 关闭DBF表
            global table_place_order, table_cancel_order, table_raw_func
            if table_place_order:
                table_place_order.close()
                table_place_order = None
            if table_cancel_order:
                table_cancel_order.close()
                table_cancel_order = None
            if table_raw_func:
                table_raw_func.close()
                table_raw_func = None
            
            success_msg = "掘金交易脚本已停止"
            self.logger.info(success_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "success",
                "message": success_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            
            return {"success": True, "message": success_msg}
            
        except Exception as e:
            error_msg = f"停止失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": f"停止失败: {str(e)}"}
    
    def _restart(self):
        """重启交易脚本"""
        info_msg = "正在重启掘金交易脚本..."
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        # 先停止
        stop_result = self._stop()
        if not stop_result.get("success", False):
            return stop_result
        
        time.sleep(1)
        
        # 再启动
        return self._start()
    
    def _pause_trading(self):
        """暂停交易"""
        info_msg = "暂停交易"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        self.end_flag['endflag'] = 1
        return {"success": True, "message": "交易已暂停"}
    
    def _resume_trading(self):
        """恢复交易"""
        info_msg = "恢复交易"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        self.end_flag['endflag'] = 0
        return {"success": True, "message": "交易已恢复"}
    
    def _cancel_all_orders(self):
        """取消所有订单"""
        try:
            all_cancel_order(self.MQ_DIR, self.MQ_ACCOUNT, self.OUT_DIR)
            info_msg = "已取消所有订单"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": True, "message": "已取消所有订单"}
        except Exception as e:
            error_msg = f"取消订单失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": f"取消订单失败: {str(e)}"}
    

    def _check_authority(self):
        """检查交易权限"""
        try:
            auth_result = check_authority(self.MQ_USERNAME, self.MQ_QUANT_ID, self.SERVER_URL)
            if auth_result:
                info_msg = "权限验证成功"
                self.logger.info(info_msg)
                self._send_to_frontend({
                    "type": "system",
                    "level": "info",
                    "message": info_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return True
            else:
                warning_msg = "您目前还没有策略,请登录QLens申请！"
                self.logger.warning(warning_msg)
                self._send_to_frontend({
                    "type": "system",
                    "level": "warning",
                    "message": warning_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return False
        except Exception as e:
            error_msg = f"权限验证过程中出错: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return False
    
    # ========== 修复：修改_start_worker_threads方法，使用安全版本的线程 ==========
    def _start_worker_threads(self):
        """启动工作线程 - 修复版"""
        thread_count = 0
        
        # 数据发送线程 - 使用安全版本
        self.sender_thread = threading.Thread(
            target=self._sender_worker_safe,
            name=f"Sender_{self.MQ_QUANT_NAME}",
            daemon=True
        )
        self.sender_thread.start()
        self.worker_threads.append(self.sender_thread)
        thread_count += 1
        
        # 数据接收线程 - 使用安全版本
        self.receiver_thread = threading.Thread(
            target=self._receiver_worker_safe,
            name=f"Receiver_{self.MQ_QUANT_NAME}",
            daemon=True
        )
        self.receiver_thread.start()
        self.worker_threads.append(self.receiver_thread)
        thread_count += 1
        
        # 监控线程 - 使用安全版本
        monitor_thread = threading.Thread(
            target=self._monitor_worker_safe,
            name=f"Monitor_{self.MQ_QUANT_NAME}",
            daemon=True
        )
        monitor_thread.start()
        self.worker_threads.append(monitor_thread)
        thread_count += 1
        
        info_msg = f"已启动 {thread_count} 个工作线程"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {
                "threads": thread_count,
                "thread_names": [t.name for t in self.worker_threads]
            }
        })
    # =====================================================================
    
    # ========== 新增：安全版本的发送线程 ==========
    def _sender_worker_safe(self):
        """数据发送工作线程 - 安全版本（带错误处理）"""
        info_msg = "数据发送线程启动"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries and self.running and self.end_flag['endflag'] == 0:
            try:
                self._sender_worker_impl()
                # 如果正常退出，不再重试
                break
            except Exception as e:
                retry_count += 1
                error_msg = f"数据发送线程异常 (重试 {retry_count}/{max_retries}): {e}"
                self.logger.error(error_msg)
                self._send_to_frontend({
                    "type": "socket",
                    "level": "error",
                    "message": error_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                
                if retry_count < max_retries:
                    time.sleep(5)  # 等待5秒后重试
                else:
                    self.logger.error("数据发送线程达到最大重试次数，停止重试")
                    break
        
        info_msg = "数据发送线程停止"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
    # ==========================================
    
    def _sender_worker_impl(self):
        """数据发送工作线程实现"""
        apush = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5,
            randomization_factor=0.5
        )
        
        @apush.event
        def connect():
            info_msg = 'SocketIO连接已建立'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @apush.event
        def connect_error(data):
            warning_msg = f'SocketIO连接错误: {data}'
            self.logger.warning(warning_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "warning",
                "message": warning_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @apush.event
        def user_message(data):
            info_msg = f'收到用户消息: {data}'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @apush.event
        def disconnect():
            info_msg = '从服务器断开连接'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @apush.on('exit')
        def handle_exit():
            self.end_flag['endflag'] = 1
            info_msg = "收到退出信号"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        try:
            apush.connect(self.SOCKETIO_SENDER_URL)
            self.logger.info(f"已连接到SocketIO服务器: {self.SOCKETIO_SENDER_URL}")
            
            # 发送注册信息
            znote = (f"{self.MQ_USERNAME}-{self.MQ_QUANT_NAME}-账户注册-"
                    f"{get_now(TimeItem='YMDHMS')}:{self.MQ_QUANT_ID}#{self.MQ_ACCOUNT}#"
                    f"{self.MQ_USERNAME}#{self.MQ_QUANT_NAME}#{self.MQ_ASSETS}")
            apush.emit('fromWebClient', {'mess': znote})
            
            last_send_time = 0
            send_interval = 5  # 发送间隔秒数
            
            while self.running and self.end_flag['endflag'] == 0:
                try:
                    current_time = time.time()
                    if current_time - last_send_time >= send_interval:
                        # 发送账户数据
                        self._send_account_data(apush)
                        last_send_time = current_time
                    
                    time.sleep(1)  # 每秒检查一次
                    
                except Exception as e:
                    error_msg = f"发送数据异常: {e}"
                    self.logger.error(error_msg)
                    self._send_to_frontend({
                        "type": "socket",
                        "level": "error",
                        "message": error_msg,
                        "timestamp": get_now(TimeItem="DateTime")
                    })
                    time.sleep(5)
            
            apush.disconnect()
            
        except Exception as e:
            error_msg = f"数据发送线程连接异常: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            raise  # 重新抛出异常，让外层捕获
    
    def _send_account_data(self, apush):
        """发送账户数据"""
        try:
            cash_info = get_cash(self.OUT_DIR, self.MQ_ACCOUNT)
            if cash_info:
                cash = cash_info[0]
                ageneral = []
                ageneral.append(float(cash.get('NAV', 0)))
                ageneral.append(float(cash.get('AVAILABLE', 0)))
                ageneral.append(float(cash.get('MARKET_VAL', 0)))
                
                # 发送账户信息到前端
                self._send_to_frontend({
                    "type": "account",
                    "level": "info",
                    "message": "账户信息更新",
                    "timestamp": get_now(TimeItem="DateTime"),
                    "data": {
                        "总资产": float(cash.get('NAV', 0)),
                        "可用金额": float(cash.get('AVAILABLE', 0)),
                        "总市值": float(cash.get('MARKET_VAL', 0)),
                        "账户": self.MQ_ACCOUNT
                    }
                })
                
                nnote1 = (f"{self.MQ_ACCOUNT.replace('-', '_')}-账户总览-"
                         f"{get_now(TimeItem='YMDHMS')}:{json.dumps(ageneral).replace(' ', '')}")
                apush.emit('fromWebClient', {'mess': nnote1})
            else:
                warning_msg = f"资金查询数据不存在"
                self.logger.warning(warning_msg)
                self._send_to_frontend({
                    "type": "account",
                    "level": "warning",
                    "message": warning_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
        except Exception as e:
            error_msg = f"发送账户数据异常: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "account",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
    
    # ========== 新增：安全版本的接收线程 ==========
    def _receiver_worker_safe(self):
        """数据接收工作线程 - 安全版本（带错误处理）"""
        info_msg = "数据接收线程启动"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries and self.running and self.end_flag['endflag'] == 0:
            try:
                self._receiver_worker_impl()
                # 如果正常退出，不再重试
                break
            except Exception as e:
                retry_count += 1
                error_msg = f"数据接收线程异常 (重试 {retry_count}/{max_retries}): {e}"
                self.logger.error(error_msg)
                self._send_to_frontend({
                    "type": "socket",
                    "level": "error",
                    "message": error_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                
                if retry_count < max_retries:
                    time.sleep(5)  # 等待5秒后重试
                else:
                    self.logger.error("数据接收线程达到最大重试次数，停止重试")
                    break
        
        info_msg = "数据接收线程停止"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
    # ==========================================
    
    def _receiver_worker_impl(self):
        """数据接收工作线程实现"""
        trec = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5,
            randomization_factor=0.5
        )
        
        @trec.event
        def connect():
            info_msg = 'mqReceiver连接已建立'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @trec.event
        def connect_error(data):
            warning_msg = f'mqReceiver连接错误: {data}'
            self.logger.warning(warning_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "warning",
                "message": warning_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @trec.event
        def user_message(data):
            info_msg = f'收到用户消息: {data}'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @trec.event
        def disconnect():
            info_msg = '从mqReceiver服务器断开连接'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        @trec.on(self.MQ_QUANT_NAME)
        def on_message(data):
            info_msg = f'收到交易指令: {data}'
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": "收到新的交易指令",
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"raw_data": str(data)}
            })
            self._execute_trade(data)
        
        @trec.on('exit')
        def handle_exit():
            info_msg = "收到退出信号"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            self.end_flag['endflag'] = 1
        
        try:
            trec.connect(self.SOCKETIO_RECEIVER_URL)
            self.logger.info(f"已连接到mqReceiver服务器: {self.SOCKETIO_RECEIVER_URL}")
            
            while self.running and self.end_flag['endflag'] == 0:
                time.sleep(1)
            
            trec.disconnect()
            
        except Exception as e:
            error_msg = f"数据接收线程连接异常: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "socket",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            raise  # 重新抛出异常，让外层捕获
    
    def _execute_trade_command(self, data: Dict):
        trade_data = data.get("trade_data", "")
        if not trade_data:
            return {"success": False, "message": "交易数据为空"}
        self._execute_trade(trade_data)
        return {"success": True, "message": "交易命令已执行"}
    

    
    # ========== 新增：安全版本的监控线程 ==========
    def _monitor_worker_safe(self):
        """监控工作线程 - 安全版本"""
        info_msg = "监控线程启动"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        try:
            self._monitor_worker_impl()
        except Exception as e:
            error_msg = f"监控线程异常: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "monitor",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        info_msg = "监控线程停止"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
    # ===========================================
    
    def _monitor_worker_impl(self):
        """监控工作线程实现"""
        last_status_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # 每60秒发送一次状态信息
                if current_time - last_status_time > 60:
                    alive_count = sum(1 for t in self.worker_threads if t.is_alive())
                    status_msg = f"系统运行正常，存活线程: {alive_count}/{len(self.worker_threads)}"
                    
                    self._send_to_frontend({
                        "type": "monitor",
                        "level": "info",
                        "message": status_msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {
                            "alive_threads": alive_count,
                            "total_threads": len(self.worker_threads),
                            "running": self.running,
                            "end_flag": self.end_flag['endflag'],
                            "workers_started": self._workers_started
                        }
                    })
                    last_status_time = current_time
                
                # 股票交易时间监控
                ltime = time.localtime()
                # 收盘前1分钟
                if ltime.tm_hour >= 14 and ltime.tm_min > 59:
                    warning_msg = "临近收盘，准备停止交易"
                    self.logger.info(warning_msg)
                    self._send_to_frontend({
                        "type": "monitor",
                        "level": "warning",
                        "message": warning_msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {
                            "hour": ltime.tm_hour,
                            "minute": ltime.tm_min
                        }
                    })
                    self.end_flag['endflag'] = 1
                
                time.sleep(60)
                
            except Exception as e:
                error_msg = f"监控线程循环异常: {e}"
                self.logger.error(error_msg)
                self._send_to_frontend({
                    "type": "monitor",
                    "level": "error",
                    "message": error_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                time.sleep(10)
    
    def _update_config(self, new_config: Dict):
        """更新配置"""
        try:
            # 更新基本配置
            if 'username' in new_config:
                self.MQ_USERNAME = new_config['username']
            if 'password' in new_config:
                self.MQ_PASSWORD = new_config['password']
            if 'quant_id' in new_config:
                self.MQ_QUANT_ID = new_config['quant_id']
            if 'quant_name' in new_config:
                self.MQ_QUANT_NAME = new_config['quant_name']
            if 'account' in new_config:
                self.MQ_ACCOUNT = new_config['account']
            if 'mq_dir' in new_config:
                self.MQ_DIR = new_config['mq_dir']
            if 'out_dir' in new_config:
                self.OUT_DIR = new_config['out_dir']
            if 'socketio_sender_url' in new_config:
                self.SOCKETIO_SENDER_URL = new_config['socketio_sender_url']
            if 'socketio_receiver_url' in new_config:
                self.SOCKETIO_RECEIVER_URL = new_config['socketio_receiver_url']
            
            # 更新日期字符串
            self.T_DATE_0 = datetime.datetime.now().strftime("%Y%m%d")
            self.T_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
            
            info_msg = f"配置已更新: {new_config}"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "info",
                "message": "配置更新成功",
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"updated_config": new_config}
            })
            
            return {"success": True, "message": "配置更新成功"}
            
        except Exception as e:
            error_msg = f"更新配置失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": f"更新配置失败: {str(e)}"}
    
    def _get_status(self):
        """获取当前状态"""
        status_info = {
            "running": self.running,
            "thread_count": len(self.worker_threads),
            "alive_threads": sum(1 for t in self.worker_threads if t.is_alive()),
            "account": self.MQ_ACCOUNT,
            "username": self.MQ_USERNAME,
            "strategy": self.MQ_QUANT_NAME,
            "algorithm": "None",
            "end_flag": self.end_flag['endflag'],
            "mq_dir": self.MQ_DIR,
            "out_dir": self.OUT_DIR,
            "socketio_sender_url": self.SOCKETIO_SENDER_URL,
            "socketio_receiver_url": self.SOCKETIO_RECEIVER_URL,
            "current_date": self.T_DATE,
            "timestamp": get_now(TimeItem="DateTime"),
            "multiprocess_env": self._in_multiprocess_env,
            "workers_started": self._workers_started,
            "init_attempts": self._init_attempts
        }
        
        # 发送状态信息到前端
        self._send_to_frontend({
            "type": "status",
            "level": "info",
            "message": "状态查询",
            "timestamp": get_now(TimeItem="DateTime"),
            "data": status_info
        })
        
        return status_info
    
    def _test_connection(self):
        """测试连接"""
        try:
            # 测试权限检查
            result = self._check_authority()
            if result:
                info_msg = "连接测试成功"
                self.logger.info(info_msg)
                self._send_to_frontend({
                    "type": "system",
                    "level": "success",
                    "message": info_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return {"success": True, "message": "连接测试成功"}
            else:
                error_msg = "连接测试失败：权限验证失败"
                self.logger.error(error_msg)
                self._send_to_frontend({
                    "type": "system",
                    "level": "error",
                    "message": error_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return {"success": False, "message": "连接测试失败：权限验证失败"}
        except Exception as e:
            error_msg = f"连接测试失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": f"连接测试失败: {str(e)}"}
    
    def cleanup(self):
        """
        清理资源 - 进程池会调用此方法
        """
        info_msg = "清理脚本资源..."
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        # 停止脚本
        self._stop()
        
        success_msg = "脚本资源清理完成"
        self.logger.info(success_msg)
        self._send_to_frontend({
            "type": "system",
            "level": "success",
            "message": success_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })


# 脚本入口函数（供独立运行使用）
def main():
    """脚本入口函数（供独立运行使用）"""
    import sys
    
    # 默认配置
    config = {
        "config_name": "golden_trader",
        "username": "quruyi0101",
        "password": "quruyi0101",
        "quant_id": "QI98874599",
        "quant_name": "上证指数选股01",
        "account": "30704410-bba2-11f0-adb5-00163e022aa6",
        "mq_dir": "D:/trader/",
        "out_dir": "D:/trader/",
        "assets": "total",
        "server_url": "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php",
        "socketio_sender_url": "http://10.10.98.51:3211",
        "socketio_receiver_url": "http://10.10.98.51:3210"
    }
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        import json
        try:
            config.update(json.loads(sys.argv[1]))
            print(f"使用配置: {config}")
        except:
            print("无法解析命令行参数，使用默认配置")
    
    try:
        script = ScriptMain(config)
        
        # 启动脚本
        result = script._start()
        print(f"启动结果: {result}")
        
        if result.get("success", False):
            try:
                # 保持运行
                while script.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n收到中断信号，正在停止...")
            finally:
                script.cleanup()
        else:
            print(f"启动失败: {result.get('message', '未知错误')}")
            
    except Exception as e:
        print(f"脚本运行异常: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()