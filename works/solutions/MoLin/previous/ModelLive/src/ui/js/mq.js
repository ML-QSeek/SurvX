;
//名称:mq.js --编写：曲如意 --编写日期：2024-12-15
//提交：01；修改：03；删除：02；查询：04；执行：05；

//用户名
// 获取当前页面的URL参数
const params = new URLSearchParams(window.location.search);
// 获取指定参数的值
Q14123101 = params.get('par');
//alert(Q14123101);
//server
var MServer = "http://10.10.98.51/test/sys/";
//用户具备的权限
var	UserAuthority=[];
//用户操作的痕迹记录
var	UserNote={};
//当前页面的主题
var NowTopic = 'mq_top_ul_li_12';//mq_top_ul_li_04;
//策略服务器
var mpushserver0 = '10.10.98.51:3210';
//交易服务器
var mpushserver1 = '10.10.98.51:3211';
//var mpushserver1 = 'quruyi0909.oicp.net:10034';
//系统监控服务器
var mpushserver3 = '10.10.98.51:3213';

//策略服务器连接
var smsocket0 = io.connect(mpushserver0);
//交易服务器连接
var smsocket1 = io.connect(mpushserver1);
//行情服务器连接
var smsocket3 = io.connect(mpushserver3);
//获取策略服务器消息集合
var quantmess= new Set();
//获取交易服务器消息集合
var clientmess= new Set();
var x1=[];
var x2=[];
var x3=[];

//策略监控页面数据推送是否动态展现相关面板,默认为不展示
var isPushDash=0;

//警示消息列表
var	WarnMessageList=[
	"你尚未开通这个模块的权限！",
	"请输入查询对象！",
	"请在上方报表中选择申请变量！",
	"还没有构建模型！",
	"登陆成功！",
	"注销成功！",
	"用户名已存在！",
	"提交失败，请重新提交！",
	"购买成功！", 
	"你的金币不足！",
	"!",
	"你还没有选择项目！",
	"此项没有内容！",
	"停止滚动，再次点击恢复滚动！",
	"恢复滚动！",
	"目前已经是最新消息！",
	"只能查看最近5条消息！",
	"请输入查询对象！",
	"该功能尚未开通！",
	"你已有权限！",
	"开始日期和结束日期不能为空!",
	"目前还没有账户！",
	"只有所有者才能查看相关信息！"
];

//主界面页面布局
var mainDiv ='<div	id="mq_main_r"></div>';
		mainDiv+='<div id="mq_main_m"></div>';
		mainDiv+='<div id="mq_main_l"></div>';
//主界面页面布局
var mainDiv1 ='<div	id="mq_main_r1"></div>';
		mainDiv1+='<div id="mq_main_l1"></div>';
//产品查询页面
var mainDiv2 ='<div	id="mq_mainT"></div><div id="pidflag" style="display:none;"></div><div id="pitflag" style="display:none;"></div><div id="pchflag" style="display:none;"></div>';
		mainDiv2+='<div style="left:100px;" id = "cpmonthlyreport" class="BList">生成月报</div>';
		mainDiv2+='<div style="left:200px;" id = "cpweeklyreport" class="BList">生成周报</div>';
		mainDiv2+='<div style="left:300px;" id = "cpdailyreport" class="BList">生成日报</div><div style="left:400px;" id = "ProductAppend" class="BList">添加数据</div>';
		mainDiv2+='<div class="BList" id="ProductNav" style="right:200px;">累计净值</div>';
		mainDiv2+='<div class="BList" id="chicjirgou" style="right:300px;">持仓结构</div>';
		mainDiv2+='<div class="BList" id="hchshuiping" style="right:400px;">回撤水平</div>';
		mainDiv2+='<div class="BList" id="huanshoulv" style="right:500px;">换手水平</div>';
		mainDiv2+='<div class="BList" id="ribodong" style="right:600px;">每日波动</div>';
		mainDiv2+='<div class="BList" id="chanpingm" style="right:700px;">产品规模</div>';
		mainDiv2+='<div class="BList" id="hangyefb" style="right:800px;">行业分布</div>';
		mainDiv2+='<div class="BList" id="hangyegx" style="right:900px;">行业贡献</div>';
		mainDiv2+='<div id="productGo" style="display:none;"><img class="TolTor" src="./assets/images/right.png"/></div>';
		mainDiv2+='<div	id="mq_mainB"></div>';
//策略配置页面布局
var QuantConfigRealDash ='<div id="xfbutton"><div id="xfbuttonl"></div><div id="xfbuttonr"></div></div>';
		QuantConfigRealDash+='<div id ="mq_main_ljBL">';
		QuantConfigRealDash+='<div class="Rcharts_kuang" id="Rcontainer1"></div>';
		QuantConfigRealDash+='<div class="Rcharts_kuang" id="Rcontainer2"></div>';
		QuantConfigRealDash+='</div>';
		QuantConfigRealDash+='<div id ="mq_main_ljBR"><div id="UPDOWN"></div><div id="ToStop"></div><div id="ToLeft"></div><div id="ToRight"></div><div id ="mq_main_ljBRD"></div><div id ="mq_main_ljBRB">';
		QuantConfigRealDash+='<div class="Mod_kuang"><div id="xLcontainer1" class="Mcontainer"></div><div class="McontainerTopic" style="background:#FF7F39;">市场概况</div></div>';
		QuantConfigRealDash+='<div class="Mod_kuang"><div id="xLcontainer9" class="Mcontainer">账户跟踪</div><div class="McontainerTopic" style="background:#FFCC00;">账户跟踪</div></div>';
		QuantConfigRealDash+='<div class="Mod_kuang"><div id="xLcontainer2" class="Mcontainer">策略时效和跟踪误差</div><div class="McontainerTopic" style="background:#FF2AAA;">策略跟踪</div></div>';
		QuantConfigRealDash+='<div class="Mod_kuang"><div id="xLcontainer10" class="Mcontainer">风险控制</div><div class="McontainerTopic" style="background:#2A8CFF;">风险控制</div></div>';
		QuantConfigRealDash+='<div class="Mod_kuang"><div id="xLcontainer4" class="Mcontainer">投研相关</div><div class="McontainerTopic" style="background:#B026FF;">投研相关</div></div>';
		QuantConfigRealDash+='<div class="Mod_kuang"><div id="xLcontainer8" class="Mcontainer">组织结构</div><div class="McontainerTopic" style="background:#FFAA00;">组织结构</div></div>';
		QuantConfigRealDash+='</div></div>';



		
var xuanz1  ='<option value="0">折线</option>';
//		xuanz1 +='<option value="1">柱形</option>';
//		xuanz1 +='<option value="2">散点</option>';
var tuxing  ='<option value="折线图1">折线图1</option>';
//		tuxing +='<option value="柱形图1">柱形图1</option>';
//		tuxing +='<option value="饼形图1">饼形图1</option>';  
function trans(name1){
	if(name1){
		     if(name1=="折线图1"){return "line1"}
//		else if(name1=="饼形图1"){return "pie1"}
//		else if(name1=="仪表盘1"){return "ybp1"}
//		else if(name1=="热力图1"){return "reli1"}
	}
	}

var	datax3 ='<div class="jkbtj">应用工具</div>';
		datax3+='<div class="jkzbj" name="ch030">QSeek</div>';
		datax3+='<div class="jkzbj" name="ch031">QForge</div>';
		datax3+='<div class="jkzbj" name="ch032">QSkill</div>';
		datax3+='<div class="jkzbj" name="ch005">项目记录</div>';
		datax3+='<div class="jkzbj" name="ch006">技术文档</div>';
		datax3+='<div class="jkzbj" name="ch008">问题跟踪</div>';
		datax3+='<div class="jkzbj" name="ch011">因子库</div>';
		datax3+='<div class="jkzbj" name="ch012">数据列表</div>';
		datax3+='<div class="jkzbj" name="ch009">事件解析</div>';
		datax3+='<div class="jkzbj" name="ch003">参数寻优</div>';
		datax3+='<div class="jkzbj" name="ch001">市值效应</div>';
		datax3+='<div class="jkzbj" name="ch007">MDCF估值</div>';
		datax3+='<div class="jkzbj" name="ch002">半年报</div>';
		datax3+='<div class="jkzbj" name="ch015">组织架构</div>';
		datax3+='<div class="jkzbj" name="ch019">投研相关</div>';
		datax3+='<div class="jkzbj" name="ch021">跟踪误差</div>';
		datax3+='<div class="jkzbj" name="ch024">风险控制</div>';
		datax3+='<div class="jkzbj" name="ch022">市场概况</div>';
		datax3+='<div class="jkzbj" name="ch023">账户信息</div>';

function myFunction1(){
	var txt  ='<div id="container1" style="height:100%;width:100%;"></div>';
	$("#mq_main_l").html(txt);
	}
function myFunction2(){
	var txt  ='<div id="container1" style="height:100%;width:50%;float:left;"></div>';
	txt +='<div id="container2" style="height:100%;width:50%;float:left;"></div>';
	$("#mq_main_l").html(txt);
	}
function myFunction3(){
	var txt  ='<div id="container1" style="height:50%;width:50%;float:left;"></div>';
	txt +='<div id="container2" style="height:50%;width:50%;float:left;"></div>';
	txt +='<div id="container3" style="height:50%;width:50%;float:left;"></div>';
	txt +='<div id="container4" style="height:50%;width:50%;float:left;"></div>';
	$("#mq_main_l").html(txt);
	}
	
function databgroup1(){myFunction1();}
function databgroup2(){myFunction2();}
function databgroup4(){myFunction3();}

function out1(sig1,sig2,sig4,sig5,sig8,sig6,sig9,sig7,sig10){
	var arr1=[];var arr2=[];var arr3=[];var arr4=[];
	$.ajax({
		url: MServer+"qi/qi00002/qi04635C/mqC.php",
		type:"post",
		async:false,//同步执行
		data:{
			qflag:"databaction",
			action1:sig2,
			action2:sig6,
			action3:sig7,
			},
		error:function(){
			alert('11Error loading XML document');
			},
			//dataType:"json",//返回数据形式为json
		success:function(result){
			if(result){
				var result=eval(trim(result));
				for(var i=0;i<result.length;i++){
				//console.log(result[i].name);
				arr1.push(result[i].times);arr2.push(result[i].close1);arr3.push(result[i].close2);arr4.push(result[i].close3);
			}
		}
	}
	})
	eval(sig1+'("'+sig4+'",sig5,arr1,arr2,arr3,arr4,sig8,sig9,sig10)');
	}
	
//屏蔽右键事件
document.oncontextmenu=function(){return	false;}
//获取日期
function getLangDate(item){
	var dateObj = new Date();
	var year = dateObj.getFullYear();
	var month = dateObj.getMonth()+1;
	var date = dateObj.getDate();
	var day = dateObj.getDay();
	var weeks = ["星期日","星期一","星期二","星期三","星期四","星期五","星期六"];
	var week = weeks[day];
	var hour = dateObj.getHours();
	var minute = dateObj.getMinutes();
	var second = dateObj.getSeconds();
	if(month<10){month="0"+month;}
	if(date<10){date="0"+date;}
	if(hour<10){hour="0"+hour;}
	if(minute<10){minute="0"+minute;}
	if(second<10){second="0"+second;}
	//var newDate = year+"年"+month+"月"+date+"日 "+hour+":"+minute+":"+second+" "+week;
	if(item=='systime'){
	var newDate ="<font class='ttext'>"+year+"年"+month+"月"+date+"日 "+hour+":"+minute+":"+second+" "+week+"</font>";
	document.getElementById("home_main_rbottom1_colr").innerHTML = newDate;
	setTimeout("getLangDate('systime')",1000);//每隔1秒重新调用一次该函数
		}
	else{
	var newDate = year.toString()+month.toString()+date.toString();
	var newMonth = year.toString()+month.toString();
	var newDate1 = year+"-"+month+"-"+date;
	return eval(item);
	}
}
//去除空格
function trim(str){return str.replace(/(^\s*)|(\s*$)/g,"");}
// 生成一个不重复的ID
function GenNonDuplicateID(randomLength){
	return Number(Math.random().toString().substr(3,randomLength) + Date.now()).toString(36)
}
//关闭按钮
$(document).on("click",".shut",function(){
	$(this).parent().remove();
	})
//关闭按钮
$(document).on("click",".shut1",function(){
	$(this).parent().parent().remove();
	})
//警示消息
function WarnMessage(content){
	var sid=GenNonDuplicateID(1);	
	$("body").append('<div class="Warn"><div class="WarnB" id="WarnB_'+sid+'"></div><div class="WarnM"><button id="Yes" class="WarnMButton"> 好的 </button></div></div>');
	$("#WarnB_"+sid).html(content);
	}
//查询某个用户针对某个模块是否具备权限
function	Authority(User,item){
	if($.inArray(item,UserAuthority)>-1){
		return 1;
	}
	else{
		var	tempflag=0;
		$.ajax({
			type:"POST",
			url: MServer+"qi/qi00002/qi04635C/AuthorityC.php",
			data:{
				username:User,
				Authority:item,
				sflag:"_04",
				date:getLangDate('newDate'),
			},
			async:false,
			success:function(data){
				if(trim(data)!=0){
					UserAuthority.push(trim(data));
					tempflag=1;
				}
				else{
					return	false;
					}
			}
		});
		return tempflag;
	}
}
//没有权限，警示不具备权限并询问是否购买这个模块，已经用户剩余的金额
function NoAuthority(item){
	//WarnMessage(WarnMessageList[0]);
	if(Q14123101=='demo'){
		$("#ch006").click();
		}
	else{
		$.ajax({
			type: "POST",
			url: MServer+"qi/qi00002/qi04635C/ServiceC.php",
			data:{
				sflag:'_04',
				item:item,
				},
			async:false,
			success: function(data){
				var data1 = eval(trim(data));;
				//alert(data1[0].ServiceID);
				$("#BG").remove();
						$("body").append('<div id="BG"><div	id="BGcontent"><div class="shut1"><img src="./assets/images/Close.png" style="width:100%;height:100%;"/></div></div></div>');
						var stxt = '<div id="PayDiv"><div style="width:300px;height:150px;"><center><img src="./assets/images/WePay.png" /></center></div>';
								stxt+='<div style="width:300px;height:50px;"><span id="pServiceID" style="display:none;">'+data1[0].ServiceID+'</span>';
								stxt+='<span id="pServiceNa">'+data1[0].ServiceNa+'</span>：<span id="pServicePr">'+data1[0].ServicePr+'</span>金币/';
								stxt+='<span id="pServiceTi">'+data1[0].ServiceTi+'</span>天，您目前剩余'+Q14123104+'金币。<span style="color:#FFC016;">添加微信获赠更多金币</span></div><center><input type="button" id="testbutton" value="购买"></center></div>';
						$("#BGcontent").css({'width':'400px','height':'300px','margin-top':'-150px','margin-right':'-200px'}).append(stxt);
			}
		})
	}	
}
function	trans1(name1){
	var data1="";
	$.ajax({
		type: "POST",
		url: MServer+"qi/qi00002/qi04635C/mqC.php",
		data:{
			qflag:"trans1",
			sflag:"_04",
			stxt:name1,
			},
		async:false,
		success: function(data){
			data1= data;
		}
		})
		return trim(data1);
}
//令某个模块可以被拖拽
function	divmove(DivId1,DivId2){
var _move=false;
var _x,_y;
$('#'+DivId1).click(function(){
	}).mousedown(function(e){
		_move=true;
		_x=e.pageX-parseInt($('#'+DivId2).css("left"));
		_y=e.pageY-parseInt($('#'+DivId2).css("top"));
		});
	$(document).mousemove(function(e){
		if(_move){
			var x=e.pageX-_x;
			var y=e.pageY-_y;
			$('#'+DivId2).css({top:y,left:x});
		}
	}).mouseup(function(){
	_move=false;
	});
}

//小于0返回绿色，大于等于0返回红色
function rcolor(tnum){if(tnum>=0){return 'style="color:#FF4D4D;"';}else{return 'style="color:#00CC66;"';}}
//日期差
function getDaysDiff(date1, date2) {
  const oneDay = 24 * 60 * 60 * 1000; // 一天的毫秒数
  const timeDiff = Math.abs(date1.getTime() - date2.getTime()); // 获取时间戳差值的绝对值
  const daysDiff = Math.round(timeDiff / oneDay); // 根据时间戳差值计算天数差
  return daysDiff;
}
//标准差
function calculateStandardDeviation(numbers) {
	if (!numbers.length) return 0; // 如果数组为空，返回0
	let sum = 0;
	for (let i = 0; i < numbers.length; i++) {
		sum += numbers[i];
	}
	let mean = sum / numbers.length;
	let varianceSum = 0;
	for (let i = 0; i < numbers.length; i++) {
		 varianceSum += Math.pow(numbers[i] - mean, 2);
	}
	let variance = varianceSum / numbers.length;
	return Math.sqrt(variance); // 返回标准差
}


// 发送数据至服务器
//msocket.emit('fromWebClient', {mess:'终端申请数据！'});
//策略数据处理器
function QuantData_(SData){
	var Msg = SData.split("#")[1];
	var MsgV = Msg.split(":")[1];
	var MsgK = Msg.split(":")[0]
	var MsgKA =MsgK.split("-");
	if(MsgKA[1]!="程序调试"){
		//$("#Rcontainer1").append(SData+'<br />');
		console.log(SData);
		/*
		if(MsgKA[3]=='general'){
			//$(Sid).append('<span style="color:#ff0000;">'+MsgKA[0]+'-'+MsgKA[2]+'-'+MsgKA[3]+'</span>-'+MsgKA[4]+':'+'<span style="color:#ffff00;">'+MsgV+'</span><br />');
			}
		else{
			//$(Sid).append(MsgKA[0]+'-'+MsgKA[2]+'-'+MsgKA[3]+'-'+MsgKA[4]+':'+MsgV+'<br />');
		}
		*/
		}
		//if (NowTopic = 'mq_top_ul_li_12'){}
}
//交易数据处理器
function ClientData_(SData){
	var Msg = SData.split("#")[1];
	var MsgV = Msg.split(":")[1];
	var MsgK = Msg.split(":")[0]
	var MsgKA =MsgK.split("-");
	if(MsgKA[1]=="程序调试"){
		if(MsgKA[3]=='general'){
			$(Sid).append('<span style="color:#ff0000;">'+MsgKA[0]+'-'+MsgKA[2]+'-'+MsgKA[3]+'</span>-'+MsgKA[4]+':'+'<span style="color:#ffff00;">'+MsgV+'</span><br />');
			}
		else{
			$(Sid).append(MsgKA[0]+'-'+MsgKA[2]+'-'+MsgKA[3]+'-'+MsgKA[4]+':'+MsgV+'<br />');
		}
		}
	else if(MsgKA[1]=="账户总览"){
		//$("#mq_main_ljBR").append(Msg+'<br />');
		//$("#mq_main_ljBR").scrollTop( $("#mq_main_ljBR")[0].scrollHeight );
		var tid = MsgKA[0];
		var tneirong = eval(MsgV);
		//$('"#'+tid+'"').html(tid);
		$('#IsOn_'+tid).css({'color':'#FF4D4D','font-weight':'bolder'}).text('1');
		//$('#IsOn_'+tid).css('background','#FFFF00');
		$('#NAV_'+tid).css({'color':'#FF4D4D','font-weight':'bolder'}).text(Math.round(tneirong[0]*100)/100);
		$('#AVAILABLE_'+tid).css({'color':'#FF4D4D','font-weight':'bolder'}).text(Math.round(tneirong[1]*100)/100);
		//#00CC66
		//alert('"#AVAILABLE_'+tid+'"');
		//$("#MARKET_VAL_"+tid).html(Math.round(tneirong[2]*100)/100);
		}
		//if (NowTopic = 'mq_top_ul_li_12'){}
}
/********************************************************/

