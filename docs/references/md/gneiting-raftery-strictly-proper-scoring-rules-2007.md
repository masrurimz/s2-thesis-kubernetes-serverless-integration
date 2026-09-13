---
# --- bibliographic record ---
entry_type: article
title: "Strictly Proper Scoring Rules, Prediction, and Estimation"
authors:
  - "Tilmann Gneiting"
  - "Adrian E Raftery"
year: 2007
venue: "Journal of the American Statistical Association"
volume: "102"
issue: "477"
pages: "359-378"
publisher: "Informa UK Limited"
doi: "10.1198/016214506000001437"
arxiv: ""
url: "https://doi.org/10.1198/016214506000001437"

# --- archive record ---
source_pdf: gneiting-raftery-strictly-proper-scoring-rules-2007.pdf
source_sha256: d31a0c5f0ae8fec1a0a6544db5d056645b2d7296d71b44a2e8efb293c7d87ba2
pdf_pages: 20
converted: 2026-09-13
record_source: crossref
key_insight: "Defines the class of proper scoring rules. The Brier score and the pinball loss are both members, so the crossing-target comparison is scored by a rule that cannot be gamed by hedging toward the base rate."
first_page: "Strictly Proper Scoring Rules, Prediction, and Estimation Tilmann GNEITING and Adrian E. RAFTERY Scoring rules assess the quality of probabilistic forecasts, by assigning a numerical score based on th"
---
**Strictly Proper Scoring Rules, Prediction, and Estimation** 

# Tilmann GNEITING and Adrian E. RAFTERY 

|Scoring rules assess the quality of probabilistic forecasts, by assigning a numerical score based on the predictive distribution and on the<br>event or value that materializes. A scoring rule is proper if the forecaster maximizes the expected score for an observation drawn from the<br>distribution_F_if he or she issues the probabilistic forecast_F_, rather than_G_̸ =_F_. It is strictly proper if the maximum is unique. In prediction<br>problems, proper scoring rules encourage the forecaster to make careful assessments and to be honest. In estimation problems, strictly proper<br>scoring rules provide attractive loss and utility functions that can be tailored to the problem at hand. This article reviews and develops the<br>theory of proper scoring rules on general probability spaces, and proposes and discusses examples thereof. Proper scoring rules derive from<br>convex functions and relate to information measures, entropy functions, and Bregman divergences. In the case of categorical variables, we<br>prove a rigorous version of the Savage representation. Examples of scoring rules for probabilistic forecasts in the form of predictive densities<br>include the logarithmic, spherical, pseudospherical, and quadratic scores. The continuous ranked probability score applies to probabilistic<br>forecasts that take the form of predictive cumulative distribution functions. It generalizes the absolute error and forms a special case of<br>a new and very general type of score, the energy score. Like many other scoring rules, the energy score admits a kernel representation<br>in terms of negative definite functions, with links to inequalities of Hoeffding type, in both univariate and multivariate settings. Proper<br>scoring rules for quantile and interval forecasts are also discussed. We relate proper scoring rules to Bayes factors and to cross-validation,<br>and propose a novel form of cross-validation known as random-fold cross-validation. A case study on probabilistic weather forecasts in<br>the North American Pacific Northwest illustrates the importance of propriety. We note optimum score approaches to point and quantile<br>estimation, and propose the intuitively appealing interval score as a utility function in interval estimation that addresses width as well as<br>coverage.|
|---|
|KEY WORDS:<br>Bayes factor; Bregman divergence; Brier score; Coherent; Continuous ranked probability score; Cross-validation; Entropy;<br>Kernel score; Loss function; Minimum contrast estimation; Negative definite function; Prediction interval; Predictive<br>distribution; Quantile forecast; Scoring rule; Skill score; Strictly proper; Utility function.|



## 1. INTRODUCTION 

One major purpose of statistical analysis is to make forecasts for the future and provide suitable measures of the uncertainty associated with them. Consequently, forecasts should be probabilistic in nature, taking the form of probability distributions over future quantities or events (Dawid 1984). Indeed, over the past two decades, probabilistic forecasting has become routine in such applications as weather and climate prediction (Palmer 2002; Gneiting and Raftery 2005), computational finance (Duffie and Pan 1997), and macroeconomic forecasting (Garratt, Lee, Pesaran, and Shin 2003; Granger 2006). In the statistical literature, advances in Markov chain Monte Carlo methodology (see, e.g., Besag, Green, Higdon, and Mengersen 1995) have led to explosive growth in the use of predictive distributions, mostly in the form of Monte Carlo samples from posterior predictive distributions of quantities of interest. In earlier work (Gneiting, Raftery, Balabdaoui, and Westveld 2003; Gneiting, Balabdaoui, and Raftery 2006), we contended that the goal of probabilistic forecasting is to maximize the sharpness of the predictive distributions subject to calibration. Calibration refers to the statistical consistency between the distributional 

Tilmann Gneiting is Associate Professor of Statistics (E-mail: _tilmann@stat. washington.edu_ ) and Adrian E. Raftery is Blumstein-Jordan Professor of Statistics and Sociology (E-mail: _raftery@u.washington.edu_ ), Department of Statistics, University of Washington, Seattle, WA 98195. This work was supported by the DoD Multidisciplinary University Research Initiative (MURI) program administered by the Office of Naval Research under grant N00014-01-10745 and by the National Science Foundation under award 0134264. Part of Tilmann Gneiting’s work was performed on sabbatical leave at the Soil Physics Group, Universität Bayreuth, 95440 Bayreuth, Germany. The authors thank Mark Albright, Veronica J. Berrocal, William M. Briggs, Andreas Buja, Ignacio Cascos, Claudia Czado, A. Philip Dawid, Werner Ehm, Thomas Gerds, Eric P. Grimit, Susanne Gschlößl, Eliezer Gurarie, Mark S. Handcock, Leonhard Held, Peter J. Huber, Nicholas A. Johnson, Ian T. Jolliffe, Hans Kuensch, Christian Lantuéjoul, Clifford F. Mass, Debashis Mondal, David B. Stephenson, Werner Stuetzle, Gabor J. Székely, Olivier Talagrand, Jon A. Wellner, Lawrence J. Wilson, Robert L. Winkler, and two anonymous reviewers for providing comments, preprints, references, and data. 

forecasts and the observations, and is a joint property of the forecasts and the events or values that materialize. Sharpness refers to the concentration of the predictive distributions and is a property of the forecasts only. 

_Scoring rules_ provide summary measures for the evaluation of probabilistic forecasts, by assigning a numerical score based on the predictive distribution and on the event or value that materializes. In terms of elicitation, the role of scoring rules is to encourage the assessor to make careful assessments and to be honest (Garthwaite, Kadane, and O’Hagan 2005). In terms of evaluation, scoring rules measure the quality of the probabilistic forecasts, reward probability assessors for forecasting jobs, and rank competing forecast procedures. Meteorologists refer to this broad task as _forecast verification_ , and much of the underlying methodology has been developed by atmospheric scientists (Jolliffe and Stephenson 2003). In a Bayesian context, scores are frequently referred to as utilities, emphasizing the Bayesian principle of maximizing the expected utility of a predictive distribution (Bernardo and Smith 1994). We take scoring rules to be positively oriented rewards that a forecaster wishes to maximize. Specifically, if the forecaster quotes the predictive distribution _P_ and the event _x_ materializes, then his or her reward is _S(P, x)_ . The function _S(P,_ · _)_ takes values in the real line R or in the extended real line R = [−∞ _,_ ∞], and we write _S(P, Q)_ for the expected value of _S(P,_ · _)_ under _Q_ . Suppose, then, that the forecaster’s best judgment is the distributional forecast _Q_ . The forecaster has no incentive to predict any _P_ ̸ = _Q_ and is encouraged to quote his or her true belief, _P_ = _Q_ , if _S(Q, Q)_ ≥ _S(P, Q)_ with equality if and only if _P_ = _Q_ . A scoring rule with this property is said to be _strictly proper_ . If _S(Q, Q)_ ≥ _S(P, Q)_ for all _P_ and _Q_ , then the scoring rule is said to be _proper_ . Propriety is essential in scientific and operational 

**© 2007 American Statistical Association Journal of the American Statistical Association March 2007, Vol. 102, No. 477, Review Article DOI 10.1198/016214506000001437** 

**359** 

Journal of the American Statistical Association, March 2007 

360 

forecast evaluation; and we present a case study that provides a striking example of the potential issues that result from the use of intuitively appealing but improper scoring rules. 

In estimation problems, strictly proper scoring rules provide attractive loss and utility functions that can be tailored to a scientific problem. To fix the idea, suppose that we wish to fit a parametric model _Pθ_ based on a sample _X_ 1 _,..., Xn_ . To estimate _θ_ , we might measure the goodness-of-fit by the mean score 



where _S_ is a strictly proper scoring rule. If _θ_ 0 denotes the true parameter value, then asymptotic arguments indicate that argmax _θ Sn(θ)_ → _θ_ 0 as _n_ →∞. This suggests a general approach to estimation: Choose a strictly proper scoring rule that is tailored to the problem at hand and use _θ_<sup>ˆ</sup> _n_ = argmax _θ Sn(θ)_ as the _optimum score estimator_ based on the scoring rule. Pfanzagl (1969) and Birgé and Massart (1993) studied this approach under the heading of _minimum contrast estimation_ . Maximum likelihood estimation forms a special case of optimum score estimation, and optimum score estimation forms a special case of _M_ -estimation (Huber 1964), in that the function to be optimized derives from a strictly proper scoring rule. 

This article reviews and develops the theory of proper scoring rules on general probability spaces, proposes and discusses examples thereof, and presents case studies. The remainder of the article is organized as follows. In Section 2 we state a fundamental characterization theorem, review the links between proper scoring rules, information measures, entropy functions, and Bregman divergences, and introduce skill scores. In Section 3 we turn to scoring rules for categorical variables. We prove a rigorous version of the representation of Savage (1971) and relate to a more recent characterization of Schervish (1989) that applies to probability forecasts of a dichotomous event. Bremnes (2004, p. 346) noted that the literature on scoring rules for probabilistic forecasts of continuous variables is sparse. We address this issue in Section 4, where we discuss the spherical, pseudospherical, logarithmic, and quadratic scores. The _continuous ranked probability score_ , which lately has attracted much attention, enjoys appealing properties and might serve as a standard score in evaluating probabilistic forecasts of real-valued variables. It forms a special case of a novel and very general type of scoring rule, the energy score. In Section 5 we introduce an even more general construction, giving rise to _kernel scores_ based on negative definite functions and inequalities of Hoeffding type, with side results on expectation inequalities and positive definite functions. In Section 6 we study scoring rules for quantile and interval forecasts. We show that the class of proper scoring rules for quantile forecasts is larger than conjectured by Cervera and Muñoz (1996) and discuss the _interval score_ , a scoring rule for prediction intervals that is proper and has intuitive appeal. In Section 7 we relate proper scoring rules to Bayes factors and to cross-validation, and propose a novel form of cross-validation known as random-fold cross-validation. In Section 8 we present a case study on the use of scoring rules in the evaluation of probabilistic weather forecasts. In Section 9 we turn to optimum score estimation. We discuss point, quantile, and interval estimation and propose using the interval score 

as a utility function that addresses width as well as coverage. We close the article with a discussion of avenues for future work in Section 10. Scoring rules show a superficial analogy to statistical depth functions, which we hint at in an Appendix. 

## 2. CHARACTERIZATIONS OF PROPER SCORING RULES 

In this section we introduce notation, provide characterizations of proper scoring rules, and relate them to convex functions, information measures, and Bregman divergences. The discussion here is more technical than that in the remainder of the article, and readers with more applied interests might skip ahead to Section 2.3, in which we discuss skill scores, without significant loss of continuity. 

## 2.1 Proper Scoring Rules and Convex Functions 

We consider probabilistic forecasts on a general sample space _�_ . Let _A_ be a _σ_ -algebra of subsets of _�_ , and let _P_ be a convex class of probability measures on _(�, A)_ . A function defined on _�_ and taking values in the extended real line, R = [−∞ _,_ ∞], is _P_ - _quasi-integrable_ if it is measurable with respect to _A_ and is quasi-integrable with respect to all _P_ ∈ _P_ (Bauer 2001, p. 64). A _probabilistic forecast_ is any probability measure _P_ ∈ _P_ . A _scoring rule_ is any extended real-valued function _S_ : _P_ × _�_ → R such that _S(P,_ · _)_ is _P_ -quasi-integrable for all _P_ ∈ _P_ . Thus if the forecast is _P_ and _ω_ materializes, the forecaster’s reward is _S(P,ω)_ . We permit algebraic operations on the extended real line and deal with the respective integrals and expectations as described in section 2.1 of Mattner (1997) and section 3.1 of Grünwald and Dawid (2004). The scoring rules used in practice are mostly real-valued, but there are exceptions, such as the logarithmic rule (Good 1952), that allow for infinite scores. 

We write 



for the expected score under _Q_ when the probabilistic forecast is _P_ . The scoring rule _S_ is _proper_ relative to _P_ if 



It is _strictly proper_ relative to _P_ if (1) holds with equality if and only if _P_ = _Q_ , thereby encouraging honest quotes by the forecaster. If _S_ is a proper scoring rule, _c >_ 0 is a constant, and _h_ is a _P_ -integrable function, then 



is also a proper scoring rule. Similarly, if _S_ is strictly proper, then _S_<sup>∗</sup> is strictly proper as well. Following Dawid (1998), we say that _S_ and _S_<sup>∗</sup> are _equivalent_ , and _strongly equivalent_ if _c_ = 1. The term _proper_ was apparently coined by Winkler and Murphy (1968, p. 754), whereas the general idea dates back at least to Brier (1950) and Good (1952, p. 112). In a parametric context, and with respect to estimators, Lehmann and Casella (1998, p. 157) refer to the defining property in (1) as _risk unbiasedness_ . 

A function _G_ : _P_ → R is _convex_ if 

_G((_ 1 − _λ)P_ 0 + _λP_ 1 _)_ ≤ _(_ 1 − _λ)G(P_ 0 _)_ + _λG(P_ 1 _)_ 



Gneiting and Raftery: Proper Scoring Rules 

361 

It is _strictly convex_ if (3) holds with equality if and only if _P_ 0 = _P_ 1. A function _G_<sup>∗</sup> _(P,_ · _)_ : _�_ → R is a _subtangent_ of _G_ at the point _P_ ∈ _P_ if it is integrable with respect to _P_ , quasi-integrable with respect to all _Q_ ∈ _P_ , and 



for all _Q_ ∈ _P_ . The following characterization theorem is more general and considerably simpler than previous results of McCarthy (1956) and Hendrickson and Buehler (1971). 

_Definition 1._ A scoring rule _S_ : _P_ × _�_ → R is _regular_ relative to the class _P_ if _S(P, Q)_ is real-valued for all _P, Q_ ∈ _P_ , except possibly that _S(P, Q)_ = −∞ if _P_ ̸ = _Q_ . 

_Theorem 1._ A regular scoring rule _S_ : _P_ × _�_ → R is proper relative to the class _P_ if and only if there exists a convex, realvalued function _G_ on _P_ such that 



for _P_ ∈ _P_ and _ω_ ∈ _�_ , where _G_<sup>∗</sup> _(P,_ · _)_ : _�_ → R is a subtangent of _G_ at the point _P_ ∈ _P_ . The statement holds with proper replaced by strictly proper, and convex replaced by strictly convex. 

