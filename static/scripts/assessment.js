// Delay table showing until page is loaded to prevent jumping
$(function () {
	$('#assessmentTable').show()
})

var row = null
var rowData = null

// Pop modal when adding a new raw testcase and clear old data
$('#newTestcase').click(function() {
	$("#newTestcaseForm").trigger('reset')
	$('#newTestcaseModal').modal('show')
});

// Wrapper for formatting server responses into table rows
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

// AJAX new testcase POST and table append
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

// AJAX new testcase from template POST and table append
$('#testcaseTemplatesButton').click(function() {
	$.ajax({
		url: `/assessment/import/template`,
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

// AJAX new testcases from template POST and table append
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

// AJAX new testcases from assessment template POST and table append
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

// Toggle visibility of testcase AJAX
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

// Testcase clone AJAX POST and row update
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

// Testcase delete AJAX POST and remove from table
function deleteTest(event) {
	event.stopPropagation();
	row = $(event.target).closest("tr")
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$.ajax({
		url: `/testcase/delete/${rowData.id}`,
		type: 'GET',
		success: function(body) {
			$('#assessmentTable').bootstrapTable('removeByUniqueId', rowData.id)
		}
	});
};

// Table formatters
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