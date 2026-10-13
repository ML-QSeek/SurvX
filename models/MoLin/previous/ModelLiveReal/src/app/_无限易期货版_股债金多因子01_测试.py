# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 18:14:54 2024

@author: test
"""
import sys
import os
import requests
import socketio
import json
import time
import datetime
import csv
import copy
import threading
import shutil
from openpyxl import load_workbook



#账号名称
mqusername = 'quruyi0101'
mqpassword = 'quruyi0101'
#策略名称
mqquantname = '股债金多因子01'
#策略编号
mqquantID = 'QI14903108'
#股票账号/路径
mqsaccount = '13817993656'
mqdir =  'Z:/'+mqsaccount+'/order'
outdir = 'Z:/'+mqsaccount
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
Url = 'http://localhost/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php'

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
#exchangedict={"中国金融期货交易所":"CFFEX","上海期货交易所":"SHFE","上海国际能源交易中心":"INE","郑州商品交易所":"CZCE","大连商品交易所":"DCE","广州期货交易所":"GFEX"} 
mcodedict = {"上交所":"SHSE","深交所":"SZSE","大商所":"DCE","郑商所":"CZCE","中金所":"CFFEX","上期所":"SHFE","能源交易中心":"INE","广期所":"GFEX","上金所":"SGE"}
ucode = {'AccountInfo':'utf-8','PositionInfo':'utf-8','TradeInfo':'utf-8','OrderInfo':'ANSI'}
交易所大小写 = {"DCE":"a","CZCE":"A","CFFEX":"A","SHFE":"a","INE":"a","GFEX":"a"}
###########################################################################
#移动文件
def move_folder(source_folder, destination_folder):
    shutil.move(source_folder, destination_folder)

#单笔委托
def place_order(olist):
    with open(outdir+'/tmp/or.csv','a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['交易所代码','合约代码','数量','买卖','开平','类型','时态','价格类型','价格','经纪公司编号','投资者账号','委托类型','报单编号','备注'])
        writer.writerow(olist)
    move_folder(outdir+'/tmp/or.csv', outdir+'/order/or.csv')
    return None
#全部撤销委托
def all_cancel_order():
    with open(outdir+'/tmp/cor.csv','a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['交易所代码','合约代码','数量','买卖','开平','类型','时态','价格类型','价格','经纪公司编号','投资者账号','委托类型','报单编号','备注'])
        交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注 = '','','','','','','','','','',mqsaccount,3,'',''
        corderlist = [交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注]
        writer.writerow(corderlist)
    move_folder(outdir+'/tmp/cor.csv', outdir+'/order/cor.csv')
    return None

#账户信息
def get_AccountInfo():
    #经纪公司编号0 投资者编号1 资金帐号2 上次结算准备金3 上日可用资金4 入金金额5 出金金额6 占用保证金7 期权权利金收支8 手续费9 冻结的保证金10 冻结权利金11 冻结手续费12 平仓盈亏13 持仓盈亏14 可用资金15 结算准备金16 多头占用保证金17 空头占用保证金18 多头冻结的保证金19 空头冻结的保证金20 动态权益21 风险度22 其他费用23 质押金额24 币种25;
    zjcxdict = {}
    with open(outdir+'/AccountInfo.txt', 'r', encoding=ucode['AccountInfo']) as infile:
        tlist = infile.read().split(',')
        accid = tlist[2]
        tdict = {'动态权益':tlist[21],'可用资金':tlist[15],'手续费':tlist[9],'占用保证金':tlist[7],'风险度':tlist[22]}
        zjcxdict[accid] = tdict
    return zjcxdict

#委托回报
def get_OrderInfo():
    wtcxlist = []
    #经纪公司编号0 投资者编号1 交易所代码2 合约代码3 买卖方向4 开平标志5 投机套保标志6 价格7 数量8 报单状态9 系统报单编号10 外部报单编号11 交易日12 数据插入时间13 资金帐号14 错误代码15 错误信息16;
    with open(outdir+'/OrderInfo.txt', 'r', encoding=ucode['OrderInfo']) as infile:
        for line in infile:
            tlist = line.split(',')
            tdict = {'投资者编号':tlist[1],'交易所代码':tlist[2],'合约代码':tlist[3],'买卖方向':tlist[4],'开平标志':tlist[5],'成交价格':tlist[7],'成交数量':tlist[8],'成交编号':tlist[9],'系统报单编号':tlist[10],'外部报单编号':tlist[11]}
            wtcxlist.append(tdict)
    return wtcxlist

#持仓文件
def get_PositionInfo():
    #投资者账号0 交易所代码1 合约代码2 买卖3 投机套保4 初始昨持仓量5 初始昨日持仓成本6 总持仓量7 昨持仓量8 总持仓可平仓数量9 总冻结持仓10 昨冻结持仓11 今开仓量12 今平仓量13 合约昨结算价14;
    cctjlist = []
    with open(outdir+'/PositionInfo.txt', 'r', encoding=ucode['PositionInfo']) as infile:
        for line in infile:
            tlist = line.split(',')
            tdict = {'投资者账号':tlist[0],'交易所代码':tlist[1],'合约代码':tlist[2],'买卖':tlist[3],'总持仓量':tlist[7],'昨持仓量':tlist[8],'今开仓量':tlist[12],'今平仓量':tlist[13]}
            cctjlist.append(tdict)
    return cctjlist

#成交回报
def get_TradeInfo():
    cjcxlist = []
    #经纪公司编号0 投资者编号1 交易所代码2 合约代码3 买卖方向4 开平标志5 投机套保标志6 成交价格7 成交数量8 成交编号9 系统报单编号10 外部报单编号11 交易日12 成交时间13;
    with open(outdir+'/TradeInfo.txt', 'r', encoding=ucode['TradeInfo']) as infile:
        for line in infile:
            tlist = line.split(',')
            tdict = {'投资者编号':tlist[1],'交易所代码':tlist[2],'合约代码':tlist[3],'买卖方向':tlist[4],'开平标志':tlist[5],'成交价格':tlist[7],'成交数量':tlist[8],'成交编号':tlist[9],'系统报单编号':tlist[10],'外部报单编号':tlist[11]}
            cjcxlist.append(tdict)
    return cjcxlist

#针对可交易总金额和持仓，按照合约价值尽可能相等为目标，进行资金分配
def fenchai(totalassets,bxuan):
    #print(totalassets)
    bxuan = dict(sorted(bxuan.items(), key=lambda item: item[1])) 
    #print(bxuan)
    holding = {}
    for key in bxuan.keys():
        if bxuan[key] == min(list(bxuan.values())):  
            xmin = key
    hxuan =copy.copy(bxuan)
    #print(hxuan)
    nsum = totalassets
    #print(nsum)
    
    while nsum>0 :
        #hxuan = dict(sorted(hxuan.items(), key=lambda item: item[1])) 
        thxuan = copy.copy(hxuan)
        tnsum = nsum
        anum = len(thxuan)
        #print(anum)
        avg = nsum/anum
        #print(avg)
        for (k,v) in thxuan.items():
            #print('11111')
            #print(avg)
            #fe = round(avg/v,0)
            fe = int(avg/v)
            #print('22222')
            #print(fe)
            if fe>0 and nsum>=fe*thxuan[k]:
                if holding.get(k)==None:
                    holding[k] = fe*thxuan[k]
                else:
                    holding[k] = holding[k]+fe*thxuan[k]
                nsum -= fe*thxuan[k]
            elif fe==0 or nsum<thxuan[k]:
                #print(nsum)
                hxuan.pop(k)
        #print(hxuan)
        if nsum==tnsum:
            break
    #print(holding)
    while nsum>0:
        tnsum = nsum
        gt = max(list(holding.values()))
        for (k,v) in holding.items():
            dif = gt - v
            pos = bxuan[k]
            if dif>=pos and nsum>=pos:
                holding[k]=holding[k]+pos
                nsum-=pos
        if nsum==tnsum and nsum>=bxuan[xmin]:
            holding[xmin]=holding[xmin]+bxuan[xmin]
            nsum-=bxuan[xmin]
        elif nsum==tnsum:
            break
    nflag = 0
    while nflag==0:
       for key in holding.keys():
           if holding[key] == min(list(holding.values())):
               minkey = key
       for key in holding.keys():
           if holding[key] == max(list(holding.values())):
               maxkey = key        
       gt = holding[maxkey]
       mt = holding[minkey]
       dif = gt-mt
       pos0 = bxuan[minkey]
       pos1 = bxuan[maxkey]
       if pos0>=pos1:
           tempdict=copy.copy(holding)
           tempdict[maxkey]=tempdict[maxkey]-(int(pos0/pos1)+1)*pos1
           tempdict[minkey]=tempdict[minkey]+pos0
           gt0=max(list(tempdict.values()))
           mt0=min(list(tempdict.values()))
           dif0=gt0-mt0
           if dif0<dif:
               holding=copy.copy(tempdict)
           else:
               nflag=1
       else:
           nflag = 1  
    #print(nsum)
    #print(sum(list(holding.values()))) 
    #print(len(list(holding.values()))) 
    #print(holding)
    return holding
#a =2000
#bdict = {'x1':79,'x2':35,'x3':33,'x4':45,'x5':2,'x6':87}
#bdict = {'x1':79,'x2':35,'x3':33,'x4':45,'x5':1}
#print(fenchai(a,bdict))

#获取期货合约代码字典
# 加载Excel文件
wb = load_workbook(filename='F:/myproject/tmodellive/data/excel/期货信息.xlsx')
# 选择工作表
sheet = wb['ilist']
fmsgdict = {}
# 遍历工作表中的行
for row in sheet.iter_rows(values_only=True):
    fmsgdict[row[0]]=[row[8],row[4]]
#print(fmsgdict)


#############查询账户信息#############
'''
print(get_AccountInfo())
OrderInfo = get_OrderInfo()
print(OrderInfo)
PositionInfo = get_PositionInfo()
print(PositionInfo)
TradeInfo = get_TradeInfo()
print(TradeInfo)
'''
#############写数据#############
'''
交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注 = 'CFFEX','IH2510',1,'B',0,0,'',2,0,1,'13817993656',1,'',''
orderlist = [交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注]
place_order(orderlist)
all_cancel_order()
'''

#交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注 = 'DCE','m2512',1,'B',0,0,'',2,0,1,'13817993656',1,'',''
#orderlist = [交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注]
#place_order(orderlist)
#all_cancel_order()



#############收到信息##############
def senddif(BaseDict):
    #结束之后，计算交易误差发送给服务器
    #汇总交易记录
    OrderStatusList = []
    #汇总交易误差
    DiffDict = {}
    #订单编号
    SidList = ['or173692150662461220', 'or173692150696754570', 'or173692150676886775', 'or173692150670640245', 'or173692150686334055', 'or173692150624675257', 'or173692150613860012', 'or173692150602465464', 'or173692150682421437', 'or173692152286539146', 'or173692152249925454', 'or173692152217484415', 'or173692152258186995', 'or173692152205937784', 'or173692152256019894', 'or173692152235124216', 'or173692152254656595', 'or173692152216936704', 'or173692153778923385', 'or173692153725481541', 'or173692153702625057', 'or173692153874012309', 'or173692153891680306', 'or173692153855688141', 'or173692153878938140', 'or173692153810353465', 'or173692153843184696']
    with open(outdir+'/order_status.csv', 'r', encoding='utf-8') as infile:
        #完整读取出来
        ttxt = infile.read().split('\n')
        i1 = 1
        while i1<len(ttxt)-1:
            tlist = ttxt[i1].split(',')
            if tlist[1] in SidList:
                diff =  tlist[18]*tlist[13] - BaseDict[tlist[5]]
                DiffDict[tlist[5]] = DiffDict[tlist[5]]+diff
            #[sid,标的代码,委托类型,委托业务属性,委托状态,委托价格,委托量,已成量,已成交均价,已成交金额]
            OrderStatusList.append([tlist[1],tlist[5],tlist[6],tlist[7],tlist[8],tlist[11],tlist[12],tlist[13],tlist[18],tlist[19]])
            i1+=1
    #发送汇总后的交易误差（这块儿的ttxt好像应该换成DiffDict）
    nnote = mqusername+"-"+mqquantname+"-交易误差-"+GetNow(TimeItem="YMDHMS")+":"+json.dumps(ttxt)
    #print(nnote)
    #subprocess.run(["python","F:/myproject/mtrade/_data/asend0_.py",nnote], stdout=subprocess.PIPE, universal_newlines=True)
    #完整交易记录整理后发送给服务器
    ttxt =  json.dumps(OrderStatusList)
    if ttxt !="":
        nnote = mqusername+"-"+mqquantname+"-交易记录-"+GetNow(TimeItem="YMDHMS")+":"+ttxt
        #print(nnote)
        #subprocess.run(["python","F:/myproject/mtrade/_data/asend0_.py",nnote], stdout=subprocess.PIPE, universal_newlines=True)
    else:
        print("没有成交记录！")
    print("命令执行完毕！")

#################################################################################
# 定义一个从线程函数:发送数据
def mqSender(znote):
    endflag = {}
    endflag['endflag']=0
    #asend0_
    #nnote1 = "[['SZ300335'#'SZ301338'#'SZ003003'#'SH600854'#'SZ300717'#'SZ301138'#'SZ002858'#'SZ002806'#'SZ300235'#'SH605180']#['Cash'#0]#['SH600051'#6.95#20]#['SH600615'#13.31#20]#['SH600730'#6.93#20]#['SH600770'#4.6#20]#['SH600880'#4.98#20]#['SH600883'#7.14#20]#['SH603029'#17.83#20]#['SH603066'#12.38#20]#['SH603311'#10.58#20]#['SH603729'#16.54#20]#['SH603860'#31.87#20]#['SH603917'#14.07#20]#['SZ001255'#28.98#20]#['SZ001259'#23.4#20]#['SZ001336'#20.11#20]#['SZ002161'#6.41#20]#['SZ002248'#9.38#20]#['SZ002343'#7.41#20]#['SZ002492'#5.23#20]#['SZ002495'#2.44#20]#['SZ002830'#13.64#20]#['SZ002963'#12.07#20]#['SZ300004'#6.95#20]#['SZ300289'#5.09#20]#['SZ300414'#8.55#20]#['SZ300417'#12.64#20]#['SZ300448'#7.77#20]#['SZ300517'#9.75#20]#['SZ300519'#13.84#20]#['SZ300626'#10.93#20]#['SZ300736'#9.85#20]#['SZ300771'#11.79#20]#['SZ300845'#14.23#20]#['SZ300886'#21.39#20]#['SZ300899'#23.3#20]#['SZ300923'#22.37#20]#['SZ300931'#7.32#20]#['SZ300995'#18.92#20]#['SZ301002'#18.19#20]#['SZ301006'#14.7#20]#['SZ301010'#17.76#20]#['SZ301042'#39.38#20]#['SZ301057'#14.1#20]#['SZ301113'#25.68#20]#['SZ301167'#13.91#20]#['SZ301198'#11.42#20]#['SZ301258'#25.38#20]#['SZ301270'#40.03#20]#['SZ301290'#24.61#20]#['SZ301359'#26#20]]"
    #连接socketio
    apush = socketio.Client()
    @apush.event
    def connect():
        print('connection established')
    #监听服务端推送消息
    @apush.event
    def user_message(data):
        print('user_message received with ', data)
        #sio.emit('my response', {'response': 'my response'})
    @apush.event
    def disconnect():
        print('disconnected from server')
    #连接服务端 IP+端口
    apush.connect('http://10.10.98.51:3211')
    '''
    try:
        apush.wait()
    except (KeyboardInterrupt,SystemExit):
        apush.disconnect()
    '''
    #从服务器接收终止信息，终止程序
    @apush.on('exit')
    def handle_exit():
        endflag['endflag'] = 1
    apush.emit('fromWebClient', {'mess':znote})
    while True:
        time.sleep(5)
        #发送数据这块目前只发送资金数据就可以，其余数据在交易函数中实现
        #经纪公司编号0,投资者编号1,资金帐号2,上次结算准备金3,上日可用资金4,入金金额5,出金金额6,占用保证金7,期权权利金收支8,手续费9,冻结的保证金10,冻结权利金11,冻结手续费12,平仓盈亏13,持仓盈亏14,可用资金15,结算准备金16,多头占用保证金17,空头占用保证金18,多头冻结的保证金19,空头冻结的保证金20,动态权益21,风险度22,其他费用23,质押金额24,币种25
        #[总资金,可用资金,占用保证金]
        with open(outdir+'/AccountInfo.txt', 'r', encoding='utf-8') as ZJCX:
            # 读取所有行到列表中
            lines = ZJCX.readlines()
            ageneral =[]
            for line in lines:
                llist = line.split(',')
                #ageneral.append()
                ageneral.append(float(llist[21]))
                ageneral.append(float(llist[15]))
                ageneral.append(float(llist[7]))
                #print(json.dumps(ageneral))
                # 向服务端发送消息
                nnote1 = mqsaccount+"-账户总览-"+GetNow(TimeItem='YMDHMS')+':'+json.dumps(ageneral).replace(' ','')
                #print(nnote1)
                apush.emit('fromWebClient', {'mess':nnote1})
        #print("maSender:")
        #apush.emit('fromWebClient', {'mess':nnote1})
        #循环体代码
        if endflag['endflag']==1:
            apush.disconnect()
            break  


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
        #_mqTrader = threading.Thread(target=mqTrader, args=(data,))
        #threads.append(_mqTrader)
        #_mqTrader.start()
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
    

# 定义一个从线程函数:交易函数
#qmt or 掘金 or 无限易在这里实现
def mqTrader(tar):
    print('mqTarder start:')
    #print(tar)
    #APositionList = '中证1000指数增强01-调仓目标-2025011394708:[[SH605128#SZ002209#SH600697]#[Cash#80]#[SZ300150#5.35#4]#[SH603238#17.35#4]#[SH603839#6.47#4]#[SH603813#14.55#4]#[SH600444#15.93#4]]'.split(':')[1].replace('#',',');
    #APositionList = data.split(':')[1].replace('#',',');
    #print(eval(APositionList))   
    ########################
    #fholdlist1=[[最低资金,杠杆率],[代码0,价格0,持仓方向0],[代码1,价格1,持仓方向1],...]
    #Order以等权权重形式给出，字段是代码，价格和持仓方向，交易端接收命令后，根据自身的资金情况结合风险度计算可用金额，再根据可用金额构建持仓组合
    #第一个元素是当交易执行后，偏差金额买入候选股票
    #Fmsg0 = "[[1000000#8]#['AU2510'#839.64#'KD']#['AU2512'#842.18#'DD']#['IC2510'#7111.6#'KD']#['IC2512'#6997.2#'KD']#['IF2510'#4515.6#'KD']#['IH2512'#2959#'KD']#['IM2510'#7383.6#'DD']]"
    #Fmsg1 = "[[2000000#8]#['A2511'#3937#'KD']#['A2601'#3940#'KD']#['A2603'#3945#'KD']#['AG2510'#10092#'DD']#['AG2512'#10120#'DD']#['AG2601'#10131#'DD']#['AG2602'#10140#'DD']#['AG2604'#10166#'DD']#['AG2606'#10192#'DD']#['AG2608'#10222#'DD']#['AL2510'#20955#'KD']#['AL2511'#20965#'KD']#['AL2512'#20950#'KD']#['AL2601'#20920#'KD']#['AO2510'#2953#'KD']#['AO2511'#2957#'KD']#['AO2601'#2982#'KD']#['AO2602'#2986#'DD']#['AP2601'#8283#'DD']#['AU2510'#839.64#'KD']#['AU2512'#842.18#'DD']#['AU2602'#844.58#'DD']#['AU2604'#846.56#'DD']#['B2511'#3754#'KD']#['B2512'#3785#'KD']#['B2601'#3777#'KD']#['IC2509'#7170.4#'DD']#['IC2510'#7111.6#'KD']#['IC2512'#6997.2#'KD']#['IC2603'#6838#'KD']#['IF2509'#4526.8#'KD']#['IF2510'#4515.6#'KD']#['IF2512'#4494.8#'KD']#['IF2603'#4469#'KD']#['IH2509'#2959#'KD']#['IH2512'#2959#'KD']#['IM2509'#7458#'KD']#['IM2510'#7383.6#'DD']#['IM2512'#7231.4#'DD']#['IM2603'#7025.6#'KD']]"
    Fmsg0 = tar
    fholdlist1 = eval(Fmsg0.replace('#',','))
    #print(type(fholdlist1))
    CashTargetList = fholdlist1[0]
    资产下限 = CashTargetList[0]
    杠杆比 = CashTargetList[1]
    HoldTargetList = fholdlist1[1:]
    #print(CashTargetList)
    #print(HoldTargetList)

    ########################
    BaseDict = {}

    #查询账户信息
    wzjcxdict = get_AccountInfo()[mqsaccount]
    #print(wzjcxdict)
    总资产 = float(wzjcxdict['动态权益'])
    #print(总资产)
    #print(资产下限)
    #print(杠杆比)
    if 总资产<资产下限:
        sys.exit(1)
    目标市值 = 总资产*杠杆比
    #print(目标市值)
    #print(HoldTargetList)

    #目标持仓
    tholddict ={}
    bdict ={}
    ix0 = 0
    while ix0<len(HoldTargetList):
        fv = HoldTargetList[ix0][0]
        fprice = HoldTargetList[ix0][1]
        dk = HoldTargetList[ix0][2]
        item = fv[:-4]
        market = fmsgdict[item][0]
        chsh = fmsgdict[item][1]
        
        if 交易所大小写[market]=='a' :
            fv_ = fv.lower()
        elif  交易所大小写[market]=='A' :
            fv_ = fv
        if market == 'CZCE':
            fv_ = fv_[:-4]+fv_[-3:]
        else:
            fv_=fv_
        fcode = market+'.'+fv_
        fvalue = fprice*chsh
        tholddict[fv] = [fvalue,dk,fcode,market]
        bdict[fv] = fvalue
        #print(HoldTargetList[ix0])
        ix0+=1
    #print('目标持仓')
    #print(tholddict)
    #print(bdict)
    fchdict = fenchai(目标市值,bdict)
    #print(fchdict)
    TargetHoldDict ={}
    for (k,v) in fchdict.items():
        fnums = v/tholddict[k][0]
        dk = tholddict[k][1]
        if dk=='DD':
            fnums=fnums
        elif dk =='KD':
            fnums=-fnums
        TargetHoldDict[k] = fnums

    #print(TargetHoldDict)

    '''
    #查询账户持仓信息
    holddict = {}
    wcctjlist = get_PositionInfo()
    #print(wcctjlist)
    ix1 = 0
    while ix1<len(wcctjlist):
        #print(wcctjlist[ix1])
        tdict = wcctjlist[ix1]
        fcode=tdict['合约代码']
        if tdict['交易所代码']=='CZCE':
            fv = fcode[:-3]+'2'+fcode[-3:]
        else:
            fv = fcode
        fv =fv.upper()
        if  holddict.get(fv) == None:
            holddict[fv] = {'总多单':0,'今多单':0,'今平多':0,'总空单':0,'今空单':0,'今平空':0,'净单量':0}
        else:
            pass
        #print(fv)
        if tdict['买卖']=='0':
            holddict[fv]['总多单'] = int(tdict['总持仓量'])
            holddict[fv]['今多单'] = int(tdict['今开仓量'])
            holddict[fv]['今平多'] = int(tdict['今平仓量'])
        else:
            holddict[fv]['总空单'] = int(tdict['总持仓量'])
            holddict[fv]['今空单'] = int(tdict['今开仓量'])
            holddict[fv]['今平空'] = int(tdict['今平仓量'])
        holddict[fv]['净单量']=holddict[fv]['总多单']-holddict[fv]['总空单']
        ix1+=1
    #print('目前持仓')
    print(holddict)

    '''

    SidList = []
    trflag= 0
    i = 0
    while trflag == 0:
        #取消掉全部尚未成交的委托单
        #全部撤单
        all_cancel_order()
        #等1秒钟
        time.sleep(1)
        
        #获取当前时间，到时间停止
        ltime= time.localtime()
        #收盘前1分钟停止交易
        #if ltime.tm_hour>=14 and ltime.tm_min>59 :
            #senddif()
            #trflag = 1
            #continue
        if i>5:
            trflag = 1
            #senddif()
            continue
        #复制目标持仓
        DDict1 = copy.copy(TargetHoldDict)
        #print(DDict1)
        #查询账户持仓信息
        holddict = {}
        wcctjlist = get_PositionInfo()
        #print(wcctjlist)
        ix1 = 0
        while ix1<len(wcctjlist):
            #print(wcctjlist[ix1])
            tdict = wcctjlist[ix1]
            fcode=tdict['合约代码']
            if tdict['交易所代码']=='CZCE':
                fv = fcode[:-3]+'2'+fcode[-3:]
            else:
                fv = fcode
            fv =fv.upper()
            if  holddict.get(fv) == None:
                holddict[fv] = {'总多单':0,'今多单':0,'今平多':0,'总空单':0,'今空单':0,'今平空':0,'净单量':0}
            else:
                pass
            #print(fv)
            if tdict['买卖']=='0':
                holddict[fv]['总多单'] = int(tdict['总持仓量'])
                holddict[fv]['今多单'] = int(tdict['今开仓量'])
                holddict[fv]['今平多'] = int(tdict['今平仓量'])
            else:
                holddict[fv]['总空单'] = int(tdict['总持仓量'])
                holddict[fv]['今空单'] = int(tdict['今开仓量'])
                holddict[fv]['今平空'] = int(tdict['今平仓量'])
            holddict[fv]['净单量']=holddict[fv]['总多单']-holddict[fv]['总空单']
            ix1+=1
        #print('目前持仓')
        #print(holddict)
            
        DDict0 = copy.copy(holddict)
        FList = []
        FListOrderList = []
        for (k,v) in DDict1.items():
            if k in DDict0.keys():
                #print(v)
                Diff = v[1]-DDict0.pop(k)['净单量']
                FList.append([k,Diff])
            else:
                #FList.append([k,v])
                if v<0:
                    item = 'SK'
                    v=-v
                else:
                    item = 'BK'
                    v = v
                FListOrderList.append([k,item,v])
        for (k,v) in DDict0.items():
            FList.append([k,-v['净单量']])
        #print('调仓目标：')
        #print(FList)
        #判断是否还有必要调仓，如果没必要则停止
        #print(FListOrderList)
        for ntxt in FList:
            fcode = ntxt[0]
            fnums = ntxt[1]
            #print(fnums)
            if fnums>0:
                if holddict[fcode]['今空单']>0:
                    item = 'BK'
                    v = holddict[fcode]['总空单']
                    FListOrderList.append([fcode,item,v])
                else:
                    item = 'BP'
                    v = holddict[fcode]['总空单']
                    FListOrderList.append([fcode,item,v])
                    dif = fnums -v
                    if dif>0:
                        item = 'BK'
                        FListOrderList.append([fcode,item,dif])  
            elif fnums<0:
                if holddict[fcode]['今多单']>0:
                    item = 'SK'
                    v = holddict[fcode]['总多单']
                    FListOrderList.append([fcode,item,v])
                else:
                    item = 'SP'
                    v = holddict[fcode]['总多单']
                    FListOrderList.append([fcode,item,v])
                    dif = -fnums -v
                    if dif>0:
                        item = 'SK'
                        FListOrderList.append([fcode,item,dif])  
                
        #print(FListOrderList)
        if 1<0:
            break
        else:
            fid = 0
            while fid <len(FListOrderList):
                #print(FList[fid])
                #order_typ = '23' if FList[fid][1]=='B' else '24'
                
                fv = FListOrderList[fid][0]
                item = fv[:-4]
                market = fmsgdict[item][0]
                if 交易所大小写[market]=='a' :
                    fv_ = fv.lower()
                elif  交易所大小写[market]=='A' :
                    fv_ = fv
                if market == 'CZCE':
                    fv_ = fv_[:-4]+fv_[-3:]
                else:
                    fv_=fv_
                交易所代码 = market
                合约代码 = fv_
                数量 = int(FListOrderList[fid][2])
                买卖 = 'B' if FListOrderList[fid][1] in ['BK','BP'] else 'S'
                开平 = 0 if FListOrderList[fid][1] in ['BK','SK'] else 1
                类型 = 0
                时态 = ''
                价格类型 = 2
                价格 = 0
                经纪公司编号 = 1
                投资者账号 = mqsaccount
                委托类型 = 1
                报单编号 = ''
                备注 = ''
                
                #交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注 = 'CFFEX','IH2510',1,'B',0,0,'',2,0,1,'13817993656',1,'',''
                orderlist = [交易所代码,合约代码,数量,买卖,开平,类型,时态,价格类型,价格,经纪公司编号,投资者账号,委托类型,报单编号,备注]
                print(orderlist)
                place_order(orderlist)
                fid+=1
        time.sleep(60)
        i+=1

    #orderlist = ['SHFE', 'au2512', 3, 'B', 0, 0, '', 2, 0, 1, '13817993656', 1, '', '']
    #place_order(orderlist)








# 定义主函数
def main():
    Login(mqusername,mqpassword)
    itAuth=mqquantID
    fAuthority=Auth(mqusername,itAuth)
    if fAuthority == 1:
        #这块儿还需要完成前期环境检查，如果都满足才可以继续
        #创建目录
        create_directory_if_not_exists(outdir)
        print("_无限易期货版 Main thread starting")
        znote = mqusername+"-"+mqquantname+"-账户注册-"+GetNow(TimeItem="YMDHMS")+":"+mqquantID+'#'+mqsaccount+'#'+mqusername+'#'+mqquantname+'#'+mqsassets
        _mqSender = threading.Thread(target=mqSender, args=(znote,))
        threads.append(_mqSender)
        _mqSender.start()
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
    main()