_Proof._ If the scoring rule _S_ is of the stated form, then the subtangent inequality (4) implies the defining inequality (1), that is, propriety. Conversely, suppose that _S_ is a regular proper scoring rule. Define _G_ : _P_ → R by _G(P)_ = _S(P, P)_ = sup _Q_ ∈ _P S(Q, P)_ , which is the pointwise supremum over a class of convex functions and thus is convex on _P_ . Furthermore, the subtangent inequality (4) holds with _G_<sup>∗</sup> _(P,ω)_ = _S(P,ω)_ . This implies the representation (5) and proves the claim for propriety. By an argument of Hendrickson and Buehler (1971), strict inequality in (1) is equivalent to no subtangent of _G_ at _P_ being a subtangent of _G_ at _Q_ , for _P, Q_ ∈ _P_ and _P_ ̸ = _Q_ , which is equivalent to _G_ being strictly convex on _P_ . 

Expressed slightly differently, a regular scoring rule _S_ is proper relative to the class _P_ if and only if the expected score function _G(P)_ = _S(P, P)_ is convex and _S(P,ω)_ is a subtangent of _G_ at the point _P_ , for all _P_ ∈ _P_ . 

## 2.2 Information Measures, Bregman Divergences, and Decision Theory 

Suppose that the scoring rule _S_ is proper relative to the class _P_ . Following Grünwald and Dawid (2004) and Buja, Stuetzle, and Shen (2005), we call the expected score function 



the _information measure_ or _generalized entropy function_ associated with the scoring rule _S_ . This is the maximally achievable utility; the term _entropy function_ is used as well. If _S_ is regular and proper, then we call 



the associated _divergence function_ . Note the order of the arguments, which differs from previous practice in that the true distribution, _Q_ , is preceded by an alternative probabilistic forecast, _P_ . The divergence function is nonnegative, and if _S_ is 

strictly proper, then _d(P, Q)_ is strictly positive, unless _P_ = _Q_ . If the sample space is finite and the entropy function is sufficiently smooth, then the divergence function becomes the _Bregman divergence_ (Bregman 1967), associated with the convex function _G_ . Bregman divergences play major roles in optimization and have recently attracted the attention of the machine learning community (Collins, Schapire, and Singer 2002). The term _Bregman distance_ is also used, even though _d(P, Q)_ is not necessarily the same as _d(Q, P)_ . 

An interesting problem is to find conditions under which a divergence function _d_ is a _score divergence_ , in the sense that it admits the representation (7) for a proper scoring rule _S_ , and to describe principled ways of finding such a scoring rule. The landmark work by Savage (1971) provides a necessary condition on a symmetric divergence function _d_ to be a score divergence: If _P_ and _Q_ are concentrated on the same two mutually exclusive events and identified with the respective probabilities, _p, q_ ∈[0 _,_ 1], then _d(P, Q)_ reduces to a linear function of _(p_ − _q)_<sup>2</sup> . Dawid (1998) noted that if _d_ is a score convergence, then _d(P, Q)_ − _d(P_<sup>′</sup> _, Q)_ is an affine function of _Q_ for all _P, P_<sup>′</sup> ∈ _P_ , and proved a partial converse. 

Friedman (1983) and Nau (1985) studied a looser type of relationship between proper scoring rules and distance measures on classes of probability distributions. They restricted attention to metrics (i.e., distance measures that are symmetric and satisfy the triangle inequality) and called a scoring rule _S effective_ with respect to a metric _d_ if 



Nau (1985) called a metric _co-effective_ if there is a proper scoring rule that is effective with respect to it. His proposition 1 implies that the _l_ 1, _l_ ∞, and Hellinger distances on spaces of absolutely continuous probability measures are not co-effective. 

Sections 3–5 provide numerous examples of proper scoring rules on general sample spaces, along with the associated entropy and divergence functions. For example, the logarithmic score is linked to Shannon entropy and Kullback–Leibler divergence. Dawid (1998, 2006), Grünwald and Dawid (2004), and Buja et al. (2005) have given further examples of proper scoring rules, entropy, and divergence functions and have elaborated on the connections to the Bregman divergence. 

Proper scoring rules occur naturally in statistical decision problems (Dawid 1998). Given an outcome space and an action space, let _U(ω, a)_ be the utility for outcome _ω_ and action _a_ , and let _P_ be a convex class of probability measures on the outcome space. Let _aP_ denote the Bayes act for _P_ ∈ _P_ . Then the scoring rule 



is proper relative to the class _P_ . Indeed, 



by the fact that the optimal Bayesian decision maximizes expected utility. Dawid (2006) has given details and discussed the generality of the construction. 

Journal of the American Statistical Association, March 2007 

362 

## 2.3 Skill Scores 

In practice, scores are aggregated, and competing forecast procedures are ranked by the average score, 



over a fixed set of forecast situations. We give examples of this in case studies in Sections 6 and 8. Recommendations for choosing a scoring rule have been given by Winkler (1994, 1996), by Buja et al. (2005), and throughout this article. 

Scores for competing forecast procedures are directly comparable if they refer to exactly the same set of forecast situations. If scores for distinct sets of situations are compared, then considerable care must be exercised to separate the confounding effects of intrinsic predictability and predictive performance. For instance, there is substantial spatial and temporal variability in the predictability of weather and climate elements (Langland et al. 1999; Campbell and Diebold 2005). Thus a score that is superior for a given location or season might be inferior for another, or vice versa. To address this issue, atmospheric scientists have put forth _skill scores_ of the form 



where _Sn_<sup>fcst</sup> is the forecaster’s score, _Sn_<sup>opt</sup> refers to a hypothetical ideal or optimal forecast, and _Sn_<sup>ref</sup> is the score for a reference strategy (Murphy 1973; Potts 2003, p. 27; Briggs and Ruppert 2005; Wilks 2006, p. 259). Skill scores are standardized in that (8) takes the value 1 for an optimal forecast, which is typically understood as a point measure in the event or value that materializes, and the value 0 for the reference forecast. Negative values of a skill score indicate forecasts that are of lesser quality than the reference. The reference forecast is typically a _climatological_ forecast, that is, an estimate of the marginal distribution of the predictand. For example, a climatological probabilistic forecast for maximum temperature on Independence Day in Seattle, Washington might be a smoothed version of the local historic record of July 4 maximum temperatures. Climatological forecasts are independent of the forecast horizon; they are calibrated by construction, but often lack sharpness. 

Unfortunately, skill scores of the form (8) are generally improper, even if the underlying scoring rule _S_ is proper. Murphy (1973) studied hedging strategies in the case of the Brier skill score for probability forecasts of a dichotomous event. He showed that the Brier skill score is asymptotically proper, in the sense that the benefits of hedging become negligible as the number of independent forecasts grows. Similar arguments may apply to skill scores based on other proper scoring rules. Mason’s (2004) claim of the propriety of the Brier skill score rests on unjustified approximations and generally is incorrect. 

## 3. SCORING RULES FOR CATEGORICAL VARIABLES 

We now review the representations of Savage (1971) and Schervish (1989) that characterize scoring rules for probabilistic forecasts of categorical and binary variables, and give examples of proper scoring rules. 

## 3.1 Savage Representation 

We consider probabilistic forecasts of a categorical variable. Thus, the sample space _�_ = {1 _,..., m_ } consists of a finite number _m_ of mutually exclusive events, and a probabilistic forecast is a probability vector _(p_ 1 _,..., pm)_ . Using the notation of Section 2, we consider the convex class _P_ = _Pm_ , where 

_Pm_ = � **p** = _(p_ 1 _,..., pm)_ : _p_ 1 _,..., pm_ ≥ 0 _, p_ 1 + ··· + _pm_ = 1� _._ A scoring rule _S_ can then be identified with a collection of _m_ functions, 



In other words, if the forecaster quotes the probability vector **p** and the event _i_ materializes, then his or her reward is _S(_ **p** _, i)_ . Theorem 2 is a special case of Theorem 1 and provides a rigorous version of the Savage (1971) representation of proper scoring rules on finite sample spaces. Our contributions lie in the notion of regularity, the rigorous treatment, and the introduction of appropriate tools for convex analysis (Rockafellar 1970, sects. 23–25). Specifically, let _G_ : _Pm_ → R be a convex function. A vector **G**<sup>′</sup> _(_ **p** _)_ = _(G_<sup>′</sup> 1<sup>_(_</sup><sup>**p**</sup><sup>_),...,G_</sup> _m_<sup>′</sup><sup>_(_</sup><sup>**p**</sup><sup>_))_isa</sup><sup>_subgradi-_</sup> _ent_ of _G_ at the point **p** ∈ _Pm_ if 



for all **q** ∈ _Pm_ , where ⟨· _,_ ·⟩ denotes the standard scalar product. If _G_ is differentiable at an interior point **p** ∈ _Pm_ , then **G**<sup>′</sup> _(_ **p** _)_ is unique and equals the gradient of _G_ at **p** . We assume that the components of **G**<sup>′</sup> _(_ **p** _)_ are real-valued, except that we permit _G_<sup>′</sup> _i_<sup>_(_</sup><sup>**p**</sup><sup>_)_= −∞if</sup><sup>_pi_= 0.</sup> 

_Definition 2._ A scoring rule _S_ for categorical forecasts is _regular_ if _S(_ · _, i)_ is real-valued for _i_ = 1 _,..., m_ , except possibly that _S(_ **p** _, i)_ = −∞ if _pi_ = 0. 

Regular scoring rules assign finite scores, except that a forecast might receive a score of −∞ if an event claimed to be impossible is realized. The logarithmic scoring rule (Good 1952) provides a prominent example of this. 

_Theorem 2_ (McCarthy, Savage) _._ A regular scoring rule _S_ for categorical forecasts is proper if and only if 



where _G_ : _Pm_ → R is a convex function and **G**<sup>′</sup> _(_ **p** _)_ is a subgradient of _G_ at the point **p** , for all **p** ∈ _Pm_ . The statement holds with proper replaced by strictly proper, and convex replaced by strictly convex. 

Phrased slightly differently, a regular scoring rule _S_ is proper if and only if the expected score function _G(_ **p** _)_ = _S(_ **p** _,_ **p** _)_ is convex on _Pm_ , and the vector with components _S(_ **p** _, i)_ for _i_ = 1 _,..., m_ is a subgradient of _G_ at the point **p** , for all **p** ∈ _Pm_ . In view of these results, every bounded convex function _G_ on _Pm_ generates a regular proper scoring rule. This function _G_ becomes the expected score function, information measure, or entropy function (6) associated with the score. The divergence function (7) is the respective Bregman distance. 

We now give a number of examples. The scoring rules in Examples 1–3 are strictly proper. The score in Example 4 is proper but not strictly proper. 

Gneiting and Raftery: Proper Scoring Rules 

363 

_Example 1_ (Quadratic or Brier score) _._ If _G(_ **p** _)_ =<sup>�</sup><sup>_m_</sup> _j_ =1<sup>_p_2</sup> _j_<sup>−</sup> 1, then (10) yields the quadratic score or Brier score, 



where _δij_ = 1 if _i_ = _j_ and _δij_ = 0 otherwise. The associated Bregman divergence is the squared Euclidean distance, _d(_ **p** _,_ **q** _)_ =<sup>�</sup><sup>_m_</sup> _j_ =1<sup>_(pj_−</sup><sup>_qj)_2.Thiswell-knownscoringrulewas</sup> proposed by Brier (1950). Selten (1998) gave an axiomatic characterization. 

_Example 2_ (Spherical score) _._ Let _α >_ 1 and consider the generalized entropy function _G(_ **p** _)_ = _(_<sup>�</sup><sup>_m_</sup> _j_ =1<sup>_pα_</sup> _j_<sup>_)_1</sup><sup>_/α_.Thiscor-</sup> responds to the pseudospherical score 



which reduces to the traditional spherical score when _α_ = 2. The associated Bregman divergence is 



_Example 3_ (Logarithmic score) _._ Negative Shannon entropy, _G(_ **p** _)_ =<sup>�</sup><sup>_m_</sup> _j_ =1<sup>_pj_log</sup><sup>_pj_,correspondstothelogarithmicscore,</sup> _S(_ **p** _, i)_ = log _pi_ . The associated Bregman distance is the Kullback–Leibler divergence, _d(_ **p** _,_ **q** _)_ =<sup>�</sup><sup>_m_</sup> _j_ =1<sup>_qj_log</sup><sup>_(qj/pj)_.[Note</sup> the order of the arguments in the definition (7) of the divergence function.] This scoring rule dates back at least to Good (1952). Information-theoretic perspectives and interpretations in terms of gambling returns have been given by Roulston and Smith (2002) and Daley and Vere-Jones (2004). Despite its popularity, the logarithmic score has been criticized for its unboundedness, with Selten (1998, p. 51) arguing that it entails value judgments that are unacceptable. Feuerverger and Rahman (1992) noted a connection to Neyman–Pearson theory and an ensuing optimality property of the logarithmic score. 

_Example 4_ (Zero–one score) _._ The zero–one scoring rule rewards a probabilistic forecast if the mode of the predictive distribution materializes. In case of multiple modes, the reward is reduced proportionally, that is, 



where _M(_ **p** _)_ = { _i_ : _pi_ = max _j_ =1 _,...,m pj_ } denotes the set of modes of **p** . This is also known as the _misclassification loss_ , and the meteorological literature uses the term _success rate_ to denote case-averaged zero–one scores (see, e.g., Toth, Zhu, and Marchok 2001). The associated expected score or generalized entropy function (6) is _G(_ **p** _)_ = max _j_ =1 _,...,m pj_ , and the divergence function (7) becomes 



This does not define a Bregman divergence, because the entropy function is neither differentiable nor strictly convex. 

The scoring rules in the foregoing examples are _symmetric_ , in the sense that 



for all **p** ∈ _Pm_ , for all permutations _π_ on _m_ elements and for all events _i_ = 1 _,..., m_ . Winkler (1994, 1996) argued that symmetric rules do not always appropriately reward forecasting skill and called for asymmetric ones, particularly in situations in which skills scores traditionally have been used. Asymmetric proper scoring rules can be generated by applying Theorem 2 to convex functions _G_ that are not invariant under coordinate permutation. 

## 3.2 Schervish Representation 

The classical case of a probability forecast for a dichotomous event suggests further discussion. We follow Dawid (1986) in considering the sample space _�_ = {1 _,_ 0}. A probabilistic forecast is a quoted probability _p_ ∈[0 _,_ 1] for the event to occur. A scoring rule _S_ can be identified with a pair of functions _S(_ · _,_ 1 _)_ : [0 _,_ 1] → R and _S(_ · _,_ 0 _)_ : [0 _,_ 1] → R. Thus, _S(p,_ 1 _)_ is the forecaster’s reward if he or she quotes _p_ and the event materializes, and _S(p,_ 0 _)_ is the reward if he or she quotes _p_ and the event does not materialize. Note the subtle change from the previous section, where we used the convex class _P_ 2 = { _(p_ 1 _, p_ 2 _)_ ∈ R<sup>2</sup> : _p_ 1 ∈[0 _,_ 1] _, p_ 2 = 1 − _p_ 1} in place of the unit interval, _P_ = [0 _,_ 1], to represent probability measures on binary sample spaces. 

