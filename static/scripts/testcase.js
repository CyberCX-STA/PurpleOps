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
		url: `${$("#assessment-crumb-button").attr("href")}/multi/${type}`,
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
			selectedIDs = $(`#${type}`).val() || []
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
	if (($(`#${type}`).val() || []).includes("Manage")) {
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
	$(`#${tableId}`).bootstrapTable("removeByUniqueId", $(event.target).closest("tr").data("uniqueid"))
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

// Dynamically update prevent fields
$('input[name="prevented"]').on('change', function() {
	current = $('input[name="prevented"]:checked').val()
	if (["No", "N/A", ""].includes(current)) {
		$("#preventedrating").val(current.replace("No", "0.0"))
		$("#preventedrating-container").hide()
	} else {
		if (["0.0", "N/A"].includes($("#preventedrating").val())) {
			$("#preventedrating").val("")
		}
		$("#preventedrating-container").show()
	}
}).trigger('change')

// Dynamically update priority fields
$('input[name="priority"]').on('change', function() {
	current = $('input[name="priority"]:checked').val()
	if (["N/A"].includes(current)) {
		$("#priorityurgency").val("N/A")
		$("#urgency-container").hide()
	} else {
		if ($("#priorityurgency").val() == "N/A") {
			$("#priorityurgency").val("")
		}
		$("#urgency-container").show()
	}
}).trigger('change')

// Dynamically update alerted fields
$('input[name="alerted"]').on('change', function() {
	current = $('input[name="alerted"]:checked').val()
	if (current == "Yes") {
		$("#alert-container").show()
		$("#detection-container").show()
		$("#logged-container").hide()
		$('input[name="logged"]').prop('checked', false)
		$('#log-yes').prop("checked", true)
		if ($('#detectionrating').val() == "0.0") {
			$('#detectionrating').val("")
		}
	} else if (current == "No") {
		$("#alert-container").hide()
		$("#alertseverity").val("")
		$("#logged-container").show()
		$("#detection-container").hide()
	} else {
		$("#alert-container").hide()
		$("#logged-container").hide()
		$("#detection-container").hide()
	}
}).trigger('change')

// Dynamically update logged fields
$('input[name="logged"]').on('change', function() {
	current = $('input[name="logged"]:checked').val()
	if (current == "Yes") {
		$('#detection-container').show()
	} else if (current == "No") {
		$('#detectionrating').val("0.0")
		$('#detection-container').hide()
	}
}).trigger('change')

// Add accessible move controls to existing evidence and keep persisted order values in sync.
function syncEvidenceOrder(colour) {
	const list = $(`#evidence-${colour}`)
	list.children(".evidence-item").each(function(index, element) {
		const item = $(element)
		const hidden = item.find(".evidence-order-input")
		hidden.attr("name", `${colour}files_order`).val(item.attr("data-filename"))
	})
}

function initializeEvidenceOrder() {
	["red", "blue"].forEach(colour => {
		const list = $(`#evidence-${colour}`)
		list.children("li").not(":has(input[type=file])").each(function() {
			const item = $(this)
			if (item.hasClass("evidence-item")) return
			const download = item.find('a[href*="?download=true"]').first()
			if (!download.length) return
			const filename = decodeURIComponent(download.attr("href").split("/evidence/").pop().split("?")[0])
			item.addClass(`evidence-item evidence-${colour}`).attr("data-filename", filename)
			const controls = $(`<div class="btn-group btn-group-sm me-2" role="group">
				<button type="button" class="btn btn-outline-secondary evidence-move-up" title="Move earlier" aria-label="Move evidence earlier"><i class="bi-arrow-up">&zwnj;</i></button>
				<button type="button" class="btn btn-outline-secondary evidence-move-down" title="Move later" aria-label="Move evidence later"><i class="bi-arrow-down">&zwnj;</i></button>
			</div>`)
			item.prepend(controls)
			item.append(`<input type="hidden" class="evidence-order-input" name="${colour}files_order" value="${filename}">`)
		})
		syncEvidenceOrder(colour)
	})
}

$(document).on("click", ".evidence-move-up", function(event) {
	const item = $(event.currentTarget).closest(".evidence-item")
	const previous = item.prevAll(".evidence-item").first()
	if (previous.length) previous.before(item)
	syncEvidenceOrder(item.hasClass("evidence-red") ? "red" : "blue")
})

$(document).on("click", ".evidence-move-down", function(event) {
	const item = $(event.currentTarget).closest(".evidence-item")
	const next = item.nextAll(".evidence-item").first()
	if (next.length) next.after(item)
	syncEvidenceOrder(item.hasClass("evidence-red") ? "red" : "blue")
})

// AJAX submit and pop toast on save success
$("#ttpform").submit(function(e){
	e.preventDefault();
	["red", "blue"].forEach(syncEvidenceOrder)
	const form = new FormData(e.target)
	fetch(e.target.action, {
		method: 'POST',
		body: form
	}).then(response => {
		if (response.status == 200) {
			displayNewEvidence(form)
			new bootstrap.Toast(document.querySelector('#toast')).show();
		} else {
			alert("Testcase save error - contact admin to review log")
		}
	})
});

// Convert UTC DB time to local time
$(document).ready(function() {
	offset = new Date().getTimezoneOffset()
	$("#timezone").val(offset)

	if ($("#time-start").val()) {
		startTime = new Date($("#time-start").val());
		startTime.setMinutes(startTime.getMinutes() - offset * 2);
		$("#time-start").val(startTime.toISOString().slice(0,16))
	}

	if ($("#time-end").val()) {
		endTime = new Date($("#time-end").val());
		endTime.setMinutes(endTime.getMinutes() - offset * 2);
		$("#time-end").val(endTime.toISOString().slice(0,16))
	}
	initializeEvidenceOrder()
});

// Alter timestamps, button labels and state when hitting run button
$("#run-button").click(function(){
	clickTime = new Date();
	clickTime.setMinutes(clickTime.getMinutes() - clickTime.getTimezoneOffset());
	clickTime = clickTime.toISOString().slice(0, 16)

	if (["Start", "Restart"].includes($("#run-button").text())) {
		$("#time-start").val(clickTime)
		$("#time-end").val("")
		$("#run-button").text("Stop").removeClass("btn-outline-success btn-outline-warning").addClass("btn-outline-danger")
		$("#state").val("Running").addClass("bg-warning text-dark").removeClass("bg-primary text-white")
	} else if ($("#run-button").text() == "Stop") {
		$("#time-end").val(clickTime)
		$("#run-button").text("Restart").removeClass("btn-outline-danger").addClass("btn-outline-warning")
		$("#state").val("Complete").removeClass("bg-warning text-dark").addClass("bg-primary text-white")
	}
});

// Delete evidence by requesting its URL and then remove its list item.
$(document).on("click", ".evidence-delete", function(event) {
	const button = $(event.currentTarget)
	const item = button.closest(".evidence-item")
	const colour = item.hasClass("evidence-red") ? "red" : "blue"
	const evidenceUrl = item.find('a[href*="/evidence/"]').first().attr("href").split("?")[0]
	const filename = item.attr("data-filename")
	const deleteUrl = evidenceUrl.replace("/evidence/", `/evidence/${colour}/`)

	$.ajax({
		url: deleteUrl,
		type: 'DELETE',
		success: function() {
			item.remove()
			syncEvidenceOrder(colour)
		}
	});
});

// Add uploaded evidence to the page after the save succeeds.
function displayNewEvidence(form) {
	["red", "blue"].forEach(colour => {
		form.getAll(`${colour}files`).forEach(file => {
			if (!file.name) return
			const filename = file.name.split(/[\\/]/).pop()
			const safeFilename = santiseFilename(filename)
			const testcaseId = window.location.pathname.split("/").pop()
			const item = $(`<li class="list-group-item evidence-item evidence-${colour}" data-filename="${filename}">
				<div class="btn-group btn-group-sm me-2" role="group">
					<button type="button" class="btn btn-outline-secondary evidence-move-up" title="Move earlier" aria-label="Move evidence earlier"><i class="bi-arrow-up">&zwnj;</i></button>
					<button type="button" class="btn btn-outline-secondary evidence-move-down" title="Move later" aria-label="Move evidence later"><i class="bi-arrow-down">&zwnj;</i></button>
				</div>
				<button type="button" class="btn btn-outline-danger btn-sm me-2 evidence-delete" title="Delete"><i class="bi-trash small">&zwnj;</i></button>
				<a href="/testcase/${testcaseId}/evidence/${encodeURIComponent(filename)}?download=true" class="btn btn-outline-primary btn-sm me-2"><i class="bi-download small">&zwnj;</i></a>
				<span class="name small">${$('<span>').text(filename).html()}</span>
				<input type="hidden" class="evidence-order-input" name="${colour}files_order" value="${$('<span>').text(filename).html()}">
			</li>`)
			if (/\.(png|jpe?g)$/i.test(filename)) {
				item.find(".name").replaceWith(`<a href="/testcase/${testcaseId}/evidence/${encodeURIComponent(filename)}" target="_blank"><img class="img-fluid img-thumbnail" style="max-width: 80%" src="/testcase/${testcaseId}/evidence/${encodeURIComponent(filename)}"/></a><input style="margin-left: 6em; width:80%;" class="form-control form-control-sm" type="text" placeholder="Caption..." value="" id="${colour.toUpperCase()}${safeFilename}" name="${colour.toUpperCase()}${safeFilename}"/>`)
			}
			$(`#evidence-${colour}`).append(item)
			$(`#${colour}files`).val("")
		})
		syncEvidenceOrder(colour)
	})
}

function santiseFilename(filename) {
    return filename
        .split('/').pop().split('\\').pop()  // Remove paths
        .normalize('NFKD').replace(/[\u0300-\u036f]/g, '')  // ASCII
        .replace(/[^\w.-]/g, '_')  // Replace unsafe chars
        .replace(/^[._-]+|[._-]+$/g, '') || 'unnamed';  // Clean edges
}
