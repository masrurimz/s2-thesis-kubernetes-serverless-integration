---
# --- bibliographic record ---
entry_type: inproceedings
title: "Non-stationary Continuum-armed Bandits for Online Hyperparameter Optimization"
authors:
  - "Shiyin Lu"
  - "Yu-Hang Zhou"
  - "Jing-Cheng Shi"
  - "Wenya Zhu"
  - "Qingtao Yu"
  - "Qing-Guo Chen"
  - "Qing Da"
  - "Lijun Zhang"
year: 2022
venue: "Proceedings of the Fifteenth ACM International Conference on Web Search and Data Mining"
volume: ""
issue: ""
pages: "618-627"
publisher: "ACM"
doi: "10.1145/3488560.3498396"
arxiv: ""
url: "https://doi.org/10.1145/3488560.3498396"

# --- archive record ---
source_pdf: lu-nonstationary-bandits-online-hyperparameter-optimization-2022.pdf
source_sha256: 7f8fe5f16ee5276fd629503acf6b6654bb37de4a0aa8bc3b9676d4151de53d55
pdf_pages: 10
converted: 2026-11-12
record_source: crossref
key_insight: "Online hyperparameter optimization where the objective drifts over time. Cited for that drift only."
first_page: "Non-stationary Continuum-armed Bandits for Online Hyperparameter Optimization Shiyin Lu National Key Lab for Novel Software Technology, Nanjing University Nanjing, China lusy@lamda.nju.edu.cn Yu-Hang"
---
WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

# **Non-stationary Continuum-armed Bandits for Online Hyperparameter Optimization** 

Shiyin Lu National Key Lab for Novel Software Technology, Nanjing University Nanjing, China lusy@lamda.nju.edu.cn 

Yu-Hang Zhou 

Jing-Cheng Shi 

Alibaba Group Hangzhou, China 

Alibaba Group Hangzhou, China 

zyh174606@alibaba-inc.com 

jingcheng.sjc@alibaba-inc.com 

Wenya Zhu Qingtao Yu Alibaba Group Alibaba Group Hangzhou, China Hangzhou, China wenya.zwy@alibaba-inc.com qingtao.yqt@alibaba-inc.com 

Qing-Guo Chen Alibaba Group Hangzhou, China qingguo.cqg@alibaba-inc.com 

Lijun Zhang<sup>∗</sup> National Key Lab for Novel Software 

Qing Da 

Alibaba Group Hangzhou, China daqing.dq@alibaba-inc.com 

Technology, Nanjing University 

Nanjing, China 

zhanglj@lamda.nju.edu.cn 

## **ABSTRACT** 

For years, machine learning has become the dominant approach to a variety of information retrieval tasks. The performance of machine learning algorithms heavily depends on their hyperparameters. It is hence critical to identity the optimal hyperparameter configuration when applying machine learning algorithms. Most of existing hyperparameter optimization methods assume a static relationship between hyperparameter configuration and algorithmic performance and are thus not suitable for many information retrieval applications with non-stationary environments such as e- commerce recommendation and online advertising. To address this limitation, we study online hyperparameter optimization, where the hyperparameter configuration is optimized on the fly. We formulate online hyperparameter optimization as a non-stationary continuum-armed bandits problem in which each arm corresponds to a hyperparameter configuration and the algorithmic performance is viewed as reward. For this problem, we develop principled methods with strong theoretical guarantees in terms of dynamic regret. The key idea is to adaptively discretize the continuous arm set and estimate the mean reward of each arm via weighted averaging. As a case application, we show how our methods can be applied to optimize the hyperparameter of vector-based candidate generation algorithm and empirically demonstrate the effectiveness and efficiency of our methods on public advertising dataset and online 

∗Lijun Zhang is the corresponding author. 

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first page. Copyrights for components of this work owned by others than ACM must be honored. Abstracting with credit is permitted. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from permissions@acm.org. _WSDM ’22, February 21–25, 2022, Tempe, AZ, USA_ 

© 2022 Association for Computing Machinery. ACM ISBN 978-1-4503-9132-0/22/02...$15.00 https://doi.org/10.1145/3488560.3498396 

A/B testing. Furthermore, to the best of our knowledge, our methods are the first to achieve sub-linear dynamic regret bounds for continuum-armed bandits, which may be of independent interest. 

## **CCS CONCEPTS** 

- **Information systems** → **Information retrieval** . 

## **KEYWORDS** 

continuum-armed bandits, non-stationary environments, hyperparameter optimization 

### **ACM Reference Format:** 

Shiyin Lu, Yu-Hang Zhou, Jing-Cheng Shi, Wenya Zhu, Qingtao Yu, QingGuo Chen, Qing Da, and Lijun Zhang. 2022. Non-stationary Continuumarmed Bandits for Online Hyperparameter Optimization. In _Proceedings of the Fifteenth ACM International Conference on Web Search and Data Mining (WSDM ’22), February 21–25, 2022, Tempe, AZ, USA._ ACM, New York, NY, USA, 10 pages. https://doi.org/10.1145/3488560.3498396 

## **1 INTRODUCTION** 

Machine learning is a popular and dominant approach for building information retrieval (IR) systems [4, 25, 27, 32, 42] and has been applied in various IR tasks such as e-commerce recommendation [43], web search [41], and online advertising [44]. The performance of machine learning algorithms typically depends on the configurations of hyperparameters, which are adjustable parameters that govern the learning process. Representative examples of hyperparameters in IR scenarios include thresholds of vector-based candidate generation algorithms [8] and step sizes of online learning to rank algorithms [16], to name a few. Due to the complex relationship between hyperparameter configuration and algorithmic performance, it is difficult to tune hyperparameters by standard optimization techniques such as convex optimization [39]. Instead, practitioners often resort to brute-force approaches such as grid search and random search [28, 31]. 

618 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

Grid search refers to exhaustive exploration on a manually determined discretization of the hyperparameter space. In grid search, each discrete hyperparameter configuration is first evaluated and the one yielding the highest performance is then identified as the best configuration. While grid search is simple to implement and easy to parallelize, it requires human expertise to specify a suitable discretization level for balancing the computational cost of evaluating all discrete configurations and the quality of the obtained best configuration. As a refinement of grid search, random search avoids human overhead by uniformly drawing candidate hyperparameter configurations from the hyperparameter space [7]. It has been empirically demonstrated and widely recognized that random search is more effective than grid search in finding well-performing hyperparameter configurations [6]. 

Nevertheless, an intrinsic drawback of random search as well as grid search is that the performance of previously explored hyperparameter configurations is totally ignored when determining the next configuration to evaluate, which makes the exploration process rather inefficient. To address this drawback, recent advances in hyperparameter optimization have introduced Bayesian optimization to utilize historical information for more efficient exploration on the hyperparameter space [33]. Under Bayesian optimization framework, the relationship between hyperparameter configuration and algorithmic performance is characterized by an objective function. While the objective function is complex and remains unknown, Bayesian optimization only requires querying the objective function and uses a probabilistic surrogate model to approximate the objective function. The surrogate model is first initialized with a prior distribution that expresses one’s belief on the unknown objective function and then iteratively updated according to the value of the objective function at the queried point. Equipped with the surrogate model, Bayesian optimization can exploit historical observations of the objective function and adaptively select the next hyperparameter configuration to explore. Such adaptivity also translates into superior performance than brute-force approaches on various tasks including information retrieval [23, 24, 37]. 

While Bayesian optimization stands as the state-of-the-art approach for optimizing hyperparameters of information retrieval systems [24], existing Bayesian optimization methods either assume a stationary objective function or lack of theoretical guarantees and hence not suitable for many non-stationary and cost-sensitive scenarios such as e-commerce recommendation and online advertising. For example, in online advertising, the click-through-rate of an ad usually changes with time and so does the objective function; a one-percent drop of click-through-rate due to a bad hyperparameter configuration can lead to million dollars losses [1]. Furthermore, Bayesian optimization is originally designed for offline hyperparameter optimization and its time complexity grows rapidly with iteration, which is prohibitive for real-time update applications. 

In this paper, we study online hyperparameter optimization, where the objective function can vary with time and the hyperparameter configuration is optimized on the fly. We propose a novel bandit learning framework termed as non-stationary continuumarmed bandits for online hyperparameter optimization: each hyperparameter configuration is viewed as an arm with the corresponding algorithmic performance being reward. We develop provably effective methods under the proposed bandit learning framework. 

The main idea is to handle the continuous arm set by adaptive discretization and deal with the non-stationary environment via dynamic mean estimator. We rigorously analyze the performance of our methods in terms of dynamic regret and establish the first sublinear dynamic regret bounds for continuum-armed bandits, which may be of independent interest. Our methods are also efficient in the sense that each iteration only takes constant time. As a practical example, we apply our methods to optimize the hyperparameter of vector-based candidate generation algorithm. Extensive experimental comparison with existing hyperparameter algorithms on both public advertising dataset and online A/B testing demonstrates the effectiveness and efficiency of our methods. 

