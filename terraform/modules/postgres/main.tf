resource "google_sql_database_instance" "main" {
  name             = "${var.project_id}-${var.environment}-${var.service_name}-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  deletion_protection = var.deletion_protection

  settings {
    tier = var.tier
    edition = var.edition

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.vpc_id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled = true
      start_time = "03:00"
    }
  }
}

resource "google_sql_database" "main" {
  name     = "slackaibot"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "main" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = var.db_password
}
