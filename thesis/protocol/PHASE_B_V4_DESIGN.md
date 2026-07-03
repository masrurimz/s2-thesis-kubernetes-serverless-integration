# Phase B v4: Multi-Node Experiment Design

**Version:** v4 (replaces v3 single-node design)
**Date:** 2026-02-16
**Status:** Draft — awaiting review before implementation

---

## Problem Statement

Phase B v3 revealed that the k3d single-node setup creates an **artificial advantage for S1 (HPA)**:

- HPA scales pods in ~2 seconds (image cached, no node provisioning)
- S1 achieved p99 = 15ms with 0 SLO violations
- S3/S4 achieved p99 = 3200+ ms with 14k-21k SLO violations

The root cause: in production, scaling beyond a node's capacity requires **new VM provisioning** (60-300 seconds). In k3d single-node, all pods schedule instantly on the same Docker container. The hybrid architecture's value proposition — Knative absorbs traffic while K8s capacity provisions — is invisible without this delay.

### Two-World Evaluation Framing

This thesis uses two distinct evaluation contexts:

1. **Stress-harness testbed** — k3d workload nodes configured with `--system-reserved=15600m`, leaving only ~400m allocatable CPU per node (~2 pods at 200m each). This is a deliberate fault-injection-style forcing function: it compresses the time-to-Pending from minutes (production) to seconds, allowing Cluster Autoscaler and HPA mechanisms to be observed within 20-minute experiment runs.

2. **Production cost projection** — a separate analytical layer that sizes a realistic cloud cluster using typical allocatable capacity (t3.medium ≈ 1.8 vCPU allocatable, ~9 pods/node at 200m request). At tested load levels (~53–73 RPS), a production-sized cluster would **not** trigger Cluster Autoscaler — all desired replicas fit on 1–2 nodes.

Results from the stress harness validate elasticity **mechanisms** (triggering, control behavior, routing decisions) but are not directly interpretable as real-world capacity or cost. The cost chapter (Section 4.4) uses production assumptions exclusively.

### What Changed from v3

| Aspect | v3 (single-node) | v4 (multi-node) |
|--------|-------------------|-------------------|
| k3d topology | 1 server + 1 agent | 1 server + 1 infra agent + 3 workload agents |
| Pod scheduling | Any pod on any node | test-app-warm → workload nodes only; Knative → infra node only |
| Node capacity | Unlimited pods per node | ~4-5 test-app pods per workload node (1.0 CPU node, 200m CPU/pod) |
| Scaling bottleneck | None (instant pod start) | Node provisioning delay (cordon/uncordon with configurable delay) |
| HPA behavior | Scales pods instantly | Pods go Pending when node full → wait for "provisioned" node |
| HAProxy/Prometheus | Docker containers (unchanged) | Docker containers (unchanged — not on K8s) |

---

## Cluster Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Host Machine (8 cores, 32GB RAM)                                   │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ Docker Containers │  │ k3d Cluster: thesis-hybrid               │ │
│  │ (host network)    │  │                                          │ │
│  │                   │  │  ┌────────────────────────────────────┐  │ │
│  │ • HAProxy         │  │  │ server-0 (system)                  │  │ │
│  │   :18082 frontend │  │  │ 1 CPU, 1 GiB                      │  │ │
│  │   :18404 stats    │  │  │ kube-system, coredns, metrics-srv  │  │ │
│  │   :19999 socket   │  │  │ label: node-type=system            │  │ │
│  │                   │  │  └────────────────────────────────────┘  │ │
│  │ • Prometheus      │  │                                          │ │
│  │   :9090           │  │  ┌────────────────────────────────────┐  │ │
│  │                   │  │  │ agent-0 (infra)                    │  │ │
│  │ • GRU Server      │  │  │ 3 CPU, 4 GiB                      │  │ │
│  │   :8090           │  │  │ Knative Serving, Kourier, KPA      │  │ │
│  │                   │  │  │ Knative user pods (test-app)       │  │ │
│  │ • Routing Daemon  │  │  │ label: node-type=infra             │  │ │
│  │   :9104           │  │  └────────────────────────────────────┘  │ │
│  │                   │  │                                          │ │
│  └──────────────────┘  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│                         │  │ agent-1  │ │ agent-2  │ │ agent-3  │  │ │
│                         │  │(workload)│ │(workload)│ │(workload)│  │ │
│                         │  │ 1.0 CPU  │ │ 1.0 CPU  │ │ 1.0 CPU  │  │ │
│                         │  │ 1 GiB    │ │ 1 GiB    │ │ 1 GiB    │  │ │
│                         │  │ 4-5 pods │ │ CORDONED │ │ CORDONED │  │ │
│                         │  │ baseline │ │ at start │ │ at start │  │ │
│                         │  └──────────┘ └──────────┘ └──────────┘  │ │
│                         └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

