;
//名称:mq.js --编写：曲如意 --编写日期???2024-12-15
//提交???01；修改：03；删除：02；查询：04；执行：05???

//用户???
// 获取当前页面的URL参数
const params = new URLSearchParams(window.location.search);
// 获取指定参数的???
Q14123101 = params.get('par');
//alert(Q14123101);
//server
var MServer = "http://10.10.98.51/test/sys/";
//用户具备的权???
var	UserAuthority=[];
//用户操作的痕迹记???
var	UserNote={};
//当前页面的主???
var NowTopic = 'ModelLiveSvr4';
//系统监控服务???
var mpushserver3 = '10.10.98.51:3213';
//行情服务器连???
var smsocket3 = io.connect(mpushserver3);
//获取策略服务器消息集???
var quantmess= new Set();
//获取交易服务器消息集???
var clientmess= new Set();
var x1=[];
var x2=[];
var x3=[];

//策略监控页面数据推送是否动态展现相关面???,默认为不展示
var isPushDash=0;

//警示消息列表
var	WarnMessageList=[
	"你尚未开通这个模块的权限???",
	"请输入查询对象！",
	"请在上方报表中选择申请变量???",
	"还没有构建模型！",
	"登陆成功???",
	"注销成功???",
	"用户名已存在???",
	"提交失败，请重新提交???",
	"购买成功???", 
	"你的金币不足???",
	"!",
	"你还没有选择项目???",
	"此项没有内容???",
	"停止滚动，再次点击恢复滚动！",
	"恢复滚动???",
	"目前已经是最新消息！",
	"只能查看最???5条消息！",
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

var	datax3 ='<div class="jkbtj">应用工具</div>';
		datax3+='<div class="jkzbj" name="ch016">IT架构</div>';
		datax3+='<div class="jkzbj" name="ch017">系统监控</div>';
		datax3+='<div class="jkzbj" name="ch018">数据流</div>';

//屏蔽右键事件
document.oncontextmenu=function(){return	false;}
//获取日期
function getLangDate(item){
	var dateObj = new Date();
	var year = dateObj.getFullYear();
	var month = dateObj.getMonth()+1;
	var date = dateObj.getDate();
	var day = dateObj.getDay();
	var weeks = ["星期???","星期一","星期???","星期???","星期???","星期???","星期???"];
	var week = weeks[day];
	var hour = dateObj.getHours();
	var minute = dateObj.getMinutes();
	var second = dateObj.getSeconds();
	if(month<10){month="0"+month;}
	if(date<10){date="0"+date;}
	if(hour<10){hour="0"+hour;}
	if(minute<10){minute="0"+minute;}
	if(second<10){second="0"+second;}
	//var newDate = year+"???"+month+"???"+date+"??? "+hour+":"+minute+":"+second+" "+week;
	if(item=='systime'){
	var newDate ="<font class='ttext'>"+year+"???"+month+"???"+date+"??? "+hour+":"+minute+":"+second+" "+week+"</font>";
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
//没有权限，警示不具备权限并询问是否购买这个模块，已经用户剩余的金???
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
								stxt+='<span id="pServiceNa">'+data1[0].ServiceNa+'</span>???<span id="pServicePr">'+data1[0].ServicePr+'</span>金币/';
								stxt+='<span id="pServiceTi">'+data1[0].ServiceTi+'</span>天，您目前剩???'+Q14123104+'金币???<span style="color:#FFC016;">添加微信获赠更多金币</span></div><center><input type="button" id="testbutton" value="购买"></center></div>';
						$("#BGcontent").css({'width':'400px','height':'300px','margin-top':'-150px','margin-right':'-200px'}).append(stxt);
			}
		})
	}	
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

