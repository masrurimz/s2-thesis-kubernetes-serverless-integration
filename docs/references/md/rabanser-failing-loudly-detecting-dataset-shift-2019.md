---
# --- bibliographic record ---
entry_type: misc
title: "Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift"
authors:
  - "Stephan Rabanser"
  - "Stephan Günnemann"
  - "Zachary C. Lipton"
year: 2018
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "1810.11953"
url: "https://arxiv.org/abs/1810.11953"

# --- archive record ---
source_pdf: rabanser-failing-loudly-detecting-dataset-shift-2019.pdf
source_sha256: 6177eb9c5ab7fa19f29816d59e4cb32219b61d4053c780647ace1bf4e9995218
pdf_pages: 38
converted: 2026-09-13
record_source: arxiv
key_insight: "Deployed models fail silently under dataset shift; two-sample tests and domain classifiers detect it, and no single detector dominates. Grounds the missing input-distribution monitor."
first_page: "Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift Stephan Rabanser∗ AWS AI Labs rabans@amazon.com Stephan G¨unnemann Technical University of Munich guennemann@in.tum.de Zachary"
---
# **Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift** 

**Stephan Rabanser**<sup>_∗_</sup> **Stephan G¨unnemann Zachary C. Lipton** AWS AI Labs Technical University of Munich Carnegie Mellon University `rabans@amazon.com guennemann@in.tum.de zlipton@cmu.edu` 

## **Abstract** 

We might hope that when faced with unexpected inputs, well-designed software systems would fire off warnings. Machine learning (ML) systems, however, which depend strongly on properties of their inputs (e.g. the i.i.d. assumption), tend to fail silently. This paper explores the problem of building ML systems that fail loudly, investigating methods for detecting dataset shift, identifying exemplars that most typify the shift, and quantifying shift malignancy. We focus on several datasets and various perturbations to both covariates and label distributions with varying magnitudes and fractions of data affected. Interestingly, we show that across the dataset shifts that we explore, a two-sample-testing-based approach, using pre-trained classifiers for dimensionality reduction, performs best. Moreover, we demonstrate that domain-discriminating approaches tend to be helpful for characterizing shifts qualitatively and determining if they are harmful. 

## **1 Introduction** 

Software systems employing deep neural networks are now applied widely in industry, powering the vision systems in social networks [47] and self-driving cars [5], providing assistance to radiologists [24], underpinning recommendation engines used by online platforms [9, 12], enabling the bestperforming commercial speech recognition software [14, 21], and automating translation between languages [50]. In each of these systems, predictive models are integrated into conventional humaninteracting software systems, leveraging their predictions to drive consequential decisions. 

The reliable functioning of software depends crucially on tests. Many classic software bugs can be caught when software is compiled, e.g. that a function receives input of the wrong type, while other problems are detected only at run-time, triggering warnings or exceptions. In the worst case, if the errors are never caught, software may behave incorrectly without alerting anyone to the problem. 

Unfortunately, software systems based on machine learning are notoriously hard to test and maintain [42]. Despite their power, modern machine learning models are brittle. Seemingly subtle changes in the data distribution can destroy the performance of otherwise state-of-the-art classifiers, a phenomenon exemplified by adversarial examples [51, 57]. When decisions are made under uncertainty, even shifts in the label distribution can significantly compromise accuracy [29, 56]. Unfortunately, in practice, ML pipelines rarely inspect incoming data for signs of distribution shift. Moreover, best practices for detecting shift in high-dimensional real-world data have not yet been established<sup>2</sup> . 

In this paper, we investigate methods for detecting and characterizing distribution shift, with the hope of removing a critical stumbling block obstructing the safe and responsible deployment of machine learning in high-stakes applications. Faced with distribution shift, our goals are three-fold: 

> _∗_ Work done while a Visiting Research Scholar at Carnegie Mellon University. 

2TensorFlow’s data validation tools compare only summary statistics of source vs target data: `https://tensorflow.org/tfx/data_validation/get_started#checking_data_skew_and_drift` 

33rd Conference on Neural Information Processing Systems (NeurIPS 2019), Vancouver, Canada. 



<!-- Start of picture text -->
x sourcesource Two-Sample Test(s) Combined Test Statistic & Shift Detection<br>Dimensionality<br>Reduction<br>x target<br>… … … …<br>… …<br>… … … …<br><!-- End of picture text -->

Figure 1: Our pipeline for detecting dataset shift. Source and target data is fed through a dimensionality reduction process and subsequently analyzed via statistical hypothesis testing. We consider various choices for how to represent the data and how to perform two-sample tests. 

(i) detect when distribution shift occurs from as few examples as possible; (ii) characterize the shift, e.g. by identifying those samples from the test set that appear over-represented in the target data; and (iii) provide some guidance on whether the shift is harmful or not. As part of this paper we principally focus on goal (i) and explore preliminary approaches to (ii) and (iii). 

We investigate shift detection through the lens of statistical two-sample testing. We wish to test the equivalence of the _source_ distribution _p_ (from which training data is sampled) and _target_ distribution _q_ (from which real-world data is sampled). For simple univariate distributions, such hypothesis testing is a mature science. However, best practices for two sample tests with high-dimensional (e.g. image) data remain an open question. While off-the-shelf methods for kernel-based multivariate two-sample tests are appealing, they scale badly with dataset size and their statistical power is known to decay badly with high ambient dimension [37]. 

Recently, Lipton et al. [29] presented results for a method called _black box shift detection (BBSD)_ , showing that if one possesses an off-the-shelf label classifier _f_ with an invertible confusion matrix, then detecting that the source distribution _p_ differs from the target distribution _q_ requires only detecting that _p_ ( _f_ ( **_x_** )) _̸_ = _q_ ( _f_ ( **_x_** )). Building on their idea of combining black-box dimensionality reduction with subsequent two-sample testing, we explore a range of dimensionality-reduction techniques and compare them under a wide variety of shifts (Figure 1 illustrates our general framework). We show (empirically) that BBSD works surprisingly well under a broad set of shifts, even when the label shift assumption is not met. Furthermore, we provide an empirical analysis on the performance of domain-discriminating classifier-based approaches (i.e. classifiers explicitly trained to discriminate between source and target samples), which has so far not been characterized for the complex high-dimensional data distributions on which modern machine learning is routinely deployed. 

## **2 Related work** 

Given just one example from the test data, our problem simplifies to _anomaly detection_ , surveyed thoroughly by Chandola et al. [8] and Markou and Singh [33]. Popular approaches to anomaly detection include density estimation [6], margin-based approaches such as the one-class SVM [40], and the tree-based isolation forest method due to [30]. Recently, also GANs have been explored for this task [39]. Given simple streams of data arriving in a time-dependent fashion where the signal is piece-wise stationary with abrupt changes, this is the classic time series problem of change point detection, surveyed comprehensively by Truong et al. [52]. An extensive literature addresses dataset shift in the context of domain adaptation. Owing to the impossibility of correcting for shift absent assumptions [3], these papers often assume either covariate shift _q_ ( **_x_** _, y_ ) = _q_ ( **_x_** ) _p_ ( _y|_ **_x_** ) [15, 45, 49] or label shift _q_ ( **_x_** _, y_ ) = _q_ ( _y_ ) _p_ ( **_x_** _|y_ ) [7, 29, 38, 48, 56]. Sch¨olkopf et al. [41] provides a unifying view of these shifts, associating assumed invariances with the corresponding causal assumptions. 

Several recent papers have proposed outlier detection mechanisms dubbing the task _out-ofdistribution (OOD) sample detection_ . Hendrycks and Gimpel [19] proposes to threshold the maximum softmax entry of a neural network classifier which already contains a relevant signal. Liang et al. [28] and Lee et al. [26] extend this idea by either adding temperature scaling and adversariallike perturbations on the input or by explicitly adapting the loss to aid OOD detection. Choi and Jang [10] and Shalev et al. [44] employ model ensembling to further improve detection reliability. Alemi et al. [2] motivate use of the variational information bottleneck. Hendrycks et al. [20] expose the model to OOD samples, exploring heuristics for discriminating between in-distribution and out-of-distribution samples. Shafaei et al. [43] survey numerous OOD detection techniques. 

2 

## **3 Shift Detection Techniques** 

Given labeled data _{_ ( **_x_** 1 _, y_ 1) _, ...,_ ( **_x_** _n, yn_ ) _} ∼ p_ and unlabeled data _{_ **_x_** 1<sup>_′, ...,_</sup><sup>**_x_**</sup><sup>_′_</sup> _m_<sup>_}∼q_,ourtaskis</sup> to determine whether _p_ ( **_x_** ) equals _q_ ( **_x_**<sup>_′_</sup> ). Formally, _H_ 0 : _p_ ( **_x_** ) = _q_ ( **_x_**<sup>_′_</sup> ) vs _HA_ : _p_ ( **_x_** ) _̸_ = _q_ ( **_x_**<sup>_′_</sup> ). Chiefly, we explore the following design considerations: (i) what **representation** to run the test on; (ii) which **two-sample test** to run; (iii) when the representation is multidimensional; whether to run **multivariate or multiple univariate two-sample tests** ; and (iv) **how to combine** their results. 

### **3.1 Dimensionality Reduction** 

