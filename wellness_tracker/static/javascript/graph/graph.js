// CONSTANTS
var isMobile = false;
if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
 	isMobile = true;
}

// ABSOLUTE OLDEST DATE: This should be the date the user first made his/her account
var USER_CREATION_DATE = new Date("1920/1/1");

var MARGIN = { top: 15, right: 70, left: 70, bottom: 30  };
var WIDTH = { max: 1000, min: 225};
var HEIGHT = { max: 800, min: 200}; 

// used for rescaling transitions 
var SCALE_DURATION = 750;

// used for drawing line graph
var DRAW_LINE_DURATION = 1250;

// number of ticks on x axis
var X_TICKS_DEFAULT = 5;
if(document.getElementById("graph").offsetWidth - MARGIN.left - MARGIN.right < 300)
	X_TICKS_DEFAULT = 3;
// number of ticks on y axis
var Y_TICKS_DEFAULT = 8;

// radius of data points
var RADIUS = 6.5;

// default opacity of data points
var DATA_POINT_OPACITY = 0.5;

var monthName = new Array(12);
monthName[0]="Jan";
monthName[1]="Feb";
monthName[2]="Mar";
monthName[3]="Apr";
monthName[4]="May";
monthName[5]="June";
monthName[6]="July";
monthName[7]="Aug";
monthName[8]="Sept";
monthName[9]="Oct";
monthName[10]="Nov";
monthName[11]="Dec";

var dayOfWeek = new Array(7);
dayOfWeek[0] = "Sun";
dayOfWeek[1] = "Mon";
dayOfWeek[2] = "Tue";
dayOfWeek[3] = "Wed";
dayOfWeek[4] = "Thur";
dayOfWeek[5] = "Fri";
dayOfWeek[6] = "Sat";

// creating dates for time scale
var date = new Date();
// today
var TODAY = date.getFullYear() + "/" + (date.getMonth() + 1).toString() + "/" + date.getDate();

// a week ago
date = new Date();
date.setDate(date.getDate() - 7);
var ONE_WEEK_AGO = date.getFullYear() + "/" + (date.getMonth() + 1).toString() + "/" + date.getDate();

// two weeks ago
date = new Date();
date.setDate(date.getDate() - 14);
var TWO_WEEK_AGO = date.getFullYear() + "/" + (date.getMonth() + 1).toString() + "/" + date.getDate();

// one months ago
date = new Date();
date.setMonth(date.getMonth() - 1);
var ONE_MONTH_AGO = date.getFullYear() + "/" + (date.getMonth() + 1).toString() + "/" + date.getDate();

// six months ago
date = new Date();
date.setMonth(date.getMonth() - 6);
var SIX_MONTH_AGO = date.getFullYear() + "/" + (date.getMonth() + 1).toString() + "/" + date.getDate();

// a year ago
date = new Date();
date.setFullYear(date.getFullYear() - 1);
var ONE_YEAR_AGO = date.getFullYear() + "/" + (date.getMonth() + 1).toString() + "/" + date.getDate();


// GLOBAL VARIABLES
var w = document.getElementById("graph").offsetWidth - MARGIN.left - MARGIN.right;
var h = w - 200 - MARGIN.top - MARGIN.bottom;

// check to see if width or height exceeded dimension limits
if(w < WIDTH.min) 		 { w = WIDTH.min; }
if( h > HEIGHT.max )	 { h = HEIGHT.max;} 
else if( h < HEIGHT.min) { h = HEIGHT.min;}

// stack used to keep track of symptom info
var symptomInfoStack = [];

/* svg CONTAINS: 
	- x & y axis 
    - average labels 
    - x & y grid lines 
    - all data points*/
var svg;

/* PATH CONTAINER CONTAINS: 
	- all data lines
 	- average line
 	- goal line */
var pathContainer;

var xScale;
var yScale;

var xAxis;
var yAxis;
var y;

var xGrid;
var yGrid;

var maxX = new Date(TODAY);
var minX = new Date(ONE_WEEK_AGO);
var xDomain = { min: minX, max: maxX };


// FUNCTIONS

