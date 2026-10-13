;
function	line1(dom,title,var1,var2,var3,var4,title1,title2,title3){
	var	myChart=echarts.init(document.getElementById(dom));
	var	line1={
			title:{
				text:title,
				left:'left',
	      textStyle:{color:'#FFC016',fontSize:16,fontWeight:'bold',},
	      top:'3px',
			},
			grid:{
			bottom:'30px',
			top:'50px',
			right:'30px',
			left:'50px',
			},
		tooltip:{
			trigger:'axis',
		},
    color:['#FFFFF0','#E93F00','#FFC016','#FFC016'],
		legend:{
			right:10,
			top:25,
			textStyle:{color:'#16C0FF',fontSize:15},
			itemHeight:10,
			itemWidth:10,
			data:[{name:title1,icon:'Rect'},{name:title2,icon:'Rect'},{name:title3,icon:'Rect'}],
		},
		dataZoom:[{
			type:'inside',
			show:true,
			realtime:true,
			start:95,
			end:100,
		}],
  	xAxis: [{
  		type: 'category',
      data : (function(){return var1;})(),
      scale: true,
      splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      boundaryGap: false,
      axisLabel:{color:'#16C0FF'},
      axisLine: {lineStyle:{color:'#16C0FF'}},
      splitNumber: 20,
      min: 'dataMin',
      max: 'dataMax'
  	}],
    yAxis: [{boundaryGap: [0, '30%'],type: 'value',axisLabel:{color:'#16C0FF'},axisLine: {lineStyle:{color:'#16C0FF'}},splitArea: {show: false},splitNumber: 5,scale:true,splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},},
         {boundaryGap: [0, '30%'],type: 'value',axisLabel:{color:'#16C0FF'},scale:true,show:false},
         {boundaryGap: [0, '30%'],type: 'value',axisLabel:{color:'#16C0FF'},scale:true,show:false}],
         series : [{
                         "name":title1,
                         "type":"line",
                         "yAxisIndex": 0,
                         "symbolSize":0.1,
                         "lineStyle":{normal:{"width":1.5}},
                         "data":(function(){return var2;})(),
                         //markPoint: {
             						 //data: [{type: 'max', name: '最大值'},
                         //        {type: 'min', name: '最小值'}]},
                           //markLine: { data: [{type: 'average', name: '平均值'}]}
										},{
                         "name":title2,
                         "type":"line",
                         "yAxisIndex": 1,
                         "symbolSize":0.1,
                         "lineStyle":{normal:{"width":1.5}},
                         "data":(function(){return var3;})(),
                   },{
                         "name":title3,
                         "type":"line",
                         "yAxisIndex": 2,
                         "symbolSize":0.1,
                         "lineStyle":{normal:{"width":1.5}},
                         "data":(function(){return var4;})(),
                   }]
        };      
        myChart.setOption(line1);
}

function hg1(dom,weighth,fenshuh){	
        var myChart = echarts.init(document.getElementById(dom));
        // 指定图表的配置项和数据
var weight = {
    title: {
        text: '因素分数及权重',left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}
    },
    tooltip: {},
    //legend: {
    //    data: ['预算分配（Allocated Budget）', '实际开销（Actual Spending）']
    //},
    color:['#FFFFF0','#E93F00','#FFC016','#FFC016'],
    grid: {left: '2',right: '2',top: '15%',bottom: '3%',containLabel: true},
    radar: {
        // shape: 'circle',
        name: {
            textStyle: {
                color: '#10BFFF',
                fontWeight:'bold',
                //backgroundColor: 'rgba(20,177,235,0.3)',
                fontSize:16,
                borderRadius: 3,
                padding: [3, 5]
           }
        },
        splitLine: {
            lineStyle: {
                color: [
                    'rgba(16,191,255, 0.1)', 'rgba(16,191,255, 0.2)',
                    'rgba(16,191,255, 0.4)', 'rgba(16,191,255, 0.6)',
                    'rgba(16,191,255, 0.8)', 'rgba(16,191,255, 1)'
                ].reverse()
            }
        },
        splitArea: {
            show: false
        },
        axisLine: {
            lineStyle: {
                color: 'rgba(16,191,255, 0.5)'
            }
        },
        indicator: [
           { name: '资金面', max: 100},
           { name: '宏观面', max: 100},
           { name: '货币与财政', max: 100},
           { name: '市场面', max: 100},
           { name: '外围市场', max: 100}
        ]
    },

    series: [{
        name: '权重 vs 分数',
        type: 'radar',
        // areaStyle: {normal: {}},
        data : [
            {
                value : (function(){return weighth;})(),
                name : '权重',
                lineStyle: {
                	normal: {
                		color:'#10BFFF',
                		opacity: 0.8
                		}
            		}
            },
             {
                value : (function(){return fenshuh;})(),
                name : '分数',
                lineStyle: {
                	normal: {
                		color:'#F34100',
                		opacity: 0.8
                		}
            		}
            }
        ]
    }]
};
        myChart.setOption(weight);
}

function hg2(dom,zf,mf,df){	
        var myChart1 = echarts.init(document.getElementById(dom));
        // 指定图表的配置项和数据
        var biao = {
            title: {
                text: '市场晴雨表',left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}
            },  
            grid: {left: '2',right: '2',top: '15%',bottom: '3%',containLabel: true},      	
    				tooltip : {
       					 formatter: "{a} <br/>{c} {b}"
    				},
   					series : [
            {
            name: '宏观总分',
            type: 'gauge',
            z: 3,
            min: 0,
            max: 100,
            splitNumber: 10,
            radius: '70%',
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    width: 5,
                    color: [
                    [0.2, '#F2F2F2'],
                    [0.7, '#00CCFF'],
                    [1, '#F34100']
                		]
                }
            },
            axisTick: {            // 坐标轴小标记
                length: 10,        // 属性length控制线长
                lineStyle: {       // 属性lineStyle控制线条样式
                    color: 'auto'
                }
            },
            splitLine: {           // 分隔线
                length: 15,         // 属性length控制线长
                lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                    color: 'auto'
                }
            },
            title : {
                textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                    fontWeight: 'bolder',
                    fontSize: 16,
                    fontStyle: 'italic',
                    color:'#10BFFF'
                }
            },
            detail : {
                textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                    fontWeight: 'bolder'
                }
            },
            data:[{value: zf, name: '今日总分'}]
        },
        {
            name: '短期',
            type: 'gauge',
            center: ['25%', '55%'],    // 默认全局居中
            radius: '45%',
            min:0,
            max:100,
            endAngle:45,
            splitNumber:5,
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    width: 1,
                    color: [
                    [0.2, '#F2F2F2'],
                    [0.7, '#00CCFF'],
                    [1, '#F34100']
                		]
                }
            },
            axisTick: {            // 坐标轴小标记
                length:3,        // 属性length控制线长
            },
            splitLine: {           // 分隔线
                length:8,         // 属性length控制线长
                lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                    color: 'auto'
                }
            },
            pointer: {
                width:5
            },
            title: {
                textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                    fontWeight: 'bolder',
                    fontSize: 16,
                    fontStyle: 'italic',
                    color:'#10BFFF'
                },
                offsetCenter: [0, '-25%'],       // x, y，单位px
            },
            detail: {
                textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                    fontWeight: 'bolder'
                }
            },
            data:[{value: df, name: '短期'}]
        },
				{
            name: '中期',
            type: 'gauge',
            center: ['80%', '55%'],    // 默认全局居中
            radius: '45%',
            min:0,
            max:100,
            endAngle:30,
            splitNumber:5,
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    width: 1,
                    color: [
                    [0.2, '#F2F2F2'],
                    [0.7, '#00CCFF'],
                    [1, '#F34100']
                		]
                }
            },
            axisTick: {            // 坐标轴小标记
                length:2,        // 属性length控制线长
                lineStyle: {       // 属性lineStyle控制线条样式
                    color: 'auto'
                }
            },
            splitLine: {           // 分隔线
                length:5,         // 属性length控制线长
                lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                    color: 'auto'
                }
            },
            pointer: {
                width:5
            },
            title: {
                textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                    fontWeight: 'bolder',
                    fontSize: 16,
                    fontStyle: 'italic',
                    color:'#10BFFF'
                },
                offsetCenter: [0, '-25%'],       // x, y，单位px
            },
            detail: {
                textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                    fontWeight: 'bolder'
                }
            },
            data:[{value: mf, name: '中期'}]
        },      
    ]
};
myChart1.setOption(biao);
}
function hg3(dom,ddate,zf,mf,df){
	var myChart2 = echarts.init(document.getElementById(dom));
	// 指定图表的配置项和数据
	var hfen = {
		title: {
			text: '历史表现',left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}
			},
			tooltip: {},
			//toolbox: {
			// feature: {
			//dataView: {show: true, readOnly: false},
			//}
			//},
			grid: {left: '2',right: '2',top: '15%',bottom: '3%',containLabel: true},
    	color:['#F2F2F2','#00CCFF','#F34100','#FFC016'],
			legend: {
				textStyle:{color:'#16C0FF',fontSize:15},
				icon:'Rect',
				itemHeight:8,
				itemWidth:10,
				data:['短期因素','中期因素','整体分数'],
				right:70,
				top:30,
				},
				dataZoom: [
				{
					type: 'inside',
					show: true,
					realtime: true,
					start:90,
					end:100,
					}
				],
				xAxis: {
					axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
					data: (function(){return ddate;})(),
					splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
					},
        yAxis: {boundaryGap: [0, '50%'],type: 'value',splitNumber:5,scale:true,axisLine:{show:true,lineStyle:{color:'#16C0FF'}},splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},},
        tooltip: {
            trigger: 'axis'
        },

            series: [{
                name: '短期因素',
                type: 'bar',
                data: (function(){return df;})(),
                },
                {
                name: '中期因素',
                type: 'bar',
                data: (function(){return mf;})(),
                },
                {
                name: '整体分数',
                type: 'line',
                data: (function(){return zf;})(),
                lineStyle:{normal:{"width":0.8}},
                }                
                ]
        };      
        // 使用刚指定的配置项和数据显示图表。
        myChart2.setOption(hfen);
}

