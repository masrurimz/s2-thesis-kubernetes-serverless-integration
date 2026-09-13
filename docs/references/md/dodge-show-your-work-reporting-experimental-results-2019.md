---
# --- bibliographic record ---
entry_type: misc
title: "Show Your Work: Improved Reporting of Experimental Results"
authors:
  - "Jesse Dodge"
  - "Suchin Gururangan"
  - "Dallas Card"
  - "Roy Schwartz"
  - "Noah A. Smith"
year: 2019
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "1909.03004"
url: "https://arxiv.org/abs/1909.03004"

# --- archive record ---
source_pdf: dodge-show-your-work-reporting-experimental-results-2019.pdf
source_sha256: 5cac75c527c93689e95509c01ae68721ac96ea5ec1f41aad7a5cd6b330326ce7
pdf_pages: 21
converted: 2026-09-13
record_source: arxiv
key_insight: "A method's score is only meaningful with the search budget that produced it. Two systems compared at different tuning budgets are not compared. Grounds recording the trial count and epoch budget beside every probe result."
first_page: "Show Your Work: Improved Reporting of Experimental Results Jesse Dodge♣ Suchin Gururangan♦ Dallas Card♥ Roy Schwartz♠♦ Noah A. Smith♠♦ ♣Language Technologies Institute, Carnegie Mellon University, Pit"
---
**Show Your Work: Improved Reporting of Experimental Results** 

**Jesse Dodge**<sup>_♣_</sup> **Suchin Gururangan**<sup>_♦_</sup> 

**Dallas Card**<sup>_♥_</sup> **Roy Schwartz**<sup>_♠♦_</sup> **Noah A. Smith**<sup>_♠♦_</sup> 

- _♣_ Language Technologies Institute, Carnegie Mellon University, Pittsburgh, PA, USA 

   - _♦_ Allen Institute for Artificial Intelligence, Seattle, WA, USA 

> _♥_ Machine Learning Department, Carnegie Mellon University, Pittsburgh, PA, USA 

- _♠_ Paul G. Allen School of Computer Science & Engineering, University of Washington, Seattle, WA, USA _{_ jessed,dcard _}_ @cs.cmu.edu _{_ suching,roys,noah _}_ @allenai.org 



<!-- Start of picture text -->
(Budget,    [accuracy])<br>current practice:<br>LR val. accuracy CNN val. accuracy<br>max 39.8 38.9<br>32.0 26.1<br>38.8 26.4<br>31.1 max 40.5<br>39.5 36.1<br>… …<br>report corresponding  test -set accuracies<br>Budget that   Budget that<br>favors LR favors CNN<br>assignments<br>Hyperparameter<br><!-- End of picture text -->

# **Abstract** 

Research in natural language processing proceeds, in part, by demonstrating that new models achieve superior performance (e.g., accuracy) on held-out test data, compared to previous results. In this paper, we demonstrate that test-set performance scores alone are insufficient for drawing accurate conclusions about which model performs best. We argue for reporting additional details, especially performance on validation data obtained during model development. We present a novel technique for doing so: _expected validation performance_ of the best-found model as a function of computation budget (i.e., the number of hyperparameter search trials or the overall training time). Using our approach, we find multiple recent model comparisons where authors would have reached a different conclusion if they had used more (or less) computation. Our approach also allows us to estimate the amount of computation required to obtain a given accuracy; applying it to several recently published results yields massive variation across papers, from hours to weeks. We conclude with a set of best practices for reporting experimental results which allow for robust future comparisons, and provide code to allow researchers to use our technique.<sup>1</sup> 

Figure 1: Current practice when comparing NLP models is to train multiple instantiations of each, choose the best model of each type based on validation performance, and compare their performance on test data (inner box). Under this setup, (assuming test-set results are similar to validation), one would conclude from the results above (hyperparameter search for two models on the 5-way SST classification task) that the CNN outperforms Logistic Regression (LR). In our proposed evaluation framework, we instead encourage practitioners to consider the expected validation accuracy ( _y_ -axis; shading shows _±_ 1 standard deviation), as a function of budget ( _x_ -axis). Each point on a curve is the _expected value_ of the best validation accuracy obtained ( _y_ ) after evaluating _x_ random hyperparameter values. Note that (1) the better performing model depends on the computational budget; LR has higher expected performance for budgets up to 10 hyperparameter assignments, while the CNN is better for larger budgets. (2) Given a model and desired accuracy (e.g., 0.395 for CNN), we can estimate the expected budget required to reach it (16; dotted lines). 

# **1 Introduction** 

In NLP and machine learning, improved performance on held-out test data is typically used as an indication of the superiority of one method over others. But, as the field grows, there is an increasing gap between the large computational budgets used for some high-profile experiments and the budgets used in most other work (Schwartz et al., 2019). This hinders meaningful comparison between experiments, as improvements in performance can, in some cases, be ob- 

1https://github.com/allenai/allentune 

tained purely through more intensive hyperparameter tuning (Melis et al., 2018; Lipton and Steinhardt, 2018).<sup>2</sup> 

Moreover, recent investigations into “state-ofthe-art” claims have found competing methods to only be comparable, without clear superiority, even against baselines (Reimers and Gurevych, 2017; Lucic et al., 2018; Li and Talwalkar, 2019); this has exposed the need for reporting more than a single point estimate of performance. 

Echoing calls for more rigorous scientific practice in machine learning (Lipton and Steinhardt, 2018; Sculley et al., 2018), we draw attention to the weaknesses in current reporting practices and propose solutions which would allow for fairer comparisons and improved reproducibility. 

Our primary technical contribution is the introduction of a tool for reporting validation results in an easily interpretable way: _expected validation performance_ of the best model under a given computational budget.<sup>3</sup> That is, given a budget sufficient for training and evaluating _n_ models, we calculate the expected performance of the best of these models on validation data. Note that this differs from the _best observed_ value after _n_ evaluations. Because the expectation can be estimated from the distribution of _N_ validation performance values, with _N ≥ n_ , and these are obtained during model development,<sup>4</sup> our method **does not require additional computation** beyond hyperparameter search or optimization. We encourage researchers to report expected validation performance as a curve, across values of _n ∈ {_ 1 _, . . . , N }_ . 

As we show in _§_ 4.3, our approach makes clear that the expected-best performing model is a function of the computational budget. In _§_ 4.4 we show how our approach can be used to estimate the budget that went into obtaining previous results; in one example, we see a too-small budget for baselines, while in another we estimate a budget of about 18 GPU days was used (but not reported). Previous work on reporting validation performance used the bootstrap to approximate the mean and variance of the best performing model (Lucic et al., 2018); in _§_ 3.2 we show that our ap- 

> 2Recent work has also called attention to the environmental cost of intensive model exploration (Strubell et al., 2019). 

> 3We use the term _performance_ as a general evaluation measure, e.g., accuracy, _F_ 1, etc. 

> 4We leave forecasting performance with larger budgets _n > N_ to future work. 

proach computes these values with strictly less error than the bootstrap. 