function initGraph() {
	svg = d3.select("svg")
				 .attr("id", "graph-container")
				 .attr("class", "graph-container")
				 .attr("height", MARGIN.top + h + MARGIN.bottom)
				 .attr("width", MARGIN.left + w + MARGIN.right )
				 .attr("transform", "translate(" + (MARGIN.left).toString() + "," + (MARGIN.top).toString() + ")");
	
	pathContainer = svg.append("svg")
							.attr("id", "line-container")
							.attr("height", h)
							.attr("width", w);
	// X & Y SCALE
	var maxY = 10;
	updateScales(maxY);
	//	X & Y GRID	
	xGrid = d3.svg.axis()
					.scale(xScale)
                   	.orient("bottom")
					.tickSize(-h, 0, 0)
					.tickFormat("")
					.ticks(X_TICKS_DEFAULT);
	yGrid = d3.svg.axis()
					.scale(yScale)
					.orient("left")
					.tickSize(-w, 0, 0)
					.tickFormat("")
					.ticks(Y_TICKS_DEFAULT);		
	pathContainer.append("g")         
			.attr("class", "grid")
			.attr("id", "xGrid")
			.attr("transform", "translate(0," + h.toString() + ")")
			.call(xGrid);
    pathContainer.append("g")         
			.attr("class", "grid")
			.attr("id", "yGrid")
			.call(yGrid);
	// X & Y AXIS
	xAxis = d3.svg.axis()
					.scale(xScale)
					.orient("bottom")
					.ticks(X_TICKS_DEFAULT)
					.tickFormat(d3.time.format('%b %d'))
					.tickSize(0)
					.tickPadding(8);
	yAxis = d3.svg.axis()
					.scale(yScale)
					.orient("left")
					.ticks(Y_TICKS_DEFAULT);
	svg.append("g")
			.attr("class", "axis")
			.attr("id", "xAxis")
			.attr("transform", "translate(0," + h.toString() + ")")
			.call(xAxis);
	svg.append("g")
			.attr("class", "axis")
			.attr("id", "yAxis")
			.call(yAxis);
	// INITIALIZE STACKS
	var defaultData = [{date: ONE_WEEK_AGO, value: 0}, {date: TODAY, value: maxY}];
	
	symptomInfoStack.push({
						maxValue: 			        maxY,
						id:     	           "default",
						data:   	         defaultData,	
						oldestDate: new Date(ONE_WEEK_AGO)
					});	
}

