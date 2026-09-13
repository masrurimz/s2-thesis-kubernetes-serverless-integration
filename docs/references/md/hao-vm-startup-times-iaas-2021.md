---
# --- bibliographic record ---
entry_type: misc
title: "An Empirical Analysis of VM Startup Times in Public IaaS Clouds: An Extended Report"
authors:
  - "Jianwei Hao"
  - "Ting Jiang"
  - "Wei Wang"
  - "In Kee Kim"
year: 2021
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2107.03467"
url: "https://arxiv.org/abs/2107.03467"

# --- archive record ---
source_pdf: hao-vm-startup-times-iaas-2021.pdf
source_sha256: 832abae195d4574b3dcb956240fdbac198c5684455456dca789e9a63e2d279cf
pdf_pages: 13
converted: 2026-09-13
record_source: arxiv
key_insight: "3-month measurement (AWS+GCP, 300K+ points/provider): cold startup AWS Linux 55.9 s / Windows 89.7 s, GCP Linux 124.1 s / Windows 107.5 s; warm 22-34 s; t2 avg 85.15 s, 90th pct 158.22 s. Brackets the K3dAutoscaler's simulated 45-120 s node-provision delay"
first_page: "An Empirical Analysis of VM Startup Times in Public IaaS Clouds: An Extended Report Jianwei Hao†∗, Ting Jiang†∗, Wei Wang‡, and In Kee Kim† †University of Georgia, Department of Computer Science, {jha"
---
# An Empirical Analysis of VM Startup Times in Public IaaS Clouds: An Extended Report 

Jianwei Hao<sup>_†∗_</sup> , Ting Jiang<sup>_†∗_</sup> , Wei Wang<sup>_‡_</sup> , and In Kee Kim<sup>_†_</sup> 

_†_ University of Georgia, Department of Computer Science, _{_ jhao, ting.jiang1, inkee.kim _}_ @uga.edu 

_‡_ The University of Texas, San Antonio, Department of Computer Science, wei.wang@utsa.edu 

**_Abstract_ —VM startup time is an essential factor in designing elastic cloud applications. For example, a cloud application with autoscaling can reduce under- and over-provisioning of VM instances with a precise estimation of VM startup time, and in turn, it is likely to guarantee the application’s performance and improve the cost efficiency. However, VM startup time has been little studied, and available measurement results performed previously did not consider various configurations of VMs for modern cloud applications.** 

**In this work, we perform comprehensive measurements and analysis of VM startup time from two major cloud providers, namely Amazon Web Services (AWS) and Google Cloud Platform (GCP). With three months of measurements, we collected more than 300,000 data points from each provider by applying a set of configurations, including 11+ VM types, four different data center locations, four VM image sizes, two OS types, and two purchase models (e.g., spot/preemptible VMs vs. on-demand VMs). With extensive analysis, we found that VM startup time can vary significantly because of several important factors, such as VM image sizes, data center locations, VM types, and OS types. Moreover, by comparing with previous measurement results, we confirm that cloud providers (specifically AWS) made significant improvements for the VM startup times and currently have much quicker VM startup times than in the past.** 

**_Index Terms_ —Performance Measurement and Analysis; VM Startup Time; IaaS; Cloud Computing;** 

## I. INTRODUCTION 

For the last decade, cloud computing has become a primary computing infrastructure as many applications have been increasingly migrated from on-premise environments to clouds [1]–[4]. At the same time, cloud infrastructure itself has been continuously evolving so that cloud computing currently offers diverse resource models, such as VMs, containers [5], [6] and orchestration [7], [8], and cloud functions [9]–[11], to support various application types and service scenarios. While VMs are the most traditional resource type in the clouds, VMs are still widely used as common hosting platforms for both user applications and different resource models, like containers [12], Kubernetes [13], and serverless/cloud functions [14]. 

Various aspects of performance implications in VMs and IaaS (Infrastructure as a Service) clouds, such as Amazon EC2, have been extensively studied [15]–[25]. The measurement results are widely adopted for developing novel cloud applications and cloud infrastructure management systems. In particular, understanding VM startup time [25]–[27] is crucial to design elastic resource management systems for cloud applications, such as autoscaling [28], [29]. According to a 

* Both authors contributed equally. 

previous study [25] performed in 2012, VM startup time could vary significantly due to various factors, such as VM image sizes, time-of-day, VM purchase models (on-demand or spot), etc. While the measurement results from the previous work are still useful to current cloud research, a number of mechanisms have been proposed for optimizing VM startup processes in cloud data centers for the last decade [30]–[37]. Therefore, it is important to see whether there is an improvement of VM startup time in public cloud providers. 

This work aims to provide _up-to-date_ information about VM startup time to the research community so that cloud researchers and practitioners facilitate the design of novel resource and performance management approaches for cloud applications. To this end, we performed an empirical analysis of VM startup times, measured from two widely-used public cloud services, namely AWS (Amazon Web Services) [2] and GCP (Google Cloud Platform) [3]. The measurement was conducted for three months with extensive trials. Each trial was performed for at least 14 consecutive days to cover the temporal impact (time-of-day, date-of-week) [16], [18], [38] on VM startup time. In total, we obtained more than 300,000 data points from each provider by exploiting a different set of factors that can change the VM startup time. The data was collected by using 11+ widely-used VM types, which are commonly hosted in four service regions, located in the U.S., Europe, and Asia. Four VM image sizes (from 32GB to 256GB), two different OS types (Linux and Windows), and two VM purchase models (on-demand and spot/preemptible) were also applied. Moreover, we measured two different types of VM startup time; a _cold startup_ and _warm startup_ time. The cold startup time means the VM’s startup time when a user creates a new VM so that this startup time is equivalent to the VM’s creation (provisioning) time. The warm startup time is the startup time measured when a user (re)starts an existing (and stopped) VM instance. 

This paper reports (cold/warm) VM startup times of AWS and GCP with diverse configurations for realistic VM usecases. With extensive analysis, we found that VMs’ startup time could be significantly changed due to several factors, such as OS types, VM image sizes, VM types (and generation), and locations/regions. Table I summarizes our analysis and important factors for changing VM startup times. 

After identifying the critical factors for VM startup times, we compare our analysis results with the previous studies [25], [27]. The comparison confirms that cloud providers 

1 

TABLE I 

IMPORTANT FACTORS AND ANALYSIS RESULTS OF VM STARTUP TIMES. 

|**Category**|**Provider**|**Observation**|**Proof**|
|---|---|---|---|
|OS|Both|**AWS VMs have faster startup times than VMs in GCP.** AWS VMs showed 2.22_×_ (Linux VMs) and<br>1.2_×_ (Windows VMs) shorter cold startup times compared to VMs in GCP.|Table IV|
|Types|AWS|**Linux VMs have a 38% shorter cold startup time** than Windows VMs.|Table IV|
||GCP|**Windows VMs have 15% – 46% shorter startup times** compared to Linux VMs.|Table IV|
|Image|AWS|**AWS VMs’ startup times are independent of the VM image size**, showing that VMs with different<br>image sizes often have similar startup time.|Fig. 1|
|Size|GCP|**VM’s startup times have a positive correlation with the VM image size.** i.e., Startup times of VMs<br>with 128GB (of the image size) are longer than that of VMs with 64GB.|Fig. 3|
|||**A caching-based mechanism is used to boost VM startup process** by temporarily storing recently used<br>VM images. VM startup times. This mechanism can (sometimes) diminish the impact of VM image sizes.|Fig. 5 and<br>Table V|
||Both|**Different VM types have different startup times.**|Fig. 6 and 8|
|Instance|AWS|**The older generation VM types have longer startup times** than the newer generation VM types.|Fig. 7|
|Type|GCP|**The older generation Linux VMs have longer startup times** than the newer generation Linux VMs.<br>|Fig. 10|
|||Windows VMs can be the opposite. **Newer (e.g., 2**<sup>**nd**</sup>**) generation VMs can have longer startup times**<br>**than older (e.g., 1**<sup>**st**</sup>**) generation VMs.**|Fig. 10|
|Location|AWS|On average, VMs in different regions have similar startup times. But, **VMs in different zones in each**<br>**region have substantially different startup times (up to 45%).**|Fig. 11 and 12|
||GCP|**VMs in different regions show distinct VM startup times.** Moreover, **VMs in different zones often**<br>**show significant changes (up to 50%) in VM startup times within the same region.**|Fig. 11 and 13|
|Purchase<br>Model|Both|Spot (AWS) and preemptible (GCP) VMs have similar startup time compared to on-demand VMs,<br>indicating that **spot or preemptible VMs no longer have slower startup times than on-demand VMs.**|Fig. 14 and<br>Table VIII|



(specifically AWS) made significant improvements for the VM startup times and currently have much quicker VM startup times. Moreover, implications and findings from this study will help various research in cloud resource and application management. In particular, autoscaling algorithms [28], [29], [39]–[43] with the accurate VM startup time can determine the exact scaling point for handling increased user demands. And, cloud simulators [44]–[48] can generate more reliable simulation results with this study. 

It is worth noting that this paper is an extended version of our previous work [49], which is published in the 2021 IEEE International Conference on Cloud Computing (IEEE CLOUD). This version of the paper contains additional measurements and analysis on VM start times in AWS and GCP, which are not included in the IEEE CLOUD 2021 version. 

