module "network" {
    source = "../../modules/network"
    project_id = var.project_id
    region = var.region
    environment = var.environment
    service_name = var.service_name
}

module "secret_manager" {
    source = "../../modules/secret-manager"
    region = var.region
    environment = var.environment
    service_account_email = var.service_account_email
}

module "repository" {
    source = "../../modules/repository"
    project_id = var.project_id
    region = var.region
    repository_id = "${var.service_name}-${var.environment}"
}

module "cloudrun" {
    source = "../../modules/cloudrun"
    project_id = var.project_id
    region = var.region
    environment = var.environment
    service_name = var.service_name
    service_account_email = var.service_account_email
    vpc_id = module.network.vpc_id
    subnet_id = module.network.subnet_id
    image = "${var.region}-docker.pkg.dev/${var.project_id}/${module.repository.repository_id}/${var.service_name}:latest"
    port = 8080
    memory = "2Gi"
    cpu = 1
    min_instance_count = 0
    max_instance_count = 1
    deletion_protection = false
    postgres_url = "postgresql://${module.secret_manager.postgres_user}:${module.secret_manager.postgres_password}@${module.postgres.private_ip_address}:5432/${module.postgres.db_name}"
    slack_bot_token = module.secret_manager.slack_bot_token
    slack_signing_secret = module.secret_manager.slack_signing_secret
    google_api_key = module.secret_manager.google_api_key
    google_cx_id = module.secret_manager.google_cx_id
}

module "postgres" {
    source = "../../modules/postgres"
    project_id = var.project_id
    region = var.region
    environment = var.environment
    service_name = var.service_name
    vpc_id = module.network.vpc_id
    tier = "db-f1-micro"
    edition = "ENTERPRISE"
    db_user = module.secret_manager.postgres_user
    db_password = module.secret_manager.postgres_password
    db_name = "slackaibot"
    deletion_protection = false
}