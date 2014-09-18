// CONSTANTS
var DATA_ANALYSIS_TYPES = ["best-fit", "goal", "average", "stdev"];
var NUM_OF_DATA_ANALYSIS_TYPES = DATA_ANALYSIS_TYPES.length;
var DATA_ANALYSIS_OPACITY = {max: 1, mid: 0.5, min: 0.2, hide: 0};

function updateAllDataAnalysis() {
	for(var i = 0; i < NUM_OF_DATA_ANALYSIS_TYPES; i++)
		updateDataAnalysis(DATA_ANALYSIS_TYPES[i]);
}

function drawAllDataAnalysis(id, color, data, goal) {
	var xOffset = 0;
	for(var i = 0; i < NUM_OF_DATA_ANALYSIS_TYPES; i++) {		
		if(DATA_ANALYSIS_TYPES[i] == "goal")
			xOffset = drawDataAnalysis(id, color, goal, DATA_ANALYSIS_TYPES[i], xOffset);
		else if(DATA_ANALYSIS_TYPES[i] == "best-fit" && data.length != 1 )
			xOffset = drawDataAnalysis(id, color, data, DATA_ANALYSIS_TYPES[i], xOffset);
		else
			xOffset = drawDataAnalysis(id, color, data, DATA_ANALYSIS_TYPES[i], xOffset);
	}
}

function eraseAllDataAnalysis(id) {
	// REMOVE AVERAGE LINE
	d3.select("#" + id + "-average").remove();
	// REMOVE AVERAGE LINE LABEL
	d3.select("#" + id + "-average-label").remove();
	// REMOVE AVERAGE LINE
	d3.select("#" + id + "-goal").remove();
	// REMOVE AVERAGE LINE LABEL
	d3.select("#" + id + "-goal-label").remove();
	// REMOVE BESTFIT LINE
    d3.select("#" + id + "-best-fit").remove();
    // REMOVE BESTFIT LINE LABEL
    d3.select("#" + id + "-best-fit-label").remove();
    // REMOVE STDEV LINE
    d3.select("#" + id + "-stdev").remove();
    // REMOVE STDEV LINE LABEL
    d3.select("#" + id + "-stdev-label").remove();
}

// type can be : "average", "goal", "best-fit", "stdev" 
function updateDataAnalysis(type) {
	var opacity = DATA_ANALYSIS_OPACITY.mid;
	var labelOpacity = DATA_ANALYSIS_OPACITY.max;
	if($('#'+type).prop('checked') && symptomInfoStack.length <= 2) { 
		opacity = DATA_ANALYSIS_OPACITY.mid;
		labelOpacity = DATA_ANALYSIS_OPACITY.max;
	} else { 
		opacity = DATA_ANALYSIS_OPACITY.hide;
		labelOpacity = DATA_ANALYSIS_OPACITY.hide;
	}
	var translate = function(d) {
						return "translate(" + xScale(d.date) + "," + yScale(d.value) + ")";
					};
	if( type == "best-fit" ) {
		translate = function (d) {
    					var s = (yScale(d.minY) -  yScale(d.maxY)) / (xScale(d.maxX) - xScale(d.minX));
						var angle = - (Math.atan(s) * (180 / Math.PI));
         				return "translate(" + xScale(d.maxX) + "," + yScale(d.maxY) + ")rotate(" + angle + ")";
    				};
	} 
	else if(type == "stdev") {
		if( opacity == DATA_ANALYSIS_OPACITY.mid ) { 
			opacity = DATA_ANALYSIS_OPACITY.min; 
			labelOpacity = DATA_ANALYSIS_OPACITY.max;
		}
	}
	var line = d3.svg.line()
					 .x(function (d) { return xScale(d.date); })
					 .y(function (d) { return yScale(d.value); });
					 
	// LINE LABELS
	svg.selectAll("."+type+"-label")
			.each(function(i) {
				d3.select(this)
					.transition()
					  .duration(SCALE_DURATION)
					  .attr("transform", translate)
					  .attr("opacity", labelOpacity);
			});
	// LINE PATHS
	pathContainer.selectAll("."+ type +"-line")
			.each(function(i) {
				d3.select(this)
					.transition()
					  .duration(SCALE_DURATION)
					  .attr("opacity", opacity)
				      .attr("d", line);
				console.log(">> "+type+" line rescale...");
			});

}

