output "vpc_id" {
    description = "VPCネットワークのID"
    value       = google_compute_network.main.id
}

output "subnet_id" {
    description = "サブネットのID"
    value       = google_compute_subnetwork.main.id
}