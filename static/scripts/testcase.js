let assID = $("#multiForm")[0].dataset.assid
let assName = $("#multiForm")[0].dataset.assname

// Show saved toast if just saved

$(function () {
	if (window.location.hash.includes("saved")) {
		new bootstrap.Toast(document.querySelector('#saveToast')).show();
		history.replaceState({}, document.title, window.location.href.split('#')[0]);		
	}
})

// Dynamic text area sizing seeing as there's no native HTML way

function textAreaDynamicHeight(e) {
	e.style.height = 0;
	e.style.height = e.scrollHeight + 5 + 'px';
}
["#objective", "#actions", "#notes", "#bluenotes"].forEach(elem => {
	// Onload and oninput
	$(elem).on('input',function(e){textAreaDynamicHeight(e.target)});
	textAreaDynamicHeight($(elem)[0])
});

// Date-time picker init

$(function () {
	if (window.location.hash.includes("saved")) {
		new bootstrap.Toast(document.querySelector('#saveToast')).show();
		history.replaceState({}, document.title, window.location.href.split('#')[0]);		
	}

	["time-start", "time-end", "time-detect"].forEach(function (id) {
		new tempusDominus.TempusDominus(document.getElementById(id), {
			display: {
				icons: {
					time: 'bi bi-clock',
					date: 'bi bi-calendar',
					up: 'bi bi-arrow-up',
					down: 'bi bi-arrow-down',
					previous: 'bi bi-chevron-left',
					next: 'bi bi-chevron-right',
					today: 'bi bi-calendar-check',
					clear: 'bi bi-trash',
					close: 'bi bi-x',
				},
				sideBySide: true
			},
			localization: {
				locale: "en-AU"
			},
			useCurrent: false
		});
	});  
})

// Intercept manage submit interface (source/target/tools)

function multiSubmit(e) {
	e.preventDefault()
	fetch(e.target.dataset.action, {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify($("#manage-table").bootstrapTable("getData"))
	})
	.then(() => {
		$('#manageMulti').modal('hide')
		populateDropdown(e.target.dataset.action.split("/")[2])
	})
	return false
}

// Tag management

function tagSubmit(e) {
	e.preventDefault()
	fetch(e.target.dataset.action, {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify($("#tag-table").bootstrapTable("getData"))
	})
	.then(() => {
		$('#manageTags').modal('hide')
		populateDropdown(e.target.dataset.action.split("/")[2])
	})
	return false
}

function manageTags(e) {
	if ($(e).prop("tagName") === "SELECT") {
		// If we opened the modal with the "manage" item
		let vals = $(e).val()

		// Hacks to use a "select" option as a button
		if (vals.includes("Manage")) {
			$(e).selectpicker('val', vals.filter(item => item !== "Manage"))
			$(e).selectpicker('toggle');
			$('#manageTags').modal('show')
		}
		else {return}
	}
	else {
		// If we opened it with the direct button
		$('#manageTags').modal('show')
	}

	$('#tag-table').bootstrapTable('showLoading')
	loadRows("#tagForm", "#tag-table")
}

window.tagEvents = {
	// Add a new row or remove old if trash or + add in manage modal
	'click .trash-multi': function (e, value, row, index) {
		$('#tag-table').bootstrapTable('remove', { field: '$index', values: [index] })
	},

	'click .add-multi': function (e, value, row, index) {
		let r = {id: 0, name: "", colour: ""}
		$('#tag-table').bootstrapTable('insertRow', { index: index + 1, row: r })
	}
}
$(document).on('change', '#tag-table .multi-editable', function(event) {
	// If a manage item's name or description is updated, refresh table markup
	$('#tag-table').bootstrapTable('updateCell', {
		index: $(this).closest("tr")[0].dataset.index,
		field: this.dataset.field,
		value: $(this).val()
	});
});


// Reference management

// function referenceNew(e) {
// 	let clone = $('#red-reflist').children().last().clone().insertAfter(e.parentNode)
// 	$(clone).find("#reftitle").val("")
// 	$(clone).find("#reflink").val("")
// 	$(clone).find("#reftab").attr("href", "")
// }

