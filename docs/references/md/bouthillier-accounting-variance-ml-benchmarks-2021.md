---
# --- bibliographic record ---
entry_type: misc
title: "Accounting for Variance in Machine Learning Benchmarks"
authors:
  - "Xavier Bouthillier"
  - "Pierre Delaunay"
  - "Mirko Bronzi"
  - "Assya Trofimov"
  - "Brennan Nichyporuk"
  - "Justin Szeto"
  - "Naz Sepah"
  - "Edward Raff"
  - "Kanika Madan"
  - "Vikram Voleti"
  - "Samira Ebrahimi Kahou"
  - "Vincent Michalski"
  - "Dmitriy Serdyuk"
  - "Tal Arbel"
  - "Chris Pal"
  - "Gaël Varoquaux"
  - "Pascal Vincent"
year: 2021
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2103.03098"
url: "https://arxiv.org/abs/2103.03098"

# --- archive record ---
source_pdf: bouthillier-accounting-variance-ml-benchmarks-2021.pdf
source_sha256: 1f458f7e606e4db86b207315c049a38b52cacde15ad34def2cc6c29124fc5d4c
pdf_pages: 23
converted: 2026-09-13
record_source: arxiv
key_insight: "Decomposes benchmark variance into its sources (seed, data order, hardware) and shows single-run comparisons routinely invert. Grounds reporting per-seed dispersion and the paired permutation test instead of a single-seed ranking."
first_page: "ACCOUNTING FOR VARIANCE IN MACHINE LEARNING BENCHMARKS Xavier Bouthillier 1 2 Pierre Delaunay 3 Mirko Bronzi 1 Assya Troﬁmov 1 2 4 Brennan Nichyporuk 1 5 6 Justin Szeto 1 5 6 Naz Sepah 1 5 6 Edward Ra"
---
**ACCOUNTING FOR VARIANCE IN MACHINE LEARNING BENCHMARKS** 

**Xavier Bouthillier**<sup>1 2</sup> **Pierre Delaunay**<sup>3</sup> **Mirko Bronzi**<sup>1</sup> **Assya Trofimov**<sup>1 2 4</sup> **Brennan Nichyporuk**<sup>1 5 6</sup> **Justin Szeto**<sup>1 5 6</sup> **Naz Sepah**<sup>1 5 6</sup> **Edward Raff**<sup>7 8</sup> **Kanika Madan**<sup>1 2</sup> **Vikram Voleti**<sup>1 2</sup> **Samira Ebrahimi Kahou**<sup>1 6 9 10</sup> **Vincent Michalski**<sup>1 2</sup> **Dmitriy Serdyuk**<sup>1 2</sup> **Tal Arbel**<sup>1 5 6 10</sup> **Chris Pal**<sup>1 11 12</sup> **Ga¨el Varoquaux**<sup>1 6 13</sup> **Pascal Vincent**<sup>1 2 10</sup> 

# **ABSTRACT** 

Strong empirical evidence that one machine-learning algorithm _A_ outperforms another one _B_ ideally calls for multiple trials optimizing the learning pipeline over sources of variation such as data sampling, augmentation, parameter initialization, and hyperparameters choices. This is prohibitively expensive, and corners are cut to reach conclusions. We model the whole benchmarking process, revealing that variance due to data sampling, parameter initialization and hyperparameter choice impact markedly the results. We analyze the predominant comparison methods used today in the light of this variance. We show a counter-intuitive result that adding more sources of variation to an imperfect estimator approaches better the ideal estimator at a 51 _×_ reduction in compute cost. Building on these results, we study the error rate of detecting improvements, on five different deep-learning tasks/architectures. This study leads us to propose recommendations for performance comparisons. 

# **1 INTRODUCTION: TRUSTWORTHY BENCHMARKS ACCOUNT FOR FLUCTUATIONS** 

Machine learning increasingly relies upon empirical evidence to validate publications or efficacy. The value of a new method or algorithm _A_ is often established by empirical benchmarks comparing it to prior work. Although such benchmarks are built on quantitative measures of performance, uncontrolled factors can impact these measures and dominate the meaningful difference between the methods. In particular, recent studies have shown that loose choices of hyper-parameters lead to non-reproducible benchmarks and unfair comparisons (Raff, 2019; 2021; Lucic et al., 2018; Henderson et al., 2018; Kadlec et al., 2017; Melis et al., 2018; Bouthillier et al., 2019; Reimers & Gurevych, 2017; Gorman & Bedrick, 2019). Properly accounting for these factors may go as far as changing the conclusions for the comparison, as shown for recommender systems (Dacrema et al., 2019), neural architecture pruning (Blalock et al., 2020), and metric learning (Musgrave et al., 2020). 

1Mila, Montreal, Canada´ 2Universite de Montr´ eal, Montr´ eal,´ Canada<sup>3</sup> Independent<sup>4</sup> IRIC<sup>5</sup> Centre for Intelligent Machines 6McGill University, Montreal,´ Canada 7Booz Allen Hamilton 8University of Maryland, Baltimore County 9 ´Ecole de technologie superieure´<sup>10</sup> CIFAR<sup>11</sup> Polytechnique Montreal, Montr´ eal, Canada´ 12ElementAI 13Inria, Saclay, France. Correspondence to: Xavier Bouthillier _<_ xavier.bouthillier@umontreal.ca _>_ . 

_Proceedings of the 3_<sup>_rd_</sup> _MLSys Conference_ , Austin, TX, USA, 2020. Copyright 2020 by the author(s). 

The steady increase in complexity –e.g. neural-network depth– and number of hyper-parameters of learning pipelines increases computational costs of models, making brute-force approaches prohibitive. Indeed, robust conclusions on comparative performance of models _A_ and _B_ would require multiple training of the full learning pipelines, including hyper-parameter optimization and random seeding. Unfortunately, since the computational budget of most researchers can afford only a small number of model fits (Bouthillier & Varoquaux, 2020), many sources of variances are not probed via repeated experiments. Rather, sampling several model initializations is often considered to give enough evidence. As we will show, there are other, larger, sources of uncontrolled variation and the risk is that conclusions are driven by differences due to arbitrary factors, such as data order, rather than model improvements. 

The seminal work of Dietterich (1998) studied statistical tests for comparison of supervised classification learning algorithms focusing on variance due to data sampling. Following works (Nadeau & Bengio, 2000; Bouckaert & Frank, 2004) perpetuated this focus, including a series of work in NLP (Riezler & Maxwell, 2005; Taylor Berg-Kirkpatrick & Klein, 2012; Anders Sogaard & Alonso, 2014) which ignored variance extrinsic to data sampling. Most of these works recommended the use of paired tests to mitigate the issue of extrinsic sources of variation, but Hothorn et al. (2005) then proposed a theoretical framework encompassing all sources of variation. This framework addressed the issue of extrinsic sources of variation by marginalizing all of them, including the hyper-parameter optimization pro- 

**Accounting for Variance in Machine Learning Benchmarks** 

cess. These prior works need to be confronted to the current practice in machine learning, in particular deep learning, where _1)_ the machine-learning pipelines has a large number of hyper-parameters, including to define the architecture, set by uncontrolled procedures, sometimes manually, _2)_ the cost of fitting a model is so high that train/validation/test splits are used instead of cross-validation, or nested crossvalidation that encompasses hyper-parameter optimization (Bouthillier & Varoquaux, 2020). 

In **Section 2** , we study the different source of variation of a benchmark, to outline which factors contribute markedly to uncontrolled fluctuations in the measured performance. **Section 3** discusses estimation the performance of a pipeline and its uncontrolled variations with a limited budget. In particular we discuss this estimation when hyper-parameter optimization is run only once. Recent studies emphasized that model comparisons with uncontrolled hyper-parameter optimization is a burning issue (Lucic et al., 2018; Henderson et al., 2018; Kadlec et al., 2017; Melis et al., 2018; Bouthillier et al., 2019); here we frame it in a statistical context, with explicit bias and variance to measure the loss of reliability that it incurs. In **Section 4** , we discuss criterion using these estimates to conclude on whether to accept algorithm _A_ as a meaningful improvement over algorithm _B_ , and the error rates that they incur in the face of noise. 

Based on our results, we issue in **Section 5** the following recommendations: 

- **1)** As many sources of variation as possible should be randomized whenever possible. These include weight initialization, data sampling, random data augmentation and the whole hyperparameter optimization. This helps decreasing the standard error of the average performance estimation, enhancing precision of benchmarks. 

- **2)** Deciding of whether the benchmarks give evidence that one algorithm outperforms another should not build solely on comparing average performance but account for variance. We propose a simple decision criterion based on requiring a high-enough probability that in one run an algorithm outperforms another. 

- **3)** Resampling techniques such as out-of-bootstrap should be favored instead of fixed held-out test sets to improve capacity of detecting small improvements. 

Before concluding, we outline a few additional considerations for benchmarking in **Section 6** . 

# **2 THE VARIANCE IN ML BENCHMARKS** 

Machine-learning benchmarks run a complete learning pipeline on a finite dataset to estimate its performance. This performance value should be considered the realization of a random variable. Indeed the dataset is itself a random sample from the full data distribution. In addition, a typical 

learning pipeline has additional sources of uncontrolled fluctuations, as we will highlight below. A proper evaluation and comparison between pipelines should thus account for the _distributions_ of such metrics. 

## **2.1 A model of the benchmarking process that includes hyperparameter tuning** 

Here we extend the formalism of Hothorn et al. (2005) to model the different sources of variation in a machinelearning pipeline and that impact performance measures. In particular, we go beyond prior works by accounting for the choice of hyperparameters in a probabilistic model of the whole experimental benchmark. Indeed, choosing good hyperparameters –including details of a neural architecture– is crucial to the performance of a pipeline. Yet these hyperparameters come with uncontrolled noise, whether they are set manually or with an automated procedure. 

**The training procedure** We consider here the familiar setting of supervised learning on i.i.d. data (and will use classification in our experiments) but this can easily be adapted to other machine learning settings. Suppose we have access to a dataset _S_ = _{_ ( _x_ 1 _, y_ 1) _, . . . ,_ ( _xn, yn_ ) _}_ containing _n_ examples of (input, target) pairs. These pairs are i.i.d. and sampled from an unknown data distribution _D_ , i.e. _S ∼D_<sup>_n_</sup> . The goal of a learning pipeline is to find a function _h ∈H_ that will have good prediction performance in expectation over _D_ , as evaluated by a metric of interest _e_ . More precisely, in supervised learning, _e_ ( _h_ ( _x_ ) _, y_ ) is a measure of how far a prediction _h_ ( _x_ ) lies from the target _y_ associated to the input _x_ (e.g., classification error). The goal is to find a predictor _h_ that minimizes the _expected risk Re_ ( _h, D_ ) = E( _x,y_ ) _∼D_ [ _e_ ( _h_ ( _x_ ) _, y_ )], but since we have access only to finite datasets, all we can ever measure is an _empirical risk R_<sup>ˆ</sup> _e_ ( _h, S_ ) = _|S_ <u>1</u> _|_ �( _x,y_ ) _∈S_<sup>_e_(</sup><sup>_h_(</sup><sup>_x_)</sup><sup>_, y_).In</sup> practice training with a training set _S_<sup>_t_</sup> consists in finding a function (hypothesis) _h ∈H_ that minimizes a trade-off between a data-fit term –typically the empirical risk of a differentiable surrogate loss _e_<sup>_′_</sup> – with a regularization Ω( _h, λ_ ) that induces a preference over hypothesis functions: 



where _λ_ represents the set of hyperparameters: regularization coefficients (s.a. strength of weight decay or the ridge penalty), architectural hyperparameters affecting _H_ , optimizer-specific ones such as the learning rate, etc. . . Note that Opt is a random variable whose value will depend also on other additional random variables that we shall collectively denote _ξO_ , sampled to determine parameter initialization, data augmentation, example ordering, etc.<sup>*</sup> . 

> *If stochastic data augmentation is used, then optimization procedure Opt for a given training set _S_<sup>_t_</sup> has to be changed to an 

**Accounting for Variance in Machine Learning Benchmarks** 

**Hyperparameter Optimization** The training procedure builds a predictor given a training set _S_<sup>_t_</sup> . But since it requires specifying hyperparameters _λ_ , a complete learning pipeline has to tune all of these. A complete pipeline will involve a hyper-parameter optimization procedure, which will strive to find a value of _λ_ that minimizes objective 



where sp( _S_<sup>_tv_</sup> ) is a distribution of random splits of the data set _S_<sup>_tv_</sup> between training and validation subsets _S_<sup>_t_</sup> _, S_<sup>_v_</sup> . Ideally, hyperparameter optimization would be applied over random dataset samples from the true distribution _D_ , but in practice the learning pipeline only has access to _S_<sup>_tv_</sup> , hence the expectation over dataset splits. An ideal hyper-parameter optimization would yield _λ_<sup>_∗_</sup> ( _S_<sup>_tv_</sup> ) = arg min _λ r_ ( _λ_ ). A concrete hyperparameter optimization algorithm HOpt will however use an average over a small number of trainvalidation splits (or just 1), and a limited training budget, � yielding _λ_<sup>_∗_</sup> ( _S_<sup>_tv_</sup> ) = HOpt( _S_<sup>_tv_</sup> ) _≈ λ_<sup>_∗_</sup> ( _S_<sup>_tv_</sup> ). We denoted earlier the sources of random variations in Opt as _ξO_ . Likewise, we will denote the sources of variation inherent to HOpt as _ξH_ . These encompass the sources of variance related to the procedure to optimize hyperparameters HOpt, whether it is manual or a search procedure which has its arbitrary choices such as the splitting and random exploration. 

After hyperparameters have been tuned, it is often customary to retrain the predictor using the full data _S_<sup>_tv_</sup> . The complete learning pipeline _P_ will finally return a single predictor: 



