---
# --- bibliographic record ---
entry_type: inproceedings
title: "Algorithms for Hyper-Parameter Optimization"
authors:
  - "James Bergstra"
  - "Rémi Bardenet"
  - "Yoshua Bengio"
  - "Balázs Kégl"
year: 2011
venue: "Advances in Neural Information Processing Systems 24"
volume: ""
issue: ""
pages: "2546-2554"
publisher: ""
doi: ""
arxiv: ""
url: "https://papers.nips.cc/paper_files/paper/2011/hash/86e8f7ab32cfd12577bc2619bc635690-Abstract.html"

# --- archive record ---
source_pdf: bergstra-tpe-hyperparameter-optimization-2011.pdf
source_sha256: a5355a3d610dc82f1cc024bb09d063790974a23a7710c0b80b1e38b8ed58a965
pdf_pages: 9
converted: 2026-11-12
record_source: manual
review: "fields entered by hand from the archived file, checked 2026-11-12"
key_insight: "x) (§3)."
first_page: "Algorithms for Hyper-Parameter Optimization James Bergstra The Rowland Institute Harvard University bergstra@rowland.harvard.edu R´emi Bardenet Laboratoire de Recherche en Informatique Universit´e Par"
---
# **Algorithms for Hyper-Parameter Optimization** 

|**James Bergstra**<br>The Rowland Institute<br>Harvard University<br>Labor|**R´emi Bardenet**<br>atoire de Recherche en Informatique<br>Universit´e Paris-Sud|
|---|---|
|bergstra@rowland.harvard.edu|bardenet@lri.fr|
|**Yoshua Bengio**|**Bal´azs K´egl**|
|D´ept. d’Informatique et Recherche Op´erationelle<br>Universit´e de Montr´eal|Linear Accelerator Laboratory<br>Universit´e Paris-Sud, CNRS|
|yoshua.bengio@umontreal.ca|balazs.kegl@gmail.com|



## **Abstract** 

Several recent advances to the state of the art in image classification benchmarks have come from better configurations of existing techniques rather than novel approaches to feature learning. Traditionally, hyper-parameter optimization has been the job of humans because they can be very efficient in regimes where only a few trials are possible. Presently, computer clusters and GPU processors make it possible to run more trials and we show that algorithmic approaches can find better results. We present hyper-parameter optimization results on tasks of training neural networks and deep belief networks (DBNs). We optimize hyper-parameters using random search and two new greedy sequential methods based on the expected improvement criterion. Random search has been shown to be sufficiently efficient for learning neural networks for several datasets, but we show it is unreliable for training DBNs. The sequential algorithms are applied to the most difficult DBN learning problems from [1] and find significantly better results than the best previously reported. This work contributes novel techniques for making response surface models _P_ ( _y|x_ ) in which many elements of hyper-parameter assignment ( _x_ ) are known to be irrelevant given particular values of other elements. 

## **1 Introduction** 

Models such as Deep Belief Networks (DBNs) [2], stacked denoising autoencoders [3], convolutional networks [4], as well as classifiers based on sophisticated feature extraction techniques have from ten to perhaps fifty hyper-parameters, depending on how the experimenter chooses to parametrize the model, and how many hyper-parameters the experimenter chooses to fix at a reasonable default. The difficulty of tuning these models makes published results difficult to reproduce and extend, and makes even the original investigation of such methods more of an art than a science. 

Recent results such as [5], [6], and [7] demonstrate that the challenge of hyper-parameter optimization in large and multilayer models is a direct impediment to scientific progress. These works have advanced state of the art performance on image classification problems by more concerted hyper-parameter optimization in simple algorithms, rather than by innovative modeling or machine learning strategies. It would be wrong to conclude from a result such as [5] that feature learning is useless. Instead, hyper-parameter optimization should be regarded as a formal outer loop in the learning process. A learning algorithm, as _a functional from data to classifier_ (taking classification problems as an example), includes a budgeting choice of how many CPU cycles are to be spent on hyper-parameter exploration, and how many CPU cycles are to be spent evaluating each hyperparameter choice (i.e. by tuning the regular parameters). The results of [5] and [7] suggest that with current generation hardware such as large computer clusters and GPUs, the optimal alloca- 

1 

tion of CPU cycles includes more hyper-parameter exploration than has been typical in the machine learning literature. 

Hyper-parameter optimization is the problem of optimizing a loss function over a graph-structured configuration space. In this work we restrict ourselves to tree-structured configuration spaces. Configuration spaces are tree-structured in the sense that some leaf variables (e.g. the number of hidden units in the 2nd layer of a DBN) are only well-defined when node variables (e.g. a discrete choice of how many layers to use) take particular values. Not only must a hyper-parameter optimization algorithm optimize over variables which are discrete, ordinal, and continuous, but it must simultaneously choose which variables to optimize. 