function drawGraph(id, color, dataset, goal, type) {
	
	console.log("> Draw new line: " + id);
	// replace any spaces in id with '-'
	id = id.replace(/ /g, "-");
	
    var data = dataset.map(function (d) {
        if( type == 'C' ) {
        	return {
            	date: d[0],
            	value: d[1],
            	categoryName: d[2],
        	}
    	}
    	else if( type == 'F' ) {
    		return {
        		date: d[0],
        		value: d[1],
            	units: d[2],
        	}
    	}
    	return {
    			date: d[0],
    			value: d[1],
    	}
    });
        
    // X & Y SCALE	
    var newMaxY = findMaxY(data, goal);  
    var minDate = d3.min(data, function(d) {return new Date(d.date); });

	 // insert new max value into stacks
  	var index = insertIntoStack(newMaxY, minDate, id, data);
  	var maxIndex = symptomInfoStack.length - 1;
  	
	updateScales(symptomInfoStack[ maxIndex ].maxValue);
	    
    // SCALE LINES
    // check if there is a new global maximum 
    if(index == maxIndex && index != 1) {
    	console.log("-------------Begin scaling-------------");
    	console.log("new Maximum: " + symptomInfoStack[ maxIndex ].maxValue );
		scaleLines(); 
		console.log("-------------Done scaling--------------");
    }
    
    // X & Y GRIDS 
	updateGrids(symptomInfoStack[ maxIndex ].maxValue);
    
	// X & Y AXIS
	updateAxes(symptomInfoStack[ maxIndex ].maxValue);
	
	// DRAW DATA ANALYSIS
	drawAllDataAnalysis(id, color, data, goal); // NOTE: need to have Data analysis before(i.e. below) data points to avoid hard-to-click bug
	
    // DATA LINE
    var line = d3.svg.line()
					 .x(function (d) { return xScale(new Date(d.date)); })
					 .y(function (d) { return yScale(d.value); });

    var path = pathContainer.selectAll(".non-existent-class")
	   				 .data([data])
	   				 .enter()
	   				   .append("path")
	   				   .attr("class", "line")
                       .attr("id", id)
                       .attr("opacity", 1)
	   				   .attr("d", line);

	// DATA POINTS
    var points = svg.selectAll(".non-existent-class")
						.data(data)
						.enter()
						  .append("circle")
						  .attr("stroke", color)
                          .attr("fill", color)
						  .attr("opacity", 0)
						  .attr("cx", function (d) { return xScale(new Date(d.date)); })
						  .attr("cy", function (d) { return yScale(d.value) ; })
						  .attr("r", RADIUS)
						  .attr("class", id + "-point" + " data-point");

    // TRANSITIONS
    // UNCOMMENT FOR LINE FADING TRANSITION 
    if(isMobile == true) {
		path.attr("stroke", color)
			.attr("fill", color)
			.transition()
			  .duration(SCALE_DURATION)
			  .attr("opacity", 1)
			  .each("end", function () {
					points.transition()
							.attr("stroke", color)
							.attr("fill", color)
							.attr("opacity", function (d) { 
								if(xScale(new Date(d.date)) < xScale(xDomain.min)) {
									return 0;
								}
								$(this).show();
								return DATA_POINT_OPACITY;
							});
			  });
	} else {	  
		// UNCOMMENT FOR LINE DRAWING TRANSITION   
		var totalLength = path.node().getTotalLength();            
		path.attr("stroke-dasharray", totalLength + " " + totalLength)
			.attr("stroke-dashoffset", totalLength)
			.attr("stroke", color)
			.attr("fill", color)
			.transition()
			  .duration(DRAW_LINE_DURATION)
			  .ease("linear")
			  .attr("stroke-dashoffset", 0)
			   .each("end", function () {
						points.transition()
							.attr("stroke", color)
							.attr("fill", color)
							.duration(SCALE_DURATION)
							.attr("opacity", function (d) { 
								if(xScale(new Date(d.date)) < xScale(xDomain.min)) {
									return 0;
								}
								return DATA_POINT_OPACITY;
							});
				 });     
	}
	// ADDING INTERACTION WITH DATA POINTS
	addDataPointInteraction(id, color, data, type);

    // HIDE data analysis if there's multiple symptom graphed
    if(maxIndex > 1) {
    	console.log("> multiple symptoms");
		updateAllDataAnalysis();
		$(".data-analysis").attr("disabled", true);
    }	
    console.log("> Done drawing: " + id);
}

function eraseGraph(id, data) {

	console.log("> Begin erasing: " + id);
	// replace any spaces in id with "-"
	id = id.replace(/ /g, "-");
	
	var points = checkPointCoord(id);
	// ERASE DATA LINE	
	d3.select("#"+id).remove();
	// ERASE DATA POINTS
	for(var i = 0; i < data.length; i++) {
		d3.select("#"+id+i.toString()).remove();
	}
	for(var i = 0; i < points.length; i++) {
		for(var j = 0; j < points[i].length; j++) {
			var content = d3.select("#" + points[i][j].id).attr("content");
			var pat = "\<br\/\>Your \<b\>" + id.replace(/-/g, " ") + "\<\/b\> was \: \<b\>.*\<\/b\>"
			var pattern = new RegExp(pat);
			var newContent = content.replace(pattern, "");
			d3.select("#" + points[i][j].id).attr("content", newContent);
		}
	}	
	
	var index = removeFromStack(id);
	var maxIndex = symptomInfoStack.length - 1;

	// X & Y SCALE
    updateScales(symptomInfoStack[ maxIndex ].maxValue);
	
	// SCALE LINES 
	// check if there is a new global maximum
	if(index > maxIndex) {
		console.log("-------------Begin scaling-------------");
		console.log("new Maximum: " + symptomInfoStack[ maxIndex ].maxValue );
		scaleLines();
		console.log("-------------Done scaling--------------");
	
		// X & Y GRIDS 
		updateGrids(symptomInfoStack[ maxIndex ].maxValue);
		// X & Y AXIS
		updateAxes(symptomInfoStack[ maxIndex ].maxValue);
	}
	// ERASE DATA ANALYSIS
	eraseAllDataAnalysis(id);
	
	// SHOW data analysis if there is only 1 symptom graphed
	if( maxIndex <= 1 ) {
		updateAllDataAnalysis();
		$(".data-analysis").attr("disabled", false);
	}
	console.log("> Done erasing: " + id);    
}

