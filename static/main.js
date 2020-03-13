function strCastToNum(v){
  if (v == ""){
    return null;
  }
  else {
    return +v;
  }
}


function updateSlider(x, h, handle) {
    // update position and text of label according to slider scale
    handle.attr("cx", x(h))
        .attr("date_str", d3.timeFormat("%Y-%m-%d")(h));
}

function makeSlider(startDate, endDate){
  const margin = 30;
  const width  = 600 - 2 * margin;
  const height = 100 - 2 * margin;

  const marginParams = {
    margin : margin,
    width  : width,
    height : height
  }

  var parseDate = d3.timeParse("%d-%b-%y");
  var formatDate = d3.timeFormat("%Y-%m");

  var dateArray = d3.timeYears(startDate, d3.timeYear.offset(endDate, 1));
    
  // x scale for time
  var x = d3.scaleTime()
        .domain([startDate, endDate])
        .range([0, width])
        .clamp(true);
    
  //Based off of:
  //https://bl.ocks.org/officeofjane/f132634f67b114815ba686484f9f7a77
  var currentValue = endDate;
  var div = d3.select('#slider_div');      

  var svg = div.append('svg')
      .attr('width',  width  + 2 * margin)
      .attr('height', height + 2 * margin);
    
    var slider = svg.append('g')
	.attr("class", "slider")    
	.attr('transform',
	      `translate(${margin}, ${margin})`);

    var handle = slider.insert("circle", ".track-overlay")
        .attr("class", "handle")
        .attr("r", 9);

    slider.append("line")
        .attr("class", "track")
        .attr("x1", x.range()[0])
        .attr("x2", x.range()[1])
	.select(function() { return this.parentNode.appendChild(this.cloneNode(true)); })
        .attr("class", "track-inset")
	.select(function() { return this.parentNode.appendChild(this.cloneNode(true)); })
        .attr("class", "track-overlay")
        .call(d3.drag()
	      .on("start.interrupt", function() { slider.interrupt(); })
	      .on("start drag", function() {
		  currentValue = d3.event.x;		  
		  updateSlider(x, x.invert(currentValue), handle);
	      })
	      .on("end", function() {
		  currentValue = d3.event.x;
		  updateLineCharts(x.invert(currentValue));
		  console.log(d3.event.x);
		  console.log(x.invert(currentValue));
	      })
	     );

    slider.insert("g", ".track-overlay")
        .attr("class", "ticks")
        .attr("transform", "translate(0," + 18 + ")")
	.selectAll("text")
        .data(x.ticks(10))
        .enter()
        .append("text")
        .attr("x", x)
        .attr("y", 10)
        .attr("text-anchor", "middle")
        .text(function(d) { return formatDate(d); });

    // slet slider initial position
    updateSlider(x, endDate, handle)

    return slider;
}



function makeTable(data){
  var titles = d3.keys(data[0]);    
  var div = d3.select('#table_div');
  var tbl = div.selectAll('table');
  tbl.remove();
  tbl = div.append('table');
  
  var header = tbl.append('tr')
      .selectAll('th')
      .data(titles)
      .enter()
      .append('th')
      .text( function(d){ return d;})
  
  var rows = tbl.selectAll('tr')
      .data(data)
      .enter()
      .append('tr');
  
  rows.selectAll('td')
    .data(function (d) {
      return titles.map(function (k) {
	return { 'value': d[k], 'name': k};
      });
    })  
    .enter()
    .append('td')
    .attr('data-th', function (d) {
      return d.name;
    })
    .text(function (d) {
      return d.value;
    });
}