As a result, this work has the following contributions. 1. We performed a thorough measurement study on VM startup time of two major cloud providers; AWS and GCP, which are widely used in research and industry. 

2. With three months of measurement, we collected a large number of data points with various VM configurations, reflecting the realistic use-cases of VMs in clouds. 

3. We report VM startup times, in AWS and GCP, with diverse configurations. With extensive analysis, we found several factors that considerably change the VM startup times. 

4. We found that GCP uses a cache-based approach to reduce VMs’ startup time. Recently used VM images are stored in the GCP data center for the next 75 – 100 minutes, and users can benefit from using cached VM images to reduce VM startup times. 

We structure the rest of the paper as follows. Section II describes the experimental setup for measuring VM startup time. Section III reports the measurement results of VM startup times from both AWS and GCP. Section IV provides 

a comparison with previous works. Section V summarizes related work. Finally, Section VI concludes this paper. 

## II. MEASUREMENT METHODOLOGY 

This section describes the methodology for measuring VM startup time from two public cloud providers. 

## _A. Measurement Setup_ 

We considered diverse factors that can lead to changing the VM startup time. The following configurations were used for this measurement to collect VM startup times with more realistic scenarios. 

**Cloud Providers.** We measured VM startup time from AWS [2] and GCP [3]. Because these two providers are widely used in both industry and academic research, it is crucial to see if there VM startup time differences exist in both providers. We used VMs from AWS EC2 and Google Compute Engine, which are IaaS models of these providers. 

**Measurement Period.** The measurement was conducted for three months in 2020 with a set of trials. Each measurement trial has at least two-weeks of duration to check there are temporal impacts on the VM startup time, such as time-ofday, day-of-week. 

**Data Center Locations (Regions and Availability Zones).** Table II describes the regions and (availability) zones of two providers used for this measurement. We chose four regions, located in the U.S. (east and west), Europe, and Asia, to check any correlations between cloud data center locations and the VM startup times. Moreover, each region has multiple zones so that we measured VM startup time from all the zones listed in Table II to see if there are VM startup time fluctuations with different (availability) zones in the regions. 

**Instance Types.** Table III shows 12 VM types from AWS and 11 VM types from GCP, used in the measurement to check 

2 

TABLE II 

DATA CENTER REGIONS AND (AVAILABILITY) ZONES. 

|**Provider**|**Region**|**Zones**|**Location**|
|---|---|---|---|
||us-east-1|5 Zones (a – d, f)|N. Virginia|
|AWS|us-west-2|3 Zones (a – c)|Oregon|
||eu-west-3|3 Zones (a – c)|Paris|
||ap-southeast-1|3 Zones (a – c)|Singapore|
||us-east4|3 Zones (a – c)|N. Virginia|
|GCP|us-west1|3 Zones (a – c)|Oregon|
||europe-west1|3 Zones (b – d)|Belgium|
||asia-southeast1|3 Zones (a – c)|Singapore|



TABLE III 

VM TYPES USED FOR MEASUREMENT. 

|**Class**|**#vCPU**|**Mem**<br>**(GB)**|**AWS**<br>**VM Types**|**GCP**<br>**VM Types**|
|---|---|---|---|---|
|tiny|0.5-1|0.5-1|t2.nano,<br>t2.micro,<br>t3.nano,<br>t3.micro|f1-micro|
|small|1-2|1.7-2|t2.small,<br>t3.small|g1-small|
|medium|1-2|3.75-4|t3.medium,<br>t3a.medium|n1-standard-1|
|large|2|7.5-8|m4.large,<br>m5a.large|n1-standard-2,<br>n2-standard-2,<br>n2d-standard-2,<br>e2-standard-2|
|xlarge|4|15-16|m4.xlarge,<br>m5.xlarge|n1-standard-4,<br>n2-standard-4,<br>n2d-standard-4,<br>e2-standard-4|
||Total||**12 Types**|**11 Types**|



the VM startup time differences in various instance types. We categorized these VM types into five VM classes: tiny, small, medium, large, and xlarge classes. This classification is based on the memory size of VM types. VM types in each class are not exactly the same, but almost equivalent VM types were chosen from both cloud providers. Moreover, when selecting instance types for the measurement, we considered VMs with different generations and CPU models. For example, we measured the startup time from both t2.small and t3.small instances (in the Small class) from AWS to see if there is the VM startup time difference from the equivalent VM instances with different generations. For the diversity of CPU models, we used t3a.medium and m5a.large with AMD CPUs from AWS. n2 (Intel), n2d (AMD), and e2 (Intel or AMD) instance types from GCP were used for the measurement to check the VM startup time differences due to different CPU models. 

**OS Types and VM Image Sizes.** We tested the VM startup times with two different operating systems (Linux and Windows). We used Ubuntu 18.04 LTS for Linux VMs and Windows Server 2016 for Windows VMs. For the VM image sizes, we used four different sizes of user-created VM images, which are 32GB, 64GB, 128GB, and 256GB. The VM images were fully filled by OS and other binary/data files. 

**VM Purchase Models.** Both on-demand and low-availability VM models were used for the measurement. The spot in- 

TABLE IV 

COLD AND WARM STARTUP TIMES OF LINUX AND WINDOWS VMS IN AWS AND GCP 

|**OST**|**Cold **|**Startup**|**Warm **|**Startup**|
|---|---|---|---|---|
|**ype**|**AWS**|**GCP**|**AWS**|**GCP**|
|Linux VM|55.9s|124.1s|34.0s|32.8s|
|Windows VM|89.7s|107.5s|24.5s|22.2s|



stance model [50] (from AWS) and the preemptible instance model [51] (from GCP) were used for the low availability models. Specifically, it is interesting to measure the VM startup time from two different VM purchase models because spot/preemptible instances can have different provisioning processes or a different level of availabilities compared to the on-demand models. 

## _B. Measurement Procedure_ 

To measure the VM startup time, we did not rely on the VM status information provided by the cloud providers because the VM status is often inaccurate [25], [52]. Instead, we implemented and deployed applications that collect VM startup times by interacting with both cloud providers. The measurement applications calculated the VM startup time based on the very first successful remote access to the target VM. For example, suppose _trequest_ is a time to call cloud APIs to start a VM, and _taccess_ is the first time to successfully access (e.g., login) the VM via ssh or RDP. Then, a VM’s startup time can be calculated by _taccess − trequest_ . 

We measured both cold startup (VM provisioning time) and warm startup time (startup time of an existing VM) of VMs. Both startup times of a VM were measured sequentially. During the measurement period, we measured the cold startup time of VMs every hour on the hour, and then, measured the warm startup time after several minutes. For example, a measurement application sent a request for creating a VM to the providers (via AWS boto3 [53] or Google Cloud APIs [54]) at the top of the hour (e.g., 1 a.m.), and the **cold VM startup time** was measured when the measurement application could successfully access the VM. Then, the measurement application stopped the VM. After several minutes (e.g., at 1:10 a.m.), the application sent another request to start the VM and measured the **warm VM startup time** of the VM with successful remote access, and then, the VM was finally terminated. It is worth noting that the VM startup time generally means the cold VM startup time in this work because we found that the cold startup time varies more significantly as per diverse factors, and the warm startup time is fairly consistent in both providers. 

## III. MEASUREMENT RESULTS AND ANALYSIS 

Our measurement collected more than 300,000 data points from each provider. These data include both warm and cold startup times measured with a set of different configurations in Section II. In total, we measured VM startup time with 768<sup>1</sup> 

> 1768 is calculated by 2 (Linux or Windows) _×_ 12 (VM types) _×_ 4 (Image sizes) _×_ 4 (Regions) _×_ 2 (On-demand or Spot) 

3 



<!-- Start of picture text -->
(a) Linux VM Startup Time (b) Windows VM Startup Time<br> 200  200<br>Cold Start Cold Start<br>Warm Start Warm Start<br> 150  150<br> 100  100<br> 50  50<br> 0  0<br>32G 64G 128G 256G 32G 64G 128G 256G<br>VM Image Size VM Image Size<br>Fig. 1. (AWS) VM startup times with different VM image sizes<br>0.03 0.06<br>0.02 0.04<br>0.01 Stragglers 0.02<br>0.00 0.00<br>0 100 200 300 400 0 100 200 300 400<br>Startup Time (sec.) Startup Time (sec.)<br>Startup Time (Sec.) Startup Time (Sec.)<br>Probability Density Probability Density<br><!-- End of picture text -->

(b) Warm Startup: Linux VM (256G) 

(a) Cold Startup: Linux VM (64G) 

Fig. 2. Startup time distribution of AWS Linux VMs 

(for AWS) and 704<sup>2</sup> (for GCP) different configurations, and the number of collected samples in each configuration has a range from 350 to 1500. For each configuration, we ensured there were enough samples to obtain accurate VM startup measurement results with high confidence using a method proposed by prior work [55]. 

## _A. OS Types_ 

Different OS types for VMs are widely-recognized factors that can impact VM startup times as per the previous works [25], [30], [32]. Therefore, it is important to see if this factor still changes VM startup time. To confirm the impact of OS types on VM startup times, we measured the VM startup time using Linux and Windows VMs with four different VM image sizes (from 32GB to 256GB). 

