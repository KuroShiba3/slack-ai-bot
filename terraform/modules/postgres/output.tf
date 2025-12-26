output "private_ip_address" {
  description = "PostgreSQL private IP address"
  value       = google_sql_database_instance.main.private_ip_address
}

output "db_name" {
  description = "Database name"
  value       = google_sql_database.main.name
}

output "db_user" {
  description = "Database user"
  value       = google_sql_user.main.name
}

output "db_password" {
  description = "Database password"
  value       = var.db_password
  sensitive   = true
}
