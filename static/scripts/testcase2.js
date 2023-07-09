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

			// Selectpicker plugin doesn't support populating a dropdown with
			// values and names seperately so we need to populate the HTML
			// manually and force it to refresh
			selectedIDs = $(`#${type}`).val()
			$(".dynopt-" + type).remove();
			result.forEach(function(i) {
				selected = selectedIDs.includes(i.id) ? "selected" : ""
				pill = type == "tags" ? `data-content="<span class='badge rounded-pill' style='background:${i.colour}'>${i.name}</span>"` : ""
				$(`#${type}`).append(`<option ${selected} class="dynopt-${type}" value="${i.id}" ${pill}>${i.name}</option>`);
			})
			$(`#${type}`).selectpicker('refresh');
		}
	});
})

// If "manage" is selected in a multi dropdown, remove the selection and pop manage modal
$('.selectpicker').change(function(event) {
	type = event.target.id
	if ($(`#${type}`).val().includes("Manage")) {
		$(event.target).selectpicker('val', $(`#${type}`).val().filter(item => item !== "Manage"))
		$(event.target).selectpicker('toggle');
		$(`#multi${type[0].toUpperCase() + type.slice(1, -1)}Modal`).modal('show')
	}
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

// Multi modal formatters
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

// Dynamic <textarea> height (no native HTML/CSS way :( )
$('#objective, #actions, #rednotes, #bluenotes').on('input', function(event) {
	event.target.style.height = 0;
	event.target.style.height = event.target.scrollHeight + 5 + 'px';
}).trigger('input')