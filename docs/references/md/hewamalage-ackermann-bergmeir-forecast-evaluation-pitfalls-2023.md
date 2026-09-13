---
# --- bibliographic record ---
entry_type: misc
title: "Forecast Evaluation for Data Scientists: Common Pitfalls and Best Practices"
authors:
  - "Hansika Hewamalage"
  - "Klaus Ackermann"
  - "Christoph Bergmeir"
year: 2022
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: ""
url: "https://10.1007/s10618-022-00894-5"

# --- archive record ---
source_pdf: hewamalage-ackermann-bergmeir-forecast-evaluation-pitfalls-2023.pdf
source_sha256: 855ffcc9a34ab7875ed2f0ba293ae9728da063898ef76ea8744014581435db4a
pdf_pages: 64
converted: 2026-09-13
record_source: arxiv
key_insight: "The evaluation rubric this work is judged against: mandatory naive baselines, no tuning on test data, seed dispersion reported, and multiple evaluation origins."
first_page: "Forecast Evaluation for Data Scientists: Common Pitfalls and Best Practices Hansika Hewamalagea, Klaus Ackermannb, Christoph Bergmeirc,∗ hansika.hewamalage@rmit.edu.au, Klaus.Ackermann@monash.edu, Chr"
---
# Forecast Evaluation for Data Scientists: Common Pitfalls and Best Practices 

Hansika Hewamalage<sup>a</sup> , Klaus Ackermann<sup>b</sup> , Christoph Bergmeir<sup>c,</sup><sup>_∗_</sup> 

_hansika.hewamalage@rmit.edu.au, Klaus.Ackermann@monash.edu, Christoph.Bergmeir@monash.edu_ 

> _aSchool of Computing Technologies, RMIT University, Melbourne, Australia_ 

> _bSoDa Labs and Dept of Econometrics & Business Statistics, Monash University, Melbourne, Australia._ 

> _cDept of Data Science and AI, Faculty of IT, Monash University, Melbourne, Australia._ 

## **Abstract** 

Machine Learning (ML) and in particular Deep Learning (DL) methods nowadays are increasingly replacing traditional methods in many different domains involved with important decision making activities. Sophisticated DL techniques tailor-made for specific tasks such as image recognition, signal processing, or speech analysis are being introduced at a fast pace with many improvements. However, for the domain of time series forecasting, the current state in the ML community is perhaps where other domains such as Natural Language Processing and Computer Vision were at several years ago. The field of forecasting has mainly been fostered by statisticians/econometricians; consequently the related concepts are not the mainstream knowledge among general ML practitioners. The different forms of non-stationarities associated with time series challenge the capabilities of data-driven ML models. Nevertheless, recent trends in the domain have demonstrated that with the availability of massive amounts of time series, ML and DL techniques are quite competent in time series forecasting, when related pitfalls are properly handled. Therefore, in this work we provide a tutorial-like compilation of the details of one of the most important steps in the overall forecasting process, namely the evaluation. This way, we intend to impart the information associated with forecast evaluation to fit the context of ML, as means of bridging the knowledge gap between traditional methods of forecasting and current state-of-the-art ML techniques. We elaborate the details of the different problematic characteristics of time series such as non-normalities and non-stationarities and how they are associated with common pitfalls in forecast evaluation. Best practices in forecast evaluation are outlined with respect to the different steps such as data partitioning, error calculation, statistical testing, and others. Further guidelines are also provided along selecting valid and suitable error measures depending on the specific characteristics of the dataset at hand. 

> _∗_ Corresponding Author Name: Christoph Bergmeir, Affiliation: Dept of Data Science and AI, Faculty of IT, Monash University, Melbourne, Australia, Postal Address: Faculty of Information Technology, Monash University, 20 Exhibition Walk, Clayton Campus, Wellington Road, Clayton VIC 3800, Australia, E-mail address: christoph.bergmeir@monash.edu 

> _Preprint submitted to Data Mining and Knowledge Discovery_ 

_April 5, 2022_ 

## **1. Introduction** 

In the present era of Big Data, Machine Learning (ML) and Deep Learning (DL) based techniques are driving the automatic decision making in many domains such as Natural Language Processing (NLP) or Time Series Classification (TSC, Bagnall et al., 2016; Fawaz et al., 2019). Although fields such as NLP and Computer Vision have heavily been dominated by ML and DL based techniques for decades by now, this has hardly been the case for the field of forecasting, until very recently. Forecasting was traditionally the field of statisticians and econometricians. However, nowadays, with many companies hiring data scientists, often these data scientists are tasked with forecasting. Therefore, now in many situations practitioners are tasked with forecasting that have a good background in ML and data science, but that are not aware of the decades of research in the forecasting space. This involves many aspects of the process of forecasting, from the point of data pre-processing, building models to final forecast evaluation. Due to the self-supervised and sequential nature of forecasting tasks, it is often associated with many pitfalls that usual ML practitioners are not aware of. Out of all these aspects, in this particular work, we focus on the evaluation of point forecasts as a key step in the overall process of forecasting. 

Evaluating the performance of models is key to the development of concepts and practices in any domain. The general process involves employing a number of models having different characteristics, training them on a training dataset and then applying them on a validation set afterwards. Then, model selection may be performed by evaluating on the validation set to select the best models. Otherwise, ensemble models may be developed instead, by combining the forecasts from all the different models, and usually a final evaluation is then performed on a test set. In research areas such as classification and regression, there are well-established standard practices for evaluation. Data partitioning is performed by using a standard k-fold Cross-Validation (CV) to tune the model hyperparameters based on the error on a validation sets, the model with the best hyperparameter combination is tested on the testing set, standard error measures such as squared errors, absolute errors or precision, recall, area under curve are computed and finally the best models are selected. These best methods may continue to deliver reasonable predictions for a certain problem task, i.e., they generalise well, under the assumption that there are no changes of the distribution of the underlying data, which otherwise would need to be addressed as concept drift (Webb et al., 2016; Ghomeshi et al., 2019; Ikonomovska et al., 2010) or non-stationarity. 

In contrast, evaluating forecasting models can be a surprisingly complicated task. Data partitioning and model selection have many different options in the context of forecasting, including fixed origin, rolling origin evaluation and other CV setups as well as controversial arguments associated with them. Due to the inherent non-independence, non-stationarities and non-normalities of time series, these choices are complex. Also, most error measures are susceptible to break down under certain of these conditions. Other considerations are whether to summarise errors across all available time series or consider different steps of the forecast horizon separately etc. As a consequence, without wanting to call them out here, we regularly come across papers in top AI/ML conferences and journals (even winning best paper awards) that use inadequate and miss-leading benchmark methods for compari- 

2 

son (e.g., non-seasonal models for long-term forecasting on seasonal series), others that use mean absolute percentage error (MAPE) for evaluation with series, e.g., with values in the [ _−_ 1 _,_ 1] interval because the authors think the MAPE is a somewhat generic “time series error measure”, even though MAPE is clearly inadequate in such settings. Other works make statements along the lines of ARIMA being able to tackle non-stationarity whereas ML models can’t, neglecting that the only thing ARIMA does is a differencing of the series as a pre-processing step to address non-stationarity. A step that can easily be done as preprocessing for any ML method as well. In other works, we see methods compared using MAE as the error measure, and only the proposed method by those authors is trained with L1 loss, all other competitors with L2 loss, which leads to unfair comparisons as the L1 loss optimises towards MAE, whereas the L2 loss optimises towards RMSE. Many other works evaluate on a handfull of somewhat randomly picked time series and then show plots of forecasts versus actuals as “proof” of how well their method works, without considering simple benchmarks or meaningful error measures, and other similar problems. Also, frequently forecasting competitions and research works introduce new evaluation measures and methodologies, sometimes neglecting the prior research, e.g., by seemingly not understanding that dividing a series by its mean will not solve scaling issues for many types of non-stationarities (e.g., strong trends). Thus, there is no generally accepted standard for forecast evaluation in every possible scenario. This gap has harmed progress in ML methods for forecasting significantly in the past. It is damaging the area currently, with spurious results in many papers, with researchers new to the field not being able to distinguish between methods that work and methods that don’t, and the associated slower progress and waste of resources. 

Overall, this article makes an effort in the direction of raising awareness among ML practitioners regarding the best practices and pitfalls associated with the different steps of the point forecast evaluation process. Similar exhaustive efforts have been taken in the literature to review, formally define and categorise other important concepts in the ML domain such as concept drift (Webb et al., 2016) and mining statistically sound patterns from data (H¨am¨al¨ainen and Webb). The rest of this paper is structured as follows. Section 2 first introduces terminology associated with the domain of forecasting. Next, Section 3 details the motivation for this article, including an introduction to the different forms of nonstationarities/non-normalities seen in time series data, along with common pitfalls related to using competitive benchmarks, visualisation of results using forecast plots and avoiding data leakage in forecast evaluation. Then, Section 4 presents an overview of the process of forecast evaluation. In Section 5, we provide a tutorial/guideline around how to best partition the data for a given forecasting problem such that it is not affecting the sequential nature or the non-stationarities involved with the problem. Section 6 first presents a comprehensive literature review of many different evaluation measures proposed over the years. This is supplemented by a critical analysis of how each of them can break/fail under different circumstances of the time series. This section also provides a guideline on selecting evaluation measures depending on the characteristics of the time series under consideration. In Section 7, we provide details of popular techniques used for statistical testing for significance of differences between models. Finally, Section 8 concludes the paper by summarising the 

3 

overall content of the paper and highlighting the best practices for forecast evaluation. 

## **2. Problem Definition and Terminology** 

The scope of the discussion in this article focusses on point forecasting, where the interest is to predict one particular statistic (mean/median) of the overall forecast distribution. However, we note that there are many works in the literature around predicting distributions and evaluating accordingly. In this section we provide a general overview of the terminology used in the context of time series forecasting. 

Throughout this article, we focus on the task of _univariate forecasting_ . Univariate forecasting is when future values of a time series are predicted using the past values of that same series as well as some other exogenous time varying variables which may affect the target series. This can be formulated as in Equation 1. 



Here, _g_ is a (non-linear, non-parametric) function, for example an ML model and _θ_ are its parameters. _Xt_ are all input data and information available to the model up until time _t_ where _t_ is the _forecast origin_ . Therefore, forecast origin is the last known data point from which the forecasting begins. _h_ denotes the _forecast horizon_ , i.e. the length of the time period into the future for which forecasting of the target value is performed. These are indicated in Figure 1. 

Traditionally, in univariate forecasting without external variables, _Xt_ = **y** = _y_ 1 _, . . . , yt_ . With external variables, _Xt_ contains also the values of the external variables, up to time _t_ or also future values if known. We do not consider multivariate regression in this work, where to predict the future values of many target series together, past values of all series as well as other potentially available external variables are used. 

In a time series context, we define a _lag_ with respect to a time step _t_ as the values of the series at previous time steps. For example, _lag 1_ is the value at time step _t −_ 1 and _lag m_ is the value at time step _t − m_ . In a so-called _Auto-Regression (AR)_ , _Xt_ in Equation 1 only goes back a fixed amount of lags, usually called the _model order_ . The very name indicates that the regression is performed against the values of the target series itself. An auto-regression of a time series uses an _embedded matrix_ . In the embedded matrix in Figure 2, when the model order is _p_ , every row has _p_ + 1 consecutive observations from the time series. During model training, every row is considered a separate data instance, where values at lags 1 _,_ 2 _, ... p_ are considered predictors for the target quantity of the time series at time step _p_ + 1. The process goes through the whole series, shifting the target quantity by one time step in each row, to form a matrix. Therefore, in an AR setup of order _p_ on a series of length _n_ , the number of data instances for training is equivalent to _n − p_ . 

Using this notion of univariate forecasting, both _local models_ and _global models_ can be developed. For a local model, the parameters _θ_ of the model are trained only using one series. Therefore, in the scenario where many time series are available, local models need to be developed as one per each series. On the other hand, for global models, the parameters _θ_ are trained across time series, i.e., using data from all the series. Thus, the embedded matrix 

4 



Figure 1: A Forecasting Scenario with Training Region of the Data, Forecast Origin and the Forecast Horizon 



Figure 2: Embedded Matrix for AR Process of Order _p_ 

5 

contains data instances from many series. However, for the prediction of a single series, _Xt_ in Equation 1 only considers the corresponding lags of that particular series (Januschowski et al., 2020). Similar to other ML tasks, validation and test sets are used for hyperparameter tuning of the models and for testing. Evaluations on validation and test sets are often called _out-of-sample (OOS)_ evaluations in forecasting. The two main setups for OOS evaluation in forecasting are _fixed origin evaluation_ and _rolling origin evaluation_ (Tashman, 2000). Figure 3 shows the difference between the two setups. In the fixed origin setup, the forecast origin is fixed as well as the training region, and the forecasts are computed as one-step ahead or multi-step ahead depending on the requirements. In the rolling origin setup, the size of the forecast horizon is fixed, but the forecast origin changes over the time series (rolling origin), thus effectively creating multiple test periods for evaluation. With every new forecast origin, new data becomes available for the model which can be used for refitting of the model. However, as seen on Figure 3, since the rolling origin setup allows the data to pass on from the testing set to the training set of the next consecutive evaluation step, this setup, if not used properly, is naturally susceptible to data leakage dangers, where information of the future may leak to the model training phase using past data (further discussed in Section 3.4). The rolling origin setup is also called _time series cross-validation (tsCV)_ and _prequential evaluation_ in the literature (Hyndman and Athanasopoulos, 2018; Gama et al., 2013). Further details of these approaches are discussed in Section 5. 



Figure 3: Comparison of fixed origin vs. rolling origin setups. The blue and orange data points represent the training and testing sets respectively at each evaluation. The figure on the left side shows the fixed origin setup where the forecast origin remains constant. The figure on the right shows the rolling origin setup where the forecast origin rolls forward and the forecast horizon is constant. The red dotted lined triangle encloses all the time steps used for testing across all the evaluations. Compared to the fixed origin setup, it is seen that in the rolling origin setup, testing data instances in each evaluation pass on to the training set in the next evaluation step. 

6 

## **3. Motivation and Common Pitfalls** 

This section is devoted to provide the motivation of our work and we discuss the general problems faced in forecasting, in comparison to a usual ML task. 

## _3.1. Characteristics of Time Series_ 

What makes time series forecasting a more difficult problem in comparison to other ML tasks, are the different _non-stationarities_ and _non-normalities_ commonly embedded in time series. Listed below are some of such possibly problematic characteristics of time series. 

1. Non-stationarities. 

   - Seasonality 

   - Trends (Deterministic, e.g., Linear/Exponential) 

   - Stochastic Trends / Unit Roots 

   - Heteroscedasticity 

   - Structural Breaks (sudden changes, often with level shifts) 

2. Non-normality 

   - Non-symmetric distributions 

   - Fat tails 

   - Intermittency 

   - Outliers 

3. Series with very short history 

Non-stationarity in general means that the distribution of the data in the time series is not constant, but it changes depending on the time (see, e.g., Salles et al., 2019). What we refer to as non-stationarity in this work is the violation of strong stationarity defined as in Equation 2 (Cox and Miller, 1965). Strong stationarity is defined as the distribution of a finite window (sub-sequence) of a time series (discrete-time stochastic process) remaining the same as we shift the window across time. In Equation 2, _yt_ refers to the time series value at time step _t_ ; _τ ∈_ Z is the size of the shift of the window and _n ∈_ N is the size of the window. _FY_ ( _yt_ + _τ , yt_ +1+ _τ , ..., yt_ + _n_ + _τ_ ) refers to the cumulative distribution function of the joint distribution of ( _yt_ + _τ , yt_ +1+ _τ , ..., yt_ + _n_ + _τ_ ). Hence, according to Equation 2, _FY_ is not a function of time, it does not depend on the shift of the window. In the rest of this paper, we refer to the violation of strong stationarity simply as non-stationarity. 



Figure 4 gives an example of possible problems when building ML models on such data, where the models fail to produce reasonable forecasts as the range of values is different in the training and test sets. Different types of non-stationarities are illustrated in Figure 5. _Seasonality_ usually means that the mean of the series changes periodically over time, with a 

7 

fixed length periodicity. Trends can be twofold; 1) _deterministic trends_ - change the mean of the series 2) _stochastic trends_ (resulting from unit roots) - change both the mean and variance of the series (Salles et al., 2019). Note that neither trend nor seasonality are concepts that have precise formal definitions. They are usually merely defined as smoothed versions of the time series, where for the seasonality the smoothing occurs over particular seasons (e.g., in a daily series, the series of all Mondays needs to be smooth, etc.). _Heteroscedasticity_ changes the variance of the series and _structural breaks_ can change the mean or other properties of the series. _Structural break_ is a term used in Econometrics and Statistics in a time series context to describe a sudden change in the series. It therewith has considerable overlap with the notion of _sudden concept drift_ in an ML environment, where a sudden change of the data distribution is observed (Webb et al., 2016). 