We conclude by presenting a set of recommendations for researchers that will improve scientific reporting over current practice. We emphasize this work is about _reporting_ , not about running additional experiments (which undoubtedly can improve evidence in comparisons among models). Our reporting recommendations aim at reproducibility and improved understanding of sensitivity to hyperparameters and random initializations. Some of our recommendations may seem obvious; however, our empirical analysis shows that out of fifty EMNLP 2018 papers chosen at random, none report all items we suggest. 

# **2 Background** 

**Reproducibility** Reproducibility in machine learning is often defined as the ability to produce the _exact_ same results as reported by the developers of the model. In this work, we follow Gundersen and Kjensmo (2018) and use an extended notion of this concept: when comparing two methods, two research groups with different implementations should follow an experimental procedure which leads to the same conclusion about which performs better. As illustrated in Fig. 1, this conclusion often depends on the amount of computation applied. Thus, to make a _reproducible_ claim about which model performs best, we must also take into account the budget used (e.g., the number of hyperparameter trials). 

**Notation** We use the term _model family_ to refer to an approach subject to comparison and to hyperparameter selection.<sup>5</sup> Each model family _M_ requires its own hyperparameter selection, in terms of a set of _k_ hypermarameters, each of which defines a range of possible values. A _hyperparameter value_ (denoted _h_ ) is a _k_ -tuple of specific values for each hyperparameter. We call the set of all possible hyperparameter values _HM_ .<sup>6</sup> Given _HM_ and a computational budget sufficient for training _B_ models, the set of hyperparameter values is _{h_ 1 _, . . . , hB}_ , _hi ∈HM_ . We let _mi ∈M_ denote the model trained with hyperparameter value _hi_ . 

> 5Examples include different architectures, but also ablations of the same architecture. 

6The hyperparameter value space can also include the random seed used to initialize the model, and some specifications such as the size of the hidden layers in a neural network, in addition to commonly tuned values such as learning rate. 

**Hyperparameter value selection** There are many ways of selecting hyperparameter values, _hi_ . Grid search and uniform sampling are popular systematic methods; the latter has been shown to be superior for most search spaces (Bergstra and Bengio, 2012). Adaptive search strategies such as Bayesian optimization select _hi_ after evaluating _h_ 1 _, . . . , hi−_ 1. While these strategies may find better results quickly, they are generally less reproducible and harder to parallelize (Li et al., 2017). Manual search, where practitioners use knowledge derived from previous experience to adjust hyperparameters after each experiment, is a type of adaptive search that is the least reproducible, as different practitioners make different decisions. Regardless of the strategy adopted, we advocate for detailed reporting of the method used for hyperparmeter value selection ( _§_ 5). We next introduce a technique to visualize results of samples which are drawn i.i.d. (e.g., random initializations or uniformly sampled hyperparameter values). 

# **3 Expected Validation Performance Given Budget** 

After selecting the best hyperparameter values _hi_<sup>_∗_</sup> from among _{h_ 1 _, . . . , hB}_ with actual budget _B_ , NLP researchers typically evaluate the associated model _mi_<sup>_∗_</sup> on the test set and report its performance as an estimate of the family _M_ ’s ability to generalize to new data. We propose to make better use of the intermediately-trained models _m_ 1 _, . . . , mB_ . 

For any set of _n_ hyperparmeter values, denote the validation performance of the best model as 



where _A_ denotes an algorithm that returns the performance on validation data _DV_ after training a model from family _M_ with hyperparameter values _h_ on training data _DT_ .<sup>7</sup> We view evaluations of _A_ as the elementary unit of experimental cost.<sup>8</sup> 

Though not often done in practice, procedure (1) could be repeated many times with different hyperparameter values, yielding a _distribution_ of values for random variable _Vn_<sup>_∗_.This would allow</sup> us to estimate the _expected_ performance, E[ _Vn_<sup>_∗|_</sup> _n_ ] (given _n_ hyperparameter configurations). The 

> 7 _A_ captures standard parameter estimation, as well as procedures that depend on validation data, like early stopping. 

> 8Note that researchers do not always report validation, but rather _test_ performance, a point we will return to in _§_ 5. 

key insight used below is that, if we use random search for hyperparameter selection, then the effort that goes into a single round of random search (Eq. 1) suffices to construct a useful estimate of expected validation performance, without requiring _any further experimentation_ . 

Under random search, the _n_ hyperparameter values _h_ 1 _, . . . , hn_ are drawn uniformly at random from _HM_ , so the values of _A_ ( _M, hi, DT , DV_ ) are i.i.d. As a result, the maximum among these is itself a random variable. We introduce a diagnostic that captures information about the computation used to generate a result: the expectation of maximum performance, _conditioned_ on _n_ , the amount of computation used in the maximization over hyperparameters and random initializations: 



Reporting this expectation as we vary _n ∈ {_ 1 _,_ 2 _, . . . , B}_ gives more information than the maximum _vB_<sup>_∗_(Eq.1with</sup><sup>_n_=</sup><sup>_B_);futurere-</sup> searchers who use this model will know more about the computation budget required to achieve a given performance. We turn to calculating this expectation, then we compare it to the bootstrap ( _§_ 3.2), and discuss estimating variance ( _§_ 3.3). 

## **3.1 Expected Maximum** 

We describe how to estimate the expected maximum validation performance (Eq. 2) given a budget of _n_ hyperparameter values.<sup>9</sup> 

Assume we draw _{h_ 1 _, . . . , hn}_ uniformly at random from hyperparameter space _HM_ . Each evaluation of _A_ ( _M, h, DT , DV_ ) is therefore an i.i.d. draw of a random variable, denoted _Vi_ , with observed value _vi_ for _hi ∼HM_ . Let the maximum among _n_ i.i.d. draws from an unknown distribution be 



We seek the expected value of _Vn_<sup>_∗_given</sup><sup>_n_:</sup> 



where _P_ ( _Vn_<sup>_∗|n_) is the probability mass function</sup> (PMF) for the max-random variable.<sup>10</sup> For dis- 

> 9Conversion to alternate formulations of budget, such as GPU hours or cloud-machine rental cost in dollars, is straightforward in most cases. 

> 10For a finite validation set _DV_ , most performance measures (e.g., accuracy) only take on a finite number of possible values, hence the use of a sum instead of an integral in Eq. 4. 

crete random variables, 



Using the definition of “max”, and the fact that the _Vi_ are drawn i.i.d., 



and similarly for _P_ ( _Vn_<sup>_∗< v| n_).</sup> _P_ ( _V ≤ v_ ) and _P_ ( _V < v_ ) are cumulative distribution functions, which we can estimate using the empirical distribution, i.e. 



and similarly for strict inequality. 

Thus, our estimate of the expected maximum validation performance is 



