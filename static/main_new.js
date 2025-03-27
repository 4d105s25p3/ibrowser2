var width = 960,
	height = 40;

var navWidth = 300,
	accessionsWidth = 100,
	legandHeight = 80,
	averSNPsHeight = 40,
	rowHeight = 40;

var projectSelector = d3.select("select.project-selection");
var currentProject = "";

var modeSelector = d3.select("select.mode-selection");
var currentMode = "single";

var chromosomeSelector = d3.select("select.chromosome-selection");
var currentChromTable = new Array();
var currentChrom = "";

var singleRefSelector = d3.select(".reference-selection#single");
var singleRef = "";
var currentRefs = "";

var doubleRefSelector = d3.select(".reference-selection#double");
var firstRef = "";
var secondRef = "";

var multiRefSelector = d3.select(".reference-selection#multi");


var sampleSelector = d3.select("select.sample-selection");
var currentSamples = new Array();
var currentSampleSelection = new Array();

var parameterSelector = d3.select("div.parameter-selection");
var start = parameterSelector.select("#start").attr('placeholder', 'Start');
var end = parameterSelector.select("#end").attr('placeholder', 'End');
var nBins = parameterSelector.select("#nbins").attr('placeholder', 'nBins');


var currentStart = 1;
var currentEnd = 0;
var currentNumOfBins = 100;
var currentData;
var dataForDisplay;
var dataSorted = false;

var reset = d3.select("button#reset")
var confirm = d3.select("button#confirm");

var treeRender = d3.select("div#tree-render");
var treeCanvas = d3.select("div#tree-canvas");
var trees = new Array();

var legands = d3.select(".legands");
var drawTree = legands.select("#draw-tree");

var header = d3.select(".header.container");
var accessions = d3.select(".accessions.container");

var output = d3.select(".output.container");
var rectBox = output.select("#rectBox");
var toolTip = output.select("#toolTip");
var selectBox = output.select("#highLight");

var dsv = d3.dsvFormat(",");

window.onload = function() {
	sendGetRequest("/data/loading", loadProjects);
}

var sendGetRequest = function (url, onReady, timeOut = 0, onTimeOut = defaultOnTimeOut) {
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
	sampleSelector.selectAll("option.sample.data").remove();
	currentSamples = new Array();
	accessions.selectAll("div").remove();
	header.selectAll("svg").remove();
	drawTree.style("visibility", "hidden");
	dataSorted = false;

	if (level >= 1) {
		/* select a new chromosome */
		singleRefSelector.selectAll("option.reference.data").remove();
		doubleRefSelector.select("#first").selectAll("option.reference.data").remove();
		doubleRefSelector.select("#second").selectAll("option.reference.data").remove();
		multiRefSelector.selectAll("option.reference.data").remove();
		singleRef = "";
		firstRef = "";
		secondRef = "";
		currentRefs = "";
		currentStart = 1;
		currentEnd = 0;

		if (level >= 2) {
			/* select a new project */
			chromosomeSelector.selectAll("option.chromosome.data").remove();
			currentChromTable = new Array();
			currentChrom = "";		
		}
	}
}

function loadProjects() {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText.split(',');
		
		projectSelector.selectAll('option.project.data')
	    .data(res)
		.enter().append('option')
				.attr('class', 'project data')
				.attr('value', function(d) { return d; })
				.text( function(d) { return d; });

		projectSelector.on("change", function(d, i) {
			var selected = projectSelector.property("selectedOptions")[0].value;

			if (selected != "" && selected != currentProject) {
				if (currentProject.length != 0) {
					resetMenu(2);
				}
				currentProject = selected;
				url = '/data/' + currentProject;
				sendGetRequest(url, loadChromosomes);
			}
		});
	}
}