A scoring rule for binary variables is _regular_ if _S(_ · _,_ 1 _)_ and _S(_ · _,_ 0 _)_ are real-valued, except possibly that _S(_ 0 _,_ 1 _)_ = −∞ or _S(_ 1 _,_ 0 _)_ = −∞. A variant of Theorem 2 shows that every regular proper scoring rule is of the form _S(p,_ 1 _)_ = _G(p)_ + _(_ 1 − _p)G_<sup>′</sup> _(p),_ (12) _S(p,_ 0 _)_ = _G(p)_ − _pG_<sup>′</sup> _(p),_ 

where _G_ : [0 _,_ 1] → R is a convex function and _G_<sup>′</sup> _(p)_ is a subgradient of _G_ at the point _p_ ∈[0 _,_ 1], in the sense that 



for all _q_ ∈[0 _,_ 1]. The statement holds with proper replaced by strictly proper, and convex replaced by strictly convex. The subgradient _G_<sup>′</sup> _(p)_ is real-valued, except that we permit _G_<sup>′</sup> _(_ 0 _)_ = −∞ and _G_<sup>′</sup> _(_ 1 _)_ = ∞. The function _G_ is the expected score function _G(p)_ = _pS(p,_ 1 _)_ + _(_ 1 − _p)S(p,_ 0 _)_ , and if _G_ is differentiable at an interior point _p_ ∈ _(_ 0 _,_ 1 _)_ , then _G_<sup>′</sup> _(p)_ is unique and equals the derivative of _G_ at _p_ . Related but slightly less general results were given by Shuford, Albert, and Massengil (1966). Figure 1 provides a geometric interpretation. 

The Savage representation (12) implies various interesting properties of regular proper scoring rules. For instance, we conclude from theorem 24.2 of Rockafellar (1970) that 



for _p_ ∈ _(_ 0 _,_ 1 _)_ , and because _G_<sup>′</sup> _(p)_ is increasing, _S(p,_ 1 _)_ is increasing as well. Similarly, _S(p,_ 0 _)_ is decreasing, as would be intuitively expected. The statements hold with proper, increasing, and decreasing replaced by strictly proper, strictly increasing, and strictly decreasing. Alternative proofs of these and other results have been given by Schervish (1989, the app.). 

Journal of the American Statistical Association, March 2007 

364 



Figure 1. Schematic Illustration of the Relationships Between a Smooth Generalized Entropy Function G (solid convex curve) and the Associated Scoring Functions and Bregman Divergence. For any probability forecast p ∈ [0, 1], the expected score S(p,q) = qS(p, 1)+(1−q)S(p, 0) equals the ordinate of the tangent to G at p [the solid line with slope G<sup>′</sup> (p)], when evaluated at q ∈ [0, 1]. In particular, the scores S(p, 0) = G(p) − pG<sup>′</sup> (p) and S(p, 1) = G(p) + (1 − p)G<sup>′</sup> (p) can be read off the tangent when evaluated at q = 0 and q = 1. The Bregman divergence d(p,q) = S(q,q) − S(p,q) equals the difference between G and its tangent at p when evaluated at q. (For a similar interpretation see fig. 8 in Buja et al. 2005.) 

Schervish (1989, p. 1861) suggested that his theorem 4.2 generalizes the Savage representation. Given Savage’s (1971, p. 793) assessment of his representation (9.15) as “figurative,” the claim can well be justified. However, in its rigorous form [eq. (12)], the Savage representation is perfectly general. 

Hereinafter, we let 1{·} denote an indicator function that takes value 1 if the event in brackets is true and 0 otherwise. 

_Theorem 3_ (Schervish) _._ Suppose that _S_ is a regular scoring rule. Then _S_ is proper and such that _S(_ 0 _,_ 1 _)_ = lim _p_ →0 _S(p,_ 1 _)_ , and _S(_ 0 _,_ 0 _)_ = lim _p_ →0 _S(p,_ 0 _)_ , and both _S(p,_ 1 _)_ and _S(p,_ 0 _)_ are left continuous if and only if there exists a nonnegative measure _ν_ on _(_ 0 _,_ 1 _)_ such that 





for all _p_ ∈[0 _,_ 1]. The scoring rule is strictly proper if and only if _ν_ assigns positive measure to every open interval. 

_Sketch of Proof._ Suppose that _S_ satisfies the assumptions of the theorem. To prove that _S(p,_ 1 _)_ is of the form (14), consider the representation (13), identify the increasing function _G_<sup>′</sup> _(p)_ with the left-continuous distribution function of a nonnegative measure _ν_ on _(_ 0 _,_ 1 _)_ , and apply the partial integration formula. The proof of the representation for _S(p,_ 0 _)_ is analogous. For the proof of the converse, reverse the foregoing steps. The statement for strict propriety follows from well-known properties of convex functions. 

A two-decision problem can be characterized by a cost–loss ratio _c_ ∈ _(_ 0 _,_ 1 _)_ that reflects the relative costs of the two possible types of inferior decision. The measure _ν(_ d _c)_ in Schervish’s representation (14) assigns relevance to distinct cost–loss ratios. This result also can be interpreted as a Choquet representation, in that every left-continuous bounded scoring rule is equivalent to a mixture of cost-weighted asymmetric zero–one scores, 

_Sc(p,_ 1 _)_ = _(_ 1 − _c)_ 1{ _p > c_ } _, Sc(p,_ 0 _)_ = _c_ 1{ _p_ ≤ _c_ } _,_ (15) with a nonnegative mixing measure _ν(_ d _c)_ . Theorem 3 allows for unbounded scores, requiring a slightly more elaborate statement. Full equivalence to the Savage representation (12) can be achieved if the regularity conditions are relaxed (Schervish 1989; Buja et al. 2005). 

Table 1 shows the mixing measure _ν(_ d _c)_ for the quadratic or Brier score, the spherical score, the logarithmic score, and the asymmetric zero–one score. If the expected score function, _G_ , is smooth, then _ν(_ d _c)_ has Lebesgue density _G_<sup>′′</sup> _(c)_ (Buja et al. 2005). For instance, the logarithmic score derives from Shannon entropy, _G(p)_ = _p_ log _p_ + _(_ 1 − _p)_ log _(_ 1 − _p)_ , and corresponds to the infinite measure with Lebesgue density _(c(_ 1 − _c))_<sup>−1</sup> . 

Buja et al. (2005) introduced the beta family, a continuous two-parameter family of proper scoring rules that includes both symmetric and asymmetric members and derives from mixing measures of beta type. 

_Example 5_ (Beta family) _._ Let _α,β >_ −1 and consider the two-parameter family 



Gneiting and Raftery: Proper Scoring Rules 

365 

Table 1. Proper Scoring Rules for Probability Forecasts of a Dichotomous Event and the Respective Mixing Measure or Lebesgue Density in the Schervish Representation (14) 

|Scoring rule|S(p,1)|S(p,0)|_ν_(dc)|
|---|---|---|---|
|Brier|−(1−p)<sup>2</sup>|−p<sup>2</sup>|Uniform|
|Spherical|p(1−2p+2p<sup>2</sup>)<sup>−1</sup><sup>_/_2</sup>|(1−p)(1−2p+2p<sup>2</sup>)<sup>−1</sup><sup>_/_2</sup>|(1−2c+2c<sup>2</sup>)<sup>−3</sup><sup>_/_2</sup>|
|Logarithmic|logp|log(1−p)|(c (1−c))<sup>−1</sup>|
|Zero–one|(1−c)1{p_>_c}|c1{p≤c}|Point measure in c|





which is of the form (14) for a mixing measure _ν(_ d _c)_ with Lebesgue density _c_<sup>_α_−1</sup> _(_ 1 − _c)_<sup>_β_−1</sup> . This family includes the logarithmic score ( _α_ = _β_ = 0), and versions of the Brier score ( _α_ = _β_ = 1), and the zero–one score (15) with _c_ =<sup><u>1</u></sup> 2<sup>(</sup><sup>_α_=</sup><sup>_β_→∞)</sup> as special or limiting cases. Asymmetric members arise when _α_ ̸ = _β_ , with the scoring rule _S(p,_ 1 _)_ = _p_ − 1 and _S(p,_ 0 _)_ = _p_ + log _(_ 1 − _p)_ being one such example ( _α_ = 0 _,β_ = 1). 

Winkler (1994) proposed a method for constructing asymmetric scoring rules from symmetric scoring rules. Specifically, if _S_ is a symmetric proper scoring rule and _c_ ∈ _(_ 0 _,_ 1 _)_ , then 





where _T(c, p)_ = _S(_ 0 _,_ 0 _)_ − _S(c,_ 0 _)_ if _p_ ≤ _c_ and _T(c, p)_ = _S(_ 1 _,_ 1 _)_ − _S(c,_ 1 _)_ if _p > c_ is also a proper scoring rule, standardized in the sense that the expected score function attains a minimum value of 0 at _p_ = _c_ and a maximum value of 1 at _p_ = 0 and _p_ = 1. 

_Example 6_ (Winkler’s score) _._ Tetlock (2005) explored what constitutes good judgment in predicting future political and economic events, and looked at why experts are often wrong in their forecasts. In evaluating experts’ predictions, he adjusted for the difficulty of the forecast task by using the special case of (16) that derives from the Brier score, that is, 



with the value of _c_ ∈ _(_ 0 _,_ 1 _)_ adapted to reflect a baseline probability. This was suggested by Winkler (1994, 1996) as an alternative to using skill scores. 

Figure 2 shows the expected score or generalized entropy function, _G(p)_ , and the scoring functions, _S(p,_ 1 _)_ and _S(p,_ 0 _)_ , for the quadratic or Brier score and the logarithmic score (Table 1), the asymmetric zero–one score (15) with _c_ = _._ 6, and Winkler’s standardized score (17) with _c_ = _._ 2. 

## 4. SCORING RULES FOR CONTINUOUS VARIABLES 

Bremnes (2004, p. 346) noted that the literature on scoring rules for probabilistic forecasts of continuous variables is sparse. We address this issue in the following. 

## 4.1 Scoring Rules for Density Forecasts 

Let _µ_ be a _σ_ -finite measure on the measurable space _(�, A)_ . For _α >_ 1, let _Lα_ denote the class of probability measures on _(�, A)_ that are absolutely continuous with respect to _µ_ and have _µ_ -density _p_ such that 



is finite. We identify a probabilistic forecast _P_ ∈ _Lα_ with its _µ_ -density, _p_ , and call _p_ a _predictive density_ or _density forecast_ . Predictive densities are defined only up to a set of _µ_ -measure zero. Whenever appropriate, we follow Bernardo (1979, p. 689) and use the unique version defined by _p(ω)_ = lim _ρ_ →0 _P(Sρ(ω))/µ(Sρ(ω))_ , where _Sρ(ω)_ is a sphere of radius _ρ_ centered at _ω_ . 

We begin by discussing scoring rules that correspond to Examples 1, 2, and 3. The _quadratic score_ , 



is strictly proper relative to the class _L_ 2. It has expected score or generalized entropy function _G(p)_ = ∥ _p_ ∥<sup>2</sup> 2<sup>,andtheassociated</sup> divergence function, _d(p, q)_ = ∥ _p_ − _q_ ∥<sup>2</sup> 2<sup>,issymmetric.Good</sup> (1971) proposed the _pseudospherical score_ , 



that reduces to the _spherical score_ when _α_ = 2. He described original and generalized versions of the score—a distinction that in a measure-theoretic framework is obsolete. The pseudospherical score is strictly proper relative to the class _Lα_ . The strict convexity of the associated entropy function, _G(p)_ = ∥ _p_ ∥ _α_ , and the nonnegativity of the divergence function are straightforward consequences of the Hölder and Minkowski inequalities. 

The _logarithmic score_ , 



emerges as a limiting case ( _α_ → 1) of the pseudospherical score when suitably scaled. This scoring rule was proposed by Good (1952) and has been widely used since then, under various names, including the _predictive deviance_ (Knorr-Held and Rainer 2001) and the _ignorance score_ (Roulston and Smith 2002). The logarithmic score is strictly proper relative to the class _L_ 1 of the probability measures dominated by _µ_ . The associated expected score function or information measure is negative Shannon entropy, and the divergence function becomes the classical Kullback–Leibler divergence. 

Bernardo (1979, p. 689) argued that “when assessing the worthiness of a scientist’s final conclusions, only the probability he attaches to a small interval containing the true value 

Journal of the American Statistical Association, March 2007 

366 



Figure 2. The Expected Score or Generalized Entropy Function G(p) (top row) and the Scoring Functions S(p, 1) ( —) and S(p, 0) ( - - -) (bottom row), for the Brier Score and Logarithmic Score (Table 1), the Asymmetric Zero–One Score (15) With c = .6 and Winkler’s Standardized Score (17) With c = .2. 

should be taken into account.” This seems subject to debate, and atmospheric scientists have argued otherwise, putting forth scoring rules that are _sensitive to distance_ (Epstein 1969; Staël von Holstein 1970). That said, Bernardo (1979) studied _local_ scoring rules _S(p,ω)_ that depend on the predictive density _p_ only through its value at the event _ω_ that materializes. Assuming regularity conditions, he showed that every proper local scoring rule is equivalent to the logarithmic score, in the sense of (2). Consequently, the _linear score_ , LinS _(p,ω)_ = _p(ω)_ , is not a proper scoring rule, despite its intuitive appeal. For instance, let _ϕ_ and _u_ denote the Lebesgue densities of a standard Gaussian distribution and the uniform distribution on _(_ − _ϵ,ϵ)_ . If _ϵ <_<sup>~~√~~</sup> log2, then 



in violation of propriety. Essentially, the linear score encourages overprediction at the modes of an assessor’s true predictive density (Winkler 1969). The probability score of Wilson, Burrows, and Lanzinger (1999) integrates the predictive density over a neighborhood of the observed, real-valued quantity. This resembles the linear score and is not a proper score either. Dawid (2006) constructed proper scoring rules from improper 

ones; an interesting question is whether this can be done for the probability score, similar to the way in which the proper quadratic score (18) derives from the linear score. 

If Lebesgue densities on the real line are used to predict discrete observations, then the logarithmic score encourages the placement of artificially high density ordinates on the target values in question. This problem emerged in the Evaluating Predictive Uncertainty Challenge at a recent PASCAL Challenges Workshop (Kohonen and Suomela 2006; Quiñonero-Candela, Rasmussen, Sinz, Bousquet, and Schölkopf 2006). It disappears if scores expressed in terms of predictive cumulative distribution functions are used, or if the sample space is reduced to the target values in question. 

## 4.2 Continuous Ranked Probability Score 

The restriction to predictive densities is often impractical. For instance, probabilistic quantitative precipitation forecasts involve distributions with a point mass at zero (Krzysztofowicz and Sigrest 1999; Bremnes 2004), and predictive distributions are often expressed in terms of samples, possibly originating from Markov chain Monte Carlo. Thus it seems more compelling to define scoring rules directly in terms of predictive cumulative distribution functions. Furthermore, the aforementioned scores are not sensitive to distance, meaning that no credit is given for assigning high probabilities to values near but not identical to the one materializing. 

Gneiting and Raftery: Proper Scoring Rules 

367 

To address this situation, let _P_ consist of the Borel probability measures on R. We identify a probabilistic forecast— a member of the class _P_ —with its cumulative distribution function _F_ , and use standard notation for the elements of the sample space R. The _continuous ranked probability score_ (CRPS) is defined as 



and corresponds to the integral of the Brier scores for the associated binary probability forecasts at all real-valued thresholds (Matheson and Winkler 1976; Hersbach 2000). 