� Recall that _h_<sup>_∗_</sup> ( _S_<sup>_tv_</sup> ) is the result of Opt which is not deterministic, as it is affected by arbitrary choices _ξO_ in the training of the model (random weight initialization, data ordering...) and now additionally _ξH_ in the hyperparameter optimization. We will use _ξ_ to denote the set of all random variations sources in the learning pipeline, _ξ_ = _ξH ∪ ξO_ . Thus _ξ_ captures all sources of variation in the learning pipeline from data _S_<sup>_tv_</sup> , that are not configurable with _λ_ . 

**The performance measure** The full learning procedure � _P_ described above yields a model _h_<sup>_∗_</sup> . We now must define a metric that we can use to evaluate the performance of this model with statistical tests. For simplicity, we will use the same evaluation metric _e_ on which we based hyperparameter optimization. The expected risk obtained by applying the full learning pipeline _P_ to datasets _S_<sup>_tv_</sup> _∼D_<sup>_n_</sup> of size _n_ is: 



expectation over _S_<sup>˜</sup><sup>_t_</sup> _∼ P_<sup>aug</sup> ( _S_<sup>˜</sup><sup>_t_</sup> _|S_<sup>_t_</sup> ; _λ_ aug) where _P_<sup>aug</sup> is the data augmentation distribution. This adds additional stochasticity to the optimization, as we will optimize this through samples from _P_<sup>aug</sup> obtained with a random number generator. 

where the expectation is also over the random sources _ξ_ that affect the learning procedure (initialization, ordering, data-augmentation) and hyperparameter optimization. 

As we only have access to a single finite dataset _S_ , the performance of the learning pipeline can be evaluated as the following expectation over splits: 



where sp is a distribution of random splits or bootstrap resampling of the data set _S_ that yield sets _S_<sup>_tv_</sup> (train+valid) of sizeresponding variance of _n_ and _S_<sup>_o_</sup> (test) of size _R_<sup>ˆ</sup> _e_ (� _h_<sup>_∗_</sup> _n_ ( _S_<sup>_′tv_</sup> . We denote as) _, S_<sup>_o_</sup> ). The performance _σ_<sup>2</sup> the cormeasures vary not only depending on how the data was split, but also on all other random factors affecting the learning procedure ( _ξO_ ) and hyperparameters optimization ( _ξH_ ). 

## **2.2 Empirical evaluation of variance in benchmarks** 

We conducted thorough experiments to probe the different sources of variance in machine learning benchmarks. 

**Cases studied** We selected i) the CIFAR10 (Krizhevsky et al., 2009) image classification with VGG11 (Simonyan & Zisserman, 2014), ii) PascalVOC (Everingham et al.) image segmentation using an FCN (Long et al., 2014) with a ResNet18 (He et al., 2015a) backbone pretrained on imagenet (Deng et al., 2009), iii-iv) Glue (Wang et al., 2019) SST-2 (Socher et al., 2013) and RTE (Bentivogli et al., 2009) tasks with BERT (Devlin et al., 2018) and v) peptide to major histocompatibility class I (MHC I) binding predictions with a shallow MLP. All details on default hyperparameters used and the computational environments –which used _∼_ 8 GPU years– can be found in Appendix D. 

**Variance in the learning procedure:** _ξO_ For the sources of variance from the learning procedure ( _ξO_ ), we identified: i) the data sampling, ii) data augmentation procedures, iii) model initialization, iv) dropout, and v) data visit order in stochastic gradient descent. We model the data-sampling variance as resulting from training the model on a finite dataset _S_ of size _n_ , sampled from an unknown true distribution. _S ∼D_<sup>_n_</sup> is thus a random variable, the standard source of variance considered in statistical learning. Since we have a single finite dataset in practice, we evaluate this variance by repeatedly generating a train set from bootstrap replicates of the data and measuring the out-of-bootstrap error (Hothorn et al., 2005)<sup>†</sup> . 

We first fixed hyperparameters to pre-selected reasonable 

†The more common alternative in machine learning is to use cross-validation, but the latter is less amenable to various sample sizes. Bootstrapping is discussed in more detail in Appendix B. 

**Accounting for Variance in Machine Learning Benchmarks** 



<!-- Start of picture text -->
source of variation case studies<br>Glue-RTE Glue-SST2 MHC PascalVOC CIFAR10<br>BERT BERT MLP ResNet VGG11<br>hyperparameter<br>Bayes Opt<br>optimization Random Search<br>HOpt { H} Noisy Grid Search<br>Data (bootstrap)<br>learning Data augment<br>Data order<br>procedure<br>Weights init<br>{ O} Dropout<br>Numerical noise<br>0 2 0.0 0.5 0 2 0.0 0.5 1.0 0.0 0.2<br>STD<br><!-- End of picture text -->

_Figure 1._ **Different sources of variation of the measured performance** : across our different case studies, as a fraction of the variance induced by bootstrapping the data. For hyperparameter optimization, we studied several algorithms. 

choices<sup>‡</sup> . Then, iteratively for each sources of variance, we randomized the seeds 200 times, while keeping all other sources fixed to initial values. Moreover, we measured the numerical noise with 200 training runs with all fixed seeds. 

Figure 1 presents the individual variances due to sources from within the learning algorithms. Bootstrapping data stands out as the most important source of variance. In contrast, model initialization generally is less than 50% of the variance of bootstrap, on par with the visit order of stochastic gradient descent. Note that these different contributions to the variance are not independent, the total variance cannot be obtained by simply adding them up. 

For classification, a simple binomial can be used to model the sampling noise in the measure of the prediction accuracy of a trained pipeline on the test set. Indeed, if the pipeline has a chance _τ_ of giving the wrong answer on a sample, makes i.i.d. errors, and is measured on _n_ samples, the observed measure follows a binomial distribution of location parameter _τ_ with _n_ degrees of freedom. If errors are correlated, not i.i.d., the degrees of freedom are smaller and the distribution is wider. Figure 2 compares standard deviations of the performance measure given by this simple binomial model to those observed when bootstrapping the data on the three classification case studies. The match between the model and the empirical results suggest that the variance due to data sampling is well explained by the limited statistical power in the test set to estimate the true performance. 

**Variance induced by hyperparameter optimization:** _ξH_ 

To study the _ξH_ sources of variation, we chose three of the most popular hyperparameter optimization methods: i) random search, ii) grid search, and iii) Bayesian optimization. While grid-search in itself has no random parameters, the specific choice of the parameter range is arbitrary and can be an uncontrolled source of variance (e.g., does the grid 

‡This choice is detailed in Appendix D. 



<!-- Start of picture text -->
In Theory: In Practice:<br>From a Binomial Random splits<br>4 Glue-RTE BERT<br>Binom(n', 0.66)<br>(n'=277)<br>Binom(n', 0.95) Glue-SST2 BERT<br>3 Binom(n', 0.91) (n'=872)<br>CIFAR10 VGG11<br>2 (n'=10000)<br>1<br>0<br>102 103 104 105 106<br>Test set size<br>Standard deviation (% acc)<br><!-- End of picture text -->

_Figure 2._ **Error due to data sampling:** The dotted lines show the standard deviation given by a binomial-distribution model of the accuracy measure; the crosses report the standard deviation observed when bootstrapping the data in our case studies, showing that the model is a reasonable. 

size step by powers of 2, 10, or increments of 0.25 or 0.5). We study this variance with a _noisy grid search_ , perturbing slightly the parameter ranges (details in Appendix E). 

For each of these tuning methods, we held all _ξO_ fixed to random values and executed 20 independent hyperparameter optimization procedures up to a budget of 200 trials. This way, all the observed variance across the hyperparameter optimization procedures is strictly due to _ξH_ . We were careful to design the search space so that it covers the optimal hyperparameter values (as stated in original studies) while being large enough to cover suboptimal values as well. 

Results in figure 1 show that hyperparameter choice induces a sizable amount of variance, not negligible in comparison to the other factors. The full optimization curves of the 320 HPO procedures are presented in Appendix F. The three hyperparameter optimization methods induce on average as much variance as the commonly studied weights initializa- 

**Accounting for Variance in Machine Learning Benchmarks** 



<!-- Start of picture text -->
cifar10<br>100.0<br>97.5<br>95.0<br>92.5<br>90.0<br>sst2<br>100<br>non-'SOTA' results<br>95 Significant<br>Non-Significant<br>90<br>85<br>2012 2014 2016 2018 2020<br>Year<br>Accuracy<br><!-- End of picture text -->

_Figure 3._ **Published improvements compared to benchmark variance** The dots give the performance of publications, function of year, as reported on paperswithcode.com; red band shows our estimated _σ_ , and the yellow band the resulting significance threshold. Green marks are results likely significant compared to prior ’State of the Art’, and red ” _×_ ” appear non-significant. 

tion. These results motivate further investigation the cost of ignoring the variance due to hyperparameter optimization. 

**The bigger picture: Variance matters** For a given case study, the total variance due to arbitrary choices and sampling noise revealed by our study can be put in perspective with the published improvements in the state-of-the-art. Figure 3 shows that this variance is on the order of magnitude of the individual increments. In other words, the variance is not small compared to the differences between pipelines. It must be accounted for when benchmarking pipelines. 

# **3 ACCOUNTING FOR VARIANCE TO RELIABLY ESTIMATE PERFORMANCE** _R_<sup>ˆ</sup> _P_ 

This section contains 1) an explanation of the counter intuitive result that accounting for more sources of variation reduces the standard error for an estimator of _R_<sup>ˆ</sup> _P_ and 2) an empirical measure of the degradation of expected empirical risk estimation due to neglecting HOpt variance. 

We will now consider different _estimators_ of the average performance _µ_ = _R_<sup>ˆ</sup> _P_ ( _S, n, n_<sup>_′_</sup> ) from Equation 5. Such estimators will use, in place of the expectation of Equation 5, an empirical average over _k_ (train+test) splits, which we will denote _µ_ ˆ( _k_ ) and _σ_ ˆ(<sup>2</sup> _k_ )<sup>the corresponding empirical variance.</sup> We will make an important distinction between an estimator which encompasses all sources of variation, the _ideal estimator µ_ ˆ( _k_ ), and one which accounts only for a portion of these sources, the _biased estimator µ_ ˜( _k_ ). 

But before delving into this, we will explain why many splits help estimating the expected empirical risk ( _R_<sup>ˆ</sup> _P_ ). 

## **3.1 Multiple data splits for smaller detectable improvements** 

The majority of machine-learning benchmarks are built with fixed training and test sets. The rationale behind this design, is that learning algorithms should be compared on the same grounds, thus on the same sets of examples for training and testing. While the rationale is valid, it disregards the fact that the fundamental ground of comparison is the true distribution from which the sets were sampled. This finite set is used to compute the expected empirical risk ( _R_<sup>ˆ</sup> _P_ Eq 5), failing to compute the expected risk ( _RP_ Eq 4) on the whole distribution. This empirical risk is therefore a noisy measure, it has some uncertainty because the risk on a particular test set gives limited information on what would be the risk on new data. This uncertainty due to data sampling is not small compared to typical improvements or other sources of variation, as revealed by our study in the previous section. In particular, figure 2 suggests that the size of the test set can be a limiting factor. 

When comparing two learning algorithms _A_ and _B_ , we estimate their expected empirical risks _R_<sup>ˆ</sup> _P_ with _µ_ ˆ( _k_ ), a noisy measure. The uncertainty of this measure is represented by the standard error _~~√~~_ _<u>σk</u>_<sup>under the normal assumption§ of</sup> _R_ ˆ _e_ . This uncertainty is an important aspect of the comparison, for instance it appears in statistical tests used to draw a conclusion in the face of a noisy evidence. For instance, a z-test states that a difference of expected empirical risk 

between _A_ and _B_ of at least _z_ 0 _._ 05 ~~�~~ _σA_<sup>2+</sup> _k_<sup>_σ_</sup> _<u>B</u>_<sup>2</sup> must be observed to control false detections at a rate of 95%. In other words, a difference smaller than this value could be due to noise alone, e.g. different sets of random splits may lead to different conclusions. 

With _k_ = 1, algorithms _A_ and _B_ must have a large difference of performance to support a reliable detection. In order to detect smaller differences, _k_ must be increased, i.e. _µ_ ˆ( _k_ ) must be computed over several data splits. The estimator _µ_ ˆ( _k_ ) is computationally expensive however, and most researchers must instead use a biased estimator _µ_ ˜( _k_ ) that does not probe well all sources of variance. 

## **3.2 Bias and variance of estimators depends on whether they account for all sources of variation** 

Probing all sources of variation, including hyperparameter optimization, is too computationally expensive for most researchers. However, ignoring the role of hyperparameter optimization induces a bias in the estimation of the expected empirical risk. We discuss in this section the expensive, unbiased, ideal estimator of _µ_ ˆ( _k_ ) and the cheap biased es- 

> §Our extensive numerical experiments show that a normal distribution is well suited for the fluctuations of the risk–figure G.3 

**Accounting for Variance in Machine Learning Benchmarks** 

timator of _µ_ ˜( _k_ ). We explain as well why accounting for many sources of variation improves the biased estimator by reducing its bias. 

## _3.2.1 Ideal estimator: sampling multiple HOpt_ 

The ideal estimator _µ_ ˆ( _k_ ) takes into account all sources of variation. For each performance measure _R_<sup>ˆ</sup> _e_ , all _ξO_ and _ξH_ are randomized, each requiring an independent hyperparameter optimization procedure. The detailed procedure is presented in Algorithm 1. For an estimation over _k_ splits with hyperparameter optimization for a budget of _T_ trials, it requires fitting the learning algorithm a total of _O_ ( _k · T_ ) times. The estimator is unbiased, with E � _µ_ ˆ( _k_ )� = _µ_ . 