function makeSvg(dataFcst, dataActl, svgParent, rangeParams, plotNamesFcst, plotNamesActl, parseTime, group_labels, marginParams, titleString) {
  const margin = marginParams['margin'],
	height = marginParams['height'],
	width  = marginParams['width'];
  
  var xScale = d3.scaleTime()
      .domain([rangeParams['xMin'], rangeParams['xMax']])
      .range([0, width]);

  var yScale = d3.scaleLinear()
      .domain([rangeParams['yMin'], rangeParams['yMax']])
      .range([height, 0]);

  var colorScale = d3.scaleLinear()
      .domain([0, group_labels.length])
      .range(['lightblue', 'darkblue']);  

  var valueLineFcst = d3.line()
      .x(function (d) {
	return xScale(parseTime(d[plotNamesFcst.xName]));
      })
      .y(function (d) {
  	return yScale(d[plotNamesFcst.yName]);
      });

  var valueLineActl = d3.line()
      .x(function (d) {
  	return xScale(parseTime(d[plotNamesActl.xName]));
      })
      .y(function (d) {
  	return yScale(d[plotNamesActl.yName]);
      });
  
  var svg = svgParent.append('svg')
      .attr('width',  width  + 2 * margin)
      .attr('height', height + 2 * margin)
      .append('g')
      .attr('transform',
	    `translate(${margin}, ${margin})`);

  svg.append('text')
    .attr('x', 0)
    .attr('y', 0 - (margin / 2))
    .attr('text-anchor', 'left')
    .style('font-size', '16px')
    .text(titleString);
  
  svg.append('g')
    .attr('class', 'x axis')
    .attr('transform', `translate(0, ${height})`)  
    .call(d3.axisBottom(xScale)
	  .ticks(d3.timeDay.every( Math.floor(group_labels.length / 7)) )
	  .tickFormat(d3.timeFormat("%b-%d"))
	 );

  svg.append('g')
    .attr('class', 'y axis')
    .attr('transform', `translate(0,0)`)    
    .call(d3.axisLeft(yScale));    

  // plot all the forecast dates
  for (var i = 0; i < group_labels.length; i++){
    pull_date = group_labels[i];

    data_date = dataFcst.filter( function (d){
      return ((d['pull_date'] == pull_date) && !!d[plotNamesFcst.yName] && !isNaN(d[plotNamesFcst.yName]));
    })

    svg.append('path')
      .data([data_date])
      .attr('class', `line_temperature-${i}`)
      .attr('fill', 'none')
      .attr('stroke', colorScale(i))
      .attr('stroke-width', 2)
      .attr('d', valueLineFcst);
  }

  // plot actual data if it has been provided
  if (dataActl != null) {
    svg.append('path')
      .data([dataActl.filter( function (d) {
	return (parseTime(d[plotNamesActl.xName]) > rangeParams['xMin']) ;
      })])
      .attr('class',  'line_actual')
      .attr('fill',   'none')
      .attr('stroke', 'black')
      .attr('stroke-opacity', .5)
      .attr('stroke-width',   1.7)
      .attr('d', valueLineActl);
  }
    
  return svg;
}


function makeGraphs(airport, start_date_str, end_date_str){
  const margin = 30;
  const width  = 600 - 2 * margin;
  const height =  250 - 2 * margin;

  const marginParams = {
    margin : margin,
    width  : width,
    height : height
  }
  
  var div = d3.select('#graph_div');      
  div.selectAll('br').remove();
  div.selectAll('svg').remove();

  // query the database in the following places
  fcst_query_url = "/weather-app/query?airport=" + airport + "&af_type=fcst" + "&start_date_str=" + start_date_str + "&end_date_str=" + end_date_str;
  actl_query_url = "/weather-app/query?airport=" + airport + "&af_type=actl" + "&start_date_str=" + start_date_str + "&end_date_str=" + end_date_str;

  Promise.all([
    d3.json(fcst_query_url),
    d3.json(actl_query_url),
  ]).then(function(data) {

    // obtain the data
    dataFcst = data[0];
    dataActl = data[1];

    // get the max and min times from the forecast data
    var parseTime = d3.isoParse;  
    var times = dataFcst.map(function(d) {
      return parseTime(d.forecast_time_stamps);
    });
    var minTime = d3.min(times);
    var maxTime = d3.max(times);
    
    var distinct_fcsts = [];
    for (var i = 0; i < dataFcst.length; i++) {
      if (!(distinct_fcsts.includes(dataFcst[i].pull_date))) {
	distinct_fcsts.push(dataFcst[i].pull_date);
      }
    }
    distinct_fcsts.sort();
    
    // Make Temperature chart
    plotNamesFcst = {xName : 'forecast_time_stamps', yName : 'temperature_hourly'};
    plotNamesActl = {xName : 'datetime', yName : 'air_temp'};      
    tempRange = {xMin : minTime, xMax : maxTime, yMin : 0, yMax : 120};
    titleString = 'Temperature Forecast Comparison';
    svgTemp   = makeSvg(dataFcst, dataActl, div, tempRange, plotNamesFcst, plotNamesActl, parseTime, distinct_fcsts, marginParams, titleString);
    div.append('br');
    
    //Make Precipitation Probability Chart
    plotNamesFcst   = {xName : 'forecast_time_stamps', yName : 'probability_of_precipitation_floating'};
    plotNamesActl   = {xName : 'datetime', yName : 'precip_1_hour'};
    precipRange = {xMin : minTime, xMax : maxTime, yMin : 0, yMax : 100};
    titleString = 'Precipitation Probability Forecast Comparison';
    svgPrecip   = makeSvg(dataFcst, null, div, precipRange, plotNamesFcst, plotNamesActl, parseTime, distinct_fcsts, marginParams, titleString);
    div.append('br');
    
    // Make Wind-speed chart
    plotNamesFcst = {xName : 'forecast_time_stamps', yName : 'wind_speed_sustained'};
    plotNamesActl = {xName : 'datetime', yName : 'wind_speed'};          
    tempRange = {xMin : minTime, xMax : maxTime, yMin : 0, yMax : 30};
    titleString = 'Wind Speed Forecast Comparison';
    svgTemp   = makeSvg(dataFcst, dataActl, div, tempRange, plotNamesFcst, plotNamesActl, parseTime, distinct_fcsts, marginParams, titleString);
  });
}


