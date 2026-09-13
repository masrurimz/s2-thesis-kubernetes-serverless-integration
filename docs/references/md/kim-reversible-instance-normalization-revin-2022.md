---
# --- bibliographic record ---
entry_type: inproceedings
title: "Reversible Instance Normalization for Accurate Time-Series Forecasting against Distribution Shift"
authors:
  - "Taesung Kim"
  - "Jinhee Kim"
  - "Yunwon Tae"
  - "Cheonbok Park"
  - "Jang-Ho Choi"
  - "Jaegul Choo"
year: 2022
venue: "International Conference on Learning Representations (ICLR)"
volume: ""
issue: ""
pages: ""
publisher: "OpenReview.net"
doi: ""
arxiv: ""
url: "https://openreview.net/forum?id=cGDAkQo1C0p"

# --- archive record ---
source_pdf: kim-reversible-instance-normalization-revin-2022.pdf
source_sha256: f535747f34dc8f627e06d94cdbb603dba8436fd86331582581b7ad4f11facbe3
pdf_pages: 25
converted: 2026-09-13
record_source: manual
review: "no DOI or arXiv ID; OpenReview API and DBLP both refuse headless calls, so the record was read from the PDF's title page"
key_insight: "Normalises each input window by its own mean and standard deviation and restores those statistics on the output, so a level shift in the input cannot bias the prediction. The fix for the frozen-scaler bias: the deployed GRU predicts from a live signal whose level sits below its training level, and a scaler fitted once on the training set carries that offset into every forecast."
first_page: "Published as a conference paper at ICLR 2022 REVERSIBLE INSTANCE NORMALIZATION FOR ACCURATE TIME-SERIES FORECASTING AGAINST DISTRIBUTION SHIFT Taesung Kim∗ KAIST AI zkm1989 @kaist.ac.kr Jinhee Kim* KA"
---
Published as a conference paper at ICLR 2022 

REVERSIBLE INSTANCE NORMALIZATION FOR ACCURATE TIME-SERIES FORECASTING AGAINST DISTRIBUTION SHIFT 

**Taesung Kim**<sup>_∗_</sup> **Jinhee Kim**<sup>*****</sup> KAIST AI KAIST AI zkm1989 seharanul17 @kaist.ac.kr @kaist.ac.kr 

**Yunwon Tae** VUNO yunwon.tae @vuno.co 

**Cheonbok Park Jang-Ho Choi** NAVER Corp. ETRI cbok.park janghochoi @navercorp.com @etri.re.kr 

**Jaegul Choo** KAIST AI jchoo @kaist.ac.kr 



<!-- Start of picture text -->
(a)<br>(b)<br>day<br><!-- End of picture text -->



Figure 1: Multivariate time-series forecasting results comparing our method with the state-of-the-art baselines, i.e., Informer (Zhou et al., 2021), N-BEATS (Oreshkin et al., 2020), and SCINet (Liu et al., 2021). The analysis is conducted on electricity consuming load (ECL) dataset, with a prediction length of seven days. The predictions of the baselines are inaccurately (a) shifted and (b) scaled. When adopted to the baselines, our method significantly improves their forecasting performance and better aligns the distribution of the prediction results with the groundtruth values. 

# ABSTRACT 

Statistical properties such as mean and variance often change over time in time series, i.e., time-series data suffer from a distribution shift problem. This change in temporal distribution is one of the main challenges that prevent accurate timeseries forecasting. To address this issue, we propose a simple yet effective normalization method called reversible instance normalization (RevIN), a generallyapplicable normalization-and-denormalization method with learnable affine transformation. The proposed method is symmetrically structured to remove and restore the statistical information of a time-series instance, leading to significant performance improvements in time-series forecasting, as shown in Fig. 1. We demonstrate the effectiveness of RevIN via extensive quantitative and qualitative analyses on various real-world datasets, addressing the distribution shift problem. 

> _∗_ Both authors contributed equally. The order of the first authors was determined by coin flip. 

1 

Published as a conference paper at ICLR 2022 

# 1 INTRODUCTION 

Time-series forecasting plays a significant role in addressing various daily problems, including health care, economics, and traffic data analyses (Kim et al., 2021a; Ahmadi et al., 2019; Park et al., 2020). Recently, time-series forecasting models have achieved outstanding performance on these problems, overcoming several challenges, such as long-term forecasting (Zhou et al., 2021; Liu et al., 2021) and missing value imputation (Zhang et al., 2021; Kim et al., 2021b). However, the time-series forecasting models often suffer badly from a unique characteristic in time-series data: their statistical properties, e.g., mean and variance, can change over time. This is widely known as the distribution shift problem, and it can yield discrepancies between the distributions of the training and test data of the forecasting models. In time-series forecasting tasks, the training and test data are usually divided from the original data based on a specific point in time. Accordingly, they often hardly overlap, which is a common reason for model performance degradation. Furthermore, the input sequences to the model can have different underlying distributions as well. We can assume that the discrepancy between different input sequences can significantly degrade the model performance. 

Under this assumption, if we remove non-stationary information from the input sequences, specifically, the mean and standard deviation of the instances, the discrepancy in the data distributions will be reduced, thereby improving model performance. However, applying such normalization to the model input can cause another problem since it can prevent the model from capturing the original data distribution. It removes non-stationary information that can be important to predict future values in the forecasting task. The model would need to reconstruct the original distribution only using the normalized input, which degrades its forecasting performance due to the inherent limitation. Thus, if we explicitly return the information removed by input normalization back to the model, the model will not have to rebuild the original distribution by itself while keeping the advantage of normalizing the input. To accomplish this, we propose to reverse the normalization applied to the input data in the output layer, i.e., to denormalize the model output using the normalization statistics. 

Inspired by this, we propose a simple yet effective normalization-and-denormalization method, **reversible instance normalization (RevIN)** , which first normalizes the input sequences and then denormalizes the model output sequences to solve the time-series forecasting problems against distribution shift. RevIN is symmetrically structured to return the original distribution information to the model output by scaling and shifting the output in the denormalization layer in an amount equivalent to the shifting and scaling of the input data in the normalization layer. To verify the effectiveness of RevIN, we conduct extensive quantitative evaluations using several state-of-the-art time-series forecasting methods as the baselines: Informer (Zhou et al., 2021), N-BEATS (Oreshkin et al., 2020), and SCINet (Liu et al., 2021). We also provide an in-depth analysis of the behavior of the proposed approach, including verification of the assumptions on reversible instance normalization. 

RevIN is a flexible, end-to-end trainable layer that can be applied to any arbitrarily chosen layers, effectively suppressing non-stationary information (mean and variance of the instance) in one layer and restoring it in another layer at a virtually symmetric position, e.g., input and output layers. Despite its remarkable performance, there has been no work on generalizing and expanding instancewise normalization-and-denormalization as a flexibly applicable, trainable layer in the time-series domain. Recently, deep learning-based time-series forecasting approaches, such as Informer (Zhou et al., 2021) and N-BEATS (Oreshkin et al., 2020), have shown outstanding performance in timeseries forecasting. However, they have overlooked the importance of normalization, merely using simple global preprocessing of the model input without further exploration and expecting their endto-end deep learning model to replace the role. Despite the simplicity of our method, there have been no cases of using such techniques in modern deep-learning-based time-series forecasting approaches (Zhou et al., 2021; Liu et al., 2021; Oreshkin et al., 2020). In this sense, we introduce the importance of an appropriate normalization method for deep-learning-based time-series approaches. We propose a carefully designed, deep-learning-friendly module for time-series forecasting by combining the method with the learnable affine transformation, which has been widely accepted in recent deep-learning-based normalization work (Ulyanov et al., 2016). 

In summary, our contributions are as follows: 

- We propose a simple yet effective normalization-and-denormalization method for timeseries, called RevIN, which is symmetrically structured to remove and restore the statisti- 

2 

Published as a conference paper at ICLR 2022 

cal information of a time-series instance. The proposed method is generally applicable to arbitrary deep neural networks with negligible cost. 

- By adding RevIN to the baseline, we achieve state-of-the-art performance on seven largescale real-world datasets by a significant margin. 

- We conduct extensive evaluations of RevIN using quantitative analysis and qualitative visualizations to verify its effectiveness, addressing the distribution shift problem. 

# 2 RELATED WORK 

**Time-series forecasting.** Time-series forecasting methods are mainly categorized into three distinct approaches: (1) statistical methods, (2) hybrid methods, and (3) deep learning-based methods. Statistical models are theoretically well guaranteed and have several advantages, including interpretability. As an example of the statistical models, exponential smoothing forecasting (Holt, 2004; Winters, 1960) is a well-established benchmark for predicting future values. To further boost performance, recent work proposed a hybrid model (Smyl, 2020) that incorporates a deep learning module with a statistical model. It achieved better performance than statistical methods in the M4 timeseries forecasting competition. The deep learning-based method basically follows the sequenceto-sequence framework to model the time-series forecasting. Initially, deep learning-based models utilized variations of recurrent neural networks (RNNs). However, to overcome the limitation of the limited receptive field, several studies utilized advanced techniques, such as the dilatation and attention module. For instance, SCINet (Liu et al., 2021) and Informer (Zhou et al., 2021) modified the sequence-to-sequence-based model to improve performance for long sequences. However, most previous deep learning-based models are hard to interpret compared to statistical models. Thus, inspired by statistical models, N-BEATS (Oreshkin et al., 2020) designed an interpretable layer for time-series forecasting by encouraging the model to learn trend, seasonality explicitly, and residual components. This model shows superior performance on the M4 competition dataset. 

**Distribution shift.** Although there are various models for time-series forecasting, they often suffer from non-stationary time-series, where the data distribution changes over time. Domain adaptation (Tzeng et al., 2017; Ganin et al., 2016; Wang et al., 2018) and domain generalization (Wang et al., 2021; Li et al., 2018; Muandet et al., 2013) are common ways to alleviate the distribution shift. A domain adaptation algorithm attempts to reduce the distribution gap between source and target domains. A domain generalization algorithm only relies on the source domain and hopes to generalize on the target domain. Both domain adaptation and generalization have a common objective, which bridges the gap between source and target distributions. However, defining a domain is not straightforward in non-stationary time series since the data distribution shifts over time. Recently, Du et al. (Du et al., 2021) proposed Adaptive RNNs to handle the distribution shift problems of non-stationary time-series data. It first characterizes the distribution information by splitting the training data into periods. Then, it matches the distributions of the discovered periods to generalize the model. However, unlike Adaptive RNNs, which is costly, RevIN is simple yet effective and model-agnostic. The method can be easily adopted to any deep neural network. 

# 3 PROPOSED METHOD 

This section proposes reversible instance normalization to alleviate the distribution shift problem in time-series, which is known to cause a substantial discrepancy between the training and test data distributions. Section 3.1 describes the proposed method in detail, and Section 3.2 discusses how our approach mitigates the distribution discrepancy in time-series data. 

## 3.1 REVERSIBLE INSTANCE NORMALIZATION 

Given a set of input _X_ = _{x_<sup>(</sup><sup>_i_)</sup> _}_<sup>_N_</sup> _i_ =1<sup>and the corresponding target</sup><sup>_Y_=</sup><sup>_{y_(</sup><sup>_i_)</sup><sup>_}N_</sup> _i_ =1<sup>, we consider a mul-</sup> tivariate time-series forecasting task in discrete time, where _N_ denotes the number of sequences. Let _K, Tx,_ and _Ty_ denote the number of variables, the input sequence length, and the model prediction length, respectively. Given an input sequence _x_<sup>(</sup><sup>_i_)</sup> _∈_ R<sup>_K×Tx_</sup> , we aim to solve the time-series forecasting problem, which is to predict the subsequent values _y_<sup>(</sup><sup>_i_)</sup> _∈_ R<sup>_K×Ty_</sup> . In RevIN, the input 

3 

Published as a conference paper at ICLR 2022 



<!-- Start of picture text -->
(b-1) (b-4)<br>Source distribution Target distribution<br>0 0<br>0 0<br>0 0<br>(a-1) (a-3) Non-stationary information (a-2)<br>Instance  RevIN Denormalization<br>normalization RevIN<br>(b-2) 𝝁𝝁, 𝝈𝝈, 𝜷𝜷, 𝜸𝜸 (b-3)<br>Source distribution Target distribution<br>0 0<br>0 𝜃𝜃 0<br>0 0<br><!-- End of picture text -->

Figure 2: **Overview of the proposed method.** We illustrate an example of a univariate case, where _x_<sup>(</sup><sup>_i_)</sup> _∈_ R<sup>1</sup><sup>_×Tx_</sup> ; the input data _x_<sup>(</sup><sup>_i_)</sup> is actually multivariate (See Section 3.1). In RevIN, the (a-1) instance normalization and (a-2) denormalization are symmetrically structured to remove (a-3) nonstationary information from one layer and restore it on the other layer. Here, RevIN is applied to the input and output layers. The (a-3) non-stationary information includes statistical properties from the input data: mean _µ_ , variance _σ_<sup>2</sup> , and learnable affine parameters _γ, β_ . The normalization layer transforms the (b-1) original data distribution into a (b-2) mean-centered distribution, where the distribution discrepancy between different instances is reduced. Using _x_ ˆ, the model predicts the future values _y_ ˜ following the (b-3) distribution where non-stationary information is eliminated. To restore it (b-4), RevIN reverses the instance normalization in the output layer. 

sequence length _Tx_ and the prediction length _Ty_ can be different since the observations are normalized and denormalized across the temporal dimension, as will be explained below. Our proposed method, RevIN, consists of symmetrically structured normalization-and-denormalization layers, as illustrated in Fig. 2. First, we normalize the input data _x_<sup>(</sup><sup>_i_)</sup> using its instance-specific mean and standard deviation, which is widely accepted as instance normalization (Ulyanov et al., 2016). The mean and standard deviation are computed for every instance _x_<sup>(</sup> _k_<sup>_i_</sup> _·_<sup>)</sup><sup>_∈_R</sup><sup>_Tx_of the input data (Fig. 2(a-3)) as</sup> 



Using these statistics, we normalize the input data _x_<sup>(</sup><sup>_i_)</sup> (Fig. 2(a-1)) as 



where _γ, β ∈_ R<sup>_K_</sup> are learnable affine parameter vectors. The normalized sequences can have a more consistent mean and variance, where the non-stationary information is reduced. As a result, the normalization layer allows the model to accurately predict the local dynamics within the sequence while receiving inputs of consistent distributions in terms of the mean and variance. 

The model then receives the transformed data _x_ ˆ<sup>(</sup><sup>_i_)</sup> as input and forecasts their future values. However, the input data have different statistics than the original distribution, and by observing only the normalized input _x_ ˆ<sup>(</sup><sup>_i_)</sup> , it is difficult to capture the original distribution of the input _x_<sup>(</sup><sup>_i_)</sup> . Thus, to make this easier for the model, we explicitly return the non-stationary properties removed from the input data to the model output by reversing the normalization step at a symmetric position, the output layer. A denormalization step can return the model output to the original time-series value as well (Ogasawara et al., 2010). Accordingly, we denormalize the model output _y_ ˜<sup>(</sup><sup>_i_)</sup> by applying the 

4 

Published as a conference paper at ICLR 2022 



<!-- Start of picture text -->
(a) original input → (b) RevIN-normalized  (c) model output → (d) RevIN-denormalized<br>ETTh1<br>ETTm1<br>ECL<br>Density<br>Density<br>Density<br><!-- End of picture text -->

Figure 3: **Effect of RevIN on distribution discrepancy between training and test data.** From left to right columns, we compare the training and test data distributions of a variable on each step of the sequential process in RevIN: (a) the original input _x_ , (b) the input _x_ ˆ normalized by RevIN, (c) the model prediction output _y_ ˜, and (d) the output _y_ ˆ denormalized by RevIN, the final prediction. The analysis is conducted on the ETT and ECL datasets using SCINet (Liu et al., 2021) as the baseline. 

reciprocal of the normalization in Eq. 2 (Fig. 2(a-3)) as 



The same statistics used in the normalization step in Eq. 2 are used for the scaling and shifting. Now, _y_ ˆ<sup>(</sup><sup>_i_)</sup> is the final prediction of the model instead of _y_ ˜<sup>(</sup><sup>_i_)</sup> . 

Simply added to virtually symmetric positions in a network, RevIN can effectively alleviate distribution discrepancy in time-series data, as a generally-applicable trainable normalization layer to arbitrary deep neural networks. Indeed, the proposed method is a flexible, end-to-end trainable layer that can be applied to any arbitrarily chosen layers, even to several layers. We verify its effectiveness as a flexible layer by adding it to the intermediate layers in the model in Table 7 in Appendix A.4. Nevertheless, RevIN is most effective when applied to virtually symmetric layers of encoder-decoder structure. In a typical time-series forecasting model, the boundary between the encoder and the decoder is often unclear. Thus, we apply RevIN to the input and output layers of a model as they can be interpreted as an encoder-decoder structure, generating subsequent values, given input data. 