function loadChromosomes() {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText;
		res = dsv.parseRows(res);
		
		currentChromTable[0] = res[0][0]; // Project Name
		res = res.slice(1); // Other Data (ChromName: ChromLength)
		for (i in res) {
			currentChromTable[res[i][0]] = res[i].slice(1);
		}
		chromNames = Object.keys(currentChromTable).slice(1); // Names of Chromosomes

		chromosomeSelector.selectAll("option.chromosome.data")
		.data(chromNames)
		.enter().append("option")
				.attr("class", "chromosome data")
				.attr("value", function(d) { return d; })
				.text( function(d) { return "Chromosome " + d + " Size:" + currentChromTable[d]; });

		chromosomeSelector.on("change", function(d, i) {
			var selected = chromosomeSelector.property("selectedOptions")[0].value;

			if (selected != "" && selected != currentChrom) {
				if (currentChrom.length != 0) {
					resetMenu(1);
				}
				currentChrom = selected;
				currentEnd = parseInt(currentChromTable[currentChrom]);
				resetInputBoxes();

				switchMode();
				modeSelector.on("change", switchMode);

				url = '/data/' + currentProject + '/' + selected;
				sendGetRequest(url, loadRefs);
			}
		});
	}
}

function switchMode() {
	currentMode = modeSelector.property("selectedOptions")[0].value;

	if (currentMode == "single") {
		singleRefSelector.style("display", "block");
		doubleRefSelector.style("display", "none");
		multiRefSelector.style("display", "none");
		currentRefs = singleRef;
	} else if (currentMode == "double") {
		singleRefSelector.style("display", "none");
		doubleRefSelector.style("display", "block");
		multiRefSelector.style("display", "none");
		currentRefs = firstRef + "," + secondRef;
	} else if (currentMode == "multi") {
		singleRefSelector.style("display", "none");
		doubleRefSelector.style("display", "none");
		multiRefSelector.style("display", "block");
	}
}

var loadRefs = function () {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText;
		res = dsv.parseRows(res);
		console.log(res);

		singleRefSelector.selectAll("option.reference.data")
	  	.data(res).enter().append("option")
			.attr("class", "reference data")
			.attr("id", function(d) { return "id" + d; })
			.attr("value", function(d) { return d; })
			.text( function(d) { return d; });

		singleRefSelector.on("change", function(d, i) {
			var selected = singleRefSelector.property("selectedOptions")[0].value;
			console.log(selected);

			if (selected != "" && selected != singleRef) {
				resetMenu(0);
				singleRef = selected;
				currentRefs = singleRef;
				url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRefs;
				sendGetRequest(url, loadSamples);
			}
		});
		
		var first = doubleRefSelector.select("#first");
		first.selectAll("option.reference.data")
		.data(res).enter().append("option")
			.attr("class", "reference data")
			.attr("id", function(d) { return "id" + d; })
			.attr("value", function(d) { return d; })
			.text( function(d) { return d; });
		first.on("change", function(d, i) {
				var selected = first.property("selectedOptions")[0].value;
				console.log(selected);

				var returnOption = function(ref) { // add a ref to the other selector
					second.append("option")
						.attr("class", "reference data")
						.attr("id", "id" + ref)
						.attr("value", ref)
						.text(ref);
				}

				if (selected != firstRef) { 	// selection changed
					if (firstRef != "") { 			// select nothing, return previous selection to other selector
						returnOption(firstRef);
					}
					firstRef = selected;
					if (firstRef != "") { 			// select something, remove the selection from other selector
						second.select("#id" + firstRef).remove();

						if (secondRef == firstRef) { 	// repeated selections, will reset other ref
							secondRef = "";
						} else if (secondRef != "") {	// valid selections, will send request
							resetMenu(0);
							currentRefs = firstRef + "," + secondRef;					 	
							url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRefs;
							console.log(url);
							sendGetRequest(url, loadSamples);
						}
					}
				}
			});

		var second = doubleRefSelector.select("#second");
		second.selectAll("option.reference.data")
		.data(res).enter().append("option")
			.attr("class", "reference data")
			.attr("id", function(d) { return "id" + d; })
			.attr("value", function(d) { return d; })
			.text( function(d) { return d; });
		second.on("change", function(d, i) {
				var selected = second.property("selectedOptions")[0].value;
				console.log(selected);

				var returnOption = function(ref) { // add a ref to the other selector
					first.append("option")
						.attr("class", "reference data")
						.attr("id", "id" + ref)
						.attr("value", ref)
						.text(ref);
				}

				if (selected != secondRef) { 	// selection changed
					if (secondRef != "") { 			// select nothing, return previous selection to other selector
						returnOption(secondRef);
					}
					secondRef = selected;
					if (secondRef != "") { 			// select something, remove the selection from other selector
						first.select("#id" + secondRef).remove();

						if (firstRef == secondRef) { 	// repeated selections, will reset other ref
							firstRef = "";
						} else if (firstRef != "") {	// valid selections, will send request
							resetMenu(0);
							currentRefs = firstRef + "," + secondRef;	
							url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRefs;
							console.log(url);
							sendGetRequest(url, loadSamples);
						}
					}
				}
			});

		multiRefSelector.attr("size", res.length)
		.selectAll("option.reference.data")
		.data(res).enter().append("option")
			.attr("class", "reference data")
			.attr("value", function(d) { return d; })
			.text( function(d) { return d; });

		multiRefSelector.on("change", function(d, i) {
			var selected = new Array();
			for (var i = 0; i < multiRefSelector.property("selectedOptions").length; i++) {
				selected[i] = multiRefSelector.property("selectedOptions")[i].value;
			}
			console.log(selected);

			if (selected.length != 0) {
				resetMenu(0);
				currentRefs = selected.toString();
				url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRefs;
				sendGetRequest(url, loadSamples);
			}
		})
	}
}