function makeAvFHeatMapSvg(data, svgParent, marginParams, titleString) {
  const margin = marginParams['margin'],
	height = marginParams['height'],
	width  = marginParams['width'],
	square_size = Math.min((width - 70) / 24, height / 7);
  
  var xScale = d3.scaleLinear()
      .domain([0, 23])
      .range([0, 24 * square_size]);

  var yScale = d3.scaleLinear()
      .domain([0, 6])
      .range([0, 7 * square_size]);

  // var tempDeltaMin = d3.min(Object.values(d3.min(data)));
  // var tempDeltaMax = d3.max(Object.values(d3.max(data)));    
  
  var tempDeltaMin = -4;
  var tempDeltaMax = 4;    

  //var colorScale = d3.scaleSequential(d3.interpolateInferno)
  //    .domain([tempDeltaMin, tempDeltaMax]);  
  
  var colorScale = d3.scaleSequential(d3.interpolateRdBu)
      .domain([tempDeltaMax, tempDeltaMin]);  

  
  var svg = svgParent.append('svg')
      .attr('width',  width  + 2 * margin)
      .attr('height', height + 2 * margin)
      .append('g')
      .attr('transform',
	    `translate(${margin}, ${margin})`);

  svg.append('text')
    .attr('x', 0)
    .attr('y', 0 - (margin / 2))
    .attr('text-anchor', 'left')
    .style('font-size', '16px')
    .text(titleString);

  var dataFlat = [];
  
  for(var i = 0; i < 7; i++){
    for(var j = 0; j < 24; j++){
      dataFlat.push({
	"i" : i,
	"j" : j,
	"val" : data[i][j]
      });
    }
  }

  for (i = 1; i <= 7; i++){
    svg.append('text')
      .attr('x', xScale(-0.5))
      .attr('y', yScale(i - 0.4))
      .attr('text-anchor', 'left')
      .style('font-size', '10px')
      .text(i);
  }
  
  for (j = 0; j <= 23; j++){
    svg.append('text')
      .attr('x', xScale(j+0.25))
      .attr('y', yScale(7.5))
      .attr('text-anchor', 'left')
      .style('font-size', '10px')
      .text(j);
  }
  
  var tooltip = d3.select("body")
      .append("div")
      .style("position", "absolute")
      .style("z-index", "10")
      .style("visibility", "hidden");
 
  var squares = svg.selectAll("rect")
      .data(dataFlat)
      .enter()
      .append("rect")
      .attr("x", d => xScale(d.j))
      .attr("y", d => yScale(d.i))
      .attr("width",  square_size)
      .attr("height", square_size)
      .style("fill", d => colorScale(d.val))
      .on("mouseover", function(d){
	return tooltip.style("visibility", "visible")
	  .style("background-color", "white")
	  .style("data-html", "true")
	  .html(
	    "Forecast Day " + (d.i + 1) + "</br>" +
	    "Hour: "        + (d.j)     + "</br>" +
	    "Forecast - Actual: " + d.val.toFixed(3)
	  );
      })
      .on("mousemove", function(d){
	return tooltip.style("top", (event.pageY-10)+"px")
	  .style("left",(event.pageX+10)+"px")
	  .html(
	    "Forecast Day " + (d.i + 1) + "</br>" +
	    "Hour: "        + (d.j)     + "</br>" +
	    "Forecast - Actual: " + d.val.toFixed(3)
	  );
      })
      .on("mouseout", function(){
	return tooltip.style("visibility", "hidden").text("");
      });
  
  var svgDefs = svg.append('defs');

  var mainGradient = svgDefs
      .append('linearGradient')
      .attr('id', 'mainGradient')
      .attr("x1", "100%")
      .attr("y1", "100%")
      .attr("x2", "100%")
      .attr("y2", "0%")
      .attr("spreadMethod", "pad")
  ;

  var tempScale = d3.scaleLinear()
      .domain([tempDeltaMax, tempDeltaMin])
      .range([0, 8 * square_size]);
  
  var nStops = 10;
  for (i = 0; i <= nStops; i++) {
    mainGradient.append('stop')
      .style('stop-color', colorScale(tempDeltaMin + (i / nStops) * (tempDeltaMax - tempDeltaMin) ))
      .attr('offset', 100 * (i / nStops) + "%")
      .attr('stop-opacity', 1);    
  }
  
  // Use the gradient to set the shape fill, via CSS.
  svg.append('rect')
    .classed('filled', true)
    .style('fill', 'url(#mainGradient)')  
    .attr('x', 27 * square_size)
    .attr('y', 0)
    .attr('width', square_size)
    .attr('height', 8 * square_size);
  
  var temp_axis = d3.axisLeft()
      .scale(tempScale);

  var displacement = 27 * square_size;
  svg.append("g")
    .attr('transform', `translate(${displacement}, 0)`)  
    .call(temp_axis);
  
  
  return svg;
}

