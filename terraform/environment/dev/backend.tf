terraform {
    backend "gcs" {
        bucket = "slackbotai-terraform-state"
    }
}