Table IV reports the average VM startup times of both Linux and Windows instances in AWS and GCP. For the cold startup times, AWS VMs had shorter startup times than the VMs in GCP. In particular, GCP VMs showed 2.22 _×_ , (Linux VMs) and 1.2 _×_ (Windows VMs) slower startup times compared to the AWS VMs. Regarding the warm startup times, both providers showed similar startup times, and warm startup time is much shorter than cold startup time. The shorter time of the warm startup case is mainly because the VM images are already stored in the physical machine so that the warm startup process does not have any delays from VM image transfer. 

Regarding OS impacts for VM startup times, we confirmed that OS types are still impacting the VM startup times based on the measurement result that both cloud providers showed different VM startup times between Linux and Windows VMs. For example, Linux VMs in AWS showed (40%) faster startup 

> 2704 is calculated by 2 (Linux or Windows) _×_ 11 (VM types) _×_ 4 (Image sizes) _×_ 4 (Regions) _×_ 2 (On-demand or Preemptible) 



<!-- Start of picture text -->
(a) Linux VM Startup Time (b) Windows VM Startup Time<br> 200  200<br>Cold Startup<br>Warm Startup<br> 150  150<br> 100 Cold Startup  100<br>Warm Startup<br> 50  50<br> 0  0<br>32G 64G 128G 256G 32G 64G 128G 256G<br>VM Image Size VM Image Size<br>Startup Time (Sec.) Startup Time (Sec.)<br><!-- End of picture text -->



<!-- Start of picture text -->
Fig. 3. (GCP) VM startup times with different VM image sizes<br>0.10<br>0.010 Faster<br>Startup<br>0.05<br>0.005<br>0.000 0.00<br>0 100 200 300 400 0 50 100 150 200<br>Startup Time (sec.) Startup Time (sec.)<br>Probability Density Probability Density<br><!-- End of picture text -->

(a) Cold Startup: Linux VM (128G) (b) Warm Startup: Linux VM (64G) 

Fig. 4. Startup time distribution of GCP Linux VMs 

times than Windows VMs, whereas, in GCP, Windows VMs had (13%) faster startup times than Linux VMs. 

**Observation#1: Different OS types** 

- AWS VMs have faster startup time VMs in GCP. 

- _•_ In AWS, the startup times of Linux VMs are 40% faster than Windows VM, but GCP shows the opposite results. 

## _B. VM Image Sizes_ 

VM image size is another widely accepted factor regarding the variability in the VM startup times [25]. We measure VM startup times with various VM image sizes (from 32GB to 256GB) in AWS and GCP to confirm that VM image size is still changing startup times. 

Fig. 1 reports average startup times of AWS Linux and Windows VMs with four different VM image sizes. The results also show both cold and warm startup times of the VMs. Unlike the previous findings, our measurement results confirm that AWS VMs had almost constant startup time regardless of their image sizes. We observed such constant patterns from both OS systems as well as both warm and cold startup times. The maximum startup time difference between the smallest (32GB) and the largest (256GB) image sizes is only 2% – 3% (Linux VMs). This result is clearly different from the widely used assumption that VM startup processes take longer as VM image size increases. We assume that AWS could leverage several optimizations (described in Section V) to provide constant startup time regarding this improvement. 

However, the results only show the average startup times, so we also analyzed the distributions of VM startup times with the same image sizes. As shown in Fig. 2, we observed that the VM startup times had multi-modal distributions, indicating 

4 

TABLE V 

VM IMAGE CACHING PERIOD IN GCP. 

|**GCP Region**<br>**Cache **|**Period (Minutes)**|
|---|---|
|us-east4 (N. Virginia)|75 – 95|
|us-central1 (Iowa)|75 – 100|
|us-west1 (Oregon)|70 – 85|
|europe-west1 (Belgium)|70 – 95|
|asia-southeast1 (Singapore)|75 – 85|



that there were (straggler) VMs that have slow startup times. Specifically, such straggler VMs were clearly observed in AWS VM’s cold startup times (e.g., Fig. 2a). We think such slow VM startup times were affected by other factors that we investigate later in this section. 

Fig. 3 reports VM startup times with different image sizes measured from GCP. The GCP results showed that GCP VMs’ startup times had a positive correlation with the VM image sizes, which is different from the AWS results. As shown in the figure, the GCP VMs’ cold startup time increased as the VM image size increased, and both Linux and Windows VMs showed the same patterns in the change of VM startup time. The measurement results with cold startup time confirm that the VM image sizes are still impacting the VM startup times in GCP. Unlike the cold startup times, the warm startup times of GCP VMs were constant and stable regardless of the VM image sizes. However, stable warm startup times are expected because cloud providers can reuse existing VM images when warm startups are performed. 

Fig. 4 shows the distributions of both cold and warm startup times from GCP Linux VMs. An interesting observation from the distributions is that the GCP measurement results had bimodal distributions. In particular, a group of VMs had faster VM startup times than the majority of measured VMs (shown in Fig. 4a). Our further analysis revealed that the group of VMs having faster startup times was because of GCP’s caching mechanism, which is described below. 

**VM Image Cache Period in GCP.** As one of the major contributions of this work, we found and analyzed GCP’s _VM image cache mechanism_ that effectively reduces the startup time and possibly offers near-constant VM startup time (regardless of its image size). Based on our measurements, we found that the cache-based approach works similarly to several VM startup time reduction mechanisms proposed by the research community [30], [35], [56]. The below procedure explains the VM image caching mechanism used in GCP. 

- 1) If a user creates a VM in a data center (a zone in a region) based on a specific VM image, which has not been used for a certain period of time ( **cache period** ) in the data center, the VM image is transferred from an image repository in GCP to the data center. And the VM is created based on the transferred VM image, and then, the image is stored in the data center. In this step, the VM startup time follows the pattern reported in Fig. 3. 

- 2) If a user creates another VM based on the VM image (used in step 1) in the same data center _within the cache_ 



<!-- Start of picture text -->
(a) Linux VMs (b) Windows VMs<br> 200  200<br>Uncached Uncached<br>Cached Cached<br> 150  150<br> 100  100<br> 50  50<br> 0  0<br>32G 64G 128G 256G 32G 64G 128G 256G<br>VM Image Size VM Image Size<br>VM Startup Time (Sec.) VM Startup Time (Sec.)<br><!-- End of picture text -->

Fig. 5. (GCP) Startup time differences with cached images. 

_period_ , the VM is created using the VM image stored in the data center. In this case, the cold startup time (VM creation time) is much faster than step 1 because there is no delay from the VM image transmission. 

- 3) If the VM image is no longer used over the cache period, the VM image is removed from the data center. 

The VM image caching is only beneficial when a user creates the VM based on a previously used VM image in the same data center (zone) within the cache period. If the user creates a VM, based on the same image, in the _different_ data center (zone) of the same region, then this mechanism does not work even within the cache period. So it is important to know the exact cache period of storing VM images in GCP. Table V reports the VM image cache period in the five GCP regions. These results also include the cache period in all zones in the five regions. As shown in Table V, GCP data centers generally have 70 – 100 minutes of VM image cache period. Within this period, the cold startup time of a VM with a prestored (cached) image is much faster than the startup time without cache. 

Fig. 5 shows the difference in VM cold startup time with and without cached VM image. VMs with cached images showed much faster cold startup times compared to the uncached cases. With this cache mechanism, VM can reduce startup time by 60% (Linux VM) and 27% (Windows VM). 

## **Observation #2: Different VM image sizes** 

- AWS VMs show near-constant VM startup times re- 

- gardless of their image sizes. (However, there are some straggler VMs.) 

- In GCP, VM image sizes still impact the VM startup 

- times. However, the startup times can decrease with GCP’s internal caching mechanism. GCP’s data centers keep recently created VM images for the next 75-10 minutes; thus, GCP can provide near-constant startup times when recreating VMs (based on the same image) within the cache period. 

## _C. Instance Types_ 

We also measured VM startup time variations of different VM types. As listed in Table III (in Section II), we used 12 VM types from AWS and 11 VM types from GCP. These 

5 



<!-- Start of picture text -->
 180<br>90%ile Startup Time<br> 150<br>Average Startup Time<br> 120<br> 90<br> 60<br> 30<br> 0<br>     m4      m5<br>t2 (previous gen.) t3 (current gen.) (prev gen) (curr gen)<br>Fig. 6. (AWS) Cold startup times of different VM types. This graph contains<br>measurement results from on-demand Linux VMs (with all image sizes).<br>Average Startup Time of Previous Generation VM Types<br> 1<br>32% 12%<br> 0.8 53% Diff. 70% Diff.<br>Diff. Diff.<br> 0.6<br> 0.4<br> 0.2<br> 0<br>t2 inst. vs. t3 inst. t2 inst. vs. t3 inst. t2.nano vs. m4 inst. vs. m5 inst.<br>(include all types) (w/o nano type) t3.nano<br>Startup Time (Sec.)<br>t2.nano t2.micro t2.small t2.med t3.nano t3.micro t3.small t3a.med m4.lg m4.xlg m5a.lg m5.xlg<br>Relative VM Startup Time<br><!-- End of picture text -->

Fig. 6. (AWS) Cold startup times of different VM types. This graph contains measurement results from on-demand Linux VMs (with all image sizes). 