## **2 RELATED WORK** 

Grid search is the most basic method for hyperparameter optimization and has been widely used in tuning hyperparameters of various machine learning models such as random forest [38], support vector machine [40], and deep neural networks [11]. Thanks to its simplicity and flexibility, grid search is commonly integrated in popular machine learning software packages including scikit-learn [30], libsvm [9], and pytorch [29]. Given a human-specified step size, grid search traverses the hyperparameter space step by step and evaluates each possible hyperparameter configuration. To find a well-performing hyperparameter configuration with affordable computational costs, one has to carefully set the step size and often repeats the process of grid search multiple times [45]. As an effort to overcoming this limitation, a variant of grid search termed as random search was proposed, where the hyperparameter space is randomly explored [2]. Random search inherits all advantages of grid search such as simple implementation and flexible parallelism and greatly reduces the manual burden of grid search [34]. The superiority of random search was delicately analyzed in [7], where random search was found to spend less time in exploring poorperforming regions of the hyperparameter space than grid search. [7] also empirically shows that random search is more effective than grid search in tuning hyperparameters of diverse machine learning algorithms on a variety of datasets. 

A common criticism of grid search and random search is that the hyperparameter configuration to explore is independent of the hyperparameter configurations that have been evaluated, which may involve a large number of unnecessary hyperparameter evaluations [39]. To improve the exploration efficiency, advanced methods including Bayesian optimization [33] and Hyperband [26] have been proposed, where the exploration process is guided by the previously evaluated hyperparameter configurations. Bayesian optimization speeds up the identification of good hyperparameter configurations by adaptively determining the next hyperparameter to evaluate [6]. In each iteration, after observing the performance of previously evaluated hyperparameter configurations, Bayesian optimization first fits the observations into a surrogate model. Then, based on the surrogate model, an acquisition function is adopted to balance the trade-off between exploring potentially better regions and exploiting the currently promising regions [19]. According to the adopted surrogate model, Bayesian optimization methods can be divided into three categories, namely, sequential model-based algorithm configuration [19], tree-structured Parzen [6], and Spearmint 

619 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

[33], where the surrogate model is random forest, Parzen density estimator, and Gaussian process, respectively. The three types of Bayesian optimization methods were empirically shown to beat random search on various tasks [12, 13, 24, 35, 37]. 

As an orthogonal research direction to Bayesian optimization, Hyperband [26] accelerates the optimization process by adaptively allocating the evaluation budget to different hyperparameter configurations. Hyperband is a best-arm identification (BAI) algorithm built upon the successive halving (SH) method [20]. Given a finite evaluation budget _𝐵_ , SH first samples _𝑛_ hyperparameter configurations each allocated _𝐵_ / _𝑛_ evaluation budget and then successively eliminates poorly-performing configurations while doubling the evaluation budget of the remain configurations. The difficultly of applying SH lies in balancing the trade-off between the number of configurations _𝑛_ and the average allocated evaluation budget across _𝑛_ configurations _𝐵_ / _𝑛_ . As a simple yet effective approach to this _𝑛_ versus _𝐵_ / _𝑛_ dilemma, Hyperband essentially performs a grid search over all feasible _𝑛_ and calls SH as a subroutine for each _𝑛_ . The effectiveness of Hyperband is empirically verified on a variety of problems [21, 36]. 

## **3 PRELIMINARY** 

We formulate online hyperparameter optimization as a novel nonstationary continuum-armed bandits problem, where a learner interacts with a continuous set of arms. Without loss of generality, we assume the arm set (the hyperparameter space) has been shifted and scaled to the unit interval, i.e., [0 _,_ 1]. The learning protocol proceeds over _𝑇_ rounds. In each round _𝑡_ ∈[ _𝑇_ ], the learner first chooses an arm (a hyperparameter configuration) _𝐼𝑡_ from [0 _,_ 1] and then receives a reward of the chosen arm _𝑟𝑡_ ( _𝐼𝑡_ ), which corresponds to the performance of the selected hyperparameter configuration. For each arm _𝑎_ ∈[0 _,_ 1], we denote by D _𝑡_ ( _𝑎_ ) the probability distribution from which the reward of _𝑎_ in round _𝑡_ is drawn. Finally, the learner updates her arm selection strategy for the next round based on the received reward _𝑟𝑡_ ( _𝐼𝑡_ ). 

In each round _𝑡_ , let _𝜇𝑡_ ( _𝑎_ ) = E _𝑟_ ∼D _𝑡_ ( _𝑎_ ) [ _𝑟_ ] denote the mean reward of an arm _𝑎_ . We define the arm with maximum mean reward as the optimal arm: _𝑎𝑡_<sup>∗= arg max</sup> _𝑎_ ∈[0 _,_ 1]<sup>_𝜇𝑡_(</sup><sup>_𝑎_). The learner’s performance</sup> is measured by dynamic regret, which is the difference between the cumulative mean rewards of the arms chosen by the learner and that of the optimal arms: 



We make three mild assumptions as follows. 

- The rewards are all bounded in [0 _,_ 1] and the reward distributions are independent across arms and rounds. 



- The environment is piecewise stationary with reward distributions varying at most Γ times<sup>1</sup> : 





## **4 METHOD** 

The main idea of our methods is to deal with the continuous arms by discretizing the arm set and handle non-stationary reward distributions via dynamic mean estimator. To ease understanding, we first present a basic method using static discretization and then propose a refined method with adaptive discretization. 

## **4.1 Static Discretization** 

Let _𝜌_ denote the discretization resolution. We first discretize the continuous arm set [0 _,_ 1] into a set of equally-spaced arms: 



We refer to each arm in A as active arm and only pull active arms during the _𝑇_ rounds. The intuition behind the discretization in (1) is two folds. On the one hand, the number of active arms only grows inverse-linearly with the discretization resolution and thus the sampling cost on the active arm set can be controlled. On the other hand, for each inactive arm _𝑎_ ∈[0 _,_ 1] −A, its mean reward can be approximated by that of certain active arm _𝑎_<sup>′</sup> ∈A and the approximate error can be bounded by the discretization resolution, since by the definition of A and the Lipschitz continuity of mean reward function, there must exist an active arm _𝑎_<sup>′</sup> ∈A such that 



After discretization, we associate each active arm _𝑎_ ∈A with two variables, namely _𝜇_ ˆ _𝑡_ ( _𝑎_ ) and _𝜉𝑡_ ( _𝑎_ ), which denote the estimated mean of arm _𝑎_ ’s reward distribution in round _𝑡_ and the confidence width of the estimation, respectively. In each round _𝑡_ = 1 _, . . . ,𝑇_ , following the principle of “optimism in the face of uncertainty” [3], we select the active arm with the maximum sum of estimated mean reward and confidence width: 



As the reward distribution of each arm is non-stationary, classical mean estimators that directly average the historical rewards do not apply. To address this problem, we adopt dynamic mean estimator [15], which can converge to the time-varying mean reward. The main idea of dynamic mean estimator is to assign more weights to recent rewards and less weights to old rewards when averaging the historical rewards. Specifically, let _𝑤𝑡_ ( _𝑠_ ) denote the weight assigned to the reward in round _𝑠_ . We estimate the mean reward of each active arm _𝑎_ ∈A in round _𝑡_ by<sup>2</sup> 





where _𝜆_ ∈ N is the drop threshold. By contrast, in the soft-drop configuration, all historical rewards are preserved and their weights constitute a geometric series: 



2We make the convention that 0/0 = +∞. 

620 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

**Algorithm 1** Static Discretization with Dynamic Mean Estimator <u>(SD</u><sup>2</sup> ME) 

|**Re**|**quire:** discretization resolution_𝜌_, drop threshold_𝜆_, drop dis-<br>count_𝛾_|
|---|---|
|1:|Construct a set of active armsA = {_𝜌𝑘_|_𝑘_=1_, . . . ,_⌊1/_𝜌_⌋}|
|2:|Initialize ˆ_𝜇_1(_𝑎_) =0 and_𝜉_1(_𝑎_) =+∞for each_𝑎_∈A|
|3:|**for**_𝑡_=1_,_2_, . . . ,𝑇_**do**|
|4:|Select an arm_𝐼𝑡_according to (2)|
|5:<br>6:|Pull_𝐼𝑡_and receive a reward_𝑟𝑡_(_𝐼𝑡_)<br>**switch**weight configuration**do**|
|7:|**case**hard-drop**:** Compute_𝑤𝑡_(_𝑠_)_,𝑠_=1_, . . . ,𝑡_−1 by (4)<br>|
|8:|**case**soft-drop**:** Compute_𝑤𝑡_(_𝑠_)_,𝑠_=1_, . . . ,𝑡_−1 by (5)<br>|
|9:|**end switch**|
|10:<br>11:|Update_𝜇𝑡_+1(_𝑎_)and_𝜉𝑡_+1(_𝑎_)for each_𝑎_∈A by (3) & (7)<br> **end for**|