// function referenceDelete(e) {
// 	if ($('#red-reflist').children().length === 1) {
// 		referenceNew(e)
// 	}
// 	$(e).parent().remove()
// }

// function referenceLink(e) {
// 	$(e).parent().find("#reftab").attr("href", e.value)
// }

// TTP save submission intercept

$('#ttpform').submit(function(e) {
	if (!$('#ttpform').data("go") == "1") e.preventDefault();
	else return true

	// Swap sources etc. names for DB IDs
	$(".filter-option-inner-inner").hide()
	let arr = ["sources", "targets", "tools", "tags", "controls"]
	arr.forEach((z) => {
		$(".dynopt-" + z).remove();
		manageData["selected-" + z].forEach(function(i) {
			$("#" + z).append(`<option class="dynopt-${z}">${i}</option>`);
		})
		$("#" + z).selectpicker('refresh');
		$("#" + z).selectpicker('val', manageData["selected-" + z])
	})

	$('#ttpform').data("go", "1")
	$('#ttpform').submit()
});

// Source / target / tool AJAX

let manageData = {
	// Globals for name/ID cross-reffing
	"sources": {},
	"selected-sources": [],
	"targets": {},
	"selected-targets": [],
	"tools": {},
	"selected-tools": [],
	"tags": {},
	"selected-tags": [],
	"controls": {},
	"selected-controls": []
}

function manageMulti(e) {
	// Reuse modal between source/targets/tools, update labels and init populate
	let modalLabel = $("#manageMultiLabel")
	let multiForm = $("#multiForm")[0]
	$("#nameField").innerText = "Hostname / IP"
	console.log(e.id)

	if (e.id.includes("source")) {
		multiForm.dataset.action = "/assessment/sources/" + assID
		modalLabel.text("Manage Sources")
	}
	if (e.id.includes("target")) {
		multiForm.dataset.action = "/assessment/targets/" + assID
		modalLabel.text("Manage Targets")
	}
	if (e.id.includes("tool")) {
		multiForm.dataset.action = "/assessment/tools/" + assID
		modalLabel.text("Manage Tools")
		$("#nameField").innerText = "Tool Name"
	}
	if (e.id.includes("control")) {
		multiForm.dataset.action = "/assessment/controls/" + assID
		modalLabel.text("Manage Controls")
		$("#nameField").innerText = "Control Name"
	}

	if ($(e).prop("tagName") === "SELECT") {
		// If we opened the modal with the "manage" item
		let vals = $(e).val()

		// Hacks to use a "select" option as a button
		if (vals.includes("Manage")) {
			$(e).selectpicker('val', vals.filter(item => item !== "Manage"))
			$(e).selectpicker('toggle');
			$('#manageMulti').modal('show')
		}
		else {return}
	}
	else {
		// If we opened it with the direct button
		$('#manageMulti').modal('show')
	}

	$('#manage-table').bootstrapTable('showLoading')
	loadRows("#multiForm", "#manage-table")
}

function nameRowFormatter(name){
	// Helper function to format name row in modal table
	return '<input type="text" class="form-control multi-editable" data-field="name" placeholder="Name..." value="' + name + '">';
}

function descRowFormatter(desc){
	return '<input type="text" class="form-control multi-editable" data-field="description" placeholder="Description..." value="' + desc + '">'
}

function colourRowFormatter(desc="#ff0000"){
	return '<input type="color" class="form-control multi-editable" data-field="colour" value="' + desc + '">'
}

function deleteRowFormatter() {
	return '<button type="button" class="btn btn-sm btn-outline-danger trash-multi"><i class="bi-trash">&zwnj;</i></button>'
}