// function to resize graph upon window resize
function resizeGraph() {
	
	w = document.getElementById("graph").offsetWidth - MARGIN.left - MARGIN.right;
	h = w - 200 - MARGIN.top - MARGIN.bottom;
	
	// check to see if width or height exceeded dimension limits
	if(w < WIDTH.min) { w = WIDTH.min; }
	if( h > HEIGHT.max )	 { h = HEIGHT.max;} 
	else if( h < HEIGHT.min) { h = HEIGHT.min;}
	
	if(w < 300) { X_TICKS_DEFAULT = 3; }
	else 		{ X_TICKS_DEFAULT = 5; }
	
	svg.transition()
				  .attr("height", MARGIN.top + h + MARGIN.bottom)
				  .attr("width", MARGIN.left + w + MARGIN.right )
				  .attr("transform", "translate(" + (MARGIN.left).toString() + "," + (MARGIN.top).toString() + ")");
	
	pathContainer.transition()
			.attr("height",  h)
			.attr("width", w);
	
	var maxIndex = symptomInfoStack.length - 1;
		
	// X & Y SCALE				 
	updateScales(symptomInfoStack[ maxIndex ].maxValue);
		
	// SCALE LINES
	scaleLines();
		
	// X & Y GRIDS 
	updateGrids(symptomInfoStack[ maxIndex ].maxValue);
	
	// X & Y AXIS
	updateAxes(symptomInfoStack[ maxIndex ].maxValue);
}	

// function to update graph upon new time frame selection
function updateTimePeriod(timePeriod) {
	var maxIndex = symptomInfoStack.length - 1;	
	
	switch(timePeriod) {
		case "oneWeek":
			// X & Y SCALE
			maxX = new Date(TODAY);					 
			minX = new Date(ONE_WEEK_AGO);
			break;
		case "twoWeek":
			maxX = new Date(TODAY);					 
			minX = new Date(TWO_WEEK_AGO);
			break;
		case "oneMonth":
			maxX = new Date(TODAY);					 
			minX = new Date(ONE_MONTH_AGO);
			break;
		case "sixMonth":
			maxX = new Date(TODAY);					 
			minX = new Date(SIX_MONTH_AGO);
			break;
		case "oneYear":
			maxX = new Date(TODAY);					 
			minX = new Date(ONE_YEAR_AGO);
			break;
		case "allTime":
			maxX = new Date(TODAY);	
			var minTime = d3.min(symptomInfoStack, function(d) { return (new Date(d.oldestDate)).getTime(); });
			minX = new Date();
			minX.setTime(minTime);				 
			break;
		default:
			maxX = new Date(TODAY);					 
			minX = d3.min(data, function(d) { return new Date(d.date); });
			break;
	}
	
	xDomain = { max: maxX, min: minX };
	
	// X & Y SCALES
	updateScales(symptomInfoStack[ maxIndex ].maxValue);
	
	// SCALE LINES
	scaleLines();
		
	// X & Y GRIDS 
	updateGrids(symptomInfoStack[ maxIndex ].maxValue);
	
	// X & Y AXIS
	updateAxes(symptomInfoStack[ maxIndex ].maxValue);
}

