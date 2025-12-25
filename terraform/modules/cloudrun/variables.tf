variable "project_id" {
    description = "プロジェクトID"
    type        = string
}

variable "region" {
    description = "リージョン名"
    type        = string
}

variable "environment" {
    description = "環境名"
    type        = string
}

variable "service_name" {
    description = "Cloud Runサービス名"
    type        = string
}

variable "service_account_email" {
    description = "サービスアカウント名"
    type        = string
}

variable "vpc_id" {
    description = "VPCネットワークのID"
    type        = string
}

variable "subnet_id" {
    description = "サブネットのID"
    type        = string
}

variable "image" {
    description = "Cloud Runで使用するコンテナイメージ"
    type        = string
}

variable "port" {
    description = "Cloud Runコンテナのポート番号"
    type        = number
}

variable "memory" {
    description = "Memory limit"
    type        = string
}

variable "cpu" {
    description = "CPU limit"
    type        = string
}

variable "slack_bot_token" {
    description = "Slack Bot TokenのSecret ID"
    type        = string
}

variable "slack_signing_secret" {
    description = "Slack Signing SecretのSecret ID"
    type        = string
}

variable "google_api_key" {
    description = "Google API KeyのSecret ID"
    type        = string
}

variable "google_cx_id" {
    description = "Google CX IDのSecret ID"
    type        = string
}

variable "postgres_url" {
    description = "PostgreSQL connection URL"
    type        = string
}

variable "deletion_protection" {
    description = "Cloud Runサービスの削除保護設定"
    type        = bool
}

variable "min_instance_count" {
    description = "Minimum number of instances"
    type        = number
    default     = 1
}