; 
var arr1=[];var arr2=[];var arr3=[];var arr4=[];var arr5=[];var arr6=[]; var arr7=[];var arr8=[];
var arr9=[];var arr10=[];var arr11=[];var arr12=[];var arr13=[];  var arr14=[];var arr15=[];var arr16=[];
var arr17=[];var arr18=[];var arr19=[];var arr20=[];var arr21=[]; var arr22=[];var arr23=[];var arr24=[];
var arr25=[];var arr26=[];var arr27=[];var arr28=[];var arr29=[];
var chic1=[];var chic1z=[];var chic1f=[];var chic1s=[];
var stockopentime=("9:30:00").split(":");
basetime=stockopentime[0]*3600+stockopentime[1]*60+stockopentime[2]*1;

$.ajax({
	type:"POST",
	url: "qi/qi00002/qi04635C/TkpiC.php",
	dataType: "json",
	data:{
		slag:"Tkpicharts",
		timer:basetime,
	},
	async:false,
	success: function(data){
					if(data!=0){
					for(var i=0;i<data.length;i++){
						  var dt =data[i].time1.split(":");
						  basetime=dt[0]*3600+dt[1]*60+dt[2]*1;
						  //console.log('变量：',basetime); 
              arr1.push(data[i].time1   );  arr2.push(data[i].zf9num  );  arr3.push(data[i].zf7num  );   arr4.push(data[i].zf5num  );
              arr5.push(data[i].zf3num  );  arr6.push(data[i].df9num  );  arr7.push(data[i].df7num  );   arr8.push(data[i].df5num  );
              arr9.push(data[i].df3num  ); arr10.push(data[i].lshxg   ); arr11.push(data[i].lshxd   );  arr12.push(data[i].jdxg    );
             arr13.push(data[i].jdxd    ); arr14.push(data[i].jrjunjia); arr15.push(data[i].zjunjia );  arr16.push(data[i].ztjzhfu );
             arr17.push(data[i].ztjnum  ); arr18.push(data[i].qtjzhfu ); arr19.push(data[i].qtjnum  );  arr20.push(data[i].ztbzk   );
             arr21.push(data[i].dkx     ); arr22.push(data[i].vol1    ); arr23.push(data[i].vol2    );  arr24.push(data[i].vol3    );
             arr25.push(data[i].ma1     ); arr26.push(data[i].ztznum  ); arr27.push(data[i].ztbilv  );  arr28.push(data[i].avgnum  );   
             arr29.push(data[i].a30  );   
     }
     }
   }});    
var app = {};//定义用于刷新的对象
Tkpiline2('myChart1','chqushit1','Lcontainer1','上涨比例(7+,9.6+)','7+:    ','9.6+  :',arr1,arr2,arr3);
Tkpiline2('myChart2','chqushit2','Lcontainer2','上涨比例(3+,5+)','3+:    ','5+  :',arr1,arr4,arr5);   
Tkpiline2('myChart3','chqushit3','Lcontainer3','下跌比例(-7-,-9.6-)','-7-:    ','-9.6-:',arr1,arr6,arr7);   
Tkpiline2('myChart4','chqushit4','Lcontainer4','下跌比例(-3-,-5-)','-3-:    ','-5-:',arr1,arr8,arr9);  
Tkpiline1('myChart5','chqushit5','Lcontainer5','创历史新高','历史新高',arr1,arr10)
Tkpiline1('myChart6','chqushit6','Lcontainer6','创历史新低','历史新低',arr1,arr11) 
Tkpiline1('myChart8','chqushit8','Lcontainer8','全A股均价','全A股均价',arr1,arr11) 
var myChart7 = echarts.init(document.getElementById('Lcontainer7'));//图表节点
var chqushit7 = {
	title: {
		text: '当日涨停被砸开个股数',
		left: 'left',
		padding:4,
		textStyle:{color:'#FFFFFF',fontSize:15,}
	},
  tooltip: {
  trigger: 'axis',
  formatter:function(params) {
   var txt  = '时间  :'          + params[0]['name']+'<br />';
        txt += '砸开个股数:  ' + params[0]['value']+'<br />';  
        txt += '触及涨停家数:' + params[1]['value']+'<br />'; 
        txt += '占比:        ' +(Math.round(params[2]['value']*10000)/100).toFixed(2)+'%'+'<br />'; 
    return txt;
  }},
	grid:{bottom:'12%',top:'13%',right:'6%'},
  color:['#F34100','#FFC016','#00CCFF','#F2F2F2'],
  legend: {textStyle:{color:'#16C0FF',fontSize:12},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:4,
    data:[{name:'触及涨停家数',icon:'Rect'},{name:'占比',icon:'Rect'},{name:'砸开个股数',icon:'Rect'}],},            
  dataZoom: [{type: 'inside',show: true,realtime: true,start: 100,end: 0}],
	xAxis : [{type : 'category',
  					axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
  					splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
            data:(function(){return arr1;})()}],
  yAxis: [{boundaryGap: [0, '30%'],type: 'value',splitNumber:5,scale:false,
  					axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
 						splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}},
 					{boundaryGap: [0, '100%'],type: 'value',splitNumber:5,scale:true,axisLine:{show:false,lineStyle:{color:'#16C0FF'}},
  				 splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}},
  				 {boundaryGap: [0, '100%'],type: 'value',splitNumber:5,scale:true,show:false,
  					axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
  					splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}}],