// FUNCTIONS TO UPDATE GRAPH
function scaleLines() {	
	console.log("> scaling...");
	// DATA POINTS
	svg.selectAll(".data-point")
            .each(function(i) {
				d3.select(this)
					.transition()
					  .duration(SCALE_DURATION)
					  .attr("cx", function (d) { return xScale(new Date(d.date)); })
					  .attr("cy", function (d) { return yScale(d.value); })
					  .attr("opacity", function (d) { 
					  		if(xScale(new Date(d.date)) < xScale(xDomain.min)) {
					  			return 0;
					  		} 
					  		return DATA_POINT_OPACITY;
					  	});
            });			  
	// DATA LINES
	var line = d3.svg.line()
					 .x(function (d) { return xScale(new Date(d.date)); })
					 .y(function (d) { return yScale(d.value); });
	pathContainer.selectAll(".line")
			.each(function(i) {
				d3.select(this)
					.transition()
					  .attr("stroke-dasharray", null)
	   				  .attr("stroke-dashoffset", null)
					  .duration(SCALE_DURATION)
				      .attr("d", line);
			});	
	// DATA ANALYSIS
	updateAllDataAnalysis();
}

function updateScales(maxY) {
	xScale = d3.time.scale()
					  .domain([xDomain.min, xDomain.max])
					  .range([0, w]);
	yScale = d3.scale.linear()
						.domain([0, maxY + 1])
						.range([h, 0]);
}

function updateAxes() {
	xAxis = d3.svg.axis()
					.scale(xScale)
					.orient("bottom")
					.ticks(X_TICKS_DEFAULT)
					.tickFormat(d3.time.format('%b %d'))
					.tickSize(0)
					.tickPadding(8);
	yAxis = d3.svg.axis()
					.scale(yScale)
					.orient("left")
					.ticks(Y_TICKS_DEFAULT);
					
	if( isMobile == false ) {			
		svg.select("#xAxis")
				.transition()
				  .duration(SCALE_DURATION)	
				  .attr("transform", "translate(0," + (h).toString() + ")")
				  .call(xAxis);
		svg.select("#yAxis")
				.transition()
				  .duration(SCALE_DURATION)
				  .call(yAxis);
	} else {
		svg.select("#xAxis")
			.attr("transform", "translate(0," + (h).toString() + ")")
			.call(xAxis);
		svg.select("#yAxis")
			.call(yAxis);
	}
}

function updateGrids() { 
	xGrid = d3.svg.axis()
					.scale(xScale)
                   	.orient("bottom")
                   	.ticks(X_TICKS_DEFAULT)
					.tickSize(-h, 0, 0)
					.tickFormat("");
	yGrid = d3.svg.axis()
					.scale(yScale)
					.orient("left")
					.ticks(Y_TICKS_DEFAULT)
					.tickSize(-w, 0, 0)
					.tickFormat("");
					
	if( isMobile == false ) {				
		pathContainer.select("#xGrid")         
			.transition()
			  .duration(SCALE_DURATION)
			  	.attr("transform", "translate(0," + (h).toString() + ")")
				.call(xGrid);
					
    	pathContainer.select("#yGrid")         
			.transition()
			  .duration(SCALE_DURATION)
				.call(yGrid);
	} else {
		pathContainer.select("#xGrid")
						.call(xGrid);
		pathContainer.select("#yGrid")         
						.call(yGrid);         
	}
}

// FUNCTIONS TO HANDLE STACK 
function insertIntoStack(maxValue, oldestDate, id, data) {
	symptomInfoStack.push({
					maxValue:       maxValue,
					id:     	  	      id,
					data:   	 	    data,
					oldestDate:   oldestDate,
				});
	
	symptomInfoStack.sort(function(obj1, obj2) {
					 	return obj1.maxValue - obj2.maxValue;
					});
	var i = 0;
	while(symptomInfoStack[i].id != id) { 
		i++; 
	} 
	
	return i;
}

function removeFromStack(id) {
	symptomInfoStack.sort(function(obj1, obj2) {
					 	return obj1.maxValue - obj2.maxValue;
					 });
	var i = 0;
	while(symptomInfoStack[i].id != id) { 
		i++; 
	} 
	console.log("> found id: " + symptomInfoStack[i].id + " at " + i.toString());
	
	symptomInfoStack.splice(i, 1);
	
	return i;
}

// HELPER FUNCTIONS
// find maximum Y value of within all symptom data
function findMaxY(data, goal) {
	var allYValue = data.slice(0);
	allYValue.push({date: xDomain.max, value: goal});
	return d3.max(allYValue, function(d) { return d.value; });  
}