var loadSamples = function () {
	if (this.readyState == 4 && this.status == 200) {
		res = dsv.parseRows(this.responseText);
		res.sort(function(item1, item2) {
			return item1[0].localeCompare(item2[0]);
		})
		console.log(res);

		sampleSelector.attr("size", res.length)
		.selectAll("option.sample.data")
		.data(res)
		.enter().append("option")
				.attr("class", "sample data")
				.attr("value", function(d) { return d; })
				.text( function(d) { return d; });

		reset.on('click', function(d, i) {
			currentStart = 1;
			currentEnd = parseInt(currentChromTable[currentChrom]);
			currentNumOfBins = 100;

			start.property("value", currentStart);
			end.property("value", currentEnd);
			nBins.property("value", currentNumOfBins);
			dataSorted = false;
			// resort by names
			currentSamples.sort(function(sample1, sample2){
				return sample1.localeCompare(sample2);
			});

			var query = [currentSamples.join(','), currentNumOfBins, currentStart, currentEnd].join("-");
			url = "/data/" + [currentProject, currentChrom, currentRefs, currentMode, query].join("/");
			sendGetRequest(url, showData);
		});

		confirm.on('click', function(d, i) {
			var selected = sampleSelector.property("selectedOptions");
			

			if (selected.length != 0) { // at least one sample is selected
				var newSampleSelection = new Array();
				for (var i = 0; i < selected.length; i++) {
					newSampleSelection[i] = selected[i].value
				}
				newSampleSelection.sort(function(sample1, sample2) { return sample1 - sample2; });
				if (currentSampleSelection.toString() != newSampleSelection.toString()) { // selected samples changed
					currentSampleSelection = newSampleSelection;
					for (var i = 0; i < selected.length; i++ ) {
						currentSamples[i] = selected[i].value;
					}
				}
				// if samples not changed, then currentSamples (which may indicate current visualizing order) will be used
				if (nBins.property('value') != "") {
					currentNumOfBins = parseInt(nBins.property('value'));
				}
				nBins.property('value', currentNumOfBins);
				if (start.property('value') != "") {
					currentStart = parseInt(start.property('value'));
				}
				start.property('value', currentStart);
				if (end.property('value') != "") {
					currentEnd = parseInt(end.property('value'));	
				}
				end.property('value', currentEnd);

				var query = [currentSamples.join(','), currentNumOfBins, currentStart, currentEnd].join("-");
				url = "/data/" + [currentProject, currentChrom, currentRefs, currentMode, query].join("/");
				sendGetRequest(url, showData);
			}
		});	
	}
}

