// When the new source/target etc. button is clicked, add a new row
$('.multiNew').click(function(event) {
	type = event.target.id.replace("NewButton", "") // Hacky
	newRow = {
		id: `tmp-${Date.now()}`, // Rows need unique IDs, so give it the time
		name: "",
		delete: ""
	}
	type == "tags" ? newRow.colour = "" : newRow.description = ""
	$(`#${type}Table`).bootstrapTable("append", [newRow])
})

// When the source/target etc. table/modal is saved, post updates and refresh table
$('.multiButton').click(function(event) {
	type = event.target.id.replace("multi", "").replace("Button", "").toLowerCase() + "s" // Hacky
	$.ajax({
		url: `/assessment/multi/${type}`,
		type: 'POST',
		
		data: JSON.stringify({
			data: $(`#${type}Table`).bootstrapTable("getData")
		}),
		dataType: 'json',
		contentType: "application/json; charset=utf-8",
		success: function(result) {
			// The model doesn't have a delete field but the table requires it
			result.map(row => row.delete = "")
			$(`#${type}Table`).bootstrapTable("load", result)
			$(event.target).closest(".modal").modal("hide")
		}
	});
})

// When source/target etc. names/descriptions are changed, update table value ready for POST
$('.multiTable').on('change', '.multi', function(event) {
	$(event.delegateTarget).bootstrapTable("updateCellByUniqueId", {
		id: $(event.target).closest("tr").data("uniqueid"),
		field: event.target.name,
		value: event.target.value
	})
});

// When a source/target etc. is deleted, nuke the row from the table
function deleteMultiRow(event) {
	tableId = $(event.target).closest("table")[0].id
	$(`#${tableId}`).bootstrapTable(
		"removeByUniqueId",
		$(event.target).closest("tr").data("uniqueid")
	)
}

function nameFormatter(val) {
	return `<input type="text" name="name" value="${val}" class="multi" placeholder="Name..."/>`
}

function descriptionFormatter(val) {
	return `<input type="text" name="description" value="${val}" class="multi" placeholder="Description..."/>`
}

function colourFormatter(val) {
	return `<input type="color" name="colour" value="${val}" class="multi"/>`
}

function deleteFormatter() {
	return `
		<button type="button" class="btn btn-danger py-0" onclick="deleteMultiRow(event)" title="Delete">
			<i class="bi-trash-fill">&zwnj;</i>
		</button>
	`
}