## 3.2 EFFECT OF REVERSIBLE INSTANCE NORMALIZATION ON DISTRIBUTION SHIFT 

This section verifies that RevIN can alleviate the distribution discrepancy problem by removing non-stationary information in the input layer and then restoring it in the output layer. We analyze the distributions of the training and test data at each step of the proposed approach, as shown in Fig. 3. 

When comparing the distribution of training and test data in each example (Fig. 3(a-b)), we can observe that RevIN significantly reduces their discrepancy. To be specific, in the original input (Fig. 3(a)), the training and test data distributions hardly overlap (especially ETTm1), which is caused by the distribution shift problem. Also, each data distribution has multiple peaks (especially the test data of ETTh1 and ECL), implying that sequences in the data might have severe discrepancies in their distributions. However, in the proposed approach, the normalization step transforms each data distribution into mean-centered distributions (Fig. 3(b)). This result supports that the original multimodal distributions (Fig. 3(a)) are caused by discrepancies in distributions between different sequences in the data. Even more, the proposed approach makes training and test data distributions overlapped. This verifies that the normalization step of RevIN can alleviate the distribution shift problem, reducing the distribution discrepancy between training and test data. 

5 

Published as a conference paper at ICLR 2022 

Taking the normalized data as the input, the model can retain aligned training and test data distributions in the prediction output (Fig. 3(c)). As expected, these are then returned back to the original distribution by the denormalization step of RevIN (Fig. 3(d)). Without denormalization, the model needs to reconstruct the values that follow the original distributions (Fig. 3(d)) using only the normalized input that follows the transformed distributions where non-stationary information is removed (Fig. 3(b)). Additionally, we hypothesize that the distribution discrepancy will be reduced in the intermediate layers of the model as well, when RevIN is applied at the input and output layers only, which will be discussed in Section 4.2.3. As a result, this RevIN procedure can be considered to first make problems easier, and then restore them back to the original state, rather than directly solving the challenging problem where the distribution shift problem exists. 

# 4 EXPERIMENTS 

This section describes the experimental setup and provides extensive experimental results of RevIN. 

## 4.1 EXPERIMENTAL SETUP 

**Datasets.** We evaluate our methods mainly on four large-scale real-world time-series datasets. Additionally, we provide experimental results on three more datasets, including the air quality and Nasdaq datasets taken from the UCI repository and M4 competition dataset (Makridakis et al., 2020) in Appendix A.1. **(i) Electricity transformer temperature (ETT)**<sup>1</sup> data consists of seven features, including power load features and oil temperature. It is collected from two different regions in China for two years. Following the same protocol as Informer (Zhou et al., 2021), we split the data into three datasets: ETTh1, ETTh2, and ETTm1. The ETTh1 and ETTh2 datasets are hourly data obtained from different regions. The ETTm1 dataset has a value every 15 minutes. For each dataset, we split the first 12 months, the middle four months, and the last four months as training, validation, and test data, respectively. **(ii) Electricity Consuming Load (ECL)**<sup>2</sup> data contains the electricity consumption (kWh) collected from 321 clients. Following the prior work (Zhou et al., 2021), data from each client is used as a variable on an hourly basis in the multivariate forecasting setting. For the ECL dataset, we use 15, 3, and 4 months as training, validation, and test data, respectively. 

**Experimental details.** We set the prediction lengths to be one day (1d), 2d, 7d, 14d, 30d, and 40d for the hourly-basis datasets, ETTh1, ETTh2, and ECL. For the ETTm1 dataset, we chose six hours (6h), 12h, 3d, 7d, and 14d as the prediction window lengths. We evaluate the time-series forecasting performance on the mean squared error (MSE) and mean absolute error (MAE). Following the same evaluation procedure used in the previous study (Zhou et al., 2021), we compute the MSE and MAE on z-score normalized data to measure different variables on the same scale. More details on experimental settings, including training details and hyperparameters, are provided in Appendix A.11. 

**Baselines compared.** RevIN is a model-agnostic method, generally applicable to any deep neural network. In this paper, we verify the effectiveness of RevIN by adopting it to three state-of-the-art time-series forecasting models: Informer (Zhou et al., 2021), N-BEATS (Oreshkin et al., 2020), and SCINet (Liu et al., 2021). These are non-autoregressive forecasting models. The reproduction details for the baselines are provided in Appendix A.12. Unless stated otherwise, we compare RevIN and the baselines under the same hyperparameter settings, including the input and prediction lengths. 

## 4.2 RESULTS AND ANALYSES 

This section provides the quantitative analysis and qualitative visualization results of RevIN in comparison with the state-of-the-art time-series forecasting baselines. 

- 4.2.1 EFFECTIVENESS OF REVERSIBLE INSTANCE NORMALIZATION ON VARIOUS TIME-SERIES FORECASTING MODELS 

Table 1 compares the forecasting accuracy of the baselines and RevIN. The results show that RevIN consistently outperforms all three baselines, Informer, N-BEATS, and SCINet, by a large margin, 

> 1https://github.com/zhouhaoyi/ETDataset 

> 2https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014 

6 

Published as a conference paper at ICLR 2022 

Table 1: **Comparison of forecasting errors between the baselines and RevIN.** The analysis on the four datasets, ETTh1, ETTh2, ETTm1, and ECL, is conducted by increasing the prediction length from 24 to 960/1344. We report the average errors for five runs. The complete results are provided in Appendix A.14, including standard deviation and the originally reported values for the baselines. 

|Me|thod|Infor|mer|**+ R**|**evIN**|N-BE|ATS|**+ Re**|**vIN**|SCI|Net|**+ R**|**evIN**|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|M|etric|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
||24|0.550|0.536|**0.504**|**0.472**|0.478|0.505|**0.330**|**0.373**|0.338|0.373|**0.308**|**0.347**|
||48|0.772|0.668|**0.646**|**0.547**|0.536|0.542|**0.372**|**0.400**|0.436|0.459|**0.365**|**0.389**|
|Th1|168|1.138|0.853|**0.655**|**0.561**|1.005|0.782|**0.466**|**0.452**|0.459|0.461|**0.406**|**0.416**|
|T|336|1.278|0.909|**1.058**|**0.758**|0.932|0.743|**0.515**|**0.483**|0.527|0.513|**0.467**|**0.471**|
|E|720|1.357|0.945|**0.926**|**0.717**|1.389|0.926|**0.576**|**0.534**|0.596|0.571|**0.507**|**0.505**|
||960|1.470|0.990|**0.902**|**0.715**|1.383|0.932|**0.678**|**0.575**|0.604|0.574|**0.545**|**0.526**|
||24|0.450|0.520|**0.238**|**0.325**|0.403|0.472|**0.192**|**0.276**|0.199|0.295|**0.180**|**0.263**|
||48|2.171|1.200|**0.361**|**0.404**|1.330|0.918|**0.254**|**0.320**|0.350|0.422|**0.231**|**0.302**|
|h2|168|8.157|2.558|**0.859**|**0.649**|7.174|2.329|**0.410**|**0.418**|0.559|0.518|**0.337**|**0.378**|
|TT|336|4.746|1.844|**0.890**|**0.673**|4.859|1.863|**0.449**|**0.447**|0.664|0.583|**0.357**|**0.403**|
|E|720|3.190|1.529|**0.576**|**0.546**|5.656|2.012|**0.496**|**0.482**|1.546|0.944|**0.411**|**0.445**|
||960|2.972|1.441|**0.600**|**0.570**|6.408|2.077|**0.471**|**0.481**|1.862|1.066|**0.438**|**0.462**|
||24|0.330|0.382|**0.309**|**0.352**|0.443|0.437|**0.403**|**0.392**|0.130|0.231|**0.106**|**0.196**|
||48|0.499|0.486|**0.390**|**0.391**|0.453|0.472|**0.328**|**0.371**|0.155|0.262|**0.135**|**0.222**|
|m1|96|0.605|0.554|**0.405**|**0.411**|0.603|0.581|**0.379**|**0.406**|0.195|0.291|**0.162**|**0.247**|
|TT|288|0.906|0.738|**0.563**|**0.502**|0.849|0.702|**0.451**|**0.445**|0.361|0.419|**0.265**|**0.321**|
|E|672|0.943|0.760|**0.663**|**0.550**|0.860|0.726|**0.555**|**0.511**|1.020|0.756|**0.357**|**0.380**|
||1344|1.095|0.823|**0.824**|**0.632**|14.613|1.948|**0.631**|**0.556**|1.841|1.044|**0.412**|**0.422**|
||24|0.250|0.358|**0.148**|**0.257**|0.279|0.372|**0.176**|**0.285**|0.138|0.246|**0.112**|**0.207**|
||48|0.300|0.386|**0.171**|**0.279**|0.309|0.388|**0.194**|**0.301**|0.163|0.265|**0.126**|**0.222**|
|L|168|0.345|0.423|**0.261**|**0.354**|0.333|0.410|**0.218**|**0.320**|0.177|0.281|**0.153**|**0.249**|
|EC|336|0.429|0.473|**0.356**|**0.414**|0.326|0.406|**0.241**|**0.337**|0.202|0.308|**0.162**|**0.262**|
||720|0.851|0.719|**0.834**|**0.700**|0.420|0.467|**0.303**|**0.383**|0.234|0.333|**0.183**|**0.281**|
||960|0.930|0.750|**0.894**|**0.741**|0.399|0.455|**0.325**|**0.398**|0.235|0.330|**0.200**|**0.292**|



Table 2: **Comparison of long sequence forecasting performance.** We analyze the forecasting error of the baselines and RevIN by increasing the prediction length from 48 to 960 while the input length is fixed to 48. The experiment is conducted on ETTh1. The average errors for five runs are reported, and the complete results, including standard deviation, are provided in Appendix A.14. 

|Prediction length|4|8|16|8|33|6|7|20|9|60|
|---|---|---|---|---|---|---|---|---|---|---|
|Metric|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
|Informer<br>**+ RevIN**|0.687<br>**0.540**|0.628<br>**0.481**|0.982<br>**0.680**|0.795<br>**0.574**|1.212<br>**0.939**|0.893<br>**0.696**|1.157<br>**1.021**|0.863<br>**0.752**|1.203<br>**1.061**|0.888<br>**0.775**|
|N-BEATS<br>**+ RevIN**|0.512<br>**0.365**|0.523<br>**0.389**|0.804<br>**0.454**|0.690<br>**0.438**|1.001<br>**0.526**|0.773<br>**0.477**|1.022<br>**0.568**|0.765<br>**0.514**|0.901<br>**0.638**|0.728<br>**0.544**|
|SCINet<br>**+ RevIN**|0.376<br>**0.349**|0.396<br>**0.370**|0.600<br>**0.445**|0.556<br>**0.426**|0.841<br>**0.509**|0.695<br>**0.461**|0.875<br>**0.533**|0.721<br>**0.494**|0.900<br>**0.557**|0.737<br>**0.510**|



achieving state-of-the-art performance on the four datasets. Moreover, the effectiveness of RevIN is more evident for the long sequence prediction, where it remarkably reduces the errors of the baselines. RevIN shows a stable performance in contrast to the baselines, which show a high increase in error as prolonging the prediction length. For example, when the prediction length increases from 24 to 960 on the ETTh2 dataset, the forecasting error of N-BEATS significantly increases from 0.403 to 6.408. In contrast, RevIN shows a much slight increase in error, i.e., from 0.192 to 0.471. A similar tendency appears with the other prediction lengths, datasets, and baseline models as well. These results demonstrate that RevIN makes the baseline model more robust to prediction length. 

7 

Published as a conference paper at ICLR 2022 



Figure 4: **Forecasting error for each time step.** We compare the error of predicting 1 _∼_ 960 steps ahead between the baselines and RevIN on ETTh1 when the prediction length is 960 (40 days). 

Table 3: **Comparison with classical and state-of-the-art normalization methods.** The mean squared errors are compared on the four datasets, using N-BEATS as the baseline for all experiments. Here, every normalization method is applied to the input data. DAIN, deep adaptive input normalization (Passalis et al., 2019); RevBN, the reversible batch normalization, i.e., the modified version of RevIN. Complete results, including different prediction lengths, are provided in Appendix A.7. 

|Dataset|ET|Th1|ET|Th2|ETT|m1|E|CL|
|---|---|---|---|---|---|---|---|---|
|Prediction length|168|960|168|960|96|1344|168|960|
|Min-max norm|1.074|1.224|2.987|3.308|1.035|1.320|0.374|0.387|
|z-score norm|0.953|1.043|3.329|3.087|1.016|1.274|0.335|0.377|
|Layer norm|0.871|1.303|4.092|5.822|0.502|2.488|0.343|0.379|
|DAIN|0.996|1.032|1.982|2.802|0.672|1.348|0.347|0.381|
|Batch norm|0.851|1.691|6.206|7.755|0.505|1.147|0.320|0.422|
|**RevBN**|0.717|0.779|0.729|2.148|0.601|0.991|0.327|0.414|
|Instance norm|0.946|1.090|3.240|3.145|1.021|1.329|0.333|0.386|
|**RevIN (ours)**|**0.515**|**0.697**|**0.419**|**0.465**|**0.388**|**0.602**|**0.220**|**0.329**|



We further quantitatively analyze the effect of RevIN on long sequence prediction in Table 2. When the model prediction length is increased from 48 to 960, RevIN reduces the prediction error compared to the baseline, showing robust performance against the prediction length. The difference in the forecasting error between SCINet and RevIN is relatively small when the prediction length is short (e.g., 48), but RevIN remarkably surpasses SCINet by a significant margin when the prediction length is long (e.g., 336, 720, and 960). These results substantiate that adopting RevIN can make a model robust to the prediction length. 

Additionally, to study how RevIN can perform well in long sequence prediction, we visualize the forecasting error for each time step in Fig. 4. The error at the _t_ -th time step is computed as MSE- _t_ = _N_ <u>1</u> � _Ni_ =1 _K_ <u>1</u> � _Kk_ =1<sup>(ˆ</sup><sup>_y_</sup> _kt_<sup>(</sup><sup>_i_)</sup><sup>_−y_</sup> _kt_<sup>(</sup><sup>_i_))2. Overall, RevIN shows superior performance compared</sup> to the baselines; the performance degradation is significantly slower, showing low error even when forecasting 960 steps ahead. Specifically, for N-BEATS and SCINet, the error extremely increases as predicting the distant future values. RevIN alleviates this significant increase in error, showing remarkable performance compared to the baselines. Informer also shows unstable performance for the different time steps. The error is substantial in the early steps and becomes relatively small in the distant steps. RevIN allows the models to have consistently minor errors in every time step, even where the baselines originally show high error (early steps for Informer, distant steps for N-BEATS and SCINet). The results demonstrate the effectiveness of RevIN when forecasting long sequences. 

## 4.2.2 COMPARISON WITH EXISTING NORMALIZATION METHODS 

We compare RevIN with classical and state-of-the-art normalization methods, including minmax normalization, z-score normalization, layer normalization (Ba et al., 2016), batch normalization (Ioffe & Szegedy, 2015), instance normalization (Ulyanov et al., 2016), and deep adaptive input 

8 

Published as a conference paper at ICLR 2022 



<!-- Start of picture text -->
+ + + +<br>Layer-1 Layer-2 Layer-1 Layer-2 Layer-1 Layer-2 Layer-1 Layer-2<br>Train-test data<br> featrue divergence<br><!-- End of picture text -->

Figure 5: **Feature divergence between the training and test data in the intermediate layers of the model** The feature divergences are computed on the ETTh1, ETTh2, ETTm1, and ECL datasets using the features obtained from the first (Layer-1) and the second (Layer-2) encoder layers in Informer. 

normalization (DAIN) (Passalis et al., 2019) in Table 3. Here, we compute the statistics for min-max and z-score normalization methods for every input instance, not for the entire data. Additionally, we attempt to use batch normalization as the input normalization method in RevIN, named reversible batch normalization (RevBN). Layer normalization cannot be used in a similar manner since it is not reversible when the input and prediction lengths are different, as in our experimental settings. 

As a result, RevIN shows outstanding performance compared to the other normalization methods, especially on ETTh2 and ETTm1 datasets. Also, RevBN improves forecasting performance of batch normalization. Specifically, the error considerably decreases in the long sequence prediction, such as 960 and 1344. This result supports that the denormalization step of RevIN is essential as a key component of the proposed method for improving long sequence forecasting. However, batch normalization applies identical normalization to all the input sequences, using the global statistics obtained from the entire training data; it can not reduce the discrepancy between the training and test data distributions. Consequently, RevIN, which transforms the data in the instance level, outperforms RevBN by a significant margin, demonstrating that successfully reducing the discrepancy between distributions of different input sequences can effectively improve performance. Moreover, RevIN not only shows the best performance but also has the advantage of being lightweight compared to the baselines. For example, when _K_ is the number of variables, DAIN requires at least 3 _K_<sup>2</sup> additional parameters, whereas RevIN only requires 2 _K_ additional parameters. 

