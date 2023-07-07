// Delay table showing until page is loaded to prevent jumping
$(function () {
	$('#assessmentTable').show()
})

var row = null
var rowData = null

$('#newTestcase').click(function() {
	$("#newTestcaseForm").trigger('reset')
	$('#newTestcaseModal').modal('show')
});

function formatRow(response) {
	return {
		add: response.add,
		id: response.id,
		mitreid: response.mitreid,
		name: response.name,
		tactic: response.tactic,
		state: `${response.state} - ${response.visible}`,
		tags: response.tags.join(","),
		start: "-",
		modified: "",
		preventscore: "",
		detectscore: "",
		outcome: "",
		actions: "",
	}
}

$("#newTestcaseForm").submit(function(e){
	e.preventDefault();

	fetch(e.target.action, {
		method: 'POST',
		body: new URLSearchParams(new FormData(e.target))
	}).then((response) => {
		return response.json();
	}).then((body) => {
		$('#assessmentTable').bootstrapTable('append', [formatRow(body)])
		$('#newTestcaseModal').modal('hide')
	})
});

$('#testcaseTemplatesButton').click(function() {
	console.log("test")
	$.ajax({
		url: `/testcase/import/template`,
		type: 'POST',
		
		data: JSON.stringify({
			ids: $('#testcaseTemplateTable').bootstrapTable('getSelections').map(row => row.id)
		}),
		dataType: 'json',
		contentType: "application/json; charset=utf-8",
		success: function(result) {
			result.forEach(result => {
				$('#assessmentTable').bootstrapTable('append', [formatRow(result)])
			})
			$('#testcaseTemplatesModal').modal('hide')
		}
	});
});

$("#navigatorTemplateForm").submit(function(e){
	e.preventDefault();

	fetch(e.target.action, {
		method: 'POST',
		body: new FormData(e.target)
	}).then((response) => {
		return response.json();
	}).then((body) => {
		body.forEach(result => {
			$('#assessmentTable').bootstrapTable('append', [formatRow(result)])
		})
		$('#testcaseNavigatorModal').modal('hide')
	})
});

$("#campaignTemplateForm").submit(function(e){
	e.preventDefault();

	fetch(e.target.action, {
		method: 'POST',
		body: new FormData(e.target)
	}).then((response) => {
		return response.json();
	}).then((body) => {
		body.forEach(result => {
			$('#assessmentTable').bootstrapTable('append', [formatRow(result)])
		})
		$('#testcaseCampaignModal').modal('hide')
	})
});

function visibleTest(event) {
	event.stopPropagation();
	row = $(event.target).closest("tr")
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$.ajax({
		url: `/testcase/toggle-visibility/${rowData.id}`,
		type: 'GET',
		success: function(body) {
			$('#assessmentTable').bootstrapTable('updateRow', {
				index: row.data("index"),
				row: formatRow(body),
				replace: true
			})
		}
	});
};

function cloneTest(event) {
	event.stopPropagation();
	row = $(event.target).closest("tr")
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$.ajax({
		url: `/testcase/clone/${rowData.id}`,
		type: 'GET',
		success: function(body) {
			$('#assessmentTable').bootstrapTable('insertRow', {
				index: row.data("index") + 1,
				row: formatRow(body)
			})
		}
	});
};

function deleteTest(event) {
	event.stopPropagation();
	row = $(event.target).closest("tr")
	console.log(row)
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$.ajax({
		url: `/testcase/delete/${rowData.id}`,
		type: 'GET',
		success: function(body) {
			$('#assessmentTable').bootstrapTable('removeByUniqueId', rowData.id)
		}
	});
};

// function editAssessmentModal(e) {
// 	// Globally store the clicked row for AJAX operations
// 	row = $(e).closest("tr")
// 	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
// 	$("#newAssessmentForm").trigger('reset')
// 	$('#newAssessmentForm').attr('action', `/assessment/${rowData.id}`) 
// 	$('#newAssessmentLabel').text("Edit Assessment")
// 	$('#newAssessmentButton').text("Update")
// 	$('#newAssessmentForm #name').val(rowData.name)
// 	$('#newAssessmentForm #description').val(rowData.description)
// 	$('#newAssessmentModal').modal('show')
// }