// type can be : "average", "goal", "best-fit", "stdev" 
// returns xOffset to somewhat spread out labels [NOTE: there is room for improvement]
function drawDataAnalysis(id, color, data, type, xOffset) {
	var opacity = DATA_ANALYSIS_OPACITY.mid;
	var labelOpacity = DATA_ANALYSIS_OPACITY.max;
	var line;
	var info = "";
	var lineData = [];
	var labelData = [];
	var path;
	var label;
	var translate;
	var strokeWidth;
	var yOffset = -2;
	var strokeDash = "none";

    if (data.length < 2 ){
        return xOffset;
    }

	if($('#'+type).prop('checked') && symptomInfoStack.length <= 2) { 
		opacity = DATA_ANALYSIS_OPACITY.mid;
		labelOpacity = DATA_ANALYSIS_OPACITY.max;
	} else { 
		opacity = DATA_ANALYSIS_OPACITY.hide;
		labelOpacity = DATA_ANALYSIS_OPACITY.hide;
	}
	// DEFAULT LINE & TRANSLATE
	line = d3.svg.line()
				   .x(function (d) { return xScale(d.date); })
				   .y(function (d) { return yScale(d.value); });
	translate = function(d) {
						return "translate(" + xScale(d.date) + "," + yScale(d.value) + ")";
					};
	
	if( type == "average" ) {
		lineData = calcAverage(data);
		labelData = lineData[1];
		info = id.replace("-", " ") + " " + type + " (" + lineData[1].value.toString() + ")";
		strokeWidth = 2;
		strokeDash = "15,15";
		console.log(">> average text length = " + info.length);
	}
	else if( type == "goal" ) {
		lineData.push({date: USER_CREATION_DATE, value: data});
		lineData.push({date: xDomain.max, value: data});
		labelData = lineData[1];
		console.log( lineData[1].value.toString() );
		info = id.replace("-", " ") + " " + "target"+ " (" + lineData[1].value.toString() + ")";
		strokeWidth = 2;
		console.log(">> goal text length = " + info.length);		
	}
	else if( type == "best-fit" && data.length > 1) { 
		lineData = calcBestFit(data);
		labelData = { minX: lineData[0].date,
    				  minY: lineData[0].value,
    				  maxX: lineData[1].date,
    				  maxY: lineData[1].value,
    				};
		info = id.replace("-", " ") + " " + type;
		var s = (yScale(labelData.minY) -  yScale(labelData.maxY)) / (xScale(labelData.maxX) - xScale(labelData.minX));
		var angle = - (Math.atan(s) * (180 / Math.PI));
    	translate = function (d) {
        				return "translate(" + xScale(d.maxX) + "," + yScale(d.maxY) + ")rotate(" + angle + ")";
    				};
    	strokeWidth = 4;
    	yOffset = -3;
    	console.log(">> bestfit text length = " + info.length);    	
	}
	else if( type == "stdev" ) {
		var stdev = d3.round(calcStdev(data), 1);
		var mean = d3.round( d3.mean(data, function(d){ return d.value; }), 1 );
		lineData.push({date: USER_CREATION_DATE, value: (mean - stdev)});
		lineData.push({date: USER_CREATION_DATE, value: (mean + stdev)});
		lineData.push({date: xDomain.max, value: (mean - stdev)});
		lineData.push({date: xDomain.max, value: (mean + stdev)});
		labelData = lineData[3];
		if( opacity == DATA_ANALYSIS_OPACITY.mid ) { 
			opacity = DATA_ANALYSIS_OPACITY.min;
			labelOpacity = DATA_ANALYSIS_OPACITY.max; 
		}
		info = id.replace("-", " ") + " " + type + " (±" + stdev.toString() + ")"; 
		console.log(">> stdev text length = " + info.length);
		yOffset = -3;
	}
	// determine x coord of label
	if(xOffset == 0) {
		xOffset = -(info.length * 5);
	} else {
		if(-xOffset > w / 4 && w < 300) 
			xOffset += -(info.length * 2.5);
		else
			xOffset += -(info.length * 7);
	}
	
	// LINE LABEL 	
	var label = svg.selectAll(".non-existent-class")
					   .data([labelData])
					   .enter()
					   .append("text")
						 .attr("transform", translate )
						 .attr("class", type+"-label")
						 .attr("id", id+"-"+type+"-label")
						 .attr("x", xOffset)
						 .attr("y", yOffset)
						 .attr("fill", color)
						 .attr("opacity", labelOpacity)
						 .style("font-size","10px")
						 .text(info);
	
	// LINE PATH
  	var path = pathContainer.selectAll(".non-existent-class")
							 .data([lineData])
							 .enter()
							   .append("path")
							   .attr("class", type+"-line")
							   .attr("id", id+"-"+type)
							   .attr("stroke", color)
			     			   .attr("fill", color)
			     			   .attr("stroke-width", strokeWidth)
			     			   .style("stroke-dasharray", strokeDash) 
							   .attr("opacity", opacity)
							   .attr("d", line);

	// TRANSITIONS
	label.transition()
		  .duration(DRAW_LINE_DURATION)
		  .attr("opacity", labelOpacity);
	path.transition()
		 .duration(DRAW_LINE_DURATION)
		 .attr("opacity", opacity);
	
	console.log("> Done "+ type +" line: " + id);
	return xOffset;
}

