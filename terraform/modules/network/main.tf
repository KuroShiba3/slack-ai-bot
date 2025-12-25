resource "google_compute_network" "main" {
    name     = "${var.project_id}-${var.environment}-${var.service_name}-vpc"
    auto_create_subnetworks = false
    mtu                     = 1460
}

resource "google_compute_subnetwork" "main" {
    name   = "${var.project_id}-${var.environment}-${var.service_name}-subnet"
    region = var.region

    ip_cidr_range = "10.0.0.0/24"
    network       = google_compute_network.main.id
}

resource "google_compute_global_address" "private_ip_range" {
    name          = "${var.project_id}-${var.environment}-${var.service_name}-private-ip-range"
    purpose       = "VPC_PEERING"
    address_type  = "INTERNAL"
    prefix_length = 24
    address       = "10.1.0.0"
    network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
    network                 = google_compute_network.main.id
    service                 = "servicenetworking.googleapis.com"
    reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}