On the other hand, data can be far from normality, for example having fat tails, or when conditions such as outliers or intermittency are observed in the series. Non-stationarities and non-normalities are both seen quite commonly in many real-world time series and the decisions taken during forecast evaluation depend on which of these characteristics the series have. There is no single universal rule that applies to every scenario. 



Figure 4: Forecasts from different models on a series with unit root based non-stationarity, with stochastic trends. In this example, we have a continuously increasing series (increasing mean) due to the unit root. The ML models are built as autoregressive models without any pre- or post-processing, and as such have very limited capacity to predict values beyond the domain of the training set. 

## _3.2. Benchmarks for Forecast Evaluation_ 

Benchmarks are an important part of forecast evaluation. Comparison against the right benchmarks and especially the simpler ones is essential. Arguably the simplest benchmark that is commonly employed in forecasting is the na¨ıve forecast, also called persistence model or no-change model, that simply uses the last known observation as the forecast. It has 

8 



Figure 5: Different Non-stationarities of Series 

demonstrated competitive performance in many scenarios (Armstrong, 2001). Figure 6 illustrates the behaviour of different models that have been trained with differencing as appropriate preprocessing on a series that has a unit root based non-stationarity. If the series has no further predictable properties above the unit root, i.e., it is a random walk where the innovation added to the last observation follows a normal distribution with a mean of zero, the na¨ıve forecast is the theoretically best forecast. Other, more complex forecasting methods in this scenario will have no true predictive power beyond the na¨ıve method, and any superiority, e.g., in error evaluations is by pure chance, and should be able to be identified as a spurious result on sufficiently large datasets. 

Equation 3 shows the definition of a random walk, where _ϵt_ is white noise; i.e. sampled from a normal distribution. Accordingly, the na¨ıve forecast at any time step in the horizon can be defined as in Equation 4. As the na¨ıve forecast is the last known observation, the forecast is a shifted version of the time series where the forecast simply follows the actuals (see Figure 6b). 





In many practical applications, we find series that show strongly integrated behaviour and therewith are close to random walks (such as stock market data, wind power, wind speed). 

9 



(a) Series with unit root based non-stationarity and forecasts from different models 



(b) Forecasts from the different models on a selected subset of the test set (timestamps 807 - 856) 

Figure 6: Forecasts from different models on a series with unit root based non-stationarity, with stochastic trends. The ML models are built as autoregressive integrated models, i.e., differencing has been done as pre-processing. The methods show very similar behaviour to the na¨ıve forecast, and do not add any value over it by definition of the Data Generating Process used. 

10 

Here, a na¨ıve forecast is a trivial yet competitive benchmark and without comparing against it, quality of more complex models cannot be meaningfully assessed. Furthermore, also more complex methods will in such series usually show a behaviour where they mostly follow the series in the same way as the na¨ıve forecast, and improvements are often small percentages over the performance of the na¨ıve benchmark. 

As such, the benchmarks and the error measure used play an important role in such a setting. For instance, by using a relative error measure (detailed further in Section 6) that lets us directly compare against a simple benchmark such as the na¨ıve, we can be certain of the competitiveness of the model against simple methods. On series that have clear seasonal patterns, models should accordingly be benchmarked against the seasonal na¨ıve model as the most simplistic benchmark, and also other simple benchmarks are commonly used in forecasting. 

## _3.3. Forecast Plots_ 

Plots with time series forecasting results can be quite misleading and should be used with caution. Analysing plots of forecasts from different models along with the actuals and concluding that they seem to fit well can lead to wrong conclusions. It is important to use benchmarks and evaluation metrics that are right for the context. Even with good error measures, in a scenario like a random walk series as in Figure 6, as stated before, our models may achieve better accuracy than the na¨ıve method, but it will be a spurious result. 

The visual appeal of a generated forecast or the possibility of such a forecast to happen in general are not good criteria to judge forecasts. 

Figure 7a shows another random walk series, with the na¨ıve forecast as the best forecast by definition of the Data Generating Process (DGP). The figure furthermore shows the forecasts under fixed origin and rolling origin data partitioning schemes. When periodic re-fitting is done with new data coming in as in a rolling origin setup, the na¨ıve forecast gets continuously updated with the last observed value. For the fixed origin context on the other hand, the na¨ıve forecast remains constant as a straight line corresponding to the last seen observation in the training series. We see that with a rolling-origin na¨ıve forecast, the predictions tend to look visually very appealing, as the forecasts follow the actuals and our eyes are deceived by the smaller horizontal distances instead of the vertical distances that are relevant for evaluation. Figure 7b illustrates this behaviour. It is clear how the horizontal distance between the actuals and the na¨ıve forecast at both points A and B are much less compared to the vertical distances which are the relevant ones for evaluation. If a scatter-plot of the actuals against the forecasts as in Figure 7c can be used instead, it may give a much better picture of where the forecasts stand with respect to reality, by discarding the time domain. On the other hand, on a series with integrated behaviour, the na¨ıve method is a strong benchmark and other competitive methods on such a series will also tend to show behaviours of following the actuals. In these situations we need to rely on the error measures, as the plots do not give us much information. 

Figure 7a shows another issue with forecasts, as the na¨ıve forecast for fixed origin is a constant. Although this does not look realistic, and in most application domains we can be certain that the actuals will not be constant, practitioners may mistakenly identify such 

11 

behaviour as a potential problem with the models, where this forecast is indeed the best possible forecast in the sense that it minimises the error based on the information available at present. 



- (a) Rolling Origin vs. Fixed Origin Comparison for the Na¨ıve Forecast 



<!-- Start of picture text -->
(c) Scatter plot of Actuals against the Na¨ıve<br>(b) Visual Delusion of the Na¨ıve Forecast Forecast<br><!-- End of picture text -->

Figure 7: Properties of the na¨ıve forecast 

In summary, plots of the forecasts can be deceiving and should be used mostly for sanity checking. Decisions should mostly be made based on evaluations with error measures and not based on plots. 

## _3.4. Data Leakage in Forecast Evaluation_ 

Data leakage refers to the inadvertent use of data from the test set, or more generally data not available during inference, while training a model. It is always a potential problem in any ML task. For example, Kaufman et al. (2012) present an extensive review on the concept of data leakage for data mining and potential ways to avoid it. Arnott et al. (2019) 

12 

discuss this in relation to the domain of finance. Hannun et al. (2021) propose a technique based on Fisher information that can be used to detect data leakage of a model with respect to various subsets of the dataset. Brownlee (2020) also provide a tutorial overview on data preparation for common ML applications while avoiding data leakage in the process. However, in forecasting data leakage can happen easier and can be harder to avoid than in other ML tasks such as classification/regression. 

Forecasting is usually performed in a self-supervised manner with rolling origin evaluations where periodic re-training of models is performed, and within this re-training, it is normal that data travels from the test to the training set. As such, it is often difficult and not practical to separate training and evaluation code bases. As such, we often have to trust the software provider that everything is implemented correctly, and an external evaluation is difficult. 

Also, more indirect forms of data leakage can happen in forecasting. In analogy to classification/regression, where data leakage sometimes happens by normalising data before partitioning for cross-validation, in forecasting, data leakage can happen by performing smoothing, decomposition (mode decomposition), normalisation etc. over the whole series before partitioning for training and testing. Data leakage can happen even when extracting features such as `tsfeatures` (Hyndman et al., 2019), `catch22` (Lubba et al., 2019) that are not constant over time, to feed as inputs to the model. Thus, features can be extracted only from the training set data, and may need to be re-calculated either periodically or over the specific input windows. However, this can be computationally expensive. 

Another type of leakage especially when training global models that learn across series, which is common practice nowadays for ML models, is when one series in the dataset contains information about the future of another series. For example with an external shock like COVID-19 or a global economy collapse, all the series in the dataset can be equally affected. Therefore, if the series in the dataset are not aligned and one series contains the future values with respect to another, when splitting the training region, future information can be already included within the training set. However, in real world application series are usually aligned so that this is not a big problem. On the other hand, in a competition setup such as the M3 and M4 forecasting competitions (Makridakis and Hibon, 2000; Makridakis et al., 2020b), where the series are not aligned, this can easily happen. 

Data leakage can also happen simply due to using the wrong forecast horizon. This can happen by using data that in practice will become available later. For example, we could build a one-day-ahead model, but use summary statistics over the whole day. This means that we cannot run the model until midnight, when we have all data from that day available. If the relevant people who use the forecasts work only from 9am-5pm, it becomes effectively a same-day model. The other option is to set the day to start and end at 5pm everyday, but that may lead to other problems. 

In conclusion, data leakage dangers are common in self-supervised forecasting tasks. It is important to avoid leakage problems 1) in rolling origin schemes by being able to verify and trust the implementation, as external evaluation can be difficult 2) during preprocessing of the data (normalising, smoothing etc.) and extracting features such as `tsfeatures` by splitting the data into training and test sets beforehand 3) by making sure that within a set 

13 

of series, one series does not contain in its training period potential information about the future of another series. 

## **4. Overview of the Forecast Evaluation Process** 

Forecast model building and evaluation typically encompasses the following steps. 

- Data partitioning 

- Forecasting 

- Error Calculation 

- Error Measure Calculation 

- Statistical Tests for Significance (optional) 

- Model Selection (optional) 

The process of evaluation in a usual regression problem is quite straightforward. The models fitted to the training dataset output a prediction for a single target value in the validation set, an error such as the quadratic loss is computed for each prediction and target value combination, and finally the errors from all the predictions in the validation set are summarised using some error measure such as the Root Mean Squared Error (RMSE). The best model out of the pool of fitted models is selected based on the value of this final error measure on the validation set. The relevant error measures used etc. are standard and established as best practices in these domains. 

However, when it comes to forecast evaluation, many different options are available for each of the aforementioned steps and no standards have been established thus far, although several pitfalls associated with certain evaluation setups have been identified. Two other optional activities related to forecast evaluation are Statistical Tests for Significance and Model Selection. They are not performed always by practitioners. Instead of selecting one best model, we may sometimes be interested in deploying an ensemble of all the models. Out of these different steps in evaluation, in this article we discuss the approaches commonly used for Data Partitioning, Model Selection, Error and Error Measure Calculation as well as Statistical Tests for Significance. 

## **5. Data Partitioning** 

When performing OOS evaluation in forecasting (using a validation or test set), we can either evaluate for every individual forecast step separately (one-step-ahead error, two-stepahead error) or the whole test period on average depending on the forecasting scheme of the underlying models. In this section, we explain the details of different data partitioning techniques for evaluations performed in the context of forecasting. We also explain the options for model selection based on these different data partitioning strategies. 

14 

## _5.1. Fixed Origin Setup_ 

Fixed origin setup is a faster and easier to implement evaluation setup. Fixed origin setup is the usual setup used in many academic contexts such as forecasting competitions since this can effectively avoid data leakage problems as the test set is not disclosed in any way. In fact for competition scenarios where the dates of the series are not aligned (like the M3, M4 competitions), a fixed origin setup may be sufficient. However, for many practical scenarios, a fixed origin setup is problematic and may not be a sufficient evaluation. With a single series, the fixed origin setup only provides one forecast per each forecast step in the horizon. According to Tashman (2000), a preferred characteristic of OOS forecast evaluation is to have sufficient forecasts at each forecast step. Furthermore, for a single series, the testing period is short unless a long forecast horizon is used. However, with a long forecast horizon, the problem is that we are mixing very different forecasts. For example, for a 400-step-ahead forecast, short-term dynamics due to autocorrelation may be irrelevant, and trend and seasonality may matter the most, where for a one-step-ahead forecast short-term dynamics may be the dominating factor. Thus, a one-step-ahead forecast may have totally different characteristics, in terms of possible accuracy, useful input features, well-performing methods, than a 400-step-ahead forecast (Petropoulos et al., 2014). 

Another requirement of OOS forecast evaluation is to make the forecast error measures insensitive to specific phases of business (Tashman, 2000). However, with a fixed origin setup, the errors may be the result of particular patterns only observable in that particular region of the horizon (Tashman, 2000), and evaluations will not generalise well to other phases such as Christmas sales, Holiday seasons, etc.. This poses a gap between what practitioners are really interested in and how forecasting is done often in academic settings. Having multiple forecasts for the same forecast step allows to produce a forecast distribution per each step for further analysis. Therefore, the following multi period evaluation setups are introduced as opposed to the fixed origin setup. 

## _5.2. Rolling Origin, Time Series Cross-Validation and Prequential Evaluation Setups_ 

Armstrong and Grohman (1972) are among the first researchers to give a descriptive explanation of the rolling origin evaluation setup. Although the terms rolling origin setup and tsCV are used interchangeably in the literature, in addition to the forecast origin rolling forward, tsCV also allows to skip origins, effectively rolling forward by more than one step at a time (analogously to the difference between a leave-one-out CV and a k-fold CV). In the field of stream data mining and concept drift, this form of evaluation is furthermore known as _interleaved-test-then-train_ or _prequential evaluation_ (Gama et al., 2013; Ghomeshi et al., 2019) as means of online evaluation. For streaming data, prequential evaluation allows to continuously monitor the performance of a model that evolves over time, and thus detect and act upon concept drifts (Gama et al., 2009; Kiran Bhowmick, 2020). With such multi period evaluations, each time the forecast origin updates, the model encounters new actual data. Hence, a rolling origin setup is typically the more practical evaluation setup in real-world application. For instance, in a task of forecasting the daily sales of a particular product, the number of actual sales can be obtained at the end of each day and can be incorporated in the model to better predict the next day’s demand. 

15 

With new data becoming available, we have the options to – in the terminology of Tashman (2000) – either update the model or recalibrate it. Recalibration here refers to either retraining the model weights from scratch or incremental learning as new data comes in. Updating on the other hand means just using the trained model to predict with new data. Although for some of the traditional models such as Exponential Smoothing (ETS) and Auto-Regressive Integrated Moving Average (ARIMA), the usual practice (and the implementation in the `forecast` package) in a rolling origin setup is to recalibrate (refit) the models, for general ML models it is more common to mostly just accept new data as inputs and only periodically retrain the model. While this is quite straightforward with a stateless ML model, on a model with a state such as a Recurrent Neural Network (RNN), updating still requires stepping through the whole series to construct the state. In this sense, the (updating-based) rolling origin setup comes more natural to many ML methods than to the traditional forecasting methods. Also, as ML methods tend to work better with higher granularities, re-fitting is not an option (for example, a monthly series predicted with ETS vs. a 5-minutely series predicted with Light Gradient Boosting Models). Therefore, retraining as the most recent data becomes available happens in ML methods mostly only when some sort of concept drift (change of the underlying data generating process) is encountered (Webb et al., 2016). 



Figure 8: Comparison of Expanding Window vs. Rolling Window setups. The blue and orange points represent the training and test sets, respectively. The figure on the left side shows the Expanding Window setup where the training set keeps expanding. The figure on the right shows the Rolling Window setup where the size of the training set keeps constant and the first point of the training set keeps rolling forward. 

Rolling origin evaluation can be conducted in two ways; 1) Expanding window setup 2) Rolling window setup. Figure 8 illustrates the difference between the two approaches. In the expanding window setup, the training region of the series for the model expands as the forecast origin rolls forward, thus effectively increasing the length of the training data per each evaluation. The expanding window method is a good setup for small datasets/short series (Bell and Smyl, 2018). However, in the rolling window setup, the size of the training region is kept constant; thus as the forecast origin rolls forward, so does the start of the 

16 

training period, dropping the oldest observations as new data becomes available (Cerqueira et al., 2020). The rolling window setup removes the oldest data from training. This will not make a difference with forecasting techniques that only minimally attend the distant past, such as ETS, but may be beneficial with pure autoregressive ML models, that have no notion of time beyond the windows. In a streaming data context as well, the most common methods of performing prequential evaluation are by using a sliding window or by using fading factors which tend to forget instances in the further past and focus on the current window (Mulinka et al., 2018). This is because the usual prequential evaluation approach with expanding window is known to provide overestimation for the validation error (Gama et al., 2009). Hidalgo et al. (2019) have empirically demonstrated that prequential evaluation with sliding window is the best approach for validation in comparison to fading factors and expanding window. A potential problem of the rolling origin setup is that the first folds may not have much data available. However, the size of the first folds is not an issue when dealing with long series, thus making rolling origin setup a good choice with sufficient amounts of data. On the other hand, with short series it is also possible to perform a combination of the aforementioned two rolling origin setups where we start with an expanding window setup and then move to a rolling window setup. 

