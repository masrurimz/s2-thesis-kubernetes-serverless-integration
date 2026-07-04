# serverless/

Serverless infrastructure — Knative serving and cold-start activation.

## Why both knative and activator?

| Subdirectory | What it does | Tool |
|-------------|-------------|------|
| `knative/` | Deploys Knative Serving + Kourier networking | Knative (k8s manifests, docker-compose) |
| `activator/` | Pre-warms Knative services to reduce cold starts | Go application (k8s controller) |

**knative** is the **platform** — it installs the serverless runtime into the cluster.
**activator** is a **component** that runs on top of Knative — it watches for scale-to-zero services and triggers warm-up requests before traffic arrives.

Both are part of the serverless domain because the activator only makes sense when Knative is installed.

## Knative service configs

Files in `knative/`:
- `service.yaml` — Knative service definition for the test app
- `domain-mapping.yaml` — Custom domain mapping
- `docker-compose.yml` — Local docker-compose for Knative gateway
- `nginx-proxy.conf` / `nginx.conf` — Nginx reverse proxy configs

## Activator (Go application)

The activator is a standalone Go module with its own `go.mod`. It's built via `docker build` and deployed as a Kubernetes Deployment. It uses the Kubernetes API (client-go) to watch for pending Knative services.
