var width = 960,
	height = 40;

var send_button = d3.select("input");
var send_request = d3.select("a");
var project = d3.select(".project.container");
var chromosome = d3.select();
var ref = d3.select();
var sample = d3.select();
var input = d3.select(".input.container");
var output = d3.select(".output.container");
var accessions = d3.select(".accessions");

/*var rectBox = output.append("div")
					.attr("id", "rectBox")
					.style("display", "none");
var toolTip = output.append("div")
					.attr("id", "toolTip")
      			    .style("position", "absolute")
      			    .style("visibility", "hidden");
*/
var rectBox = output.select("#rectBox");
var toolTip = output.select("#toolTip");

var dsv = d3.dsvFormat(",");
var currentProject = "";
var currentChromTable = new Array();
var currentChrom = "";
var currentRef = "";
var currentSamples = new Array();

var currentStart = 1;
var currentEnd = 0;
var currentNumOfBins = 100;

window.onload = function() {
	sendGetRequest("/data/loading", loadProjects);
}

var sendGetRequest = function (url, onReady, timeOut = 3000, onTimeOut = defaultOnTimeOut) {
	xmlhttp = new XMLHttpRequest();
	xmlhttp.open("GET", url, true);
	xmlhttp.timeout = timeOut;
	xmlhttp.onreadystatechange = onReady;
	xmlhttp.ontimeout = onTimeOut;
	xmlhttp.send();
}

var resetMenu = function(level = 0, removeResults = true) {
	if (removeResults == true) {
		output.selectAll("svg").remove();
	}

	/* select a new reference */
	ref.selectAll('a').style('background-color', 'green');
	sample.remove();
	input.selectAll('div').remove();
	input.selectAll('input').remove();
	input.selectAll('a').remove();

	currentSamples = new Array();

	if (level >= 1) {
		/* select a new chromosome */
		chromosome.selectAll('a').style('background-color', 'orange');
		ref.remove();
		currentRef = "";
		currentStart = 1;
		currentEnd = 0;

		if (level >= 2) {
			/* select a new project */
			project.selectAll('a').style('background-color', 'steelblue');
			chromosome.remove();
			currentChromTable = new Array();
			currentChrom = "";		
		}
	}
}

function loadProjects() {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText.split(',');
		project.selectAll('div')
			.data(res)
		.enter().append('div')
			.attr('class', 'project box')
			.attr('id', function(d) { return d; })
				.append('a')
				.attr('class', 'project element')
				.attr('id', function(d) { return d; })
				.text(function(d) { return d ;})
				.on('click', function(d, i) {
					if (d != currentProject) {
						if (currentProject.length != 0) {
							resetMenu(2);
						}
						currentProject = d;
						chromosome = d3.select('[id="' + d + '"]' + ".project.box")
									   .append('div')
									   .attr('class', 'chromosome container');
						url = '/data/' + d;
						sendGetRequest(url, loadChromosomes);
					}
				})
	}
}

function loadChromosomes() {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText;
		res = dsv.parseRows(res);
		
		currentChromTable[0] = res[0][0];
		res = res.slice(1);
		for (i in res) {
			currentChromTable[res[i][0]] = res[i].slice(1);
		}
		chroms = Object.keys(currentChromTable).slice(1); /*names of chromosomes*/

		chromosome.selectAll('div')
			.data(chroms)
		.enter().append('div')
			.attr('class', 'chromosome box')
			.attr('id', function(d) { return d; })
				.append('a')
				.attr('class', 'chromosome element')
				.attr('id', function(d) { return d; })
				.text(function(d) { return "Chromosome " + d + " Size:" + currentChromTable[d]; })
				.on('click', function(d, i) {
					if (d != currentChrom) {
						if (currentChrom.length != 0) {
							resetMenu(1);
						}
						currentChrom = d;
						currentEnd = currentChromTable[d];
						ref = d3.select('[id="' + d + '"]' + ".chromosome.box")
								.append('div')
								.attr('class', 'ref container');

						url = '/data/' + currentProject + '/' + this.id;
						sendGetRequest(url, loadRefs);
					}
				})
	}
}

var loadRefs = function () {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText;
		res = dsv.parseRows(res);

		ref.selectAll('div')
			.data(res)
		.enter().append('div')
			.attr('class', 'ref box')
			.attr('id', function(d) { return d; })
				.append('a')
				.attr('class', 'ref element')
				.attr('id', function(d) { return d; })
				.text(function(d) { return "Samples " + d; })
				.on('click', function(d, i) {
					if (d != currentRef) {
						if (currentRef.length != 0) {
							resetMenu(0);
						}
						currentRef = d;
						sample = d3.select('[id="' + d + '"]' + ".ref.box")
								   .append('div')
								   .attr('class', 'sample container');
						this.style.backgroundColor = 'lightgreen';
						url = '/data/' + currentProject + '/' + currentChrom + '/' + d;
						sendGetRequest(url, loadSamples);
					}
				})
	}
}

