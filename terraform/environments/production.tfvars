# Production Environment Configuration

project_id  = "gemini-prod-project"
region      = "us-central1"
environment = "production"

# GKE Configuration - Production scale
initial_node_count    = 5
min_node_count        = 3
max_node_count        = 20
node_machine_type     = "n2-standard-8"
use_preemptible_nodes = false  # Stability in production

# Database - Production tier
db_tier = "db-n1-standard-4"

# Redis - Production size
redis_memory_gb = 5

# Monitoring
alert_email = "sre-team@example.com"

# Features
enable_vertex_ai         = true
enable_private_cluster   = true  # Security in production
enable_autoscaling       = true
enable_workload_identity = true

# Backup
backup_retention_days = 30

# Network Security - Restrict in production
authorized_networks = [
  {
    name = "office"
    cidr = "203.0.113.0/24"  # Replace with actual office IP
  },
  {
    name = "vpn"
    cidr = "198.51.100.0/24"  # Replace with VPN range
  }
]

# Labels
labels = {
  project     = "gemini"
  environment = "production"
  managed-by  = "terraform"
  cost-center = "engineering"
  compliance  = "soc2"
}