For a variance of the performance measures Var( _R_<sup>ˆ</sup> _e_ ) = _σ_<sup>2</sup> , we can derive the variance of the ideal estima= _<u>σ</u>_<sup>2</sup> tor Var(ˆ _µ_ ( _k_ )) _k_ by taking the sum of the variances in _µ_ ˆ( _k_ ) = _k_ <u>1</u> � _ki_ =1<sup>_R_ˆ</sup><sup>_ei_.</sup> We see that with lim _k→∞_ Var(ˆ _µ_ ( _k_ )) = 0. Thus _µ_ ˆ( _k_ ) is a well-behaved unbiased estimator of _µ_ , as its mean squared error vanishes with _k_ infinitely large: 



Note that _T_ does not appear in these equations. Yet it controls HOpt’s runtime cost ( _T_ trials to determine _λ_<sup>ˆ</sup><sup>_∗_</sup> ), and thus the variance _σ_<sup>2</sup> is a function of _T_ . 

## _3.2.2 Biased estimator: fixing HOpt_ 

A computationally cheaper but biased estimator consists in re-using the hyperparameters obtained from a _single_ hyperparameter optimization to generate _k_ subsequent performance measures _R_<sup>ˆ</sup> _e_ where only _ξO_ (or a subset of _ξO_ ) is randomized. This procedure is presented in Algorithm 2. It requires only _O_ ( _k_ + _T_ ) fittings, substantially less than the ideal estimator. The estimator is biased with _k >_ 1, E � _µ_ ˜( _k_ )� = _µ_ . A bias will occur when a set of hyperparam� eters _λ_<sup>_∗_</sup> are optimal for a particular instance of _ξO_ but not over most others. 

When we fix sources of variation _ξ_ to arbitrary values (e.g. random seed), we are conditioning the distribution of _R_<sup>ˆ</sup> _e_ on some arbitrary _ξ_ . Intuitively, holding fix some sources of variations should reduce the variance of the whole process. What our intuition fails to grasp however, is that this conditioning to arbitrary _ξ_ induces a correlation between the trainings which in turns increases the variance of the estimator. Indeed, a sum of correlated variables increases with the strength of the correlations. 

Let Var( _R_<sup>ˆ</sup> _e | ξ_ ) be the variance of the conditioned performance measures _R_<sup>ˆ</sup> _e_ and _ρ_ the average correlation among 

|**Algorithm 1**IdealEst|**Algorithm 2**FixHOptEst|
|---|---|
|Ideal Estimator ˆ_µ_(_k_)_,_ˆ_σ_(_k_)|Biased Estimator ˜_µ_(_k_)_,_˜_σ_(_k_)|
|**Input:**|**Input:**|
|dataset_S_|dataset_S_|
|sample size_k_|sample size_k_|
|**for**i in_{_1_, · · · , k}_**do**<br>|_ξO ∼_RNG()<br>|
|_ξO ∼_RNG()<br>|_ξH ∼_RNG()<br>|
|_ξH ∼_RNG()<br>|_S_<sup>_tv_</sup>_, S_<sup>_o _</sup>_∼_sp(_S_;_ξO_)<br>ˆ|
|_S_<sup>_tv_</sup>_, S_<sup>_o _</sup>_∼_sp(_S_;_ξO_)<br>_λ_<sup>_∗_</sup><br>�<br>=HOpt(_S_<sup>_tv_</sup>_, ξO, ξH_<br>_h_<sup>_∗_</sup><br>�<br>= Opt(_S_<sup>_tv_</sup>_, λ_<sup>_∗_</sup><br>�<br>)<br><br>|)<br>_λ_<sup>_∗_</sup>=HOpt(_S_<sup>_tv_</sup>_, ξO, ξH_)<br>**for**i in_{_1_, · · · , k}_**do**<br>_ξO ∼_RNG()<br>_S_<sup>_tv_</sup>_, S_<sup>_o _</sup>_∼_sp(_S_;_ξO_)<br>�<br>�|
|_pi_ = <sup>ˆ</sup>_Re_(_h_<sup>_∗_</sup><br>�<br>_, S_<sup>_o_</sup>)|_h_<sup>_∗_</sup><br><br>= Opt(_S_<sup>_tv_</sup>_, λ_<sup>_∗_</sup><br><br>)<br><br>�|
|**end for**<br>|_pi_ = <sup>ˆ</sup>_Re_(_h_<sup>_∗_</sup><br><br>_, S_<sup>_o_</sup>)|
|**Return** ˆ_µ_(_k_) =mean(_p_),<br>|**end for**|
|ˆ_σ_(_k_) =std(_p_)|**Return** ˜_µ_(_k_) =mean(_p_),<br>˜_σ_(_k_) =std(_p_)|



_Figure 4._ Estimators of the performance of a method, and its variation. We represent the seeding of sources of variations with _ξ ∼_ RNG(), where RNG() is some random number generator. Their difference lies in the hyper-parameter optimization step (HOpt). The ideal estimator requires executing _k_ times HOpt, each requiring _T_ trainings for the hyperparameter optimization, for a total of _O_ ( _k · T_ ) trainings. The biased estimator requires executing only 1 time HOpt, for _O_ ( _k_ + _T_ ) trainings in total. 

all pairs of _R_<sup>ˆ</sup> _e_ . The variance of the biased estimator is then given by the following equation. 



We can see that with a large enough correlation _ρ_ , the variance Var(˜ _µ_ ( _k_ ) _| ξ_ ) could be dominated by the second term. In such case, increasing the number of data splits _k_ would not reduce the variance of _µ_ ˜( _k_ ). Unlike with _µ_ ˆ( _k_ ), the mean square error for _µ_ ˜( _k_ ) will not decreases with _k_ : 



This result has two implications, one beneficial to improving benchmarks, the other not. Bad news first: the limited effectiveness of increasing _k_ to improve the quality of the estimator _µ_ ˜( _k_ ) is a consequence of ignoring the variance induced by hyperparameter optimization. We cannot avoid this loss of quality if we do not have the budget for repeated independent hyperoptimization. The good news is that current practices generally account for only one or two sources of variation; there is thus room for improvement. This has the potential of decreasing the average correlation _ρ_ and 

**Accounting for Variance in Machine Learning Benchmarks** 

moving _µ_ ˜( _k_ ) closer to _µ_ ˆ( _k_ ). We will see empirically in next section how accounting for more sources of variation moves us closer to _µ_ ˆ( _k_ ) in most of our case studies. 

## **3.3 The cost of ignoring** HOpt **variance** 

To compare the estimators _µ_ ˆ( _k_ ) and _µ_ ˜( _k_ ) presented above, we measured empirically the statistics of the estimators on budgets of _k_ = (1 _, · · · ,_ 100) points on our five case studies. The ideal estimator is asymptotically unbiased and therefore only one repetition is enough to estimate Var(ˆ _µ_ ( _k_ )) for each task. For the biased estimator we run 20 repetitions to estimate Var(˜ _µ_ ( _k_ ) _| ξ_ ). We sample 20 arbitrary _ξ_ (random seeds) and compute the standard deviation of _µ_ ˜( _k_ ) for _k_ = (1 _, · · · ,_ 100). 

We compared the biased estimator FixedHOptEst() while varying different subset of sources of variations to see if randomizing more of them would help increasing the quality of the estimator. We note FixedHOptEst( _k_ ,Init) the biased estimator _µ_ ˜( _k_ ) randomizing only the weights initialization, FixedHOptEst( _k_ ,Data) the biased estimator randomizing only data splits, and FixedHOptEst( _k_ ,All) the biased estimator randomizing all sources of variation _ξO_ except for hyperparameter optimization. 

We present results from a subset of the tasks in Figure 5 (all tasks are presented in Figure H.4). Randomizing weights initialization only (FixedHOptEst( _k_ ,init)) provides only a small improvement with _k >_ 1. In the task where it best performs (Glue-RTE), it converges to the equivalent of _µ_ ˆ( _k_ =2). This is an important result since it corresponds to the predominant approach used in the literature today. Bootstrapping with FixedHOptEst( _k_ ,Data) improves the standard error for all tasks, converging to equivalent of _µ_ ˆ( _k_ =2) to _µ_ ˆ( _k_ =10). Still, the biased estimator including all sources of variations excluding hyperparameter optimization FixedHOptEst( _k_ ,All) is by far the best estimator after the ideal estimator, converging to equivalent of _µ_ ˆ( _k_ =2) to _µ_ ˆ( _k_ =100). 

This shows that accounting for all sources of variation reduces the likelihood of error in a computationally achievable manner. IdealEst( _k_ = 100) takes 1 070 hours to compute, compared to only 21 hours for each FixedHOptEst( _k_ = 100). Our study paid the high computational cost of multiple rounds of FixedHOptEst( _k_ ,All), and the cost of IdealEst( _k_ ) for a total of _6.4 GPU years_ to show that FixedHOptEst( _k_ ,All) is better than the status-quo and a satisfying option for statistical model comparisons _without_ these prohibitive costs. 



<!-- Start of picture text -->
FixHOptEst(k, Init) FixHOptEst(k, All)<br>FixHOptEst(k, Data) IdealEst(k)<br>0.03<br>Glue-RTE<br>0.02 BERT<br>0.01<br>0.015<br>0.010 PascalVOC<br>ResNet<br>0.005<br>0 20 40 60 80 100<br>Number of samples for the estimator (k)<br>of estimators<br>Standard deviation<br>of estimators<br>Standard deviation<br><!-- End of picture text -->

_Figure 5._ **Standard error of biased and ideal estimators with** _k_ **samples.** Top figure presents results from BERT trained on RTE and bottom figure VGG11 on CIFAR10. All other tasks are presented in Figure H.4. On x axis, the number of samples used by the estimators to compute the average classification accuracy. On y axis, the standard deviation of the estimators. Uncertainty represented in light color is computed analytically as the approximate standard deviation of the standard deviation of a normal distribution computed on _k_ samples. For most case studies, **accounting for more sources of variation reduces the standard error of** _µ_ ˆ( _k_ ) **.** This is caused by the decreased correlation _ρ_ thanks to additional randomization in the learning pipeline. FixHOptEst(k, All) provides an improvement towards IdealEst(k) for no additional computational cost compared to FixHOptEst(k, Init) which is currently considered as a good practice. **Ignoring variance from** HOpt **is harmful for a good estimation of** _R_<sup>ˆ</sup> _P_ **.** 

# **4 ACCOUNTING FOR VARIANCE TO DRAW RELIABLE CONCLUSIONS** 

## **4.1 Criteria used to conclude from benchmarks** 

Given an estimate of the performance of two learning pipelines and their variance, are these two pipelines different in a meaningful way? We first formalize common practices to draw such conclusions, then characterize their error rates. 

**Comparing the average difference** A typical criterion to conclude that one algorithm is superior to another is that one reaches a performance superior to another by some (often implicit) threshold _δ_ . The choice of the threshold _δ_ can be arbitrary, but a reasonable one is to consider previous accepted improvements, e.g. improvements in Figure 3. 

This difference in performance is sometimes computed across a single run of the two pipelines, but a better practice used in the deep-learning community is to average multiple seeds (Bouthillier & Varoquaux, 2020). Typically hyperparameter optimization is performed for each learning 

**Accounting for Variance in Machine Learning Benchmarks** 

algorithm and then several weights initializations or other sources of fluctuation are sampled, giving _k_ estimates of the risk _R_<sup>ˆ</sup> _e_ – note that these are biased as detailed in subsubsection 3.2.2. If an algorithm _A_ performs better than an algorithm _B_ by at least _δ_ on average, it is considered as a better algorithm than _B_ for the task at hand. This approach does not account for false detections and thus can not easily distinguish between true impact and random chance. 

Let _R_<sup>ˆ</sup> _e_<sup>_A_=</sup> _k_<sup><u>1</u></sup> � _ki_ =1<sup>_R_ˆ</sup> _ei_<sup>_A_, where</sup><sup>_R_ˆ</sup> _ei_<sup>_A_is the empirical risk of</sup> algorithm _A_ on the _i_ -th split, be the mean performance of algorithm _A_ , and similarly for _B_ . The decision whether _A_ outperforms _B_ is then determined by ( _R_<sup>ˆ</sup> _e_<sup>_A−R_ˆ</sup> _e_<sup>_B> δ_).</sup> 

The variance is not accounted for in the average comparison. We will now present a statistical test accounting for it. Both comparison methods will next be evaluated empirically using simulations based on our case studies. 

**Probability of outperforming** The choice of threshold _δ_ is problem-specific and does not relate well to a statistical improvement. Rather, we propose to formulate the comparison in terms of _probability of improvement_ . Instead of comparing the average performances, we compare their distributions altogether. Let P( _A > B_ ) be the probability of measuring a better performance for _A_ than _B_ across fluctuations such as data splits and weights initialization. To consider an algorithm _A_ significantly better than _B_ , we ask that _A_ outperforms _B often enough_ : P( _A > B_ ) _≥ γ_ . Often enough, as set by _γ_ , needs to be defined by community standards, which we will revisit below. This probability can simply be computed as the proportion of successes, _R_ ˆ _ei_<sup>_A>R_ˆ</sup> _ei_<sup>_B_,where( ˆ</sup><sup>_R_</sup> _ei_<sup>_A,R_ˆ</sup> _ei_<sup>_B_)</sup><sup>_, i∈{_1</sup><sup>_, . . . , k}_arepairsof</sup> empirical risks measured on _k_ different data splits for algorithms _A_ and _B_ . 



where _I_ is the indicator function. We will build upon the non-parametric Mann-Whitney test to produce decisions about whether P( _A > B_ ) _≥ γ_ (Perme & Manevski, 2019) . 

