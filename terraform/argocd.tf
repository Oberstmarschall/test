resource "helm_release" "argocd" {
  name = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart = "argo-cd"
  version = "8.2.6"

  namespace = "argocd"
  create_namespace = "true"
  verify = false

  values = [
    file("argo-values.yaml")
  ]
}

resource "kubernetes_manifest" "argocd" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name      = "my-proj"
      namespace = "argocd"
    }
    spec = {
      project = "default"

      source = {
        repoURL        = "https://github.com/Oberstmarschall/test.git"
        targetRevision = "main"
        path           = "envs/default/apps"
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "my-proj"
      }
      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = false
        }
      }
    }
  }

  field_manager {
    name            = "terraform"
    force_conflicts = true
  }

  depends_on = [helm_release.argocd]
}

# resource "argocd_application" "argocd" {
#   depends_on = [ helm_release.argocd ]

#   metadata {
#     name      = "argocd"
#     namespace = "argocd"
#   }
#   wait    = true
#   spec {
#     project = "default"

#     destination {
#       server    = "https://kubernetes.default.svc"
#       namespace = "argocd"
#     }

#     source {
#       repo_url        = "https://github.com/Oberstmarschall/test"
#       path            = "envs/default"
#       target_revision = "main"
#     }

#     # sync_policy {
#     #   automated {
#     #     prune       = true
#     #     self_heal   = true
#     #     allow_empty = true
#     #   }
#     #   # Only available from ArgoCD 1.5.0 onwards
#     #   sync_options = ["Validate=false"]
#     #   retry {
#     #     limit = "5"
#     #     backoff {
#     #       duration     = "30s"
#     #       max_duration = "2m"
#     #       factor       = "2"
#     #     }
#     #   }
#     # }

#   }
# }