In this work we define a configuration space by a generative process for drawing valid samples. Random search is the algorithm of drawing hyper-parameter assignments from that process and evaluating them. Optimization algorithms work by identifying hyper-parameter assignments that could have been drawn, and that appear promising on the basis of the loss function’s value at other points. This paper makes two contributions: 1) Random search is competitive with the manual optimization of DBNs in [1], and 2) Automatic sequential optimization outperforms both manual and random search. 

Section 2 covers sequential model-based optimization, and the expected improvement criterion. Section 3 introduces a Gaussian Process based hyper-parameter optimization algorithm. Section 4 introduces a second approach based on adaptive Parzen windows. Section 5 describes the problem of DBN hyper-parameter optimization, and shows the efficiency of random search. Section 6 shows the efficiency of sequential optimization on the two hardest datasets according to random search. The paper concludes with discussion of results and concluding remarks in Section 7 and Section 8. 

## **2 Sequential Model-based Global Optimization** 

Sequential Model-Based Global Optimization (SMBO) algorithms have been used in many applications where evaluation of the fitness function is expensive [8, 9]. In an application where the true fitness function _f_ : _X →_ R is costly to evaluate, model-based algorithms approximate _f_ with a surrogate that is cheaper to evaluate. Typically the inner loop in an SMBO algorithm is the numerical optimization of this surrogate, or some transformation of the surrogate. The point _x_<sup>_∗_</sup> that maximizes the surrogate (or its transformation) becomes the proposal for where the true function _f_ should be evaluated. This active-learning-like algorithm template is summarized in Figure 1. SMBO algorithms differ in what criterion they optimize to obtain _x_<sup>_∗_</sup> given a model (or surrogate) of _f_ , and in they model _f_ via observation history _H_ . 

|SMBO<br><br>1|�<br>_f, M_0_, T, S_<br>�<br>_H ←∅_,|
|---|---|
|2|For_t ←_1**to** _T_,|
|3|_x_<sup>_∗_</sup>_←_argmin_x S_(_x, Mt−_1),|
|4|Evaluate_f_(_x_<sup>_∗_</sup>),<br>_▷Expensive step_|
|5|_H ←H ∪_(_x_<sup>_∗_</sup>_, f_(_x_<sup>_∗_</sup>)),|
|6|Fit a new model_Mt_to_H_.|
|7|**return**_H_|



Figure 1: The pseudo-code of generic Sequential Model-Based Optimization. 

The algorithms in this work optimize the criterion of Expected Improvement (EI) [10]. Other criteria have been suggested, such as Probability of Improvement and Expected Improvement [10], minimizing the Conditional Entropy of the Minimizer [11], and the bandit-based criterion described in [12]. We chose to use the EI criterion in our work because it is intuitive, and has been shown to work well in a variety of settings. We leave the systematic exploration of improvement criteria for future work. Expected improvement is the expectation under some model _M_ of _f_ : _X →_ R<sup>_N_</sup> that _f_ ( _x_ ) will exceed (negatively) some threshold _y_<sup>_∗_</sup> : 



2 

The contribution of this work is two novel strategies for approximating _f_ by modeling _H_ : a hierarchical Gaussian Process and a tree-structured Parzen estimator. These are described in Section 3 and Section 4 respectively. 

## **3 The Gaussian Process Approach (GP)** 

Gaussian Processes have long been recognized as a good method for modeling loss functions in model-based optimization literature [13]. Gaussian Processes (GPs, [14]) are priors over functions that are _closed under sampling_ , which means that if the prior distribution of _f_ is believed to be a GP with mean 0 and kernel _k_ , the conditional distribution of _f_ knowing a sample _H_ = ( _xi, f_ ( _xi_ ))<sup>_n_</sup> _i_ =1 of its values is also a GP, whose mean and covariance function are analytically derivable. GPs with generic mean functions can in principle be used, but it is simpler and sufficient for our purposes to only consider zero mean processes. We do this by centering the function values in the considered data sets. Modelling e.g. linear trends in the GP mean leads to undesirable extrapolation in unexplored regions during SMBO [15]. 