//const numbers = [1, 2, 3, 4, 5];
//console.log(calculateStandardDeviation(numbers));
//用户登录验证，以及成功登录之后运行的程序
function	minit(username){

	$.ajax({
		type:"POST",
		url:MServer+"qi/qi00002/qi04635C/loginC.php",
		data:{
			sflag:'_04',
			username:username,
		},
		async:false,
		success:function(data){
			var	backtext=eval('('+trim(data)+')');
			//JSON.stringify()
			//alert(backtext[0].Q14123105);
			UserNote=JSON.parse(backtext[0].Q14123105);//用户记录
			Q14123101=backtext[0].Q14123101;//登录名
			Q14123104=backtext[0].Q14123104;//金币
			//Q14123002=backtext[0].Q14123002;//部门
			//Q14123004=backtext[0].Q14123004;//岗位
			$("#mq_top_T1").append('<li id="Client"></li>');
			//$("#Client").html('用户名：'+Q14123101);
			
	//---------------------------------------------
	DashMessage();
	DashMessageList =[];
	$.ajax({
		type: "POST",
		url: MServer+"qi/qi00002/qi04635C/mqC.php",
		data:{
			qflag:"Redis1Redis2",
			sflag:"_04",
			},
				async:false,
				success: function(data1){
					var Jdata = JSON.parse(data1);
					var qJdata = Jdata[0];
					var cJdata = Jdata[1];
					if (qJdata != "init"){
						//alert(qJdata);
						$.ajax({
							type: "POST",
							url: MServer+"qi/qi00002/qi04635C/mqC.php",
							data:{
								qflag:"Redis1",
								sflag:"_04",
								sKey:qJdata,
								},
									async:false,
									success: function(_data1){
										//alert(_data1);
										var Jdatas = JSON.parse(_data1);
										for (var key1 in Jdatas) {
											if (Jdatas[key1].includes("策略错误")) {
												$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
												$("#Dash_0").css("display","block");
												
												var Msg = Jdatas[key1].split("#")[1];
												var MsgV = Msg.split(":")[1];
												var MsgK = Msg.split(":")[0]
												var MsgKA =MsgK.split("-");
												$("#DashB_0").append('<span style="color:#ffff00;">'+MsgKA[0]+'</span><span style="color:#ff0000;">'+'-'+MsgKA[1]+'-'+MsgKA[2]+':</span><span style="color:#00ff00;">'+MsgV+'</span><br />');
												$("#DashB_0").scrollTop( $("#DashB_0")[0].scrollHeight );
												}
											quantmess.add(Jdatas[key1]);
											}
										}
									});
						
						}
					if (cJdata != "init"){
						//alert(cJdata);
						$.ajax({
							type: "POST",
							url: MServer+"qi/qi00002/qi04635C/mqC.php",
							data:{
								qflag:"Redis2",
								sflag:"_04",
								sKey:cJdata,
								},
									async:false,
									success: function(_data2){
										var Jdatas = JSON.parse(_data2);
										for (var key2 in Jdatas) {
											
											if (Jdatas[key2].includes("交易错误")) {
												$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
												$("#Dash_0").css("display","block");
												
												var Msg = Jdatas[key2].split("#")[1];
												var MsgV = Msg.split(":")[1];
												var MsgK = Msg.split(":")[0]
												var MsgKA =MsgK.split("-");
												$("#DashB_0").append('<span style="color:#ffff00;">'+MsgKA[0]+'-'+MsgKA[1]+'-'+MsgKA[2]+'</span><span style="color:#ff0000;">-'+MsgKA[3]+'-'+MsgKA[4]+':</span>'+'<span style="color:#00ff00;">'+MsgV+'</span><br />');
												$("#DashB_0").scrollTop( $("#DashB_0")[0].scrollHeight );
												}
											clientmess.add(Jdatas[key2]);
											}
										}
									});
						}
						
					}
				});

			//接收策略端消息
			var bflag0= 0;
			smsocket0.off().on('pushToWebClient', function (data1){
				//console.log(Array.from(quantmess).join(','));
				if (bflag0==0){
					var tt = data1.split("#")[0];
					var mkey = tt.split("_")[0];
					var mnum = parseInt(tt.split("_")[1]);
					if (mnum>0){
						$.ajax({
							type: "POST",
							url: MServer+"qi/qi00002/qi04635C/mqC.php",
							data:{
								qflag:"Redis1",
								sflag:"_04",
								sKey:tt,
								},
					 		async:false,
					 		success: function(_data1){
					 			var Jdata = JSON.parse(_data1);
					 			for (var key1 in Jdata) {
					 				if(!quantmess.has(Jdata[key1])){
					 						//alert(11);
											if (Jdata[key1].includes("策略错误")) {
												$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
												$("#Dash_0").css("display","block");
												var Msg = Jdata[key1].split("#")[1];
												var MsgV = Msg.split(":")[1];
												var MsgK = Msg.split(":")[0]
												var MsgKA =MsgK.split("-");
												$("#DashB_0").append('<span style="color:#ffff00;">'+MsgKA[0]+'</span><span style="color:#ff0000;">'+'-'+MsgKA[1]+'-'+MsgKA[2]+':</span><span style="color:#00ff00;">'+MsgV+'</span><br />');
												$("#DashB_0").scrollTop( $("#DashB_0")[0].scrollHeight );
												}
											quantmess.add(Jdata[key1]);
											QuantData_(Jdata[key1]);
					 						}
					 					}
					 				}
					 			});
					 		}
					bflag0+=1;
					 	}
					else{
						
						if (data1.includes("策略错误")) {
							$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
							$("#Dash_0").css("display","block");
							var Msg = data1.split("#")[1];
							var MsgV = Msg.split(":")[1];
							var MsgK = Msg.split(":")[0]
							var MsgKA =MsgK.split("-");
							$("#DashB_0").append('<span style="color:#ffff00;">'+MsgKA[0]+'</span><span style="color:#ff0000;">'+'-'+MsgKA[1]+'-'+MsgKA[2]+':</span><span style="color:#00ff00;">'+MsgV+'</span><br />');
							$("#DashB_0").scrollTop( $("#DashB_0")[0].scrollHeight );
							}
						quantmess.add(data1);
					 	QuantData_(data1);
					 }
					
				});
			
			//获取交易端信息
			var bflag1= 0;
			smsocket1.off().on('pushToWebClient', function (data1){
				if (bflag1==0){
					var tt = data1.split("#")[0];
					var mkey = tt.split("_")[0];
					var mnum = parseInt(tt.split("_")[1]);
					if (mnum>0){
						$.ajax({
							type: "POST",
							url: MServer+"qi/qi00002/qi04635C/mqC.php",
							data:{
								qflag:"Redis2",
								sflag:"_04",
								sKey:tt,
								},
					 			async:false,
					 			success: function(_data1){
					 				var Jdata = JSON.parse(_data1);
					 				for (var key2 in Jdata) {
					 					if(!clientmess.has(Jdata[key2])){
					 					
											if (Jdata[key2].includes("交易错误")) {
												$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
												$("#Dash_0").css("display","block");
												var Msg = Jdata[key2].split("#")[1];
												var MsgV = Msg.split(":")[1];
												var MsgK = Msg.split(":")[0]
												var MsgKA =MsgK.split("-");
												$("#DashB_0").append('<span style="color:#ffff00;">'+MsgKA[0]+'-'+MsgKA[1]+'-'+MsgKA[2]+'</span><span style="color:#ff0000;">-'+MsgKA[3]+'-'+MsgKA[4]+':</span>'+'<span style="color:#00ff00;">'+MsgV+'</span><br />');
												$("#DashB_0").scrollTop( $("#DashB_0")[0].scrollHeight );
												}
											clientmess.add(Jdata[key2]);
											ClientData_(Jdata[key2]);
					 						}
					 					}
					 				}
					 			});
					 		}
					 	bflag1+=1;
					}
					else{
						
						if (data1.includes("交易错误")) {
							$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
							$("#Dash_0").css("display","block");
							
							var Msg = data1.split("#")[1];
							var MsgV = Msg.split(":")[1];
							var MsgK = Msg.split(":")[0]
							var MsgKA =MsgK.split("-");
							$("#DashB_0").append('<span style="color:#ffff00;">'+MsgKA[0]+'-'+MsgKA[1]+'-'+MsgKA[2]+'</span><span style="color:#ff0000;">-'+MsgKA[3]+'-'+MsgKA[4]+':</span>'+'<span style="color:#00ff00;">'+MsgV+'</span><br />');
							$("#DashB_0").scrollTop( $("#DashB_0")[0].scrollHeight );
							}
						clientmess.add(data1);
					 	ClientData_(data1);
					 }
				});
							
			//---------------------------------------------
			
			//第一个界面是实时数据，登录后进入A股市场
			
			$("#mq_top_ul_li_12").click();
			//alert(UserNote.dd);
		}
	});


}

$(document).ready(function(){	minit(Q14123101);})


//登录按钮，点击登录按钮，调用登录函数
$(document).off('click',"#mq_top_ul_li_06").on('click',"#mq_top_ul_li_06",function(){
		if($("#mq_top_ul_li_user").length == 0) {
    	$("body").append('<div id="mq_top_ul_li_user"></div>');
			$("#mq_top_ul_li_user").html('<div class="form3">用&nbsp;户&nbsp;名：'+Q14123101+'</div><div class="form3">权&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;益：'+Q14123104+'金币</div>').mouseleave(function(){$("#mq_top_ul_li_user").remove();});
		}
})

//商店按钮，点击按钮，显示商品
$(document).off('click',"#mq_top_ul_li_07").on('click',"#mq_top_ul_li_07",function(){

			$("body").append('<div id="BG"><div	id="BGcontent"><div class="shut1"><img src="./assets/images/Close.png" style="width:100%;height:100%;"/></div></div></div>');
			
			$.post(MServer+"qi/qi00002/qi04635C/mqC.php",
				{	qflag:"goodslist",
					sflag:'_04',
					},
				function(data1){
					$("#BGcontent").append(data1);
					});		

})
//商品购买函数，点击某个具体商品，实现购买
$(document).off('click',".SellT").on('click',".SellT",function(){
	var tcID	=	$(this).attr("id").split("_")[1];
	var	itName=tcID;
	var itAuth=itName+'_04';
	var fAuthority=Authority(Q14123101,itAuth);
	//alert(Q14123101+itAuth+getLangDate('newDate'));
	if(fAuthority==1){
			stxt = '<img src="./assets/images/WePay0.png" style="height:98px;margin-top:16px;"/>';
			WarnMessage(stxt);
			$(document).off('click',"#Yes").on('click',"#Yes",function(){
						$(this).parent().parent().remove();
					})
	}
	else{
		NoAuthority(itAuth);
	}
})

//进入策略监控主题
$(document).off("click","#mq_top_ul_li_12").on("click","#mq_top_ul_li_12",function(){
	NowTopic = 'mq_top_ul_li_12';
	//alert(Array.from(quantmess).join(','));
	//alert(Array.from(clientmess).join(','));
	//遍历集合
	//quantmess.forEach(function(value) {console.log(value);})
	//clientmess.forEach(function(value) {console.log(value);})
	
	$("#mq_main").html(QuantConfigRealDash);
	//请求策略列表
	$.post(MServer+"qi/qi00002/qi04635C/mqC.php",
			{	qflag:"qlist",
				sflag:'_04',
				},
			function(data){
				
				var data1=eval(trim(data));
				$("#Rcontainer2").append(data1[0]);
				//alert(data1[1]);
				//$(".RealDash_body1:eq(0)").click();
				$.post(MServer+"qi/qi00002/qi04635C/mtraderC.php",
							 {qflag:"tgAccount",
								sflag:"_04",
								tvar:data1[1],
									},
					function(data1){
							var stxt = '';
							var tlist =  data1.split(',');
							var ctxt = '<center><table class="caltrowstable">';
									ctxt+= '<thead><tr><th style="width:200px;">账号</th><th style="width:80px;">名称</th><th style="width:80px;">策略</th><th style="width:50px;">运行</th><th style="width:80px;">可用资金</th><th style="width:80px;">总资产</th></tr></thead><tbody id="acctbody">';
							for(var si=0;si<tlist.length;si++){
									xtlist = tlist[si].split("#");
									var thisid = xtlist[1].replaceAll('-','_');
									//alert(xtlist[1]);
							 		ctxt+='<tr class="RealDash_body" id = "at_'+thisid+'" name="qt_'+xtlist[0]+'">';
							 		ctxt+='<td id="AccCode_'+thisid+'" style="width:200px;">'+xtlist[1]+'</td>';
							 		ctxt+='<td style="width:80px;" id="AccName_'+thisid+'">'+xtlist[2]+'</td>';
							 		ctxt+='<td style="width:80px;" id="AccQuant_'+thisid+'">'+xtlist[3]+'</td>';
							 		ctxt+='<td style="width:50px;" id="IsOn_'+thisid+'">'+0+'</td>';
							 		ctxt+='<td style="width:80px;" id="AVAILABLE_'+thisid+'">'+0+'</td>';
							 		ctxt+='<td style="width:80px;" id="NAV_'+thisid+'">'+xtlist[4]+'</td>';
							 		ctxt+='</tr>';
									}
								ctxt+= "</tbody></table></center>";	
								$("#Rcontainer1").html(ctxt);
								var qbodyheight = $("#mq_main_ljBL").height()-$("#Rcontainer1").height()-$("#quatthead").height()-6;
								$(".qaltrowstable	tbody").height(qbodyheight);
								//.qaltrowstable	tbody
								oncontextmenu();
								$("#xLcontainer1").click();
								
						});
			
			var xxxtt='<div class="left-column"><div class="status-grid"><div class="status-card normal"><div class="status-value">42</div><div class="status-label">正常</div></div><div class="status-card warning"><div class="status-value">5</div><div class="status-label">警告</div></div><div class="status-card error"><div class="status-value">2</div><div class="status-label">错误</div></div><div class="status-card"><div class="status-value">49</div><div class="status-label">总计</div></div></div><div class="data-section"><div class="data-item"><span>处理消息</span><span class="data-value">1,234</span></div><div class="data-item"><span>响应时间</span><span class="data-value">128ms</span></div><div class="data-item"><span>在线用户</span><span class="data-value">342</span></div><div class="data-item"><span>CPU使用率</span><span class="data-value">67%</span></div><div class="data-item"><span>内存使用率</span><span class="data-value">58%</span></div></div></div><div class="right-column"><div class="alert-item">数据库连接池使用率超过80%</div><div class="alert-item">API服务响应时间异常</div><div class="alert-item">服务器内存使用率过高</div><div class="alert-item">网络延迟增加</div><div class="alert-item">用户登录失败次数异常</div><div class="alert-item">磁盘空间不足警告</div></div>';
			$("#xLcontainer1").html(xxxtt);
			$("#xLcontainer2").html(xxxtt);
			$("#xLcontainer4").html(xxxtt);
			$("#xLcontainer8").html(xxxtt);
			$("#xLcontainer9").html(xxxtt);
			$("#xLcontainer10").html(xxxtt);
			
			});
	})
$(document).off('click',"#xfbuttonl").on('click',"#xfbuttonl",function(){$('#Rcontainer2').prependTo('#mq_main_ljBL');})
$(document).off('click',"#xfbuttonr").on('click',"#xfbuttonr",function(){$('#Rcontainer1').prependTo('#mq_main_ljBL');})

//自定义右键上下文
function oncontextmenu(){
	var obCon={text:"连接",func:function(){
	startRemoteDesktop();
	oncontextmenu();
	}
	};
	var mailMenuData = [[obCon]];
	$(".RealDash_body").smartMenu(mailMenuData, {
		name: "mail",
		beforeShow: function() {
		$.smartMenu.remove();
		}
	});
}

//查看账户情况情况
$(document).off('click',".RealDash_body").on('click',".RealDash_body",function(){
	$(".RealDash_body").css('background','transparent');
	$(this).css('background','rgba(20,177,235,0.3)');
	var thisid = $(this).attr("id");
	//alert($(this).attr("name"));
	WarnMessage(WarnMessageList[22]);
	$(document).off('click',"#Yes").on('click',"#Yes",function(){
			$(this).parent().parent().remove();
		})
	
})

//查看策略情况
$(document).off('click',".RealDash_body1").on('click',".RealDash_body1",function(){
	$("#RealDash_zhu_main").html('');
	var thisid = $(this).attr("id");
	var thisname = $(this).attr("name");
	$(".RealDash_body1").css('background','transparent');
	$(this).css('background','rgba(255,255,0,0.3)');
	$('.RealDash_body').css('color','#16C0FF');
	//alert(thisid);
	$("[name='"+thisid+"']").prependTo('#acctbody').css('color','#FFFF00');
	})

//进入策略回溯主题
$(document).off('click',"#mq_top_ul_li_04").on('click',"#mq_top_ul_li_04",function(){
	NowTopic = 'mq_top_ul_li_04';
	$.post(MServer+"qi/qi00002/qi04635C/mqC.php",{
		qflag:"databQ22",
		table:'PortfolioRanking',
		dflag:'04',
		},
	function(data){
		$("#mq_main").html(mainDiv);
		$("#mq_main_r").html(data);
		var txt='<div id="mxflag" style="display:none;"></div><div class="mq_main_lT" style="border:none;"><div style="flex:1;display:flex;">';
		txt+='<div id="cqmonthlyreport">生成月报</div><div id="cqweeklyreport">生成周报</div><div id="cqdailyreport">生成日报</div><div style="flex:1;"></div></div>';
		txt+='<div class="divselect" style="width:200px;"><div class="divinput" id="mxdatex"></div><div style="width:1px;"></div><div class="divselectsub" id="mxSubmit">查询</div></div><div style="flex:1;"></div></div>';
		txt+='<div id="mq_main_lT2" class="mq_main_lT" style="height:354px;justify-content: left;border: 1px solid var(--border-color);">';
		txt+='<div class="charts_kuang_ll" id ="charts_kuang_ll"></div><div id="charts_kuang_lr" class="charts_kuang_lr"></div></div>';
		txt+='<div id="mq_main_lT6" class="mq_main_lT" style="height:26px;justify-content: left;padding-left:3px;border:none;">策略介绍和评价</div>';
		txt+='<div id="mq_main_lT5" class="mq_main_lT" style="color:#FFFF00;min-height:50px;padding:10px;height:auto;"></div>';
		txt+='<div id="mq_main_lT3" class="mq_main_lT" style="height:26px; justify-content: left"><div id="shezhi" style="width:100px;padding-left:3px;">设置区间图>></div><div style="flex:1;"></div></div>';
		txt+='<div id="mq_main_lT4"></div>';
	$("#mq_main_l").empty().html(txt);
	$("#mxdatex").val(getLangDate('newDate1'));
	//点击第一个元素
	$('#mq_main_r > :first-child').click();
	
		});
	})