where _𝛾_ ∈(0 _,_ 1] is the drop discount. 

It remains to design the confidence width _𝜉𝑡_ ( _𝑎_ ). To this end, we resort to the Hoeffding’s inequality [17]. Specifically, it can be proved that<sup>3</sup> in most of rounds, the following inequality holds with a high probability 



Thus, we set the confidence width of each active arm _𝑎_ ∈A as 



We summarize the whole procedure in Algorithm 1, which is referred to as Static Discretization with Dynamic Mean Estimator (SD<sup>2</sup> ME) and enjoys the following theoretical guarantee. 



_satisfies_ E[DR( _𝑇_ )] ≤ _𝑂_ (Γ<sup>1/4</sup> _𝑇_<sup>3/4</sup> ) _._ 

Remark 4.1. The pseudo-code in Algorithm 1 is not optimized for runtime but for ease of exposition and understanding. In fact, for each active arm _𝑎_ ∈A, both the estimated mean reward _𝜇_ ˆ _𝑡_ ( _𝑎_ ) and the confidence width _𝜉𝑡_ ( _𝑎_ ) can be computed in an online manner with _𝑂_ (1) time complexity per round. Specifically, let _𝑛𝑡_ ( _𝑎_ ) =<sup>�</sup> _𝑠_<sup>_𝑡_−</sup> =1<sup>1</sup><sup>_𝑤𝑡_(</sup><sup>_𝑠_)1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_],</sup><sup>_𝑅𝑡_(</sup><sup>_𝑎_)=�</sup> _𝑠_<sup>_𝑡_−</sup> =1<sup>1</sup><sup>_𝑤𝑡_(</sup><sup>_𝑠_)1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_]</sup><sup>_𝑟𝑠_(</sup><sup>_𝑎_),</sup> and _𝑊𝑡_ =<sup><u>�</u></sup> _<u>𝑠</u>_<sup>_𝑡_−</sup> =1<sup>1</sup><sup>_𝑤𝑡_(</sup><sup>_𝑠_). We have</sup><sup>_𝜇_ˆ</sup><sup>_𝑡_(</sup><sup>_𝑎_)=</sup><sup>_𝑅𝑡_(</sup><sup>_𝑎_)/</sup><sup>_𝑛𝑡_(</sup><sup>_𝑎_)and</sup><sup>_𝜉𝑡_(</sup><sup>_𝑎_)=</sup> √︁(log _𝑊𝑡_ )/ _𝑛𝑡_ ( _𝑎_ ). In the hard-drop weight configuration, we can maintain two queues of length _𝜆_ (one for storing the rewards _𝑟𝑠_ ( _𝑎_ ) _,𝑠_ = _𝑡_ − _𝜆, . . . ,𝑡_ − 1 and the other for storing the indicators 1[ _𝐼𝑠_ = _𝑎_ ] _,𝑠_ = _𝑡_ − _𝜆, . . . ,𝑡_ − 1) and update _𝑛𝑡_ ( _𝑎_ ), _𝑅𝑡_ ( _𝑎_ ), and _𝑊𝑡_ incrementally as 



3The proof is postponed to the next section. 

In the soft-drop weight configuration, the values of _𝑛𝑡_ ( _𝑎_ ), _𝑅𝑡_ ( _𝑎_ ), and _𝑊𝑡_ can be also updated on the fly: 



## **4.2 Adaptive Discretization** 

While SD<sup>2</sup> ME is simple, it cannot utilize the rewards received on the fly to refine the discretization, which hinders its effectiveness in dealing with complex mean reward functions. To overcome this limitation, we propose an adaptive discretization based method, where the discretization is not determined in advance but adaptively adjusted throughout the _𝑇_ rounds. 

Specifically, we maintain a time-varying active arm set A _𝑡_ ⊂ [0 _,_ 1], which is initialized to be empty and updated in each round. Similarly to SD<sup>2</sup> ME, each active arm _𝑎_ ∈A _𝑡_ is associated with a time-varying estimated mean reward _𝜇_ ˆ _𝑡_ ( _𝑎_ ) and a corresponding confidence width _𝜉𝑡_ ( _𝑎_ ). While we compute _𝜇_ ˆ _𝑡_ ( _𝑎_ ) in the same way as that of SD<sup>2</sup> ME, we slightly modify the design of _𝜉𝑡_ ( _𝑎_ ) in (7) to<sup>4</sup> : 



where _𝛿_ ∈(0 _,_ 1) controls the failure probability of the concentration inequality in (6). 

An active arm _𝑎_ ∈A _𝑡_ and its associated confidence width _𝜉𝑡_ ( _𝑎_ ) define a covering interval [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )]. By the Lipschitz continuity of the mean reward function and the concentration inequality of the dynamic mean estimator in (6), the mean reward _𝜇𝑡_ ( _𝑎_<sup>′</sup> ) of each arm _𝑎_<sup>′</sup> in the covering interval [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )] can be approximated by the estimated mean reward _𝜇_ ˆ _𝑡_ ( _𝑎_ ) of the active arm _𝑎_ as 



Thus, in each round, we can only pull active arms if the arm set [0 _,_ 1] can be covered by the union of the covering interval of each active arm, i.e., 



Our adaptive discretization based method is designed such that (10) is guaranteed throughout the _𝑇_ rounds. Specifically, in each round _𝑡_ = 1 _, . . . ,𝑇_ , we first check whether [0 _,_ 1] ⊆∪ _𝑎_ ∈A _𝑡_ −1 [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )] holds. If yes, (10) can be guaranteed by simply setting A _𝑡_ = A _𝑡_ −1. Otherwise, we pick an arbitrary arm _𝑎_<sup>′</sup> from the uncovered region [0 _,_ 1] −∪ _𝑎_ ∈A _𝑡_ −1 [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )] and add it into the active arm set, i.e., A _𝑡_ = A _𝑡_ −1 ∪{ _𝑎_<sup>′</sup> }. Then, we set the estimated mean reward and the confidence width of this newly added active arm as zero and infinity, respectively. By doing so, the arm set [0 _,_ 1] becomes a subset of the covering interval of _𝑎_<sup>′</sup> and thus (10) holds. 

With (10) guaranteed, we can only pull arm from the active arm set A _𝑡_ . In each round _𝑡_ = 1 _, . . . ,𝑇_ , we first select an active arm in a similar way to that of SD<sup>2</sup> ME, with the only difference of doubling 

> 4This modification is essential in deriving a dynamic regret bound that holds with high probability rather than in expectation. 

621 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

**Algorithm 2** Adaptive Discretization with Dynamic Mean Estimator (AD<sup>2</sup> ME) 

|**Re**<br>1: <br>2:|**quire:** drop threshold_𝜆_, drop discount_𝛾_<br> Initialize the active arm set asA0 =∅<br> **for**_𝑡_=1_,_2_, . . . ,𝑇_**do**<br>|
|---|---|
|3:|**if** [0_,_1] ⊆∪_𝑎_∈A_𝑡_−1[_𝑎_−_𝜉𝑡_(_𝑎_)_,𝑎_+_𝜉𝑡_(_𝑎_)] **then**|
|4:|SetA_𝑡_=A_𝑡_−1<br>|
|5:|**else**|
|6:|Pick an arm_𝑎_<sup>′ </sup>∈[0_,_1] −∪_𝑎_∈A_𝑡_−1[_𝑎_−_𝜉𝑡_(_𝑎_)_,𝑎_+_𝜉𝑡_(_𝑎_)]<br>|
|7:|SetA_𝑡_=A_𝑡_−1∪{_𝑎_<sup>′</sup>}, ˆ_𝜇𝑡_(_𝑎_<sup>′</sup>) =0, and_𝜉𝑡_(_𝑎_<sup>′</sup>) =+∞<br>|
|8:|**end if**<br>|
|9:|Select an arm_𝐼𝑡_according to (11)|
|10:|Pull_𝐼𝑡_and receive a reward_𝑟𝑡_(_𝐼𝑡_)|
|11:|**switch**weight configuration**do**|
|12:|**case**hard-drop**:** compute_𝑤𝑡_(_𝑠_)_,𝑠_=1_, . . . ,𝑡_−1 by (4)|
|13:|**case**soft-drop**:** compute_𝑤𝑡_(_𝑠_)_,𝑠_=1_, . . . ,𝑡_−1 by (5)|
|14:|**end switch**|
|15:<br>16:|Update_𝜇𝑡_+1(_𝑎_)and_𝜉𝑡_+1(_𝑎_)for each_𝑎_∈A_𝑡_by (3) & (9)<br> **end for**|



the confidence width: 



Then, we pull the selected arm and receive a reward _𝑟𝑡_ ( _𝐼𝑡_ ). Finally, we update the estimated mean reward and the confidence width of each active arm according to (3) and (9). 

