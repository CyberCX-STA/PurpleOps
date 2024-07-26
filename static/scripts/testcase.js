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
			selectedIDs = $(`#${type}`).val()
			$(".dynopt-" + type).remove();
			result.forEach(function(i) {
				selected = selectedIDs.includes(i.id) ? "selected" : ""
				pill = type == "tags" ? `data-content="<span class='badge rounded-pill' style='background:${i.colour}'>${i.name}</span>"` : ""
				$(`#${type}`).append(`<option ${selected} class="dynopt-${type}" value="${i.id}" ${pill}>${i.name}</option>`);
			})
			$(`#${type}`).selectpicker('destroy');
			$(`#${type}`).selectpicker();
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

// Dynamically update prevent fields
$('input[name="prevented"]').on('change', function() {
	current = $('input[name="prevented"]:checked').val()
	if (["No", "N/A", ""].includes(current)) {
		$("#preventedrating").val(current.replace("No", "0.0"))
		$("#preventedrating-container").hide()
		$("#preventionsources-container").hide()
		$("#preventionsources").val("")
		$("#preventiontime-container").hide()
		$("#time-preventtime").val("")
	} else {
		if (["0.0", "N/A"].includes($("#preventedrating").val())) {
			$("#preventedrating").val("")
		}
		$("#preventedrating-container").hide()
		$("#preventionsources-container").show()
		$("#preventiontime-container").show()
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
		$("#detectionsources-container").show()
		$("#detection-container").hide()
		$("#logged-container").hide()
		$('input[name="logged"]').prop('checked', false)
		$('#log-yes').prop("checked", true)
		if ($('#detectionrating').val() == "0.0") {
			$('#detectionrating').val("")
		}
	} else if (current == "No") {
		$("#alert-container").hide()
		$("#detectionsources-container").hide()
		$("#time-alerttime").val("")
		$("#detectionsources").val("")
		$("#detectionsources").val("")
		$("#alertseverity").val("")
		$("#logged-container").show()
		$("#detection-container").hide()
	} else {
		$("#alert-container").hide()
		$("#detectionsources-container").hide()
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

// AJAX submit and pop toast on save success
$("#ttpform").submit(function(e) {
  e.preventDefault();

  fetch(e.target.action, {
    method: 'POST',
    body: new FormData(e.target)
  })
  .then(response => {
    if (response.status === 200) { // Use === for strict comparison
      return response.text(); // Chain .text() for text response
    } else {
      throw new Error(`Error: ${response.status}`);
    }
  })
  .then(text => {
    displayNewEvidence(new FormData(e.target));
    showToast('Testcase Saved');
    const modifyTimeInput = document.getElementById('modifytime');
    if (modifyTimeInput) {
      modifyTimeInput.value = text; // Set the response text as the new value
    }
  })
  .catch(error => {
    if (error.message.includes('409')) {
      alert("Testcase save error - Testcase was saved in the meantime");
    } else {
      alert("Testcase save error - contact admin to review log");
      console.error(error); // Log the error for debugging
    }
  });
});

// Convert UTC DB time to local time
$( document ).ready(function() {
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

	if ($("#time-alerttime").val()) {
		endTime = new Date($("#time-alerttime").val());
		endTime.setMinutes(endTime.getMinutes() - offset * 2);
		$("#time-alerttime").val(endTime.toISOString().slice(0,16))
	}

	if ($("#time-preventtime").val()) {
		endTime = new Date($("#time-preventtime").val());
		endTime.setMinutes(endTime.getMinutes() - offset * 2);
		$("#time-preventtime").val(endTime.toISOString().slice(0,16))
	}

});

// Alter timestamps, button labels and state when hitting run button
$("#run-button").click(function(){
	clickTime = new Date();
	clickTime.setMinutes(clickTime.getMinutes() - clickTime.getTimezoneOffset());
	clickTime = clickTime.toISOString().slice(0, 16)

	if ($("#run-button").text() == "Start") {
		$("#time-start").val(clickTime)
		$("#time-end").val("")
		$("#run-button").text("Stop")
		$("#run-button").removeClass("btn-outline-success")
		$("#run-button").addClass("btn-outline-danger")
		$("#state").val("Running")
		$("#state").addClass("bg-warning")
		$("#state").removeClass("text-white")
		$("#state").addClass("text-dark")
	} else if ($("#run-button").text() == "Stop") {
		$("#time-end").val(clickTime)
		$("#run-button").text("Restart")
		$("#run-button").removeClass("btn-outline-danger")
		$("#run-button").addClass("btn-outline-warning")
		$("#state").val("Waiting Blue")
		$("#state").removeClass("bg-warning")
		$("#state").addClass("bg-info")
		$("#state").removeClass("text-dark")
		$("#state").addClass("text-white")
	} else if ($("#run-button").text() == "Restart") {
		$("#time-start").val("")
		$("#time-end").val("")
		$("#run-button").text("Start")
		$("#run-button").removeClass("btn-outline-danger")
		$("#run-button").removeClass("btn-outline-warning")
		$("#run-button").addClass("btn-outline-success")
		$("#state").val("Pending")
		$("#state").removeClass("bg-primary")
		$("#state").removeClass("text-white")
	} 
});

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
		}
	});
});

