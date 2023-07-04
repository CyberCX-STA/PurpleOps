// Delay table showing until page is loaded to prevent jumping
$(function () {
	$('#userTable').show()
})

var row = null
var rowData = null

function newUserModal(e) {
	// This mess allows us to reuse the modal between new and edit user
	$("#userDetailForm").trigger('reset')
	$('#userDetailForm').attr('action', '/manage/access/user') 
	$('#userDetailLabel').text("New User")
	$('#userDetailButton').text("Create")
	$('#password').attr("type", "text")
	$('#userDetailForm #roles').selectpicker('val', "");
	$('#userDetailForm #assessments').selectpicker('val', "");
	$('#userDetailModal').modal('show')
}

function editUserModal(e) {
	// Globally store the clicked row for AJAX operations
	row = $(e).closest("tr")
	rowData = $('#userTable').bootstrapTable('getData')[row.data("index")]
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

function deleteUserModal(e) {
	// Globally store the clicked row for AJAX operations
	row = $(e).closest("tr")
	rowData = $('#userTable').bootstrapTable('getData')[row.data("index")]
	$('#deleteUserForm').attr('action', '/manage/access/user/' + rowData.id) 
	$('#deleteUserWarning').html(`Really Delete <code>${rowData.username}</code>?`)
	$('#deleteUserModal').modal('show')
}

// Hook the native new/edit user HTML form to catch and action the response
$("#userDetailForm").submit(function(e){
	e.preventDefault();

    fetch(e.target.action, {
        method: 'POST',
        body: new URLSearchParams(new FormData(e.target))
    }).then((response) => {
        return response.json();
    }).then((body) => {
		// Format assessment cell
		if (body.roles.includes("Admin")) {
			body.assessments = "*"
		} else if (body.assessments.length) {
			body.assessments = body.assessments.join(", ")
		} else {
			body.assessments = "-"
		}

		// Format last login cell
		body["last-login"] = body.last_login_at ? body.last_login_at : "-"
		if (body.last_login_at) {
			body["last-login"] += ` (${body.current_login_ip || body.last_login_ip})`
		}

		newRow = {
			id: body.id,
			username: body.username,
			email: body.email,
			roles: body.roles.length ? body.roles.join(", ") : "-",
			"last-login": body["last-login"],
			assessments: body.assessments,
			actions: body.username
		}
        
		// This function is shared between new and edit user, so do we need to
		// edit a row or create a new one?
		if ($('#userTable').bootstrapTable('getRowByUniqueId', body.id)) {
			$('#userTable').bootstrapTable('updateRow', {
				index: row.data("index"),
				row: newRow,
				replace: true
			})
		} else {
			$('#userTable').bootstrapTable('append', [newRow])
		}

		$('#userDetailModal').modal('hide')
    })
});

// AJAX DELETE user call
$('#deleteUserButton').click(function() {
	$.ajax({
		url: '/manage/access/user/' + rowData.id,
		type: 'DELETE',
		success: function(result) {
			$('#userTable').bootstrapTable('removeByUniqueId', rowData.id)
			$('#deleteUserModal').modal('hide')
		}
	});
});

// Template for the action buttons (i.e. edit / delete user)
function actionFormatter(username) {
	return `
		<div class="btn-group btn-group-sm" role="group">
			<button type="button" class="btn btn-primary py-0" title="Edit" onclick="editUserModal(this)">
				<i class="bi-pencil-fill">&zwnj;</i>
			</button>
			${username == "admin" ? "" : `
				<button type="button" class="btn btn-danger py-0" title="Delete" onclick="deleteUserModal(this)">
					<i class="bi-trash">&zwnj;</i>
				</button>
			`}
		</div>
	`
}