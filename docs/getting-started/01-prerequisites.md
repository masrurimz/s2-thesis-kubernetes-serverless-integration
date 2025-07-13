# Prerequisites Installation

This guide explains how to install the necessary tools to run the Kubernetes cluster simulation on both macOS and Linux.

## System Requirements

### Minimum Hardware Requirements

**Full Development Environment:**

- **CPU**: 4+ cores (8+ cores recommended)
- **RAM**: 16GB (32GB recommended)
- **Storage**: 50GB available space
- **Network**: Stable internet connection for container images

**Resource-Constrained Testing Environment:**

- **CPU**: 2+ cores (4+ cores recommended)
- **RAM**: 8GB total (6GB usable for testing)
- **Storage**: 20GB available space
- **Note**: Suitable for basic testing and development

### Resource Allocation for Testing

If you have limited resources (like 8GB usable RAM), use these constrained configurations:

**Sprint 1 - Basic Hybrid (Resource-Constrained):**

```yaml
# k3s cluster: 2GB RAM, 1 CPU
# Serverless simulation: 1GB RAM, 0.5 CPU
# HAProxy: 512MB RAM, 0.25 CPU
# Prometheus: 1GB RAM, 0.25 CPU
# Total: ~4.5GB RAM, 2 CPU cores
```

**Sprint 2-3 - With Prediction (Resource-Constrained):**

```yaml
# Add InfluxDB: 1GB RAM, 0.25 CPU
# Add Python services: 1GB RAM, 0.5 CPU
# Total: ~6.5GB RAM, 2.75 CPU cores
```

**Sprint 4-5 - Full ML System (Requires Full Resources):**

```yaml
# GRU model training requires: 8GB+ RAM, 4+ CPU cores
# Real dataset processing: 4GB+ RAM
# Recommendation: Use cloud instance or upgrade hardware
```

### Docker Resource Configuration

For resource-constrained environments, configure Docker limits:

**macOS Docker Desktop:**

1. Open Docker Desktop → Settings → Resources
2. Set Memory: 6GB (leave 2GB for system)
3. Set CPUs: 4 (or available cores - 1)
4. Set Swap: 2GB

**Linux Docker:**

```bash
# Add to /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {"hard": -1, "soft": -1},
    "nofile": {"hard": 65536, "soft": 65536}
  },
  "default-runtime": "runc"
}
```

### Performance Expectations by Hardware

**8GB RAM Configuration:**

- Sprint 1-2: Full functionality
- Sprint 3: Good performance with monitoring
- Sprint 4-5: Limited to small datasets, consider cloud for training

**16GB+ RAM Configuration:**

- All sprints: Full functionality
- Real dataset processing: Supported
- GRU model training: Supported

**32GB+ RAM Configuration:**

- Optimal performance for all components
- Multiple environment testing
- Large dataset processing

## macOS Installation

### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Docker

```bash
brew install --cask docker
```

After installation, open Docker from the Applications folder.

### 3. Install kubectl

```bash
brew install kubectl
```

### 4. Install k3d

```bash
brew install k3d
```

### 5. Install Helm

```bash
brew install helm
```

### 6. Install Rust (via rustup)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Verify installations:

```bash
docker --version
kubectl version --client
k3d version
helm version
rustc --version
cargo --version
```

## Linux Installation

### 1. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

### 2. Install kubectl

```bash
sudo apt-get update && sudo apt-get install -y apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
```

### 3. Install k3d

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

### 4. Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 5. Install Rust (via rustup)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Verify installations:

```bash
docker --version
kubectl version --client
k3d version
helm version
rustc --version
cargo --version
```