// function deleteAssessmentModal(e) {
// 	// Globally store the clicked row for AJAX operations
// 	row = $(e).closest("tr")
// 	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
// 	$('#deleteAssessmentForm').attr('action', `/assessment/${rowData.id}`) 
// 	// TODO XSS
// 	$('#deleteAssessmentWarning').html(`Really Delete <code>${rowData.name}</code>?`)
// 	$('#deleteAssessmentModal').modal('show')
// }

// // Hook the native new/edit assessment HTML form to catch and action the response
// $("#newAssessmentForm").submit(function(e){
// 	e.preventDefault();

// 	fetch(e.target.action, {
// 		method: 'POST',
// 		body: new URLSearchParams(new FormData(e.target))
// 	}).then((response) => {
// 		return response.json();
// 	}).then((body) => {
// 		newRow = {
// 			id: body.id,
// 			name: body.name,
// 			description: body.description,
// 			progress: body.progress,
// 			actions: ""
// 		}
		
// 		// This function is shared between new and edit assessment, so do we
// 		// need to edit a row or create a new one?
// 		if ($('#assessmentTable').bootstrapTable('getRowByUniqueId', body.id)) {
// 			$('#assessmentTable').bootstrapTable('updateRow', {
// 				index: row.data("index"),
// 				row: newRow,
// 				replace: true
// 			})
// 		} else {
// 			$('#assessmentTable').bootstrapTable('append', [newRow])
// 		}

// 		$('#newAssessmentModal').modal('hide')
// 	})
// });

// // AJAX DELETE assessment call
// $('#deleteAssessmentButton').click(function() {
// 	$.ajax({
// 		url: `/assessment/${rowData.id}`,
// 		type: 'DELETE',
// 		success: function(result) {
// 			$('#assessmentTable').bootstrapTable('removeByUniqueId', rowData.id)
// 			$('#deleteAssessmentModal').modal('hide')
// 		}
// 	});
// });

function nameFormatter(name, row) {
	return `<a href="/testcase/${row.id}">${name}</a>`
}

function tagFormatter(tags) {
	html = ""
	tags.split(",").forEach(tag => {
		html += `<span class='badge rounded-pill' style="background:#ff0000; cursor:pointer" onclick="filterTag(this)">${tag}</span>`
	})
	return html
}

function actionFormatter() {
	return `
		<div class="btn-group btn-group-sm" role="group">
			<button type="button" class="btn btn-info py-0" onclick="visibleTest(event)" title="Toggle Visiblity">
				<i class="bi-eye">&zwnj;</i>
			</button>
			<button type="button" class="btn btn-warning py-0" onclick="cloneTest(event)" title="Clone">
				<i class="bi-files">&zwnj;</i>
			</button>
			<button type="button" class="btn btn-danger py-0" onclick="deleteTest(event)" title="Delete">
				<i class="bi-trash-fill">&zwnj;</i>
			</button>
		</div>
	`
}





































// selectedIds = []

// function deleteTest(e, ids) {
// 	if (e.target.tagName != "A") e.stopPropagation();
// 	$("#table").bootstrapTable('uncheckAll')
// 	ids.forEach(id => $("#table").bootstrapTable('remove', {field: "id", values: [id]}));
// 	$.get("/testcase/delete?ids=" + ids.join(), function (data, status) {
// 		if (status == "success") {
// 			new bootstrap.Toast(document.querySelector('#deleteToast')).show();
// 		}
// 	});
// }

// function cloneTest (e, id, name, description) {
// 	e.stopPropagation();
// 	new bootstrap.Toast(document.querySelector('#cloningToast')).show();
// 	$.get("/testcase/clone/" + id, function (data, status) {
// 	if (status == "success") {