The problem is well formulated in the Neyman-Pearson view of statistical testing (Neyman & Pearson, 1928; Perezgonzalez, 2015), which requires the explicit definition of both a null hypothesis _H_ 0 to control for _statistically significant_ results, and an alternative hypothesis _H_ 1 to declare results _statistically meaningful_ . A _statistically significant_ result is one that is not explained by noise, the null-hypothesis _H_ 0 : P( _A > B_ ) = 0 _._ 5. With large enough sample size, any arbitrarily small difference can be made _statistically significant_ . A _statistically meaningful_ result is one large enough to satisfy the alternative hypothesis _H_ 1 : P( _A > B_ ) = _γ_ . Recall that _γ_ is a threshold that needs to be defined by community standards. We will discuss reasonable values for _γ_ 

in next section based on our simulations. 

We recommend to conclude that algorithm _A_ is better than _B_ on a given task if the result is both _statistically significant_ and _meaningful_ . The reliability of the estimation of P( _A > B_ ) can be quantified using confidence intervals, computed with the non-parametric percentile bootstrap (Efron, 1982). The lower bound of the confidence interval CImin controls if the result is _significant_ (P( _A > B_ ) _−_ CImin _>_ 0 _._ 5), and the upper bound of the confidence interval CImax controls if the result is _meaningful_ (P( _A > B_ ) + CImax _> γ_ ). 

## **4.2 Characterizing errors of these conclusion criteria** 

We now run an empirical study of the two conclusion criteria presented above, the popular _comparison of average differences_ and our recommended _probability of outperforming_ . We will re-use mean and variance estimates from subsection 3.3 with the ideal and biased estimators to simulate performances of trained algorithms so that we can measure the reliability of these conclusion criteria when using ideal or biased estimators. 

**Simulation of algorithm performances** We simulate realizations of the ideal estimator _µ_ ˆ( _k_ ) and the biased estimator _µ_ ˜( _k_ ) with a budget of _k_ = 50 data splits. For the ideal estimator, we model _µ_ ˆ( _k_ ) with a normal distribution _µ_ ˆ( _k_ ) _∼N_ ( _µ,_<sup>_<u>σ</u>_</sup> _k_<sup>2), where</sup><sup>_σ_2 is the variance measured with</sup> the ideal estimator in our case studies, and _µ_ is the empirical risk _R_<sup>ˆ</sup> _e_ . Our experiments consist in varying the difference in _µ_ for the two algorithms, to span from identical to widely different performance ( _µA >> µB_ ). 

For the biased estimator, we rely on a two stage sampling process for the simulation. First, we sample the bias of _µ_ ˜( _k_ ) based on the variance Var(˜ _µ_ ( _k_ ) _| ξ_ ) measured in our case studies, _Bias ∼N_ (0 _,_ Var(˜ _µ_ ( _k_ ) _| ξ_ )). Given _b_ , a sample of _Bias_ , we sample _k_ empirical risks following _R_<sup>ˆ</sup> _e ∼N_ ( _µ_ + _b,_ Var( _R_<sup>ˆ</sup> _e | ξ_ )), where Var( _R_<sup>ˆ</sup> _e | ξ_ ) is the variance of the empirical risk _R_<sup>ˆ</sup> _e_ averaged across 20 realizations of _µ_ ˜( _k_ ) that we measured in our case studies. 

In simulation we vary the mean performance of _A_ with respect to the mean performance of _B_ so that P( _A > B_ ) varies from 0.4 to 1 to test three regions: 

- _H_ 0 **is true** : Not significant, not meaningful P( _A > B_ ) _−_ CImin _≤_ 0 _._ 5 

- _H_ 0 **&** _H_ 1 **are false (** _H_ 0 _H_ 1 **)** : Significant, not meaningful P( _A > B_ ) _−_ CImin _>_ 0 _._ 5 _∧_ P( _A > B_ ) + CImin _≤ γ_ 

- _H_ 1 **is true** : Significant _and_ meaningful P( _A > B_ ) _−_ CImin _>_ 0 _._ 5 _∧_ P( _A > B_ ) + CImin _> γ_ 

For decisions based on comparing averages, we set _δ_ = 1 _._ 9952 _σ_ where _σ_ is the standard deviation measured in our 

**Accounting for Variance in Machine Learning Benchmarks** 

case studies with the ideal estimator. The value 1.9952 is set by linear regression so that _δ_ matches the average improvements obtained from paperswithcode.com. This provides a threshold _δ_ representative of the published improvements. For the probability of outperforming, we use a threshold of _γ_ = 0 _._ 75 which we have observed to be robust across all case studies (See Appendix I). 

**Observations** Figure 6 reports results for different decision criteria, using the ideal estimator and the biased estimator, as the difference in performance of the algorithms _A_ and _B_ increases (x-axis). The x-axis is broken into three regions: 1) Leftmost is when _H_ 0 is true (not-significant). 2) The grey middle when the result is significant, but not meaningful in our framework ( _H_ 0 _H_ 1 ). 3) The rightmost is when _H_ 1 is true (significant and meaningful). The single point comparison leads to the worst decision by far. It suffers from both high false positives ( _≈_ 10%) and high false negatives ( _≈_ 75%). The average with _k_ = 50, on the other hand, is very conservative with low false positives ( _<_ 5%) but very high false negatives ( _≈_ 90%). Using the probability of outperforming leads to better balanced decisions, with a reasonable rate of false positives ( _≈_ 5%) on the left and a reasonable rate of false negatives on the right ( _≈_ 30%). 

The main problem with the average comparison is the threshold. A t-test only differs from an average in that the threshold is computed based on the variance of the model performances and the sample size. It is this adjustment of the threshold based on the variance that allows better control on false negatives. 

Finally, we observe that the test of probability of outperforming (P( _A > B_ )) controls well the error rates even when used with a biased estimator. Its performance is nevertheless impacted by the biased estimator compared to the ideal estimator. Although we cannot guarantee a nominal control, we confirm that it is a major improvement compared to the commonly used comparison method at no additional cost. 

# **5 OUR RECOMMENDATIONS: GOOD BENCHMARKS WITH A BUDGET** 

We now distill from the theoretical and empirical results of the previous sections a set of practical recommendations to benchmark machine-learning pipelines. Our recommendations are pragmatic in the sense that they are simple to implement and cater for limited computational budgets. 

**Randomize as many sources of variations as possible** Fitting and evaluating a modern machine-learning pipeline comes with many arbitrary aspects, such as the choice of initializations or the data order. Benchmarking a pipeline given a specific instance of these choices will not give an evaluation that generalize to new data, even drawn from the same 



<!-- Start of picture text -->
IdealEst FixHOptEst Comparison Methods<br>Single point comparison<br>Average comparison thresholded based<br>on typical published improvement<br>Proposed testing probability of improvement<br>100<br>H0 H1<br>Optimal<br>oracle H1<br>50 H0 (higher=better)<br>(lower=better)<br>0<br>0.4 0.5 0.6 0.7 0.8 0.9 1.0<br>P(A > B)<br>Rate of Detections<br><!-- End of picture text -->

_Figure 6._ **Rate of detections of different comparison methods.** x axis is the true simulated probability of a learning algorithm _A_ to outperform another algorithm _B_ across random fluctuations (ex: random data splits). We vary the mean performance of _A_ with respect to that of _B_ so that P( _A > B_ ) varies from 0.4 to 1. The blue line is the optimal oracle, with perfect knowledge of the variances. The single-point comparison (green line) has both a high rate of false positives in the left region ( _≈_ 10%) and a high rate of false negative on the right ( _≈_ 75%). The orange and purple lines show the results for the _average comparison method_ (prevalent in the literature) and our proposed _probability of outperforming_ method respectively. The solid versions are using the expensive ideal estimator, and the dashed line our 51 _×_ cheaper, but biased, estimator. The average comparison is highly conservative with a low rate of false positives ( _<_ 5%) on the left and a high rate of false negative on the right ( _≈_ 90%), even with the expensive and exhaustive simulation. Using the probability of outperforming has both a reasonable rate of false positives ( _≈_ 5%) on the left and a reasonable rate of false negatives on the right ( _≈_ 30%) even when using our biased estimator, and approaches the oracle when using the expensive estimator. 

distribution. On the opposite, a benchmark that varies these arbitrary choices will not only evaluate the associated variance (section 2), but also reduce the error on the expected performance as they enable measures of performance on the test set that are less correlated (3). This counter-intuitive phenomenon is related to the variance reduction of bagging (Breiman, 1996a; Buhlmann et al.¨ , 2002), and helps characterizing better the expected behavior of a machine-learning pipeline, as opposed to a specific fit. 

**Use multiple data splits** The subset of the data used as test set to validate an algorithm is arbitrary. As it is of a limited size, it comes with a limited estimation quality with regards to the performance of the algorithm on wider samples of the same data distribution (figure 2). Improvements smaller than this variance observed on a given test set will not generalize. Importantly, this variance is not negligible compared to typical published improvements or other sources of variance (figures 1 and 3). For pipeline 

**Accounting for Variance in Machine Learning Benchmarks** 

comparisons with more statistical power, it is useful to draw multiple tests, for instance generating random splits with a out-of-bootstrap scheme (detailed in appendix B). 

**Account for variance to detect meaningful improvements** Concluding on the significance –statistical or practical– of an improvement based on the difference between average performance requires the choice of a threshold that can be difficult to set. A natural scale for the threshold is the variance of the benchmark, but this variance is often unknown before running the experiments. Using the probability of outperforming P( _A > B_ ) with a threshold of 0 _._ 75 gives empirically a criterion that separates well benchmarking fluctuations from published improvements over the 5 case studies that we considered. We recommend to always highlight not only the best-performing procedure, but also all those within the significance bounds. We provide an example in Appendix C to illustrate the application of our recommended statistical test. 

# **6 ADDITIONAL CONSIDERATIONS** 

There are many aspects of benchmarks which our study has not addressed. For completeness, we discuss them here. 

**Comparing models instead of procedures** Our framework provides value when the user can control the model training process and source of variation. In cases where models are _given_ but not under our control (e.g., purchased via API or a competition), the only source of variation left is the data used to test the model. Our framework and analysis does not apply to such scenarios. 

**Benchmarks and competitions with many contestants** We focused on comparing two learning algorithms. Benchmarks – and competitions in particular – commonly involve large number of learning algorithms that are being compared. Part of our results carry over unchanged in such settings, in particular those related to variance and performance estimation. With regards to reaching a well-controlled decision, a new challenge comes from multiple comparisons when there are many algorithms. A possible alley would be to adjust the decision threshold _γ_ , raising it with a correction for multiple comparisons (e.g. Bonferroni) (Dudoit et al., 2003). However, as the number gets larger, the correction becomes stringent. In competitions where the number of contestants can reach hundreds, the choice of a winner comes necessarily with some arbitrariness: a different choice of test sets might have led to a slightly modified ranking. 

**Comparisons across multiple dataset** Comparison over multiple datasets is often used to accumulate evidence that one algorithm outperforms another one. The challenge is to account for different errors, in particular different levels of 

variance, on each dataset. 

Demsarˇ (2006) recommended Wilcoxon signed ranks test or Friedman tests to compare classifiers across multiple datasets. These recommendations are however hardly applicable on small sets of datasets – machine learning works typically include as few as 3 to 5 datasets (Bouthillier & Varoquaux, 2020). The number of datasets corresponds to the sample size of these tests, and such a small sample size leads to tests of very limited statistical power. 

Dror et al. (2017) propose to accept methods that give improvements on _all_ datasets, controlling for multiple comparisons. As opposed to Demsarˇ (2006)’s recommendation, this approach performs well with a small number of datasets. On the other hand, a large number of datasets will increase significantly the severity of the family-wise error-rate correction, making Demˇsar’s recommendations more favorable. 

**Non-normal metrics** We focused on model performance, but model evaluation in practice can include other metrics such as the training time to reach a performance level or the memory foot-print (Reddi et al., 2020). Performance metrics are generally averages over samples which typically makes them amenable to a reasonable normality assumption. 

# **7 CONCLUSION** 

We showed that fluctuations in the performance measured by machine-learning benchmarks arise from many different sources. In deep learning, most evaluations focus on the effect of random weight initialization, which actually contribute a small part of the variance, on par with residual fluctuations of hyperparameter choices after their optimization but much smaller than the variance due to perturbing the split of the data in train and test sets. Our study clearly shows that these factors must be accounted to give reliable benchmarks. For this purpose, we study estimators of benchmark variance as well as decision criterion to conclude on an improvement. Our findings outline recommendations to improve reliability of machine learning benchmarks: 1) randomize as many sources of variations as possible in the performance estimation; 2) prefer multiple random splits to fixed test sets; 3) account for the resulting variance when concluding on the benefit of an algorithm over another. 

# **REFERENCES** 

- Anders Sogaard, Anders Johannsen, B. P. D. H. and Alonso, H. M. What’s in a p-value in nlp? In _Proceedings of the Eighteenth Conference on Computational Natural Language Learning_ , pp. 1–10. Association for Computational Linguistics, 2014. 

Bentivogli, L., Dagan, I., Dang, H. T., Giampiccolo, D., 

**Accounting for Variance in Machine Learning Benchmarks** 

- and Magnini, B. The fifth PASCAL recognizing textual entailment challenge. 2009. 

- Blalock, D., Gonzalez Ortiz, J. J., Frankle, J., and Guttag, J. What is the State of Neural Network Pruning? In _Proceedings of Machine Learning and Systems 2020_ , pp. 129–146. 2020. 

- Bouckaert, R. R. and Frank, E. Evaluating the replicability of significance tests for comparing learning algorithms. In _Pacific-Asia Conference on Knowledge Discovery and Data Mining_ , pp. 3–12. Springer, 2004. 

- Bouthillier, X. and Varoquaux, G. Survey of machinelearning experimental methods at NeurIPS2019 and ICLR2020. Research report, Inria Saclay Ile de France, January 2020. URL https://hal. archives-ouvertes.fr/hal-02447823. 