//回测报告按日期查询
$(document).off('click',"#mxSubmit").on('click',"#mxSubmit",function(){
	mxchaxun($("#mxflag").html(),$("#mxdatex").html().replace(/-/g,''),'hcbiaoxian');
})

$(document).off('click',"#shezhi").on('click',"#shezhi",function(){
	WarnMessage('<div style="display:flex;height:24px;justify-content:center;align-items:center;"><div>开始日期:</div><div style="width:3px;"></div>'
								+'<div  id="startdate" style="width:100px;height:100%;border: 1px solid var(--primary-dark);"></div><div style="width:3px;"></div>'
								+'<div>-</div><div style="width:3px;"></div><div>结束日期:</div><div style="width:3px;"></div><div id="enddate" style="width:100px;height:100%;border: 1px solid var(--primary-dark);" ></div></div>'
								);
	$(document).off('click',"#startdate").on('click','#startdate',function(){laydate.reset();laydate({elem:'#startdate'});$(this).css("background","rgba(20,177,235,0.3)");});
	$(document).off('click',"#enddate").on('click','#enddate',function(){laydate.reset();laydate({elem:'#enddate'});$(this).css("background","rgba(20,177,235,0.3)");});
	$("#Yes").html('提交');
	$(document).off('click',"#Yes").on('click',"#Yes",function(){
		
			var startdate = $("#startdate").html().replace(/-/g,'') ;
			var enddate = $("#enddate").html().replace(/-/g,'');
			var notestr = startdate+'_'+enddate;
			var	itName=$("#mxflag").html().split("#")[0];
			if (startdate=="" || enddate=="" ){
				$(this).parent().parent().remove();
				WarnMessage(WarnMessageList[20]);
				$(document).off('click',"#Yes").on('click',"#Yes",function(){$(this).parent().parent().remove();})
				}
			else{
				$(this).parent().parent().remove();
				//alert(UserNote);
				var itName = itName+"_interval";
				if (itName in UserNote){
						var _interval = UserNote[itName];
					} else {
						var _interval = [];
						}
				
				if($.inArray(notestr,_interval)>-1){
					return;
					}else{
						//修改UserNote,并保存
						_interval.push(notestr);
						UserNote[itName]=_interval;
						//保存
						//alert(JSON.stringify(UserNote));
						$.ajax({
								type: "POST",
								url: MServer+"qi/qi00002/qi04635C/mqC.php",
								data:{
									qflag:"_UserNote",
									sflag:"_01",
									username:Q14123101,
									UserNote:JSON.stringify(UserNote),
									},
						 		async:false,
						 		success: function(_data1){
						 			//alert(_data1);
						 			//alert(JSON.stringify(UserNote));
						 			}
						 			});
						
						
						
						$(document).off("click",".shut3").on("click",".shut3",function(){
							var	itName=$("#mxflag").html().split("#")[0]+"_interval";
							var notestr = $(this).parent().attr("name");
							var _interval = UserNote[itName];
							//修改UserNote,并保存
							_interval.splice(_interval.indexOf(notestr),1);
							UserNote[itName]=_interval;
							
							$.ajax({
									type: "POST",
									url: MServer+"qi/qi00002/qi04635C/mqC.php",
									data:{
										qflag:"_UserNote",
										sflag:"_01",
										username:Q14123101,
										UserNote:JSON.stringify(UserNote),
										},
							 		async:false,
							 		success: function(_data1){
							 			//alert(_data1);
							 			//alert(JSON.stringify(UserNote));
							 			}
							 			});
							
							//修改UserNote,并保存
							$(this).parent().remove();
							});		
						//画图
						var sid=GenNonDuplicateID(1);
						var thisID = 'mxcontainer_'+sid;
						var tx1 = []; var tx2 = []; var tx3 = [];
						var xt2 = 1;
						var xt3 = 1;
						for(var i=0;i<x1.length;i++){
							if (parseInt(startdate)>=parseInt(x1[i])){var _startdate = x1[i];}
							else if (parseInt(startdate)<parseInt(x1[i]) && parseInt(x1[i])<=parseInt(enddate)){
								tx1.push(x1[i]);
								xt2 = xt2*(parseFloat(x2[i])+1)
								xt3 = xt3*(parseFloat(x3[i])+1)
								tx2.push(Math.round((xt2-1)*10000)/100);
								tx3.push(Math.round((xt3-1)*10000)/100);
								}
							else{break;}
							}
						tx1.unshift(_startdate);tx2.unshift(0);tx3.unshift(0);
						$("#mq_main_lT4").append('<div class="charts_kuang_l"  name ="'+notestr+'" style="display: flex; flex-direction: row;"><div class="shut3" style="order:2;z-index:2;"><img src="./assets/images/Close2.png"/></div><div id="'+thisID+'" class="mxcontainer" style="order:1;z-index:1;"></div></div>');
						NodeLine2(thisID,startdate+"-"+enddate,tx1,tx2,tx3,'本策略','基准');
					}
				}
			})
	})
//产品表现统计
function Navchaxun(sid1,datax1,ditem){
	  var txt ='<div id="mxcontainer1" style="width:70%;height:100%;float:left;padding-top:30px;padding-left:30px;padding-bottom:50px;box-sizing:border-box;"></div>';
				txt+='<div id="mxcontainer2" style="width:30%;height:100%;float:left;padding-top:100px;padding-right:30px;box-sizing:border-box;"></div>';
		$("#mq_mainT").html(txt);
		$.post(MServer+"qi/qi00002/qi04635C/mqC.php",{
			qflag:"product",
			item:ditem,
		 	sid:sid1,
		 	datex:datax1,
		 	sflag:'_04',
		},
		function(data){
			//alert(data);
			//x1=[];x2=[];x3=[]
			var data1=eval(trim(data));
			var datelist = data1[0];
			var bqlist = data1[1].map(Number);
			var bilist = data1[2].map(Number);
			//x1 = datelist;
			//x2 = bqlist;
			//x3 = bilist;
			var btext = data1[3].split('_');
			var bqname = btext[0];
			var biname = btext[1];
			
			var lbq = 1;
			var lbi = 1;
			var mlbq = 1;
			var mlbi = 1;
			var bqhch = 0;
			var bihch = 0 ;
			var bqlist1 = [lbq-1];
			var bilist1 = [lbi-1];
			var bqhchlist = [bqhch];
			var bihchlist = [bihch];
			var maxbqhch = 0;
			var maxbihch = 0;
			for(var i=1;i<datelist.length;i++){
				lbq = lbq*(parseFloat(bqlist[i])+1);
				lbi = lbi*(parseFloat(bilist[i])+1);
				if (lbq>mlbq){mlbq=lbq;}
				if (lbi>mlbi){mlbi=lbi;}
				bqhch = (lbq/mlbq)-1;
				bihch = (lbi/mlbi)-1;
				if (bqhch<maxbqhch){maxbqhch=bqhch;}
				if (bihch<maxbihch){maxbihch=bihch;}
				bqhchlist.push(Math.round(bqhch*10000)/100);
				bihchlist.push(Math.round(bihch*10000)/100);
				bqlist1.push(Math.round((lbq-1)*10000)/100);
				bilist1.push(Math.round((lbi-1)*10000)/100);
				}
				Fproduct("mxcontainer1",bqname,datelist,bqlist1,bilist1,bqhchlist,bihchlist,'本策略收益',biname,'本策略回撤',biname+'回撤');
				
				var startdate = datelist[0];
				var enddate = datelist[datelist.length-1];
				var daydiff = getDaysDiff(new Date(enddate.substr(0,4)+'-'+enddate.substr(4,2)+'-'+enddate.substr(6,2)),new Date(startdate.substr(0,4)+'-'+startdate.substr(4,2)+'-'+startdate.substr(6,2)));
				var bqljsyl = Math.round((lbq-1)*10000)/100;
				var biljsyl = Math.round((lbi-1)*10000)/100;
				var cdifljsyl = Math.round((bqljsyl-biljsyl)*100)/100;
				var bqnhsyl = Math.round((lbq**(365/daydiff)-1)*10000)/100;
				var binhsyl = Math.round((lbi**(365/daydiff)-1)*10000)/100;
				var cdifnhsyl = Math.round((bqnhsyl-binhsyl)*100)/100;
				var bqdev = Math.round(calculateStandardDeviation(bqlist)*365**0.5*10000)/100;
				var bidev = Math.round(calculateStandardDeviation(bilist)*365**0.5*10000)/100;
				var cdifdev = Math.round((bqdev-bidev)*100)/100;
				var bqsharp = Math.round((bqnhsyl/bqdev)*100)/100;
				var bisharp = Math.round((binhsyl/bidev)*100)/100;
				var cdifsharp = Math.round((bqsharp-bisharp)*100)/100;
				var cdifmaxhch = maxbqhch-maxbihch;
				var maxbqhch = Math.round(maxbqhch*10000)/100;
				var maxbihch = Math.round(maxbihch*10000)/100;
				var cdifmaxhch = Math.round(cdifmaxhch*10000)/100;
				
				var txt = '<div style="width:auto;height:24px;color:#FFC016;">&nbsp&nbsp统计区间：'+startdate+'-'+enddate+'</div>';
						txt+= '<center><div class="mq_main_lT"><table class="altrowstable">';
						txt+='<tr><th>项目</th><th>累计收益</th><th>年化收益</th><th>夏普比率</th><th>年化波动</th><th>最大回撤</th></tr>';
						txt+='<tr><td>本策略</td><td '+rcolor(bqljsyl)+'>'+bqljsyl+'%</td><td '+rcolor(bqnhsyl)+'>'+bqnhsyl+'%</td><td '+rcolor(bqsharp)+'>'+bqsharp+'</td><td '+rcolor(bqdev)+'>'+bqdev+'%</td><td '+rcolor(maxbqhch)+'>'+maxbqhch+'%</td></tr>';
						txt+='<tr><td>'+biname+'</td><td '+rcolor(biljsyl)+'>'+biljsyl+'%</td><td '+rcolor(binhsyl)+'>'+binhsyl+'%</td><td '+rcolor(bisharp)+'>'+bisharp+'</td><td '+rcolor(bidev)+'>'+bidev+'%</td><td '+rcolor(maxbihch)+'>'+maxbihch+'%</td></tr>';
						txt+='<tr><td>超额</td><td '+rcolor(cdifljsyl)+'>'+cdifljsyl+'%</td><td '+rcolor(cdifnhsyl)+'>'+cdifnhsyl+'%</td><td '+rcolor(cdifsharp)+'>'+cdifsharp+'</td><td '+rcolor(cdifdev)+'>'+cdifdev+'%</td><td '+rcolor(cdifmaxhch)+'>'+cdifmaxhch+'%</td></tr>';
						txt+= "</table></div></center>";
						txt+= '<center><div class="mq_main_lT"><table class="altrowstable" style="margin-top:3px;">';
						txt+='<tr><th>年度</th><th>策略收益</th><th>策略回撤</th><th>基准收益</th><th>基准回撤</th></tr>';
				var sy = 0;
				var bisy = 0;
				var mlbqs = 0;
				var mlbis = 0;
				var bqhchs = 0;
				var bihchs = 0 ;
				var bgMaxDrawdown = 0;
				var biMaxDrawdown = 0;
				var tyear0 = datelist[0].substring(0,4);
				var leijizhi = datelist.length-1;
				for(var i=1;i<datelist.length;i++){
					var tyear1 = datelist[i].substring(0,4);
					sy = (sy+1)*(1+parseFloat(bqlist[i]))-1;
					bisy = (bisy+1)*(1+parseFloat(bilist[i]))-1;
					if (sy>mlbqs){mlbqs=sy;}
					if (bisy>mlbis){mlbis=bisy;}
					bqhchs = ((sy+1)/(mlbqs+1))-1;
					bihchs = ((bisy+1)/(mlbis+1))-1;
					if (bqhchs<bgMaxDrawdown){bgMaxDrawdown=bqhchs;}
					if (bihchs<biMaxDrawdown){biMaxDrawdown=bihchs;}
					
					if((tyear1!=tyear0 && i>0) || i==leijizhi){
						sy = Math.round(sy*10000)/100;
						bisy = Math.round(bisy*10000)/100;
						bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
						biMaxDrawdown = Math.round(biMaxDrawdown*10000)/100;
						txt+='<tr><td>'+tyear0+'</td><td '+rcolor(sy)+'>'+sy+'%</td><td  '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td><td '+rcolor(bisy)+'>'+bisy+'%</td><td  '+rcolor(biMaxDrawdown)+'>'+biMaxDrawdown+'%</td></tr>';
						tyear0 =tyear1;
						sy = parseFloat(bqlist[i]);
						bisy = parseFloat(bilist[i]);
						mlbqs = 0;
						mlbis = 0;
						bqhchs = 0;
						bihchs = 0 ;
						bgMaxDrawdown = 0;
						biMaxDrawdown = 0;
						}
					}
			txt+= "</table></div></center>";
			$("#mxcontainer2").html(txt);
	});
}

	
//进入产品查询
$(document).off('click',"#mq_top_ul_li_14").on('click',"#mq_top_ul_li_14",function(){
	
	$("#mq_main").html(mainDiv2);
	$.post(MServer+"qi/qi00002/qi04635C/mqC.php",{
		qflag:"productC",
		tflag:"contents",
		sflag:'_04',
		},
	function(data){
		$('#mq_mainB').html(data);
		});
		$("#ProductAppend").css('background','rgba(255,255,255,0.3)');
		$("#pitflag").html('ProductAppend');
		$("#ProductNav").css('background','rgba(255,255,255,0.3)');
		$("#pchflag").html('ProductNav');	
})

$(document).off('click',".BList").on('click',".BList",function(){
	var CId=$(this).attr('id');
	$(".BList").css('background','transparent');
	$(this).css('background','rgba(255,255,255,0.3)');
	$("#pchflag").html(CId);
})
$(document).off('click',".RList").on('click',".RList",function(){
	var CId=$(this).attr('id');
	$(".RList").css('background','transparent');
	$(this).css('background','rgba(255,255,255,0.3)');
	$("#pitflag").html(CId);
})
$(document).off('click',".productC").on('click',".productC",function(){
	var CName=$(this).html();
	var CChar=$(this).attr('id');
	var CBindex=$(this).attr('name');
	$("#pidflag").html(CChar+'#'+CName+'#'+CBindex);
	$(".productC").css('color','#16C0FF');
	$(this).css('color','#FFFFFF');
	$('#productGo').click();
})

$(document).off('click',"#productGo").on('click',"#productGo",function(){
	var pchflag = $("#pchflag").html();
	var pitflag = $("#pitflag").html();
	var pidflag = $("#pidflag").html();
	if (pchflag== "ProductNav" && pitflag== "ProductAppend" ) {
		Navchaxun(pidflag,'20501231','chpbiaoxian');
		}
		else {
			var	prRealDash ='<div class="Lcharts_kuang0"><div id="Lcontainer1" class="Lcontainer"></div></div>';
					prRealDash+='<div class="Lcharts_kuang0"><div id="Lcontainer2" class="Lcontainer"></div></div>';
					prRealDash+='<div class="Lcharts_kuang0"><div id="Lcontainer3" class="Lcontainer"></div></div>';
					prRealDash+='<div class="Lcharts_kuang0"><div id="Lcontainer4" class="Lcontainer"></div></div>';
					prRealDash+='<div class="Lcharts_kuang0"><div id="Lcontainer5" class="Lcontainer"></div></div>';
					prRealDash+='<div class="Lcharts_kuang0"><div id="Lcontainer6" class="Lcontainer"></div></div>';
					prRealDash+='<div class="Lcharts_kuang0"><div id="Lcontainer7" class="Lcontainer"></div></div>';
		$("#mq_mainT").html(prRealDash);
		
				//WarnMessage("没有可执行的项目！");
				//$(document).off('click',"#Yes").on('click',"#Yes",function(){$(this).parent().parent().remove();})
				var  thisname='中证1000指数增强01';
				$.post(MServer+"qi/qi00002/qi04635C/mtraderC.php",
					{	qflag:"qgraph",
						sflag:"_04",
						tname:thisname,
							},
				function(data2){
					
					data2=eval(trim(data2));
					
					//清空全局x1,x2列表
					x1=[];x2=[];x3=[];x4=[];x5=[];x6=[];
					for(var i=0;i<data2.length;i++){
						tdate = data2[i].date;
						tNAV = data2[i].NAV;
						tRet = data2[i].Ret;
						tMaxDrawdown = data2[i].MaxDrawdown;
						tHsl = data2[i].Hsl;
						tZj = data2[i].Zj;
						x1.push(tdate);
						x2.push(Math.round((tNAV-1)*100)/100);
						x3.push(Math.round((tRet-1)*100)/100);
						x4.push(tMaxDrawdown);
						x5.push(tHsl);
						x6.push(tZj);
						}
						Fproduct("Lcontainer1",'',x1,x2);	
						Rproduct("Lcontainer3",'',x1,x3);	
						NodeBar("Lcontainer2",'最大回撤',x1,x4);	
						NodeBar("Lcontainer4",'换手率',x1,x5);	
						NodeLine("Lcontainer7",'资金规模',x1,x6);	
					})
			$.post(MServer+"qi/qi00002/qi04635C/mtraderC.php",
					{	qflag:"qhyfb",
						sflag:"_04",
						tname:thisname,
							},
				function(data2){
					
					data2=eval(trim(data2));
					mxhxfb("Lcontainer6","",data2)
					})
			$.post(MServer+"qi/qi00002/qi04635C/mtraderC.php",
					{	qflag:"qgggx",
						sflag:"_04",
						tname:thisname,
							},
				function(data2){
					var chic1=[];var chic1z=[];var chic1f=[];
					data2=eval(trim(data2));
					for(var i=0;i<data2.length;i++){
						chic1.push(data2[i].name);
						chic1z.push(data2[i].flhz);
						chic1f.push(data2[i].flhf);
						}
					Szhbar('myChart7','option7','Lcontainer5','行业贡献',chic1,chic1z,chic1f)
					})
			
		}
})