**Discussion** As we increase the amount of computation for evaluating hyperparameter values ( _n_ ), the maximum among the samples will approach the observed maximum _vB_<sup>_∗_.Hencethecurveof</sup> E[ _Vn_<sup>_∗| n_] as a function of</sup><sup>_n_will appear to asymp-</sup> tote. Our focus here is not on estimating that value, and we do not make any claims about extrapolation of _V_<sup>_∗_</sup> beyond _B_ , the number of hyperparameter values to which _A_ is actually applied. 

Two points follow immediately from our derivation. First, at _n_ = 1, E[ _V_ 1<sup>_∗| n_= 1] is the mean of</sup> _v_ 1 _, . . . , vn_ . Second, for all _n_ , E[ _Vn_<sup>_∗|n_]</sup><sup>_≤v_</sup> _n_<sup>_∗_=</sup> max _i vi_ , which means the curve is a lower bound on the selected model’s validation performance. 

## **3.2 Comparison with Bootstrap** 

Lucic et al. (2018) and Henderson et al. (2018) have advocated for using the bootstrap to estimate the mean and variance of the best validation performance. The bootstrap (Efron and Tibshirani, 1994) is a general method which can be used to estimate statistics that do not have a closed form. The bootstrap process is as follows: draw _N_ i.i.d. samples (in our case, _N_ model evaluations). From these _N_ points, sample _n_ points (with replacement), and compute the statistic of interest (e.g., the max). Do this _K_ times (where _K_ is large), and 

average the computed statistic. By the law of large numbers, as _K →∞_ this average converges to the sample expected value (Efron and Tibshirani, 1994). 

The bootstrap has two sources of error: the error from the finite sample of _N_ points, and the error introduced by resampling these points _K_ times. Our approach has strictly less error than using the bootstrap: our calculation of the expected maximum performance in _§_ 3.1 provides a closed-form solution, and thus contains none of the resampling error (the finite sample error is the same). 

## **3.3 Variance of** _Vn_<sup>_∗_</sup> 

Expected performance becomes more useful with an estimate of variation. When using the bootstrap, standard practice is to report the standard deviation of the estimates from the _K_ resamples. As _K →∞_ , this standard deviation approximates the sample standard error (Efron and Tibshirani, 1994). We instead calculate this from the distribution in Eq. 5 using the standard plug-in-estimator. 

In most cases, we advocate for reporting a measure of variability such as the standard deviation or variance; however, in some cases it might cause confusion. For example, when the variance is large, plotting the expected value plus the variance can go outside of reasonable bounds, such as accuracy greater than any observed (even greater than 1). In such situations, we recommend shading only values within the observed range, such as in Fig. 4. Additionally, in situations where the variance is high and variance bands overlap between model families (e.g., Fig. 1), the mean is still the most informative statistic. 

# **4 Case Studies** 

Here we show two clear use cases of our method. First, we can directly estimate, for a given budget, which approach has better performance. Second, we can estimate, given our experimental setup, the budget for which the reported validation performance ( _V_<sup>_∗_</sup> ) matches a desired performance level. We present three examples that demonstrate these use cases. First, we reproduce previous findings that compared different models for text classification. Second, we explore the time vs. performance tradeoff of models that use contextual word embeddings (Peters et al., 2018). Third, from two previously published papers, we examine the budget required for our expected performance to 

match their reported performance. We find these budget estimates vary drastically. Consistently, we see that the best model is a function of the budget. We publicly release the search space and training configurations used for each case study.<sup>11</sup> 

Note that we do not report test performance in our experiments, as our purpose is not to establish a benchmark level for a model, but to demonstrate the utility of expected validation performance for model comparison and reproducibility. 

## **4.1 Experimental Details** 

For each experiment, we document the hyperparameter search space, hardware, average runtime, number of samples, and links to model implementations. We use public implementations for all models in our experiments, primarily in AllenNLP (Gardner et al., 2018). We use Tune (Liaw et al., 2018) to run parallel evaluations of uniformly sampled hyperparameter values. 

## **4.2 Validating Previous Findings** 

We start by applying our technique on a text classification task in order to confirm a well-established observation (Yogatama and Smith, 2015): logistic regression has reasonable performance with minimal hyperparameter tuning, but a well-tuned convolutional neural network (CNN) can perform better. 

We experiment with the fine-grained Stanford Sentiment Treebank text classification dataset (Socher et al., 2013). For the CNN classifier, we embed the text with 50-dim GloVe vectors (Pennington et al., 2014), feed the vectors to a ConvNet encoder, and feed the output representation into a softmax classification layer. We use the _scikit-learn_ implementation of logistic regression with bag-of-word counts and a linear classification layer. The hyperparameter spaces _H_ CNN and _H_ LR are detailed in Appendix B. For logistic regression we used bounds suggested by Yogatama and Smith (2015), which include term weighting, n- grams, stopwords, and learning rate. For the CNN we follow the hyperparameter sensitivity analysis in Zhang and Wallace (2015). 

We run 50 trials of random hyperparameter search for each classifier. Our results (Fig. 1) confirm previous findings (Zhang and Wallace, 2015): under a budget of fewer than 10 hyperparameter 

> 11https://github.com/allenai/ show-your-work 



<!-- Start of picture text -->
SST (binary)<br>0.92<br>0.90<br>0.88<br>0.86<br>0.84<br>0.82<br>0.80<br>0.78<br>GloVe + ELMo (FT)<br>0.76 GloVe + ELMo (FR)<br>GloVe<br>30min 1h 6h 1d 3d 10d<br>Training duration<br>Expected validation accuracy<br><!-- End of picture text -->

Figure 2: Expected maximum performance of a BCN classifier on SST. We compare three embedding approaches (GloVe embeddings, GloVe + frozen ELMo, and GloVe + fine-tuned ELMo). The _x_ -axis is time, on a log scale. We omit the variance for visual clarity. For each of the three model families, we sampled 50 hyperparameter values, and plot the expected maximum performance with the _x_ -axis values scaled by the average training duration. The plot shows that for each approach (GloVe, ELMo frozen, and ELMo fine-tuned), there exists a budget for which it is preferable. 

search trials, logistic regression achieves a higher expected validation accuracy than the CNN. As the budget increases, the CNN gradually improves to a higher overall expected validation accuracy. For all budgets, logistic regression has lower variance, so may be a more suitable approach for fast prototyping. 

## **4.3 Contextual Representations** 

We next explore how computational budget affects the performance of contextual embedding models (Peters et al., 2018). Recently, Peters et al. (2019) compared two methods for using contextual representations for downstream tasks: _feature extraction_ , where features are fixed after pretraining and passed into a task-specific model, or _fine-tuning_ , where they are updated during task training. Peters et al. (2019) found that feature extraction is preferable to fine-tuning ELMo embeddings. Here we set to explore whether this conclusion depends on the experimental budget. 

Closely following their experimental setup, in Fig. 2 we show the expected performance of the biattentive classification network (BCN; McCann et al., 2017) with three embedding approaches (GloVe only, GloVe + ELMo frozen, and GloVe 

+ ELMo fine-tuned), on the binary Stanford Sentiment Treebank task.<sup>12</sup> 

