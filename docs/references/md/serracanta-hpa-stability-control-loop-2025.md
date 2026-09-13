---
# --- bibliographic record ---
entry_type: article
title: "On the Stability of the Kubernetes Horizontal Autoscaler Control Loop"
authors:
  - "Berta Serracanta"
  - "Andor Lukács"
  - "Alberto Rodriguez-Natal"
  - "Albert Cabellos"
  - "Gábor Rétvári"
year: 2025
venue: "IEEE Access"
volume: "13"
issue: ""
pages: "7160-7166"
publisher: "Institute of Electrical and Electronics Engineers (IEEE)"
doi: "10.1109/ACCESS.2025.3526751"
arxiv: ""
url: "https://doi.org/10.1109/ACCESS.2025.3526751"

# --- archive record ---
source_pdf: serracanta-hpa-stability-control-loop-2025.pdf
source_sha256: 89efb1425386e0429c12eb10cbacb85d12a96d1cab9cee61058d7d856c4c9ef7
pdf_pages: 7
converted: 2026-09-13
record_source: crossref
key_insight: "Formal proof of HPA control-loop stability (global asymptotic, zero steady-state error) at any utilization target 30--80%. Justifies threshold tuning."
first_page: "Received 22 November 2024, accepted 27 December 2024, date of publication 7 January 2025, date of current version 13 January 2025. Digital Object Identifier 10.1109/ACCESS.2025.3526751 On the Stabilit"
---


Received 22 November 2024, accepted 27 December 2024, date of publication 7 January 2025, date of current version 13 January 2025. _Digital Object Identifier 10.1109/ACCESS.2025.3526751_ 

On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 

# BERTA SERRACANTA 1, ANDOR LUKÁCS 2, ALBERTO RODRIGUEZ-NATAL 3, ALBERT CABELLOS<sup>1</sup> , AND GÁBOR RÉTVÁRI 4, (Member, IEEE) 

1Department of Computer Architecture, Universitat Politècnica de Catalunya, 08034 Barcelona, Spain 

2Faculty of Mathematics and Computer Science, Babeş-Bolyai University, 400084 Cluj-Napoca, Romania 

3Cisco, 28108 Madrid, Spain 

4Department of Telecommunications and Artificial Intelligence, Budapest University of Technology and Economics, 1111 Budapest, Hungary 

Corresponding author: Berta Serracanta (berta.serracanta@upc.edu) 

This work was supported in part by the Spanish I+D+i Project TowaRds fully AI-empowered NetwoRks, subproject A (TRAINER-A), funded by Ministerio de Ciencia e Innovación (MCIN)/Agencia Estatal de Investigación (AEI)/10.13039/501100011033 under Grant PID2020-118011GB-C21; in part by the Catalan Institution for Research and Advanced Studies (ICREA) through the Secretariat for Universities and Research of the Ministry of Business and Knowledge of the Government of Catalonia; in part by the European Social Fund; and in part by the National Research, Development and Innovation Fund of Hungary under Grant OTKA/ANN-135606, Grant OTKA/FK-135074, and Grant OTKA/FK-134604. 

- **ABSTRACT** Kubernetes is a widely used platform for deploying and managing containerized applications due to its efficient elastic capabilities. The Horizontal Pod Autoscaler (HPA) in Kubernetes independently adjusts the number of pods for each service, yet these services often operate in an interconnected manner. This study aims to understand the effects of autoscaling events on a graph of interconnected services. To achieve this, we apply control theory to model the HPA’s behavior. We analyze the stability of this model, perform numerical simulations, and deploy a real testbed to evaluate the performance. Our findings demonstrate that the control theory-based model accurately predicts the HPA’s behavior, ensuring system stability with CPU utilization meeting desired thresholds and no traffic loss after a transitional period. The model provides insights into optimizing resource scheduling and improving application performance in Kubernetes environments. Additionally, we extend our model to the whole service graph to understand how individual scaling decisions influence the complex graphs of cloud applications. 

- **INDEX TERMS** Cloud autoscaling, control theory, Horizontal Pod Autoscaler, Kubernetes, microservices architecture, numerical simulations, system stability. 

## **I. INTRODUCTION** 