Applications of the CRPS have been hampered by a lack of readily computable solutions to the integral in (20), and the use of numerical quadrature rules has been proposed instead (Staël von Holstein 1977; Unger 1985). However, the integral often can be evaluated in closed form. By lemma 2.2 of Baringhaus and Franz (2004) or identity (17) of Székely and Rizzo (2005), 



where _X_ and _X_<sup>′</sup> are independent copies of a random variable with distribution function _F_ and finite first moment. If the predictive distribution is Gaussian with mean _µ_ and variance _σ_<sup>2</sup> , then it follows that 





where _ϕ_ and _�_ denote the probability density function and the cumulative distribution function of a standard Gaussian variable. If the predictive distribution takes the form of a sample of size _n_ , then the right side of (20) can be evaluated in terms of the respective order statistics in a total of _O(n_ log _n)_ operations (Hersbach 2000, sec. 4.b). 

The CRPS is proper relative to the class _P_ and strictly proper relative to the subclass _P_ 1 of the Borel probability measures that have finite first moment. The associated expected score function or information measure, 



coincides with the negative selectivity function (Matheron 1984), and the respective divergence function, 



is symmetric and of the Cramér–von Mises type. 

The CRPS lately has attracted renewed interest in the atmospheric sciences community (Hersbach 2000; Candille and Talagrand 2005; Gneiting, Raftery, Westveld, and Goldman 2005; Grimit, Gneiting, Berrocal, and Johnson 2006; Wilks 2006, pp. 302–303). It is typically used in negative orientation, say CRPS<sup>∗</sup> _(F, x)_ = −CRPS _(F, x)_ . The representation (21) then can be written as 



which sheds new light on the score. In negative orientation, the CRPS can be reported in the same unit as the observations, and it generalizes the absolute error to which it reduces if _F_ is a deterministic forecast—that is, a point measure. Thus the CRPS provides a direct way to compare deterministic and probabilistic forecasts. 

## 4.3 Energy Score 

We introduce a generalization of the CRPS that draws on Székely’s (2003) statistical energy perspective. Let _Pβ_ , _β_ ∈ _(_ 0 _,_ 2 _)_ , denote the class of the Borel probability measures _P_ on R<sup>_m_</sup> that are such that _EP_ ∥ **X** ∥<sup>_β_</sup> is finite, where ∥· ∥ denotes the Euclidean norm. We define the _energy score_ , 



where **X** and **X**<sup>′</sup> are independent copies of a random vector with distribution _P_ ∈ _Pβ_ . This generalizes the CRPS, to which (22) reduces when _β_ = 1 and _m_ = 1, by allowing for an index _β_ ∈ _(_ 0 _,_ 2 _)_ and applying to distributional forecasts of a vectorvalued quantity in R<sup>_m_</sup> . Theorem 1 of Székely (2003) shows that the energy score is strictly proper relative to the class _Pβ_ . [For a different and more general argument, see Sec. 5.1.] In the limiting case _β_ = 2, the energy score (22) reduces to the negative squared error, 



where **_µ_** _P_ denotes the mean vector of _P_ . This scoring rule is regular and proper, but not strictly proper, relative to the class _P_ 2. 

The energy score with index _β_ ∈ _(_ 0 _,_ 2 _)_ applies to all Borel probability measures on R<sup>_m_</sup> , by defining 



where _φP_ denotes the characteristic function of _P_ . If _P_ belongs to _Pβ_ , then theorem 1 of Székely (2003) implies the equality of the right sides in (22) and (24). Essentially, the score computes a weighted distance between the characteristic function of _P_ and the characteristic function of the point measure at the value that materializes. 

## 4.4 Scoring Rules That Depend on First and Second Moments Only 

An interesting question is that for proper scoring rules that apply to the Borel probability measures on R<sup>_m_</sup> and depend on the predictive distribution, _P_ , only through its mean vector, **_µ_** _P_ , and dispersion or covariance matrix, **_�_** _P_ . Dawid (1998) and Dawid and Sebastiani (1999) studied proper scoring rules of this type. A particularly appealing example is the scoring rule 



which is linked to the generalized entropy function 



and to the divergence function 



Journal of the American Statistical Association, March 2007 

368 

[Note the order of the arguments in the definition (7) of the divergence function.] This scoring rule is proper but not strictly proper relative to the class _P_ 2 of the Borel probability measures _P_ for which _EP_ ∥ **X** ∥<sup>2</sup> is finite. It is strictly proper relative to any convex class of probability measures characterized by the first two moments, such as the Gaussian measures, for which (25) is equivalent to the logarithmic score (19). For other examples of scoring rules that depend on **_µ_** _P_ and **_�_** _P_ only, see (23) and the right column of table 1 of Dawid and Sebastiani (1999). 

The predictive model choice criterion of Laud and Ibrahim (1995) and Gelfand and Ghosh (1998) has lately attracted the attention of the statistical community. Suppose that we fit a predictive model to observed, real-valued data _x_ 1 _,..., xn_ . The predictive model choice criterion (PMCC) assesses the model fit through the quantity 



where _µi_ and _σi_<sup>2denote the expected value and the variance of</sup> a replicate variable _Xi_ , given the model and the observations. Within the framework of scoring rules, the PMCC corresponds to the positively oriented score 



where _P_ has mean _µP_ and variance _σP_<sup>2.Thescoringrule(26)</sup> depends on the predictive distribution through its first two moments only, but it is improper; if the forecaster’s true belief is _P_ and if he or she wishes to maximize the expected score, then he or she will quote the point measure at _µP_ —that is, a deterministic forecast—rather than the predictive distribution _P_ . This suggests that the predictive model choice criterion should be replaced by a criterion based on the scoring rule (25), which reduces to 



in the case in which _m_ = 1 and the observations are real-valued. 

## 5. KERNEL SCORES, NEGATIVE AND POSITIVE DEFINITE FUNCTIONS, AND INEQUALITIES OF HOEFFDING TYPE 

In this section we use negative definite functions to construct proper scoring rules and present expectation inequalities that are of independent interest. 

## 5.1 Kernel Scores 

Let _�_ be a nonempty set. A real-valued function _g_ on _�_ × _�_ is said to be a _negative definite kernel_ if it is symmetric in its arguments and<sup>�</sup><sup>_n_</sup> _i_ =1 � _nj_ =1<sup>_aiajg(xi,xj)_≤0 for all positive inte-</sup> gers _n_ , all _a_ 1 _,..., an_ ∈ R that sum to 0, and all _x_ 1 _,..., xn_ ∈ _�_ . Numerous examples of negative definite kernels have been given by Berg, Christensen, and Ressel (1984) and the references cited therein. 

We now give the key result of this section, which generalizes a kernel construction of Eaton (1982, p. 335). The term _kernel score_ was coined by Dawid (2006). 

_Theorem 4._ Let _�_ be a Hausdorff space and let _g_ be a nonnegative, continuous negative definite kernel on _�_ × _�_ . For a Borel probability measure _P_ on _�_ , let _X_ and _X_<sup>′</sup> be independent random variables with distribution _P_ . Then the scoring rule 



is proper relative to the class of the Borel probability measures _P_ on _�_ for which the expectation _EPg(X, X_<sup>′</sup> _)_ is finite. 

_Proof._ Let _P_ and _Q_ be Borel probability measures on _�_ , and suppose that _X, X_<sup>′</sup> and _Y, Y_<sup>′</sup> are independent random variates with distribution _P_ and _Q_ . We need to show that 



Next we give examples of scoring rules that admit a kernel representation. In each case, we equip the sample space with the standard topology. Note that evaluating the kernel scores is straightforward if _P_ is discrete and has only a moderate number of atoms. 

_Example 7_ (Quadratic or Brier score) _._ Let _�_ = {1 _,_ 0} and suppose that _g(_ 0 _,_ 0 _)_ = _g(_ 1 _,_ 1 _)_ = 0 and _g(_ 0 _,_ 1 _)_ = _g(_ 1 _,_ 0 _)_ = 1. Then (28) recovers the quadratic or Brier score. 

_Example 8_ (CRPS) _._ If _�_ = R and _g(x, x_<sup>′</sup> _)_ = | _x_ − _x_<sup>′</sup> | for _x, x_<sup>′</sup> ∈ R in Theorem 4, we obtain the CRPS (21). 

_Example 9_ (Energy score) _._ If _�_ = R<sup>_m_</sup> , _β_ ∈ _(_ 0 _,_ 2 _)_ , and _g(_ **x** _,_ **x**<sup>′</sup> _)_ = ∥ **x** − **x**<sup>′</sup> ∥<sup>_β_</sup> for **x** _,_ **x**<sup>′</sup> ∈ R<sup>_m_</sup> , where ∥· ∥ denotes the Euclidean norm, then (28) recovers the energy score (22). 

_Example 10_ (CRPS for circular variables) _._ We let _�_ = S denote the circle and write _α(θ,θ_<sup>′</sup> _)_ for the angular distance between two points _θ,θ_<sup>′</sup> ∈ S. Let _P_ be a Borel probability measure on S, and let _�_ and _�_<sup>′</sup> be independent random variates with distribution _P_ . By theorem 1 of Gneiting (1998), angular distance is a negative definite kernel. Thus, 



defines a proper scoring rule relative to the class of the Borel probability measures on the circle. Grimit et al. (2006) introduced (30) as an analog of the CRPS (21) that applies to directional variables, and used Fourier analytic tools to prove the propriety of the score. 

We turn to a far-reaching generalization of the energy score. For **x** = _(x_ 1 _,..., xm)_ ∈ R<sup>_m_</sup> and _α_ ∈ _(_ 0 _,_ ∞], define the vector norm ∥ **x** ∥ _α_ = _(_<sup>�</sup><sup>_m_</sup> _i_ =1<sup>|</sup><sup>_xi_|</sup><sup>_α)_1</sup><sup>_/α_if</sup><sup>_α_∈</sup><sup>_(_0</sup><sup>_,_∞</sup><sup>_)_and</sup> ∥ **x** ∥ _α_ = max1≤ _i_ ≤ _m_ | _xi_ | if _α_ = ∞. Schoenberg’s theorem (Berg et al. 1984, p. 74) and a strand of literature culminating in the work of Koldobskiˇı (1992) and Zastavnyi (1993) imply that if _α_ ∈ _(_ 0 _,_ ∞] and _β >_ 0, then the kernel 



is negative definite if and only if the following holds. 

Gneiting and Raftery: Proper Scoring Rules 

369 

_Assumption 1._ Suppose that (a) _m_ = 1, _α_ ∈ _(_ 0 _,_ ∞], and _β_ ∈ _(_ 0 _,_ 2]; (b) _m_ ≥ 2, _α_ ∈ _(_ 0 _,_ 2], and _β_ ∈ _(_ 0 _,α_ ]; or (c) _m_ = 2, _α_ ∈ _(_ 2 _,_ ∞], and _β_ ∈ _(_ 0 _,_ 1]. 

_Example 11_ (Non-Euclidean energy score) _._ Under Assumption 1, the scoring rule 



is proper relative to the class of the Borel probability measures _P_ on R<sup>_m_</sup> for which the expectation _EP_ ∥ **X** − **X**<sup>′</sup> ∥<sup>_β_</sup> _α_<sup>isfi-</sup> nite. If _m_ = 1 or _α_ = 2, then we recover the energy score; if _m_ ≥ 2 and _α_ ̸ = 2, then we obtain non-Euclidean analogs. Mattner (1997, sec. 5.2) showed that if _α_ ≥ 1, then _EP,Q_ ∥ **X** − **Y** ∥ _α_<sup>_β_</sup> is finite if and only if _EP_ ∥ **X** ∥<sup>_β_</sup> _α_<sup>and</sup><sup>_E_</sup> _Q_<sup>∥</sup><sup>**Y**∥</sup> _α_<sup>_β_are finite. In partic-</sup> ular, if _α_ ≥ 1, then _EP_ ∥ **X** − **X**<sup>′</sup> ∥<sup>_β_</sup> _α_<sup>is finite if and only if</sup><sup>_E_</sup> _P_<sup>∥</sup><sup>**X**∥</sup> _α_<sup>_β_</sup> is finite. 

The following result sharpens Theorem 4 in the crucial case of Euclidean sample spaces and spherically symmetric negative definite functions. Recall that a function _η_ on _(_ 0 _,_ ∞ _)_ is said to be _completely monotone_ if it has derivatives _η_<sup>_(k)_</sup> of all orders and _(_ −1 _)_<sup>_k_</sup> _η_<sup>_(k)_</sup> _(t)_ ≥ 0 for all nonnegative integers _k_ and all _t >_ 0. 

_Theorem 5._ Let _ψ_ be a continuous function on [0 _,_ ∞ _)_ with − _ψ_<sup>′</sup> completely monotone and not constant. For a Borel probability measure _P_ on R<sup>_m_</sup> , let **X** and **X**<sup>′</sup> be independent random vectors with distribution _P_ . Then the scoring rule 



is strictly proper relative to the class of the Borel probability measures _P_ on R<sup>_m_</sup> for which _EPψ(_ ∥ **X** − **X**<sup>′</sup> ∥<sup>2</sup> 2<sup>_)_is finite.</sup> 

The proof of this result is immediate from theorem 2.2 of Mattner (1997). In particular, if _ψ(t)_ = _t_<sup>_β/_2</sup> for _β_ ∈ _(_ 0 _,_ 2 _)_ , then Theorem 5 ensures the strict propriety of the energy score relative to the class of the Borel probability measures _P_ on R<sup>_m_</sup> for which _EP_ ∥ **X** ∥<sup>_β_</sup> 2<sup>is finite.</sup> 

## 5.2 Inequalities of Hoeffding Type and Positive Definite Kernels 

A number of side results seem to be of independent interest, even though they are easy consequences of previous work. Briefly, if the expectations _EPg(X, X_<sup>′</sup> _)_ and _EPg(Y, Y_<sup>′</sup> _)_ are finite, then (29) can be written as a Hoeffding-type inequality, 



Theorem 1 of Székely and Rizzo (2005) provides a nearly identical result and a converse: If _g_ is not negative definite, then there are counterexamples to (31), and the respective scoring rule is improper. Furthermore, if _�_ is a group and the negative definite function _g_ satisfies _g(x, x_<sup>′</sup> _)_ = _g(_ − _x,_ − _x_<sup>′</sup> _)_ for _x, x_<sup>′</sup> ∈ _�_ , then a special case of (31) can be stated as 



In particular, if _�_ = R<sup>_m_</sup> and Assumption 1 holds, then inequalities (31) and (32) apply and reduce to 



and 



thereby generalizing results of Buja, Logan, Reeds, and Shepp (1994), Székely (2003), and Baringhaus and Franz (2004). 

In the foregoing case in which _�_ is a group and _g_ satisfies _g(x, x_<sup>′</sup> _)_ = _g(_ − _x,_ − _x_<sup>′</sup> _)_ for _x, x_<sup>′</sup> ∈ _�_ , the argument leading to theorem 2.3 of Buja et al. (1994) and theorem 4 of Ma (2003) implies that 



is a _positive definite kernel_ , in the sense that _h_ is symmetric in its arguments and<sup>�</sup><sup>_n_</sup> _i_ =1 � _nj_ =1<sup>_aiajh(xi,xj)_≥0forallpositive</sup> integers _n_ , all _a_ 1 _,..., an_ ∈ R, and all _x_ 1 _,..., xn_ ∈ _�_ . Specifically, under Assumption 1, 



is a positive definite kernel, a result that extends and completes the aforementioned theorem of Buja et al. (1994). 