function loadRows(form, table) {
	// Keep data up to date by pulling from DB
	let bsTable = $(table)
	fetch($(form)[0].dataset.action)
	.then(
		function(response) {
			response.json().then(function(data) {
				let rows = []
				// Populate the rows, then remove "loading"
				if (form == "#multiForm") {
					data.forEach(e => rows.push({
						id: e.id,
						name: e.name,
						description: e.description
					}));
				}
				else {
					data.forEach(e => rows.push({
						id: e.id,
						name: e.name,
						colour: e.colour
					}));
				}
				bsTable.bootstrapTable('load', rows)
				bsTable.bootstrapTable('hideLoading')
			});
		}
	)
}

function dropdownValsToIDs (item) {
	// Helper function to translate dropdown names to DB IDs
	let translated = []
	let selected = $("#" + item).val();
	manageData[item].forEach(function(i){
		if (selected.includes(i.name)) translated.push(i.id)
	});
	return translated
}

function dropdownIDsToVals (item) {
	// Helper function to translate dropdown DB IDs to names
	let translated = []
	let selectedIDs = manageData["selected-" + item]
	manageData[item].forEach(function(i){
		if (selectedIDs.includes(i.id)) translated.push(i.name)
	});
	return translated
}

$('.selectpicker').on('changed.bs.select', function (e, clickedIndex, newValue, oldValue) {
	// Update internal selected global var when a new option is (un)ticked
	let item = e.target.id
	manageData["selected-" + item] = dropdownValsToIDs(item)
});

function populateDropdown(item, init=0) {
	// Populate dropdown options based on initial or updated data
	let dropDownElem = $('#' + item)
	if (init) {
		manageData["selected-" + item] = dropDownElem.selectpicker().val()
	}
	$(".dynopt-" + item).remove();
	fetch(`/assessment/${item}/${assID}`)
	.then(
		function(response) {
			response.json().then(function(data) {
				manageData[item] = data
				data.forEach(function(i){
					if (item == "tags") {
						dropDownElem.append(`<option data-id="${i.id}" class="dynopt-${item}" data-content="<span class='badge rounded-pill' style='background:${i.colour}'>${i.name}</span>">${i.name}</option>`);
					}
					else {
						dropDownElem.append(`<option data-id="${i.id}" class="dynopt-${item}">${i.name}</option>`);
					}
				})
				dropDownElem.selectpicker('refresh');
				dropDownElem.selectpicker('val', dropdownIDsToVals(item))
			});
		}
	)
}

window.manageEvents = {
	// Add a new row or remove old if trash or + add in manage modal
	'click .trash-multi': function (e, value, row, index) {
		$('#manage-table').bootstrapTable('remove', { field: '$index', values: [index] })
	}
}
function addManageRow(tabe) {
	var r = {id: 0, name: "", description: ""}
	$('#' + tabe).bootstrapTable('append', r)
}
$(document).on('change', '#manage-table .multi-editable', function(event) {
	// If a manage item's name or description is updated, refresh table markup
	$('#manage-table').bootstrapTable('updateCell', {
		index: $(this).closest("tr")[0].dataset.index,
		field: this.dataset.field,
		value: $(this).val()
	});
});

populateDropdown("sources", 1)
populateDropdown("targets", 1)
populateDropdown("tools", 1)
populateDropdown("tags", 1)
populateDropdown("controls", 1)

$('#tag-table').bootstrapTable();
$('#manage-table').bootstrapTable();

// Score management
$(function() {
	dynamicScores()
});

$('#blocked-yes, #blocked-no, #blocked-partial, #blocked-na, #alert-yes, #alert-no, #alert, #log-yes, #log-no, #detection-quality, #time-detect, #priority-prevent, #priority-detect, #priority-na').change(function() {
	dynamicScores()
  })

