var $table = $("#userTable")[0]
var rowData = null

$(function () {
	$('#userTable').bootstrapTable()
})

function newUserModal(e) {
	$("#userDetailForm").trigger('reset')
	$('#userDetailForm').attr('action', '/manage/access/user') 
	$('#userDetailLabel').text("New User")
	$('#userDetailButton').text("Create")
	$('#password').attr("type", "text")
	$('#userDetailModal').modal('show')
}

function editUserModal(e) {
	let i = $(e).closest("tr").data("index")
	rowData = $('#userTable').bootstrapTable('getData')[i]
	$("#userDetailForm").trigger('reset')
	$('#userDetailForm').attr('action', '/manage/access/user/' + rowData.id) 
	$('#userDetailLabel').text("Edit User")
	$('#userDetailButton').text("Update")
	// Make it look like a password is in the form, stops admins getting scared
	// that altering a user's details will wipe their password whilst still
	// giving them a chance to change it
	$('#password').attr("type", "password")
	$('#password').val(" ".repeat(128))
	$('#userDetailForm #username').val(rowData.username)
	$('#userDetailForm #email').val(rowData.email)
	$('#userDetailForm #roles').selectpicker('val', rowData.roles.split(", "));
	$('#userDetailForm #assessments').selectpicker('val', rowData.assessments.split(", "));
	$('#userDetailModal').modal('show')
}

function delUserModal(e) {
	let i = $(e).closest("tr").data("index")
	rowData = $('#userTable').bootstrapTable('getData')[i]
	$('#delUserForm').attr('action', '/manage/access/user/' + rowData.id) 
	$('#delUserWarning').text("Really Delete " + rowData.username + "?")
	$('#delUserModal').modal('show')
}

$('#delUserButton').click(function() {
	$.ajax({
		url: '/manage/access/user/' + rowData.id,
		type: 'DELETE',
		success: function(result) {
			// location.reload();
		}
	});
});