> **⚠️ Stress-Harness Node Constraint:** Workload nodes (agent-1 through agent-3) use `--system-reserved=15600m`, reducing allocatable CPU from 16 vCPU to ~400m per node. This limits each node to ~2 pods at 200m request — far fewer than the ~9 pods/node possible on a production t3.medium (1.8 vCPU allocatable). The purpose is to force Pending pods and NodeProvisioner/CA exercise at modest load levels. This is NOT a claim about typical Kubernetes packing density; see "Interpretation Rules" below.

### Pod Resource Configuration (Revised from v3)

| | v3 (500m) | v4 (200m) |
|--|-----------|-----------|
| CPU request/limit | 500m / 500m | 200m / 200m |
| Per-pod saturation | ~60 RPS | ~25 RPS |
| α (Algorithm 2) | 0.0167 | 0.04 |
| Peak pods (164 RPS) | 4 | 7 |
| Mean pods (73 RPS) | 2 | 3 |
| Pods per 1.0 CPU node | 1-2 | 4-5 |

**Why 200m:** More realistic — production pods typically use 100-500m, and multiple pods share a node. With 500m + 0.75 CPU nodes, only 1 pod fit per node, making the experiment degenerate to "1 pod = 1 node". With 200m, 4-5 pods fit per node, which means HPA can scale partially within a node before needing a new one.

**CFS throttling note:** At 200m CPU limit, Linux CFS gives the pod 20ms of CPU per 100ms period. fib(32) uses ~8ms CPU per call → 2 calls fit per period without throttling, but tail latency may show 100ms-period stair-step artifacts. This is documented as a known measurement characteristic.

### Resource Budget

| Node | CPU | Memory | Purpose | Pods |
|------|-----|--------|---------|------|
| server-0 | 1.0 | 1 GiB | Control plane, kube-system | System only |
| agent-0 (infra) | 3.0 | 4 GiB | Knative Serving + Kourier + user pods | Knative pods scale freely |
| agent-1 (workload) | 1.0 | 1 GiB | Baseline workload node | ~4-5 pods (200m each) |
| agent-2 (workload) | 1.0 | 1 GiB | Cordoned → uncordon on demand | ~4-5 pods |
| agent-3 (workload) | 1.0 | 1 GiB | Cordoned → uncordon on demand | ~4-5 pods |
| **Total** | **7.0** | **8 GiB** | | |

Host has 8 cores / 32 GB — leaves headroom for Docker, HAProxy, Prometheus, GRU, k6.

### Why 3 Workload Nodes

ClarkNet trace: peak ~164 RPS, single-pod saturation ~25 RPS (at 200m CPU).
- Peak needs ceil(164/25 × 1.2 buffer) = ceil(7.87) = **8 pods**
- Mean ~73 RPS needs ceil(73/25 × 1.2) = ceil(3.50) = **4 pods**
- 1 workload node holds ~4-5 pods → covers mean load on a single node
- Peak 8 pods → **requires 2 nodes** (4-5 + 3-4) → forces node provisioning
- 3 workload nodes (1 baseline + 2 provisioned) = enough for peak + buffer

---

### Interpretation Rules

When citing results from this experiment design:

1. **Mechanism correctness inferences are valid** — CA trigger detection, HPA scaling decisions, Knative burst absorption, routing weight shifts, and PREDICTIVE pre-warming all operate correctly under stress-harness conditions. The mechanisms do not depend on absolute node capacity.

2. **Cost and capacity inferences must use production assumptions** — the cost chapter (Section 4.4) sizes clusters using t3.medium allocatable capacity (1.8 vCPU), not the stress-harness constraint (400m). At tested load (~53–73 RPS), S1's 9 desired replicas fit on 1–2 real nodes with no CA trigger.

3. **CA trigger counts reflect the stress regime** — the frequency and timing of node provisioning events are artifacts of the 400m constraint. In production at the same load, CA would not trigger. Report as "under stress-harness constraints" when citing.

---

## Node Provisioning Simulation