The whole procedure is summarized in Algorithm 2. We call this algorithm as Adaptive Discretization with Dynamic Mean Estimator (AD<sup>2</sup> ME). We derive a high probability dynamic regret bound for AD<sup>2</sup> ME as follows, which is stronger than the expected dynamic regret bound of SD<sup>2</sup> ME. 

Theorem 4.2. _With probability at least_ 1 − _𝛿, the dynamic regret of AD_<sup>2</sup> _ME with_ 





Remark 4.2. In AD<sup>2</sup> ME, both the estimated mean reward _𝜇_ ˆ _𝑡_ ( _𝑎_ ) and the confidence width _𝜉𝑡_ ( _𝑎_ ) of each active arm _𝑎_ can be also computed online in the same way as Remark 4.1. Furthermore, we would like to point out that the operation of checking [0 _,_ 1] ⊆ ∪ _𝑎_ ∈A _𝑡_ −1 [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )] at Step 3 of AD<sup>2</sup> ME can be performed with constant time complexity in each round. Specifically, we can maintain a sorted and doubly linked list _𝐿_ = _ℓ_ 1 ↔ _ℓ_ 2 ↔· · · ↔ _ℓ_ |A _𝑡_ | with _ℓ_ 1 _< ℓ_ 2 _<_ · · · _< ℓ_ |A _𝑡_ | to store the active arm set A _𝑡_ . In the first round, we initialize _𝐿_ = _ℓ_ 1 and set _𝜉_ 1 ( _ℓ_ 1) = +∞. Then, in each round _𝑡_ = 2 _, . . . ,𝑇_ , let _ℓ𝑘_ be the node storing the arm pulled at round _𝑡_ − 1, i.e., _ℓ𝑘_ = _𝐼𝑡_ −1. By the definition of the confidence width, all active arms _𝑎_ ∈A _𝑡_ −1 except for _𝐼𝑡_ −1 satisfy _𝜉𝑡_ ( _𝑎_ ) ≥ _𝜉𝑡_ −1 ( _𝑎_ ). Thus, if the linked list is sorted before round _𝑡_ and [0 _,_ 1] ⊆∪ _𝑎_ ∈A _𝑡_ −1 [ _𝑎_ − _𝜉𝑡_ −1 ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ −1 ( _𝑎_ )], we only need to check whether any of the following two inequalities holds. 





If no inequality holds, we simply keep the linked list _𝐿_ unchanged, so that _𝐿_ is sorted after round _𝑡_ and [0 _,_ 1] ⊆∪ _𝑎_ ∈A _𝑡_ [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )]. Otherwise, taking the case of _ℓ𝑘_ + _𝜉𝑡_ ( _ℓ𝑘_ ) _< ℓ𝑘_ +1 − _𝜉𝑡_ ( _ℓ𝑘_ +1) as an example, we first pick a new active arm _𝑎_<sup>′</sup> ∈<sup>�</sup> _ℓ𝑘_ + _𝜉𝑡_ ( _ℓ𝑘_ ) _, ℓ𝑘_ +1 − _𝜉𝑡_ ( _ℓ𝑘_ +1)<sup>�</sup> and create a new node _ℓ_<sup>′</sup> to store _𝑎_<sup>′</sup> . Then, we update the pointers of _ℓ𝑘_ , _ℓ𝑘_ +1, and _ℓ_<sup>′</sup> to _ℓ𝑘_ ↔ _ℓ_<sup>′</sup> ↔ _ℓ𝑘_ +1 so as to ensure _𝐿_ is sorted after round _𝑡_ . Finally, we set _𝜉𝑡_ ( _𝑎_<sup>′</sup> ) = +∞ to guarantee [0 _,_ 1] ⊆∪ _𝑎_ ∈A _𝑡_ [ _𝑎_ − _𝜉𝑡_ ( _𝑎_ ) _,𝑎_ + _𝜉𝑡_ ( _𝑎_ )]. 

## **5 ANALYSIS** 

Due to space limitation, we only prove Theorem 4.1 and Theorem 4.2 for the hard-drop weight configuration and the proofs for the soft-drop weight configuration can be done in a similar way. 

## **5.1 Proof of Theorem 4.1** 

We first partition the _𝑇_ rounds into Γ epochs such that in each epoch the reward distributions are stationary: 



where _𝜏𝑖,𝑖_ = 1 _, . . . ,_ Γ denotes the _𝑖_ -th change point of the reward distributions, i.e., _𝜏_ 1 _<_ · · · _< 𝜏_ Γ and ∃ _𝑎_ ∈[0 _,_ 1] _,_ D _𝜏𝑖_ ≠ D _𝜏𝑖_ −1 ( _𝑎_ ). For notational convenience, we additionally define _𝜏_ Γ+1 = _𝑇_ + 1. 

Fix an epoch _𝑖_ . Let O _𝑖_ = { _𝑎_ ∈A | _𝜇𝜏𝑖_ ( _𝑎_ ) = max _𝑎_ ′ ∈A _𝜇𝜏𝑖_ ( _𝑎_<sup>′</sup> )} be all optimal active arms during the epoch [ _𝜏𝑖,𝜏𝑖_ +1) and _𝑜𝑖_ ∈O _𝑖_ be an optimal active arm. We denote the mean reward gap between an active arm _𝑎_ and the optimal active arm _𝑜𝑖_ by Δ _𝑖_ ( _𝑎_ ) = _𝜇𝜏𝑖_ ( _𝑜𝑖_ ) − _𝜇𝜏𝑖_ ( _𝑎_ ). Define A _𝜌_ = { _𝑎_ ∈A | Δ _𝑖_ ( _𝑎_ ) ≥ _𝜌_ }. We have 



Fix an arm _𝑎_ ∈A _𝜌_ . Define Λ _𝑖_ ( _𝑎_ ) = 4Δ _𝑖_<sup>−2(</sup><sup>_𝑎_) log (</sup><sup>_𝜆_+ 1) and</sup><sup>_𝑛𝑡_(</sup><sup>_𝑎_)=</sup> � _𝑠𝑡_ −=11<sup>_𝑤𝑡_(</sup><sup>_𝑠_)1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_]= �</sup> _𝑠_<sup>_𝑡_−</sup> = _𝑡_<sup>1</sup> − _𝜆_<sup>1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_]. On one hand, we have</sup> 





622 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

Let _𝑜𝑖_<sup>∗beanoptimalarmduringepoch</sup><sup>_𝑖_:</sup><sup>_𝜇𝑡_(</sup><sup>_𝑜_</sup> _𝑖_<sup>∗)=</sup><sup>_𝜇𝑡_(</sup><sup>_𝑎_</sup> _𝑡_<sup>∗)</sup><sup>_,_∀</sup><sup>_𝑡_∈</sup> [ _𝜏𝑖,𝜏𝑖_ +1) _._ By the definition of the active arm set A in (1), there must exist _𝑎_<sup>′</sup> ∈A such that | _𝑜𝑖_<sup>∗−</sup><sup>_𝑎_′|≤</sup><sup>_𝜌_. Thus, we have</sup> 



## **5.2 Proof of Theorem 4.2** 

Following the previous subsection, we partition the _𝑇_ rounds into Γ stationary epochs: [1 _,𝑇_ ] = [ _𝜏_ 1 _,𝜏_ 2) ∪[ _𝜏_ 2 _,𝜏_ 3) ∪· · ·∪[ _𝜏_ Γ _,𝜏_ Γ+1) _._ Let T be a subset of the _𝑇_ rounds: T = ∪ _𝑖_<sup>Γ</sup> =1<sup>[</sup><sup>_𝜏𝑖_+</sup><sup>_𝜆,𝜏𝑖_+1). We first introduce</sup> the following lemma, which is a straightforward consequence of the Hoeffding’s inequality [17] and the union bound [10]. 

Lemma 1. _With probability at least_ 1 − _𝛿, for all rounds 𝑡_ ∈T _and all active arms 𝑎_ ∈A _𝑡 ,_ | ˆ _𝜇𝑡_ ( _𝑎_ ) − _𝜇𝑡_ ( _𝑎_ )| ≤ _𝜉𝑡_ ( _𝑎_ ) _._ 

corpus is first filtered by a candidate generation algorithm and the generated candidate items are then sorted by a ranking method. Taking web search as an example, the goal of candidate generation algorithm is to preserve relevant items w.r.t. user’s query while discarding irrelevant items. Let _𝑣𝑞_ and _𝑣𝑑_ denote the embedding vector of a query _𝑞_ and a document _𝑑_ , respectively. Then, the relevance <u>⟨</u> _𝑣𝑞,𝑣𝑑_ <u>⟩</u> between _𝑞_ and _𝑑_ can be measured via the cosine similarity ∥ _𝑣𝑞_ ∥∥ _𝑣𝑑_ ∥ and documents with relevance exceeding the truncation threshold <u>⟨</u> _𝑣𝑞,𝑣𝑑_ <u>⟩</u> _𝛽_ are designated as candidate items: C _𝑞_ = � _𝑑_ : ∥ _𝑣𝑞_ ∥∥ _𝑣𝑑_ ∥<sup>≥</sup><sup>_𝛽_</sup> � _._ 