We now introduce the multiple dimensionality reduction (DR) techniques that we compare visa-vis their effectiveness in shift detection (in concert with two-sample testing). Note that absent assumptions on the data, these mappings, which reduce the data dimensionality from _D_ to _K_ (with _K ≪ D_ ), are in general surjective, with many inputs mapping to the same output. Thus, it is trivial to construct pathological cases where the distribution of inputs shifts while the distribution of lowdimensional latent representations remains fixed, yielding false negatives. However, we speculate that in a non-adversarial setting, such shifts may be exceedingly unlikely. Thus our approach is (i) empirically motivated; and (ii) not put forth as a defense against worst-case adversarial attacks. 

**No Reduction (** **_NoRed_ )** : To justify the use of any DR technique, our default baseline is to run tests on the original raw features. 

**Principal Components Analysis (** **_PCA_ )** : Principal components analysis is a standard tool that finds an optimal orthogonal transformation matrix **_R_** such that points are linearly uncorrelated after transformation. This transformation is learned in such a way that the first principal component accounts for as much of the variability in the dataset as possible, and that each succeeding principal component captures as much of the remaining variance as possible subject to the constraint that it be orthogonal to the preceding components. Formally, we wish to learn **_R_** given **_X_** under the mentioned constraints such that **_X_**<sup>ˆ</sup> = **_XR_** yields a more compact data representation. 

**Sparse Random Projection (** **_SRP_ )** : Since computing the optimal transformation might be expensive in high dimensions, random projections are a popular DR technique which trade a controlled amount of accuracy for faster processing times. Specifically, we make use of sparse random projections, a more memory- and computationally-efficient modification of standard Gaussian random projections. Formally, we generate a random projection matrix **_R_** and use it to reduce the dimensionality of a given data matrix **_X_** , such that **_X_**<sup>ˆ</sup> = **_XR_** . The elements of **_R_** are generated using the following rule set [1, 27]: 



**Autoencoders (** **_TAE_ and** **_UAE_ )** : We compare the above-mentioned linear models to non-linear reduced-dimension representations using both _trained_ (TAE) and _untrained_ autoencoders (UAE). Formally, an autoencoder consists of an encoder function _φ_ : _X →H_ and a decoder function _ψ_ : _H →X_ where the latent space _H_ has lower dimensionality than the input space _X_ . As part of the training process, both the encoding function _φ_ and the decoding function _ψ_ are learned jointly to reduce the reconstruction loss: _φ, ψ_ = arg min _φ,ψ ∥_ **_X_** _−_ ( _ψ ◦ φ_ ) **_X_** _∥_<sup>2</sup> . 

**Label Classifiers (** **_BBSDs_** _◁_ **and** **_BBSDh_** _▷_ **)** : Motivated by recent results achieved by black box shift detection (BBSD) [29], we also propose to use the outputs of a (deep network) _label classifier_ trained on source data as our dimensionality-reduced representation. We explore variants using either the softmax outputs (BBSDs) or the hard-thresholded predictions (BBSDh) for subsequent two-sample testing. Since both variants provide differently sized output (with BBSDs providing an entire softmax vector and BBSDh providing a one-dimensional class prediction), different statistical tests are carried out on these representations. 

**Domain Classifier (** **_Classif_** _×_ **)** : Here, we attempt to detect shift by explicitly training a _domain classifier_ to discriminate between data from source and target domains. To this end, we partition both the source data and target data into two halves, using the first to train a domain classifier to distinguish source (class 0) from target (class 1) data. We then apply this model to the second 

3 

half and subsequently conduct a significance test to determine if the classifier’s performance is statistically different from random chance. 

### **3.2 Statistical Hypothesis Testing** 

The DR techniques each yield a representation, either uni- or multi-dimensional, and either continuous or discrete, depending on the method. The next step is to choose a suitable statistical hypothesis test for each of these representations. 

**Multivariate Kernel Two-Sample Tests: Maximum Mean Discrepancy (MMD)** : For all multidimensional representations, we evaluate the Maximum Mean Discrepancy [16], a popular kernelbased technique for multivariate two-sample testing. MMD allows us to distinguish between two probability distributions _p_ and _q_ based on the mean embeddings **_µ_** _p_ and **_µ_** _q_ of the distributions in a reproducing kernel Hilbert space _F_ , formally 



Given samples from both distributions, we can calculate an unbiased estimate of the squared MMD statistic as follows 



where we use a squared exponential kernel _κ_ ( **_x_** _,_ **˜** **_x_** ) = _e_<sup>_−_</sup> _σ_<sup><u>1</u></sup><sup>_∥_</sup><sup>**_x_**</sup><sup>_−_</sup><sup>**_x_˜**</sup><sup>_∥_2</sup> and set _σ_ to the median distance between points in the aggregate sample over _p_ and _q_ [16]. A _p_ -value can then be obtained by carrying out a permutation test on the resulting kernel matrix. 

**Multiple Univariate Testing: Kolmogorov-Smirnov (KS) Test + Bonferroni Correction** : As a simple baseline alternative to MMD, we consider the approach consisting of testing each of the _K_ dimensions separately (instead testing over all dimensions jointly). Here, for continuous data, we adopt the Kolmogorov-Smirnov (KS) test, a non-parametric test whose statistic is calculated by computing the largest difference _Z_ of the cumulative density functions (CDFs) over all values **_z_** as follows 



where _Fp_ and _Fq_ are the empirical CDFs of the source and target data, respectively. Under the null hypothesis, _Z_ follows the Kolmogorov distribution. 

Since we carry out a KS test on each of the _K_ components, we must subsequently combine the _p_ - values from each test, raising the issue of multiple hypothesis testing. As we cannot make strong assumptions about the (in)dependence among the tests, we rely on a conservative aggregation method, notably the Bonferroni correction [4], which rejects the null hypothesis if the minimum _p_ -value among all tests is less than _α/K_ (where _α_ is the significance level of the test). While several less conservative aggregations methods have been proposed [18, 32, 46, 53, 55], they typically require assumptions on the dependencies among the tests. 

**Categorical Testing: Chi-Squared Test** : For the hard-thresholded label classifier (BBSDh), we employ Pearson’s chi-squared test, a parametric tests designed to evaluate whether the frequency distribution of certain events observed in a sample is consistent with a particular theoretical distribution. Specifically, we use a test of homogeneity between the class distributions (expressed in a contingency table) of source and target data. The testing problem can be formalized as follows: Given a contingency table with 2 rows (one for absolute source and one for absolute target class frequencies) and _C_ columns (one for each of the _C_ -many classes) containing observed counts _Oij_ , the expected frequency under the independence hypothesis for a particular cell is _Eij_ = _N_ sum _pi•p•j_ with _N_ sum being the sum of all cells in the table, _pi•_ = _N_<sup>_<u>O</u>_</sup> sum<sup>_<u>i•</u>_= �</sup> _j_<sup>_C_</sup> =1 _NO_ sum _ij_<sup>being the fraction of row</sup> totals, and _p•j_ = _N_<sup>_O_</sup> sum<sup>_•j_=�</sup> _i_<sup>2</sup> =1 _NO_ sum _ij_<sup>being the fraction of column totals.The relevant test statistic</sup> _X_<sup>2</sup> can be computed as 



which, under the null hypothesis, follows a chi-squared distribution with _C −_ 1 degrees of freedom: _X_<sup>2</sup> _∼ χ_<sup>2</sup> _C−_ 1<sup>.</sup> 

4 

**Binomial Testing** : For the domain classifier, we simply compare its accuracy (acc) on held-out data to random chance via a binomial test. Formally, we set up a testing problem _H_ 0 : acc = 0 _._ 5 vs _HA_ : acc _̸_ = 0 _._ 5. Under the null hypothesis, the accuracy of the classifier follows a binomial distribution: acc _∼_ Bin( _N_ hold _,_ 0 _._ 5), where _N_ hold corresponds to the number of held-out samples. 

### **3.3 Obtaining Most Anomalous Samples** 

As our detection framework does not detect outliers but rather aims at capturing top-level shift dynamics, it is not possible for us to decide whether any given sample is in- or out-of-distribution. However, we can still provide an indication of what typical samples from the shifted distribution look like by harnessing domain assignments from the domain classifier. Specifically, we can identify the exemplars which the classifier was most confident in assigning to the target domain. Since the domain classifier assigns class-assignment confidence scores to each incoming sample via the softmax-layer at its output, it is easy to create a ranking of samples that are most confidently believed to come from the target domain (or, alternatively, from the source domain). Hence, whenever the binomial test signals a statistically significant accuracy deviation from chance, we can use use the domain classifier to obtain the most anomalous samples and present them to the user. 

In contrast to the domain classifier, the other shift detectors do not base their shift detection potential on explicitly deciding which domain a single sample belongs to, instead comparing entire distributions against each other. While we did explore initial ideas on identifying samples which if removed would lead to a large increase in the overall _p_ -value, the results we obtained were unremarkable. 

### **3.4 Determining the Malignancy of a Shift** 

Theoretically, absent further assumptions, distribution shifts can cause arbitrarily severe degradation in performance. However, in practice distributions shift constantly, and often these changes are benign. Practitioners should therefore be interested in distinguishing malignant shifts that damage predictive performance from benign shifts that negligibly impact performance. Although prediction quality can be assessed easily on source data on which the black-box model _f_ was trained, we are not able compute the target error directly without labels. 

