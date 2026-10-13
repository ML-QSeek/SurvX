;
//server
var MServer = "http://10.10.98.51/test/sys/";
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
function trim(str){return str.replace(/(^\s*)|(\s*$)/g,"");}
//关闭按钮
$(document).on("click",".shut",function(){
	var thisid= $(this).attr('id').split("_")[1];
	//alert(thisid);
	$(this).parent().remove();
	if (["Q3LIB01","Q3LIB02","Q3LIB03"].includes(thisid)){
		$('#'+thisid).attr('name','k0');
	}
	})
// 模块拖拽	
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
// 生成一个用不重复的ID
function GenNonDuplicateID(randomLength){
	return Number(Math.random().toString().substr(3,randomLength) + Date.now()).toString(36)
}
//随机数
function sum(m,n){
　　var num = Math.floor(Math.random()*(m - n) + n);
　　return num;
}
//警示消息
function WarnMessage(content){
	var sid=GenNonDuplicateID(1);	
	$("body").append('<div class="Warn"><div class="WarnB" id="WarnB_'+sid+'"></div><div class="WarnM"><button id="Yes" class="WarnMButton"> 好的 </button></div></div>');
	$("#WarnB_"+sid).html(content);
	}	
	
//信息浏览
function Q3LIBtoolCon(content,item0,topic,lnum){
	var sid=GenNonDuplicateID(1);
	var txt ='<div class="Q3LIBtool" id="Q3LIBtool_'+sid+'">';
			txt +='<div class="shut" id="shut_'+item0+'"><img src="./assets/images/close2.png"/></div><div class="Q3LIBtoolH" id="Q3LIBtoolH_'+sid+'"></div>';
			txt +='<div class="Q3LIBtoolB" id="Q3LIBtoolB_'+sid+'"></div></div>';
			$("body").append(txt);     
			var top =  parseInt($("#Q3LIBtool_"+sid).css("top"))+sum(30,100);
			var left = parseInt($("#Q3LIBtool_"+sid).css("left"))+sum(30,100);
			$("#Q3LIBtool_"+sid).css({"top":top,"left":left}).height(lnum+'px');
			$("#Q3LIBtoolB_"+sid).html(content).height((lnum-30)+'px');
			$("#Q3LIBtoolH_"+sid).html(topic);
			divmove("Q3LIBtoolH_"+sid,"Q3LIBtool_"+sid);
	}
	
