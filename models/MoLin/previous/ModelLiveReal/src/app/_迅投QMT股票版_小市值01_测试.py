# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 14:14:59 2026

@author: Administrator
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
import sqlite3
import queue  # 【新增】导入队列模块
import math
from typing import List, Dict, Optional, Union, Any


#账号名称
mqusername = 'quruyi0101'
mqpassword = 'quruyi0101'
#策略名称
mqquantname = '小市值01'
#策略编号
mqquantID = 'QI88921489'
#股票账号/路径
mqsaccount = '2018134'
mqdir = 'D:/迅投模拟盘/export_data/'
outdir = 'D:/迅投模拟盘/export_data/'
#总资金
mqsassets = 'total'

###########################

#利用一个dict做为全局变量的容器
Reg_Msg = {}
Reg_Msg['Reg_User'] = "None"
#利用一个list存储用户的已经查询过的权限，实现同权限不在查
User_Auth = []
#线程池
threads = []
#服务器地址
Url = 'http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php'

# 【新增】交易指令队列（用于串行处理）
_trade_queue = queue.Queue()
# 【新增】交易工作线程控制标志
_trade_worker_running = False
# 【新增】交易工作线程对象
_trade_worker_thread = None

####################
#使用os模块来检查一个目录是否存在，如果不存在则创建它
def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
#获取当前日期
def GetNow(TimeItem=None):
    if TimeItem == "Stamp":
        tvar = int(time.time())
    elif TimeItem == "DateTime":
        tvar = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif TimeItem == "Date":
        tvar = datetime.datetime.now().strftime("%Y-%m-%d")
    elif TimeItem == "YMDHMS":
        tvar = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return tvar
#print(GetNow(TimeItem="DateTime"))

# 数据库管理函数
def init_trade_db(account_id):
    """初始化交易数据库，如果不存在则创建"""
    # 确保data目录存在
    data_dir = '../../data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 数据库文件路径
    db_path = os.path.join(data_dir, f'{account_id}.db')
    
    # 检查数据库是否存在，不存在则创建
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建持仓记录表
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
#position 持仓记录 order 调仓指令 result 执行结果
def save_record(account_id, litem , lnote):
    """保存持仓记录到数据库
    Args:
        account_id: 交易账号
    """
    db_path = os.path.join('../../data', f'{account_id}.db')
    
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取当前时间
        current_time = GetNow(TimeItem="DateTime")
        
        # 将字典转换为JSON字符串
        if litem  in ['result','position']:
            xnote = json.dumps(lnote, ensure_ascii=False)
        else:
            xnote = lnote
        # 插入记录
        cursor.execute('''
            INSERT INTO note (datetime,item,note)
            VALUES (?,?,?)
        ''', (current_time, litem ,xnote))
        
        conn.commit()
        conn.close()
        print(f"持仓记录已保存: {current_time}")
        return True
    except Exception as e:
        print(f"保存持仓记录失败: {e}")
        return False


#print(r.dbsize())
def TimeStampToDateTime(TimeStamp,Format):
    timeStamp = TimeStamp
    dateArray = datetime.datetime.fromtimestamp(timeStamp)
    tvar = dateArray.strftime(Format)
    return tvar
#tv=TimeStampToDateTime(1381420800,"%Y-%m-%d %H:%M:%S")
def DateTimeToTimeStamp(DateTimeStr,Format):
    TimeArray = time.strptime(DateTimeStr,Format)
    tvar = int(time.mktime(TimeArray))
    return tvar
#tv = DateTimeToTimeStamp("20131010","%Y%m%d")

#当前日期str
TDate0 = datetime.datetime.now().strftime("%Y%m%d")
#TDate = datetime.datetime.now().strftime("%Y-%m-%d")

#用户登录
def Login(UserName,PassWord):
    Sub_Field= {
    'sflag':'login',
    'sid':'_04',
    'username':UserName,
    'password':PassWord,
    } 
    r = requests.post(Url,data = Sub_Field)
    rtext = r.text.strip()[1:]
    rtext = json.loads(rtext)
    if type(rtext)==list :
        Reg_Msg['Reg_User'] = rtext[0]['Q14123101']
        print(rtext[0]['Q14123103']+'：登录成功！')
    elif type(rtext)==str :
        print(rtext)
    return
#注销,这块涉及到对全局变量的修改，注销这块需要向server报告，把策略注销
def LoginOut():
    try:
        user =  Reg_Msg['Reg_User']
        Reg_Msg['Reg_User'] = "None"
    except:
        #这块需要用一个错误信息替代
        print("注销不成功！")
    finally:
        if user == "None":
            print("没用用户登录！")
        else:
            print(user+'：已注销！')