We therefore explore a heuristic method for approximating the target performance by making use of the domain classifier’s class assignments as follows: Given access to a labeling function that can correctly label samples, we can feed in those examples predicted by the domain classifier as likely to come from the target domain. We can then compare these (true) labels to the labels returned by the black box model _f_ by feeding it the same anomalous samples. If our model is inaccurate on these examples (where the exact threshold can be user-specified to account for varying sensitivities to accuracy drops), then we ought to be concerned that the shift is malignant. Put simply, we suggest evaluating the accuracy of our models on precisely those examples which are most confidently assigned to the target domain. 

## **4 Experiments** 

Our main experiments were carried out on the MNIST ( _N_ tr = 50000; _N_ val = 10000; _N_ te = 10000; _D_ = 28 _×_ 28 _×_ 1; _C_ = 10 classes) [25] and CIFAR-10 ( _N_ tr = 40000; _N_ val = 10000; _N_ te = 10000; _D_ = 32 _×_ 32 _×_ 3; _C_ = 10 classes) [23] image datasets. For the autoencoder (UAE & TAE) experiments, we employ a convolutional architecture with 3 convolutional layers and 1 fullyconnected layer. For both the label and the domain classifier we use a ResNet-18 [17]. We train all networks (TAE, BBSDs, BBSDh, Classif) using stochastic gradient descent with momentum in batches of 128 examples over 200 epochs with early stopping. 

For PCA, SRP, UAE, and TAE, we reduce dimensionality to _K_ = 32 latent dimensions, which for PCA explains roughly 80% of the variance in the CIFAR-10 dataset. The label classifier BBSDs reduces dimensionality to the number of classes _C_ . Both the hard label classifier BBSDh and the domain classifier Classif reduce dimensionality to a one-dimensional class prediction, where BBSDh predicts label assignments and Classif predicts domain assignments. 

To challenge our detection methods, we simulate a variety of shifts, affecting both the covariates and the label proportions. For all shifts, we evaluate the various methods’ abilities to detect shift at 

5 

a significance level of _α_ = 0 _._ 05. We also include the no-shift case to check against false positives. We randomly split all of the data into training, validation, and test sets according to the indicated proportions _N_ tr, _N_ val, and _N_ te and then apply a particular shift to the test set only. In order to qualitatively quantify the robustness of our findings, shift detection performance is averaged over a total of 5 random splits, which ensures that we apply the same type of shift to different subsets of the data. The selected training data used to fit the DR methods is kept constant across experiments with only the splits between validation and test changing across the random runs. Note that DR methods are learned using training data, while shift detection is being performed on dimensionality-reduced representations of the validation and the test set. We evaluate the models with various amounts of samples from the test set _s ∈{_ 10 _,_ 20 _,_ 50 _,_ 100 _,_ 200 _,_ 500 _,_ 1000 _,_ 10000 _}_ . Because of the unfavorable dependence of kernel methods on the dataset size, we run these methods only up until 1000 target samples have been acquired. 

For each shift type (as appropriate) we explored three levels of shift intensity (e.g. the magnitude of added noise) and various percentages of affected data _δ ∈{_ 0 _._ 1 _,_ 0 _._ 5 _,_ 1 _._ 0 _}_ . Specifically, we explore the following types of shifts: 

(a) **Adversarial (** **_adv_ )** : We turn a fraction _δ_ of samples into adversarial samples via FGSM [13]; 

(b) **Knock-out (** **_ko_ )** : We remove a fraction _δ_ of samples from class 0, creating class imbalance [29]; 

(c) **Gaussian noise (** **_gn_ )** : We corrupt covariates of a fraction _δ_ of test set samples by Gaussian noise with standard deviation _σ ∈{_ 1 _,_ 10 _,_ 100 _}_ (denoted _s_ _~~g~~ n_ , _m_ _~~g~~ n_ , and _l_ _~~g~~ n_ ); 

(d) **Image (** **_img_ )** : We also explore more natural shifts to images, modifying a fraction _δ_ of images with combinations of random rotations _{_ 10 _,_ 40 _,_ 90 _}_ , ( _x, y_ )-axis-translation percentages _{_ 0 _._ 05 _,_ 0 _._ 2 _,_ 0 _._ 4 _}_ , as well as zoom-in percentages _{_ 0 _._ 1 _,_ 0 _._ 2 _,_ 0 _._ 4 _}_ (denoted _s_ _~~i~~ mg_ , _m_ _~~i~~ mg_ , and _l_ _~~i~~ mg_ ); 

(e) **Image + knock-out (** **_m_** **_~~i~~ mg+ko_ )** : We apply a fixed medium image shift with _δ_ 1 = 0 _._ 5 and a variable knock-out shift _δ_ ; 

(f) **Only-zero + image (** **_oz+m_** **_~~i~~ mg_ )** : Here, we only include images from class 0 in combination with a variable medium image shift affecting only a fraction _δ_ of the data; 

(g) **Original splits** : We evaluate our detectors on the original source/target splits provided by the creators of MNIST, CIFAR-10, Fashion MNIST [54], and SVHN [35] datasets (assumed to be i.i.d.); 

(h) **Domain adaptation datasets** : Data from the domain adaptation task transferring from MNIST (source) to USPS (target) ( _N_ tr = _N_ val = _N_ te = 1000; _D_ = 16 _×_ 16 _×_ 1; _C_ = 10 classes) [31] as well as the COIL-100 dataset ( _N_ tr = _N_ val = _N_ te = 2400; _D_ = 32 _×_ 32 _×_ 3; _C_ = 100 classes) [34] where images between 0<sup>_◦_</sup> and 175<sup>_◦_</sup> are sampled by the source and images between 180<sup>_◦_</sup> and 355<sup>_◦_</sup> are sampled by the target distribution. 

We provide a sample implementation of our experiments-pipeline written in Python, making use of sklearn [36] and Keras [11], located at: `https://github.com/steverab/failing-loudly` . 

## **5 Discussion** 

**Univariate VS Multivariate Tests** : We first evaluate whether we can detect shifts more easily using multiple univariate tests and aggregating their results via the Bonferroni correction or by using multivariate kernel tests. We were surprised to find that, despite the heavy correction, multiple univariate testing seem to offer comparable performance to multivariate testing (see Table 1a). 

**Dimensionality Reduction Methods** : For each testing method and experimental setting, we evaluate which DR technique is best suited to shift detection. Specifically in the multiple-univariatetesting case (and overall), BBSDs was the best-performing DR method. In the multivariate-testing case, UAE performed best. In both cases, these methods consistently outperformed others across sample sizes. The domain classifier, a popular shift detection approach, performs badly in the lowsample regime ( _≤_ 100 samples), but catches up as more samples are obtained. Noticeably, the multivariate test performs poorly in the no reduction case, which is also regarded a widely used shift detection baseline. Table 1a summarizes these results. 

We note that BBSDs being the best overall method for detecting shift is good news for ML practitioners. When building black-box models with the main purpose of classification, said model can be 

6 

Table 1: Dimensionality reduction methods (a) and shift-type (b) comparison. <u>Underlined</u> entries indicate accuracy values larger than 0.5. 

(a) Detection accuracy of different dimensionality reduction techniques across all simulated shifts on MNIST and CIFAR-10. **Green bold** entries indicate the best DR method at a given sample size, _red italic_ the worst. Results for _χ_<sup>2</sup> and Bin tests are only reported once under the univariate category. BBSDs performs best for univariate testing, while both UAE and TAE perform best for multivariate testing. 

|Test|DR|||Numb|er of s|amples|from te|st||
|---|---|---|---|---|---|---|---|---|---|
|||10|20|50|100|200|500|1,000|10,000|
||NoRed|0.03|0.15|0.26|0.36|0.41|0.47|0.54|0.72|
|sts|_PCA_|0.11|0.15|0.30|0.36|0.41|0.46|0.54|0.63|
|te|SRP|0.15|0.15|0.23|0.27|0.34|0.42|0.55|0.68|
|iv.|UAE|0.12|0.16|0.27|0.33|0.41|0.49|0.56|0.77|
|Un|TAE|0.18|0.23|0.31|0.38|0.43|0.47|0.55|0.69|
||**BBSDs**|**0.19**|**0.28**|**0.47**|**0.47**|**0.51**|**0.65**|**0.70**|**0.79**|
|_χ_<sup>2</sup>|_BBSDh_|0.03|0.07|0.12|0.22|_0.22_|_0.40_|_0.46_|_0.57_|
|Bin|_Classif_|_0.01_|_0.03_|_0.11_|_0.21_|0.28|0.42|0.51|0.67|
||NoRed|0.14|_0.15_|_0.22_|_0.28_|0.32|_0.44_|0.55|–|
|sts|PCA|0.15|0.18|0.33|0.38|0.40|0.46|0.55|–|
|. te|SRP|_0.12_|0.18|0.23|0.31|_0.31_|_0.44_|0.54|–|
|ltiv|**UAE**|**0.20**|**0.27**|**0.40**|**0.43**|**0.45**|**0.53**|**0.61**|–|
|Mu|TAE|0.18|0.26|0.37|0.38|0.45|0.52|0.59|–|
||BBSDs|0.16|0.20|0.25|0.35|0.35|0.47|_0.50_|–|