series : [{name:'触及涨停家数',type:'line',symbolSize:0.3,lineStyle:{normal:{width:1}},yAxisIndex:2,data:(function(){return arr26;})()},
          {name:'占比',type:'line',symbolSize:0.3,lineStyle:{normal:{width:1}},smooth:true,yAxisIndex:1,data:(function(){return arr27;})()},
          {name:'砸开个股数',type:'bar',yAxisIndex:0,data:(function(){return arr20;})()}]
    };  
if (chqushit7 && typeof chqushit7 === "object") {myChart7.setOption(chqushit7, true);myChart7.resize();}

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

Szhbar('myChart7','option7','RLcontainer1','多策略混合1号',chic1,chic1z,chic1f);
Topology("RRcontainer1","xx","yy");
/*
app.timeTicket = setInterval(function () {  
$.ajaxSettings.async = true;//设置同步
//console.log('变量：',basetime); 
$.post("TkpiC.php",
				{slag:"Tkpicharts",
				 timer:basetime,	
					},
				function(data){
					if(data!=0){
					for(var i=0;i<data.length;i++){
							var dt =data[i].time1.split(":");
						  basetime=dt[0]*3600+dt[1]*60+dt[2]*1;
              arr1.push(data[i].time1   );  arr2.push(data[i].zf9num  );  arr3.push(data[i].zf7num  );   arr4.push(data[i].zf5num  );
              arr5.push(data[i].zf3num  );  arr6.push(data[i].df9num  );  arr7.push(data[i].df7num  );   arr8.push(data[i].df5num  );
              arr9.push(data[i].df3num  ); arr10.push(data[i].lshxg   ); arr11.push(data[i].lshxd   );  arr12.push(data[i].jdxg    );
             	arr13.push(data[i].jdxd    ); arr14.push(data[i].jrjunjia); arr15.push(data[i].zjunjia );  arr16.push(data[i].ztjzhfu );
             	arr17.push(data[i].ztjnum  ); arr18.push(data[i].qtjzhfu ); arr19.push(data[i].qtjnum  );  arr20.push(data[i].ztbzk   );
             	arr21.push(data[i].dkx     ); arr22.push(data[i].vol1    ); arr23.push(data[i].vol2    );  arr24.push(data[i].vol3    );
             	arr25.push(data[i].ma1     ); arr26.push(data[i].ztznum  ); arr27.push(data[i].ztbilv  );  arr28.push(data[i].avgnum  );   
             	arr29.push(data[i].a30  ); }  
							Tkpiline2up('myChart1','7+:    ','9.6+  :',arr1,arr2,arr3);
							Tkpiline2up('myChart2','3+:    ','5+  :',arr1,arr4,arr5);   
							Tkpiline2up('myChart3','-7-:    ','-9.6-:',arr1,arr6,arr7);   
							Tkpiline2up('myChart4','-3-:    ','-5-:',arr1,arr8,arr9); 
							Tkpiline1up('myChart5','阶段新高',arr1,arr12)
							Tkpiline1up('myChart6','历史新高',arr1,arr10)
							myChart7.setOption({xAxis : [{type : 'category',data : (function(){return arr1;})()}],
							            series : [{name:'砸开个股数',type:'bar',yAxisIndex:0,data:(function(){return arr20;})()},
							            					{name:'触及涨停家数',type:'line',yAxisIndex:2,data:(function(){return arr26;})()},
							            					{name:'占比',type:'line',smooth:true,yAxisIndex:1,data:(function(){return arr27;})()}]});
zhbarup('myChart7',chic1,chic1z,chic1f)
}
     },"json");   
}, 10000);
*/