## 4.2.3 ANALYSIS OF DISTRIBUTION SHIFT IN THE INTERMEDIATE LAYERS 

In Fig. 5, we analyze the feature divergence between the training and test data to verify that RevIN can reduce the distribution shift at the intermediate feature level as well. We conduct the experiment using Informer as the baseline; it comprises two encoder layers and one decoder layer. Thus, we analyze the features of the first (Layer-1) and the second (Layer-2) encoder layers. Following the prior work (Pan et al., 2018), we compute the average feature divergence using symmetric KL divergence (See Appendix A.10). The results show that RevIN significantly reduces the feature divergence between the training and test data in both layers, demonstrating that the proposed approach, when added only to the input and output layers, successfully alleviates the distribution shift problem in the intermediate layers. Moreover, this strengthens RevIN as a generally-applicable flexible layer. An arbitrary model can adopt RevIN by adding it to input and output layers without any architectural modifications. Note that our approach still can be added to any arbitrarily chosen layers, significantly improving the model performance, as shown in Appendix A.4. 

# 5 CONCLUSION 

This paper aims to address the distribution shift problem in time series, proposing a simple yet effective normalization-and-denormalization method, reversible instance normalization (RevIN). The proposed approach effectively alleviates the discrepancy between training and test data distributions, leading to significant performance improvements in time-series forecasting. As a generallyapplicable layer to arbitrary deep neural networks, the proposed approach achieves state-of-the-art performance on seven real-world time-series datasets by a significant margin. The extensive quantitative and qualitative experiments with in-depth analysis demonstrate the effectiveness of RevIN for accurate time-series forecasting against the distribution shift problem. 

9 

Published as a conference paper at ICLR 2022 

## REPRODUCIBILITY STATEMENT 

To ensure reproducibility, we provide the source code of our method publicly, including the pretrained model weights. In the main manuscript, Section 4.1 describes how we conduct data preprocessing on the datasets used in the experiments. Appendix A.11 explains the experimental details, including random seed values for the experiments. Appendix A.12 provides a detailed explanation of hyperparameter configurations with the reproduction details of the baselines. 

## ACKNOWLEDGMENTS 

This work was supported by the Institute of Information & communications Technology Planning & Evaluation (IITP) grant funded by the Korea government (MSIT) (No. 2018-0-00219, Spacetime complex artificial intelligence blue-green algae prediction technology based on direct-readable water quality complex sensor and hyperspectral image, and No.2019-0-00075, Artificial Intelligence Graduate School Program (KAIST)). 

# REFERENCES 

- Mohsen Ahmadi, Saeid Jafarzadeh-Ghoushchi, Rahim Taghizadeh, and Abbas Sharifi. Presentation of a new hybrid approach for forecasting economic growth using artificial intelligence approaches. _Neural Computing and Applications_ , 31(12):8661–8680, 2019. 

- Jimmy Lei Ba, Jamie Ryan Kiros, and Geoffrey E Hinton. Layer normalization. _arXiv preprint arXiv:1607.06450_ , 2016. 

- Yuntao Du, Jindong Wang, Wenjie Feng, Sinno Pan, Tao Qin, Renjun Xu, and Chongjun Wang. Adarnn: Adaptive learning and forecasting of time series. _Proc. the International Conference on Information and Knowledge Management (CIKM)_ , 2021. 

- Laura Fr´ıas-Paredes, Ferm´ın Mallor, Mart´ın Gast´on-Romeo, and Teresa Le´on. Assessing energy forecasting inaccuracy by simultaneously considering temporal and absolute errors. _Energy Conversion and Management_ , 142:533–546, 2017. 

- Yaroslav Ganin, Evgeniya Ustinova, Hana Ajakan, Pascal Germain, Hugo Larochelle, Franc¸ois Laviolette, Mario Marchand, and Victor Lempitsky. Domain-adversarial training of neural networks. _The journal of machine learning research (JMLR)_ , 17(1):2096–2030, 2016. 

- Charles C Holt. Forecasting seasonals and trends by exponentially weighted moving averages. _International journal of forecasting_ , 20(1):5–10, 2004. 

- Sergey Ioffe and Christian Szegedy. Batch normalization: Accelerating deep network training by reducing internal covariate shift. In _Proc. the International Conference on Machine Learning (ICML)_ , pp. 448–456. PMLR, 2015. 

- Jinhee Kim, Taesung Kim, Jang-Ho Choi, and Jaegul Choo. End-to-end multi-task learning of missing value imputation and forecasting in time-series data. In _2020 25th International Conference on Pattern Recognition (ICPR)_ , pp. 8849–8856. IEEE, 2021a. 

- Taesung Kim, Jinhee Kim, Wonho Yang, Hunjoo Lee, and Jaegul Choo. Missing value imputation of time-series air-quality data via deep neural networks. _International journal of environmental research and public health_ , 18(22):12213, 2021b. 

- Guokun Lai, Wei-Cheng Chang, Yiming Yang, and Hanxiao Liu. Modeling long- and short-term temporal patterns with deep neural networks. _CoRR_ , 2017. 

- Vincent Le Guen and Nicolas Thome. Shape and time distortion loss for training deep time series forecasting models. In _Proc. the Advances in Neural Information Processing Systems (NeurIPS)_ , volume 4191, 2019. 

- Haoliang Li, Sinno Jialin Pan, Shiqi Wang, and Alex C Kot. Domain generalization with adversarial feature learning. In _Proc. of the IEEE conference on computer vision and pattern recognition (CVPR)_ , 2018. 

10 

Published as a conference paper at ICLR 2022 

- Minhao Liu, Ailing Zeng, Qiuxia Lai, and Qiang Xu. Time series is a special sequence: Forecasting with sample convolution and interaction. _arXiv preprint arXiv:2106.09305_ , 2021. 

- Spyros Makridakis, Evangelos Spiliotis, and Vassilios Assimakopoulos. The m4 competition: 100,000 time series and 61 forecasting methods. _International Journal of Forecasting_ , 36(1): 54–74, 2020. 

- Krikamol Muandet, David Balduzzi, and Bernhard Sch¨olkopf. Domain generalization via invariant feature representation. In _Proc. the International Conference on Machine Learning (ICML)_ . PMLR, 2013. 

- Eduardo Ogasawara, Leonardo C Martinez, Daniel De Oliveira, Geraldo Zimbr˜ao, Gisele L Pappa, and Marta Mattoso. Adaptive normalization: A novel data normalization approach for nonstationary time series. In _The International Joint Conference on Neural Networks (IJCNN)_ , pp. 1–8. IEEE, 2010. 

- Boris N Oreshkin, Dmitri Carpov, Nicolas Chapados, and Yoshua Bengio. N-beats: Neural basis expansion analysis for interpretable time series forecasting. _Proc. the International Conference on Learning Representations (ICLR)_ , 2020. 

- Xingang Pan, Ping Luo, Jianping Shi, and Xiaoou Tang. Two at once: Enhancing learning and generalization capacities via ibn-net. In _Proc. of the European Conference on Computer Vision (ECCV)_ , 2018. 

- Cheonbok Park, Chunggi Lee, Hyojin Bahng, Yunwon Tae, Seungmin Jin, Kihwan Kim, Sungahn Ko, and Jaegul Choo. St-grat: A novel spatio-temporal graph attention network for accurately forecasting dynamically changing road speed. In _Proc. the ACM Conference on Information and Knowledge Management (CIKM)_ , 2020. 

- Nikolaos Passalis, Anastasios Tefas, Juho Kanniainen, Moncef Gabbouj, and Alexandros Iosifidis. Deep adaptive input normalization for time series forecasting. _IEEE transactions on neural networks and learning systems_ , 31(9):3760–3765, 2019. 

- Adam Paszke, Sam Gross, Francisco Massa, Adam Lerer, James Bradbury, Gregory Chanan, Trevor Killeen, Zeming Lin, Natalia Gimelshein, Luca Antiga, et al. Pytorch: An imperative style, highperformance deep learning library. _Proc. the Advances in Neural Information Processing Systems (NeurIPS)_ , 32, 2019. 

- Slawek Smyl. A hybrid method of exponential smoothing and recurrent neural networks for time series forecasting. _International Journal of Forecasting_ , 36(1):75–85, 2020. 

- Eric Tzeng, Judy Hoffman, Kate Saenko, and Trevor Darrell. Adversarial discriminative domain adaptation. In _Proc. of the IEEE conference on computer vision and pattern recognition (CVPR)_ , 2017. 

- Dmitry Ulyanov, Andrea Vedaldi, and Victor Lempitsky. Instance normalization: The missing ingredient for fast stylization. _arXiv preprint arXiv:1607.08022_ , 2016. 

- Jindong Wang, Wenjie Feng, Yiqiang Chen, Han Yu, Meiyu Huang, and Philip S Yu. Visual domain adaptation with manifold embedded distribution alignment. In _Proc. the ACM international conference on Multimedia_ , pp. 402–410, 2018. 

- Jindong Wang, Cuiling Lan, Chang Liu, Yidong Ouyang, Wenjun Zeng, and Tao Qin. Generalizing to unseen domains: A survey on domain generalization. _arXiv preprint arXiv:2103.03097_ , 2021. 

- Peter R Winters. Forecasting sales by exponentially weighted moving averages. _Management science_ , 6(3):324–342, 1960. 

- Ying Zhang, Baohang Zhou, Xiangrui Cai, Wenya Guo, Xiaoke Ding, and Xiaojie Yuan. Missing value imputation in multivariate time series with end-to-end generative adversarial networks. _Information Sciences_ , 551:67–82, 2021. 

- Haoyi Zhou, Shanghang Zhang, Jieqi Peng, Shuai Zhang, Jianxin Li, Hui Xiong, and Wancai Zhang. Informer: Beyond efficient transformer for long sequence time-series forecasting. In _Proc. the AAAI Conference on Artificial Intelligence (AAAI)_ , 2021. 

11 

Published as a conference paper at ICLR 2022 

# A APPENDIX 

This section provides additional information, visualizations, and experimental results that support the main manuscript. Section A.1 shows the experimental results on additional real-world datasets along with a qualitative analysis on one of the datasets to verify the effectiveness of our method on obvious non-stationary time series. Section A.2 addresses the potential of RevIN on solving the cross-domain time-series forecasting task. Section A.3 and Section A.4 present the hyperparameter sensitivity analysis and the ablation study on the proposed method, respectively. Section A.5 evaluates our method using complementary metrics, which measure the similarity between two sequences. Section A.6 and Section A.7 compare the forecasting results using the proposed method and existing normalization methods. Section A.8, Section A.9, and Section A.10 provide the algorithm for RevIN, the theoretical justification of RevIN, and the calculation details of the feature divergence used in Section 4.2.3, respectively. Section A.11 and Section A.12 describe additional implementation details and the reproduction details of the baselines where RevIN is applied, respectively. Section A.13 illustrates additional quantitative results for RevIN and the baselines. Lastly, Section A.14 provides complete quantitative results, including the standard deviation values for five experiments, which can not be included in the main manuscript due to the lack of space. 

- A.1 EXPERIMENTAL RESULTS ON ADDITIONAL REAL-WORLD TIME-SERIES DATASETS 

Table 4: **Forecasting performance on the air quality, Nasdaq, and M4 competition datasets. The results on the M4 dataset (*) are multiplied by ten for readability. The average value and the standard deviation value for five runs are reported.** 

|Methods|Info|rmer|**+ R**|**evIN**|N-BE|ATS|**+ R**|**evIN**|SCI|Net|**+ R**|**evIN**|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Metric|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
|24|0.802|0.671|**0.585**|**0.539**|0.698|0.626|**0.527**|**0.498**|0.512|0.514|**0.490**|**0.474**|
||_±_0.178|_±_0.084|_±_**0.033**|_±_**0.023**|_±_0.064|_±_0.029|_±_**0.005**|_±_**0.003**|_±_0.029|_±_0.019|_±_**0.006**|_±_**0.004**|
|4|0.966|0.761|**0.859**|**0.668**|0.955|0.740|**0.705**|**0.600**|0.712|0.627|**0.659**|**0.566**|
|ity<br>8|_±_0.054|_±_0.023|_±_**0.086**|_±_**0.041**|_±_0.106|_±_0.035|_±_**0.019**|_±_**0.009**|_±_0.091|_±_0.047|_±_**0.013**|_±_**0.007**|
|ual<br>|1.328|0.923|**1.036**|**0.761**|1.079|0.818|**0.789**|**0.660**|0.957|0.737|**0.794**|**0.645**|
|r q<br>168|_±_0.107|_±_0.040|_±_**0.056**|_±_**0.020**|_±_0.108|_±_0.046|_±_**0.008**|_±_**0.005**|_±_0.067|_±_0.031|_±_**0.025**|_±_**0.014**|
|Ai<br>|1.278|0.901|**1.145**|**0.801**|1.105|0.835|**0.860**|**0.685**|0.989|0.760|**0.854**|**0.676**|
|<br>336|_±_0.074|_±_0.032|_±_**0.032**|_±_**0.010**|_±_0.052|_±_0.021|_±_**0.017**|_±_**0.006**|_±_0.111|_±_0.046|_±_**0.029**|_±_**0.010**|
|720|2.028|1.104|**1.161**|**0.810**|1.538|0.968|**0.842**|**0.686**|1.228|0.858|**0.839**|**0.680**|
||_±_0.216|_±_0.061|_±_**0.028**|_±_**0.009**|_±_0.419|_±_0.110|_±_**0.015**|_±_**0.008**|_±_0.048|_±_0.021|_±_**0.024**|_±_**0.013**|
|30|5.318|1.093|**1.273**|**0.630**|5.500|1.254|**1.023**|**0.577**|1.742|0.739|**0.985**|**0.564**|
|q<br>|_±_0.052|_±_0.017|_±_**0.078**|_±_**0.009**|_±_0.647|_±_0.086|_±_**0.034**|_±_**0.007**|_±_0.111|_±_0.028|_±_**0.018**|_±_**0.005**|
|da<br>60|5.525|1.098|**1.573**|**0.666**|5.226|1.236|**1.207**|**0.617**|2.304|0.790|**1.161**|**0.601**|
|as<br>|_±_0.022|_±_0.016|_±_**0.098**|_±_**0.011**|_±_0.424|_±_0.032|_±_**0.044**|_±_**0.009**|_±_0.062|_±_0.010|_±_**0.021**|_±_**0.003**|
|N<br>120|5.793|1.090|**2.648**|**0.762**|6.023|1.197|**1.959**|**0.714**|3.227|0.853|**1.869**|**0.697**|
||_±_0.140|_±_0.012|_±_**0.186**|_±_**0.016**|_±_0.382|_±_0.034|_±_**0.062**|_±_**0.006**|_±_0.236|_±_0.007|_±_**0.037**|_±_**0.003**|
|4_∗_<br>|0.099|0.258|**0.008**|**0.074**|2.241|2.065|**2.082**|**1.974**|2.180|1.943|**2.079**|**1.892**|
|M<br>average|_±_0.002|_±_0.020|_±_**0.005**|_±_**0.005**|_±_0.037|_±_0.029|_±_**0.014**|_±_**0.006**|_±_1.943|_±_0.011|_±_**0.011**|_±_**0.004**|



We evaluate the proposed method on the four large-scale real-world time-series datasets, the ETTh1, ETTh2, ETTm1, and ECL datasets in the main manuscript. Additionally, this section provides experimental results on three more datasets, including two real-world datasets taken from the UCI repository, the air quality dataset and the Nasdaq dataset, and the M4 competition dataset (Makridakis et al., 2020). In total, our proposed method is evaluated on seven datasets in this paper. 

**Air quality**<sup>3</sup> dataset contains hourly averaged responses collected from five metal oxide chemical sensors located in Italy. The data consist of 13 variables of length 9537. We set the prediction length as _{_ 24, 48, 168, 336, 720 _}_ and the corresponding input length as _{_ 48, 96, 168, 168, 360 _}_ so that their ratios become _{_ 2x, 2x, 1x, 0.5x, 0.5x _}_ . 

**Nasdaq**<sup>4</sup> dataset consists of 82 variables, including important indices of markets around the world, the price of major companies in the U.S. market, treasury bill rates, etc. It is measured daily, having a total of 1984 data samples for each variable. We prolong the prediction length as _{_ 30, 60, 120 _}_ and set the corresponding input length as 60 for all. 

> 3https://archive.ics.uci.edu/ml/datasets/Air+Quality 

> 4https://archive.ics.uci.edu/ml/datasets/CNNpred%3A+CNN-based+stock+market+prediction+using+ a+diverse+set+of+variables 

12 

Published as a conference paper at ICLR 2022 



