output "repository_id" {
    description = "Artifact RegistryのリポジトリID"
    value       = google_artifact_registry_repository.main.repository_id
}