function makeAvFHeatMap(airport) {
  const margin = 30;
  const width  = 600 - 2 * margin;
  const height =  250 - 2 * margin;

  const marginParams = {
    margin : margin,
    width  : width,
    height : height
  }
  
  var div = d3.select('#avf_heatmap_div');

  // Drop the svgs from this div
  var svgs = div.selectAll('svg');
  svgs.remove();
  
  heatmap_url = "/weather-app/avf_heatmap?airport=" + airport;
  d3.csv(heatmap_url)
    .then(function(data) {

      // convert data to numeric 
      data.forEach(function(d) {
	for(var i=0; i < 24; i++){
	  //strCastToNum(d[i]);	  
	  if(d[i] != "") {
	    d[i] = +d[i];
	  }
	  else{
	    d[i] = null;
	  }
	}
      });

      // Make the heatmap SVG
      svg = makeAvFHeatMapSvg(data, div, marginParams, 'Temperature Fcst vs Actl Comparison Heat Map');  
  });   
  
}


/*-------------------------------------------------------------------------------*/
/*                 Forecast to Forecast Variation Heatmap                        */
/*-------------------------------------------------------------------------------*/

function makeFvFHeatMapSvg(data, svgParent, marginParams, titleString, heatmap_type) {
  const margin = marginParams['margin'],
	height = marginParams['height'],
	width  = marginParams['width'],
	square_size = Math.min((width - 70) / 24, height / 21);
  
  var xScale = d3.scaleLinear()
      .domain([0, 23])
      .range([0, 24 * square_size]);

  var yScale = d3.scaleLinear()
      .domain([0, 20])
      .range([0, 21 * square_size]);

  function flat_map(i, j) {
    return (i * (i - 1)) / 2 + j;    
  }

  var deltaMin = -4.0;
  var deltaMax =  4.0;    

  //var colorScale = d3.scaleSequential(d3.interpolateInferno)
  //    .domain([tempDeltaMin, tempDeltaMax]);  
  
  var colorScale = d3.scaleSequential(d3.interpolateRdBu)
      .domain([deltaMax, deltaMin]);
  
  var svg = svgParent.append('svg')
      .attr('width',  width  + 2 * margin)
      .attr('height', height + 2 * margin)
      .append('g')
      .attr('transform',
	    `translate(${margin}, ${margin})`);

  svg.append('text')
    .attr('x', 0)
    .attr('y', 0 - (margin / 2))
    .attr('text-anchor', 'left')
    .style('font-size', '16px')
    .text(titleString);

  for (day1 = 1; day1 <= 6; day1++){
    for (day2 = 0; day2 < day1; day2++){
      svg.append('text')
  	.attr('x', xScale(-1.5))
  	.attr('y', yScale( flat_map(day1, day2) + 1 - 0.3))
  	.attr('text-anchor', 'left')
  	.style('font-size', '10px')
  	.text(day1 + ", " + day2);
    }
  }
  
  for (j = 0; j <= 23; j++){
    svg.append('text')
      .attr('x', xScale(j+0.25))
      .attr('y', yScale(21.5))
      .attr('text-anchor', 'left')
      .style('font-size', '10px')
      .text(j);
  }
  
  var tooltip = d3.select("body")
      .append("div")
      .attr('id', 'fvf_tooltip_' + heatmap_type)
      .style("position", "absolute")
      .style("z-index", "10")
      .style("visibility", "hidden");
 
  var squares = svg.selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
      .attr("x", d => xScale( d['fcst_hour'] ))
      .attr("y", d => yScale( flat_map(d['day_of_snp1'], d['day_of_snp2'])) )
      .attr("width",  square_size)
      .attr("height", square_size)
      .style("fill", d => d[heatmap_type] != null ? colorScale(d[heatmap_type]) : "none")
      .on("mouseover", function(d){
	return tooltip.style("visibility", "visible")
	  .style("background-color", "white")
	  .style("data-html", "true")
	  .html(
 	    "Days into earlier snapshot: " + d['day_of_snp1'] + "</br>" +
	    "Days into later snapshot: " + d['day_of_snp2'] + "</br>" +	
	    "Hour: "         + d['fcst_hour']   + "</br>" +      	      
            heatmap_type + " (later - earlier): " + d[heatmap_type].toFixed(3) + "</br>" + 
            "Observations: "             + d['cnt_snp2_v_snp1'] 
	  );
      })
      .on("mousemove", function(d){
	return tooltip.style("top", (event.pageY-10)+"px")
	  .style("left",(event.pageX+10)+"px")
	  .html(
 	    "Days into earlier snapshot: " + d['day_of_snp1'] + "</br>" +
	    "Days into later snapshot: " + d['day_of_snp2'] + "</br>" +	
	    "Hour: "         + d['fcst_hour']   + "</br>" +
             heatmap_type + " (later - earlier): " + d[heatmap_type].toFixed(3) + "</br>" + 
            "Observations: "             + d['cnt_snp2_v_snp1'] 	      
	  );
      })
      .on("mouseout", function(){
	return tooltip.style("visibility", "hidden").text("");
      });
  
  var svgDefs = svg.append('defs');
  
  var mainGradient = svgDefs
      .append('linearGradient')
      .attr('id', 'mainGradient')
      .attr("x1", "100%")
      .attr("y1", "100%")
      .attr("x2", "100%")
      .attr("y2", "0%")
      .attr("spreadMethod", "pad");

  var deltaScale = d3.scaleLinear()
      .domain([deltaMax, deltaMin])
      .range([0, 22 * square_size]);
  
  var nStops = 10;
  for (i = 0; i <= nStops; i++) {
    mainGradient.append('stop')
      .style('stop-color', colorScale(deltaMin + (i / nStops) * (deltaMax - deltaMin) ))
      .attr('offset', 100 * (i / nStops) + "%")
      .attr('stop-opacity', 1);    
  }
  
  // Use the gradient to set the shape fill, via CSS.
  svg.append('rect')
    .classed('filled', true)
    .style('fill', 'url(#mainGradient)')  
    .attr('x', 27 * square_size)
    .attr('y', 0)
    .attr('width', square_size)
    .attr('height', 22 * square_size);
  
  var delta_axis = d3.axisLeft()
      .scale(deltaScale);

  var displacement = 27 * square_size;
  svg.append("g")
    .attr('transform', `translate(${displacement}, 0)`)  
    .call(delta_axis);
  
  return svg;
}