## 5.3 Constructions With Complex-Valued Kernels 

With suitable modifications, the foregoing results allow for complex-valued kernels. A complex-valued function _h_ on _�_ × _�_ is said to be a _<u>positive definite kernel</u>_ if it is Hermitian, that is, _h(x, x_<sup>′</sup> _)_ = _h(x_<sup><u>′</u></sup> _, x)_ for _x, x_<sup>′</sup> ∈ _�_ , and<sup>�</sup><sup>_n_</sup> _i_ =1 � _nj_ =1<sup>_ci_</sup> _<u>cjh(xi,</u> xj)_ ≥ 0 for all positive integers _n_ , all _c_ 1 _,..., cn_ ∈ C, and all _x_ 1 _,..., xn_ ∈ _�_ . The general idea (Dawid 1998, 2006) is that if _h_ is continuous and positive definite, then 



defines a proper scoring rule. If _h_ is positive definite, then _g_ = − _h_ is negative definite; thus, if _h_ is real-valued and sufficiently regular, then the scoring rules (37) and (28) are equivalent. 

In the next example, we discuss scoring rules for Borel probability measures and observations on Euclidean spaces. However, the representation (37) allows for the construction of proper scoring rules in more general settings, such as probabilistic forecasts of structured data, including strings, sequences, graphs, and sets, based on positive definite kernels defined on such structures (Hofmann, Schölkopf, and Smola 2005). 

_Example 12._ Let _�_ = R<sup>_m_</sup> and **y** ∈ R<sup>_m_</sup> , and consider the positive definite kernel _h(_ **x** _,_ **x**<sup>′</sup> _)_ = _e_<sup>_i_⟨</sup><sup>**x**−</sup><sup>**x**′</sup><sup>_,_</sup><sup>**y**⟩</sup> − 1, where **x** _,_ **x**<sup>′</sup> ∈ R<sup>_m_</sup> . Then (37) reduces to 



that is, the negative squared distance between the characteristic function of the predictive distribution, _φP_ , and the characteristic function of the point measures in the value that materializes, evaluated at **y** ∈ R<sup>_m_</sup> . If we integrate with respect to a nonnegative measure _µ(_ d **y** _)_ , then the scoring rule (38) generalizes to 



If the measure _µ_ is finite and assigns positive mass to all intervals, then this scoring rule is strictly proper relative to the class of the Borel probability measures on R<sup>_m_</sup> . Eaton, Giovagnoli, and Sebastiani (1996) used the associated divergence function 

Journal of the American Statistical Association, March 2007 

370 

to define metrics for probability measures. If _µ_ is the infinite measure with Lebesgue density ∥ **y** ∥<sup>−</sup><sup>_m_−</sup><sup>_β_</sup> , where _β_ ∈ _(_ 0 _,_ 2 _)_ , then the scoring rule (39) is equivalent to the Euclidean energy score (24). 

## 6. SCORING RULES FOR QUANTILE AND INTERVAL FORECASTS 

Occasionally, full predictive distributions are difficult to specify, and the forecaster might quote predictive quantiles, such as value at risk in financial applications (Duffie and Pan 1997) or prediction intervals (Christoffersen 1998) only. 

## 6.1 Proper Scoring Rules for Quantiles 

We consider probabilistic forecasts of a continuous quantity that take the form of predictive quantiles. Specifically, suppose that the quantiles at the levels _α_ 1 _,...,αk_ ∈ _(_ 0 _,_ 1 _)_ are sought. If the forecaster quotes quantiles _r_ 1 _,..., rk_ and _x_ materializes, then he or she will be rewarded by the score _S(r_ 1 _,..., rk_ ; _x)_ . We define 



as the expected score under the probability measure _P_ when the forecaster quotes the quantiles _r_ 1 _,..., rk_ . To avoid technical complications, we suppose that _P_ belongs to the convex class _P_ of Borel probability measures on R that have finite moments of all orders and whose distribution function is strictly increasing on R. For _P_ ∈ _P_ , let _q_ 1 _,..., qk_ denote the true _P_ -quantiles at levels _α_ 1 _,...,αk_ . Following Cervera and Muñoz (1996), we say that a scoring rule _S_ is _proper_ if 



for all real numbers _r_ 1 _,..., rk_ and for all probability measures _P_ ∈ _P_ . If _S_ is proper, then the forecaster who wishes to maximize the expected score is encouraged to be honest and to volunteer his or her true beliefs. 

To avoid technical overhead, we tacitly assume _P_ -integrability whenever appropriate. Essentially, we require that the functions _s(x)_ and _h(x)_ in (40) and (42) be _P_ -measurable and grow at most polynomially in _x_ . Theorem 6 addresses the prediction of a single quantile; Corollary 1 turns to the general case. 

_Theorem 6._ If _s_ is nondecreasing and _h_ is arbitrary, then the scoring rule 



is proper for predicting the quantile at level _α_ ∈ _(_ 0 _,_ 1 _)_ . 

_Proof._ Let _q_ be the unique _α_ -quantile of the probability measure _P_ ∈ _P_ . We identify _P_ with the associated distribution function so that _P(q)_ = _α_ . If _r < q_ , then 



as desired. If _r > q_ , then an analogous argument applies. 



which has been proposed by Koenker and Machado (1999), Taylor (1999), Giacomini and Komunjer (2005), Theis (2005, p. 232), and Friederichs and Hense (2006) for measuring insample goodness of fit and out-of-sample forecast performance in meteorological and financial applications. In negative orientation, the econometric literature refers to the scoring rule (41) as the _tick_ or _check_ loss function. 

_Corollary 1._ If _si_ is nondecreasing for _i_ = 1 _,..., k_ and _h_ is arbitrary, then the scoring rule 

_S(r_ 1 _,..., rk_ ; _x)_ 



is proper for predicting the quantiles at levels _α_ 1 _,...,αk_ ∈ _(_ 0 _,_ 1 _)_ . 

Cervera and Muñoz (1996, pp. 515 and 519) proved Corollary 1 in the special case in which each _si_ is linear. They asked whether the resulting rules are the only proper ones for quantiles. Our results give a negative answer; that is, the class of proper scoring rules for quantiles is considerably larger than anticipated by Cervera and Muñoz. We do not know whether or not (40) and (42) provide the general form of proper scoring rules for quantiles. 

## 6.2 Interval Score 

Interval forecasts form a crucial special case of quantile prediction. We consider the classical case of the central _(_ 1 − _α)_ × 100% prediction interval, with lower and upper endpoints that are the predictive quantiles at level<sup>_<u>α</u>_</sup> 2<sup>and1 −</sup><sup>_<u>α</u>_</sup> 2<sup>. We denote a</sup> scoring rule for the associated interval forecast by _Sα(l, u_ ; _x)_ , where _l_ and _u_ represent for the quoted<sup>_<u>α</u>_</sup> 2<sup>and1 −</sup><sup>_<u>α</u>_</sup> 2<sup>quantiles.</sup> Thus, if the forecaster quotes the _(_ 1 − _α)_ × 100% central prediction interval [ _l, u_ ] and _x_ materializes, then his or her score will be _Sα(l, u_ ; _x)_ . Putting _α_ 1 =<sup>_<u>α</u>_</sup> 2<sup>,</sup><sup>_α_2 = 1 −</sup><sup>_<u>α</u>_</sup> 2<sup>,</sup><sup>_s_1</sup><sup>_(x)_=</sup><sup>_s_2</sup><sup>_(x)_= 2</sup> _α_<sup>_<u>x</u>_,</sup> and _h(x)_ = −2 _α_<sup>_<u>x</u>_in(42),andreversingthesignofthescoring</sup> rule, yields the negatively oriented _interval score_ , 

_Sα_<sup>int</sup><sup>_(l,u_;</sup><sup>_x)_</sup> 



This scoring rule has intuitive appeal and can be traced back to Dunsmore (1968), Winkler (1972), and Winkler and Murphy (1979). The forecaster is rewarded for narrow prediction intervals, and he or she incurs a penalty, the size of which depends on _α_ , if the observation misses the interval. In the case _α_ =<sup><u>1</u></sup> 2<sup>, Hamill and Wilks (1995, p. 622) used a scoring rule that</sup> is equivalent to the interval score. They noted that “a strategy for gaming [...] was not obvious,” thereby conjecturing propriety, which is confirmed by the foregoing. We anticipate novel applications, particularly for the evaluation of volatility forecasts in computational finance. 

Gneiting and Raftery: Proper Scoring Rules 

371 

## 6.3 Case Study: Interval Forecasts for a Conditionally Heteroscedastic Process 

This section illustrates the use of the interval score in a time series context. Kabaila (1999) called for rigorous ways of specifying prediction intervals for conditionally heteroscedastic processes and proposed a relevance criterion in terms of conditional coverage and width dependence. We contend that the notion of proper scoring rules provides an alternative and possibly simpler, more general, and more rigorous paradigm. The prediction intervals that we deem appropriate derive from the true conditional distribution, as implied by the data-generating mechanism, and optimize the expected value of all proper scoring rules. 

To fix the idea, consider the stationary bilinear process { _Xt_ : _t_ ∈ Z} defined by 



where the _ϵt_ ’s are independent standard Gaussian random variates. Kabaila and He (2001) studied central one-step-ahead prediction intervals at the 95% level. The process is Markovian, and the conditional distribution of _Xt_ +1 given _Xt, Xt_ −1 _,..._ is Gaussian with mean<sup><u>1</u></sup> 2<sup>_Xt_and variance</sup><sup>_(_1 +</sup><sup><u>1</u></sup> 2<sup>_Xt)_2, thereby sug-</sup> gesting the prediction interval 



where _c_ = _�_<sup>−1</sup> _(._ 975 _)_ . This interval satisfies the relevance property of Kabaila (1999), and Kabaila and He (2001) adopted _I_ as the standard prediction interval. We agree with this choice, but we prefer the aforementioned more direct justification; the prediction interval _I_ is the standard interval because its lower and upper endpoints are the 2 _._ 5% and 97 _._ 5% percentiles of the true conditional distribution function. Kabaila and He considered two alternative prediction intervals, 



where _F_ denotes the unconditional, stationary distribution function of _Xt_ , and 



where _γ (y)_ = _(_ 2 _(_ log7 _._ 36 − log _y))_<sup>1</sup><sup>_/_2</sup> _y_ for _y_ ≤ 7 _._ 36 and _γ (y)_ = 0 otherwise. This choice minimizes the expected width of the prediction interval under the constraint of nominal coverage. However, the interval forecast _K_ seems misguided, in that it collapses to a point forecast when the conditional predictive variance is highest. 

We generated a sample path { _Xt_ : _t_ = 1 _,...,_ 100 _,_ 001} from the bilinear process (44) and considered sequential one-stepahead interval forecasts for _Xt_ +1, where _t_ = 1 _,...,_ 100 _,_ 000. Table 2 summarizes the results of this experiment. The interval forecasts _I_ , _J_ , and _K_ all showed close to nominal coverage, with the prediction interval _K_ being sharpest on average. Nevertheless, the classical prediction interval _I_ performed best in terms of the interval score. 

Table 2. Comparison of One-Step-Ahead 95% Interval Forecasts for the Stationary Bilinear Process (44) 

|Interval<br>forecast||Empirical<br>coverage|Average<br>width|Average<br>interval score|
|---|---|---|---|---|
|I|(45)|95.01%|4.00|4.77|
|J|(46)|95.08%|5.45|8.04|
|K|(47)|94.98%|3.79|5.32|



NOTE: The table shows the empirical coverage, the average width, and the average value of the negatively oriented interval score (43) for the prediction intervals I, J, and K in 100,000 sequential forecasts in a sample path of length 100,001. See text for details. 

## 6.4 Scoring Rules for Distributional Forecasts 

Specifying a predictive cumulative distribution function is equivalent to specifying all predictive quantiles; thus we can build scoring rules for predictive distributions from scoring rules for quantiles. Matheson and Winkler (1976) and Cervera and Muñoz (1996) suggested ways of doing this. Specifically, if _Sα_ denotes a proper scoring rule for the quantile at level _α_ and _ν_ is a Borel measure on _(_ 0 _,_ 1 _)_ , then the scoring rule 



is proper, subject to regularity and integrability constraints. Similarly, we can build scoring rules for predictive distributions from scoring rules for binary probability forecasts. If _S_ denotes a proper scoring rule for probability forecasts and _ν_ is a Borel measure on R, then the scoring rule 



is proper, subject to integrability constraints (Matheson and Winkler 1976; Gerds 2002). The CRPS (20) corresponds to the special case in (49) in which _S_ is the quadratic or Brier score and _ν_ is the Lebesgue measure. If _S_ is the Brier score and _ν_ is a sum of point measures, then the ranked probability score (Epstein 1969) emerges. 

The construction carries over to multivariate settings. If _P_ denotes the class of the Borel probability measures on R<sup>_m_</sup> , then we identify a probabilistic forecast _P_ ∈ _P_ with its cumulative distribution function _F_ . A multivariate analog of the CRPS can be defined as 



This is a weighted integral of the Brier scores at all _m_ -variate thresholds. The Borel measure _ν_ can be chosen to encourage the forecaster to concentrate his or her efforts on the important ones. If _ν_ is a finite measure that dominates the Lebesgue measure, then this scoring rule is strictly proper relative to the class _P_ . 

## 7. SCORING RULES, BAYES FACTORS, AND RANDOM–FOLD CROSS–VALIDATION 

We now relate proper scoring rules to Bayes factors and to cross-validation and propose a novel form of cross-validation: random-fold cross-validation. 

Journal of the American Statistical Association, March 2007 

372 

## 7.1 Logarithmic Score and Bayes Factors 

Probabilistic forecasting rules are often generated by probabilistic models, and the standard Bayesian approach to comparing probabilistic models is by Bayes factors. Suppose that we have a sample **X** = _(X_ 1 _,..., Xn)_ of values to be forecast. Suppose also that we have two forecasting rules, based on probabilistic models _H_ 1 and _H_ 2. So far in this article we have concentrated on the situation where the forecasting rule is completely specified before any of the _Xi_ ’s are observed; that is, there are no parameters to be estimated from the data being forecast. In that situation, the _Bayes factor_ for _H_ 1 against _H_ 2 is 



where _P(_ **X** | _Hk)_ =<sup>�</sup><sup>_n_</sup> _i_ =1<sup>_P(Xi_|</sup><sup>_Hk)_for</sup><sup>_k_= 1</sup><sup>_,_2(Jeffreys1939;</sup> Kass and Raftery 1995). 

Thus, if the logarithmic score is used, then the log Bayes factor is the difference of the scores for the two models, 



This was pointed out by Good (1952), who called the log Bayes factor the _weight of evidence_ . It establishes two connections: (1) the Bayes factor is equivalent to the logarithmic score in this no-parameter case, and (2) the Bayes factor applies more generally than merely to the comparison of parametric probabilistic models, but also to the comparison of probabilistic forecasting rules of any kind. 

So far in this article we have taken probabilistic forecasts to be fully specified, but often they are specified only up to unknown parameters estimated from the data. Now suppose that the forecasting rules considered are specified only up to unknown parameters, _θk_ for _Hk_ , to be estimated from the data. Then the Bayes factor is still given by (50), but now _P(_ **X** | _Hk)_ is the _integrated likelihood_ , 



where _p(_ **X** | _θk, Hk)_ is the (usual) likelihood under model _Hk_ , and _p(θk_ | _Hk)_ is the prior distribution of the parameter _θk_ . 