- Bouthillier, X., Laurent, C., and Vincent, P. Unreproducible research is reproducible. In Chaudhuri, K. and Salakhutdinov, R. (eds.), _Proceedings of the 36th International Conference on Machine Learning_ , volume 97 of _Proceedings of Machine Learning Research_ , pp. 725–734, Long Beach, California, USA, 09–15 Jun 2019. PMLR. URL http://proceedings.mlr. press/v97/bouthillier19a.html. 

- Breiman, L. Bagging predictors. _Machine learning_ , 24(2): 123–140, 1996a. 

Breiman, L. Out-of-bag estimation. 1996b. 

- Buhlmann, P., Yu, B., et al.¨ Analyzing bagging. _The Annals of Statistics_ , 30(4):927–961, 2002. 

- Canty, A. J., Davison, A. C., Hinkley, D. V., and Ventura, V. Bootstrap diagnostics and remedies. _Canadian Journal of Statistics_ , 34(1):5–27, 2006. 

- Dacrema, M. F., Cremonesi, P., and Jannach, D. Are we really making much progress? A Worrying Analysis of Recent Neural Recommendation Approaches. In _Proceedings of the 13th ACM Conference on Recommender Systems - RecSys ’19_ , pp. 101–109, New York, New York, USA, 2019. ACM Press. ISBN 9781450362436. doi: 10.1145/3298689.3347058. URL http://dl.acm. org/citation.cfm?doid=3298689.3347058. 

- Demsar, J.ˇ Statistical comparisons of classifiers over multiple data sets. _Journal of Machine learning research_ , 7 (Jan):1–30, 2006. 

- Deng, J., Dong, W., Socher, R., Li, L.-J., Li, K., and FeiFei, L. ImageNet: A Large-Scale Hierarchical Image Database. In _CVPR09_ , 2009. 

- Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. Bert: Pre-training of deep bidirectional transformers for language understanding, 2018. 

- Dietterich, T. G. Approximate statistical tests for comparing supervised classification learning algorithms. _Neural computation_ , 10(7):1895–1923, 1998. 

- Dror, R., Baumer, G., Bogomolov, M., and Reichart, R. Replicability analysis for natural language processing: Testing significance with multiple datasets. _Transactions of the Association for Computational Linguistics_ , 5:471– 486, 2017. 

- Dudoit, S., Shaffer, J. P., and Boldrick, J. C. Multiple hypothesis testing in microarray experiments. _Statistical Science_ , pp. 71–103, 2003. 

- Efron, B. Bootstrap methods: Another look at the jackknife. _Ann. Statist._ , 7(1):1–26, 01 1979. doi: 10.1214/aos/ 1176344552. URL https://doi.org/10.1214/ aos/1176344552. 

- Efron, B. _The jackknife, the bootstrap, and other resampling plans_ , volume 38. Siam, 1982. 

- Efron, B. and Tibshirani, R. J. _An introduction to the bootstrap_ . CRC press, 1994. 

- Everingham, M., Van Gool, L., Williams, C. K. I., Winn, J., and Zisserman, A. The PASCAL Visual Object Classes Challenge 2012 (VOC2012) Results. http://www.pascalnetwork.org/challenges/VOC/voc2012/workshop/index.html. 

- Glorot, X. and Bengio, Y. Understanding the difficulty of training deep feedforward neural networks. In Teh, Y. W. and Titterington, M. (eds.), _Proceedings of the Thirteenth International Conference on Artificial Intelligence and Statistics_ , volume 9 of _Proceedings of Machine Learning Research_ , pp. 249– 256, Chia Laguna Resort, Sardinia, Italy, 13–15 May 2010. PMLR. URL http://proceedings.mlr. press/v9/glorot10a.html. 

- Gorman, K. and Bedrick, S. We need to talk about standard splits. In _Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics_ , pp. 2786–2791, Florence, Italy, July 2019. Association for Computational Linguistics. doi: 10.18653/ v1/P19-1267. URL https://www.aclweb.org/ anthology/P19-1267. 

- He, K., Zhang, X., Ren, S., and Sun, J. Deep residual learning for image recognition, 2015a. 

- He, K., Zhang, X., Ren, S., and Sun, J. Delving deep into rectifiers: Surpassing human-level performance on 

**Accounting for Variance in Machine Learning Benchmarks** 

- imagenet classification. In _Proceedings of the IEEE international conference on computer vision_ , pp. 1026–1034, 2015b. 

- He, K., Zhang, X., Ren, S., and Sun, J. Identity mappings in deep residual networks. In _European conference on computer vision_ , pp. 630–645. Springer, 2016. 

- Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., and Meger, D. Deep reinforcement learning that matters. In _Thirty-Second AAAI Conference on Artificial Intelligence_ , 2018. 

- Henikoff, S. and Henikoff, J. G. Amino acid substitution matrices from protein blocks. _Proceedings of the National Academy of Sciences_ , 89(22):10915–10919, 1992. 

- Hothorn, T., Leisch, F., Zeileis, A., and Hornik, K. The design and analysis of benchmark experiments. _Journal of Computational and Graphical Statistics_ , 14(3):675– 699, 2005. 

- Hutter, F., Hoos, H., and Leyton-Brown, K. An efficient approach for assessing hyperparameter importance. In _Proceedings of International Conference on Machine Learning 2014 (ICML 2014)_ , pp. 754–762, June 2014. 

- Jurtz, V., Paul, S., Andreatta, M., Marcatili, P., Peters, B., and Nielsen, M. Netmhcpan-4.0: improved peptide–mhc class i interaction predictions integrating eluted ligand and peptide binding affinity data. _The Journal of Immunology_ , 199(9):3360–3368, 2017. 

- Kadlec, R., Bajgar, O., and Kleindienst, J. Knowledge base completion: Baselines strike back. In _Proceedings of the 2nd Workshop on Representation Learning for NLP_ , pp. 69–74, 2017. 

- Kingma, D. P. and Welling, M. Auto-encoding variational bayes. In Bengio, Y. and LeCun, Y. (eds.), _2nd International Conference on Learning Representations, ICLR 2014, Banff, AB, Canada, April 14-16, 2014, Conference Track Proceedings_ , 2014. URL http://arxiv.org/ abs/1312.6114. 

- Klein, A., Falkner, S., Mansur, N., and Hutter, F. Robo: A flexible and robust bayesian optimization framework in python. In _NIPS 2017 Bayesian Optimization Workshop_ , December 2017. 

- Krizhevsky, A., Hinton, G., et al. Learning multiple layers of features from tiny images. 2009. 

- Liu, C., Zoph, B., Neumann, M., Shlens, J., Hua, W., Li, L.-J., Fei-Fei, L., Yuille, A., Huang, J., and Murphy, K. Progressive neural architecture search. In _The European Conference on Computer Vision (ECCV)_ , September 2018. 

- Long, J., Shelhamer, E., and Darrell, T. Fully convolutional networks for semantic segmentation, 2014. 

- Lucic, M., Kurach, K., Michalski, M., Gelly, S., and Bousquet, O. Are gans created equal? a large-scale study. In Bengio, S., Wallach, H., Larochelle, H., Grauman, K., Cesa-Bianchi, N., and Garnett, R. (eds.), _Advances in Neural Information Processing Systems 31_ , pp. 700–709. Curran Associates, Inc., 2018. 

- Maddison, C. J., Mnih, A., and Teh, Y. W. The concrete distribution: A continuous relaxation of discrete random variables. In _5th International Conference on Learning Representations, ICLR 2017, Toulon, France, April 24-26, 2017, Conference Track Proceedings_ . OpenReview.net, 2017. URL https://openreview.net/forum? id=S1jE5L5gl. 

- Mahajan, D., Girshick, R., Ramanathan, V., He, K., Paluri, M., Li, Y., Bharambe, A., and van der Maaten, L. Exploring the limits of weakly supervised pretraining. In _Proceedings of the European Conference on Computer Vision (ECCV)_ , pp. 181–196, 2018. 

- Melis, G., Dyer, C., and Blunsom, P. On the state of the art of evaluation in neural language models. _ICLR_ , 2018. 

- Musgrave, K., Belongie, S., and Lim, S.-N. A Metric Learning Reality Check. _arXiv_ , 2020. URL http: //arxiv.org/abs/2003.08505. 

- Nadeau, C. and Bengio, Y. Inference for the generalization error. In Solla, S. A., Leen, T. K., and Muller, K. (eds.),¨ _Advances in Neural Information Processing Systems 12_ , pp. 307–313. MIT Press, 2000. 

- Neyman, J. and Pearson, E. S. On the use and interpretation of certain test criteria for purposes of statistical inference: Part i. _Biometrika_ , pp. 175–240, 1928. 

- Nielsen, M., Lundegaard, C., Blicher, T., Lamberth, K., Harndahl, M., Justesen, S., Røder, G., Peters, B., Sette, A., Lund, O., et al. Netmhcpan, a method for quantitative predictions of peptide binding to any hla-a and-b locus protein of known sequence. _PloS one_ , 2(8), 2007. 

- Noether, G. E. Sample size determination for some common nonparametric tests. _Journal of the American Statistical Association_ , 82(398):645–647, 1987. 

- O’Donnell, T. J., Rubinsteyn, A., Bonsack, M., Riemer, A. B., Laserson, U., and Hammerbacher, J. Mhcflurry: open-source class i mhc binding affinity prediction. _Cell systems_ , 7(1):129–132, 2018. 

- Pearson, H., Daouda, T., Granados, D. P., Durette, C., Bonneil, E., Courcelles, M., Rodenbrock, A., Laverdure, J.-P., 

**Accounting for Variance in Machine Learning Benchmarks** 

- Cotˆ e,´ C., Mader, S., et al. Mhc class i–associated peptides derive from selective regions of the human genome. _The Journal of clinical investigation_ , 126(12):4690–4701, 2016. 

- Perezgonzalez, J. D. Fisher, neyman-pearson or nhst? a tutorial for teaching data testing. _Frontiers in Psychology_ , 6:223, 2015. 

- Perme, M. P. and Manevski, D. Confidence intervals for the mann–whitney test. _Statistical methods in medical research_ , 28(12):3755–3768, 2019. 

- Raff, E. A Step Toward Quantifying Independently Reproducible Machine Learning Research. In _NeurIPS_ , 2019. URL http://arxiv.org/abs/1909.06674. 

- Raff, E. Research Reproducibility as a Survival Analysis. In _The Thirty-Fifth AAAI Conference on Artificial Intelligence_ , 2021. URL http://arxiv.org/abs/ 2012.09932. 

- Reddi, V. J., Cheng, C., Kanter, D., Mattson, P., Schmuelling, G., Wu, C.-J., Anderson, B., Breughe, M., Charlebois, M., Chou, W., et al. Mlperf inference benchmark. In _2020 ACM/IEEE 47th Annual International Symposium on Computer Architecture (ISCA)_ , pp. 446– 459. IEEE, 2020. 

- Reimers, N. and Gurevych, I. Reporting score distributions makes a difference: Performance study of LSTMnetworks for sequence tagging. In _Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing_ , pp. 338–348, Copenhagen, Denmark, September 2017. Association for Computational Linguistics. doi: 10.18653/v1/D17-1035. URL https: //www.aclweb.org/anthology/D17-1035. 

   - Taylor Berg-Kirkpatrick, D. B. and Klein, D. An empirical investigation of statistical significance in nlp. In _Proceedings of the 2012 Joint Conference on Empirical Methods in Natural Language Processing and Computational Natural Language Learning_ , pp. 995–1005. Association for Computational Linguistics, 2012. 

   - Torralba, A., Fergus, R., and Freeman, W. T. 80 million tiny images: A large data set for nonparametric object and scene recognition. _IEEE transactions on pattern analysis and machine intelligence_ , 30(11):1958–1970, 2008. 

   - Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., and Polosukhin, I. Attention is all you need, 2017. 

   - Vita, R., Mahajan, S., Overton, J. A., Dhanda, S. K., Martini, S., Cantrell, J. R., Wheeler, D. K., Sette, A., and Peters, B. The immune epitope database (iedb): 2018 update. _Nucleic acids research_ , 47(D1):D339–D343, 2019. 

   - Wang, A., Singh, A., Michael, J., Hill, F., Levy, O., and Bowman, S. R. GLUE: A multi-task benchmark and analysis platform for natural language understanding. 2019. In the Proceedings of ICLR. 

   - Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P., Rault, T., Louf, R., Funtowicz, M., and Brew, J. Huggingface’s transformers: State-of-theart natural language processing. _ArXiv_ , abs/1910.03771, 2019. 

   - Xie, Q., Hovy, E., Luong, M.-T., and Le, Q. V. Selftraining with noisy student improves imagenet classification. _arXiv preprint arXiv:1911.04252_ , 2019. 

- Riezler, S. and Maxwell, J. T. On some pitfalls in automatic evaluation and significance testing for mt. In _Proceedings of the ACL Workshop on Intrinsic and Extrinsic Evaluation Measures for Machine Translation and/or Summarization_ , pp. 57–64, 2005. 

- Simonyan, K. and Zisserman, A. Very deep convolutional networks for large-scale image recognition. _arXiv preprint arXiv:1409.1556_ , 2014. 

- Socher, R., Perelygin, A., Wu, J., Chuang, J., Manning, C. D., Ng, A., and Potts, C. Recursive deep models for semantic compositionality over a sentiment treebank. In _Proceedings of EMNLP_ , pp. 1631–1642, 2013. 

- Srivastava, N., Hinton, G., Krizhevsky, A., Sutskever, I., and Salakhutdinov, R. Dropout: A simple way to prevent neural networks from overfitting. _Journal of Machine Learning Research_ , 15(56):1929–1958, 2014. URL http://jmlr.org/papers/v15/ srivastava14a.html. 

**Accounting for Variance in Machine Learning Benchmarks** 

# **A NOTES ON REPRODUCIBILITY** 

Ensuring full reproducibility is often a tedious work. We provide here notes and remarks on the issues we encountered while working towards fully reproducible experiments. 

