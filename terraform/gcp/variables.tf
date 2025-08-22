# Terraform Variables for Gemini Enterprise Architect GCP Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "gemini-enterprise"
}

variable "terraform_state_bucket" {
  description = "GCS bucket for Terraform state"
  type        = string
}

# Network variables
variable "gke_subnet_cidr" {
  description = "CIDR range for GKE subnet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "gke_pod_cidr" {
  description = "CIDR range for GKE pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "gke_service_cidr" {
  description = "CIDR range for GKE services"
  type        = string
  default     = "10.2.0.0/16"
}

variable "gke_master_cidr" {
  description = "CIDR range for GKE master"
  type        = string
  default     = "10.3.0.0/28"
}

# GKE variables
variable "gke_num_nodes" {
  description = "Number of GKE nodes per zone"
  type        = number
  default     = 2
}

variable "gke_min_nodes" {
  description = "Minimum number of GKE nodes"
  type        = number
  default     = 1
}

variable "gke_max_nodes" {
  description = "Maximum number of GKE nodes"
  type        = number
  default     = 10
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

# Database variables
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 20
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Redis variables
variable "redis_tier" {
  description = "Redis instance tier"
  type        = string
  default     = "BASIC"
}

variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# GitHub variables for CI/CD
variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "your-github-username"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "gemini-cli"
}

# Vertex AI variables
variable "vertex_ai_region" {
  description = "Vertex AI region (may differ from main region)"
  type        = string
  default     = "us-central1"
}

variable "gemini_model_name" {
  description = "Gemini model name for Vertex AI"
  type        = string
  default     = "gemini-1.5-pro"
}

# Monitoring variables
variable "enable_monitoring" {
  description = "Enable advanced monitoring and logging"
  type        = bool
  default     = true
}

variable "enable_dora_metrics" {
  description = "Enable DORA metrics collection"
  type        = bool
  default     = true
}

# Security variables
variable "enable_workload_identity" {
  description = "Enable Workload Identity for secure service account access"
  type        = bool
  default     = true
}

variable "enable_private_cluster" {
  description = "Enable private GKE cluster"
  type        = bool
  default     = true
}

variable "enable_network_policy" {
  description = "Enable Kubernetes network policies"
  type        = bool
  default     = true
}

# Resource labels
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "gemini-enterprise-architect"
    managed_by  = "terraform"
    team        = "platform"
  }
}

# Cost optimization
variable "enable_preemptible_nodes" {
  description = "Use preemptible nodes for cost optimization (not for production)"
  type        = bool
  default     = false
}

variable "enable_auto_scaling" {
  description = "Enable cluster auto-scaling"
  type        = bool
  default     = true
}

variable "enable_auto_upgrade" {
  description = "Enable automatic node upgrades"
  type        = bool
  default     = true
}