//放大镜功能
$(document).on('click',".Q3LIB_item_ul li", function(e){
	if($(this).text().length>0){
		Q3LIBtoolCon($(this).html(),sum(30,100),"<div style='height:100%;width:auto;padding:4px;box-sizing:border-box;'>查看信息</div>","300");
}
})
$(document).on('click',".Q3LIB_yuce_ul li", function(e){
	if($(this).text().length>0){
		Q3LIBtoolCon($(this).html(),sum(30,100),"<div style='height:100%;width:auto;padding:4px;box-sizing:border-box;'>预测信息</div>","300");
}
})
$(document).off('click',".Q3LIBbtn2").on('click',".Q3LIBbtn2",function(){
	$(this).css('background','rgba(20,177,235,0.3)');  
	var jname =$(this).val();
	var jid =$(this).attr('id');
	var uList=$('#Q3LIB_zhu_rowTR').find("ul"); 
	var uListArr=[];
	for (var f=0;f<uList.length;f++) {
	    uListArr.push(uList.eq(f).attr("id").split('_')[1]); 
	   }
	if ($.inArray(jid,uListArr)!=-1) {
		WarnMessage('请不要重复选择相同项目！');
		$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
		}
	else if (uListArr.length>=5){
		WarnMessage('最大同时申请5个项目！');
		$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
		}
	else{
	var	itName=jid;
	var itAuth=itName+'_04';
	var fAuthority=parent.Authority(window.parent.Q14123101,itAuth);
	if(fAuthority==1){
		$("#Q3LIB_zhu_rowTR").append('<div class="Q3LIB_item"><ul class="Q3LIB_item_ulT"  id="jl_'+jid+'"><li>'+jname+'</li></ul></div>');
					$("#Q3LIB_zhu_mainR").append('<div class="Q3LIB_item"><ul class="Q3LIB_item_ul" id="Q3LIB_'+jid+'"></ul></div>');
					appendli('Q3LIB_'+jid,jid);
							$.post(MServer+"qi/qi00002/qi04635C/Q3LIBC.php", 
								{	sid:'_04',
									user:Q14123101,
									item:jid,
		 							},
									function(content){
										var jcontent=eval(trim(content));
													for(var i=0;i<jcontent.length;i++){
														$('#'+jid+'_'+(jcontent[i].TimeAxis).substr(0,4)+(jcontent[i].TimeAxis).substr(5,2)).append('<span class="ttext">'+jcontent[i].TimeAxis.replace(/&gt;/g,">").replace(/&lt;/g,"<")+'：'+jcontent[i].ThematicCon.replace(/&gt;/g,">").replace(/&lt;/g,"<")+'<span/><span class="ttext" style="color:yellow;font-weight:bold;">文档：'+(function(){if(jcontent[i].ThematicDoc!=""){return jcontent[i].ThematicDoc;}else{return "无";}})()+'</span><br />--------------------------------------------分割线--------------------------------------------<br />');
														}
										})
							var trList=$('#Q3LIB_zhu_rowTR').find('[class="Q3LIB_item_ulT"]');
							var tridArr='';
							for (var f=0;f<trList.length;f++) {tridArr += '#'+trList.eq(f).text();}
							$.post(MServer+"qi/qi00002/qi04635C/Q3LIBC.php", 
								{	sid:'_0402',
									user:Q14123101,
									jid:tridArr,
		 							},
									function(content1){
										$("#Q3LIB_yuce").find('li').html('');
										var jcontent1=eval(trim(content1));
													for(var i=0;i<jcontent1.length;i++){
														$('#Q3LIByuce_'+(jcontent1[i].TimeAxis).substr(0,4)+(jcontent1[i].TimeAxis).substr(5,2)).append('<span class="ttext" style="color:red;font-weight:bold;">'+jcontent1[i].starttime+'-->'+jcontent1[i].TimeAxis+'（'+(function(){if(jcontent1[i].ASItm=='分析'){return '<span style="color:yellow;font-weight:bold;">类型：分析</span>';}else{return '<span style="color:yellow;font-weight:bold;">类型：预测</span>';}})()+'）：<span/><span class="ttext">'+jcontent1[i].ASCon.replace(/&gt;/g,">").replace(/&lt;/g,"<")+'<span/><br />--------------------------------------------分割线--------------------------------------------<br />');
														}
										})

	}
	else{
		parent.NoAuthority(itAuth);
	}	
		}
})
//选择主题
$(document).off('click',".Q3LIBbtn3").on('click',".Q3LIBbtn3",function(){
	$("#Q3LIB02Topic").attr('contenteditable','false')
	var thisid = $(this).attr('name');
	var thisname = $(this).val();
	$("#Q3LIB02Topic").attr('name',thisid);
	$("#Q3LIB02Topic").html(thisname);
})

//添加项目
$(document).off('click',"#Q3LIB01").on('click',"#Q3LIB01",function(){
	var thisname = $(this).attr('name');
	if (thisname=="k0"){
		$.post(MServer+"qi/qi00002/qi04635C/Q3LIBC.php",  
				{sid:'_0401',
				 user:Q14123101,
		 		},
				function(data){  
						var jcontent=eval(trim(data)); 
						var jtext ='<div id ="Q3LIB01Board">';
						for(var i=0;i<jcontent.length;i++){
							jtext+= '<input id="'+jcontent[i].MEntityID+'"  class="Q3LIBbtn2" type="button" value="'+jcontent[i].MEntityName+'" />';
							}
							jtext+='</div>';
						Q3LIBtoolCon(jtext,"Q3LIB01","<div style='height:100%;width:auto;padding:4px;box-sizing:border-box;'>添加项目</div>","300");
						$("#Q3LIB01").attr("name","k1");
				})
		}
	})