Figure 6: **Prediction results on the Nasdaq dataset.** The results on three variables in the data, Close, DTB6, and DE1, are shown. The prediction length is 60 days, and the seventh value is illustrated to show the results on the entire test set. We compare RevIN with N-BEATS. 

**M4**<sup>5</sup> competition dataset consists of six different hourly, daily, weekly, monthly, quarterly, and yearly sets, containing 100,000 test data. We follow the original experimental protocol of the M4 competition (Makridakis et al., 2020). For evaluation, we measure the micro-averaged mean absolute error and mean squared error: we first compute the metric independently for each set, i.e., hourly, daily, weekly, monthly, quarterly, and yearly sets, and then calculate the weighted average of the metrics using the contributions of each set as the weights. 

As shown in Table 4, RevIN significantly improves the forecasting performance of the baselines on all three datasets. Notably, RevIN shows outstanding performance on the Nasdaq dataset, reducing the prediction errors by more than half compared to the baselines. 

Additionally, we conduct a qualitative analysis on the Nasdaq dataset to verify the effectiveness of our method on obvious non-stationary time series. As shown in Fig. 6, the Nasdaq index (the variable ’Close’) has steadily increased since 2010. Accordingly, when data are divided into the training and test data based on a specific point in time (vertical dashed line in Fig. 6), the test data values tend to be higher than the training data values. In other words, the data severely suffers from the distribution shift problem, where the training and test data show a discrepancy in their distribution. As a result, even existing state-of-the-art models often cannot predict the future values appropriately, as shown in Fig. 6. The baseline fails to keep up with the trend in data, whose mean value continues to increase, and thus the prediction results are shifted. However, RevIN mitigates this distribution discrepancy and remarkably increases the prediction performance of the baseline. 

> 5https://mofc.unic.ac.cy/m4/ 

13 

Published as a conference paper at ICLR 2022 

Similarly, RevIN shows superior performance on the other rapidly increasing data (’DTB6’ in Fig. 6) and the decreasing test data (‘DE1’ in Fig. 6), accurately predicting the changing mean of the data. 

## A.2 CROSS-DOMAIN TIME-SERIES FORECASTING 

Table 5: **Cross-domain time-series forecasting results.** We conduct a cross-domain evaluation on the ETT datasets, ETTh1, ETTh2, and ETTm1. We train RevIN using SCINet as the baseline. We report the average errors and the standard deviation values for five runs. 

|Trai|n||ETT|h1|||ETT|h2|||ETT|m1||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Test||ETT|h2|ETT|m1|ETT|h1|ETT|m1|ETT|h1|ET|Th2|
|Prediction|length|336|960|336|960|336|960|336|960|288|1344|288|1344|
|SCINet|MSE<br>MAE|0.471<br>_±_0.034<br>0.450<br>_±_0.024|0.741<br>_±_0.056<br>0.640<br>_±_0.027|0.471<br>_±_0.043<br>0.427<br>_±_0.032|0.765<br>_±_0.029<br>0.636<br>_±_0.013|0.614<br>_±_0.020<br>0.507<br>_±_0.014|0.671<br>_±_0.061<br>0.607<br>_±_0.035|0.608<br>_±_0.049<br>0.487<br>_±_0.031|1.668<br>_±_0.110<br>1.004<br>_±_0.046|0.659<br>_±_0.032<br>0.562<br>_±_0.015|0.654<br>_±_0.026<br>0.608<br>_±_0.016|0.518<br>_±_0.009<br>0.509<br>_±_0.004|1.813<br>_±_0.166<br>1.027<br>_±_0.078|
|**+ RevIN**|MSE|**0.350**<br>_±_**0.010**|**0.419**<br>_±_**0.007**|**0.346**<br>_±_**0.008**|**0.452**<br>_±_**0.004**|**0.501**<br>_±_**0.006**|**0.586**<br>_±_**0.015**|**0.321**<br>_±_**0.009**|**0.441**<br>_±_**0.001**|**0.478**<br>_±_**0.003**|**0.542**<br>_±_**0.013**|**0.387**<br>_±_**0.005**|**0.506**<br>_±_**0.010**|
||MAE|**0.383**<br>_±_**0.006**|**0.451**<br>_±_**0.004**|**0.331**<br>_±_**0.005**|**0.449**<br>_±_**0.001**|**0.449**<br>_±_**0.004**|**0.542**<br>_±_**0.007**|**0.331**<br>_±_**0.004**|**0.445**<br>_±_**0.001**|**0.477**<br>_±_**0.002**|**0.531**<br>_±_**0.006**|**0.417**<br>_±_**0.002**|**0.503**<br>_±_**0.006**|



As RevIN can alleviate the distribution discrepancy between the training and test data, we investigate the ability of RevIN in mitigating distribution discrepancy between different domains through crossdomain time-series forecasting task. In time series, a domain can be a location of a sensor where the data is collected. We use the ETT datasets for the experiment since they have the same feature categories. However, their distributions can exhibit significant discrepancy because the ETTh1 and ETTh2 datasets are collected from different locations, and the ETTh and ETTm1 datasets have different measurement time intervals. Thus, we alternately use each ETT dataset as a source domain for training and a target domain for testing. The goal of cross-domain time-series forecasting is to alleviate the data distribution discrepancy between the source and target domains, e.g., between the ETTh1 and ETTh2 datasets. 

In Table 5, despite the difference in the <u>data distributions, RevIN shows remarkable performance in</u> cross-do ~~<u><mark>main time-</mark> series for</u>~~ ec ~~<u>astin</u>~~ ~~<u><mark>g</mark> . In</u>~~ ~~<u><mark>p</mark> articular</u>~~ ~~<u><mark>,</mark> R</u>~~ evIN outperforms SCINet by a large margin when the ~~<u><mark>model needs to re</mark></u>~~ d ~~<u><mark>uce the discrepancy b</mark> e</u>~~ tween the ETTh2 and ETTm1 datasets. The results de ~~<u><mark>monstrate that RevI</mark></u>~~ N ~~<u><mark>successfully solves th</mark></u>~~ e distribution shift problem by alleviating data distributio ~~<u><mark>n discrepa</mark></u>~~ ncy betwe ~~<u><mark>en diff</mark></u>~~ erent ~~<u><mark>doma</mark></u>~~ ins, leading to better generalization performance. 

## A.3 HYPERPARAMETER SENSITIVITY ANALYSIS 

~~<u><mark>We an</mark></u>~~ aly ~~<u><mark>ze the hyperparamet</mark></u>~~ er ~~<u><mark>sensitivity of</mark></u>~~ th ~~<u><mark>e proposed me</mark></u>~~ thod compared with the baseline models. Input se ~~<mark>quence</mark>~~ <u>len</u> <u><mark>g</mark> th can be</u> ~~<mark>a crucial hy</mark>~~ perp ~~<mark>arameter to</mark>~~ RevIN since the method computes the mean and the stan ~~<u><mark>dard devia</mark></u>~~ tion acros ~~<u><mark>s the e</mark></u>~~ ntire inpu ~~<u><mark>t sequ</mark></u>~~ ence and then uses the statistics at its 



<!-- Start of picture text -->
1.9 Informer MSE Informer MAE N-BEATS MSE N-BEATS MAE SCINet MSE SCINet MAE<br>1.7 +RevIN MSE +RevIN MAE 4.0 +RevIN MSE +RevIN MAE ±.  1.3 +RevIN MSE +RevIN MAE<br>3.5 1.2<br>1.5 3.0 1.1<br>1.3 2.5 1.0<br>1.1 2.0 0.9<br>0.8<br>0.9 1.5 0.7<br>0.7 1.0 0.6<br>0.5 0.5 0.5<br>48 168 336 480 720 960 48 168 336 480 720 960 48 168 336 480 720 960<br>Input sequence length Input sequence length Input sequence length<br><!-- End of picture text -->

~~<u>Figure 7:</u>~~ **~~<u>Impacts of the in</u>~~ put s** **~~<u>equence length o</u>~~** **<u>n</u> RevIN compared with the baselines.** We ~~<u>prolong the input length fro</u>~~ m 48 ( ~~<u>two days) to 960 (4</u>~~ 0 days) when the prediction length is set as ~~<u>960 (40 days) on the ETTh1</u>~~ dataset ~~<u>. The average errors</u>~~ for five runs, with standard deviation values, <u>ar</u> ~~<u>e reported. In N-BEATS,</u>~~ <u>the</u> sta ~~ndard~~ ~~<u>deviation</u> valu~~ e for the mean squared error is too large to ~~visualize when the prediction~~ length is 960; we write the value as “ _±_ 4 _._ 955” instead. 

14 

Published as a conference paper at ICLR 2022 

normalization and denormalization steps. Thus, the input sequence length would play a crucial role in the prediction accuracy and stability of the training process. Accordingly, we prolong the model input sequence length to see its impact on the forecasting performance of RevIN, as shown in Fig. 7. As a result, RevIN consistently outperforms the baseline for various input sequence lengths. More importantly, RevIN makes the baseline models more robust to the input length. In other words, RevIN shows stable performance for various input lengths in contrast to the baseline models, which shows the high variance in their performance according to the input length. Notably, in N-BEATS, the average error, as well as the standard deviation of the error, significantly increase as prolonging the input length. This is because the trend in data is expressed as a linear function in N-BEATS. As the input length becomes prolonged, there is a chance that the variance (or non-stationarity) in the time-series values will become higher, decreasing the accuracy of the linear trend to fit the data unless the data is monotonically increasing or decreasing. Also, the mispredicted trends linearly increase the error in future values. However, when N-BEATS adopts the RevIN layer, it removes the non-stationary statistics from the input, and thus, the model shows robust performance against the input length. Removing the variability, i.e., normalizing its mean and standard deviation, before feeding it to the model and returning it to the output makes the model learning stable. 

## A.4 ABLATION STUDY 

Table 6: **Ablation study results.** We ablate the affine transformation (affine.) from RevIN and evaluate forecasting performance on the six datasets. N-BEATS is used as the baseline for all experiments. We report the average and the standard deviation values for the five runs. 

|Meth|od|+ RevIN  i|w/o affine.|**+ RevIN w/ i**|**affine. (ours)**|
|---|---|---|---|---|---|
|Met|ric|MSE|MAE|MSE|MAE|
|ETTh1|48<br>960|0.370_±_0.006<br>0.675_±_0.038|0.393_±_0.003<br>0.576_±_0.014|**0.363**_±_**0.005**<br>**0.638**_±_**0.035**|**0.389**_±_**0.003**<br>**0.559**_±_**0.017**|
|ETTh2|48<br>960|0.257_±_0.003<br>0.483_±_0.012|0.322_±_0.002<br>0.487_±_0.007|**0.255**_±_**0.008**<br>**0.471**_±_**0.015**|**0.321**_±_**0.005**<br>**0.481**_±_**0.008**|
|ETT|96|0.384_±_0.013|0.408_±_0.009|**0.378**_±_**0.011**|**0.406**_±_**0.007**|
|m1|1344|0.664_±_0.085|0.567_±_0.039|**0.631**_±_**0.061**|**0.556**_±_**0.020**|
|ECL|48|0.197_±_0.002|0.302_±_0.002|**0.195**_±_**0.002**|**0.301**_±_**0.001**|
||960|0.347_±_0.034|0.415_±_0.026|**0.325**_±_**0.019**|**0.398**_±_**0.015**|
|Air|48|0.707_±_0.009|0.601_±_0.002|**0.705**_±_**0.019**|**0.600**_±_**0.009**|
|quality|720|0.852_±_0.025|0.689_±_0.013|**0.842**_±_**0.015**|**0.686**_±_**0.008**|
|Nd|30|0.983_±_0.017|0.565_±_0.005|**0.981**_±_**0.017**|**0.564**_±_**0.005**|
|asaq|60|1.163_±_0.010|0.610_±_0.002|**1.155**_±_**0.020**|**0.608**_±_**0.005**|



We ablate the affine transformation from RevIN to analyze its impact on forecasting performance. We conduct the analysis on the ETTh1, ETTh2, ETTm1, ECL, Nasdaq, and air quality datasets using N-BEATS as the baseline. The results in Table 6 show that the affine transformation consistently contributes to performance improvement on a variety of datasets. As mentioned earlier, a model can add RevIN in an intermediate layer, even to several layers. While existing approaches are a preprocessing-and-postprocessing method applied outside of the main prediction model, RevIN is an end-to-end trainable layer that can be added to any layer in the model as batch normalization (Ioffe & Szegedy, 2015) and instance normalization (Ulyanov et al., 2016), which are recently proposed deep learning-based normalization layers. Thus, we verify that adopting RevIN in the intermediate layers instead of the input and output layers can improve the forecasting performance as well. We add RevIN to the first stack of N-BEATS and SCINet and evaluate their performance on the six datasets. The results in Table 7 demonstrate that even when added to the intermediate layers, RevIN improves the performance of the baselines, as a learnable normalization layer. We mainly focus on adding RevIN to the input and output of a model since it shows robust performance on average. Nevertheless, the model adopting RevIN in the intermediate layers consistently outperforms the baseline without RevIN, frequently achieving the best performance among all. This performance is even better than the dynamic normalization methods, LSTNet<sup>_∗_</sup> and ES-RNN<sup>_∗_</sup> , when they are 

15 

Published as a conference paper at ICLR 2022 

adopted to N-BEATS as well (See Table 9 in Appendix A.6). For example, when the prediction length is 960, the mean squared errors of LSTNet<sup>_∗_</sup> , ES-RNN<sup>_∗_</sup> , RevIN (inter.), and RevIN (i/o) are 5.627, 1.338, 0.523, and 0.471, on average. In conclusion, RevIN is a flexible, end-to-end trainable 

Table 7: **Effectiveness of RevIN when added to the intermediate layers in the model.** We add RevIN to the first stack of N-BEATS and SCINet and evaluate their performance on the six datasets. We report the average value and standard deviation of five experiments. RevIN (inter.) indicates the model where RevIN is added to the intermediate layers of the baseline network. RevIN (i/o) indicates the model where RevIN is added to the input and output layer of the baseline network. 