Kubernetes<sup>1</sup> has emerged as a preferred platform for deploying and managing containerized applications, credited largely to its efficient elastic capabilities. This has allowed the platform’s widespread adoption across diverse industries, with many leading organizations depending on its robust features, which is a testament to its effectiveness. It was reported in 2023 that 66% of cloud service consumers were using Kubernetes in production [1], highlighting its pervasive adoption and significant impact on the industrial landscape. 

The associate editor coordinating the review of this manuscript and approving it for publication was Libo Huang . 1Kubernetes: http://kubernetes.io/ 

Kubernetes runs distributed applications that are typically implemented using the microservice architecture [2]. Each microservice is designed to perform a specific business function and can be developed, deployed, and scaled independently. With this, one can describe the architecture in terms of a service graph, a collection of looselycoupled microservices. In the service graph each node is a microservice and edges exist when two nodes exchange information. In this context Kubernetes’ elastic resource allocation system allocates/deallocates resources (e.g, CPU) to each node using the Horizontal Pod Autoscaling (HPA) algorithm [3]. 

Specifically, HPA automatically adjusts the number of pods, replicas of the same service, by continuously 

2025 The Authors. This work is licensed under a Creative Commons Attribution 4.0 License. For more information, see https://creativecommons.org/licenses/by/4.0/ 

7160 

VOLUME 13, 2025 

B. Serracanta et al.: On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 



monitoring specific metrics and scaling the service up or down. This allows dynamic scaling to match the demand, providing better application performance and resource utilization for each of the individual services in a service graph. Each service in the graph has its own independent HPA control loop, ensuring that scaling decisions are tailored to its own specific metrics. 

Despite the benefits of HPA in dynamically managing resources, research on scaling complex applications following service-based architectures has highlighted several challenges. One significant issue is the lack of accurate resource estimation models, which causes current approaches to frequently involve cautious and iterative adjustments to resource allocations [4]. In this paper we present a model for Kubernetes services and use it to analyze the stability of the application service graph when operated by HPA’s Kubernetes algorithm. We aim to understand if the autonomous scaling decisions made to individual services can collectively lead to a stable scaling effect for the entire application, or some unwanted effects such as large-scale oscillations emerge. Even if a large chunk of cloud applications rely on Kubernetes, and a lot of focus has been put on improving the resource allocation and performance optimization when performing autoscaling events [4], [5], little research effort has been devoted to formally model Kubernetes’ HPA behavior. Our model specifically focuses on CPU-intensive applications, demonstrating that properly managing CPU bottlenecks is key to maintaining performance and ensuring system stability. 

For this we employ control theory principles. This model treats each service as a plant and the HPA algorithm as the controller, with the control signal being the adjustment of the number of pods based on the CPU utilization feedback. The main contributions of this paper are (1) the formal verification of the stability of the Kubernetes HPA control loop for the single-service scenario and (2) an experimental analysis of the stability and efficiency of HPA in the multiservice scenario. 

The remainder of this paper is structured as follows: Section II dives into related work, Section III presents the service model, Section IV discusses the control theory framework and stability analysis, Section V provides experimental results, and Section VI presents the conclusions. 

all the layers involved in a microservice application, whitebox models often use computationally complex solutions such as layered queuing networks [6]. Another interesting approach is to model the service mesh sidecar attached to each microservice in the graph [7] as an abstraction of the whole microservice. Black-box models, on the other hand, typically apply reinforcement learning (RL) techniques, such as GNNs or SVMs, combined with online metrics tracing [8], [9], [10]. In both cases, these models focus on applying optimization techniques directly to the modeled application, either to achieve better resource allocation guaranteeing stronger Service Level Objectives (SLO) or to run simulations in a digital twin. However, we do not intend to model all the complexities and layers of a service graph application, from the kernel to user space. Instead, we focus on modeling the behavior of the HPA in each individual microservice and their interconnections. 

Rather than modeling, many studies focus on enhancing the HPA through modifications and optimizations to overcome the traditional approach of overprovisioning to avoid SLO violations. These can be classified into four different categories [4], [5] (and the references therein): (i) rule-based autoscaling, common among cloud providers; (ii) time series data analysis; (iii) queuing network models; and (iv) RL-based optimizations or a combination of several of the techniques above [11]. As pointed out in [8], many existing autoscalers manage resources for each microservice individually, which means there is a possibility of cascading effects propagated along the graph and, in turn, performance degradations. This is because these autoscalers are agnostic to changes in the workload of the graph until it reaches them directly, becoming more severe the deeper the microservice is located. 