## _5.3. (Randomised) Cross-Validation_ 

The aforementioned two techniques of data partitioning preserve the temporal order of the time series when splitting and using the data. Another form of data partitioning is to use a common randomised CV scheme as first proposed by Stone (1974). This scheme is visualised in Figure 9. The dataset is initially shuffled randomly and then partitioned into non-overlapping train and validation sets. Often a k-fold CV scheme is used for this purpose. For example, in a 5-fold CV strategy, the whole training dataset is randomly split into 5 partitions and 4 of them are used to train the model and the remaining partition held out for validation. This is done in iterations until all partitions are considered for validation separately. The set of validation scores produced this way are finally summarised. LeaveOne-Out-Cross-Validation (LOOCV) is the extreme case of the k-fold CV where k is equal to the number of data points in the dataset. Therefore, compared to the aforementioned validation schemes which preserve the temporal order of the data, this form of randomised CV strategy can make efficient use of the data, since all the data is used for both model training as well as evaluation in iterations (Hastie et al., 2009). This helps to make a more informed estimation about the generalisation error of the model. 

However, this form of random splitting of a time series does not preserve the temporal order of the data, and is therefore oftentimes not used and seen as problematic. The common points of criticism for this strategy are that, 1) it can make it difficult for a model to capture serial correlation between data points (autocorrelation) properly, 2) potential nonstationarities in time series can cause problems (for example, depending on the way that the data is partitioned, if all data from Sundays happen to be in the test set but not the training set in a series with weekly seasonality, then the model will not be able to produce accurate forecasts for Sundays since it has never seen data of Sundays before), 3) the training data contains future observations and the test set contains past data due to the random splitting 

17 



Figure 9: Comparison of randomised CV vs. OOS evaluation. The blue and orange dots represent the training and test sets, respectively. In the usual k-fold-CV setup the testing instances are chosen randomly over the series. In OSS, the test set is always reserved from the end of the series. 

and 4) since evaluation data is reserved randomly across the series, the forecasting problem shifts to a missing value imputation problem which certain time series models are not capable of handling (Petropoulos et al., 2020). 

Out of these problems, to address the serial correlation issues, researchers have proposed a few variations of CV. Different forms of blocked CV have been introduced for this purpose, where the folds are selected in blocks, without initial shuffling and preserving the temporal order of the data within the folds (Racine, 2000; Bergmeir and Ben´ıtez, 2012). Further non-dependent CV techniques have also been proposed, where a sufficiently sized block of instances surrounding the test instances are discarded to ensure independence between the training and test sets (Burman et al., 1994; Racine, 2000). Nonetheless, randomised CV can be applied to pure AR models without a problem. Bergmeir et al. (2018) theoretically and empirically show that CV performs well in a pure AR setup, as long as the models nest or approximate the true model, as then the errors are uncorrelated, leaving no dependency between the individual windows. To check this, it is important to estimate the serial correlation of residuals. For this, the Ljung-Box test (Ljung and Box, 1978) can be used on the OOS residuals of the models. While for overfitting models there will be no autocorrelation left in the residuals, if the models are underfitted, some autocorrelation will be left in the OOS residuals. If there is autocorrelation left, then the model still does not use all the information available in the data, which means there will be dependencies between the separate windows. In such a scenario, CV of the time series dataset will not hold valid, and underestimate the true generalisation error. The existence of significant autocorrelations anyway means that the model should be improved to do better on the respective series (increase the AR order to capture autocorrelation etc.), since the model has not captured all the available information. Once the models are sufficiently competent in capturing the patterns of the series, for pure AR setups (without exogenous variables), standard k-fold CV is a valid strategy. Therefore, in situations with short series and small amounts of training data, where it is not practically feasible to apply the aforementioned tsCV techniques due to the initial folds involving very small lengths of the series, the standard CV method with some control of underfitting of the models is a better choice with efficient use of data. 

The aforementioned problem that the testing windows can contain future observations, is also addressed by Bergmeir et al. (2018). With the CV strategy, the past observations 

18 

not in the training data but existing in the test set can be considered missing observations, and the task is seen more as a missing value imputation problem rather than a forecasting problem. Many forecasting models such as ETS (in its implementation in the `forecast` package (Hyndman and Athanasopoulos, 2018)), which iterate throughout the whole series, cannot properly deal with missing data. For RNNs as well, due to their internal states that are propagated forward along the series, standard k-fold CV which partitions data randomly across the series is usually not applicable. Therefore, for such models, the only feasible validation strategy is tsCV. Models such as ETS can anyway train competitively with minimal amounts of data (as is the case with the initial folds of the tsCV technique) and thus, are not quite problematic with tsCV. However, for reasonably trained pure AR models, where the forecasts for one window do not in any way depend on the information from other windows (due to not underfitting and having no internal state), it does not make a difference between filling the missing values in the middle of the series and predicting future values, where both are performed OOS. Nevertheless, the findings by Bergmeir et al. (2018) are restricted to only stationary series. Cerqueira et al. (2020)’s work on the same area has concluded that for stationary series, using a pure AR setup, a blocked CV strategy works the best, and they also perform an analysis on non-stationary data, discussed in the following section. 

## _5.4. Data partitioning for non-stationary data_ 

Cerqueira et al. (2020) experimented using non-stationary series, where they have concluded that OOS validation procedures preserving the temporal order (such as tsCV), are the right choice when non-stationarities exist in the series. However, a possible criticism of that work is the choice of models. We have seen in Section 3 that ML models are oftentimes not able to address certain types of non-stationarities out of the box. More generally speaking, ML models are non-parametric, data-driven models. As such, the models are typically very flexible and the function fitted depends heavily on the characteristics of the observed data. Though recently challenged (Balestriero et al., 2021), a common notion is that ML models are typically good at interpolation and lack extrapolation capabilities. The models used by Cerqueira et al. (2020) include several ML models such as a Rule-based Regression (RBR) model, a Random Forest (RF) model and a Generalised Linear Model (GLM), without in any way explicitly tackling the non-stationarity in the data (similar to our example in Section 3). Thus, if a model is poor and not producing good forecasts, performing a validation to select hyperparameters, using any of the aforementioned CV strategies, will be of limited value. Furthermore, and more importantly, non-stationarity is a broad concept and it will depend both for the modelling and the evaluation on the type of non-stationarity which procedures will perform well. For example, with abrupt structural breaks and level shifts occurring in the unknown future, but not in the training and test set, it will be impossible for the models to address this change and none of the aforementioned evaluation strategies would do so either. In this situation, even tsCV would grossly underestimate the generalisation error. For a more gradual underlying change of the DGP, a validation set at the end of the series would be more appropriate since in that case, the data points closer to the end of the series may be already undergoing the change of the distribution. On the other hand, if the series has 

19 

deterministic trend or seasonality, which are straightforward to forecast, they can be simply extracted from the series and predicted separately whereas the stationary remainder can be handled using the model. In such a setup, the k-fold CV scheme will work well for the model, since the remainder complies with the stationarity condition. For other non-deterministic trends, there are several data pre-processing steps mentioned in the literature such as lag-1 differencing, logarithmic transformation (for exponential trends), Seasonal and Trend Decomposition using Loess (STL Decomposition), local window normalisation (Hewamalage et al., 2021), moving average smoothing, percentage change transform, wavelet transform etc. (Salles et al., 2019). Salles et al. (2019) have conducted an extensive empirical study to investigate the impact of the choice of the data transformation technique on the accuracy of the model, using a linear ARMA model. Their findings have concluded that there is no single universally best transformation technique across all datasets; rather it depends on the characteristics of the individual datasets. However, for the particular datasets used in their study, differencing and moving average smoothing have generally worked the best for addressing trend. If appropriate data pre-processing steps are applied to enable models to handle non-stationarities, with a pure AR setup, the CV strategy still holds valid after the data transformation, if the transformation achieves stationarity. As such, to conclude, for non-stationarities, tsCV seems the most adequate as it preserves the temporal order in the data. However, there are situations where also tsCV will be misleading, and the forecasting practitioner will already for the modeling need to attempt to understand the type of non-stationarity they are dealing with. This information can subsequently be used for evaluation, which may render CV methods for stationary data applicable after transformations of the data to make them stationary. 

## _5.5. Other model selection methods_ 

The aforementioned data partitioning schemes are quite important when it comes to model selection based on the performance of the models on the validation sets. Apart from the CV strategies discussed above, other model selection techniques exist such as information criteria (IC) or techniques like minimum message length (Fitzgibbon et al., 2004). The advantage of these techniques over data partitioning is typically that all data can be used for training and no validation set is needed. 

For example, let us consider Akaike’s Information Criterion (AIC, Akaike, 1974), but similar considerations hold for other IC. For time series models, it has been found that minimising AIC is asymptotically equivalent to minimising the MSE of OOS one-step ahead forecasts (Inoue and Kilian, 2006). However, using AIC has several downsides. To use it to compare across models, the respective likelihoods need to be computed the same way, using the same data. Therefore, it cannot be used to compare across models, with different model orders, from different model families such as ETS and ARIMA (since likelihoods for those models are computed in different ways), with and without differencing, since differencing effectively reduces the amount of data points available for the model. Apart from that, AIC is in general used when getting access to a separate test set is expensive (due to limited data), which is often not the case with data-abundant scenarios where ML models are applicable. Therefore, AIC is more suitable for small datasets and this is why models such as ETS and 

20 

ARIMA that are not very data-intensive, use AIC and other IC internally. Moreover, the definition of AIC uses (an estimation of) the number of parameters of the model, which is not straightforward for complex ML models, since simply counting the number of parameters does not represent well the complexity of such models. Due to these reasons, generally AIC and other IC are not used for ML models that work on large datasets. For such situations, the data partitioning methods discussed before are usually preferable. 

## _5.6. Summary and guidelines for data partitioning and model selection_ 

It is important to identify which out of the above data partitioning strategies most closely estimates (without under/overestimation) the final error of a model for the test set under the given scenario (subject to different non-stationarities/serial correlations/amount of data of the given time series). In particular, in the M5 competition as well, it was reemphasised that a reliable CV strategy is essential, to be able to assess the generalisation error of models (Makridakis et al., 2020a). 

The gist of the guidelines for model selection is visualised by the flow chart in Figure 10. If the series are not short, tsCV is usually preferrable over k-fold CV, if there are no practical considerations such as that an implementation of an algorithm is used that is not primarily intended for time series forecasting, and that internally performs a certain type of cross-validation. If series are short, then k-fold CV should be used, accounting adequately for non-stationarities and autocorrelation in the residuals. 



Figure 10: Guidelines on Data Partitioning and Model Selection 

## **6. Error Measures for Forecast Evaluation** 

Once the predictions are obtained from models, the next requirement is to compute errors of the predictions to assess the model performance. Belt (2017) argue in their work that a bias-variance decomposition of the error measure should be considered. Bias and variance of forecasts may yield different business decisions. Bias in predictions occurs due to errors from wrong model assumptions, which result in a weak model not having captured the exact patterns of the data. This happens mostly due to the selected sample of data 

21 

(used for model training) being under-representative of the whole distribution, which is also called as the selection bias. Because of this reason, a model can be very accurate (forecasts being very close to actuals), but consistently produce more overestimations than underestimations, which may be concerning from a business perspective. Therefore, forecast bias is calculated with a sign, as opposed to absolute errors, so that it indicates the direction of the forecast errors, either positive or negative. For example, scale-dependent forecast bias can be assessed with the Mean Error (ME) as defined in Equation in 5. Here, _yt_ indicates the true value of the series, _y_ ˆ _t_ the forecast and _n_ , the number of all available errors (across series, across horizons, etc.). The scale-dependent standard deviation (Std) of the errors for the population is defined in Equation 6, assuming a 0 population mean of the errors, i.e., an unbiased model. Note that the Std of the errors for an unbiased model is identical to the Root Mean Squared Error (RMSE) defined later in Equation 10. Therefore, RMSE produces an estimate of the Std of the distribution of forecast errors. Other scale-free versions of bias and Std can be defined by scaling with respect to appropriate scaling factors, such as actual values of the series. 





Two other popular and simple error measures used in a usual regression context are Mean Squared Error (MSE) and Mean Absolute Error (MAE) defined in Equations 7 and 8 respectively. 





Apart from these simple measures used as in usual ML tasks such as regression, for forecasting a wide variety of error measures have been proposed by researchers over the years. The main reason for this is the need to have measures that allow for comparisons across series. For this, the measures need to be scaled, and it has turned out to be next to impossible to develop a scaling procedure that works for any type of possible non-stationarity and non-normality in a time series. Eventually we encounter a particular condition of the time series in the real world, that makes the proposed error measure fail (Svetunkov, 2021). Thus, new measures usually either focus on specific business needs or have the intention of addressing issues of previously used measures, but have new issues then. This has led to a large pool of proposals in the literature. Researchers/practitioners very often have particular series in mind when evaluating in a certain way (using specific measures) in their 

22 

work, but these preconditions are often never stated. For example, smart meter or wind power production series do not usually have exponential trends, and they hardly have level shifts or long-term trends etc. On the other hand, growing businesses such as tech start-ups or ride-share providers often have strong trends in any business related time series that they have collected. The key to selecting a particular error measure for forecast evaluation is that it is mathematically and practically robust under the given data. From a business point of view there can be other requirements for an error measure such as being interpretable (easy to communicate) and reflecting on the key performance indicators of the underlying business application such as the net profit; which we do not focus on in this work. 

Point forecasting which is the main focus of this work is about predicting a particular statistic of interest from the future distribution of values, such as mean or median. Therefore, different point forecast evaluation measures are also targeted towards optimising for a specific statistic of the distribution and it is important to distinguish which statistic it is for each error measure. For example, measures with squared base errors such as MSE and RMSE optimise for the mean whereas others with absolute value base errors such as MAE and Mean Absolute Scaled Error (MASE) optimise for the median. Although the mean and median are the same for a symmetric distribution, that does not hold for skewed distributions as with intermittent series. There exist numerous controversies in the literature regarding this. Petropoulos et al. (2020) suggest that it is not appropriate to evaluate the same forecasts using many different error measures, since each one optimises for a different statistics of the distribution. Also according to Kolassa (2020), if different point forecast evaluation measures are considered, multiple point forecasts for each series and time point also need to be created. Kolassa (2020) further argues that, if the ultimate evaluation measure is, e.g., MAE which focusses on the median of the distribution, it does not make sense to optimise the models using an error measure like MSE (which accounts for the mean). It is more meaningful to consider MAE also during model training as well. However, these arguments hold only if it is not an application requirement for the same forecasts to perform generally well under all these measures. Koutsandreas et al. (2021) have empirically shown that, when the sample size is large, a wide variety of error measures agree on the most consistently dominating methods as the best methods for that scenario. They have also demonstrated that using two different error measures for optimising and final evaluation has an insignificant impact on the final accuracy of the models. Berm´udez et al. (2006) have developed a fuzzy ETS model optimised via a multi-objective function combining three error measures MAPE, RMSE and MAE. Empirical results have demonstrated that using such a mix of error measures instead of just one for the loss function leads to overall better, robust and generalisable results even when the final evaluation is performed with just one of those measures. Fry and Lichtendahl (2020) also assess their same forecasts across numerous error measures in a business context. 

On the other hand, Kolassa (2016) also argues that point forecast evaluation alone is not sufficient. This is due to all the pitfalls associated with every point forecast evaluation measure as discussed in the rest of this section. Also, according to that author, evaluating only individual statistics of a distribution is not adequate and the overall predictive distributions need to be considered instead, in order to estimate the uncertainty of the produced point 

23 

forecasts with a reasonable confidence. Although not the main point of focus in this article, different evaluation measures have been proposed in this respect. Kolassa (2016) explains most of them including randomised probability integral transform (rPIT) and several proper scoring rules such as logarithmic score, Brier score, ranked probability score etc. 