The above mentioned closedness property, along with the fact that GPs provide an assessment of prediction uncertainty incorporating the effect of data scarcity, make the GP an elegant candidate for both finding candidate _x_<sup>_∗_</sup> (Figure 1, step 3) and fitting a model _Mt_ (Figure 1, step 6). The runtime of each iteration of the GP approach scales cubically in _|H|_ and linearly in the number of variables being optimized, however the expense of the function evaluations _f_ ( _x_<sup>_∗_</sup> ) typically dominate even this cubic cost. 

### **3.1 Optimizing EI in the GP** 

We model _f_ with a GP and set _y_<sup>_∗_</sup> to the best value found after observing _H_ : _y_<sup>_∗_</sup> = min _{f_ ( _xi_ ) _,_ 1 _≤ i ≤ n}_ . The model _pM_ in (1) is then the posterior GP knowing _H_ . The EI function in (1) encapsulates a compromise between regions where the mean function is close to or better than _y_<sup>_∗_</sup> and under-explored regions where the uncertainty is high. 

EI functions are usually optimized with an exhaustive grid search over the input space, or a Latin Hypercube search in higher dimensions. However, some information on the landscape of the EI criterion can be derived from simple computations [16]: 1) it is always non-negative and zero at training points from _D_ , 2) it inherits the smoothness of the kernel _k_ , which is in practice often at least once differentiable, and noticeably, 3) the EI criterion is likely to be highly multi-modal, especially as the number of training points increases. The authors of [16] used the preceding remarks on the landscape of EI to design an evolutionary algorithm with mixture search, specifically aimed at optimizing EI, that is shown to outperform exhaustive search for a given budget in EI evaluations. We borrow here their approach and go one step further. We keep the Estimation of Distribution (EDA, [17]) approach on the discrete part of our input space (categorical and discrete hyper-parameters), where we sample candidate points according to binomial distributions, while we use the Covariance Matrix Adaptation - Evolution Strategy (CMA-ES, [18]) for the remaining part of our input space (continuous hyper-parameters). CMA-ES is a state-of-the-art gradient-free evolutionary algorithm for optimization on continuous domains, which has been shown to outperform the Gaussian search EDA. Notice that such a gradient-free approach allows non-differentiable kernels for the GP regression. We do not take on the use of mixtures in [16], but rather restart the local searches several times, starting from promising places. The use of tesselations suggested by [16] is prohibitive here, as our task often means working in more than 10 dimensions, thus we start each local search at the center of mass of a simplex with vertices randomly picked among the training points. 

Finally, we remark that all hyper-parameters are not relevant for each point. For example, a DBN with only one hidden layer does not have parameters associated to a second or third layer. Thus it is not enough to place one GP over the entire space of hyper-parameters. We chose to group the hyper-parameters by common use in a tree-like fashion and place different independent GPs over each group. As an example, for DBNs, this means placing one GP over common hyper-parameters, including categorical parameters that indicate what are the _conditional_ groups to consider, three GPs on the parameters corresponding to each of the three layers, and a few 1-dimensional GPs over individual conditional hyper-parameters, like ZCA energy (see Table 1 for DBN parameters). 

3 

## **4 Tree-structured Parzen Estimator Approach (TPE)** 

Anticipating that our hyper-parameter optimization tasks will mean high dimensions and small fitness evaluation budgets, we now turn to another modeling strategy and EI optimization scheme for the SMBO algorithm. Whereas the Gaussian-process based approach modeled _p_ ( _y|x_ ) directly, this strategy models _p_ ( _x|y_ ) and _p_ ( _y_ ). 

Recall from the introduction that the configuration space _X_ is described by a graph-structured generative process (e.g. first choose a number of DBN layers, then choose the parameters for each). The tree-structured Parzen estimator (TPE) models _p_ ( _x|y_ ) by transforming that generative process, replacing the distributions of the configuration prior with non-parametric densities. In the experimental section, we will see that the configuation space is described using uniform, log-uniform, quantized log-uniform, and categorical variables. In these cases, the TPE algorithm makes the following replacements: uniform _→_ truncated Gaussian mixture, log-uniform _→_ exponentiated truncated Gaussian mixture, categorical _→_ re-weighted categorical. Using different observations _{x_<sup>(1)</sup> _, ..., x_<sup>(</sup><sup>_k_)</sup> _}_ in the non-parametric densities, these substitutions represent a _learning algorithm_ that can produce a variety of densities over the configuration space _X_ . The TPE defines _p_ ( _x|y_ ) using two such densities: 