// 		orig = $("#table").bootstrapTable('getData').find(row => row.id == "#ID#")
// 		idx = $("#table").bootstrapTable('getData').findIndex(row => row.id == id)
// 		clone = JSON.stringify(orig).replaceAll("#ID#", data.id)
// 		clone = clone.replaceAll("#NAME#", data.name)
// 		clone = clone.replaceAll("#TACTIC#", data.tactic)
// 		clone = clone.replaceAll("#MITREID#", data.mitreid)
// 		$("#table").bootstrapTable('insertRow', {index: idx + 1, row: JSON.parse(clone)})
// 		new bootstrap.Toast(document.querySelector('#cloneToast')).show();
// 	}
// 	});
	
// }

// function newTest (multi) {
// 	if (multi) {
// 		dat = {ids: $("#template-table").bootstrapTable('getSelections').map(i => i.id)}
// 	}
// 	else {
// 		name = $('#name').val()
// 		mitreid = $('#mitreid').val()
// 		tactic = $('#tactic').val()
// 		dat = {name: name, mitreid: mitreid, tactic: tactic}
// 	}
// 	$.post("/testcase/add", dat, function (data, status) {
// 	if (status == "success") {
// 		data.forEach(test => {
// 			orig = $("#table").bootstrapTable('getData').find(row => row.id == "#ID#")
// 			clone = JSON.stringify(orig).replaceAll("#ID#", test.id)
// 			clone = clone.replaceAll("#NAME#", test.name)
// 			clone = clone.replaceAll("#TACTIC#", test.tactic)
// 			clone = clone.replaceAll("#MITREID#", test.mitreid)
// 			$("#table").bootstrapTable('insertRow', {index: 0, row: JSON.parse(clone)})
// 		});     
// 	}
// 	});
// 	$('#newtestcase').modal('hide')
// 	$('#templatesModal').modal('hide')
// 	$("#template-table").bootstrapTable('uncheckAll')
// }

// function resetTest (e, id) {
// 	e.stopPropagation();
// 	$.get("/testcase/reset/" + id, function (data, status) {
// 	if (status == "success") {

// 		orig = $("#table").bootstrapTable('getData').find(row => row.id == "#ID#")
// 		idx = $("#table").bootstrapTable('getData').findIndex(row => row.id == id)
// 		clone = JSON.stringify(orig).replaceAll("#ID#", data.id)
// 		clone = clone.replaceAll("#NAME#", data.name)
// 		clone = clone.replaceAll("#TACTIC#", data.tactic)
// 		clone = clone.replaceAll("#MITREID#", data.mitreid)
// 		$("#table").bootstrapTable('remove', {field: "id", values: [id]})
// 		$("#table").bootstrapTable('insertRow', {index: idx, row: JSON.parse(clone)})
// 		new bootstrap.Toast(document.querySelector('#resetToast')).show();
// 	}
// 	});
// }

// function visibleTest (e, ids) {
// 	if (e.target.tagName != "A") e.stopPropagation();
// 	$.get("/testcase/visible?ids=" + ids.join(), function (data, status) {
// 		if (status == "success") {
// 			ids.forEach((id) => {
// 				idx = $("#table").bootstrapTable('getData').findIndex(row => row.id == id)
// 				oldState = $("#table").bootstrapTable('getData')[idx]["state"]
// 				if (oldState.includes("Hidden")) {
// 					$("#table").bootstrapTable('updateCell', {index: idx, field: 'state', value: oldState.replace(" (Hidden)", "")})
// 				}
// 				else {
// 					$("#table").bootstrapTable('updateCell', {index: idx, field: 'state', value: oldState + " (Hidden)"})
// 				}
// 			})
// 		}
// 	});
// }

// function testcaseFormatter(i, row) {
// 	// var html = []
// 	// $.each(row, function (key, value) {
// 	//     html.push('<p><b>' + key + ':</b> ' + value + '</p>')
// 	// })
// 	// return html.join('')
// 	return "<p>Are there any testcase details that are useful to store in the fold to save you from opening a testcase just to peek at one detail? Keep in mind it may be better suited for tags e.g 'No Red Files' or a column e.g 'Start Date'. I'm keeping this PoC here if we /do/ think of something to put here.</p>"
// }