Furthermore, depending on different data partitioning schemes, we may obtain many errors for the same model either for a fixed forecast origin or rolling forecast origin etc. In the context of global forecasting models, we train using many different series and also often evaluate on that same set of series. Thus, the number of series further increases the amount of errors available for a single model. For summarising errors across all available series as well as the different steps in the forecast horizon, we can consider a number of statistics such as median, arithmetic mean or geometric mean etc. Using medians and geometric means instead of arithmetic means helps with avoiding sensitivity to outlier series in a set of time series. However, this means that using the arithmetic mean identifies the existence of such outlier errors for certain series. The problem specifically with geometric mean based measures is that a model can perform perfectly (0 or _<_ 1 error) on one series and quite bad on all the others but still become the best (as the overall error becomes 0 or quite small due to multiplication) (Boylan and Syntetos, 2006). Thus, Svetunkov (2021) mentions that the use of several summary operators on the same errors can raise awareness regarding these issues of the individual errors. Summarising across series and across the horizon can be done using the same or different statistical operators. We can also change the order of summarising the errors; for instance we can first summarise the errors for the different time steps separately and then summarise those per time step error measures. When summarising across the horizon, weights can be assigned to different time steps to get a weighted measure as well. Different terminology has been introduced by researchers for these base errors, statistical operators etc. For instance, in the work by Kunst (2016), the base error functions are named as local distance functions and the statistical operators to summarise base errors are denoted as link functions. The resulting final error functions are known as metrics or distance functions. According to the terminology introduced by Hyndman and Koehler (2006), which we follow in this paper, the base errors are called Errors, and summarised by using different statistical operators into Error Measures. 

There are many different point forecast error measures available in the forecasting literature categorised based on 1) whether squared or absolute errors are used 2) techniques used to make them scale-free and 3) the operator such as mean, median used to summarise the errors (Koutsandreas et al., 2021). In the rest of this section, we first introduce, define, and categorise all different error measures introduced in the literature. We also provide the formulae for these measures and their general mathematical issues (not relevant to specific characteristics of the series). Then, we move on to provide an overview of certain types of data and possible problems that the error measures can have with them. We discuss which error measures are preferrable or should be avoided depending on each of the characteristics of time series as also stated in Section 3.1. 

Summarising all these details, the main results of this section are then Table 1 and Figure 11. Table 1 can be used to choose error measures under given characteristics of the data. In Table 1, the scaling column indicates the type of scaling associated with each 

24 

error measure mentioned in the previous column. This includes no scaling, scaling based on actual values, scaling based on benchmark errors as well as the categorisation such as per-step, per-series and all-series (per-dataset) scaling. The _†_ sign in Table 1 indicates that the respective error measures need to be used with caution under the given circumstances as explained in the above discussions. The flow chart in Figure 11 provides further support for forecast evaluation measure selection based on user requirements and other characteristics in the data. In Figure 11, the error measures selected to be used with outlier time series are in the context of being robust against outliers, not capturing them. 

## _6.1. Categorisation of Error Measures_ 

Different error measures in the literature are categorised as detailed in the following. We follow the categorisation of error measures introduced by Hyndman and Koehler (2006) and adopted by many successive works in this space. 

## _6.1.1. Scale-Dependent Error Measures_ 

Scale-dependent measures as the name suggests, are dependent on the scale of the series. In all the scale-dependent measures defined below, the scale-dependent base error _et_ used is as defined in Equation 9. 



Apart from MSE and MAE as defined in Equations 7 and 8, other examples of scaledependent measures which use _et_ as the base error are as defined below. 

1. Root Mean Squared Error (RMSE) 



2. Root Median Squared Error (RMdSE) 



3. Median Absolute Error (MdAE) 



4. Geometric Root Mean Squared Error (GRMSE) - Proposed by Syntetos and Boylan (2005). 



Geometric Mean Absolute Error (GMAE) 







Figure 11: Flow Chart for Forecast Error Measure Selection 

26 