//策略组合数据统计
function mxchaxun(sid1,datax1,ditem){
		var thisname = sid1.split('#')[1];
		//alert(sid1);
		$.post(MServer+"qi/qi00002/qi04635C/mqC.php",{
		qflag:"product",
		 item:ditem,
		 sid:sid1,
		 datex:datax1,
		 sflag:'_04',
		},
		function(data){
			x1=[];x2=[];x3=[];
			//alert(data);
			var data1=eval(trim(data));
			var datelist = data1[0];
			var bqlist = data1[1].map(Number);
			var bilist = data1[2].map(Number);
			x1 = datelist;
			x2 = bqlist;
			x3 = bilist;
			var btext = data1[3].split('_');
			var bqname = btext[0];
			var biname = btext[1];
			
			var lbq = 1;
			var lbi = 1;
			var mlbq = 1;
			var mlbi = 1;
			var bqhch = 0;
			var bihch = 0 ;
			var bqlist1 = [lbq-1];
			var bilist1 = [lbi-1];
			var bqhchlist = [bqhch];
			var bihchlist = [bihch];
			var maxbqhch = 0;
			var maxbihch = 0;
			for(var i=1;i<datelist.length;i++){
				lbq = lbq*(parseFloat(bqlist[i])+1);
				lbi = lbi*(parseFloat(bilist[i])+1);
				if (lbq>mlbq){mlbq=lbq;}
				if (lbi>mlbi){mlbi=lbi;}
				bqhch = (lbq/mlbq)-1;
				bihch = (lbi/mlbi)-1;
				if (bqhch<maxbqhch){maxbqhch=bqhch;}
				if (bihch<maxbihch){maxbihch=bihch;}
				bqhchlist.push(Math.round(bqhch*10000)/100);
				bihchlist.push(Math.round(bihch*10000)/100);
				bqlist1.push(Math.round((lbq-1)*10000)/100);
				bilist1.push(Math.round((lbi-1)*10000)/100);
				}
				Fproduct("charts_kuang_ll",thisname,datelist,bqlist1,bilist1,bqhchlist,bihchlist,'本策略收益',biname,'本策略回撤',biname+'回撤');
				var startdate = datelist[0];
				var enddate = datelist[datelist.length-1];
				var daydiff = getDaysDiff(new Date(enddate.substr(0,4)+'-'+enddate.substr(4,2)+'-'+enddate.substr(6,2)),new Date(startdate.substr(0,4)+'-'+startdate.substr(4,2)+'-'+startdate.substr(6,2)));
				var bqljsyl = Math.round((lbq-1)*10000)/100;
				var biljsyl = Math.round((lbi-1)*10000)/100;
				var cdifljsyl = Math.round((bqljsyl-biljsyl)*100)/100;
				var bqnhsyl = Math.round((lbq**(365/daydiff)-1)*10000)/100;
				var binhsyl = Math.round((lbi**(365/daydiff)-1)*10000)/100;
				var cdifnhsyl = Math.round((bqnhsyl-binhsyl)*100)/100;
				var bqdev = Math.round(calculateStandardDeviation(bqlist)*365**0.5*10000)/100;
				var bidev = Math.round(calculateStandardDeviation(bilist)*365**0.5*10000)/100;
				var cdifdev = Math.round((bqdev-bidev)*100)/100;
				var bqsharp = Math.round((bqnhsyl/bqdev)*100)/100;
				var bisharp = Math.round((binhsyl/bidev)*100)/100;
				var cdifsharp = Math.round((bqsharp-bisharp)*100)/100;
				var cdifmaxhch = maxbqhch-maxbihch;
				var maxbqhch = Math.round(maxbqhch*10000)/100;
				var maxbihch = Math.round(maxbihch*10000)/100;
				var cdifmaxhch = Math.round(cdifmaxhch*10000)/100;
				
				var txt = '<div style="height:24px;color:#FFC016;padding-left:3px;display:flex;align-items:center;justify-content:left;">统计区间：'+startdate+'-'+enddate+'</div>';
						txt+= '<div class="mq_main_lT"><table class="altrowstable">';
						txt+='<tr><th>项目</th><th>累计收益</th><th>年化收益</th><th>夏普比率</th><th>年化波动</th><th>最大回撤</th></tr>';
						txt+='<tr><td>本策略</td><td '+rcolor(bqljsyl)+'>'+bqljsyl+'%</td><td '+rcolor(bqnhsyl)+'>'+bqnhsyl+'%</td><td '+rcolor(bqsharp)+'>'+bqsharp+'</td><td '+rcolor(bqdev)+'>'+bqdev+'%</td><td '+rcolor(maxbqhch)+'>'+maxbqhch+'%</td></tr>';
						txt+='<tr><td>'+biname+'</td><td '+rcolor(biljsyl)+'>'+biljsyl+'%</td><td '+rcolor(binhsyl)+'>'+binhsyl+'%</td><td '+rcolor(bisharp)+'>'+bisharp+'</td><td '+rcolor(bidev)+'>'+bidev+'%</td><td '+rcolor(maxbihch)+'>'+maxbihch+'%</td></tr>';
						txt+='<tr><td>超额</td><td '+rcolor(cdifljsyl)+'>'+cdifljsyl+'%</td><td '+rcolor(cdifnhsyl)+'>'+cdifnhsyl+'%</td><td '+rcolor(cdifsharp)+'>'+cdifsharp+'</td><td '+rcolor(cdifdev)+'>'+cdifdev+'%</td><td '+rcolor(cdifmaxhch)+'>'+cdifmaxhch+'%</td></tr>';
						txt+= "</table></div>";
						txt+= '<div class="mq_main_lT"><table class="altrowstable" style="margin-top:3px;">';
						txt+='<tr><th>年度</th><th>策略收益</th><th>策略回撤</th><th>基准收益</th><th>基准回撤</th></tr>';
				var sy = 0;
				var bisy = 0;
				var mlbqs = 0;
				var mlbis = 0;
				var bqhchs = 0;
				var bihchs = 0 ;
				var bgMaxDrawdown = 0;
				var biMaxDrawdown = 0;
				var tyear0 = datelist[0].substring(0,4);
				var leijizhi = datelist.length-1;
				for(var i=1;i<datelist.length;i++){
					var tyear1 = datelist[i].substring(0,4);
					sy = (sy+1)*(1+parseFloat(bqlist[i]))-1;
					bisy = (bisy+1)*(1+parseFloat(bilist[i]))-1;
					if (sy>mlbqs){mlbqs=sy;}
					if (bisy>mlbis){mlbis=bisy;}
					bqhchs = ((sy+1)/(mlbqs+1))-1;
					bihchs = ((bisy+1)/(mlbis+1))-1;
					if (bqhchs<bgMaxDrawdown){bgMaxDrawdown=bqhchs;}
					if (bihchs<biMaxDrawdown){biMaxDrawdown=bihchs;}
					
					if((tyear1!=tyear0 && i>0) || i==leijizhi){
						sy = Math.round(sy*10000)/100;
						bisy = Math.round(bisy*10000)/100;
						bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
						biMaxDrawdown = Math.round(biMaxDrawdown*10000)/100;
						txt+='<tr><td>'+tyear0+'</td><td '+rcolor(sy)+'>'+sy+'%</td><td  '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td><td '+rcolor(bisy)+'>'+bisy+'%</td><td  '+rcolor(biMaxDrawdown)+'>'+biMaxDrawdown+'%</td></tr>';
						tyear0 =tyear1;
						sy = parseFloat(bqlist[i]);
						bisy = parseFloat(bilist[i]);
						mlbqs = 0;
						mlbis = 0;
						bqhchs = 0;
						bihchs = 0 ;
						bgMaxDrawdown = 0;
						biMaxDrawdown = 0;
						}
					}
			txt+= "</table></div>";
			$("#charts_kuang_lr").html(txt);
			
			$("#mq_main_lT4").empty();
			var itName = sid1.split("#")[0]+"_interval";
			//alert(UserNote);
			if (itName in UserNote){
				var _interval = UserNote[itName];
				$(document).off("click",".shut3").on("click",".shut3",function(){
					//修改UserNote,并保存
					var	itName=$("#mxflag").html().split("#")[0]+"_interval";
					var notestr = $(this).parent().attr("name");
					var _interval = UserNote[itName];
					//修改UserNote,并保存
					_interval.splice(_interval.indexOf(notestr),1);
					UserNote[itName]=_interval;
					
					$.ajax({
							type: "POST",
							url: MServer+"qi/qi00002/qi04635C/mqC.php",
							data:{
								qflag:"_UserNote",
								sflag:"_01",
								username:Q14123101,
								UserNote:JSON.stringify(UserNote),
								},
					 		async:false,
					 		success: function(_data1){
					 			//alert(_data1);
					 			//alert(JSON.stringify(UserNote));
					 			}
					 			});
					$(this).parent().remove();
					});
				for(var j=0;j<_interval.length;j++){
						var notestr = _interval[j];
						var notestrlist = notestr.split('_');
						var startdate = notestrlist[0];
						var enddate = notestrlist[1];
						//画图
						var sid=GenNonDuplicateID(1);
						var thisID = 'mxcontainer_'+sid;
						var tx1 = []; var tx2 = []; var tx3 = [];
						var xt2 = 1;
						var xt3 = 1;
						for(var i=0;i<x1.length;i++){
							if (parseInt(startdate)>=parseInt(x1[i])){var _startdate = x1[i];}
							else if (parseInt(startdate)<parseInt(x1[i]) && parseInt(x1[i])<=parseInt(enddate)){
								tx1.push(x1[i]);
								xt2 = xt2*(parseFloat(x2[i])+1)
								xt3 = xt3*(parseFloat(x3[i])+1)
								tx2.push(Math.round((xt2-1)*10000)/100);
								tx3.push(Math.round((xt3-1)*10000)/100);
								}
							else{break;}
							}
						tx1.unshift(_startdate);tx2.unshift(0);tx3.unshift(0);
						$("#mq_main_lT4").append('<div class="charts_kuang_l"  name ="'+notestr+'" style="display: flex; flex-direction: row;"><div class="shut3" style="order:2;z-index:2;"><img src="./assets/images/Close2.png"/></div><div id="'+thisID+'" class="mxcontainer" style="order:1;z-index:1;"></div></div>');
						NodeLine2(thisID,startdate+"-"+enddate,tx1,tx2,tx3,'本策略','基准');
					}
				}
	
	});
}

//选择日期下拉框绑定
$(document).off('click',"#mxdatex").on('click','#mxdatex',function(){laydate.reset();laydate({elem:'#mxdatex'});$(this).css("background","rgba(20,177,235,0.3)");});

//弹出聊天框
$(document).off('click',"#pet").on('click',"#pet",function(){
	if($("#PetTalk").length>0){}else{AddPetTalk();}
	});
//弹出聊天交互后，绑定键盘按键，发送问候语
function AddPetTalk(){
	
	var txt ='<div id="PetTalk">';
	txt+='<div id="PetTalkH"><span style="color:#16C0FF;">&nbsp;β9-</span><span id="PetTalkFlag" style="display:none;"></span></div>';
	txt+='<div class="shut"><img src="./assets/images/Close2.png"/></div>';
	txt+='<div id="PetTalkB"></div>';
	txt+='<div id="PetTalkC">';
	txt+='<div id="PetTalkCL">';
	txt+='<textarea id="UserTalk"></textarea>';
	txt+='</div>';
	txt+='<div id="PetTalkCR">发送</div>';
	txt+='</div>';
	txt+='</div>';
	
		$('body').append(txt);
		//回车键绑定
	  $('#UserTalk').unbind().keypress(function(event){  
    	var keynum = (event.keyCode ? event.keyCode : event.which);  
    	if(keynum == '13' && event.shiftKey){
    		//留空就可以
    		}
    	else if(keynum == '13'){
    		event.cancelBubble=true;
    		event.preventDefault();
    		event.stopPropagation();
    		$('#PetTalkCR').click();
    		}
			}); 
		$("#UserTalk").focus();
		$(document).off("click",".shut").on("click",".shut",function(){$(this).parent().remove();});

	divmove("PetTalkH","PetTalk");
	//填加统计模块儿
	//RealDash
	//###
$("#PetTalkB").append('<div class="TalkDiv"><div class="PetTalkDiv"><div class="PetTalk">'+'你好，我可以回答你一些问题。'+'</div></div><div class="PetTalkTouXiang"><div class="jPetTalkTouXiang" style="background-image:url(./assets/images/dting.jpg); background-size :100% 100%;"></div></div></div>');
};
//利用关键词交互
$(document).off('click','#PetTalkCR').on('click','#PetTalkCR', function(){
	var ClientTalk = $("#UserTalk").val();
	if(ClientTalk!=''){
		$("#PetTalkB").append('<div class="TalkDiv"><div class="UserTalkDiv"><div class="UserTalk">'+ClientTalk+'</div></div><div class="UserTalkTouXiang"><div class="jUserTalkTouXiang" style="background-image:url(./assets/images/Client.jpg); background-size :100% 100%;"></div></div></div>');
		$("#PetTalkB").scrollTop( $("#PetTalkB")[0].scrollHeight );
		$("#UserTalk").val('');
		if(ClientTalk=="ClientBill#q"){
			//调取客户信息表
			var sid=GenNonDuplicateID(1);
			$.ajax({
				type: "POST",
				url: "qi/qi00001/qi04635/DashBoard.php",
				data:{fid:sid, },
				async:false,
				success: function(datax){
					$("body").append(datax);
					var DashBWH="DashBWH_"+sid;
					var DashBWB="DashBWB_"+sid;
					var DashBW="DashBW_"+sid;
					divmove(DashBWH,DashBW);
					$("#"+DashBW).css({"width":"800px","margin-right":"-400px"});
					$("#"+DashBWB).css("padding","3px");
					$("#"+DashBWH).html('<span style="color:#ffff00;">---客户账单---</span>');
					$.ajax({
							type: "POST",
							url: MServer+"qi/qi00002/qi04635C/mqC.php",
							data:{
								qflag:"ClientBill",
								sflag:"_04",
								},
					 		async:false,
					 		success: function(_data1){$("#"+DashBWB).html(_data1);}
					 			});
					}
				})
		
		}
		else if(ClientTalk=="#MDDashboard"){
			var MEntityID = ClientTalk.substr(1);
			//alert(MEntityID);
			//MDDashboard+
			$.ajax({
				type: "POST",
				url: MServer+"qi/qi00002/qi04635C/NetCalC.php",
				data:{
					qflag:"mnamesel",
					sid:"_04",
					MEntityID:MEntityID,
					MFlag:"MDDashboard",
					},
				async:false,
				success: function(data){
					$("#mq_top_ul_li_01").click();
					var PetAnswer =data;
					$("#PetTalkB").append('<div class="TalkDiv"><div class="PetTalkDiv"><div class="PetTalk">'+PetAnswer+'</div></div><div class="PetTalkTouXiang"><div class="jPetTalkTouXiang" style="background-image:url(./assets/images/dting.jpg); background-size :100% 100%;"></div></div></div>');
					$("#PetTalkB").scrollTop( $("#PetTalkB")[0].scrollHeight );
					$("#UserTalk").focus();				
					
				}
			
			
			})
		
		}
		else if(ClientTalk=='#MDSubmit'){
			MDSubmit();
			}
		else{
			$.post(MServer+"qi/qi00002/qi04635C/mqC.php",
			{
			qflag:"training",
			username:Q14123101,
			content:ClientTalk,
			},
			function(data){
				Aitr = data.replace('#','<br/>---------<br/>').replace('\n','<br/>');
			//alert(data);
			$("#PetTalkB").append('<div class="TalkDiv"><div class="PetTalkDiv"><div class="PetTalk">'+Aitr+'</div></div><div class="PetTalkTouXiang"><div class="jPetTalkTouXiang" style="background-image:url(./assets/images/dting.jpg); background-size :100% 100%;"></div></div></div>');
			$("#PetTalkB").scrollTop( $("#PetTalkB")[0].scrollHeight );
			$("#UserTalk").focus();		
				
				})
		
		}
		}
	})

//提示框
function DashMessage(content){
		var txt ='<div class="Dash" id="Dash_0" style="display:none;">';
				txt+='<div class="shut2"><img src="./assets/images/Close2.png"/></div><div class="DashH" id="DashH_0"></div>';
				txt+='<div class="DashB" id="DashB_0"></div>';
				txt+='</div>';
		$("body").append(txt);
		
		var DashH="DashH_0";
		var Dash="Dash_0";
		divmove(DashH,Dash);
		$(document).off("click",".shut2").on("click",".shut2",function(){
		$(this).parent().hide();
		$("#mq_top_ul_li_War").css("animation-name","none");
		});
	}
//提示框
function DashMessage_(content){
	var sid=GenNonDuplicateID(1);
	$.ajax({
		type: "POST",
		url: "qi/qi00001/qi04635/dash1.php",
		data:{fid:sid, },
		async:false,
		success: function(data){
			$("body").append(data);
			$("#DashB_"+sid).html(content);
			var DashH="DashH_"+sid;
			var Dash="Dash_"+sid;
			divmove(DashH,Dash);
		}
		})
	}
//策略回测模块，选择不同策略	
$(document).off('click',".PRIT").on('click',".PRIT",function(){
	var itCode=$(this).attr('name');
	var	itChar=$(this).attr('id');
	var itName=$(this).html();
	
	$(".PRIT").css('background','transparent');
	$(this).css('background','rgba(20,177,235,0.3)');
	//alert(itChar); 
	var itAuth=itChar+'_04';
	//var fAuthority=Authority(Q14123101,itAuth);
	//alert(Q14123101+itAuth+getLangDate('newDate'));
	var fAuthority=1;
	if(fAuthority==1){
	$("#mxflag").html(itChar+"#"+itName+"#"+itCode);
	$.post(MServer+"qi/qi00002/qi04635C/NodeC.php",{
	sid:"_04",
	sflag:"MEntityNote",
	sKey:itChar,
	},
	function(data){
		data1=eval(trim(data));
		var x1='';
		for(var i=0;i<data1.length;i++){
			x1+=data1[i].Note;
			}
		$("#mq_main_lT5").html(x1);
		});
		
	mxchaxun(itChar+"#"+itName+"#"+itCode,$("#mxdatex").val().replace(/-/g,''),'hcbiaoxian');
	}
	else{
		NoAuthority(itAuth);
	}

	})

//提示消息
$(document).off('click',"#mq_top_ul_li_War").on('click',"#mq_top_ul_li_War",function(){
	$("#Dash_0").css("display","block");
	
	$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
	$(document).off("click",".shut2").on("click",".shut2",function(){
		$(this).parent().hide();
		$("#mq_top_ul_li_War").css("animation-name","none");
		});
	
})
//购买服务
$(document).off('click',"#testbutton").on('click',"#testbutton",function(){
	var	CpServiceID=$("#pServiceID").text();
	var	CpServiceNa=$("#pServiceNa").text();
	var	CpServicePr=$("#pServicePr").text();
	var	CpServiceTi=$("#pServiceTi").text();
	$.ajax({
		type:"POST",
		url:MServer+"qi/qi00002/qi04635C/SellC.php",
		data:{
			username:Q14123101,
			CpServicePr:CpServicePr,
			sflag:"_01_04",
			dflag:"sell",
		},
		async:false,
		success:function(cdata){
			if(cdata==0){
				WarnMessage(WarnMessageList[9]);
				$(document).off('click',"#Yes").on('click',"#Yes",function(){
					$(this).parent().parent().remove();
					})
				}
			else{
				$.ajax({
					type:"POST",
					url:MServer+"qi/qi00002/qi04635C/AuthorityC.php",
					data:{
						username:Q14123101,
						Authority:CpServiceID,
						CpServiceNa:CpServiceNa,
						sflag:"_01",
						date:CpServiceTi,
					},
					async:false,
					success:function(data){
						if(trim(data)==1){
							Q14123104=cdata;
							$("#BG").remove();
							WarnMessage(WarnMessageList[8]);
							$(document).off('click',"#Yes").on('click',"#Yes",function(){
								$(this).parent().parent().remove();
							})
						}
						else{
							return	false;
							}
					}
				});
				
				
				}
		}
	});
//alert(Q14123101+'-'+CpServiceID+'-'+CpServiceNa+'-'+CpServicePr+'-'+CpServiceTi);
})

