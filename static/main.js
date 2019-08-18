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

function makeSvg(data, svgParent, rangeParams, plotNames, parseTime, group_labels, marginParams, titleString) {
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

  var valueLine = d3.line()
      .x(function (d) {
	return xScale(parseTime(d[plotNames.xName]));
      })
      .y(function (d) {
  	return yScale(d[plotNames.yName]);
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
    .call(d3.axisBottom(xScale));

  svg.append('g')
    .attr('class', 'y axis')
    .attr('transform', `translate(0,0)`)    
    .call(d3.axisLeft(yScale));    

  for (var i = 0; i < group_labels.length; i++){
    pull_date = group_labels[i];

    data_date = data.filter( function (d){
      return ((d['pull_date'] == pull_date) && !!d[plotNames.yName] && !isNaN(d[plotNames.yName]));
    })

    svg.append('path')
      .data([data_date])
      .attr('class', `line_temperature-${i}`)
      .attr('fill', 'none')
      .attr('stroke', colorScale(i))
      .attr('stroke-width', 2)
      .attr('d', valueLine);
  }

  return svg;
}


function makeGraphs(data){
  const margin = 30;
  const width  = 600 - 2 * margin;
  const height =  250 - 2 * margin;

  const marginParams = {
    margin : margin,
    width  : width,
    height : height
  }
  
  var div = d3.select('#graph_div');      

  var svgs = div.selectAll('svg');
  svgs.remove();
    
  var parseTime = d3.isoParse;  
  var times = data.map(function(d) {
    return parseTime(d.forecast_time_stamps);
  });
  var minTime = d3.min(times);
  var maxTime = d3.max(times);

  var distinct_fcsts = [];
  for (var i = 0; i < data.length; i++) {
    if (!(distinct_fcsts.includes(data[i].pull_date))) {
      distinct_fcsts.push(data[i].pull_date);
    }
  }
  distinct_fcsts.sort();

  // Make Temperature chart
  plotNames = {xName : 'forecast_time_stamps', yName : 'temperature_hourly'};  
  tempRange = {xMin : minTime, xMax : maxTime, yMin : 0, yMax : 120};
  titleString = 'Temperature Forecast Comparison';
  svgTemp   = makeSvg(data, div, tempRange, plotNames, parseTime, distinct_fcsts, marginParams, titleString);

  // Make Precipitation Probability Chart
  plotNames   = {xName : 'forecast_time_stamps', yName : 'probability_of_precipitation_floating'};
  precipRange = {xMin : minTime, xMax : maxTime, yMin : 0, yMax : 100};
  titleString = 'Precipitation Probability Forecast Comparison';
  svgPrecip   = makeSvg(data, div, precipRange, plotNames, parseTime, distinct_fcsts, marginParams, titleString);
  
}

function updatePage() {
  var airport_elt = document.getElementById("airport_list");
  airport = airport_elt.value;
  query_url = "/query?airport=" + airport;// + "&limit=100";
  console.log(query_url);
  
  d3.json(query_url)
    .then(function(data) {
      //makeTable(data);
      makeGraphs(data);
    });
}