|Error Measures<br>Scaling||RMSE|None<br>||ME|MAPE|OOS<br>RMSPE|Per Step<br>sMAPE|msMAPE|Actual<br>WAPE<br>OOS|Values<br>Per Series<br>WRMSPE|sMAE<br>In-Sample|Per Series<br>sMSE|ND<br>OOS|AllSi<br>NRMSE|eres<br>|MRAE|OOS<br>MdRAE|Per Step<br>GMRAE|Benchmark<br>RMRSE|Errors<br>Relative Measures<br>OOS<br>Per Series|MASE<br>In-Sample|Per Series<br>RMSSE|In-Sample<br>All Series|Measures with<br>Transformations<br>None|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Outliers|||<br>||||||||||||||†|†|†||†|||||
|Intermittence|||||||||||†||†|||||||†|†||†|||
|reaks<br>ferences)|f<br><br>Forecast<br>Origin||<br>|||||||||||||||||||||||
|uctural B<br> Scale Diff|f<br>Training<br>Region||<br>||||||||||||||†|†|†|†|†|†|†|||
|Str<br>(With|Forecast<br>Horizon||<br>|||||||||||||||||||||||
|Heteroscedasticity|||<br>|||†<br>|†||||||||||||||||||†|
|Unit<br>|Roots||<br>|||†<br>|†|||||||||||||||||||
|Stationary Count<br><br>Seasonality<br>Trend<br>|Data (_>>_0)<br><br>(Linear/Exp.)|<br><br>|<br> <br> <br> <br> <br>|<br> <br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br><br>|<br> <br>|†<br>†<br>|†<br>†<br>|†<br>†<br>|†<br>†<br>|†<br>†<br>|†<br>†<br>|†<br>†<br>|†<br>†<br>|<br><br>†|



27 

Since RMSE is on the same scale as the original data (due to the square and the squareroot), it is often preferred over MSE. Squared errors are known to lead to unbiased point forecasts since they predict the mean when used as a loss function (Kolassa, 2016). Although the definitions are slightly different, mathematically both GMAE and GRMSE are equivalent. The problem specifically with these geometric mean based measures is that a model can perform perfectly (0 or _<_ 1 error) on one series and quite bad on all the others but still become the best (as the overall error becomes 0 or quite small due to multiplication) (Boylan and Syntetos, 2006). 

Scale-invariant measures on the other hand are introduced for the requirement to be able to compare across series having different scales. Traditionally in forecasting, one series was mostly considered as a single dataset by practitioners in the domain. Therefore, scaling errors was limited to scales computed per each series or even each time step (to be able to compare errors across series). These approaches had several issues as explained next. However, in the current context of Big Data and global forecasting models, we are now in the situation where we want to compare models across datasets or select models that perform generally well on many datasets each having many series. Consequently, the error measures being introduced have also shifted from computing a scale per-series to a scale for the whole dataset. Such global scaling based error measures can address some of the issues with the per-step or per-series scaling. Nevertheless, Chen et al. (2017) state that despite the type of scaling used, the resulting error measure values need to be closely related to the scale of the series at the specific observation points. Hence, those authors opt for those measures that compute a per-step scaling. Due to the non-stationarities and non-normalities that are inherent in many time series, a constant estimator for scale (along the series or for the whole dataset) has been shown as a comparatively poor form of scaling for time series (Chen et al., 2017). 

## _6.1.2. Measures based on Percentage Errors_ 

In percentage error based measures, base errors are scaled by actual time series values. This means that the time series values get scaled with respect to the actual scale of the series. Percentage based measures were invented for inventory based series (having very high volumes, no intermittency) since they are more meaningful as indicating the percentage loss and thus easy to communicate. The percentage error is usually defined as in Equation 15, where _et_ is the scale-dependent error and _yt_ is the actual value at the _t_<sup>_th_</sup> time step. 



Examples of percentage errors are as follows. 

1. Mean Absolute Percentage Error (MAPE) 



28 

2. Median Absolute Percentage Error (MdAPE) 



3. Root Mean Square Percentage Error (RMSPE) - Used in the Rossmann Store Sales Forecasting Competition<sup>1</sup> (Bojer and Meldgaard, 2020) 



4. Root Median Square Percentage Error (RMdSPE) 



Percentage based measures have the issue that _pt_ is not symmetric since exchanging _yt_ with _y_ ˆ _t_ changes the value of the error measure. Moreover, percentages can be above 100% sometimes, which makes a flat forecast of all 0’s a better forecast with a 100% MAPE (Kolassa, 2017). Apart from that, percentage based measures only make sense with the existence of a meaningful zero (where divisions and ratios are meaningful). Other forms of percentage based measures have been introduced with different scaling factors. 

5. Symmetric Mean Absolute Percentage Error (sMAPE) - Idea first proposed by Makridakis (1993)<sup>2</sup> 



6. Symmetric Median Absolute Percentage Error (sMdAPE) 



sMAPE fixes the type of asymmetry seen with MAPE that the penalisation is different if _yt_ and _y_ ˆ _t_ are exchanged. Hence, it was used heavily in most early forecasting competitions. However, sMAPE is not as symmetric as its name suggests (Goodwin and Lawton, 1999); it is arguably even less symmetric. It penalises the underestimates more than the overestimates for the same value of _yt_ . Thus, it may tend towards selecting a slightly overestimating model. Nevertheless, this kind of asymmetry may be of interest to certain domains where underestimates are considered to be more costly than overestimates (Armstrong, 2001). sMAPE is also in general further criticised for its lack of interpretability (Hyndman and Koehler, 2006). 

> 1 `https://www.kaggle.com/c/rossmann-store-sales` 

> 2The original definition of sMAPE used at the M3 forecasting competition did not use absolute values of _yt_ and _y_ ˆ _t_ in the denominator, since all series had only positive values there. 

29 

7. Modified Symmetric Mean Absolute Percentage Error (msMAPE) 



This was introduced by Suilin (2017), to address issues with sMAPE, as detailed in the next Section. In Equation 22, _ϵ_ = 0 _._ 1 by default. msMAPE assigns the same scaling factor (0.6 in this case) for all _|yt|_ + _|y_ ˆ _t|_ less than or equal a certain threshold (0.5 in this case). This means that in this range, all errors are simply divided by a fixed constant, irrespective of the actual value or the forecast of the series. This idea is similar to the concept of winsorising of error distributions suggested by Armstrong and Collopy (1992), which is to clip extreme values/outliers (tails of the distribution) of the errors and replace them with certain limits/thresholds. Arnott et al. (2019) discuss the same idea of winsorisation for the purpose of excluding outliers from the data in the first place. In this sense, msMAPE can be considered as a winsorised version of sMAPE. 

However, the exact threshold at which to cut off the errors/data, depends on the scale of the series. For example, this threshold cannot be the same (say 0.5) on two series where one goes to a maximum value of 1000 and the other has values only in-between 0-1. Also, winsorising basically skews the error measure/data since all values in the distribution are cut off at a certain threshold. Therefore, msMAPE is rather ad-hoc and it does not estimate any statistic like the mean or median of the distribution; it is rather a biased version of mean/median. Apart from that, the issues arising from symmetry in sMAPE are still there in msMAPE as well, but only for larger actuals and forecasts that exceed the threshold. Due to these reasons, msMAPE is often disapproved by researchers, as it has no theoretical foundation and its statistical properties have not been explored. 

Kim and Kim (2016) introduced the Mean Arctangent Absolute Percentage Error (MAAPE), which retains the original scaling factor of percentage based measures, and thus its associated intuitive interpretation. 

8. Mean Arctangent Absolute Percentage Error (MAAPE) 



The Weighted Absolute Percentage Error (WAPE) is defined as in Equation 24 and performs the scaling based on the OOS values of the series in the whole forecast horizon. 

9. Weighted Absolute Percentage Error (WAPE) 



Similar to the modification on MAPE to obtain sMAPE, WAPE can also be modified in the denominator to form the Symmetric Weighted Absolute Percentage Error (sWAPE) 

30 

measure, although this has not been defined previously in the literature, to the best of our knowledge. Similar to sMAPE, sWAPE also avoids the problem of the final error being different when _yt_ and _y_ ˆ _t_ are exchanged. 

10. Symmetric Weighted Absolute Percentage Error (sWAPE) 



A similar version can be defined as follows, using squared errors in the numerator as opposed to absolute errors. 

11. Weighted Root Mean Squared Percentage Error (WRMSPE) 



WAPE and WRMSPE defined above are for a single series, whereas for multiple series, the per-series errors can be summarised using mean, median etc. In the denominator of WAPE and WRMSPE, _T_ is the length of the training part of the series whereas _h_ is the size of the forecast horizon. A different version of the OOS scaling of WAPE was proposed by Wong (2019) as in Equation 27. 

12. Relative Total Absolute Error (RTAE) 



RTAE above is defined for a single series. In Equation 27, _C_ refers to a regularisation constant to ensure that the denominator does not fall below the threshold _C_ . In this sense, RTAE also follows the concept of winsorising discussed above for msMAPE and thus, all the associated issues hold here as well. However, as opposed to WAPE and RTAE where the aggregation of the values in the denominator is done OOS, this aggregation can be done in-sample as well. Petropoulos and Kourentzes (2015) use a set of error measures in their work that follow this idea. The base error for these measures is defined as in Equation 28 where _T_ stands again for the length of the training part of the series. 



In the work by Petropoulos and Kourentzes (2015), _p_<sup>_†_</sup> _t_<sup>isnamed asthescaledError(sE)</sup> and _p_<sup>_†_</sup> _t_ 2 is named as the scaled Squared Error (sSE). Similarly the scaled Absolute Error (sAE) is defined in Equation 29. 

31 



In both _p_<sup>_†_</sup> _t_<sup>and</sup><sup>_p‡_</sup> _t_<sup>,theerrorattimestep</sup><sup>_t_intheforecasthorizonisscaledbythemean</sup> of the actual values in the whole training region of the series. They are named as scaled errors to indicate similarity to the scaled errors discussed further in Section 6.1.5, where error measures are scaled by a scaling factor dependent on the time series to make them scale-free. However, in this case, since actual values of the series are used to compute the scale, they can be interpreted similar to the aforementioned percentage based measures. The error measures by using these as the base errors can be defined as below. 

13. Scaled Mean Error (sME) 



14. Scaled Mean Squared Error (sMSE) 



15. Scaled Mean Absolute Error (sMAE) 



Another option for scaling based on actual values is to consider the OOS values (in the forecast horizon) as in the WAPE error measure mentioned above, but aggregated over all the series in the dataset. Salinas et al. (2020) use such error measures in their work as defined below. 

16. Normalised Deviation (ND) 



17. Normalised Root Mean Squared Error (NRMSE) 



## _6.1.3. Measures based on Relative Errors_ 

In Relative Errors, scaling is done through dividing by errors from a benchmark method. This scaling is done per each time step (the error of the model at a particular time step is divided by the error from a benchmark method such as the na¨ıve or the seasonal na¨ıve for the same time step). The idea is to measure the performance of the forecasting model with 

32 

respect to this benchmark method. On top of being scale-independent (errors scaled with respect to the scale of the series), relative measures are useful when necessary to average over series that differ in forecastability. These measures can standardise the series for their degree of difficulty in forecasting since the models are compared against a benchmark method on the same series (Armstrong et al., 2001). The relative error is defined as in Equation 35 where _e_<sup>_b_</sup> _t_<sup>denotestheerrorofabenchmarkmethod,commonlythena¨ıvemethod.</sup> 



Measures based on relative errors are as defined below. 

1. Mean Relative Absolute Error (MRAE) 



2. Median Relative Absolute Error (MdRAE) 



3. Root Mean Relative Squared Errors (RMRSE) 



4. Geometric Mean Relative Absoluate Error (GMRAE) 



Relative Geometric Root Mean Squared Error (RGRMSE) 



Although the definitions are slightly different, mathematically both GMRAE and RGRMSE are equivalent. 

The biggest advantage of these measures is that they are more interpretable, and directly comparable across datasets unlike those unbounded measures mentioned before. For instance, a MAPE value of 1% in itself gives no indication whether it is a high or a low value for the particular series without any explicit benchmark comparisons. On the other hand, measures which scale based on benchmark errors give direct interpretation of how 

33 

good or bad the model is with respect to the benchmark, and thus also become comparable across datasets. However, with these relative measures the relative magnitude of the overall errors that we get depends on the competence of the underlying benchmark method on the respective series. Large errors from the benchmark methods tend to lessen the impact of the errors from our models. The opposite can happen too, where the underlying benchmark method is extremely good on one of the series in the dataset (very low benchmark errors), and thus overly exaggerates the errors from the forecasting model for that particular series, compared to the others. Thus, it becomes hard to capture models that do well on such series. Therefore, the choice of the benchmark method plays an important role for relative errors. 

## _6.1.4. Relative Measures_ 

An alternative way of estimating the accuracy of methods with respect to benchmarks is by using Relative Measures. These measures simply consider the division of an error measure for the forecasting model, by that of a benchmarking method; which resolves to the relative of error measures. For example, the relative measure with MAE can be defined as below, where _MAEb_ indicates the MAE value of the benchmarking method for the considered period. 

1. Relative Mean Absolute Error (RelMAE) 



Similar measures can be defined using the previously mentioned scale-dependent measures such as MSE, MdAE as well as scale-invariant measures such as MAPE, sMAPE etc. For example, RelMSE and RelRMSE can be defined as below. 

2. Relative Mean Squared Error (RelMSE) 



3. Relative Root Mean Squared Error (RelRMSE) 



Lai et al. (2018) introduced a different version of a relative measure defined as below. 

4. Root Relative Squared Error (RSE) 



34 

In RSE, the root squared error of all the OOS time steps across all the series is scaled by the root squares of the difference between the actuals and the mean computed for the same data points. Therefore, the benchmark forecast used in RSE is the mean forecast by considering the OOS points across all the series. 

Davydenko and Fildes (2013) proposed the following relative measure across series in their work, where _m_ denotes the number of series and _hi_ the number of testing time steps in the _ith_ series. Those authors argue that the geometric mean is the more suitable operator over the arithmetic mean for summarising relative measures. 

## 5. Average Relative Mean Absolute Error (AvgRelMAE) 



Similar to relative errors, the benefit of using relative measures is that their interpretation is quite intuitive. If the value of the error measure is _<_ 1, this means that the forecasts from the model are more accurate than the benchmark. If the value is _>_ 1, it means the opposite that the benchmark is better than the evaluated forecasting technique. However, relative measures require more than one step forecasts from each series to compute an MAE per each series. Otherwise, in the one-step forecasts case, it basically resolves to computing a relative error per each step, which brings back all the issues of relative errors as discussed later in the next section. However, this can be resolved by computing the MAE across multiple series. Yet, scale-dependent measures such as MAE only make sense when all the series have the same scale. Other than that, problems of the relative measures depend on the pitfalls of the base error metrics chosen, as detailed in the next section. 

## _6.1.5. Measures based on Scaled Errors_ 

The idea of scaled errors was first introduced by Hyndman and Koehler (2006) as an alternative to relative errors and relative measures which compare methods with respect to a benchmark. A scaled error as discussed here, scales the error of a forecasting method by the in-sample MAE of a benchmark method such as the na¨ıve method. The scaled error by using MAE for the benchmark can be defined as in Equation 46. 



Error measures which use the above scaled error _qt_ as the base error can be defined as below. 

1. Mean Absolute Scaled Error (MASE) 



35 

## 2. Median Absolute Scaled Error (MdASE) 



A similar scaled error by using MSE of the benchmark for the denominator can be defined as in Equation 49. 



Error measures by using _qt_<sup>_†_asthebaseerrorcanbedefinedasbelow.</sup> 

3. Root Mean Squared Scaled Error (RMSSE) - used in the M5 Forecasting Competition (Makridakis et al., 2020a). 



Measures based on scaled errors are symmetric, meaning that both positive and negative errors as well as errors of the same magnitude at both high-valued and low-valued points of the series, get penalised the same way (Koutsandreas et al., 2021). The interpretation of MASE is that, if the value is _<_ 1, the proposed method is better than the one-step ahead na¨ıve method in-sample and the opposite if the value is _>_ 1. In this sense, these measures have a meaningful interpretation and according to Hyndman and Koehler (2006), they are applicable to a wide variety of forecasting scenarios without any problems. However, as Koutsandreas et al. (2021) argue, the measure generally has limited interpretability when applied in business applications in practice. Since the comparison is performed against insample benchmark errors, the results are difficult to communicate. Therefore, these measures are used mostly in research related work due to their beneficial properties. 

Another problem with scaling based on in-sample one-step ahead benchmark errors occurs when the evaluated model produces multi-step ahead forecasts. Using a one-step ahead in-sample na¨ıve forecast as benchmark will often result in huge errors ( _>>_ 1) for the forecasts far ahead in the horizon, simply because the benchmark tackles an easier forecasting problem. Another problem is that this procedure makes the MASE errors coming from two datasets with two different sizes of the forecast horizon incomparable with each other. The solution is to consider in-sample multi-step ahead forecasts (with the same size as the forecast horizon) for the benchmark method as well, for reasonable comparison (Hyndman and Koehler, 2006). However, this procedure may be complicated to implement and may hinder interpretability. Also, care needs to be taken about which benchmark is used. For certain series a one-step-ahead na¨ıve may be adequate, and for other series a seasonal na¨ıve benchmark. The measures cannot be compared across datasets/series when the underlying benchmark used is different in each scenario. 

36 

## _6.1.6. Measures based on Ranks/Counting_ 

Instead of summarising base errors, we can also summarise rankings of models resulting from the base errors for the different series or different time steps in the horizon. This way we can obtain a fully scale-free error measure even by using absolute error as the base error. The M competition and the M3 competition used a ranking among the participating methods (Makridakis and Hibon, 2000). However, one problem with ranking is that it is dependent on the other competing methods. 

A similar idea to measures based on ranks is “Percentage Better”, also used in the M3 competition (Makridakis and Hibon, 2000). Here, the idea is to use a benchmark method such as random walk and count how many times (across series and time steps) a given method is better than the benchmark and report it as a percentage. In this sense, this measure also has similarities with the relative measures since the comparison is done against a benchmark (Koutsandreas et al., 2021). Hyndman and Koehler (2006) name this measure as PB score and define it for instance with MAE base errors as follows. 



A similar idea was proposed by Wong (2019) to measure the percentage of forecasts where the value of a particular error is higher than a margin X. This error measure can capture succinctly how severe the deviations of the forecasts of the model from the actuals are and whether to take action about it. This error measure was named the ‘Percentage of Critical Event for Margin X’ and is slightly different from Equation 51 as below. In Equation 52, the error measure _E_ can be any measure defined per user requirements. 



## _6.1.7. Measures based on a Transformation_ 

There are other scale-invariant error measures which use a transformation such as logarithm on the errors which can be defined as follows. Assuming non-negative time series, to avoid problems with 0 values in the logarithm, 1 is added to both the actual values as well as the predictions. The following is defined by using the natural logarithm. 



Error measures based on logarithmic errors are known to optimise for the geometric mean of the distribution (Svetunkov, 2021). The above formula is mathematically equivalent to the following Equation 54. Therefore, as Tofallis (2015) also claim this error gives rich information indicating both a difference as well as a ratio (similar to percentage based measures). 



1. Root Mean Squared Logarithmic Error (RMSLE) - Used for the Walmart Stormy 

37 

Weather Forecasting Competition<sup>3</sup> and Recruit Restaurant Visitor Forecasting Competition<sup>4</sup> (Bojer and Meldgaard, 2020) 



Tofallis (2015) name the same error measure as Log Accuracy Ratio (LogAR). 

2. Normalised Weighted Root Mean Squared Logarithmic Error (NWRMSLE) - Used for the Corporaci´on Favorita Grocery Sales Forecasting Competition<sup>5</sup> (Bojer and Meldgaard, 2020). In this particular competition, the weights for the different series were provided separately to the participants. Perishable items were assigned a weight of 1 _._ 25 and all the others were assigned a weight of 1 _._ 00. 



Log transformation makes the data approximately normal by scaling down the errors using a monotonic transformation. However, the transformation due to logarithm is not a bounded transformation; thus it does not scale values to a pre-specified range. Nevertheless, it has several useful mathematical properties. The RMSLE measure is symmetric meaning that interchanging _yt_ and _y_ ˆ _t_ does not change the value of the measure. Moreover, these measures produce unbiased forecasts, with the effect from the over-forecasts and underforecasts being balanced (Tofallis, 2015). 

## _6.1.8. Other Error Measures in the Literature_ 

In this section, we also report a few other error measures that have been published in the literature. 

1. Rate-based Error Measures - Introduced by Kourentzes (2014) 



Measures which use _ct_ as the base error can be defined as below. 

- Mean Squared Rate (MSR) 



> 3 `https://www.kaggle.com/c/walmart-recruiting-sales-in-stormy-weather/` 

> 4 `https://www.kaggle.com/c/recruit-restaurant-visitor-forecasting` 

> 5 `https://www.kaggle.com/c/favorita-grocery-sales-forecasting` 

38 

• Mean Absolute Rate (MAR) 



Measures based on rate-based errors, are in general suitable for inventory management decision making where the exact accuracy per each time step is not the interest; rather, maintaining an optimal inventory without many underestimations is more important. 2. Weighted Mean Absolute Error (WMAE) - Used at the Walmart Store Sales Forecasting Competition<sup>6</sup> (Bojer and Meldgaard, 2020). The weights can be assigned either for particular series (when summarising across series) or particular time steps in the horizon (for promotion periods etc.) For example, in the aforementioned competition, a weight of 5 has been assigned to the days if the corresponding week has a holiday and a weight of 1 otherwise. 



With WMAE, the idea is to heighten or lessen the impact on particular series/days based on their importance by using appropriate weights. However, if the individual series have very different scales, the intended impact from a particular day from different series would still be subject to scale differences of those series. The error impact from a series with high scale will be higher than the impact on a series with lower scale (even though the used weight is the same). This can be circumvented by adjusting the weights assigned to the individual series based on their scales or by using a scale-free base error. 

3. Empirical Correlation Coefficient (CORR) - Proposed by Lai et al. (2018). 



This definition follows the idea of the correlation coefficient to measure the linear relationship between two variables. The outer mean in Equation 61 is calculated across multiple series where _m_ denotes the number of series in the dataset. The inner mean is calculated for the different time steps of the individual series. Unlike other error measures, for CORR higher values are better. With the CORR error measure, we may select a biased model as the best model since the correlation between the actuals and the biased actuals is perfect. This scenario is illustrated in Figure 12 where model A is a heavily overestimating model with a better CORR value of 4.55 than model B with a lower CORR value of 4.48. Therefore, CORR will select model A as the better model although model B as shown is a better suited model for this scenario. 

> 6 `https://www.kaggle.com/c/walmart-recruiting-store-sales-forecasting/` 

39 



Figure 12: CORR Error Measure Issue - With Heavily Biased Forecasts 

## _6.2. Problems of the Error Measures and Guidelines_ 

In this section, we outline which error measures are applicable for each of the characteristics of the underlying time series. Since there is no single error measure that is applicable universally for all circumstances, as long as we are aware of the common pitfalls of error measures and ensure that the series under consideration are free from the troublesome characteristics, it should be safe to use the respective error measures for forecast evaluation. 

Scale-dependent measures perform no scaling and are thus suitable for comparing methods across series that have similar scales, but not with different scales. When evaluating across series, the total error with scale-dependent error measures is dominated by those series that have higher scales/volumes. Because of this, a model can perform poorly on higher scaled series and really good on all the other series, but still end up as the worse model, with scale-dependent measures. However, depending on the business context, this can be a valid objective to forecast more accurately the series that have higher scales, since they may be really the objects of interest. Also, if the set of series under consideration have meaningful scales, making errors scale-free is perhaps not needed at all. This is the case with most of the real-world time series such as retail sales of certain products. However, the problem with scale-dependent measures is that, as soon as the scale of the series is changed (for example converting from one currency to another), the value of the error measures change (Tashman, 2000). We may sometimes be even more interested in the final dollar value of the sales rather than the actual sales volume itself. In such a scenario, the errors need to be calculated in the respective scales of interest. Furthermore, if the underlying series/datasets contain no scale differences at all, the best option to compute errors is by using scale-dependent RMSE/MAE 

40 

error measures which are robust against scaling in many practical time series scenarios. The errors computed likewise can be used in statistical tests for significance of the differences as described in Section 7 to get a better picture of the competitiveness of the used models. 

The need for scale-free measures comes from the wish to be able to evaluate models across time steps/series/datasets, with different scales. For example, if we say that MAE is 10 for a particular series, we have no idea whether it is a good or a bad accuracy. For a series with an average value of 1000, this amount of accuracy is presumably quite good, whereas for another series with an average value of 1, it is a very bad accuracy. If we want to obtain models that in general produce good forecasts for all the time series despite their scales, then scale-invariant measures are the better option. The underlying objective of making errors scale-free is that all the errors (coming from different time steps/series/datasets) contribute to comparable amounts of influence in the final overall error measure value, instead of some errors always dominating over others due to their scales. The error measures seen in the literature, have different forms of scaling; per-step, per-series or per-dataset. The particular scaling and therewith the error measures selected, depend on the underlying intentions of practitioners. In general, applications which intend to have comparability across differently scaled time steps of a single series may be more interested in per time step scales. Per series scaling holds for comparing among differently scaled series (with respect to forecastability or volume) within a dataset, but not necessarily for such differently scaled time steps within an individual series. On the other hand, global scales apply mostly for similar scaled time series within datasets, but have totally varying scales on different datasets, which we want to compare the models across. This is because, within a dataset, a global scaling does not perform a scaling per each series, but rather scaling all of them, due to simply dividing by a constant for the dataset, which still makes the errors scale-dependent in their relative differences. Therefore, if we are confident that the series within a single dataset are similar scaled, this type of scaling can be used to select models that perform well in general across different datasets with different scales, or to investigate how the performance of models differ across datasets by comparing. Log transformed errors also perform a scaling down of all the errors. However, log transformation is a monotonic transformation and therefore, unlike global scaling, log transformed errors are not quite suitable for comparison across datasets having different scales. 

Apart from that, counting/ranking is a good option for making errors scale-free in general, since there are no issues associated with the computation of the scale arising due to non-stationarities of the time series considered. Scale-dependent measures such as RMSE, MAE also avoid issues arising from the computation of the scale in scale-free measures (as further detailed in the following). Therefore, if comparison across different scaled series is a necessity, a more robust way of making errors scale-free is to compute RMSE/MAE values and consider the ranks of the involved models per series according to those measures. Ranking ignores the actual size of the errors, this can effectively avoid the errors being biased towards higher scaled series. However, due to the same reason, one method can perform marginally better than all the other methods in all the series except one where it is drastically worse than all the others. In such a scenario, a measure based on ranking would select that method as the best whereas in reality we would be more interested in a method that 

41 

performs generally good on all the series. PB score too follows the same behaviour. 

Traditionally, in forecasting, the scale of series was only a problem at the end, because methods were trained per series but evaluated across series. Now, with global/pooled models which learn across many series, we have these scaling problems already at the model building phase, i.e. when normalising the input data. If the series have meaningful scales, and the final evaluation is expected to be performed on these original scales, it does not make sense to perform the modelling initially on pre-processed scale-free series. On the other hand, as is the practice in the ML community, most ML based models (apart from tree based models) are known to perform better with normalised data where all data points have similar scales. This makes the convergence of these models to optimal parameters much faster and accurate. Therefore, this poses a form of a contradiction between the model building and model evaluation phases for a global model. This can be addressed to a certain extent by using other techniques such as enforcing a partial scale dependence in the loss function used for model training or use the scale normalisation only for feeding inputs to the models and compute the losses on the original scale etc. As we deem the pre-processing of data to be outside the scope of our work, we focus in the following on the error measures and problems. However, very similar considerations hold for normalising data as pre-processing for ML methods. 

Apart from that, from a business perspective, we are more interested in calculating different error measures and estimating the model performance from many dimensions/aspects collectively (Fry and Lichtendahl, 2020). Evaluating the same forecasts with respect to many evaluation measures is a form of sanity checking to ensure that even under other measures (though not directly optimising for them), the forecasts still perform well. Furthermore, within a more practical context, forecasting and the respective accuracies of models alone are not sufficient, but rather how the produced forecasts affect the downstream decision making processes. In this sense, it can be argued that the final accuracy of the evaluated models need to be closely tied to business utility as seen by the downstream processes being optimised, such as energy costs, storage costs and trade-offs between them etc. This effectively makes the loss functions of models dependent upon each application specific requirement by having different constraints imposed. For example, with respect to short-term air quality prediction, it is more important to predict the peaks (extreme events) right, to detect potential health hazards. Similarly, in terms of wind power prediction, ramp forecasting (forecasting large and rapid variations in wind power) is of more importance, since that may help better plan for costs of extreme power integration into the grid and other power system operations. Hence, in both these scenarios probabilistic forecasting may be more interesting to understand how reliable the extreme forecasts would be. 

In the work by Spiliotis et al. (2021), using the M5 Competition dataset they demonstrate that simpler empirical methods may outperform sophisticated ML models when the focus is on the downstream inventory optimisation processes. Therefore, oftentimes, the relationship between accuracy and final business utility is not a linear one indicating that a fine-grained improvement of one model over another in terms of forecasting does not necessarily guarantee significantly improved business value. Abolghasemi and Esmaeilbeigi (2021) have also emphasised the same with respect to their first place solution at the IEEE-CIS Techni- 

42 

cal Challenge on Predict + Optimize for Renewable Energy Scheduling (Bergmeir, 2021). Forecasting and optimisation are considered as difficult problems by themselves separately. While methods can be developed by combining the two together, this inevitably results in quite complex loss functions customised for each specific business scenario. Although such exhaustive discussions would be useful, we opt to limit the scope of this work to analyse how the evaluation measures are influenced by other common patterns and characteristics of time series, due to the lack of practicality in the former approach. 

In the following, we conduct an in-depth analysis on which error measures out of those mentioned in Section 6.1 are applicable under different characteristics of the underlying time series. 

## _6.2.1. Count Data Well above Zero with Stationarity_ 

Under this category we imply series having no special non-stationarities such as trends or seasonalities. Apart from these characteristics, these types of series are also bounded by certain upper and lower limits. For series like these having no problematic characteristics generally any error measure is applicable. However, on certain types of series such as an AR process with a large negative coefficient at a low order lag where the series keeps fluctuating considerably for each time step, measures which scale based on errors from a na¨ıve benchmark method, need to be used with caution. This is because on such series, the na¨ıve method will usually have bad performance, even when considering rolling origin to constitute the forecast horizon. Figure 13 depicts this scenario for the rolling origin na¨ıve forecast. According to this figure, the model forecast in scenario _A_ , which has a slightly higher MAE of 0.41 than scenario _B_ , has resulted in a much lower MRAE of 0.25 than the 4.46 in scenario _B_ , simply due to the bad performance of the na¨ıve forecast in scenario _A_ . 

Furthermore, relative measures face similar issues of relative errors where the errors depend on the relative competence of the benchmark method in the intended forecast horizon. 

## _6.2.2. Seasonality_ 

On series having seasonality, percentage based measures tend to underestimate the errors at uncaptured peaks of the time series heavily, due to dividing by large actual values in the percentage (Wong, 2019; Kunst, 2016). On the other hand, when the actual values of the time series are quite small in magnitude, percentage based measures overstate the errors due to noise. This scenario is depicted in Figure 14, where for the three points _A, B_ and _C_ , Absolute Percentage Error (APE), is indicated separately. According to this scenario, the large error at peaks _A_ and _C_ get more or less similar attention to the small error at the relatively lower-scaled point _B_ . Averaging to compute MAPE, further decreases the effects on uncaptured peaks on this series. Depending on the business scenario, predicting these peaks accurately may be important, rather than focussing on the smaller fluctuations due to noise; for example, the peak demands of electricity. Therefore, percentage based measures such as MAPE, MdAPE, RMSPE can be problematic with seasonal series. 

However, this problem of percentage based measures on seasonal series can be largely overcome by using measures such as WAPE or ND, NRMSE which compute the scale based on several aggregated time steps or series. When scaling based on benchmark errors is used, 

43 



Figure 13: Relative Errors Issue - On a Series Following an AR Process with a Negative Coefficient) 



