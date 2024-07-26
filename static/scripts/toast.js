function showToast(message) {
  const toastBody = document.getElementById('toastBody');
  toastBody.innerHTML = `<strong>${message}</strong>`;

  const toast = new bootstrap.Toast(document.getElementById('toast'));
  toast.show();
}