where _ℓ_ ( _x_ ) is the density formed by using the observations _{x_<sup>(</sup><sup>_i_)</sup> _}_ such that corresponding loss _f_ ( _x_<sup>(</sup><sup>_i_)</sup> ) was less than _y_<sup>_∗_</sup> and _g_ ( _x_ ) is the density formed by using the remaining observations. Whereas the GP-based approach favoured quite an aggressive _y_<sup>_∗_</sup> (typically less than the best observed loss), the TPE algorithm depends on a _y_<sup>_∗_</sup> that is larger than the best observed _f_ ( _x_ ) so that some points can be used to form _ℓ_ ( _x_ ). The TPE algorithm chooses _y_<sup>_∗_</sup> to be some quantile _γ_ of the observed _y_ values, so that _p_ ( _y < y_<sup>_∗_</sup> ) = _γ_ , but no specific model for _p_ ( _y_ ) is necessary. By maintaining sorted lists of observed variables in _H_ , the runtime of each iteration of the TPE algorithm can scale linearly in _|H|_ and linearly in the number of variables (dimensions) being optimized. 

### **4.1 Optimizing EI in the TPE algorithm** 

The parametrization of _p_ ( _x, y_ ) as _p_ ( _y_ ) _p_ ( _x|y_ ) in the TPE algorithm was chosen to facilitate the optimization of EI. 



### **4.2 Details of the Parzen Estimator** 

The models _ℓ_ ( _x_ ) and _g_ ( _x_ ) are hierarchical processes involving discrete-valued and continuousvalued variables. The Adaptive Parzen Estimator yields a model over _X_ by placing density in the vicinity of _K_ observations _B_ = _{x_<sup>(1)</sup> _, ..., x_<sup>(</sup><sup>_K_)</sup> _} ⊂H_ . Each continuous hyper-parameter was specified by a uniform prior over some interval ( _a, b_ ), or a Gaussian, or a log-uniform distribution. The TPE substitutes an equally-weighted mixture of that prior with Gaussians centered at each of the _x_<sup>(</sup><sup>_i_)</sup> _∈B_ . The standard deviation of each Gaussian was set to the greater of the distances to the left and right neighbor, but clipped to remain in a reasonable range. In the case of the uniform, the points _a_ and _b_ were considered to be potential neighbors. For discrete variables, supposing the prior was a vector of _N_ probabilities _pi_ , the posterior vector elements were proportional to _Npi_ + _Ci_ where _Ci_ counts the occurrences of choice _i_ in _B_ . The log-uniform hyper-parameters were treated as uniforms in the log domain. 

4 

Table 1: Distribution over DBN hyper-parameters for random sampling. Options separated by “or” such as pre-processing (and including the random seed) are weighted equally. Symbol _U_ means uniform, _N_ means Gaussian-distributed, and log _U_ means uniformly distributed in the log-domain. CD (also known as CD-1) stands for contrastive divergence, the algorithm used to initialize the layer parameters of the DBN. 

|**Whol**<br>Parameter|**e model**<br>Prior|**P**<br>Parameter|**er-layer**<br>Prior|
|---|---|---|---|
|pre-processing|raw or ZCA|n. hidden units|log_U_(128_,_4096)|
|ZCA energy|_U_(_._5_,_1)|_W_ init|_U_(_−a, a_)or_N_(0_, a_<sup>2</sup>)|
|random seed|5 choices|_a_|algo A or B (see text)|
|classifier learn rate|log_U_(0_._001_,_10)|algo A coef|_U_(_._2_,_2)|
|classifier anneal start|log_U_(100_,_10<sup>4</sup>)|CD epochs|log_U_(1_,_10<sup>4</sup>)|
|classifier_ℓ_2-penalty|0 orlog_U_(10<sup>_−_7</sup>_,_10<sup>_−_4</sup>)|CD learn rate|log_U_(10<sup>_−_4</sup>_,_1)|
|n. layers|1 to 3|CD anneal start|log_U_(10_,_10<sup>4</sup>)|
|batch size|20 or 100|CD sample data|yes or no|



## **5 Random Search for Hyper-Parameter Optimization in DBNs** 

One simple, but recent step toward formalizing hyper-parameter optimization is the use of random search [5]. [19] showed that random search was much more efficient than grid search for optimizing the parameters of one-layer neural network classifiers. In this section, we evaluate random search for DBN optimization, compared with the sequential grid-assisted manual search carried out in [1]. 

We chose the prior listed in Table 1 to define the search space over DBN configurations. The details of the datasets, the DBN model, and the greedy layer-wise training procedure based on CD are provided in [1]. This prior corresponds to the search space of [1] except for the following differences: (a) we allowed for ZCA pre-processing [20], (b) we allowed for each layer to have a different size, (c) we allowed for each layer to have its own training parameters for CD, (d) we allowed for the possibility of treating the continuous-valued data as either as Bernoulli means (more theoretically correct) or Bernoulli samples (more typical) in the CD algorithm, and (e) we did not discretize the possible values of real-valued hyper-parameters. These changes expand the hyper-parameter search problem, while maintaining the original hyper-parameter search space as a subset of the expanded search space. 