Figure 14: MAPE Error Measure Issue - On Series with Seasonality 

44 

on series having seasonality, it needs to be ensured that the used benchmark method can capture seasonality, such as a seasonal na¨ıve method, to be competitive against the evaluated forecasting method. 

## _6.2.3. Trends_ 

When there are strong trends existing in the series, scale-free measures which compute their scale by aggregating the values (actual values or benchmark errors) at several time steps, tend to face problems. This situation is in resonance with the phenomenon explained by Chen et al. (2017) that the error values at each time step need to comply with the scale of the series at each point. A scale computed by aggregating over several time steps which include non-stationarities/non-normalities such as strong trends may not always be a good estimator to represent the scaling factors for all the time steps of such a series. For example, on a series having a strong upward trend, when calculating WAPE as the error measure, a certain amount of discrepancy between the actuals and the forecasts can get a lower attention than the same amount of discrepancy on a series having no such strong trends. The opposite can happen too, due to downward trends. The same situation occurs with in-sample values based scaling such as sMAE, sMSE. With Relative Errors and Relative Measures as well, on series having strong trends/heteroscedasticity, if the benchmark is fixed origin mean forecast or the na¨ıve method, the benchmark errors become large on such non-stationary series as depicted in Figure 15. This results in very small overall relative errors for the evaluated model, as in scenario _A_ , although the model here seems to have similar performance to the model in scenario _B_ . 

To deal with this problem related to non-stationarities of series when computing the scale of percentage based measures, some form of rolling-window based summary statistic computed along the series can be used. The size of the windows are to be decided to fit the context of the underlying series. However, for measures such as MASE, RMSSE, which scale based on in-sample benchmark errors, this is not a problem. MASE can compute comparable amounts of scaling for both stationary and non-stationary series with for example trends, since the in-sample error from the na¨ıve method is considered which can account for trends in the training region. 

Apart from that, when a global scale is computed, as with the ND measure, it is no different from measures such as RMSE, MAE which are scale-dependent. Because, the scaling factor that they compute is constant for all the time steps across all the series. Therefore, they are clearly not used in place of measures such as MAPE on trended series, where non-stationarities are accounted for, in the scaling factor per each time step. It is also important to be aware that, on series especially having exponential trends, when using log transformation based error measures, they greatly reduce the impact of errors from models. This is indicated in Figure 16. 

## _6.2.4. Unit Roots_ 

The characteristics of a series resulting from unit roots are very similar to trends. They have stochastic trends, where the direction of the series at each time step is random (due to noise) in contrast to deterministic trends. However, on a series like this, the na¨ıve forecast is 

45 



Figure 15: Relative Errors Issue - On Trended Series 

a quite competitive benchmark and as explained in Section 3.2, and it is essential to compare against it. Scaled Errors such as MASE provide this support directly. On the other hand, since level changes are often seen with these unit root based series, the error measures which are suitable or unsuitable here are the same as with trended series explained in the previous section. This means that measures which compute their scale based on aggregate in-sample or OOS values or Relative Errors may tend to have problems on unit root based series. However, measures which compute a per-step scaling based on actual values, such as MAPE, RMSPE may also have issues with these series not capturing peak points similar to seasonal series. 

## _6.2.5. Heteroscedasticity_ 

Heteroscedastic series experience a change in the variance of the data over time. This happens mostly due to noise embedded in the time series data. With respect to forecast evaluation, this is not a very problematic characteristic since it is not associated with level changes in the time series. However, due to potential peaks and troughs in the series which may have very high and low variances due to the heteroscedasticity, measures such as MAPE and RMSPE may have problems with capturing those peaks similar to seasonal time series. Apart from that, log transformation based errors can reduce the impact from heteroscedasticity, consequently also suppressing the errors of models at such points with high variance in the data. 

46 



Figure 16: Transformation based Measures Issue - On a Series having Exponential Trend 

47 

## _6.2.6. Structural Breaks (with Level Shifts)_ 

Due to trend changepoints/structural breaks existing in the horizon, especially if we are predicting over a long horizon, WAPE can have problems as with trends in Section 6.2.3. This scenario is illustrated in Figure 17 where there are two regimes within the forecast horizon with a changepoint in scenario _A_ . Regime change here is the same as concept drift that we refer to in ML. Because of this non-stationarity, the scale/mean of the series is not consistent throughout the series. Due to the downward trend in the second regime, the overall scale of this series becomes smaller than in series _B_ with no regime shifts. Thus, the same amount of error (with same forecast and same actual value) at point _X_ , gets a higher attention on series _A_ than on series _B_ . 



Figure 17: WAPE Error Issue - On Series with Structural Break in the Horizon 

A similar situation applies to error measures which scale based on in-sample values, such as sMSE, sMAE. Due to structural breaks (anywhere in the series including in-sample, forecast horizon or the forecast origin), the mean of the series is not expected to hold constant throughout the whole series. For example, the same amount of _et_ in the horizons of two series, with same actuals and same forecasts from the model, can result in different overall errors when the values in the training region of the two series are different from each other, due to for example structural breaks in-sample. This scenario is depicted in Figure 18, where the series _A_ has a structural break in the training region, but has the same actual values as series _B_ in the forecast horizon. The model too has produced the same forecasts for both series _A_ and _B_ , in the forecast horizon. This means that _et_ is the same for both 

48 

series. However, due to scaling based on in-sample values, for series _A_ , sMAE gives a slightly higher value than on series _B_ . With OOS global scaling, the situation is similar to trends. On a series having non-stationarities such as a structural break, such measures are not used in the idea of scaling with respect to each time step or series, since the global estimator if the scale is a constant one. 



Figure 18: In-sample Scaling based Error Measures Issue - On a Series with Structural Break In-sample 

On the other hand, measures which compare against a benchmark are applicable as long as the used benchmark is comparable in accuracy to the model in the intended forecast horizon. This holds true for relative errors and measures (purely based on OOS errors), on series with structural breaks anywhere in the series. The evaluated model is expected to perform poorly on such a series when for example the structural break is in the horizon or the forecast origin. The same applies for the benchmark OOS as well. However, if the mean forecast is used as the benchmark instead of the na¨ıve method, in the particular case when there are structural breaks in the training region, the evaluated model may be quite good OOS, but the mean forecast both in-sample and OOS may be badly affected by the changepoint. This is because, the mean forecast depends on the whole history of the series, including both before and after the changepoint. On scaled errors too, potential structural breaks in the horizon or the forecast origin can become problematic. The in-sample na¨ıve will perform well whereas the OOS forecast from the proposed method may be completely different from the actuals. This situation is illustrated in Figure 19 where a changepoint existing at the forecast origin makes the training region different from the testing region. Hence, considering in-sample errors of the benchmark for the scaling factor in this case has resulted in a MASE value higher than 1, which means that the model is worse than the 

49 

seasonal na¨ıve benchmark. However, OOS it is seen that the benchmark method has even a higher MAE than the model due to the structural break. Therefore, high or low value of this error measure is not necessarily equivalent to good or bad performance. It needs to be ensured that the scale computed in-sample with benchmark errors is a reasonable scale for the errors OOS. 



Figure 19: Scaled Errors Issue - On series with a Structural Break 

## _6.2.7. Intermittent Series_ 

With intermittent series where the distribution is heavily skewed with mostly 0’s (e.g., common in retail), the mean of the series is typically higher than 0 and the median is a 0 if more than 50% of the values in the series are zeros. However, on such intermittent series, the non-zero values are important and need to be captured well. Therefore, on such series, RMSE which minimises for the mean will be a better option to select models that predict non-zero values while MAE may select models that predict constant 0’s, or are at least heavily biased towards zeros. Due to the same reason, when used as a loss function for model training too, RMSE is better on intermittent series than MAE. Therefore, using squared errors with mean operator for aggregating the errors is usually the better option for this type of series. 

With any percentage based error measure, _pt_ can be undefined when the actual values _yt_ are 0 or close to 0, which is a very common phenomenon with intermittent time series observed in the real-world. When the actual values are close to 0, the error distribution becomes heavily skewed with extremely large errors. But, these large errors do not mean that the model performs poorly; they are simply a result of low actual values of the series (Davydenko and Fildes, 2013). Those large error values are produced from the error 

50 

measure despite the forecasts from the model at those points. It may be the case that the model produces a very accurate forecast quite close to 0, but the division by the actual value results in a very high error. On the other hand, even with an inaccurate forecast at such a point, the final error would be equally very high. Due to this reason, measures such as MAPE are not competent in distinguishing good and bad forecasts at actual values of 0. When the actual value and the forecast are both 0 too (perfect prediction at 0 actual values), MAPE becomes undefined. Some software systems that deal with MAPE error values simply disregard the errors at 0 actuals when computing the overall error measure. But, this has teh problem that it means that the accuracy of forecasts for 0 actuals are not important, which depending on the application may be true or not. (Kolassa, 2017). It also means that such a modified measure does not estimate the mean nor the median nor any other meaningful summary statistic of the distribution that was originally intended to be optimised for. Using MdAPE on intermittent series instead of MAPE also results in a slightly more robust error measure to 0 actual values. However, this also makes MdAPE less sensitive to errors at the 0 actuals, which are important and meaningful, and may overlook problems of the underlying model at such points (Davydenko and Fildes, 2013). 

The problem of division by values close to 0 in MAPE is addressed to a certain extent in sMAPE. Yet, if _yt_ is close to 0, it is highly probable that _y_ ˆ _t_ is also close to 0. So the problem of undefined values arising from division by values close to 0 still exists in sMAPE. Furthermore, if the actual value is 0, regardless of the value of the forecast (unless equal to 0), the sMAPE value ends up as 200 (the maximal value) (Syntetos and Boylan, 2006) even though the difference between the actual and predicted values can be quite small. Therefore, in the case of intermittent series, if sMAPE is used as the evaluation measure, we effectively require the underlying forecasting technique to predict actual zeros, for example through a zero-inflated model, since the error measure does not capture good forecasts at such points, similar to MAPE. The msMAPE with its modified denominator, specifically addresses the issue of division by values close to 0 in sMAPE. It provides a very straightforward fix/adjustment for the issue of division by 0 values, but it has issues as discussed in Section 6.1.2. In the MAAPE measure, The _arctan_ function is well defined for all real values. Thus, unlike _pt_ , the base error in MAAPE approaches _π/_ 2 when division by 0 occurs. However, when both _yt_ and _y_ ˆ _t_ are 0 (perfect prediction), MAAPE becomes undefined. Therefore, predicting 0’s right in a series can break this measure similar to sMAPE and MAPE. On the other hand, for any forecast other than 0, at a time step of an actual 0, MAAPE produces its maximum value of _π/_ 2, despite how close the forecast is to 0. In this sense, MAAPE shows a similar behaviour to sMAPE and MAPE where for actual 0’s, the error measure is not consistent. 

Another technique for avoiding division by 0 issues in error measures is to consider multiple time steps in the denominator as opposed to just one. This is what measures such as WAPE try to achieve. The actual values of the series for the whole forecast horizon are summed up before the division. This greatly reduces the risk of dividing by 0 values in the original percentage error _pt_ , where the division happens per each time step. WAPE is undefined only when the total of all the actual values corresponding to the forecast horizon are zero. However, that too is not that rare with a short forecasting horizon and very 

51 

intermittent series. Nevertheless, due to this robustness, WAPE is generally more preferred in application scenarios than MAPE. However, due to using absolute errors, WAPE too has the problem that, on intermittent series it may select models predicting constant 0’s. This can be circumvented by including squared errors _e_<sup>2</sup> _t_<sup>inthenumeratorasintheWRMSPE</sup> measure. The RTAE measure also tries to fix the problem of WAPE when having all 0’s or close to 0’s in the whole forecast horizon. As discussed in Section 6.1.2, this is done by using a fix similar to msMAPE which has its own issues. On the other hand, with percentage based measures that scale based on in-sample values, on short intermittent series, the scale can still be 0, even when computed by aggregating several values, which is rare but possible. Specifically with the sMAE measure, it has the same problem that due to computing absolute errors, an all 0’s prediction can be selected as the best on an intermittent series. This is also the case with the ND measure. However, the NRMSE measure overcomes the problem due to squared errors. Apart from that, global scaling based measures are oftentimes good measures on intermittent series, since the global summary statistic computed for the scale is less susceptible to failures on a set of intermittent series. 

With respect to relative errors, due to using absolute errors, MRAE, MdRAE and GMRAE also have the problem with intermittent series that, constant 0’s can be selected as the best forecasts. Using squared errors _rt_<sup>2,as in RMRSE overcomes this.However,the error of</sup> the benchmark method can be very small on intermittent series. For example, if the actual value at the forecast origin was 0, the na¨ıve forecasts for the whole forecast horizon would be all 0’s, which results in an exact match at a 0 actual in the horizon of this intermittent series. This results in division by values close to 0 which makes relative errors undefined (Hyndman and Koehler, 2006). The same issue is encountered, if both the benchmark and the forecasting model produce 0 errors. The solution of winsorising errors proposed by Armstrong and Collopy (1992) in this context has the same issues as discussed for msMAPE in Section 6.1.2. Another solution proposed by Kolassa (2016) for this is to sum the benchmark errors over multiple time steps and then take the ratio. This idea follows the concept behind WAPE defined in Section 6.1.2 and is similar to the Relative Measures as discussed in Section 6.1.4. In this case, such undefined values can only occur if the benchmark error is zero for all the considered time steps, which is a very rare case. However, this too is likely with a very short forecast horizon on an intermittent series. 

Similar to the comparison between MAE and RMSE, RMSSE is better suited than MASE, with intermittent series, for the purpose of capturing spikes well. Apart from that, if all the historical observations are equal or 0 (rare but possible with a short intermittent series) the MASE and RMSSE can be infinite/undefined. 

