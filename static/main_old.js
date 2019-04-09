var width = 960,
	height = 50;

var y = d3.scaleLinear()
	.range([height, 0]);

var send_button = d3.select("input");
var send_request = d3.select("a");
var project = d3.select(".project.container");
var chromosome = d3.select(".chromosome.container");
var ref = d3.select(".ref.container");
var input = d3.select(".input.container");
var output = d3.select(".output.container")
	.attr('width', width + 200);

var dsv = d3.dsvFormat(",");
var currentProject = "";
var currentChrom = "";
var currentRef = "";
var currentSamples = new Array();

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

function loadProjects() {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText.split(',');
		project.selectAll('div')
			.data(res)
		.enter().append('div')
			.attr('class', 'project element')
			.attr('id', function(d) { return d; })
			.text(function(d) { return d ;})
			.on('click', function(d, i) {
				output.selectAll('svg').remove();
				chromosome.selectAll('div').remove();
				ref.selectAll('div').remove();
				resetRefsChoices();
				currentProject = d;
				url = '/data/' + d;
				sendGetRequest(url, loadChromosomes);
			})
	}
}

function loadChromosomes() {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText;
		console.log(res);
		res = dsv.parseRows(res);
		console.log(res)
		
		chromsTable = new Array();
		chromsTable[0] = res[0][0];
		res = res.slice(1);
		for (i in res) {
			chromsTable[res[i][0]] = res[i].slice(1);
		}
		chroms = Object.keys(chromsTable).slice(1); /*names of chromosomes*/

		console.log(chromsTable);
		console.log(chroms);

		chromosome.selectAll('div')
			.data(chroms)
		.enter().append('div')
			.attr('class', 'chromosome element')
			.attr('id', function(d) { return d; })
			.text(function(d) { return "Chromosome " + d + " Size:" + chromsTable[d]; })
			.on('click', function(d, i) {
				output.selectAll('svg').remove();
				ref.selectAll('div').remove();
				resetRefsChoices();
				url = '/data/' + currentProject + '/' + this.id;
				console.log(url);
				currentChrom = d;
				sendGetRequest(url, loadRefs);
			})
	}
}

var loadRefs = function () {
	if (this.readyState == 4 && this.status == 200) {
		var res = this.responseText;
		res = dsv.parseRows(res);
		console.log(res);

		ref.selectAll('div')
			.data(res)
		.enter().append('div')
			.attr('class', 'ref element')
			.attr('id', function(d) { return d; })
			.text(function(d) { return "Samples " + d; })
			.on('click', function(d, i) {
				currentRef = d;

				resetRefsChoices();
				this.style.backgroundColor = 'lightgreen';
				url = '/data/' + currentProject + '/' + currentChrom + '/' + d;
				console.log(url);
				sendGetRequest(url, loadSamples);
			})
	}
}

var loadSamples = function () {
	if (this.readyState == 4 && this.status == 200) {
		res = dsv.parseRows(this.responseText);
		console.log(res);

		input.selectAll('div')
			.data(res)
		.enter().append('div')
			.attr('class', 'sample element')
			.attr('id', function(d) { return d; })
			.text(function(d) { return d; })
			.on('click', function(d, i) {
				if (this.classList[0] == 'clicked') {
					this.setAttribute('class', 'sample element');
					this.style.backgroundColor = 'black';
					
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
					this.style.backgroundColor = 'grey';

					currentSamples.push(d);
				}
				console.log(currentSamples)
			});

		showInputBoxes();
	}
}

var showInputBoxes = function () {
	var start = input.append('input')
		.attr('class', 'input element')
		.attr('id', 'start')
		.attr('placeholder', 'start');

	var end = input.append('input')
		.attr('class', 'input element')
		.attr('id', 'end')
		.attr('placeholder', 'end');

	var nBins = input.append('input')
		.attr('class', 'input element')
		.attr('id', 'nBins')
		.attr('placeholder', 'nBins')

	var send = input.append('a')
		.attr('class', 'input element')
		.attr('id', 'send')
		.attr('text', 'send')
		.property('text', 'send')
		.on('click', function(d, i) {
			if (currentSamples.length != 0) {
				var numOfBins = nBins.property('value');
				console.log(numOfBins)
				if (numOfBins == "") {
					numOfBins = 50; /* default */
				} else {
					numOfBins = parseInt(numOfBins);
				}
				var startPos = start.property('value');
				var endPos = end.property('value');

				var query = currentSamples.join(',') + '-' + numOfBins + '-' + startPos + '-' + endPos;
				url = '/data/' + currentProject + '/' + currentChrom + '/' + currentRef + '/' + query;
				console.log(url);
				sendGetRequest(url, showData);
			}
		})
}

var resetRefsChoices = function () {
	ref.selectAll('div').style('background-color', 'green');
	input.selectAll('div').remove();
	input.selectAll('input').remove();
	input.selectAll('a').remove();
	currentSamples = new Array();
}

var showData = function () {
	if (this.readyState == 4 && this.status == 200) {
		output.selectAll('svg').remove();

		res = dsv.parseRows(this.responseText);
		var data = new Array()
		for (i in res) {
			data[res[i][0]] = res[i].slice(1);
		}

		console.log(data)

		for (i in data) {
			var barWidth = width / data[i].length;

			var bar = output.append('svg')
				.attr('class', 'chart')
				.attr('width', width)
				.attr('height', height)
				.selectAll('g')
				.data(data[i])
			.enter().append('g')
				.attr('class', 'output element')
				.attr('transform', function(d, i) { return "translate(" + i * barWidth + ",0)"; });

			bar.append('rect')
				.attr('y', function(d) { return y(d * 100) ; })
				.attr('height', function(d) { return height - y(d * 100); })
				.attr('width', barWidth - 1);
		}
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

