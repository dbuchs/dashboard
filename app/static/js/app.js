// HTMX configuration for CSRF
document.addEventListener("DOMContentLoaded", function() {
  document.body.addEventListener("htmx:configRequest", function(evt) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
      evt.detail.headers["X-CSRFToken"] = csrfToken.content;
    }
  });
});
