
## Table of Contents

- [Table of Contents](#table-of-contents)
- [Prerequisites](#prerequisites)
  - [Installation Commands](#installation-commands)
- [Setting Up K3D Clusters](#setting-up-k3d-clusters)
  - [Creating Cluster Control Plane](#creating-cluster-control-plane)
  - [Creating Cluster Main Kubernetes](#creating-cluster-main-kubernetes)
- [Deploying Prometheus on Cluster Control Plane](#deploying-prometheus-on-cluster-control-plane)
  - [Using Helm to Install Prometheus](#using-helm-to-install-prometheus)
- [Configuring Cluster Main Kubernetes to Export Metrics to Cluster Control Plane](#configuring-cluster-main-kubernetes-to-export-metrics-to-cluster-control-plane)
  - [Setting Up Prometheus on Cluster Main Kubernetes](#setting-up-prometheus-on-cluster-main-kubernetes)
  - [Configuring Remote Write to Cluster Control Plane's Prometheus](#configuring-remote-write-to-cluster-control-planes-prometheus)
- [Networking Considerations](#networking-considerations)
- [Testing the Setup](#testing-the-setup)
  - [Verifying Prometheus on Cluster Control Plane](#verifying-prometheus-on-cluster-control-plane)
  - [Checking Metrics from Cluster Main Kubernetes](#checking-metrics-from-cluster-main-kubernetes)
- [Troubleshooting](#troubleshooting)
- [Conclusion](#conclusion)

---

## Prerequisites

Before proceeding, ensure you have the following installed on your local machine:

- **Docker**: K3D runs K3s clusters inside Docker containers.
- **K3D**: Tool for running K3s in Docker.
- **kubectl**: Kubernetes command-line tool.
- **Helm**: Kubernetes package manager (optional but recommended for deploying Prometheus).

### Installation Commands

If you don't have these tools installed, you can install them using the following commands:

**Docker:**

- Follow the [official Docker installation guide](https://docs.docker.com/get-docker/) for your operating system.

**K3D:**

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

**kubectl:**

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/$(uname | tr '[:upper:]' '[:lower:]')/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

**Helm:**

```bash
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
```

---

## Setting Up K3D Clusters

We'll create two separate K3D clusters: **Cluster Control Plane** and **Cluster Main Kubernetes**.

### Creating Cluster Control Plane

1. **Create Cluster Control Plane with an Internal LoadBalancer:**

   ```bash
   k3d cluster create cluster-control-plane --api-port 6550 -p "8080:80@loadbalancer" --agents 2
   ```

   - `--api-port 6550`: Exposes the Kubernetes API server on port 6550.
   - `-p "8080:80@loadbalancer"`: Forwards port 80 in the cluster's load balancer to port 8080 on the host.
   - `--agents 2`: Creates a cluster with 1 server node and 2 agent (worker) nodes.

2. **Verify Cluster Control Plane is Running:**

   ```bash
   k3d cluster list
   ```

   You should see `cluster-control-plane` listed.

### Creating Cluster Main Kubernetes

1. **Create Cluster Main Kubernetes with an Internal LoadBalancer:**

   ```bash
   k3d cluster create cluster-main-kubernetes --api-port 6551 -p "8081:80@loadbalancer" --agents 2
   ```

   - `--api-port 6551`: Exposes the Kubernetes API server on port 6551.
   - `-p "8081:80@loadbalancer"`: Forwards port 80 in the cluster's load balancer to port 8081 on the host.
   - `--agents 2`: Creates a cluster with 1 server node and 2 agent (worker) nodes.

2. **Verify Cluster Main Kubernetes is Running:**

   ```bash
   k3d cluster list
   ```

   You should see both `cluster-control-plane` and `cluster-main-kubernetes` listed.

3. **Configure `kubectl` Contexts:**

   K3D automatically configures `kubectl` contexts for each cluster. You can switch between them using:

   ```bash
   kubectl config use-context k3d-cluster-control-plane
   ```

   and

   ```bash
   kubectl config use-context k3d-cluster-main-kubernetes
   ```

---

## Deploying Prometheus on Cluster Control Plane

We'll deploy Prometheus on the **Cluster Control Plane** to serve as the central monitoring system.

### Using Helm to Install Prometheus

1. **Add the Prometheus Community Helm Repository:**

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   ```

2. **Create a Namespace for Monitoring:**

   ```bash
   kubectl create namespace monitoring
   ```

3. **Install Prometheus:**

   ```bash
   helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring
   ```

   This command installs the Prometheus Operator along with Prometheus, Alertmanager, and Grafana.

4. **Verify Prometheus Deployment:**

   ```bash
   kubectl get pods -n monitoring
   ```

   Ensure all pods are running without issues.

5. **Access Prometheus Dashboard:**

   To access the Prometheus UI, you can port-forward the service:

   ```bash
   kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
   ```

   Then, navigate to `http://localhost:9090` in your browser.

---

## Configuring Cluster Main Kubernetes to Export Metrics to Cluster Control Plane

To export metrics from **Cluster Main Kubernetes** to **Cluster Control Plane**'s Prometheus, we'll set up a Prometheus instance on Cluster Main Kubernetes that uses **remote_write** to send metrics to Cluster Control Plane.

### Setting Up Prometheus on Cluster Main Kubernetes

1. **Switch to Cluster Main Kubernetes Context:**

   ```bash
   kubectl config use-context k3d-cluster-main-kubernetes
   ```

2. **Install Prometheus on Cluster Main Kubernetes:**

   You can reuse the same Helm chart or use a simplified Prometheus setup.

   **Using Helm:**

   ```bash
   helm install prometheus prometheus-community/prometheus --namespace monitoring --create-namespace
   ```

   **Or Using a Custom Prometheus Deployment:**

   Create a YAML file `prometheus-cluster-main-kubernetes.yaml`:

   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: monitoring
   ---
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: prometheus
     namespace: monitoring
   ---
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: prometheus-config
     namespace: monitoring
   data:
     prometheus.yml: |
       global:
         scrape_interval: 15s
       scrape_configs:
         - job_name: 'kubernetes'
           kubernetes_sd_configs:
             - role: node
       remote_write:
         - url: "http://<PROMETHEUS_CONTROL_PLANE_IP>:9090/api/v1/write"
   ---
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: prometheus
     namespace: monitoring
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: prometheus
     template:
       metadata:
         labels:
           app: prometheus
       spec:
         serviceAccountName: prometheus
         containers:
           - name: prometheus
             image: prom/prometheus:latest
             args:
               - "--config.file=/etc/prometheus/prometheus.yml"
             ports:
               - containerPort: 9090
             volumeMounts:
               - name: config
                 mountPath: /etc/prometheus
         volumes:
           - name: config
             configMap:
               name: prometheus-config
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: prometheus
     namespace: monitoring
   spec:
     type: ClusterIP
     ports:
       - port: 9090
         targetPort: 9090
         protocol: TCP
         name: http
     selector:
       app: prometheus
   ```

   Replace `<PROMETHEUS_CONTROL_PLANE_IP>` with the accessible IP or hostname of **Cluster Control Plane**'s Prometheus instance. Since both clusters are separate, you need to expose **Cluster Control Plane**'s Prometheus to be accessible from **Cluster Main Kubernetes**.

   **Apply the Configuration:**

   ```bash
   kubectl apply -f prometheus-cluster-main-kubernetes.yaml
   ```

   **Note:** Using Helm is recommended for easier management and better feature support.

### Configuring Remote Write to Cluster Control Plane's Prometheus

1. **Expose Cluster Control Plane's Prometheus to Cluster Main Kubernetes:**

   - **Option 1: Use a LoadBalancer or NodePort**

     Since K3D clusters are running on your local machine, you can expose Prometheus on **Cluster Control Plane** using a NodePort or by port-forwarding.

     **Using NodePort:**

     ```bash
     kubectl patch svc prometheus-operated -n monitoring -p '{"spec": {"type": "NodePort"}}'
     ```

     Then, get the NodePort:

     ```bash
     kubectl get svc prometheus-operated -n monitoring
     ```

     Note the port assigned (e.g., 32000).

     **Determine Cluster Control Plane's IP:**

     Since K3D runs in Docker, **Cluster Control Plane**'s services are accessible via `localhost` and the forwarded ports.

     Therefore, the `remote_write` URL would be `http://localhost:<NodePort>/api/v1/write`.

   - **Option 2: Use Port-Forwarding (For Testing Purposes):**

     ```bash
     kubectl port-forward svc/prometheus-operated -n monitoring 9090:9090
     ```

     Then, use `http://localhost:9090/api/v1/write` as the `remote_write` URL.

     **Note:** Port-forwarding is not suitable for production but works for testing.

2. **Update Prometheus Configuration on Cluster Main Kubernetes:**

   If you used Helm to install Prometheus on **Cluster Main Kubernetes**, you can configure the `remote_write` by setting the appropriate Helm values.

   **Example Using Helm:**

   ```bash
   helm upgrade prometheus cluster-main-prometheus prometheus-community/prometheus --namespace monitoring --set remoteWrite[0].url=http://localhost:32000/api/v1/write
   ```

   Replace `localhost:32000` with the appropriate URL (e.g., `localhost:32000` if using NodePort).

   **Alternatively, Modify the Prometheus ConfigMap:**

   ```bash
   kubectl edit configmap prometheus-config -n monitoring
   ```

   Add the `remote_write` section:

   ```yaml
   remote_write:
     - url: "http://localhost:32000/api/v1/write"
   ```

   Save and exit. Prometheus should reload the configuration automatically.

---

## Networking Considerations

Since K3D clusters are isolated Docker networks, networking between **Cluster Main Kubernetes** and **Cluster Control Plane** requires that Prometheus in **Cluster Control Plane** is accessible from **Cluster Main Kubernetes**. The simplest way to achieve this on a local machine is to use `localhost` with appropriate port forwarding or NodePort services.

**Security Note:** In a production environment, ensure secure communication between clusters using TLS and authentication mechanisms.

---

## Testing the Setup

After setting up both clusters and configuring Prometheus, it's essential to test and verify that metrics from **Cluster Main Kubernetes** are successfully being ingested into **Cluster Control Plane**'s Prometheus.

### Verifying Prometheus on Cluster Control Plane

1. **Access Prometheus UI:**

   If you haven't already, access the Prometheus UI on **Cluster Control Plane**:

   ```bash
   kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
   ```

   Navigate to `http://localhost:9090` in your browser.

2. **Check `remote_write` Metrics:**

   In the Prometheus UI, go to **Status > Targets** and verify that Prometheus is receiving data.

### Checking Metrics from Cluster Main Kubernetes

1. **Ensure Prometheus on Cluster Main Kubernetes is Sending Metrics:**

   On **Cluster Main Kubernetes**, verify that the Prometheus pods are running and that there are no errors.

   ```bash
   kubectl get pods -n monitoring
   ```

   Check the logs for the Prometheus pod:

   ```bash
   kubectl logs -n monitoring <prometheus-pod-name>
   ```

   Look for logs indicating successful `remote_write` operations.

2. **Verify Metrics in Cluster Control Plane:**

   Back in **Cluster Control Plane**'s Prometheus UI, perform a query to check for metrics from **Cluster Main Kubernetes**.

   For example, you can query a node metric:

   ```bash
   node_cpu_seconds_total
   ```

   You should see metrics corresponding to the nodes and applications in **Cluster Main Kubernetes**.

3. **Grafana Dashboard (Optional):**

   If you've installed Grafana via the `kube-prometheus-stack`, you can set up dashboards to visualize the metrics.

   - **Access Grafana:**

     ```bash
     kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
     ```

     Navigate to `http://localhost:3000` and log in (default credentials are `admin/prom-operator` or check the Helm chart values).

   - **Create Dashboards:**

     Import or create dashboards to visualize the metrics coming from **Cluster Main Kubernetes**.

---

## Troubleshooting

If you encounter issues, consider the following troubleshooting steps:

1. **Prometheus Not Receiving Metrics:**

   - **Check Network Connectivity:**
     Ensure that **Cluster Main Kubernetes** can reach **Cluster Control Plane**'s Prometheus endpoint.

     ```bash
     kubectl exec -n monitoring <prometheus-pod-name> -- curl -I http://localhost:32000/api/v1/write
     ```

     Replace `localhost:32000` with your actual `remote_write` URL.

   - **Verify Remote Write Configuration:**
     Ensure that the `remote_write` URL is correctly set in **Cluster Main Kubernetes**'s Prometheus configuration.

   - **Check Prometheus Logs:**
     Look for errors related to `remote_write` in the Prometheus logs on **Cluster Main Kubernetes**.

2. **Authentication Issues:**

   - If you've set up authentication for Prometheus on **Cluster Control Plane**, ensure that **Cluster Main Kubernetes**'s Prometheus is configured to use the correct credentials.

3. **Firewall or Port Issues:**

   - Ensure that the necessary ports are open and not blocked by your local firewall.

4. **Helm Configuration Errors:**

   - If using Helm, ensure that all values are correctly set, especially the `remote_write` URLs.

---

## Conclusion

By following the steps outlined above, you should have a functional multi-cluster Prometheus monitoring setup using K3D. The **Cluster Control Plane** serves as the central Prometheus instance, aggregating metrics from **Cluster Main Kubernetes**, the Application Worker Cluster. This setup allows for scalable and organized monitoring of multiple Kubernetes clusters.

**Next Steps:**

- **Secure Communication:** Implement TLS and authentication for secure metric transmission.
- **Alerting:** Configure Alertmanager to send alerts based on Prometheus metrics.
- **Grafana Dashboards:** Create comprehensive dashboards for better visualization.
- **Scalability:** Consider automating cluster setups using scripts or infrastructure-as-code tools like Terraform.

Feel free to reach out if you have any further questions or need assistance with specific configurations!