We use _time_ for the budget by scaling the curves by the average observed training duration for each model. We observe that as the time budget increases, the expected best-performing model changes. In particular, we find that our experimental setup leads to the same conclusion as Peters et al. (2019) given a budget between approximately 6 hours and 1 day. For larger budgets (e.g., 10 days) fine-tuning outperforms feature extraction. Moreover, for smaller budgets ( _<_ 2 hours), using GloVe embeddings is preferable to ELMo (frozen or fine-tuned). 

## **4.4 Inferring Budgets in Previous Reports** 

Our method provides another appealing property: estimating the budget required for the expected performance to reach a particular level, which we can compare against previously reported results. We present two case studies, and show that the amount of computation required to match the reported results varies drastically. 

We note that in the two examples that follow, the original papers only reported partial experimental information; we made sure to tune the hyperparameters they did list in addition to standard choices (such as the learning rate). In neither case do they report the method used to tune the hyperparameters, and we suspect they tuned them manually. Our experiments here are meant give an idea of the budget that would be required to reproduce their results or to apply their models to other datasets under random hyperparameter value selection. 

**SciTail** When introducing the SciTail textual entailment dataset, Khot et al. (2018) compared four models: an _n-gram_ baseline, which measures word-overlap as an indicator of entailment, _ESIM_ (Chen et al., 2017), a sequence-based entailment model, _DAM_ (Parikh et al., 2016), a bagof-words entailment model, and their proposed model, _DGEM_ (Khot et al., 2018), a graph-based structured entailment model. Their conclusion was that DGEM outperforms the other models. 

> 12Peters et al. (2019) use a BCN with frozen embeddings and a BiLSTM BCN for fine-tuning. We conducted experiments with both a BCN and a BiLSTM with frozen and finetuned embeddings, and found our conclusions to be consistent. We report the full hyperparameter search space, which matched Peters et al. (2019) as closely as their reporting allowed, in Appendix C. 



<!-- Start of picture text -->
SciTail<br>DGEM<br>0.825 DAM<br>ESIM<br>n-gram baseline<br>0.800<br>reported DGEM accuracy<br>0.775<br>0.750 reported DAM accuracy<br>0.725<br>reported ESIM accuracy<br>0.700<br>0.675<br>0.650<br>reported n-gram baseline accuracy<br>0.625<br>5 10 50 100<br>Hyperparameter assignments<br>Expected validation accuracy<br><!-- End of picture text -->

Figure 3: Comparing reported accuracies (dashed lines) on SciTail to expected validation performance under varying levels of compute (solid lines). The estimated budget required for expected performance to match the reported result differs substantially across models, and the relative ordering varies with budget. We omit variance for visual clarity. 

We use the same implementations of each of these models each with a hyperparameter search space detailed in Appendix D.<sup>13</sup> We use a budget based on trials instead of runtime so as to emphasize how these models behave when given a comparable number of hyperparameter configurations. 

> 13The search space bounds we use are large neighborhoods around the hyperparameter assignments specified in the public implementations of these models. Note that these curves depend on the specific hyperparameter search space adopted; as the original paper does not report hyperparameter search or model selection details, we have chosen what we believe to be reasonable bounds, and acknowledge that different choices could result in better or worse expected performance. 



<!-- Start of picture text -->
SQuAD<br>0.7 reported BIDAF EM<br>0.6<br>0.5<br>0.4<br>0.3<br>0.2<br>0.1<br>BIDAF<br>8h 1d 3d 10d 18d 1mo<br>Training duration<br>Expected validation EM<br><!-- End of picture text -->

Figure 4: Comparing reported development exactmatch score of BIDAF (dashed line) on SQuAD to expected performance of the best model with varying computational budgets (solid line). The shaded area represents the expected performance _±_ 1 standard deviation, within the observed range of values. It takes about 18 days (55 hyperparameter trials) for the expected performance to match the reported results. 

Our results (Fig. 3) show that the different models require different budgets to reach their reported performance in expectation, ranging from 2 (ngram) to 20 (DGEM). Moreover, providing a large budget for each approach improves performance substantially over reported numbers. Finally, under different computation budgets, the top performing model changes (though the neural models are similar). 

**SQuAD** Next, we turn our attention to SQuAD (Rajpurkar et al., 2016) and report performance of the commonly-used BiDAF model (Seo et al., 2017). The set of hyperparameters we tune covers those mentioned in addition to standard choices (details in Appendix D). We see in Fig. 4 that we require a budget of 18 GPU days in order for the expected maximum validation performance to match the value reported in the original paper. This suggests that some combination of prior intuition and extensive hyperparameter tuning were used by the original authors, though neither were reported. 

- ✓ **For all reported experimental results** 

   - Description of computing infrastructure 

   - Average runtime for each approach 

   - Details of train/validation/test splits 

   - Corresponding validation performance for each reported test result 

   - A link to implemented code 

- ✓ **For experiments with hyperparameter search** 

   - Bounds for each hyperparameter 

   - Hyperparameter configurations for bestperforming models 

   - Number of hyperparameter search trials 

   - The method of choosing hyperparameter values (e.g., uniform sampling, manual tuning, etc.) and the criterion used to select among them (e.g., accuracy) 

   - Expected validation performance, as introduced in _§_ 3.1, or another measure of the mean and variance as a function of the number of hyperparameter trials. 

Text Box 1: Experimental results checklist. 

# **5 Recommendations** 

**Experimental results checklist** The findings discussed in this paper and other similar efforts highlight methodological problems in experimental NLP. In this section we provide a checklist to encourage researchers to report more comprehensive experimentation results. Our list, shown in Text Box 1, builds on the reproducibility checklist that was introduced for the machine learning community during NeurIPS 2018 (which is required to be filled out for each NeurIPS 2019 submission; Pineau, 2019). 

Our focus is on improved reporting of experimental results, thus we include relevant points from their list in addition to our own. Similar to other calls for improved reporting in machine learning (Mitchell et al., 2019; Gebru et al., 2018), we recommend pairing experimental results with the information from this checklist in a structured format (see examples provided in Appendix A). 

**EMNLP 2018 checklist coverage.** To estimate how commonly this information is reported in the NLP community, we sample fifty random EMNLP 2018 papers that include experimental results and evaluate how well they conform to our proposed reporting guidelines. We find that none of the papers reported all of the items in our checklist. However, every paper reported at least one item in the checklist, and each item is reported by at 

least one paper. Of the papers we analyzed, 74% reported at least some of the best hyperparameter assignments. By contrast, 10% or fewer papers reported hyperparameter search bounds, the number of hyperparameter evaluation trials, or measures of central tendency and variation. We include the full results of this analysis in Table 1 in the Appendix. 