Fig. 7. (AWS) Cold startup time comparison of VMs between older and newer VM types. This graph only contains measurement results from ondemand Linux VMs. 

instance types include shared core (or burstable) and generalpurpose instances. Fig. 6 reports the average and 90%ile cold startup time variations of 12 instance types in AWS. Please note that the results are only reporting the cold startup times of different VM types with Linux OS, and all image sizes are considered for calculating the results as the VM image sizes do not meaningfully impact the startup times. We omit the results from Windows instances, and the results with Windows VMs had a similar pattern to the results reported in Fig. 6. Among AWS instances, t2 instances (previous generation of burstable instances) showed significantly longer startup time compared to other instance types. t2 instances had 85.15 seconds of average and 158.22 seconds of 90%ile of startup time. In particular, t2.nano, the smallest instance type in AWS (with 1 vCPU and 0.5GB memory), showed the most unstable and longest cold startup time among 12 AWS instances. For other instance types (t3, m4, and m5), the VM types tended to have similar cold startup time with other VM types in the same instance family. 

We also observed that different generations in the same purpose instance types (e.g., t2 vs. t3, m4 vs. m5) could have differences in VM startup time. We measured the differences in cold startup times between older and newer generation instances. Fig. 7 shows the comparison results between t2 and t3, as well as m4 and m5 instances. Regarding the comparison between t2 and t3, we also report the results with including, excluding, and solely comparing nano types because t2.nano showed substantially slower startup time. As shown in Fig. 7, the newer generation instances showed faster cold 



<!-- Start of picture text -->
 180<br>Avg. 90%<br> 150 Start- Start-<br>up up<br> 120 Time Time<br> 90<br> 60<br> 30<br> 0<br>Shared Core n1 (Prev. Gen.) n2/n2d/e2 (Current Generation)<br>Fig. 8. (GCP) Cold startup times of different VM types with Linux OS (with<br>64GB image size).<br> 180 Avg. 90%<br> 150 Start- Start-<br> 120 up Time uTimep<br> 90<br> 60<br> 30<br> 0<br>Shared Core n1 (Prev. Gen.) n2/n2d/e2 (Current Generation)<br>Startup Time (Sec.)<br>f1-micro g1-small n1-std-1 n1-std-2 n1-std-4 n2-std-2 n2-std-4 n2d-std-2 n2d-std-4 e2-std-2 e2-std-4<br>Startup Time (Sec.)<br>f1-micro g1-small n1-std-1 n1-std-2 n1-std-4 n2-std-2 n2-std-4 n2d-std-2 n2d-std-4 e2-std-2 e2-std-4<br><!-- End of picture text -->

Fig. 8. (GCP) Cold startup times of different VM types with Linux OS (with 64GB image size). 

Fig. 9. (GCP) Cold startup times of different VM types with Windows OS (with 32GB image size). 

startup times than the older instance types in AWS. For example, t3 instances had 53% to 32% (without nano types) faster startup times compared to t2 instances. Specifically, the average startup time of t3.nano was 70% faster than that of t2.nano, and t2.nano only took 36.87 seconds on average. Regarding the general-purpose instances (m4 and m5), the time differences between two instance families are smaller than t-instances, and the results showed that m5 (newergeneration) instances had 12% faster cold startup time than m4 (older-generation) instances. 

Fig. 8 and 9 show the cold startup time variations of 11 VM types in GCP. Fig. 8 contains the measurement results from Linux VMs with 64GB image size, and Fig. 9 has the measurement results from Windows VMs with 32GB image size. We omit the results with other image sizes because the measurements with other image sizes showed similar results with Fig. 8 and 9. Regarding VM types with Linux OS (Fig. 8), share-core (f1-small and g1-micro) and n1<sup>3</sup> instances showed slower (up to 42%) VM startup time than n2, n2d, and e2-standard instances<sup>4</sup> . In other words, the first (previous) generation VM types (f1/g1/n1) had longer startup time compared to the second (current) generation VM types (n2/n2d/e2) with Linux OS in GCP. 

> 3n1 instances are the first generation general-purpose machine type in GCP [57]. n1 instances use one of the following Intel CPU models; Skylake, Broadwell, Haswell, Sandy Bridge, and Ivy Bridge CPU 

4n2, n2d, and e2-standard instances are the second-generation general purpose VM types in GCP [57]. n2 VMs run on Intel Cascade Lake CPUs, n2d VMs are based on AMD EPYC Rome processors, and e2 instances are running on available CPU platforms from either Intel or AMD. 

6 



<!-- Start of picture text -->
N1 N2 N2D E2<br> 1.2 Previous Generation VM Types 12%⬆ 10%⬆<br> 1<br> 0.8 24%⬇ 9%⬇<br>36%⬇<br> 0.6<br> 0.4<br> 0.2<br> 0<br>Linux VMs Types Windows VM Types<br>Fig. 10. (GCP) Cold startup time comparison of (on-demand) VMs between<br>older and newer VM types.<br>(a) AWS Regions (b) GCP Regions<br> 200  200<br>Average<br>90%ile<br> 150  150<br> 100  100<br> 50  50<br>Average<br>90%ile<br> 0  0<br>US-E. US-W. EU Asia US-E. US-W. EU Asia<br>Relative VM Startup Time<br>VM Startup Time VM Startup Time<br><!-- End of picture text -->

Fig. 10. (GCP) Cold startup time comparison of (on-demand) VMs between older and newer VM types. 

Fig. 11. Average and 90%ile VM cold startup times in different regions. (a) AWS VM startup times in four regions. US-E.: us-east-1 (N.Va), US-W.: us-west-2 (Oregon), EU: eu-west-3 (Paris), and Asia: ap-southeast-1 (Singapore). (b) GCP VM startup times in four regions. US-E.: us-east4 (N.Va), US-W.: us-west1 (Oregon), EU: europe-west1 (Belgium), and Asia: asia-southeast1 (Singapore). 

However, the measurement results from Windows VMs (Fig. 9) are different from the results with Linux VMs (Fig. 8). While the n2D (second generation) instances showed the fastest VM startup times, the first generation Windows VMs (e.g., shared-core and n1 instances) had shorter startup time than other second generation (n2/e2) instances. The cold startup time differences between the first and second generation VMs in GCP are summarized in Fig. 10. In general, the newer generation instance types are 9% – 36% faster in startup time than the older generation instance types with Linux, but, the startup times from the newer generation VM types with Windows can be slower (10% – 12%) than the startup times from the older generation VM types. 

**Observation #3: Different instance types** 

- In AWS, the t2 family shows significantly longer 

- startup time than other instance types. Specifically, t2-nano is the slowest instance among 12 VM types. 

- In AWS, newer generation VM types (e.g., t3 and m5 

- family) show 12% – 70% faster startup time than old generation VM instance types (e.g., t2 and m4). 

- In GCP, older generation (f1/g1/n1) VMs with 

- Linux OS show slower startup times than newer generation VMs (e.g., n2/e2), but Windows VMs report the opposite results. 



<!-- Start of picture text -->
Avg. (All Reg.) 90% (All Reg.) Avg. (Zone) 90% (Zone)<br> 180<br> 150<br> 120<br> 90<br> 60<br> 30<br> 0<br>ZA ZB ZC ZD ZF ZA ZB ZC ZA ZB ZC ZA ZB ZC<br>us-east-1 us-west-3 eu-west-3 ap-southeast-1<br>VM Startup Time (Sec.)<br><!-- End of picture text -->

Fig. 12. (AWS) Average and 90%ile VM cold startup times in 14 different zones. (ZA – ZF: Zone A to Zone F.) 



<!-- Start of picture text -->
Avg. (All Reg.) 90% (All Reg.) Avg. (Zone) 90% (Zone)<br> 200<br> 150<br> 100<br> 50<br> 0<br>ZA ZB ZC ZA ZB ZC ZB ZC ZD ZA ZB ZC<br>us-east4 us-west1 europe-west1 asia-southeast1<br>VM Startup Time (Sec.)<br><!-- End of picture text -->

Fig. 13. (GCP) Average and 90%ile VM cold startup times in 12 different zones. (ZA – ZD: Zone A to Zone D.) 

## _D. Regions and Data Center Locations_ 

In this subsection, we analyzed the VM startup time variations in different regions. Fig. 11 shows the average and 90%ile (cold) VM startup times in four different regions (U.S. east, U.S. west, EU, and Asia) from both providers. Please note that the results in Fig. 11 were collected from on-demand Linux VMs. We omit the results from Windows VMs because they showed similar results with the Linux VMs. As shown in Fig. 11(a), the four regions in AWS had relatively consistent and stable VM cold startup times. The maximum difference in the four regions was only 5.02 seconds on average. However, the VM (cold) startup times (both average and 90%ile) of GCP varied considerably with different regions. The maximum startup time difference was about 40 seconds on average, which is 32% of average startup times of all four regions. Among four regions us-east4 (US-E., N.Va) was the fastest region and us-west1 (US-W., Oregon) showed the longest VM startup times. 

