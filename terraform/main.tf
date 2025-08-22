# Gemini Enterprise Architect - GCP Infrastructure
# Main Terraform configuration for deploying to Google Cloud Platform

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  
  backend "gcs" {
    bucket = "gemini-terraform-state"
    prefix = "terraform/state"
  }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Data sources
data "google_client_config" "default" {}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "cloudrun.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "storage-api.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtrace.googleapis.com"
  ])
  
  service = each.key
  
  disable_on_destroy = false
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "gemini_registry" {
  location      = var.region
  repository_id = "gemini-containers"
  description   = "Container registry for Gemini agents"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# VPC Network
resource "google_compute_network" "gemini_network" {
  name                    = "gemini-network"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

# Subnet for GKE
resource "google_compute_subnetwork" "gemini_subnet" {
  name          = "gemini-subnet"
  network       = google_compute_network.gemini_network.id
  region        = var.region
  ip_cidr_range = "10.0.0.0/16"
  
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }
  
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
  
  private_ip_google_access = true
}

# GKE Cluster for agent services
resource "google_container_cluster" "gemini_cluster" {
  name     = "gemini-cluster"
  location = var.region
  
  # Use release channel for automatic updates
  release_channel {
    channel = "STABLE"
  }
  
  # Network configuration
  network    = google_compute_network.gemini_network.name
  subnetwork = google_compute_subnetwork.gemini_subnet.name
  
  # IP allocation
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  
  # Initial node pool (will be removed after cluster creation)
  initial_node_count       = 1
  remove_default_node_pool = true
  
  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Monitoring and logging
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
    
    managed_prometheus {
      enabled = true
    }
  }
  
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }
  
  # Add-ons
  addons_config {
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
    
    network_policy_config {
      disabled = false
    }
    
    horizontal_pod_autoscaling {
      disabled = false
    }
  }
  
  # Security
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
  
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"  # Restrict in production
      display_name = "all"
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Node pool for agent workloads
resource "google_container_node_pool" "agent_nodes" {
  name       = "agent-node-pool"
  cluster    = google_container_cluster.gemini_cluster.id
  node_count = var.initial_node_count
  
  # Autoscaling
  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }
  
  # Node configuration
  node_config {
    preemptible  = var.use_preemptible_nodes
    machine_type = var.node_machine_type
    
    disk_size_gb = 100
    disk_type    = "pd-standard"
    
    # Service account
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    # Labels
    labels = {
      environment = var.environment
      team        = "platform"
    }
    
    # Taints for agent-specific nodes
    taint {
      key    = "agent-workload"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
  
  # Management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Service account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "gemini-gke-nodes"
  display_name = "Gemini GKE Nodes Service Account"
}

# IAM roles for GKE nodes
resource "google_project_iam_member" "gke_nodes_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/artifactregistry.reader"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# Cloud SQL for persistent data
resource "google_sql_database_instance" "gemini_db" {
  name             = "gemini-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = var.db_tier
    
    disk_size       = 100
    disk_type       = "PD_SSD"
    disk_autoresize = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      
      backup_retention_settings {
        retained_backups = 30
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.gemini_network.id
    }
    
    database_flags {
      name  = "max_connections"
      value = "1000"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  deletion_protection = var.environment == "production"
  
  depends_on = [google_project_service.required_apis]
}

# Cloud SQL databases
resource "google_sql_database" "gemini_databases" {
  for_each = toset(["agents", "knowledge", "metrics"])
  
  name     = each.key
  instance = google_sql_database_instance.gemini_db.name
}

# Redis for caching
resource "google_redis_instance" "gemini_cache" {
  name           = "gemini-cache-${var.environment}"
  tier           = "STANDARD_HA"
  memory_size_gb = var.redis_memory_gb
  region         = var.region
  
  authorized_network = google_compute_network.gemini_network.id
  
  redis_version = "REDIS_7_0"
  
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }
  
  depends_on = [google_project_service.required_apis]
}

# Storage buckets
resource "google_storage_bucket" "gemini_buckets" {
  for_each = {
    artifacts = "gemini-artifacts-${var.project_id}"
    knowledge = "gemini-knowledge-${var.project_id}"
    backups   = "gemini-backups-${var.project_id}"
  }
  
  name     = each.value
  location = var.region
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Vertex AI configuration
resource "google_vertex_ai_endpoint" "gemini_endpoint" {
  name         = "gemini-endpoint"
  display_name = "Gemini AI Endpoint"
  location     = var.region
  
  depends_on = [google_project_service.required_apis]
}

# Secret Manager for sensitive data
resource "google_secret_manager_secret" "api_keys" {
  for_each = toset([
    "openai-api-key",
    "anthropic-api-key",
    "github-token",
    "slack-webhook"
  ])
  
  secret_id = each.key
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

# Monitoring workspace
resource "google_monitoring_dashboard" "gemini_dashboard" {
  dashboard_json = file("${path.module}/dashboards/main.json")
  
  depends_on = [google_project_service.required_apis]
}

# Alert policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate above 5%"
    
    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND metric.type=\"logging.googleapis.com/user/error_rate\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  depends_on = [google_project_service.required_apis]
}

# Notification channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notifications"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
  
  depends_on = [google_project_service.required_apis]
}

# Outputs
output "cluster_endpoint" {
  value       = google_container_cluster.gemini_cluster.endpoint
  description = "GKE cluster endpoint"
  sensitive   = true
}

output "database_connection" {
  value       = google_sql_database_instance.gemini_db.connection_name
  description = "Cloud SQL connection name"
}

output "redis_host" {
  value       = google_redis_instance.gemini_cache.host
  description = "Redis instance host"
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gemini_registry.repository_id}"
  description = "Artifact Registry URL for container images"
}