|Method|N-BE|ATS|**+ RevIN**|(inter.)|**+ RevI**|**N**(i/o)|SCI|Net|**+ RevIN**|(inter.)|**+ Rev**|**IN**(i/o)|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Metric|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
|24|0.478|0.505|0.347|0.389|**0.330**|**0.373**|0.338|0.373|**0.306**|0.347|0.308|**0.347**|
||_±_0.022<br>0536|_±_0.012<br>0542|_±_0.006<br>0375|_±_0.004<br>0407|_±_**0.006**<br>**0372**|_±_**0.004**<br>**0400**|_±_0.012<br>0436|_±_0.009<br>0459|_±_**0.004**<br>**0363**|_±_0.004<br>0394|_±_0.003<br>0365|_±_**0.002**<br>**0389**|
|48|.<br>_±_0.060|.<br>_±_0.041|.<br>_±_0.008|.<br>_±_0.005|**.**<br>_±_**0.001**|**.**<br>_±_**0.002**|.<br>_±_0.025|.<br>_±_0.021|**.**<br>_±_**0.004**|.<br>_±_0.004|.<br>_±_0.005|**.**<br>_±_**0.003**|
|1|1005|0782|0495|0481|**0466**|**0452**|0459|0461|0415|0424|**0406**|**0416**|
|Th<br>168|.<br>_±_0.146|.<br>_±_0.064|.<br>_±_0.086|.<br>_±_0.062|**.**<br>_±_**0.030**|**.**<br>_±_**0.014**|.<br>_±_0.015|.<br>_±_0.013|.<br>_±_0.001|.<br>_±_0.002|**.**<br>_±_**0.003**|**.**<br>_±_**0.003**|
|ET<br>|0932|0743|0538|0508|**0.515**|**0.483**|0527|0513|0552|0516|**0.467**|**0.471**|
|336|.<br>_±_0.079|.<br>_±_0.042|.<br>_±_0.043|.<br>_±_0.027|_±_**0.013**|_±_**0.008**|.<br>_±_0.010|.<br>_±_0.006|.<br>_±_0.002|.<br>_±_0.001|_±_**0.005**|_±_**0.003**|
||1.389|0.926|0.608|0.572|**0.576**|**0.534**|0.596|0.571|0.560|0.550|**0.507**|**0.505**|
|720|_±_0230|_±_0066|_±_0016|_±_0009|_±_**0035**|_±_**0018**|_±_0015|_±_0013|_±_0007|_±_0005|_±_**0006**|_±_**0004**|
||.<br>1.383|.<br>0.932|.<br>**0.664**|.<br>0.604|**.**<br>0.678|**.**<br>**0.575**|.<br>0.604|.<br>0.574|.<br>0.619|.<br>0.582|**.**<br>**0.545**|**.**<br>**0.526**|
|960|_±_0.380|_±_0.120|_±_**0.033**|_±_0.015|_±_0.019|_±_**0.009**|_±_0.017|_±_0.014|_±_0.005|_±_0.002|_±_**0.010**|_±_**0.005**|
|24|0.403<br>|0.472<br>|0.199<br>|0.291<br>|**0.192**<br>|**0.276**<br>|0.199<br>|0.295<br>|0.186<br>|0.272<br>|**0.180**<br>|**0.263**<br>|
||_±_0.185|_±_0.101|_±_0.002|_±_0.002|_±_**0.003**|_±_**0.002**|_±_0.026|_±_0.027|_±_0.003|_±_0.001|_±_**0.004**|_±_**0.002**|
||1330|0918|0263|0335|**0254**|**0320**|0350|0422|0313|0373|**0231**|**0302**|
|48|.<br>_±_0.240|.<br>_±_0.073|.<br>_±_0.007|.<br>_±_0.005|**.**<br>_±_**0.011**|**.**<br>_±_**0.008**|.<br>_±_0.025|.<br>_±_0.027|.<br>_±_0.045|.<br>_±_0.032|**.**<br>_±_**0.006**|**.**<br>_±_**0.006**|
|2<br>|7.174|2.329|0.425|0.434|**0.410**|**0.418**|0.559|0.518|0.338|0.380|**0.337**|**0.378**|
|TTh<br>168|_±_0.449<br>|_±_0.049<br>|_±_0.015<br>|_±_0.010<br>|_±_**0.010**|_±_**0.005**<br>|_±_0.044<br>|_±_0.025<br>|_±_0.003|_±_0.001|_±_**0.007**<br>|_±_**0.003**<br>|
|E<br>|4.859|1.863|**0.446**|0.456|0.449|**0.447**|0.664|0.583|0.422|0.443|**0.357**|**0.403**|
|336|_±_0.268<br>|_±_0.043<br>|_±_**0.007**<br>|_±_0.005<br>|_±_0.011<br>|_±_**0.006**<br>|_±_0.073<br>|_±_0.030<br>|_±_0.001<br>|_±_0.001<br>|_±_**0.003**<br>|_±_**0.002**<br>|
||5.656|2.012|0.505|0.501|**0.496**|**0.482**|1.546|0.944|0.634|0.564|**0.411**|**0.445**|
|720|_±_1053|_±_0186|_±_0022|_±_0013|_±_**0008**|_±_**0002**|_±_0378|_±_0141|_±_0010|_±_0005|_±_**0003**|_±_**0002**|
|960|.<br>6.408|.<br>2.077|.<br>0.523|.<br>0.522|**.**<br>**0.471**|**.**<br>**0.481**|.<br>1.862|.<br>1.066|.<br>0.734|.<br>0.603|**.**<br>**0.438**|**.**<br>**0.462**|
||_±_2.039|_±_0.242|_±_0.040|_±_0.025|_±_**0.015**|_±_**0.008**|_±_0.153|_±_0.055|_±_0.014|_±_0.005|_±_**0.007**|_±_**0.004**|
||0443|0437|**0.387**|**0.391**|0403|0392|0130|0231|0108|0203|**0.106**|**0.196**|
|24|.<br>_±_0.043|.<br>_±_0.035|_±_**0.018**|_±_**0.012**|.<br>_±_0.006|.<br>_±_0.005|.<br>_±_0.003|.<br>_±_0.003|.<br>_±_0.002|.<br>_±_0.004|_±_**0.002**|_±_**0.001**|
||0.453|0.472|0.341|0.388|**0.328**|**0.371**|0.155|0.262|0.142|0.241|**0.135**|**0.222**|
|48|_±_0.034|_±_0.018|_±_0.008|_±_0.007|_±_**0.010**|_±_**0.007**|_±_0.004|_±_0.004|_±_0.011|_±_0.013|_±_**0.003**|_±_**0.002**|
|1<br>|0.603|0.581|0.401|0.428|**0.379**|**0.406**|0.195|0.291|0.192|0.285|**0.162**|**0.247**|
|TTm<br>96|_±_0.051<br>|_±_0.027<br>|_±_0.007<br>|_±_0.004<br>|_±_**0.011**<br>|_±_**0.007**<br>|_±_0.012<br>|_±_0.013<br>|_±_0.016<br>|_±_0.017<br>|_±_**0.001**<br>|_±_**0.001**<br>|
|E<br>|0.849|0.702|0.502|0.483|**0.451**|**0.445**|0.361|0.419|**0.264**|0.323|0.265|**0.321**|
|288|_±_0095|_±_0051|_±_0032|_±_0018|_±_**0016**|_±_**0008**|_±_0008|_±_0004|_±_**0002**|_±_0001|_±_0003|_±_**0002**|
|672|.<br>0.860|.<br>0.726|.<br>**0.553**|.<br>0.512|**.**<br>0.555|**.**<br>**0.511**|.<br>1.020|.<br>0.756|**.**<br>0.663|.<br>0.583|.<br>**0.357**|**.**<br>**0.380**|
||_±_0.057|_±_0.026|_±_**0.020**|_±_0.009|_±_0.011|_±_**0.008**|_±_0.040|_±_0.025|_±_0.081|_±_0.033|_±_**0.004**|_±_**0.002**|
|1344|<br>14.613|<br>1.948|<br>0.722|<br>0.594|<br>**0.631**|<br>**0.556**|<br>1.841|<br>1.044|<br>0.989|<br>0.717|<br>**0.412**|<br>**0.422**|
||_±_26.108|_±_1.655|_±_0.064|_±_0.027|_±_**0.061**|_±_**0.020**|_±_0.242|_±_0.100|_±_0.211|_±_0.081|_±_**0.008**|_±_**0.003**|
||0.279|0.372|0.182|0.300|**0.176**|**0.285**|0.138|0.246|**0.111**|**0.207**|0.112|**0.207**|
|24|_±_0.007|_±_0.003|_±_0.001|_±_0.001|_±_**0.002**<br>|_±_**0.001**<br>|_±_0.004|_±_0.005<br>|_±_**0.000**<br>|_±_**0.001**<br>|_±_0.001|_±_**0.001**|
||0.309|0.388|0.207|0.318|**0.194**|**0.301**|0.163|0.265|**0.124**|**0.221**|0.126|0.222|
|48|_±_0007|_±_0004|_±_0003|_±_0002|_±_**0001**|_±_**0001**|_±_0007|_±_0007|_±_**0001**|_±_**0001**|_±_0001|_±_0001|
||.<br>0.333|.<br>0.410|.<br>0.237|.<br>0.340|**.**<br>**0.218**|**.**<br>**0.320**|.<br>0.177|.<br>0.281|**.**<br>0.154|**.**<br>**0.248**|.<br>**0.153**|.<br>0.249|
|CL<br>168|_±_0016|_±_0012|_±_0007|_±_0004|_±_**0.002**|_±_**0.001**|_±_0003|_±_0005|_±_0002|_±_**0.001**|_±_**0.003**|_±_0002|
|E<br>336|.<br>0.326|.<br>0.406|.<br>0.245|.<br>0.348|<br>**0.241**|<br>**0.337**|.<br>0.202|.<br>0.308|.<br>**0.161**|<br>**0.261**|<br>0.162|.<br>0.262|
||_±_0.004|_±_0.001|_±_0.011|_±_0.007|_±_**0.005**|_±_**0.002**|_±_0.004|_±_0.004|_±_**0.002**|_±_**0.002**|_±_0.001|_±_0.001|
|720|<br>0.420|<br>0.467<br>|<br>0.308|<br>0.393|<br>**0.303**<br>|<br>**0.383**<br>|<br>0.234|<br>0.333|<br>0.184|<br>0.283|<br>**0.183**<br>|<br>**0.281**<br>|
||_±_0.094|_±_0.058|_±_0.019|_±_0.016|_±_**0.012**|_±_**0.011**|_±_0.006|_±_0.004|_±_0.003|_±_0.003|_±_**0.003**|_±_**0.002**|
|960|0.399<br>|0.455<br>|0.335<br>|0.413<br>|**0.325**<br>|**0.398**<br>|0.235<br>|0.330<br>|**0.196**<br>|0.295<br>|0.200<br>|**0.292**<br>|
||_±_0.022|_±_0.017|_±_0.018|_±_0.015|_±_**0.019**|_±_**0.015**|_±_0.011|_±_0.008|_±_**0.005**|_±_0.005|_±_0.003|_±_**0.002**|
||0.698|0.626|0.558|0.537|**0.527**|**0.498**|0.512|0.514|**0.488**|0.486|0.490|**0.474**|
|24|_±_0.064<br>|_±_0.029<br>|_±_0.011<br>|_±_0.008<br>|_±_**0.005**<br>|_±_**0.003**<br>|_±_0.029<br>|_±_0.019<br>|_±_**0.006**<br>|_±_0.009<br>|_±_0.006<br>|_±_**0.004**<br>|
|y<br>48|0.955<br>_±_0106|0.740<br>_±_0035|0.722<br>_±_0013|0.629<br>_±_0005|**0.705**<br>_±_**0019**|**0.600**<br>_±_**0009**|0.712<br>_±_0091|0.627<br>_±_0047|**0.651**<br>_±_**0032**|0.578<br>_±_0023|0.659<br>_±_0013|**0.566**<br>_±_**0007**|
|ualit<br>168|.<br>1.079|.<br>0.818|.<br>0.819|.<br>0.691|**.**<br>**0.789**|**.**<br>**0.660**|.<br>0.957|.<br>0.737|**.**<br>**0.787**|.<br>0.648|.<br>0.794|**.**<br>**0.645**|
|ir q<br>|_±_0.108<br>1105|_±_0.046<br>0835|_±_0.007<br>002|_±_0.004<br>021|_±_**0.008**<br>**0860**|_±_**0.005**<br>**0685**|_±_0.067<br>08|_±_0.031<br>060|_±_**0.020**<br>080|_±_0.012<br>065|_±_0.025<br>**0854**|_±_**0.014**<br>**0676**|
|A<br>336|.<br>|.<br>|.9<br>|.7<br>|**.**<br>|**.**<br>|.99<br>|.7<br>|.7<br>|.9<br>|**.**<br>|**.**<br>|
||_±_0.052|_±_0.021|_±_0.018|_±_0.010|_±_**0.017**|_±_**0.006**|_±_0.111|_±_0.046|_±_0.022|_±_0.011|_±_**0.029**|_±_**0.010**|
||1538|0968|0945|0757|**0842**|**0686**|1228|0858|0939|0730|**0839**|**0680**|
|720|.<br>_±_0.419|.<br>_±_0.110|.<br>_±_0.030|.<br>_±_0.012|**.**<br>_±_**0.015**|**.**<br>_±_**0.008**|.<br>_±_0.048|.<br>_±_0.021|.<br>_±_0.064|.<br>_±_0.025|**.**<br>_±_**0.024**|**.**<br>_±_**0.013**|
|30|5.500<br>_±_0647|1.254<br>_±_0086|**0.940**<br>_±_**0055**|0.581<br>_±_0037|1.023<br>_±_**0034**|0.577<br>_±_**0007**|1.742<br>_±_0111|0.739<br>_±_0028|1.111<br>_±_0095|0.599<br>_±_0020|**0.985**<br>_±_**0018**|**0.564**<br>_±_**0005**|
|daq<br>60|.<br>5.226|.<br>1.236|**.**<br>**0.989**|.<br>**0.578**|**.**<br>1.207|**.**<br>0.617|.<br>2.304|.<br>0.790|.<br>1.280|.<br>0.630|**.**<br>**1.161**|**.**<br>**0.601**|
|Nas<br>|_±_0.424<br>|_±_0.032<br>|_±_**0.025**<br>|_±_**0.008**<br>|_±_0.044<br>|_±_0.009<br>|_±_0.062<br>|_±_0.010<br>|_±_0.023<br>|_±_0.004<br>|_±_**0.021**<br>|_±_**0.003**<br>|
|120|6.023|1.197|**1.166**|**0.615**|1.959|0.714|3.227|0.853|2.585|0.776|**1.869**|**0.697**|
||_±_0.382|_±_0.034|_±_**0.014**|_±_**0.003**|_±_0.062|_±_0.006|_±_0.236|_±_0.007|_±_0.374|_±_0.031|_±_**0.037**|_±_**0.003**|



16 

Published as a conference paper at ICLR 2022 

layer that can significantly increase the performance of a model in time series forecasting, applied to any arbitrarily chosen layers. 

## A.5 PERFORMANCE EVALUATION ON SIMILARITY METRICS FOR TIME SERIES 

We evaluate the forecasting performance of RevIN mainly on the mean squared error and the mean absolute error. Additionally, we use complementary metrics that measure the similarity between two sequences, dynamic time warping (DTW) and temporal distortion index (TDI) (Le Guen & Thome, 2019; Fr´ıas-Paredes et al., 2017). Table 8 shows that our approach significantly improves the baseline models across all datasets in terms of the DTW and TDI. Notably, RevIN exhibits outstanding performance by a large margin compared to the baselines for long prediction length. For example, when RevIN is added, the average DTW decreases from 38.348 to 15.240 for Informer, from 53.148 to 12.766 for N-BEATS, and from 20.498 to 11.080 for SCINet when the prediction length is 960 on ETTh2. There are a few cases where the proposed method predicts a less similar sequence than the baseline. However, the margin is minimal in terms of either DTW or TDI compared to the significant margin found when our method outperforms the baseline. These results demonstrate that adopting RevIN can generate a sequence more similar to the groundtruth than the baseline, especially showing better prediction accuracy on the longer sequences. 

Table 8: **Comparison results on similarity metrics for time series.** We assess the model forecasting results in terms of the shape and temporal errors using the DTW and the TDI, respectively (the lower, the better). The experiments are conducted for the four datasets, using the three baselines. We report the average value and standard deviation of five experiments. 