### Mechanism: Cordon/Uncordon with Configurable Delay

At each run start:
1. **agent-1** is always schedulable (baseline capacity — 1 warm pod)
2. **agent-2, agent-3** are cordoned (unschedulable)
3. A **background provisioner thread** monitors for Pending pods
4. When Pending pods detected → wait randomized delay (45-120s) → uncordon next node

```
Timeline (example at peak load):

t=0s     HPA target=1, agent-1 has 1 pod (baseline)
t=30s    Load ramps → CPU > 50% → HPA scales to 4 pods on agent-1
t=60s    Load peaks → HPA wants 7 pods → pods 5-7 Pending (agent-1 full)
t=60s    Provisioner detects Pending → starts randomized delay (45-120s)
t=105-180s  Provisioner uncordons agent-2 → Pods 5-7 schedule → Ready in ~5s
t=110-185s  Full capacity online

         During provisioning gap: S3/S4 routes to Knative (instant burst absorption)
         S1: queues excess requests on available pods → latency spikes
```

### Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PROVISION_DELAY_MIN_SEC` | 45 | Minimum provisioning delay (seconds) |
| `PROVISION_DELAY_MAX_SEC` | 120 | Maximum provisioning delay (seconds) |
| `WORKLOAD_NODES` | `agent-1,agent-2,agent-3` | Node names |
| `BASELINE_NODES` | `agent-1` | Always-schedulable node(s) |

### Scientific Defensibility

This emulates the **observable effect** of node provisioning:
- ✅ Pods go genuinely Pending (Kubernetes scheduler cannot place them)
- ✅ Delay is randomized per-event (uniform 45-120s), capturing real-world variability
- ✅ HPA sees Pending pods and continues requesting (realistic)
- ✅ Knative operates independently on infra node (not affected)

**What it captures:** Time from capacity exhaustion to new capacity available, with realistic variability.
**What it does not capture:** Heterogeneous node types, cloud API rate limiting, multi-AZ placement.

**Provisioning delay calibration (based on industry benchmarks):**

| Platform / Tool | Measured Node Ready Time | Source |
|----------------|------------------------|--------|
| AWS Karpenter v1.5 | ~45-60s | Chkk benchmark, July 2025 |
| AWS EKS + Cluster Autoscaler | ~120-240s (2-4 min) | AWS EKS Best Practices documentation |
| General Cluster Autoscaler (official SLO) | CA decision <30s + cloud provider boot | Kubernetes Autoscaler FAQ, SIG Autoscaling |
| Azure AKS | `max-node-provision-time` default 15 min | Microsoft Learn AKS documentation |

**Chosen range (45-120s):** Represents modern cloud provisioning (Karpenter-class best case to typical managed node group). Each provisioning event samples `uniform(45, 120)` to introduce realistic variability without the extremes of cold ASG scale-up (which can exceed 5 minutes).

**Thesis framing:** "Emulated node provisioning latency via randomized delay (uniform 45-120 seconds per event), calibrated against published cloud provider benchmarks: Karpenter achieves ~45-60s on AWS (Chkk, 2025), while traditional Cluster Autoscaler with Auto Scaling Groups typically requires 2-4 minutes (AWS EKS Best Practices)."

---

## Scheduling Isolation

### 1. Node Labels (applied after cluster creation)

```bash
kubectl label node k3d-thesis-hybrid-server-0    node-type=system    --overwrite
kubectl label node k3d-thesis-hybrid-agent-0      node-type=infra     --overwrite
kubectl label node k3d-thesis-hybrid-agent-1      node-type=workload  --overwrite
kubectl label node k3d-thesis-hybrid-agent-2      node-type=workload  --overwrite
kubectl label node k3d-thesis-hybrid-agent-3      node-type=workload  --overwrite
```

### 2. test-app-warm Deployment → workload nodes only

```yaml
# infrastructure/test-app/test-app-warm-deployment.yaml
spec:
  template:
    spec:
      nodeSelector:
        node-type: workload
      containers:
        - name: test-app-warm
          # ... unchanged
```

### 3. Knative pods → infra node only

Apply ConfigMap in `knative-serving` namespace (governs all Knative revisions):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-features
  namespace: knative-serving
data:
  kubernetes.podspec-nodeselector: "enabled"
```

Then in the Knative Service:

```yaml
# infrastructure/test-app/knative-service.yaml
spec:
  template:
    spec:
      nodeSelector:
        node-type: infra
      containers:
        - image: k3d-registry.localhost:5000/test-app:latest
          # ... unchanged