var loadSamples = function () {
	if (this.readyState == 4 && this.status == 200) {
		res = dsv.parseRows(this.responseText);

		sample.selectAll('div')
			.data(res)
		.enter().append('div')
			.attr('class', 'sample element')
			.attr('id', function(d) { return d; })
			.text(function(d) { return d; })
			.on('click', function(d, i) {
				if (this.classList[0] == 'clicked') {
					this.setAttribute('class', 'sample element');
					
					var pos = -1;
					for (idx in currentSamples) {
						if (currentSamples[idx] == d) {
							pos = idx;
						}
					}
					if (pos > -1) {
						currentSamples.splice(pos, 1);
					}
				} else {
					this.setAttribute('class', 'clicked sample element')

					currentSamples.push(d);
				}
			});

		showInputBoxes();
	}
}

var showInputBoxes = function () {
	var start = input.append('input')
		.attr('class', 'input element')
		.attr('id', 'start')
		.attr('placeholder', 'start: ' + 1);

	var end = input.append('input')
		.attr('class', 'input element')
		.attr('id', 'end')
		.attr('placeholder', 'end: ' + currentEnd);

	var nBins = input.append('input')
		.attr('class', 'input element')
		.attr('id', 'nBins')
		.attr('placeholder', 'nBins: ' + currentNumOfBins);

	var reset = input.append('a')
		.attr('class', 'input element')
		.attr('id', 'reset')
		.property('text', 'Reset')
		.on('click', function(d, i) {
			currentStart = 1;
			currentEnd = currentChromTable[currentChrom];
			currentNumOfBins = 100;

			start.property('value', currentStart);
			end.property('value', currentEnd);
			nBins.property('value', currentNumOfBins);

			var query = currentSamples.join(',') + '-' + currentNumOfBins + '-' + currentStart + '-' + currentEnd;
			url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRef + '/' + query;
			sendGetRequest(url, showData);
		});

	var send = input.append('a')
		.attr('class', 'input element')
		.attr('id', 'send')
		.property('text', 'send')
		.on('click', function(d, i) {
			if (currentSamples.length != 0) {
				if (nBins.property('value') != "") {
					currentNumOfBins = nBins.property('value');
				}
				nBins.property('value', currentNumOfBins);
				if (start.property('value') != "") {
					currentStart = start.property('value');
				}
				start.property('value', currentStart);
				if (end.property('value') != "") {
					currentEnd = end.property('value');	
				}
				end.property('value', currentEnd);

				var query = currentSamples.join(',') + '-' + currentNumOfBins + '-' + currentStart + '-' + currentEnd;
				url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRef + '/' + query;
				sendGetRequest(url, showData);
			}
		});


}