The key here is to tune the hyperparameter _𝛽_ ∈[0 _,_ 1]. On the one hand, large _𝛽_ leads to overall high quality of candidate items but may prevent some user-desired items from entering into the ranking phase. On the other hand, small _𝛽_ allows a large number of candidate items but may introduce irrelevant items into the ranking phase. Thus, the tuning of _𝛽_ is non-trivial and requires principled approaches. Since the whose corpus as well as user preference varies with time, the optimal value of _𝛽_ is also not fixed. Furthermore, it is reasonable to believe that similar values of _𝛽_ lead to similar search performance. Thus, we can formulate the tuning of _𝛽_ as a nonstationary continuum-armed bandits problem with each possible configuration of _𝛽_ being an arm. 

## **7 EXPERIMENT** 

Based on this lemma, we then show that the confidence width of each active arm is lower bounded by its mean reward gap. 

Lemma 2. _Let 𝑜𝑖_<sup>∗</sup><sup>_be an optimal arm during epoch 𝑖, i.e., 𝜇𝜏𝑖_(</sup><sup>_𝑜_</sup> _𝑖_<sup>∗)=</sup> max _𝑎_ ∈[0 _,_ 1] _𝜇𝜏𝑖_ ( _𝑎_ ) _and denote the mean reward gap of each arm 𝑎 by_ Δ _𝑖_ ( _𝑎_ ) = _𝜇𝜏𝑖_ ( _𝑜𝑖_<sup>∗) −</sup><sup>_𝜇𝜏𝑖_(</sup><sup>_𝑎_)</sup><sup>_. For all epochs 𝑖_= 1</sup><sup>_, . . . ,_Γ</sup><sup>_, we have_</sup> _𝜋𝜉𝑡_ ( _𝑎_ ) ≥ Δ _𝑖_ ( _𝑎_ ) _,_ ∀ _𝑡_ ∈[ _𝜏𝑖_ + 2 _𝜆,𝜏𝑖_ +1) _,_ ∀ _𝑎_ ∈A _𝑡 ._ 

Proof. The proof is postponed to appendix. □ 

We are now ready to prove Theorem 4.2. Fix an epoch _𝑖_ . We partition [ _𝜏𝑖_ +2 _𝜆,𝜏𝑖_ +1) into [ _𝜈_ 0 _,𝜈_ 1)∪[ _𝜈_ 1 _,𝜈_ 2)∪· · ·∪[ _𝜈 𝐽 ,𝜏𝑖_ +1) with _𝐽_ = ⌊( _𝜏𝑖_ +1 − _𝜏𝑖_ −2 _𝜆_ )/ _𝜆_ ⌋ and _𝜈 𝑗_ = _𝜏𝑖_ +(2+ _𝑗_ ) _𝜆, 𝑗_ = 0 _, . . . , 𝐽_ . Define _𝑛𝑡_ ( _𝑎_ ) = � _𝑠𝑡_ −= _𝑡_ 1− _𝜆_<sup>1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_]</sup><sup>_._By Lemma 2, for each</sup><sup>_𝑗_= 1</sup><sup>_, . . . , 𝐽_and</sup><sup>_𝑎_∈A</sup><sup>_𝜈𝑗_,</sup> we have Δ _𝑖_ ( _𝑎_ ) ≤ _𝜋𝜉𝜈𝑗_ ≤ _𝜋_ √︃log (2 _𝑇_<sup>1</sup><sup>_._5</sup> / _𝛿_<sup>0</sup><sup>_._5</sup> )/ _𝑛𝜈𝑗_ ( _𝑎_ ) _._ It follows that<sup><u>�</u></sup> _𝑡_<sup>_𝜈_</sup> =<sup>_𝑗_−</sup> _𝜈𝑗_<sup>1</sup> −1<sup>[</sup><sup>_𝜇𝑡_(</sup><sup>_𝑎_</sup> _𝑡_<sup>∗)−</sup><sup>_𝜇𝑡_(</sup><sup>_𝐼𝑡_)]=�</sup> _𝑎_ ∈A _𝜈𝑗_ : _𝑛𝜈𝑗_ ( _𝑎_ ) _>_ 0<sup>_𝑛_</sup> _𝜈𝑗_<sup>(</sup><sup>_𝑎_)Δ</sup> _𝑖_<sup>(</sup><sup>_𝑎_)≤</sup> _𝜋_ √︃ _𝜆_<sup>4/3</sup> log (2 _𝑇_<sup>1</sup><sup>_._5</sup> / _𝛿_<sup>0</sup><sup>_._5</sup> ) _._ Summing this over _𝑗_ = 1 _, . . . , 𝐽_ gives _𝜏𝑖_ +1−1 ∑︁ [ _𝜇𝑡_ ( _𝑎𝑡_<sup>∗) −</sup><sup>_𝜇𝑡_(</sup><sup>_𝐼𝑡_)]≤3</sup><sup>_𝜆_+</sup><sup>_𝜆_−1/3(</sup><sup>_𝜏𝑖_+1 −</sup><sup>_𝜏𝑖_)</sup><sup>_𝜋_</sup> √︃log (2 _𝑇_<sup>1</sup><sup>_._5</sup> / _𝛿_<sup>0</sup><sup>_._5</sup> ) _. 𝑡_ = _𝜏𝑖_ 



## **6 APPLICATION: CANDIDATE GENERATION** 

As a case application, we show how our methods can be applied to tune the hyperparameter of the vector-based candidate generation algorithm. In industrial retrieval scenarios such as web search, e-commerce recommendation, and online advertising, a common practice for balancing the trade-off between effectiveness and efficiency is to rank items by a two-phased strategy, where a large 

In this section, we provide extensive experimental results to demonstrate the effectiveness and efficiency of our methods for online hyperparameter optimization. 

## **7.1 Setup** 

_7.1.1 Dataset._ We conduct experiments on the Ali-Display-Ad dataset [14, 44], which was collected from the online advertising logs of taobao for 8 days and has been publicly released<sup>5</sup> . The dataset consists of 26 million records of interactions between 1061768 users and 846811 ads. Each record comprises the identities of the served user and the displayed ad in the interaction, as well as the time stamp of the interaction and the user’s click feedback on the ad. The basic information of both users and ads is also provided in the dataset. Specifically, each user is associated with 8 profile features such as age level, shopping level, and gender. Each ad is described by 5 features including the identity of the advertiser, the campaign of the ad, the category, the brand, and the price of the advertised commodity. All the 13 features except for the price of the advertised commodity are categorical. Following common industrial practice, we also convert the price of the advertised commodity into a categorical feature by splitting the prices of all commodities into 5 equal-sized bins. As the Ali-Display-Ad dataset is sufficiently large, we simply drop the records with missing values of any feature. 

_7.1.2 Experimental Framework._ As described in the previous section, to run the vector-based candidate generation algorithm on the Ali-Display-Ad dataset, an encoding model that can transform the raw features of both user and ad into embedding vectors is required. We take DSSM [18] as the encoding model, which is widely used in online advertising and consists of two sub-networks, one for 

> 5https://tianchi.aliyun.com/dataset/dataDetail?dataId=56 

623 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

encoding user’s features and the other for encoding ad’s features. Each sub-network is comprised of four fully-connected layers with 500, 300, 300, and 128 neurons, respectively and all fully-connected layers are followed by the _tanh_ activation function. Following the approach in [18], we train the DSSM model as follows: We first choose a user _𝑢_ , an ad _𝑎_<sup>+</sup> that was clicked by the user and four ads _𝑎_<sup>−</sup> 1<sup>_, . . . ,𝑎_−</sup> 4<sup>that were not clicked by the user uniformly at ran-</sup> domly from the Ali-Display-Ad dataset. Then, the raw features of user and ads are fed into the corresponding sub-networks to obtain embedding vectors of the user and ads _𝑣𝑢, 𝑣𝑎_ + _, 𝑣𝑎_<sup>−</sup> 1<sup>_, . . . , 𝑣𝑎_−</sup> 4<sup>. The rel-</sup> evance between user and ad is measured via the cosine distance M <u>(</u> _𝑣𝑢,𝑣𝑎_ + <u>)</u> and the loss is defined as _ℓ_ = − log M( _𝑣𝑢,𝑣𝑎_ + )+<sup><u>�</u></sup> _𝑖_<sup>4</sup> =1<sup>M(</sup><sup>_𝑣𝑢,𝑣𝑎_</sup> _𝑖_<sup>−)where</sup> 

