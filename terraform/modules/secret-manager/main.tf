resource "google_secret_manager_secret" "postgres_url" {
    secret_id = "${var.environment}-postgres-url"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "postgres_url_access" {
    secret_id = google_secret_manager_secret.postgres_url.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "slack_bot_token" {
    secret_id = "${var.environment}-slack-bot-token"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "slack_bot_token_access" {
    secret_id = google_secret_manager_secret.slack_bot_token.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "slack_signing_secret" {
    secret_id = "${var.environment}-slack-signing-secret"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "slack_signing_secret_access" {
    secret_id = google_secret_manager_secret.slack_signing_secret.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "google_api_key" {
    secret_id = "${var.environment}-google-api-key"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "google_api_key_access" {
    secret_id = google_secret_manager_secret.google_api_key.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "google_cx_id" {
    secret_id = "${var.environment}-google-cx-id"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "google_cx_id_access" {
    secret_id = google_secret_manager_secret.google_cx_id.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "postgres_user" {
    secret_id = "${var.environment}-postgres-user"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "postgres_user" {
    secret_id = google_secret_manager_secret.postgres_user.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "postgres_password" {
    secret_id = "${var.environment}-postgres-password"

    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_iam_member" "postgres_password" {
    secret_id = google_secret_manager_secret.postgres_password.id
    role      = "roles/secretmanager.secretAccessor"
    member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "gdrive_sa_key" {
    secret_id = "${var.environment}-gdrive-sa-key"

    replication {
        auto {}
    }
}