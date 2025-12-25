module "network" {
    source = "../../modules/network"
    project_id = local.project_id
    region = local.region
    environment = local.environment
    service_name = local.service_name
}

module "secret_manager" {
    source = "../../modules/secret-manager"
    region = local.region
    environment = local.environment
    service_account_email = local.service_account_email
}

module "repository" {
    source = "../../modules/repository"
    project_id = local.project_id
    region = local.region
    repository_id = "${local.service_name}-${local.environment}"
}

module "cloudrun" {
    source = "../../modules/cloudrun"
    project_id = local.project_id
    region = local.region
    environment = local.environment
    service_name = local.service_name
    service_account_email = local.service_account_email
    vpc_id = module.network.vpc_id
    subnet_id = module.network.subnet_id
    image = "${local.region}-docker.pkg.dev/${local.project_id}/${module.repository.repository_id}/${local.service_name}:latest"
    port = 8080
    memory = "2Gi"
    cpu = 1
    min_instance_count = 0
    slack_bot_token = module.secret_manager.slack_bot_token
    slack_signing_secret = module.secret_manager.slack_signing_secret
    google_api_key = module.secret_manager.google_api_key
    google_cx_id = module.secret_manager.google_cx_id
    postgres_url = "postgresql://${module.postgres.db_user}:${module.postgres.db_password}@${module.postgres.private_ip_address}:5432/${module.postgres.database_name}"
    deletion_protection = false
}

module "postgres" {
    source = "../../modules/postgres"
    project_id = local.project_id
    region = local.region
    environment = local.environment
    service_name = local.service_name
    vpc_id = module.network.vpc_id
    tier = "db-f1-micro"
    edition = "ENTERPRISE"
    db_user = module.secret_manager.postgres_user
    db_password = module.secret_manager.postgres_password
    deletion_protection = false
}