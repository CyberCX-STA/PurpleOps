var $table = $("#user-table")[0]
var rowData = null

$(function () {
	$('#user-table').bootstrapTable()
	$('#engagement-selector').selectpicker()
})

function newUserModal(e) {
	$('#userDetailForm').attr('action', '/manage/access/user') 
	$('#userDetailLabel').text("New User")
	$('#userDetailButton').text("Create")
	$('#password-section').show()
	$('#password').attr('required', 'required');
	$('#userDetailForm #username').val("")
	$('#userDetailForm #email').val("")
	$('#userDetailForm #roles').selectpicker('val', "");
	$('#userDetailForm #assessments').selectpicker('val', "");
	$('#userDetailModal').modal('show')
}

function editUserModal(e) {
	let i = $(e).closest("tr").data("index")
	rowData = $('#user-table').bootstrapTable('getData')[i]
	$('#userDetailForm').attr('action', '/manage/access/user/' + rowData.id) 
	$('#userDetailLabel').text("Update Details For " + rowData.username)
	$('#userDetailButton').text("Update")
	$('#password-section').hide()
	$('#password').removeAttr('required');
	$('#userDetailForm #username').val(rowData.username)
	$('#userDetailForm #email').val(rowData.email)
	$('#userDetailForm #roles').selectpicker('val', rowData.roles.split(", "));
	$('#userDetailForm #assessments').selectpicker('val', rowData.assessments.split(", "));
	$('#userDetailModal').modal('show')
}

function pwdResetModal(e) {
	let i = $(e).closest("tr").data("index")
	rowData = $('#user-table').bootstrapTable('getData')[i]
	$('#pwdResetForm').attr('action', '/manage/access/user/' + rowData.id) 
	$('#pwdresetModalLabel').text("Reset Password For " + rowData.username)
	$('#pwdResetModal').modal('show')
}

function delUserModal(e) {
	let i = $(e).closest("tr").data("index")
	rowData = $('#user-table').bootstrapTable('getData')[i]
	$('#delUserForm').attr('action', '/manage/access/user/' + rowData.id) 
	$('#delUserWarning').text("Really Delete " + rowData.username + "?")
	$('#delUserModal').modal('show')
}

function delUser(e) {
	$.ajax({
		url: '/manage/access/user/' + rowData.id,
		type: 'DELETE',
		success: function(result) {
			location.reload();
		}
	});
}