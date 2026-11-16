// Delete evidence AJAX handler
$(document).on("click", ".evidence-delete", function(event) {
	target = event.target.tagName == "I" ? event.target.parentNode : event.target
	colour = $(target).attr("class").includes("evidence-red") ? "red" : "blue"
	url = $(target).next("a").attr("href").split("?")[0]
	url = url.replace("/evidence/", `/evidence/${colour}/`)

	$.ajax({
		url: url,
		type: 'DELETE',
		success: function(result) {
			$(target).parent().remove()
			syncEvidenceOrder(colour)
		}
	});
});

$(document).on("click", ".evidence-move-up", function(event) {
	const item = $(event.currentTarget).closest(".evidence-item")
	const list = item.parent()
	const siblings = list.children(".evidence-item")
	const index = siblings.index(item)
	if (index <= 0) {
		return
	}
	const previous = siblings.eq(index - 1)
	previous.before(item)
	syncEvidenceOrder(item.hasClass("evidence-red") ? "red" : "blue")
})

$(document).on("click", ".evidence-move-down", function(event) {
	const item = $(event.currentTarget).closest(".evidence-item")
	const list = item.parent()
	const siblings = list.children(".evidence-item")
	const index = siblings.index(item)
	if (index >= siblings.length - 1) {
		return
	}
	const next = siblings.eq(index + 1)
	next.after(item)
	syncEvidenceOrder(item.hasClass("evidence-red") ? "red" : "blue")
})

function syncEvidenceOrder(colour) {
	const list = $(`#evidence-${colour}`)
	list.children(".evidence-item").each(function(index, element) {
		const fileName = $(element).data("filename") || $(element).find(".evidence-order-input").val()
		if (!fileName) {
			return
		}
		let hidden = $(element).find(".evidence-order-input")
		if (!hidden.length) {
			hidden = $("<input type='hidden' class='evidence-order-input' value=''>")
			$(element).append(hidden)
		}
		hidden.attr("name", `${colour}files_order`)
		hidden.val(fileName)
		$(element).data("filename", fileName)
	})
}

// AJAX inject new evidence HTML on testcase save
function displayNewEvidence(form) {
	["red", "blue"].forEach(colour => {
		form.getAll(`${colour}files`).forEach(file => {
			if (file.name == "") {
				return
			}
			const cleanedFilename = santiseFilename(file.name);
			testcaseId = window.location.pathname.split("/").slice(-1)[0]
			html = `
				<li class="list-group-item evidence-item evidence-${colour}" data-filename="${file.name}">
					<div class="d-flex align-items-center gap-2">
						<div class="btn-group btn-group-sm" role="group">
							<button type="button" class="btn btn-outline-secondary evidence-move evidence-move-up evidence-${colour}" title="Move earlier">
								<i class="bi-arrow-up small">&zwnj;</i>
							</button>
							<button type="button" class="btn btn-outline-secondary evidence-move evidence-move-down evidence-${colour}" title="Move later">
								<i class="bi-arrow-down small">&zwnj;</i>
							</button>
						</div>
						<button type="button" class="btn btn-outline-danger btn-sm evidence-delete evidence-${colour}">
							<i class="bi-trash small">&zwnj;</i>
						</button>
						<a href="/testcase/${testcaseId}/evidence/${file.name}?download=true" class="btn btn-outline-primary btn-sm">
							<i class="bi-download small">&zwnj;</i>
						</a>
					</div>`
			if (file.name.toLowerCase().endsWith(".png") || 
				file.name.toLowerCase().endsWith(".jpg") ||
				file.name.toLowerCase().endsWith(".jpeg")) {
				html += `
						<a href="/testcase/${testcaseId}/evidence/${file.name}" target="_blank">
							<img class="img-fluid img-thumbnail" style="max-width: 80%" src="/testcase/${testcaseId}/evidence/${file.name}"/>
						</a>
						<input style="margin-left: 6em; width:80%;" class="form-control form-control-sm" type="text" placeholder="Caption..." value="" id="${colour.toUpperCase()}${cleanedFilename}" name="${colour.toUpperCase()}${cleanedFilename}"/>
					`
				} else {
					html += `<span class="name small">${ file.name }</span>`
				}
			html += `<input type="hidden" class="evidence-order-input" name="${colour}files_order" value="${file.name}">`
			$(`#evidence-${colour}`).append(html)
			$(`#${colour}files`).val("")
		}) 
	})
}

function santiseFilename(filename) {
    return filename
        .split('/').pop().split('\\').pop()  // Remove paths
        .normalize('NFKD').replace(/[\u0300-\u036f]/g, '')  // ASCII
        .replace(/[^\w.-]/g, '_')  // Replace unsafe chars
        .replace(/^[._-]+|[._-]+$/g, '') || 'unnamed';  // Clean edges
}

// Ensure hidden evidence order fields match the current list order before save.
$(document).on('submit', '#ttpform', function() {
	['red', 'blue'].forEach(colour => syncEvidenceOrder(colour))
})