(b) Detection accuracy of different shifts on MNIST and CIFAR-10 using the best-performing DR technique (univariate: BBSDs, multivariate: UAE). **Green bold** shifts are identified as harmless, _red italic_ shifts as harmful. 

|Test|Shift|||Numb|er of s|ample|s from|test||
|---|---|---|---|---|---|---|---|---|---|
|||10|20|50|100|200|500|1,000|10,000|
||**s**<br>**gn**|0.00|0.00|0.03|0.03|0.07|0.10|0.10|0.10|
|s|**m**<br>**gn**|0.00|0.00|0.10|0.13|0.13|0.13|0.23|0.37|
|SD|**l**<br>**~~g~~n**<br>|0.17<br>|0.27<br>|0.53<br>|0.63<br>|0.67<br>|0.83<br>|0.87<br>|1.00<br>|
|B|**s**<br>**~~i~~mg**|0.00|0.00|0.23|0.30|0.40|0.63|0.70|0.93|
|e B|_m_<br>_~~i~~mg_|0.30|0.37|0.60|0.67|0.70|0.80|0.90|1.00|
|riat|_l_<br>_~~i~~mg_|0.30|0.50|0.70|0.70|0.77|0.87|0.97|1.00|
|iva|_adv_|0.13|0.27|0.40|0.43|0.53|0.77|0.83|0.90|
|Un|**ko**|0.00|0.00|0.07|0.07|0.07|0.33|0.40|0.70|
||_m_<br>_~~i~~mg+ko_|0.13|0.40|0.87|0.93|0.90|1.00|1.00|1.00|
||_oz+m_<br>_~~i~~mg_|0.67|1.00|1.00|1.00|1.00|1.00|1.00|1.00|
||s<br>~~g~~n|0.03|0.03|0.03|0.03|0.03|0.07|0.07|–|
||m<br>gn|0.03|0.03|0.03|0.03|0.17|0.27|0.30|–|
|AE|l<br>~~g~~n|0.50|0.57|0.67|0.70|0.80|0.90|1.00|–|
|U|s<br>~~i~~mg|0.17|0.20|0.27|0.30|0.40|0.47|0.63|–|
|iate|m<br>~~i~~mg|0.23|0.33|0.37|0.40|0.47|0.60|0.70|–|
|var|l<br>~~i~~mg|0.30|0.30|0.37|0.47|0.60|0.77|0.87|–|
|lti|adv|0.03|0.20|0.27|0.27|0.33|0.40|0.40|–|
|Mu|ko|0.10|0.13|0.13|0.13|0.17|0.17|0.30|–|
||m<br>~~i~~mg+ko|0.20|0.30|0.37|0.53|0.54|0.63|0.87|–|
||oz+m<br>~~i~~mg|0.27|0.63|0.77|1.00|1.00|1.00|1.00|–|



Table 2: Shift detection performance based on shift intensity (a) and perturbed sample percentages (b) using the best-performing DR technique (univariate: BBSDs, multivariate: UAE). <u>Underlined</u> entries indicate accuracy values larger than 0.5. 

(a) Detection accuracy of varying shift intensities. 

(b) Detection accuracy of varying shift percentages. 

|Test|Intensity|||Numb|er of s|amples|from t|est||Test<br>Percentage|||Numb|er of s|ample|s from|test||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|||10|20|50|100|200|500|1,000|10,000||10|20|50|100|200|500|1,000|10,000|
|.|Small|0.00|0.00|0.14|0.14|0.18|0.36|0.40|0.54|.<br>10%|0.11|0.15|0.24|0.25|0.28|0.44|0.54|0.66|
|niv|Medium|0.14|0.21|0.39|0.38|0.42|0.57|0.66|0.76|niv<br>50%|0.14|0.28|0.52|0.53|0.60|0.68|0.72|0.85|
|U|Large|0.32|0.54|0.78|0.82|0.83|0.92|0.96|1.00|U<br>100%|0.26|0.41|0.61|0.64|0.70|0.82|0.84|0.86|
|iv.|Small|0.11|0.11|0.12|0.14|0.20|0.23|0.33|–|iv.<br>10%|0.12|0.13|0.21|0.26|0.27|0.31|0.44|–|
|ult|Medium|0.11|0.19|0.23|0.27|0.32|0.42|0.44|–|ult<br>50%|0.19|0.27|0.41|0.41|0.47|0.57|0.60|–|
|M|Large|0.34|0.45|0.57|0.68|0.72|0.82|0.93|–|M<br>100%|0.29|0.41|0.44|0.53|0.60|0.70|0.78|–|



easily extended to also double as a shift detector. Moreover, black-box models with soft predictions that were built and trained in the past can be turned into shift detectors retrospectively. 

**Shift Types** : Table 1b lists shift detection accuracy values for each distinct shift as an increasing amount of samples is obtained from the target domain. Specifically, we see that _l_ _~~g~~ n_ , _m_ _~~g~~ n_ , _l_ _~~i~~ mg_ , _m_ _~~i~~ mg+ko_ , _oz+m_ _~~i~~ mg_ , and even _adv_ are easily detectable, many of them even with few samples, while _s_ _~~g~~ n_ , _m gn_ , and _ko_ are hard to detect even with many samples. With a few exceptions, the best DR technique (BBDSs for multiple univariate tests, UAE for multivariate tests) is significantly faster and more accurate at detecting shift than the average of all dimensionality reduction methods. 

**Shift Strength** : Based on the results in Table 2a, we can conclude that small shifts ( _s_ _~~g~~ n_ , _s_ _~~i~~ mg_ , and _ko_ ) are harder to detect than medium shifts ( _m_ _~~g~~ n_ , _m_ _~~i~~ mg_ , and _adv_ ) which in turn are harder to detect than large shifts ( _l_ _~~g~~ n_ , _l img_ , _m_ _~~i~~ mg+ko_ , and _oz+m_ _~~i~~ mg_ ). Specifically, we see that large shifts can on average already be detected with better than chance accuracy at only 20 samples using BBSDs, while medium and small shifts require orders of magnitude more samples in order to achieve similar accuracy. Moreover, the results in Table 2b show that while target data exhibiting only 10% anomalous samples are hard to detect, suggesting that this setting might be better addressed via outlier detection, perturbation percentages 50% and 100% can already be detected with better than chance accuracy using 50 samples. 

7 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Shift test (univ.) with (b) Shift test (univ.) with (c) Shift test (univ.) with<br>10% perturbed test data. 50% perturbed test data. 100% perturbed test data.<br>1 . 00 1 . 0 1 . 0<br>0 . 8<br>0 . 8<br>0 . 95 0 . 6 pq<br>0 . 6 Classif<br>0 . 90 0 . 4<br>0 . 4 0 . 2<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->



<!-- Start of picture text -->
(c) Shift test (univ.) with<br>100% perturbed test data.<br><!-- End of picture text -->



<!-- Start of picture text -->
(e) Classification accuracy (f) Classification accuracy (g) Classification accuracy<br>on 10% perturbed data. on 50% perturbed data. on 100% perturbed data.<br><!-- End of picture text -->





<!-- Start of picture text -->
(d) Top different.<br><!-- End of picture text -->





<!-- Start of picture text -->
(h) Top similar.<br><!-- End of picture text -->

Figure 2: Shift detection results for medium image shift on MNIST. Subfigures (a)-(c) show the _p_ -value evolution of the different DR methods with varying percentages of perturbed data, while subfigures (e)-(g) show the obtainable accuracies over the same perturbations. Subfigures (d) and (h) show the _most different_ and _most similar_ exemplars returned by the domain classifier across perturbation percentages. Plots show mean values obtained over 5 random runs with a 1- _σ_ error-bar. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDsBBSDh<br>0 . 4 0 . 4 Classif<br>0 . 2 0 . 2<br>0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Shift test (univ.) with shuffled sets (b) Shift test (univ.) with angle parti-<br>containing images from all angles. tioned source and target sets.<br>1 . 00 1 . 00<br>0 . 99 0 . 98<br>0 . 98 0 . 96<br>p<br>q<br>0 . 97 0 . 94 Classif<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(d) Classification accuracy on ran- (e) Classification accuracy on angle<br>domly shuffled sets containing images partitioned source and target sets.<br>from all angles.<br>-value p -value p<br>Accuracy Accuracy<br><!-- End of picture text -->





<!-- Start of picture text -->
(c) Top different.<br><!-- End of picture text -->





<!-- Start of picture text -->
(f) Top similar.<br><!-- End of picture text -->

Figure 3: Shift detection results on COIL-100 dataset. Subfigure organization is similar to Figure 2. 

**Most Anomalous Samples and Shift Malignancy** : Across all experiments, we observe that the most different and most similar examples returned by the domain classifier are useful in characterizing the shift. Furthermore, we can successfully distinguish malignant from benign shifts (as reported in Table 1b) by using the framework proposed in Section 3.4. While we recognize that having access to an external labeling function is a strong assumption and that accessing all true labels would be prohibitive at deployment, our experimental results also showed that, compared to the total sample size, two to three orders of magnitude fewer labeled examples suffice to obtain a good approximation of the (usually unknown) target accuracy. 

8 