The results of this preliminary random search are in Figure 2. Perhaps surprisingly, the result of manual search can be reliably matched with 32 random trials for several datasets. The efficiency of random search in this setting is explored further in [21]. Where random search results match human performance, it is not clear from Figure 2 whether the reason is that it searched the original space as efficiently, or that it searched a larger space where good performance is easier to find. But the objection that random search is somehow cheating by searching a larger space is backward – the search space outlined in Table 1 is a natural description of the hyper-parameter optimization problem, and the restrictions to that space by [1] were presumably made to simplify the search problem and make it tractable for grid-search assisted manual search. Critically, both methods train DBNs on the same datasets. 

The results in Figure 2 indicate that hyper-parameter optimization is harder for some datasets. For example, in the case of the “MNIST rotated background images” dataset ( **MRBI** ), random sampling appears to converge to a maximum relatively quickly (best models among experiments of 32 trials show little variance in performance), but this plateau is lower than what was found by manual search. In another dataset ( **convex** ), the random sampling procedure exceeds the performance of manual search, but is slow to converge to any sort of plateau. There is considerable variance in generalization when the best of 32 models is selected. This slow convergence indicates that better performance is probably available, but we need to search the configuration space more efficiently to find it. The remainder of this paper explores sequential optimization strategies for hyper-parameter optimization for these two datasets: **convex** and **MRBI** . 

## **6 Sequential Search for Hyper-Parameter Optimization in DBNs** 

We validated our GP approach of Section 3.1 by comparing with random sampling on the Boston Housing dataset, a regression task with 506 points made of 13 scaled input variables and a scalar 

5 