//购买服务
$(document).off('click',".ClientB").on('click',".ClientB",function(){
	var tcID	=	$(this).attr("id");
	//alert(tcID);
	
	//调取客户信息表
	var sid=GenNonDuplicateID(1);
	$.ajax({
		type: "POST",
		url: "qi/qi00001/qi04635/DashBoard.php",
		data:{fid:sid, },
		async:false,
		success: function(datax){
			$("body").append(datax);
			var DashBWH="DashBWH_"+sid;
			var DashBWB="DashBWB_"+sid;
			var DashBW="DashBW_"+sid;
			divmove(DashBWH,DashBW);
			$("#"+DashBW).css({"width":"1000px","height":"600px","margin-right":"-500px","margin-top":"-300px"});
			$("#"+DashBWB).css("padding","3px");
			$("#"+DashBWH).html('<span style="color:#ffff00;">---'+tcID+'-明细账单---</span>');
			$.ajax({
					type: "POST",
					url: MServer+"qi/qi00002/qi04635C/mqC.php",
					data:{
						qflag:"ClientBillDetails",
						sflag:"_04",
						ClientA:tcID,
						},
			 		async:false,
			 		success: function(_data1){$("#"+DashBWB).html(_data1);}
			 			});
			 			
			}
		})
	})

$(document).off("click","#mq_top_ul_li_05").on("click","#mq_top_ul_li_05",function(){
	$("#mq_main").html(mainDiv);
	var txt = '<div class="divselect">';
	txt += '<div  class="divinput" id="Report_inputTxt" contenteditable="true"></div><div style="width:1px;"></div>';
	txt += '<div  class="divselectsub" id="Report_dataSelect" class="btn2">查询</div>';
	txt += '</div>';
	txt += '<div id="Report_jbaobiao" class="jbaobiao"></div>';
	$("#mq_main_r").html(txt);
	//最新报告
	var QRep_sTxt='#';
	if(QRep_sTxt!=''){
	$.post(MServer+"qi/qi00002/qi04635C/mqC.php",
	{
		qflag:"Report",
		sflag:"_04",
		QRep_sTxt:QRep_sTxt,
		},
		function(data){
			$("#Report_jbaobiao").html('<div class="reportdiv" style="padding-left:3px;color:#FFC016;justify-content: left;">最新报告：</div>'+data);
			});
		}
	})
$(document).off('click',".xRep").on('click',".xRep",function(){
	var xReportID=$(this).attr('name');
	var xReportNa=$(this).text();
	//alert(xReportID);
	var	itName=xReportID;
	var itAuth=itName+'_04';
	//var fAuthority=Authority(Q14123101,itAuth);
	var fAuthority=1;
	var Package01=Authority(Q14123101,"TC0003_04");
	
	if(fAuthority==1||Package01==1){
		var tpdf = "'doc/"+xReportNa+"'";
		var xpdf = '<iframe class="mq_main_l_Frame" runat="server" src="'+MServer+'qi/qi00004/pdf/t.php?aa='+tpdf+'"></iframe>';
		$("#mq_main_l").html(xpdf);
	}
	else{
		NoAuthority(itAuth);
	}
	})
$(document).off('click',"#Report_dataSelect").on('click',"#Report_dataSelect",function(){
	var QRep_sTxt=$("#Report_inputTxt").html();
	if(QRep_sTxt==''){
		WarnMessage(WarnMessageList[1]);
	$(document).off('click',"#Yes").on('click',"#Yes",function(){
		$(this).parent().parent().remove();
		})
	}
	else if(QRep_sTxt!=''){
	$.post(MServer+"qi/qi00002/qi04635C/mqC.php",
	{
		qflag:"Report",
		sflag:"_04",
		QRep_sTxt:QRep_sTxt,
		},
		function(data){
			$("#Report_jbaobiao").html(data);
			});
		}
	})

$(document).off("click","#mq_top_ul_li_01").on("click","#mq_top_ul_li_01",function(){
	//var mq_main_rmainT = '<div class="zhu_main"><div id="databnote"></div>';
	var mq_main_rmainT = '<div id="databside"></div>';
	//mq_main_rmainT+= '<div id="dashboard"></div>';
	$("#mq_main").html(mainDiv+mq_main_rmainT);
	divmove("databside","databside");	
	$.post(MServer+"qi/qi00002/qi04635C/mqC.php",
	{
		qflag:"Specialdata",
		sflag:"_04",
		},
		function(data1){
			$("#mq_main_r").html(data1);
			});
	})
$(document).off('click',".jkzb").on('click',".jkzb",function(){
	$(".jkzb").css('background','transparent');
	$(this).css('background','rgba(20,177,235,0.3)');
	var	itName=$(this).attr("name");
	var itAuth=itName+'_04';
	var fAuthority=Authority(Q14123101,itAuth);
	//alert(Q14123101+itAuth+getLangDate('newDate'));
	if(fAuthority==1){
		eval(itName+'();');
	}
	else{
		NoAuthority(itAuth);
	}
	})
	
function MDSubmit(){
	//offpush();
	var tmid1;var tmid2;var tmid3;var tmid4; var d1;var d2;var d3;var d4;
	var check1;	var check2;	var check3;	var check4;
	var scheck1;	var scheck2;	var scheck3;	var scheck4;
	var dcheck1;	var dcheck2;	var dcheck3;	var dcheck4;
	var kcheck1;	var kcheck2;	var kcheck3;	var kcheck4;
	var kscheck1;	var kscheck2;	var kscheck3;	var kscheck4;
	var kdcheck1;	var kdcheck2;	var kdcheck3;	var kdcheck4;
	var bt1;var bt2;var bt3;var bt4;
	if(document.getElementById("tu1")){tmid1=document.getElementById("tu1").value;}	d1=trans(tmid1);
	if(document.getElementById("biaoti1")){bt1=document.getElementById("biaoti1").value;}
	if(document.getElementById("d1")){check1=document.getElementById("d1").value;} kcheck1=trans1(check1);
	if(document.getElementById("d2")){scheck1=document.getElementById("d2").value;} kscheck1=trans1(scheck1); 
	if(document.getElementById("d3")){dcheck1=document.getElementById("d3").value;} kdcheck1=trans1(dcheck1); 
	if(d1 && check1 && !scheck1 && !dcheck1){out1(d1,kcheck1,"container1",bt1,check1);}
	if(d1 && check1 && scheck1 && !dcheck1){out1(d1,kcheck1,"container1",bt1,check1,kscheck1,scheck1);}
	if(d1 && check1 && scheck1 && dcheck1){out1(d1,kcheck1,"container1",bt1,check1,kscheck1,scheck1,kdcheck1,dcheck1);}
	if(document.getElementById("tu2")){tmid2=document.getElementById("tu2").value;} d2=trans(tmid2);
	if(document.getElementById("biaoti2")){bt2=document.getElementById("biaoti2").value;}
	if(document.getElementById("s1")){check2=document.getElementById("s1").value;} kcheck2=trans1(check2); 
	if(document.getElementById("s2")){scheck2=document.getElementById("s2").value;} kscheck2=trans1(scheck2); 
	if(document.getElementById("s3")){dcheck2=document.getElementById("s3").value;} kdcheck2=trans1(dcheck2); 
	if(d2 && check2 && !scheck2 && !dcheck2){out1(d2,kcheck2,"container2",bt2,check2);}  
	if(d2 && check2 && scheck2 && !dcheck2){out1(d2,kcheck2,"container2",bt2,check2,kscheck2,scheck2);}  
	if(d2 && check2 && scheck2 && dcheck2){out1(d2,kcheck2,"container2",bt2,check2,kscheck2,scheck2,kdcheck2,dcheck2);}  
	if(document.getElementById("tu3")){tmid3=document.getElementById("tu3").value;} d3=trans(tmid3);
	if(document.getElementById("biaoti3")){bt3=document.getElementById("biaoti3").value;}
	if(document.getElementById("t1")){check3=document.getElementById("t1").value;} kcheck3=trans1(check3); 
	if(document.getElementById("t2")){scheck3=document.getElementById("t2").value;} kscheck3=trans1(scheck3); 
	if(document.getElementById("t3")){dcheck3=document.getElementById("t3").value;} kdcheck3=trans1(dcheck3); 
	if(d3 && check3 && !scheck3 && !dcheck3){out1(d3,kcheck3,"container3",bt3,check3);}  
	if(d3 && check3 && scheck3 && !dcheck3){out1(d3,kcheck3,"container3",bt3,check3,kscheck3,scheck3);}  
	if(d3 && check3 && scheck3 && dcheck3){out1(d3,kcheck3,"container3",bt3,check3,kscheck3,scheck3,kdcheck3,dcheck3);}  
	if(document.getElementById("tu4")){tmid4=document.getElementById("tu4").value;} d4=trans(tmid4);
	if(document.getElementById("biaoti4")){bt4=document.getElementById("biaoti4").value;}
	if(document.getElementById("f1")){check4=document.getElementById("f1").value;} kcheck4=trans1(check4);
	if(document.getElementById("f2")){scheck4=document.getElementById("f2").value;} kscheck4=trans1(scheck4); 
	if(document.getElementById("f3")){dcheck4=document.getElementById("f3").value;} kdcheck4=trans1(dcheck4);  
	if(d4 && check4 && !scheck4 && !dcheck4){out1(d4,kcheck4,"container4",bt4,check4);}
	if(d4 && check4 && scheck4 && !dcheck4){out1(d4,kcheck4,"container4",bt4,check4,kscheck4,scheck4);}
	if(d4 && check4 && scheck4 && dcheck4){out1(d4,kcheck4,"container4",bt4,check4,kscheck4,scheck4,kdcheck4,dcheck4);}
}
//)


function check1(d,j1)
{
	var txt1 ='<input id='+j1+' type="text" style="width: 70%;border-style:none;" onkeyup="'+j1+'lookup(this.value);" onblur="'+j1+'fill();">';
	var x1=j1+'1';var x11=j1+'11';
	txt1 +='<div class="suggestionsBox1" id='+x1+' style="display: none;"> <div class="suggestionList" id='+x11+' > </div> </div>';
	txt1 +='<select name="p1i1type" style="width: 20%;border-style:none;">';
	txt1 +=xuanz1;
	txt1 +='</select>';
	document.getElementById(d).innerHTML=txt1;
}
function check2(d,j1,j2)
{
	var txt1 ='<input id='+j1+' type="text" style="width: 25%;border-style:none;" onkeyup="'+j1+'lookup(this.value);" onblur="'+j1+'fill();">';
	var x1=j1+'1';var x11=j1+'11';
	txt1 +='<div class="suggestionsBox1" id='+x1+' style="display: none;"> <div class="suggestionList" id='+x11+' > </div> </div>';
	txt1 +='<select name="p1i1type" style="width: 20%;border-style:none;">';
	txt1 +=xuanz1;
	txt1 +='</select>'; 
	txt1 +='<input id='+j2+' type="text" style="width: 25%;border-style:none;" onkeyup="'+j2+'lookup(this.value);" onblur="'+j2+'fill();">';
	x2=j2+'2';x22=j2+'22';
	txt1 +='<div class="suggestionsBox2" id='+x2+' style="display: none;"> <div class="suggestionList" id='+x22+' > </div> </div>';
	txt1 +='<select name="p1i1type" style="width: 20%;border-style:none;">';
	txt1 +=xuanz1;
	txt1 +='</select>';
	document.getElementById(d).innerHTML=txt1;
}
function check3(d,j1,j2,j3)
{
	var txt1 ='<input id='+j1+' type="text" style="width: 15%;border-style:none;" onkeyup="'+j1+'lookup(this.value);" onblur="'+j1+'fill();">';
	var x1=j1+'1';var x11=j1+'11';
	txt1 +='<div class="suggestionsBox1" id='+x1+' style="display: none;"> <div class="suggestionList" id='+x11+' > </div> </div>';
	txt1 +='<select name="p1i1type" style="width: 15%;border-style:none;">';
	txt1 +=xuanz1;
	txt1 +='</select>'; 
	txt1 +='<input id='+j2+' type="text" style="width: 15%;border-style:none;" onkeyup="'+j2+'lookup(this.value);" onblur="'+j2+'fill();">';
	x2=j2+'2';x22=j2+'22';
	txt1 +='<div class="suggestionsBox2" id='+x2+' style="display: none;"> <div class="suggestionList" id='+x22+' > </div> </div>';
	txt1 +='<select name="p1i1type" style="width: 15%;border-style:none;">';
	txt1 +=xuanz1;
	txt1 +='</select>'; 
	txt1 +='<input id='+j3+' type="text" style="width: 15%;border-style:none;" onkeyup="'+j3+'lookup(this.value);" onblur="'+j3+'fill();">';
	x3=j3+'3';x33=j3+'33';
	txt1 +='<div class="suggestionsBox3" id='+x3+' style="display: none;"> <div class="suggestionList" id='+x33+' > </div> </div>';
	txt1 +='<select name="p1i1type" style="width: 15%;border-style:none;">';
	txt1 +=xuanz1;
	txt1 +='</select>'; 
	document.getElementById(d).innerHTML=txt1;	
}
function dcheck1(){check1("jt1","d1");}function dcheck2(){check2("jt1","d1","d2");}function dcheck3(){check3("jt1","d1","d2","d3");}
function scheck1(){check1("jt2","s1");}function scheck2(){check2("jt2","s1","s2");}function scheck3(){check3("jt2","s1","s2","s3");}
function tcheck1(){check1("jt3","t1");}function tcheck2(){check2("jt3","t1","t2");}function tcheck3(){check3("jt3","t1","t2","t3");}
function fcheck1(){check1("jt4","f1");}function fcheck2(){check2("jt4","f1","f2");}function fcheck3(){check3("jt4","f1","f2","f3");}


$(document).off('click',"#databgroup1").on('click',"#databgroup1", function(){
	var txt ='<div class="ttext1"  style="background:rgba(14,32,45,1);"><form style="width: 100%;height: 100%;" >';
	txt+='<div id="jt1"></div>';
	txt +='<select id="tu1" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>'; 
	txt +='<input name="biaoti1" id="biaoti1" type="text"  value="图表标题"  onfocus="ClearValue1();" onblur="WriteValue1();"style="color:Gray;width:20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div>'; 
	$("#databside").html(txt);
	myFunction1();dcheck1();

})
$(document).off('click',"#databgroup2").on('click',"#databgroup2", function(){
	var txt ='<div class="ttext1" style="background:rgba(14,32,45,1);"><form style="width: 100%;height: 100%;">';	
	txt+='<div id="jt1"></div>';
	txt +='<select id="tu1" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>'; 
	txt +='<input name="biaoti1" id="biaoti1" type="text" value="图表标题"  onfocus="ClearValue1();" onblur="WriteValue1();"  style="color:Gray;width: 20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div>'; 
	txt +='<div class="ttext1"  style="background:rgba(14,32,45,1);"><form  style="width: 100%;height: 100%;">';
	txt+='<div id="jt2"></div>';
	txt +='<select id="tu2" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>';
	txt +='<input name="biaoti2" id="biaoti2" type="text"  value="图表标题" onfocus="ClearValue2();" onblur="WriteValue2();"  style="color:Gray;width: 20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="scheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="scheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="scheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div>';
 	$("#databside").html(txt);
	myFunction2();dcheck1();scheck1();
})
$(document).off('click',"#databgroup4").on('click',"#databgroup4", function(){
	var txt ='<div class="ttext1"  style="background:rgba(14,32,45,1);"><form style="width: 100%;height: 100%;">';
	txt+='<div id="jt1"></div>';
	txt +='<select id="tu1" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>';
	txt +='<input name="biaoti1" id="biaoti1" type="text"  value="图表标题" onfocus="ClearValue1();" onblur="WriteValue1();"  style="color:Gray;width: 20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value="" onclick="dcheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div>'; 
	txt +='<div class="ttext1" style="background:rgba(14,32,45,1);"><form style="width: 100%;height: 100%;">';
	txt+='<div id="jt2"></div>';
	txt +='<select id="tu2" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>';
	txt +='<input name="biaoti2" id="biaoti2" type="text"  value="图表标题" onfocus="ClearValue2();" onblur="WriteValue2();"  style="color:Gray;width: 20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="scheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="scheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="scheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div><div class="ttext1"  style="background:rgba(14,32,45,1);"><form style="width: 100%;height: 100%;">';
	txt+='<div id="jt3"></div>';
	txt +='<select id="tu3" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>'; 
	txt +='<input name="biaoti3" id="biaoti3" type="text"  value="图表标题" onfocus="ClearValue3();" onblur="WriteValue3();"  style="color:Gray;width: 20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="tcheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="tcheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="tcheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div><div class="ttext1"  style="background:rgba(14,32,45,1);"><form style="width: 100%;height: 100%;">';
	txt	+='<div id="jt4"></div>';
	txt +='<select id="tu4" style="width: 25%;border-style:none;">';
	txt +=tuxing;
	txt +='</select>'; 
	txt +='<input name="biaoti4" id="biaoti4" type="text"  value="图表标题" onfocus="ClearValue4();" onblur="WriteValue4();"  style="color:Gray;width: 20%;border-style:none;"/>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="fcheck3()" style="width: 5%"/>叠加3 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="fcheck2()" style="width: 5%"/>叠加2 </label>';
	txt +='<label style="font-size:90%;"><input name="diejia" type="radio" value=""  onclick="fcheck1()" checked="checked" style="width: 5%"/>不叠加 </label>';
	txt +='</form></div>'; 
	$("#databside").html(txt);
	myFunction3();dcheck1();scheck1();tcheck1();fcheck1();
})

function d1lookup(inputString){
if(inputString.length == 0){
// Hide the suggestion box.
$('#d11').hide();
} else {
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString: ""+inputString+""}, function(data){
if(data.length >0) {
$('#d11').show();
$('#d111').html(data);
}
});
}
}
function d1fill(thisValue) {
$('#d1').val(thisValue);
setTimeout("$('#d11').hide();", 200);
}

function s1lookup(inputString) {
if(inputString.length == 0) {
// Hide the suggestion box.
$('#s11').hide();
} else {
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString2: ""+inputString+""}, function(data){
if(data.length >0) {
$('#s11').show();
$('#s111').html(data);
}
});
}
}//lookup
function s1fill(thisValue){
$('#s1').val(thisValue);
setTimeout("$('#s11').hide();", 200);
}