We do not aim to modify the existing autoscaler but rather seek to understand the particularities and robustness of the de facto Kubernetes HPA. This research models CPU fluctuations driving HPA autoscaling events, not only on individual microservices but across the entire graph. Long Short-Term Memory (LSTM) and Gated Recurrent Units (GRUs) could be used to predict these changes by forecasting incoming traffic load. However, their effectiveness is limited when clear correlations, like seasonal patterns, do not exist. To the best of our knowledge, no prior work has focused on this specific objective. 

## **II. RELATED WORK** 

In this paper, we model the functionality of the Kubernetes Horizontal Pod Autoscaler (HPA). We examine how the addition or removal of pods impacts the performance and stability of the targeted service. Once we understand how these affects a particular service, we extrapolate the findings to the entire service graph to study how an autoscaling event propagates throughout it. 

There is extensive literature on models of the entire service graph. These models can be classified into two main types: white-box and black-box models, which respectively show or hide the complexities of the units being modeled. To capture 

## **III. SERVICE MODEL** 

We first present the basic entities of the Kubernes autoscaling system: the pod, the service and the Horizontal Pod Autoscaler. These are the entities that we model using control theory, firstly for a single service, and then generalized to a whole service graph. 

## _A. THE KUBERNETES HORIZONTAL AUTOSCALER_ 

A pod is the smallest deployable unit in Kubernetes and can be thought of as a wrapper around a single container. It is deployed based on its specified resource requirements and 

7161 

VOLUME 13, 2025 

B. Serracanta et al.: On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 





**FIGURE 1.** Microservice model. 

**TABLE 1.** Variables and signals used in our model. 



limits. A microservice, also referred to as service, groups multiple pods that perform the same functions, presenting them as a single entity. 

The Kubernetes Horizontal Pod Autoscaler (HPA) dynamically adjusts the number of pods allocated to a service. Each service has one dedicated HPA control loop, which manages the number of pod replicas running based on resource configuration and real-time resource consumption metrics. By default, HPA can scale pods using CPU or memory utilization metrics, with CPU usage being the most commonly used. HPA continuously monitors the service’s CPU usage: if it exceeds a threshold it adds new pods, whereas if the CPU usage drops below the threshold ite HPA decreases the number of running pods to optimize resource use. Managing the number of pods running in a service can be viewed as a control system, where the service represents the plant and HPA functions as the controller, as illustrated in Figure 1. 

Table 1 summarizes the notation used in the paper. Variables related to a single microservice system are denoted without a subscript (e.g., _x_ [ _k_ ]). Variables with the same meaning but pertaining to a specific microservice within the service graph _G_ ( _V , E_ ) are denoted with a subscript _i_ , _i_ ∈ _V_ (e.g., _xi_ [ _k_ ]). Where _V_ represents the set of microservices and _E_ the set of directed edges indicating interactions between them. 

## _B. MICROSERVICE MODEL_ 

Below, we provide a formal model to describe each of the components in the HPA control loop. First we introduce a 

model for describing the service’s response to the input load in terms of CPU consumption. 

When considering different approaches to modeling, it is important to account for the trade-off between the ease of analysis and the modeling capabilities and power. For example, a simple memoryless model describing how the average CPU utilization of an service _x_ [ _k_ ] [percentage] varies with respect to the system’s incoming load _q_ [ _k_ ] [req/sec] and the total amount of CPU (number of pod replicas times CPU per pod) assigned by the HPA control loop to the service _u_ [ _k_ ] [mcore], would be the following: 



Here, _γ_ ( _._ ) [mcore/req/sec] is a generic function that describes the ideal CPU requirement the service needs to process a given load. In general, _γ_ may be linear (see below), it may describe a diminishing returns characteristics often found in practice [12], or it may be any monotonically increasing function. The essence of the microservice model is then that the average CPU utilization _x_ [ _k_ ] in the _k_ -th timestep equals the total amount of CPU _γ_ ( _q_ [ _k_ ]) required to serve the current load _q_ [ _k_ ] divided by the total CPU _u_ [ _k_ ] assigned by the HPA controller. 

