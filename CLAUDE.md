# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Kubernetes & Serverless Integration research project that demonstrates multi-cluster Kubernetes environments using k3d with incremental Rust application development, PostgreSQL/MinIO integration, Prometheus monitoring, HAProxy traffic management, and Knative serverless integration.

### Architecture

The project implements a 3-cluster architecture:

- **Cluster A**: Main Rust application deployment with HAProxy traffic controller
- **Cluster B**: Backend services (PostgreSQL database, MinIO object storage)
- **Cluster C**: Serverless backup using Knative for traffic overflow

### Key Components

- **Rust Applications**: Incremental versions (v1-basic → v5-full-app) using actix-web framework
- **Traffic Controller**: Python-based LSTM controller for intelligent traffic routing
- **Autoscaling Experiments**: Multiple autoscaling strategies and implementations
- **Infrastructure Scripts**: Automated cluster setup, deployment, and teardown

## Development Commands

### Rust Applications

The project contains multiple Rust app versions in `apps/rust-app/`:

```bash
# Build Rust applications
cd apps/rust-app/v1-basic && cargo build --release
cd apps/rust-app/v2-prometheus && cargo build --release

# Run locally
cd apps/rust-app/v1-basic && cargo run
cd apps/rust-app/v2-prometheus && cargo run

# Test Rust code
cargo test

# Check Rust code
cargo check
cargo clippy
```

### Infrastructure Management

```bash
# Set up all clusters
./infra/setup-clusters.sh

# Deploy applications to clusters
./infra/deploy-applications.sh

# Tear down all clusters
./infra/teardown-clusters.sh
```

### Kubernetes Operations

```bash
# Switch between cluster contexts
kubectl config use-context k3d-cluster-a
kubectl config use-context k3d-cluster-b
kubectl config use-context k3d-cluster-c

# Apply configurations to specific clusters
kubectl apply -f cluster-configs/cluster-a/ --context k3d-cluster-a
kubectl apply -f cluster-configs/cluster-b/ --context k3d-cluster-b
kubectl apply -f cluster-configs/cluster-c/ --context k3d-cluster-c

# Check cluster status
kubectl get nodes --context k3d-cluster-a
kubectl get pods --all-namespaces --context k3d-cluster-a
```

### Docker Operations

```bash
# Build Rust app images
docker build -t rust-app:v1 apps/rust-app/v1-basic/
docker build -t rust-app:v2 apps/rust-app/v2-prometheus/

# Build controller image
docker build -t traffic-controller controller/
```

## Code Structure

### Rust Applications Evolution

- `apps/rust-app/v1-basic/`: Basic HTTP server with actix-web
- `apps/rust-app/v2-prometheus/`: Adds Prometheus metrics integration
- `apps/rust-app/v3-file-upload/`: Adds file upload to MinIO
- `apps/rust-app/v4-db-integration/`: Adds PostgreSQL database integration
- `apps/rust-app/v5-full-app/`: Complete application with all features

### Infrastructure Components

- `cluster-configs/`: Kubernetes manifests for each cluster
- `controller/`: Python-based LSTM traffic prediction controller
- `infra/`: Shell scripts for infrastructure automation
- `autoscaler/`: Various autoscaling experiments and implementations
- `monitoring/`: Prometheus monitoring configurations

### Dependencies

- **Rust**: actix-web framework for HTTP servers
- **Python**: LSTM model dependencies in controller/requirements.txt
- **Kubernetes**: k3d for local cluster management
- **Monitoring**: Prometheus for metrics collection

## Development Workflow

1. **Start clusters**: `./infra/setup-clusters.sh`
2. **Build Rust apps**: Navigate to version directory and run `cargo build --release`
3. **Build Docker images**: Use appropriate Dockerfiles in each app version
4. **Deploy to clusters**: `./infra/deploy-applications.sh` or manual kubectl apply
5. **Monitor**: Access Prometheus metrics and check application logs
6. **Test autoscaling**: Use load testing tools against deployed applications
7. **Cleanup**: `./infra/teardown-clusters.sh`

## Important Notes

- All Rust applications use actix-web framework with specific optimization profiles
- Infrastructure scripts handle k3d cluster lifecycle management
- Multiple autoscaling experiments are available in the autoscaler/ directory
- The project simulates real-world Kubernetes environments with resource constraints
- Traffic routing between clusters is handled by HAProxy with LSTM-based intelligence
