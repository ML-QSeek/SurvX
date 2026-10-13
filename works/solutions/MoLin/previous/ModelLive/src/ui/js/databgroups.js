;
//function bof(){zuhe001();zuhe002();zuhe003();zuhe004();zuhe005();zuhe006();zuhe007();zuhe008();zuhe009();zuhe010();}
function	zuhe002(){
	databgroup4();
	kline1('涨停家数','z9.json',"container1");
	kline1('涨幅7','z7.json',"container2");
	kline1('涨幅5','z5.json',"container3");
	kline1('涨幅3','z3.json',"container4");
	}

function	zuhe003(){
	databgroup4();
	kline1('下跌家数','d9.json',"container1");
	kline1('跌幅7','d7.json',"container2");
	kline1('跌幅5','d5.json',"container3");
	kline1('跌幅3','d3.json',"container4");
	}
function	zuhe004(){	databgroup2();kline1('创历史新高','lh.json',"container1");kline1('创历史新低','ld.json',"container2");}
function	zuhe008(){	databgroup1();out1("line1","M0075992","container1","融资融券余额与两个指数","融资融券余额","SH000001","上证指数","SZ399006","创业板指");}
function	zuhe009(){	databgroup4();out1("line1","M0218109","container1","沪股通与上证指数","沪股通当日买入金额","M0218110","沪股通当日卖出金额","SH000001","上证指数");
														out1("line1","M0218109","container2","沪股通买入金额和笔数","沪股通当日买入金额","M0218111","沪股通当日买入笔数","SH000001","上证指数");
														out1("line1","M0218110","container3","沪股通卖出金额和笔数","沪股通当日卖出金额","M0218112","沪股通当日卖出笔数","SH000001","上证指数");}
function	zuhe010(){	databgroup4();out1("line1","M5207855","container1","公募基金","公募基金数量","M5207861","公募基金份额");
														out1("line1","M5550224","container2","信托产品","信托产品数量","M5550252","信托产品规模");
														out1("line1","M5543219","container3","阳光私募","阳光私募发行家数","M5550184","中证众筹平台本年累计募集成功");
														out1("line1","M5543219","container4","集合理财","阳光私募发行家数","M0067887","集合理财发行份额");}
function	zuhe011(){	databgroup4();out1("line1","M0001380","container1","M0/M1/M2期末值","M0","M0001382","M1","M0001384","M2");
														out1("line1","M0001381","container2","M0/M1/M2同比增长","M0","M0001383","M1","M0001385","M2");
														out1("line1","M0061614","container3","公开市场操作","货币净投放量","M0061615","货币投放量","M0061616","货币回笼量");
														out1("line1","M0009940","container4","金融机构存款和贷款","存款余额","M0009969","贷款余额");}
function	zuhe012(){	databgroup4();out1("line1","M0017138","container1","SHIBOR","Shibor隔夜","M0017141","Shibor1M","M0017143","Shibor6M");
														out1("line1","M1001812","container2","新质押式国债回购利率","1D","M1001818","1M","M1001820","6M");
														out1("line1","M1000028","container3","银行间国债到期收益率","6M","M1000029","1Y","M1000033","5Y");}
function	zuhe013(){	databgroup4();out1("line1","M0290205","container1","美元和人民币","人民币在岸价","FXUSDX","美元指数","M0000185","美元兑人民币(中间价)");
														out1("line1","G0002347","container2","英镑/欧元/澳元->美元","英镑兑美元","G0002331","欧元兑美元","G0002326","澳元兑美元");
														out1("line1","G0002334","container3","美元->日元/加元","美元兑日元","G0002328","美元兑加元");}
function	zuhe014(){	databgroup4();out1("line1","M0089119","container1","财政当月收支","财政收入当月值","M0089123","财政支出当月值");
														out1("line1","M0089127","container2","财政累计收支","财政收入累计值","M0089131","财政支出累计值");
														out1("line1","M0089121","container3","财政收支当月同比","财政收入当月同比","M0089125","财政支出当月同比");
														out1("line1","M0089129","container4","财政收支累计同比","财政收入累计同比","M0089133","财政支出累计同比");}
function	zuhe015(){	databgroup4();out1("line1","M5558005","container1","新增投资者","新增投资者数量","M5558006","新增自然人","M5558007","新增非自然人");
														out1("line1","M5558008","container2","投资者状态","期末投资者数量","M5558015","期末持仓投资者数量","M5558018","期间参与交易投资者");
														out1("line1","M5558009","container3","期末投资者成分","期末自然人","M5558012","期末非自然人");
														out1("line1","M0010351","container4","A股印花税","印花税沪市A股(亿元)","M0010371","印花税深市A股(亿元)");}