function t1lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#t11').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString3: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#t11').show(); 
$('#t111').html(data); 
} 
}); 
} 
} // lookup 
function t1fill(thisValue) { 
$('#t1').val(thisValue); 
setTimeout("$('#t11').hide();", 200); 
}  
function f1lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#f11').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString4: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#f11').show(); 
$('#f111').html(data); 
} 
}); 
} 
} // lookup 
function f1fill(thisValue) { 
$('#f1').val(thisValue); 
setTimeout("$('#f11').hide();", 200); 
} 
function d2lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#d22').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString5: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#d22').show(); 
$('#d222').html(data); 
} 
}); 
} 
} 
function d2fill(thisValue) { 
$('#d2').val(thisValue); 
setTimeout("$('#d22').hide();", 200); 
}   
function s2lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#s22').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString6: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#s22').show(); 
$('#s222').html(data); 
} 
}); 
} 
} // lookup 
function s2fill(thisValue) { 
$('#s2').val(thisValue); 
setTimeout("$('#s22').hide();", 200); 
}
function t2lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#t22').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString7: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#t22').show(); 
$('#t222').html(data); 
} 
}); 
} 
} // lookup 
function t2fill(thisValue) { 
$('#t2').val(thisValue); 
setTimeout("$('#t22').hide();", 200); 
}  
function f2lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#f22').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString8: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#f22').show(); 
$('#f222').html(data); 
} 
}); 
} 
} // lookup 
function f2fill(thisValue) { 
$('#f2').val(thisValue); 
setTimeout("$('#f22').hide();", 200); 
}
function d3lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#d33').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString9: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#d33').show(); 
$('#d333').html(data); 
} 
}); 
} 
} 
function d3fill(thisValue) { 
$('#d3').val(thisValue); 
setTimeout("$('#d33').hide();", 200); 
}   
function s3lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#s33').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString10: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#s33').show(); 
$('#s333').html(data); 
} 
}); 
} 
} // lookup 
function s3fill(thisValue) { 
$('#s3').val(thisValue); 
setTimeout("$('#s33').hide();", 200); 
}
function t3lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#t33').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString11: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#t33').show(); 
$('#t333').html(data); 
} 
}); 
} 
} // lookup 
function t3fill(thisValue) { 
$('#t3').val(thisValue); 
setTimeout("$('#t33').hide();", 200); 
}  
function f3lookup(inputString) { 
if(inputString.length == 0) { 
// Hide the suggestion box. 
$('#f33').hide(); 
} else { 
$.post(MServer+"qi/qi00002/qi04635C/mqC.php", {qflag:"databsuggest",queryString12: ""+inputString+""}, function(data){ 
if(data.length >0) { 
$('#f33').show(); 
$('#f333').html(data); 
} 
}); 
} 
} // lookup 
function moren()
{   txt1 ='<img src='+'qi/qi00001/qi04645/momo.gif'+'><br/> <font size="3" face="arial" color="blue"><b>数据正在准备当中...</b></font>';
	document.getElementById("container1").innerHTML=txt1;	
}
function pic1(name1,note1)
{   txt1 ='<img width=800px src="qi/qi00001/qi04645/'+name1+'"><br/> <font size="3" face="arial" color="blue"><b>'+note1+'</b></font>';
	document.getElementById("container1").innerHTML=txt1;	
}
function pic2(name1,note1)
{   txt1 ='<img width=800px src="qi/qi00001/qi04645/'+name1+'"><br/> <font size="3" face="arial" color="blue"><b>'+note1+'</b></font>';
	document.getElementById("container2").innerHTML=txt1;	
}
function pic3(name1,note1)
{   txt1 ='<img width=800px src="qi/qi00001/qi04645/'+name1+'"><br/> <font size="3" face="arial" color="blue"><b>'+note1+'</b></font>';
	document.getElementById("container3").innerHTML=txt1;	
}
function pic4(name1,note1)
{   txt1 ='<img width=800px src="qi/qi00001/qi04645/'+name1+'"><br/> <font size="3" face="arial" color="blue"><b>'+note1+'</b></font>';
	document.getElementById("container4").innerHTML=txt1;	
}

function ltm(demo,pd){
	DashMessage('<iframe src='+pd+' width="100%" height="100%" frameborder="no" border="0" marginwidth="0" marginheight="0"  allowtransparency="yes"></iframe>'+'</div>');
}; 
function out1(sig1,sig2,sig4,sig5,sig8,sig6,sig9,sig7,sig10)
{
	var arr1=[];var arr2=[];var arr3=[];var arr4=[];
				$.ajax({
				url : MServer+"qi/qi00002/qi04635C/mqC.php",
				type : "post",
				async : false, //同步执行
				data : {
				qflag:"databaction",
				action1:sig2,action2:sig6,action3:sig7
			},
			error: function(){  
				alert('11Error loading XML document');  
			},
			//dataType : "json", //返回数据形式为json
			success : function(result){
			if (result) {
				var result =eval(trim(result)); 
			for(var i=0;i<result.length;i++){
				//console.log(result[i].name);
				arr1.push(result[i].times);arr2.push(result[i].close1);arr3.push(result[i].close2);arr4.push(result[i].close3);
			}
		}
	}
})
	eval(sig1+'("'+sig4+'",sig5,arr1,arr2,arr3,arr4,sig8,sig9,sig10)');
}
function f3fill(thisValue) {
$('#f3').val(thisValue);
setTimeout("$('#f33').hide();", 200);
}
function ClearValue1(){
	var txt1=document.getElementById("biaoti1");
	if(txt1.value=="图表标题"){
		document.getElementById("biaoti1").value = "";
		txt1.style.color = "";}
}
function WriteValue1() {
	var txt1=document.getElementById("biaoti1");
	if (txt1.value=="") {
		txt1.value ="图表标题";
		txt1.style.color = "gray";
	}
}
function ClearValue2(){
	var txt2=document.getElementById("biaoti2");
	if(txt2.value=="图表标题"){
		document.getElementById("biaoti2").value = "";
		txt2.style.color = "";}
}
function WriteValue2() {
	var txt2=document.getElementById("biaoti2");
	if (txt2.value=="") {
		txt2.value ="图表标题";
		txt2.style.color = "gray";
	}
}
function ClearValue3(){
	var txt3=document.getElementById("biaoti3");
	if(txt3.value=="图表标题"){
		document.getElementById("biaoti3").value = "";
		txt3.style.color = "";}

}
function WriteValue3(){
	vartxt3=document.getElementById("biaoti3");
	if(txt3.value==""){
	txt3.value	="图表标题";
	txt3.style.color	=	"gray";
	}
}
function ClearValue4(){
var txt4=document.getElementById("biaoti4");
if(txt4.value=="图表标题"){
document.getElementById("biaoti4").value = "";
		txt4.style.color = "";
		}
}
function WriteValue4(){
	var txt4=document.getElementById("biaoti4");
	if (txt4.value=="") {
		txt4.value ="图表标题";
		txt4.style.color = "gray";
	}
}
$(document).off('click',"#mq_top_ul_li_10").on('click',"#mq_top_ul_li_10",function(){
	var xQ3LIB = '<iframe class="mq_main_l_Frame" runat="server" src="./Q3LIB.html?par='+Q14123101+'"></iframe>';
	$("#mq_main").html(xQ3LIB);
	})
	
$(document).off('click',"#mq_top_ul_li_99").on('click',"#mq_top_ul_li_99",function(){
  try {
      // 调用 Python 的方法
      window.pywebview.api.open_test_window(Q14123101);
  } catch (error) {
      console.error('调用失败:', error);
      alert('调用失败：' + error);
  }
    
});
	
$(document).off('click',"#logo-q-char").on('click',"#logo-q-char",function(){
	var xProjective = '<iframe class="mq_main_l_Frame" runat="server" src="./mo/index.html?par='+Q14123101+'"></iframe>';
	$("#mq_main").html(xProjective);
	})
	
$(document).off('click',"#mq_top_ul_li_15").on('click',"#mq_top_ul_li_15",function(){
	var ch010 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch010.html?par='+Q14123101+'"></iframe>';
	$("#mq_main").html(ch010);
	})

//进入实时数据主题
$(document).off("click","#mq_top_ul_li_13").on("click","#mq_top_ul_li_13",function(){
	$("#mq_main").html(mainDiv1);
	$("#mq_main_r1").html(datax3);
	})


$(document).off('click',".jkzbj").on('click',".jkzbj",function(){
	$(".jkzbj").css('background','transparent');
	$(this).css('background','rgba(20,177,235,0.3)');
	var	itName=$(this).attr("name");
	var itAuth=itName+'_04';
	var fAuthority=Authority(Q14123101,itAuth);
	if(fAuthority==1){
		
		if(itName=="ch030"){
			var  xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="http://10.10.98.51:3224/agent"></iframe>';
			$("#mq_main").html(xChannel);
			}
		else if (itName=="ch031"){
			var  xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="http://10.10.98.51:3223/qforge"></iframe>';
			$("#mq_main").html(xChannel);
			}
		else if (itName=="ch032"){
			var  xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="http://10.10.98.51:3222/skills"></iframe>';
			$("#mq_main").html(xChannel);
			}
		else {
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="./'+itName+'.html?par='+Q14123101+'"></iframe>';
			$("#mq_main_l1").html(xChannel);
		}
		
	}
	else{
		NoAuthority(itAuth);
	}
	})

$(document).off('click',"#cpmonthlyreport").on('click',"#cpmonthlyreport",function(){
	$.ajax({
	type: "POST",
	url: MServer+"qi/qi00002/qi04635C/mqC.php",
	data:{
		qflag:"cpmonthlyreport",
		sflag:"_04",
		},
		async:false,
		success: function(_data1){
			//alert(_data1)	;
					$("#mq_main").append('<div id="BG1"><div class="shut"><img src="./assets/images/Close2.png"/></div><center><div id="BGcontentxx" style="width:800px;min-height:500px;height:auto;margin-top:30px;background:#FFFFFF;padding:9px;text-align:left;"></div></center></div>');
					var Zdata = JSON.parse(_data1);
					var tpoint = Zdata[0].split('_')[0];
					var ypoint = Zdata[0].split('_')[1];
					//var tpoint_=tpoint.replaceAll('-','');
					var ypoint_=ypoint.replaceAll('-','');
					var vtxt ='<div id="_toimg" >>>>下载图片>>></div>';
							vtxt+= '<div class="PeriodReport" name="_PeriodReport" id="WeeklyReport">';
							vtxt+='<div class="PeriodReportH">产品月报（<span>'+tpoint.substring(0,7)+'</span>）</div>';
							vtxt+='<div class="_PeriodReportbcolor"><div class="_PeriodReport">本月总结：</div>';
							vtxt+='<div class="PeriodReportM">'+Zdata[1].replace(/&gt;/g,">").replace(/&lt;/g,"<")+'</div></div>';
					    vtxt+='</div>';
					$("#BGcontentxx").css('background','transparent').append(vtxt);
					for(var i=2;i<Zdata.length;i++){

						var datelist = Zdata[i][0];
						var bqlist = Zdata[i][1].map(Number);
						var bilist = Zdata[i][2].map(Number);
						var btext = Zdata[i][3];
						var bqname = btext[0];
						var biname = btext[1];
						var bqcon =  btext[2];
						var bqinitdate = btext[3];
						var bqid = btext[4];
						var bqfhong = btext[5];
						
						var lbq = 1;
						var lbi = 1;
						var mlbq = 1;
						var mlbi = 1;
						var bqhch = 0;
						var bihch = 0 ;
						var bqlist1 = [lbq-1];
						var bilist1 = [lbi-1];
						var cdifsyllist1 =[lbq-lbi];
						var bqhchlist = [bqhch];
						var bihchlist = [bihch];
						var maxbqhch = 0;
						var maxbihch = 0;
						var wlbq = 1;
						var wlbi = 1;
						if(bqfhong.length>5){
							bqfhongdate = bqfhong.split('-')[0];
							bqfhongjzh =  parseFloat(bqfhong.split('-')[1]);
							}else{bqfhongdate ='19900101';bqfhongjzh=1;}
						
						for(var i0=1;i0<datelist.length;i0++){
							if (parseInt(datelist[i0])>parseInt(ypoint_)){
								wlbq = wlbq*(parseFloat(bqlist[i0])+1);
								wlbi = wlbi*(parseFloat(bilist[i0])+1);
								}
							if (parseInt(datelist[i0])>parseInt(bqfhongdate)){
								bqfhongjzh = bqfhongjzh*(parseFloat(bqlist[i0])+1);
								}
								
							lbq = lbq*(parseFloat(bqlist[i0])+1);
							lbi = lbi*(parseFloat(bilist[i0])+1);
							if (lbq>mlbq){mlbq=lbq;}
							if (lbi>mlbi){mlbi=lbi;}
							bqhch = (lbq/mlbq)-1;
							bihch = (lbi/mlbi)-1;
							if (bqhch<maxbqhch){maxbqhch=bqhch;}
							if (bihch<maxbihch){maxbihch=bihch;}
							bqhchlist.push(Math.round(bqhch*10000)/100);
							bihchlist.push(Math.round(bihch*10000)/100);
							bqlist1.push(Math.round((lbq-1)*10000)/100);
							bilist1.push(Math.round((lbi-1)*10000)/100);
							cdifsyllist1.push(Math.round((lbq-1)*10000)/100-Math.round((lbi-1)*10000)/100);
							}
							var wbqsy = Math.round((wlbq-1)*10000)/100;
							var wbisy = Math.round((wlbi-1)*10000)/100;
							var wcsy = Math.round((wbqsy-wbisy)*100)/100;
							
							var startdate = datelist[0];
							var enddate = datelist[datelist.length-1];
							var daydiff = getDaysDiff(new Date(enddate.substr(0,4)+'-'+enddate.substr(4,2)+'-'+enddate.substr(6,2)),new Date(startdate.substr(0,4)+'-'+startdate.substr(4,2)+'-'+startdate.substr(6,2)));
							var bqljsyl = Math.round((lbq-1)*10000)/100;
							var biljsyl = Math.round((lbi-1)*10000)/100;
							var cdifljsyl = Math.round((bqljsyl-biljsyl)*100)/100;
							var bqnhsyl = Math.round((lbq**(365/daydiff)-1)*10000)/100;
							var binhsyl = Math.round((lbi**(365/daydiff)-1)*10000)/100;
							var cdifnhsyl = Math.round((bqnhsyl-binhsyl)*100)/100;
							//var bqdev = Math.round(calculateStandardDeviation(bqlist)*365**0.5*10000)/100;
							//var bidev = Math.round(calculateStandardDeviation(bilist)*365**0.5*10000)/100;
							//var cdifdev = Math.round((bqdev-bidev)*100)/100;
							//var bqsharp = Math.round((bqnhsyl/bqdev)*100)/100;
							//var bisharp = Math.round((binhsyl/bidev)*100)/100;
							//var cdifsharp = Math.round((bqsharp-bisharp)*100)/100;
							//var cdifmaxhch = maxbqhch-maxbihch;
							var maxbqhch = Math.round(maxbqhch*10000)/100;
							var maxbihch = Math.round(maxbihch*10000)/100;
							//var cdifmaxhch = Math.round(cdifmaxhch*10000)/100;
							var sy = 0;
							var bisy = 0;
							var mlbqs = 0;
							var mlbis = 0;
							var bqhchs = 0;
							var bihchs = 0 ;
							var bgMaxDrawdown = 0;
							var biMaxDrawdown = 0;
							var tyear0 = datelist[0].substring(0,4);
							var leijizhi = datelist.length-1;
							for(var i1=1;i1<datelist.length;i1++){
								var tyear1 = datelist[i1].substring(0,4);
								sy = (sy+1)*(1+parseFloat(bqlist[i1]))-1;
								bisy = (bisy+1)*(1+parseFloat(bilist[i1]))-1;
								if (sy>mlbqs){mlbqs=sy;}
								if (bisy>mlbis){mlbis=bisy;}
								bqhchs = ((sy+1)/(mlbqs+1))-1;
								bihchs = ((bisy+1)/(mlbis+1))-1;
								if (bqhchs<bgMaxDrawdown){bgMaxDrawdown=bqhchs;}
								if (bihchs<biMaxDrawdown){biMaxDrawdown=bihchs;}
								if((tyear1!=tyear0 && i>0) || i==leijizhi){
									//sy = Math.round(sy*10000)/100;
									//bisy = Math.round(bisy*10000)/100;
									//bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
									//biMaxDrawdown = Math.round(biMaxDrawdown*10000)/100;
									//txt+='<tr><td>'+tyear0+'</td><td '+rcolor(sy)+'>'+sy+'%</td><td  '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td><td '+rcolor(bisy)+'>'+bisy+'%</td><td  '+rcolor(biMaxDrawdown)+'>'+biMaxDrawdown+'%</td></tr>';
									tyear0 =tyear1;
									sy = parseFloat(bqlist[i1]);
									bisy = parseFloat(bilist[i1]);
									mlbqs = 0;
									mlbis = 0;
									bqhchs = 0;
									bihchs = 0 ;
									bgMaxDrawdown = 0;
									biMaxDrawdown = 0;
									}
								}
						

							sy = Math.round(sy*10000)/100;
							bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
							var stxt ='<div class="PeriodReportDiv">';
									stxt+='<div class="_PeriodReport">策略名称：'+bqname+'</div>';
							    stxt+='<div class="PeriodReportB">';
							    stxt+='<div class="PeriodReportBH">';
							    stxt+=bqcon;
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBB">';
							    stxt+='<div class="PeriodReportBBL">';
							    stxt+='<center><table class="reporttable" style="border-left:0px;">';
							    stxt+='<tr><td>起始时间</td><td>'+bqinitdate+'</td></tr>';
							    stxt+='<tr><td>单位净值</td><td '+rcolor(bqfhongjzh)+'>'+Math.round(bqfhongjzh*10000)/10000+'</td></tr>';
							    stxt+='<tr><td>累计净值</td><td '+rcolor(lbq)+'>'+Math.round(lbq*10000)/10000+'</td></tr>';
							    stxt+='<tr><td>年化收益</td><td '+rcolor(bqnhsyl)+'>'+bqnhsyl+'%</td></tr>';
							    stxt+='<tr><td>业绩基准</td><td>'+biname+'</td></tr>';
							    stxt+='<tr><td>本月收益</td><td '+rcolor(wbqsy)+'>'+wbqsy+'%</td></tr>';
							    stxt+='<tr><td>本月超额</td><td '+rcolor(wcsy)+'>'+wcsy+'%</td></tr>';
							    stxt+='<tr><td>今年收益</td><td '+rcolor(sy)+'>'+sy+'%</td></tr>';
							    stxt+='<tr><td>今年回撤</td><td '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td></tr>';
							    stxt+='<tr><td>最大回撤</td><td '+rcolor(maxbqhch)+'>'+maxbqhch+'%</td></tr>';
							    stxt+='<tr><td>累计超额</td><td '+rcolor(cdifljsyl)+'>'+cdifljsyl+'%</td></tr>';
							    stxt+='</table></center>';
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBBR" id="PeriodReportBBR_'+bqid+'"></div>';
							    stxt+='</div>';
							    stxt+='</div>';
							    $("#WeeklyReport").append(stxt);
							    WeeklyReportGrouph("PeriodReportBBR_"+bqid,datelist,cdifsyllist1,bqhchlist,bqlist1,bilist1,'超额收益','本策略回撤','本策略收益',biname);
								}
			}
		})	

	})
		