**Comparisons with different budgets.** We have argued that claims about relative model performance should be qualified by computational expense. With varying amounts of computation, not all claims about superiority are valid. If two models have similar budgets, we can claim one outperforms the other (with that budget). Similarly, if a model with a small budget outperforms a model with a large budget, increasing the small budget will not change this conclusion. However, if a model with a large budget outperforms a model with a small budget, the difference might be due to the model or the budget (or both). As a concrete example, Melis et al. (2018) report the performance of an LSTM on language modeling the Penn Treebank after 1,500 rounds of Bayesian optimization; if we compare to a new _M_ with a smaller budget, we can only draw a conclusion if the new model outperforms the LSTM.<sup>14</sup> 

In a larger sense, there may be no simple way to make a comparison “fair.” For example, the two models in Fig. 1 have hyperparameter spaces that are different, so fixing the same number of hyperparameter trials for both models does not imply a fair comparison. In practice, it is often not possible to measure how much past human experience has contributed to reducing the hyperparameter bounds for popular models, and there might not be a way to account for the fact that better understood (or more common) models can have better spaces to optimize over. Further, the cost of one application of _A_ might be quite different depending on the model family. Converting to runtime is one possible solution, but implementation effort could still affect comparisons at a fixed _x_ -value. Because of these considerations, our focus is on reporting whatever experimental results exist. 

# **6 Discussion: Reproducibility** 

In NLP, the use of standardized test sets and public leaderboards (which limit test evaluations) has 

> 14This is similar to controlling for the amount of training data, which is an established norm in NLP research. 

helped to mitigate the so-called “replication crisis” happening in fields such as psychology and medicine (Ioannidis, 2005; Gelman and Loken, 2014). Unfortunately, leaderboards can create additional reproducibility issues (Rogers, 2019). First, leaderboards obscure the budget that was used to tune hyperparameters, and thus the amount of work required to apply a model to a new dataset. Second, comparing to a model on a leaderboard is difficult if they _only_ report test scores. For example, on the GLUE benchmark (Wang et al., 2018), the differences in _test set_ performance between the top performing models can be on the order of a tenth of a percent, while the difference between test and validation performance might be one percent or larger. Verifying that a new implementation matches established performance requires submitting to the leaderboard, wasting test evaluations. Thus, we recommend leaderboards report validation performance for models evaluated on test sets. 

As an example, consider Devlin et al. (2019), which introduced BERT and reported state-of-theart results on the GLUE benchmark. The authors provide some details about the experimental setup, but do not report a specific budget. Subsequent work which extended BERT (Phang et al., 2018) included distributions of validation results, and we highlight this as a positive example of how to report experimental results. To achieve comparable test performance to Devlin et al. (2019), the authors report the best of twenty or one hundred random initializations. Their validation performance reporting not only illuminates the budget required to fine-tune BERT on such tasks, but also gives other practitioners results against which they can compare without submitting to the leaderboard. 

# **7 Related Work** 

Lipton and Steinhardt (2018) address a number of problems with the practice of machine learning, including incorrectly attributing empirical gains to modeling choices when they came from other sources such as hyperparameter tuning. Sculley et al. (2018) list examples of similar evaluation issues, and suggest encouraging stronger standards for empirical evaluation. They recommend detailing experimental results found throughout the research process in a time-stamped document, as is done in other experimental science fields. Our work formalizes these issues and provides an ac- 

tionable set of recommendations to address them. 

Reproducibility issues relating to standard data splits (Schwartz et al., 2011; Gorman and Bedrick, 2019; Recht et al., 2019a,b) have surfaced in a number of areas. Shuffling standard training, validation, and test set splits led to a drop in performance, and in a number of cases the inability to reproduce rankings of models. Dror et al. (2017) studied reproducibility in the context of consistency among multiple comparisons. 

Limited community standards exist for documenting datasets and models. To address this, Gebru et al. (2018) recommend pairing new datasets with a “datasheet” which includes information such as how the data was collected, how it was cleaned, and the motivation behind building the dataset. Similarly, Mitchell et al. (2019) advocate for including a “model card” with trained models which document training data, model assumptions, and intended use, among other things. Our recommendations in _§_ 5 are meant to document relevant information for experimental results. 

- Rotem Dror, Gili Baumer, Marina Bogomolov, and Roi Reichart. 2017. Replicability analysis for natural language processing: Testing significance with multiple datasets. _TACL_ , 5:471–486. 

- Bradley Efron and Robert Tibshirani. 1994. _An Introduction to the Bootstrap_ . CRC Press. 

- Matt Gardner, Joel Grus, Mark Neumann, Oyvind Tafjord, Pradeep Dasigi, Nelson F. Liu, Matthew E. Peters, Michael Schmitz, and Luke S. Zettlemoyer. 2018. AllenNLP: A deep semantic natural language processing platform. In _Proc. of NLP-OSS_ . 

- Timnit Gebru, Jamie H. Morgenstern, Briana Vecchione, Jennifer Wortman Vaughan, Hanna M. Wallach, Hal Daum´e, and Kate Crawford. 2018. Datasheets for datasets. arXiv:1803.09010. 

- Andrew Gelman and Eric Loken. 2014. The statistical crisis in science. _American Scientist_ , 102:460. 

- Kyle Gorman and Steven Bedrick. 2019. We need to talk about standard splits. In _Proc. of ACL_ . 

- Odd Erik Gundersen and Sigbjrn Kjensmo. 2018. State of the art: Reproducibility in artificial intelligence. In _Proc. of AAAI_ . 

# **8 Conclusion** 

We have shown how current practice in experimental NLP fails to support a simple standard of reproducibility. We introduce a new technique for estimating the expected validation performance of a method, as a function of computation budget, and present a set of recommendations for reporting experimental findings. 

# **Acknowledgments** 

This work was completed while the first author was an intern at the Allen Institute for Artificial Intelligence. The authors thank Kevin Jamieson, Samuel Ainsworth, and the anonymous reviewers for helpful feedback. 

# **References** 

- James Bergstra and Yoshua Bengio. 2012. Random search for hyper-parameter optimization. _JMLR_ , 13:281–305. 

- Qian Chen, Xiao-Dan Zhu, Zhen-Hua Ling, Si Wei, Hui Jiang, and Diana Inkpen. 2017. Enhanced LSTM for natural language inference. In _Proc. of ACL_ . 

- Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. BERT: Pre-training of deep bidirectional transformers for language understanding. In _Proc. of NAACL_ . 

- Peter Henderson, Riashat Islam, Philip Bachman, Joelle Pineau, Doina Precup, and David Meger. 2018. Deep reinforcement learning that matters. In _Proc. of AAAI_ . 

- John P. A. Ioannidis. 2005. Why most published research findings are false. _PLoS Med_ , 2(8). 

- Tushar Khot, Ashutosh Sabharwal, and Peter Clark. 2018. SciTaiL: A textual entailment dataset from science question answering. In _Proc. of AAAI_ . 

- Liam Li and Ameet Talwalkar. 2019. Random search and reproducibility for neural architecture search. In _Proc. of UAI_ . 

- Lisha Li, Kevin Jamieson, Giulia DeSalvo, Afshin Rostamizadeh, and Ameet Talwalkar. 2017. Hyperband: Bandit-based configuration evaluation for hyperparameter optimization. In _Proc. of ICLR_ . 