**The testing procedure** To ensure proper study of the sources of variation it was necessary to control them close to perfection. For all tasks, we ran a pipeline of tests to ensure perfect reproducibility at execution and also at resumption. During the tests, each source of variation was varied with 5 different seeds, each executed 5 times. This ensured that the pipeline was reproducible for different seeds. Additionally, for each source of variation and for each seed, another training was executed but automatically interrupted after each epoch. The worker would then start the training of the next seed and iterate through the trainings for all seeds before resuming the first one. All these tests uncovered many bugs and typical reproducibility issues in machine learning. We report here some notes. 

**Computer architecture & drivers** Although we did not measure the variance induced by different GPU architectures, we did observe that different GPU models would lead to different results. The CPU model had less impact on the Deep Learning tasks but the MLP-MHC task was sensitive to it. We therefore limited all tasks to specific computer architectures. We also observed issues when CUDA drivers were updated during preliminary experiments. We ensured all experiments were run using CUDA 10.2. 

**Software & seeds** PyTorch versions lead to different results as well. We ran every Deep Learning experiments with PyTorch 1.2.0. 

We implemented our data pipeline so that we could seed the iterators, the data augmentation objects and the splitting of the datasets. We had less control at the level of the models however. For PyTorch 1.2.0, the random number generator (RNG) must be seeded globally which makes it difficult to seed different parts separately. We seeded PyTorch’s global RNG for weight initialization at the beginning of the training process and then seeded PyTorch’s RNG for the dropout. Afterwards we checkpoint the RNG state so that we can restore the RNG states at resumption. We found that models with convolutionnal layers would not yield reproducible results unless we enabled cudnn.deterministic and disabled cudnn.benchmark. 

We used the library RoBO (Klein et al., 2017) for our Bayesian Optimizer. There was no support for seeding, we therefore resorted to seeding the global seed of python and numpy random number generators. We needed again to keep track of the RNG states and checkpoint them so that we can resume the Bayesian Optimizer without harming the 

## reproducibility. 

For one of our case study, image segmentation, we have been unable to make the learning pipeline perfectly reproducible. This is problematic because it prevents us from studying each source of variation in isolation. We thus trained our model with every seeds fixed across all 200 trainings and measured the variance we could not control. This is represented as the numerical noise in Figures 1 and G.3. 

# **B OUR BOOTSTRAP PROCEDURE** 

Cross-validation with different _k_ impacts the number of samples, it is not the case with not bootstrap. That means flexible sample sizes for statistical tests is hardly possible with cross-validation within affecting the training dataset sizes. (Hothorn et al., 2005) focuses on the dataset sampling as the most important source of variation and marginalize out all other sources by taking the average performance over multiple runs for a given dataset. This increases even more the computational cost of the statistical tests. 

We probe the effect of data sampling with bootstrap, specifically by bootstrapping to generate training sets and measuring the out-of-bootstrap error, as introduced by Breiman (1996b) in the context of bagging and generalized by (Hothorn et al., 2005). For completeness, we formalize this use of the bootstrap to create training and test sets and how it can estimate the variance of performance measure due to data sampling on a finite dataset. 

We assume we are seeking to generate sets of i.i.d. samples from true distribution _D_ . Ideally we would have access to _D_ and could sample our finite datasets independently from it. 



Instead we have one dataset _S ∼D_<sup>_n_</sup> of finite size _n_ and need to sample independent datasets from it. A popular method in machine learning to estimate performance on a small dataset is cross-validation (Bouckaert & Frank, 2004; Dietterich, 1998). This method however underestimates variance because of correlations induced by the process. We instead favor bootstrapping (Efron, 1979) as used by (Hothorn et al., 2005) to simulate independent data sampling from the true distribution. 



Where _Sb_<sup>_t∼S_representssamplingthe</sup><sup>_b_-thtrainingset</sup> with replacement from the set _S_ . We then turn to out-ofbootstrapping to generate the held-out set. We use all remaining samples in _S \ Sb_<sup>_t_to sample</sup><sup>_S_</sup> _b_<sup>_o_.</sup> 

_Sb_<sup>_o_=</sup><sup>_{_(</sup><sup>_x_1</sup><sup>_, y_1)</sup><sup>_,_(</sup><sup>_x_2</sup><sup>_, y_2)</sup><sup>_, · · ·_(</sup><sup>_xn, yn_)</sup><sup>_} ∼S \ S_</sup> _b_<sup>_t_</sup> (12) This procedure is represented as ( _S_<sup>_tv_</sup> _, S_<sup>_o_</sup> ) _∼ spn,n′_ ( _S_ ) in the empirical average risk _R_<sup>ˆ</sup> _P_ ( _S, n, n_<sup>_′_</sup> ), end of Section 2.1. 

**Accounting for Variance in Machine Learning Benchmarks** 

# **C STATISTICAL TESTING** 

We are interested in asserting whether a learning algorithm _A_ better performs than another learning algorithm _B_ . Measuring the performance of these learning algorithms is not a deterministic process however and we may be deceived if noise is not accounted for. Because of the noise, we cannot know for sure whether a conclusion we draw is true, but using a statistical test, we can at least ensure a bounded rate of false positives (drawing _A > B_ while truth is _A ≤ B_ ) and false negatives (drawing _A ≤ B_ while truth is _A > B_ ). The capacity of a statistical test to identify true differences, that is, of correctly inferring _A > B_ when this is true, is called the statistical power of a test. The procedure we describe here seeks to avoid deception from false positives while providing a strong statistical power. 

We will describe the entire procedure, from the generation of the performance measures (Sections C.1 & C.2), the estimation of sample size (Section C.3), computation of P( _A > B_ ) (Section C.4), computation of the confidence interval (Section C.5) to the inference based on the statistical test (Section C.6) 

## **C.1 Randomizing sources of variance** 

As shown in Section 3, randomizing as many sources of variance as possible in the learning pipelines help reduce the correlation and thus improve the reliability of the performance estimation. The simplest way to randomize as many as possible is to simply avoid seeding the random number generators. We list here sources of variations we faced in our case studies, but there exists many other sources of variations in diverse learning algorithms and tasks. 

- **Data splits** The data being used should ideally always be different samples from the true distribution of interest. In practice we only have access to a finite dataset and therefore the best we can do is random splits with cross-validation or out-of-bootstrap as described in Appendix B. 

- **Data order** The ordering of the data can have a surprisingly important impact as can be observed in Figure 1. 

- **Data augmentation** Stochastic data augmentation should not be seeded, so that it follows a different sequence at each run. 

- **Model initialization** Model initialization, e.g. weights initialization in neural networks, should be randomized across all trainings. 

- **Model stochasticity** Learning algorithms sometimes include stochastic computations such as dropout in neural networks (Srivastava et al., 2014), or samplings 

methods (Kingma & Welling, 2014; Maddison et al., 2017). 

- **Hyperparameter optimization** The optimization of the hyperparameters generally include stochasticity which should ideally be randomized. Running multiple hyperparameter optimizations may often be practically unaffordable. Tests may still be carried out while fixing the hyperparameters after a single hyperparameter optimization, but keep in mind the incurred degradation of the reliability of the conclusion as shown in Section 4. 

## **C.2 Pairing** 

Pairing is optional but is highly recommended to increase statistical power. Avoiding seeding is the simplest solution for the randomization, but it is not the best solution. If possible, meticulously seeding all sources of variation with different random seeds at each run makes it possible to pair trainings of the algorithms so that we can conduct paired comparisons. 

Pairing is a simple but powerful way of increasing the power of statistical tests, that is, enabling the reliable detection of difference with smaller sample sizes. Let _σA_ and _σB_ be the standard deviation of the performance metric of learning algorithms _A_ and _B_ respectively. If measures of _R_<sup>ˆ</sup> _e_<sup>_A_and</sup><sup>_R_ˆ</sup> _e_<sup>_A_</sup> are not paired, the standard deviation of _R_<sup>ˆ</sup> _e_<sup>_A−R_ˆ</sup> _e_<sup>_B_is then</sup> _σA_ + _σB_ . If we pair them, then we marginalize out sources of variance which results in a smaller variance _σA−B ≤ σA_ + _σB_ . This reduction of variance makes it possible to reliably detect smaller differences without increasing the sample size. 

To pair the learning algorithms, sources of variation should be randomized similarly for all of them. For instance, the random split of the dataset obtained from out-ofbootstrap should be used for both _A_ and _B_ when making a comparison. Suppose we plan to execute 10 runs of _A_ and _B_ , then we should generate 10 different splits _{_ ( _S_ 1<sup>_tv, S_</sup> 1<sup>_o_)</sup><sup>_,_(</sup><sup>_S_</sup> 2<sup>_tv, S_</sup> 2<sup>_o_)</sup><sup>_, · · ·,_(</sup><sup>_S_</sup> 10<sup>_tv, S_</sup> 10<sup>_o_)</sup><sup>_}_andtrain</sup><sup>_A_and</sup><sup>_B_</sup> on each. The performances ( _R_<sup>ˆ</sup> _ei_<sup>_A,R_ˆ</sup> _ei_<sup>_B_) would then be com-</sup> pared only on the corresponding splits ( _Si_<sup>_tv, S_</sup> _i_<sup>_o_).The same</sup> would apply to all other sources of variations. In practical terms, pairing _A_ and _B_ requires sampling seeds for each pairs, re-using the same seed for _A_ and _B_ in each pairs. 

For some sources of variation it may not make sense to pair. This is the case for instance with weights initialization if _A_ and _B_ involve different neural network architectures. We can still pair. This would not help much, but would not hurt as well. In doubt, it is better to pair. 

## **C.3 Sample size** 

As explained in Section 3, the more runs we have from _R_<sup>ˆ</sup> _e_<sup>_A_</sup> and _R_<sup>ˆ</sup> _e_<sup>_B_,themorereliabletheestimateofP(</sup><sup>_A>B_)is.</sup> 

**Accounting for Variance in Machine Learning Benchmarks** 



<!-- Start of picture text -->
150<br>100<br>50<br>Recommended<br>29<br>0<br>0.6 0.7 0.75 0.8 0.9 1.0<br>Sample size<br><!-- End of picture text -->

_Figure C.1._ **Minimum sample size to detect** _P_ ( _A > B_ ) _> γ_ **reliably.** x-axis is the threshold _γ_ and y-axis is the minimum sample size to reliably detect _P_ ( _A > B_ ) _> γ_ . The red star shows the recommended threshold _γ_ based on our results in Section 4 and the corresponding minimal sample size. We see that detecting reliably _P_ ( _A > B_ ) _<_ 0 _._ 6 is unpractical with minimal sample sizes quickly moving above 500. The recommended threshold on the other hand leads to a reasonable sample size of 29. 

Lets note this number of runs as the sample size _N_ , not to be confused with dataset size _n_ . There exist a way of computing the minimal sample size required to ensure a minimal rate of false negatives based on power analysis. 

We must first set the threshold _γ_ for our test. Based on our experiments in Section 4, we recommend a value of 0.75. We then set the desired rates of false positives and false negatives with _α_ and _β_ respectively. Usual value for _α_ is 0.05 while _β_ ranges from 0.05 to 0.2. We recommend _β_ = 0 _._ 05 for a strong statistical power. 

The estimation of _P_ ( _A > B_ ) is equivalent to a Mann–Whitney test (Perme & Manevski, 2019), thus we can use Noether’s sample size determination method for this type of test (Noether, 1987). 



## **C.4 Compute** P( _A > B_ ) 

For all paired performances ( _R_<sup>ˆ</sup> _ei_<sup>_A,R_ˆ</sup> _ei_<sup>_B_),wecompute</sup> _I{_ ˆ _Rei_<sup>_A,_ˆ</sup> _Rei_<sup>_B}_,where</sup><sup>_I_istheindicatorfunction.Iftrainings</sup> were not paired as described in Section C.2, the pairs are randomly selected. We can then compute P( _A > B_ ) following Equation 9. 

## **C.5 Confidence interval of** P( _A > B_ ) **with percentile bootstrap** 

For the estimation of P( _A > B_ ) with values below 0.95, we recommend the use of the the percentile bootstrap<sup>¶</sup> (Efron & Tibshirani, 1994). 

Suppose we have _N_ pairs ( _R_<sup>ˆ</sup> _ei_<sup>_A,R_ˆ</sup> _ei_<sup>_B_).To compute the per-</sup> centile bootstrap, we first generate _K_ groups of _N_ pairs. To do so, we sample with replacement _N_ pairs, and do so independently _K_ times. For each of the _K_ groups, we compute P( _A > B_ ). We sort the _K_ estimations of P( _A > B_ ) and pick the _α/_ 2-percentile and (1 _− α/_ 2)- percentile as the lower and upper bounds. The confidence interval is defined as these lower and upper bounds computed with percentile bootstrap. 

## **C.6 Statistical test with** P( _A > B_ ) 

Let CImin and CImax be the lower and upper bounds of the confidence interval. We draw a conclusion based on the three following scenarios. 

- **CI** min _≤_ 0 _._ 5 : Not statistically significant. No conclusion should be drawn as the result could be explained by noise alone. 

- **CI** max _≤ γ_ : Not statistically meaningful. Perhaps CImin _>_ 0 _._ 5 but it is irrelevant since P( _A > B_ ) is too small to be meaningful. 

- **CI** min _>_ 0 _._ 5 _∧_ **CI** max _> γ_ : Statistically significant and meaningful. We can conclude that learning algorithm _A_ is better performing than _B_ in the conditions defined by the experiments. 

# **D CASE STUDIES** 

## **D.1 CIFAR10 Image classification with VGG11** 

Where Φ<sup>_−_1</sup> is the inverse cumulative function of the normal distribution. 

Figure C.1 shows how the minimal sample size evolves with _γ_ . Detecting _P_ ( _A > B_ ) below _γ_ = 0 _._ 6 is unpractical, requiring more that 700 trainings below 0.55 for instance. For a threshold that is representative of the published improvements as presented in Figure 3, _γ_ = 0 _._ 75, the minimal sample size required to ensure a rate of 5% false negatives (as defined by _β_ = 0 _._ 05) is reasonably small; 29 trainings. 