$(document).off('click',"#cpweeklyreport").on('click',"#cpweeklyreport",function(){
	$.ajax({
	type: "POST",
	url: MServer+"qi/qi00002/qi04635C/mqC.php",
	data:{
		qflag:"cpweeklyreport",
		sflag:"_04",
		},
		async:false,
		success: function(_data1){
			//alert(_data1)	;
					$("#mq_main").append('<div id="BG1"><div class="shut"><img src="./assets/images/Close2.png"/></div><center><div id="BGcontentxx" style="width:800px;min-height:500px;height:auto;margin-top:30px;background:#FFFFFF;padding:9px;text-align:left;"></div></center></div>');
					var Zdata = JSON.parse(_data1);
					var tpoint = Zdata[0].split('_')[0];
					var ypoint = Zdata[0].split('_')[1];
					//var tpoint_=tpoint.replaceAll('-','');
					var ypoint_=ypoint.replaceAll('-','');
					var vtxt ='<div id="_toimg" >>>>下载图片>>></div>';
							vtxt+='<div class="PeriodReport" name="_PeriodReport" id="WeeklyReport">';
							vtxt+='<div class="PeriodReportH">产品周报（<span>'+tpoint+'</span>）</div>';
							vtxt+='<div class="_PeriodReportbcolor"><div class="_PeriodReport">本周总结：</div>';
							vtxt+='<div class="PeriodReportM">'+Zdata[1].replace(/&gt;/g,">").replace(/&lt;/g,"<")+'</div></div>';
					    vtxt+='</div>';
					$("#BGcontentxx").css('background','transparent').append(vtxt);
					for(var i=2;i<Zdata.length;i++){

						var datelist = Zdata[i][0];
						var bqlist = Zdata[i][1].map(Number);
						var bilist = Zdata[i][2].map(Number);
						var btext = Zdata[i][3];
						var bqname = btext[0];
						var biname = btext[1];
						var bqcon =  btext[2];
						var bqinitdate = btext[3];
						var bqid = btext[4];
						var bqfhong = btext[5];
						
						var lbq = 1;
						var lbi = 1;
						var mlbq = 1;
						var mlbi = 1;
						var bqhch = 0;
						var bihch = 0 ;
						var bqlist1 = [lbq-1];
						var bilist1 = [lbi-1];
						var cdifsyllist1 =[lbq-lbi];
						var bqhchlist = [bqhch];
						var bihchlist = [bihch];
						var maxbqhch = 0;
						var maxbihch = 0;
						var wlbq = 1;
						var wlbi = 1;
						
						if(bqfhong.length>5){
							bqfhongdate = bqfhong.split('-')[0];
							bqfhongjzh =  parseFloat(bqfhong.split('-')[1]);
							}else{bqfhongdate ='19900101';bqfhongjzh=1;}
						
						for(var i0=1;i0<datelist.length;i0++){
							if (parseInt(datelist[i0])>parseInt(ypoint_)){
								wlbq = wlbq*(parseFloat(bqlist[i0])+1);
								wlbi = wlbi*(parseFloat(bilist[i0])+1);
								}
							if (parseInt(datelist[i0])>parseInt(bqfhongdate)){
								bqfhongjzh = bqfhongjzh*(parseFloat(bqlist[i0])+1);
								}
								
							lbq = lbq*(parseFloat(bqlist[i0])+1);
							lbi = lbi*(parseFloat(bilist[i0])+1);
							if (lbq>mlbq){mlbq=lbq;}
							if (lbi>mlbi){mlbi=lbi;}
							bqhch = (lbq/mlbq)-1;
							bihch = (lbi/mlbi)-1;
							if (bqhch<maxbqhch){maxbqhch=bqhch;}
							if (bihch<maxbihch){maxbihch=bihch;}
							bqhchlist.push(Math.round(bqhch*10000)/100);
							bihchlist.push(Math.round(bihch*10000)/100);
							bqlist1.push(Math.round((lbq-1)*10000)/100);
							bilist1.push(Math.round((lbi-1)*10000)/100);
							cdifsyllist1.push(Math.round((lbq-1)*10000)/100-Math.round((lbi-1)*10000)/100);
							}
							var wbqsy = Math.round((wlbq-1)*10000)/100;
							var wbisy = Math.round((wlbi-1)*10000)/100;
							var wcsy = Math.round((wbqsy-wbisy)*100)/100;
							
							var startdate = datelist[0];
							var enddate = datelist[datelist.length-1];
							var daydiff = getDaysDiff(new Date(enddate.substr(0,4)+'-'+enddate.substr(4,2)+'-'+enddate.substr(6,2)),new Date(startdate.substr(0,4)+'-'+startdate.substr(4,2)+'-'+startdate.substr(6,2)));
							var bqljsyl = Math.round((lbq-1)*10000)/100;
							var biljsyl = Math.round((lbi-1)*10000)/100;
							var cdifljsyl = Math.round((bqljsyl-biljsyl)*100)/100;
							var bqnhsyl = Math.round((lbq**(365/daydiff)-1)*10000)/100;
							var binhsyl = Math.round((lbi**(365/daydiff)-1)*10000)/100;
							var cdifnhsyl = Math.round((bqnhsyl-binhsyl)*100)/100;
							//var bqdev = Math.round(calculateStandardDeviation(bqlist)*365**0.5*10000)/100;
							//var bidev = Math.round(calculateStandardDeviation(bilist)*365**0.5*10000)/100;
							//var cdifdev = Math.round((bqdev-bidev)*100)/100;
							//var bqsharp = Math.round((bqnhsyl/bqdev)*100)/100;
							//var bisharp = Math.round((binhsyl/bidev)*100)/100;
							//var cdifsharp = Math.round((bqsharp-bisharp)*100)/100;
							//var cdifmaxhch = maxbqhch-maxbihch;
							var maxbqhch = Math.round(maxbqhch*10000)/100;
							var maxbihch = Math.round(maxbihch*10000)/100;
							//var cdifmaxhch = Math.round(cdifmaxhch*10000)/100;
							var sy = 0;
							var bisy = 0;
							var mlbqs = 0;
							var mlbis = 0;
							var bqhchs = 0;
							var bihchs = 0 ;
							var bgMaxDrawdown = 0;
							var biMaxDrawdown = 0;
							var tyear0 = datelist[0].substring(0,4);
							var leijizhi = datelist.length-1;
							for(var i1=1;i1<datelist.length;i1++){
								var tyear1 = datelist[i1].substring(0,4);
								sy = (sy+1)*(1+parseFloat(bqlist[i1]))-1;
								bisy = (bisy+1)*(1+parseFloat(bilist[i1]))-1;
								if (sy>mlbqs){mlbqs=sy;}
								if (bisy>mlbis){mlbis=bisy;}
								bqhchs = ((sy+1)/(mlbqs+1))-1;
								bihchs = ((bisy+1)/(mlbis+1))-1;
								if (bqhchs<bgMaxDrawdown){bgMaxDrawdown=bqhchs;}
								if (bihchs<biMaxDrawdown){biMaxDrawdown=bihchs;}
								if((tyear1!=tyear0 && i>0) || i==leijizhi){
									//sy = Math.round(sy*10000)/100;
									//bisy = Math.round(bisy*10000)/100;
									//bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
									//biMaxDrawdown = Math.round(biMaxDrawdown*10000)/100;
									//txt+='<tr><td>'+tyear0+'</td><td '+rcolor(sy)+'>'+sy+'%</td><td  '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td><td '+rcolor(bisy)+'>'+bisy+'%</td><td  '+rcolor(biMaxDrawdown)+'>'+biMaxDrawdown+'%</td></tr>';
									tyear0 =tyear1;
									sy = parseFloat(bqlist[i1]);
									bisy = parseFloat(bilist[i1]);
									mlbqs = 0;
									mlbis = 0;
									bqhchs = 0;
									bihchs = 0 ;
									bgMaxDrawdown = 0;
									biMaxDrawdown = 0;
									}
								}
						

							sy = Math.round(sy*10000)/100;
							bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
							var stxt ='<div class="PeriodReportDiv">';
									stxt+='<div class="_PeriodReport">策略名称：'+bqname+'</div>';
							    stxt+='<div class="PeriodReportB">';
							    stxt+='<div class="PeriodReportBH">';
							    stxt+=bqcon;
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBB">';
							    stxt+='<div class="PeriodReportBBL">';
							    stxt+='<center><table class="reporttable" style="border-left:0px;">';
							    stxt+='<tr><td>起始时间</td><td>'+bqinitdate+'</td></tr>';
							    stxt+='<tr><td>单位净值</td><td '+rcolor(bqfhongjzh)+'>'+Math.round(bqfhongjzh*10000)/10000+'</td></tr>';
							    stxt+='<tr><td>累计净值</td><td '+rcolor(lbq)+'>'+Math.round(lbq*10000)/10000+'</td></tr>';
							    stxt+='<tr><td>年化收益</td><td '+rcolor(bqnhsyl)+'>'+bqnhsyl+'%</td></tr>';
							    stxt+='<tr><td>业绩基准</td><td>'+biname+'</td></tr>';
							    stxt+='<tr><td>本周收益</td><td '+rcolor(wbqsy)+'>'+wbqsy+'%</td></tr>';
							    stxt+='<tr><td>本周超额</td><td '+rcolor(wcsy)+'>'+wcsy+'%</td></tr>';
							    stxt+='<tr><td>今年收益</td><td '+rcolor(sy)+'>'+sy+'%</td></tr>';
							    stxt+='<tr><td>今年回撤</td><td '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td></tr>';
							    stxt+='<tr><td>最大回撤</td><td '+rcolor(maxbqhch)+'>'+maxbqhch+'%</td></tr>';
							    stxt+='<tr><td>累计超额</td><td '+rcolor(cdifljsyl)+'>'+cdifljsyl+'%</td></tr>';
							    stxt+='</table></center>';
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBBR" id="PeriodReportBBR_'+bqid+'"></div>';
							    stxt+='</div>';
							    stxt+='</div>';
							    $("#WeeklyReport").append(stxt);
							    WeeklyReportGrouph("PeriodReportBBR_"+bqid,datelist,cdifsyllist1,bqhchlist,bqlist1,bilist1,'超额收益','本策略回撤','本策略收益',biname);
								}
			}
		})
		
	})
	
$(document).off('click',"#cpdailyreport").on('click',"#cpdailyreport",function(){		
	$.ajax({
	type: "POST",
	url: MServer+"qi/qi00002/qi04635C/mqC.php",
	data:{
		qflag:"cpdailyreport",
		sflag:"_04",
		},
		async:false,
		success: function(_data1){
			//alert(_data1);
					$("#mq_main").append('<div id="BG1"><div class="shut"><img src="./assets/images/Close2.png"/></div><center><div id="BGcontentxx" style="width:800px;min-height:500px;height:auto;margin-top:30px;background:#FFFFFF;padding:9px;text-align:left;"></div></center></div>');
					var Zdata = JSON.parse(_data1);
					var vtxt ='<div id="_toimg" >>>>下载图片>>></div>';
							vtxt+='<center><table class="PeriodReportD" name="_PeriodReport" style="background:#101010;">';
					    vtxt+='<tr><th>日期</th><th style="width:200px;">名称</th><th>基准</th><th>单日收益</th><th>基准收益</th><th>超额收益</th></tr>';
							for(var i=0;i<Zdata.length;i++){
								vtxt+='<tr class="PeriodReportStr"><td>'+Zdata[i][0]+'</td><td>'+Zdata[i][1]+'</td><td>'+Zdata[i][2]+'</td><td '+rcolor(Zdata[i][3])+'>'+Math.round(Zdata[i][3]*10000)/100+'%</td><td '+rcolor(Zdata[i][4])+'>'+Math.round(Zdata[i][4]*10000)/100+'%</td><td '+rcolor(Zdata[i][5])+'>'+Math.round(Zdata[i][5]*10000)/100+'%</td></tr>';
								}
							vtxt+='</table></center>';
					$("#BGcontentxx").css('background','transparent').append(vtxt);
			}
		});
		
	})
	
$(document).off('click',"#cqmonthlyreport").on('click',"#cqmonthlyreport",function(){
	
	$.ajax({
	type: "POST",
	url: MServer+"qi/qi00002/qi04635C/mqC.php",
	data:{
		qflag:"cqmonthlyreport",
		sflag:"_04",
		},
		async:false,
		success: function(_data1){
			//alert(_data1)	;
					$("#mq_main").append('<div id="BG1"><div class="shut"><img src="./assets/images/Close2.png"/></div><center><div id="BGcontentxx" style="width:800px;min-height:500px;height:auto;margin-top:30px;background:#FFFFFF;padding:9px;text-align:left;"></div></center></div>');
					var Zdata = JSON.parse(_data1);
					var tpoint = Zdata[0].split('_')[0];
					var ypoint = Zdata[0].split('_')[1];
					//var tpoint_=tpoint.replaceAll('-','');
					var ypoint_=ypoint.replaceAll('-','');
					var vtxt ='<div id="_toimg" >>>>下载图片>>></div>';
							vtxt+= '<div class="PeriodReport" name="_PeriodReport" id="WeeklyReport">';
							vtxt+='<div class="PeriodReportH">量化策略月报（<span>'+tpoint.substring(0,7)+'</span>）</div>';
							vtxt+='<div class="_PeriodReportbcolor"><div class="_PeriodReport">本月总结：</div>';
							vtxt+='<div class="PeriodReportM">'+Zdata[1].replace(/&gt;/g,">").replace(/&lt;/g,"<")+'</div></div>';
					    vtxt+='</div>';
					$("#BGcontentxx").css('background','transparent').append(vtxt);
					for(var i=2;i<Zdata.length;i++){

						var datelist = Zdata[i][0];
						var bqlist = Zdata[i][1].map(Number);
						var bilist = Zdata[i][2].map(Number);
						var btext = Zdata[i][3];
						var bqname = btext[0];
						var biname = btext[1];
						var bqcon =  btext[2];
						var bqinitdate = btext[3];
						var bqid = btext[4];
						
						var lbq = 1;
						var lbi = 1;
						var mlbq = 1;
						var mlbi = 1;
						var bqhch = 0;
						var bihch = 0 ;
						var bqlist1 = [lbq-1];
						var bilist1 = [lbi-1];
						var cdifsyllist1 =[lbq-lbi];
						var bqhchlist = [bqhch];
						var bihchlist = [bihch];
						var maxbqhch = 0;
						var maxbihch = 0;
						var wlbq = 1;
						var wlbi = 1;
						for(var i0=1;i0<datelist.length;i0++){
							if (parseInt(datelist[i0])>parseInt(ypoint_)){
								wlbq = wlbq*(parseFloat(bqlist[i0])+1);
								wlbi = wlbi*(parseFloat(bilist[i0])+1);
								}
							lbq = lbq*(parseFloat(bqlist[i0])+1);
							lbi = lbi*(parseFloat(bilist[i0])+1);
							if (lbq>mlbq){mlbq=lbq;}
							if (lbi>mlbi){mlbi=lbi;}
							bqhch = (lbq/mlbq)-1;
							bihch = (lbi/mlbi)-1;
							if (bqhch<maxbqhch){maxbqhch=bqhch;}
							if (bihch<maxbihch){maxbihch=bihch;}
							bqhchlist.push(Math.round(bqhch*10000)/100);
							bihchlist.push(Math.round(bihch*10000)/100);
							bqlist1.push(Math.round((lbq-1)*10000)/100);
							bilist1.push(Math.round((lbi-1)*10000)/100);
							cdifsyllist1.push(Math.round((lbq-1)*10000)/100-Math.round((lbi-1)*10000)/100);
							}
							var wbqsy = Math.round((wlbq-1)*10000)/100;
							var wbisy = Math.round((wlbi-1)*10000)/100;
							var wcsy = Math.round((wbqsy-wbisy)*100)/100;
							
							var startdate = datelist[0];
							var enddate = datelist[datelist.length-1];
							var daydiff = getDaysDiff(new Date(enddate.substr(0,4)+'-'+enddate.substr(4,2)+'-'+enddate.substr(6,2)),new Date(startdate.substr(0,4)+'-'+startdate.substr(4,2)+'-'+startdate.substr(6,2)));
							var bqljsyl = Math.round((lbq-1)*10000)/100;
							var biljsyl = Math.round((lbi-1)*10000)/100;
							var cdifljsyl = Math.round((bqljsyl-biljsyl)*100)/100;
							var bqnhsyl = Math.round((lbq**(365/daydiff)-1)*10000)/100;
							var binhsyl = Math.round((lbi**(365/daydiff)-1)*10000)/100;
							var cdifnhsyl = Math.round((bqnhsyl-binhsyl)*100)/100;
							//var bqdev = Math.round(calculateStandardDeviation(bqlist)*365**0.5*10000)/100;
							//var bidev = Math.round(calculateStandardDeviation(bilist)*365**0.5*10000)/100;
							//var cdifdev = Math.round((bqdev-bidev)*100)/100;
							//var bqsharp = Math.round((bqnhsyl/bqdev)*100)/100;
							//var bisharp = Math.round((binhsyl/bidev)*100)/100;
							//var cdifsharp = Math.round((bqsharp-bisharp)*100)/100;
							//var cdifmaxhch = maxbqhch-maxbihch;
							var maxbqhch = Math.round(maxbqhch*10000)/100;
							var maxbihch = Math.round(maxbihch*10000)/100;
							//var cdifmaxhch = Math.round(cdifmaxhch*10000)/100;
							var sy = 0;
							var bisy = 0;
							var mlbqs = 0;
							var mlbis = 0;
							var bqhchs = 0;
							var bihchs = 0 ;
							var bgMaxDrawdown = 0;
							var biMaxDrawdown = 0;
							var tyear0 = datelist[0].substring(0,4);
							var leijizhi = datelist.length-1;
							for(var i1=1;i1<datelist.length;i1++){
								var tyear1 = datelist[i1].substring(0,4);
								sy = (sy+1)*(1+parseFloat(bqlist[i1]))-1;
								bisy = (bisy+1)*(1+parseFloat(bilist[i1]))-1;
								if (sy>mlbqs){mlbqs=sy;}
								if (bisy>mlbis){mlbis=bisy;}
								bqhchs = ((sy+1)/(mlbqs+1))-1;
								bihchs = ((bisy+1)/(mlbis+1))-1;
								if (bqhchs<bgMaxDrawdown){bgMaxDrawdown=bqhchs;}
								if (bihchs<biMaxDrawdown){biMaxDrawdown=bihchs;}
								if((tyear1!=tyear0 && i>0) || i==leijizhi){
									//sy = Math.round(sy*10000)/100;
									//bisy = Math.round(bisy*10000)/100;
									//bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
									//biMaxDrawdown = Math.round(biMaxDrawdown*10000)/100;
									//txt+='<tr><td>'+tyear0+'</td><td '+rcolor(sy)+'>'+sy+'%</td><td  '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td><td '+rcolor(bisy)+'>'+bisy+'%</td><td  '+rcolor(biMaxDrawdown)+'>'+biMaxDrawdown+'%</td></tr>';
									tyear0 =tyear1;
									sy = parseFloat(bqlist[i1]);
									bisy = parseFloat(bilist[i1]);
									mlbqs = 0;
									mlbis = 0;
									bqhchs = 0;
									bihchs = 0 ;
									bgMaxDrawdown = 0;
									biMaxDrawdown = 0;
									}
								}
						

							sy = Math.round(sy*10000)/100;
							bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
							var stxt ='<div class="PeriodReportDiv">';
									stxt+='<div class="_PeriodReport">策略名称：'+bqname+'</div>';
							    stxt+='<div class="PeriodReportB">';
							    stxt+='<div class="PeriodReportBH">';
							    stxt+=bqcon;
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBB">';
							    stxt+='<div class="PeriodReportBBL">';
							    stxt+='<center><table class="reporttable" style="border-left:0px;">';
							    stxt+='<tr><td>起始时间</td><td>'+bqinitdate+'</td></tr>';
							    stxt+='<tr><td>累计净值</td><td '+rcolor(lbq)+'>'+Math.round(lbq*10000)/10000+'</td></tr>';
							    stxt+='<tr><td>年化收益</td><td '+rcolor(bqnhsyl)+'>'+bqnhsyl+'%</td></tr>';
							    stxt+='<tr><td>业绩基准</td><td>'+biname+'</td></tr>';
							    stxt+='<tr><td>本月收益</td><td '+rcolor(wbqsy)+'>'+wbqsy+'%</td></tr>';
							    stxt+='<tr><td>本月超额</td><td '+rcolor(wcsy)+'>'+wcsy+'%</td></tr>';
							    stxt+='<tr><td>今年收益</td><td '+rcolor(sy)+'>'+sy+'%</td></tr>';
							    stxt+='<tr><td>今年回撤</td><td '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td></tr>';
							    stxt+='<tr><td>最大回撤</td><td '+rcolor(maxbqhch)+'>'+maxbqhch+'%</td></tr>';
							    stxt+='<tr><td>累计超额</td><td '+rcolor(cdifljsyl)+'>'+cdifljsyl+'%</td></tr>';
							    stxt+='</table></center>';
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBBR" id="PeriodReportBBR_'+bqid+'"></div>';
							    stxt+='</div>';
							    stxt+='</div>';
							    $("#WeeklyReport").append(stxt);
							    WeeklyReportGrouph("PeriodReportBBR_"+bqid,datelist,cdifsyllist1,bqhchlist,bqlist1,bilist1,'超额收益','本策略回撤','本策略收益',biname);
								}
			}
		})
		
	})
		