<!-- Start of picture text -->
Training set average for 6 Test set average for 6 Training set 6s — test set 6s<br>0 0 .8 0 0 .8 0 0.08<br>0.06<br>5 0 .7 5 0 .7 5<br>0.04<br>0 .6 0 .6<br>1 0 0 .5 1 0 0 .5 1 0 0.02<br>0.00<br>1 5 0 .4 1 5 0 .4 1 5 - 0.02<br>0 .3 0 .3<br>- 0.04<br>2 0 0 .2 2 0 0 .2 2 0<br>- 0.06<br>2 5 0 .1 2 5 0 .1 2 5 - 0.08<br>0 .0 0 .0<br>0 5 10 15 20 25 0 5 10 15 20 25 0 5 10 15 20 25<br><!-- End of picture text -->

Figure 4: Difference plot for training and test set sixes. 

**Individual Examples** : While full results with exact _p_ -value evolution and anomalous samples are documented in the supplementary material, we briefly present two illustrative results in detail: 

(a) _Synthetic medium image shift on MNIST (Figure 2)_ : From subfigures (a)-(c), we see that most methods are able to detect the simulated shift with BBSDs being the quickest method for all tested perturbation percentages. We further observe in subfigures (e)-(g) that the (true) accuracy on samples from _q_ increasingly deviates from the model’s performance on source data from _p_ as more samples are perturbed. Since true target accuracy is usually unknown, we use the accuracy obtained on the top anomalous labeled instances returned by the domain classifier Classif. As we can see, these values significantly deviate from accuracies obtained on _p_ , which is why we consider this shift harmful to the label classifier’s performance. 

(b) _Rotation angle partitioning on COIL-100 (Figure 3)_ : Subfigures (a) and (b) show that our testing framework correctly claims the randomly shuffled dataset containing images from all angles to not contain a shift, while it identifies the partitioned dataset to be noticeably different. However, as we can see from subfigure (e), this shift does not harm the classifier’s performance, meaning that the classifier can safely be deployed even when encountering this specific dataset shift. 

**Original Splits** : According to our tests, the original split from the MNIST dataset appears to exhibit a dataset shift. After inspecting the most anomalous samples returned by the domain classifier, we observed that many of these samples depicted the digit 6. A mean-difference plot (see Figure 4) between sixes from the training set and sixes from the test set revealed that the training instances are rotated slightly to the right, while the test samples are drawn more open and centered. To back up this claim even further, we also carried out a two-sample KS test between the two sets of sixes in the input space and found that the two sets can conclusively be regarded as different with a _p_ -value of 2 _._ 7 _·_ 10<sup>_−_10</sup> , significantly undercutting the respective Bonferroni threshold of 6 _._ 3 _·_ 10<sup>_−_5</sup> . While this specific shift does not look particularly significant to the human eye (and is also declared harmless by our malignancy detector), this result however still shows that the original MNIST split is not i.i.d. 

## **6 Conclusions** 

In this paper, we put forth a comprehensive empirical investigation, examining the ways in which dimensionality reduction and two-sample testing might be combined to produce a practical pipeline for detecting distribution shift in real-life machine learning systems. Our results yielded the surprising insights that (i) black-box shift detection with soft predictions works well across a wide variety of shifts, even when some of its underlying assumptions do not hold; (ii) that aggregated univariate tests performed separately on each latent dimension offer comparable shift detection performance to multivariate two-sample tests; and (iii) that harnessing predictions from domain-discriminating classifiers enables characterization of a shift’s type and its malignancy. Moreover, we produced the surprising observation that the MNIST dataset, despite ostensibly representing a random split, exhibits a significant (although not worrisome) distribution shift. 

Our work suggests several open questions that might offer promising paths for future work, including (i) shift detection for online data, which would require us to account for and exploit the high degree of correlation between adjacent time steps [22]; and, since we have mostly explored a standard image classification setting for our experiments, (ii) applying our framework to other machine learning domains such as natural language processing or graphs. 

9 

### **Acknowledgements** 

We thank the Center for Machine Learning and Health, a joint venture of Carnegie Mellon University, UPMC, and the University of Pittsburgh for supporting our collaboration with Abridge AI to develop robust models for machine learning in healthcare. We are also grateful to Salesforce Research, Facebook AI Research, and Amazon AI for their support of our work on robust deep learning under distribution shift. 

## **References** 

- [1] Dimitris Achlioptas. Database-Friendly Random Projections: Johnson-Lindenstrauss with Binary Coins. _Journal of Computer and System Sciences_ , 66, 2003. 

- [2] Alexander A Alemi, Ian Fischer, and Joshua V Dillon. Uncertainty in the Variational Information Bottleneck. _arXiv Preprint arXiv:1807.00906_ , 2018. 

- [3] Shai Ben-David, Tyler Lu, Teresa Luu, and D´avid P´al. Impossibility Theorems for Domain Adaptation. In _International Conference on Artificial Intelligence and Statistics (AISTATS)_ , 2010. 

- [4] J Martin Bland and Douglas G Altman. Multiple Significance Tests: The Bonferroni Method. _BMJ_ , 1995. 

- [5] Mariusz Bojarski, Davide Del Testa, Daniel Dworakowski, Bernhard Firner, Beat Flepp, Prasoon Goyal, Lawrence D Jackel, Mathew Monfort, Urs Muller, Jiakai Zhang, et al. End to End Learning for Self-Driving Cars. _arXiv Preprint arXiv:1604.07316_ , 2016. 

- [6] Markus M Breunig, Hans-Peter Kriegel, Raymond T Ng, and J¨org Sander. LOF: Identifying Density-Based Local Outliers. In _ACM SIGMOD Record_ , 2000. 

- [7] Yee Seng Chan and Hwee Tou Ng. Word Sense Disambiguation with Distribution Estimation. In _International Joint Conference on Artificial intelligence (IJCAI)_ , 2005. 

- [8] Varun Chandola, Arindam Banerjee, and Vipin Kumar. Anomaly Detection: A Survey. _ACM Computing Surveys (CSUR)_ , 2009. 

- [9] Heng-Tze Cheng, Levent Koc, Jeremiah Harmsen, Tal Shaked, Tushar Chandra, Hrishi Aradhye, Glen Anderson, Greg Corrado, Wei Chai, Mustafa Ispir, et al. Wide & Deep Learning for Recommender Systems. In _Proceedings of the 1st Workshop on Deep Learning for Recommender Systems_ . ACM, 2016. 

- [10] Hyunsun Choi and Eric Jang. Generative Ensembles for Robust Anomaly Detection. _arXiv Preprint arXiv:1810.01392_ , 2018. 

- [11] Franc¸ois Chollet et al. Keras. `https://keras.io` , 2015. 

- [12] Paul Covington, Jay Adams, and Emre Sargin. Deep Neural Networks for YouTube Recommendations. In _Proceedings of the 10th ACM Conference on Recommender Systems_ . ACM, 2016. 

- [13] Ian Goodfellow, Jonathon Shlens, and Christian Szegedy. Explaining and Harnessing Adversarial Examples. In _International Conference on Learning Representations (ICLR)_ , 2014. 

- [14] Alex Graves, Abdel-rahman Mohamed, and Geoffrey Hinton. Speech Recognition with Deep Recurrent Neural Networks. In _IEEE International Conference on Acoustics, Speech and Signal Processing_ . IEEE, 2013. 

- [15] Arthur Gretton, Alexander J Smola, Jiayuan Huang, Marcel Schmittfull, Karsten M Borgwardt, and Bernhard Sch¨olkopf. Covariate Shift by Kernel Mean Matching. _Journal of Machine Learning Research (JMLR)_ , 2009. 

- [16] Arthur Gretton, Karsten M Borgwardt, Malte J Rasch, Bernhard Sch¨olkopf, and Alexander Smola. A Kernel Two-Sample Test. _Journal of Machine Learning Research (JMLR)_ , 2012. 

10 

- [17] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep Residual Learning for Image Recognition. In _Computer Vision and Pattern Recognition (CVPR)_ , 2016. 

- [18] Nicholas A Heard and Patrick Rubin-Delanchy. Choosing Between Methods of CombiningValues. _Biometrika_ , 2018. 

- [19] Dan Hendrycks and Kevin Gimpel. A Baseline for Detecting Misclassified and Out-OfDistribution Examples in Neural Networks. In _International Conference on Learning Representations (ICLR)_ , 2017. 

- [20] Dan Hendrycks, Mantas Mazeika, and Thomas G Dietterich. Deep Anomaly Detection with Outlier Exposure. In _International Conference on Learning Representations (ICLR)_ , 2019. 

- [21] Geoffrey Hinton, Li Deng, Dong Yu, George Dahl, Abdel-rahman Mohamed, Navdeep Jaitly, Andrew Senior, Vincent Vanhoucke, Patrick Nguyen, Brian Kingsbury, et al. Deep Neural Networks for Acoustic Modeling in Speech Recognition. _IEEE Signal Processing Magazine_ , 29, 2012. 

- [22] Steven R Howard, Aaditya Ramdas, Jon McAuliffe, and Jasjeet Sekhon. Uniform, Nonparametric, Non-Asymptotic Confidence Sequences. _arXiv Preprint arXiv:1810.08240_ , 2018. 

- [23] Alex Krizhevsky and Geoffrey Hinton. Learning Multiple Layers of Features from Tiny Images. Technical report, Citeseer, 2009. 

