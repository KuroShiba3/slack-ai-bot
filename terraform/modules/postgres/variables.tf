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
    description = "サービス名"
    type        = string
}


variable "vpc_id" {
  description = "VPCネットワークのID"
  type        = string
}

variable "tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_user" {
  description = "Database user"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "deletion_protection" {
    description = "Cloud Runサービスの削除保護設定"
    type        = bool
}

variable "edition" {
    description = "Cloud SQL edition (ENTERPRISE_PLUS, ENTERPRISE, or omit for Standard)"
    type        = string
    default     = null
}