- Richard Liaw, Eric Liang, Robert Nishihara, Philipp Moritz, Joseph E Gonzalez, and Ion Stoica. 2018. Tune: A research platform for distributed model selection and training. In _Proc. of the ICML Workshop on AutoML_ . 

- Zachary C. Lipton and Jacob Steinhardt. 2018. Troubling trends in machine learning scholarship. arXiv:1807.03341. 

- Mario Lucic, Karol Kurach, Marcin Michalski, Olivier Bousquet, and Sylvain Gelly. 2018. Are GANs created equal? A large-scale study. In _Proc. of NeurIPS_ . 

- Bryan McCann, James Bradbury, Caiming Xiong, and Richard Socher. 2017. Learned in translation: Contextualized word vectors. In _Proc. of NeurIPS_ . 

- G´abor Melis, Chris Dyer, and Phil Blunsom. 2018. On the state of the art of evaluation in neural language models. In _Proc. of EMNLP_ . 

- Margaret Mitchell, Simone Wu, Andrew Zaldivar, Parker Barnes, Lucy Vasserman, Ben Hutchinson, Elena Spitzer, Inioluwa Deborah Raji, and Timnit Gebru. 2019. Model cards for model reporting. In _Proc. of FAT*_ . 

- Ankur P. Parikh, Oscar T¨ackstr¨om, Dipanjan Das, and Jakob Uszkoreit. 2016. A decomposable attention model for natural language inference. In _Proc. of EMNLP_ . 

- Jeffrey Pennington, Richard Socher, and Christopher Manning. 2014. GloVe: Global vectors for word representation. In _Proc. of EMNLP_ . 

- Matthew Peters, Sebastian Ruder, and Noah A. Smith. 2019. To tune or not to tune? Adapting pretrained representations to diverse tasks. In _Proc. of the RepL4NLP Workshop at ACL_ . 

- Matthew E. Peters, Mark Neumann, Mohit Iyyer, Matt Gardner, Christopher Clark, Kenton Lee, and Luke S. Zettlemoyer. 2018. Deep contextualized word representations. In _Proc. of NAACL_ . 

- Jason Phang, Thibault F´evry, and Samuel R. Bowman. 2018. Sentence encoders on STILTs: Supplementary training on intermediate labeled-data tasks. arXiv:1811.01088. 

- Joelle Pineau. 2019. Machine learning reproducibility checklist. https://www.cs.mcgill.ca/ ˜<sup>jpineau/ReproducibilityChecklist.</sup> pdf. Accessed: 2019-5-14. 

   - Roy Schwartz, Omri Abend, Roi Reichart, and Ari Rappoport. 2011. Neutralizing linguistically problematic annotations in unsupervised dependency parsing evaluation. In _Proc. of ACL_ . 

   - Roy Schwartz, Jesse Dodge, Noah A. Smith, and Oren Etzioni. 2019. Green AI. arXiv:1907.10597. 

   - D. Sculley, Jasper Snoek, Ali Rahimi, and Alex Wiltschko. 2018. Winner’s curse? On pace, progress, and empirical rigor. In _Proc. of ICLR (Workshop Track)_ . 

   - Min Joon Seo, Aniruddha Kembhavi, Ali Farhadi, and Hannaneh Hajishirzi. 2017. Bidirectional attention flow for machine comprehension. In _Proc. of ICLR_ . 

   - Richard Socher, Alex Perelygin, Jean Wu, Jason Chuang, Christopher D. Manning, Andrew Y. Ng, and Christopher Potts. 2013. Recursive deep models for semantic compositionality over a sentiment treebank. In _Proc. of EMNLP_ . 

   - Emma Strubell, Ananya Ganesh, and Andrew McCallum. 2019. Energy and policy considerations for deep learning in NLP. In _Proc. of ACL_ . 

   - Alex Wang, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, and Samuel R. Bowman. 2018. GLUE: A multi-task benchmark and analysis platform for natural language understanding. In _Proc. of ICLR_ . 

   - Dani Yogatama and Noah A. Smith. 2015. Bayesian optimization of text representations. In _Proc. of EMNLP_ . 

   - Ye Zhang and Byron Wallace. 2015. A sensitivity analysis of (and practitioners’ guide to) convolutional neural networks for sentence classification. arXiv:1510.03820. 

- Pranav Rajpurkar, Jian Zhang, Konstantin Lopyrev, and Percy Liang. 2016. SQuAD: 100,000+ questions for machine comprehension of text. In _Proc. of EMNLP_ . 

- Benjamin Recht, Rebecca Roelofs, Ludwig Schmidt, and Vaishaal Shankar. 2019a. Do CIFAR-10 classifiers generalize to CIFAR-10? arXiv:1806.00451. 

- Benjamin Recht, Rebecca Roelofs, Ludwig Schmidt, and Vaishaal Shankar. 2019b. Do ImageNet classifiers generalize to ImageNet? In _Proc. of ICML_ . 

- Nils Reimers and Iryna Gurevych. 2017. Reporting score distributions makes a difference: Performance study of LSTM-networks for sequence tagging. In _Proc. of EMNLP_ . 

- Anna Rogers. 2019. How the transformers broke NLP leaderboards. https://hackingsemantics. xyz/2019/leaderboards/. Accessed: 20198-29. 

# **A EMNLP 2018 Checklist Survey** 

|**Checklist item**<br>**Percentage of EMNLP 2018 papers**|
|---|
|Reports train/validation/test splits<br>92%|
|Reports best hyperparameter assignments<br>74%|
|Reports code<br>30%|
|Reports dev accuracy<br>24%|
|Reports computing infrastructure<br>18%|
|Reports empirical runtime<br>14%|
|Reports search strategy<br>14%|
|Reports score distribution<br>10%|
|Reports number of hyperparameter trials<br>10%|
|Reports hyperparameter search bounds<br>8%|



Table 1: Presence of checklist items from _§_ 5 across 50 randomly sampled EMNLP 2018 papers that involved modeling experiments. 

# **B Hyperparameter Search Spaces for Section 4.2** 

|**Computing infrastructure**|GeForce GTX 1080 GP|U|
|---|---|---|
|**Number of search trials**|50||
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|40.5||
|**Training duration**|39 sec||
|**Model implementation**<br>http://|github.com/allenai/s|how-your-work|
|**Hyperparameter**<br>number of epochs|**Search space**<br>50|**Best assignment**<br>50|
|patience|10|10|
|batch size|64|64|
|embedding|GloVe (50 dim)|GloVe (50 dim)|
|encoder|ConvNet|ConvNet|
|max filter size|_uniform-integer_[3, 6]|4|
|number of filters|_uniform-integer_[64, 512]|332|
|dropout|_uniform-float_[0, 0.5]|0.4|
|learning rate scheduler|reduce on plateau|reduce on plateau|
|learning rate scheduler patience|2 epochs|2 epochs|
|learning rate scheduler reduction factor|0.5|0.5|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.0008|



Table 2: SST (fine-grained) CNN classifier search space and best assignments. 

