# Terraform Outputs for Gemini Enterprise Architect GCP Infrastructure

# Cluster information
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth.0.cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "GKE cluster location"
  value       = google_container_cluster.primary.location
}

# Network information
output "vpc_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "GKE subnet name"
  value       = google_compute_subnetwork.gke_subnet.name
}

output "subnet_cidr" {
  description = "GKE subnet CIDR"
  value       = google_compute_subnetwork.gke_subnet.ip_cidr_range
}

# Database information
output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.gemini_db.name
}

output "database_username" {
  description = "Database username"
  value       = google_sql_user.gemini_user.name
}

# Redis information
output "redis_instance_name" {
  description = "Redis instance name"
  value       = google_redis_instance.cache.name
}

output "redis_host" {
  description = "Redis host IP"
  value       = google_redis_instance.cache.host
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = google_redis_instance.cache.port
}

output "redis_auth_string" {
  description = "Redis AUTH string"
  value       = google_redis_instance.cache.auth_string
  sensitive   = true
}

# Artifact Registry
output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.gemini_repo.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gemini_repo.repository_id}"
}

# Vertex AI
output "vertex_ai_endpoint_name" {
  description = "Vertex AI endpoint name"
  value       = google_vertex_ai_endpoint.gemini_endpoint.name
}

output "vertex_ai_endpoint_id" {
  description = "Vertex AI endpoint ID"
  value       = google_vertex_ai_endpoint.gemini_endpoint.id
}

# Service Accounts
output "gke_service_account_email" {
  description = "GKE nodes service account email"
  value       = google_service_account.gke_nodes.email
}

output "vertex_ai_service_account_email" {
  description = "Vertex AI service account email"
  value       = google_service_account.vertex_ai.email
}

# Cloud Build
output "cloudbuild_trigger_name" {
  description = "Cloud Build trigger name"
  value       = google_cloudbuild_trigger.gemini_trigger.name
}

# Secret Manager
output "secret_names" {
  description = "Secret Manager secret names"
  value = {
    db_password = google_secret_manager_secret.db_password.secret_id
    redis_auth  = google_secret_manager_secret.redis_auth.secret_id
  }
}

# Monitoring
output "dora_metrics_topic" {
  description = "Pub/Sub topic for DORA metrics"
  value       = google_pubsub_topic.dora_metrics.name
}

output "dora_processor_function" {
  description = "Cloud Function for DORA metrics processing"
  value       = google_cloudfunctions2_function.dora_processor.name
}

# kubectl commands
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}

# Environment configuration
output "environment_config" {
  description = "Environment configuration for applications"
  value = {
    project_id                 = var.project_id
    region                    = var.region
    cluster_name              = google_container_cluster.primary.name
    database_connection_name  = google_sql_database_instance.postgres.connection_name
    redis_host               = google_redis_instance.cache.host
    redis_port               = google_redis_instance.cache.port
    artifact_registry_url    = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gemini_repo.repository_id}"
    vertex_ai_endpoint       = google_vertex_ai_endpoint.gemini_endpoint.name
  }
  sensitive = true
}

# Deployment URLs (to be used after k8s deployment)
output "deployment_urls" {
  description = "Application deployment URLs"
  value = {
    agent_server = "https://gemini-agent.${var.project_id}.run.app"
    dashboard    = "https://gemini-dashboard.${var.project_id}.run.app"
    api_docs     = "https://gemini-agent.${var.project_id}.run.app/docs"
  }
}

# Cost estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost (USD) - rough approximation"
  value = {
    gke_cluster = "~$200-400 (depends on usage)"
    cloud_sql   = "~$30-100 (depends on tier)"
    redis       = "~$25-50 (depends on memory)"
    total       = "~$255-550 per month"
    note        = "Actual costs may vary based on usage, data transfer, and other factors"
  }
}