Unfortunately, this model, while formally analyzable, is memoryless (i.e., the output depends only on the state at the current timestep _k_ ). Thus, it does not account for critical parameters shaping system dynamics, like the impact of queue buffering (which is dependent on the state in _earlier_ timesteps). Therefore, below we use a slightly more complex non-linear recursive model inspired by Finite Impulse Response (FIR) systems in control theory [13]. 

Equation 2 gives the general form of the microservice model used throughout this paper. Here, _N_ denotes the order of the system and _αn_ are the coefficients that weigh the contribution of CPU utilization in the previous timestep _k_ − _n_ to the current state. For brevity, we assume that _γ_ ( _._ ) is linear henceforth. 



In the following we assume a minimum threshold for the number of CPU units of 1 assigned per each service. This means that each service retains at least one pod, even in the absence of incoming traffic. This assumption is based on the practical need to ensure service availability and responsiveness. 

## _C. CONTROLLER MODEL_ 

Next, we formally model the Kubernetes Horizontal Pod Autoscaler (HPA) control loop. The HPA control loop aims to maintain the CPU utilization around a target level by continuously adjusting the number of pods based on the CPU utilization measured from the service. If the CPU utilization exceeds a given upper threshold then HPA assigns more pods to the service. Conversely, if the CPU utilization 

7162 

VOLUME 13, 2025 

B. Serracanta et al.: On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 





**FIGURE 2.** Service graph model as a 2-service chain. 

is below a lower threshold, HPA reduces the number of pods to optimize resource usage. This closed-loop system ensures that the microservice adapts to varying loads while maintaining performance and resource efficiency. 

In our model we represent the upper and the lower thresholds with a single reference threshold _R_ (a userconfigurable parameter). Our HPA model is then a direct formal representation of the HPA control law specified in the official Kubernetes documentation [14]: 



Here, _u_ [ _k_ ] [mcore] denotes the control input, which determines the total CPU units assigned to the microservice. 

We quantify the amount of traffic _y_ [ _k_ ] at the service output in response to a given input load and the available compute resources as follows: 



## _D. SERVICE GRAPH MODEL_ 

Next we extend the model to a conceptual application constituted by _multiple_ linked microservices, as illustrated in Figure 2. This composite model supposes a distinct plant and an HPA control loop for each microservice. These elements form a microservice graph _G_ ( _V , E_ ), where _G_ represents a rooted Directed Acyclic Graph (DAG) with the root denoted by _r_ ∈ _V_ . 

In this model, the instantaneous propagation of traffic across microservices can be expressed as in Equation 5, which takes into account that the system can not process more traffic than the input load. 



Here, _λij_ : ( _i, j_ ) ∈ _V_ defines the intensity of requests transmitted from microservice _i_ to _j_ . 

## _E. TRAFFIC LOSS_ 

The stability of stability of the proposed model will be evaluated based on a _traffic loss_ metric, which describes the resource deficit of the current CPU allocation. The traffic loss metric _di_ [ _k_ ] quantifies the amount of requests the application 

is unable to process due to the lack of available CPU resources: 



In general, _di_ [ _k_ ] = 0 means a perfect CPU allocation, while _di_ [ _k_ ] _>_ 0 indicates service degradation and/or interruption, affecting the overall application performance. The target of the HPA control loop is to drive the system to a state where the loss is zero. 

Similarly, the aggregated traffic loss metric for the service graph model, represented by the set _V_ , is computed as the sum of each of the loss at each service at a given time step _k_ : _d_ [ _k_ ] =<sup>�</sup> _i_ ∈ _V_<sup>_di_[</sup><sup>_k_].Here,</sup><sup>_di_[</sup><sup>_k_]isthesingleservicequality</sup> metric as previously defined. 

## **IV. STABILITY ANALYSIS** 

In this section, we present the main contribution of the paper: a formal stability analysis of the single-service HPA control loop in terms of the traffic loss metric. In the subsequent section we extend the analysis to the multi-service model using numerical evaluations. 