|**Computing Infrastructure**|3.1 GHz Intel Core i7 CPU|
|---|---|
|**Number of search trials**|50|
|**Search strategy**|uniform sampling|
|**Best validation accuracy**|39.8|
|**Training duration**|1.56 seconds|
|**Model implementation**|http://github.com/allenai/show-your-work|



|**Hyperparameter**|**Search space**|**Best assignment**|
|---|---|---|
|penalty|_choice_[L1, L2]|L2|
|no. of iter|100|100|
|solver|liblinear|liblinear|
|regularization|_uniform-float_[0, 1]|0.13|
|n-grams|_choice_[(1, 2), (1, 2, 3), (2, 3)]|[1, 2]|
|stopwords|_choice_[True, False]|True|
|weight|_choice_[tf, tf-idf, binary]|binary|
|tolerance|_loguniform-float_[10e-5, 10e-3]|0.00014|



Table 3: SST (fine-grained) logistic regression search space and best assignments. 

# **C Hyperparameter Search Spaces for Section 4.3** 

|**Computing Infrastructure**|GeForce GTX 1080 GPU||
|---|---|---|
|**Number of search trials**|50||
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|87.6||
|**Training duration**|1624 sec||
|**Model implementation**<br>http://git|hub.com/allenai/show|-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|50|50|
|patience|10|10|
|batch size|64|64|
|gradient norm|_uniform-float_[5, 10]|9.0|
|embedding dropout|_uniform-float_[0, 0.5]|0.3|
|number of pre-encode feedforward layers|_choice_[1, 2, 3]|3|
|number of pre-encode feedforward hidden dims|_uniform-integer_[64, 512]|232|
|pre-encode feedforward activation|_choice_[relu, tanh]|tanh|
|pre-encode feedforward dropout|_uniform-float_[0, 0.5]|0.0|
|encoder hidden size|_uniform-integer_[64, 512]|424|
|number of encoder layers|_choice_[1, 2, 3]|2|
|integrator hidden size|_uniform-integer_[64, 512]|337|
|number of integrator layers|_choice_[1, 2, 3]|3|
|integrator dropout|_uniform-float_[0, 0.5]|0.1|
|number of output layers|_choice_[1, 2, 3]|3|
|output hidden size|_uniform-integer_[64, 512]|384|
|output dropout|_uniform-float_[0, 0.5]|0.2|
|output pool sizes|_uniform-integer_[3, 7]|6|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.0001|
|learning rate scheduler|reduce on plateau|reduce on plateau|
|learning rate scheduler patience|2 epochs|2 epochs|
|learning rate scheduler reduction factor|0.5|0.5|



Table 4: SST (binary) BCN GloVe search space and best assignments. 

|**Computing Infrastructure**|GeForce GTX 1080 GPU||
|---|---|---|
|**Number of search trials**|50||
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|91.4||
|**Training duration**|6815 sec||
|**Model implementation**<br>http://git|hub.com/allenai/show|-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|50|50|
|patience|10|10|
|batch size|64|64|
|gradient norm|_uniform-float_[5, 10]|9.0|
|freeze ELMo|True|True|
|embedding dropout|_uniform-float_[0, 0.5]|0.3|
|number of pre-encode feedforward layers|_choice_[1, 2, 3]|3|
|number of pre-encode feedforward hidden dims|_uniform-integer_[64, 512]|206|
|pre-encode feedforward activation|_choice_[relu, tanh]|relu|
|pre-encode feedforward dropout|_uniform-float_[0, 0.5]|0.3|
|encoder hidden size|_uniform-integer_[64, 512]|93|
|number of encoder layers|_choice_[1, 2, 3]|1|
|integrator hidden size|_uniform-integer_[64, 512]|159|
|number of integrator layers|_choice_[1, 2, 3]|3|
|integrator dropout|_uniform-float_[0, 0.5]|0.4|
|number of output layers|_choice_[1, 2, 3]|1|
|output hidden size|_uniform-integer_[64, 512]|399|
|output dropout|_uniform-float_[0, 0.5]|0.4|
|output pool sizes|_uniform-integer_[3, 7]|6|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.0008|
|use integrator output ELMo|_choice_[True, False]|True|
|learning rate scheduler|reduce on plateau|reduce on plateau|
|learning rate scheduler patience|2 epochs|2 epochs|
|learning rate scheduler reduction factor|0.5|0.5|



Table 5: SST (binary) BCN GLoVe + ELMo (frozen) search space and best assignments. 

|**Computing Infrastructure**|NVIDIA Titan Xp GPU||
|---|---|---|
|**Number of search trials**|50||
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|92.2||
|**Training duration**|16071 sec||
|**Model implementation**<br>http://git|hub.com/allenai/show|-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|50|50|
|patience|10|10|
|batch size|64|64|
|gradient norm|_uniform-float_[5, 10]|7.0|
|freeze ELMo|False|False|
|embedding dropout|_uniform-float_[0, 0.5]|0.1|
|number of pre-encode feedforward layers|_choice_[1, 2, 3]|3|
|number of pre-encode feedforward hidden dims|_uniform-integer_[64, 512]|285|
|pre-encode feedforward activation|_choice_[relu, tanh]|relu|
|pre-encode feedforward dropout|_uniform-float_[0, 0.5]|0.3|
|encoder hidden size|_uniform-integer_[64, 512]|368|
|number of encoder layers|_choice_[1, 2, 3]|2|
|integrator hidden size|_uniform-integer_[64, 512]|475|
|number of integrator layers|_choice_[1, 2, 3]|3|
|integrator dropout|_uniform-float_[0, 0.5]|0.4|
|number of output layers|_choice_[1, 2, 3]|3|
|output hidden size|_uniform-integer_[64, 512]|362|
|output dropout|_uniform-float_[0, 0.5]|0.4|
|output pool sizes|_uniform-integer_[3, 7]|5|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|2.1e-5|
|use integrator output ELMo|_choice_[True, False]|True|
|learning rate scheduler|reduce on plateau|reduce on plateau|
|learning rate scheduler patience|2 epochs|2 epochs|
|learning rate scheduler reduction factor|0.5|0.5|



Table 6: SST (binary) BCN GloVe + ELMo (fine-tuned) search space and best assignments. 

# **D Hyperparameter Search Spaces for Section 4.4** 