//小于0返回绿色，大于等???0返回红色
function rcolor(tnum){if(tnum>=0){return 'style="color:#FF4D4D;"';}else{return 'style="color:#00CC66;"';}}
//日期???
function getDaysDiff(date1, date2) {
  const oneDay = 24 * 60 * 60 * 1000; // 一天的毫秒???
  const timeDiff = Math.abs(date1.getTime() - date2.getTime()); // 获取时间戳差值的绝对???
  const daysDiff = Math.round(timeDiff / oneDay); // 根据时间戳差值计算天数差
  return daysDiff;
}
//标准???
function calculateStandardDeviation(numbers) {
	if (!numbers.length) return 0; // 如果数组为空，返???0
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
	return Math.sqrt(variance); // 返回标准???
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
			Q14123101=backtext[0].Q14123101;//登录???
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
							
			//---------------------------------------------
			
			//第一个界面是实时数据，登录后进入A股市???
			
			$("#ModelLiveSvr4").click();
			//alert(UserNote.dd);
		}
	});


}

$(document).ready(function(){	minit(Q14123101);})


//登录按钮，点击登录按钮，调用登录函数
$(document).off('click',"#mq_top_ul_li_06").on('click',"#mq_top_ul_li_06",function(){
		if($("#mq_top_ul_li_user").length == 0) {
    	$("body").append('<div id="mq_top_ul_li_user"></div>');
			$("#mq_top_ul_li_user").html('<div class="form3">???&nbsp;???&nbsp;名：'+Q14123101+'</div><div class="form3">???&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;益：'+Q14123104+'金币</div>').mouseleave(function(){$("#mq_top_ul_li_user").remove();});
		}
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

//提示???
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
//提示???
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

//提示消息
$(document).off('click',"#mq_top_ul_li_War").on('click',"#mq_top_ul_li_War",function(){
	$("#Dash_0").css("display","block");
	
	$("#mq_top_ul_li_War").css({'animation':'blink 1s infinite'});
	$(document).off("click",".shut2").on("click",".shut2",function(){
		$(this).parent().hide();
		$("#mq_top_ul_li_War").css("animation-name","none");
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
	



//进入实时数据主题
$(document).off("click","#ModelLiveSvr0").on("click","#ModelLiveSvr0",function(){
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="./ch004.html?par='+Q14123101+'"></iframe>';
			$("#mq_main").html(xChannel);
	
	})
//进入实时数据主题
$(document).off("click","#ModelLiveSvr1").on("click","#ModelLiveSvr1",function(){
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="./ch013.html?par='+Q14123101+'"></iframe>';
			$("#mq_main").html(xChannel);
	
	})


//进入实时数据主题
$(document).off("click","#ModelLiveSvr2").on("click","#ModelLiveSvr2",function(){
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="http://10.10.98.51:8888"></iframe>';
			$("#mq_main").html(xChannel);
	
	})


//进入实时数据主题
$(document).off("click","#ModelLiveSvr3").on("click","#ModelLiveSvr3",function(){			
			var  xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="./qteam.html?par='+Q14123101+'"></iframe>';
			$("#mq_main").html(xChannel);
			
	})

//进入实时数据主题
$(document).off("click","#ModelLiveSvr4").on("click","#ModelLiveSvr4",function(){
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="http://10.10.98.51:9999"></iframe>';
			$("#mq_main").html(xChannel);
	
	})
	

//进入实时数据主题
$(document).off("click","#ModelLiveSvr5").on("click","#ModelLiveSvr5",function(){
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="http://10.10.98.123:3000"></iframe>';
			$("#mq_main").html(xChannel);
	
	})

//进入实时数据主题
$(document).off("click","#ModelLiveSvr6").on("click","#ModelLiveSvr6",function(){
			var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="./ch020.html?par='+Q14123101+'"></iframe>';
			$("#mq_main").html(xChannel);
	
	})

//进入实时数据主题
$(document).off("click","#ModelLiveSvr7").on("click","#ModelLiveSvr7",function(){
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
		var xChannel = '<iframe class="mq_main_l_Frame" runat="server" src="./'+itName+'.html?par='+Q14123101+'"></iframe>';
		$("#mq_main_l1").html(xChannel);
		
	}
	else{
		NoAuthority(itAuth);
	}
	})


//warnmessage的确定按???
$(document).off('click',"#Yes").on('click',"#Yes",function(){
			$(this).parent().parent().remove();
		})