<u>⟨</u> _𝑥,𝑦_ <u>⟩</u> M( _𝑥,𝑦_ ) = ∥ _𝑥_ ∥∥ _𝑦_ ∥<sup>denotes the cosine of the angle between</sup><sup>_𝑥_and</sup> _𝑦_ . We train the DSSM model with batch size 1024 by the Adam optimizer [22] for 10000 epochs. 

Equipped with the trained DSSM model, we are now ready to construct an online hyperparameter optimization framework, which proceeds in a sequence of rounds _𝑡_ = 1 _, . . . ,𝑇_ . In each round _𝑡_ , we first select a user _𝑢𝑡_ and collect the ads _𝐴𝑡_ = _𝐴𝑡_<sup>+∪</sup><sup>_𝐴_</sup> _𝑡_<sup>−that were</sup> displayed to this user, where _𝐴𝑡_<sup>+and</sup><sup>_𝐴_</sup> _𝑡_<sup>−denote the set of clicked</sup> and unclicked ads, respectively. To comply with the real-world non-stationary environment, the users are not sampled uniformly at random but picked in order according to the most frequent hour in their interaction time stamps. Then, the trained DSSM model is employed to output the embedding vectors of both the user and ads, denoted as _𝑣𝑢𝑡_ and { _𝑣𝑎_ : _𝑎_ ∈ _𝐴𝑡_<sup>+∪</sup><sup>_𝐴_</sup> _𝑡_<sup>−}. Next, we invoke the</sup> examined hyperparameter optimization algorithm, which outputs a truncation threshold _𝛽𝑡_ . Intuitively, we wish the truncation threshold could preserve as many clicked ads while filtering out as many unclicked ads as possible. Thus, we measure the quality of the truncation threshold via F-score [5], which is the harmonic mean of precision and recall, defined as follows 



Finally, we reveal F _𝑡_ to the examined hyperparameter optimization algorithm as its instantaneous reward. The overall performance of the examined hyperparameter optimization algorithm is measured by its cumulative rewards over _𝑇_ = 10000 rounds:<sup>�</sup><sup>_𝑇_</sup> _𝑡_ =1<sup>F</sup><sup>_𝑡_.</sup> 

_7.1.3 Baselines._ We compare our methods with the following hyperparameter optimization algorithms: 

- **Grid Search.** We split the _𝑇_ rounds into two equal-length phases, one for exploration and the other for exploitation. Specifically, during the first _𝑇_ /2 rounds, ten evenly spaced points over the unit interval [0 _,_ 1] are explored in a roundrobin fashion. Then, the one that achieves the maximum average F-score is exploited in the last _𝑇_ /2 rounds. 

- **Random Search.** We sample ten points uniformly at random from the unit interval [0 _,_ 1]. Similarly to grid search, the first _𝑇_ /2 rounds are taken to explore the sampled points and the empirically best one is used in last _𝑇_ /2 rounds. 

- **Bayesian Optimization.** Following [24], we adopt Gaussian process as the surrogate model and examine two covariance functions, namely squared exponential (SE) function and Matérn function. To make fair comparison, we take upper 

- confidence bound (UCB) as the acquisition function. In each round _𝑡_ , Bayesian Optimization needs to compute the inverse covariance matrix, whose time complexity grows cubicly with _𝑡_ . To control the computation time within a reasonable limit, we train Bayesian optimization during the first _𝑇_ /10 rounds and use its output in the remaining rounds. 

- **Hyperband.** Following [26], we set the proportion of candidate hyperparameter configurations discarded in each round as 1/3. As Hyperband is originally designed for offline scenarios, we take the first _𝑇_ /2 rounds to train Hyperband and use its output in the last _𝑇_ /2 rounds. Accordingly, the maximum amount of resource that can be allocated to a single hyperparameter configuration is set as _<u>𝑇</u>_ 2(ln _𝑇_ +1)<sup>2.</sup> 

We configure our methods according to Theorem 4.1 and Theorem 4.2. While the actual non-stationarity Γ remains unknown in the experiments, we simply replace Γ with an estimated nonstationarity Γ<sup>˜</sup> = 10 in (8) and (12). 

_7.1.4 Research Questions._ We aim to answer the following research questions via experiments: 

- (1) How does our methods perform in comparison with the baseline algorithms? 

- (2) To what extent does the mismatch between the estimated non-stationarity Γ<sup>˜</sup> and the actual non-stationarity Γ affect the performance of our methods? 

- (3) How about the efficiency of our methods compared to the baseline algorithms? 

## **7.2 Results and Analysis** 

We start with the first research question and run our methods and each baseline algorithm in the online hyperparameter optimization experimental framework ten times. The average performance as well as the standard deviation of each algorithm is listed in Table 1. We can observe that the two brute-force algorithms grid search and random search behave the worst. This is because the two algorithms lack guidance in exploring on the unit interval [0 _,_ 1] and hence waste too much time on bad truncation thresholds. This drawback is addressed by the Bayesian optimization and Hyperband algorithms where the exploration process is guided by historical observations of previously tried truncation thresholds. As can be seen, such informative exploration indeed translates into improved cumulative F-score. Nevertheless, we can also see that our methods with both soft-drop and hard-drop weight configurations achieve significantly higher cumulative F-score than the Bayesian optimization and Hyperband algorithms. This is expected as online advertising is a typical non-stationary scenario where the overall click-through-rate varies with time period and so does the optimal truncation threshold, while Bayesian optimization and Hyperband are designed for stationary scenarios assuming the existence of a global optimal truncation threshold over all time periods. By contrast, both of our methods SD<sup>2</sup> ME and AD<sup>2</sup> ME take the non-stationarity into account and track the time-varying optimism truncation threshold via dynamic mean estimator. Taking a closer look at the performance of our methods, there is clear performance improvement of AD<sup>2</sup> ME over SD<sup>2</sup> ME, which validates the 

624 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

**Table 1: Performance comparison between our methods and the baseline algorithms on the Ali-Display-Ad dataset.**<sup>_★_</sup> **denotes significant improvement over all baseline algorithms at** _𝑝 <_ 0 _._ 01 **. The unit of computation time is second.** 

|Algorithm|Cumulative F-score|Computation Time|
|---|---|---|
|Grid Search|3396±0_._0|517|
|Random Search|3467±64_._9|528|
|Hyperband|3550±49_._2|546|
|Bayesian-Matérn|3564±14_._5|43426|
|Bayesian-SE|3533±20_._7|37283|
|SD<sup>2</sup>ME-hard|3673±5_._9<sup>_★_</sup>|612|
|SD<sup>2</sup>ME-soft|3671±4_._3<sup>_★_</sup>|568|
|AD<sup>2</sup>ME-hard|3714±15_._2<sup>_★_</sup>|745|
|AD<sup>2</sup>ME-soft|3720±19_._8<sup>_★_</sup>|671|



superiority of adaptive discretization for online hyperparameter optimization. 

We then answer the second research question by running our methods with different estimated non-stationarity ranging from 5 to 25. Except for the estimated non-stationarity, the other experimental setup is the same as that in the above investigation of the first research question. We plot the performance of our methods under each estimated non-stationarity Γ<sup>˜</sup> = 5 _,_ 10 _,_ 15 _,_ 20 _,_ 25 in Figure 1. The curve of cumulative F-score versus estimated non-stationarity varies slowly, which reveals that our methods are relatively robust to the mismatch between the estimated non-stationarity and the actual non-stationarity of the experimental environment. 

Finally, we investigate the last research question. To this end, we record the overall computation time of each algorithm, which is also listed in Table 1 for saving space. The first observation is that Bayesian optimization takes much longer time than the other algorithms. This is due to the time-consuming operation of inverting the covariance matrix, which makes the overall time complexity of Bayesian optimization scale with _𝑂_ ( _𝑇_<sup>3</sup> ). By contrast, the other algorithms all perform constant-time operations in each round, leading to an overall time complexity of _𝑂_ ( _𝑇_ ). Further comparing our methods with grid search, random search and Hyperband, we see that the computation time of our methods are slightly higher, which is acceptable in light of the improvement on online performance. We can also observe that within our methods, soft-drop weight configuration is more efficient than hard-drop weight configuration, which is intuitive as the latter needs to additionally maintain queues as discussed in Remark 4.1. 

## **7.3 Online A/B Testing** 

The candidate generation is an important stage for search, recommendation, and advertising on e-commerce platforms. In practice, several candidate generation algorithms are always kept in online service, each providing a set of candidate items for the subsequent ranking stage. Among them, the vector-based candidate generation algorithm has attracted much attention recently. As discussed in Section 6, the performance of the vector-based candidate generation algorithm heavily depends on the truncation threshold. A common 



<!-- Start of picture text -->
3800<br>SD 2 ME-hard<br>3775 SD 2 ME-soft<br>3750 AD 2 ME-hard<br>AD 2 ME-soft<br>3725<br>3700<br>3675<br>3650<br>3625<br>3600<br>5 10 15 20 25<br>estimated non-stationarity<br>Cumulative F-score<br><!-- End of picture text -->