$(document).off('click',"#cqweeklyreport").on('click',"#cqweeklyreport",function(){
	$.ajax({
	type: "POST",
	url: MServer+"qi/qi00002/qi04635C/mqC.php",
	data:{
		qflag:"cqweeklyreport",
		sflag:"_04",
		},
		async:false,
		success: function(_data1){
			//alert(_data1)	;
					$("#mq_main").append('<div id="BG1"><div class="shut"><img src="./assets/images/Close2.png"/></div><center><div id="BGcontentxx" style="width:800px;min-height:500px;height:auto;margin-top:30px;background:#FFFFFF;padding:9px;text-align:left;"></div></center></div>');
					var Zdata = JSON.parse(_data1);
					var tpoint = Zdata[0].split('_')[0];
					var ypoint = Zdata[0].split('_')[1];
					//var tpoint_=tpoint.replaceAll('-','');
					var ypoint_=ypoint.replaceAll('-','');
					var vtxt ='<div id="_toimg" >>>>下载图片>>></div>';
							vtxt+= '<div class="PeriodReport" name="_PeriodReport" id="WeeklyReport">';
							vtxt+='<div class="PeriodReportH">量化策略周报（<span>'+tpoint+'</span>）</div>';
							vtxt+='<div class="_PeriodReportbcolor"><div class="_PeriodReport">本周日志：</div>';
							vtxt+='<div class="PeriodReportM">'+Zdata[1].replace(/&gt;/g,">").replace(/&lt;/g,"<")+'</div></div>';
					    vtxt+='</div>';
					$("#BGcontentxx").css('background','transparent').append(vtxt);
					for(var i=2;i<Zdata.length;i++){

						var datelist = Zdata[i][0];
						var bqlist = Zdata[i][1].map(Number);
						var bilist = Zdata[i][2].map(Number);
						var btext = Zdata[i][3];
						var bqname = btext[0];
						var biname = btext[1];
						var bqcon =  btext[2];
						var bqinitdate = btext[3];
						var bqid = btext[4];
						
						var lbq = 1;
						var lbi = 1;
						var mlbq = 1;
						var mlbi = 1;
						var bqhch = 0;
						var bihch = 0 ;
						var bqlist1 = [lbq-1];
						var bilist1 = [lbi-1];
						var cdifsyllist1 =[lbq-lbi];
						var bqhchlist = [bqhch];
						var bihchlist = [bihch];
						var maxbqhch = 0;
						var maxbihch = 0;
						var wlbq = 1;
						var wlbi = 1;
						for(var i0=1;i0<datelist.length;i0++){
							if (parseInt(datelist[i0])>parseInt(ypoint_)){
								wlbq = wlbq*(parseFloat(bqlist[i0])+1);
								wlbi = wlbi*(parseFloat(bilist[i0])+1);
								}
							lbq = lbq*(parseFloat(bqlist[i0])+1);
							lbi = lbi*(parseFloat(bilist[i0])+1);
							if (lbq>mlbq){mlbq=lbq;}
							if (lbi>mlbi){mlbi=lbi;}
							bqhch = (lbq/mlbq)-1;
							bihch = (lbi/mlbi)-1;
							if (bqhch<maxbqhch){maxbqhch=bqhch;}
							if (bihch<maxbihch){maxbihch=bihch;}
							bqhchlist.push(Math.round(bqhch*10000)/100);
							bihchlist.push(Math.round(bihch*10000)/100);
							bqlist1.push(Math.round((lbq-1)*10000)/100);
							bilist1.push(Math.round((lbi-1)*10000)/100);
							cdifsyllist1.push(Math.round((lbq-1)*10000)/100-Math.round((lbi-1)*10000)/100);
							}
							var wbqsy = Math.round((wlbq-1)*10000)/100;
							var wbisy = Math.round((wlbi-1)*10000)/100;
							var wcsy = Math.round((wbqsy-wbisy)*100)/100;
							
							var startdate = datelist[0];
							var enddate = datelist[datelist.length-1];
							var daydiff = getDaysDiff(new Date(enddate.substr(0,4)+'-'+enddate.substr(4,2)+'-'+enddate.substr(6,2)),new Date(startdate.substr(0,4)+'-'+startdate.substr(4,2)+'-'+startdate.substr(6,2)));
							var bqljsyl = Math.round((lbq-1)*10000)/100;
							var biljsyl = Math.round((lbi-1)*10000)/100;
							var cdifljsyl = Math.round((bqljsyl-biljsyl)*100)/100;
							var bqnhsyl = Math.round((lbq**(365/daydiff)-1)*10000)/100;
							var binhsyl = Math.round((lbi**(365/daydiff)-1)*10000)/100;
							var cdifnhsyl = Math.round((bqnhsyl-binhsyl)*100)/100;
							//var bqdev = Math.round(calculateStandardDeviation(bqlist)*365**0.5*10000)/100;
							//var bidev = Math.round(calculateStandardDeviation(bilist)*365**0.5*10000)/100;
							//var cdifdev = Math.round((bqdev-bidev)*100)/100;
							//var bqsharp = Math.round((bqnhsyl/bqdev)*100)/100;
							//var bisharp = Math.round((binhsyl/bidev)*100)/100;
							//var cdifsharp = Math.round((bqsharp-bisharp)*100)/100;
							//var cdifmaxhch = maxbqhch-maxbihch;
							var maxbqhch = Math.round(maxbqhch*10000)/100;
							var maxbihch = Math.round(maxbihch*10000)/100;
							//var cdifmaxhch = Math.round(cdifmaxhch*10000)/100;
							var sy = 0;
							var bisy = 0;
							var mlbqs = 0;
							var mlbis = 0;
							var bqhchs = 0;
							var bihchs = 0 ;
							var bgMaxDrawdown = 0;
							var biMaxDrawdown = 0;
							var tyear0 = datelist[0].substring(0,4);
							var leijizhi = datelist.length-1;
							for(var i1=1;i1<datelist.length;i1++){
								var tyear1 = datelist[i1].substring(0,4);
								sy = (sy+1)*(1+parseFloat(bqlist[i1]))-1;
								bisy = (bisy+1)*(1+parseFloat(bilist[i1]))-1;
								if (sy>mlbqs){mlbqs=sy;}
								if (bisy>mlbis){mlbis=bisy;}
								bqhchs = ((sy+1)/(mlbqs+1))-1;
								bihchs = ((bisy+1)/(mlbis+1))-1;
								if (bqhchs<bgMaxDrawdown){bgMaxDrawdown=bqhchs;}
								if (bihchs<biMaxDrawdown){biMaxDrawdown=bihchs;}
								if((tyear1!=tyear0 && i>0) || i==leijizhi){
									//sy = Math.round(sy*10000)/100;
									//bisy = Math.round(bisy*10000)/100;
									//bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
									//biMaxDrawdown = Math.round(biMaxDrawdown*10000)/100;
									//txt+='<tr><td>'+tyear0+'</td><td '+rcolor(sy)+'>'+sy+'%</td><td  '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td><td '+rcolor(bisy)+'>'+bisy+'%</td><td  '+rcolor(biMaxDrawdown)+'>'+biMaxDrawdown+'%</td></tr>';
									tyear0 =tyear1;
									sy = parseFloat(bqlist[i1]);
									bisy = parseFloat(bilist[i1]);
									mlbqs = 0;
									mlbis = 0;
									bqhchs = 0;
									bihchs = 0 ;
									bgMaxDrawdown = 0;
									biMaxDrawdown = 0;
									}
								}
						

							sy = Math.round(sy*10000)/100;
							bgMaxDrawdown = Math.round(bgMaxDrawdown*10000)/100;
							var stxt ='<div class="PeriodReportDiv">';
									stxt+='<div class="_PeriodReport">策略名称：'+bqname+'</div>';
							    stxt+='<div class="PeriodReportB">';
							    stxt+='<div class="PeriodReportBH">';
							    stxt+=bqcon;
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBB">';
							    stxt+='<div class="PeriodReportBBL">';
							    stxt+='<center><table class="reporttable" style="border-left:0px;">';
							    stxt+='<tr><td>起始时间</td><td>'+bqinitdate+'</td></tr>';
							    stxt+='<tr><td>累计净值</td><td '+rcolor(lbq)+'>'+Math.round(lbq*10000)/10000+'</td></tr>';
							    stxt+='<tr><td>年化收益</td><td '+rcolor(bqnhsyl)+'>'+bqnhsyl+'%</td></tr>';
							    stxt+='<tr><td>业绩基准</td><td>'+biname+'</td></tr>';
							    stxt+='<tr><td>本周收益</td><td '+rcolor(wbqsy)+'>'+wbqsy+'%</td></tr>';
							    stxt+='<tr><td>本周超额</td><td '+rcolor(wcsy)+'>'+wcsy+'%</td></tr>';
							    stxt+='<tr><td>今年收益</td><td '+rcolor(sy)+'>'+sy+'%</td></tr>';
							    stxt+='<tr><td>今年回撤</td><td '+rcolor(bgMaxDrawdown)+'>'+bgMaxDrawdown+'%</td></tr>';
							    stxt+='<tr><td>最大回撤</td><td '+rcolor(maxbqhch)+'>'+maxbqhch+'%</td></tr>';
							    stxt+='<tr><td>累计超额</td><td '+rcolor(cdifljsyl)+'>'+cdifljsyl+'%</td></tr>';
							    stxt+='</table></center>';
							    stxt+='</div>';
							    stxt+='<div class="PeriodReportBBR" id="PeriodReportBBR_'+bqid+'"></div>';
							    stxt+='</div>';
							    stxt+='</div>';
							    $("#WeeklyReport").append(stxt);
							    WeeklyReportGrouph("PeriodReportBBR_"+bqid,datelist,cdifsyllist1,bqhchlist,bqlist1,bilist1,'超额收益','本策略回撤','本策略收益',biname);
								}		
			}
		})
	})	
		
$(document).off('click',"#cqdailyreport").on('click',"#cqdailyreport",function(){
	$.ajax({
	type: "POST",
	url: MServer+"qi/qi00002/qi04635C/mqC.php",
	data:{
		qflag:"cqdailyreport",
		sflag:"_04",
		},
		async:false,
		success: function(_data1){
					$("#mq_main").append('<div id="BG1"><div class="shut"><img src="./assets/images/Close2.png"/></div><center><div id="BGcontentxx" style="width:800px;min-height:500px;height:auto;margin-top:30px;background:#FFFFFF;padding:9px;text-align:left;"></div></center></div>');
					var Zdata = JSON.parse(_data1);
					var vtxt ='<div id="_toimg" >>>>下载图片>>></div>';
							vtxt+='<center><table class="PeriodReportD" name="_PeriodReport" style="background:#101010;">';
					    vtxt+='<tr><th>日期</th><th style="width:200px;">名称</th><th>基准</th><th>单日收益</th><th>基准收益</th><th>超额收益</th></tr>';
							for(var i=0;i<Zdata.length;i++){
								vtxt+='<tr class="PeriodReportStr"><td>'+Zdata[i][0]+'</td><td>'+Zdata[i][1]+'</td><td>'+Zdata[i][2]+'</td><td '+rcolor(Zdata[i][3])+'>'+Math.round(Zdata[i][3]*10000)/100+'%</td><td '+rcolor(Zdata[i][4])+'>'+Math.round(Zdata[i][4]*10000)/100+'%</td><td '+rcolor(Zdata[i][5])+'>'+Math.round(Zdata[i][5]*10000)/100+'%</td></tr>';
								}
							vtxt+='</table></center>';
					$("#BGcontentxx").css('background','transparent').append(vtxt);

			}
		});
	})	
//双击删除指定产品的报告
$(document).off('dblclick',".PeriodReportDiv").on('dblclick',".PeriodReportDiv",function(){$(this).remove();})
$(document).off('dblclick',".PeriodReportStr").on('dblclick',".PeriodReportStr",function(){$(this).remove();})


/*
//下载方法
function savePic(base64) {
	var arr = base64.split(',');
	var bytes = atob(arr[1]);
	let ab = new ArrayBuffer(bytes.length);
	let ia = new Uint8Array(ab);
	for (let i = 0; i < bytes.length; i++) {
		ia[i] = bytes.charCodeAt(i);
	}
	var blob = new Blob([ab], { type: 'application/octet-stream' });
	var url = URL.createObjectURL(blob);
	var a = document.createElement('a');
	a.href = url;
	a.download = new Date().valueOf() + ".png";
	var e = document.createEvent('MouseEvents');
	e.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
	a.dispatchEvent(e);
	URL.revokeObjectURL(url);
}
*/

function savePic(base64) {
    // 检查是否在 pywebview 环境中
    if (typeof window.pywebview !== 'undefined' && window.pywebview.api) {
        // 在 pywebview 中，将 base64 传递给 Python 处理
        window.pywebview.api.download_image(base64);
    } else {
        // 普通浏览器环境，保持原有逻辑
        var arr = base64.split(',');
        var bytes = atob(arr[1]);
        let ab = new ArrayBuffer(bytes.length);
        let ia = new Uint8Array(ab);
        for (let i = 0; i < bytes.length; i++) {
            ia[i] = bytes.charCodeAt(i);
        }
        var blob = new Blob([ab], { type: 'application/octet-stream' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = new Date().valueOf() + ".png";
        var e = document.createEvent('MouseEvents');
        e.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
        a.dispatchEvent(e);
        URL.revokeObjectURL(url);
    }
}



//下载图片
$(document).off('click',"#_toimg").on('click',"#_toimg",function(){
	$.getScript("./js/html2canvas.min.js",function(){
		html2canvas(document.querySelector('[name="_PeriodReport"]')).then(canvas => {
			document.body.appendChild(canvas)
			let imageURL = canvas.toDataURL("image/png");    //canvas转base64图片
			savePic(imageURL);
			document.body.removeChild(canvas)
			});
		});
	})
	

	
//策略监控右侧上下div展示比例操作
$(document).off('click',"#UPDOWN").on('click',"#UPDOWN",function(){
	if($("#mq_main_ljBRD").height()>$("#mq_main_ljBRB").height()){
		//$("#mq_main_ljBRD").css('height','30%');
		$("#mq_main_ljBRD").html('');
		$("#mq_main_ljBRB").css({'height':'100%','display':'inline'});
		$(".Mod_kuang").css('height','161px');
		//$(".Mcontainer").css('height','161px');
		$(".McontainerTopic").css({'height':'20px','font-size':'14px'});
		$("#ToStop").css('display','none');
		$("#ToRight").css('display','none');
		$("#ToLeft").css('display','none');
		$("#UPDOWN").css('transform','rotate(180deg)');
	}
	else	{
		//$("#mq_main_ljBRD").css('height','70%');
		$("#mq_main_ljBRB").css({'height':'150px','display':'flex'});
		$(".Mod_kuang").css('height','150px');
		//$(".Mcontainer").css('height','145px');
		$(".McontainerTopic").css({'height':'4px','font-size':'0px'});
		$("#ToStop").css('display','block');
		$("#ToRight").css('display','block');
		$("#ToLeft").css('display','block');
		$("#UPDOWN").css('transform','rotate(360deg)');
		}
	})

//warnmessage的确定按钮
$(document).off('click',"#Yes").on('click',"#Yes",function(){
			$(this).parent().parent().remove();
		})
	
$(document).off('click',".Mcontainer").on('click',".Mcontainer",function(){
	$(".Mcontainer").css('background','transparent');
	$(this).css('background','rgba(255,255,255,0.1)');
	})
	
$(document).off('click',"#ToStop").on('click',"#ToStop",function(){
	if(isPushDash==0){
		isPushDash=1;
		WarnMessage('开始动态播放！');
		$(document).off('click',"#Yes").on('click',"#Yes",function(){
			$(this).parent().parent().remove();
		})
		}
	else if (isPushDash==1){
		isPushDash=0;
		WarnMessage('关闭动态播放！');
		$(document).off('click',"#Yes").on('click',"#Yes",function(){
			$(this).parent().parent().remove();
		})
		}
	})

$(document).off('click',"#ToLeft").on('click',"#ToLeft",function(){
	 	var $firstElement = $('#mq_main_ljBRB').children().last(); // 获取第一个元素
    $firstElement.detach(); // 移除元素但不删除
    $('#mq_main_ljBRB').prepend($firstElement); // 将元素添加到div的末尾
	})

$(document).off('click',"#ToRight").on('click',"#ToRight",function(){
	 	var $firstElement = $('#mq_main_ljBRB').children().first(); // 获取第一个元素
    $firstElement.detach(); // 移除元素但不删除
    $('#mq_main_ljBRB').append($firstElement); // 将元素添加到div的末尾
	})
//市场概况
$(document).off('click',"#xLcontainer1").on('click',"#xLcontainer1",function(){
	var ch022 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch022.html?par='+Q14123101+'"></iframe>';
	$("#mq_main_ljBRD").html(ch022);
	})


//策略跟踪
$(document).off('click',"#xLcontainer2").on('click',"#xLcontainer2",function(){
	var ch021 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch021.html?par='+Q14123101+'"></iframe>';
	$("#mq_main_ljBRD").html(ch021);
	})
//投研相关
$(document).off('click',"#xLcontainer4").on('click',"#xLcontainer4",function(){
	var ch019 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch019.html?par='+Q14123101+'"></iframe>';
	$("#mq_main_ljBRD").html(ch019);
	})
//组织结构
$(document).off('click',"#xLcontainer8").on('click',"#xLcontainer8",function(){
	var ch015 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch015.html?par='+Q14123101+'"></iframe>';
	$("#mq_main_ljBRD").html(ch015);
	})

//账户跟踪
$(document).off('click',"#xLcontainer9").on('click',"#xLcontainer9",function(){
	var ch023 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch023.html?par='+Q14123101+'"></iframe>';
	$("#mq_main_ljBRD").html(ch023);
	})
//风险控制
$(document).off('click',"#xLcontainer10").on('click',"#xLcontainer10",function(){
	var ch024 = '<iframe class="mq_main_l_Frame" runat="server" src="./ch024.html?par='+Q14123101+'"></iframe>';
	$("#mq_main_ljBRD").html(ch024);
	})	
	