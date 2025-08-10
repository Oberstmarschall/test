terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.16.1"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.8.0"
    }

    argocd = {
        source = "argoproj-labs/argocd"
        version = "7.10.0"
    }
  }
}

provider "kubernetes" {
  config_path           = "C:/Users/VHoncharenko/.kube/config"
  config_context        = "docker-desktop"
}

provider "helm" {
  kubernetes {
    config_path           = "C:/Users/VHoncharenko/.kube/config"
    config_context        = "docker-desktop"
  }
}

provider "argocd" {
  server_addr = "localhost:30080"
  username    = "admin"
  password    = "1234"
  insecure    = true
  plain_text = true
}