We further analyzed the VM startup times per zones, and Fig. 12 reports the Linux VM startup time differences in 14 zones that belong to four AWS regions. Although AWS showed similar VM startup times in four regions (in our previous analysis), the VM startup times were fluctuating as per we choose different zones even within the same region. Among 14 zones we measured in AWS, 3 zones (ZA in us-west-2, ZB in us-east-1, and ZA in ap-east-1) had at least 20% longer startup time compared to the average startup time of all four regions. VMs in another 3 zones (ZB in us-west-2, ZA and ZB in eu-west-3) had 11% to 17% 

7 



<!-- Start of picture text -->
 1.4 On-Demand<br> 1.2<br> 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br>Avg. (Zone)<br> 0<br>t2.micro t3.small t3a.medium m5a.large m5.xlarge<br>Norm. VM Startup Time<br>US-E. US-W. EU. Asia US-E. US-W. EU. Asia US-E. US-W. EU. Asia US-E. US-W. EU. Asia US-E. US-W. EU. Asia<br><!-- End of picture text -->

Fig. 14. (AWS) Normalized startup times of spot instances. The startup times of spot VMs are normalized to the startup times of on-demand VMs. 

longer startup time. Moreover, it is observed that there was up to a 45% difference (average startup time) among different zones, even within the same region (us-west-2). These results thus imply that to minimize VM startup time, AWS users should carefully choose zones when creating VMs. 

Fig. 13 shows the VM startup time variations of Linux VMs in 12 different zones within four regions in GCP. The overall startup time variations are similar to the startup time fluctuations reported in Fig. 11(b). And, we also observed there are significant startup time variations from a zone to another belonging to the same geographical region in GCP. For example, Zd in europe-west1 had 32% longer VM startup time than the GCP average. Interestingly, the Zc of the same region had 3<sup>rd</sup> fastest VM startup time (18% shorter) out of all 12 zones, and the VM startup time difference in the europe-west1 region can be up to 62 seconds. In particular, europe-west1 and asia-southeast1 showed high fluctuations of VM startup time among their zones. We observed that europe-west1 and asia-southeast1 regions could have 33% – 50% differences in the VM startup times. Consequently, these results also imply that GCP users need to carefully choose zones in a specific region when starting VMs for minimizing the VM startup time in order to improve resource elasticity. 

## **Observation #4: Different data center regions** 

- In both cloud providers, different zones in the same 

- region can significantly differ in VMs’ startup time. 

## _E. Other Potential Factors_ 

In addition to previous analyses, we further investigated potential factors that can change the VM startup time. In this subsection, we provide our analysis of the VM purchase models and temporal factors for changing VM startup times. 

**VM Purchase Models.** Public cloud providers typically offer three different ways of purchasing VMs, which are ondemand, reserved, and low-availability models. In particular, low-availability models, such as spot instances in AWS [50] and preemptible VMs in GCP [51], are being increasingly used by cloud users due to the high cost-efficiency. As per a previous study [25] and industry report [58], the AWS spot 

TABLE VI 

VM STARTUP TIME DIFFERENCES BETWEEN ON-DEMAND AND PREEMPTIBLE VMS IN GCP 

|**Region**|**Zone**|**Linux VMs**|**Windows VMs**|
|---|---|---|---|
||a|0.6%|0.6%|
|us-east-4|b|1.2%|0.9%|
||c|0.9%|0.5%|
||a|1.1%|2.3%|
|us-west-1|b|1.9%|2.0%|
||c|2.6%|5.2%|
||b|5.2%|5.9%|
|europe-west1|c|2.5%|5.5%|
||d|0.9%|3.3%|
||a|4.9%|4.7%|
|asia-southeast1|b|3.2%|1.6%|
||c|3.7%|5.9%|



instances tended to have longer cold startup times, so it is important to see if the previous reports are still valid. A potential factor for AWS spot instances having longer startup time is the bidding process to determine the VMs’ price. However, in this study, we always used the bidding prices higher than the current price of spot instances to minimize the delay due to the bidding process and precisely measure the startup time or delay only caused by the cloud infrastructure. Moreover, in this measurement, we experienced the failure of VM startup (or provisioning) in both AWS spot and GCP preemptible VMs due to the limited capacity of such instances. Nevertheless, we do not report the failure rate or statistics of the startup process of the low-availability VMs as it is out of the scope of this work. 

Fig. 14 shows the startup times of the five different spot VM types, and the startup times are normalized to the startup time of on-demand VMs. While the startup time of spot instances (e.g., t2-micro type) could be considerably (e.g., 20%) different from the on-demand VMs’ startup time, we could not observe any measurement results, which support that spot VMs had longer startup times than on-demand VMs. Interestingly, it is observed that spot VMs can have a shorter startup time than on-demand VMs. i.e., t2/t3 instances in us-west-1. Similar results (as reported in Table 4) were measured from GCP’s preemptible VMs. The maximum difference in the startup time between preemptible and on-demand VMs was less than 6% (Windows VMs in asia-southeast1), and most zones/regions have less than 2% – 3% difference in the startup times between two models. Also, we have observed several cases that the preemptible VMs had shorter (cold) startup time. As a result, low-availability models (spot and preemptible VMs) no longer have slower startup time compared to on-demand VMs. 

**Temporal Factors.** Cloud data centers may have a different amount of workloads as per “time-of-day” or “day-of-week” because cloud applications (e.g., web) may have repeating or diurnal workload patterns [29], [41]. So, we further analyzed whether such temporal factors could change the VM startup times. We first examined the VM startup time variations on different days of week. While we omit the visualized results 

8 



<!-- Start of picture text -->
t2.nano<br> 160<br> 120<br> 80 t2.small<br> 40<br>t3a.med.<br> 0<br> 0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  20  21  22  23<br>Time of Day (hr)<br>VM Startup Time (sec.)<br><!-- End of picture text -->

Fig. 15. (AWS) VM startup time changes of three VM types (t2.nano, t2.small, and t3a.medium) at different times of day. These results only contain the measurement results with Linux VMs. 

for this variation, both providers commonly showed that the VMs have shorter startup times on Saturdays and Sundays and longer startup times on weekdays. For example, AWS has a 14% longer VM startup times on weekdays. 

Fig. 15 reports the VM startup time differences of three VM types at a different time-of-day, and the results confirm that the VM startup times could be varying over time. We also observed that smaller and older generation VM types could have more substantial VM startup time changes compared to bigger and newer generations VMs. As shown in Fig. 15, t2 instances (specifically t2.nano) in AWS showed more dynamic changes in their startup times. Fig. 16 shows the VM startup time changes in a GCP VM type in three different regions at different time-of-day. Similar to the AWS result, the startup times of GCP VMs were varying with time-of-day, but the startup times are more affected by location factors (e.g., geographical regions). As shown in Fig. 16, e2-standard-2 VMs in asia-southeast1 and europe-west1 had more significant changes in their startup times than VMs in us-east4. The results reported in Fig. 15 and 16 are consistent with our findings in Section III-C and III-D. Also, the results indicate that the VM startup times in both providers can be affected by temporal factors, and the VM startup time fluctuations can be amplified by other factors, such as different VM types (in AWS) and geographical locations/regions (in GCP). 

## **Observation #5: Other Potential Factors** 

- Spot or preemptible VMs (low availability models) no 

- longer have slower startup time than on-demand VMs. 

- The temporal factors (different times) can change VMs’ 

- startup time. Moreover, VMs’ startup time can be amplified by other factors like VM types and locations/regions. 

## IV. DISCUSSION 

## _A. Comparison with Previous Measurement Results_ 

We compare our analysis results with previous reports to see how much improvement has been made by cloud providers. For the comparison, we use AWS’s measurement results reported by Mao et al. [25] in 2012 and measurements from both AWS and GCP by Abrita et al. [27] in 2018. Please note 



<!-- Start of picture text -->
 160<br> 140<br> 120<br> 100<br> 80<br> 60<br> 40 e2-standard-2 (asia-southeast1)<br> 20 e2-standard-2 (europe-west1)<br>e2-standard-2 (us-east4)<br> 0<br> 0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  20  21  22  23<br>Time of Day (hr)<br>Fig. 16. (GCP) VM startup time fluctuations of VMs (e2-standard-2e2-standard-2<br>instance type) at different times of day. The results were measured with Linux<br>VM with 32GB.<br> 400<br> 350<br> 300<br> 250<br> 200<br> 150<br> 100 Average: 56s<br> 50<br> 0<br>0.5G 1G 2G 4G 32G 64G 128G 256G<br>Mao et al. (2012) Current Measurement<br>VM Startup Time (sec.)<br>VM Startup Time (Sec.)<br><!-- End of picture text -->

Fig. 16. (GCP) VM startup time fluctuations of VMs (e2-standard-2e2-standard-2 instance type) at different times of day. The results were measured with Linux VM with 32GB. 

Fig. 17. Comparison with previous work (Mao et al. in 2012 [25]); VM startup times with different VM image sizes. 

that the results and graphs for Mao et al.’s measurements in this section are our interpretations of graphs and tables in the original author’s report [25]. Therefore, the results in Fig. 17 and 18, and Table VIII may have a marginal difference from the original results. 