Dawid (1984) showed that when the data come in a particular order, such as time order, the integrated likelihood can be reformulated in predictive terms, 



where **X**<sup>_t_−1</sup> = { _X_ 1 _,..., Xt_ −1} if _t_ ≥ 1, _X_<sup>0</sup> is the empty set and _P(Xt_ | **X**<sup>_t_−1</sup> _, Hk)_ is the predictive distribution of _Xt_ given the past values under _Hk_ , namely 



with _P(θk_ | **X**<sup>_t_−1</sup> _, Hk)_ the posterior distribution of _θk_ given the past observations **X**<sup>_t_−1</sup> . 

We let _Sk,B_ = log _P(_ **X** | _Hk)_ denote the log-integrated likelihood, viewed now as a scoring rule. To view it as a scoring rule it helps to rewrite it as 



Dawid (1984) showed that _Sk,B_ is asymptotically equivalent to the plug-in maximum likelihood prequential score 



where _θ_<sup>ˆ</sup> _k_<sup>_t_−1</sup> is the maximum likelihood estimator (MLE) of _θk_ based on the past observations, **X**<sup>_t_−1</sup> , in the sense that _Sk,D/Sk,B_ → 1 as _n_ →∞. Initial terms for which _θ_<sup>ˆ</sup> _k_<sup>_t_−1</sup> is possibly undefined can be ignored. Dawid also showed that _Sk,B_ is asymptotically equivalent to the Bayes information criterion (BIC) score, 



where _dk_ = dim _(θk)_ , in the same sense, namely _Sk,_ BIC _/Sk,B_ → 1 as _n_ →∞. This justifies using the BIC for comparing forecasting rules, extending the previous justification of Schwarz (1978), which related only to comparing models. 

These results have two limitations, however. First, they assume that the data come in a particular order. Second, they use only the logarithmic score, not other scores that might be more appropriate for the task at hand. We now briefly consider how these limitations might be addressed. 

## 7.2 Scoring Rules and Random-Fold Cross-Validation 

Suppose now that the data are unordered. We can replace (53) by 



where _D_ is a random sample from {1 _,..., t_ − 1 _, t_ + 1 _,..., n_ }, the size of which is a random variable with a discrete uniform distribution on {0 _,_ 1 _,..., n_ − 1}. Dawid’s results imply that this is asymptotically equivalent to the plug-in maximum likelihood version, 



where _θ_<sup>ˆ</sup> _k_<sup>_(D)_</sup> is the MLE of _θk_ based on **X**<sup>_(D)_</sup> . Terms for which the size of _D_ is small and _θ_<sup>ˆ</sup> _k_<sup>_(D)_</sup> is possibly undefined can be ignored. 

The formulations (55) and (56) may be useful because they turn a score that was a sum of nonidentically distributed terms into one that is a sum of identically distributed exchangeable terms. This opens the possibility of evaluating _Sk_<sup>∗</sup> _,B_<sup>or</sup><sup>_S_</sup> _k_<sup>∗</sup> _,D_ by Monte Carlo, which would be a form of cross-validation. In this cross-validation, the amount of data left out would be random rather than fixed, leading us to call it _random-fold cross-validation_ . Smyth (2000) used the log-likelihood as the criterion function in cross-validation, as here, calling the resulting method cross-validated likelihood, but used a fixed holdout sample size. This general approach can be traced back at least to Geisser and Eddy (1979). One issue in cross-validation generally is how much data to leave out; different choices lead to different versions of cross-validation, such as leave-one-out, 

Gneiting and Raftery: Proper Scoring Rules 

373 

10-fold, and so on. Considering versions of cross-validation in the context of scoring rules may shed some light on this issue. 

We have seen by (51) that when there are no parameters being estimated, the Bayes factor is equivalent to the difference in the logarithmic score. Thus we could replace the logarithmic score by another proper score, and the difference in scores could be viewed as a kind of predictive Bayes factor with a different type of score. In _Sk,B_ , _Sk,D_ , _Sk,_ BIC, _Sk_<sup>∗</sup> _,B_<sup>,and</sup><sup>_S_</sup> _k_<sup>∗</sup> _,D_<sup>,wecould</sup> replace the terms in the sums (each of which has the form of a logarithmic score) by another proper scoring rule, such as the CRPS, and we conjecture that similar asymptotic equivalences would remain valid. 

## 8. CASE STUDY: PROBABILISTIC FORECASTS OF SEA–LEVEL PRESSURE OVER THE NORTH AMERICAN PACIFIC NORTHWEST 

Our goals in this case study are to illustrate the use and the properties of scoring rules and to demonstrate the importance of propriety. 

## 8.1 Probabilistic Weather Forecasting Using Ensembles 

Operational probabilistic weather forecasts are based on _ensemble prediction systems_ . Ensemble systems typically generate a set of perturbations of the best estimate of the current state of the atmosphere, run each of them forward in time using a numerical weather prediction model, and use the resulting set of forecasts as a sample from the predictive distribution of future weather quantities (Palmer 2002; Gneiting and Raftery 2005). 

Grimit and Mass (2002) described the University of Washington ensemble prediction system over the Pacific Northwest, which covers Oregon, Washington, British Columbia, and parts of the Pacific Ocean. This is a five-member ensemble comprising distinct runs of the MM5 numerical weather prediction model with initial conditions taken from distinct national and international weather centers. We consider 48-hour-ahead forecasts of sea-level pressure in January–June 2000, the same period as that on which the work of Grimit and Mass was based. The unit used is the millibar (mb). Our analysis builds on a verification data base of 16,015 records scattered over the North American Pacific Northwest and the aforementioned 6-month period. Each record consists of the five ensemble member forecasts and the associated verifying observation. The root mean squared error of the ensemble mean forecast was 3.30 mb, and the square root of the average variance of the five-member forecast ensemble was 2.13 mb, resulting in a ratio of _r_ 0 = 1 _._ 55. 

This underdispersive behavior—that is, observed errors that tend to be larger on average than suggested by the ensemble spread—is typical of ensemble systems and seems unavoidable, given that ensembles capture only some of the sources of uncertainty (Raftery, Gneiting, Balabdaoui, and Polakowski 2005). Thus, to obtain calibrated predictive distributions, it seems necessary to carry out some form of statistical postprocessing. One natural approach is to take the predictive distribution for sealevel pressure at any given site as Gaussian, centered at the ensemble mean forecast, and with predictive standard deviation equal to _r_ times the standard deviation of the forecast ensemble. Density forecasts of this type were proposed by Déqué, Royer, and Stroe (1994) and Wilks (2002). Following Wilks, we refer to _r_ as an _inflation factor_ . 

## 8.2 Evaluation of Density Forecasts 

In the aforementioned approach, the predictive density is Gaussian, say _ϕµ,rσ_ ; its mean, _µ_ , is the ensemble mean forecast, and its standard deviation, _rσ_ , is the product of the inflation factor, _r_ , and the standard deviation of the five-member forecast ensemble, _σ_ . We considered various scoring rules _S_ and computed the average score, 



as a function of the inflation factor _r_ . The index _i_ refers to the _i_ th record in the verification database, and _xi_ denotes the value that materialized. Given the underdispersive character of the ensemble system, we expect _s(r)_ to be maximized at some _r >_ 1, possibly near the observed ratio, _r_ 0 = 1 _._ 55, of the root mean squared error of the ensemble mean forecast over the square root of the average ensemble variance. 

We computed the mean score (57) for inflation factors _r_ ∈ _(_ 0 _,_ 5 _)_ and for the quadratic score (QS), spherical score (SphS), logarithmic score (LogS), CRPS, linear score (LinS), and probability score (PS), as defined in Section 4. Briefly, if _p_ denotes the predictive density and _x_ denotes the observed value, then 





and 



Figure 3 and Table 3 summarize the results of this experiment. The scores shown in the figure are linearly transformed, so that the graphs can be compared side by side, and the transformations are listed in the rightmost column of the table. In the case of the quadratic score, for instance, we plotted 40 times the value in (57) plus 6. Clearly, transformed and original scores are equivalent in the sense of (2). The quadratic score, spherical score, logarithmic score and CRPS were maximized at values of _r >_ 1, thereby confirming the underdispersive character of 

Table 3. Probabilistic Forecasts of Sea-Level Pressure Over the North American Pacific Northwest in January–July 2000 

|Score|Argmaxrs(r)<br>in eq. (57)|Linear transformation<br>plotted in Figure 3|
|---|---|---|
|Quadratic score (QS)|2.18|40s+6|
|Spherical score (SphS)|1.84|108s−22|
|Logarithmic score (LogS)|2.41|s+13|
|CRPS|1.62|10s+8|
|Linear score (LinS)|.05|105s−5|
|Probability score (PS)|.02|60s−5|



NOTE: The predictive density is Gaussian, centered at the ensemble mean forecast, and with predictive standard deviation equal to r times the standard deviation of the forecast ensemble. 

Journal of the American Statistical Association, March 2007 

374 



Figure 3. Probabilistic Forecasts of Sea-Level Pressure Over the North American Pacific Northwest in January–July 2000. The scores are shown as a function of the inflation factor r, where the predictive density is Gaussian, centered at the ensemble mean forecast, and with predictive standard deviation equal to r times the standard deviation of the forecast ensemble. The scores were subject to linear transformations as detailed in Table 3. 

the ensemble. These scores are proper. The linear and probability scores were maximized at _r_ = _._ 05 and _r_ = _._ 02, thereby suggesting ignorable forecast uncertainty and essentially deterministic forecasts. The latter two scores have intuitive appeal, and the probability score has been used to assess forecast ensembles (Wilson et al. 1999). However, they are improper, and their use may result in misguided scientific inferences, as in this experiment. A similar comment applies to the predictive model choice criterion given in Section 4.4. 

It is interesting to observe that the logarithmic score gave the highest maximizing value of _r_ . The logarithmic score is strictly proper but involves a harsh penalty for low probability events and thus is highly sensitive to extreme cases. Our verification database includes a number of low-spread cases for which the ensemble variance implodes. The logarithmic score penalizes the resulting predictions unless the inflation factor _r_ is large. Weigend and Shi (2000, p. 382) noted similar concerns and considered the use of trimmed means when computing the logarithmic score. In our experience, the CRPS is less sensitive to extreme cases or outliers and provides an attractive alternative. 

## 8.3 Evaluation of Interval Forecasts 

The aforementioned predictive densities also provide interval forecasts. We considered the central _(_ 1 − _α)_ × 100% prediction interval where _α_ = _._ 50 and _α_ = _._ 10. The associated lower and upper prediction bounds _li_ and _ui_ are the<sup>_<u>α</u>_</sup> 2<sup>and 1 −</sup><sup>_<u>α</u>_</sup> 2<sup>quantiles</sup> of a Gaussian distribution with mean _µi_ and standard deviation _rσi_ , as described earlier. We assessed the interval forecasts in 

their dependence on the inflation factor _r_ in two ways: by computing the empirical coverage of the prediction intervals and by computing 



where _Sα_<sup>intdenotesthenegativelyorientedintervalscore(43).</sup> This scoring rule assesses both calibration and sharpness, by rewarding narrow prediction intervals and penalizing intervals missed by the observation. Figure 4(a) shows the empirical coverage of the interval forecasts. Clearly, the coverage increases with _r_ . For _α_ = _._ 50 and _α_ = _._ 10, the nominal coverage was obtained at _r_ = 1 _._ 78 and _r_ = 2 _._ 11, which confirms the underdispersive character of the ensemble. Figure 4(b) shows the interval score (58) as a function of the inflation factor _r_ . For _α_ = _._ 50 and _α_ = _._ 10, the score was optimized at _r_ = 1 _._ 56 and _r_ = 1 _._ 72. 

## 9. OPTIMUM SCORE ESTIMATION 

Strictly proper scoring rules also are of interest in estimation problems, where they provide attractive loss and utility functions that can be adapted to the problem at hand. 

## 9.1 Point Estimation 

We return to the generic estimation problem described in Section 1. Suppose that we wish to fit a parametric model _Pθ_ based on a sample _X_ 1 _,..., Xn_ of identically distributed observations. To estimate _θ_ , we can measure the goodness of fit by 

Gneiting and Raftery: Proper Scoring Rules 

375 

(a) 





<!-- Start of picture text -->
(b)<br><!-- End of picture text -->



Figure 4. Interval Forecasts of Sea-Level Pressure Over the North American Pacific Northwest in January–July 2000. (a) Nominal and actual coverage and (b) the negatively oriented interval score (58), for the 50% central prediction interval ( _α_ = .50, - - -) and the 90% central prediction interval ( _α_ = .10, —; score scaled by a factor of .60). The predictive density is Gaussian, centered at the ensemble mean forecast, and with predictive standard deviation equal to r times the standard deviation of the forecast ensemble. 

the mean score 



where _S_ is a scoring rule that is strictly proper relative to a convex class of probability measures that contains the parametric model. If _θ_ 0 denotes the true parameter value, then asymptotic arguments indicate that 



This suggests a general approach to estimation: Choose a strictly proper scoring rule tailored to the problem at hand and take _θ_<sup>ˆ</sup> _n_ = argmax _θ Sn(θ)_ as the respective _optimum score estimator_ . The first four values of the argmax in Table 3, for instance, refer to the optimum score estimates of the inflation factor _r_ based on the logarithmic score, spherical score, quadratic score, and CRPS. Pfanzagl (1969) and Birgé and Massart (1993) studied optimum score estimators under the heading of _minimum contrast estimators_ . This class includes many of the most popular estimators in various situations, such as MLEs, least squares and other estimators of regression models, and estimators for mixture models or deconvolution. Pfanzagl (1969) proved rigorous versions of the consistency result (59), and Birgé and Massart (1993) related rates of convergence to the entropy structure of the parameter space. Maximum likelihood estimation forms the special case of optimum score estimation based on the logarithmic score, and optimum score estimation forms a special case of _M_ -estimation (Huber 1964), in that the function to be optimized derives from a strictly proper scoring rule. When estimating the location parameter in 

a Gaussian population with known variance, for example, the optimum score estimator based on the CRPS amounts to an _M_ - estimator with a _ψ_ -function of the form _ψ(x)_ = 2 _�(_<sup>_<u>x</u>_</sup> _c_<sup>_)_−1,</sup> where _c_ is a positive constant and _�_ denotes the standard Gaussian cumulative. This provides a smooth version of the _ψ_ - function for Huber’s (1964) robust minimax estimator (see Huber 1981, p. 208). Asymptotic results for _M_ -estimators, such as the consistency theorems of Huber (1967) and Perlman (1972), then apply to optimum scores estimators as well. Wald’s (1949) classical proof of the consistency of MLEs relies heavily on the strict propriety of the logarithmic score, which is proved in his lemma 1. 

The appeal of optimum score estimation lies in the potential adaption of the scoring rule to the problem at hand. Gneiting et al. (2005) estimated a predictive regression model using the optimum score estimator based on the CRPS—a choice motivated by the meteorological problem. They showed empirically that such an approach can yield better predictive results than approaches using maximum likelihood plug-in estimates. This agrees with the findings of Copas (1983) and Friedman (1989), who showed that the use of maximum likelihood and least squares plug-in estimates can be suboptimal in prediction problems. Buja et al. (2005) argued that strictly proper scoring rules are the natural loss functions or fitting criteria in binary class probability estimation, and proposed tailoring scoring rules in situations in which false positives and false negatives have different cost implications. 

## 9.2 Quantile Estimation 

