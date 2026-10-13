;
//名称:mq.js --编写：曲如意 --编写日期：2024-12-15
//提交：01；修改：03；删除：02；查询：04；执行：05；

//用户名
//用户具备的权限
var	UserAuthority=[];
//用户操作的痕迹记录
var	UserNote={};
//当前页面的主题
var NowTopic = 'ModelLiveSvr4';
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
			
			//第一个界面是实时数据，登录后进入A股市???
			
			//$("#MLQSeek0").click();
			//alert(UserNote.dd);
		}
	});


}

$(document).ready(function(){	minit(Q14123101);})

