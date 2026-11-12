---
# --- bibliographic record ---
entry_type: misc
title: "Autoscaling Workloads"
authors:
  - "The Kubernetes Authors"
year: 2026
venue: "kubernetes.io documentation"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: ""
url: "https://kubernetes.io/docs/concepts/workloads/autoscaling/"

# --- archive record ---
source_pdf: kubernetes-autoscaling-workloads-docs-2026.pdf
source_sha256: 71eee9e2959b8d08cac7a807c193a6435894483a95ca596c08a10962560dd2f5
pdf_pages: 4
converted: 2026-11-12
record_source: manual
review: "web page printed to PDF on 2026-11-12 (https://kubernetes.io/docs/concepts/workloads/autoscaling/); page last modified 2025-11-23"
key_insight: "Kubernetes scales a workload automatically and horizontally with a HorizontalPodAutoscaler, a controller that adjusts the replica count to match observed CPU or memory use."
first_page: "Autoscaling Workloads With autoscaling, you can automatically update your workloads in one way or another. This allows your cluster to react to changes in resource demand more elastically and efficien"
---
### <mark></mark> 

# Autoscaling Workloads 

## Autoscaling Workloads 

With autoscaling, you can automatically update your workloads in one way or another. This allows your cluster to react to changes in resource demand more elastically and efficiently. 

In Kubernetes, you can scale a workload depending on the current demand of resources. This allows your cluster to react to changes in resource demand more elastically and efficiently. 

When you scale a workload, you can either increase or decrease the number of replicas managed by the workload, or adjust the resources available to the replicas in-place. 

The first approach is referred to as horizontal scaling, while the second is referred to as vertical scaling. 

There are manual and automatic ways to scale your workloads, depending on your use case. 

#### Scaling workloads manually 

Kubernetes supports manual scaling of workloads. Horizontal scaling can be done using the `kubectl` CLI. For vertical scaling, you need to patch the resource definition of your workload. 

See below for examples of both strategies. 

- Horizontal scaling: Running multiple instances of your app 

- Vertical scaling: Resizing CPU and memory resources assigned to containers 

Scaling workloads automatically 

Kubernetes also supports automatic scaling of workloads, which is the focus of this page. 

The concept of Autoscaling in Kubernetes refers to the ability to automatically update an object that manages a set of Pods (for example a Deployment). 

##### Scaling workloads horizontally 

In Kubernetes, you can automatically scale a workload horizontally using a HorizontalPodAutoscaler (HPA). 

It is implemented as a Kubernetes API resource and a controller and periodically adjusts the number of replicas in a workload to match observed resource utilization such as CPU or memory usage. 

There is a walkthrough tutorial of configuring a HorizontalPodAutoscaler for a Deployment. 

##### Scaling workloads vertically 

###### Ⓘ Feature State: <mark>Stable since Kubernetes v1.25</mark> 

You can automatically scale a workload vertically using a VerticalPodAutoscaler (VPA). Unlike the HPA, the VPA doesn't come with Kubernetes by default, but is a an add-on that you or a cluster administrator may need to deploy before you can use it. 

Once installed, it allows you to create CustomResourceDefinitions (CRDs) for your workloads which define how and when to scale the resources of the managed replicas. 

Note: 

You will need to have the Metrics Server installed to your cluster for the VPA to work. 

###### In-place pod vertical scaling 

###### <mark>Ⓘ Feature State: Stable since Kubernetes v1.35</mark> 

More information about this feature… 

As of Kubernetes 1.37, VPA does not support resizing pods in-place, but this integration is being worked on. For manually resizing pods in-place, see Resize Container Resources InPlace. 

##### Autoscaling based on cluster size 

For workloads that need to be scaled based on the size of the cluster (for example `cluster-dns` or other system components), you can use the Cluster Proportional Autoscaler. Just like the VPA, it is not part of the Kubernetes core, but hosted as its own project on GitHub. 

The Cluster Proportional Autoscaler watches the number of schedulable nodes and cores and scales the number of replicas of the target workload accordingly. 

If the number of replicas should stay the same, you can scale your workloads vertically according to the cluster size using the Cluster Proportional Vertical Autoscaler. The project is currently in beta and can be found on GitHub. 

While the Cluster Proportional Autoscaler scales the number of replicas of a workload, the Cluster Proportional Vertical Autoscaler adjusts the resource requests for a workload (for example a Deployment or DaemonSet) based on the number of nodes and/or cores in the cluster. 

##### Event driven Autoscaling 

It is also possible to scale workloads based on events, for example using the Kubernetes Event Driven Autoscaler (KEDA). 

KEDA is a CNCF-graduated project enabling you to scale your workloads based on the number of events to be processed, for example the amount of messages in a queue. There exists a wide range of adapters for different event sources to choose from. 

##### Autoscaling based on schedules 

Another strategy for scaling your workloads is to schedule the scaling operations, for example in order to reduce resource consumption during off-peak hours. 

Similar to event driven autoscaling, such behavior can be achieved using KEDA in conjunction with its `Cron` scaler. The `Cron` scaler allows you to define schedules (and time zones) for scaling your workloads in or out. 

#### Scaling cluster infrastructure 

If scaling workloads isn't enough to meet your needs, you can also scale your cluster infrastructure itself. 

Scaling the cluster infrastructure normally means adding or removing nodes. Read Node autoscaling for more information. 

#### What's next 

- Learn more about scaling horizontally 

   - Scale a StatefulSet 

   - HorizontalPodAutoscaler Walkthrough 

- Resize Container Resources In-Place 

- Autoscale the DNS Service in a Cluster 

- Learn about Node autoscaling 

#### Feedback 

Was this page helpful? 

Yes No 

Last modified November 23, 2025 at 1:47 PM PST: Move HorizontalPodAutoscaler concept page (57e1fdd7f9) 