- [24] Paras Lakhani and Baskaran Sundaram. Deep Learning at Chest Radiography: Automated Classification of Pulmonary Tuberculosis by Using Convolutional Neural Networks. _Radiology_ , 284, 2017. 

- [25] Yann LeCun, L´eon Bottou, Yoshua Bengio, and Patrick Haffner. Gradient-Based Learning Applied to Document Recognition. _Proceedings of the IEEE_ , 86, 1998. 

- [26] Kimin Lee, Honglak Lee, Kibok Lee, and Jinwoo Shin. Training Confidence-Calibrated Classifiers for Detecting Out-Of-Distribution Samples. In _International Conference on Learning Representations (ICLR)_ , 2018. 

- [27] Ping Li, Trevor J Hastie, and Kenneth W Church. Very Sparse Random Projections. In _Proceedings of the 12th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD)_ . ACM, 2006. 

- [28] Shiyu Liang, Yixuan Li, and R Srikant. Enhancing the Reliability of Out-Of-Distribution Image Detection in Neural Networks. In _International Conference on Learning Representations (ICLR)_ , 2018. 

- [29] Zachary C Lipton, Yu-Xiang Wang, and Alex Smola. Detecting and Correcting for Label Shift with Black Box Predictors. In _International Conference on Machine Learning (ICML)_ , 2018. 

- [30] Fei Tony Liu, Kai Ming Ting, and Zhi-Hua Zhou. Isolation Forest. In _International Conference on Data Mining (ICDM)_ , 2008. 

- [31] Mingsheng Long, Jianmin Wang, Guiguang Ding, Jiaguang Sun, and Philip S Yu. Transfer Feature Learning with Joint Distribution Adaptation. In _International Conference on Computer Vision (ICCV)_ , 2013. 

- [32] Thomas M Loughin. A Systematic Comparison of Methods for Combining _p_ -Values from Independent Tests. _Computational Statistics & Data Analysis_ , 2004. 

- [33] Markos Markou and Sameer Singh. Novelty Detection: A Review: Part 1: Statistical Approaches. _Signal Processing_ , 2003. 

- [34] Sameer A Nene, Shree K Nayar, and Hiroshi Murase. Columbia Object Image Library (COIL100). 1996. 

- [35] Yuval Netzer, Tao Wang, Adam Coates, Alessandro Bissacco, Bo Wu, and Andrew Y Ng. Reading Digits in Natural Images With Unsupervised Feature Learning. 2011. 

11 

- [36] F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. Scikit-learn: Machine learning in Python. _Journal of Machine Learning Research_ , 12:2825–2830, 2011. 

- [37] Aaditya Ramdas, Sashank Jakkam Reddi, Barnab´as P´oczos, Aarti Singh, and Larry A Wasserman. On the Decreasing Power of Kernel and Distance Based Nonparametric Hypothesis Tests in High Dimensions. In _Association for the Advancement of Artificial Intelligence (AAAI)_ , 2015. 

- [38] Marco Saerens, Patrice Latinne, and Christine Decaestecker. Adjusting the Outputs of a Classifier to New a Priori Probabilities: A Simple Procedure. _Neural Computation_ , 2002. 

- [39] Thomas Schlegl, Philipp Seeb¨ock, Sebastian M Waldstein, Ursula Schmidt-Erfurth, and Georg Langs. Unsupervised Anomaly Detection with Generative Adversarial Networks to Guide Marker Discovery. In _International Conference on Information Processing in Medical Imaging_ , 2017. 

- [40] Bernhard Sch¨olkopf, Robert C Williamson, Alex J Smola, John Shawe-Taylor, and John C Platt. Support Vector Method for Novelty Detection. In _Advances in Neural Information Processing Systems (NIPS)_ , 2000. 

- [41] Bernhard Sch¨olkopf, Dominik Janzing, Jonas Peters, Eleni Sgouritsa, Kun Zhang, and Joris Mooij. On Causal and Anticausal Learning. In _International Conference on Machine Learning (ICML)_ , 2012. 

- [42] D Sculley, Todd Phillips, Dietmar Ebner, Vinay Chaudhary, and Michael Young. Machine Learning: The High-Interest Credit Card of Technical Debt. In _SE4ML: Software Engineering for Machine Learning (NIPS 2014 Workshop)_ , 2014. 

- [43] Alireza Shafaei, Mark Schmidt, and James J Little. Does Your Model Know the Digit 6 Is Not a Cat? A Less Biased Evaluation of Outlier Detectors. _arXiv Preprint arXiv:1809.04729_ , 2018. 

- [44] Gabi Shalev, Yossi Adi, and Joseph Keshet. Out-Of-Distribution Detection Using Multiple Semantic Label Representations. In _Advances in Neural Information Processing Systems (NeurIPS)_ , 2018. 

- [45] Hidetoshi Shimodaira. Improving Predictive Inference Under Covariate Shift by Weighting the Log-Likelihood Function. _Journal of Statistical Planning and Inference_ , 2000. 

- [46] R John Simes. An Improved Bonferroni Procedure for Multiple Tests of Significance. _Biometrika_ , 1986. 

- [47] Zak Stone, Todd Zickler, and Trevor Darrell. Autotagging Facebook: Social Network Context Improves Photo Annotation. In _IEEE Computer Society Conference on Computer Vision and Pattern Recognition Workshops_ . IEEE, 2008. 

- [48] Amos Storkey. When Training and Test Sets Are Different: Characterizing Learning Transfer. _Dataset Shift in Machine Learning_ , 2009. 

- [49] Masashi Sugiyama, Shinichi Nakajima, Hisashi Kashima, Paul V Buenau, and Motoaki Kawanabe. Direct Importance Estimation with Model Selection and Its Application to Covariate Shift Adaptation. In _Advances in Neural Information Processing Systems (NIPS)_ , 2008. 

- [50] Ilya Sutskever, Oriol Vinyals, and Quoc V Le. Sequence to Sequence Learning with Neural Networks. In _Advances in Neural Information Processing Systems (NIPS)_ , 2014. 

- [51] Christian Szegedy, Wojciech Zaremba, Ilya Sutskever, Joan Bruna, Dumitru Erhan, Ian Goodfellow, and Rob Fergus. Intriguing Properties of Neural Networks. In _International Conference on Learning Representations (ICLR)_ , 2014. 

- [52] Charles Truong, Laurent Oudre, and Nicolas Vayatis. A Review of Change Point Detection Methods. _arXiv Preprint arXiv:1801.00718_ , 2018. 

12 

- [53] Vladimir Vovk and Ruodu Wang. Combining _p_ -Values via Averaging. _arXiv Preprint arXiv:1212.4966_ , 2018. 

- [54] Han Xiao, Kashif Rasul, and Roland Vollgraf. Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms, 2017. 

- [55] Dmitri V Zaykin, Lev A Zhivotovsky, Peter H Westfall, and Bruce S Weir. Truncated Product Method for Combining _p_ -Values. _Genetic Epidemiology: The Official Publication of the International Genetic Epidemiology Society_ , 2002. 

- [56] Kun Zhang, Bernhard Sch¨olkopf, Krikamol Muandet, and Zhikun Wang. Domain Adaptation Under Target and Conditional Shift. In _International Conference on Machine Learning (ICML)_ , 2013. 

- [57] Daniel Z¨ugner, Amir Akbarnejad, and Stephan G¨unnemann. Adversarial Attacks on Neural Networks for Graph Data. In _International Conference on Knowledge Discovery & Data Mining (KDD)_ , 2018. 

13 

## **A Detailed Shift Detection Results** 

Our complete shift detection results in which we evaluate different kinds of target shifts on MNIST and CIFAR-10 using the proposed methods are documented below. In addition to our artificially generated shifts, we also evaluated our testing procedure on the original splits provided by MNIST, Fashion MNIST, CIFAR-10, and SVHN. 

### **A.1 Artificially Generated Shifts** 

### **A.1.1 MNIST** 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% adversarial samples. (b) 50% adversarial samples. (c) 100% adversarial samples.<br>1 . 00 1 . 0 1 . 0<br>0 . 8<br>0 . 95 0 . 8<br>0 . 6 p<br>0 . 90 0 . 6 0 . 4 q Classif<br>0 . 85 0 . 4 0 . 2<br>0 . 80 0 . 2 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% adversarial samples. (e) 50% adversarial samples. (f) 100% adversarial samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 5: MNIST adversarial shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
NoRed<br>0 . 8 0 . 8 PCA<br>0 . 6 SRP<br>UAE<br>0 . 6 0 . 6 TAE<br>0 . 4 BBSDs<br>0 . 4 0 . 4<br>0 . 2<br>0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% adversarial samples. (b) 50% adversarial samples. (c) 100% adversarial samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 6: MNIST adversarial shift, multivariate two-sample tests. 

14 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>1 . 00 1 . 000 1 . 000<br>0 . 998<br>0 . 98 0 . 996 0 . 995<br>0 . 994<br>0 . 96<br>0 . 990<br>0 . 992<br>p<br>0 . 94 0 . 990 q Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) Knock out 10% of class 0. (e) Knock out 50% of class 0. (f) Knock out 100% of class 0.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 7: MNIST knock-out shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 8 0 . 8 0 . 8 NoRedPCA<br>SRP<br>0 . 6 0 . 6 0 . 6 UAETAE<br>BBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 8: MNIST knock-out shift, multivariate two-sample tests. 