_1) VM Startup Time Comparison with Different VM Image Sizes:_ We first compare the VM startup times with various VM image sizes. Fig. 17 shows AWS’s VM startup times measured by Mao et al. (2012) and by this work with different VM sizes. In the 2012 measurement, AWS clearly showed that the VM startup time has a positive correlation with the VM image sizes. Based on this result, we assume that AWS used external storage to store VM images, and inter/intra-data center networks may increase VM startup time. However, AWS in 2020 does not appear to have such a pattern in their VMs’ startup time. AWS now can offer near-constant VM startup time with various image sizes. Moreover, the image sizes we used in this work are much larger than the VM image sizes used in 2012. e.g., up to 4G in 2012 vs. up to 256G in 2020. The measured startup time is much smaller than the previous measurement, implying that AWS significantly improved the data center infrastructures so that and AWS could dramatically reduce VM startup times. 

_2) VM Startup Time Comparison with Different VM Types:_ Next, we compare the VM startup times with different VM types. Fig. 18 shows the startup time differences in Mao et al.’s measurements and our measurements. Due to the 9 years gap, we could not directly compare the VM startup time using the 

9 



<!-- Start of picture text -->
Mao et al. (2012) 2020 Measurement<br>120<br>100<br>80<br>60<br>40<br>20<br>0<br>t1-mic. t3-mic. m1-sm.t3-sm. c1-med.t3a-med. m1-lg.m5a-lg. m2-xlg.m5-xlg.<br>TimeStartup(Sec.)VM<br><!-- End of picture text -->

Fig. 18. Comparison with previous work (Mao et al. [25]); VM startup times with different VM types. Note that the VM image size in 2012 measurement was 0.5G and the results from this work contain all VM image sizes. 

same instance types. Instead, we tried to compare the startup time with similar VM types. As shown in Fig. 18, except for micro instance types, the newer instances used in this work show a significant reduction (53% – 67%) in their startup times. This result also confirms that newer generation instances often show faster startup times than older generation instances, which is one of our findings described in Section III-C. 

Fig. 19 reports the comparison of VM startup times between the previous report by Abrita et al. (2018) and this measurement. For AWS, our work and Abrita et al. commonly measured startup times of three VM types; t2.nano, t2.micro, and m4.large. The AWS VM startup times shown in Fig. 19(a) are considerably different from the previous comparison with Mao et al. Specifically, Abrita et al. reported much faster VM startup times (17 – 19 seconds) than our measurements, and their results are even faster than warm startup times of these three VM types. We believe this difference can be because Abrita et al. used different VM image sizes and/or templates than those used in our work. In the early stage of this work, we observed similar startup times when creating VMs with default OS images (without extra data in the image). Since detailed information regarding VM images used in Abrita et al. is unknown, we presume that using different VM images _may_ be the reason for the faster startup time reported in Abrita et al.’s work. 

Fig. 19(b) shows the startup time comparisons in GCP against the measurement results by Abrita et al. We compared the startup time results from f1-micro, g1-small, and n1-standard-1 VM types because these VM types were commonly measured. The results from Abrita et al. showed much faster VM startup times than our measurement of cold startup times, but Abrita et al’s results are very similar to the warm startup times of these VM types. We tried to perform a further investigation to understand the differences/similarities, but [27] lacks the description of measurement methodology (especially for the procedure to measure cold/warm startup times). Therefore, we assume that the majority of the measurements by Abrita et al. contains the warm startup time results. 

_3) VM Startup Time Comparison with Different Regions:_ Our measurements for VM startup times per different regions are also compared with Abrita et al.’s benchmark results. In 



<!-- Start of picture text -->
(a) AWS (b) GCP<br>160 Abrita et al. (2018) 160 Abrita et al. (2018)<br>140 Cold Start (2020) 140 Cold Start (2020)<br>Warm Start (2020) Warm Start (2020)<br>120 120<br>100 100<br>80 80<br>60 60<br>40 40<br>20 20<br>0 0<br>t2.nano t2.micro m4.large f1-micro g1-small n1-std-1<br>TimeStartup(Sec.)VM TimeStartup(Sec.)VM<br><!-- End of picture text -->

Fig. 19. Comparison with previous work (Abrita et al. [27]); VM startup times with different VM types in AWS and GCP. Note that the VM image size measured by Abrita et al. was not specified. 

this comparison, the startup times of t2.micro (AWS) in three regions and GCP f1-micro’s startup times for three regions are used. Table VII reports the comparison results. For both providers, the VM startup times’ differences are similar to the previous VM types comparisons reported in Section IV-A2. t2.micro of AWS showed faster VM startup times in Abrita et al.’s report than warm startup times from our work. We also assume that this can be because of the VM image size differences and the use of default VM images. In GCP, f1-micro’s startup times measured by Abrita et al. are also very close to warm startup times from our measurements; thus, we hold the same conclusion described in Section IV-A2. 

_4) Spot Instance Startup Time Comparison:_ The spot VMs’ startup times are compared with the results reported by Mao et al., and Table VIII reports the comparison results. As shown in the table, the spot instances in 2012 had 500 – 595 seconds of startup times. A significant portion of such slow startup times was mainly related to the bidding process for determining the spot price [59], [60]. However, after AWS released a new spot pricing model in 2018 [61], such a slower bidding process has been replaced with a simplified mechanism so that AWS users can quickly move on to the VM startup process. For a fair comparison, we calculate VM startup time without a bidding process by subtracting bidding time from the whole spot VM startup time reported from the original author. The calculated results are shown in Table VIII (please refer to the values in the parentheses), and the startup times after the spot bidding process are from 95 to 160 seconds These results are similar to on-demand VM startup times reported in Fig. 18, except for t1.micro, which is 58% slower (about 60 seconds in ondemand VMs, 95s in spot VMs). However, our measurements show that spot instances have 41 to 53 seconds of startup times, which are 43% – 69% quicker than the measurements in 2012, indicating that AWS improves spot infrastructure significantly and provides much faster startup times. 

**Summary of Comparison.** We compared our measurements with the two most relevant previous reports for VM startup times. By comparing with the results by Mao et al., we confirm that AWS made significant improvements for the VM startup times and currently have much quicker VM startup times in both on-demand and spot instances. However, compared with 

10 

TABLE VII 

COMPARISON WITH PREVIOUS WORK (ABRITA ET AL. [27]); VM STARTUP TIMES IN DIFFERENT REGIONS OF AWS AND GCP. 

|**VM Type**<br>**(Provider)**|**Region**|**2018**<br>**Measure.**|**Current **<br>**Cold**|**Measure.**<br>**Warm**|
|---|---|---|---|---|
|t2micro|us-east-1|27.6s|58.8s|39.3s|
|.<br>(AWS)|us-west-2|30.2s|61.5s|41.0s|
||ap-s.east-1|26.2s|54.6s|35.6s|
|f1-micro|eu-west1-c|33.0s|116.9s|33.7s|
|(GCP)|us-west1-a|36.1s|133.9s|35.1s|
||asia-s.east1-a|32.8s|130.1s|28.7s|



Abrita et al.’s results, we could not confirm the improvements or changes in VM startup times because we were not able to reproduce their results. This could be because of differences in VM configurations and measurement methodologies. i.e., cold vs. warm startup times, VM image sizes. 

## _B. Use Cases_ 

The accurate knowledge of VM startup time is critical for designing effective predictive auto-scaling policies [28], [29], [40]–[43], [62]–[64]. In predictive auto-scaling, new VMs are provisioned in advance to handle the increased workloads before the increased workload arrives. Without accurate knowledge of the VM startup time, the newly-provisioned VMs may be created too early, leading to idle VMs and wasted resources. Without this knowledge, the newly provisioned VMs may also be started too late. The delayed provision makes resource under-provisioning, resulting in low performance and Quality-of-Service (QoS) requirement violations. 

The accurate knowledge of VM startup time is also crucial for reliable cloud simulation. Instead of actual executions in the cloud, cloud simulators typically use execution time profiles of the VMs in their simulations [44]–[48], [65]. Therefore, the accuracy of the simulation results depends on the accuracy of these profiles. Furthermore, as reported in this paper, the VM startup time can be considerably longer and thus cannot be ignored. Therefore, accurate VM startup time is also an important factor to be considered by cloud simulators for reliable simulation results. 

## V. RELATED WORK 

There has been a large body of works that measured the performance of cloud infrastructures, such as CPU, IO, Network, and application performance [15]–[25], [27]. Regarding the VM startup time, Mao et al. [25] performed a measurement study on VM startup times from AWS EC2, Azure, and Rackspace in 2012. The authors identified several factors that could affect the VM startup time. Abrita et al. [27] reported benchmarking results of VM startup times in three cloud providers. However, both previous works’ measurement results have limitations to be used for the current cloud research and resource management. First, the measurement from Mao et al. was performed 9 years ago and the results do not correctly reflect the current status of VM startup times. This is because a number of mechanisms [30]–[37] have been proposed and applied for optimizing VM provisioning 

TABLE VIII 

COMPARISON WITH PREVIOUS WORK; VM STARTUP TIMES OF SPOT INSTANCES. FOR THE 2012 MEASUREMENT BY MAO ET AL. [25], THE NUMBERS IN PARENTHESES ARE VM PROVISIONING TIME AFTER FINISHING BIDDING PROCESS OF SPOT INSTANCES. 