Koenker and Bassett (1978) proposed quantile regression using an optimum score estimator based on the proper scoring rule (41). 

Journal of the American Statistical Association, March 2007 

376 

## 9.3 Interval Estimation 

We now turn to interval estimation. Casella, Hwang, and Robert (1993, p. 141) pointed out that “the question of measuring optimality (either frequentist or Bayesian) of a set estimator against a loss criterion combining size and coverage does not yet have a satisfactory answer.” 

Their work was motivated by an apparent paradox due to J. O. Berger, which concerns interval estimators of the location parameter _θ_ in a Gaussian population with unknown scale. Under the loss function 



where _c_ is a positive constant and _λ(I)_ denotes the Lebesgue measure of the interval estimate _I_ , the classical _t_ -interval is dominated by a misguided interval estimate that shrinks to the sample mean in the cases of the highest uncertainty. Casella et al. (1993, p. 145) commented that “we have a case where a disconcerting rule dominates a time honored procedure. The only reasonable conclusion is that there is a problem with the loss function.” We concur, and propose using proper scoring rules to assess interval estimators based on a loss criterion that combines width and coverage. 

Specifically, we contend that a meaningful comparison of interval estimators requires either equal coverage or equal width. The loss function (60) applies to all set estimates, regardless of coverage and size, which seems unnecessarily ambitious. Instead, we focus attention on interval estimators with equal nominal coverage and use the negatively oriented interval score (43). This loss function can be written as 



and applies to interval estimates with upper and lower exceedance probability<sup>_<u>α</u>_</sup> 2<sup>× 100%.Thisapproachcanagainbe</sup> traced back to Dunsmore (1968) and Winkler (1972) and avoids paradoxes, as a consequence of the propriety of the interval score. Compared with (60), the loss function (61) provides a more flexible assessment of the coverage, by taking the distance between the interval estimate and the estimand into account. 10. AVENUES FOR FUTURE WORK Our paper aimed to bring proper scoring rules to the attention of a broad statistical and general scientific audience. Proper scoring rules lie at the heart of much statistical theory and practice, and we have demonstrated ways in which they bear on prediction and estimation. We close with a succinct, necessarily incomplete, and subjective discussion of directions for future work. 

Theoretically, the relationships between proper scoring rules and divergence functions are not fully understood. The Savage representation (10), Schervish’s Choquet-type representation (14), and the underlying geometric arguments surely allow generalizations, and the characterization of proper scoring rules for quantiles remains open. Little is known about the propriety of skill scores, despite Murphy’s (1973) pioneering work and their ubiquitous use by meteorologists. Briggs and Ruppert (2005) have argued that skill score departures from propriety do little harm. Although we tend to agree, there is a need for follow-up studies. Diebold and Mariano (1995), Hamill (1999), 

Briggs (2005), Briggs and Ruppert (2005), and Jolliffe (2006) have developed formal tests of forecast performance, skill, and value. This is a promising avenue for future work, particularly in concert with biomedical applications (Pepe 2003; Schumacher, Graf, and Gerds 2003). Proper scoring rules form key tools within the broader framework of diagnostic forecast evaluation (Murphy and Winkler 1992; Gneiting et al. 2006), and in addition to hydrometeorological and biomedical uses, we see a wealth of potential applications in computational finance. 

Guidelines for the selection of scoring rules are in strong demand, both for the assessment of predictive performance and in optimum score approaches to estimation. The tailoring approach of Buja et al. (2005) applies to binary class probability estimation, and we wonder whether it can be generalized. Last but not least, we anticipate novel applications of proper scoring rules in model selection and model diagnosis problems, particularly in prequential (Dawid 1984) and cross-validatory frameworks, and including Bayesian posterior predictive distributions and Markov chain Monte Carlo output (Gschlößl and Czado 2005). More traditional approaches to model selection such as Bayes factors (Kass and Raftery 1995), the Akaike information criterion, the BIC, and the deviance information criterion (Spiegelhalter, Best, Carlin, and van der Linde 2002) are likelihood-based and relate to the logarithmic scoring rule, as discussed in Section 7. We would like to know more about their relationships to cross-validatory approaches based directly on proper scoring rules, including, but not limited to, the logarithmic rule. 

## APPENDIX: STATISTICAL DEPTH FUNCTIONS 

Statistical depth functions (Zuo and Serfling 2000) provide useful tools in nonparametric inference for multivariate data. In Section 1 we hinted at a superficial analogy to scoring rules. Specifically, if _P_ is a Borel probability measure on R<sup>_m_</sup> , then a _depth function D(P,_ **x** _)_ gives a _P_ -based center-outward ordering of points **x** ∈ R<sup>_m_</sup> . Formally, this resembles a scoring rule _S(P,_ **x** _)_ that assigns a _P_ -based numerical value to an event **x** ∈ R<sup>_m_</sup> . Liu (1990) and Zuo and Serfling (2000) have listed desirable properties of depth functions, including maximality at the center, monotonicity relative to the deepest point, affine invariance, and vanishing at infinity. The latter two properties are not necessarily defendable requirements for scoring rules; conversely, propriety is irrelevant for depth functions. 

_[Received December 2005. Revised September 2006.]_ 

## REFERENCES 

Baringhaus, L., and Franz, C. (2004), “On a New Multivariate Two-Sample Test,” _<u>Journal of Multivariate Analysis</u>_ <u>, 88, 190–206.</u> 

Bauer, H. (2001), _Measure and Integration Theory_ , Berlin: Walter de Gruijter. Berg, C., Christensen, J. P. R., and Ressel, P. (1984), _Harmonic Analysis on Semigroups_ , New York: Springer-Verlag. 

Bernardo, J. M. (1979), “Expected Information as Expected Utility,” _The Annals of Statistics_ <u>, 7, 686–690.</u> 

Bernardo, J. M., and Smith, A. F. M. (1994), _Bayesian Theory_ , New York: Wiley. 

Besag, J., Green, P., Higdon, D., and Mengersen, K. (1995), “Bayesian Computing and Stochastic Systems,” _<u>Statistical Science</u>_ <u>, 10, 3–66.</u> 

Birgé, L., and Massart, P. (1993), “Rates of Convergence for Minimum Contrast Estimators,” _<u>Probability Theory and Related Fields</u>_ <u>, 97, 113–150.</u> 

Bregman, L. M. (1967), “The Relaxation Method of Finding the Common Point of Convex Sets and Its Application to the Solution of Problems in Convex Programming,” _USSR Computational Mathematics and Mathematical Physics_ , 7, 200–217. 

Gneiting and Raftery: Proper Scoring Rules 

377 

Bremnes, J. B. (2004), “Probabilistic Forecasts of Precipitation in Terms of Quantiles Using NWP Model Output,” _Monthly_ _<u>Weather</u> Review_ <u>,</u> 132, 338–347. 

- Brier, G. W. (1950), “Verification of Forecasts Expressed in Terms of Probability,” _Monthly Weather Review_ <u>, 78, 1–3.</u> 

- Briggs, W. (2005), “A General Method of Incorporating Forecast Cost and Loss in Value Scores,” _Monthly Weather Review_ <u>, 133, 3393–3397.</u> 

- Briggs, W., and Ruppert, D. (2005), “Assessing the Skill of Yes/No Predictions,” _<u>Biometrics</u>_ <u>, 61, 799–807.</u> 

- Buja, A., Logan, B. F., Reeds, J. A., and Shepp, L. A. (1994), “Inequalities and Positive-Definite Functions Arising From a Problem in Multidimensional Scaling,” _The Annals of_ _<u>Statistics</u>_ <u>, 22, 406–438.</u> 

- Buja, A., Stuetzle, W., and Shen, Y. (2005), “Loss Functions for Binary Class Probability Estimation and Classification: Structure and Applications,” manuscript, available at _<u>www-stat.wharton.upenn.edu/~buja/.</u>_ 

- Campbell, S. D., and Diebold, F. X. (2005), “Weather Forecasting for Weather Derivatives,” _<u>Journal of the American Statistical Association</u>_ <u>, 100, 6–16.</u> 

- Candille, G., and Talagrand, O. (2005), “Evaluation of Probabilistic Prediction Systems for a Scalar Variable,” _<u>Quarterly Journal of the Royal Meteorological Society</u>_ <u>, 131, 2131–2150.</u> 

- Casella, G., Hwang, J. T. G., and Robert, C. (1993), “A Paradox in DecisionTheoretic Interval Estimation,” _Statistica Sinica_ , 3, 141–155. 

- Cervera, J. L., and Muñoz, J. (1996), “Proper Scoring Rules for Fractiles,” in _Bayesian Statistics 5_ , eds. J. M. Bernardo, J. O. Berger, A. P. Dawid, and A. F. M. Smith, Oxford, U.K.: Oxford University Press, pp. 513–519. 

- Christoffersen, P. F. (1998), “Evaluating Interval Forecasts,” _<u>International Economic Review</u>_ <u>, 39, 841–862.</u> 

- Collins, M., Schapire, R. E., and Singer, J. (2002), “Logistic Regression, AdaBoost and Bregman Distances,” _<u>Machine Learning</u>_ <u>, 48, 253–285.</u> 

- Copas, J. B. (1983), “Regression, Prediction and Shrinkage,” _Journal of the Royal Statistical Society_ , Ser. B, 45, 311–354. 

- Daley, D. J., and Vere-Jones, D. (2004), “Scoring Probability Forecasts for Point Processes: The Entropy Score and Information Gain,” _Journal of Applied Probability_ , 41A, 297–312. 

- Dawid, A. P. (1984), “Statistical Theory: The Prequential Approach,” _Journal of the Royal Statistical Society_ , Ser. A, 147, 278–292. 

- (1986), “Probability Forecasting,” in _Encyclopedia of Statistical Sci-_ 

- _ences_ , Vol. 7, eds. S. Kotz, N. L. Johnson, and C. B. Read, New York: Wiley, pp. 210–218. 

(1998), “Coherent Measures of Discrepancy, Uncertainty and Dependence, With Applications to Bayesian Predictive Experimental Design,” Research Report 139, University College London, Dept. of Statistical Science. 

- (2006), “The Geometry of Proper Scoring Rules,” Research Report 

- 268, University College London, Dept. of Statistical Science. 

- Dawid, A. P., and Sebastiani, P. (1999), “Coherent Dispersion Criteria for Optimal Experimental Design,” _<u>The Annals of Statistics</u>_ <u>, 27, 65–81.</u> 

- Déqué, M., Royer, J. T., and Stroe, R. (1994), “Formulation of Gaussian Probability Forecasts Based on Model Extended-Range Integrations,” _Tellus_ , Ser. A, 46, 52–65. 

- Diebold, F. X., and Mariano, R. S. (1995), “Comparing Predictive Accuracy,” _Journal of Business & Economic Statistics_ <u>, 13, 253–263.</u> 

- Duffie, D., and Pan, J. (1997), “An Overview of Value at Risk,” _Journal of Derivatives_ , 4, 7–49. 

- Dunsmore, I. R. (1968), “A Bayesian Approach to Calibration,” _Journal of the Royal Statistical Society_ , Ser. B, 30, 396–405. 

- Eaton, M. L. (1982), “A Method for Evaluating Improper Prior Distributions,” in _Statistical Decision Theory and Related Topics III_ , eds. S. S. Gupta and J. O. Berger, New York: Academic Press, pp. 329–352. 

- Eaton, M. L., Giovagnoli, A., and Sebastiani, P. (1996), “A Predictive Approach to the Bayesian Design Problem With Application to Normal Regression Models,” _Biometrika_ <u>, 83, 111–125.</u> 

- Epstein, E. S. (1969), “A Scoring System for Probability Forecasts of Ranked Categories,” _<u>Journal of Applied Meteorology</u>_ <u>, 8, 985–987.</u> 

- Feuerverger, A., and Rahman, S. (1992), “Some Aspects of Probability Forecasting,” _<u>Communications in Statistics—Theory and Methods</u>_ <u>, 21,</u> 1615–1632. 

- Friederichs, P., and Hense, A. (2006), “Statistical Down-Scaling of Extreme Precipitation Events Using Censored Quantile Regression,” _Monthly Weather Review_ , in press. 

- Friedman, D. (1983), “Effective Scoring Rules for Probabilistic Forecasts,” _Management Science_ , 29, 447–454. 

- Friedman, J. H. (1989), “Regularized Discriminant Analysis,” _<u>Journal of the American Statistical Association</u>_ <u>, 84, 165–175.</u> 

- Garratt, A., Lee, K., Pesaran, M. H., and Shin, Y. (2003), “Forecast Uncertainties in Macroeconomic Modelling: An Application to the U.K. Economy,” _Journal of the American Statistical Association_ <u>, 98, 829–838.</u> 

- Garthwaite, P. H., Kadane, J. B., and O’Hagan, A. (2005), “Statistical Methods for Eliciting Probability Distributions,” _Journal of the American Statistical Association_ <u>, 100, 680–700.</u> 

- Geisser, S., and Eddy, W. F. (1979), “A Predictive Approach to Model Selection,” _<u>Journal of the American Statistical Association</u>_ <u>, 74, 153–160.</u> 

- Gelfand, A. E., and Ghosh, S. K. (1998), “Model Choice: A Minimum Posterior Predictive Loss Approach,” _<u>Biometrika</u>_ <u>, 85, 1–11.</u> 

- Gerds, T. (2002), “Nonparametric Efficient Estimation of Prediction Error for Incomplete Data Models,” unpublished doctoral dissertation, AlbertLudwigs-Universität Freiburg, Germany, Mathematische Fakultät. 

- Giacomini, R., and Komunjer, I. (2005), “Evaluation and Combination of Conditional Quantile Forecasts,” _<u>Journal of Business & Economic Statistics</u>_ <u>, 23, 416–431.</u> 

- Gneiting, T. (1998), “Simple Tests for the Validity of Correlation Function Models on the Circle,” _<u>Statistics & Probability Letters</u>_ <u>, 39, 119–122.</u> 

- Gneiting, T., Balabdaoui, F., and Raftery, A. E. (2006), “Probabilistic Forecasts, Calibration and Sharpness,” _Journal of the Royal Statistical Society_ , Ser. B, in press. 

- Gneiting, T., and Raftery, A. E. (2005), “Weather Forecasting With Ensemble Methods,” _<u>Science</u>_ <u>, 310, 248–249.</u> 

- Gneiting, T., Raftery, A. E., Balabdaoui, F., and Westveld, A. (2003), “Verifying Probabilistic Forecasts: Calibration and Sharpness,” presented at the Workshop on Ensemble Forecasting, Val-Morin, Québec. 

- Gneiting, T., Raftery, A. E., Westveld, A., and Goldman, T. (2005), “Calibrated Probabilistic Forecasting Using Ensemble Model Output Statistics and Minimum CRPS Estimation,” _<u>Monthly Weather Review</u>_ <u>, 133, 1098–1118.</u> 

- Good, I. J. (1952), “Rational Decisions,” _Journal of the Royal Statistical Society_ , Ser. B, 14, 107–114. 

- (1971), Comment on “Measuring Information and Uncertainty,” by 

- R. J. Buehler, in _Foundations of Statistical Inference_ , eds. V. P. Godambe and D. A. Sprott, Toronto: Holt, Rinehart and Winston, pp. 337–339. 

- Granger, C. W. J. (2006), “Preface: Some Thoughts on the Future of Forecasting,” _<u>Oxford Bulletin of Economics and Statistics</u>_ <u>, 67S, 707–711.</u> 