15 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 000 1 . 00 1 . 00<br>0 . 99 0 . 95<br>0 . 995<br>0 . 98<br>0 . 90<br>0 . 990<br>0 . 97<br>0 . 85<br>0 . 985 0 . 96 p<br>0 . 95 0 . 80 q Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 9: MNIST large Gaussian noise shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 8 0 . 8 0 . 8 NoRedPCA<br>SRP<br>0 . 6 0 . 6 0 . 6 UAETAE<br>BBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 10: MNIST large Gaussian noise shift, multivariate two-sample tests. 

16 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0000 1 . 000 1 . 000<br>0 . 9975 0 . 998<br>0 . 995<br>0 . 9950 0 . 996<br>0 . 9925<br>0 . 994 0 . 990<br>0 . 9900 p<br>0 . 992 q<br>Classif<br>0 . 9875<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->



(g) Top different samples. 





<!-- Start of picture text -->
(h) Top similar samples.<br><!-- End of picture text -->

Figure 11: MNIST medium Gaussian noise shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>0 . 8 0 . 8 0 . 8 PCASRPUAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 12: MNIST medium Gaussian noise shift, multivariate two-sample tests. 

17 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0000 1 . 000 1 . 000 p<br>q<br>0 . 9975 0 . 998<br>0 . 995<br>0 . 9950 0 . 996<br>0 . 9925<br>0 . 994 0 . 990<br>0 . 9900<br>0 . 992<br>0 . 9875<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 13: MNIST small Gaussian noise shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>0 . 8 0 . 8 0 . 8 PCASRPUAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 14: MNIST small Gaussian noise shift, multivariate two-sample tests. 

18 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 00 1 . 0 1 . 0<br>0 . 95 0 . 8 0 . 8<br>0 . 90 0 . 6 00 .. 64 pq Classif<br>0 . 4<br>0 . 85 0 . 2<br>0 . 2<br>0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 15: MNIST large image shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 8 0 . 6 0 . 5 NoRedPCA<br>0 . 6 0 . 4 00 .. 43 SRPUAETAEBBSDs<br>0 . 4<br>0 . 2<br>0 . 2<br>0 . 2 0 . 1<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 16: MNIST large image shift, multivariate two-sample tests. 

19 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 00 1 . 0 1 . 0<br>0 . 8<br>0 . 95 0 . 8<br>p<br>0 . 6 q<br>Classif<br>0 . 6<br>0 . 90 0 . 4<br>0 . 4 0 . 2<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 17: MNIST medium image shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 6 0 . 6 NoRed<br>0 . 8 PCA<br>SRP<br>UAE<br>0 . 6 0 . 4 0 . 4 TAEBBSDs<br>0 . 4<br>0 . 2 0 . 2<br>0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 18: MNIST medium image shift, multivariate two-sample tests. 

20 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 00 1 . 000 1 . 00<br>0 . 98 0 . 995 0 . 98<br>0 . 990<br>0 . 96 0 . 96<br>0 . 985<br>0 . 94 0 . 94<br>0 . 980<br>p<br>0 . 92 q<br>0 . 975 0 . 92 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 19: MNIST small image shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
NoRed<br>0 . 8 0 . 8 0 . 8 PCASRP<br>UAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 20: MNIST small image shift, multivariate two-sample tests. 

21 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>1 . 0 1 . 0 1 . 0<br>0 . 8<br>0 . 8 0 . 8<br>0 . 6<br>0 . 6<br>0 . 4 0 . 6<br>p<br>0 . 2 0 . 4 q Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) Knock out 10% of class 0. (e) Knock out 50% of class 0. (f) Knock out 100% of class 0.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->





<!-- Start of picture text -->
(g) Top different samples.<br><!-- End of picture text -->





<!-- Start of picture text -->
(h) Top similar samples.<br><!-- End of picture text -->

Figure 21: MNIST medium image shift (50%, fixed) plus knock-out shift (variable), univariate twosample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 8<br>NoRed<br>0 . 8 PCA<br>0 . 6 SRP<br>0 . 6 UAE<br>0 . 6 TAE<br>0 . 4 0 . 4 BBSDs<br>0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 22: MNIST medium image shift (50%, fixed) plus knock-out shift (variable), multivariate two-sample tests. 

22 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>0 . 8 0 . 8 0 . 8 PCASRPUAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 00 1 . 0 1 . 0<br>0 . 9 0 . 8<br>0 . 95<br>0 . 6<br>0 . 8<br>0 . 90 0 . 4<br>0 . 7<br>0 . 2 p<br>0 . 85 0 . 6 0 . 0 q Classif<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->





<!-- Start of picture text -->
(g) Top different samples.<br><!-- End of picture text -->





<!-- Start of picture text -->
(h) Top similar samples.<br><!-- End of picture text -->

Figure 23: MNIST only-zero shift (fixed) plus medium image shift (variable), univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 3 0 . 6 NoRedPCA<br>SRP<br>0 . 4 0 . 4 UAETAE<br>0 . 2 BBSDs<br>0 . 1 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 24: MNIST only-zero shift (fixed) plus medium image shift (variable), multivariate twosample tests. 

23 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDsBBSDh<br>0 . 4 Classif<br>0 . 4<br>0 . 2<br>0 . 2<br>0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>1 . 00 1 . 00 p<br>q<br>Classif<br>0 . 95 0 . 95<br>0 . 90 0 . 90<br>0 . 85 0 . 85<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(c) Randomly shuffled dataset with (d) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br>Accuracy Accuracy<br><!-- End of picture text -->





<!-- Start of picture text -->
(e) Top different samples.<br><!-- End of picture text -->





<!-- Start of picture text -->
(f) Top similar samples.<br><!-- End of picture text -->

Figure 25: MNIST to USPS domain adaptation, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0<br>0 . 04<br>0 . 8<br>0 . 02<br>0 . 6<br>0 . 00<br>0 . 4 NoRed<br>− 0 . 02 PCASRP<br>0 . 2 UAE<br>− 0 . 04 TAE<br>0 . 0 BBSDs<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br><!-- End of picture text -->

Figure 26: MNIST to USPS domain adaptation, multivariate two-sample tests. 

24 

### **A.1.2 CIFAR-10** 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6 NoRed<br>PCA<br>0 . 4 0 . 4 0 . 4 SRP<br>UAE<br>TAE<br>0 . 2 0 . 2 0 . 2 BBSDs<br>BBSDh<br>0 . 0 0 . 0 0 . 0 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% adversarial samples. (b) 50% adversarial samples. (c) 100% adversarial samples.<br>1 . 0 1 . 0 1 . 0<br>0 . 8<br>0 . 9 0 . 8<br>0 . 6 p<br>q<br>0 . 8 0 . 6 0 . 4 Classif<br>0 . 2<br>0 . 7 0 . 4<br>0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% adversarial samples. (e) 50% adversarial samples. (f) 100% adversarial samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 27: CIFAR-10 adversarial shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6<br>0 . 4 0 . 4 0 . 4 NoRed<br>PCA<br>SRP<br>0 . 2 0 . 2 0 . 2 UAE<br>TAE<br>0 . 0 0 . 0 0 . 0 BBSDs<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% adversarial samples. (b) 50% adversarial samples. (c) 100% adversarial samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 28: CIFAR-10 adversarial shift, multivariate two-sample tests. 

25 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>1 . 0 1 . 0 1 . 0 p<br>q<br>0 . 9<br>0 . 9 0 . 9<br>0 . 8<br>0 . 8<br>0 . 8<br>0 . 7<br>0 . 6 0 . 7<br>0 . 7<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) Knock out 10% of class 0. (e) Knock out 50% of class 0. (f) Knock out 100% of class 0.<br>No samples available as  Classif  did not detect a shift. No samples available as  Classif  did not detect a shift.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 29: CIFAR-10 knock-out shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 30: CIFAR-10 knock-out shift, multivariate two-sample tests. 

26 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0<br>0 . 9<br>0 . 8<br>0 . 9<br>0 . 8<br>0 . 6<br>0 . 7<br>0 . 8<br>0 . 6 0 . 4<br>p<br>0 . 7 0 . 5 0 . 2 q Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 31: CIFAR-10 large Gaussian noise shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 NoRed<br>0 . 8 0 . 8 0 . 8 PCASRP<br>UAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 32: CIFAR-10 large Gaussian noise shift, multivariate two-sample tests. 

27 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6 NoRed<br>PCA<br>0 . 4 0 . 4 0 . 4 SRPUAE<br>TAE<br>0 . 2 0 . 2 0 . 2 BBSDs<br>BBSDh<br>0 . 0 0 . 0 0 . 0 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0 p<br>q<br>Classif<br>0 . 9 0 . 9 0 . 9<br>0 . 8 0 . 8 0 . 8<br>0 . 7 0 . 7 0 . 7<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 33: CIFAR-10 medium Gaussian noise shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6<br>0 . 4 0 . 4 0 . 4 NoRed<br>PCA<br>SRP<br>0 . 2 0 . 2 0 . 2 UAE<br>TAE<br>0 . 0 0 . 0 0 . 0 BBSDs<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 34: CIFAR-10 medium Gaussian noise shift, multivariate two-sample tests. 