var resetInputBoxes = function () {
	start.attr('placeholder', 'Start: ' + 1)
		.property("value", 1);
	end.attr('placeholder', 'End: ' + currentEnd)
		.property("value", currentEnd);
	nBins.attr('placeholder', 'nBins: ' + currentNumOfBins)
		.property("value", currentNumOfBins);
}


var transferMultiColor = function(distArray, colorArray) {
	if (distArray.length == colorArray.length) {
		var totalDist = 0;
		distArray.forEach(function(val){
			totalDist += val;
		});

		var colorFractions = colorArray.map(function(baseColor, idx){
			var colorFraction = baseColor.map(function(val){
				return val * distArray[idx] / totalDist;
			});
			return colorFraction;
		});

		var finalColor = [0, 0, 0];
		colorFractions.forEach(function(colorFraction) {
			colorFraction.forEach(function(val, idx){
				finalColor[idx] += val;
			});
		});

		return finalColor;
	}
}

var multiColor = function(res, colorArray) {
	var samples = Object.keys(res);
	var refs = Object.keys(res[samples[0]]);
	var numOfBins = res[samples[0]][refs[0]].length;
	if (refs.length == colorArray.length) {
		var colorRes = [];
		for (var i = 0; i < samples.length; i++) {
			colorRes[i] = {data: [], sample: samples[i]};
			for (var j = 0; j < numOfBins; j++) {
				var distArray = [];
				for (var k = 0; k < refs.length; k++) {
					distArray[k] = res[samples[i]][refs[k]][j];
				}
				colorRes[i].data[j] = transferMultiColor(distArray, colorArray);
			}
		}
		return colorRes;
	}
}

var isArrEqual = function (arr1, arr2) {
	// returns true if two arrays have identical unique elements
	return arr1.every(function(item){
		return arr2.includes(item);
	}) && arr2.every(function(item){
		return arr1.includes(item);
	});
}