// $(window).on('load', function() {
// 	$('#table').bootstrapTable()
// 	idx = $("#table").bootstrapTable('getData').findIndex(row => row.id == "#ID#")
// 	$('#table').bootstrapTable('hideRow', {index:idx})
// 	$('#table').show()
// 	$('#template-table').bootstrapTable()

// 	$('#template-table').on( 'check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table', function (e) {
// 		count = $('#template-table').bootstrapTable('getSelections').length
// 		$('#add-templates').text(`Add ${count} Testcase(s)`)
// 		if (count == 0) {
// 			$('#add-templates').hide()
// 		}
// 		else {
// 			$('#add-templates').show()
// 		}
// 	} );
// 	$('#table').on( 'check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table', function (e) {
// 		selectedIds = $("#table").bootstrapTable('getSelections').map(i => i.id)
// 		if (selectedIds.length > 0) {
// 			$("#selected-dropdown").show()
// 			id = $("#selected-json").data('id')
// 			ids = selectedIds.join(",")
// 			$("#selected-csv").attr('href', `/assessment/export/csv/${id}?ids=${ids}`)
// 			$("#selected-json").attr('href', `/assessment/export/json/${id}?ids=${ids}`)
// 			$("#selected-template").attr('href', `/assessment/export/template/${id}?ids=${ids}`)
// 			$("#selected-atomics").attr('href', `/assessment/export/atomics/${id}?ids=${ids}`)

// 			$("#bulk-dropdown").show()
			
// 			$("#selected-count").show()
// 			$("#selected-count").text("(" + selectedIds.length + " selected)")

// 		}
// 		else {
// 			$("#selected-dropdown").hide()
// 			$("#bulk-dropdown").hide()
// 			$("#selected-count").hide()
// 		}
// 	} );

// 	// MITRE HEXS
// 	// Grab the SVG document
// 	var svgDoc = document.getElementById("mitre-hexs").contentDocument;

// 	// Order to display hexagons in
// 	tactics = ["Execution", "Command and Control", "Discovery", "Persistence", "Privilege Escalation", "Credential Access", "Lateral Movement", "Exfiltration", "Impact"]
// 	hex = 1

// 	// Initalise all hexagons as blank
// 	for (const x of Array(9).keys()) {
// 		svgDoc.querySelectorAll('.hex-' + (x+1)).forEach(j => j.style.display = "none");
// 	}

// 	// For each tactic we have data for
// 	tactics.forEach(tactic => {
// 		if (Object.keys(tacticStats).includes(tactic)) {
// 			// Calculate the score
// 			total = tacticStats[tactic].blocked + tacticStats[tactic].alerted - tacticStats[tactic].missed
// 			if (total > 1) color = "#B8DF43"
// 			else if (total < -1) color = "#FB6B64"
// 			else color = "#FFC000"

// 			// Update the hexagon text and colours
// 			svgDoc.querySelectorAll('.hex-' + hex).forEach(j => j.style.display = "block");
// 			svgDoc.getElementById(`hex-${hex}-stroke`).style.stroke = color
// 			svgDoc.getElementById(`hex-${hex}-stroke`).style.fill = "#eeeeee"
// 			svgDoc.getElementById(`hex-${hex}-label`).innerText = tactic
// 			hex += 1
// 		}
// 	})

// 	// Hexagon starts hidden, once populate, show to user
// 	document.getElementById("mitre-hexs").style.opacity = 1
// });



// function detailFormatter(index, row) {
// 	return row["html"]
// }

// // Badge filtering

// function filterBadge(event, e) {
// 	event.stopPropagation()
// 	$('.bootstrap-table-filter-control-name').val(e.innerText)
// 	$('#table').bootstrapTable('triggerSearch')
// } 
// function filterTag(event, e) {
// 	event.stopPropagation()
// 	$('.bootstrap-table-filter-control-tags').val(e.innerText)
// 	$('#table').bootstrapTable('triggerSearch')
// }   