function	zuhe016(){	databgroup2();out1("line1","M0010049","container1","官方外汇储备","官方外汇储备");
														out1("line1","M0043420","container2","外汇占款余额","外汇占款余额");}
function	zuhe017(){	databgroup4();out1("line1","G0000891","container1","美债10年收益率","美债10年收益率");
														out1("line1","G0000027","container2","CPI/PMI","美CPI当月同比","G0000029","美核心CPI当月同比","G0002323","美ISM_PMI");
														out1("line1","G0000087","container3","就业","美失业率季调","G0002446","美非农就业人数季调","FXUSDX","美元指数");
														out1("line1","G0003366","container4","美工业生产指数季调","美工业生产指数季调");}
function	zuhe018(){	databgroup4();out1("line1","G0000891","container1","美债10年收益率","美债10年收益率");
														out1("line1","G0000027","container2","CPI/PMI","美CPI当月同比","G0000029","美核心CPI当月同比","G0002323","美ISM_PMI");
														out1("line1","G0000087","container3","就业","美失业率季调","G0002446","美非农就业人数季调","FXUSDX","美元指数");
														out1("line1","G0003366","container4","美工业生产指数季调","美工业生产指数季调");}
function	zuhe019(){	databgroup4();out1("line1","M5206730","container1","社会融资规模","社会融资规模增量当月值(亿元)","M5201630","社会融资规模增量累计值(亿元)","SH000001","上证指数");
														out1("line1","M0000331","container2","固定资产投资","全国固定资产新开工项目计划总投资累计同比","M0000330","全国固定资产新开工项目计划总投资累计值(亿元)","M0000272","城镇固定资产投资完成额累计值(亿元)");
														out1("line1","S0029659","container3","房地产","房地产销售额商品房累计值(亿元)","S0049591","房地产销售额商品房累计同比","M0000448","城镇固定资产投资完成额房地产累计值(亿元)");}
function	zuhe020(){	databgroup4();out1("line1","M0000612","container1","CPI","CPI当月同比","M0000705","CPI环比");
														out1("line1","M0000616","container2","CPI食品","CPI食品当月同比","M0000706","CPI食品环比");
														out1("line1","M0017126","container3","PMI","制造业PMI","M0290204","财新PMI");
														out1("line1","M0001427","container4","社会消费品零售总额","当月值(亿元)","M0001428","当月同比");}
function	zuhe021(){	databgroup4();out1("line1","M0009870","container1","实际使用外资","当月值(亿美元)","M0009871","当月同比","M5405461","累计同比");
														out1("line1","M0000606","container2","出口总值","当月值(亿元)","M0000607","当月同比");
														out1("line1","M0000608","container3","进口总值","当月值(亿元)","M0000609","当月同比");}
function	zuhe022(){	databgroup4();out1("line1","M0001227","container1","PPI","当月同比","M0049160","环比","SH000001","上证指数");
														out1("line1","M0000545","container2","工业增加值","当月同比","M0061571","季调环比","SH000001","上证指数");
														out1("line1","M0000556","container3","规模以上工业企业利润总额","累计值(亿元)","M0000557","累计值(亿元)1","SH000001","上证指数");
														out1("line1","S0027012","container4","发电量","当期值(亿千瓦小时)","S0027013","同比增长","SH000001","上证指数");}
function	zuhe023(){	databgroup4();out1("line1","SH000001","container1","中国指数","上证指数","SZ399006","创业板指","SH000300","沪深300");
														out1("line1","GIDJI","container2","美国指数","道琼斯工业","GISPX","标准普尔","GIIXIC","纳斯达克");
														out1("line1","GIFTSE","container3","欧洲","英国富时100","GIGDAXI","德国DAX30","GIFCHI","法国CAC40");
														out1("line1","GIN225","container4","日俄韩","日经225","GIRTS","俄罗斯RTS","GIKS11","韩国综合指数");}
function	zuhe024(){	databgroup4();out1("line1","FXUSDX","container1","美元/纽金/纽银","美元指数","CMXGC00","CMX黄金","CMXSI00","CMX白银");
														out1("line1","FXUSDX","container2","美元/美原油/布伦特原油","美元指数","IPET00","美原油","IPEB00","布伦特原油");
														out1("line1","LMECA00","container3","LME铜/铝/锌","LME铜","LMEAH00","LME铝","LMEZS00","LME锌");
														out1("line1","LMENI00","container4","LME镍/锡/铅","LME镍","LMESN00","LME锡","LMEPB00","LME铅");}
														
