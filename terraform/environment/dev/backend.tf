terraform {
    backend "gcs" {
        bucket = "slackaibot-terraform-state"
    }
}