|Method|Infor|mer|**+ Re**|**vIN**|N-BE|ATS|**+ Re**|**vIN**|SCI|Net|**+ R**|**evIN**|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Metric|TDI|DTW|TDI|DTW|TDI|DTW|TDI|DTW|TDI|DTW|TDI|DTW|
|24|1.602|2.515|**1.207**|**2.206**|1.309|2.361|**1.031**|**1.830**|1.136|1.784|**0.969**|**1.672**|
||_±_0.093|_±_0.121|_±_**0.037**|_±_**0.097**|_±_0.147|_±_0.048|_±_**0.021**|_±_**0.012**|_±_0.113|_±_0.037|_±_**0.017**|_±_**0.007**|
|48|3.932|4.178|**2.762**|**3.401**|2.430|3.564|**1.592**|**2.745**|2.418|2.873|**1.456**|**2.508**|
||_±_0.796|_±_0.333|_±_**0.190**|_±_**0.063**|_±_0.386|_±_0.230|_±_**0.055**|_±_**0.012**|_±_0.297|_±_0.117|_±_**0.045**|_±_**0.012**|
|h1<br>168|31.569|10.384|**9.459**|**6.532**|19.369|8.937|**6.190**|**5.756**|4.913|5.344|**3.791**|**5.017**|
|TT<br>|_±_4.652|_±_0.420|_±_**1.173**|_±_**0.227**|_±_3.679|_±_0.490|_±_**1.033**|_±_**0.161**|_±_1.085|_±_0.170|_±_**0.075**|_±_**0.008**|
|E<br>|72.959|14.850|**45.215**|**11.605**|47.961|11.782|**14.302**|**8.532**|**6.120**|7.723|6.973|**7.319**|
|336|_±_6.769|_±_0.514|_±_**17.098**|_±_**1.321**|_±_8.500|_±_0.531|_±_**2.127**|_±_**0.162**|_±_**0.329**|_±_0.087|_±_0.292|_±_**0.025**|
|720|167.254|23.295|**98.648**|**18.483**|143.832|20.494|**26.265**|**12.383**|20.351|11.550|**11.337**|**10.511**|
||_±_13.008|_±_0.244|_±_**18.571**|_±_**0.346**|_±_28.984|_±_0.952|_±_**8.439**|_±_**0.458**|_±_3.588|_±_0.246|_±_**0.296**|_±_**0.056**|
|960|182.008|28.848|**128.152**|**22.018**|148.671|23.810|**40.774**|**15.107**|24.067|13.551|**14.148**|**12.508**|
||_±_16.076|_±_1.217|_±_**9.174**|_±_**0.204**|_±_48.669|_±_2.418|_±_**13.985**|_±_**0.744**|_±_3.383|_±_0.270|_±_**0.461**|_±_**0.063**|
|24|2.016|2.481|**1.528**|**1.601**|1.476|2.307|**1.128**|**1.409**|1.210|1.350|**1.088**|**1.250**|
||_±_0.152|_±_0.353|_±_**0.142**|_±_**0.029**|_±_0.230|_±_0.488|_±_**0.084**|_±_**0.007**|_±_0.128|_±_0.095|_±_**0.022**|_±_**0.015**|
|48|**4.462**|8.194|4.802|**2.806**|4.244|6.131|**2.529**|**2.207**|3.368|2.362|**2.374**|**1.906**|
||_±_**0.567**|_±_0.397|_±_0.342|_±_**0.081**|_±_0.470|_±_0.542|_±_**0.165**|_±_**0.010**|_±_0.380|_±_0.183|_±_**0.058**|_±_**0.019**|
|2<br>|**24.016**|32.496|24.516|**6.950**|42.270|28.487|**14.759**|**5.242**|12.307|4.899|**10.205**|**4.225**|
|TTh<br>168|_±_**3.355**|_±_1.563|_±_1.705|_±_**0.313**|_±_1.708|_±_0.642|_±_**1.149**|_±_**0.104**|_±_1.637|_±_0.229|_±_**0.533**|_±_**0.083**|
|E<br>336|74.168|29.549|**55.817**|**9.572**|95.645|30.837|**42.654**|**8.063**|28.823|7.447|**15.831**|**5.975**|
||_±_9.015|_±_2.453|_±_**3.180**|_±_**0.270**|_±_6.432|_±_1.115|_±_**3.450**|_±_**0.155**|_±_2.681|_±_0.350|_±_**0.141**|_±_**0.022**|
|720|129.440|35.908|**111.842**|**13.109**|185.321|47.461|**92.521**|**11.953**|142.118|16.428|**26.577**|**8.989**|
||_±_22.426|_±_2.230|_±_**18.634**|_±_**0.391**|_±_17.061|_±_6.122|_±_**33.126**|_±_**0.977**|_±_36.524|_±_2.748|_±_**0.987**|_±_**0.035**|
|960|177.336|38.348|**170.218**|**15.240**|281.720|53.148|**100.142**|**12.766**|218.477|20.498|**43.028**|**11.080**|
||_±_18.126|_±_1.665|_±_**14.187**|_±_**0.246**|_±_75.629|_±_9.408|_±_**29.742**|_±_**0.734**|_±_27.365|_±_1.979|_±_**2.007**|_±_**0.108**|
|24|**2.343**|1.730|2.478|**1.590**|**3.109**|2.062|3.368|**1.882**|2.618|1.194|**2.134**|**0.995**|
||_±_**0.130**|_±_0.098|_±_0.094|_±_**0.040**|_±_**0.135**|_±_0.178|_±_0.067|_±_**0.026**|_±_0.096|_±_0.023|_±_**0.034**|_±_**0.007**|
|48|4.818<br>|3.133<br>|**4.116**<br>|**2.457**<br>|5.223<br>|3.036<br>|**4.400**<br>|**2.426**<br>|4.176<br>|1.661<br>|**3.317**<br>|**1.470**<br>|
||_±_0.122<br>|_±_0.097<br>|_±_**0.093**<br>|_±_**0.038**<br>|_±_0.340<br>|_±_0.083<br>|_±_**0.084**<br>|_±_**0.061**<br>|_±_0.355<br>|_±_0.077<br>|_±_**0.045**<br>|_±_**0.015**<br>|
|1<br>|8.550|4.813|**5.837**|**3.586**|9.686|5.220|**6.803**|**3.803**|5.479|2.409|**4.782**|**2.180**|
|Tm<br>96|_±_0.671|_±_0.228|_±_**0.098**|_±_**0.085**|_±_1.050|_±_0.162|_±_**0.271**|_±_**0.090**|_±_0.349|_±_0.093|_±_**0.045**|_±_**0.009**|
|ET<br>288|32.918|11.054|**17.231**|**7.403**|42.809|10.706|**15.942**|**7.285**|22.650|5.365|**15.457**|**4.436**|
||_±_2.223|_±_0.341|_±_**0.759**|_±_**0.122**|_±_3.710|_±_0.513|_±_**0.531**|_±_**0.064**|_±_2.713|_±_0.072|_±_**0.273**|_±_**0.033**|
|672|80.546|16.365|**38.265**|**12.030**|111.531|16.601|**45.064**|**12.482**|149.483|13.980|**44.721**|**8.040**|
||_±_17.739|_±_0.749|_±_**6.209**|_±_**0.455**|_±_13.075|_±_0.649|_±_**5.369**|_±_**0.311**|_±_10.180|_±_0.350|_±_**1.867**|_±_**0.126**|
|1344|161.539<br>|23.822<br>|**77.844**<br>|**17.293**<br>|444.199<br>|69.125<br>|**161.725**<br>|**19.490**<br>|397.100<br>|27.319<br>|**98.890**<br>|**12.779**<br>|
||_±_16.808|_±_1.203|_±_**7.652**|_±_**0.606**|_±_59.765|_±_63.858|_±_**99.382**|_±_**3.115**|_±_39.675|_±_2.824|_±_**4.495**|_±_**0.156**|
|24|0.517|1.610|**0.339**|**1.234**|0.506|1.702|**0.384**|**1.368**|0.368|1.171|**0.281**|**1.058**|
||_±_0.007|_±_0.015|_±_**0.005**|_±_**0.006**|_±_0.004|_±_0.017|_±_**0.002**|_±_**0.010**|_±_0.017|_±_0.016|_±_**0.001**|_±_**0.053**|
|48|0.677|2.375|**0.383**|**1.806**|0.676|2.444|**0.446**|**1.972**|0.466|1.752|**0.318**|**1.527**|
||_±_0.029|_±_0.038|_±_**0.006**|_±_**0.012**|_±_0.025|_±_0.028|_±_**0.008**|_±_**0.011**|_±_0.034|_±_0.038|_±_**0.006**|_±_**0.004**|
||1.338|4.364|**0.785**|**3.709**|1.738|4.576|**0.839**|**3.828**|0.955|3.379|**0.730**|**3.122**|
|L<br>168|_±_0.017|_±_0.071|_±_**0.024**|_±_**0.054**|_±_0.166|_±_0.087|_±_**0.013**|_±_**0.016**|_±_0.077|_±_0.033|_±_**0.029**|_±_**0.026**|
|C|2276|6358|**1495**|**5640**|3555|6448|**1661**|**5702**|2336|5103|**1194**|**4591**|
|E<br>336|.|.|**.**|**.**|.|.|**.**|**.**|.|.|**.**|**.**|
||_±_0.046|_±_0.148|_±_**0.044**|_±_**0.126**|_±_0.562|_±_0.049|_±_**0.083**|_±_**0.038**|_±_0.209|_±_0.033|_±_**0.034**|_±_**0.012**|
|720|23.481|**16.561**|**22.117**|17.227|12.379|10.841|**5.583**|**9.239**|4.576|7.913|**2.830**|**7.162**|
||_±_15.963<br>|_±_**5.353**<br>|_±_**12.615**<br>|_±_3.790<br>|_±_4.196<br>|_±_1.204<br>|_±_**1.060**<br>|_±_**0.230**<br>|_±_0.806<br>|_±_0.102<br>|_±_**0.092**<br>|_±_**0.056**<br>|
||32.548|**21.065**|**28.328**|21.717|15.866|12.128|**9.198**|**11.140**|6.972|9.255|**4.502**|**8.560**|
|960|_±_18.405|_±_**3.649**|_±_**8.781**|_±_3.002|_±_3.309|_±_0.377|_±_**1.400**|_±_**0.347**|_±_0.678|_±_0.108|_±_**0.233**|_±_**0.064**|



17 

Published as a conference paper at ICLR 2022 

Table 9: **Forecasting performance of RevIN in comparison with existing dynamic normalization methods.** LSTNet<sup>_∗_</sup> indicates the model where the autoregressive linear bypass module of LSTNet is added to the baseline network. ES-RNN<sup>_∗_</sup> indicates the model where the exponential smoothing of ES-RNN is added to the baseline network. The experiments are conducted on the ETTh1, ETTh2, ETTm1, ECL, and the M4 datasets using N-BEATS as the baseline. The missing performances in the table are where the model fails to converge. 

|M|ethods|N-BE|ATS|+ LST|Net<sup>_∗_</sup>|+ ES|RNN<sup>_∗_</sup>|**+ R**|**evIN**|
|---|---|---|---|---|---|---|---|---|---|
||Metric|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
||24<br>48|0.478<br>_±_0.022<br>0.536<br>_±_0.060|0.505<br>_±_0.012<br>0.542<br>_±_0.041|0.462<br>_±_0.047<br>0.587<br>_±_0.063|0.497<br>_±_0.035<br>0.576<br>_±_0.043|0.547<br>_±_0.031<br>0.662<br>_±_0.027|0.515<br>_±_0.021<br>0.567<br>_±_0.012|**0.330**<br>_±_**0.006**<br>**0.372**<br>_±_**0.001**|**0.373**<br>_±_**0.004**<br>**0.400**<br>_±_**0.002**|
|h1|168|1.005|0.782|1.031|0.795|0.698|0.600|**0.466**|**0.452**|
|T||_±_0.146|_±_0.064|_±_0.099|_±_0.054|_±_0.044|_±_0.018|_±_**0.030**|_±_**0.014**|
|ET|336|0.932|0.743|0.964|0.760|0.768|0.640|**0.515**|**0.483**|
|||_±_0.079|_±_0.042|_±_0.047|_±_0.023|_±_0.041|_±_0.022|_±_**0.013**|_±_**0.008**|
||720<br>960|1.389<br>_±_0.230<br>1.383<br>|0.926<br>_±_0.066<br>0.932<br>|1.549<br>_±_0.061<br>1.293<br>|0.994<br>_±_0.022<br>0.897<br>|0.966<br>_±_0.084<br>-|0.742<br>_±_0.022<br>-|**0.576**<br>_±_**0.035**<br>**0.678**<br>|**0.534**<br>_±_**0.018**<br>**0.575**<br>|
|||_±_0.380|_±_0.120|_±_0.059|_±_0.026|||_±_**0.019**|_±_**0.009**|
|||0.403|0.472|0.394|0.485|0.614|0.522|**0.192**|**0.276**|
||24<br>48|_±_0.185<br>1.330<br>|_±_0.101<br>0.918<br>|_±_0.099<br>1.261<br>|_±_0.068<br>0.907<br>|_±_0.010<br>0.654<br>|_±_0.004<br>0.543<br>|_±_**0.003**<br>**0.254**<br>|_±_**0.002**<br>**0.320**<br>|
|||_±_0.240|_±_0.073|_±_0.214|_±_0.075|_±_0.009|_±_0.007|_±_**0.011**|_±_**0.008**|
|h2|168|7.174|2.329|7.053|2.290|0.962|0.696|**0.410**|**0.418**|
|T||_±_0.449|_±_0.049|_±_0.428|_±_0.095|_±_0.129|_±_0.054|_±_**0.010**|_±_**0.005**|
|ET||4.859|1.863|5.070|1.914|1.204|0.789|**0.449**|**0.447**|
||336<br>|_±_0.268<br>5.656|_±_0.043<br>2.012|_±_0.336<br>6.311|_±_0.083<br>2.049|_±_0.158<br>1.284|_±_0.050<br>0.810|_±_**0.011**<br>**0.496**|_±_**0.006**<br>**0.482**|
||720<br>960|_±_1.053<br>6.408<br>_±_2.039|_±_0.186<br>2.077<br>_±_0.242|_±_2.057<br>5.627<br>_±_1.670|_±_0.225<br>1.965<br>_±_0.314|_±_0.145<br>1.338<br>_±_0.535|_±_0.033<br>0.809<br>_±_0.127|_±_**0.008**<br>**0.471**<br>_±_**0.015**|_±_**0.002**<br>**0.481**<br>_±_**0.008**|
|||0.443|0.437|0.412|0.426|0.564|0.477|**0.403**|**0.392**|
||24<br>48|_±_0.043<br>0.453|_±_0.035<br>0.472|_±_0.026<br>0.420|_±_0.024<br>0.455|_±_0.015<br>0.615|_±_0.009<br>0.531|_±_**0.006**<br>**0.328**|_±_**0.005**<br>**0.371**|
|||_±_0.034|_±_0.018|_±_0.028|_±_0.018|_±_0.093|_±_0.049|_±_**0.010**|_±_**0.007**|
|1||0603|0581|0572|0553|0668|0555|**0.379**|**0.406**|
|Tm|96|.<br>_±_0.051|.<br>_±_0.027|.<br>_±_0.039|.<br>_±_0.030|.<br>_±_0.031|.<br>_±_0.015|_±_**0.011**|_±_**0.007**|
|ET||<br>0.849|<br>0.702|<br>0.789|<br>0.677|<br>0.795|<br>0.623|<br>**0.451**|<br>**0.445**|
||288<br>672|_±_0.095<br>0.860|_±_0.051<br>0.726|_±_0.069<br>0.958|_±_0.039<br>0.758|_±_0.070<br>1.657|_±_0.032<br>0.890|_±_**0.016**<br>**0.555**|_±_**0.008**<br>**0.511**|
|||_±_0.057<br>|_±_0.026<br>|_±_0.183<br>|_±_0.076<br>|_±_1.116|_±_0.290|_±_**0.011**<br>|_±_**0.008**<br>|
||1344|14.613<br>_±_26.108|1.948<br>_±_1.655|5.592<br>_±_7.032|1.497<br>_±_0.671|-|-|**0.631**<br>_±_**0.061**|**0.556**<br>_±_**0.020**|
||24|0.279|0.372|0.198|0.310|0.242|0.332|**0.176**|**0.285**|
||48|_±_0.007<br>0.309<br>|_±_0.003<br>0.388<br>|_±_0.005<br>0.245<br>|_±_0.003<br>0.343<br>|_±_0.005<br>0.275<br>|_±_0.006<br>0.352<br>|_±_**0.002**<br>**0.194**<br>|_±_**0.001**<br>**0.301**<br>|
|||_±_0.007|_±_0.004|_±_0.009|_±_0.007|_±_0.007|_±_0.006|_±_**0.001**|_±_**0.001**|
|||0.333|0.410|0.285|0.375|||**0.218**|**0.320**|
|L|168|_±_0.016|_±_0.012|_±_0.006|_±_0.004|-|-|_±_**0.002**|_±_**0.001**|
|EC||0326|0406|0304|0393|||**0241**|**0337**|
||336|.<br>_±_0.004|.<br>_±_0.001|.<br>_±_0.019|.<br>_±_0.013|-|-|**.**<br>_±_**0.005**|**.**<br>_±_**0.002**|
|||<br>0.420|<br>0.467|<br>0.378|<br>0.443|||<br>**0.303**|<br>**0.383**|
||720|_±_0.094|_±_0.058|_±_0.083|_±_0.056|-|-|_±_**0.012**|_±_**0.011**|
|||0.399|0.455|0.360|0.433|||**0.325**|**0.398**|
||960|_±_0.022|_±_0.017|_±_0.037|_±_0.027|-|-|_±_**0.019**|_±_**0.015**|
|||0.224|0.207|0.223|0.206|0.223|0.204|**0.208**|**0.197**|
|M4|average|_±_0.004|_±_0.003|_±_0.004|_±_0.003|_±_0.001|_±_0.001|_±_**0.001**|_±_**0.001**|



18 

Published as a conference paper at ICLR 2022 



<!-- Start of picture text -->
(a) model input (b) normalized input  (c) model output (d) denormalized output<br>ESRNN*<br>LSTNet*<br>RevIN<br>Density<br>Density<br>Density<br><!-- End of picture text -->

Figure 8: **Effect of RevIN on distribution discrepancy on training and test data compared to existing dynamic normalization methods.** We compare RevIN with LSTNet<sup>_∗_</sup> , which adds the autoregressive linear bypass module of LSTNet to the baseline and ES-RNN<sup>_∗_</sup> , which adds the exponential smoothing of ES-RNN to the baseline. The analysis is conducted on the ETTh2 dataset with a prediction length of 960 using N-BEATS as the baseline. From left to right, the columns compare the training and test data distributions of each step of the sequential process in each method. 

## A.6 COMPARISON WITH EXISTING DYNAMIC NORMALIZATION METHODS 

We compare RevIN with the dynamic normalization methods proposed in LSTNet (Lai et al., 2017) and ES-RNN (Smyl, 2020). Similar to adding RevIN to the baseline model, we add the autoregressive linear bypass module of LSTNet and the modified Holt-Winters exponential smoothing of ESRNN to the baseline model, respectively. As shown in Table 9, RevIN consistently achieves the best performance among the normalization methods adopted on N-BEATS by a significant margin. When we replace RevIN with the other normalization methods, the autoregressive linear bypass module of LSTNet (LSTNet<sup>_∗_</sup> ) also consistently reduces the prediction error compared to the baseline. However, the performance improvement is smaller than our method. For example, when the prediction length is 960 on the ETTh2 dataset, N-BEATS shows an average error of 6.408, and LSTNet<sup>_∗_</sup> reduces the error to 5.627. But this is still much worse than RevIN, which reduces the error to 0.471. Similarly, when the prediction length is 1344 on the ETTm1 dataset, the baseline shows an average error of 14.613 and LSTNet<sup>_∗_</sup> largely decreases the error to 5.592, but RevIN more significantly decreases the error to 0.631. In the case of ES-RNN<sup>_∗_</sup> , the training of the model is unstable, failing to converge for several cases. Also, ES-RNN<sup>_∗_</sup> often degrades the baseline performance, e.g., when the prediction length is either 24 or 48 on the ETTh1 and ETTm1 datasets. It significantly reduces the error for long prediction length much better than LSTNet<sup>_∗_</sup> , but still worse than RevIN, for example, when the prediction length is 960 on the ETTh2 dataset. 

