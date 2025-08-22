# Development Environment Configuration

project_id  = "gemini-dev-project"
region      = "us-central1"
environment = "dev"

# GKE Configuration - Smaller for dev
initial_node_count    = 2
min_node_count        = 1
max_node_count        = 5
node_machine_type     = "n2-standard-2"
use_preemptible_nodes = true  # Save costs in dev

# Database - Smaller tier for dev
db_tier = "db-f1-micro"

# Redis - Minimal size for dev
redis_memory_gb = 1

# Monitoring
alert_email = "dev-team@example.com"

# Features
enable_vertex_ai         = true
enable_private_cluster   = false  # Easier access in dev
enable_autoscaling       = true
enable_workload_identity = true

# Backup
backup_retention_days = 7  # Shorter retention in dev

# Labels
labels = {
  project     = "gemini"
  environment = "dev"
  managed-by  = "terraform"
  cost-center = "engineering"
}