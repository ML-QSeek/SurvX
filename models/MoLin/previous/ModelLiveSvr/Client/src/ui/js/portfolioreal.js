;
var arr1=[];var arr2=[];var arr8=[];var arr9=[];var chic1=[];var chic1z=[];var chic1f=[];
var chic1s=[]; var res1='';var zres1=[] ;
 //console.log(data[i].fl1h);    
var stockopentime=("9:29:00").split(":");
basetime=stockopentime[0]*3600+stockopentime[1]*60+stockopentime[2]*1;
//console.log('变量：',basetime);  
       
       
$.ajax({
	type:"POST",
	url: "qi/qi00002/qi04635C/portfoliorealC.php",
	dataType: "json",
	data:{
		slag:"yunsuan",
		timer:basetime,
	},
	async:false,
	success: function(data){
		if(data!=0){
			for(var i=0;i<data.length;i++){
				var dt =data[i].name.split(":");
				basetime=dt[0]*3600+dt[1]*60+dt[2]*1;
				//console.log('变量：',basetime); 
				arr1.push(data[i].name);
				arr2.push(data[i].fl1h);
				arr8.push(data[i].shzh);
				arr9.push(data[i].chye);
			}
		}
	}
}); 
$.ajax({
	type:"POST",
	url: "qi/qi00002/qi04635C/portfoliorealC.php",
	dataType: "json",
	data:{
		slag:"chic",
		chic:"chcc1"
	},
	async:false,
	success: function(data){
		for(var i=0;i<data.length;i++){
			chic1.push(data[i].name);
			chic1z.push(data[i].flhz);
			chic1f.push(data[i].flhf);
			chic1s.push(data[i].flhs);
			//alert(data[i].name+"-"+data[i].flhz+"-"+data[i].flhf+"-"+data[i].fl1hs);
		}
	}
});      
$.post("qi/qi00002/qi04635C/portfoliorealC.php",{slag:"baobiao",baobiao:"data1"},function(data){$('#PcontainerP3').html(data);});      

var sres1=eval(chic1s.join('+')); 
         for (var i = 0, len = chic1.length; i < len; i++) {	res1+='{value:'+chic1s[i]+',name:"'+chic1[i]+'"},';}
         for (var i = 0, len = chic1.length; i < len; i++) {zres1.push((chic1z[i]+chic1f[i]+','+(Math.round(chic1s[i]/sres1*10000)/100).toFixed(2)+','+ Math.abs((chic1z[i]+chic1f[i])*(chic1s[i]/sres1))+','+ chic1[i]+'').split(','));}  

var app = {};

