# Gemini Enterprise Architect - GCP Infrastructure
# Terraform configuration for complete cloud deployment

terraform {
  required_version = ">= 1.0"
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
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "gcs" {
    bucket = var.terraform_state_bucket
    prefix = "gemini-enterprise-architect"
  }
}

# Provider configurations
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth.0.cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.primary.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth.0.cluster_ca_certificate)
  }
}

# Data sources
data "google_client_config" "default" {}

data "google_project" "current" {
  project_id = var.project_id
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "container.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com"
  ])

  project                    = var.project_id
  service                    = each.value
  disable_dependent_services = false
  disable_on_destroy         = false
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.name_prefix}-vpc"
  auto_create_subnetworks = false
  mtu                     = 1460

  depends_on = [google_project_service.apis]
}

# Private subnet for GKE
resource "google_compute_subnetwork" "gke_subnet" {
  name          = "${var.name_prefix}-gke-subnet"
  ip_cidr_range = var.gke_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "gke-pod-range"
    ip_cidr_range = var.gke_pod_cidr
  }

  secondary_ip_range {
    range_name    = "gke-service-range"
    ip_cidr_range = var.gke_service_cidr
  }

  private_ip_google_access = true
}

# Cloud Router for NAT Gateway
resource "google_compute_router" "router" {
  name    = "${var.name_prefix}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

# NAT Gateway
resource "google_compute_router_nat" "nat" {
  name                               = "${var.name_prefix}-nat"
  router                            = google_compute_router.router.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = "${var.name_prefix}-gke"
  location = var.region

  # Network configuration
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.gke_subnet.name

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Networking
  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pod-range"
    services_secondary_range_name = "gke-service-range"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.gke_master_cidr
  }

  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Security settings
  enable_shielded_nodes = true
  
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Release channel
  release_channel {
    channel = "STABLE"
  }

  depends_on = [
    google_project_service.apis,
    google_compute_subnetwork.gke_subnet
  ]
}

# Primary node pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.name_prefix}-primary-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_num_nodes

  node_config {
    preemptible  = var.environment != "production"
    machine_type = var.gke_machine_type
    disk_size_gb = 50
    disk_type    = "pd-ssd"

    # Google recommends custom service accounts that have cloud-platform scope
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Shielded nodes
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    labels = {
      environment = var.environment
      team        = "gemini-enterprise"
    }

    tags = ["gke-node", "${var.name_prefix}-gke"]
  }

  # Auto-scaling
  autoscaling {
    min_node_count = var.gke_min_nodes
    max_node_count = var.gke_max_nodes
  }

  # Auto-upgrade and auto-repair
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Service account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "${var.name_prefix}-gke-nodes"
  display_name = "GKE Nodes Service Account"
}

resource "google_project_iam_member" "gke_nodes" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/storage.objectViewer",
    "roles/artifactregistry.reader"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "gemini_repo" {
  location      = var.region
  repository_id = "${var.name_prefix}-repo"
  description   = "Gemini Enterprise Architect container repository"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

# Cloud SQL instance for PostgreSQL
resource "google_sql_database_instance" "postgres" {
  name             = "${var.name_prefix}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_size

    backup_configuration {
      enabled    = true
      start_time = "03:00"
      location   = var.region
      
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]

  deletion_protection = var.environment == "production"
}

# Database
resource "google_sql_database" "gemini_db" {
  name     = "gemini_enterprise"
  instance = google_sql_database_instance.postgres.name
}

# Database user
resource "google_sql_user" "gemini_user" {
  name     = "gemini_app"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.name_prefix}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [google_project_service.apis]
}

# Redis instance for caching
resource "google_redis_instance" "cache" {
  name           = "${var.name_prefix}-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size
  region         = var.region

  authorized_network = google_compute_network.vpc.id
  redis_version      = "REDIS_7_0"

  auth_enabled = true
  
  depends_on = [google_project_service.apis]
}

# Vertex AI endpoint for Gemini models
resource "google_vertex_ai_endpoint" "gemini_endpoint" {
  name         = "${var.name_prefix}-gemini-endpoint"
  display_name = "Gemini Enterprise Architect Endpoint"
  description  = "Endpoint for Gemini model serving"
  location     = var.region

  depends_on = [google_project_service.apis]
}

# Service account for Vertex AI
resource "google_service_account" "vertex_ai" {
  account_id   = "${var.name_prefix}-vertex-ai"
  display_name = "Vertex AI Service Account"
}

resource "google_project_iam_member" "vertex_ai" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.vertex_ai.email}"
}

# Workload Identity binding for Vertex AI
resource "google_service_account_iam_member" "vertex_ai_workload_identity" {
  service_account_id = google_service_account.vertex_ai.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[gemini/vertex-ai]"
}

# Cloud Build trigger for CI/CD
resource "google_cloudbuild_trigger" "gemini_trigger" {
  name        = "${var.name_prefix}-build-trigger"
  description = "Trigger for Gemini Enterprise Architect builds"
  
  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gemini_repo.repository_id}/gemini-agent:$COMMIT_SHA",
        "."
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gemini_repo.repository_id}/gemini-agent:$COMMIT_SHA"
      ]
    }

    step {
      name = "gcr.io/cloud-builders/gke-deploy"
      args = [
        "run",
        "--filename=k8s/",
        "--image=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gemini_repo.repository_id}/gemini-agent:$COMMIT_SHA",
        "--location=${var.region}",
        "--cluster=${google_container_cluster.primary.name}"
      ]
    }
  }

  depends_on = [google_project_service.apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.name_prefix}-db-password"
  
  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "${var.name_prefix}-redis-auth"
  
  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "redis_auth" {
  secret      = google_secret_manager_secret.redis_auth.id
  secret_data = google_redis_instance.cache.auth_string
}

# Monitoring - Log sink for DORA metrics
resource "google_logging_project_sink" "dora_metrics" {
  name = "${var.name_prefix}-dora-metrics-sink"

  destination = "pubsub.googleapis.com/projects/${var.project_id}/topics/${google_pubsub_topic.dora_metrics.name}"

  filter = <<EOF
resource.type="k8s_container"
resource.labels.cluster_name="${google_container_cluster.primary.name}"
jsonPayload.message=~"DEPLOYMENT|INCIDENT|LEAD_TIME"
EOF

  unique_writer_identity = true

  depends_on = [google_project_service.apis]
}

# Pub/Sub topic for DORA metrics
resource "google_pubsub_topic" "dora_metrics" {
  name = "${var.name_prefix}-dora-metrics"

  depends_on = [google_project_service.apis]
}

# Cloud Function for processing DORA metrics
resource "google_storage_bucket" "function_source" {
  name     = "${var.project_id}-${var.name_prefix}-functions"
  location = var.region
}

resource "google_storage_bucket_object" "dora_processor_zip" {
  name   = "dora-processor.zip"
  bucket = google_storage_bucket.function_source.name
  source = "${path.module}/functions/dora-processor.zip"
}

resource "google_cloudfunctions2_function" "dora_processor" {
  name        = "${var.name_prefix}-dora-processor"
  location    = var.region
  description = "Process DORA metrics from logs"

  build_config {
    runtime     = "python39"
    entry_point = "process_dora_metrics"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.dora_processor_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "256M"
    timeout_seconds    = 60

    environment_variables = {
      PROJECT_ID = var.project_id
      REGION     = var.region
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.dora_metrics.id
  }

  depends_on = [google_project_service.apis]
}