```

Additionally, patch Kourier gateway (runs in kourier-system, not governed by knative-serving config):

```bash
kubectl -n kourier-system patch deploy kourier-gateway \
  --type='json' -p='[{"op":"add","path":"/spec/template/spec/nodeSelector","value":{"node-type":"infra"}}]'
```

### 4. System pods stay on server-0

kube-system DaemonSets (kube-proxy, svclb-*) run everywhere by default — that's fine, they're lightweight. Critical system pods (coredns, metrics-server, local-path-provisioner) already prefer the server node.

### Isolation Verification

```bash
# Verify no Knative pods on workload nodes
kubectl get pods -A -o wide | grep -E "agent-[1-4]" | grep -v test-app-warm
# Should return empty (only test-app-warm on workload nodes)

# Verify no test-app-warm on infra node
kubectl get pods -o wide | grep test-app-warm | grep agent-0
# Should return empty
```

---

## Scenario Designs (Revised)

### S1: K8s + HPA Baseline

**What it tests:** Native Kubernetes horizontal pod autoscaling with node provisioning delay.

**Configuration:**
- HAProxy: 100% k3s / 0% knative
- HPA: CPU target 50%, min=1, max=10
- Algorithm 1/2: Disabled
- GRU: Off
- Node provisioner: **Active** (60s delay)

**Expected behavior:**
1. Baseline: 1 pod on agent-1 handles ~60 RPS
2. Load increases → CPU > 50% → HPA requests 2 replicas
3. Pod-2 Pending (agent-1 full, agent-2 cordoned)
4. 60s delay → agent-2 uncordoned → Pod-2 schedules
5. **During 60s gap: all traffic queues on 1 pod → latency spike**
6. Repeat for further scale-up

**Key difference from v3:** S1 now experiences real capacity delays. p99 should be significantly higher than v3's 15ms.

### S2: Knative-Only (KPA)

**What it tests:** Serverless-native autoscaling with scale-to-zero.

**Configuration:**
- HAProxy: 0% k3s / 100% knative
- HPA: Deleted
- Algorithm 1/2: Disabled
- GRU: Off
- Node provisioner: **Not needed** (Knative scales on infra node, which has 3 CPU)

**Expected behavior:**
1. KPA scales pods 0→N on agent-0 (infra node has 3 CPU → fits ~6 Knative pods)
2. Cold start ~1.2s on first request after scale-to-zero
3. Concurrency-based scaling responds to request rate
4. No node provisioning involved (infra node has ample capacity)

**Note:** S2 doesn't need node provisioning because Knative pods run on the infra node. This is realistic: serverless platforms pre-provision capacity and scale from a shared pool.

### S3: Hybrid Reactive

**What it tests:** Custom control plane (Algorithm 1 routing + Algorithm 2 scaling) reacting to observed metrics, with Knative as burst absorber during node provisioning.

**Configuration:**
- HAProxy: 80% k3s / 20% knative (initial)
- HPA: **Deleted** (Algorithm 2 controls replicas)
- Algorithm 1: Enabled (routing decisions based on SLO monitoring)
- Algorithm 2: Enabled (replica scaling based on observed load x_obs)
- GRU: Off
- Node provisioner: **Active** (60s delay)

**Expected behavior:**
1. Baseline: 1 warm pod on agent-1, Knative warm on infra
2. Load increases → SLO violation detected
3. Algorithm 1: shifts weight toward Knative (burst absorption)
4. Algorithm 2: requests scale-up → Pod-2 Pending
5. 60s delay → agent-2 uncordoned → Pod-2 Ready
6. Algorithm 1: detects K8s capacity available → shifts weight back to K8s
7. **Key advantage: Knative handles traffic during 60s provisioning gap**

### S4: Hybrid Predictive

**What it tests:** Same as S3 but with GRU prediction driving proactive scaling.

**Configuration:**
- HAProxy: 80% k3s / 20% knative (initial)
- HPA: **Deleted** (Algorithm 2 controls replicas)
- Algorithm 1: Enabled (includes PREDICTIVE trigger)
- Algorithm 2: Enabled (replica scaling based on predicted load x_pred)
- GRU: **On** (30-second-ahead forecast)
- Node provisioner: **Active** (60s delay)

**Expected behavior:**
1. GRU predicts load increase 30s ahead
2. Algorithm 1: PREDICTIVE trigger → proactively shifts weight to Knative
3. Algorithm 2: proactively requests scale-up → Pod-2 Pending
4. 60s delay → agent-2 uncordoned → Pod-2 Ready
5. By the time load actually arrives, K8s capacity is closer to ready
6. **Key advantage over S3: 30s head start on provisioning**

### Scenario Comparison Matrix

| Aspect | S1 (HPA) | S2 (KPA) | S3 (Reactive) | S4 (Predictive) |
|--------|----------|----------|---------------|-----------------|
| K8s scaling | HPA (native) | N/A | Algorithm 2 (observed) | Algorithm 2 (predicted) |
| Serverless | None | KPA (native) | Burst absorber | Proactive + burst |
| Node provisioning | 60s delay, no fallback | N/A (infra node) | 60s delay, Knative covers | 60s delay, predicted + Knative covers |
| GRU | Off | Off | Off | On |
| Expected p99 | High (queues during provisioning) | Medium (cold start) | Low-Medium (Knative absorbs) | Lowest (proactive + absorbs) |

---

## Infrastructure Changes

### 1. k3d-cluster.yaml

```yaml
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: thesis-hybrid
servers: 1
agents: 4   # was: 1 (agent-0 infra + agent-1..3 workload)
image: rancher/k3s:v1.28.5-k3s1
kubeAPI:
  hostIP: "0.0.0.0"
  hostPort: "6443"
