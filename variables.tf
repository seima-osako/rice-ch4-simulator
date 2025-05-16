variable "app_port" {
  description = "Port on which Streamlit listens (default 8501)"
  type        = number
  default     = 8501
}

variable "aws_region" {
  description = "AWS region for Lightsail"
  type        = string
  default     = "us-east-1"
}

variable "blueprint_id" {
  description = "Lightsail blueprint (OS) ID"
  type        = string
  default     = "ubuntu_22_04"
}

variable "bundle_id" {
  description = "Lightsail bundle ID (size). 512 MB plan = nano_2_0"
  type        = string
  default     = "nano_2_0"
}

variable "domain_name" {
  description = <<EOT
FQDN for TLS/HTTPS (Let’s Encrypt). Leave empty to skip Nginx/Certbot and serve plain HTTP.
EOT
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "Git repository URL to deploy"
  type        = string
  default     = "https://github.com/seima-osako/rice-ch4-simulator.git"
}

variable "instance_name" {
  description = "Lightsail instance name"
  type        = string
  default     = "rice-ch4-simulator"
}

variable "key_pair_name" {
  description = "Existing Lightsail/EC2 key pair for SSH (optional)"
  type        = string
  default     = ""
}
