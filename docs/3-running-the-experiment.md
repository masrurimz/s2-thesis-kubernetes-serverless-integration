# Running the Experiment

Once the services are deployed, follow these steps to run the experiment:

## Step 1: Generate Traffic

You can use `curl` or load testing tools like **k6** to generate traffic to the Rust app in **Cluster A**:

```bash
curl http://<cluster-a-IP>:8080
```

## Step 2: Monitor Metrics

Check Prometheus in **Cluster A** for metrics like request counts, response times, and latency:

```bash
kubectl port-forward service/prometheus 9090 --context k3d-cluster-a
```

Visit `http://localhost:9090` to see the metrics.

## Step 3: Simulate Overload and Test Controller

Generate higher traffic loads to trigger traffic rerouting to **Cluster C** (Knative). Monitor HAProxy's behavior to see if it reroutes the traffic.

## Step 4: Test File Uploads and Database Updates

Use the Rust app’s

 `/upload` endpoint to test file uploads to MinIO and database updates in PostgreSQL.

Verify that files are stored in MinIO and database records are created in PostgreSQL.