#登录
#Login(mqusername,mqpassword)
#LoginOut()
#查询权限
def Auth(User,item):
    #如果已经在本线程注册过权限，直接返回，不需要再提交服务器查询
    if item in User_Auth:
        return 1
    else:
        tempflag=0
        Today = GetNow(TimeItem="Date")
        Sub_Field= {
            'sflag':'auth',
            'sid':'_04',
            'username':User,
            'Authority':item,
            'date':Today,
            }
        r = requests.post(Url,data = Sub_Field)
        rtext = r.text.strip()[1:]
        rtext = json.loads(rtext)
        if rtext!=0:
            User_Auth.append(rtext)
            tempflag = 1
        return tempflag
#print(Auth('quruyi0101','Current_Ratio'))
def NoAuth(item):
    whttp = 'http://localhost/test/sys/'
    rtext = '您目前还没有策略：'+item+'的权限，请登录'+whttp+'申请！'
    return rtext
#print(NoAuth('Momentum_based_on_Swing_Cutting'))


##############交易#############
#交易所代码：区分大小写
mcodedict = {"上交所":"SHSE","深交所":"SZSE","大商所":"DCE","郑商所":"CZCE","中金所":"CFFEX","上期所":"SHFE","能源交易中心":"INE","广期所":"GFEX","上金所":"SGE"}
###########################################################################
#############写数据#############
'''
order_type 下单类型 Y  （23 证券买入/担保品买入 24 证券卖出/担保品卖出）
price_type 委托价格类型 Y （1 最新价 2 对手价 3 指定价）
mode_price 委托价格 N （当price_type为1时，不生效，当price_type为3时，生效）
stock_code 证券代码 Y （支持格式“证券代码”或“市场代码+证券代码”）
volume 委托数量 Y
account_id 下单资金账号 Y （支持入参账号key）
act_type 账号类别 N （49 资金账号）
brokertype 账号类型 N （2 股票账号）
strategy 策略备注 N
note 投资备注 N
tradeparam 交易参数 N
inserttime 写入时间 N
basketpath 篮子文件绝对路径 N
'''
#下单
#orderset = ('23','1','0','SH600008','100','2018134','49','2')
# 迅投底层封装:单笔委托
def place_order(stock_code: str, volume: int, direction: str,
                price_type: str = '1', limit_price: float = 0) -> bool:
    if volume <= 0:
        return False
    volume = (volume // 100) * 100
    if volume <= 0:
        return False
    order_type = '23' if direction == 'buy' else '24'
    orderset = (order_type, price_type, str(limit_price), stock_code,
                str(volume), mqsaccount, '49', '2')
    rORDER = dbf.Table(mqdir+'XT_DBF_ORDER.dbf').open(mode=dbf.READ_WRITE)
    rORDER.append(orderset)
    rORDER.close()
    print(f"  [下单] {direction} {stock_code} {volume}股")
    return True

#获取内部行情服务最新报价
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
    return False

#撤销委托
def cancel_order(orderid):
    rORDER = dbf.Table(mqdir+'XT_DBF_ORDER.dbf').open(mode=dbf.READ_WRITE)
    corderset = ('cancel_order',mqsaccount,orderid)
    rORDER.append(corderset)
    rORDER.close()
    return None
#全部撤单
def cancel_all():
    """全撤未成交委托"""
    try:
        wwtcxlist = get_wtcx()
        for item in wwtcxlist:
            if item['委托状态'] != '已成':
                cancel_order(item['合同编号'])
        print("[撤单] 全部撤单")
    except Exception as e:
        print(f"[撤单] 失败: {e}")

#委托/撤单文件
def get_order(n):
    ORDER = DBF(outdir+'XT_DBF_ORDER.dbf',load=True,encoding='gbk') 
    orderlist = []
    fn = 0
    for record in ORDER:
        if fn ==n:
            tdict ={'order_type':record['order_type'],'price_type':record['price_type'],'stock_code':record['stock_code'],'volume':record['volume'],'account_id':record['account_id']}
            orderlist.append(tdict)
            break
        else:
            fn+=1
        #for field in record:
            #print(field,"=", record[field], end = ",")
    return orderlist

#委托/撤单反馈文件
def get_orderresult(n):
    ORDERResult = DBF(outdir+'XT_DBF_ORDER_result.dbf',load=True,encoding='gbk')
    orderresultlist =[]
    fn = 0
    for record in ORDERResult:
        if fn ==n:
            tdict ={'orderId':record['orderId'],'message':record['message'],'status':record['status'],'taskMsg':record['taskMsg'],'orderNum':record['orderNum']}
            orderresultlist.append(tdict)
            break
        else:
            fn+=1
        #for field in record:
            #print(field,"=", record[field], end = ",")
    return orderresultlist

#持仓统计CCTJ
def get_cctj():
    CCTJ = DBF(outdir+'XT_CCTJ_Stock_'+TDate0+'.dbf',load=True,encoding='gbk')
    cctjlist = []
    for record in CCTJ:
        tdict = {'市场代码':record['市场代码'],'市场名称':record['市场名称'],'证券代码':record['证券代码'],'证券名称':record['证券名称'],'当前拥股':record['当前拥股'],'持仓成本':record['持仓成本'],'成本价':record['成本价'],'市值':record['市值'],'可用数量':record['可用数量'],'当日涨幅':record['当日涨幅'],'昨夜拥股':record['昨夜拥股'],'最新价':record['最新价']}
        cctjlist.append(tdict)
        #for field in record:
            #print(field,"=", record[field], end = ",")
    return cctjlist

#获取当前持仓 {stock_code: 可用数量}
def get_holdings() -> dict:
    try:
        positions = get_cctj()
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
    
#成交查询
def get_cjcx():
    CJCX = DBF(outdir+'XT_CJCX_Stock_'+TDate0+'.dbf',load=True,encoding='gbk')
    cjcxlist = []
    for record in CJCX:
        tdict = {'资金名称':record['资金账号'],'任务编号':record['任务编号'],'合同编号':record['合同编号'],'成交编号':record['成交编号'],'市场名称':record['证券市场'],'证券代码':record['证券代码'],'成交数量':record['成交数量'],'成交价格':record['成交价格'],'成交金额':record['成交金额'],'手续费':record['手续费'],'订单编号':record['订单编号'],'成交日期':record['成交日期'],'成交时间':record['成交时间']}
        cjcxlist.append(tdict)
        #for field in record:
            #print(field,"=", record[field], end = ",")
    return cjcxlist

#委托查询文件
def get_wtcx():
    WTCX = DBF(outdir+'XT_WTCX_Stock_'+TDate0+'.dbf',load=True,encoding='gbk')
    wtcxlist = []
    for record in WTCX:
        tdict = {'资金账号':record['资金账号'],'合同编号':record['合同编号'],'证券代码':record['证券代码'],'委托量':record['委托量'],'委托状态':record['委托状态'],'成交数量':record['成交数量'],'委托剩余量':record['委托剩余量'],'成交均价':record['成交均价'],'订单编号':record['订单编号'],'任务编号':record['任务编号']}
        wtcxlist.append(tdict)
        #for field in record:
            #print(field,"=", record[field], end = ",")
    return wtcxlist

#资金查询文件
def get_zjcx():
    ZJCX = DBF(outdir+'XT_ZJCX_Stock_'+TDate0+'.dbf',load=True,encoding='gbk')
    zjcxdict = {}
    for record in ZJCX:
        accid = record['资金账号']
        tdict = {'总资产':record['总资产'],'可用金额':record['可用金额'],'手续费':record['手续费'],'盈亏':record['盈亏'],'总市值':record['总市值']}
        zjcxdict[accid] = tdict
        #for field in record:
            #print(field,"=", record[field], end = ",")
    return zjcxdict

#获取可用资金
def get_cash() -> float:
    """获取可用资金"""
    try:
        wzjcxdict = get_zjcx()[mqsaccount]
        return float(wzjcxdict['可用金额'])
    except Exception as e:
        print(f"[资金] 查询失败: {e}")
        return 0

def is_close_soon(minutes: int = 5) -> bool:
    now = datetime.datetime.now()
    close_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return now >= close_time or (close_time - now).total_seconds() <= minutes * 60

def round_lot(vol: int) -> int:
    return max(0, (int(vol) // 100) * 100)

#############查询账户信息#############
#print(get_wtcx())
#print(get_cjcx())
#print(get_order(4))
#print(get_orderresult(4))

#################################################################################

#参数说明:wait_seconds:每一轮等待几秒,stop_abs:结束的绝对股数差异,stop_ratio:结束的比率差异,close_minutes:收盘前几分钟结束
#first_ratio:买单首次下单比例,final_wait:最后一轮兜底等待多少秒
DEFAULT_CONFIG = {
    'wait_seconds': 30,
    'stop_abs': 100,
    'stop_ratio': 0.05,
    'close_minutes': 5,
    'first_ratio': 0.95,
    'final_wait': 10,
}

# ============================================================
# 执行层：一轮
# ============================================================
def _execute_round(tasks: dict, price_type: str, limit_price: float,
                   wait_seconds: int) -> dict:
    if not tasks:
        return {}

    since = datetime.datetime.now().strftime('%H:%M:%S')

    for code, task in tasks.items():
        vol = round_lot(task['volume'])
        if vol > 0:
            place_order(code, vol, task['direction'], price_type, limit_price)

    time.sleep(wait_seconds)
    cancel_all()
    time.sleep(1)

    result = {}
    try:
        cjcxlist = get_cjcx()
        for item in cjcxlist:
            code = item['市场名称'] + item['证券代码']
            if code not in tasks:
                continue
            if item['成交时间'] < since:
                continue
            if code not in result:
                result[code] = {'filled': 0, 'cost': 0}
            result[code]['filled'] += int(item['成交数量'])
            result[code]['cost'] += float(item['成交金额'])
    except Exception as e:
        print(f"[成交] 查询失败: {e}")

    return {k: v for k, v in result.items() if v['filled'] > 0}


# ============================================================
# 执行层：混合执行
# ============================================================

def _execute_mixed(sell_targets: dict, buy_targets: dict,
                   price_type: str, limit_price: float, config: dict,
                   candidates: list = None) -> dict:
    """
    卖和买每轮同时进行，卖出回款滚入下一轮可用资金
    涨停买不到跳过，用候选池替换
    跌停卖不掉跳过
    """
    wait_seconds = config['wait_seconds']
    stop_abs = config['stop_abs']
    stop_ratio = config['stop_ratio']
    close_minutes = config['close_minutes']
    first_ratio = config['first_ratio']
    final_wait = config['final_wait']

    sell_cum = {code: 0 for code in sell_targets}
    sell_cum_cost = {code: 0 for code in sell_targets}
    buy_cum = {code: 0 for code in buy_targets}
    buy_cum_cost = {code: 0 for code in buy_targets}

    # 已放弃的股票（涨跌停）
    abandoned_sells = set()
    abandoned_buys = set()

    # 候选池索引
    cand_idx = 0

    initial_cash = get_cash()
    total_sell_proceeds = 0
    is_first_round = True

    while True:
        if is_close_soon(close_minutes):
            print(f"[执行] 收盘前{close_minutes}分钟，强制停止")
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

            # 跌停跳过
            if _is_limit_down(code):
                print(f"[卖] {code} 跌停，跳过")
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

                # 涨停跳过，记下剩余金额用于候选替换
                if _is_limit_up(code):
                    skipped_amount = remain * get_price(code)
                    if skipped_amount > 0:
                        total_need += skipped_amount
                        buy_need[code] = {'vol': 0, 'need': skipped_amount, 'skipped': True}
                    abandoned_buys.add(code)
                    print(f"[买] {code} 涨停，跳过，剩余{remain}股约{skipped_amount:.2f}元转候选")
                    continue

                order_vol = round_lot(int(remain * first_ratio)) if is_first_round else round_lot(remain)
                if order_vol <= 0:
                    continue

                price = get_price(code)
                if price <= 0:
                    continue
                need = order_vol * price
                buy_need[code] = {'vol': order_vol, 'need': need, 'skipped': False}
                total_need += need

            # 钱不够，按比例缩减
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

        # ---- 候选替换：涨停跳过的金额转到候选池 ----
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
                        print(f"[候选] {cand_code} 也涨停，换下一个")
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
                    print(f"[候选] {code} → {cand_code} {cand_vol}股 ({cand_need:.2f}元)")
                    replace_amount -= cand_need
                    if replace_amount <= 0:
                        break
                    cand_idx += 1

        # ---- 合并本轮 ----
        round_tasks = {}
        round_tasks.update(round_sells)
        round_tasks.update(round_buys)

        # 全是跳过的情况，直接退出循环
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
        print(f"\n[执行] 第{'首' if is_first_round else '续'}轮: 卖{n_sell}只 买{n_buy}只, 可用{available_cash:.2f}")
        is_first_round = False

        round_result = _execute_round(round_tasks, price_type, limit_price, wait_seconds)

        for code, res in round_result.items():
            if code in sell_targets:
                sell_cum[code] += res['filled']
                sell_cum_cost[code] += res['cost']
                total_sell_proceeds += res['cost']
                print(f"[卖] {code} 本轮{res['filled']}股, 累计{sell_cum[code]}/{sell_targets[code]}")
            elif code in buy_targets or (candidates and code in candidates):
                if code not in buy_cum:
                    buy_cum[code] = 0
                    buy_cum_cost[code] = 0
                buy_cum[code] += res['filled']
                buy_cum_cost[code] += res['cost']
                print(f"[买] {code} 本轮{res['filled']}股, 累计{buy_cum[code]}")

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
        print(f"\n[执行] 兜底: {len(final_tasks)}只")
        final_result = _execute_round(final_tasks, price_type, limit_price, final_wait)
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

    sell_result = {code: {'target': sell_targets[code], 'filled': sell_cum[code],
                           'cost': sell_cum_cost[code]} for code in sell_targets}
    buy_result = {code: {'target': buy_targets.get(code, 0), 'filled': buy_cum.get(code, 0),
                          'cost': buy_cum_cost.get(code, 0)} for code in 
                  set(list(buy_targets.keys()) + list(buy_cum.keys()))}

    return {'sell': sell_result, 'buy': buy_result}

'''
result = execute([
    ['SH600697', 'S', 200],
    ['SH600698', 'B', 100],
], candidates=['SZ000001', 'SH600000'])
'''

# ============================================================
# 算法层：TWAP
# ============================================================

def _execute_twap(sell_targets: dict, buy_targets: dict,
                  price_type: str, limit_price: float,
                  slices: int = 10, interval: int = 60, config: dict = None,
                  candidates: list = None) -> dict:
    if config is None:
        config = DEFAULT_CONFIG

    sell_slices = []
    buy_slices = []

    for code, target in sell_targets.items():
        sv = target // slices
        rem = target % slices
        for i in range(slices):
            if i >= len(sell_slices):
                sell_slices.append({})
            vol = sv + (rem if i == slices - 1 else 0)
            if vol > 0:
                sell_slices[i][code] = vol

    for code, target in buy_targets.items():
        sv = target // slices
        rem = target % slices
        for i in range(slices):
            if i >= len(buy_slices):
                buy_slices.append({})
            vol = sv + (rem if i == slices - 1 else 0)
            if vol > 0:
                buy_slices[i][code] = vol

    all_sell = {}
    all_buy = {}
    for i in range(slices):
        if is_close_soon(config['close_minutes']):
            break

        s = sell_slices[i] if i < len(sell_slices) else {}
        b = buy_slices[i] if i < len(buy_slices) else {}
        if not s and not b:
            continue

        print(f"\n[TWAP] 第{i+1}/{slices}片")
        r = _execute_mixed(s, b, price_type, limit_price, config, candidates=candidates)

        for code, v in r['sell'].items():
            if code not in all_sell:
                all_sell[code] = v
            else:
                all_sell[code]['filled'] += v['filled']
                all_sell[code]['cost'] += v['cost']

        for code, v in r['buy'].items():
            if code not in all_buy:
                all_buy[code] = v
            else:
                all_buy[code]['filled'] += v['filled']
                all_buy[code]['cost'] += v['cost']

        if i < slices - 1:
            time.sleep(interval)

    return {'sell': all_sell, 'buy': all_buy, 'algorithm': 'TWAP'}


# ============================================================
# 入口层
# ============================================================

def execute(orders: list,
            price_type: str = '1',
            limit_price: float = 0,
            algorithm: str = None,
            config: dict = None,
            candidates: list = None) -> dict:
    """
    统一入口

    orders: [['SH600697', 'B', 200], ['SH600698', 'S', 100], ...]
    algorithm: None / 'TWAP'
    candidates: 候选股票池 ['SZ000001', 'SH600000', ...]，涨停买不到时顺次替换
    """
    if config is None:
        config = DEFAULT_CONFIG

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

    holdings = get_holdings()
    for code in list(sell_targets.keys()):
        available = holdings.get(code, 0)
        if sell_targets[code] > available:
            sell_targets[code] = available
        if sell_targets[code] <= 0:
            del sell_targets[code]

    print(f"\n[执行] 卖出: {len(sell_targets)}只, 买入: {len(buy_targets)}只")
    if candidates:
        print(f"[执行] 候选池: {candidates}")

    if algorithm == 'TWAP':
        return _execute_twap(sell_targets, buy_targets, price_type, limit_price, 
                             config=config, candidates=candidates)
    else:
        return _execute_mixed(sell_targets, buy_targets, price_type, limit_price, 
                              config, candidates=candidates)



#################################################################################
# 定义一个从线程函数:接收数据
def mqReceiver(num):
    #连接socketio
    trec = socketio.Client()
    @trec.event
    def connect():
        print('mqReceiver connection established')

    #监听服务端推送消息
    @trec.event
    def user_message(data):
        print('user_message received with ', data)
        #sio.emit('my response', {'response': 'my response'})
    @trec.event
    def disconnect():
        print('disconnected from mqReceiverServer')
    #连接服务端 IP+端口
    trec.connect('http://10.10.98.51:3210')
    
    #@sio.on('pushToWebClient')
    @trec.on(mqquantname)
    def on_message(data):
        print('mqReceiver：',data)
        #收到记录之后先存储记录
        save_record(mqsaccount, 'order',data)
        # 【修改】不再直接创建线程执行交易，而是将指令放入队列（实现串行处理）
        submit_trade(data)  # 【新增】提交交易指令到队列
   #从服务器接收终止信息，终止程序
    @trec.on('exit')
    def handle_exit():
        print("Exiting...")
        #eventlet.sleep(0)  # 这行代码是为了确保事件处理函数执行完毕
        trec.disconnect()
        exit(0)  # 退出程序
    try:
        trec.wait()
    except (KeyboardInterrupt,SystemExit):
        trec.disconnect() 

tar = "小市值01-调仓目标-20260313110524:0#{'tqbasket':[['SH603788'#'SZ002614'#'SZ300838'#'SZ300729'#'SZ301208'#'SZ301131'#'SZ002790'#'SH603558'#'SZ000948'#'SZ002955']#[]#['SH605138'#7.24#2.0]#['SH603230'#11.67#2.0]#['SH603787'#13.57#2.0]#['SZ301195'#34.15#2.0]#['SH603153'#16.63#2.0]#['SH603073'#21.02#2.0]#['SH603886'#12.82#2.0]#['SH603677'#16.93#2.0]#['SZ300500'#12.35#2.0]#['SZ003013'#14.52#2.0]#['SZ003016'#8.39#2.0]#['SH605009'#29.63#2.0]#['SH603909'#11.57#2.0]#['SZ001368'#25.93#2.0]#['SH605151'#19.88#2.0]#['SZ301065'#24.72#2.0]#['SH603357'#8.37#2.0]#['SZ301519'#15.41#2.0]#['SH603657'#27.78#2.0]#['SZ300616'#13.18#2.0]#['SH603180'#20.13#2.0]#['SZ002732'#17.43#2.0]#['SZ301167'#17.94#2.0]#['SH603307'#40.07#2.0]#['SH603801'#9.43#2.0]#['SZ301310'#38.84#2.0]#['SH603029'#19.64#2.0]#['SZ300645'#19.24#2.0]#['SZ301520'#42.99#2.0]#['SH603711'#13.07#2.0]#['SZ300577'#20.26#2.0]#['SH600697'#12.98#2.0]#['SH605266'#20.1#2.0]#['SH603933'#21.81#2.0]#['SZ002331'#8.82#2.0]#['SZ300732'#7.59#2.0]#['SZ000619'#6.35#2.0]#['SZ300625'#12.75#2.0]#['SH603385'#7.11#2.0]#['SZ000910'#7.51#2.0]#['SZ002022'#5.94#2.0]#['SH603237'#17.23#2.0]#['SZ301355'#13.06#2.0]#['SZ001218'#26.07#2.0]#['SZ002566'#8.37#2.0]#['SH603201'#18.38#2.0]#['SZ301223'#19.81#2.0]#['SZ002521'#8.1#2.0]#['SH603518'#9.21#2.0]#['SH600327'#4.1#2.0]]#'_tqbasket':[['SZ000910'#7.5]#['SZ003030'#21.3]#['SH603307'#40.7]#['SZ002722'#15.88]#['SH603677'#17.47]#['SH605266'#20.22]#['SH605500'#9.2]#['SZ001211'#29.18]#['SZ000526'#35.22]#['SZ300736'#22.11]#['SZ002790'#8.19]#['SZ002976'#28.72]#['SZ301429'#21.63]#['SZ002521'#8.17]#['SZ300928'#33.53]#['SZ300949'#42.88]#['SZ301036'#30.96]#['SZ002959'#42.43]#['SH603180'#20.42]#['SH603602'#14.33]#['SH603206'#16.4]#['SH603518'#9.25]#['SZ301296'#8.42]#['SH603877'#15.51]#['SH600081'#11.86]#['SH605158'#8.25]#['SZ002732'#17.78]#['SZ001222'#21.12]#['SZ300729'#13.68]#['SH603886'#13.02]#['SH600097'#11.94]#['SH603661'#33.71]#['SZ002661'#9.54]#['SH603600'#11.02]#['SZ301126'#12.61]#['SZ001218'#26.17]#['SZ002991'#53.39]#['SZ001283'#64.15]#['SZ001368'#26.75]#['SH605151'#20.65]#['SZ003013'#14.59]#['SZ300838'#16.93]#['SH603768'#11.96]#['SH603788'#16.19]#['SZ301335'#27.95]#['SH603787'#13.88]#['SH603586'#18.09]#['SZ000049'#25.82]#['SZ301503'#39.36]#['SH603153'#16.64]]}"
#tar = "小市值01-调仓目标-20260313110524:10#20"
#tar = "小市值01-调仓目标-20260313110524:20#[['SH601899'#'B'#12.98#2.0]]"
#tar = "小市值01-调仓目标-20260313110524:20#[['SH600697'#'S'#12.98#2.0]]"

# 定义一个从线程函数:交易函数
#qmt or 掘金 or 无限易在这里实现
def mqTrader(tar):
    print('mqTarder start:')
    #print(tar)a
    #然后获取最新账户持仓记录
    actual_holdings_list = get_cctj()
    #print(f'最新账户持仓记录:{actual_holdings_list}')    
    orderkey, ordervalue = tar.split(':', 1)
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
    #查询账户信息
    wzjcxdict = get_zjcx()[mqsaccount]
    totalAssets = float(wzjcxdict['总资产'])
    totalMarketValue = float(wzjcxdict['总市值'])
    #availableBalance = float(wzjcxdict['可用金额'])
    #commission = wzjcxdict['手续费']
    #print(f'总资产：{totalAssets},总市值：{totalMarketValue},可用金额：{availableBalance},手续费:{commission}')
    if ordertype == '0':
        ordertext = eval(temptext0.replace('#',','))
        dict0 ={}
        list0 = ordertext['_tqbasket']
        #理论价格存储
        for item in list0:
            dict0[item[0]]=item[1]
        
        #取调仓集合
        HoldTargetList = ordertext['tqbasket']
        houxuan = HoldTargetList.pop(0)
        baoliu = HoldTargetList.pop(0)
        
        #print(houxuan)
        #print(baoliu)
        #print(HoldTargetList)
        
        BaseDict = {}

        TargetHoldDict = {}
        for ix0 in HoldTargetList:
            fv = ix0[0]
            fprice =  ix0[1]
            fpos = (ix0[2]/100)*totalAssets
            dict0[fv] = fprice
            TargetHoldDict[fv] = [fprice,fpos]
            BaseDict [fv] = fprice
            #print(HoldTargetList[ix])
            
        #print('目标持仓')
        #print(TargetHoldDict)
        
        #查询账户持仓信息
        holddict = {}
        wcctjlist = get_cctj()
        #print(wcctjlist)
        ix1 = 0
        while ix1<len(wcctjlist):
            #print(wcctjlist[ix1])
            tdict = wcctjlist[ix1]
            fv = tdict['市场代码']+tdict['证券代码']
            #print(fv)
            #[持仓方向,总持仓量,持仓市值,当前行情价格,当前可平仓位]
            holddict[fv] = [float(char) for char in [1,tdict['当前拥股'],tdict['市值'],tdict['最新价'],tdict['可用数量']]]
            if  BaseDict.get(fv) == None:
                BaseDict[fv] = float(tdict['最新价'])
            ix1+=1
        #print('目前持仓')
        #print(holddict)
        FList = []
        for (k,v) in TargetHoldDict.items():
            if k in holddict.keys():
                #print(v)
                Diff = v[1]-holddict.pop(k)[2]
                if Diff>0:
                    FList.append([k,"B",math.floor(Diff/v[0]/100)*100])
                elif Diff<0 and k not in baoliu:
                    FList.append([k,"S",math.floor(-Diff/v[0]/100)*100])
            else:
                FList.append([k,"B",math.floor(v[1]/v[0]/100)*100])
        for (k,v) in holddict.items():
            if k not in baoliu:
                FList.append([k,"S",math.floor(v[2]/v[3]/100)*100])
        print('调仓指令：')
        print(FList)
                
        save_record(mqsaccount, '调仓理论价格', f'{dict0}')
        execute(orders = FList,candidates = houxuan)
        
    elif ordertype =='10':
        #print(temptext0)
        ordertext = float(temptext0)/100
        #print(ordertext)
        #理论持仓比例
        print(f'理论持仓比例:{ordertext}')
        #目前账户持仓比例
        holdratio = float(totalMarketValue/totalAssets)
        print(f'目前账户持仓比例:{holdratio}')
        holddiff = holdratio-ordertext
        
        if holddiff>0 :            
            #print(type(actual_holdings_list))
            selllist = []
            for item in actual_holdings_list:
                acode = item['市场代码']+item['证券代码']
                
                gnum = math.floor((float(item['市值'])*holddiff)/float(item['最新价'])/100)*100
                
                selllist.append([acode,'S',gnum])
            execute(orders = selllist)
            
    elif ordertype == '20':
        ordertext = eval(temptext0.replace('#',','))
        print(f'收到指令：{ordertext}')
        dict0 = {}
        list1 = []
        for text in ordertext:
            dict0[text[0]] = text[2]
            #理论上应买入的金额
            lvalue = totalAssets*float(text[3])/100
            lnum = math.floor(lvalue/text[2]/100)*100
            list1.append([text[0],text[1],lnum])
            print(list1)
        save_record(mqsaccount, '理论价格', f'{dict0}')
        execute(orders = list1)
        
         

# 【新增】交易工作线程函数（单线程串行处理队列中的交易指令）
def trade_worker():
    """交易工作线程 - 单线程串行处理所有交易指令"""
    global _trade_worker_running
    _trade_worker_running = True
    
    print("交易工作线程启动，开始串行处理队列中的指令...")
    
    while _trade_worker_running:
        try:
            # 从队列获取指令，超时1秒以便检查退出标志
            tar = _trade_queue.get(timeout=1)
            print(f"\n{'='*50}")
            print(f"开始处理交易指令，队列剩余指令数: {_trade_queue.qsize()}")
            print(f"指令内容: {tar[:100]}...")
            print(f"{'='*50}")
            
            # 执行实际的交易逻辑
            mqTrader(tar)
            
            print(f"交易指令处理完成，队列剩余指令数: {_trade_queue.qsize()}\n")
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"交易执行异常: {e}")
            # 记录失败的指令
            save_record(mqsaccount, 'trade_error', f"指令:{tar[:100] if 'tar' in dir() else 'unknown'}, 错误:{str(e)}")
    
    print("交易工作线程退出")

# 【新增】提交交易指令到队列（非阻塞）
def submit_trade(tar):
    """提交交易指令到队列（非阻塞，立即返回）"""
    _trade_queue.put(tar)
    print(f"交易指令已加入队列，当前队列长度: {_trade_queue.qsize()}")

# 【新增】启动交易工作线程
def start_trade_worker():
    """启动交易工作线程（在主函数中调用一次）"""
    global _trade_worker_thread
    _trade_worker_thread = threading.Thread(target=trade_worker, name="TradeWorker", daemon=True)
    _trade_worker_thread.start()
    return _trade_worker_thread

# 【新增】停止交易工作线程
def stop_trade_worker():
    """停止交易工作线程"""
    global _trade_worker_running
    _trade_worker_running = False

# 定义主函数
def main():
    Login(mqusername,mqpassword)
    itAuth=mqquantID
    fAuthority=Auth(mqusername,itAuth)
    if fAuthority == 1:
        # 初始化数据库
        db_path = init_trade_db(mqsaccount)
        print(f"交易数据库路径: {db_path}")
        
        # 可选：记录初始持仓状态
        #initial_position = {}
        #save_record(mqsaccount, 'position',initial_position)
        
        # 这块儿还需要完成前期环境检查，如果都满足才可以继续
        # 创建目录
        create_directory_if_not_exists(outdir)
        print("_迅投QMT股票版 Main thread starting")
        znote = mqusername+"-"+mqquantname+"-账户注册-"+GetNow(TimeItem="YMDHMS")+":"+mqquantID+'#'+mqsaccount+'#'+mqusername+'#'+mqquantname+'#'+mqsassets
        print(znote)
        
        # 【新增】启动交易工作线程（单线程串行处理）
        start_trade_worker()
        
        _mqReceiver = threading.Thread(target=mqReceiver, args=(1,))
        threads.append(_mqReceiver)
        _mqReceiver.start()
        
        # 等待所有从线程完成
        for t in threads:
            t.join()
        print("Main thread finishing")
    else:
        print(NoAuth(mqquantname))
    

if __name__ == "__main__":
    #print(type(get_latest_position(mqsaccount)))
    #tt = {'小市值01': {'SH600008':200,'SH601615':500,'SZ002180':14500},'事件驱动': {'SH603833':6100,'SZ300091':300},'T0': {'SH600754':800,'SZ300957':300}}
    #print(tt)
    #save_record(mqsaccount,'position', tt)
    #print(get_latest_position(mqsaccount))
    
    #print(get_cctj())
    #main()
    #strategy_holdings = get_latest_position(mqquantID)
    #然后获取最新账户持仓记录
    #actual_holdings_list = get_cctj()
    #print(wcctjlist)
    #result = compare_holdings(strategy_holdings, actual_holdings_list)
    #print(result)  # False
    
    #保存命令
    #save_record(mqsaccount, 'order',tar)
    
    # 【注意】测试时如果直接调用main()会启动完整系统
    # 如果只想测试单个指令，可以取消下面的注释
    
    mqTrader(tar)
    
    # 启动完整系统
    #main()