Additionally, we further analyze the data distributions of the dynamic normalization methods on the ETTh2 dataset, as shown in Fig. 8. We compare the training and test data distributions of each step of the sequential process in each method. 

**ES-RNN**<sup>_∗_</sup> shows the distributions of (a) the original model input, (b) the normalized input where the level and seasonality are removed by its proposed method, (c) the model prediction output, (d) the denormalized output where the level and seasonality is multiplied back to the original distribution. 

**LSTNet**<sup>_∗_</sup> shows the distributions of (a) the original model input, (b) the same original input since the method does not transform the input data before feeding them to the main prediction model, the model prediction output (c) before, and (d) after adding the output of the autoregressive network. 

**RevIN** shows the distributions of (a) the original model input, (b) the normalized input by RevIN, (c) the model prediction output, and (d) the denormalized output by RevIN. 

19 

Published as a conference paper at ICLR 2022 

In Fig. 8(a), the original training and test data show a discrepancy in their distributions. Also, they have several peaks, not being centered on the mean. This implies that sequences in the data will have different mean values. In Fig. 8(b), both RevIN and ES-RNN<sup>_∗_</sup> transform data distributions into mean-centered distributions. Particularly, ES-RNN<sup>_∗_</sup> extremely concentrates the distribution on the mean, with only a small variance. Both RevIN and ES-RNN<sup>_∗_</sup> result in data sequences with similar statistics, thereby alleviating the distribution shift problem in the input data. This leads to outstanding performance on long prediction sequences, in contrast to LSTNet<sup>_∗_</sup> . LSTNet<sup>_∗_</sup> cannot resolve the distribution discrepancy because it does not have any module that can change the input statistics. Also, in LSTNet<sup>_∗_</sup> , the distributions of the model output (Fig. 8(c)) completely differ from the input data distributions (Fig. 8(b)). The method cannot make the input and output distribution to be consistent. In addition, its proposed autoregressive model barely affects the model output distributions, as shown in Fig. 8(c-d); there is almost no difference between the model output and the final output distributions. 

Most importantly, the distributions of the final output (Fig. 8(d)) significantly differ from the original data (Fig. 8(a)) in LSTNet<sup>_∗_</sup> . Similarly, although ES-RNN<sup>_∗_</sup> alleviates the distribution discrepancy in the input data, it fails to return the model output (Fig. 8(d)) back to the original distribution (Fig. 8(a)), especially with the test data. These results imply that LSTNet<sup>_∗_</sup> and ES-RNN<sup>_∗_</sup> fail to learn the appropriate data distribution, and this could be the main reason why their prediction error is higher than RevIN. On the other hand, in RevIN, the distributions of the final output (Fig. 8(d)) are successfully returned to the original distributions (Fig. 8(a)). Also, with RevIN, the input and output of the model maintain consistent distributions, as well as the training and test data be overlapped. As a result, RevIN shows superior performance than the other dynamic normalization methods. 

Table 10: **Additional results on the comparison with classical and state-of-the-art normalization methods in Table 3 in the main manuscript.** The mean squared error is measured on the ETTh1, ETTh2, ETTm1, and ECL datasets. _Ty_ indicates the prediction length. **RevBN** is the modified version of RevIN, where the input normalization is replaced by batch normalization. 

|Dataset|_Ty_|Min-max<br>norm|z-score<br>norm|Layer<br>norm|DAIN|Batch<br>norm|**RevBN**|Instance<br>norm|**RevIN**<br>**(Ours)**|
|---|---|---|---|---|---|---|---|---|---|
||24|0.885|0.959|0.472|0.652|0.451|0.574|0.989|**0.322**|
||48|1.010|0.898|0.741|1.389|0.557|0.649|0.999|**0.373**|
|h1|168|1.074|0.953|0.871|0.996|0.851|0.717|0.946|**0.515**|
|TT|336|1.083|0.969|0.827|0.979|0.828|0.775|1.078|**0.509**|
|E|720|1.226|0.978|1.184|1.014|0.916|0.705|0.986|**0.567**|
||960|1.224|1.043|1.303|1.032|1.691|0.779|1.090|**0.697**|
||24|2.659|3.152|0.478|1.437|0.336|0.550|2.976|**0.192**|
||48|2.772|3.232|1.335|1.476|1.018|1.058|3.175|**0.244**|
|h2|168|2.987|3.329|4.092|1.982|6.206|0.729|3.240|**0.419**|
|TT|336|2.914|3.288|4.207|2.631|5.422|0.546|3.186|**0.452**|
|E|720|3.092|3.031|5.822|2.954|7.062|1.552|3.079|**0.492**|
||960|3.308|3.087|5.204|2.802|7.755|2.148|3.145|**0.465**|
||24|0.981|0.930|0.515|0.431|0.477|0.680|0.926|**0.395**|
|1|48|0.998|1.005|0.555|0.747|0.489|0.531|1.005|**0.337**|
|m|96|1.035|1.016|0.502|0.672|0.505|0.601|1.021|**0.388**|
|TT|288|0.974|0.988|0.773|0.877|0.677|0.656|1.056|**0.444**|
|E|672|1.157|1.029|0.795|1.043|0.620|0.670|1.157|**0.549**|
||1344|1.320|1.274|2.488|1.348|1.147|0.991|1.329|**0.602**|
||24|0.370|0.313|0.294|0.348|0.301|0.304|0.307|**0.174**|
||48|0.334|0.326|0.310|0.387|0.319|0.331|0.313|**0.194**|
|L|168|0.374|0.335|0.343|0.347|0.320|0.327|0.333|**0.220**|
|EC|336|0.378|0.338|0.358|0.357|0.337|0.369|0.335|**0.244**|
||720|0.746|0.417|0.371|0.366|0.374|0.440|0.378|**0.294**|
||960|0.387|0.377|0.379|0.381|0.422|0.414|0.386|**0.329**|



20 

Published as a conference paper at ICLR 2022 

## A.7 ADDITIONAL RESULTS ON COMPARISON WITH EXISTING NORMALIZATION METHODS 

This section provides complete results that compare with existing normalization methods, which are not included in the main manuscript due to lack of space. The forecasting error of RevIN and existing normalization methods are evaluated on the ETTh1, ETTh2, ETTm1, and ECL datasets in Table 10. RevIN consistently outperforms the other normalization methods across all datasets. Interestingly, when the denormalization step is added to batch normalization (RevBN) as RevIN, the model better forecasts long sequences than batch normalization (Batch norm), e.g., when the prediction length is 960. The denormalization step of RevIN plays a critical role in improving model performance by restoring the model prediction to the original distribution. However, a denormalization step cannot be added to DAIN since it has the Hadamard multiplication operation in the last step, which is not reversible when the input and prediction sequence lengths are different. These differences could be the reason for its worse performance compared to RevIN despite that DAIN requires higher computational costs and a larger amount of model parameters. 

## A.8 ALGORITHM OF REVERSIBLE INSTANCE NORMALIZATION 

Algorithm 1 summarizes the procedure of the proposed approach. Reversible instance normalization consists of the normalization (line 3-4) and denormalization layers (line 6-7). It transforms the input and output of a model using identical statistics. As RevIN is generally applicable, _gθ_ in Algorithm 1 (line 5) can be any arbitrary deep neural network. 

## **Algorithm 1:** RevIN, applied to input _x_ and output _y_ of a module in the model. 

**Input :** _Tx ∈_ R<sup>1</sup> , the input sequence length; _x_<sup>(</sup> _kt_<sup>_i_)</sup><sup>_∈_R1, the</sup><sup>_k_-th feature at time step</sup><sup>_t_</sup> of the _i_ -th item in a mini-batch; _γ, β ∈_ R<sup>_K_</sup> , learnable parameters for RevIN; _gθ_ , a module in the model parameterized by _θ_ . **Output:** _γ, β_ , _θ_ . <u>1</u> **1** _Compute µT ← Tx_ � _Tj_ =1 _x_<sup>_x_(</sup> _kj_<sup>_i_)</sup> _▷_ instance mean <u>1</u> **2** _Compute σT_<sup>2</sup><sup>_←_</sup> _Tx_ � _Tj_ =1 _x_<sup>(</sup><sup>_x_(</sup> _kj_<sup>_i_)</sup><sup>_−µT_)2</sup> _▷_ instance variance _<u>kt</u>_<sup>_−µT_</sup> **3** _Normalize x_ ˆ<sup>(</sup> _kt_<sup>_i_)</sup><sup>_←x_</sup> _~~√~~_<sup>(</sup><sup>_i_</sup> _σ_<sup>)</sup> _T_<sup>2+</sup><sup>_ϵ_</sup> _▷_ normalization **4** _Transform x_ ˆ _kt_<sup>(</sup><sup>_i_)</sup><sup>_←γk ·_ˆ</sup><sup>_x_(</sup> _kt_<sup>_i_)+</sup><sup>_βk≡_</sup><sup>**RevIN**n</sup> _γ,β_<sup>(</sup><sup>_x_</sup> _kt_<sup>(</sup><sup>_i_))</sup> _▷_ scale and shift **5** _Predict y_ ˜ _← gθ_ (ˆ _x_ ) _▷_ forward propagation _<u>kt</u>_<sup>_−βk_</sup> **6** _Retransform y_ ˆ _kt_<sup>(</sup><sup>_i_)</sup><sup>_←_</sup><sup>_<u>y</u>_˜(</sup><sup>_i_)</sup> _γk ▷_ reverse scale and shift **7** _Denormalize y_ ˆ _kt_<sup>(</sup><sup>_i_)</sup><sup>_←µT_+ ˆ</sup><sup>_y_</sup> _kt_<sup>(</sup><sup>_i_)</sup> <u>�</u> _σT_<sup>2+</sup><sup>_ϵ ≡_</sup><sup>**RevIN**dn</sup> _γ,β_<sup>(˜</sup><sup>_y_</sup> _kt_<sup>(</sup><sup>_i_))</sup> _▷_ denormalization 

## A.9 THEORETICAL JUSTIFICATION OF REVIN AGAINST DISTRIBUTION SHIFT 

Let _x_<sup>(</sup><sup>_i_)</sup> _∈_ R<sup>_K×Tx_</sup> denote a time series comprising _K_ variables of length _Tx_ . Consider a univariate case where _K_ = 1 without the loss of generality. Then, _x_<sup>(</sup><sup>_i_)</sup> _∈_ R<sup>_Tx_</sup> denotes the _i_ -th time series in the data. Consider training and test data, whose distributions are denoted as _Ptra_ and _Ptst_ , respectively. We consider a distribution shift problem where the training and test data have different distributions (Du et al., 2021). That is, 



In our work, we consider the distribution shift problem in terms of the mean and the variance. Then, the distribution shift problem can be redefined as 



Let’s assume that the given training and test data suffer from the distribution shift problem in terms of the mean and variance. In order to solve this problem, RevIN first normalizes a training sample 

21 

Published as a conference paper at ICLR 2022 

_x_<sup>(</sup><sup>_i_)</sup> _∼ Ptra_ . Mathematically, a training sample is transformed as 



By the laws of expectation and variance, 



By symmetry, this also holds for _x_<sup>(</sup><sup>_i_)</sup> _∼ Ptst_ , for all _i_ . Therefore, the mean and variance of the training and test data distributions become identical. Thus, by definition (Eq. 5), the distribution shift problem for the training and test data is solved by the first step of RevIN. 

Given the normalized time-series data, the forecasting model parameterized by _θ_ , _fθ_ : R<sup>_Tx_</sup> _→_ R<sup>_Ty_</sup> , predicts the corresponding subsequent future values, _y_ ˜ = _fθ_ (ˆ _x_ ). Then, the denormalization step of RevIN returns the non-stationary information of the original data, i.e., E[ _x_<sup>(</sup><sup>_i_)</sup> ] and Var[ _x_<sup>(</sup><sup>_i_)</sup> ] in Eq. 6, to the prediction output so that model does not have to reconstruct them from the normalized input. In summary, the model prediction _y_ ˜<sup>(</sup><sup>_i_)</sup> is denormalized as 



By the laws of expectation and variance, the mean and variance of _y_ ˆ<sup>(</sup><sup>_i_)</sup> can be expressed as 



The denormalization step allows the mean and variance of the final prediction values to be expressed as the difference from the input statistics. Here, since the input data _x_<sup>(</sup><sup>_i_)</sup> and the groundtruth future values are consecutive sequences, we can assume that their difference in the mean and variance can be expressed as Eq. 9 as well. Under this assumption, the model adopting RevIN only needs to capture the difference from the input statistics, ∆ and _λ_ , to accurately predict the statistics of the future values. In conclusion, through the normalization and denormalization steps of RevIN, a model can focus on learning the offset from the input distribution to the output distribution by removing their common non-stationary statistics. 

## A.10 CALCULATION DETAILS ON FEATURE DIVERGENCE 

This section explains how the feature divergence is computed in Section 4.2.3. Following the previous work (Pan et al., 2018), we calculate the average feature divergence between the training and test data using symmetric KL divergence, assuming that the output features of the model layer will follow a Gaussian distribution with mean _µ_ and variance _σ_<sup>2</sup> . Then, the equation for the feature divergence of the _k_ -th feature _fk_ can be expressed as 



## A.11 ADDITIONAL EXPERIMENTAL DETAILS 

We train and evaluate the models using the following seeds: 12, 22, 32, 42, and 52. The experiments using N-BEATS and Informer as the baseline are performed on NVIDIA TITAN RTX, and the experiments using SCINet are conducted on NVIDIA TITAN Xp. Following the multivariate timeseries forecasting settings of the previous studies (Zhou et al., 2021; Liu et al., 2021), we select input sequence length from two days (2d), 4d, 7d, 14d, 15d, 20d, 28d, 30d for the hourly datasets, i.e., the ETTh1, ETTh2, and ECL datasets, and from half day, 1d, 3.5d, 7d for the ETTm1 dataset. Particularly, we set the ratio of input length to prediction length to be smaller from 2.0 to 0.35 as the prediction length becomes longer. In the case of SCINet, when the prediction length is 720, we set its input length to be 736, unlike the other baselines. It is because the original paper of the method requires its input sequence length to meet a specific condition. To be specific, the input length needs to be a multiple of 32 due to its hierarchical architecture (Liu et al., 2021). 

22 

Published as a conference paper at ICLR 2022 

## A.12 REPRODUCTION DETAILS FOR BASELINE MODELS 

This section describes the implementation details of the baselines, Informer, N-BEATS, and SCINet. Note that we compare each baseline model and RevIN using the same hyperparameters except for the presence of RevIN. We exactly follow the experimental settings of the baseline models by using their official code to conduct experiments, except for N-BEATS that have no officially released code. We reproduce the model and set hyperparameters as stated in the original N-BEATS paper. 

**Informer.** We use the official open-source code of Informer<sup>6</sup> . If provided, we follow the same hyperparameter settings in training the network, e.g., hidden dimension of the network or the learning rate. For the ECL dataset, detailed hyperparameter settings are not officially provided in Informer; we use the same settings with the ETTh1 dataset. 

**N-BEATS.** We reproduce N-BEATS using the PyTorch framework (Paszke et al., 2019). We follow the same hyperparameter settings of the N-BEATS-I model in the original paper. We train N-BEATS to minimize the mean squared error between the model prediction and groundtruth values. For a fair comparison with the other baselines, we use a single model instead of using the ensemble method originally proposed in the N-BEATS paper. Since N-BEATS is a model tailored to univariate timeseries forecasting, we flatten each multivariate input sequence into a univariate sequence having a single dimension for the feature before feeding it to the model. Additionally, we conduct a grid search for the learning rate of N-BEATS with the range of [1e-5, 1e-3] and train the model using the weight decay with the factor of 0.001 to stabilize training. 

**SCINet.** We follow the experimental settings provided in the official code<sup>7</sup> of SCINet. 

## A.13 ADDITIONAL QUALITATIVE RESULTS 

In Fig. 9, we illustrate the additional results comparing the predictions of RevIN and the baselines. Overall, the prediction results of the baselines are inaccurately scaled and shifted. However, RevIN shows remarkable performance, consistently improving the baselines to predict more precise results. With RevIN, the forecasting results are better aligned with the groundtruth. 

## A.14 COMPLETE QUANTITATIVE RESULTS 

