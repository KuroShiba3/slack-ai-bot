output "postgres_user" {
    description = "PostgreSQL User Secret ID"
    value       = google_secret_manager_secret.postgres_user.secret_id
}

output "postgres_password" {
    description = "PostgreSQL Password Secret ID"
    value       = google_secret_manager_secret.postgres_password.secret_id
}

output "slack_bot_token" {
    description = "Slack Bot TokennSecret ID"
    value       = google_secret_manager_secret.slack_bot_token.secret_id
}

output "slack_signing_secret" {
    description = "Slack Signing SecretnSecret ID"
    value       = google_secret_manager_secret.slack_signing_secret.secret_id
}

output "google_api_key" {
    description = "Google API KeynSecret ID"
    value       = google_secret_manager_secret.google_api_key.secret_id
}

output "google_cx_id" {
    description = "Tavily API KeynSecret ID"
    value       = google_secret_manager_secret.google_cx_id.secret_id
}

