resource "google_cloud_run_v2_service" "main" {
    name     = "${var.project_id}-${var.environment}-${var.service_name}-cloudrun"
    location = var.region
    deletion_protection = var.deletion_protection
    ingress = "INGRESS_TRAFFIC_ALL"

    template {
        service_account = var.service_account_email

        scaling {
            min_instance_count = var.min_instance_count
            max_instance_count = 5
        }

        vpc_access {
            network_interfaces {
                network    = var.vpc_id
                subnetwork = var.subnet_id
            }
            egress = "PRIVATE_RANGES_ONLY"
        }

        containers {
            image = var.image

            resources {
                limits = {
                    cpu    = var.cpu
                    memory = var.memory
                }
            }

            ports {
                container_port = var.port
            }

            env {
                name  = "POSTGRES_URL"
                value = var.postgres_url
            }

            env {
                name = "SLACK_BOT_TOKEN"
                value_source {
                    secret_key_ref {
                        secret  = var.slack_bot_token
                        version = "latest"
                    }
                }
            }

            env {
                name = "SLACK_SIGNING_SECRET"
                value_source {
                    secret_key_ref {
                        secret  = var.slack_signing_secret
                        version = "latest"
                    }
                }
            }

            env {
                name = "GOOGLE_API_KEY"
                value_source {
                    secret_key_ref {
                        secret  = var.google_api_key
                        version = "latest"
                    }
                }
            }

            env {
                name = "GOOGLE_CX"
                value_source {
                    secret_key_ref {
                        secret  = var.google_cx_id
                        version = "latest"
                    }
                }
            }
        }
    }
    lifecycle {
        ignore_changes = [
            template[0].containers[0].image,
            client,
            invoker_iam_disabled
        ]
    }
}