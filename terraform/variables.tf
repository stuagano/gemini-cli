# Variables for Gemini Enterprise Architect Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production"
  }
}

# GKE Variables
variable "initial_node_count" {
  description = "Initial number of nodes in GKE cluster"
  type        = number
  default     = 3
}

variable "min_node_count" {
  description = "Minimum number of nodes for autoscaling"
  type        = number
  default     = 2
}

variable "max_node_count" {
  description = "Maximum number of nodes for autoscaling"
  type        = number
  default     = 10
}

variable "node_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "n2-standard-4"
}

variable "use_preemptible_nodes" {
  description = "Use preemptible nodes for cost savings"
  type        = bool
  default     = false
}

# Database Variables
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
  
  validation {
    condition = can(regex("^db-", var.db_tier))
    error_message = "Database tier must start with 'db-'"
  }
}

# Redis Variables
variable "redis_memory_gb" {
  description = "Redis instance memory size in GB"
  type        = number
  default     = 1
}

# Monitoring Variables
variable "alert_email" {
  description = "Email address for alerts"
  type        = string
}

# Vertex AI Variables
variable "enable_vertex_ai" {
  description = "Enable Vertex AI features"
  type        = bool
  default     = true
}

# Network Variables
variable "enable_private_cluster" {
  description = "Enable private GKE cluster"
  type        = bool
  default     = true
}

variable "authorized_networks" {
  description = "List of authorized networks for GKE master"
  type = list(object({
    name = string
    cidr = string
  }))
  default = [
    {
      name = "all"
      cidr = "0.0.0.0/0"
    }
  ]
}

# Cost Optimization Variables
variable "enable_autoscaling" {
  description = "Enable cluster autoscaling"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable Workload Identity for secure pod authentication"
  type        = bool
  default     = true
}

# Backup Variables
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

# Tags and Labels
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "gemini"
    managed-by  = "terraform"
    cost-center = "engineering"
  }
}

variable "tags" {
  description = "Network tags for resources"
  type        = list(string)
  default     = ["gemini", "agent-platform"]
}