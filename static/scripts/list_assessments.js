$(function () {
    $('#ass-table').bootstrapTable('hideRow', {index:0})
    $('#ass-table').show()
  })

  // document.querySelector("#name-update").addEventListener("keyup", event => {
  //   if(event.key !== "Enter") return;
  //   editAssessment()
  //   event.preventDefault();
  // });

  // document.querySelector("#description-update").addEventListener("keyup", event => {
  //   if(event.key !== "Enter") return;
  //   editAssessment()
  //   event.preventDefault();
  // });

  // document.querySelector("#name-new").addEventListener("keyup", event => {
  //   if(event.key !== "Enter") return;
  //   newAssessment()
  //   event.preventDefault();
  // });

  // document.querySelector("#description-new").addEventListener("keyup", event => {
  //   if(event.key !== "Enter") return;
  //   newAssessment()
  //   event.preventDefault();
  // });

  function softDeleteAssessment (name, id) {
    $("#delete-warning").text("Really delete '" + name + "'? This will remove all tests, results, notes and evidence.")
    $("#hard-delete-button").attr("onclick", "hardDeleteAssessment('" + id + "')")
    $('#deleteassessmentmodal').modal('show')
  }

  function hardDeleteAssessment (id) {
    $('#deleteassessmentmodal').modal('hide')

    $.get("/assessment/delete/" + id, function (data, status) {
      if (status == "success") {
        $("#ass-table").bootstrapTable('remove', {field: "id", values: [id]})
        new bootstrap.Toast(document.querySelector('#deleteToast')).show();
      }
    });
  }

  function updateAssessmentModal(e, id, name, description, industry="", techmaturity="", opmaturity="", socmodel="", socprovider="", webhook="") {
		$('#updateassessmentmodal #id').val(id)
		$('#updateassessmentmodal').data('id', id)
		$('#updateassessmentmodal #name-update').val(name)
		$('#updateassessmentmodal').data('name', name)
		$('#updateassessmentmodal #description-update').val(description)
		$('#updateassessmentmodal').data('description', description)
		$('#updateassessmentmodal #industry-update').val(industry)
		$('#updateassessmentmodal').data('industry', industry)
		$('#updateassessmentmodal #techmaturity-update').val(techmaturity)
		$('#updateassessmentmodal').data('techmaturity', techmaturity)
		$('#updateassessmentmodal #opmaturity-update').val(opmaturity)
		$('#updateassessmentmodal').data('opmaturity', opmaturity)
		$('#updateassessmentmodal #socmodel-update').val(socmodel)
		$('#updateassessmentmodal').data('socmodel', socmodel)
		$('#updateassessmentmodal #socprovider-update').val(socprovider)
		$('#updateassessmentmodal').data('socprovider', socprovider)
		$('#updateassessmentmodal #webhook-update').val(webhook)
		$('#updateassessmentmodal').data('webhook', webhook)
		$('#updateassessmentmodal').modal('show')
	}

  function cloneAssessment (e, id, name, description, pct) {
    new bootstrap.Toast(document.querySelector('#cloningToast')).show();
    $.get("/assessment/clone/" + id, function (data, status) {
      if (status == "success") {
        orig = $("#ass-table").bootstrapTable('getData').find(row => row.id == id)
        idx = $("#ass-table").bootstrapTable('getData').findIndex(row => row.id == id)
        clone = JSON.stringify(orig).replaceAll(id, data.id)
        clone = clone.replaceAll(name, "Copy of " + name)
        clone = clone.replaceAll(pct + "%", "0")
        $("#ass-table").bootstrapTable('insertRow', {index: idx + 1, row: JSON.parse(clone)})
        new bootstrap.Toast(document.querySelector('#cloneToast')).show();
      }
    });
    
  }

  function editAssessment () {
    id = $('#updateassessmentmodal #id').val()
		newName = $('#updateassessmentmodal #name-update').val()
		origName = $('#updateassessmentmodal').data('name')
		newDesc = $('#updateassessmentmodal #description-update').val()
		origDesc = $('#updateassessmentmodal').data('description')
		newIndustry = $('#updateassessmentmodal #industry-update').val()
		origIndustry = $('#updateassessmentmodal').data('industry')
		newTechMaturity = $('#updateassessmentmodal #techmaturity-update').val()
		origTechMaturity = $('#updateassessmentmodal').data('techmaturity')
		newOpMaturity = $('#updateassessmentmodal #opmaturity-update').val()
		origOpMaturity = $('#updateassessmentmodal').data('opmaturity')
		newSocModel = $('#updateassessmentmodal #socmodel-update').val()
		origSocModel = $('#updateassessmentmodal').data('socmodel')
		newSocProvider = $('#updateassessmentmodal #socprovider-update').val()
		origSocProvider = $('#updateassessmentmodal').data('socprovider')
		newWebhook = $('#updateassessmentmodal #webhook-update').val()
		origWebhook = $('#updateassessmentmodal').data('webhook')

    let dat = {
      name: newName,
      description: newDesc,
      industry: newIndustry,
      techmaturity: newTechMaturity,
      opmaturity: newOpMaturity,
      socmodel: newSocModel,
      socprovider: newSocProvider,
      webhook: newWebhook
    }

    $.post("/assessment/update/" + id, dat, function (data, status) {
      console.log(status)
      if (status == "nocontent") {
        orig = $("#ass-table").bootstrapTable('getData').find(row => row.id == id)
        idx = $("#ass-table").bootstrapTable('getData').findIndex(row => row.id == id)
        clone = JSON.stringify(orig).replaceAll(origName, newName)
        clone = clone.replaceAll(origDesc, newDesc)
        clone = clone.replaceAll(origIndustry, newIndustry)
        clone = clone.replaceAll(origTechMaturity, newTechMaturity)
        clone = clone.replaceAll(origOpMaturity, newOpMaturity)
        clone = clone.replaceAll(origSocModel, newSocModel)
        clone = clone.replaceAll(origSocProvider, newSocProvider)
        clone = clone.replaceAll(origWebhook, newWebhook)
        $("#ass-table").bootstrapTable('updateRow', {index: idx, row: JSON.parse(clone)})
      }
    });

    $('#updateassessmentmodal').modal('hide')
  }

  function newAssessment () {
		name = $('#newassessmentmodal #name-new').val()
		desc = $('#newassessmentmodal #description-new').val()
		industry = $('#newassessmentmodal #industry-new').val()
		techmaturity = $('#newassessmentmodal #techmaturity-new').val()
		opmaturity = $('#newassessmentmodal #opmaturity-new').val()
		socmodel = $('#newassessmentmodal #socmodel-new').val()
		socprovider = $('#newassessmentmodal #socprovider-new').val()
		webhook = $('#newassessmentmodal #webhook-new').val()

    let dat = {
      name: name,
      description: desc,
      industry: industry,
      techmaturity: techmaturity,
      opmaturity: opmaturity,
      socmodel: socmodel,
      socprovider: socprovider,
      webhook: webhook
    }

    $.post("/assessment/new", dat, function (data, status) {
      console.log(status)
      if (status == "success") {
        rowTmpl = $("#ass-table").bootstrapTable('getData')[0]
        clone = JSON.stringify(rowTmpl).replaceAll("#ID#", data.id)
        clone = clone.replaceAll("#NAME#", name)
        clone = clone.replaceAll("#DESC#", desc)
        clone = clone.replaceAll("#INDUSTRY#", industry)
        clone = clone.replaceAll("#TECHMATURITY#", techmaturity)
        clone = clone.replaceAll("#OPMATURITY#", opmaturity)
        clone = clone.replaceAll("#SOCMODEL#", socmodel)
        clone = clone.replaceAll("#SOCPROVIDER#", socprovider)
        clone = clone.replaceAll("#WEBHOOK#", webhook)
        $("#ass-table").bootstrapTable('append', JSON.parse(clone))
      }
    });
    $('#newassessmentmodal').modal('hide')
  }