//增加数据
$(document).off('click',"#Q3LIB02").on('click',"#Q3LIB02",function(){
	var thisname = $(this).attr('name');
	if (thisname=="k0"){
		var ztxt  ='<div id = "Q3LIB02Board"></div>';
				ztxt += '<div style="width:100%;height:26px;float:left;padding-left:10px;box-sizing:border-box;">';
				ztxt += '<div style="float:left;font-size:16px;padding-top:6px;box-sizing:border-box;">主题：</div><div id ="Q3LIB02Topic" name="None"></div> <div style="float:left;font-size:16px;padding-top:6px;box-sizing:border-box;">日期：</div><div id = "Q3LIB02Date"></div></div>';
				ztxt += '<div id ="Q3LIB02Con" contenteditable="true"></div>';
				ztxt += '<div style="width:100%;height:20px;float:left;"><center><div id ="Q3LIB02Submit">提交</div></center></div>';
		Q3LIBtoolCon(ztxt,"Q3LIB02","<div style='height:100%;width:auto;padding:4px;box-sizing:border-box;'>增加数据</div>","500");
		$("#Q3LIB02Date").html(getLangDate('newDate1'));
		$.post(MServer+"qi/qi00002/qi04635C/Q3LIBC.php", 
				{sid:'_0401',
				 user:Q14123101,
		 		},
				function(data){  
						var jcontent=eval(trim(data)); 
						var jtext ='';
						for(var i=0;i<jcontent.length;i++){
							jtext+= '<input name="'+jcontent[i].MEntityID+'"  class="Q3LIBbtn3" type="button" value="'+jcontent[i].MEntityName+'" />';
							}
							$("#Q3LIB02Board").html(jtext);
					})
		//选择日期下拉框绑定
		$(document).off('click',"#Q3LIB02Date").on('click','#Q3LIB02Date',function(){laydate.reset();laydate({elem:'#Q3LIB02Date'});$(this).css("background","rgba(20,177,235,0.3)");});
		$("#Q3LIB02").attr("name","k1");
		}
})

$(document).off('dblclick',"#Q3LIB02Topic").on('dblclick',"#Q3LIB02Topic",function(){
	$(this).attr('contenteditable','true').attr('name','None');
	$("#Q3LIB02Topic").html("");
	
})
//增加数据提交
$(document).off('click',"#Q3LIB02Submit").on('click',"#Q3LIB02Submit",function(){
	var thistopic = $("#Q3LIB02Topic").html();
	var thisname =  $("#Q3LIB02Topic").attr('name');
	var thisdate = $("#Q3LIB02Date").html().replace(/-/g,'');
	var thiscon = $("#Q3LIB02Con").html();
	if (thistopic==''||thiscon==''){
		WarnMessage('请完善表格内容！');
		$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
		}
	else{
		$.post(MServer+"qi/qi00002/qi04635C/Q3LIBC.php", 
			{sid:'_01',
			 itemid:thisname,
			 user:Q14123101,
			 itemname:thistopic,
			 date:thisdate,
			 itemcon:thiscon,
			 itemdoc:'',
	 		},
			function(data){  
				WarnMessage('保存成功！');
				$(document).off("click","#Yes").on("click","#Yes",function(){
					$(this).parent().parent().remove();
					$("#shut_Q3LIB02").click();
					});
				})
		}
})

