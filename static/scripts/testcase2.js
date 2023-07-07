$('#sourceNewButton').click(function() {
	$("#sourceTable").bootstrapTable("append", [{id: `tmp-${Date.now()}`, name: "a", description: "a", delete: ""}])
})

function deleteMultiRow(event) {
	console.log(event.target)
	tableId = $(event.target).closest("table")[0].id
	console.log(tableId)
	console.log($(event.target).closest("tr").data("uniqueid"))
	$(`#${tableId}`).bootstrapTable(
		"removeByUniqueId",
		$(event.target).closest("tr").data("uniqueid")
	)
}

function nameFormatter(val) {
	return `<input type="text" name="name" value="${val}"/>`
}

function descriptionFormatter(val) {
	return `<input type="text" name="name" value="${val}"/>`
}

function deleteFormatter() {
	return `
		<button type="button" class="btn btn-danger py-0" onclick="deleteMultiRow(event)" title="Delete">
			<i class="bi-trash-fill">&zwnj;</i>
		</button>
	`
}