<!-- Start of picture text -->
1 . 0 mnist basic 0 . 9 mnist background images 0 mnist . 6 rotated background images<br>0 . 8<br>0 . 8 0 . 7 0 . 5<br>0 . 6 0 . 4<br>0 . 6<br>0 . 5<br>0 . 3<br>0 . 4<br>0 . 4<br>0 . 3 0 . 2<br>0 . 2 0 . 2 0 . 1<br>0 . 1<br>0 . 0 1 2 4 8 16 32 64 128 0 . 0 1 2 4 8 16 32 64 128 0 . 0 1 2 4 8 16 32 64 128<br>experiment size (# trials) experiment size (# trials) experiment size (# trials)<br>0 . 85 convex 1 . 0 rectangles 0 . 80 rectangles images<br>0 . 80 0 . 9 0 . 75<br>0 . 75 0 . 70<br>0 . 8<br>0 . 70<br>0 . 65<br>0 . 65 0 . 7<br>0 . 60<br>0 . 60<br>0 . 6<br>0 . 55 0 . 55<br>0 . 50 0 . 5 0 . 50<br>0 . 45 1 2 4 8 16 32 64 128 0 . 4 1 2 4 8 16 32 64 128 0 . 45 1 2 4 8 16 32 64 128<br>experiment size (# trials) experiment size (# trials) experiment size (# trials)<br>accuracy accuracy accuracy<br>accuracy accuracy accuracy<br><!-- End of picture text -->

Figure 2: Deep Belief Network (DBN) performance according to random search. Random search is used to explore up to 32 hyper-parameters (see Table 1). Results found using a grid-search-assisted manual search over a similar domain with an average 41 trials are given in green (1-layer DBN) and red (3-layer DBN). Each box-plot (for _N_ = 1 _,_ 2 _,_ 4 _, ..._ ) shows the distribution of test set performance when the best model among _N_ random trials is selected. The datasets “convex” and “mnist rotated background images” are used for more thorough hyper-parameter optimization. 

regressed output. We trained a Multi-Layer Perceptron (MLP) with 10 hyper-parameters, including learning rate, _ℓ_ 1 and _ℓ_ 2 penalties, size of hidden layer, number of iterations, whether a PCA preprocessing was to be applied, whose energy was the only conditional hyper-parameter [22]. Our results are depicted in Figure 3. The first 30 iterations were made using random sampling, while from the 30<sup>th</sup> on, we differentiated the random samples from the GP approach trained on the updated history. The experiment was repeated 20 times. Although the number of points is particularly small compared to the dimensionality, the surrogate modelling approach finds noticeably better points than random, which supports the application of SMBO approaches to more ambitious tasks and datasets. 

Applying the GP to the problem of optimizing DBN performance, we allowed 3 random restarts to the CMA+ES algorithm per proposal _x_<sup>_∗_</sup> , and up to 500 iterations of conjugate gradient method in fitting the length scales of the GP. The squared exponential kernel [14] was used for every node. The CMA-ES part of GPs dealt with boundaries using a penalty method, the binomial sampling part dealt with it by nature. The GP algorithm was initialized with 30 randomly sampled points in _H_ . After 200 trials, the prediction of a point _x_<sup>_∗_</sup> using this GP took around 150 seconds. 

For the TPE-based algorithm, we chose _γ_ = 0 _._ 15 and picked the best among 100 candidates drawn from _ℓ_ ( _x_ ) on each iteration as the proposal _x_<sup>_∗_</sup> . After 200 trials, the prediction of a point _x_<sup>_∗_</sup> using this TPE algorithm took around 10 seconds. TPE was allowed to grow past the initial bounds used with for random sampling in the course of optimization, whereas the GP and random search were restricted to stay within the initial bounds throughout the course of optimization. The TPE algorithm was also initialized with the same 30 randomly sampled points as were used to seed the GP. 

### **6.1 Parallelizing Sequential Search** 

Both the GP and TPE approaches were actually run asynchronously in order to make use of multiple compute nodes and to avoid wasting time waiting for trial evaluations to complete. For the GP approach, the so-called _constant liar_ approach was used: each time a candidate point _x_<sup>_∗_</sup> was proposed, a fake fitness evaluation equal to the mean of the _y_ ’s within the training set _D_ was assigned temporarily, until the evaluation completed and reported the actual loss _f_ ( _x_<sup>_∗_</sup> ). For the TPE approach, we simply ignored recently proposed points and relied on the stochasticity of draws from _ℓ_ ( _x_ ) to provide different candidates from one iteration to the next. The consequence of parallelization is that each proposal _x_<sup>_∗_</sup> is based on less feedback. This makes search less efficient, though faster in terms of wall time. 

6 



<!-- Start of picture text -->
26<br>24<br>22<br>20<br>18<br>16<br>14<br>0 10 20 30 40 50<br>Time<br>Best value so far<br><!-- End of picture text -->

Figure 3: After time 30, GP optimizing the MLP hyper-parameters on the Boston Housing regression task. Best minimum found so far every 5 iterations, against time. Red = GP, Blue = Random. Shaded areas = one-sigma error bars. 

||**convex**|**MRBI**|
|---|---|---|
|TPE|**14.13**_±_0_._30%|**44.55**_±_0_._44%|
|GP|16_._70_±_0_._32%|47_._08_±_0_._44%|
|Manual|18_._63_±_0_._34%|47_._39_±_0_._44%|
|Random|18_._97_±_0_._34%|50_._52_±_0_._44%|



Table 2: The test set classification error of the best model found by each search algorithm on each problem. Each search algorithm was allowed up to 200 trials. The manual searches used 82 trials for **convex** and 27 trials **MRBI** . 

Runtime per trial was limited to 1 hour of GPU computation regardless of whether execution was on a GTX 285, 470, 480, or 580. The difference in speed between the slowest and fastest machine was roughly two-fold in theory, but the actual efficiency of computation depended also on the load of the machine and the configuration of the problem (the relative speed of the different cards is different in different hyper-parameter configurations). With the parallel evaluation of up to five proposals from the GP and TPE algorithms, each experiment took about 24 hours of wall time using five GPUs. 

## **7 Discussion** 

The trajectories ( _H_ ) constructed by each algorithm up to 200 steps are illustrated in Figure 4, and compared with random search and the manual search carried out in [1]. The generalization scores of the best models found using these algorithms and others are listed in Table 2. On the **convex** dataset (2-way classification), both algorithms converged to a validation score of 13% error. In generalization, TPE’s best model had 14.1% error and GP’s best had 16.7%. TPE’s best was significantly better than both manual search (19%) and random search with 200 trials (17%). On the **MRBI** dataset (10-way classification), random search was the worst performer (50% error), the GP approach and manual search approximately tied (47% error), while the TPE algorithm found a new best result (44% error). The models found by the TPE algorithm in particular are better than previously found ones on both datasets. The GP and TPE algorithms were slightly less efficient than manual search: GP and EI identified performance on par with manual search within 80 trials, the manual search of [1] used 82 trials for **convex** and 27 trials for **MRBI** . 

There are several possible reasons for why the TPE approach outperformed the GP approach in these two datasets. Perhaps the inverse factorization of _p_ ( _x|y_ ) is more accurate than the _p_ ( _y|x_ ) in the Gaussian process. Perhaps, conversely, the exploration induced by the TPE’s lack of accuracy turned out to be a good heuristic for search. Perhaps the hyper-parameters of the GP approach itself were not set to correctly trade off exploitation and exploration in the DBN configuration space. More empirical work is required to test these hypotheses. Critically though, all four SMBO runs matched or exceeded both random search and a careful human-guided search, which are currently the state of the art methods for hyper-parameter optimization. 

The GP and TPE algorithms work well in both of these settings, but there are certainly settings in which these algorithms, and in fact SMBO algorithm in general, would not be expected to do well. Sequential optimization algorithms work by leveraging structure in observed ( _x, y_ ) pairs. It is possible for SMBO to be arbitrarily bad with a bad choice of _p_ ( _y|x_ ). It is also possible to be slower than random sampling at finding a global optimum with a apparently good _p_ ( _y|x_ ), if it extracts structure in _H_ that leads only to a local optimum. 

## **8 Conclusion** 

This paper has introduced two sequential hyper-parameter optimization algorithms, and shown them to meet or exceed human performance and the performance of a brute-force random search in two difficult hyper-parameter optimization tasks involving DBNs. We have relaxed standard constraints (e.g. equal layer sizes at all layers) on the search space, and fall back on a more natural hyperparameter space of 32 variables (including both discrete and continuous variables) in which many 

7 



<!-- Start of picture text -->
Dataset: convex Dataset: mnist rotated background images<br>0 . 50 manual 0 . 9 manual<br>99.5’th q. 99.5’th q.<br>0 . 45 GP GP<br>TPE 0 . 8 TPE<br>0 . 40<br>0 . 35 0 . 7<br>0 . 30<br>0 . 6<br>0 . 25<br>0 . 20 0 . 5<br>0 . 15<br>0 50 100 150 200 0 50 100 150 200<br>time(trials) time(trials)<br>error (fraction incorrect) error (fraction incorrect)<br><!-- End of picture text -->

Figure 4: Efficiency of Gaussian Process-based (GP) and graphical model-based (TPE) sequential optimization algorithms on the task of optimizing the validation set performance of a DBN of up to three layers on the **convex** task (left) and the **MRBI** task (right). The dots are the elements of the trajectory _H_ produced by each SMBO algorithm. The solid coloured lines are the validation set accuracy of the best trial found before each point in time. Both the TPE and GP algorithms make significant advances from their random initial conditions, and substantially outperform the manual and random search methods. A 95% confidence interval about the best validation means on the **convex** task extends 0.018 above and below each point, and on the **MRBI** task extends 0.021 above and below each point. The solid black line is the test set accuracy obtained by domain experts using a combination of grid search and manual search [1]. The dashed line is the 99.5% quantile of validation performance found among trials sampled from our prior distribution (see Table 1), estimated from 457 and 361 random trials on the two datasets respectively. 

variables are sometimes irrelevant, depending on the value of other parameters (e.g. the number of layers). In this 32-dimensional search problem, the TPE algorithm presented here has uncovered new best results on both of these datasets that are significantly better than what DBNs were previously believed to achieve. Moreover, the GP and TPE algorithms are practical: the optimization for each dataset was done in just 24 hours using five GPU processors. Although our results are only for DBNs, our methods are quite general, and extend naturally to any hyper-parameter optimization problem in which the hyper-parameters are drawn from a measurable set. 

We hope that our work may spur researchers in the machine learning community to treat the hyperparameter optimization strategy as an interesting and important component of all learning algorithms. The question of “How well does a DBN do on the **convex** task?” is not a fully specified, empirically answerable question – different approaches to hyper-parameter optimization will give different answers. Algorithmic approaches to hyper-parameter optimization make machine learning results easier to disseminate, reproduce, and transfer to other domains. The specific algorithms we have presented here are also capable, at least in some cases, of finding better results than were previously known. Finally, powerful hyper-parameter optimization algorithms broaden the horizon of models that can realistically be studied; researchers need not restrict themselves to systems of a few variables that can readily be tuned by hand. 

The TPE algorithm presented in this work, as well as parallel evaluation infrastructure, is available as BSD-licensed free open-source software, which has been designed not only to reproduce the results in this work, but also to facilitate the application of these and similar algorithms to other hyper-parameter optimization problems.<sup>1</sup> 

### **Acknowledgements** 

This work was supported by the National Science and Engineering Research Council of Canada, Compute Canada, and by the ANR-2010-COSI-002 grant of the French National Research Agency. GPU implementations of the DBN model were provided by Theano [23]. 

> 1“Hyperopt” software package: https://github.com/jaberg/hyperopt 

8 

## **References** 

- [1] H. Larochelle, D. Erhan, A. Courville, J. Bergstra, and Y. Bengio. An empirical evaluation of deep architectures on problems with many factors of variation. In _ICML 2007_ , pages 473–480, 2007. 

- [2] G. E. Hinton, S. Osindero, and Y. Teh. A fast learning algorithm for deep belief nets. _Neural Computation_ , 18:1527–1554, 2006. 

- [3] P. Vincent, H. Larochelle, I. Lajoie, Y. Bengio, and P. A. Manzagol. Stacked denoising autoencoders: Learning useful representations in a deep network with a local denoising criterion. _Machine Learning Research_ , 11:3371–3408, 2010. 

- [4] Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner. Gradient-based learning applied to document recognition. _Proceedings of the IEEE_ , 86(11):2278–2324, November 1998. 

- [5] Nicolas Pinto, David Doukhan, James J. DiCarlo, and David D. Cox. A high-throughput screening approach to discovering good forms of biologically inspired visual representation. _PLoS Comput Biol_ , 5(11):e1000579, 11 2009. 

- [6] A. Coates, H. Lee, and A. Ng. An analysis of single-layer networks in unsupervised feature learning. NIPS Deep Learning and Unsupervised Feature Learning Workshop, 2010. 

- [7] A. Coates and A. Y. Ng. The importance of encoding versus training with sparse coding and vector quantization. In _Proceedings of the Twenty-eighth International Conference on Machine Learning (ICML11)_ , 2010. 

- [8] F. Hutter. _Automated Configuration of Algorithms for Solving Hard Computational Problems_ . PhD thesis, University of British Columbia, 2009. 

- [9] F. Hutter, H. Hoos, and K. Leyton-Brown. Sequential model-based optimization for general algorithm configuration. In _LION-5_ , 2011. Extended version as UBC Tech report TR-2010-10. 

- [10] D.R. Jones. A taxonomy of global optimization methods based on response surfaces. _Journal of Global Optimization_ , 21:345–383, 2001. 

- [11] J. Villemonteix, E. Vazquez, and E. Walter. An informational approach to the global optimization of expensive-to-evaluate functions. _Journal of Global Optimization_ , 2006. 

- [12] N. Srinivas, A. Krause, S. Kakade, and M. Seeger. Gaussian process optimization in the bandit setting: No regret and experimental design. In _ICML_ , 2010. 

- [13] J. Mockus, V. Tiesis, and A. Zilinskas. The application of Bayesian methods for seeking the extremum. In L.C.W. Dixon and G.P. Szego, editors, _Towards Global Optimization_ , volume 2, pages 117–129. North Holland, New York, 1978. 

- [14] C.E. Rasmussen and C. Williams. _Gaussian Processes for Machine Learning_ . 

- [15] D. Ginsbourger, D. Dupuy, A. Badea, L. Carraro, and O. Roustant. A note on the choice and the estimation of kriging models for the analysis of deterministic computer experiments. 25:115–131, 2009. 

- [16] R. Bardenet and B. K´egl. Surrogating the surrogate: accelerating Gaussian Process optimization with mixtures. In _ICML_ , 2010. 

- [17] P. Larra˜naga and J. Lozano, editors. _Estimation of Distribution Algorithms: A New Tool for Evolutionary Computation_ . Springer, 2001. 

- [18] N. Hansen. The CMA evolution strategy: a comparing review. In J.A. Lozano, P. Larranaga, I. Inza, and E. Bengoetxea, editors, _Towards a new evolutionary computation. Advances on estimation of distribution algorithms_ , pages 75–102. Springer, 2006. 

- [19] J. Bergstra and Y. Bengio. Random search for hyper-parameter optimization. The Learning Workshop (Snowbird), 2011. 

- [20] A. Hyv¨arinen and E. Oja. Independent component analysis: Algorithms and applications. _Neural Networks_ , 13(4–5):411–430, 2000. 

- [21] J. Bergstra and Y. Bengio. Random search for hyper-parameter optimization. JMLR, 2012. Accepted. 

- [22] C. Bishop. Neural networks for pattern recognition. 1995. 

- [23] J. Bergstra, O. Breuleux, F. Bastien, P. Lamblin, R. Pascanu, G. Desjardins, J. Turian, and Y. Bengio. Theano: a CPU and GPU math expression compiler. In _Proceedings of the Python for Scientific Computing Conference (SciPy)_ , June 2010. 

9 