Table 11 provides the standard deviation values of five independent experiments to compare long sequence forecasting performance in Table 2 in the main manuscript. Table 12 shows the complete results of the comparison of the forecasting errors between the baselines and RevIN in Table 1 in the main manuscript. They include the standard deviation of five runs and the performance reported in the original papers of the baselines. RevIN shows significant performance improvement compared to the state-of-the-art forecasting baselines. 

Table 11: **Standard deviation values of the five runs for the comparison of long sequence forecasting performance in Table 2 in the main manuscript.** 

|Prediction length|4|8|1|68|33|6|7|20|9|60|
|---|---|---|---|---|---|---|---|---|---|---|
|Metric|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
|Informer<br>**+ RevIN**|0.056<br>0.030|0.035<br>0.008|0.052<br>0.051|0.024<br>0.030|0.085<br>0.073|0.031<br>0.026|0.037<br>0.067|0.024<br>0.033|0.034<br>0.041|0.022<br>0.022|
|N-BEATS|0.042|0.030|0.056|0.027|0.081|0.037|0.072|0.029|0.067|0.030|
|**+ RevIN**|0.006|0.003|0.014|0.007|0.011|0.006|0.041|0.020|0.027|0.012|
|SCINet<br>**+ RevIN**|0.008<br>0.002|0.007<br>0.001|0.063<br>0.013|0.042<br>0.007|0.115<br>0.022|0.064<br>0.010|0.033<br>0.028|0.022<br>0.017|0.049<br>0.015|0.029<br>0.008|



> 6https://github.com/zhouhaoyi/Informer2020 

> 7https://github.com/cure-lab/SCINet 

23 

Published as a conference paper at ICLR 2022 



<!-- Start of picture text -->
ETTh<br>ETTh<br>ETTm1<br>ECL<br>1<br>2<br><!-- End of picture text -->



Figure 9: **Additional multivariate time-series forecasting results comparing RevIN and stateof-the-art baselines.** The analysis is conducted on the ETTh1, ETTh2, ETTm1, and ECL datasets. We set the prediction length as 168 for the hour datasets and 288 for the ETTm1 dataset. 

24 

Published as a conference paper at ICLR 2022 

|SCINet<br>SCINet+**RevIN**<br>E<br>MSE<br>MAE<br>MSE<br>MAE|8<br>0.338<br>_±_0.012<br>0.373<br>_±_0.009<br>**0.308**<br>_±_**0.003**<br>**0.347**<br>_±_**0.002**<br>8<br>0.436<br>_±_0.025<br>0.459<br>_±_0.021<br>**0.365**<br>_±_**0.005**<br>**0.389**<br>_±_**0.003**<br>1<br>0.459<br>_±_0.015<br>0.461<br>_±_0.013<br>**0.406**<br>_±_**0.003**<br>**0.416**<br>_±_**0.003**<br>4<br>0.527<br>_±_0.010<br>0.513<br>_±_0.006<br>**0.467**<br>_±_**0.005**<br>**0.471**<br>_±_**0.003**<br>2<br>0.596<br>_±_0.015<br>0.571<br>_±_0.013<br>**0.507**<br>_±_**0.006**<br>**0.505**<br>_±_**0.004**<br>0.604<br>_±_0.017<br>0.574<br>_±_0.014<br>**0.545**<br>_±_**0.010**<br>**0.526**<br>_±_**0.005**|1<br>0.199<br>_±_0.026<br>0.295<br>_±_0.027<br>**0.180**<br>_±_**0.004**<br>**0.263**<br>_±_**0.002**<br>1<br>0.350<br>_±_0.025<br>0.422<br>_±_0.027<br>**0.231**<br>_±_**0.006**<br>**0.302**<br>_±_**0.006**<br>9<br>0.559<br>_±_0.044<br>0.518<br>_±_0.025<br>**0.337**<br>_±_**0.007**<br>**0.378**<br>_±_**0.003**<br>8<br>0.664<br>_±_0.073<br>0.583<br>_±_0.030<br>**0.357**<br>_±_**0.003**<br>**0.403**<br>_±_**0.002**<br>1<br>1.546<br>_±_0.378<br>0.944<br>_±_0.141<br>**0.411**<br>_±_**0.003**<br>**0.445**<br>_±_**0.002**<br>1.862<br>_±_0.153<br>1.066<br>_±_0.055<br>**0.438**<br>_±_**0.007**<br>**0.462**<br>_±_**0.004**|6<br>0.130<br>_±_0.003<br>0.231<br>_±_0.003<br>**0.106**<br>_±_**0.002**<br>**0.196**<br>_±_**0.001**<br>1<br>0.155<br>_±_0.004<br>0.262<br>_±_0.004<br>**0.135**<br>_±_**0.003**<br>**0.222**<br>_±_**0.002**<br>1<br>0.195<br>_±_0.012<br>0.291<br>_±_0.013<br>**0.162**<br>_±_**0.001**<br>**0.247**<br>_±_**0.001**<br>2<br>0.361<br>_±_0.008<br>0.419<br>_±_0.004<br>**0.265**<br>_±_**0.003**<br>**0.321**<br>_±_**0.002**<br>7<br>1.020<br>_±_0.040<br>0.756<br>_±_0.025<br>**0.357**<br>_±_**0.004**<br>**0.380**<br>_±_**0.002**<br>1.841<br>_±_0.242<br>1.044<br>_±_0.100<br>**0.412**<br>_±_**0.008**<br>**0.422**<br>_±_**0.003**|0.138<br>_±_0.004<br>0.246<br>_±_0.005<br>**0.112**<br>_±_**0.001**<br>**0.207**<br>_±_**0.001**<br>0.163<br>_±_0.007<br>0.265<br>_±_0.007<br>**0.126**<br>_±_**0.001**<br>**0.222**<br>_±_**0.001**<br>0.177<br>_±_0.003<br>0.281<br>_±_0.005<br>**0.153**<br>_±_**0.003**<br>**0.249**<br>_±_**0.002**<br>0.202<br>_±_0.004<br>0.308<br>_±_0.004<br>**0.162**<br>_±_**0.001**<br>**0.262**<br>_±_**0.001**<br>0.234<br>_±_0.006<br>0.333<br>_±_0.004<br>**0.183**<br>_±_**0.003**<br>**0.281**<br>_±_**0.002**<br>0.235<br>_±_0.011<br>0.330<br>_±_0.008<br>**0.200**<br>_±_**0.003**<br>**0.292**<br>_±_**0.002**|
|---|---|---|---|---|
|INet_†_<br>MA|0.34<br>0.38<br>0.49<br>0.49<br>0.58<br>_·_|0.27<br>0.34<br>0.50<br>0.60<br>0.76<br>_·_|0.22<br>0.26<br>0.29<br>0.46<br>0.52<br>_·_|_·_<br>_·_<br>_·_<br>_·_<br>_·_<br>_·_|
|SC<br>MSE|0.311<br>0.364<br>0.497<br>0.491<br>0.612<br>_·_|0.183<br>0.259<br>0.528<br>0.648<br>1.074<br>_·_|0.127<br>0.150<br>0.190<br>0.417<br>0.554<br>_·_|_·_<br>_·_<br>_·_<br>_·_<br>_·_<br>_·_|
|N-BEATS<br>N-BEATS+**RevIN**<br>MSE<br>MAE<br>MSE<br>MAE|.478<br>0.022<br>0.505<br>_±_0.012<br>**0.330**<br>_±_**0.006**<br>**0.373**<br>_±_**0.004**<br>.536<br>0.060<br>0.542<br>_±_0.041<br>**0.372**<br>_±_**0.001**<br>**0.400**<br>_±_**0.002**<br>.005<br>0.146<br>0.782<br>_±_0.064<br>**0.466**<br>_±_**0.030**<br>**0.452**<br>_±_**0.014**<br>.932<br>0.079<br>0.743<br>_±_0.042<br>**0.515**<br>_±_**0.013**<br>**0.483**<br>_±_**0.008**<br>.389<br>0.230<br>0.926<br>_±_0.066<br>**0.576**<br>_±_**0.035**<br>**0.534**<br>_±_**0.018**<br>.383<br>0.380<br>0.932<br>_±_0.120<br>**0.678**<br>_±_**0.019**<br>**0.575**<br>_±_**0.009**|.403<br>0.185<br>0.472<br>_±_0.101<br>**0.192**<br>_±_**0.003**<br>**0.276**<br>_±_**0.002**<br>.330<br>0.240<br>0.918<br>_±_0.073<br>**0.254**<br>_±_**0.011**<br>**0.320**<br>_±_**0.008**<br>.174<br>0.449<br>2.329<br>_±_0.049<br>**0.410**<br>_±_**0.010**<br>**0.418**<br>_±_**0.005**<br>.859<br>0.268<br>1.863<br>_±_0.043<br>**0.449**<br>_±_**0.011**<br>**0.447**<br>_±_**0.006**<br>.656<br>1.053<br>2.012<br>_±_0.186<br>**0.496**<br>_±_**0.008**<br>**0.482**<br>_±_**0.002**<br>.408<br>2.039<br>2.077<br>_±_0.242<br>**0.471**<br>_±_**0.015**<br>**0.481**<br>_±_**0.008**|.443<br>0.043<br>0.437<br>_±_0.035<br>**0.403**<br>_±_**0.006**<br>**0.392**<br>_±_**0.005**<br>.453<br>0.034<br>0.472<br>_±_0.018<br>**0.328**<br>_±_**0.010**<br>**0.371**<br>_±_**0.007**<br>.603<br>0.051<br>0.581<br>_±_0.027<br>**0.379**<br>_±_**0.011**<br>**0.406**<br>_±_**0.007**<br>.849<br>0.095<br>0.702<br>_±_0.051<br>**0.451**<br>_±_**0.016**<br>**0.445**<br>_±_**0.008**<br>.860<br>0.057<br>0.726<br>_±_0.026<br>**0.555**<br>_±_**0.011**<br>**0.511**<br>_±_**0.008**<br>4.613<br>26.108<br>1.948<br>_±_1.655<br>**0.631**<br>_±_**0.061**<br>**0.556**<br>_±_**0.020**|.279<br>0.007<br>0.372<br>_±_0.003<br>**0.176**<br>_±_**0.002**<br>**0.285**<br>_±_**0.001**<br>.309<br>0.007<br>0.388<br>_±_0.004<br>**0.194**<br>_±_**0.001**<br>**0.301**<br>_±_**0.001**<br>.333<br>0.016<br>0.410<br>_±_0.012<br>**0.218**<br>_±_**0.002**<br>**0.320**<br>_±_**0.001**<br>.326<br>0.004<br>0.406<br>_±_0.001<br>**0.241**<br>_±_**0.005**<br>**0.337**<br>_±_**0.002**<br>.420<br>0.094<br>0.467<br>_±_0.058<br>**0.303**<br>_±_**0.012**<br>**0.383**<br>_±_**0.011**<br>.399<br>0.022<br>0.455<br>_±_0.017<br>**0.325**<br>_±_**0.019**<br>**0.398**<br>_±_**0.015**|
|Informer<br>Informer +**RevIN**<br><br>MSE<br>MAE<br>MSE<br>MAE<br>|0.550<br>_±_0.041<br>0.536<br>_±_0.025<br>**0.504**<br>_±_**0.049**<br>**0.472**<br>_±_**0.025**<br>0<br>_±_ <br><br>0.772<br>_±_0.122<br>0.668<br>_±_0.055<br>**0.646**<br>_±_**0.039**<br>**0.547**<br>_±_**0.015**<br>0<br>_±_ <br><br>1.138<br>_±_0.096<br>0.853<br>_±_0.045<br>**0.655**<br>_±_**0.055**<br>**0.561**<br>_±_**0.024**<br>1<br>_±_ <br><br>1.278<br>_±_0.129<br>0.909<br>_±_0.058<br>**1.058**<br>_±_**0.119**<br>**0.758**<br>_±_**0.059**<br>0<br>_±_ <br><br>1.357<br>_±_0.056<br>0.945<br>_±_0.009<br>**0.926**<br>_±_**0.057**<br>**0.717**<br>_±_**0.036**<br>1<br>_±_ <br>1.470<br>_±_0.124<br>0.990<br>_±_0.052<br>**0.902**<br>_±_**0.033**<br>**0.715**<br>_±_**0.025**<br>1<br>_±_|0.450<br>_±_0.099<br>0.520<br>_±_0.071<br>**0.238**<br>_±_**0.010**<br>**0.325**<br>_±_**0.006**<br>0<br>_±_ <br><br>2.171<br>_±_0.094<br>1.200<br>_±_0.048<br>**0.361**<br>_±_**0.023**<br>**0.404**<br>_±_**0.014**<br>1<br>_±_ <br><br>8.157<br>_±_0.631<br>2.558<br>_±_0.113<br>**0.859**<br>_±_**0.072**<br>**0.649**<br>_±_**0.026**<br>7<br>_±_ <br><br>4.746<br>_±_0.455<br>1.844<br>_±_0.102<br>**0.890**<br>_±_**0.057**<br>**0.673**<br>_±_**0.023**<br>4<br>_±_ <br><br>3.190<br>_±_0.326<br>1.529<br>_±_0.085<br>**0.576**<br>_±_**0.044**<br>**0.546**<br>_±_**0.025**<br>5<br>_±_ <br>2.972<br>_±_0.183<br>1.441<br>_±_0.035<br>**0.600**<br>_±_**0.033**<br>**0.570**<br>_±_**0.018**<br>6<br>_±_|0.330<br>_±_0.021<br>0.382<br>_±_0.017<br>**0.309**<br>_±_**0.020**<br>**0.352**<br>_±_**0.010**<br>0<br>_±_ <br><br>0.499<br>_±_0.024<br>0.486<br>_±_0.012<br>**0.390**<br>_±_**0.008**<br>**0.391**<br>_±_**0.006**<br>0<br>_±_ <br><br>0.605<br>_±_0.033<br>0.554<br>_±_0.027<br>**0.405**<br>_±_**0.013**<br>**0.411**<br>_±_**0.006**<br>0<br>_±_ <br><br>0.906<br>_±_0.039<br>0.738<br>_±_0.028<br>**0.563**<br>_±_**0.024**<br>**0.502**<br>_±_**0.015**<br>0<br>_±_ <br><br>0.943<br>_±_0.062<br>0.760<br>_±_0.034<br>**0.663**<br>_±_**0.082**<br>**0.550**<br>_±_**0.031**<br>0<br>_±_ <br>1.095<br>_±_0.065<br>0.823<br>_±_0.040<br>**0.824**<br>_±_**0.039**<br>**0.632**<br>_±_**0.019**<br>1<br>_±_|0.250<br>_±_0.005<br>0.358<br>_±_0.005<br>**0.148**<br>_±_**0.001**<br>**0.257**<br>_±_**0.001**<br>0<br>_±_ <br><br>0.300<br>_±_0.010<br>0.386<br>_±_0.005<br>**0.171**<br>_±_**0.004**<br>**0.279**<br>_±_**0.003**<br>0<br>_±_ <br><br>0.345<br>_±_0.012<br>0.423<br>_±_0.010<br>**0.261**<br>_±_**0.010**<br>**0.354**<br>_±_**0.007**<br>0<br>_±_ <br><br>0.429<br>_±_0.041<br>0.473<br>_±_0.023<br>**0.356**<br>_±_**0.026**<br>**0.414**<br>_±_**0.015**<br>0<br>_±_ <br><br>0.851<br>_±_0.088<br>0.719<br>_±_0.072<br>**0.834**<br>_±_**0.122**<br>**0.700**<br>_±_**0.076**<br>0<br>_±_ <br><br>0.930<br>_±_0.075<br>0.750<br>_±_0.042<br>**0.894**<br>_±_**0.047**<br>**0.741**<br>_±_**0.031**<br>0<br>_±_|
|rmer_†_<br>MAE|0.549<br>0.625<br>0.752<br>0.873<br>0.896<br>_·_|0.665<br>1.001<br>1.515<br>1.340<br>1.473<br>_·_|0.369<br>0.503<br>0.614<br>0.786<br>0.926<br>_·_|_·_<br>0.393<br>0.424<br>0.431<br>0.443<br>0.548|
|Info<br>MSE|0.577<br>0.685<br>0.931<br>1.128<br>1.215<br>_·_|0.720<br>1.457<br>3.489<br>2.723<br>3.467<br>_·_|0.323<br>0.494<br>0.678<br>1.056<br>1.192<br>_·_|_·_<br>0.344<br>0.368<br>0.381<br>0.406<br>0.460|
|Methods<br>Metric|ETTh1<br>24<br>48<br>168<br>336<br>720<br>960|ETTh2<br>24<br>48<br>168<br>336<br>720<br>960|ETTm1<br>24<br>48<br>96<br>288<br>672<br>1344|ECL<br>24<br>48<br>168<br>336<br>720<br>960|



25 

