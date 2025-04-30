/**
 * EKS Cluster Configuration for PILT Dashboard
 * This module creates an EKS cluster with worker nodes and necessary IAM roles
 */

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 18.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # EKS Managed Node Group
  eks_managed_node_group_defaults = {
    ami_type               = "AL2_x86_64"
    disk_size              = 50
    instance_types         = ["t3.medium"]
    vpc_security_group_ids = [aws_security_group.eks_additional.id]
  }

  eks_managed_node_groups = {
    main = {
      min_size     = var.min_nodes
      max_size     = var.max_nodes
      desired_size = var.desired_nodes

      instance_types = var.node_instance_types
      capacity_type  = var.node_capacity_type

      labels = {
        Environment = var.environment
        App         = "pilt-dashboard"
      }

      tags = {
        Environment = var.environment
        Project     = var.project_name
        Terraform   = "true"
        ManagedBy   = "terraform"
      }
    }
  }

  # Fargate Profiles
  fargate_profiles = {
    default = {
      name = "default"
      selectors = [
        {
          namespace = "kube-system"
          labels = {
            k8s-app = "kube-dns"
          }
        },
        {
          namespace = "default"
        },
        {
          namespace = "pilt-dashboard"
        }
      ]

      tags = {
        Environment = var.environment
      }
    }
  }

  # OIDC Provider for IAM roles for service accounts
  cluster_identity_providers = {
    sts = {
      client_id = "sts.amazonaws.com"
    }
  }

  # Additional IAM roles that can access the EKS cluster
  manage_aws_auth_configmap = true
  aws_auth_roles = [
    {
      rolearn  = aws_iam_role.eks_admin.arn
      username = "eks-admin"
      groups   = ["system:masters"]
    }
  ]

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Terraform   = "true"
    ManagedBy   = "terraform"
  }
}

# Additional security group for EKS nodes
resource "aws_security_group" "eks_additional" {
  name        = "${var.cluster_name}-additional-sg"
  description = "Additional security group for EKS cluster nodes"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Allow node communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-additional-sg"
    Environment = var.environment
    Project     = var.project_name
    Terraform   = "true"
    ManagedBy   = "terraform"
  }
}

# IAM role for EKS admin access
resource "aws_iam_role" "eks_admin" {
  name = "${var.cluster_name}-admin-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
      },
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Terraform   = "true"
    ManagedBy   = "terraform"
  }
}

# IAM role for monitoring tools (Prometheus)
resource "aws_iam_role" "monitoring" {
  name = "${var.cluster_name}-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:monitoring:prometheus-server"
          }
        }
      },
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Terraform   = "true"
    ManagedBy   = "terraform"
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Outputs for use in other modules and for reference
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "eks_managed_node_groups" {
  description = "EKS managed node groups"
  value       = module.eks.eks_managed_node_groups
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = module.eks.oidc_provider_arn
}

output "monitoring_role_arn" {
  description = "ARN of IAM role for monitoring tools"
  value       = aws_iam_role.monitoring.arn
}