// HELPER FUNCTIONS
function calcBestFit(data) {
    var BestFitData = [];
	var minTime = d3.min(data, function(d) { return (new Date(d.date)).getTime(); });
	var maxTime = d3.max(data, function(d) { return (new Date(d.date)).getTime(); });
	var minDate = new Date();
	minDate.setTime(minTime);
	var maxDate = new Date();
	maxDate.setTime(maxTime);
    var count = data.length;
    var sumX = d3.sum(data, function (d) { return xScale(new Date(d.date)) });
    var sumY = d3.sum(data, function (d) { return (d.value) });

    var sumX2 = d3.sum(data, function (d) { return (xScale(new Date(d.date)) * xScale(new Date(d.date))) });
    var sumXY = d3.sum(data, function (d) { return (xScale(new Date(d.date)) * (d.value)) });
    var XMean = sumX / count;
    var YMean = sumY / count;
    var slope = (sumXY - sumX * YMean) / (sumX2 - sumX * XMean);
    var YInt = YMean - (slope * XMean);
	
	var minYValue = xScale(minDate) * slope + YInt;
	var maxYValue = xScale(maxDate) * slope + YInt;

    BestFitData.push({ date: minDate, value: minYValue});
    BestFitData.push({ date: maxDate, value: maxYValue});

    return BestFitData;
}

function calcStdev(data) {
	var numOfData = data.length;
	var mean = (d3.mean(data, function(d) { return d.value; }));
	var sqrdiff = [];
	for(var i = 0; i < numOfData; i++) {
		sqrdiff.push(Math.pow((data[i].value - mean), 2));
	}
	var variance = d3.sum(sqrdiff) / numOfData;	
		
	return Math.sqrt(variance);  
}

function calcAverage(data) {
	var averageData = [];
	var average = d3.round( d3.mean(data, function(d) { return d.value }), 1);	
	averageData.push({date: USER_CREATION_DATE, value: average});
	averageData.push({date: xDomain.max, value: average});

	return averageData;
}