function dynamicScores() {
	blocked = null
	if ($("#blocked-yes").prop('checked')) blocked = "yes"
	if ($("#blocked-partial").prop('checked')) blocked = "partial"
	if ($("#blocked-no").prop('checked')) blocked = "no"
	if ($("#blocked-na").prop('checked')) blocked = "na"

	if (blocked == "yes" || blocked == "partial") {
		$("#blockedrating-container").show()
	}
	if (blocked == "no") {
		$("#blockedrating-container").hide()
	}
	if (blocked == "na") {
		$("#blockedrating-container").hide()
	}
	if (blocked == null) {
		$("#blockedrating-container").hide()
	}

	alerted = null
	if ($("#alert-yes").prop("checked")) alerted = true
	if ($("#alert-no").prop("checked")) alerted = false

	if (alerted) {
		$("#alert-container").show()
		$("#logged-container").hide()
		$("#log-yes").click()

		if (!$("#time-detect").val()) {
			cur = new Date().toLocaleString('en-AU').split(":")
			cur = cur[0] + ":" + cur[1] + " " + cur[2].slice(-2)
			$("#time-detect").val(cur)
		}
	}
	if (!alerted && alerted != null) {
		$("#alert-container").hide()
		$("#logged-container").show()
	}
	if (alerted == null) {
		$("#alert-container").hide()
		$("#logged-container").hide()
		$("#detection-container").hide()
	}

	logged = null
	if ($("#log-yes").prop("checked")) logged = true
	if ($("#log-no").prop("checked")) logged = false

	if (!alerted && !logged) {
		$("#detection-container").hide()
	}
	else if (logged != null && alerted != null) {
		$("#detection-container").show()
	}
	if (alerted) $("#detection-container").show()

	priority = null
	if ($("#priority-prevent").prop("checked")) priority = true
	if ($("#priority-detect").prop("checked")) priority = true
	if ($("#priority-na").prop("checked")) priority = false

	if (priority) $("#urgency-container").show()
	else $("#urgency-container").hide()
}

// State management

function updateState() {
    currentstate = $("#run-button").val();
	cur = new Date().toLocaleString('en-AU').split(":")
	cur = cur[0] + ":" + cur[1] + " " + cur[2].slice(-2)

    var formData = {
        testid: $("#ttpform").attr('value'),
        state: currentstate,
        starttime: $("#time-start").val() || cur,
        endtime: $("#time-end").val() || cur,
    };

    var result = null;

    $.ajax({
        type: "POST",
        url: "/testcase/state",
        data: formData,
        dataType: "html",
        encode: true,
    }).done(function (data) {
        console.log(data);
        result = data
        if (currentstate === "Pending" || currentstate === "Complete") {
            $("#run-button").text('Stop');
            $("#run-button").removeClass("btn-outline-success btn-outline-primary").addClass("btn-outline-warning");
            $("#state").val('In progress');
            $("#state").removeClass("bg-success").addClass("bg-warning");
            $("#time-start").val(cur)
            $("#time-end").val("")
            $("#run-button").val(result)
        }
        else if (currentstate === "In progress") {
            $("#run-button").text('Restart');
            $("#run-button").removeClass("btn btn-outline-warning btn-sm w-100").addClass("btn btn-outline-primary btn-sm w-100");
			$("#state").val('Complete');
            $("#state").removeClass("bg-warning").addClass("bg-success");
			$("#time-end").val(cur)
            $("#run-button").val(result)
        }
    });
}

// File management

function deleteFile(e, color, id, file) {
	$(e).parent().remove()
	$.ajax({
		url: '/testcase/file/' + color + "/" + id + "/" + file,
		type: 'DELETE',
		success: function(result) {
			
		}
	});
}

function downloadFile(e, id, file) {
	window.location.href = '/testcase/download/' + id + '/' + file;
}

// Breadcrumb back button

$("#assessment-crumb-button").css("display", "block");
$("#assessment-crumb").text(assName)
$("#assessment-crumb-button").attr("href", "/assessment/" + assID)

// Template select

function templateChange(e) {
	$('#templateHTMLs').children().each(function () {this.style.display = "none"});
	$("#actions").val($("#" + e.value).children("pre")[0].firstChild.innerText)
	$("#template-info").show()
	textAreaDynamicHeight($("#actions")[0])
}

function templateClear() {
	$("#template-info").hide()
	$("#templateselect").val("")
}

function templateModal() {
	id = $("#templateselect").val()
	if (id) {
		$("#" + $("#templateselect").val()).css("display", "block")
		$("#manageTest").modal("show")
	}
}