zhline('myChart1','chqushit1','PcontainerP1','多策略混合1号',arr1,arr2,arr8,arr9);
zhbar('myChart7','option7','PcontainerP2','多策略混合1号',chic1,chic1z,chic1f)
$("#PcontainerP4").html('<span style="color:#FFC016;">今日操作：</span>');
var wmychart = echarts.init(document.getElementById('Pcontainery'));//图表节点  
woption = {
    title: {text: '标的分布',left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}},
    tooltip : {trigger: 'axis',showDelay : 0,formatter : function (params) {
            if (params.value.length > 1) {return params.seriesName + ' :<br/>' + '净值贡献：'+ params.value[0]+ ' 市值比例：'+ params.value[1];
            }else {return params.seriesName + ' :<br/>'+ params.name + ' : '+ params.value + 'kg ';}}, axisPointer:{show: true,type : 'cross',lineStyle: {type : 'dashed', width : 1}}},
    color:['#00CCFF','#F34100','#FFC016','#F2F2F2'],
    grid: {left: '2',right: '2',top: '15%',bottom: '3%',containLabel: true},
    legend: {textStyle:{color:'#16C0FF',fontSize:12},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:0,icon:'Rect',data: ['多策略混合1号'] }, 
    xAxis: {axisLabel: {rotate: 60,interval:0,textStyle:{color:'#16C0FF',fontSize:12,}},
    	axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
    splitLine: {lineStyle: {type: 'dashed',color:'#16C0FF',width:0.5}}},    
    yAxis: {axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
    	splitLine: {lineStyle: {type: 'dashed',color:'#16C0FF',width:0.5}},scale: true},
    series: [{name: '多策略混合1号',data:(function(){return zres1;})(),type:'scatter',symbolSize: function (data) { return Math.sqrt(data[2])*100;},
        label: {emphasis: {show: true,formatter: function (param){return param.data[3];},position: 'top'}}}, 
]};
wmychart.setOption(woption); 


		$.ajax({
		type: "POST",
		url: "qi/qi00002/qi04635C/YuceC.php",
		data:{
			dflag:'yuce',
			sflag:'_04',
			item:'shy',
			date:getLangDate('newDate'),
			},
		async:false,
		success: function(data){
			var data1 = eval(trim(data));
			var ddate1=[];var zf1=[];var mf1=[];var df1=[];var n1=[];var n2=[];var df4=[['rank', 'amount', 'product']];
			var dlen =data1.length-1;
			for(var i=0;i<dlen;i++){
				ddate1.push(data1[i].date1);
				zf1.push(data1[i].Market);
				mf1.push(data1[i].MarketmM_7);
				df1.push(data1[i].MarketmR_3);
				}
			var dtemp =data1[dlen].Bankuai_7.split('-')
			for(var m=9;m>-1;m--){
				df4.push([dtemp[m].split('_')[1],dtemp[m].split('_')[2],dtemp[m].split('_')[0]])
				}
				
			n1.push(data1[dlen].zijin_7.split('_')[1]);
			n1.push(data1[dlen].hongguan_7.split('_')[1]);
			n1.push(data1[dlen].huobiczh_7.split('_')[1]);
			n1.push(data1[dlen].shichang_7.split('_')[1]);
			n1.push(data1[dlen].Waishch_7.split('_')[1]);
			n2.push(data1[dlen].zijin_7.split('_')[0]);
			n2.push(data1[dlen].hongguan_7.split('_')[0]);
			n2.push(data1[dlen].huobiczh_7.split('_')[0]);
			n2.push(data1[dlen].shichang_7.split('_')[0]);
			n2.push(data1[dlen].Waishch_7.split('_')[0]);
	
			hg1("PcontainerT1",n1,n2);
			hg2("Pcontainerx",data1[dlen].Market,data1[dlen].MarketmM_7,data1[dlen].MarketmR_3);	
			hg3("PcontainerT2",ddate1,zf1,mf1,df1);
			hg4("PcontainerT3",df4);
		}
	})



/*
      
app.timeTicket = setInterval(function () {   
	

//$.ajaxSettings.async = true;//设置同步
$.post("chic.php",
				{slag:"yunsuan",
				 timer:basetime,
					},
				function(data){
					if(data!=0){
					for(var i=0;i<data.length;i++){
						  var dt =data[i].name.split(":");
						  basetime=dt[0]*3600+dt[1]*60+dt[2]*1;
						  //console.log('变量：',basetime); 
							arr1.push(data[i].name);
							arr2.push(data[i].fl1h);
      				arr8.push(data[i].shzh);
    					arr9.push(data[i].chye);
    		}
var chic1=[];var chic1z=[];var chic1f=[];

$.post("chic.php",{slag:"chic",chic:"chcc1"},function(data){for(var i=0;i<data.length;i++){chic1.push(data[i].name);chic1z.push(data[i].flhz);chic1f.push(data[i].flhf);}},"json");
zhlineup('myChart1',arr1,arr2,arr8,arr9);
zhbarup('myChart7',chic1,chic1z,chic1f)
$.post("chic.php",{slag:"baobiao",baobiao:"data1"},function(data){$('#container13').html(data);});
}
    		},"json");

            
}, 10000);
                        
*/