// AJAX inject new evidence HTML on testcase save
function displayNewEvidence(form) {
	["red", "blue"].forEach(colour => {
		form.getAll(`${colour}files`).forEach(file => {
			if (file.name == "") {
				return
			}
			testcaseId = window.location.pathname.split("/").slice(-1)[0]
			html = `
				<li class="list-group-item">
					<button type="button" class="btn btn-outline-danger btn-sm me-2 evidence-delete evidence-${colour}">
						<i class="bi-trash small">&zwnj;</i>
					</button>
					<a href="/testcase/${testcaseId}/evidence/${file.name}?download=true" class="btn btn-outline-primary btn-sm me-2">
						<i class="bi-download small">&zwnj;</i>
					</a>`
			if (file.name.toLowerCase().endsWith(".png") || 
				file.name.toLowerCase().endsWith(".jpg") ||
				file.name.toLowerCase().endsWith(".jpeg")) {
					html += `
						<a href="/testcase/${testcaseId}/evidence/${file.name}" target="_blank">
							<img class="img-fluid img-thumbnail" style="max-width: 80%" src="/testcase/${testcaseId}/evidence/${file.name}"/>
						</a>
						<input style="margin-left: 6em; width:80%;" class="form-control form-control-sm" type="text" placeholder="Caption..." value="" id="${colour.toUpperCase()}${file.name}" name="${colour.toUpperCase()}${file.name}"/>
					`
				} else {
					html += `<span class="name small">${ file.name }</span>`
				}
			$(`#evidence-${colour}`).append(html)
			$(`#${colour}files`).val("")
		}) 
	})
}

//add copy code button to testcaseKB
function copyCodeBlocks() {
  const testcaseKBModalDIV = document.getElementById('testcaseKBModal');
  const codeBlocks = testcaseKBModalDIV.querySelectorAll('code');

  codeBlocks.forEach(codeBlock => {
    const copyButton = document.createElement('button');
    copyButton.classList.add("btn", "btn-secondary", "bi-code");

    // Add click event listener to the button
    copyButton.addEventListener('click', () => {
      const text = codeBlock.textContent;
      navigator.clipboard.writeText(text)
        .then(() => {
        	showToast('Code Copied')
        })
        .catch(err => {
        	alert('Failed to copy code: '+ err)
        });
    });

    // Append the button directly within the loop
    codeBlock.parentNode.insertBefore(copyButton, codeBlock.nextSibling);
  });
}
//execute the function. Not sure where to put it else.
copyCodeBlocks()


//add toggle button to testcaseKB
function toggleVariablesinCodeBlocks() {

	const testcaseKBModalDIV = document.getElementById('testcaseKBModal');
  const codeBlocks = testcaseKBModalDIV.querySelectorAll('code');
  const assessmentid = document.getElementById('assessmentid').textContent;

  codeBlocks.forEach(codeBlock => {
    const toggleButton = document.createElement('button');
    toggleButton.classList.add("btn", "btn-secondary", "bi-toggles", "mx-sm-2");
    let isToggled = codeBlock.dataset.isToggled === 'true';

    toggleButton.addEventListener('click', () => {
      isToggled = !isToggled;

      if (isToggled) {
        const content = codeBlock.textContent;
        const regex = /\{\{([^}]+)\}\}/g; // Global flag for multiple matches
        codeBlock.dataset.originalTextContent = content;

        codeBlock.textContent = content.replace(regex, (match, variable) => {
          const value = sessionStorage.getItem(assessmentid + "_" + variable);
          return value !== null ? value : match;
        });
      } else if (codeBlock.dataset.originalTextContent) {
        codeBlock.textContent = codeBlock.dataset.originalTextContent;
      }
    });

    codeBlock.parentNode.insertBefore(toggleButton, codeBlock.nextSibling);
  });
}
//execute the function. Not sure where to put it else.
toggleVariablesinCodeBlocks()