28 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6 NoRed<br>PCA<br>0 . 4 0 . 4 0 . 4 SRP<br>UAE<br>TAE<br>0 . 2 0 . 2 0 . 2 BBSDs<br>BBSDh<br>0 . 0 0 . 0 0 . 0 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0 p<br>q<br>0 . 9 0 . 9 0 . 9<br>0 . 8 0 . 8 0 . 8<br>0 . 7<br>0 . 7 0 . 7<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>No samples available as  Classif  did not detect a shift. No samples available as  Classif  did not detect a shift.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 35: CIFAR-10 small Gaussian noise shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6<br>0 . 4 0 . 4 0 . 4 NoRed<br>PCA<br>SRP<br>0 . 2 0 . 2 0 . 2 UAE<br>TAE<br>0 . 0 0 . 0 0 . 0 BBSDs<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 36: CIFAR-10 small Gaussian noise shift, multivariate two-sample tests. 

29 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0<br>0 . 8<br>0 . 9 0 . 8<br>0 . 6 p<br>q<br>0 . 8 0 . 6 0 . 4 Classif<br>0 . 7 0 . 2<br>0 . 4<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 37: CIFAR-10 large image shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 0 . 8 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 6 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDs<br>0 . 4<br>0 . 4 0 . 4<br>0 . 2<br>0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 38: CIFAR-10 large image shift, multivariate two-sample tests. 

30 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0<br>0 . 9<br>0 . 9 0 . 8<br>0 . 8<br>0 . 6<br>0 . 8 0 . 7<br>0 . 7 00 .. 65 0 . 4 pq Classif<br>0 . 2<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 39: CIFAR-10 medium image shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2<br>0 . 2<br>0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 40: CIFAR-10 medium image shift, multivariate two-sample tests. 

31 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0 p<br>q<br>Classif<br>0 . 9<br>0 . 9 0 . 9<br>0 . 8<br>0 . 8 0 . 8<br>0 . 7<br>0 . 7 0 . 7 0 . 6<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 41: CIFAR-10 small image shift, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2<br>0 . 2<br>0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 42: CIFAR-10 small image shift, multivariate two-sample tests. 

32 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>1 . 0 1 . 0 1 . 0 p<br>q<br>0 . 9 0 . 9 Classif<br>0 . 8<br>0 . 8 0 . 8<br>0 . 7 0 . 7 0 . 6<br>0 . 6 0 . 6<br>0 . 4<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) Knock out 10% of class 0. (e) Knock out 50% of class 0. (f) Knock out 100% of class 0.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 43: CIFAR-10 medium image shift (50%, fixed) plus knock-out shift (variable), univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>0 . 8 0 . 8 0 . 8 PCASRPUAE<br>0 . 6 0 . 6 0 . 6 TAEBBSDs<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) Knock out 10% of class 0. (b) Knock out 50% of class 0. (c) Knock out 100% of class 0.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 44: CIFAR-10 medium image shift (50%, fixed) plus knock-out shift (variable), multivariate two-sample tests. 

33 



<!-- Start of picture text -->
1 . 0 1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 0 . 4 Classif<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>1 . 0 1 . 0 1 . 0 p<br>q<br>0 . 9 Classif<br>0 . 9 0 . 8<br>0 . 8<br>0 . 8 0 . 7<br>0 . 6<br>0 . 6<br>0 . 7<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(d) 10% perturbed samples. (e) 50% perturbed samples. (f) 100% perturbed samples.<br>(g) Top different samples. (h) Top similar samples.<br>-value p -value p -value p<br>Accuracy Accuracy Accuracy<br><!-- End of picture text -->

Figure 45: CIFAR-10 only-zero shift (fixed) plus medium image shift (variable), univariate twosample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
0 . 6 0 . 8 NoRed<br>PCA<br>0 . 6 0 . 6 SRPUAE<br>0 . 4 TAE<br>BBSDs<br>0 . 4 0 . 4<br>0 . 2<br>0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test Number of samples from test<br>(a) 10% perturbed samples. (b) 50% perturbed samples. (c) 100% perturbed samples.<br>-value p -value p -value p<br><!-- End of picture text -->

Figure 46: CIFAR-10 only-zero shift (fixed) plus medium image shift (variable), multivariate twosample tests. 

34 

### **A.2 Original Splits** 

### **A.2.1 MNIST** 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 Classif<br>0 . 2 0 . 2<br>0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>1 . 000 1 . 000<br>0 . 998<br>0 . 998<br>0 . 996<br>0 . 994 0 . 996<br>p<br>0 . 992 q<br>0 . 994 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(c) Randomly shuffled dataset with (d) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br>Accuracy Accuracy<br><!-- End of picture text -->





(e) Top different samples. (f) Top similar samples. 

Figure 47: MNIST randomized and original split, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDs<br>0 . 4 0 . 4<br>0 . 2 0 . 2<br>0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br><!-- End of picture text -->

Figure 48: MNIST randomized and original split, multivariate two-sample tests. 

35 

### **A.2.2 Fashion MNIST** 



<!-- Start of picture text -->
1 . 0 1 . 0<br>0 . 8 0 . 8<br>0 . 6 0 . 6 NoRed<br>PCA<br>0 . 4 0 . 4 SRPUAE<br>TAE<br>0 . 2 0 . 2 BBSDs<br>BBSDh<br>0 . 0 0 . 0 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>1 . 00 1 . 00 p<br>q<br>0 . 98 0 . 98<br>0 . 96 0 . 96<br>0 . 94 0 . 94<br>0 . 92<br>0 . 92<br>0 . 90<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(c) Randomly shuffled dataset with (d) Original split.<br>same split proportions as original<br>dataset.<br>No samples available as  Classif  did not detect a shift. No samples available as  Classif  did not detect a shift.<br>(e) Top different samples. (f) Top similar samples.<br>-value p -value p<br>Accuracy Accuracy<br><!-- End of picture text -->

Figure 49: Fashion MNIST randomized and original split, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0<br>0 . 8 0 . 8<br>0 . 6 0 . 6<br>0 . 4 0 . 4 NoRed<br>PCA<br>SRP<br>0 . 2 0 . 2 UAE<br>TAE<br>0 . 0 0 . 0 BBSDs<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br><!-- End of picture text -->

Figure 50: Fashion MNIST randomized and original split, multivariate two-sample tests. 

36 

### **A.2.3 CIFAR-10** 



<!-- Start of picture text -->
1 . 0 1 . 0<br>0 . 8 0 . 8<br>0 . 6 0 . 6 NoRed<br>PCA<br>0 . 4 0 . 4 SRP<br>UAE<br>TAE<br>0 . 2 0 . 2 BBSDs<br>BBSDh<br>0 . 0 0 . 0 Classif<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>1 . 0 1 . 00 p<br>q<br>0 . 9 0 . 95<br>0 . 8 0 . 90<br>0 . 7 0 . 85<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(c) Randomly shuffled dataset with (d) Original split.<br>same split proportions as original<br>dataset.<br>No samples available as  Classif  did not detect a shift. No samples available as  Classif  did not detect a shift.<br>(e) Top different samples. (f) Top similar samples.<br>-value p -value p<br>Accuracy Accuracy<br><!-- End of picture text -->

Figure 51: CIFAR-10 randomized and original split, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDs<br>0 . 4<br>0 . 4<br>0 . 2<br>0 . 2<br>0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br><!-- End of picture text -->

Figure 52: CIFAR-10 randomized and original split, multivariate two-sample tests. 

37 

### **A.2.4 SVHN** 



<!-- Start of picture text -->
1 . 0 1 . 0 NoRed<br>PCA<br>0 . 8 0 . 8 SRPUAE<br>TAE<br>0 . 6 0 . 6 BBSDs<br>BBSDh<br>0 . 4 0 . 4 Classif<br>0 . 2 0 . 2<br>0 . 0 0 . 0<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>1 . 000 1 . 00 p<br>q<br>0 . 975 0 . 98 Classif<br>0 . 950 0 . 96<br>0 . 925 0 . 94<br>0 . 900 0 . 92<br>0 . 875 0 . 90<br>10 1 10 2 10 3 10 4 10 1 10 2 10 3 10 4<br>Number of samples from test Number of samples from test<br>(c) Randomly shuffled dataset with (d) Original split.<br>same split proportions as original<br>dataset.<br>(e) Top different samples. (f) Top similar samples.<br>-value p -value p<br>Accuracy Accuracy<br><!-- End of picture text -->

Figure 53: SVHN randomized and original split, univariate two-sample tests + Bonferroni aggregation. 



<!-- Start of picture text -->
1 . 0 NoRed<br>0 . 8 0 . 8 PCASRP<br>UAE<br>0 . 6 TAE<br>0 . 6 BBSDs<br>0 . 4 0 . 4<br>0 . 2 0 . 2<br>0 . 0 0 . 0<br>10 1 10 2 10 3 10 1 10 2 10 3<br>Number of samples from test Number of samples from test<br>(a) Randomly shuffled dataset with (b) Original split.<br>same split proportions as original<br>dataset.<br>-value p -value p<br><!-- End of picture text -->

Figure 54: SVHN randomized and original split, multivariate two-sample tests. 

38 