||**2012**<br>**Measurements**|**2020**<br>**Measurements**|
|---|---|---|
|micro (t1 vs. t3)|550s (95s)|53.53s|
|small (m1 vs. t3)|595s (100s)|41.62s|
|medium (c1 vs. t3a)|500s (95s)|41.80s|
|large (m1 vs. m5a)|590s (160s)|42.98s|
|xlarge (m2 vs. m5)|500s (120s)|39.75s|



processes in cloud data centers so that it is necessary to measure updated VM startup times to provide up-to-date information to the research community. Second, the report from Abrita et al. provides recent statistics in VM startup times, but the benchmarking results employed the limited VM configurations with unclear measurement methodologies. Moreover, our analysis and measurement study considered a much broader set of VM configurations (768 configurations in AWS, 704 configurations in GCP), including instance types, image sizes, and data center locations, and we conducted this measurement study for a much more extended period of time (three months). For example, Mao et al. used 6 VM types in AWS, and Abrita et al. only considered 5 VM types in AWS and 3 VM types in GCP, but our work employed more than 11 VM types from each provider. Our measurement results were collected across 12+ zones in four regions from both providers, and we were able to collect and analyze 300,000 data points for VM startup times. Therefore, we report a much more comprehensive and thorough analysis of VM startup times with diverse configurations and realistic scenarios. 

## VI. CONCLUSION 

In this work, we report the analysis of VM startup times in AWS and GCP. We measured and analyzed VM startup times with diverse configurations, which include two different OS types, 11+ VM types, four different VM image sizes (from 32GB to 256GB), four geographical regions (two in the U.S., one in Europe, and one in Asia), and two purchase models (on-demand vs. spot/preemptible). We collected more than 300,000 data points from each provider with three months of measurements, analyzed these data points, and identified factors that change VM startup times. Our measurement results show that VM startup time can be varying significantly due to diverse factors such as OS types, VM image sizes, VM instance types, data center locations, and a caching mechanism in a cloud provider (e.g., GCP). 

We then compared measurement and analysis results from this work against prior measurement studies. By comparing with the 2012 measurement [25], we confirmed that cloud providers (specifically AWS) made significant improvements for the VM startup times and currently offer much quicker VM startup times compared to the previous measurement results. 

11 

## ACKNOWLEDGMENT 

The authors thank Radhika Bhavsar for contributions to earlier versions of this work. 

## REFERENCES 

- [1] Michael Armbrust, Armando Fox, Rean Griffith, Anthony D. Joseph, Randy H. Katz, Andy Konwinski, Gunho Lee, David A. Patterson, Ariel Rabkin, Ion Stoica, and Matei Zaharia. A View of Cloud Computing. _Communications of ACM_ , 53(4):50–58, 2010. 

- [2] Amazon Web Services. http://aws.amazon.com, 2021. 

- [3] Google Cloud Platform. https://cloud.google.com, 2021. 

- [4] OpenStack. https://www.openstack.org/, 2021. 

- [5] Docker. https://www.docker.com/, 2021. 

- [6] gVisor. https://github.com/google/gvisor, 2021. 

- [7] Benjamin Hindman, Andy Konwinski, Matei Zaharia, Ali Ghodsi, Anthony D. Joseph, Randy H. Katz, Scott Shenker, and Ion Stoica. Mesos: A Platform for Fine-Grained Resource Sharing in the Data Center. In _USENIX Symposium on Networked Systems Design and Implementation (NSDI)_ , Boston, MA, April, 2011. 

- [8] Muhammad Tirmazi, Adam Barker, Nan Deng, Md E. Haque, Zhijing Gene Qin, Steven Hand, Mor Harchol-Balter, and John Wilkes. Borg: the Next Generation. In _European Conference on Computer Systems (EuroSys)_ , Heraklion, Greece, April, 2020. 

- [9] AWS Lambda. https://aws.amazon.com/lambda/, 2021. 

- [10] Eric Jonas, Qifan Pu, Shivaram Venkataraman, Ion Stoica, and Benjamin Recht. Occupy the Cloud: Distributed Computing for the 99%. In _ACM Symposium on Cloud Computing (SoCC)_ , Santa Clara, CA, USA, September, 2017. 

- [11] Paul C. Castro, Vatche Ishakian, Vinod Muthusamy, and Aleksander Slominski. The rise of serverless computing. _Communications of ACM_ , 62(12):44–54, 2019. 

- [12] Amazon Elastic Container Service. https://aws.amazon.com/ecs/, 2021. 

- [13] Kubernetes. https://kubernetes.io/, 2021. 

- [14] Dong Du, Tianyi Yu, Yubin Xia, Binyu Zang, Guanglu Yan, Chenggang Qin, Qixuan Wu, and Haibo Chen. Catalyzer: Sub-millisecond Startup for Serverless Computing with Initialization-less Booting. In _ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)_ , Lausanne, Switzerland, March, 2020. 

- [15] J¨org Schad, Jens Dittrich, and Jorge-Arnulfo Quian´e-Ruiz. Runtime Measurements in the Cloud: Observing, Analyzing, and Reducing Variance. _Proc. VLDB Endow._ , 3(1):460–471, 2010. 

- [16] Alexandru Iosup, Nezih Yigitbasi, and Dick H. J. Epema. On the Performance Variability of Production Cloud Services. In _IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing (CCGrid)_ , Newport Beach, CA, USA, May, 2011. 

- [17] Philipp Leitner and J¨urgen Cito. Patterns in the Chaos – A Study of Performance Variation and Predictability in Public IaaS Clouds. _ACM Trans. on Internet Technology_ , 16(3):15:1–15:23, 2016. 

- [18] Sen He, Glenna Manns, John Saunders, Wei Wang, Lori L. Pollock, and Mary Lou Soffa. A Statistics-based Performance Testing Methodology for Cloud Applications. In _ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE)_ , Tallinn, Estonia, August, 2019. 

- [19] Zach Hill, Jie Li, Ming Mao, Arkaitz Ruiz-Alvarez, and Marty Humphrey. Early Observations on the Performance of Windows Azure. In _ACM International Symposium on High Performance Distributed Computing (HPDC)_ , Chicago, Illinois, USA, June, 2010. 

- [20] Iman Sadooghi, Jesus Hernandez Martin, Tonglin Li, Kevin Brandstatter, Ketan Maheshwari, Tiago Pais Pitta De Lacerda Ruivo, Gabriele Garzoglio, Steven Timm, Yong Zhao, and Ioan Raicu. Understanding the Performance and Potential of Cloud Computing for Scientific Applications. _IEEE Transactions on Cloud Computing_ , 5(2):358–371, 2017. 

- [21] Roberto R. Exp´osito, Guillermo L. Taboada, Sabela Ramos, Jorge Gonz´alez-Dom´ınguez, Juan Touri˜no, and Ramon Doallo. Analysis of I/O Performance on an Amazon EC2 Cluster Compute and High I/O Platform. _Journal of Grid Computing_ , 11(4):613–631, 2013. 