First, we introduce a simplification. In particular, since our approach is highly non-linear we reduce the general microservice model to a second-order model. This means that the CPU dynamics is fully described by the coefficients _α_ 0 and _α_ 1, plus the input _q_ [ _._ ] and _u_ [ _._ ] This simplification allows us to incorporate both the current CPU value and the value from the previous time step into the model, providing a balance between model accuracy and ease of analysis. The proposed control model has a time complexity of _O_ ( _N_<sup>2</sup> ), where _N_ represents the evaluated time steps. 

_Theorem 1:_ Consider the system described by the second-order application dynamics (2), the HPA control law (3), and let the input be a step function: 



Assume _x_ [ _k_ ] ∈ (0 _,_ +∞) and _u_ [ _k_ ] ∈ (0 _,_ +∞) _, u_ [0] = 1. Then, the control system is globally asymptotically stable, i.e.: 

1) The steady state error is zero: lim _k_ →∞ _x_ [ _k_ ] − _R_ = 0. 

2) The steady state traffic loss is zero: lim _k_ →∞ _d_ [ _k_ ] = 0. 

These conditions define stability as a system that allocates the exact amount of resources required to meet the corresponding load by aligning the CPU consumption with the desired threshold _R_ . When there is a mismatch between the incoming load and the allocated resources, the system compensates by either adding or removing pods ensuring that in steady state there are the necessary resources. 

In order to demonstrate the previous stability definitions we start by analyzing the system boundaries and convergence of the control signal _u_ [ _k_ ] and later extrapolate the results to find the steady-state error and traffic loss. _<u>γ q</u>_ <u>[</u> _k_ <u>]</u> _Proof:_ Using _B_ = _R_ to define _b_ 0 = _Bα_ 0 and _b_ 1 = _Bα_ 1. Let _b_ 0 _, b_ 1 _, u_ [0] _, u_ [1] ∈ (0 _,_ +∞) and define the 

7163 

VOLUME 13, 2025 

B. Serracanta et al.: On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 



sequence ( _u_ [ _k_ ]) _k_ ∈N by the recursion: 



Then ( _u_ [ _k_ ]) _k_ ∈N converges to _b_ 0 + _b_ 1. 

Using the transformation _u_ [ _k_ ] = _b_ 0(1+ _z_ [ _k_ ]), the recursion becomes: 



Next, we introduce a Lemma from prior work that we use to establish the main result: 

_Lemma 1 (Theorem 6.3.3 of [15]):_ Let us consider the variables _p, q, z_ 0 _, z_ 1 ∈ (0 _,_ +∞) and define the sequence: 



The unique positive equilibrium of this recursion is globally asymptotically stable if one of the following two conditions holds: 





Using the notations of Lemma 1, we have _p_ = _q_ =<sup>_<u>b</u>_</sup> _b_<sup><u>1</u></sup> 0<sup>.</sup> The case _b_ 0 _> b_ 1 translates to _q <_ 1, and the case _b_ 0 ≤ _b_ 1 translates to _q_ ≥ 1 and _p_ = _q_ . Thus, the sequence ( _z_ [ _k_ ]) _k_ ∈N converges for every _b_ 0 _, b_ 1 _, z_ 0 _, z_ 1 ∈ (0 _,_ +∞) to the unique positive equilibrium of the recursion which is _b_<sup>_<u>b</u>_</sup> 0<sup><u>1</u>. This means</sup> that the sequence ( _u_ [ _k_ ]) _k_ ∈N converges to _b_ 0 + _b_ 1. Finally, by undoing the substitutions we obtain that ( _u_ [ _k_ ]) _k_ ∈N converges to<sup>_<u>γ</u>_</sup> _R_<sup>_<u>q</u>_(</sup><sup>_α_0+</sup><sup>_α_1).Inturn,thecontrol</sup> signal makes the plant ( _x_ [ _k_ ]) _k_ ∈N converge at the desired steady-state: 





And consequently, we can demonstrate that in steady state we achieve null traffic loss with the following simple computation: 



_Corollary 1:_ Consider an application graph _G_ ( _V , E_ ) composed of autonomous services operating independently. If every service in the graph fulfills the requirements in Theorem 1, then the service graph _G_ is globally asymptotically stable. 

This corollary follows directly from Theorem 1. If every autonomous service in the graph _G_ satisfies the conditions, then each service is stable, exhibits no deviation error, and has no traffic loss in steady state. Since these services operate 



**FIGURE 3.** Microservice model performance. 

independently, their stability ensures the overall stability of the graph _G_ . 