function hg4(dom,zf){	
var myChart = echarts.init(document.getElementById(dom));

var option = {
	
	  title: {
        text: '板块推荐（前十）',left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}
    },
    grid: {left: '2',right: '2',top: '15%',bottom: '3%',containLabel: true},
    dataset: {
        source:  (function(){return zf;})()   
    //    [
    //        ['rank', 'amount', 'product'],
    //        [89.3, 58212, '军工'],
    //        [57.1, 78254, '国企改革'],
    //        [74.4, 41032, '雄安概念'],
    //        [50.1, 12755, '新能源汽车'],
    //        [89.7, 20145, '医药板块'],
    //        [68.1, 79146, '在线教育'],
    //        [19.6, 91852, '家电行业'],
    //        [10.6, 101852, '机械行业'],
    //        [32.7, 20112, '软件行业'],
    //        [50.1, 12755, '船舶制造']
    //    ]
    },
    grid: {containLabel: true},
    xAxis: {name: '分数',	axisLine:{show:true,lineStyle:{color:'#16C0FF'}},splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},},
    yAxis: {type: 'category',	axisLine:{show:true,lineStyle:{color:'#16C0FF'}},},
    visualMap: {
        orient: 'horizontal',
        left: 'center',
        min: 1,
        max: 10,
        text: ['高', '低'],
        textStyle:{color:'#10BFFF',},
        // Map the score column to color
        dimension: 0,
        inRange: {
            color: ['#F2F2F2', '#00CCFF']
        }
    },
    series: [
        {
            type: 'bar',
            encode: {
                // Map the "amount" column to X axis.
                x: 'amount',
                // Map the "product" column to Y axis
                y: 'product'
            }
        }
    ]
};
myChart.setOption(option);
}
function splitData(rawData) {
    var categoryData = [];
    var values = [];
    var volumns = [];
    for (var i = 0; i < rawData.length; i++) {
        categoryData.push(rawData[i].splice(0, 1)[0]);
        values.push(rawData[i]);
        //volumns.push(rawData[i][4]);
    }
    return {
        categoryData: categoryData,
        values: values
    };
}
function MA(data0,dayCount) {
    var result = [];
    for (var i = 0, len = data0.values.length; i < len; i++) {
        if (i < dayCount) {
            result.push('-');
            continue;
        }
        var sum = 0;
        for (var j = 0; j < dayCount; j++) {
            sum += data0.values[i - j][1];
        }
        result.push(sum / dayCount);
    }
    return result;
}
function GetDateStr(AddDayCount) { 
var dd = new Date(); 
dd.setDate(dd.getDate()+AddDayCount);//获取AddDayCount天后的日期 
var y = dd.getFullYear(); 
var m = dd.getMonth()+1;//获取当前月份的日期 
var d = dd.getDate(); 
return y+"-"+m+"-"+d; 
} 	
function kline1(title0,data0,dom){
	var dom1 = document.getElementById(dom);//节点
	var myChart = echarts.init(dom1);//图表节点
	$.get("qi/qi00005/data/"+data0, function (rawData) {
		var data0 = splitData(rawData);
		myChart.setOption(option = {
			//backgroundColor: '#eee',
			animation: false,
			title: {
				text: title0,
				left:'left',
	      textStyle:{color:'#FFC016',fontSize:16,fontWeight:'bold',},
	      top:'3px',
			},
			grid:{
			bottom:'30px',
			top:'50px',
			right:'30px',
			left:'50px',
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'line'
				}
			},
			legend:{
				data: ['日K线', 'MA5', 'MA10', 'MA20', 'MA30']
			},
			brush: {
				xAxisIndex:'all',
				brushLink:'all',
				outOfBrush: {
					colorAlpha: 0.1
				}
			},
			xAxis: {
				type: 'category',
        data: data0.categoryData,
	      splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
	      axisLine: {lineStyle:{color:'#16C0FF'}},
	      axisLabel:{color:'#16C0FF'},
	      splitNumber: 20,
	      min: 'dataMin',
	      max: 'dataMax'
      },
      yAxis: {boundaryGap: [0, '30%'],type: 'value',axisLabel: {formatter: '{value} %',color:'#16C0FF'},axisLine: {lineStyle:{color:'#16C0FF'}},splitArea: {show: false},splitNumber: 5,scale:true,splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},},
      dataZoom: [
      {
      	type: 'inside',
      	start: 95,
      	end: 100
      }
      ],
      series:[
      {
      	name: '日K线',
      	type: 'candlestick',
      	data: data0.values,
      	markPoint: {
      		label: {
      			normal: {
      				formatter: function (param) {
      					return param != null ? Math.round(param.value) : '';
      				}
      			}
      		},
      		data:[
      		{
      			name:'XX标点',
      			coord:['2016/1/7', 2300],
      			value:2300,
      			itemStyle:{
      				normal:{color: '#16C0FF'}
      			}
      		},
      		{
      			name:'最高值',
      			type:'max',
      			valueDim: 'highest'
      		},
      		{
      			name:'最低值',
      			type:'min',
      			valueDim: 'lowest'
      		},
      		{
      			name: '均值',
      			type: 'average',
      			valueDim: 'close'
      		}
      		],
      		tooltip: {
      			formatter: function (param) {
      				return param.name + '<br>' + (param.data.coord || '');
      			}
      		}
      	},
      	markLine: {
      		symbol: ['none', 'none'],
      		data: [
      		[
      		{
      			name:'从最低到最高',
      			type:'min',
      			valueDim:'lowest',
      			symbol:'circle',
      			symbolSize:10,
      			label:{
      				normal: {show: false},
      				emphasis: {show: false}
      			}
      		},
      		{
      			type:'max',
      			valueDim:'highest',
      			symbol:'circle',
      			symbolSize:10,
      			label:{
      				normal: {show: false},
      				emphasis: {show: false}
      			}
      		}
      	],
      	{
      		name:'最低线',
      		type:'min',
      		valueDim: 'close'
      	},
      	{
      		name:'最高线',
      		type:'max',
      		valueDim:'close'
      	}
      	]
      	}
      },
      {
      	name:'MA5',
      	type:'line',
      	data: MA(data0,5),
      	smooth: true,
      	lineStyle:{
      		normal:{opacity: 0.5}
      	}
      },
      {
      	name:'MA10',
      	type:'line',
      	data: MA(data0,10),
      	smooth: true,
      	lineStyle:{
      		normal:{opacity: 0.5}
      	}
      },
      {
      	name:'MA20',
      	type:'line',
      	data: MA(data0,20),
      	smooth: true,
      	lineStyle:{
      		normal:{opacity: 0.5}
      	}
      },
      {
      	name:'MA30',
      	type:'line',
      	data: MA(data0,30),
      	smooth: true,
      	lineStyle:{
      		normal: {opacity: 0.5}
      	}
      },
    ]
    },
    true
    );
  myChart.dispatchAction(
  {
  	type:'brush',
  	areas:[{brushType: 'lineX',coordRange: [GetDateStr(0),GetDateStr(0)],xAxisIndex: 0}],
  	//areas: [{brushType: 'lineX',coordRange: ['2016-01-08','2016-07-01'],xAxisIndex: 0}],
  	xAxisIndex:0
  }
  );
  });
}
//节点引发的数据折线图
function NodeLine1(ctable,h3,x1,x2,t2){
var myChart = echarts.init(document.getElementById(ctable));
var chqushit1 = {
    title: {
    	text: h3,
			left:'left',
      textStyle:{color:'#FFC016',fontSize:16,fontWeight:'bold',},
      top:'3px',
    	},
		grid:{
		bottom:'30px',
		top:'40px',
		right:'0px',
		left:'60px',
		},
		tooltip:{
			trigger:'axis',
		},
    color:['#FF0000'],
    legend: {
    	textStyle:{color:'#10BFFF'},
    	itemHeight:8,
    	itemWidth:10,
    	right:'30px',
    	top:'20px',
    	padding:0,
      data:[{name:t2,icon:'Rect'}],
    },
    dataZoom: [{	  
    type: 'inside',
    show: true,
    realtime: true,
    start: 0,
    end:100
		}],
  	xAxis: [{
  		type: 'category',
      data : (function(){return x1;})(),
      splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      axisLine: {lineStyle:{color:'#16C0FF'}},
      axisLabel:{color:'#16C0FF'},
      splitNumber: 20,
      min: 'dataMin',
      max: 'dataMax'
  	}],
    yAxis: [{boundaryGap: [0, '30%'],type: 'value',axisLabel: {formatter: '{value} %',color:'#16C0FF'},axisLine: {lineStyle:{color:'#16C0FF'}},splitArea: {show: false},splitNumber: 5,scale:true,splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},}],
    series: [
    {
    	name: t2,
    	type: 'line',
    	symbolSize:0.3,
    	lineStyle:{normal:{"width":1.5}},
    	data: (function(){return x2;})(),
    	}
    ]
};
myChart.setOption(chqushit1);
}
//节点引发的数据折线图
function NodeLine2(ctable,h3,x1,x2,x3,t2,t3){
var myChart = echarts.init(document.getElementById(ctable));
var chqushit1 = {
    title: {
    	text: h3,
			left:'left',
      textStyle:{color:'#FFC016',fontSize:16,fontWeight:'bold',},
      top:'3px',
    	},
		grid:{
		bottom:'30px',
		top:'40px',
		right:'0px',
		left:'60px',
		},
		tooltip:{
			trigger:'axis',
		},
    color:['#FF0000','#FFFF00'],
    legend: {
    	textStyle:{color:'#10BFFF'},
    	itemHeight:8,
    	itemWidth:10,
    	right:'30px',
    	top:'20px',
    	padding:0,
      data:[{name:t2,icon:'Rect'},{name:t3,icon:'Rect'}],
    },
    dataZoom: [{	  
    type: 'inside',
    show: true,
    realtime: true,
    start: 0,
    end:100
		}],
  	xAxis: [{
  		type: 'category',
      data : (function(){return x1;})(),
      splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      axisLine: {lineStyle:{color:'#16C0FF'}},
      axisLabel:{color:'#16C0FF'},
      splitNumber: 20,
      min: 'dataMin',
      max: 'dataMax'
  	}],
    yAxis: [{boundaryGap: [0, '30%'],type: 'value',axisLabel: {formatter: '{value} %',color:'#16C0FF'},axisLine: {lineStyle:{color:'#16C0FF'}},splitArea: {show: false},splitNumber: 5,scale:true,splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},}],
    series: [
    {
    	name: t2,
    	type: 'line',
    	symbolSize:0.3,
    	lineStyle:{normal:{"width":1.5}},
    	data: (function(){return x2;})(),
    	},
    {
    	name: t3,
    	type: 'line',
    	symbolSize:0.3,
    	lineStyle:{normal:{"width":1.5}},
    	data: (function(){return x3;})(),
    	}
    ]
};
myChart.setOption(chqushit1);
}
//节点引发的数据折线图
function NodeBar(ctable,h3,x1,x2){
var myChart = echarts.init(document.getElementById(ctable));
var chqushit1 = {
    title: {
    	text: h3,
      left: 'left',
      padding:0,
      textStyle:{color:'#FFC016',fontSize:15,fontWeight:'bold',}
    	},
    toolbox: {feature: {dataZoom: {yAxisIndex: false},}},
		grid:{
			bottom:'12%',
			top:'13%',
			right:'2%'
		},
    tooltip: {
    	trigger: 'axis',
    	formatter:function(params) {
        var txt  = '日期:'          + params[0]['name']+'<br />';
            txt += h3+':' + params[0]['value']+'%'+'<br />';
        return txt;
    }},
    color:['#E93F00','#FFFFF0','#FFC016','#FFC016'],
    legend: {
    	textStyle:{color:'#10BFFF'},
    	itemHeight:8,
    	itemWidth:10,
    	right:'15%',
    	top:'5%',
    	padding:0,
      data:[{name:h3,icon:'Rect'}],
    },
    dataZoom: [{	  
    type: 'inside',
    show: true,
    realtime: true,
    start: 100,
    end: 80
		}],
    xAxis : [
    {
    	type : 'category',
    	axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
    	axisLabel:{color:'#16C0FF'},
    	splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
    	data : (function(){return x1;})(),
    }
    ],
   yAxis: {boundaryGap: [0, '30%'],
   	type: 'value',
   	splitNumber:5,
   	scale:true,
     axisLine:{
     	show:true,
     	lineStyle:{
     		color:'#16C0FF'
     	}
     },
     axisLabel:{color:'#16C0FF'},
     splitLine:{
     	show:true,
     	lineStyle:{
     		color:'#16C0FF',
     		width:0.5,
     		type:'dotted'
     	}
     }
   	},
    series: [
    {
    	name: h3,
    	type: 'bar',
    	symbolSize:0.3,
    	lineStyle:{normal:{"width":1.5}},
    	data: (function(){return x2;})(),
    	}
    ]
};
myChart.setOption(chqushit1);
}
//节点引发的数据折线图
function	Fproduct(dom,title,var1,var2,var3,var4,var5,title1,title2,title3,title4){
	var	myChart=echarts.init(document.getElementById(dom));
	var	line1={
		title:{
			text:title,
			left:'left',
      textStyle:{color:'#FFC016',fontSize:16,fontWeight:'bold',},
      top:'3px',
		},
		grid:{
		bottom:'30px',
		top:'50px',
		right:'30px',
		left:'50px',
		},
		tooltip:{
			trigger:'axis',
		},
    color:['#FF0000','#FFFF00','#FFFFFF','#FF0000','#FFFF00','#FFFFFF'],
		legend:{
			right:10,
			top:15,
			textStyle:{color:'#16C0FF',fontSize:15},
			itemHeight:10,
			itemWidth:10,
			data:[{name:title1,icon:'Rect'},{name:title2,icon:'Rect'},{name:title3,icon:'Rect'},{name:title4,icon:'Rect'}],
		},
		
		dataZoom:[{
			type:'inside',
			show:true,
			realtime:true,
			start:70,
			end:100,
		}],
  	xAxis: [{
  		type: 'category',
      data : (function(){return var1;})(),
      splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      axisLine: {lineStyle:{color:'#16C0FF'}},
      axisLabel:{color:'#16C0FF'},
      splitNumber: 20,
      min: 'dataMin',
      max: 'dataMax'
  	}],
    yAxis: [{boundaryGap: [0, '30%'],type: 'value',axisLabel: {formatter: '{value} %',color:'#16C0FF'},axisLine: {lineStyle:{color:'#16C0FF'}},splitArea: {show: false},splitNumber: 5,scale:true,splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},},
    				{boundaryGap: ['100%', '300%'],show:true,axisLabel:{formatter: '{value} %',color:'#16C0FF'},axisLine: {lineStyle:{color:'#16C0FF'}},splitLine:{show:false}}],
    series : [{
                    "name":title1,
                    "type":"line",
                    "yAxisIndex": 0,
                    "symbolSize":0.1,
                    "lineStyle":{normal:{"width":1.5}},
                    "data":(function(){return var2;})(),
								},{
                    "name":title2,
                    "type":"line",
                    "yAxisIndex": 0,
                    "symbolSize":0.1,
                    "lineStyle":{normal:{"width":1.5}},
                    "data":(function(){return var3;})(),
              },{
                    "name":title3,
                    "type":"bar",
                    "barWidth": 3,
                    "barGap":0,
                    "yAxisIndex": 1,
                    "itemStyle":{normal:{color:'rgba(255,0,0,0.3)'}},
                    "data":(function(){return var4;})(),
								},{
                    "name":title4,
                    "type":"bar",
                    "barWidth": 3,
                    "barGap":0,
                    "yAxisIndex": 1,
                    "itemStyle":{normal:{color:'rgba(255,255,0,0.3)'}},
                    "data":(function(){return var5;})(),
								}
              
              ]
   	};      
   	myChart.setOption(line1);
}
//节点引发的数据折线图
function	WeeklyReportGrouph(dom,var1,var2,var3,var4,var5,title1,title2,title3,title4){
	var	myChart=echarts.init(document.getElementById(dom));
	var	line1={
		grid:{
		bottom:'30px',
		top:'30px',
		right:'10px',
		left:'50px',
		},
		tooltip:{
			trigger:'axis',
		},
    color:['#FFDCB4','#BCD2FF','#FF0000','#E46C0A'],
		legend:{
			right:20,
			top:3,
			textStyle:{color:'#16365C',fontSize:15},
			itemHeight:6,
			itemWidth:30,
			itemGap:15,
			data:[{name:title1,icon:'Rect'},{name:title2,icon:'Rect'},{name:title3,icon:'Rect'},{name:title4,icon:'Rect'}],
		},
		
		dataZoom:[{
			type:'inside',
			show:true,
			realtime:true,
			start:0,
			end:100,
		}],
  	xAxis: [{
  		type: 'category',
      data : (function(){return var1;})(),
      splitLine:{show:true,lineStyle:{color:'#16365C',width:0.5,type:'dotted'}},
      axisLine: {lineStyle:{color:'#16365C'}},
      axisLabel:{color:'#16365C'},
      splitNumber: 20,
      min: 'dataMin',
      max: 'dataMax'
  	}],
    yAxis: [{boundaryGap: [0, '30%'],type: 'value',axisLabel: {formatter: '{value} %',color:'#16365C'},axisLine: {lineStyle:{color:'#16365C'}},splitArea: {show: false},splitNumber: 5,scale:true,splitLine:{show:true,lineStyle:{color:'#16365C',width:0.5,type:'dotted'}},},
    				{boundaryGap: ['100%', '300%'],show:true,axisLabel:{formatter: '{value} %',color:'#16365C'},axisLine: {lineStyle:{color:'#16365C'}},splitLine:{show:false}}],
    series : [{
                    "name":title1,
                    "type":"line",
                    "areaStyle":{},
                    "yAxisIndex": 0,
                    "symbolSize":0.1,
                    "lineStyle":{normal:{"width":0.5}},
                    "data":(function(){return var2;})(),
								},{
                    "name":title2,
                    "type":"line",
                    "areaStyle":{},
                    "yAxisIndex": 0,
                    "symbolSize":0.1,
                    "lineStyle":{normal:{"width":0.5}},
                    "data":(function(){return var3;})(),
              },{
                    "name":title3,
                    "type":"line",
                    "yAxisIndex": 0,
                    "symbolSize":0.1,
                    "lineStyle":{normal:{"width":1.5}},
                    "data":(function(){return var4;})(),
								},{
                    "name":title4,
                    "type":"line",
                    "yAxisIndex": 0,
                    "symbolSize":0.1,
                    "lineStyle":{normal:{"width":1.5}},
                    "data":(function(){return var5;})(),
								}
              
              ]
   	};      
   	myChart.setOption(line1);
}
//有交互的关系图
function guanxitu(ds,title1,fd1,fd2){
	echarts.init(document.getElementById(ds)).dispose();
	var myChart = echarts.init(document.getElementById(ds));
	var option = {
		title: { text: title1 },
		tooltip: {
			formatter: function (x) {
				return x.data.des;
			}
		},
		animationEasingUpdate: 'quinticInOut',
		series: [
		{
			type: 'graph',
			layout: 'force',
			symbol:"rect",//circle,rect,roundRect,triangle,diamond,pin,arrow
			symbolSize: [100,30],
			roam: true,
			focusNodeAdjacency:true,
			edgeSymbol: ['circle', 'arrow'],
			edgeSymbolSize: [4, 10],
			force: {
				repulsion: 2000,
				edgeLength: [10, 50],
				layoutAnimation:false
			},
			draggable: true,
			itemStyle: {
				normal: {
					color: '#16C0FF'
				}
			},
			lineStyle: {
				normal: {
					width: 2,
					color: '#16C0FF'
				}
			},
			edgeLabel: {
				normal: {
					show: true,
					formatter: function (x) {
						return x.data.name;
					},
					textStyle: {
						fontSize: '12',
					}
				}
			},
			label: {
				normal: {
					show: true,
					textStyle: {
						color:'#16C0FF',
						fontSize:'14',
					}
				}
			},
			data:(function(){return fd1;})(),
			links:(function(){return fd2;})()
    }
    ]
  };
myChart.setOption(option);
myChart.on("click", function (param){
var tecode=	option.series[0].data[param.dataIndex].des;
var tename= option.series[0].data[param.dataIndex].name;
var echarts_group_var = trim(tecode.substring(eval(tecode.indexOf('<span style="display:none;">')+28),eval(tecode.indexOf('</span>'))));
//var biaoti='<p>'+tename+'<span class="wjbd" name="'+tename+'">维</span><span class="wjbd" name="'+tename+'">百</span>：</p>';
var biaoti='<h3>'+tename+'：</h3>';
//alert(echarts_group_var);
$.post("qi/qi00002/qi04635C/NodeC.php",{
	sid:"_04",
	sflag:"MEntityNote",
	sKey:echarts_group_var,
	},
function(data){
	data1=eval(trim(data));
	var x1='';
	for(var i=0;i<data1.length;i++){
		x1+=data1[i].Note;
		}
	$("#mq_main_lnb").append('<center><div class="DashNote">'+biaoti+'<p>'+x1+'</p></div></center>');
	
	$.post("qi/qi00002/qi04635C/NodeC.php",{
		sid:"_04",
		sflag:"Doc",
		sKey:echarts_group_var,
	},
	function(data2){
		if(data2.length>3){
		data3=eval(trim(data2))[0].Note.split(",");
		for(var i=0;i<data3.length;i++){
		$("#mq_main_lnb").append('<center><div class="DashNote"><center><img src="qi/qi00005/doc/'+data3[i]+'"/></center></div></center>');
			}
		}
		$.post("qi/qi00002/qi04635C/NodeC.php",{
			sid:"_04",
			sflag:"Data",
			sKey:echarts_group_var,
		},
		function(data4){
			var data5= eval(trim(data4));
			var ddate1=[];var close1=[];
			var dlen =data5.length;
			for(var i=0;i<dlen;i++){
				ddate1.push(data5[i].times);
				close1.push(data5[i].close1);
				}
				var NodeSid='NodeC_'+GenNonDuplicateID(1);
			$("#mq_main_lnb").append('<center><div class="DashNote"><center><div class="NodeCharts" id="'+NodeSid+'"/></div></center></div></center>');
			NodeLine(NodeSid,tename,ddate1,close1);
		$.post("qi/qi00002/qi04635C/NodeC.php",{
			sid:"_04",
			sflag:"Event",
			sKey:echarts_group_var,
		},
		function(data6){
			var data7= eval(trim(data6));
			var dlen =data7.length;
			for(var i=0;i<dlen;i++){ 
				$("#mq_main_lnb").append('<center><div class="DashNote"><h3>'+data7[i].NoStrTop+'</h3><p>'+data7[i].NoStrCon+'</p></div></center>');
				}
		//$("#mq_main_lnb").append(data6);	
			});
			
			});
		});
	});
$("#mq_main_lnb").scrollTop( $("#mq_main_lnb")[0].scrollHeight );
});

myChart.on("mouseover", function(data) {
//取消节点连接线触发效果
if (data.dataType == "edge") {
    myChart.dispatchAction({
        type: 'unfocusNodeAdjacency',
        seriesIndex: 0
    });
}
})
//myChart.on("contextmenu", function (param){ 
//WarnMessage('右键还没有定义事件！');
//$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
//});

}
//有交互的关系图之Z
function Zguanxitu(ds,title1,fd1,fd2){
	echarts.init(document.getElementById(ds)).dispose();
	var myChart = echarts.init(document.getElementById(ds));
	var option = {
		title: { text: title1 },
		tooltip: {
			formatter: function (x) {
				return x.data.des;
			}
		},
		animationEasingUpdate: 'quinticInOut',
		series: [
		{
			type: 'graph',
			layout: 'force',
			symbol:"rect",//circle,rect,roundRect,triangle,diamond,pin,arrow
			symbolSize: [100,30],
			roam: true,
			focusNodeAdjacency:true,
			edgeSymbol: ['circle', 'arrow'],
			edgeSymbolSize: [4, 10],
			force: {
				repulsion: 2000,
				edgeLength: [10, 50],
				layoutAnimation:false
			},
			draggable: true,
			itemStyle: {
				normal: {
					color: '#16C0FF'
				}
			},
			lineStyle: {
				normal: {
					width: 2,
					color: '#16C0FF'
				}
			},
			edgeLabel: {
				normal: {
					show: true,
					formatter: function (x) {
						return x.data.name;
					},
					textStyle: {
						fontSize: '12',
					}
				}
			},
			label: {
				normal: {
					show: true,
					textStyle: {
						color:'#16C0FF',
						fontSize:'14',
					}
				}
			},
			data:(function(){return fd1;})(),
			links:(function(){return fd2;})()
    }
    ]
  };
myChart.setOption(option);
myChart.on("click", function (param){
var tecode=	option.series[0].data[param.dataIndex].des;
var tename= option.series[0].data[param.dataIndex].name;
var echarts_group_var = trim(tecode.substring(eval(tecode.indexOf('<span style="display:none;">')+28),eval(tecode.indexOf('</span>'))));
//var biaoti='<p>'+tename+'<span class="wjbd" name="'+tename+'">维</span><span class="wjbd" name="'+tename+'">百</span>：</p>';
var biaoti='<h3>'+tename+'：</h3>';
//alert(echarts_group_var);
$.post("qi/qi00002/qi04635C/NodeC.php",{
	sid:"_04",
	sflag:"MEntityNote",
	sKey:echarts_group_var,
	},
function(data){
	data1=eval(trim(data));
	var x1='';
	for(var i=0;i<data1.length;i++){
		x1+=data1[i].Note;
		}
	$("#mq_main_lnb").append('<center><div class="DashNote">'+biaoti+'<p>'+x1+'</p></div></center>');
	
	$.post("qi/qi00002/qi04635C/NodeC.php",{
		sid:"_04",
		sflag:"Doc",
		sKey:echarts_group_var,
	},
	function(data2){
		if(data2.length>3){
		data3=eval(trim(data2))[0].Note.split(",");
		for(var i=0;i<data3.length;i++){
		$("#mq_main_lnb").append('<center><div class="DashNote"><center><img src="qi/qi00005/doc/'+data3[i]+'"/></center></div></center>');
			}
		}
		$.post("qi/qi00002/qi04635C/NodeC.php",{
			sid:"_04",
			sflag:"Data",
			sKey:echarts_group_var,
		},
		function(data4){
			var data5= eval(trim(data4));
			var ddate1=[];var close1=[];
			var dlen =data5.length;
			for(var i=0;i<dlen;i++){
				ddate1.push(data5[i].times);
				close1.push(data5[i].close1);
				}
				var NodeSid='NodeC_'+GenNonDuplicateID(1);
			$("#mq_main_lnb").append('<center><div class="DashNote"><center><div class="NodeCharts" id="'+NodeSid+'"/></div></center></div></center>');
			NodeLine(NodeSid,tename,ddate1,close1);
		$.post("qi/qi00002/qi04635C/NodeC.php",{
			sid:"_04",
			sflag:"Event",
			sKey:echarts_group_var,
		},
		function(data6){
			var data7= eval(trim(data6));
			var dlen =data7.length;
			for(var i=0;i<dlen;i++){ 
				$("#mq_main_lnb").append('<center><div class="DashNote"><h3>'+data7[i].NoStrTop+'</h3><p>'+data7[i].NoStrCon+'</p></div></center>');
				}
		//$("#mq_main_lnb").append(data6);	
			});
			
			});
		});
	});
$("#mq_main_lnb").scrollTop( $("#mq_main_lnb")[0].scrollHeight );
});

myChart.on("mouseover", function(data) {
//取消节点连接线触发效果
if (data.dataType == "edge") {
    myChart.dispatchAction({
        type: 'unfocusNodeAdjacency',
        seriesIndex: 0
    });
}
})
//myChart.on("contextmenu", function (param){ 
//WarnMessage('右键还没有定义事件！');
//$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
//});
}