ports:
  # unchanged from current
  - port: 8080:80
    nodeFilters: [loadbalancer]
  - port: 8081:31080
    nodeFilters: [loadbalancer]
  - port: 8082:31082
    nodeFilters: [loadbalancer]
  - port: 8404:31404
    nodeFilters: [loadbalancer]
  - port: 9090:31090
    nodeFilters: [loadbalancer]
  - port: 9102:31102
    nodeFilters: [loadbalancer]
options:
  k3d:
    wait: true
    timeout: "180s"   # longer for 6 nodes
    disableLoadbalancer: false
    disableImageVolume: false
  k3s:
    extraArgs:
      - arg: --disable=traefik
        nodeFilters: [server:*]
      - arg: --kubelet-arg=eviction-hard=memory.available<100Mi
        nodeFilters: [server:*, agent:*]
  kubeconfig:
    updateDefaultKubeconfig: true
    switchCurrentContext: true
registries:
  create:
    name: k3d-registry.localhost
    host: "0.0.0.0"
    hostPort: "5000"
```

### 2. create-cluster.sh (revised resource limits + labels)

```bash
apply_resource_limits() {
    log_info "Applying per-node resource limits..."

    # Server: control plane
    docker update --cpus 1 --memory 1g --memory-swap 1g \
        "k3d-thesis-hybrid-server-0" || true

    # Agent-0 (infra): Knative + Kourier
    docker update --cpus 3 --memory 4g --memory-swap 4g \
        "k3d-thesis-hybrid-agent-0" || true

    # Agent-1..3 (workload): 1 CPU each, ~4-5 pods at 200m each
    for i in 1 2 3; do
        docker update --cpus 1 --memory 1g --memory-swap 1g \
            "k3d-thesis-hybrid-agent-${i}" || true
    done
}

label_nodes() {
    log_info "Labeling nodes by role..."
    kubectl label node k3d-thesis-hybrid-server-0 node-type=system    --overwrite
    kubectl label node k3d-thesis-hybrid-agent-0  node-type=infra     --overwrite
    for i in 1 2 3; do
        kubectl label node "k3d-thesis-hybrid-agent-${i}" node-type=workload --overwrite
    done
}
```

### 3. test-app-warm-deployment.yaml (add nodeSelector)

```yaml
spec:
  template:
    spec:
      nodeSelector:
        node-type: workload
      containers:
        - name: test-app-warm
          # ... all existing config unchanged
```

### 4. knative-service.yaml (add nodeSelector)

First, enable nodeSelector in Knative:
```yaml
# Apply to knative-serving namespace
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-features
  namespace: knative-serving
data:
  kubernetes.podspec-nodeselector: "enabled"
```

Then in the service:
```yaml
spec:
  template:
    spec:
      nodeSelector:
        node-type: infra
      containers:
        - image: k3d-registry.localhost:5000/test-app:latest
          # ... all existing config unchanged