## **V. RESULTS** 

To further illustrate the stability demonstrated through the analytical solutions, this section presents the results obtained from both numerical simulations and real deployment experiments. These results provide graphical insights that validate the theoretical findings on HPA stability. 

## _A. NUMERICAL SIMULATIONS_ 

We have conducted numerical simulations using Matlab Simulink [16] for both the microservice model, with time complexity _O_ ( _N_ !), and the service graph model. These simulations aim to visualize the stability behavior and dynamic response of the Kubernetes HPA under various conditions, providing a controlled environment to verify our theoretical analysis. 

Figure 3 shows the main signals of the microservice model, the incoming load _q_ [ _k_ ] (blue line), the CPU utilization _x_ [ _k_ ] (red) and the control signal _u_ [ _k_ ] (green line) discussed in the previous sections for a user-defined HPA threshold of _R_ = 0 _,_ 8, meaning that in steady state we desire an average CPU utilization of _x_ [ _k_ ] = 0 _,_ 8. It can be seen that given an input load the system reacts and starts autoscaling by allocating more CPU resources and reducing them until the desired steady state is achieved at _k_ = 14. It is important to note that typical values for the CPU-targeted HPA threshold are around 30%, as applications in production cannot afford to lose traffic and typically overprovision to prevent this. However, for verification purposes, we use a threshold of _R_ = 0 _._ 8 (80%) CPU consumption to observe the model’s behavior under more stressful conditions. 

When we extend these results to the service graph, as depicted in Fig. 4, we observe that the stability achieved by each independent and stable service is reflected in the overall system behavior. As shown, for each of the three independent services deployed in a chain-like configuration the CPU utilization follows a similar pattern to the results achieved in the microservice model simulations, meaning that all three of them are able to independently adjust their resources to reach a steady state without being impacted by the autoscaling decisions of other nodes in the graph. 

7164 

VOLUME 13, 2025 

B. Serracanta et al.: On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 







**FIGURE 5.** Kubernetes 3-Service chain deployment performance. 

**FIGURE 4.** Service graph model performance. 

In summary, these results demonstrate that the entire system can reach the desired steady state after a transitional period, where CPU utilization aligns with the target threshold and traffic loss is eliminated. 

## _B. EXPERIMENTAL RESULTS_ 

To verify our theoretical analysis in a real-world scenario, we deployed a Kubernetes testbed focusing on the general case of the service graph model for a CPU-intensive application. This real deployment aims to observe the HPA’s performance and stability in a practical setting, ensuring that the analytical and simulation results hold true in live environments. 

The experimental setup comprises three interconnected microservices configured in a cascading topology, as detailed in [17]. Each service is CPU load generator that, upon receiving a request, executes arithmetic operations for 8ms. The request is then forwarded to the subsequent service in the sequence. 

We deployed Kubernetes’ HPA (v2) on each microservice. HPA is configured to auto-scale based on CPU consumption and configured to trigger an autoscaling event to deploy another replica when CPU utilization reaches 80% of the requested 100mcore per service. This mimics the previous analysis for direct comparison. 

To generate the requests we use K6 [18], a well-established synthetic load generator. Specifically we define an initial virtual spike of 20 users that plateaus at 22 virtual users. In total each experiments lasts 20 minutes. 

Figure 5 illustrates the CPU usage for each microservice involved in our system. The first microservice initially receives the incoming load, leading to an early rise in its CPU consumption. As this service processes the traffic, the load is then transferred to the second microservice, which exhibits a similar increase in CPU usage. Eventually, the load reaches the third and final microservice. The vertical lines represent the active pods for each service, highlighting the points at which CPU usage at each service meets the Horizontal Pod Autoscaler (HPA) threshold, prompting an autoscaling event to deploy a new replica. 

It demonstrates the impact of CPU saturation on service performance. Until a new replica is successfully deployed, the 

affected service’s CPU remains saturated, making it unable of processing additional incoming requests. This results in the loss of traffic. Notably, the request failures start when autoscaling events are triggered. These losses remain until the deployment of additional replicas sufficiently increases resource availability, allowing the system to manage the incoming load effectively. 