//预测分析
$(document).off('click',"#Q3LIB03").on('click',"#Q3LIB03",function(){
	var thisname = $(this).attr('name');
	var uList=$('#Q3LIB_zhu_rowTR').find("ul"); 
	var uListArr=[];
	for (var f=0;f<uList.length;f++) {
	    uListArr.push(uList.eq(f).attr("id")); 
	   }
	if (uListArr.length==0){
				WarnMessage('请选择至少一个项目！');
				$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
		}
	else{
		if (thisname=="k0"){
			var	ytxt = '<div style="width:100%;height:26px;float:left;padding-left:10px;box-sizing:border-box;display: inline-block;">';
					ytxt+= '<div id ="isFY">预测</div><div style="float:left;font-size:16px;padding-top:6px;box-sizing:border-box;">日期：</div><div id = "Q3LIB03Date"></div></div>';
					ytxt+= '<div id = "Q3LIB03Con" contenteditable="true"></div>';
					ytxt+= '<div style="width:100%;height:20px;float:left;font-size:16px;"><center><div id ="Q3LIB03Submit">提交</div></center></div>';
			Q3LIBtoolCon(ytxt,"Q3LIB03","<div id='Q3LIB03topic' style='height:100%;width:auto;padding:4px;box-sizing:border-box;'>预测分析：</div>","230");
			$("#Q3LIB03").attr("name","k1");
			$("#Q3LIB03Date").html(getLangDate('newDate1'));
			//选择日期下拉框绑定
			$(document).off('click',"#Q3LIB03Date").on('click','#Q3LIB03Date',function(){laydate.reset();laydate({elem:'#Q3LIB03Date'});$(this).css("background","rgba(20,177,235,0.3)");});
			for (var i=0;i<uListArr.length;i++) {$("#Q3LIB03topic").append("#"+$("#"+uListArr[i]).text());}
			}
	}	
})
$(document).off('click',"#isFY").on('click',"#isFY",function(){
	if($("#isFY").html()=='预测'){$("#isFY").html('分析');}else{$("#isFY").html('预测');}
})
//预测数据提交
$(document).off('click',"#Q3LIB03Submit").on('click',"#Q3LIB03Submit",function(){
	var thisdate = $("#Q3LIB03Date").html().replace(/-/g,'');
	var itemid = $("#Q3LIB03topic").html().replace('预测分析：','');
	var itemsel = $("#isFY").html();
	var itemcon = $("#Q3LIB03Con").html();
	if (itemcon=='')
	{
		WarnMessage('请完善表格内容！');
		$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
		}else{
			$.post(MServer+"qi/qi000002/3LIBC.php", 
					{sid:'_0101',
					 user:Q14123101,
					 date:thisdate,
					 itemid:itemid,
					 itemsel:itemsel,
					 itemcon:itemcon,
			 		},
					function(data){
						//alert(data);
						WarnMessage('保存成功！');
						$(document).off("click","#Yes").on("click","#Yes",function(){
							$(this).parent().parent().remove();
							$("#shut_Q3LIB03").click();
							});
						})
		}	
})
//查询
$(document).off('click',"#Q3LIBSel").on('click',"#Q3LIBSel",function(){
	var selvalue = $("#Q3LIBKey").val();
	//alert(selvalue);
	$.post(MServer+"qi/qi00002/qi04635C/Q3LIBC.php", 
			{sid:'_0403',
			 user:Q14123101,
			 itcon:selvalue,
	 		},
			function(data){
				$('.Q3LIBbtn2').css('color','#16C0FF');
				$('.Q3LIBbtn3').css('color','#16C0FF');
				var jtid=eval(trim(data));
				for (var f=0;f<jtid.length;f++) {
					//alert(jtid[0]);
					$("#"+jtid[f]).css('color','#FFFF00').prependTo('#Q3LIB01Board');
					$("[name='"+jtid[f]+"']").css('color','#FFFF00').prependTo('#Q3LIB02Board');
					}
				})
})
//接受参数
$(document).ready(function(){
	// 获取当前页面的URL参数
	const params = new URLSearchParams(window.location.search);
	// 获取指定参数的值
	Q14123101 = params.get('par');
	appendli('Q3LIB_yuce','Q3LIByuce');
	var offsettop =$('#Qy'+getLangDate('newMonth')).offset().top-300;
	$("#Q3LIB_zhu_main").animate({scrollTop: offsettop}, 1000);
	$('#Qy'+getLangDate('newMonth')).css({"background-color":"#FF0000","color":"#FFFFFF"});
})