- Grimit, E. P., Gneiting, T., Berrocal, V. J., and Johnson, N. A. (2006), “The Continuous Ranked Probability Score for Circular Variables and Its Application to Mesoscale Forecast Ensemble Verification,” _Quarterly Journal of the Royal Meteorological Society_ , in press. 

- Grimit, E. P., and Mass, C. F. (2002), “Initial Results of a Mesoscale ShortRange Ensemble System Over the Pacific Northwest,” _<u>Weather and Forecasting</u>_ <u>, 17, 192–205.</u> 

- Grünwald, P. D., and Dawid, A. P. (2004), “Game Theory, Maximum Entropy, Minimum Discrepancy and Robust Bayesian Decision Theory,” _<u>The Annals of Statistics</u>_ <u>, 32, 1367–1433.</u> 

- Gschlößl, S., and Czado, C. (2005), “Spatial Modelling of Claim Frequency and Claim Size in Insurance,” Discussion Paper 461, Ludwig-MaximiliansUniversität, Munich, Germany, Sonderforschungsbereich 368. 

- Hamill, T. M. (1999), “Hypothesis Tests for Evaluating Numerical Precipitation Forecasts,” _<u>Weather and Forecasting</u>_ <u>, 14, 155–167.</u> 

- Hamill, T. M., and Wilks, D. S. (1995), “A Probabilistic Forecast Contest and the Difficulty in Assessing Short-Range Forecast Uncertainty,” _<u>Weather and Forecasting</u>_ <u>, 10, 620–631.</u> 

- Hendrickson, A. D., and Buehler, R. J. (1971), “Proper Scores for Probability Forecasters,” _<u>The Annals of Mathematical Statistics</u>_ <u>, 42, 1916–1921.</u> 

- Hersbach, H. (2000), “Decomposition of the Continuous Ranked Probability Score for Ensemble Prediction Systems,” _<u>Weather and Forecasting</u>_ <u>, 15, 559–570.</u> 

- Hofmann, T., Schölkopf, B., and Smola, A. (2005), “A Review of RKHS Methods in Machine Learning,” preprint. 

- Huber, P. J. (1964), “Robust Estimation of a Location Parameter,” _<u>The Annals of Mathematical Statistics</u>_ <u>, 35, 73–101.</u> 

- (1967), “The Behavior of Maximum Likelihood Estimates Under Non- 

- Standard Conditions,” in _Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability I_ , eds. L. M. Le Cam and J. Neyman, Berkeley, CA: University of California Press, pp. 221–233. 

   - (1981), _Robust Statistics_ , New York: Wiley. 

Jeffreys, H. (1939), _Theory of Probability_ , Oxford, U.K.: Oxford University Press. 

- Jolliffe, I. T. (2006), “Uncertainty and Inference for Verification Measures,” _Weather and Forecasting_ , in press. 

- Jolliffe, I. T., and Stephenson, D. B. (eds.) (2003), _Forecast Verification: A Practicioner’s Guide in Atmospheric Science_ , Chichester, U.K.: Wiley. 

- Kabaila, P. (1999), “The Relevance Property for Prediction Intervals,” _Journal of Time Series Analysis_ <u>, 20, 655–662.</u> 

- Kabaila, P., and He, Z. (2001), “On Prediction Intervals for Conditionally Heteroscedastic Processes,” _Journal of Time Series Analysis_ <u>, 22, 725–731.</u> 

- Kass, R. E., and Raftery, A. E. (1995), “Bayes Factors,” _Journal of the American Statistical Association_ <u>, 90, 773–795.</u> 

Knorr-Held, L., and Rainer, E. (2001), “Projections of Lung Cancer in West Germany: A Case Study in Bayesian Prediction,” _Biostatistics_ <u>, 2, 109–129.</u> Koenker, R., and Bassett, G. (1978), “Regression Quantiles,” _Econometrica_ <u>, 46,</u> 33–50. 

Journal of the American Statistical Association, March 2007 

378 

Koenker, R., and Machado, J. A. F. (1999), “Goodness-of-Fit and Related Inference Processes for Quantile Regression,” _<u>Journal of the American Statistical Association</u>_ <u>, 94, 1296–1310.</u> 

- Kohonen, J., and Suomela, J. (2006), “Lessons Learned in the Challenge: Making Predictions and Scoring Them,” in _Machine Learning Challenges: Evaluating Predictive Uncertainty, Visual Object Classification, and Recognizing Textual Entailment_ , eds. J. Quinonero-Candela,˜ I. Dagan, B. Magnini, and F. d’Alché-Buc, Berlin: Springer-Verlag, pp. 95–116. 

- Koldobskiˇı, A. L. (1992), “Schoenberg’s Problem on Positive Definite Functions,” _St. Petersburg Mathematical Journal_ , 3, 563–570. 

- Krzysztofowicz, R., and Sigrest, A. A. (1999), “Comparative Verification of Guidance and Local Quantitative Precipitation Forecasts: Calibration Analyses,” _<u>Weather and Forecasting</u>_ <u>, 14, 443–454.</u> 

- Langland, R. H., Toth, Z., Gelaro, R., Szunyogh, I., Shapiro, M. A., Majumdar, S. J., Morss, R. E., Rohaly, G. D., Velden, C., Bond, N., and Bishop, C. H. (1999), “The North Pacific Experiment (NORPEX-98): Targeted Observations for Improved North American Weather Forecasts,” _Bulletin of the American Meteorological Society_ , 90, 1363–1384. 

- Laud, P. W., and Ibrahim, J. G. (1995), “Predictive Model Selection,” _Journal of the Royal Statistical Society_ , Ser. B, 57, 247–262. 

- Lehmann, E., and Casella, G. (1998), _Theory of Point Estimation_ (2nd ed.), New York: Springer. 

- Liu, R. Y. (1990), “On a Notion of Data Depth Based on Random Simplices,” _<u>The Annals of Statistics</u>_ <u>, 18, 405–414.</u> 

- Ma, C. (2003), “Nonstationary Covariance Functions That Model Space–Time Interactions,” _<u>Statistics & Probability Letters</u>_ <u>, 61, 411–419.</u> 

- Mason, S. J. (2004), “On Using Climatology as a Reference Strategy in the Brier and Ranked Probability Skill Scores,” _<u>Monthly Weather Review</u>_ <u>, 132, 1891–1895.</u> 

- Matheron, G. (1984), “The Selectivity of the Distributions and the ‘Second Principle of Geostatistics,’ ” in _Geostatistics for Natural Resources Characterization_ , eds. G. Verly, M. David, and A. G. Journel, Dordrecht: Reidel, pp. 421–434. 

- Matheson, J. E., and Winkler, R. L. (1976), “Scoring Rules for Continuous Probability Distributions,” _Management Science_ , 22, 1087–1096. 

- Mattner, L. (1997), “Strict Definiteness via Complete Monotonicity of Integrals,” _<u>Transactions of the American Mathematical Society</u>_ <u>, 349, 3321–3342.</u> 

- McCarthy, J. (1956), “Measures of the Value of Information,” _<u>Proceedings of the National Academy of Sciences</u>_ <u>, 42, 654–655.</u> 

- Murphy, A. H. (1973), “Hedging and Skill Scores for Probability Forecasts,” _<u>Journal of Applied Meteorology</u>_ <u>, 12, 215–223.</u> 

- Murphy, A. H., and Winkler, R. L. (1992), “Diagnostic Verification of Probability Forecasts,” _<u>International Journal of Forecasting</u>_ <u>, 7, 435–455.</u> 

- Nau, R. F. (1985), “Should Scoring Rules Be ‘Effective’?,” _Management Science_ , 31, 527–535. 

- Palmer, T. N. (2002), “The Economic Value of Ensemble Forecasts as a Tool for Risk Assessment: From Days to Decades,” _<u>Quarterly Journal of the Royal</u> Meteorological Society_ <u>, 128, 747–774.</u> 

- Pepe, M. S. (2003), _The Statistical Evaluation of Medical Tests for Classification and Prediction_ , Oxford, U.K.: Oxford University Press. 

- Perlman, M. D. (1972), “On the Strong Consistency of Approximate Maximum Likelihood Estimators,” in _Proceedings of the Sixth Berkeley Symposium on Mathematical Statistics and Probability I_ , eds. L. M. Le Cam, J. Neyman, and E. L. Scott, Berkeley, CA: University of California Press, pp. 263–281. 

- Pfanzagl, J. (1969), “On the Measurability and Consistency of Minimum Contrast Estimates,” _Metrika_ <u>, 14, 249–272.</u> 

- Potts, J. (2003), “Basic Concepts,” in _Forecast Verification: A Practicioner’s Guide in Atmospheric Science_ , eds. I. T. Jolliffe and D. B. Stephenson, Chichester, U.K.: Wiley, pp. 13–36. 

- Quiñonero-Candela, J., Rasmussen, C. E., Sinz, F., Bousquet, O., and Schölkopf, B. (2006), “Evaluating Predictive Uncertainty Challenge,” in _Machine Learning Challenges: Evaluating Predictive Uncertainty, Visual Object Classification, and Recognizing Textual Entailment_ , eds. J. Quinonero-˜ Candela, I. Dagan, B. Magnini, and F. d’Alché-Buc, Berlin: Springer, pp. 1–27. 

- Raftery, A. E., Gneiting, T., Balabdaoui, F., and Polakowski, M. (2005), “Using Bayesian Model Averaging to Calibrate Forecast Ensembles,” _Monthly Weather Review_ <u>, 133, 1155–1174.</u> 

- Rockafellar, R. T. (1970), _Convex Analysis_ , Princeton, NJ: Princeton University Press. 

- Roulston, M. S., and Smith, L. A. (2002), “Evaluating Probabilistic Forecasts Using Information Theory,” _Monthly Weather Review_ <u>, 130, 1653–1660.</u> 

- Savage, L. J. (1971), “Elicitation of Personal Probabilities and Expectations,” _<u>Journal of the American Statistical Association</u>_ <u>, 66, 783–801.</u> 

Schervish, M. J. (1989), “A General Method for Comparing Probability Assessors,” _<u>The Annals of Statistics</u>_ <u>, 17, 1856–1879.</u> 

Schumacher, M., Graf, E., and Gerds, T. (2003), “How to Assess Prognostic Models for Survival Data: A Case Study in Oncology,” _<u>Methods of Information in Medicine</u>_ <u>, 42, 564–571.</u> 

- Schwarz, G. (1978), “Estimating the Dimension of a Model,” _<u>The Annals of Statistics</u>_ <u>, 6, 461–464.</u> 

- Selten, R. (1998), “Axiomatic Characterization of the Quadratic Scoring Rule,” _<u>Experimental Economics</u>_ <u>, 1, 43–62.</u> 

- Shuford, E. H., Albert, A., and Massengil, H. E. (1966), “Admissible Probability Measurement Procedures,” _<u>Psychometrika</u>_ <u>, 31, 125–145.</u> 

- Smyth, P. (2000), “Model Selection for Probabilistic Clustering Using CrossValidated Likelihood,” _<u>Statistics and Computing</u>_ <u>, 10, 63–72.</u> 

Spiegelhalter, D. J., Best, N. G., Carlin, B. R., and van der Linde, A. (2002), “Bayesian Measures of Model Complexity and Fit” (with discussion and rejoinder), _Journal of the Royal Statistical Society_ , Ser. B, 64, 583–616. 

Staël von Holstein, C.-A. S. (1970), “A Family of Strictly Proper Scoring Rules Which Are Sensitive to Distance,” _<u>Journal of Applied Meteorology</u>_ <u>, 9, 360–364.</u> 

(1977), “The Continuous Ranked Probability Score in Practice,” in _Decision Making and Change in Human Affairs_ , eds. H. Jungermann and G. de Zeeuw, Dordrecht: Reidel, pp. 263–273. 

Székely, G. J. (2003), “ _E_ -Statistics: The Energy of Statistical Samples,” Technical Report 2003-16, Bowling Green State University, Dept. of Mathematics and Statistics. 

- Székely, G. J., and Rizzo, M. L. (2005), “A New Test for Multivariate Normality,” _<u>Journal of Multivariate Analysis</u>_ <u>, 93, 58–80.</u> 

- Taylor, J. W. (1999), “Evaluating Volatility and Interval Forecasts,” _<u>Journal of Forecasting</u>_ <u>, 18, 111–128.</u> 

- Tetlock, P. E. (2005), _Political Expert Judgement_ , Princeton, NJ: Princeton University Press. 

- Theis, S. (2005), “Deriving Probabilistic Short-Range Forecasts From a Deterministic High-Resolution Model,” unpublished doctoral dissertation, Rheinische Friedrich-Wilhelms-Universität, Bonn, Germany, MathematischNaturwissenschaftliche Fakultät. 

- Toth, Z., Zhu, Y., and Marchok, T. (2001), “The Use of Ensembles to Identify Forecasts With Small and Large Uncertainty,” _<u>Weather and Forecasting</u>_ <u>, 16, 463–477.</u> 

- Unger, D. A. (1985), “A Method to Estimate the Continuous Ranked Probability Score,” in _Preprints of the Ninth Conference on Probability and Statistics in Atmospheric Sciences, Virginia Beach, Virginia_ , Boston: American Meteorological Society, pp. 206–213. 

- Wald, A. (1949), “Note on the Consistency of the Maximum Likelihood Estimate,” _<u>The Annals of Mathematical Statistics</u>_ <u>, 20, 595–601.</u> 

- Weigend, A. S., and Shi, S. (2000), “Predicting Daily Probability Distributions of S&P500 Returns,” _<u>Journal of Forecasting</u>_ <u>, 19, 375–392.</u> 

- Wilks, D. S. (2002), “Smoothing Forecast Ensembles With Fitted Probability Distributions,” _<u>Quarterly</u> Journal of the Royal Meteorological Society_ <u>,</u> 128, 2821–2836. 

- (2006), _Statistical Methods in the Atmospheric Sciences_ (2nd ed.), 

- Amsterdam: Elsevier. 

- Wilson, L. J., Burrows, W. R., and Lanzinger, A. (1999), “A Strategy for Verification of Weather Element Forecasts From an Ensemble Prediction System,” _Monthly Weather Review_ <u>, 127, 956–970.</u> 

- Winkler, R. L. (1969), “Scoring Rules and the Evaluation of Probability Asses- 

- sors,” _Journal of the American Statistical Association_ <u>, 64, 1073–1078.</u> 

- (1972), “A Decision-Theoretic Approach to Interval Estimation,” _Jour-_ 

- _nal of the American Statistical Association_ <u>, 67, 187–191.</u> 

- (1994), “Evaluating Probabilities: Asymmetric Scoring Rules,” _Man-_ 

- _agement Science_ , 40, 1395–1405. 

- (1996), “Scoring Rules and the Evaluation of Probabilities” (with dis- 

- cussion and reply), _Test_ , 5, 1–60. 

- Winkler, R. L., and Murphy, A. H. (1968), “‘Good’ Probability Assessors,” _Journal of Applied Meteorology_ <u>, 7, 751–758.</u> 

- (1979), “The Use of Probabilities in Forecasts of Maximum and Min- 

- imum Temperatures,” _Meteorological Magazine_ , 108, 317–329. 

- Zastavnyi, V. P. (1993), “Positive Definite Functions Depending on the Norm,” _Russian Journal of Mathematical Physics_ , 1, 511–522. 

- Zuo, Y., and Serfling, R. (2000), “General Notions of Statistical Depth Functions,” _The Annals of Statistics_ <u>, 28, 461–482.</u> 