// add data-point interaction
function addDataPointInteraction(id, color, data, type) {
	svg.selectAll("." + id + "-point")
            .each(function(d) {
            	var index = data.indexOf(d);
				var date = new Date(d.date);
				var y = date.getFullYear();
				var m = date.getMonth();
				var d = date.getDate();
				var da = date.getDay();
            	var idStr = id+(index).toString();
            	var title = "<b>" + dayOfWeek[ da ] + " " + monthName[ m ] + " " + d.toString() + ", " + y.toString() + "</b>";
                if(isMobile == false) {
                	title += '<a class="pull-right close-button" onclick="$(&quot;#' +
                			  idStr +'&quot;).popover(&quot;hide&quot;);">×</a>';
                }
                d3.select(this)
                	.attr("id", idStr)
                	.attr("title", title);
            });
    var points = checkPointCoord(id);
 	dataPointPopover(id, data, points, type);       
    $("."+id+"-point").hover(
			function () {
				d3.select(this)
					.attr("opacity", function (d) { 
						if(xScale(new Date(d.date)) < xScale(xDomain.min)) {
							$(this).hide();
							return 0;
						}
						$(this).show();
						return DATA_POINT_OPACITY;
					})
					.style("stroke", function() { return d3.rgb(color).darker(1); })
					.attr("stroke-width", 3);
			},
			function () {
				d3.select(this)
					.attr("opacity", function (d) { 
						if(xScale(new Date(d.date)) < xScale(xDomain.min)) {
							$(this).hide();
							return 0;
						}
						$(this).show();
						return DATA_POINT_OPACITY;
					})
					.attr("stroke-width", 0);
			}
		);    
}

// function returns an array of arrays -> array of points containing points each index is duplicate of 
function checkPointCoord(id) {
	var points = [];
	svg.selectAll("." + id + "-point")
            .each(function(d) {
            	var point = [];
			   	$.grep(symptomInfoStack, function(stack, j) {             					
					if (stack.id != id && stack.id != 'default') {
						$.grep(stack.data, function(array, index) {
							if( xScale(new Date(array.date)) ==  xScale(new Date(d.date))
								&& yScale(array.value) == yScale(d.value))
							{
								console.log("> SAME COORD: "+ stack.id+index.toString());
								point.push({id: stack.id+index.toString(), value: d.value});
							}
						});
					}
				});
				points.push(point);
			}
		);
	return points;
}

// adds popover functionality to data points (NOTE: points holds all duplicate points)
function dataPointPopover(id, data, points, type) {
	svg.selectAll("." + id + "-point")
            .each(function(d) {
            	var i = data.indexOf(d);
         		var val = d.value;
         		var content = "";
         		if( isDoctor == false )
         			content = "Your <b>" + id.replace(/-/g, " ") + "</b> was : <b>";
         		else 
         			content = userName + "'s <b>" + id.replace(/-/g, " ") + "</b> was : <b>";
         		// get additional content text based on question type 
         		if( type == 'C' ) 		{ content += d.categoryName + "</b>"; }
				else if( type == 'F' ) 	{ content += val.toString() + " " + d.units + "</b>"; }
				else 					{ content += val.toString() + "</b>"; }
				
				for(var j = 0; j < points[i].length; j++) { // <--- NOTE: not sure why this only works in a for loop???
					j = points[i].length - 1; 
					if(j == points[i].length - 1)  // <---- only add content of the data point on top
						content += "<br/>" + d3.select("#"+points[i][j].id).attr("content");
				}
				d3.select(this).attr("content", content);
				console.log("> content: "+ content);
				if(isMobile == true) { 
					$(this).click(function(){
						$('.modal').modal('show');
						$('#my-modal-title').append(d3.select(this).attr('title'));
						$('#my-modal-body').append(d3.select(this).attr('content'));
					});  
				} else {
					var options = {
						'container': 'body',
						'placement': function(context, source){
												var x = $(source).attr('cx');
												// check if popover is close to window limit
												if (x > (w - 110))  { return "left"; }
												if (x < (110)) 		{ return "right"; }
			
												return "top";
											},
						'content': function(){
												console.log(d3.select(this).attr("content"));
												return d3.select(this).attr("content");
											},	
						'trigger': 'click',
						 html: true	
					};
					$(this).popover(options); 
				}
            }
        );
}