The rate-based measures mentioned in Section 6.1.8 are designed specifically for the purpose of intermittent demand forecasting, in an inventory management context. The usual scale-dependent measures such as MSE and MAE have been criticised in this context, since they may bias the forecasts towards zero demand due to the high sparsity of the series and consequently disrupt inventory management for intermittent demand. Moreover, techniques such as Croston’s method (see, e.g., Hyndman and Athanasopoulos, 2018) which are specifically developed for intermittent series, forecast a demand rate (average expected demand in each period) as opposed to an exact demand for each time step, for the convenience of 

52 

making inventory management decisions. Therefore, rather than comparing the demand and forecast per each time step, a rate-based error has been proposed to compare the cumulative mean of the actual demand computed over time to the intermittent demand forecasts produced by Croston-type models. 

## _6.2.8. Outliers_ 

Susceptibility to outliers depends on the underlying business needs. In some applications we may be interested in capturing outliers well (e.g., in intermittent series), whereas some others may require the models to be robust against them. The choice between squared or absolute errors and the operator used for aggregating errors mostly depend on such considerations. To be robust against outliers, a summary operator other than mean (such as median or another quantile) can be used. Geometric mean is also a generally robust option for summarising errors in the presence of outliers. Using the geometric mean has been recommended by Davydenko and Fildes (2013) especially since it takes into account all values even in the tails of the distribution to compute the final summary, as opposed to the median. Moreover, anomaly detection techniques can be applied to identify and remove such outliers from series (relevant threshold values for the scale can be used), if they are unimportant (Arnott et al., 2019). 

With scale-dependent measures, a model which performs generally well can end up being the worst due to large errors at outlier series. Due to considering the square of the error, RMSE and MSE are both more susceptible to outliers than MAE and MdAE which use absolute errors instead of squared errors (Hyndman and Koehler, 2006). Similarly, measures such as RMdSE are also better with outliers due to using the median operator for summarising the errors as opposed to mean which is affected by outliers. Therefore, if the outliers are of interest and capturing them is important, using squared errors with mean operator for aggregating the errors is the better option. 

MAPE is less sensitive to errors at higher valued outlier points in the test region. On the other hand, at outliers with unexpectedly low values, the overall error gets dominated by the errors at such points. This is illustrated in Figure 20, where series _A_ and _B_ are the same except for a low valued outlier in series _A_ . The model forecasts on the two series are also exactly the same. However, because of the outlier in series _A_ , the overall MAPE of the model on series _A_ is higher than on series _B_ . MdAPE can be robust against outliers. sMAPE has the advantage that it is bounded by 200, since the denominator is never less than the numerator. This makes it robust to outliers unlike other measures which are unbounded (Chen et al., 2017). 

The problems with extreme values described above for the MAPE are possible with WAPE too. Even if a mean on the actual values over the horizon is computed for the scale, the impact from such extreme values can be large. The problem is even worse here than with MAPE, since that same scale is used for the errors of the whole horizon. Thus, the problems at a single time step in the forecast horizon, can affect the errors from the whole horizon. For example, if there exists at least one outlier with an extremely large value in the test region, the denominator becomes very large and totally diminishes the effects from all the other errors for that particular series. The opposite can happen too, where due to 

53 



Figure 20: MAPE Error Measure Issue - On a Series having a Low Valued Outlier 

very low valued outliers, even small errors from the forecasts of the series can have a large impact in the final error. Effects from such outliers can be mitigated by excluding them in the computation of the scaling factor. With respect to measures such as sMAE or sMSE, anomalous time steps/short periods of time in the series can affect the scale significantly and consequently lessen or increase the impact from such errors in the horizon unnecessarily for that particular series. However, similar to WAPE, this can be avoided by ignoring the outlier time steps from the series in the scale computation. On the other hand, when the scale is computed globally by considering all the series in the dataset, effects from such outliers in particular points of the series are mostly mitigated. 

In terms of relative errors, MdRAE and GMRAE are relatively more robust to outliers, due to the used summarisation operators. Nevertheless, when computing the geometric mean, it needs to be ensured that 0 errors for both the benchmark as well as the evaluated forecasting technique are excluded. Also, MRAE is more robust with outliers than RMRSE, due to considering absolute errors in the former. However, if using the fixed origin na¨ıve method as the benchmark for relative errors, its value in the forecast horizon can get affected by outliers in the last part of the training region of the series. This effectively results in large benchmark errors in the forecast horizon. This scenario is illustrated in Figure 21, where except for the outlier around the forecast origin in series _A_ , both series _A_ and _B_ are equivalent in values. The model in series _A_ is robust to outliers and thus, despite the outlier in series _A_ , the model produces identical forecasts for both series _A_ and _B_ . On the other hand, the OOS na¨ıve forecast on series _A_ is completely affected by this outlier. Due to this reason, the MRAE for the model on series _A_ is much smaller than in series _B_ , although the model demonstrates the same discrepancy from the actuals in the forecast horizon on both 

54 

the series. This difference of MRAE is merely due to the susceptibility of the na¨ıve forecast to the outlier and not due to any misbehaviour of the model on series _B_ . With Relative Measures too, the same factors as with relative errors hold on outlier series. In between the two scaled errors MASE and RMSSE, MASE is preferred to be robust over RMSSE on outliers. 



Figure 21: Relative Errors Issue - On a Series having an Outlier at the Forecast Origin 

Measures based on a transformation such as logarithm are good options to de-emphasise effects from errors at extremely large outlier points in the series. This is shown in Figure 22, where at point _X_ lies an outlier. 

## **7. Statistical Tests for Significance** 

While forecast evaluation measures are critical to see the relative performance of the methods and select the best ones from their rankings, they do not give information regarding the statistical significance of the differences between these methods; i.e. whether better performance of the best method is just by chance on this sample of the series or whether it is likely to dominate all the methods significantly in other samples of the data. This means that the information provided by the error metrics alone is not enough to conclude 

55 



Figure 22: Transformation based Measures Issue - On a Series having an Outlier 

that the selected best method is the only one that should be always selected, or if there are other methods that are not significantly different from the best so that they can be used interchangeably due to their other preferable properties such as simplicity, computational efficiency etc. 

There are many ways of performing statistical significance tests reported in the literature. The general principal behind all these tests is hypothesis testing, where the null hypothesis stands for non-significance of difference in the results, and the alternative hypothesis stands for their significance. The null hypothesis is then rejected based on the value of a certain test statistic. The Diebold-Mariano test (Diebold and Mariano, 2002) and the Wilcoxon rank-sum test (Mann and Whitney, 1947) are both designed for comparing only between two competing forecasts, not necessarily methods or models. However, the Diebold-Mariano test is designed specifically for time series and parametric, meaning that it has the assumption of normality of the data whereas the Wilcoxon test is a generic non-parametric test based on the ranks of the methods. Due to considering ranks of methods for each series separately, the error measures used do not necessarily have to be scale-free. The Giacomini-White test (Giacomini and White, 2006) again is based on the comparison of two forecasts, with the potential to assess the conditional predictive ability (CPA), a concept that refers to conditioning the choice of a potential future state of the economy, an important concept for marco economic forecasting of a small number of series. A continuation in this line of research is work by Li et al. (2022) that focuses on conditional superior predictive ability, in regards to a benchmark method and time series with general serial dependence. It should be noted that many of the mentioned comparison tests are per-se designed for comparing 

56 

two forecasts, and a multiple testing of more than two requires a correction for multiple hypothesis testing, such as, e.g., a Bonferroni correction. 

There are other techniques developed to perform comparison within a group of methods (more than 2) as well. Means of error distributions from different methods can be used to compare the mean performance of the methods. The F-test and the t-test are statistical tests in this respect. They both have parametric assumptions for the means of the error distributions, that they need to follow a normal distribution. Nevertheless, according to the Central Limit Theorem, for a sufficiently large random sample (of size _n ≥_ 30) from the original population, the distribution of the sample means follow an approximately normal distribution, irrespective of the distribution of the original population of errors. However, this only holds for measures such as MSE, MAE etc. and does not hold for e.g., RMSE, since the root of a normally distributed variable is following a chi-square distribution, which is close to normality but not equivalent. On the other hand, the Friedman test (Friedman, 1937, 1939, 1940) is a non-parametric statistical test that can be used to detect significance between multiple competing methods, using the ranks of the methods according to mean errors. Ranks of means are equivalent to the median of the distribution (Svetunkov, 2021). 

However, the Friedman test only gives information on the existence of the significance between methods, but does not indicate which methods are significantly different from each other. Hence, the Friedman test is usually followed by a post-hoc test, when the null hypothesis which states that “there are no significant differences between the methods”, is rejected. There are different types of post-hoc tests, for example, the Hochberg procedure (Hochberg, 1988), the Holm process (Holm, 1979), the Bonferroni-Dunn procedure (Dunn, 1961), the Nemenyi method (Nemenyi, 1963), the Multiple Comparisons with the Best (MCB) method (practically equivalent to the Nemenyi method) or the Multiple Comparisons with the Mean (ANOM) method (Halperin et al., 1955), and others. In general, the ANOM test holds less value in practice since it is more useful to find which methods are not significantly different from the best, than from some averagely performing method overall. The Nemenyi method works by defining confidence bounds, in terms of a Critical Distance (CD) around the mean ranks of the methods to identify which methods have overlapping confidence bounds and which do not. This method also has the added advantage that it allows to identify significant differences between two different groups of methods. As Demˇsar (2006) suggests, if all the comparisons are to be performed against one control method as opposed to each method against each other, procedures such as Bonferroni-Dunn and Hochberg’s are better over the Nemenyi test. Once, the quantitative results for the significance of the differences are obtained using any of the aforementioned methods, they can be visualised using CD diagrams (Demˇsar, 2006). They are illustrated differently for the different post-hoc tests. In general, in these diagrams, a horizontal axis reports the average ranks of all the methods, and groups of methods that are not significantly different from each other are connected using black bars. This is illustrated in Figure 23, an example CD diagram. 

In general, when performing significance testing, depending on the amount of data that we have, ranking can be performed either for each step in the horizon, each time series or each overall dataset. More importantly, the amount of data included heavily impacts the results of the significance tests. For example, with a very high number of series, the CD 

57 



Figure 23: An example of a CD diagram to visualise the significance of the differences between a number of competing methods. The best three methods A, B and C are not significantly different from each other. On the other hand, methods D, E and F are significantly worse than those three methods. Again, the amount of data has not been enough to check whether method E is significantly better than method D or worse than method F. 

is usually very low, producing significant results for even small differences between models. This does not indicate a problem with the procedure, rather it means that the results are more reliable, that even the slightest differences between models encountered for such a large amount of data are statistically highly significant. On the other hand, it also depends on the number and the relative performance of the set of models included in the comparison. For example, having more and more poorly performing methods in the group may tend towards making the CD larger, thus making other intermediate methods have no significant difference from the best. In essence, with respect to statistical testing for significance of differences, it is important to include a reasonable amount of data as well as a reasonable number of models with sufficient diversity to avoid spurious conclusions regarding statistical significance. 

## **8. Conclusions** 

Model evaluation, just as in any other domain, is a crucial step in forecasting. In other major fields such as regression, classification, there exist established techniques that are the standard best practices. On the contrary, in the domain of forecasting, evaluation remains a much more complex task. The numerous research that has been conducted in this space over the years has contributed to many new ideas and concepts. The general trend has been to propose new methodologies to address pitfalls associated with the previously introduced. Nevertheless, for example with the forecast evaluation measures, to the best of our knowledge, all the introduced measures thus far, can break under given certain characteristics/non-stationarities of the time series. Due to the self-supervised nature of the forecasting problem, data leakage dangers need to be especially kept in mind. Furthermore, 

58 

general ML practitioners and Data Scientists new to the field of forecasting are often not aware of these issues. The huge collection of forecast evaluation techniques that different practitioners use with various intentions (which are not explicitly stated), adds up to further confusion. All of this is a consequence of the lack of established best practices and guidelines for the different steps of the forecast evaluation process. Therefore, to support the ML community in this aspect, in this article we provide a compilation of common pitfalls and best practice guidelines related to forecast evaluation including data partitioning, calculating error measures etc. The key set of guidelines that we have developed are as follows. 

- It is always important to compare models against the right and the simplest benchmarks such as the na¨ıve and the seasonal na¨ıve. 

- Using forecast plots can be misleading; making decisions purely based on the visual appeal on forecast plots is not advisable. The benchmarks and the error measures used are more important. 

- Data leakage needs to be avoided explicitly in rolling origin evaluation and other data pre-processing tasks such as smoothing, decomposition and normalisation of the series. 

- k-fold CV is a valid and a data efficient strategy of data partitioning for forecast model validation with pure AR based setups, when the models do not underfit the data (which can be detected with a test for serial correlation in the residuals, such as the Ljung-Box test). As such, we advise this procedure especially for short series where tsCV leads to test sets that are too small. However, if the models underfit, it is advisable to improve the models first before using any CV technique. 

- If enough data are available, tsCV is the procedure of choice. Also, for models with a continuous state such as RNNs and ETS where the temporal order of the data is important, tsCV may be the only applicable validation strategy. 

- There is no single globally valid evaluation measure for all scenarios. It depends on the characteristics of the data. Table 1 provides a guide on how to select error measures to suit the data characteristics. 

- It is advisable to evaluate the same forecasts in terms of several evaluation measures as means of sanity checking, but be aware that the forecasts cannot be optimised towards all measures together, and one particular measure will need to be chosen as the main measure. 

- When using statistical testing for significance of the differences between models, balancing the diversity of the compared models and against the number of data points is important to avoid spurious statistical similarity/difference between models. 

Techniques available in the literature for capturing non-stationarities, such as moving average smoothing, STL decomposition etc. have also been highlighted in our work. While 

59 

the literature on evaluation measures is quite extensive, the exact errors (squared/absolute), summarisation operators (mean/median/geometric mean), type of scaling to use (global/perseries/per-step/, in-sample/OOS, relative/percentage) differ based on the user expectations, business utility and the characteristics of the underlying time series. Also, in real-world applications, with meaningful scales on the series, scale-dependent measures hold much value; however, the relevant scales need to be computed with respect to the underlying business utility (price/volume). 

Throughout this work, we hope to establish the knowledge and formalised guidelines related to forecast evaluation within the ML community. Due to the lack of proper knowledge in this area, ML research in the literature thus far has often either struggled to demonstrate the competitiveness of its models or arrived at spurious conclusions. It is our objective that this effort supports better and correct forecast evaluation practices within the ML community. The adoption of correct principles in this domain will certainly contribute towards developing even further superior ML based systems for forecasting. As a potential avenue for further work, it would be useful to design combination based evaluation measures for forecasting, similar to the Huber loss for model training, which is a combination of the MAE and the RMSE. These types of measures can be quite robust, combining the strengths of both measures while minimising the potential disadvantages associated with the individual measures. 

## **Acknowledgement** 

This work was done as part of the PhD degree of Hansika Hewamalage at the Faculty of IT, Monash University. This research was supported by the Australian Research Council under grant DE190100045, a Facebook Statistics for Improving Insights and Decisions research award and Monash University Graduate Research funding. 

## **References** 

- Abolghasemi, M., Esmaeilbeigi, R., 2021. State-of-the-art predictive and prescriptive analytics for ieee cis 3rd technical challenge. URL: `https://arxiv.org/abs/2112.03595` , `arXiv:2112.03595` . 

- Akaike, H., 1974. A new look at the statistical model identification. IEEE transactions on automatic control 19, 716–723. 

- Armstrong, J., 2001. Evaluating forecasting methods, in: Armstrong, J.S. (Ed.), Principles of Forecasting: A Handbook for Researchers and Practitioners. Kluwer Academic Publishers: Norwell, MA. 

- Armstrong, J., Adya, M., Collopy, F., 2001. Rule-based forecasting: Using judgment in time-series extrapolation, in: Armstrong, J.S. (Ed.), Principles of Forecasting: A Handbook for Researchers and Practitioners. Kluwer Academic Publishers: Norwell, MA. 

- Armstrong, J., Collopy, F., 1992. Error measures for generalizing about forecasting methods: Empirical comparisons. International Journal of Forecasting 8, 69–80. 

- Armstrong, J.S., Grohman, M.C., 1972. A comparative study of methods for long-range market forecasting. Management Science 19, 211–221. doi: `10.1287/mnsc.19.2.211` . 

- Arnott, R., Harvey, C.R., Markowitz, H., 2019. A backtesting protocol in the era of machine learning. The Journal of Financial Data Science doi: `10.3905/jfds.2019.1.064` . 

- Bagnall, A., Lines, J., Bostrom, A., Large, J., Keogh, E., 2016. The great time series classification bake off: a review and experimental evaluation of recent algorithmic advances. Data Mining and Knowledge Discovery 31, 606–660. doi: `10.1007/s10618-016-0483-9` . 

