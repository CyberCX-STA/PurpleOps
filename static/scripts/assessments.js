// Delay table showing until page is loaded to prevent jumping
$(function () {
  $('#assessmentsTable').show()
})

var row = null
var rowData = null

$('#newAssessment').click(function() {
	$("#newAssessmentForm").trigger('reset')
    $('#newAssessmentForm').attr('action', '/assessment') 
	$('#newAssessmentLabel').text("New Assessment")
	$('#newAssessmentButton').text("Create")
    $('#newAssessmentModal').modal('show')
});

function editAssessmentModal(e) {
	// Globally store the clicked row for AJAX operations
	row = $(e).closest("tr")
	rowData = $('#assessmentsTable').bootstrapTable('getData')[row.data("index")]
	$("#newAssessmentForm").trigger('reset')
    $('#newAssessmentForm').attr('action', `/assessment/${rowData.id}`) 
	$('#newAssessmentLabel').text("Edit Assessment")
	$('#newAssessmentButton').text("Update")
    $('#newAssessmentForm #name').val(rowData.name)
	$('#newAssessmentForm #description').val(rowData.description)
    $('#newAssessmentModal').modal('show')
}

function deleteAssessmentModal(e) {
	// Globally store the clicked row for AJAX operations
	row = $(e).closest("tr")
	rowData = $('#assessmentsTable').bootstrapTable('getData')[row.data("index")]
	$('#deleteAssessmentForm').attr('action', `/assessment/${rowData.id}`) 
    // TODO XSS
	$('#deleteAssessmentWarning').html(`Really Delete <code>${rowData.name}</code>?`)
	$('#deleteAssessmentModal').modal('show')
}

// Hook the native new/edit assessment HTML form to catch and action the response
$("#newAssessmentForm").submit(function(e){
	e.preventDefault();

    fetch(e.target.action, {
        method: 'POST',
        body: new URLSearchParams(new FormData(e.target))
    }).then((response) => {
        return response.json();
    }).then((body) => {
		newRow = {
			id: body.id,
			name: body.name,
			description: body.description,
			progress: body.progress,
            actions: ""
		}
        
		// This function is shared between new and edit assessment, so do we
		// need to edit a row or create a new one?
		if ($('#assessmentsTable').bootstrapTable('getRowByUniqueId', body.id)) {
			$('#assessmentsTable').bootstrapTable('updateRow', {
				index: row.data("index"),
				row: newRow,
				replace: true
			})
		} else {
			$('#assessmentsTable').bootstrapTable('append', [newRow])
		}

		$('#newAssessmentModal').modal('hide')
		$('#newAssessmentForm').trigger('reset')
    })
});

// Submit entire testcase and AJAX add new row
$("#importAssessmentForm").submit(function(e){
	e.preventDefault();

    fetch(e.target.action, {
        method: 'POST',
        body: new FormData(e.target)
    }).then((response) => {
        return response.json();
    }).then((body) => {
		newRow = {
			id: body.id,
			name: body.name,
			description: body.description,
			progress: body.progress,
            actions: ""
		}
		$('#assessmentsTable').bootstrapTable('append', [newRow])
		$('#importAssessmentModal').modal('hide')
		$('#importAssessmentForm').trigger('reset')
    })
});

// AJAX DELETE assessment call
$('#deleteAssessmentButton').click(function() {
	$.ajax({
		url: `/assessment/${rowData.id}`,
		type: 'DELETE',
		success: function(result) {
			$('#assessmentsTable').bootstrapTable('removeByUniqueId', rowData.id)
			$('#deleteAssessmentModal').modal('hide')
		}
	});
});

function nameFormatter(name, row) {
	return `<a href="/assessment/${row.id}">${name}</a>`
}

function progressFormatter(progress) {
	return `
		<div class="progress">
			<div class="progress-bar bg-danger" role="progressbar" style="width: ${progress.split('|')[0]}%"></div>
			<div class="progress-bar bg-warning" role="progressbar" style="width: ${progress.split('|')[1]}%"></div>
			<div class="progress-bar bg-success" role="progressbar" style="width: ${progress.split('|')[2]}%"></div>
			<div class="progress-bar bg-info" role="progressbar" style="width: ${progress.split('|')[3]}%"></div>
		</div>
	`
}

function actionFormatter() {
	return `
		<div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-primary py-0" title="Edit" onclick="editAssessmentModal(this)">
                <i class="bi-pencil">&zwnj;</i>
            </button>
            <button type="button" class="btn btn-danger py-0" title="Delete" onclick="deleteAssessmentModal(this)">
                <i class="bi-trash-fill">&zwnj;</i>
            </button>
		</div>
	`
}

// TODO import assessment form
// TODO assessment clone