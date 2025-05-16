terraform {
  required_version = ">= 1.4"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Networking & Compute ───────────────────────────────────
resource "aws_lightsail_static_ip" "ip" {
  name = "${var.instance_name}-ip"
}

resource "aws_lightsail_instance" "app" {
  name              = var.instance_name
  availability_zone = "${var.aws_region}a"
  blueprint_id      = var.blueprint_id # Ubuntu 22.04 LTS
  bundle_id         = var.bundle_id    # 512 MB / 1 vCPU plan (nano_2_0)

  # SSH key‑pair name (optional). If blank Lightsail auto‑generates one.
  key_pair_name = var.key_pair_name == "" ? null : var.key_pair_name

  user_data = templatefile("${path.module}/user_data.sh", {
    github_repo = var.github_repo,
    domain_name = var.domain_name,
    app_port    = var.app_port,
    GITHUB_REPO = var.github_repo,
    DOMAIN_NAME = var.domain_name,
    APP_PORT    = var.app_port
  })
}

resource "aws_lightsail_static_ip_attachment" "attach" {
  static_ip_name = aws_lightsail_static_ip.ip.name
  instance_name  = aws_lightsail_instance.app.name
}


resource "aws_lightsail_instance_public_ports" "web" {
  instance_name = aws_lightsail_instance.app.name

  port_info {
    protocol  = "tcp"
    from_port = 22
    to_port   = 22
  }

  port_info {
    protocol  = "tcp"
    from_port = var.app_port
    to_port   = var.app_port
  }

  port_info {
    protocol  = "tcp"
    from_port = 443
    to_port   = 443
  }
}

# ── Outputs ────────────────────────────────────────────────
output "app_public_ip" {
  description = "Public IP address of the Streamlit app"
  value       = aws_lightsail_static_ip.ip.ip_address
}