var showData = function () {
	if (this.readyState == 4 && this.status == 200) {
		output.selectAll('svg').remove();
		accessions.selectAll("div").remove();

		res = dsv.parseRows(this.responseText);
		var data = new Array()
		var maxData = 0;
		for (i in res) {
			data[res[i][0]] = res[i].slice(1).map(parseFloat);
			maxData = d3.max([maxData, d3.max(data[res[i][0]])]);
		}
		
		var colorScale = function (d) {
			var scale = d3.scaleLinear().domain([0, maxData]);
			return d3.interpolateRdPu(scale(d));
		}
		var y = d3.scaleLinear()
				  .range([height, 0])
				  .domain([0, maxData]);

		var width = output.property("clientWidth") * 0.9;
		var mouseLeft = parseInt(output.style("left")) - 15
		var mouseTop = parseInt(output.style("top")) - 5

		for (name in data) {
			accessions.append('div')
				.attr('id', name)
				.style('height', height + "px")
				.style('width', "100%")
				.append('a')
					.style('id', name)
					.style('display', "block")
					.property('text', name)
					.style('font-size', "30px");

			var barWidth = width / data[name].length;

			var bar = output.append('svg')
				.attr('class', 'chart ' + name)
				.attr('width', width)
				.attr('height', height)
				.selectAll('g')
				.data(data[name])
			.enter().append('g')
				.attr('class', 'output element ' + name)
				.attr('start', function(d, i) {
					return parseInt(currentStart) + parseInt((currentEnd - currentStart) * i / currentNumOfBins);
				})
				.attr('end', function(d, i) {
					return parseInt(currentStart) + parseInt((currentEnd - currentStart) * (i + 1) / currentNumOfBins);
				})
				.attr('transform', function(d, i) { return "translate(" + i * barWidth + ",0)"; })
				.on('mouseenter', function(d, i) {
					toolTip.append("div").text("Start: " + this.attributes["start"].value);
					toolTip.append("div").text("End: " + this.attributes["end"].value);
					toolTip.append("div").text("Distance: " + d);
					toolTip.style("left", event.pageX - mouseLeft + "px")
						   .style("top", event.pageY - mouseTop + "px")
						   //.text("Start: " + this.attributes["start"].value + "\n" + "End: " + this.attributes["end"].value + "\n" + "Distance: " + d)
						   .style("visibility", "visible");
				})
				.on('mousemove', function(d, i) {
					toolTip.style("left", event.pageX - mouseLeft + "px")
						   .style("top", event.pageY - mouseTop + "px");
				})
				.on("mouseleave", function(d, i) {
					toolTip.style("visibility", "hidden");
					toolTip.selectAll("div").remove();
				});

			bar.append('rect')
				.attr('class', name)
				.attr('id', function(d, i) { return i; })
				//.attr('y', function(d) { return y(d) ; })
				//.attr('height', function(d) { return height - y(d); })
				.attr('height', height)
				.attr('width', barWidth)
				.style("fill", function(d) { return colorScale(d); });
				/*.on("mousemove", function(d, i) {
					toolTip.append("div").text(this.attributes["class"].value);
					toolTip.append("div").text(this.id);
					toolTip.append("div").text(d);
					toolTip.style("left", event.pageX - 320 + "px")
						   .style("top", event.pageY + "px")
						   //.text(this.attributes["class"].value + "\n" + this.id + "\n" + d)
						   .style("visibility", "visible");
				});*/
				
		}

		output.on('click', function (d, i) {
			if (rectBox.style("display") == "none") {
				var startPos = d3.mouse(this);
				console.log(startPos);

				rectBox.style("left", startPos[0] + "px")
					   .style("top", startPos[1] + "px")
					   .style("width", "0px")
					   .style("height", "0px")
					   .style("display", "block");
					   //.text(startPos);

				output.on("mousemove", function (d, i) {
					var pos = d3.mouse(this);
					var width = pos[0] - startPos[0];
					var height = pos[1] - startPos[1];

					//rectBox.text(pos);
					if (width < 0) {
						rectBox.style("left", pos[0] + "px")
							   .style("width", Math.abs(width) + "px");
					} else {
						rectBox.style("left", startPos[0] + "px")
							   .style("width", Math.abs(width) + "px");
					}
					if (height < 0) {
						rectBox.style("top", pos[1] + "px")
							   .style("height", Math.abs(height) + "px");
					} else {
						rectBox.style("top", startPos[1] + "px")
							   .style("height", Math.abs(height) + "px");
					}
				});
			} else {
				
				var chartWidth = output.select("svg").property("clientWidth");
				var newStart = rectBox.property("offsetLeft");
				var newEnd = newStart + rectBox.property("offsetWidth");

				var currentLength = currentEnd - currentStart

				console.log(chartWidth);
				console.log(newStart);
				console.log(rectBox.property("offsetWidth"));
				console.log(newEnd);
				console.log(currentLength);

				currentEnd = parseInt(currentLength / chartWidth * newEnd + currentStart);
				currentStart = parseInt(currentLength / chartWidth * newStart + currentStart);

				console.log(currentEnd);
				console.log(currentStart);

				rectBox.style("display", "none");

				input.select("#end").property("value", currentEnd);
				input.select("#start").property("value", currentStart);
				nBins = input.select("#nBins")
				newNumOfBins = nBins.property("value")
				if (newNumOfBins != "") {
					currentNumOfBins = newNumOfBins
				} else {
					nBins.property("value", currentNumOfBins);
				}

				var query = currentSamples.join(',') + '-' + currentNumOfBins + '-' + currentStart + '-' + currentEnd;
				url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRef + '/' + query;
				sendGetRequest(url, showData);
			}
		});
	}
}

function defaultOnTimeOut() {
	console.log("Time Out");
}

send_request.on("click", function(d, i){

	var value = send_button.property("value")
	console.log(value)

	xmlhttp = new XMLHttpRequest();
	url = "/data/ref-10-1-1-10000-88:265"; 
	// format: data/reference-nBlocks-chromosome-start-end-samples
	// start and end should between 1 and length of chromosome
	xmlhttp.open("GET", url, true);
	xmlhttp.onreadystatechange = getOkGet;
	xmlhttp.send();

	function getOkGet(){
		if (xmlhttp.readyState==1||xmlhttp.readyState==2||xmlhttp.readyState==3) {
		}
		if (xmlhttp.readyState==4 && xmlhttp.status==200){ 
	　　　　	var res = xmlhttp.responseText;
			console.log(res);
		}
	}
});