```

### 5. knative-install.sh (add Kourier patch + node selector config)

After existing install steps, add:
```bash
configure_node_isolation() {
    log_info "Configuring Knative node isolation..."

    # Enable nodeSelector in Knative pod specs
    kubectl patch configmap/config-features \
        --namespace knative-serving \
        --type merge \
        --patch '{"data":{"kubernetes.podspec-nodeselector":"enabled"}}'

    # Patch Kourier to run on infra node only
    kubectl -n kourier-system patch deploy kourier-gateway \
        --type='json' \
        -p='[{"op":"add","path":"/spec/template/spec/nodeSelector","value":{"node-type":"infra"}}]'

    log_info "Node isolation configured."
}
```

### 6. HAProxy config (unchanged)

HAProxy runs as a Docker container, not a K8s pod. No changes needed. Backend addresses may need updating if k3d node IPs change with multi-node setup — verify with:
```bash
# K8s NodePort accessible via any node IP or k3d loadbalancer
docker inspect k3d-thesis-hybrid-serverlb --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

---

## Experiment Runner Changes

### New: NodeProvisioner class

```python
class NodeProvisioner:
    """Simulates cloud node provisioning via cordon/uncordon with delay."""

    WORKLOAD_NODES = [
        "k3d-thesis-hybrid-agent-1",  # baseline (always schedulable)
        "k3d-thesis-hybrid-agent-2",
        "k3d-thesis-hybrid-agent-3",
    ]
    BASELINE_NODES = ["k3d-thesis-hybrid-agent-1"]

    def __init__(self, provision_delay_sec: int = 60):
        self.provision_delay_sec = provision_delay_sec
        self._stop_event = threading.Event()
        self._thread = None
        self._provisioned_nodes = []
        self._provision_log = []  # [(timestamp, event, node)]

    def reset(self) -> bool:
        """Reset all workload nodes: uncordon all, then cordon non-baseline."""
        self.stop()
        self._provisioned_nodes = list(self.BASELINE_NODES)
        self._provision_log = []

        # Uncordon all first (clean state)
        for node in self.WORKLOAD_NODES:
            _kubectl(["uncordon", node])

        # Cordon non-baseline nodes
        for node in self.WORKLOAD_NODES:
            if node not in self.BASELINE_NODES:
                r = _kubectl(["cordon", node])
                if r.returncode != 0:
                    logger.error("cordon_failed", node=node)
                    return False

        logger.info("node_provisioner_reset",
                    schedulable=self.BASELINE_NODES,
                    cordoned=[n for n in self.WORKLOAD_NODES if n not in self.BASELINE_NODES])
        return True

    def start_background(self) -> None:
        """Start background thread that watches for Pending pods."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._provision_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the provisioner thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

    def get_log(self) -> list:
        """Return provision events for experiment metadata."""
        return list(self._provision_log)

    def _provision_loop(self) -> None:
        """Poll for Pending warm pods → wait delay → uncordon next node."""
        cordoned = [n for n in self.WORKLOAD_NODES if n not in self._provisioned_nodes]

        while not self._stop_event.is_set() and cordoned:
            time.sleep(2)  # poll interval

            # Check for Pending test-app-warm pods
            r = _kubectl(["get", "pods", "-l", "app=test-app-warm",
                         "--field-selector=status.phase=Pending", "-o", "json"])
            if r.returncode != 0:
                continue

            pods = json.loads(r.stdout).get("items", [])
            pending_unschedulable = []
            for pod in pods:
                conditions = pod.get("status", {}).get("conditions", [])
                for c in conditions:
                    if c.get("reason") == "Unschedulable":
                        pending_unschedulable.append(pod["metadata"]["name"])

            if not pending_unschedulable:
                continue

            # Pending pod detected — start provisioning delay
            next_node = cordoned[0]
            self._provision_log.append((time.time(), "pending_detected",
                                       {"pods": pending_unschedulable, "next_node": next_node}))
            logger.info("node_provisioning_triggered",
                       pending_pods=len(pending_unschedulable),
                       next_node=next_node,
                       delay_sec=self.provision_delay_sec)

            # Wait for provisioning delay (interruptible)
            for _ in range(self.provision_delay_sec):
                if self._stop_event.is_set():
                    return
                time.sleep(1)

            # Uncordon the node
            r = _kubectl(["uncordon", next_node])
            if r.returncode == 0:
                self._provisioned_nodes.append(next_node)
                cordoned.pop(0)
                self._provision_log.append((time.time(), "node_provisioned", {"node": next_node}))
                logger.info("node_provisioned", node=next_node,
                           remaining_cordoned=len(cordoned))
            else:
                logger.error("uncordon_failed", node=next_node)
```