var showData = function () {

	if (this.readyState == 4 && this.status == 200) {
		output.selectAll("svg").remove();
		accessions.selectAll("div").remove();
		header.selectAll("svg").remove();
		selectBox.style("visibility", "hidden");

		// store data
		res = JSON.parse(this.responseText);
		
		if (currentMode == "multi") {
			var colorArray = [[255, 0, 0], [0, 255, 0], [0, 0, 255]];
			currentData = multiColor(res, colorArray);
		} else {
			currentData = res;
		}
		
		// find largest and smallest data point
		var maxData = 0;
		var minData = 1;
		for (idx in currentData) {
			minData = d3.min([minData, d3.min(currentData[idx].data)]);
			maxData = d3.max([maxData, d3.max(currentData[idx].data)])
		}

		if (dataSorted){
			currentData.sort(function(item1, item2){ // Sort by order in samples list
				var sample1 = item1.sample,
					sample2 = item2.sample;
				var index1 = currentSamples.findIndex(function(sample){
					return sample == sample1;
				}),
					index2 = currentSamples.findIndex(function(sample){
					return sample == sample2;
				});
				return index1 - index2;
			});
		} else {
			currentData.sort(function(row1, row2) { // By default, sort by name
				return row1.sample.localeCompare(row2.sample);
			});
		}
		
		console.log("maxData: ");
		console.log(maxData);
		console.log("minData: ");
		console.log(minData);
		
		// construct color scale
		var multiColorScale = function (distMatrix, colorArray) {

		}

		var colorScale = function (d) {
			var scale = d3.scaleLinear().domain([0, maxData]);
			return d3.interpolateRdPu(scale(d));
		}
		var colorScaleBuGn = function (d) {
			var scale = d3.scaleLinear().domain([1, maxData]);
			return d3.interpolateBuGn(scale(d));
		}
		
		var pow2Scale1 = function (d) {
			var scale = d3.scalePow().domain([1, minData]).exponent(0.3);
			return d3.interpolateOrRd(scale(d));
		}
		var pow2Scale2 = function (d) {
			var scale = d3.scalePow().domain([1, maxData]).exponent(0.3);
			return d3.interpolateBuGn(scale(d));
		}
		var y = d3.scaleLinear()
				  .range([height, 0])
				  .domain([0, maxData]);
		var fillColor = function (d) {
			if (currentMode == "single") {
				return colorScale(d);
			} else if (currentMode == "double") {
				if (d > 1) { return pow2Scale2(d); }
				else { return pow2Scale1(d); }
			} else if (currentMode == "multi") {
				return "rgb(" + d + ")";
			}
		}

		// remove old color scale legands
		legands.select("svg#bar").selectAll("g").remove();
		legands.select("div#text").text("");

		// draw new color scale legands 
		var legandScale = function() {
			if (currentMode == "single") {
				return Array.from(Array(10)).map((val, i) => { 
					return maxData*i/10; });
			} else {
				return Array.from(Array(16)).map((val, i) => {
					if (i < 8) { 
						return (1-minData)*(i+1)/8+minData; 
					} else { 
						return (maxData-1)*(i-7)/8+1; 
					}
				});
			}
		}
		legands.select("div#text").text("Min: " + d3.format(".3")(minData) + " Max: " + d3.format(".3")(maxData));
		legands.select("svg#bar")
			.selectAll("g")
			.data(legandScale()).enter()
			.append("g")
				.attr("class", "colorScale element")
				.attr('transform', function(d, i) { return "translate(" + i * 10 + ",0)"; })
				.on("mouseenter", function(d, i) {
					legands.select("div#text").text("Distance: " + d3.format(".3")(d));
				})
				.on("mouseleave", function(d, i) {
					legands.select("div#text").text("Min: " + d3.format(".3")(minData) + " Max: " + d3.format(".3")(maxData))
				})
				.append("rect")
					.attr("class", "colorScale block")
					.style("fill", function(d) { return fillColor(d); });

		var width = (output.property("clientWidth") - 300) * 0.9;

		accessions.append("div")
			.attr("class", "sum")
			.style("height", height + "px")
			.style("width", "100%")
			.append("a")
				.attr("class", "accession-text sum")
				.property("text", "Total SNPs");

		var totalSNPs = new Array();
		for (var i = 0; i < currentNumOfBins; i++) {
			totalSNPs[i] = 0;
		}

		// draw graphs
		var rowCounter = 0;
		for (idx in currentData) {
			var sample = currentData[idx].sample;
			var data = currentData[idx].data;

			accessions.append('div')
				.attr("class", "samples")
				.attr('id', sample)
				.style('height', height + "px")
				.style('width', "100%")
				.append('a')
					.attr("class", "accession-text samples " + sample)
					.property('text', sample);

			var barWidth = width / data.length;
			for (var i = 0; i < data.length; i++) {
				totalSNPs[i] += data[i];
			}
			
			output.append("svg")
				.attr("id", "row" + rowCounter)
				.attr("class", "chart " + sample)
				.attr("width", "100%")
				.attr("height", height)
				.selectAll("g")
				.data(data)
				.enter().append("g")
					.attr("class", "output element " + sample)
					.attr("id", function(d, i) { return "col" + i; })
					.attr("start", function(d, i) {
						return currentStart + parseInt((currentEnd - currentStart) * i / currentNumOfBins);
					})
					.attr("end", function(d, i) {
						return currentStart + parseInt((currentEnd - currentStart) * (i + 1) / currentNumOfBins);
					})
					.attr("transform", function(d, i) { return "translate(" + i * barWidth + ",0)"; })
					.attr("value", function(d) { return d; })
					// for mouse hover
					.on('mouseenter', function(d, i) {
						legands.select("#start").text("Start: " + this.getAttribute("start"));
						legands.select("#end").text("End: " + this.getAttribute("end"));
						legands.select("#distance").text("Distance: " + d3.format(".3")(d));

						legands.selectAll(".position").style("visibility", "visible");
					})
					.on("mouseleave", function(d, i) {
						legands.selectAll(".position").style("visibility", "hidden");
					})
					// for selecting a column
					.on("click", function(d, i){ 
						var leftOffSet = i * barWidth;
						//var topOffSet = legandHeight + averSNPsHeight; //rowCounter * rowHeight + legandHeight + averSNPsHeight;
						var selectBox =   d3.select("#highLight")
											.style("left", leftOffSet + "px")
											.style("top", "0px")
											.style("width", barWidth + "px")
											.style("height", height * currentData.length + "px")
											.style("visibility", "visible");
						legands.select(".selectedCol#information").text("selected: " + this.getAttribute("start") + " to " + this.getAttribute("end"));
						
						var selectedStart = parseInt(this.getAttribute("start"));
						var selectedEnd = parseInt(this.getAttribute("end"));

						var accessions = currentSamples.concat(currentRefs.split(","));
						accessions.sort( function(a,b) { return a.localeCompare(b); } );
						url = "/tree/" + currentProject + "/" + currentChrom + "/" + accessions.join(",") + "/" + selectedStart + "/" + selectedEnd;

						drawTree.style("visibility", "visible")
						if (!document.getElementById(url)) {
							drawTree.text("Draw Tree")
								.on("click", function(d, i){
									var newTree = document.createElement("div");
									newTree.setAttribute("id", url);
									newTree.setAttribute("class", "tree");
									treeCanvas.node().appendChild(newTree);
									sendGetRequest(url, showTree);
									drawTree.property("disabled", false)
										.text("Show Tree")
										.on("click", function(d, i){
											document.getElementById(url).setAttribute("style", "display: block");
										});
								});
						} else {
							drawTree.text("Show Tree")
								.on("click", function(d, i){
									document.getElementById(url).setAttribute("style", "display: block");
								});
						}
					})
					// draw blocks
					.append("rect")
						.attr("height", height)
						.attr("width", barWidth)
						.style("fill", function(d) { return fillColor(d); });
			rowCounter++;
		}

		// add data to header
		totalSNPs = totalSNPs.map(x => x / currentData.length);
		header.append("svg")
			.attr("class", "chart " + currentRefs)
			.attr('width', width)
			.attr('height', height)
			.selectAll("g")
			.data(totalSNPs)
			.enter().append("g")
				.attr("class", "output element")
				.attr("id", function(d, i) { return "col" + i; })
				.attr("start", function(d, i) {
					return currentStart + parseInt((currentEnd - currentStart) * i / currentNumOfBins);
				})
				.attr("end", function(d, i) {
					return currentStart + parseInt((currentEnd - currentStart) * (i + 1) / currentNumOfBins);
				})
				.attr("transform", function(d, i) { return "translate(" + i * barWidth + ",0)"; })
				.attr("value", function(d) { return d; })
				.attr("sort", "none")
				.append("rect")
					.attr("height", height)
					.attr("width", barWidth)
					.style("fill", function(d) { return fillColor(d); });

		/*
		// for mouse hover
		d3.selectAll("g.output.element").on('mouseenter', function(d, i) {
				legands.select("#start").text("Start: " + this.attributes["start"].value);
				legands.select("#end").text("End: " + this.attributes["end"].value);
				legands.select("#distance").text("Distance: " + d3.format(".3")(d));

				legands.selectAll(".position").style("visibility", "visible");
			})
			.on("mouseleave", function(d, i) {
				legands.selectAll(".position").style("visibility", "hidden");
			})
		// for choosing a block/column
			.on("click", function(){ 
				var leftOffSet = parseFloat(this.getAttribute("transform").split("(")[1].split(",")[0]);
				var topOffSet = parseInt(this.parentElement.getAttribute("id").slice(3)) * rowHeight + legandHeight + averSNPsHeight;

				var selectBox =   d3.select("#highLight")
									.style("left", leftOffSet + "px")
									.style("top", topOffSet + "px")
									.style("width")
			});
			*/

		// click on header to sort
		header.selectAll("g").on("click", function(d, i) {
			var colId = parseInt(this.id.slice(3,));

			var sortState = this.getAttribute("sort");
			if (sortState == "none" || sortState == "desend") {
				this.setAttribute("sort", "ascend");
				currentData.sort(function(sample1, sample2) {
					return sample1.data[colId] - sample2.data[colId];
				});
			} else {
				this.setAttribute("sort", "desend");
				currentData.sort(function(sample1, sample2) {
					return sample2.data[colId] - sample1.data[colId];
				});
			}
			dataSorted = true;
			console.log(currentData);

			for (var i = 0; i < currentData.length; i++) {
				currentSamples[i] = currentData[i].sample;
			}

			accessions.selectAll("div.samples").remove();

			var rowCounter = 0;
			for (idx in currentData) {
				var sample = currentData[idx].sample;
				var data = currentData[idx].data;
				accessions.append('div')
					.attr("class", "samples")
					.attr('id', sample)
					.style('height', height + "px")
					.style('width', "100%")
					.append('a')
						.attr("class", "accession-text samples " + sample)
						.property('text', sample);

				var row = output.select("svg#row" + rowCounter);
				row.selectAll("g")
					.data(data)
					.attr("class", "output element " + sample)
					.attr("value", function(d) { return d; })
					.select("rect")
						.style("fill", function(d) { return fillColor(d); });
				rowCounter++;
			}
		});

		// click on data to zoom in
		output.on("mousedown", function() {
			if (d3.event.ctrlKey){
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
			}
		});
		output.on("mouseup", function(){
			if (rectBox.style("display") == "block"){
				var chartWidth = output.select("svg").property("clientWidth");
				var newStart = rectBox.property("offsetLeft") + navWidth + accessionsWidth;
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

				end.property("value", currentEnd);
				start.property("value", currentStart);
				newNumOfBins = nBins.property("value")
				if (newNumOfBins != "") {
					currentNumOfBins = parseInt(newNumOfBins);
				} else {
					nBins.property("value", currentNumOfBins);
				}

				var query = [currentSamples.join(','), currentNumOfBins, currentStart, currentEnd].join("-");
				url = "/data/" + [currentProject, currentChrom, currentRefs, currentMode, query].join("/");
				sendGetRequest(url, showData);
			}
		})

		/*
		output.on('click', function (d, i) {
			if (d3.event.ctrlKey) {
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

					end.property("value", currentEnd);
					start.property("value", currentStart);
					newNumOfBins = nBins.property("value")
					if (newNumOfBins != "") {
						currentNumOfBins = parseInt(newNumOfBins);
					} else {
						nBins.property("value", currentNumOfBins);
					}

					var query = currentSamples.join(',') + '-' + currentNumOfBins + '-' + currentStart + '-' + currentEnd;
					url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRefs + '/' + query;
					sendGetRequest(url, showData);
				}
			}
		});
		*/

		// enable button for tree generating
		
	}
}

