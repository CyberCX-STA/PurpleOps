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
		height: 370 	// Originally 350
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
		categories: [],
		labels: {
                show: true,
                rotate: -45,
                rotateAlways: true,
                trim: false,
        },
    },
	yaxis: {
		title: {
			text: 'Count'
		},
		tickAmount: 2 	// Originally 1
	},
	fill: {
		opacity: 1
	},
	title: {
		text: '',
		align: 'left'
	},
};

// Custom bar chart styles for individual Tactics results
var barChartOptionsCustom = {
	series: [{
		name: 'Results',
		data: []
	}],
	chart: {
		type: 'bar',
		height: 370 	// Originally 350
	},
	plotOptions: {
		bar: {
			horizontal: false,
			columnWidth: '55%',
			endingShape: 'rounded'
		},
	},
	dataLabels: {
		enabled: true 	// Originally false
	},
	stroke: {
		show: true,
		width: 2,
		colors: ['transparent']
	},
	xaxis: {
		type: 'category',
		categories: ["Prevented and Alerted", "Prevented","Alerted","Logged","Missed"],
		labels: {
                	show: false,
                	rotate: -45,
                	rotateAlways: true,
                	trim: false,
        	},
    	},
	yaxis: {
		show: true,
		title: {
			text: 'Count',
			rotate: -90,
		},
		labels: {
			show: true,
			rotate: 0,
		},
		tickAmount: 2 	// Originally 1
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


// Outcomes pie chart
var resultsPie = JSON.parse(JSON.stringify(pieChartOptions));
resultsPie.title.text = "Outcomes"
keys = ["Prevented and Alerted", "Prevented", "Alerted", "Logged", "Missed"]
resultsPie.series = keys.map((t) => {
	return tacticStats["All"][t]
})
resultsPie.labels = keys
var chart = new ApexCharts(document.querySelector("#resultspie"), resultsPie);
chart.render();


// Outcome bar chart (Excluding "All")
var results = JSON.parse(JSON.stringify(barChartOptions));
results.title.text = "Outcome per Tactic"
results.series = ["Prevented and Alerted", "Prevented", "Alerted", "Logged", "Missed"].map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).filter((i) => i !== "All").map((i) => {
			return tacticStats[i][t]
		})
	}
})
results.xaxis.categories = Object.keys(tacticStats).filter((i) => i !== "All");
var chart = new ApexCharts(document.querySelector("#results"), results);
chart.render();


// Alert bar chart (Excluding "All")
var alerts = JSON.parse(JSON.stringify(barChartOptions));
alerts.title.text = "Alert Severities per Tactic"
alerts.series = ["Informational", "Low", "Medium", "High", "Critical"].map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).filter((i) => i !== "All").map((i) => {
			return tacticStats[i][t]
		})
	}
})
alerts.xaxis.categories = Object.keys(tacticStats).filter((i) => i !== "All");
var chart = new ApexCharts(document.querySelector("#alerts"), alerts);
chart.render();


// Priority bar chart (Excluding "All")
var priorities = JSON.parse(JSON.stringify(barChartOptions));
priorities.title.text = "Priority Action and Priority per Tactic"
priorities.series = ["Prevent and Alert", "Prevent", "Detect", "Low", "Medium", "High"].map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).filter((i) => i !== "All").map((i) => {
			return tacticStats[i]["priorityType"].concat(tacticStats[i]["priorityUrgency"]).filter(x => x === t).length
		})
	}
})
priorities.xaxis.categories = Object.keys(tacticStats).filter((i) => i !== "All");
var chart = new ApexCharts(document.querySelector("#priorities"), priorities);
chart.render();


// Control bar chart (Excluding "All")
var controls = JSON.parse(JSON.stringify(barChartOptions));
controls.title.text = "Controls per Tactic"
controlKeys = [...new Set(tacticStats["All"]["controls"])]
controls.series = controlKeys.map((t) => {
	return {
		name: t,
		data: Object.keys(tacticStats).filter((i) => i !== "All").map((i) => {
			return tacticStats[i]["controls"].filter(x => x === t).length
		})
	}
})
controls.xaxis.categories = Object.keys(tacticStats).filter((i) => i !== "All");
var chart = new ApexCharts(document.querySelector("#controls"), controls);
chart.render();


// Prev/detect box plot chart
var chart = new ApexCharts(document.querySelector("#scores"), boxChartOptions);
chart.render();


function isObjectNotEmpty(obj) {
    if (obj === undefined) {
        return false; // If object is undefined, return false
    }
    for (var key in obj) {
        if (obj.hasOwnProperty(key) && obj[key] !== 0) {
            return true; // If any non-zero value is found, return true
        }
    }
    return false; // If all values are zero or undefined, return false
}

var noDataOptions = {
    text: 'There is no data available for this Tactic',
    align: 'center',
    verticalAlign: 'middle',
    offsetX: 0,
    offsetY: 0,
    style: {
        fontSize: '14px',
    }
};

function renderTacticChart(name, filteredTacticStats, chartContainerId) {
    var results = JSON.parse(JSON.stringify(barChartOptionsCustom));
    results.title.text = name + " Results";
    if (isObjectNotEmpty(filteredTacticStats)) {
            // Loop over each element and set each value from filteredTacticStats
            results.series = ["Prevented and Alerted", "Prevented", "Alerted", "Logged", "Missed"].map((t) => {
                return {
                    name: t,
                    data: [filteredTacticStats[t]] // Put the count of each outcome into an array
                };
            });
            results.xaxis.categories = [name];
            var chart = new ApexCharts(document.querySelector(chartContainerId), results);
            chart.render();
    } else {
            console.warn(`No data available for rendering the '${name}' chart.`);
            var chart = new ApexCharts(document.querySelector(chartContainerId), {
		...results,
		noData: noDataOptions
	    });
            chart.render();
    }
}

// Render individual chart results of each Tactic - Outputs "No data available" if chart is empty
var Tactics = ["Reconnaissance","Resource Development","Initial Access","Execution","Persistence","Privilege Escalation","Defense Evasion","Credential Access","Discovery","Lateral Movement","Collection","Command and Control","Exfiltration","Impact"]
for (const tactic of Tactics) {
	renderTacticChart(tactic, tacticStats[tactic], `#results${tactic.toLowerCase().split(' ').join('')}`);
}