### Revised: ScenarioResetter.reset()

Add node provisioner reset to all scenarios that use K8s pods:

```python
def reset(self, scenario: str, provisioner: NodeProvisioner) -> bool:
    logger.info("scenario_reset_start", scenario=scenario)

    # Reset node provisioning state for scenarios with K8s workload
    if scenario in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
        if not provisioner.reset():
            logger.error("node_provisioner_reset_failed")
            return False

    if scenario == "s1-k8s-only":
        ok = self._reset_s1()
    elif scenario == "s2-serverless-only":
        ok = self._reset_s2()
    elif scenario in ("s3-hybrid-reactive", "s4-hybrid-predictive"):
        ok = self._reset_s3_s4()
    else:
        return False

    if ok:
        if not self._reset_haproxy_weights(scenario):
            return False
    return ok
```

### Revised: ExperimentRunner.run_single()

Start provisioner thread alongside daemon:

```python
def run_single(self, scenario, run_id, run_order_idx, seed):
    # ... existing setup ...

    # Reset with node provisioner
    if not self.resetter.reset(scenario, self.provisioner):
        return None

    # Start daemon
    daemon_proc = self.daemon.start(scenario, daemon_log)

    # Start node provisioner for K8s scenarios
    if scenario != "s2-serverless-only":
        self.provisioner.start_background()

    try:
        # ... existing k6 execution ...

        # Capture provisioner log
        provision_events = self.provisioner.get_log()
        # Save to run directory
        with open(run_dir / "provision_events.json", "w") as f:
            json.dump(provision_events, f, indent=2)

        # ... existing metric export ...

    finally:
        self.provisioner.stop()
        self.daemon.stop(daemon_proc)
```

### New Prometheus Queries

Add node-level metrics to MetricExporter.QUERIES:

```python
# Node provisioning metrics
"node_count_schedulable": 'count(kube_node_spec_unschedulable == 0)',
"pods_pending_count": 'count(kube_pod_status_phase{phase="Pending",namespace="default"})',
```

### New ExperimentResult Fields

```python
@dataclass
class ExperimentResult:
    # ... existing fields ...

    # Node provisioning metrics (v4)
    nodes_provisioned: int = 0          # How many nodes were uncordoned
    first_provision_delay_sec: float = 0  # Time from first Pending to first uncordon
    total_provision_events: int = 0
    provision_log_path: str = ""
```

---

## Experiment Protocol (Phase B v4)

### Pre-Experiment Setup (One-Time)

1. Destroy existing cluster: `./infrastructure/k3d/delete-cluster.sh`
2. Create multi-node cluster: `./infrastructure/k3d/create-cluster.sh` (updated)
3. Apply resource limits per node (in create-cluster.sh)
4. Label nodes (in create-cluster.sh)
5. Install Knative + Kourier: `./infrastructure/k3d/knative-install.sh` (updated)
6. Apply Knative node isolation (config-features + Kourier patch)
7. Deploy test-app-warm (with nodeSelector)
8. Deploy Knative service (with nodeSelector)
9. Start HAProxy, Prometheus (Docker — unchanged)
10. Build and push test-app image to k3d registry
11. **Verify isolation:**
    ```bash
    # All test-app-warm pods on workload nodes
    kubectl get pods -l app=test-app-warm -o wide
    # All Knative pods on infra node
    kubectl get pods -l serving.knative.dev/service=test-app -o wide
    # Workload node allocatable ~750m CPU
    kubectl describe node k3d-thesis-hybrid-agent-1 | grep -A3 Allocatable
    ```

### Per-Run Reset Procedure (Updated)

Before each run:

1. **Node reset:**
   - Uncordon all workload nodes (clean state)
   - Cordon agent-2, agent-3
   - Verify agent-1 is schedulable

2. **Autoscaler reset (scenario-dependent):**
   - S1: Delete HPA → scale to 1 → recreate HPA (cpu=50%, min=1, max=10)
   - S2: Ensure Knative scaled to zero
   - S3/S4: Delete HPA → scale to 1 → wait ready

3. **HAProxy weight reset:**
   - S1: 100/0, S2: 0/100, S3/S4: 80/20

4. **Daemon restart** with scenario flags

5. **Start node provisioner thread** (S1, S3, S4 only)