function makeFvFHeatMap(airport) {
  const margin = 30;
  const width  = 600 - 2 * margin;
  const height = 600 - 2 * margin;

  const marginParams = {
    margin : margin,
    width  : width,
    height : height
  }
  
  var div = d3.select('#fvf_heatmap_div');

  // Drop the svgs from this div
  var svgs = div.selectAll('svg');
  svgs.remove();
  
  heatmap_url = "/weather-app/fvf_heatmap?airport=" + airport;
  d3.csv(heatmap_url)
    .then(function(data) {
      // convert data to numeric 
      data.forEach(function(d) {
	d['day_of_snp1']  = +d['day_of_snp1'];
	d['day_of_snp2']  = +d['day_of_snp2'];	
	d['fcst_hour']    = +d['fcst_hour'];
	d['avg_temp_delta']        = strCastToNum(d['avg_temp_delta']);
	d['avg_prob_precip_delta'] = strCastToNum(d['avg_prob_precip_delta']);
	d['avg_wind_speed_delta']  = strCastToNum(d['avg_wind_speed_delta']);
	d['cnt_snp2_v_snp1']       = strCastToNum(d['cnt_snp2_v_snp1']);
      });

      // Make the heatmap SVG
      svg = makeFvFHeatMapSvg(data, div, marginParams, 'Temperature Fcst vs Fcst Comparison Heat Map', 'avg_temp_delta');  
  });
      
}

