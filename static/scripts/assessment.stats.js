// Template pie chart styles
var pieChartOptions = {
	chart: {
		width: 380,
		type: 'pie',
	},
	title: {
		text: '',
		align: 'left'
	}
};

// Template bar chart styles
var barChartOptions = {
	series: [],
	chart: {
		type: 'bar',
		height: 350
	},
	plotOptions: {
		bar: {
			horizontal: false,
			columnWidth: '55%',
			endingShape: 'rounded'
		},
	},
	dataLabels: {
		enabled: false
	},
	stroke: {
		show: true,
		width: 2,
		colors: ['transparent']
	},
	xaxis: {
		categories: []
	},
	yaxis: {
		title: {
			text: 'Count'
		},
		tickAmount: 1
	},
	fill: {
		opacity: 1
	},
	title: {
		text: '',
		align: 'left'
	},
};

// Template boxplot styling
var boxChartOptions = {
	series: [
		{
			type: 'boxPlot',
			data: Object.keys(tacticStats).map((i) => {
				return {
					x: i,
					y: boxPlotVals(tacticStats[i]["scoresPrevent"])
				}
			})
		}
	],
	chart: {
		type: 'boxPlot',
		height: 350
	},
	title: {
		text: 'Prevention and Detection Scores per Tactic',
		align: 'left'
	}
};

// Boxplot helper functions
function getPercentile(data, percentile) {
	data.sort(numSort);
	var index = (percentile / 100) * data.length;
	var result;
	if (Math.floor(index) == index) {
		result = (data[(index - 1)] + data[index]) / 2;
	}
	else {
		result = data[Math.floor(index)];
	}
	return result;
}
function numSort(a, b) {
	return a - b;
}
function boxPlotVals(data) {
	return [
		Math.min.apply(Math, data),
		getPercentile(data, 25),
		getPercentile(data, 50),
		getPercentile(data, 75),
		Math.max.apply(Math, data)
	]
}

// Outcome pie chart
var resultsPie = JSON.parse(JSON.stringify(pieChartOptions));
resultsPie.title.text = "Outcomes"
keys = ["Prevented", "Alerted", "Logged", "Missed"]
resultsPie.series = keys.map((t) => {
	return tacticStats["All"][t]
})
resultsPie.labels = keys
var chart = new ApexCharts(document.querySelector("#resultspie"), resultsPie);
chart.render();

// Outcome bar chart
var results = JSON.parse(JSON.stringify(barChartOptions));
results.title.text = "Outcome per Tactic"
results.series = ["Prevented", "Alerted", "Logged", "Missed"].map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).map((i) => {
			return tacticStats[i][t]
		})
	}
})
results.xaxis.categories = Object.keys(tacticStats)
var chart = new ApexCharts(document.querySelector("#results"), results);
chart.render();

// Alert bar chart
var alerts = JSON.parse(JSON.stringify(barChartOptions));
alerts.title.text = "Alert Severities per Tactic"
alerts.series = ["Informational", "Low", "Medium", "High", "Critical"].map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).map((i) => {
			return tacticStats[i][t]
		})
	}
})
alerts.xaxis.categories = Object.keys(tacticStats)
var chart = new ApexCharts(document.querySelector("#alerts"), alerts);
chart.render();

// Priority bar chart
var priorities = JSON.parse(JSON.stringify(barChartOptions));
priorities.title.text = "Priority Action and Priority per Tactic"
priorities.series = ["Prevent", "Detect", "Low", "Medium", "High"].map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).map((i) => {
			return tacticStats[i]["priorityType"].concat(tacticStats[i]["priorityUrgency"]).filter(x => x === t).length
		})
	}
})
priorities.xaxis.categories = Object.keys(tacticStats)
var chart = new ApexCharts(document.querySelector("#priorities"), priorities);
chart.render();

// Control bar chart
var controls = JSON.parse(JSON.stringify(barChartOptions));
controls.title.text = "Controls per Tactic"
controlKeys = [...new Set(tacticStats["All"]["controls"])]
controls.series = controlKeys.map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).map((i) => {
			return tacticStats[i]["controls"].filter(x => x === t).length
		})
	}
})
controls.xaxis.categories = Object.keys(tacticStats)
var chart = new ApexCharts(document.querySelector("#controls"), controls);
chart.render();

// Prev/detect box plot chart
var chart = new ApexCharts(document.querySelector("#scores"), boxChartOptions);
chart.render();