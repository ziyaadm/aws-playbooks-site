# variables.tf

variable "project_name" {
  description = "Name of the project (used in resource names)"
  type        = string
}

variable "owner_name" {
  description = "Your name or identifier for uniqueness (e.g., ziyaadm)"
  type        = string
}

variable "domain_name" {
  description = "Root domain name (e.g., ziyaadm.com)"
  type        = string
}

variable "subdomain" {
  description = "Subdomain to use (e.g., playbooks)"
  type        = string
}

variable "region" {
  description = "AWS region to deploy in (excluding us-east-1 for ACM)"
  type        = string
  default     = "us-east-2"
}