function datesStrFromSlider(){
  var selected_date_str = d3.select('#slider_div').select("circle").attr("date_str");
  var selected_date = d3.timeParse("%Y-%m-%d")(selected_date_str);

  // First day is two weeks prior to selected date    
  var start_date = new Date(selected_date.getTime());
  start_date.setDate(start_date.getDate()-14);
  var start_date_str = d3.timeFormat("%Y-%m-%d")(start_date);

  // Last day is one week past selected date
  var end_date = new Date(selected_date.getTime());
  end_date.setDate(end_date.getDate()+7);
  var end_date_str = d3.timeFormat("%Y-%m-%d")(end_date);    

  return {"start_date_str" : start_date_str, "end_date_str" : end_date_str}
    
}

function updateLineCharts() {
  // Define date range to pull.
  var date_strs = datesStrFromSlider();
  var start_date_str = date_strs['start_date_str'];
  var end_date_str = date_strs['end_date_str'];    

  // make some line graphs
  makeGraphs(airport, start_date_str, end_date_str);    
}


function updatePage() {
  var airport_elt = document.getElementById("airport_list");
  airport = airport_elt.value;

  // Define date range to pull.
  var date_strs = datesStrFromSlider();
  var start_date_str = date_strs['start_date_str'];
  var end_date_str = date_strs['end_date_str'];    
    
  // make some line graphs
  makeGraphs(airport, start_date_str, end_date_str);
      
  // add avf heatmap plot
  makeAvFHeatMap(airport);

  // add fvf heatmap plot
  makeFvFHeatMap(airport);  
}

function onLoadPage(){
    // Hard coded date, first date I pulled
    var startDate = new Date("2019-08-25");

    // Most recent date
    var endDate = new Date();
    
    makeSlider(startDate, endDate);

    // // Define date range to pull.
    // var now_date = new Date();
    // var now_date_str = now_date.toISOString().split('T')[0];
    
    // var start_date = new Date();
    // start_date.setDate(now_date.getDate()-14);
    // var start_date_str = start_date.toISOString().split('T')[0];
    
    // var end_date = new Date();
    // end_date.setDate(now_date.getDate()+7);
    // var end_date_str = end_date.toISOString().split('T')[0];
    
    updatePage();
}