var showTree = function() {
	if (this.readyState == 4 && this.status == 200) {
		console.log(this.responseText);
		console.log(this.responseURL);

		var url = this.responseURL;
		url = url.slice(url.indexOf("tree") - 1);
		/*
		var query = this.responseURL.split("/").reverse()[0].split("-");
		var start = query[1];
		var end = query[2];
		var accessions = query[0].split(",");
		*/
		//treeCanvas.select("div.")

		var treeSvg = insertTree(this.responseText, url);
	}
}

var insertTree = function(treeStr, id_to_render) {
	Smits.PhyloCanvas.Render.Style.bootstrap = { 'font-size': 0 };

    var numSpps          = treeStr.split(',').length;
    var height 			 = numSpps * 14;
    var heightS          = numSpps * 12;
    var width 			 = 300;
    var widthS           = heightS;

    var phylocanvas = new Smits.PhyloCanvas(
        { 'newick': treeStr }, // Newick or XML string
        id_to_render,         // div id where to render
        widthS,
        heightS,
        'rectangular'
    );

    console.log('show tree: created');

    var el = document.getElementById(id_to_render).getElementsByTagName('svg')[0];
    el.setAttribute('viewBox'            , '0 0 '+widthS+' '+(heightS + 12) );
    el.setAttribute('preserveAspectRatio',                          'none' );
    el.setAttribute('width'              ,                          width  );
    el.setAttribute('height'             ,                          height );

    return phylocanvas.getSvgSource();
}

var defaultOnTimeOut = function() {
	console.log("Time Out");
}