- [22] Valerio Persico, Pietro Marchetta, Alessio Botta, and Antonio Pescap`e. Measuring network throughput in the cloud: The case of Amazon EC2. _Computer Networks_ , 93:408–422, 2015. 

- [23] Jiawei Wen, Lei Lu, Giuliano Casale, and Evgenia Smirni. Less Can Be More: Micro-managing VMs in Amazon EC2. In _IEEE International Conference on Cloud Computing (CLOUD)_ , New York City, NY, USA, June, 2015. 

- [24] Anshul Gandhi and Justin Chan. Analyzing the Network for AWS Distributed Cloud Computing. _SIGMETRICS Performance Evaluation Review_ , 43(3):12–15, 2015. 

- [25] Ming Mao and Marty Humphrey. A Performance Study on the VM Startup Time in the Cloud. In _IEEE International Conference on Cloud Computing (CLOUD)_ , Honolulu, HI, USA, June, 2012. 

- [26] Gabriella Carrozza, Luigi Battaglia, Vittorio Manetti, Antonio Marotta, Roberto Canonico, and Stefano Avallone. On the Evaluation of VM Provisioning Time in Cloud Platforms for Mission-Critical Infrastructures. In _IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing (CCGrid)_ , Chicago, IL, USA, May, 2014. 

- [27] Samiha Islam Abrita, Moumita Sarker, Faheem Abrar, and Muhammad Abdullah Adnan. Benchmarking VM Startup Time in the Cloud. In _Benchmarking, Measuring, and Optimizing - BenchCouncil International Symposium (Bench)_ , Seattle, WA, USA, December, 2018. 

- [28] Ming Mao and Marty Humphrey. Auto-scaling to minimize cost and meet application deadlines in cloud workflows. In _International Conference on High Performance Computing Networking, Storage and Analysis (SC)_ , Seattle, WA, USA, November, 2011. 

- [29] In Kee Kim, Wei Wang, Yanjun Qi, and Marty Humphrey. Empirical Evaluation of Workload Forecasting Techniques for Predictive Cloud Resource Scaling. In _IEEE International Conference on Cloud Computing (CLOUD)_ , San Francisco, CA, USA, June, 2016. 

- [30] Kaveh Razavi and Thilo Kielmann. Scalable Virtual Machine Deployment Using VM Image Caches. In _International Conference for High Performance Computing, Networking, Storage and Analysis (SC)_ , Denver, CO, USA, November, 2013. 

- [31] Kaveh Razavi, Ana Ion, and Thilo Kielmann. Squirrel: scatter hoarding VM image contents on IaaS compute nodes. In _International Symposium on High-Performance Parallel and Distributed Computing (HPDC)_ , Vancouver, BC, Canada, June, 014. 

- [32] Kaveh Razavi, Gerrit Van Der Kolk, and Thilo Kielmann. Prebaked _µ_ VMs: Scalable, Instant VM Startup for IaaS Clouds. In _IEEE International Conference on Distributed Computing Systems (ICDCS)_ , Columbus, OH, June, 2015. 

- [33] Jiwei Xu, Wenbo Zhang, Zhenyu Zhang, Tao Wang, and Tao Huang. Clustering-based acceleration for virtual machine image deduplication in the cloud environment. _Journal of Systems and Software_ , 121:144– 156, 2016. 

- [34] Filipe Manco, Costin Lupu, Florian Schmidt, Jose Mendes, Simon Kuenzer, Sumit Sati, Kenichi Yasukata, Costin Raiciu, and Felipe Huici. My VM is Lighter (and Safer) than your Container. In _ACM Symp. on Operating Systems Principles (SOSP)_ , Shanghai, China, October, 2017. 

- [35] Yifan Zhang, Kai Niu, Weigang Wu, Keqin Li, and Yu Zhou. Speeding Up VM Startup by Cooperative VM Image Caching. _IEEE Transactions on Cloud Computing_ , pages 1–1, 2018. 

- [36] Thuy-Linh Nguyen, Ramon Nou, and Adrien Lebre. YOLO: Speeding Up VM and Docker Boot Time by Reducing I/O Operations. In _European Conference on Parallel and Distributed Processing (EuroPar)_ , G¨ottingen, Germany, August, 2019. 

- [37] Alexandru Agache, Marc Brooker, Alexandra Iordache, Anthony Liguori, Rolf Neugebauer, Phil Piwonka, and Diana-Maria Popa. Firecracker: Lightweight Virtualization for Serverless Applications. In _USENIX Symposium on Networked Systems Design and Implementation (NSDI)_ , Santa Clara, CA, USA, February, 2020. 

- [38] Alexandru Iosup, Simon Ostermann, Nezih Yigitbasi, Radu Prodan, Thomas Fahringer, and Dick H. J. Epema. Performance Analysis of Cloud Computing Services for Many-Tasks Scientific Computing. _IEEE Transactions on Parallel and Distributed Systems_ , 22(6):931–945, 2011. 

- [39] In Kee Kim, Jacob Steele, Yanjun Qi, and Marty Humphrey. Comprehensive Elastic Resource Management to Ensure Predictable Performance for Scientific Applications on Public IaaS Clouds. In _IEEE/ACM International Conference on Utility and Cloud Computing (UCC)_ , London, United Kingdom, December, 2014. 

- [40] Alexey Ilyushkin, Ahmed Ali-Eldin, Nikolas Herbst, Andr´e Bauer, Alessandro Vittorio Papadopoulos, Dick H. J. Epema, and Alexandru Iosup. An Experimental Performance Evaluation of Autoscalers for Complex Workflows. _ACM Transactions on Modeling and Performance Evaluation of Computing Systems_ , 3(2):8:1–8:32, 2018. 

12 

- [41] In Kee Kim, Wei Wang, Yanjun Qi, and Marty Humphrey. CloudInsight: Utilizing a Council of Experts to Predict Future Cloud Application Workloads. In _IEEE International Conference on Cloud Computing (CLOUD)_ , San Francisco, CA, USA, July, 2018. 

- [42] Vinodh Kumaran Jayakumar, Jaewoo Lee, In Kee Kim, and Wei Wang. A Self-Optimized Generic Workload Prediction Framework for Cloud Computing. In _IEEE International Parallel and Distributed Processing Symposium (IPDPS)_ , Virtual Event, May, 2020. 

   - [64] Nikolas Roman Herbst, Nikolaus Huber, Samuel Kounev, and Erich Amrehn. Self-adaptive workload classification and forecasting for proactive resource provisioning. In _ACM/SPEC International Conference on Performance Engineering (ICPE)_ , 2013. 

   - [65] Christian Stier, J¨org Domaschka, Anne Koziolek, Sebastian Krach, Jakub Krzywda, and Ralf H. Reussner. Rapid Testing of IaaS Resource Management Algorithms via Cloud Middleware Simulation. In _ACM/SPEC International Conference on Performance Engineering (ICPE)_ , 2018. 

- [43] In Kee Kim, Wei Wang, Yanjun Qi, and Marty Humphrey. Forecasting Cloud Application Workloads with CloudInsight for Predictive Resource Management. _IEEE Transactions on Cloud Computing_ , pages 1–1, 2020. 

- [44] Rodrigo N. Calheiros, Rajiv Ranjan, Anton Beloglazov, C´esar A. F. De Rose, and Rajkumar Buyya. CloudSim: a toolkit for modeling and simulation of cloud computing environments and evaluation of resource provisioning algorithms. _Software: Practice and Experience (SPE)_ , 41(1):23–50, 2011. 

- [45] Alberto Nu˜nez, Jos´e Luis V´azquez-Poletti, Agust´ın C. Caminero, Gabriel G. Casta˜n´e, Jes´us Carretero, and Ignacio Mart´ın Llorente. iCanCloud: A Flexible and Scalable Cloud Infrastructure Simulator. _Journal of Grid Computing_ , 10(1):185–209, 2012. 

- [46] Dzmitry Kliazovich, Pascal Bouvry, and Samee Ullah Khan. GreenCloud: a packet-level simulator of energy-aware cloud computing data centers. _Journal of Supercomputing_ , 62(3):1263–1283, 2012. 

- [47] In Kee Kim, Wei Wang, and Marty Humphrey. PICS: A Public IaaS Cloud Simulator. In _IEEE International Conference on Cloud Computing (CLOUD)_ , New York City, NY, USA, June, 2015. 

- [48] Alexander Pucher, Emre Gul, Rich Wolski, and Chandra Krintz. Using Trustworthy Simulation to Engineer Cloud Schedulers. In _IEEE International Conference on Cloud Engineering (IC2E)_ , Tempe, AZ, USA, March, 2015. 

- [49] Jianwei Hao, Ting Jiang, Wei Wang, and In Kee Kim. An Empirical Analysis of VM Startup Times in Public IaaS Clouds. In _IEEE International Conference on Cloud Computing (CLOUD)_ , Virtual Event, September, 2021. 

- [50] Amazon EC2 Spot Instances. https://aws.amazon.com/ec2/spot/, 2021. [51] Preemptible VM instances. https://cloud.google.com/compute/docs/ instances/preemptible, 2021. 

- [52] Michael Smit, Bradley Simmons, and Marin Litoiu. Distributed, application-level monitoring for heterogeneous clouds using stream processing. _Future Generation Computing Systems_ , 29(8):2103–2114, 2013. 

- [53] AWS SDK for Python (Boto3). https://aws.amazon.com/ sdk-for-python/, 2021. 

- [54] Compute Engine client libraries. https://cloud.google.com/compute/ docs/api/libraries _\_ #google <u>apis python client library,</u> 2021. 

- [55] Aleksander Maricq, Dmitry Duplyakin, Ivo Jimenez, Carlos Maltzahn, Ryan Stutsman, Robert Ricci, and Ana Klimovic. Taming Performance Variability. In _USENIX Symposium on Operating Systems Design and Implementation (OSDI)_ , Carlsbad, CA, USA, October, 2018. 

- [56] Pradipta De, Manish Gupta, Manoj Soni, and Aditya Thatte. Caching VM Instances for Fast VM Provisioning: A Comparative Evaluation. In _European Conference on Parallel Processing (Euro-Par)_ , Rhodes Island, Greece, August, 2012. 

- [57] Google Compute Engine Machine types. https://cloud.google.com/ compute/docs/machine-types, 2021. 

- [58] Zillow. Saving Money with EMR Auto Scaling and Spot Instances. https://www.zillow.com/tech/save-money-emr-autoscaling-spot/, 2017. 

- [59] Thanh-Phuong Pham, Sasko Ristov, and Thomas Fahringer. Performance and Behavior Characterization of Amazon EC2 Spot Instances. In _IEEE International Conference on Cloud Computing (CLOUD)_ , San Francisco, CA, USA, July, 2018. 

- [60] Cheng Wang, Qianlin Liang, and Bhuvan Urgaonkar. An Empirical Analysis of Amazon EC2 Spot Instance Features Affecting CostEffective Resource Procurement. _ACM Transactions on Modeling and Performance Evaluation of Computing Systems_ , 3(2):6:1–6:24, 2018. 

- [61] Amazon Web Services. New Amazon EC2 Spot pricing model: Simplified purchasing without bidding and fewer interruptions. https: //aws.amazon.com/blogs/compute/new-amazon-ec2-spot-pricing/, 2018. 

- [62] Netflix Technology Blog. Scryer: Netflix’s predictive auto scaling engine. https://netflixtechblog.com/ scryer-netflixs-predictive-auto-scaling-engine-a3f8fc922270, 2013. 

- [63] N. Roy, A. Dubey, and A. Gokhale. Efficient Autoscaling in the Cloud Using Predictive Models for Workload Forecasting. In _IEEE International Conference on Cloud Computing_ , 2011. 

13 