These experimental results validate the theoretical model and testbed configuration. They demonstrate that the system effectively reaches the desired steady state where CPU utilization meets the threshold and traffic loss is minimized after the initial transitory period. This confirms the practical applicability and reliability of the HPA under real-world conditions. 

## **VI. CONCLUSION** 

Kubernetes, with its extensive deployment over the past several years, has proven to be a crucial platform for managing containerized applications in large-scale production environments [1]. Many organizations depend on Kubernetes for its robust and dynamic scaling capabilities, underscoring its importance and effectiveness. 

This work not only models and validates the stability of HPA in both single and multi-service scenarios but also lays the groundwork for future advancements in cloud application scaling and resource management. This can further enhance application performance in Kubernetes environments, i.e., by optimizing resource allocation and scheduling, which is critical given the platform’s widespread industrial adoption. 

In conclusion, our research builds on the extensive use and proven success of Kubernetes and HPA in production environments. By addressing the analytical gaps, we provide initial steps towards a more in-depth study and open up research possibilities in optimizing Kubernetes’ scaling mechanisms. 

## **ACKNOWLEDGMENT** 

The authors would like to express their gratitude to the editor and the reviewers for their valuable comments and constructive feedback. Their insightful suggestions have greatly contributed to the improvement of this manuscript. They deeply appreciate their time and effort in reviewing their work. 

7165 

VOLUME 13, 2025 

B. Serracanta et al.: On the Stability of the Kubernetes Horizontal Autoscaler Control Loop 



## **REFERENCES** 

- [1] Cloud Native Computing Foundation. (2023). _2023 Annual Survey_ . Accessed: May 29, 2024. [Online]. Available: https://www.cncf.io/reports/ cncf-annual-survey-2023/ 

BERTA SERRACANTA is currently pursuing the Ph.D. degree with UPC BarcelonaTech. Her research focuses on network-enabled application acceleration, exploring the integration of network and application layers, and the optimization of distributed systems for enhanced operational efficiency. 

- [2] T. Salah, M. J. Zemerly, C. Y. Yeun, M. Al-Qutayri, and Y. Al-Hammadi, ‘‘The evolution of distributed systems towards microservices architecture,’’ in _Proc. 11th Int. Conf. Internet Technol. Secured Trans. (ICITST)_ , Dec. 2016, pp. 318–325. 

- [3] B. Burns, J. Beda, K. Hightower, and L. Evenson, _Kubernetes: Up and Running_ , 3rd ed., New York, NY, USA: O’Reilly Media, 2022. 

- [4] C. Qu, R. N. Calheiros, and R. Buyya, ‘‘Auto-scaling web applications in clouds: A taxonomy and survey,’’ _ACM Comput. Surveys_ , vol. 51, no. 4, pp. 1–33, Jul. 2018. [Online]. Available: https://doiorg.recursos.biblioteca.upc.edu/10.1145/3148149 

- [5] T. Lorido-Botran, J. Miguel-Alonso, and J. A. Lozano, ‘‘A review of auto-scaling techniques for elastic applications in cloud environments,’’ _J. Grid Comput._ , vol. 12, no. 4, pp. 559–592, Dec. 2014. C. Qu, R. N. Calheiros, and R. Buyya, ‘‘Auto-scaling web applications in clouds: A taxonomy and survey,’’ _ACM Comput. Surveys_ , vol. 51, no. 4, pp. 1–33, Jul. 2018. [Online]. Available: https://doiorg.recursos.biblioteca.upc.edu/10.1145/3148149 

ANDOR LUKÁCS received the Ph.D. degree in mathematics from Utrecht University. He is currently a Lecturer with Babeş-Bolyai University. His research interests include abstract homotopy theory, operads, dendroidal sets, and metric fixed point theory. 

- [6] E. Incerto, R. Pizziol, and M. Tribastone, ‘‘ _µ_ Opt: An efficient optimal autoscaler for microservice applications,’’ in _Proc. IEEE Int. Conf. Autonomic Comput. Self-Organizing Syst. (ACSOS)_ , Sep. 2023, pp. 67–76. 

- [7] X. Zhu, G. She, B. Xue, Y. Zhang, Y. Zhang, X. K. Zou, X. Duan, P. He, A. Krishnamurthy, M. Lentz, D. Zhuo, and R. Mahajan, ‘‘Dissecting overheads of service mesh sidecars,’’ in _Proc. ACM Symp. Cloud Comput._ , New York, NY, USA, Oct. 2023, pp. 142–157, doi: 10.1145/3620678.3624652. 