|**Computing Infrastructure**<br>**Number of search trials**|GeForce GTX 1080 GP<br>100|U|
|---|---|---|
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|82.7||
|**Training duration**|339 sec||
|**Model implementation**<br>http://|github.com/allenai/sh|ow-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|140|140|
|patience|20|20|
|batch size|64|64|
|gradient clip|_uniform-float_[5, 10]|5.28|
|embedding projection dim|_uniform-integer_[64, 300]|78|
|number of attend feedforward layers|_choice_[1, 2, 3]|1|
|attend feedforward hidden dims|_uniform-integer_[64, 512]|336|
|attend feedforward activation|_choice_[relu, tanh]|tanh|
|attend feedforward dropout|_uniform-float_[0, 0.5]|0.1|
|number of compare feedforward layers|_choice_[1, 2, 3]|1|
|compare feedforward hidden dims|_uniform-integer_[64, 512]|370|
|compare feedforward activation|_choice_[relu, tanh]|relu|
|compare feedforward dropout|_uniform-float_[0, 0.5]|0.2|
|number of aggregate feedforward layers|_choice_[1, 2, 3]|2|
|aggregate feedforward hidden dims|_uniform-integer_[64, 512]|370|
|aggregate feedforward activation|_choice_[relu, tanh]|relu|
|aggregate feedforward dropout|_uniform-float_[0, 0.5]|0.1|
|learning rate optimizer|Adagrad|Adagrad|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.009|



Table 7: SciTail DAM search space and best assignments. 

|**Computing Infrastructure**|GeForce GTX 1080 GP|U|
|---|---|---|
|**Number of search trials**|100||
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|82.8||
|**Training duration**|372 sec||
|**Model implementation**<br>http://|github.com/allenai/sh|ow-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|75|75|
|patience|5|5|
|batch size|64|64|
|encoder hidden size|_uniform-integer_[64, 512]|253|
|dropout|_uniform-float_[0, 0.5]|0.28|
|number of encoder layers|_choice_[1, 2, 3]|1|
|number of projection feedforward layers|_choice_[1, 2, 3]|2|
|projection feedforward hidden dims|_uniform-integer_[64, 512]|85|
|projection feedforward activation|_choice_[relu, tanh]|relu|
|number of inference encoder layers|_choice_[1, 2, 3]|1|
|number of output feedforward layers|_choice_[1, 2, 3]|2|
|output feedforward hidden dims|_uniform-integer_[64, 512]|432|
|output feedforward activation|_choice_[relu, tanh]|tanh|
|output feedforward dropout|_uniform-float_[0, 0.5]|0.03|
|gradient norm|_uniform-float_[5, 10]|7.9|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.0004|
|learning rate scheduler|reduce on plateau|reduce on plateau|
|learning rate scheduler patience|0 epochs|0 epochs|
|learning rate scheduler reduction factor|0.5|0.5|
|learning rate scheduler mode|max|max|



Table 8: SciTail ESIM search space and best assignments. 

|**Computing Infrastructure**|GeForce GTX 1080 GPU|
|---|---|
|**Number of search trials**|100|
|**Search strategy**|uniform sampling|
|**Best validation accuracy**|81.2|
|**Training duration**|137 sec|
|**Model implementation**<br>http|://github.com/allenai/show-your-work|
|**Hyperparameter**|**Search space**<br>**Best assignment**|
|number of epochs|140<br>140|
|patience|20<br>20|
|batch size|64<br>64|
|dropout|_uniform-float_[0, 0.5]<br>0.2|
|hidden size|_uniform-integer_[64, 512]<br>167|
|activation|_choice_[relu, tanh]<br>tanh|
|number of layers|_choice_[1, 2, 3]<br>3|
|gradient norm|_uniform-float_[5, 10]<br>6.8|
|learning rate optimizer|Adam<br>Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]<br>0.01|
|learning rate scheduler|exponential<br>exponential|
|learning rate scheduler gamma|0.5<br>0.5|



Table 9: SciTail n-gram baseline search space and best assignments. 

|**Computing Infrastructure**|GeForce GTX 1080 G|PU|
|---|---|---|
|**Number of search trials**|100||
|**Search strategy**|uniform sampling||
|**Best validation accuracy**|81.2||
|**Training duration**|1015 sec||
|**Model implementation**<br>http:/|/github.com/allenai/s|how-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|140|140|
|patience|20|20|
|batch size|16|16|
|embedding projection dim|_uniform-integer_[64, 300]|100|
|edge embedding size|_uniform-integer_[64, 512]|204|
|premise encoder hidden size|_uniform-integer_[64, 512]|234|
|number of premise encoder layers|_choice_[1, 2, 3]|2|
|premise encoder is bidirectional|_choice_[True, False]|True|
|number of phrase probability layers|_choice_[1, 2, 3]|2|
|phrase probability hidden dims|_uniform-integer_[64, 512]|268|
|phrase probability dropout|_uniform-float_[0, 0.5]|0.2|
|phrase probability activation|_choice_[tanh, relu]|tanh|
|number of edge probability layers|_choice_[1, 2, 3]|1|
|edge probability dropout|_uniform-float_[0, 0.5]|0.2|
|edge probability activation|_choice_[tanh, relu]|tanh|
|gradient norm|_uniform-float_[5, 10]|7.0|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.0006|
|learning rate scheduler|exponential|exponential|
|learning rate scheduler gamma|0.5|0.5|



Table 10: SciTail DGEM search space and best assignments. 

|**Computing Infrastructure**|GeForce GTX 1080 GP|U|
|---|---|---|
|**Number of search trials**|128||
|**Search strategy**|uniform sampling||
|**Best validation EM**|68.2||
|**Training duration**|31617 sec||
|**Model implementation**<br>http://|github.com/allenai/s|how-your-work|
|**Hyperparameter**|**Search space**|**Best assignment**|
|number of epochs|20|20|
|patience|10|10|
|batch size|16|16|
|token embedding|GloVe (100 dim)|GloVe (100 dim)|
|gradient norm|_uniform-float_[5, 10]|6.5|
|dropout|_uniform-float_[0, 0.5]|0.46|
|character embedding dim|_uniform-integer_[16, 64]|43|
|max character filter size|_uniform-integer_[3, 6]|3|
|number of character filters|_uniform-integer_[64, 512]|33|
|character embedding dropout|_uniform-float_[0, 0.5]|0.15|
|number of highway layers|_choice_[1, 2, 3]|3|
|phrase layer hidden size|_uniform-integer_[64, 512]|122|
|number of phrase layers|_choice_[1, 2, 3]|1|
|phrase layer dropout|_uniform-float_[0, 0.5]|0.46|
|modeling layer hidden size|_uniform-integer_[64, 512]|423|
|number of modeling layers|_choice_[1, 2, 3]|3|
|modeling layer dropout|_uniform-float_[0, 0.5]|0.32|
|span end encoder hidden size|_uniform-integer_[64, 512]|138|
|span end encoder number of layers|_choice_[1, 2, 3]|1|
|span end encoder dropout|_uniform-float_[0, 0.5]|0.03|
|learning rate optimizer|Adam|Adam|
|learning rate|_loguniform-float_[1e-6, 1e-1]|0.00056|
|Adam_β_1|_uniform-float_[0.9, 1.0]|0.95|
|Adam_β_2|_uniform-float_[0.9, 1.0]|0.93|
|learning rate scheduler|reduce on plateau|reduce on plateau|
|learning rate scheduler patience|2 epochs|2 epochs|
|learning rate scheduler reduction factor|0.5|0.5|
|learning rate scheduler mode|max|max|



Table 11: SQuAD BiDAF search space and best assignments. 