**Figure 1: Performance of our methods with different** Γ<sup>˜</sup> 

practice is to manually choose the truncation threshold based on historical data, which may fail in the non-stationary environment. 

We deployed our methods on an international e-commerce platform, to optimize the truncation threshold of the vector-based candidate generation algorithm. In this platform, the queries are categorized into several disjointed classes according to their natural categories. Thus, we run our methods for each category separately to obtain meticulous thresholds. Our goal is to maximize the user conversion rate, which is defined as the ratio of the buyer number to the visitor number in the platform. Moreover, to decrease the gap between the conversion rate of users and that of items, we introduce a novel reward formulation where every arm benefits from the conversion of the same user-query pair in the future 10 minutes time window. The results of online A/B testing demonstrate that compared to the manually fine-tuning, our methods gain 2 _._ 24% more user conversion rate and 2 _._ 38% more GMV per visitor over 14 days. 

## **8 CONCLUSION AND FUTURE WORK** 

In this paper, we propose a novel bandit-type formulation for online hyperparameter optimization, where each hyperparameter configuration is viewed as an arm and the algorithmic performance is modelled as reward. We name the proposed bandit formulation as non-stationary continuum-armed bandits, for which we develop two effective and efficient methods. Theoretically, we prove that both of our methods can achieve sub-linear dynamic regret bounds, which, to the best of our knowledge, is the first theoretical result for continuum-armed bandits in non-stationary environments and may be of independent interest. We also empirically demonstrate the effectiveness and efficiency of our methods by extensive experiments on both public advertising dataset and online A/B testing. 

Currently, we only consider online optimization of single hyperparameter. While multiple hyperparameters can be optimized separately by our methods, the correlation structure between different hyperparameters remains to be investigated. We leave the study of online and joint optimization of multiple hyperparameters as a future work. 

## **ACKNOWLEDGMENTS** 

This work was partially supported by NSFC (62122037), JiangsuSF (BK20200064), and the Open Research Projects of Zhejiang Lab (NO. 2021KB0AB02). We thank the anonymous reviewers for their constructive suggestions. 

625 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

## **REFERENCES** 

- [1] Deepak Agarwal, Bo Long, Jonathan Traupman, Doris Xin, and Liang Zhang. 2014. Laser: A scalable response prediction platform for online advertising. In _Proceedings of the 7th ACM international conference on Web search and data mining_ . 173–182. 

- [2] Richard Loree Anderson. 1953. Recent advances in finding best operating conditions. _J. Amer. Statist. Assoc._ 48, 264 (1953), 789–798. 

- [3] Peter Auer, Nicolo Cesa-Bianchi, and Paul Fischer. 2002. Finite-time analysis of the multiarmed bandit problem. _Machine learning_ 47, 2-3 (2002), 235–256. 

- [4] Manpreet Singh Bajwa, Ravi Rana, and Geetanshi Bagga. 2020. Machine LearningBased Information Retrieval System. In _The International Conference on Recent Innovations in Computing_ . Springer, 13–22. 

- [5] Steven M Beitzel. 2006. _On understanding and classifying web queries_ . Citeseer. 

- [6] James Bergstra, Rémi Bardenet, Yoshua Bengio, and Balázs Kégl. 2011. Algorithms for hyper-parameter optimization. In _25th annual conference on neural information processing systems (NIPS 2011)_ , Vol. 24. Neural Information Processing Systems Foundation. 

- [7] James Bergstra and Yoshua Bengio. 2012. Random search for hyper-parameter optimization. _Journal of machine learning research_ 13, 2 (2012). 

- [8] Fedor Borisyuk, Krishnaram Kenthapadi, David Stein, and Bo Zhao. 2016. CaSMoS: A framework for learning candidate selection models over structured queries and documents. In _Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining_ . 441–450. 

- [9] Chih-Chung Chang and Chih-Jen Lin. 2011. LIBSVM: a library for support vector machines. _ACM transactions on intelligent systems and technology (TIST)_ 2, 3 (2011), 1–27. 

- [10] Louis Comtet. 2012. _Advanced Combinatorics: The art of finite and infinite expansions_ . Springer Science & Business Media. 

- [11] Nuno Dionísio, Fernando Alves, Pedro M Ferreira, and Alysson Bessani. 2019. Cyberthreat detection from twitter using deep neural networks. In _2019 International Joint Conference on Neural Networks_ . IEEE, 1–8. 

- [12] Katharina Eggensperger, Matthias Feurer, Frank Hutter, James Bergstra, Jasper Snoek, Holger Hoos, and Kevin Leyton-Brown. 2013. Towards an empirical foundation for assessing bayesian optimization of hyperparameters. In _NIPS workshop on Bayesian Optimization in Theory and Practice_ , Vol. 10. 3. 

- [13] Matthias Feurer, Aaron Klein, Katharina Eggensperger, Jost Springenberg, Manuel Blum, and Frank Hutter. 2015. Efficient and Robust Automated Machine Learning. In _Advances in Neural Information Processing Systems_ . Curran Associates, Inc. 

- [14] Kun Gai, Xiaoqiang Zhu, Han Li, Kai Liu, and Zhe Wang. 2017. Learning piecewise linear models from large scale data for ad click prediction. _arXiv preprint arXiv:1704.05194_ (2017). 

- [15] Aurélien Garivier and Eric Moulines. 2011. On upper-confidence bound policies for switching bandit problems. In _Proceedings of the 22nd International Conference on Algorithmic Learning Theory_ . PRML, 174–188. 

- [16] Artem Grotov and Maarten de Rijke. 2016. Online learning to rank for information retrieval: Sigir 2016 tutorial. In _Proceedings of the 39th International ACM SIGIR conference on Research and Development in Information Retrieval_ . 1215–1218. 

- [17] Wassily Hoeffding. 1963. Probability inequalities for sums of bounded random variables. _Journal of the American statistical association_ 58, 301 (1963), 13–30. 

- [18] Po-Sen Huang, Xiaodong He, Jianfeng Gao, Li Deng, Alex Acero, and Larry Heck. 2013. Learning deep structured semantic models for web search using clickthrough data. In _Proceedings of the 22nd ACM international conference on Information & Knowledge Management_ . 2333–2338. 

- [19] Frank Hutter, Holger H Hoos, and Kevin Leyton-Brown. 2011. Sequential modelbased optimization for general algorithm configuration. In _International conference on learning and intelligent optimization_ . Springer, 507–523. 

- [20] Kevin Jamieson and Ameet Talwalkar. 2016. Non-stochastic Best Arm Identification and Hyperparameter Optimization. In _Proceedings of the 19th International Conference on Artificial Intelligence and Statistics_ , Arthur Gretton and Christian C. Robert (Eds.), Vol. 51. PMLR, Cadiz, Spain, 240–248. 

- [21] Abdul Rehman Khan, Ameer Tamoor Khan, Masood Salik, and Sunila Bakhsh. 2021. An Optimally Configured HP-GRU Model Using Hyperband for the Control of Wall Following Robot. _International Journal of Robotics and Control Systems_ 1, 1 (2021), 66–74. 

- [22] Diederik P Kingma and Jimmy Ba. 2014. Adam: A method for stochastic optimization. _arXiv preprint arXiv:1412.6980_ (2014). 

- [23] Aaron Klein, Stefan Falkner, Simon Bartels, Philipp Hennig, and Frank Hutter. 2017. Fast Bayesian Optimization of Machine Learning Hyperparameters on Large Datasets. In _Proceedings of the 20th International Conference on Artificial Intelligence and Statistics_ , Aarti Singh and Jerry Zhu (Eds.), Vol. 54. PMLR, Fort Lauderdale, FL, USA, 528–536. 

- [24] Dan Li and Evangelos Kanoulas. 2018. Bayesian optimization for optimizing retrieval systems. In _Proceedings of the Eleventh ACM International Conference on Web Search and Data Mining_ . 360–368. 

- [25] Hang Li and Zhengdong Lu. 2016. Deep learning for information retrieval. In _Proceedings of the 39th International ACM SIGIR conference on Research and Development in Information Retrieval_ . 1203–1206. 

- [26] Lisha Li, Kevin Jamieson, Giulia DeSalvo, Afshin Rostamizadeh, and Ameet Talwalkar. 2017. Hyperband: A novel bandit-based approach to hyperparameter optimization. _The Journal of Machine Learning Research_ 18, 1 (2017), 6765–6816. 

- [27] Tie-Yan Liu. 2011. Learning to rank for information retrieval. (2011). 

- [28] Debanjan Mahata, Jasper Friedrichs, Rajiv Ratn Shah, and Jing Jiang. 2018. Detecting personal intake of medicine from twitter. _IEEE Intelligent Systems_ 33, 4 (2018), 87–95. 