- [8] J. Park, B. Choi, C. Lee, and D. Han, ‘‘GRAF: A graph neural network based proactive resource allocation framework for SLO-oriented microservices,’’ in _Proc. 17th Int. Conf. Emerg. Netw. Exp. Technol._ , 2021, pp. 154–167, doi: 10.1145/3485983.3494866. 

ALBERTO RODRIGUEZ-NATAL received the Ph.D. degree from BarcelonaTech, with a thesis on software-defined networking. He is a Senior Technology Lead with the Enterprise Networking CTO Team, Cisco, where he works in the intersection of network and applications. 

- [9] H. Qiu, S. S. Banerjee, S. Jha, Z. Kalbarczyk, and R. K. Iyer, ‘‘FIRM: An intelligent fine-grained resource management framework for SLOoriented microservices,’’ in _Proc. 14th USENIX Symp. Operating Syst. Design Implement. (OSDI)_ , Aug. 2020, pp. 805–825. [Online]. Available: https://www.usenix.org/conference/osdi20/presentation/qiu 

- [10] D. Borsatti, W. Cerroni, L. Foschini, G. Ya Grabarnik, L. Manca, F. Poltronieri, D. Scotece, L. Shwartz, C. Stefanelli, M. Tortonesi, and M. Zaccarini, ‘‘KubeTwin: A digital twin framework for Kubernetes deployments at scale,’’ _IEEE Trans. Netw. Service Manage._ , vol. 21, no. 4, pp. 3889–3903, Aug. 2024. 

- [11] A. U. Gias, G. Casale, and M. Woodside, ‘‘ATOM: Model-driven autoscaling for microservices,’’ in _Proc. IEEE 39th Int. Conf. Distrib. Comput. Syst. (ICDCS)_ , Jul. 2019, pp. 1994–2004. 

ALBERT CABELLOS received the Ph.D. degree in 2008. He has been a Full Professor with the Computer Architecture Department, Universitat Politècnica de Catalunya, since 2020. He is the co-founder of Barcelona Neural Networking (https://bnn.upc.edu/) and the NaNoNetworking Center in Catalunya (https://www.n3cat.upc.edu/). 

- [12] M. D. Hill and M. R. Marty, ‘‘Amdahl’s law in the multicore era,’’ _Computer_ , vol. 41, no. 7, pp. 33–38, Jul. 2008. 

- [13] A. Oppenheim, A. Willsky, and I. Young, _Signals and Systems_ (Prentice-Hall Signal Processing Series). Upper Saddle River, NJ, USA: Prentice-Hall, 1983. [Online]. Available: https://books.google.es/ books?id=UQJRAAAAMAAJ 

- [14] _Horizontal Pod Autoscaling: Algorithm Details_ . Accessed: Jun. 28, 2024. [Online]. Available: https://kubernetes.io/docs/tasks/run-application/ horizontal-pod-autoscale/ 

- [15] M. Kulenovic and G. Ladas, _Dynamics of Second Order Rational Difference Equations: With Open Problems and Conjectures_ , 1st ed., Boca Raton, FL, USA: CRC Press, 2001, doi: 10.1201/9781420035384. 

- [16] MathWorks, Inc., Natick, MA, USA. (2022). _Matlab Version: 9.13.0 (r2023a)_ . [Online]. Available: https://www.mathworks.com 

- [17] _Kubernetes Horizontal Autoscaling Benchmark_ . Accessed: May 2, 2024. [Online]. Available: https://github.com/rg0now/k8s-hpa-benchmark/tree/ main?tab=readme-ov-file 

GÁBOR RÉTVÁRI (Member, IEEE) received the M.Sc. and Ph.D. degrees in electrical engineering from Budapest University of Technology and Economics (BME), and the D.Sc. degree from the Hungarian Academy of Sciences. He is currently an Associate Systems Professor with the Department of Telecommunications and Artificial Intelligence, BME. He is interested in all theoretical and practical aspects of distributed systems and data networking. 

- [18] _K6_ . Accessed: May 2, 2024. [Online]. Available: https://k6.io/docs/ 

7166 

VOLUME 13, 2025 