**Task** CIFAR10 (Krizhevsky et al., 2009) is a dataset of 60,000 32x32 color images selected from 80 million tiny images dataset (Torralba et al., 2008), divided in 10 balanced classes. The original split contains 50,000 images for training and 10,000 images for testing. We applied random 

> ¶Percentile bootstrap is not always reliable depending on the underlying distribution and resampling methods but should generally be good for distributions of P( _A > B_ ) of learning algorithms below 0.95. See (Canty et al., 2006) for a discussion on the topic. 

**Accounting for Variance in Machine Learning Benchmarks** 

_Table 1._ Computational infrastructure for CIFAR10-VGG11 experiments. 

|Hardware/Software|Type/Version|
|---|---|
|CPU|Intel(R) Xeon(R) Gold|
||6148 CPU @ 2.40GHz|
|GPU model|Tesla V100-SXM2-16GB|
|GPU driver|440.33.01|
|OS|CentOS 7.7.1908 Core|
|Python|3.6.3|
|PyTorch|1.2.0|
|CUDA|10.2|



_Table 3._ Search space and default values for the hyperparameters in SST-2/RTE-BERT experiments. 

|Hyperparameters|Default<br>|Space<br>|
|---|---|---|
|learning rate<br>weight decay|2_∗_10<sup>_−_5</sup><br>0_._0|log(10<sup>_−_5</sup>,10<sup>_−_4</sup>)<br>log(10<sup>_−_4</sup>,2_∗_10<sup>_−_3</sup>)|
|std for weights init.|0_._2|log(0_._01,0_._5)|
|_β_1|0.9|-|
|_β_2|0.999|-|
|dropout rate|0_._1|-|
|batch size|32|-|



## **D.2 Glue-SST2 sentiment prediction with BERT** 

_Table 2._ Search space and default values for the hyperparameters in CIFAR10-VGG11 experiments. 

|Hyperparameters|Default|Space|
|---|---|---|
|learning rate|0.03|log(0_._001,0_._3)|
|weight decay|0.002|log(10<sup>_−_6</sup>,10<sup>_−_2</sup>)|
|momentum|0.9|lin(0_._5,0_._99)|
|_γ_ of lr schedule|0.97|lin(0_._96,0_._999)|
|batch-size|128|-|



cropping and random horizontal flipping data augmentations. 

**Bootstrapping** The aggregation of all original training and testing samples are used for the bootstrap. To preserve the balance of the classes, we applied stratified bootstrap. For each class separately, we sampled with replacement 4,000 training samples, 1,000 for validation and 1,000 for testing. As for all tasks, we use out-of-bootstrap to ensure samples cannot be contained in more than one set. 

**Model** We used VGG11 (Simonyan & Zisserman, 2014) with batch-normalization and no dropout. The weights are initialized with Glorot method based on a uniform distribution (Glorot & Bengio, 2010). 

**Search space for hyperparameters** We focused on learning rate, weight decay, momentum and learning rate schedule. Batch-size was omitted to simplify the multi-model training on GPUs, so that memory usage was consistent and predictable across all hyperparameter settings. To ease the definition of the search space for the learning rate schedule, we used exponential decay instead of multi-step decay despite the wide use of the latter with similar tasks and models (Simonyan & Zisserman, 2014; Xie et al., 2019; Mahajan et al., 2018; Liu et al., 2018; He et al., 2016; 2015b). The former only require tuning of _γ_ while the later requires additionally selecting number of steps. Search space for all experiments and default values used for the variance experiments are presented in Table 2. 

**Task** SST2 (Stanford Sentiment Treebank) (Socher et al., 2013) is a binary classification task included in GLUE (Wang et al., 2019). In this task, the input is a sentence from a collection of movie reviews, and the target is the associated sentiment (either positive or negative). The publicly available data contains around 68k entries. 

**Bootstrapping** We maintained the same size ratio between train/validation (i.e., 0.013) when performing the bootstrapping analysis. We performed standard out-ofbootstrap without conserving class balance since the original dataset is not balanced and ratios between classes vary from training and validation set in the original splits. The variable ratios of classes across bootstrap samples generate additional variance in our results, but is representative of the effect of generating a dataset that is not perfectly balanced. 

**Model** We used the BERT (Devlin et al., 2018) implementation provided by the Hugging Face (Wolf et al., 2019) repository. BERT is a Transformer (Vaswani et al., 2017) encoder pre-trained on the self-supervised Masked Language Model task (Devlin et al., 2018). We chose BERT given its importance and influence in the NLP literature. It is worthy to note that the pre-training phase of BERT is also affected by sources of variations. Nevertheless, we didn’t investigate this phase given the amount of time (and resources) required to perform it. Instead, we always start from the (same) pre-trained model image provided by the Hugging Face (Wolf et al., 2019) repository. Indeed, the weight initialization was only applied to the final classifier. The initialization method used is standard Gaussian with 0 _._ 0 mean and standard deviation that depends on the related hyperparameter. 

**Search space of hyperparameters** We ran a small-scale hyperparameter space exploration in order to select the hyperparameter search space to use in our experiments. As such, we decided to include the learning rate, weight decay and the standard deviation for the model parameter initialization (see Table 3). We fixed the dropout probability to the 

**Accounting for Variance in Machine Learning Benchmarks** 

value of 0.1 as in the original BERT architecture. For the same reason, we fixed _β_ 1 = 0 _._ 9 and _β_ 2 = 0 _._ 999. Default values used for the variance experiments are also reported in Table 3. The model has been fine-tuned on SST2 for 3 epochs, with a batch size of 32. Training has been performed with mixed precision. Note that for weight decay we used the default value from the Hugging Face repository (i.e., 0 _._ 0) even if this is outside of the hyperparameter search space. We confirmed that this makes no difference by looking at the results of the small-scale hyperparameter space exploration. 

_Table 4._ Computational infrastructure for PASCAL VOC experiments. 

|Hardware/Software|Type/Version|
|---|---|
|CPU|Intel(R) Xeon(R) Silver|
||4216 CPU @ 2.1GHz|
|GPU model|Tesla V100 Volta 32G|
|GPU driver|440.33.01|
|OS|CentOS 7.7.1908 Core|
|Python|3.6.3|
|PyTorch|1.2.0|
|CUDA|10.2|



## **D.3 Glue-RTE entailment prediction with BERT** 

_Table 5._ Search spaces for PASCAL VOC image segmentation. 

**Task** RTE (Recognizing Textual Entailment) (Bentivogli et al., 2009) is a also a binary classification task included in GLUE (Wang et al., 2019). The task is a collection of text fragment pairs, and the target is to predict if the first text fragment entails the second one. RTE dataset only contains around 2.5k entries. 

**Bootstrapping** In our bootstrapping analysis we maintained the train/validation ratio of 0.1. As for Glue-SST2, we used standard out-of-bootstrap and did not preserve original class ratios. 

**Model & search space of hyperparameters** We used the BERT (Devlin et al., 2018) model for RTE as well, trained in the same way specified in the SST-2 section. In particular, we used the same hyperparameters (see Table 3), same batch size, and we trained in the same mixed-precision environment. The model has been fine-tuned on RTE for 3 epochs. 

## **D.4 PascalVOC image segmentation with ResNet Backbone** 

**Task** The PascalVOC segmentation task (Everingham et al.) entails generating pixel-level segmentations to classify each pixel in an image as one of 20 classes or background. This publicly available dataset contains 2913 images and associated ground truth segmentation labels. The original splits contains 2184 images for training and 729 for validation. Images were normalized and zero-padded to a final size of 512x512. 

**Bootstrapping** We used a train/validation ratio of 0.25 for our bootstrap analysis, generating training sets of 2184 images, validation and test sets of 729 images each. Since multiple classes can appear in a single image, the original dataset was not balanced, we thus used standard out-ofbootstrap for our experiments. 

**Model** We used an FCN-16s (Long et al., 2014) with a ResNet18 backbone (He et al., 2015a) pretrained on Ima- 

|Hyperparameters|Default|Space|
|---|---|---|
|learning rate|0.002|log(10<sup>_−_5</sup>,10<sup>_−_2</sup>)|
|momentum|0.9|lin(0_._50,0_._99)|
|weight decay|0.000001|log(10<sup>_−_8</sup>,10<sup>_−_1</sup>)|
|batch-size|16|-|



geNet (Deng et al., 2009). After exploring several possible backbones, ResNet18 was selected since it could be trained relatively quickly. We use weighted cross entropy, with only predictions within the original image boundary contributing to the loss. The model is optimized using SGD with momentum. 

**Metric** The metric used is the mean Intersection over Union (mIoU) of the twenty classes and the background class. The complement of the mIoU, the mean Jaccard Distance, is the metric minimized in all HPO experiments. 

**Search space of hyperparameters** Certain hyperparmeters, such as the number of kernals, or the total number of layers, are part of the definition of the ResNet18 architecture. As a result, we explored key optimization hyperparameters including: learning rate, momentum, and weight decay. The hyperparameter ranges selected, as well as the default hyperparameters used in the variance experiments, can be found in table 5 and in table **??** , respectively. A batch size of 16 was used for all experiments. 

## **D.5 Major histocompatibility class I-associated peptide binding prediction with shallow MLP** 

**Task** The MLP-MHC is a regression task with the goal of predicting the relative binding affinity for a given peptide and major histocompatibility complex class I (MHC) allele pair. The major histocompatibility complex (MHC) class I proteins are present on the surface of most nucleated cells in jawed vertebrates (Pearson et al., 2016). These proteins bind short peptides that arise from the degradation of intracellular proteins (Pearson et al., 2016). The complex of peptide-MHC molecule is used by immune cells to recog- 

**Accounting for Variance in Machine Learning Benchmarks** 

_Table 6._ Search spaces for the different hyperparameters for the MLP-MHC task 

_Table 8._ Comparison of performance on datasets 

|HC task<br><br>||Model name|Dataset|AUC|PCC|
|---|---|---|---|---|---|
|Hyperparameters<br>Default|Space|NetMHCpan4|HPV|0.53|0.39|
|hidden layer size|lin(20,400)|MHCflurry|HPV|0.58|0.41|
|L2-weight decay|log(0,1)|l<br>MLP-MHC|HPV|0.63|0.31|
|# HPs<br>Hyperparameters<br>1<br>hidden layer size<br>2<br>L2-weight decay|Default Value<br>150<br>0.001|NetMHCpan4<br>MHCflurry<br>MLP-MHC|NetMHC-CVsplits<br>NetMHC-CVsplits<br>NetMHC-CVsplits|0.854<br>0.964*<br>0.861|0.620<br>0.671*<br>0.660|



### _Table 7._ Defaults for MLP-MHC task. 

## models. 

nize healthy cells and eliminate cancerous or infected cells, a mechanism studied in the development of immunotherapy and vaccines (O’Donnell et al., 2018). The peptide binding prediction task is therefore at the base of the search for good vaccine and immunotherapy targets (O’Donnell et al., 2018; Jurtz et al., 2017). 

The input data is the concatenated pairs of sequences: the MHC allele and the peptide sequence. For the MHC alleles, we restricted the sequences to the binding pocket of the peptide, as seen in (Jurtz et al., 2017). The prediction target is a normalized binding affinity score, as described in (Jurtz et al., 2017; O’Donnell et al., 2018). 

**Datasets and sequence encoding** While both _MHCflurry_ and _NetMHCpan4_ models use a BLOSUM62 encoding (Henikoff & Henikoff, 1992) for the amino acids, in we chose to instead encode the amino acids as one-hot as described in (Nielsen et al., 2007). 

The _NetMHCpan4_ model is trained on a manually filtered dataset from the immune epitope database (Vita et al., 2019; Jurtz et al., 2017) that has been split into five folds used for cross-validation, available on the author’s website (Jurtz et al., 2017). 

In contrast, the _MHCflurry_ model is trained on a custom multi-source dataset (available from Mendeley data and the (O’Donnell et al., 2018) publication cite) and validated/tested on two external datasets from (Pearson et al., 2016) and an HPV peptide dataset available at the same website as above. 

**Bootstrapping** We have three different sets for training, validating and testing. We thus performed bootstrapping separately on each set for every training and evaluation. 

**Model** The model is a shallow MLP with one hidden layer from _sklearn_ . We used the default setting for the nonlinearity _relu_ and weight initialization strategy ((Glorot & Bengio, 2010)). The following table (Table 9) offers some comparison points between our model and the _NetMHCpan4_ (Jurtz et al., 2017) and _MHCflurry_ (O’Donnell et al., 2018) 

While the _MHCflurry_ model (O’Donnell et al., 2018) train only no the peptide sequences and uses ensembling to perform its predictions, training multiple models for each MHC allele, the _NetMHCpan4_ model (Jurtz et al., 2017) uses the allele sequence as input and trains one single model. 

We chose to retain the strategy proposed by the _NetMHCpan4_ model, where a single model is trained for all alleles (Jurtz et al., 2017). As a reference, MHCflurry uses ensembling to perform predictions; indeed, the authors report that for each MHC allele, an ensemble of 8-16 are selected from the 320 that were trained (O’Donnell et al., 2018). 

**Search space of hyperparameters** For the hyperparameter search, we selected hidden layer sizes between 20 and 400 (Table 6), to engulph a range slightly larger than the ones described by both (Jurtz et al., 2017; O’Donnell et al., 2018). The second hyperparameter that was explored was the L2 regularisation parameter, for which a log-uniform range between 0 and 1 was explored. 