//没有交互的关系图
function GxtNoInteractive(ds,title1,fd1,fd2){
	echarts.init(document.getElementById(ds)).dispose();
	var myChart = echarts.init(document.getElementById(ds));
	var option = {
		title: { text: title1 },
		tooltip: {
			formatter: function (x) {
				return x.data.des;
			}
		},
		animationEasingUpdate: 'quinticInOut',
		series: [
		{
			type: 'graph',
			layout: 'force',
			symbol:"rect",//circle,rect,roundRect,triangle,diamond,pin,arrow
			symbolSize: [100,30],
			roam: true,
			focusNodeAdjacency:true,
			edgeSymbol: ['circle', 'arrow'],
			edgeSymbolSize: [4, 10],
			force: {
				repulsion: 2000,
				edgeLength: [10, 50],
				layoutAnimation:false
			},
			draggable: true,
			itemStyle: {
				normal: {
					color: '#16C0FF'
				}
			},
			lineStyle: {
				normal: {
					width: 2,
					color: '#16C0FF'
				}
			},
			edgeLabel: {
				normal: {
					show: true,
					formatter: function (x) {
						return x.data.name;
					},
					textStyle: {
						fontSize: '12',
					}
				}
			},
			label: {
				normal: {
					show: true,
					textStyle: {
						color:'#16C0FF',
						fontSize:'14',
					}
				}
			},
			data:(function(){return fd1;})(),
			links:(function(){return fd2;})()
		}
		]
	};
	myChart.setOption(option);
	myChart.on("click", function (param){
		var tecode=	option.series[0].data[param.dataIndex].des;
		var tename= option.series[0].data[param.dataIndex].name;
		var echarts_group_var = trim(tecode.substring(eval(tecode.indexOf('<span style="display:none;">')+28),eval(tecode.indexOf('</span>'))));
		//alert(echarts_group_var);
	});
	myChart.on("mouseover", function(data) {
		//取消节点连接线触发效果
		if (data.dataType == "edge") {
			myChart.dispatchAction({
				type: 'unfocusNodeAdjacency',
				seriesIndex: 0
			});
		}
	})
}
function Lproduct(ctable,h2,x1,x2,x3,x4,x5,x6){
// 基于准备好的dom，初始化echarts实例
var myChart = echarts.init(document.getElementById(ctable));
// 指定图表的配置项和数据
var chqushit1 = {
    title: {
    	text: h2+'累计收益',
      left: 'left',
      padding:0,
      textStyle:{color:'#10BFFF',fontSize:15,fontWeight:'bold',}
    	},
    toolbox: {feature: {dataZoom: {yAxisIndex: false},}},
		grid:{
			bottom:'12%',
			top:'13%',
			right:'2%'
		},
    tooltip: {
    	show: true,
    	trigger: 'axis',
    	formatter:function(params) {
        var txt  = '日期:'        + params[0]['name'] +'<br />';
            txt += h2+'净值:'     + params[0]['value']+'%'+'<br />';
            txt += '上证指数:'    + params[1]['value']+'%'+'<br />';
            txt += '创业板指数:'  + params[2]['value']+'%'+'<br />';
            txt += '沪深300:'     + params[3]['value']+'%'+'<br />';
            txt += '中小板指数:'  + params[4]['value']+'%'+'<br />';
        return txt;
    }},
    color:['#E93F00','#FFC016','#CC3399','#00CCFF','#FFFFF0'],
    legend: {
    	textStyle:{color:'#10BFFF'},
    	itemHeight:8,
    	itemWidth:10,
    	right:'12%',
    	top:'7%',
    	padding:0,
      data:[h2+'净值','上证','创业板','沪深300','中小板'],
      icon:'Rect',
    },
    dataZoom: [{
	  type: 'inside',
    show: true,
    realtime: true,
    start: 100,
    end: 80
}],
    xAxis : [
    {
    	type : 'category',
    	axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
    	axisLabel:{color:'#16C0FF'},
    	splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
    	data : x1,
    }
    ],
    
   yAxis: {boundaryGap: [0, '30%'],
   	type: 'value',
   	splitNumber:5,
   	scale:true,
     axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
     axisLabel:{color:'#16C0FF'},
     splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}
   	},
    series: [{
        name: h2+'净值',
        symbolSize:0.3,                  
        lineStyle:{normal:{"width":1.5}},
        type: 'line',
        data: x2,
    },
    {   name: '上证',
        symbolSize:0.3,                  
        lineStyle:{normal:{"width":1.5}},
        type: 'line',
        data: x3,
    },
    {   name: '创业板',
        symbolSize:0.3,                  
        lineStyle:{normal:{"width":1.5}},
        type: 'line',
        data: x4,
    },
    {   name: '沪深300',
        symbolSize:0.3,                  
        lineStyle:{normal:{"width":1.5}},
        type: 'line',
        data: x5,
    },
    {   name: '中小板',
        symbolSize:0.3,                  
        lineStyle:{normal:{"width":1.5}},
        type: 'line',
        data: x6,
    }]
};
myChart.clear();
myChart.setOption(chqushit1); 
}