function	zuhe025(){	databgroup4();out1("line1","S5914501","container1","草甘膦（95%原药）全国市场价","草甘膦（95%原药）全国市场价");
														out1("line1","S5068270","container2","草甘膦异丙胺盐（41%水剂）瓶装均价","草甘膦异丙胺盐（41%水剂）瓶装均价");
														out1("line1","S5068290","container3","草甘膦异丙胺盐（41%水剂）瓶装均价同比","草甘膦异丙胺盐（41%水剂）瓶装均价同比");
														out1("line1","S5470359","container4","草甘膦（95%）国内现货价","草甘膦（95%）国内现货价");}														

function zuhe056(){	databgroup4();out1("line1","S0027702","container1","水泥产量当月值和同比","当月值","S0027703","同比");
														out1("line1","S0027704","container2","水泥产量累计值和同比","累计值","S0027705","同比");
														out1("line1","S0027834","container3","水泥专用设备产量当月值和同比","当月值","S0027835","同比");
														out1("line1","S0027836","container4","水泥专用设备产量累计值和同比","累计值","S0027837","同比");
														}

function zuhe140(){databgroup4();out1("line1","S5441243","container1","MDI（纯）（桶装）外盘现货","低端价","S5441245","中间价","S5441244","高端价");
														out1("line1","S5443289","container2","MDI（纯）市场价（主流价）","华北地区","S5443290","华东地区","S5443294","华南地区");
	}
function zuhe141(){databgroup4();out1("line1","S5441174","container1","TDI（甲苯二异氰酸酯T80）外盘现货","低端价","S5441176","中端价","S5441175","高端价");
														out1("line1","S5443296","container2","TDI市场价（主流价）","华北地区","S5443297","华东地区","S5443298","华南地区");
	}
function zuhe142(){databgroup4();out1("line1","S5441459","container1","聚醚软泡指导价（中海壳牌）","指导价");
														out1("line1","S5443305","container2","聚醚软泡市场价（主流价）","东北地区","S5443306","华北地区","S5443307","华东地区");
														out1("line1","S5443308","container3","聚醚软泡市场价（主流价）","华南地区","S5443309","山东地区");
														out1("line1","S5420084","container4","聚醚软泡（出厂价）","福建湄洲","S5420085","上海高桥");
	}
function zuhe143(){databgroup4();out1("line1","S5456762","container1","聚醚硬泡市场价（主流价）","华北地区","S5456763","华东地区","S5456764","山东地区");
														out1("line1","S5456516","container2","聚醚硬泡出厂价（桶装，4110）","河北全振","S5456518","常熟一统","S5456523","万华荣威");
														out1("line1","S5456524","container3","聚醚硬泡出厂价（桶装，4110）","山东滨化","S5456526","淄博诺力");
														out1("line1","S5456525","container4","聚醚硬泡出厂价（4110）","山东一诺威");
	}
function zuhe144(){	databgroup4();out1("line1","S5458327","container1","乙二酸（一级）市场价","市场价");
	}
function zuhe145(){	databgroup4();out1("line1","S5914504","container1","瓦楞纸高强市场价","瓦楞纸高强市场价");
														out1("line1","S0070149","container2","瓦楞纸箱产量当月值和同比","当月值","S0070359","同比");
														out1("line1","S0070569","container3","瓦楞纸箱产量累计值和同比","累计值","S0070779","同比");
	}
function zuhe146(){
	databgroup1();out1("line1","S0146481","container1","瓦楞箱板纸（山鹰纸业）","产销比","S0146479","产量","S0146480","销量");
	}
function zuhe147(){	databgroup4();out1("line1","S5501075","container1","白板纸进口和出口数量","白板纸进口数量","S5501087","白板纸出口数量");
														out1("line1","S5501076","container2","白板纸涂布进口和出口数量","白板纸涂布进口数量","S5501088","白板纸涂布出口数量");
	}
function	zhhy00x(){	databgroup1();out1("line1","S0031550","container1","波罗的海指数","BDI","SH000001","上证指数","SZ399006","创业板指");}
function	zhfl1h1(){	databgroup4();}
function	zhfl2h1(){	databgroup4();}
function	zhwf1h1(){	databgroup4();}
function	zhfl5h1(){	databgroup4();}
function	zhfl6h1(){	databgroup4();}
function	zhfl8h1(){	databgroup4();}
function	zhfl9h1(){databgroup4();}
function	zhzt01(){databgroup4();}
function	zuhe1000(){
	databgroup4();
	gx1("container1");
	ld1("container2");
	gx2("container3");
	}