**Comparison of performance** We would like to state the goal of the present study was not to establish new state of the art (SOTA) on the MHC-peptide binding prediction task. However, we still report that when comparing the performance of our model to those of _NetMHCpan4_ and _MHCflurry_ we found the performance of our model comparable. Briefly, for the results in Table 9, we used the existing pre-trained _NetMHCpan4_ and _MHCflurry_ tools to predict the binding affinity of both datasets: the previously described HPV external test data (HPV) from (O’Donnell et al., 2018) and the cross-validation test datasets from (Jurtz et al., 2017) (NetMHC-CVsplits). 

We would like to point out that since the _MHCflurry_ model was published later than the _NetMHCpan4_ one, there is a high chance that the dataset from the cross-validation splits (NetMHC-CVsplits) may be contained in the dataset used to train the existing _MHCflurry_ tool. The proper way to compare performances would be to re-train the _MHCflurry_ model on each fold and test susequently its performance; however, since our goal is not to reach new SOTA on this task, we leave this experiment to be performed at a later 

**Accounting for Variance in Machine Learning Benchmarks** 

_Table 9._ Comparison of models for the MLP-MHC task 

|Model name|Inputs|Model design|Dataset|Sequence encoding|
|---|---|---|---|---|
|NetMHCpan4|allele+peptide|shallow MLP|custom CV split(Vita et al.,2019)|BLOSUM62|
|MHCflurry|peptide|ensemble of shallow MLPs|(O’Donnell et al.,2018)|BLOSUM62|
|MLP-MHC|allele+peptide|shallow MLP|same as (O’Donnell et al.,2018)|Sparse|



_Table 10._ Computational infrastructure for MLP-MHC experi- 

|ments.<br>Hardware/Software|Type/Version|
|---|---|
|CPU|Intel(R) Xeon(R) CPU E5-2640 v4|
||320 CPU @ 2.40GHz|
|OS|CentOS 7.7.1908 Core|
|Python|3.6.8|
|sklearn|0.22.2.post1|
|BLAS|3.4.2|



time. 

This would result in a likely overestimation of the performance of _MHCflurry_ on this dataset, which we noted with the _∗_ sign in Table 9. 

A more in-depth study is necessary to compare in a more through way this performance with respect to the differences in model design, dataset encoding and other factors. 

# **E HYPERPARAMETER OPTIMIZATION ALGORITHMS** 

## **E.1 Grid Search** 

Let _ai_ , _bi_ and _n_ be the hyperparameters of the grid search, where _ai_ and _bi_ are vectors of minima and maxima for each dimension of the search space, and _n_ is the number of values per dimension. We define ∆ _i_ as the interval between each value on dimension _i_ . A point on the grid is defined by _pij_ = _ai_ + ∆ _i_ ( _j −_ 1). Grid search is simply the evaluation of _r_ ( _λ_ ) from Equation 2 on all possible combinations of values _pij_ . 

## **E.2 Noisy Grid Search** 

Grid search is a fully deterministic algorithm. Yet, it is highly sensitive to the design of the grid. To provide a variance estimate of similar choices of the grid and to be able to distinguish lucky grid, we consider a noisy version of grid search. 

For the noisy grid search, we replace _ai_ by _a_ ˜ _i ∼ U_ ( _ai −_ <u>∆2</u> _<u>i</u>_<sup>_, ai_+</sup><sup><u>∆</u></sup> 2<sup>_<u>i</u>_) and similarly for</sup><sup>_bi_.˜∆</sup><sup>_i_and</sup> _p_<sup>˜</sup> _ij_ then follows from ˜ _ai_ and<sup>˜</sup> _bi_ . In expectation, noisy grid search will cover the same grid as grid search, as proven below. 



This provides us a variance estimate of grid search that we can compare against non-deterministic hyperparameter optimization algorithms. 

## **E.3 Random Search** 

The search space of random search will be increased by _±_<sup><u>∆</u></sup> 2<sup>_<u>i</u>_as defined for the noisy grid search to ensure that they</sup> both cover the same search space. For all hyperparameters, the values are sampled from a uniform _pi ∼ U_ ( _ai −_<sup><u>∆</u></sup> 2<sup>_<u>i</u>, bi_+</sup> <u>∆2</u> _<u>i</u>_<sup>).For learning rate and weight decay, values are sampled</sup> uniformly in the logarithmic space. 

# **F HYPERPARAMETER OPTIMIZATION RESULTS** 

Figure F.2 presents the optimization curves of the hyperparameter optimization executions in Section 2.2. 

# **G NORMALITY OF PERFORMANCE DISTRIBUTIONS IN THE CASE STUDIES** 

Figure G.3 presents the Shapiro-Wilk test of normality on all our results on sources of variations. 

# **H RANDOMIZING MORE SOURCES OF VARIANCE INCREASE THE QUALITY OF THE ESTIMATOR** 

Figure 5 only presented the Glue-RTE and CIFAR10 tasks. We provide here a complete picture of the standard deviation 

**Accounting for Variance in Machine Learning Benchmarks** 



<!-- Start of picture text -->
Validation Test<br>Error-rate Error-rate<br>0.35<br>0.30 Glue-RTE<br>BERT<br>0.25<br>0.05<br>Glue-SST2<br>BERT<br>0.04<br>0.225<br>MHC<br>0.200<br>MLP<br>0.175<br>0.475<br>PascalVOC<br>ResNet<br>0.450<br>0.10<br>CIFAR10<br>VGG11<br>0.08<br>0 100 200 0 100 200<br>HPO iterations HPO iterations<br>bayesopt noisy grid search random search<br>regret<br><!-- End of picture text -->

_Figure F.2._ **Optimization curves of hyperparameter optimization executions** Each row presents the result for a different task. Left column are results on validation set, the one hyperparameters were optimized on. Right column are results on the test sets. Hyperparameter optimization methods are Bayesian Optimization, Noisy Grid Search (See Section E.2), and Random Search. The y- axis are the best objectives found until an iteration _i_ , on a different scale for each task. Left and right plots share the same scale on y-axis, so that we can easily observe whether validation error-rate corresponds to test error-rate. The bold lines are averages and the size of lighter colored areas represents the standard deviations. They are computed based on 20 independent executions for each algorithms, during which only the seed of the hyperparameter optimization is randomized. For more details on the experiments see Section 2.2. Two striking results emerge from these graphs. 1) The typical search spaces are well optimized by all algorithms, and in some cases there is even signs of slight over-fitting (on BERT tasks). 2) The standard deviation stabilizes early, before 50 iterations in most cases. These results suggests that larger budgets for hyperparameter optimization would not reduce the variability of the results in similar search spaces. This is likely not the case however for more complex search spaces such as those observed in the neural architecture search literature. 



<!-- Start of picture text -->
Bootstrap 58.63 78.88 16.81 83.58 91.13<br>Weights init 60.50 19.41 0.10 44.38 89.69<br>Data order 68.09 61.41 0.59 10.31 Kernel DensityEstimator<br>Dropout 2.48 28.73<br>Data augment 43.53 Test Performances p-value of<br>Shapiro-Wilk test<br>Num. Noise 16.75<br>Altogether 43.27 25.60 0.09 97.76 69.71<br>CIFAR10 PascalVOC Glue-SST2 Glue-RTE MHC<br>VGG11 ResNet BERT BERT MLP<br><!-- End of picture text -->

_Figure G.3._ **Performance distributions conditional to different sources of variations.** Each row is a different source of variation. For each source, all other sources are kept fix when training and evaluating models. The last row presents the distributions when all the sources of variation are randomized altogether. Each column is the results for the different tasks. We can see that except for Glue-SST2 BERT, all case studies have distributions of performances very close to normal. In the case of Glue-SST2 BERT, we note that the size of the test set is so small that it discretizes the possible performances. The distribution is nevertheless roughly symmetrical and thus amenable to many statistical tests. 

of the different estimators in Figure H.4. We further present a decomposition of the mean-squared-error in Figure H.5 to help understand why accounting for more sources of variations improves the mean-squared-error of the biased estimators. 

# **I ANALYSIS OF ROBUSTNESS OF COMPARISON METHODS** 

In addition to simulations described in Section 4.2, we executed experiments in which we varied the sample size and the threshold _γ_ . To select the threshold of the average, we converted _γ_ into the equivalent performance difference ( _δ_ = Φ<sup>_−_1</sup> ( _γ_ ) _σ_ ). Results are presented in Figure I.6 

**Accounting for Variance in Machine Learning Benchmarks** 



<!-- Start of picture text -->
FixHOptEst(k, Init) FixHOptEst(k, All)<br>FixHOptEst(k, Data) IdealEst(k) IdealEst(1)<br>FixHOptEst(100, Init)<br>0.03 FixHOptEst(100, Data)<br>Glue-RTE FixHOptEst(100, All)<br>0.02 BERT IdealEst(100) Acc IoU Acc Acc AUC<br>0.01<br>Bias( k , )<br>IdealEst(1)<br>0.0075 FixHOptEst(100, Init)<br>0.0050 Glue-SST2 FixHOptEst(100, Data)<br>BERT<br>0.0025 FixHOptEst(100, All)<br>IdealEst(100)<br>0.03 Var( k )<br>IdealEst(1)<br>0.02 MHC<br>MLP FixHOptEst(100, Init)<br>0.01 FixHOptEst(100, Data)<br>FixHOptEst(100, All)<br>IdealEst(100)<br>0.015<br>= corr(Rei, Rej)<br>0.010 PascalVOC<br>ResNet IdealEst(1)<br>0.005 FixHOptEst(100, Init)<br>FixHOptEst(100, Data)<br>FixHOptEst(100, All)<br>0.004 IdealEst(100)<br>0.002 CIFAR10VGG11 MSE( (k) , )<br>0 20 40 60 80 100<br>Figure H.5. Decomposition of the Mean-Squared-Error for<br>Number of samples for the estimator (k)<br>different estimators of R ˆ P . On each sub-figure from top to<br>Glue-RTEGlue-SST2MHC PascalVOCCIFAR10<br>BERT BERT MLP ResNet VGG11<br>(Acc)<br>(Acc)<br>(AUC)<br>of estimators<br>Standard deviation<br>(IoU)<br>(Acc)<br><!-- End of picture text -->

_Figure H.5._ **Decomposition of the Mean-Squared-Error for different estimators of** _R_<sup>ˆ</sup> _P_ **.** On each sub-figure from top to bottom, 1) bias between the estimator and the expected empirical risk Bias( _µ_ ( _k_ ) _, µ_ ), 2) variance of the estimator Var( _µ_ ( _k_ )), 3) correlation between performances measures _R_<sup>ˆ</sup> _e_ as presented in Equation 7 and 4) the mean-squared-error of the estimator MSE( _µ_ ( _k_ ) _, µ_ ). For each sub-figure, each row is a different estimators, with IdealEst(k=1) as a comparison point. The experimental procedure to compute these statistics are described in section subsection 3.3. Without any surprise the IdealEst(100, All) minimizes the mean-squared-error so well that it looks close to 0 on the figure compared to the other estimators. Among the other estimators, the mean-squared-error is reduced most significantly by FixedHOptEst(100, All) on all tasks. If we look at the decomposition of the mean-squared-error, i.e., the bias and the variance, we see on first sub-figure that the bias is stable across all biased estimators on all tasks, while on second sub-figure the variance varies widely. It is thus the reduced variance of the biased estimators that leads to improved mean-squared-error. This is a counter-intuitive result because the estimator with lowest variance are these accounting for more sources of variations. The intuition is thus that they should have more variance, not less. We derived the variance of the biased estimators in Equation 7 which highlighted that the correlation among performances _R_<sup>ˆ</sup> _e_ can increase the variance of the biased estimators. We can see in the third sub-figure that this correlation drastically drops when accounting for more sources of variances. The mean-squared-error, in other words the quality of the estimators, is thus significantly improved by decorrelating the performance measures. 

_Figure H.4._ **Standard error of biased and ideal estimators with** _k_ **samples.** Each plot represents the standard error of the different tasks described in Section 2.2. On x axis, the number of samples used by the estimators to compute the average performance. On y axis, the standard deviation of the estimations, in terms of task objective; Classification accuracy (Acc), Intersection over Union (IoU), Area Under the Curve (AUC). Uncertainty represented in light color is computed analytically as the approximate standard deviation of the standard deviation of a normal distribution computed on _k_ samples. For all case studies, **accounting for more sources of variation reduces or keeps constant the standard error of** ˆ _µ_ ( _k_ ) **.** In all case studies, only accounting for weights initialization, FixHOptEst(k, Init), is by far the worst estimator. Comparatively, FixHOptEst(k, All) provides a systematic improvement towards IdealEst(k) for no additional computational cost compared to FixHOptEst(k, Init). **Ignoring variance from** HOpt **is harmful for a good estimation of** _R_<sup>ˆ</sup> _P_ **.** The MHC task with MLP is the only one for which FixHOptEst(k, All) matches IdealEST(k, All). We suspect this may be explained by the relatively small standard deviation due to hyperparameter optimization observed in Figure 1. FixHOptEst(k, All) would have thus captured most of the variability in the learning pipeline. 

**Accounting for Variance in Machine Learning Benchmarks** 



<!-- Start of picture text -->
Average Prob of improvement T-test<br>P(A>B) = 0.5 P(A>B) = 0.6 P(A>B) = 0.7 P(A>B) = 0.8<br>100<br>0<br>0 50 100 0 50 100 0 50 100 0 50 100<br>Sample Size Sample Size Sample Size Sample Size<br>100<br>0<br>0.6 0.7 0.8 0.9 0.6 0.7 0.8 0.9 0.6 0.7 0.8 0.9 0.6 0.7 0.8 0.9<br>Rate of Detections<br>Rate of Detections<br><!-- End of picture text -->

_Figure I.6._ **Analysis of the robustness of comparison methods.** On the first row, rate of detections of comparison methods in function of the sample size. On the second row, rate of detections of comparison methods in function of the threshold _γ_ . Each column are simulations with different true simulated probability of of a learning algorithm _A_ to outperform another algorithm _B_ across random fluctuations (ex: random data splits). 