- [29] Adam Paszke, Sam Gross, Francisco Massa, Adam Lerer, James Bradbury, Gregory Chanan, Trevor Killeen, Zeming Lin, Natalia Gimelshein, Luca Antiga, et al. 2019. PyTorch: An Imperative Style, High-Performance Deep Learning Library. _Advances in Neural Information Processing Systems_ 32 (2019), 8026–8037. 

- [30] F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. 2011. Scikit-learn: Machine Learning in Python. _Journal of Machine Learning Research_ 12 (2011), 2825–2830. 

- [31] BH Shekar and Guesh Dagnew. 2019. Grid search-based hyperparameter tuning and classification of microarray cancer data. In _2019 Second International Conference on Advanced Computational and Communication Paradigms (ICACCP)_ . IEEE, 1–8. 

- [32] Luo Si and Rong Jin. 2011. Machine Learning for Information Retrieval. In _Proceedings of the 34th International ACM SIGIR Conference on Research and Development in Information Retrieval_ . Association for Computing Machinery, New York, NY, USA, 1293–1294. 

- [33] Jasper Snoek, Hugo Larochelle, and Ryan Prescott Adams. 2012. Practical Bayesian Optimization of Machine Learning Algorithms. _Advances in Neural Information Processing Systems_ (2012). 

- [34] Francisco J Solis and Roger J-B Wets. 1981. Minimization by random search techniques. _Mathematics of operations research_ 6, 1 (1981), 19–30. 

- [35] Chris Thornton, Frank Hutter, Holger H Hoos, and Kevin Leyton-Brown. 2013. Auto-WEKA: Combined selection and hyperparameter optimization of classification algorithms. In _Proceedings of the 19th ACM SIGKDD international conference on Knowledge discovery and data mining_ . 847–855. 

- [36] Lazar Valkov, Rodolphe Jenatton, Fela Winkelmolen, and Cédric Archambeau. 2018. A simple transfer-learning extension of Hyperband. In _NIPS Workshop on Meta-Learning_ . 

- [37] Lidan Wang, Minwei Feng, Bowen Zhou, Bing Xiang, and Sridhar Mahadevan. 2015. Efficient hyper-parameter optimization for NLP applications. In _Proceedings of the 2015 Conference on Empirical Methods in Natural Language Processing_ . 2112– 2117. 

- [38] Xiashuang Wang, Guanghong Gong, Ni Li, and Shi Qiu. 2019. Detection analysis of epileptic EEG using a novel random forest model combined with grid search optimization. _Frontiers in human neuroscience_ 13 (2019), 52. 

- [39] Li Yang and Abdallah Shami. 2020. On hyperparameter optimization of machine learning algorithms: Theory and practice. _Neurocomputing_ 415 (2020), 295–316. 

- [40] Lei Yao, Zhanpeng Fang, Yanqiu Xiao, Junjian Hou, and Zhijun Fu. 2021. An intelligent fault diagnosis method for lithium battery systems based on grid search support vector machine. _Energy_ 214 (2021), 118866. 

- [41] Hema Yoganarasimhan. 2020. Search personalization using machine learning. _Management Science_ 66, 3 (2020), 1045–1070. 

- [42] Weinan Zhang, Xiangyu Zhao, Li Zhao, Dawei Yin, Grace Hui Yang, and Alex Beutel. 2020. Deep Reinforcement Learning for Information Retrieval: Fundamentals and Advances. In _Proceedings of the 43rd International ACM SIGIR Conference on Research and Development in Information Retrieval_ . 2468–2471. 

- [43] Qi Zhao, Yi Zhang, Daniel Friedman, and Fangfang Tan. 2015. E-commerce recommendation with personalized promotion. In _Proceedings of the 9th ACM Conference on Recommender Systems_ . 219–226. 

- [44] Guorui Zhou, Xiaoqiang Zhu, Chenru Song, Ying Fan, Han Zhu, Xiao Ma, Yanghui Yan, Junqi Jin, Han Li, and Kun Gai. 2018. Deep interest network for click-through rate prediction. In _Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining_ . Association for Computing Machinery, New York, NY, USA, 1059–1068. 

- [45] Marc-André Zöller and Marco F Huber. 2021. Benchmark and survey of automated machine learning frameworks. _Journal of Artificial Intelligence Research_ 70 (2021), 409–472. 

## **A PROOF OF LEMMA 2** 

Proof. Fix an epoch _𝑖_ , a round _𝑡_ ∈[ _𝜏𝑖_ + 2 _𝜆,𝜏𝑖_ +1), and an active arm _𝑎_ ∈A _𝑡_ . Let _𝑡_<sup>′</sup> be the last round when _𝑎_ is pulled, i.e., _𝐼𝑡_<sup>′</sup> = _𝑎_ and _𝑎_ ∉ <u>{</u> _𝐼𝑡_<sup>′</sup> +1 _, . . . , 𝐼𝑡_ −1}. If _𝑡_<sup>′</sup> _< 𝑡_ − _𝜆_ , we have _𝜉𝑡_ ( _𝑎_ ) = ~~√~~ log (2 _𝑡_<sup>1</sup><sup>_._5</sup> / _𝛿_<sup>0</sup><sup>_._5</sup> )/<sup><u>�</u></sup> _𝑠_<sup>_𝑡_−</sup> = _𝑡_<sup>1</sup> − _𝜆_<sup>1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_]=+∞</sup><sup>_._Thus,theinequality</sup> _𝜋𝜉𝑡_ ( _𝑎_ ) ≥ Δ _𝑖_ ( _𝑎_ ) trivially holds. 

Below, we consider the case _𝑡_<sup>′</sup> ≥ _𝑡_ − _𝜆_ . On the one hand, since (10) is guaranteed throughout the _𝑇_ rounds, there must exist an 

626 

WSDM ’22, Feb. 21–25, 2022, Virtual Event, Tempe, AZ, USA 

Research Paper 

active arm _𝑎_<sup>′</sup> ∈A _𝑡_<sup>′</sup> such that its covering interval contains the optimal arm _𝑜𝑖_<sup>∗, i.e.,</sup><sup>_𝑜_</sup> _𝑖_<sup>∗∈[</sup><sup>_𝑎_′ −</sup><sup>_𝜉𝑡_′(</sup><sup>_𝑎_′)</sup><sup>_,𝑎_′ +</sup><sup>_𝜉𝑡_′(</sup><sup>_𝑎_′)]. By the Lipschitz</sup> continuity of mean reward function, we have 



On the other hand, according to the arm selection rule in (11), _𝐼𝑡_<sup>′</sup> = _𝑎_ implies _𝜇_ ˆ _𝑡_<sup>′</sup> ( _𝑎_ ) + 2 _𝜉𝑡_<sup>′</sup> ( _𝑎_ ) ≥ _𝜇_ ˆ _𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) + 2 _𝜉𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) _._ As _𝑡_<sup>′</sup> ≥ _𝑡_ − _𝜆_ , we have _𝑡_<sup>′</sup> ≥ _𝜏𝑖_ + _𝜆_ and hence _𝑡_ ∈T . Applying Lemma 1 gives 

_𝜇_ ˆ _𝑡_<sup>′</sup> ( _𝑎_ ) − _𝜇𝑡_<sup>′</sup> ( _𝑎_ ) ≤ _𝜉𝑡_<sup>′</sup> ( _𝑎_ ) and _𝜇𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) − _𝜇_ ˆ _𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) ≤ _𝜉𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) _._ By these three inequalities, we obtain 

_𝜇𝑡_<sup>′</sup> ( _𝑎_ ) + 3 _𝜉𝑡_<sup>′</sup> ( _𝑎_ ) ≥ _𝜇𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) + _𝜉𝑡_<sup>′</sup> ( _𝑎_<sup>′</sup> ) _._ (19) 

Combining (18) and (19) leads to Δ _𝑖_ ( _𝑎_ ) = _𝜇𝑡_<sup>′</sup> ( _𝑜𝑖_<sup>∗)−</sup><sup>_𝜇𝑡_′(</sup><sup>_𝑎_)≤3</sup><sup>_𝜉𝑡_′(</sup><sup>_𝑎_)</sup><sup>_._</sup> Finally, if _𝑎_ is pulled not more than ten times during [ _𝑡_<sup>′</sup> − _𝜆,𝑡_<sup>′</sup> −1], we have<sup>�</sup> _𝑠_<sup>_𝑡_−</sup> = _𝑡_<sup>1</sup> − _𝜆_<sup>1[</sup><sup>_𝐼𝑠_=</sup><sup>_𝑎_]≤11 and hence</sup><sup>_𝜋𝜉𝑡_(</sup><sup>_𝑎_)≥1≥Δ</sup><sup>_𝑖_(</sup><sup>_𝑎_)</sup><sup>_._</sup> Otherwise, we have _𝜉𝑡_ ( _𝑎_ )/ _𝜉𝑡_<sup>′</sup> ( _𝑎_ ) ≥ ~~√~~ 11/12 ≥ 3/ _𝜋_ . □ 

627 