function Rproduct(ctable,h3,x1,x2){
// 基于准备好的dom，初始化echarts实例
var myChart = echarts.init(document.getElementById(ctable));
// 指定图表的配置项和数据
var chqushit1 = {
    title: {
    	text: '日波动',
      left: 'left',
      padding:0,
      textStyle:{color:'#10BFFF',fontSize:15,fontWeight:'bold',}
    	},
    toolbox: {feature: {dataZoom: {yAxisIndex: false},}},
		grid:{
			bottom:'12%',
			top:'13%',
			right:'2%'
		},
    tooltip: {
    	trigger: 'axis',
    	formatter:function(params) {
        var txt  = '日期:'          + params[0]['name']+'<br />';
            txt += h3+'日波动:' + params[0]['value']+'%'+'<br />';
        return txt;
    }},
    color:['#E93F00','#FFC016','#CC3399','#00CCFF','#FFFFF0'],
    legend: {
    	textStyle:{color:'#10BFFF'},
    	itemHeight:8,
    	itemWidth:10,
    	right:'15%',
    	top:'5%',
    	padding:0,
      data:[{name:'日波动',icon:'Rect'}],
    },
    dataZoom: [{	  
    type: 'inside',
    show: true,
    realtime: true,
    start: 100,
    end: 80
		}],
    xAxis : [
    {
    	type : 'category',
    	axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
    	axisLabel:{color:'#16C0FF'},
    	splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
    	data : x1,
    }
    ],
   yAxis: {boundaryGap: [0, '30%'],
   	type: 'value',
   	splitNumber:5,
   	scale:true,
     axisLine:{show:true,lineStyle:{color:'#16C0FF'}},
     axisLabel:{color:'#16C0FF'},
     splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}
   	},
    series: [{
        name: h3+'日波动',
        type: 'line', 
        symbolSize:0.3,                  
        lineStyle:{normal:{"width":1.5}},
        data: x2,
    }]
    
};
myChart.clear();
myChart.setOption(chqushit1);
}
function mxhxfb(ctable,h2,x1){
var dom2 = document.getElementById(ctable);//节点
var myChart2 = echarts.init(dom2);//图表节点
chqushit2 = {
    title : {
    	text: '行业分布',
      left: 'left',
      padding:0,
      textStyle:{color:'#10BFFF',fontSize:15,fontWeight:'bold',}
    },
    grid:{
			bottom:'12%',
			top:'13%',
			right:'2%'
		},
    tooltip : {
        trigger: 'item',
        formatter: "{a} <br/>{b} : {c} ({d}%)"
    },
    color:['#FF0033','#FF9966','#0099CC','#FF6666','#666699','#CC9999','#CC3399','#993366','#66CCCC','#FF6600'],
    series : [
        {
            name: '行业分布',
            type: 'pie',
            radius : '75%',
            center: ['55%', '60%'],
            data:(function(){return x1;})(),
            itemStyle: {
                emphasis: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }
    ]
};
if (chqushit2 && typeof chqushit2 === "object") {
    myChart2.setOption(chqushit2, true);
    myChart2.resize();    
}	 
}

function treetu(ds,data){
	echarts.init(document.getElementById(ds)).dispose();
	var myChart = echarts.init(document.getElementById(ds));
	echarts.util.each(data.children, function (datum, index) {
		index % 2 === 0 && (datum.collapsed = true);
	});
	option = {
		tooltip: {
			trigger: 'item',
			triggerOn: 'mousemove',
      textStyle:{color:'#FFFFFF',fontSize:15,fontWeight:'bold',}
		},
		series:[
		{
			type: 'tree',
			data: [data],
			top: '1%',
			left: '15%',
			bottom: '1%',
			right: '7%',
			symbol: 'Rect',
			symbolSize: 7,
			orient: 'RL',
			itemStyle: {
				normal: {
					color:'#FFF',
					borderWidth: 1,
					borderColor: '#FFC016'
				}
			},
			label: {
				position: 'right',
				verticalAlign: 'middle',
				align: 'left',
				textStyle:{color:'#10BFFF',fontSize:15,},
			},
			lineStyle: {
				normal: {
					width: 1,
					color: '#16C0FF'
				},
			},
			leaves: {
				label: {
					position: 'left',
					verticalAlign: 'middle',
					align: 'right'
				}
			},
			expandAndCollapse: true,
			animationDuration: 550,
			animationDurationUpdate: 750
		}
		]
	}
	myChart.setOption(option);
	/*
	myChart.on("contextmenu", function (param){
		//var echarts_tree_var = param.dataIndex+':'+option.series[0].data[param.dataIndex]['name'];
		var echarts_tree_var = '尚未定义右键事件！';
		WarnMessage(echarts_tree_var);
		$(document).off("click","#Yes").on("click","#Yes",function(){$(this).parent().parent().remove();});
	}
	);
	*/
}

function Test3D(ctable){
var myChart = echarts.init(document.getElementById(ctable));
        var title = {
            text: '3d散点图',
        };
        var xAxis3D={
            type: 'value'
        };
        var yAxis3D={
           type: 'value'
        };
        var zAxis3D = {
           type: 'value'
        };
        var grid3D={};
        var series = [
            {
                type: 'scatter3D', //设置图表类型为3d散点图
                data: [[0, 0, 5], [0, 1, 1], [0, 2, 0], [0, 3, 0], [0, 4, 0], [0, 5, 0], [0, 6, 0], [0, 7, 0], [0, 8, 0], [0, 9, 0], [0, 10, 0], [0, 11, 2], [0, 12, 4], [0, 13, 1], [0, 14, 1], [0, 15, 3], [0, 16, 4], [0, 17, 6], [0, 18, 4], [0, 19, 4], [0, 20, 3], [0, 21, 3], [0, 22, 2], [0, 23, 5], [1, 0, 7], [1, 1, 0], [1, 2, 0], [1, 3, 0], [1, 4, 0], [1, 5, 0], [1, 6, 0], [1, 7, 0], [1, 8, 0], [1, 9, 0], [1, 10, 5], [1, 11, 2], [1, 12, 2], [1, 13, 6], [1, 14, 9], [1, 15, 11], [1, 16, 6], [1, 17, 7], [1, 18, 8], [1, 19, 12], [1, 20, 5], [1, 21, 5], [1, 22, 7], [1, 23, 2], [2, 0, 1], [2, 1, 1], [2, 2, 0], [2, 3, 0], [2, 4, 0], [2, 5, 0], [2, 6, 0], [2, 7, 0], [2, 8, 0], [2, 9, 0], [2, 10, 3], [2, 11, 2], [2, 12, 1], [2, 13, 9], [2, 14, 8], [2, 15, 10], [2, 16, 6], [2, 17, 5], [2, 18, 5], [2, 19, 5], [2, 20, 7], [2, 21, 4], [2, 22, 2], [2, 23, 4], [3, 0, 7], [3, 1, 3], [3, 2, 0], [3, 3, 0], [3, 4, 0], [3, 5, 0], [3, 6, 0], [3, 7, 0], [3, 8, 1], [3, 9, 0], [3, 10, 5], [3, 11, 4], [3, 12, 7], [3, 13, 14], [3, 14, 13], [3, 15, 12], [3, 16, 9], [3, 17, 5], [3, 18, 5], [3, 19, 10], [3, 20, 6], [3, 21, 4], [3, 22, 4], [3, 23, 1], [4, 0, 1], [4, 1, 3], [4, 2, 0], [4, 3, 0], [4, 4, 0], [4, 5, 1], [4, 6, 0], [4, 7, 0], [4, 8, 0], [4, 9, 2], [4, 10, 4], [4, 11, 4], [4, 12, 2], [4, 13, 4], [4, 14, 4], [4, 15, 14], [4, 16, 12], [4, 17, 1], [4, 18, 8], [4, 19, 5], [4, 20, 3], [4, 21, 7], [4, 22, 3], [4, 23, 0], [5, 0, 2], [5, 1, 1], [5, 2, 0], [5, 3, 3], [5, 4, 0], [5, 5, 0], [5, 6, 0], [5, 7, 0], [5, 8, 2], [5, 9, 0], [5, 10, 4], [5, 11, 1], [5, 12, 5], [5, 13, 10], [5, 14, 5], [5, 15, 7], [5, 16, 11], [5, 17, 6], [5, 18, 0], [5, 19, 5], [5, 20, 3], [5, 21, 4], [5, 22, 2], [5, 23, 0], [6, 0, 1], [6, 1, 0], [6, 2, 0], [6, 3, 0], [6, 4, 0], [6, 5, 0], [6, 6, 0], [6, 7, 0], [6, 8, 0], [6, 9, 0], [6, 10, 1], [6, 11, 0], [6, 12, 2], [6, 13, 1], [6, 14, 3], [6, 15, 4], [6, 16, 0], [6, 17, 0], [6, 18, 0], [6, 19, 0], [6, 20, 1], [6, 21, 2], [6, 22, 2], [6, 23, 6]],
                lineStyle: {
                    width: 4
                }
            },
        ];
        var json = {};
        json.title = title;
        json.xAxis3D = xAxis3D;
        json.yAxis3D = yAxis3D;
        json.zAxis3D = zAxis3D;
        json.grid3D = grid3D;
        json.series = series;
        // 为echarts对象加载数据
        myChart.setOption(json);
}


//实时市场数据函数
function Tkpiline1(myChart,chqushit,cdom,ctitle1,ctitle2,x1,x2){ 		
 eval(myChart+" = echarts.init(document.getElementById(cdom));"+
  chqushit+" = {"
          +"title: {text: ctitle1,left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}},"
          +"tooltip: {trigger: 'axis',"
          +"formatter:function(params) {"
          +" var txt  = '时间  :'          + params[0]['name']+'<br />';"
          +"      txt += ctitle2 + params[0]['value']+'家.'+'占比:'+(Math.round(params[0]['value']/totalnum*10000)/100).toFixed(2)+'%'+'<br />';  "
          +"  return txt;"
          +"}},"
					+"grid:{bottom:'12%',top:'13%',right:'2%'},"
          +"color:['#F34100','#FFC016','#F2F2F2','#00CCFF'],"
          +"legend: {textStyle:{color:'#16C0FF',fontSize:12},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:4,data:[{name:ctitle2,icon:'Rect'}],},"
          +"dataZoom: [{type: 'inside',show: true,realtime: true,start: 100,end: 0}],"
          +"xAxis : [{type : 'category',"
          +"    				axisLine:{show:true,lineStyle:{color:'#16C0FF'}},"
          +"    				splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},"
          +"           data:(function(){return x1;})()"
          +"          }],"
          +"  yAxis: {boundaryGap: [0, '30%'],type: 'value',splitNumber:5,scale:true,"
          +"    axisLine:{show:true,lineStyle:{color:'#16C0FF'}},"
          +"    splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}"
          +"  	},"
          +"  series : [{name:ctitle2,type:'line',symbolSize:0.3,lineStyle:{normal:{width:1}},data:(function(){return x2;})()}"
          +"  ]};  "
+"if ("+chqushit+" && typeof("+chqushit+") === 'object') {"+myChart+".setOption("+chqushit+", true);"+myChart+".resize();}"
)} 
function Tkpiline1up(myChart,ctitle2,x1,x2){ 		
 eval(myChart+".setOption({xAxis : [{type : 'category',data : (function(){return x1;})()}],"
      +"series : [{name:ctitle2,type:'line',data:(function(){return x2;})()"
    	+"}]});"
)} 

function Tkpiline2(myChart,chqushit,cdom,ctitle1,ctitle2,ctitle3,x1,x2,x3){ 		
	eval(myChart+" = echarts.init(document.getElementById(cdom));"+
  chqushit+" = {"
      +" title: {text: ctitle1,left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}},"
			+"grid:{bottom:'12%',top:'13%',right:'2%'},"
      +" tooltip: {trigger: 'axis',"
      +"	formatter:function(params) {"
      +"   var txt  = '时间  :'          + params[0]['name']+'<br />';"
      +"        txt += ctitle3 + params[0]['value']+'家.'+'占比:'+(Math.round(params[0]['value']/totalnum*10000)/100).toFixed(2)+'%'+'<br />';  "
      +"        txt += ctitle2 + params[1]['value']+'家.'+'占比:'+(Math.round(params[1]['value']/totalnum*10000)/100).toFixed(2)+'%'+'<br />';  "
      +"    return txt;"
      +" }},"
      +"color:['#F34100','#FFC016','#F2F2F2','#00CCFF'],"
      +" legend: {textStyle:{color:'#16C0FF',fontSize:12},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:4,"
      +"    data:[{name:ctitle2,icon:'Rect'},{name:ctitle3,icon:'Rect'}],},"
      +" dataZoom: [{type: 'inside',show: true,realtime: true,start: 100,end: 0}],"
      +" xAxis : [{type : 'category',"
      +"    				axisLine:{show:true,lineStyle:{color:'#16C0FF'}},"
      +"    				splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},"
      +"           data : (function(){return x1;})()}],"
      +"  yAxis: {boundaryGap: [0, '30%'],type: 'value',splitNumber:5,scale:true,"
      +"    axisLine:{show:true,lineStyle:{color:'#16C0FF'}},"
      +"    splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}"
      +"  	},"
      +"  /*visualMap: [{show: false,seriesIndex:1,pieces: [{lte: 30,color: '#ffff00'},{gt: 30,lte: 50,color: '#28ff28'},{"
      +"       gt: 50,lte:100,color: '#ff0000'}, {gt: 100,color: '#ff2d2d'}]},{show: false,seriesIndex:0,pieces: [{"
      +"       gt: 0,color: '#ffffff'}]}],*/"
      +"  series : [{name:ctitle2,type:'line',symbolSize:0.3,lineStyle:{normal:{'width':1}},data:(function(){return x2;})()},"
      +"  					 {name:ctitle3,type:'line',symbolSize:0.3,lineStyle:{normal:{'width':1}},data:(function(){return x3;})()}"
      +"            ]};"
			+"if ("+chqushit+" && typeof ("+chqushit+") === 'object') {"+myChart+".setOption("+chqushit+", true);"+myChart+".resize();}	"
)} 
function Tkpiline2up(myChart,ctitle2,ctitle3,x1,x2,x3){ 		
   eval(myChart+".setOption({xAxis : [{type : 'category',data : (function(){return x1;})()}],"
            +"series : [{name:ctitle2,type:'line',data:(function(){return x2;})()},"
            +"					{name:ctitle3,type:'line',data:(function(){return x3;})()}]});"
)} 
//组合及时跟踪
function zhline(myChart,chqushit,cdom,ctitle,x1,x2,x3,x4){
	eval(myChart+"= echarts.init(document.getElementById(cdom));"+
	chqushit+" = {"
       +"title: {text: ctitle+'盘中跟踪',left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}},"
			 +"grid:{bottom:'12%',top:'13%',right:'1%',left:'7%',},"
       +"tooltip: {trigger: 'axis',formatter:function(params) {"
       +"         var txt  = '时间:'          + params[0]['name']+'<br />';"
       +"             txt += '净值:' + params[0]['value']+'<br />';"
       +"             txt += '上证:' + params[1]['value']+'<br />';"
       +"             txt += '创业:' + params[2]['value']+'<br />';"
       +"         return txt;}},"
       +"color:['#F34100','#FFC016','#F2F2F2','#00CCFF'],"      
       +"legend: {textStyle:{color:'#16C0FF'},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:0,icon:'Rect',data:['净值','上证','创业'],},"
       +"dataZoom: [{type: 'inside',show: true,realtime: true,start: 100,end: 0}],"
       +"xAxis : [{type : 'category',axisLine:{show:true,lineStyle:{color:'#16C0FF'}},splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},"
       +"          data : (function(){ return x1;})()}],   "      
       +"yAxis: {boundaryGap: [0, '30%'],type: 'value',splitNumber:5,scale:true,"
       +"       axisLine:{show:true,lineStyle:{color:'#16C0FF'}},splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}},  "        	
			 +"series : [{name:'净值',type:'line',symbolSize:0.3,lineStyle:{normal:{width:1.5}},data:(function(){return x2;})()},"
			 +"         {name:'上证',type:'line',symbolSize:0.3,lineStyle:{normal:{width:1.5}},data:(function(){return x3;})()},"
			 +"         {name:'创业',type:'line',symbolSize:0.3,lineStyle:{normal:{width:1.5}},data:(function(){return x4;})()}]"
			+"};"
			+"if ("+chqushit+" && typeof("+chqushit+") === 'object') {"+myChart+".setOption("+chqushit+", true);"+myChart+".resize();}"
			)}
function zhlineup(myChart,x1,x2,x3,x4){
	eval(myChart+".setOption({"
	+"xAxis : [{type : 'category',data : (function(){return x1;})()}],"
	+"series : [{name:'净值',type:'line',data:(function(){return x2;})()},"
  +"        {name:'上证',type:'line',data:(function(){return x3;})()},"
  +"        {name:'创业',type:'line',data:(function(){return x4;})()}]});"
	)}	
function zhbar(myChart,chqushit,cdom,ctitle,x1,x2,x3){
	eval(myChart+" = echarts.init(document.getElementById(cdom));"+
	chqushit+" = {"
			+"title: {text: ctitle,left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}},"
   		+"tooltip : {trigger: 'axis',axisPointer : {type : 'shadow'}},"
   		+"legend: {textStyle:{color:'#16C0FF',fontSize:12},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:0,icon:'Rect',data:['正贡献','负贡献'],},"
   		+"dataZoom: [{type: 'inside',show: true,realtime: true,start: 100,end: 0}],"
    	+"grid: {left: '2',right: '2',top: '15%',bottom: '3%',containLabel: true},"
    	+"xAxis: {axisLabel: {rotate: 60,interval:0,textStyle:{color:'#16C0FF',fontSize:12,}},axisLine:{show:true,lineStyle:{color:'#16C0FF'}},type : 'category',data : (function(){return x1;})()},"
     	+"yAxis: {type : 'value',axisLine:{show:true,lineStyle:{color:'#16C0FF'}},splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}},"
     	+"series: [{name: '正贡献',type: 'bar',label: {normal: {show:  true,position: 'bottom'}},stack: '总量',itemStyle:{normal:{color:'#F34100'}},data: (function(){return x2;})()},"
			+"{name: '负贡献',type: 'bar',label: {normal: {show:  true,position: 'top'}},stack: '总量',itemStyle:{normal:{color:'#00FF80'}},data: (function(){return x3})()"
			+"}]};"
			+"if ("+chqushit+" && typeof("+chqushit+") === 'object') {"+myChart+".setOption("+chqushit+", true);"+myChart+".resize();}"
)}
function zhbarup(myChart,x1,x2,x3){		
	eval(myChart+".setOption({"
    	+"xAxis: {axisLabel: {rotate: 60,interval:0,textStyle:{color:'#16C0FF',fontSize:12,}},axisLine:{show:true,lineStyle:{color:'#16C0FF'}},type : 'category',data : (function(){return x1;})()},"
     	+"yAxis: {type : 'value',axisLine:{show:true,lineStyle:{color:'#16C0FF'}},splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}}},"
     	+"series: [{name: '正贡献',type: 'bar',label: {normal: {show:  true,position: 'bottom'}},stack: '总量',itemStyle:{normal:{color:'#F34100'}},data: (function(){return x2;})()},"
			+"{name: '负贡献',type: 'bar',label: {normal: {show:  true,position: 'top'}},stack: '总量',itemStyle:{normal:{color:'#00FF80'}},"
	+"					data:(function(){return x3;})()}]});"
	)}

function Szhbar(myChart,chqushit,cdom,ctitle,x1,x2,x3){
	eval(myChart+" = echarts.init(document.getElementById(cdom));"+
	chqushit+" = {"
			+"title: {text: ctitle,left: 'left',padding:4,textStyle:{color:'#FFFFFF',fontSize:15,}},"
   		+"tooltip : {trigger: 'axis',axisPointer : {type : 'shadow'}},"
   		+"legend: {textStyle:{color:'#16C0FF',fontSize:12},itemHeight:8,itemWidth:10,right:'5%',top:'5%',padding:0,icon:'Rect',data:['正贡献','负贡献'],},"
    	+"grid: {left: '2',right: '2',top: '8%',bottom: '2',containLabel: true},"
      +"xAxis : [{type : 'category',axisLine:{show:true,lineStyle:{color:'#16C0FF'}},"
      +"	splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},type : 'value'}],"
      +"yAxis:[{type : 'category',axisLabel: {rotate: 0,interval:0,textStyle:{color:'#16C0FF',fontSize:12,}},axisTick : {show: false},data : (function(){return x1;})()}],"
      +"series:[{name:'正贡献',type:'bar',stack: '总量',barWidth: 10,barGap:1,itemStyle:{normal:{color:'#F34100'}},label: {normal: {show:true,position: 'left'}},data:(function(){return x2;})()}, " 
			+" {name:'负贡献',type:'bar',stack: '总量',barWidth: 10,barGap:1,itemStyle:{normal:{color:'#00FF80'}},label: {normal: {show:true,position:'right'}},data:(function(){return x3;})()"
			+" }]};"
			+"if ("+chqushit+" && typeof("+chqushit+") === 'object') {"+myChart+".setOption("+chqushit+", true);"+myChart+".resize();}"
)}
function Szhbarup(myChart,x1,x2,x3){		
	eval(myChart+".setOption({"
      +"yAxis:[{type : 'category',axisTick : {show: false},data : (function(){return x1;})()}],"
      +"series:[{name:'正贡献',type:'bar',stack: '总量',barWidth: 10,barGap:1,itemStyle:{normal:{color:'#F34100'}},label: {normal: {show:true,position: 'left'}},data:(function(){return x2;})()}, " 
			+" {name:'负贡献',type:'bar',stack: '总量',barWidth: 10,barGap:1,itemStyle:{normal:{color:'#00FF80'}},label: {normal: {show:true,position:'right'}},"
			+"	data:(function(){return x3;})()}]});"
	)}




function Surface3D(ctable,data0){
	
	var myChart = echarts.init(document.getElementById(ctable));
	
		option = {
		    tooltip: {},
		    //backgroundColor: '#fff',
		    visualMap: {
		        show: false,
		        dimension: 2,
		        min: -1,
		        max: 1,
		        inRange: {
		            color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
		        }
		    },
		    xAxis3D: {
		        type: 'value',
        		min: 'dataMin',
      			max: 'dataMax',
      			splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      			axisLine: { onZero: false,lineStyle:{color:'#16C0FF'}},
      			axisPointer:{lineStyle: {color: '#16C0FF',}}
		    },
		    yAxis3D: {
		        type: 'value',
        		min: 'dataMin',
      			max: 'dataMax',
      			splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      			axisLine: { onZero: false,lineStyle:{color:'#16C0FF'}},
      			axisPointer:{lineStyle: {color: '#16C0FF',}}
		    },
		    zAxis3D: {
		        type: 'value',
        		min: 'dataMin',
      			max: 'dataMax',
      			splitLine:{show:true,lineStyle:{color:'#16C0FF',width:0.5,type:'dotted'}},
      			axisLine: { onZero: false,lineStyle:{color:'#16C0FF'}},
      			axisPointer:{lineStyle: {color: '#16C0FF',}}
		    },
		    grid3D: {
		        viewControl: {
		            // projection: 'orthographic'
		        }
		    },
		    series: [{
		        type: 'surface',
		        wireframe: {
		            // show: false
		        },
		        
		        /*
		        equation: {
		            x: {
		                step: 0.05
		            },
		            y: {
		                step: 0.05
		            },
		            z: function (x, y) {
		                if (Math.abs(x) < 0.1 && Math.abs(y) < 0.1) {
		                    return '-';
		                }
		                return Math.sin(x * Math.PI) * Math.sin(y * Math.PI);
		            }
		        }
		        */
				//data:eval(data0)
				data:(function(){return eval(data0);})(),
		    }]
		}
	myChart.setOption(option);
}










//结构流程图
function Topology(cdom,xx,yy){
	echarts.init(document.getElementById(cdom)).dispose();
	var myChart= echarts.init(document.getElementById(cdom));

	var nodes = [{
		x:'5',
		y:'5',
		name:'服务器',
		alarm: '产生告警了哦'
		},
		{
			x:'3',
			y:'0',
			name:'存储设备1',
		},
		{
			x: '7',
			y: '0',
			name: '存储设备2',
		},
		{
			x: '0',
			y: '10',
			name: '防火墙',
		},
	    {
	        x: '5',
	        y: '10',
	        name: '网络设备1',
	        alarm: '产生告警了哦'
	    },
	    {
	        x: '12',
	        y: '12',
	        name: '网络设备2',
	    }
	]
	var links = [{
	        source: '存储设备2',
	        target: '存储设备1',
	        name: '数据传输'
	    }, {
	        source: '存储设备1',
	        target: '服务器',
	        name: '数据传输'
	    },
	    {
	        source: '服务器',
	        target: '防火墙',
	        name: '访问'
	    },
	    {
	        source: '防火墙',
	        target: '网络设备1',
	        name: '访问'
	    },
	    {
	        source: '网络设备1',
	        target: '网络设备2',
	        name: '访问'
	    }
	]
	var charts = {
	    nodes: [],
	    links: [],
	    linesData: []
	}
	var dataMap = new Map()
	for (var j = 0; j < nodes.length; j++) {
	    var x = parseInt(nodes[j].x)
	    var y = parseInt(nodes[j].y)
	    var node = {
	        name: nodes[j].name,
	        value: [x, y],
	        symbolSize: 10,
	        alarm: nodes[j].alarm,
	        symbol: nodes[j].name,
	        itemStyle: {
	            normal: {
	                color: '#16C0FF',
	            }
	        }
	    }
	    dataMap.set(nodes[j].name, [x, y])
	    charts.nodes.push(node)
	}
	for (var i = 0; i < links.length; i++) {
	    var link = {
	        source: links[i].source,
	        target: links[i].target,
	        label: {
	            normal: {
	                show: true,
	                formatter: links[i].name
	            }
	        },
	        lineStyle: {
	            normal: {
	                color: '#16C0FF'
	            }
	        }
	    }
	    charts.links.push(link)
	    // 组装动态移动的效果数据
	    var lines = [{
	        coord: dataMap.get(links[i].source)
	    }, {
	        coord: dataMap.get(links[i].target)
	    }]
	    charts.linesData.push(lines)
	}
	option = {
	    title: {
			text: '系统运行',
			left: 'left',
			padding:4,
			textStyle:{color:'#FFFFFF',fontSize:15,}
			},
	    xAxis: {
	        show: false,
	        type: 'value'
	    },
	    yAxis: {
	        show: false,
	        type: 'value'
	    },
	    series: [{
	        type: 'graph',
	        layout: 'none',
	        coordinateSystem: 'cartesian2d',
	        symbolSize: 10,
	        label: {
	            normal: {
	                show: true,
	                position: 'bottom',
	                color: '#16C0FF'
	            }
	        },
	        lineStyle: {
	            normal: {
	                width: 2,
	                shadowColor: 'none'
	            }
	        },
	        edgeSymbolSize: 8,
	        data: charts.nodes,
	        links: charts.links,
	        itemStyle: {
	            normal: {
	                label: {
	                    show: true,
	                    formatter: function(item) {
	                        return item.data.name
	                    }
	                }
	            }
	        }
	    }, {
	        name: 'A',
	        type: 'lines',
	        coordinateSystem: 'cartesian2d',
	        effect: {
	            show: true,
	            trailLength: 0,
	            symbol: 'arrow',
	            color: '#16C0FF',
	            symbolSize: 8
	        },
	        data: charts.linesData
	    }]
	};
	// 用于告警的动态效果
	xx=setInterval(() => {
	    var dataI = []
	    for (var n = 0; n < nodes.length; n++) {
	        var alarm = nodes[n].alarm
	        if (alarm !== null && alarm !== '' && alarm !== undefined) {
	            option.series[0].data[n].symbolSize = 60
	            option.series[0].data[n].label = {
	                normal: {
	                    color: '#DC143C'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                if (item.data.alarm !== undefined) {
	                    return item.data.name + '\n[ ' + item.data.alarm + ' ]'
	                } else {
	                    return item.data.name
	                }
	            }
	            dataI.push(n)
	        }
	    }
	    myChart.setOption(option)
	yy=setTimeout(() => {
	        for (var m = 0; m < dataI.length; m++) {
	            option.series[0].data[dataI[m]].symbolSize = 50
	            option.series[0].data[dataI[m]].label = {
	                normal: {
	                    color: '#16C0FF'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                return item.data.name
	            }
	        }
	        myChart.setOption(option)
	    }, 500)
	}, 1000)
}



//数据流
function shujuliu(cdom,xx,yy){
	echarts.init(document.getElementById(cdom)).dispose();
	var myChart= echarts.init(document.getElementById(cdom));

	var nodes = [{
		x:'5',
		y:'5',
		name:'因子库',
		alarm: '查看问题'
		},
		{
			x:'3',
			y:'0',
			name:'数据库',
		},
		{
			x: '7',
			y: '0',
			name: '外部数据',
		},
		{
			x: '0',
			y: '10',
			name: '衍生变量',
		},
	    {
	        x: '5',
	        y: '10',
	        name: '模型集合',
	        alarm: '产生告警了哦'
	    },
	    {
	        x: '12',
	        y: '12',
	        name: '交易服务器',
	    }
	]
	var links = [{
	        source: '外部数据',
	        target: '数据库',
	        name: '数据ETL'
	    }, {
	        source: '数据库',
	        target: '因子库',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '衍生变量',
	        name: '计算'
	    },
	    {
	        source: '衍生变量',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '模型集合',
	        target: '交易服务器',
	        name: '输出'
	    }
	]
	var charts = {
	    nodes: [],
	    links: [],
	    linesData: []
	}
	var dataMap = new Map()
	for (var j = 0; j < nodes.length; j++) {
	    var x = parseInt(nodes[j].x)
	    var y = parseInt(nodes[j].y)
	    var node = {
	        name: nodes[j].name,
	        value: [x, y],
	        symbolSize: 10,
	        alarm: nodes[j].alarm,
	        symbol: nodes[j].name,
	        itemStyle: {
	            normal: {
	                color: '#16C0FF',
	            }
	        }
	    }
	    dataMap.set(nodes[j].name, [x, y])
	    charts.nodes.push(node)
	}
	for (var i = 0; i < links.length; i++) {
	    var link = {
	        source: links[i].source,
	        target: links[i].target,
	        label: {
	            normal: {
	                show: true,
	                formatter: links[i].name
	            }
	        },
	        lineStyle: {
	            normal: {
	                color: '#16C0FF'
	            }
	        }
	    }
	    charts.links.push(link)
	    // 组装动态移动的效果数据
	    var lines = [{
	        coord: dataMap.get(links[i].source)
	    }, {
	        coord: dataMap.get(links[i].target)
	    }]
	    charts.linesData.push(lines)
	}
	option = {
	    title: {
			text: '系统运行',
			left: 'left',
			padding:4,
			textStyle:{color:'#FFFFFF',fontSize:15,}
			},
	    xAxis: {
	        show: false,
	        type: 'value'
	    },
	    yAxis: {
	        show: false,
	        type: 'value'
	    },
	    series: [{
	        type: 'graph',
	        layout: 'none',
	        coordinateSystem: 'cartesian2d',
	        symbolSize: 10,
	        label: {
	            normal: {
	                show: true,
	                position: 'bottom',
	                color: '#16C0FF'
	            }
	        },
	        lineStyle: {
	            normal: {
	                width: 2,
	                shadowColor: 'none'
	            }
	        },
	        edgeSymbolSize: 8,
	        data: charts.nodes,
	        links: charts.links,
	        itemStyle: {
	            normal: {
	                label: {
	                    show: true,
	                    formatter: function(item) {
	                        return item.data.name
	                    }
	                }
	            }
	        }
	    }, {
	        name: 'A',
	        type: 'lines',
	        coordinateSystem: 'cartesian2d',
	        effect: {
	            show: true,
	            trailLength: 0,
	            symbol: 'arrow',
	            color: '#16C0FF',
	            symbolSize: 8
	        },
	        data: charts.linesData
	    }]
	};
	// 用于告警的动态效果
	xx=setInterval(() => {
	    var dataI = []
	    for (var n = 0; n < nodes.length; n++) {
	        var alarm = nodes[n].alarm
	        if (alarm !== null && alarm !== '' && alarm !== undefined) {
	            option.series[0].data[n].symbolSize = 60
	            option.series[0].data[n].label = {
	                normal: {
	                    color: '#FFFF00'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                if (item.data.alarm !== undefined) {
	                    return item.data.name + '\n[ ' + item.data.alarm + ' ]'
	                } else {
	                    return item.data.name
	                }
	            }
	            dataI.push(n)
	        }
	    }
	    myChart.setOption(option)
	yy=setTimeout(() => {
	        for (var m = 0; m < dataI.length; m++) {
	            option.series[0].data[dataI[m]].symbolSize = 50
	            option.series[0].data[dataI[m]].label = {
	                normal: {
	                    color: '#16C0FF'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                return item.data.name
	            }
	        }
	        myChart.setOption(option)
	    }, 500)
	}, 1000)
}

//系统监控
function xitongjiankong(cdom,xx,yy){
	echarts.init(document.getElementById(cdom)).dispose();
	var myChart= echarts.init(document.getElementById(cdom));

	var nodes = [{
		x:'5',
		y:'5',
		name:'因子库',
		alarm: '查看问题'
		},
		{
			x:'3',
			y:'0',
			name:'数据库',
		},
		{
			x: '7',
			y: '0',
			name: '外部数据',
		},
		{
			x: '0',
			y: '10',
			name: '衍生变量',
		},
	    {
	        x: '5',
	        y: '10',
	        name: '模型集合',
	        alarm: '产生告警了哦'
	    },
	    {
	        x: '12',
	        y: '12',
	        name: '交易服务器',
	    }
	]
	var links = [{
	        source: '外部数据',
	        target: '数据库',
	        name: '数据ETL'
	    }, {
	        source: '数据库',
	        target: '因子库',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '衍生变量',
	        name: '计算'
	    },
	    {
	        source: '衍生变量',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '模型集合',
	        target: '交易服务器',
	        name: '输出'
	    }
	]
	var charts = {
	    nodes: [],
	    links: [],
	    linesData: []
	}
	var dataMap = new Map()
	for (var j = 0; j < nodes.length; j++) {
	    var x = parseInt(nodes[j].x)
	    var y = parseInt(nodes[j].y)
	    var node = {
	        name: nodes[j].name,
	        value: [x, y],
	        symbolSize: 10,
	        alarm: nodes[j].alarm,
	        symbol: nodes[j].name,
	        itemStyle: {
	            normal: {
	                color: '#16C0FF',
	            }
	        }
	    }
	    dataMap.set(nodes[j].name, [x, y])
	    charts.nodes.push(node)
	}
	for (var i = 0; i < links.length; i++) {
	    var link = {
	        source: links[i].source,
	        target: links[i].target,
	        label: {
	            normal: {
	                show: true,
	                formatter: links[i].name
	            }
	        },
	        lineStyle: {
	            normal: {
	                color: '#16C0FF'
	            }
	        }
	    }
	    charts.links.push(link)
	    // 组装动态移动的效果数据
	    var lines = [{
	        coord: dataMap.get(links[i].source)
	    }, {
	        coord: dataMap.get(links[i].target)
	    }]
	    charts.linesData.push(lines)
	}
	option = {
	    title: {
			text: '系统运行',
			left: 'left',
			padding:4,
			textStyle:{color:'#FFFFFF',fontSize:15,}
			},
	    xAxis: {
	        show: false,
	        type: 'value'
	    },
	    yAxis: {
	        show: false,
	        type: 'value'
	    },
	    series: [{
	        type: 'graph',
	        layout: 'none',
	        coordinateSystem: 'cartesian2d',
	        symbolSize: 10,
	        label: {
	            normal: {
	                show: true,
	                position: 'bottom',
	                color: '#16C0FF'
	            }
	        },
	        lineStyle: {
	            normal: {
	                width: 2,
	                shadowColor: 'none'
	            }
	        },
	        edgeSymbolSize: 8,
	        data: charts.nodes,
	        links: charts.links,
	        itemStyle: {
	            normal: {
	                label: {
	                    show: true,
	                    formatter: function(item) {
	                        return item.data.name
	                    }
	                }
	            }
	        }
	    }, {
	        name: 'A',
	        type: 'lines',
	        coordinateSystem: 'cartesian2d',
	        effect: {
	            show: true,
	            trailLength: 0,
	            symbol: 'arrow',
	            color: '#16C0FF',
	            symbolSize: 8
	        },
	        data: charts.linesData
	    }]
	};
	// 用于告警的动态效果
	xx=setInterval(() => {
	    var dataI = []
	    for (var n = 0; n < nodes.length; n++) {
	        var alarm = nodes[n].alarm
	        if (alarm !== null && alarm !== '' && alarm !== undefined) {
	            option.series[0].data[n].symbolSize = 60
	            option.series[0].data[n].label = {
	                normal: {
	                    color: '#FFFF00'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                if (item.data.alarm !== undefined) {
	                    return item.data.name + '\n[ ' + item.data.alarm + ' ]'
	                } else {
	                    return item.data.name
	                }
	            }
	            dataI.push(n)
	        }
	    }
	    myChart.setOption(option)
	yy=setTimeout(() => {
	        for (var m = 0; m < dataI.length; m++) {
	            option.series[0].data[dataI[m]].symbolSize = 50
	            option.series[0].data[dataI[m]].label = {
	                normal: {
	                    color: '#16C0FF'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                return item.data.name
	            }
	        }
	        myChart.setOption(option)
	    }, 500)
	}, 1000)
}


//IT架构
function itjiagou(cdom,xx,yy){
	echarts.init(document.getElementById(cdom)).dispose();
	var myChart= echarts.init(document.getElementById(cdom));

	var nodes = [{
		x:'5',
		y:'5',
		name:'因子库',
		alarm: '查看问题'
		},
		{
			x:'3',
			y:'0',
			name:'数据库',
		},
		{
			x: '7',
			y: '0',
			name: '外部数据',
		},
		{
			x: '0',
			y: '10',
			name: '衍生变量',
		},
	    {
	        x: '5',
	        y: '10',
	        name: '模型集合',
	        alarm: '产生告警了哦'
	    },
	    {
	        x: '12',
	        y: '12',
	        name: '交易服务器',
	    }
	]
	var links = [{
	        source: '外部数据',
	        target: '数据库',
	        name: '数据ETL'
	    }, {
	        source: '数据库',
	        target: '因子库',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '衍生变量',
	        name: '计算'
	    },
	    {
	        source: '衍生变量',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '模型集合',
	        target: '交易服务器',
	        name: '输出'
	    }
	]
	var charts = {
	    nodes: [],
	    links: [],
	    linesData: []
	}
	var dataMap = new Map()
	for (var j = 0; j < nodes.length; j++) {
	    var x = parseInt(nodes[j].x)
	    var y = parseInt(nodes[j].y)
	    var node = {
	        name: nodes[j].name,
	        value: [x, y],
	        symbolSize: 10,
	        alarm: nodes[j].alarm,
	        symbol: nodes[j].name,
	        itemStyle: {
	            normal: {
	                color: '#16C0FF',
	            }
	        }
	    }
	    dataMap.set(nodes[j].name, [x, y])
	    charts.nodes.push(node)
	}
	for (var i = 0; i < links.length; i++) {
	    var link = {
	        source: links[i].source,
	        target: links[i].target,
	        label: {
	            normal: {
	                show: true,
	                formatter: links[i].name
	            }
	        },
	        lineStyle: {
	            normal: {
	                color: '#16C0FF'
	            }
	        }
	    }
	    charts.links.push(link)
	    // 组装动态移动的效果数据
	    var lines = [{
	        coord: dataMap.get(links[i].source)
	    }, {
	        coord: dataMap.get(links[i].target)
	    }]
	    charts.linesData.push(lines)
	}
	option = {
	    title: {
			text: '系统运行',
			left: 'left',
			padding:4,
			textStyle:{color:'#FFFFFF',fontSize:15,}
			},
	    xAxis: {
	        show: false,
	        type: 'value'
	    },
	    yAxis: {
	        show: false,
	        type: 'value'
	    },
	    series: [{
	        type: 'graph',
	        layout: 'none',
	        coordinateSystem: 'cartesian2d',
	        symbolSize: 10,
	        label: {
	            normal: {
	                show: true,
	                position: 'bottom',
	                color: '#16C0FF'
	            }
	        },
	        lineStyle: {
	            normal: {
	                width: 2,
	                shadowColor: 'none'
	            }
	        },
	        edgeSymbolSize: 8,
	        data: charts.nodes,
	        links: charts.links,
	        itemStyle: {
	            normal: {
	                label: {
	                    show: true,
	                    formatter: function(item) {
	                        return item.data.name
	                    }
	                }
	            }
	        }
	    }, {
	        name: 'A',
	        type: 'lines',
	        coordinateSystem: 'cartesian2d',
	        effect: {
	            show: true,
	            trailLength: 0,
	            symbol: 'arrow',
	            color: '#16C0FF',
	            symbolSize: 8
	        },
	        data: charts.linesData
	    }]
	};
	// 用于告警的动态效果
	xx=setInterval(() => {
	    var dataI = []
	    for (var n = 0; n < nodes.length; n++) {
	        var alarm = nodes[n].alarm
	        if (alarm !== null && alarm !== '' && alarm !== undefined) {
	            option.series[0].data[n].symbolSize = 60
	            option.series[0].data[n].label = {
	                normal: {
	                    color: '#FFFF00'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                if (item.data.alarm !== undefined) {
	                    return item.data.name + '\n[ ' + item.data.alarm + ' ]'
	                } else {
	                    return item.data.name
	                }
	            }
	            dataI.push(n)
	        }
	    }
	    myChart.setOption(option)
	yy=setTimeout(() => {
	        for (var m = 0; m < dataI.length; m++) {
	            option.series[0].data[dataI[m]].symbolSize = 50
	            option.series[0].data[dataI[m]].label = {
	                normal: {
	                    color: '#16C0FF'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                return item.data.name
	            }
	        }
	        myChart.setOption(option)
	    }, 500)
	}, 1000)
}



//组织架构
function zuzhijiagou(cdom,xx,yy){
	echarts.init(document.getElementById(cdom)).dispose();
	var myChart= echarts.init(document.getElementById(cdom));

	var nodes = [{
		x:'5',
		y:'5',
		name:'因子库',
		alarm: '查看问题'
		},
		{
			x:'3',
			y:'0',
			name:'数据库',
		},
		{
			x: '7',
			y: '0',
			name: '外部数据',
		},
		{
			x: '0',
			y: '10',
			name: '衍生变量',
		},
	    {
	        x: '5',
	        y: '10',
	        name: '模型集合',
	        alarm: '产生告警了哦'
	    },
	    {
	        x: '12',
	        y: '12',
	        name: '交易服务器',
	    }
	]
	var links = [{
	        source: '外部数据',
	        target: '数据库',
	        name: '数据ETL'
	    }, {
	        source: '数据库',
	        target: '因子库',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '衍生变量',
	        name: '计算'
	    },
	    {
	        source: '衍生变量',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '因子库',
	        target: '模型集合',
	        name: '计算'
	    },
	    {
	        source: '模型集合',
	        target: '交易服务器',
	        name: '输出'
	    }
	]
	var charts = {
	    nodes: [],
	    links: [],
	    linesData: []
	}
	var dataMap = new Map()
	for (var j = 0; j < nodes.length; j++) {
	    var x = parseInt(nodes[j].x)
	    var y = parseInt(nodes[j].y)
	    var node = {
	        name: nodes[j].name,
	        value: [x, y],
	        symbolSize: 10,
	        alarm: nodes[j].alarm,
	        symbol: nodes[j].name,
	        itemStyle: {
	            normal: {
	                color: '#16C0FF',
	            }
	        }
	    }
	    dataMap.set(nodes[j].name, [x, y])
	    charts.nodes.push(node)
	}
	for (var i = 0; i < links.length; i++) {
	    var link = {
	        source: links[i].source,
	        target: links[i].target,
	        label: {
	            normal: {
	                show: true,
	                formatter: links[i].name
	            }
	        },
	        lineStyle: {
	            normal: {
	                color: '#16C0FF'
	            }
	        }
	    }
	    charts.links.push(link)
	    // 组装动态移动的效果数据
	    var lines = [{
	        coord: dataMap.get(links[i].source)
	    }, {
	        coord: dataMap.get(links[i].target)
	    }]
	    charts.linesData.push(lines)
	}
	option = {
	    title: {
			text: '系统运行',
			left: 'left',
			padding:4,
			textStyle:{color:'#FFFFFF',fontSize:15,}
			},
	    xAxis: {
	        show: false,
	        type: 'value'
	    },
	    yAxis: {
	        show: false,
	        type: 'value'
	    },
	    series: [{
	        type: 'graph',
	        layout: 'none',
	        coordinateSystem: 'cartesian2d',
	        symbolSize: 10,
	        label: {
	            normal: {
	                show: true,
	                position: 'bottom',
	                color: '#16C0FF'
	            }
	        },
	        lineStyle: {
	            normal: {
	                width: 2,
	                shadowColor: 'none'
	            }
	        },
	        edgeSymbolSize: 8,
	        data: charts.nodes,
	        links: charts.links,
	        itemStyle: {
	            normal: {
	                label: {
	                    show: true,
	                    formatter: function(item) {
	                        return item.data.name
	                    }
	                }
	            }
	        }
	    }, {
	        name: 'A',
	        type: 'lines',
	        coordinateSystem: 'cartesian2d',
	        effect: {
	            show: true,
	            trailLength: 0,
	            symbol: 'arrow',
	            color: '#16C0FF',
	            symbolSize: 8
	        },
	        data: charts.linesData
	    }]
	};
	// 用于告警的动态效果
	xx=setInterval(() => {
	    var dataI = []
	    for (var n = 0; n < nodes.length; n++) {
	        var alarm = nodes[n].alarm
	        if (alarm !== null && alarm !== '' && alarm !== undefined) {
	            option.series[0].data[n].symbolSize = 60
	            option.series[0].data[n].label = {
	                normal: {
	                    color: '#FFFF00'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                if (item.data.alarm !== undefined) {
	                    return item.data.name + '\n[ ' + item.data.alarm + ' ]'
	                } else {
	                    return item.data.name
	                }
	            }
	            dataI.push(n)
	        }
	    }
	    myChart.setOption(option)
	yy=setTimeout(() => {
	        for (var m = 0; m < dataI.length; m++) {
	            option.series[0].data[dataI[m]].symbolSize = 50
	            option.series[0].data[dataI[m]].label = {
	                normal: {
	                    color: '#16C0FF'
	                }
	            }
	            option.series[0].itemStyle.normal.label.formatter = function(item) {
	                return item.data.name
	            }
	        }
	        myChart.setOption(option)
	    }, 500)
	}, 1000)
}