60 

Balestriero, R., Pesenti, J., LeCun, Y., 2021. Learning in high dimension always amounts to extrapolation. arXiv preprint arXiv:2110.09485 . 

- Bell, F., Smyl, S., 2018. Forecasting at uber: An introduction. URL: `https://eng.uber.com/forecastingintroduction/` . 

- Belt, T., 2017. When is forecast accuracy important in the retail industry? Effect of key product parameters. Master’s thesis. Aalto University. School of Science. URL: `http://urn.fi/URN:NBN:fi:aalto201704133520` . 

- Bergmeir, C., 2021. Ieee-cis technical challenge on predict+optimize for renewable energy scheduling. URL: `https://dx.doi.org/10.21227/1x9c-0161` , doi: `10.21227/1x9c-0161` . 

- Bergmeir, C., Ben´ıtez, J.M., 2012. On the use of cross-validation for time series predictor evaluation. Information Sciences 191, 192–213. Data Mining for Software Trustworthiness. 

- Bergmeir, C., Hyndman, R.J., Koo, B., 2018. A note on the validity of cross-validation for evaluating autoregressive time series prediction. Computational Statistics & Data Analysis 120, 70–83. 

- Berm´udez, J.D., Segura, J.V., Vercher, E., 2006. A decision support system methodology for forecasting of time series based on soft computing. Comput. Stat. Data Anal. 51, 177–191. 

- Bojer, C.S., Meldgaard, J.P., 2020. Kaggle forecasting competitions: An overlooked learning opportunity. International Journal of Forecasting . 

- Boylan, J., Syntetos, A., 2006. Accuracy and accuracy implication metrics for intermittent demand. Foresight: The International Journal of Applied Forecasting , 39–42. 

- Brownlee, J., 2020. Data preparation for machine learning: data cleaning, feature selection, and data transforms in Python. Machine Learning Mastery. 

- Burman, P., Chow, E., Nolan, D., 1994. A cross-validatory method for dependent data. Biometrika 81, 351–358. 

- Cerqueira, V., Torgo, L., Mozetiˇc, I., 2020. Evaluating time series forecasting models: an empirical study on performance estimation methods. Mach. Learn. 109, 1997–2028. 

- Chen, C., Twycross, J., Garibaldi, J.M., 2017. A new accuracy measure based on bounded relative error for time series forecasting. PLOS ONE 12, e0174202. doi: `10.1371/journal.pone.0174202` . 

- Cox, D., Miller, H., 1965. The Theory of Stochastic Processes. 

- Davydenko, A., Fildes, R., 2013. Measuring forecasting accuracy: The case of judgmental adjustments to SKU-level demand forecasts. Int. J. Forecast. 29, 510–522. 

- Demˇsar, J., 2006. Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research 7, 1–30. 

- Diebold, F.X., Mariano, R.S., 2002. Comparing predictive accuracy. Journal of Business & Economic Statistics 20, 134–144. doi: `10.1198/073500102753410444` . 

- Dunn, O.J., 1961. Multiple comparisons among means. Journal of the American Statistical Association 56, 52–64. doi: `10.1080/01621459.1961.10482090` . 

- Fawaz, H.I., Forestier, G., Weber, J., Idoumghar, L., Muller, P.A., 2019. Deep learning for time series classification: a review. Data Mining and Knowledge Discovery 33, 917–963. doi: `10.1007/s10618-01900619-1` . 

- Fitzgibbon, L.J., Dowe, D.L., Vahid, F., 2004. Minimum message length autoregressive model order selection, in: International Conference on Intelligent Sensing and Information Processing, 2004. Proceedings of, IEEE. pp. 439–444. 

- Friedman, M., 1937. The use of ranks to avoid the assumption of normality implicit in the analysis of variance. Journal of the American Statistical Association 32, 675–701. doi: `10.1080/01621459.1937.10503522` . 

- Friedman, M., 1939. A correction: The use of ranks to avoid the assumption of normality implicit in the analysis of variance. Journal of the American Statistical Association 34, 109–109. URL: `http: //www.jstor.org/stable/2279169` . 

- Friedman, M., 1940. A Comparison of Alternative Tests of Significance for the Problem of _m_ Rankings. The Annals of Mathematical Statistics 11, 86 – 92. doi: `10.1214/aoms/1177731944` . 

- Fry, C., Lichtendahl, C., 2020. Google practitioner session, 40th international symposium on forecasting. URL: `https://www.youtube.com/watch?v=FoUX-muLlB4&t=3007s` . 

61 

Gama, J., Sebastiao, R., Rodrigues, P.P., 2013. On evaluating stream learning algorithms. Machine learning 90, 317–346. 

Gama, J.a., Sebasti˜ao, R., Rodrigues, P.P., 2009. Issues in evaluation of stream learning algorithms, in: Proceedings of the 15th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, Association for Computing Machinery, New York, NY, USA. p. 329–338. doi: `10.1145/1557019. 1557060` . 

Ghomeshi, H., Gaber, M.M., Kovalchuk, Y., 2019. EACD: evolutionary adaptation to concept drifts in data streams. Data Mining and Knowledge Discovery 33, 663–694. doi: `10.1007/s10618-019-00614-6` . Giacomini, R., White, H., 2006. Tests of conditional predictive ability. Econometrica 74, 1545–1578. Goodwin, P., Lawton, R., 1999. On the asymmetry of the symmetric mape. International Journal of 

Forecasting 15, 405–408. 

Halperin, M., Greenhouse, S.W., Cornfield, J., Zalokar, J., 1955. Tables of percentage points for the studentized maximum absolute deviate in normal samples. Journal of the American Statistical Association 50, 185–195. 

H¨am¨al¨ainen, W., Webb, G.I., . A tutorial on statistically sound pattern discovery. Data Mining and 

Knowledge Discovery 33, 325–377. doi: `10.1007/s10618-018-0590-x` . 

Hannun, A., Guo, C., van der Maaten, L., 2021. Measuring data leakage in machine-learning models with fisher information, in: de Campos, C., Maathuis, M.H. (Eds.), Proceedings of the Thirty-Seventh Conference on Uncertainty in Artificial Intelligence, PMLR. pp. 760–770. 

Hastie, T., Tibshirani, R., Friedman, J., 2009. The Elements of Statistical Learning: Data Mining, Inference, and Prediction. Springer, New York, NY. 

Hewamalage, H., Bergmeir, C., Bandara, K., 2021. Recurrent neural networks for time series forecasting: Current status and future directions. International Journal of Forecasting 37, 388–427. 

Hidalgo, J.I.G., Maciel, B.I.F., Barros, R.S.M., 2019. Experimenting with prequential variations for data stream learning evaluation. Computational Intelligence 35, 670–692. doi: `https://doi.org/10.1111/ coin.12208` . 

Hochberg, Y., 1988. A sharper bonferroni procedure for multiple tests of significance. Biometrika 75, 800–802. Holm, S., 1979. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6, 65–70. 

- Hyndman, R., Kang, Y., Talagala, T., Wang, E., Yang, Y., 2019. tsfeatures: Time Series Feature Extraction. URL: `https://pkg.robjhyndman.com/tsfeatures/` . R package version 1.0.0. 

- Hyndman, R.J., Athanasopoulos, G., 2018. Forecasting: Principles and Practice. second ed., OTexts. URL: `https://otexts.com/fpp2/` . 

- Hyndman, R.J., Koehler, A.B., 2006. Another look at measures of forecast accuracy. International Journal of Forecasting 22, 679 – 688. 

Ikonomovska, E., Gama, J., Dˇzeroski, S., 2010. Learning model trees from evolving data streams. Data Mining and Knowledge Discovery 23, 128–168. doi: `10.1007/s10618-010-0201-y` . 

Inoue, A., Kilian, L., 2006. On the selection of forecasting models. Journal of Econometrics 130, 273–306. Januschowski, T., Gasthaus, J., Wang, Y., Salinas, D., Flunkert, V., Bohlke-Schneider, M., Callot, L., 2020. Criteria for classifying forecasting methods. International Journal of Forecasting 36, 167 – 177. M4 Competition. 

- Kaufman, S., Rosset, S., Perlich, C., Stitelman, O., 2012. Leakage in data mining: Formulation, detection, and avoidance. ACM transactions on knowledge discovery from data 6, 1–21. 

- Kim, S., Kim, H., 2016. A new metric of absolute percentage error for intermittent demand forecasts. International Journal of Forecasting 32, 669–679. 

- Kiran Bhowmick, M.N., 2020. Pre cdaci: Prequential learning based concept drift detection and adaptation for classification of imbalanced data streams. International Journal of Advanced Science and Technology 29, 14275 – 14283. 

- Kolassa, S., 2016. Evaluating predictive count data distributions in retail sales forecasting. International Journal of Forecasting 32, 788 – 803. 

62 

- Kolassa, S., 2017. What are the shortcomings of the mean absolute percentage error (mape)? URL: `https://stats.stackexchange.com/questions/299712/what-are-the-shortcomings-of-themean-absolute-percentage-error-mape/299713#299713` . 

- Kolassa, S., 2020. Why the “best” point forecast depends on the error or accuracy measure. International Journal of Forecasting 36, 208–211. M4 Competition. 

- Kourentzes, N., 2014. On intermittent demand model optimisation and selection. Int. J. Prod. Econ. 156, 180–190. 

- Koutsandreas, D., Spiliotis, E., Petropoulos, F., Assimakopoulos, V., 2021. asures. J. Oper. Res. Soc. , 1–18. 

- Kunst, R., 2016. Visualization of distance measures implied by forecast evaluation criteria. URL: `https: //forecasters.org/wp-content/uploads/gravity_forms/7-621289a708af3e7af65a7cd487aee6eb/ 2016/07/Kunst_Robert_ISF2016.pdf` . international Symposium on Forecasting 2016. 

- Lai, G., Chang, W.C., Yang, Y., Liu, H., 2018. Modeling long- and short-term temporal patterns with deep neural networks, in: The 41st International ACM SIGIR Conference on Research &; Development in Information Retrieval, Association for Computing Machinery, New York, NY, USA. p. 95–104. doi: `10. 1145/3209978.3210006` . 

- Li, J., Liao, Z., Quaedvlieg, R., 2022. Conditional superior predictive ability. The Review of Economic Studies 89, 843–875. 

- Ljung, G.M., Box, G.E.P., 1978. On a measure of lack of fit in time series models. Biometrika 65, 297–303. Lubba, C.H., Sethi, S.S., Knaute, P., Schultz, S.R., Fulcher, B.D., Jones, N.S., 2019. catch22: CAnonical time-series CHaracteristics. Data Mining and Knowledge Discovery 33, 1821–1852. doi: `10.1007/s10618019-00647-x` . 

- Makridakis, S., 1993. Accuracy measures: theoretical and practical concerns. International Journal of Forecasting 9, 527–529. 

- Makridakis, S., Hibon, M., 2000. The m3-competition: results, conclusions and implications. International Journal of Forecasting 16, 451–476. The M3- Competition. 

- Makridakis, S., Spiliotis, E., Assimakopoulos, V., 2020a. The m5 accuracy competition: Results, findings and conclusions. URL: `https://www.researchgate.net/publication/344487258_The_M5_Accuracy_ competition_Results_findings_and_conclusions` . 

- Makridakis, S., Spiliotis, E., Assimakopoulos, V., 2020b. The M4 Competition: 100,000 time series and 61 forecasting methods. International Journal of Forecasting 36, 54–74. 

- Mann, H.B., Whitney, D.R., 1947. On a Test of Whether one of Two Random Variables is Stochastically Larger than the Other. The Annals of Mathematical Statistics 18, 50 – 60. doi: `10.1214/aoms/ 1177730491` . 

- Mulinka, P., Wassermann, S., Mar´ın, G., Casas, P., 2018. Remember the Good, Forget the Bad, do it Fast - Continuous Learning over Streaming Data, in: Continual Learning Workshop at NeurIPS 2018, Montr´eal, Canada. 

- Nemenyi, P., 1963. Distribution-free multiple comparisons. Ph.D. thesis. Princeton University. 

- Petropoulos, F., Apiletti, D., Assimakopoulos, V., Babai, M.Z., Barrow, D.K., Bergmeir, C., Bessa, R.J., Boylan, J.E., Browell, J., Carnevale, C., Castle, J.L., Cirillo, P., Clements, M.P., Cordeiro, C., Oliveira, F.L.C., Baets, S.D., Dokumentov, A., Fiszeder, P., Franses, P.H., Gilliland, M., G¨on¨ul, M.S., Goodwin, P., Grossi, L., Grushka-Cockayne, Y., Guidolin, M., Guidolin, M., Gunter, U., Guo, X., Guseo, R., Harvey, N., Hendry, D.F., Hollyman, R., Januschowski, T., Jeon, J., Jose, V.R.R., Kang, Y., Koehler, A.B., Kolassa, S., Kourentzes, N., Leva, S., Li, F., Litsiou, K., Makridakis, S., Martinez, A.B., Meeran, S., Modis, T., Nikolopoulos, K., Onkal, D., Paccagnini, A., Panapakidis, I., Pav´ıa, J.M., Pedio, M., Pedregal,<sup>¨</sup> D.J., Pinson, P., Ramos, P., Rapach, D.E., Reade, J.J., Rostami-Tabar, B., Rubaszek, M., Sermpinis, G., Shang, H.L., Spiliotis, E., Syntetos, A.A., Talagala, P.D., Talagala, T.S., Tashman, L., Thomakos, D., Thorarinsdottir, T., Todini, E., Arenas, J.R.T., Wang, X., Winkler, R.L., Yusupova, A., Ziel, F., 2020. Forecasting: theory and practice. URL: `https://arxiv.org/abs/2012.03854` , `arXiv:2012.03854` . 

- Petropoulos, F., Kourentzes, N., 2015. Forecast combinations for intermittent demand. Journal of the Operational Research Society 66, 914–924. 

63 

- Petropoulos, F., Makridakis, S., Assimakopoulos, V., Nikolopoulos, K., 2014. ‘horses for courses’ in demand forecasting. European Journal of Operational Research 237, 152–163. 

- Racine, J., 2000. Consistent cross-validatory model-selection for dependent data: hv-block cross-validation. Journal of Econometrics 99, 39–61. 

- Salinas, D., Flunkert, V., Gasthaus, J., Januschowski, T., 2020. Deepar: Probabilistic forecasting with autoregressive recurrent networks. International Journal of Forecasting 36, 1181 – 1191. 

- Salles, R., Belloze, K., Porto, F., Gonzalez, P.H., Ogasawara, E., 2019. Nonstationary time series transformation methods: An experimental review. Knowledge-Based Systems 164, 274–291. 

- Spiliotis, E., Makridakis, S., Kaltsounis, A., Assimakopoulos, V., 2021. Product sales probabilistic forecasting: An empirical evaluation using the m5 competition data. International Journal of Production Economics 240, 108237. 

- Stone, M., 1974. Cross-validatory choice and assessment of statistical predictions. Journal of the Royal Statistical Society. Series B (Methodological) 36, 111–147. 

- Suilin, A., 2017. kaggle-web-traffic. URL: `https://github.com/Arturus/kaggle-web-traffic/` . accessed: 2018-11-19. 

- Svetunkov, I., 2021. Forecasting and analytics with adam. OpenForecast. URL: `https://openforecast. org/adam/` . (version: [current date]). 

- Syntetos, A.A., Boylan, J.E., 2005. The accuracy of intermittent demand estimates. International Journal of Forecasting 21, 303 – 314. 

- Syntetos, A.A., Boylan, J.E., 2006. On the stock control performance of intermittent demand estimators. International Journal of Production Economics 103, 36 – 47. 

- Tashman, L.J., 2000. Out-of-sample tests of forecasting accuracy: an analysis and review. International Journal of Forecasting 16, 437 – 450. The M3- Competition. 

- Tofallis, C., 2015. A better measure of relative prediction accuracy for model selection and model estimation. J. Oper. Res. Soc. 66, 1352–1362. 

- Webb, G.I., Hyde, R., Cao, H., Nguyen, H.L., Petitjean, F., 2016. Characterizing concept drift. Data Min. Knowl. Discov. 30, 964–994. doi: `10.1007/s10618-015-0448-4` . 

- Wong, L., 2019. Error metrics in time series forecasting. URL: `https://isf.forecasters.org/wpcontent/uploads/gravity_forms/2-dd30f7ae09136fa695c552259bdb3f99/2019/07/ISF_2019_ slides.pdf` . international Symposium on Forecasting 2019. 

64 

