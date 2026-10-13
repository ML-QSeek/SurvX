# -*- coding: utf-8 -*-
"""
期货CTA交易脚本 - 适配进程池版本 - 修复版
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
from typing import List, Dict, Any, Optional
from openpyxl import load_workbook

# 交易所代码
M_CODE_DICT = {
    "上交所": "SHSE", "深交所": "SZSE", "大商所": "DCE",
    "郑商所": "CZCE", "中金所": "CFFEX", "上期所": "SHFE",
    "能源交易中心": "INE", "广期所": "GFEX", "上金所": "SGE"
}

# 交易所大小写映射
交易所大小写 = {"DCE": "a", "CZCE": "A", "CFFEX": "A", "SHFE": "a", "INE": "a", "GFEX": "a"}


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


##############期货交易相关函数#############
# DBF表对象
table_place_order = None
table_cancel_order = None
table_raw_func = None


class Order(object):
    def __init__(self, account_id: str, symbol: str, volume: int, order_type: int, order_biz: int, price: float = 0,
                 sid: str = '', comment: str = '') -> None:
        """报单委托"""
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
        """撤单委托"""
        self.sid = sid
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


def place_order(dbf_dir: str, order: Order) -> str:
    """下单"""
    return place_orders(dbf_dir, [order])[0]


def place_orders(dbf_dir: str, orders: List[Order]) -> List[str]:
    """批量下单"""
    global table_place_order
    import dbf
    
    sids = []
    if table_place_order is None:
        filename = os.path.join(dbf_dir, "futures_orders.dbf")
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
        ord = (order.sid, order.account_id, order.symbol, order.volume, order.order_type, order.order_biz, order.price,
               order.comment)
        table_place_order.append(ord)
        sids.append(order.sid)

    return sids


def cancel_order(dbf_dir: str, order: CancelOrder) -> str:
    """撤单"""
    return cancel_orders(dbf_dir, [order])[0]


def cancel_orders(dbf_dir: str, orders: List[CancelOrder]) -> List[str]:
    """批量撤单"""
    global table_cancel_order
    import dbf
    
    sids = []
    if table_cancel_order is None:
        filename = os.path.join(dbf_dir, "futures_cancel_orders.dbf")
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


# 全部撤单
def all_cancel_order(mq_dir, account_id, out_dir):
    """全部撤单"""
    try:
        orders = get_orders(out_dir, account_id, status=[1, 2])  # 获取待成交订单
        if orders:
            for order in orders:
                cancel_order(dbf_dir=mq_dir, order=CancelOrder(sid=order['sid']))
    except Exception as e:
        print(f"全部撤单失败: {e}")


# 针对可交易总金额和持仓，按照合约价值尽可能相等为目标，进行资金分配
def fenchai(totalassets, bxuan):
    """资金分配算法"""
    bxuan = dict(sorted(bxuan.items(), key=lambda item: item[1]))
    holding = {}
    for key in bxuan.keys():
        if bxuan[key] == min(list(bxuan.values())):
            xmin = key
    hxuan = copy.copy(bxuan)
    nsum = totalassets

    while nsum > 0:
        thxuan = copy.copy(hxuan)
        tnsum = nsum
        anum = len(thxuan)
        avg = nsum / anum
        for (k, v) in thxuan.items():
            fe = int(avg / v)
            if fe > 0 and nsum >= fe * thxuan[k]:
                if holding.get(k) is None:
                    holding[k] = fe * thxuan[k]
                else:
                    holding[k] = holding[k] + fe * thxuan[k]
                nsum -= fe * thxuan[k]
            elif fe == 0 or nsum < thxuan[k]:
                hxuan.pop(k)
        if nsum == tnsum:
            break

    while nsum > 0:
        tnsum = nsum
        gt = max(list(holding.values()))
        for (k, v) in holding.items():
            dif = gt - v
            pos = bxuan[k]
            if dif >= pos and nsum >= pos:
                holding[k] = holding[k] + pos
                nsum -= pos
        if nsum == tnsum and nsum >= bxuan[xmin]:
            holding[xmin] = holding[xmin] + bxuan[xmin]
            nsum -= bxuan[xmin]
        elif nsum == tnsum:
            break

    nflag = 0
    while nflag == 0:
        for key in holding.keys():
            if holding[key] == min(list(holding.values())):
                minkey = key
        for key in holding.keys():
            if holding[key] == max(list(holding.values())):
                maxkey = key
        gt = holding[maxkey]
        mt = holding[minkey]
        dif = gt - mt
        pos0 = bxuan[minkey]
        pos1 = bxuan[maxkey]
        if pos0 >= pos1:
            tempdict = copy.copy(holding)
            tempdict[maxkey] = tempdict[maxkey] - (int(pos0 / pos1) + 1) * pos1
            tempdict[minkey] = tempdict[minkey] + pos0
            gt0 = max(list(tempdict.values()))
            mt0 = min(list(tempdict.values()))
            dif0 = gt0 - mt0
            if dif0 < dif:
                holding = copy.copy(tempdict)
            else:
                nflag = 1
        else:
            nflag = 1

    return holding


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


###########################
# 期货CTA专用交易算法
class FuturesCTATradingAlgorithm:
    """期货CTA专用交易算法"""
    
    def __init__(self, futures_info_file: str = None):
        self.name = "FuturesCTATradingAlgorithm"
        self.order_biz_dict = {'BK': 10, 'BP': 15, 'SK': 14, 'SP': 11}
        self.logger = logging.getLogger(f"TradingAlgorithm.{self.name}")
        
        # 加载期货信息
        self.futures_info = {}
        self._load_futures_info(futures_info_file)
    
    def _load_futures_info(self, futures_info_file: str = None):
        """加载期货信息"""
        try:
            if futures_info_file and os.path.exists(futures_info_file):
                wb = load_workbook(filename=futures_info_file)
                sheet = wb['ilist']
                for row in sheet.iter_rows(values_only=True):
                    if row[0]:
                        self.futures_info[row[0]] = [row[8], row[4]]
                self.logger.info(f"期货信息加载完成: {len(self.futures_info)} 个品种")
            else:
                # 默认期货信息
                self.futures_info = {
                    'IF': ['CFFEX', 300],
                    'IC': ['CFFEX', 200],
                    'IH': ['CFFEX', 300],
                    'TF': ['CFFEX', 10000],
                    'T': ['CFFEX', 10000],
                    'TS': ['CFFEX', 20000],
                }
                self.logger.warning(f"期货信息文件不存在: {futures_info_file}")
        except Exception as e:
            self.logger.error(f"加载期货信息失败: {e}")
            self.futures_info = {}
    
    def _convert_futures_symbol(self, symbol: str) -> str:
        """转换期货合约代码格式"""
        if not symbol or len(symbol) < 4:
            return symbol
            
        item = symbol[:-4]
        market = self.futures_info.get(item, [''])[0]
        
        if not market:
            return symbol
            
        if 交易所大小写.get(market) == 'a':
            fv_ = symbol.lower()
        elif 交易所大小写.get(market) == 'A':
            fv_ = symbol
        else:
            fv_ = symbol
            
        if market == 'CZCE':
            fv_ = fv_[:-4] + fv_[-3:]
            
        return f"{market}.{fv_}"
    
    def calculate_orders(self, fholdlist1: List, total_assets: float, account_id: str, out_dir: str) -> List[Dict]:
        """
        期货CTA算法：根据目标持仓列表计算交易指令
        
        Args:
            fholdlist1: 期货目标持仓列表
            total_assets: 总资产
            account_id: 账户ID
            out_dir: 输出目录
            
        Returns:
            交易指令列表
        """
        orders = []
        
        # 解析目标持仓
        if not fholdlist1:
            self.logger.warning("目标持仓列表为空")
            return orders
            
        CashTargetList = fholdlist1[0]
        资产下限 = CashTargetList[0] if len(CashTargetList) > 0 else 0
        杠杆比 = CashTargetList[1] if len(CashTargetList) > 1 else 1.0
        HoldTargetList = fholdlist1[1:]
        
        if total_assets < 资产下限:
            self.logger.warning(f"总资产 {total_assets} 低于资产下限 {资产下限}")
            return orders
            
        目标市值 = total_assets * 杠杆比
        
        # 构建目标持仓字典
        tholddict = {}
        bdict = {}
        
        for item in HoldTargetList:
            if len(item) < 3:
                continue
                
            fv = item[0]
            fprice = item[1] if item[1] > 0 else 1.0
            dk = item[2]
            
            item_code = fv[:-4]
            market_info = self.futures_info.get(item_code, ['', 1])
            market = market_info[0]
            chsh = market_info[1]
            
            if market and 交易所大小写.get(market) == 'a':
                fv_ = fv.lower()
            elif market and 交易所大小写.get(market) == 'A':
                fv_ = fv
            else:
                fv_ = fv
                
            if market == 'CZCE':
                fv_ = fv_[:-4] + fv_[-3:]
                
            fcode = f"{market}.{fv_}" if market else fv
            fvalue = fprice * chsh
            
            tholddict[fv] = [fvalue, dk, fcode, market]
            bdict[fv] = fvalue
        
        # 资金分配
        if not bdict:
            self.logger.warning("可交易品种列表为空")
            return orders
            
        fchdict = fenchai(目标市值, bdict)
        
        # 计算目标持仓
        TargetHoldDict = {}
        for (k, v) in fchdict.items():
            if k not in tholddict:
                continue
                
            fnums = v / tholddict[k][0] if tholddict[k][0] > 0 else 0
            dk = tholddict[k][1]
            if dk == 'DD':
                fnums = fnums
            elif dk == 'KD':
                fnums = -fnums
            TargetHoldDict[k] = fnums
        
        # 获取当前持仓
        holddict = {}
        try:
            wcctjlist = get_position(out_dir, account_id)
        except Exception as e:
            self.logger.warning(f"获取持仓失败: {e}")
            wcctjlist = []
        
        for tdict in wcctjlist:
            fvar = tdict.get('SYMBOL', '').split('.')
            if len(fvar) < 2:
                continue
                
            fcode = fvar[1]
            
            if fvar[0] == 'CZCE':
                fv = fcode[:-3] + '2' + fcode[-3:]
            else:
                fv = fcode
                
            fv = fv.upper()
            
            if fv not in holddict:
                holddict[fv] = {'总多单': 0, '今多单': 0, '总空单': 0, '今空单': 0, '净单量': 0}
                
            side = tdict.get('SIDE', '1')
            volume = int(tdict.get('VOLUME', 0))
            vol_today = int(tdict.get('VOL_TODAY', 0))
            
            if side == '1':
                holddict[fv]['总多单'] = volume
                holddict[fv]['今多单'] = vol_today
            else:
                holddict[fv]['总空单'] = volume
                holddict[fv]['今空单'] = vol_today
                
            holddict[fv]['净单量'] = holddict[fv]['总多单'] - holddict[fv]['总空单']
        
        # 计算交易指令
        DDict1 = copy.copy(TargetHoldDict)
        DDict0 = copy.copy(holddict)
        FList = []
        FListOrderList = []
        
        # 处理目标持仓与当前持仓的差异
        for (k, v) in DDict1.items():
            if k in DDict0:
                Diff = v - DDict0.pop(k)['净单量']
                FList.append([k, Diff])
            else:
                if v < 0:
                    item = 'SK'
                    v = -v
                else:
                    item = 'BK'
                FListOrderList.append([k, item, v])
        
        # 处理需要清仓的持仓
        for (k, v) in DDict0.items():
            FList.append([k, -v['净单量']])
        
        # 生成具体的交易指令
        for ntxt in FList:
            fcode = ntxt[0]
            fnums = ntxt[1]
            
            if fnums > 0:
                if fcode in holddict and holddict[fcode]['今空单'] > 0:
                    item = 'BK'
                    v = holddict[fcode]['总空单']
                    FListOrderList.append([fcode, item, v])
                else:
                    item = 'BP'
                    v = holddict[fcode]['总空单'] if fcode in holddict else 0
                    if v > 0:
                        FListOrderList.append([fcode, item, v])
                    dif = fnums - v
                    if dif > 0:
                        item = 'BK'
                        FListOrderList.append([fcode, item, dif])
            elif fnums < 0:
                if fcode in holddict and holddict[fcode]['今多单'] > 0:
                    item = 'SK'
                    v = holddict[fcode]['总多单']
                    FListOrderList.append([fcode, item, v])
                else:
                    item = 'SP'
                    v = holddict[fcode]['总多单'] if fcode in holddict else 0
                    if v > 0:
                        FListOrderList.append([fcode, item, v])
                    dif = -fnums - v
                    if dif > 0:
                        item = 'SK'
                        FListOrderList.append([fcode, item, dif])
        
        # 转换为订单格式
        for order_data in FListOrderList:
            fv = order_data[0]
            item = order_data[1]
            vol = int(order_data[2])
            
            if vol <= 0:
                continue
                
            fu_code = self._convert_futures_symbol(fv)
            orderbiz = self.order_biz_dict.get(item, 10)
            
            orders.append({
                "symbol": fu_code,
                "order_type": 2,  # 市价单
                "order_biz": orderbiz,
                "volume": vol,
                "action": item,
                "original_symbol": fv
            })
        
        self.logger.info(f"期货CTA算法生成 {len(orders)} 个交易指令")
        return orders
    
    def should_cancel_orders(self, pending_orders: List, market_conditions: Dict) -> List[str]:
        """
        期货CTA算法：根据市场条件决定是否撤销订单
        """
        cancel_list = []
        current_time = time.time()
        
        for order in pending_orders:
            order_time = order.get('created_time', 0)
            if current_time - order_time > 60:  # 超过60秒
                cancel_list.append(order.get('sid', ''))
        
        return cancel_list


class ScriptMain:
    """
    期货CTA交易脚本主类 - 遵循进程池接口规范
    从配置中读取所有参数，遵循迅投QMT模板架构
    支持前端消息推送
    修复多进程环境下的线程启动问题
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化期货CTA交易脚本
        
        Args:
            config: 脚本配置，必须包含:
                - username: 用户名
                - password: 密码
                - quant_id: 策略ID
                - quant_name: 策略名称
                - account: 账户ID
                - mq_dir: 期货数据目录
                - out_dir: 输出目录
                - assets: 资产类型
                - server_url: HTTP服务器地址
                - socketio_sender_url: SocketIO发送服务器地址
                - socketio_receiver_url: SocketIO接收服务器地址
                可选:
                - futures_info_file: 期货信息文件路径
                - data_queue: 数据队列（用于向前端发送消息）
        """
        self.config = config
        self.running = False
        
        # 从配置中读取参数
        self.MQ_USERNAME = config.get("username", "")
        self.MQ_PASSWORD = config.get("password", "")
        self.MQ_QUANT_ID = config.get("quant_id", "")
        self.MQ_QUANT_NAME = config.get("quant_name", "")
        self.MQ_ACCOUNT = config.get("account", "")
        self.MQ_DIR = config.get("mq_dir", "") + "fuhua/"
        self.OUT_DIR = config.get("out_dir", "")
        self.MQ_ASSETS = config.get("assets", "total")
        self.SERVER_URL = config.get("server_url", "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php")
        self.SOCKETIO_SENDER_URL = config.get("socketio_sender_url", "http://10.10.98.51:3211")
        self.SOCKETIO_RECEIVER_URL = config.get("socketio_receiver_url", "http://10.10.98.51:3210")
        self.FUTURES_INFO_FILE = config.get("futures_info_file", "F:/myproject/tmodellive/data/excel/期货信息.xlsx")
        
        # 数据队列（用于向前端发送消息）
        self.data_queue = config.get("data_queue", None)
        
        # 验证必要参数
        required_params = ["username", "password", "quant_id", "quant_name", "account"]
        missing_params = [p for p in required_params if not self.config.get(p)]
        if missing_params:
            raise ValueError(f"缺少必要参数: {missing_params}")
        
        # 工作线程列表
        self.worker_threads = []
        
        # 交易算法
        self.trading_algorithm = None
        
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
        
        # 发送初始化消息到前端
        self._send_to_frontend({
            "type": "system",
            "level": "info",
            "message": f"初始化期货CTA交易脚本: {self.MQ_QUANT_NAME}",
            "timestamp": get_now(TimeItem="DateTime"),
            "account": self.MQ_ACCOUNT,
            "strategy": self.MQ_QUANT_NAME,
            "multiprocess_env": self._in_multiprocess_env
        })
        
        self.logger.info(f"初始化期货CTA交易脚本: {self.MQ_QUANT_NAME}")
        self.logger.info(f"账号: {self.MQ_ACCOUNT}, 用户: {self.MQ_USERNAME}")
        self.logger.info(f"数据目录: {self.MQ_DIR}, 输出目录: {self.OUT_DIR}")
        self.logger.info(f"期货信息文件: {self.FUTURES_INFO_FILE}")
        self.logger.info(f"SocketIO发送地址: {self.SOCKETIO_SENDER_URL}")
        self.logger.info(f"SocketIO接收地址: {self.SOCKETIO_RECEIVER_URL}")
        self.logger.info(f"多进程环境: {self._in_multiprocess_env}")
    
    def _setup_logging(self):
        """设置日志"""
        script_name = self.config.get("config_name", f"futures_cta_{self.MQ_QUANT_NAME}")
        
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
                log_dir = os.path.join("logs", "futures_cta", script_name)
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"{datetime.datetime.now().strftime('%Y%m%d')}.log")
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                
                # 格式化
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
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
                
                # 初始化交易算法
                if not self.trading_algorithm:
                    self._init_trading_algorithm()
                
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
                "message": "正在启动期货CTA交易脚本...",
                "timestamp": get_now(TimeItem="DateTime")
            })
            
            # 初始化交易算法
            self._init_trading_algorithm()
            
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
            
            success_msg = "期货CTA交易脚本启动成功"
            self.logger.info(success_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "success",
                "message": success_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {
                    "account": self.MQ_ACCOUNT,
                    "strategy": self.MQ_QUANT_NAME,
                    "algorithm": self.trading_algorithm.name if self.trading_algorithm else "未初始化",
                    "期货品种数": len(self.trading_algorithm.futures_info) if self.trading_algorithm else 0,
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
            info_msg = "正在停止期货CTA交易脚本..."
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
            
            success_msg = "期货CTA交易脚本已停止"
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
        info_msg = "正在重启期货CTA交易脚本..."
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
    
    def _init_trading_algorithm(self):
        """初始化交易算法"""
        try:
            self.trading_algorithm = FuturesCTATradingAlgorithm(self.FUTURES_INFO_FILE)
            info_msg = f"初始化期货CTA交易算法: {self.trading_algorithm.name}"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {
                    "算法名称": self.trading_algorithm.name,
                    "加载期货品种数": len(self.trading_algorithm.futures_info)
                }
            })
        except Exception as e:
            self.logger.error(f"初始化交易算法失败: {e}")
            # 创建简单的期货CTA算法
            self.trading_algorithm = FuturesCTATradingAlgorithm()
            info_msg = f"使用默认期货CTA交易算法: {self.trading_algorithm.name}"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "system",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            
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
            
            trader_thread = threading.Thread(
                target=self._execute_trade_safe,
                args=(data,),
                name=f"TradeExecutor_{self.MQ_QUANT_NAME}",
                daemon=True
            )
            trader_thread.start()
            self.worker_threads.append(trader_thread)
        
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
    
    # ========== 新增：安全版本的交易执行 ==========
    def _execute_trade_safe(self, trade_data):
        """安全执行交易"""
        try:
            self._execute_trade(trade_data)
        except Exception as e:
            error_msg = f"执行交易异常: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    # ===========================================
    
    def _execute_trade_command(self, data: Dict):
        """执行交易命令（供外部调用）"""
        try:
            trade_data = data.get("trade_data", "")
            if not trade_data:
                error_msg = "交易数据为空"
                self.logger.error(error_msg)
                self._send_to_frontend({
                    "type": "trade",
                    "level": "error",
                    "message": error_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return {"success": False, "message": "交易数据为空"}
            
            info_msg = "收到手动交易命令"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            
            trader_thread = threading.Thread(
                target=self._execute_trade_safe,
                args=(trade_data,),
                name=f"ManualTrade_{self.MQ_QUANT_NAME}",
                daemon=True
            )
            trader_thread.start()
            self.worker_threads.append(trader_thread)
            
            return {"success": True, "message": "交易命令已接收，正在执行"}
            
        except Exception as e:
            error_msg = f"执行交易命令失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return {"success": False, "message": f"执行交易命令失败: {str(e)}"}
    
    def _execute_trade(self, trade_data):
        """执行交易"""
        info_msg = "开始执行期货CTA交易"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "trade",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime")
        })
        
        try:
            # 解析交易数据
            tsour = trade_data.split(':', 1)[1][:1]
            torder = trade_data.split(':', 1)[1][2:]
            
            try:
                # 尝试解析为JSON格式
                fholdlist1 = json.loads(torder.replace('#', ','))
            except:
                # 尝试解析为Python对象
                fholdlist1 = eval(torder.replace('#', ','))
            
            # 执行期货CTA交易逻辑
            self._execute_futures_cta_trade(fholdlist1)
            
            info_msg = "期货CTA交易执行完成"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "success",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            
        except Exception as e:
            error_msg = f"执行交易异常: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            traceback.print_exc()
    
    def _execute_futures_cta_trade(self, fholdlist1):
        """执行期货CTA交易"""
        BaseDict = {}
        
        # 查询账户信息
        try:
            cash_info = get_cash(self.OUT_DIR, self.MQ_ACCOUNT)
            if not cash_info:
                error_msg = "无法获取账户资金信息"
                self.logger.error(error_msg)
                self._send_to_frontend({
                    "type": "trade",
                    "level": "error",
                    "message": error_msg,
                    "timestamp": get_now(TimeItem="DateTime")
                })
                return
            cash = cash_info[0]
        except Exception as e:
            error_msg = f"获取账户信息失败: {e}"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return
            
        总资产 = cash.get('NAV', 0)
        
        info_msg = f"开始执行交易，总资产: {总资产}"
        self.logger.info(info_msg)
        self._send_to_frontend({
            "type": "trade",
            "level": "info",
            "message": info_msg,
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {"total_assets": 总资产}
        })
        
        # 使用期货CTA算法计算交易指令
        if self.trading_algorithm:
            orders = self.trading_algorithm.calculate_orders(fholdlist1, 总资产, self.MQ_ACCOUNT, self.OUT_DIR)
        else:
            error_msg = "交易算法未初始化"
            self.logger.error(error_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "error",
                "message": error_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
            return
        
        # 执行交易
        if orders:
            info_msg = f"开始执行 {len(orders)} 个交易指令"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime"),
                "data": {"order_count": len(orders)}
            })
            
            trflag = 0
            i = 0
            SidList = []
            wtlist = []
            
            while trflag == 0:
                # 取消掉全部尚未成交的委托单
                if wtlist:
                    all_cancel_order(wtlist, self.MQ_DIR)
                    wtlist.clear()
                time.sleep(1)
                
                # 检查时间，收盘前停止
                ltime = time.localtime()
                # 期货日盘收盘前1分钟停止交易
                if ltime.tm_hour >= 14 and ltime.tm_min > 59:
                    info_msg = "临近收盘，停止交易"
                    self.logger.info(info_msg)
                    self._send_to_frontend({
                        "type": "trade",
                        "level": "warning",
                        "message": info_msg,
                        "timestamp": get_now(TimeItem="DateTime")
                    })
                    trflag = 1
                    continue
                
                if i > 5:
                    trflag = 1
                    continue
                
                # 执行订单
                SidList.clear()
                for order_data in orders:
                    symbol = order_data["symbol"]
                    order_type = order_data.get("order_type", 2)
                    order_biz = order_data.get("order_biz", 10)
                    volume = order_data.get("volume", 0)
                    action = order_data.get("action", "未知")
                    
                    if volume <= 0:
                        continue
                    
                    # 下单
                    order = Order(
                        account_id=self.MQ_ACCOUNT, 
                        symbol=symbol, 
                        volume=volume,
                        order_type=order_type,
                        order_biz=order_biz,
                        price=0,  # 市价委托
                        comment=f'期货CTA算法:{self.trading_algorithm.name}'
                    )
                    
                    sid = place_order(dbf_dir=self.MQ_DIR, order=order)
                    SidList.append(sid)
                    wtlist.append(sid)
                    
                    trade_msg = f"下单: {symbol} {action} {volume}手, 订单ID: {sid}"
                    self.logger.info(trade_msg)
                    self._send_to_frontend({
                        "type": "trade",
                        "level": "info",
                        "message": trade_msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {
                            "symbol": symbol,
                            "action": action,
                            "volume": volume,
                            "order_id": sid,
                            "order_type": "市价单"
                        }
                    })
                
                time.sleep(60)
                
                # 检查待成交订单
                pending_orders = []
                if SidList:
                    try:
                        order_status = get_orders(self.OUT_DIR, self.MQ_ACCOUNT, sids=SidList, status=[1, 2])
                        for order in order_status:
                            pending_orders.append({
                                'sid': order['sid'],
                                'symbol': order['symbol'],
                                'price': order.get('price', 0),
                                'created_time': time.time() - 30
                            })
                    except Exception as e:
                        error_msg = f"获取订单状态失败: {e}"
                        self.logger.error(error_msg)
                        self._send_to_frontend({
                            "type": "trade",
                            "level": "error",
                            "message": error_msg,
                            "timestamp": get_now(TimeItem="DateTime")
                        })
                
                # 检查是否需要撤销订单
                if pending_orders:
                    cancel_list = self.trading_algorithm.should_cancel_orders(
                        pending_orders=pending_orders,
                        market_conditions={}
                    )
                    
                    if cancel_list:
                        self.logger.info(f"需要撤销 {len(cancel_list)} 个订单")
                        self._send_to_frontend({
                            "type": "trade",
                            "level": "warning",
                            "message": f"需要撤销 {len(cancel_list)} 个超时订单",
                            "timestamp": get_now(TimeItem="DateTime"),
                            "data": {"cancel_count": len(cancel_list)}
                        })
                        
                        for sid in cancel_list:
                            cancel_order(dbf_dir=self.MQ_DIR, order=CancelOrder(sid=sid))
                            cancel_msg = f"撤销订单: {sid}"
                            self.logger.info(cancel_msg)
                            self._send_to_frontend({
                                "type": "trade",
                                "level": "info",
                                "message": cancel_msg,
                                "timestamp": get_now(TimeItem="DateTime"),
                                "data": {"order_id": sid}
                            })
                
                i += 1
                
                # 更新执行进度
                if i <= 5:
                    progress_msg = f"交易执行中，第 {i} 轮"
                    self._send_to_frontend({
                        "type": "trade",
                        "level": "info",
                        "message": progress_msg,
                        "timestamp": get_now(TimeItem="DateTime"),
                        "data": {"round": i, "total_rounds": 5}
                    })
        else:
            info_msg = "没有需要执行的交易指令"
            self.logger.info(info_msg)
            self._send_to_frontend({
                "type": "trade",
                "level": "info",
                "message": info_msg,
                "timestamp": get_now(TimeItem="DateTime")
            })
        
        # 发送交易结果
        senddif(BaseDict, self.MQ_USERNAME, self.MQ_QUANT_NAME, self.OUT_DIR)
        
        # 发送交易完成消息
        self._send_to_frontend({
            "type": "trade",
            "level": "success",
            "message": "交易执行完成",
            "timestamp": get_now(TimeItem="DateTime"),
            "data": {"status": "completed", "order_count": len(orders) if orders else 0}
        })
    
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
                
                # 期货交易时间监控
                ltime = time.localtime()
                # 期货日盘收盘前1分钟
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
            if 'futures_info_file' in new_config:
                self.FUTURES_INFO_FILE = new_config['futures_info_file']
                # 重新初始化算法
                self._init_trading_algorithm()
            
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
            "algorithm": self.trading_algorithm.name if self.trading_algorithm else "None",
            "end_flag": self.end_flag['endflag'],
            "mq_dir": self.MQ_DIR,
            "out_dir": self.OUT_DIR,
            "socketio_sender_url": self.SOCKETIO_SENDER_URL,
            "socketio_receiver_url": self.SOCKETIO_RECEIVER_URL,
            "futures_info_file": self.FUTURES_INFO_FILE,
            "futures_count": len(self.trading_algorithm.futures_info) if self.trading_algorithm else 0,
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
        "config_name": "futures_cta_trader",
        "username": "quruyi0101",
        "password": "quruyi0101",
        "quant_id": "QI46028792",
        "quant_name": "期货全品种cta01",
        "account": "252129ac-7d9a-11f0-ab52-00163e022aa6",
        "mq_dir": "D:/trader/",
        "out_dir": "D:/trader/",
        "assets": "total",
        "server_url": "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php",
        "socketio_sender_url": "http://10.10.98.51:3211",
        "socketio_receiver_url": "http://10.10.98.51:3210",
        "futures_info_file": "F:/myproject/tmodellive/data/excel/期货信息.xlsx"
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
    
    
    
    
'''
from process_manager import get_process_pool

# 获取进程池
pool = get_process_pool()

# 创建期货CTA交易进程配置
futures_cta_config = {
    "script_path": "futures_cta_trader.py",
    "config_name": "期货CTA_001",
    "username": "quruyi0101",
    "password": "quruyi0101",
    "quant_id": "QI46028792",
    "quant_name": "期货全品种cta01",
    "account": "252129ac-7d9a-11f0-ab52-00163e022aa6",
    "mq_dir": "D:/trader/",
    "out_dir": "D:/trader/",
    "assets": "total",
    "server_url": "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php",
    "socketio_sender_url": "http://10.10.98.51:3211",
    "socketio_receiver_url": "http://10.10.98.51:3210",
    "futures_info_file": "F:/myproject/tmodellive/data/excel/期货信息.xlsx"
}

# 创建进程
process_id = pool.create_process(futures_cta_config)
print(f"期货CTA交易进程已启动: {process_id}")

# 发送命令（与迅投QMT完全相同的接口）
pool.send_command_to_process(process_id, "get_status")
pool.send_command_to_process(process_id, "pause")
pool.send_command_to_process(process_id, "resume")
pool.send_command_to_process(process_id, "cancel_all_orders")
'''