# Kubernetes & Serverless Integration

This guide will walk you through the process of setting up a multi-cluster Kubernetes environment using k3d, building a Rust app incrementally, and deploying services like PostgreSQL and MinIO. It will also cover monitoring with Prometheus, traffic management with HAProxy, and serverless integration using Knative.

### **Table of Contents**

- [Kubernetes \& Serverless Integration](#kubernetes--serverless-integration)
  - [**Table of Contents**](#table-of-contents)
  - [Repo Structure](#repo-structure)
    - [**1. Prerequisites**](#1-prerequisites)
    - [**2. Step 1: Set Up Multi-Cluster Kubernetes**](#2-step-1-set-up-multi-cluster-kubernetes)
      - [**Cluster A Setup:**](#cluster-a-setup)
    - [**3. Step 2: Create the Basic Rust App**](#3-step-2-create-the-basic-rust-app)
    - [**4. Step 3: Integrate PostgreSQL and MinIO**](#4-step-3-integrate-postgresql-and-minio)
    - [**5. Step 4: Add Prometheus Monitoring**](#5-step-4-add-prometheus-monitoring)
    - [**6. Step 5: Implement Traffic Controller with HAProxy**](#6-step-5-implement-traffic-controller-with-haproxy)
    - [**7. Step 6: Deploy Knative for Serverless Backup**](#7-step-6-deploy-knative-for-serverless-backup)
    - [**8. Testing and Validation**](#8-testing-and-validation)
    - [**9. Experiment Results**](#9-experiment-results)

## Repo Structure

```md
kubernetes-cluster-simulation/
│
├── apps/                         # Application-related code
│   ├── rust-app/
│   │   ├── src/
│   │   │   ├── main.rs             # Main Rust app file
│   │   │   └── monitoring.rs       # Module for Prometheus metrics
│   │   │   └── storage.rs          # Module for file upload to object storage
│   │   │   └── db.rs               # Module for database updates
│   │   ├── Cargo.toml              # Rust app dependencies
│   │   └── Dockerfile              # Dockerfile for the Rust app
│
├── cluster-configs/              # Kubernetes cluster configurations
│   ├── clusterA/
│   │   ├── deployment.yaml       # Application deployment for Cluster A
│   │   ├── prometheus.yaml       # Prometheus configuration for Cluster A
│   │   ├── haproxy.yaml          # HAProxy configuration for Cluster A
│   │   ├── daemon-controller.yaml# DaemonSet for HAProxy controller
│   │   └── k3d-clusterA.yaml     # k3d configuration for Cluster A
│   ├── clusterB/
│   │   ├── postgres.yaml         # PostgreSQL StatefulSet for Cluster B
│   │   ├── minio.yaml            # MinIO StatefulSet for Cluster B
│   │   └── k3d-clusterB.yaml     # k3d configuration for Cluster B
│   └── clusterC/
│       ├── knative-app.yaml      # Knative application deployment for Cluster C
│       └── k3d-clusterC.yaml     # k3d configuration for Cluster C
│
├── controller/                   # LSTM traffic prediction controller
│   ├── src/
│   │   └── main.py               # Python code for traffic controller
│   ├── model/                    # Pretrained LSTM model for traffic prediction
│   ├── Dockerfile                # Dockerfile to containerize the controller
│   └── requirements.txt          # Python dependencies for the controller
│
├── infra/                        # Infrastructure setup scripts
│   ├── setup-clusters.sh         # Script to set up clusters with k3d
│   ├── deploy-applications.sh    # Script to deploy apps to clusters
│   └── teardown-clusters.sh      # Script to tear down clusters
│
├── docs/
│   ├── README.md                 # Main documentation for setup and experiment
│   ├── experiment-results.md     # Record experiment results
│
├── tests/
│   └── integration_tests/        # Integration tests for each milestone
├── .gitignore
└── README.md

```

---

### **1. Prerequisites**

Before we begin, ensure you have the following tools installed:

- [Docker](https://docs.docker.com/get-docker/)
- [k3d](https://k3d.io/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/) (optional, for installing services like Prometheus)

---

### **2. Step 1: Set Up Multi-Cluster Kubernetes**

In this step, we'll create three Kubernetes clusters using **k3d**:

- **Cluster A**: For the Rust application and HAProxy.
- **Cluster B**: For PostgreSQL and MinIO.
- **Cluster C**: For the serverless Rust app using Knative.

#### **Cluster A Setup:**

Create the configuration file for Cluster A (`cluster-configs/clusterA/k3d-clusterA.yaml`), and add resource limits to simulate real-world scenarios:

```yaml
apiVersion: k3d.io/v1alpha1
kind: Simple
metadata:
  name: clusterA
servers: 1
agents: 2
options:
  k3s:
    extraArgs:
      - --kubelet-arg=eviction-hard=memory.available<500Mi
      - --kubelet-arg=eviction-hard=nodefs.available<5%
  limits:
    cpu: 2
    memory: 4Gi
```

Repeat the process for **Cluster B** and **Cluster C**. Now, create the clusters using `k3d`:

```bash
./scripts/setup-clusters.sh
```

This script will create all three clusters using the `k3d` configurations you've defined.

---

### **3. Step 2: Create the Basic Rust App**

Next, we'll create a basic HTTP server in Rust and deploy it to **Cluster A**.

1. **Write the basic Rust app:**
   In `apps/rust-app/src/main.rs`, create a simple HTTP server using **actix-web**:

   ```rust
   use actix_web::{web, App, HttpServer, Responder};

   async fn index() -> impl Responder {
       "Hello from Rust app!"
   }

   #[tokio::main]
   async fn main() -> std::io::Result<()> {
       HttpServer::new(|| App::new().route("/", web::get().to(index)))
           .bind("0.0.0.0:8080")?
           .run()
           .await
   }
   ```

2. **Dockerize the Rust app:**
   Create a `Dockerfile` in `apps/rust-app/`:

   ```Dockerfile
   FROM rust:latest
   WORKDIR /usr/src/rust-app
   COPY . .
   RUN cargo install --path .
   CMD ["rust-app"]
   ```

3. **Deploy the Rust app to Cluster A:**
   Define the `deployment.yaml` in `cluster-configs/clusterA/` for deploying the Rust app:

   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: rust-app
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: rust-app
     template:
       metadata:
         labels:
           app: rust-app
       spec:
         containers:
         - name: rust-app
           image: rust-app:latest
           ports:
           - containerPort: 8080
   ```

   Deploy the app to Cluster A:

   ```bash
   kubectl apply -f cluster-configs/clusterA/deployment.yaml --context k3d-clusterA
   ```

---

### **4. Step 3: Integrate PostgreSQL and MinIO**

To support database updates and file uploads, you need to set up **PostgreSQL** and **MinIO** in **Cluster B**.

1. **PostgreSQL Setup:**
   Create the `postgres.yaml` in `cluster-configs/clusterB/`:

   ```yaml
   apiVersion: apps/v1
   kind: StatefulSet
   metadata:
     name: postgres
   spec:
     serviceName: "postgres"
     replicas: 1
     selector:
       matchLabels:
         app: postgres
     template:
       metadata:
         labels:
           app: postgres
       spec:
         containers:
         - name: postgres
           image: postgres:latest
           env:
           - name: POSTGRES_PASSWORD
             value: example
   ```

2. **MinIO Setup:**
   Similarly, create the `minio.yaml` for object storage:

   ```yaml
   apiVersion: apps/v1
   kind: StatefulSet
   metadata:
     name: minio
   spec:
     serviceName: "minio"
     replicas: 1
     selector:
       matchLabels:
         app: minio
     template:
       metadata:
         labels:
           app: minio
       spec:
         containers:
         - name: minio
           image: minio/minio:latest
           args:
           - server
           - /data
   ```

Deploy both services to **Cluster B**:

```bash
kubectl apply -f cluster-configs/clusterB/postgres.yaml --context k3d-clusterB
kubectl apply -f cluster-configs/clusterB/minio.yaml --context k3d-clusterB
```

---

### **5. Step 4: Add Prometheus Monitoring**

Now, add **Prometheus** to monitor the Rust app's performance.

1. **Prometheus Configuration:**
   In `cluster-configs/clusterA/prometheus.yaml`, configure Prometheus to scrape the Rust app metrics:

   ```yaml
   apiVersion: monitoring.coreos.com/v1
   kind: ServiceMonitor
   metadata:
     name: rust-app-monitor
   spec:
     selector:
       matchLabels:
         app: rust-app
     endpoints:
     - port: 8080
       path: /metrics
   ```

2. **Integrate Prometheus Metrics in the Rust App:**
   Update your Rust app to expose metrics (see Prometheus integration in the incremental Rust app steps above).

---

### **6. Step 5: Implement Traffic Controller with HAProxy**

Next, implement HAProxy to manage traffic between **Cluster A** and **Cluster C** using the Dataplane API.

1. **Deploy HAProxy** to **Cluster A**.
2. **Develop the traffic controller** that monitors Prometheus and reroutes traffic to **Cluster C** during spikes.

---

### **7. Step 6: Deploy Knative for Serverless Backup**

Finally, deploy **Knative** in **Cluster C** to run the serverless Rust app as a backup when **Cluster A** becomes overloaded.

---

### **8. Testing and Validation**

After deploying all services, perform load testing to simulate traffic spikes, verify file uploads to MinIO, and monitor metrics in Prometheus.

---

### **9. Experiment Results**

Document your experiment results, including performance metrics, observed behaviors, and conclusions.