6. **Warm-up:** 30s idle

### Run Execution

1. Record t_start
2. Execute k6 ClarkNet trace replay (same as v3)
3. 60s cooldown
4. Record t_end
5. Stop provisioner thread
6. Export Prometheus metrics for [t_start, t_end]
7. Save provisioner event log

### Replication

- 5 runs × 4 scenarios = 20 runs
- Randomized order (same protocol as v3)
- 60s inter-run pause + full reset

---

## Expected Results (Hypothesis)

With node provisioning delay, we expect:

| Scenario | p99 Latency | SLO Violations | Why |
|----------|-------------|----------------|-----|
| S1 (HPA) | **High** | **High** | No fallback during 60s provisioning gap — traffic queues on 1 pod |
| S2 (KPA) | Medium | Medium | Scales freely on infra node, but cold start latency |
| S3 (Reactive) | **Medium-Low** | **Medium** | Knative absorbs burst during provisioning, but reacts after SLO breach |
| S4 (Predictive) | **Lowest** | **Lowest** | GRU predicts load → proactive Knative engagement → 30s head start |

**Key comparisons:**
- **S1 vs S3/S4:** Demonstrates hybrid value (serverless as provisioning buffer)
- **S3 vs S4:** Isolates GRU prediction value (30s earlier response)
- **S1 vs S2:** Platform baselines (constrained K8s vs unconstrained Knative)

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Workload node fits 2 pods | Medium | Verify allocatable CPU with `kubectl describe node`; reduce to 0.6 CPU if needed |
| System pods land on workload nodes | Low | kube-proxy DaemonSet is tiny (~10m CPU); won't block scheduling |
| Knative pods on workload nodes | Low | config-features + nodeSelector enforces isolation |
| k3d multi-node networking issues | Low | All nodes share Docker network; NodePort accessible from all |
| HAProxy backend IPs change | Medium | Use loadbalancer IP (stable) or update after cluster creation |
| Provisioner thread race conditions | Low | Polling with 2s interval; uncordon is idempotent |
| Host CPU contention (7 cores allocated) | Medium | Monitor with `docker stats`; reduce if needed |

---

## Implementation Checklist

- [ ] Update `infrastructure/k3d/k3d-cluster.yaml` (agents: 5)
- [ ] Update `infrastructure/k3d/create-cluster.sh` (per-node limits + labels)
- [ ] Update `infrastructure/k3d/knative-install.sh` (node isolation)
- [ ] Update `infrastructure/test-app/test-app-warm-deployment.yaml` (nodeSelector)
- [ ] Update `infrastructure/test-app/knative-service.yaml` (nodeSelector)
- [ ] Verify HAProxy backend addresses work with multi-node
- [ ] Add `NodeProvisioner` class to `scripts/run_phase_b_experiments.py`
- [ ] Update `ScenarioResetter` to integrate provisioner reset
- [ ] Update `ExperimentRunner.run_single()` to manage provisioner lifecycle
- [ ] Add provision event logging to run output
- [ ] Add node-related Prometheus queries to `MetricExporter`
- [ ] Add provision fields to `ExperimentResult`
- [ ] End-to-end test: single run of each scenario
- [ ] Verify pod Pending → uncordon → scheduling works
- [ ] Verify Knative responds immediately on infra node
- [ ] Update `THREATS_TO_VALIDITY.md` with v4 framing
- [ ] Run full 20-run experiment
- [ ] Update `EXPERIMENT_PROTOCOL.md` status

---

## Effort Estimate

| Phase | Effort | Hours |
|-------|--------|-------|
| Infrastructure (k3d config, labels, limits) | S | 1-2 |
| Scheduling isolation (nodeSelector, Knative config, Kourier patch) | S | 1-2 |
| Experiment runner (NodeProvisioner, reset, metrics) | M | 2-3 |
| End-to-end validation (single run per scenario) | M | 2-3 |
| Full 20-run experiment | L | 8-12 (mostly wall-clock) |
| **Total** | | **14-22 hours** |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-02-12 | Initial design, `duration_ms=5`, single-node |
| v2 | 2026-02-15 | Recalibrated to `duration_ms=10`; invalidated (busy-loop) |
| v3 | 2026-02-15 | Switched to `/fib?n=32`, α=0.0167; pilot confirmed mechanisms work; S1 artificial advantage discovered |
| **v4** | **2026-02-16** | **Multi-node with emulated node provisioning delay** |
