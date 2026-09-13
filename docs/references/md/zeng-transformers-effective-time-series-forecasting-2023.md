---
# --- bibliographic record ---
entry_type: misc
title: "Are Transformers Effective for Time Series Forecasting?"
authors:
  - "Ailing Zeng"
  - "Muxi Chen"
  - "Lei Zhang"
  - "Qiang Xu"
year: 2022
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: ""
url: "https://10.1609/aaai.v37i9.26317"

# --- archive record ---
source_pdf: zeng-transformers-effective-time-series-forecasting-2023.pdf
source_sha256: 97abddd1821cc72942c8d7ddde7e99466bb91f1bddc37c2b54e0e97be7b5be1b
pdf_pages: 15
converted: 2026-09-13
record_source: arxiv
key_insight: "Peer-reviewed evidence that a one-layer linear model matches or beats deep architectures on standard benchmarks, strengthening the case for parsimony when accuracy ties."
first_page: "Are Transformers Effective for Time Series Forecasting? Ailing Zeng1*, Muxi Chen1*, Lei Zhang2, Qiang Xu1 1The Chinese University of Hong Kong 2International Digital Economy Academy (IDEA) {alzeng, mx"
---
## **Are Transformers Effective for Time Series Forecasting?** 

Ailing Zeng<sup>1*</sup> , Muxi Chen<sup>1*</sup> , Lei Zhang<sup>2</sup> , Qiang Xu<sup>1</sup> 

1The Chinese University of Hong Kong 

2International Digital Economy Academy (IDEA) 

{alzeng, mxchen21, qxu}@cse.cuhk.edu.hk 

{leizhang}@idea.edu.cn 

## **Abstract** 

_Recently, there has been a surge of Transformer-based solutions for the long-term time series forecasting (LTSF) task. Despite the growing performance over the past few years,_ we question the validity of this line of research in this work _. Specifically, Transformers is arguably the most successful solution to extract the semantic correlations among the elements in a long sequence. However, in time series modeling, we are to extract the temporal relations in_ an ordered set of continuous points _. While employing positional encoding and using tokens to embed sub-series in Transformers facilitate preserving some ordering information, the nature of the_ permutation-invariant _self-attention mechanism inevitably results in temporal information loss._ 

_To validate our claim, we introduce a set of embarrassingly simple one-layer linear models named_ LTSF-Linear _for comparison. Experimental results on nine real-life datasets show that_ LTSF-Linear _surprisingly outperforms existing sophisticated Transformer-based LTSF models in all cases, and often by a large margin. Moreover, we conduct comprehensive empirical studies to explore the impacts of various design elements of LTSF models on their temporal relation extraction capability. We hope this surprising finding opens up new research directions for the LTSF task. We also advocate revisiting the validity of Transformer-based solutions for other time series analysis tasks (e.g., anomaly detection) in the future. Code is available at: https://github.com/cure-lab/LTSFLinear._ 

## **1. Introduction** 

Time series are ubiquitous in today’s data-driven world. Given historical data, time series forecasting (TSF) is a long-standing task that has a wide range of applications, including but not limited to traffic flow estimation, en- 

*Equal contribution 

ergy management, and financial investment. Over the past several decades, TSF solutions have undergone a progression from traditional statistical methods (e.g., ARIMA [1]) and machine learning techniques (e.g., GBRT [11]) to deep learning-based solutions, e.g., Recurrent Neural Networks [15] and Temporal Convolutional Networks [3, 17]. 

Transformer [26] is arguably the most successful sequence modeling architecture, demonstrating unparalleled performances in various applications, such as natural language processing (NLP) [7], speech recognition [8], and computer vision [19, 29]. Recently, there has also been a surge of Transformer-based solutions for time series analysis, as surveyed in [27]. Most notable models, which focus on the less explored and challenging long-term time series forecasting (LTSF) problem, include LogTrans [16] (NeurIPS 2019), Informer [30] (AAAI 2021 Best paper), Autoformer [28] (NeurIPS 2021), Pyraformer [18] (ICLR 2022 Oral), Triformer [5] (IJCAI 2022) and the recent FEDformer [31] (ICML 2022). 

The main working power of Transformers is from its multi-head self-attention mechanism, which has a remarkable capability of extracting semantic correlations among elements in a long sequence (e.g., words in texts or 2D patches in images). However, self-attention is _permutationinvariant_ and “anti-order” to some extent. While using various types of positional encoding techniques can preserve some ordering information, it is still inevitable to have temporal information loss after applying self-attention on top of them. This is usually not a serious concern for semanticrich applications such as NLP, e.g., the semantic meaning of a sentence is largely preserved even if we reorder some words in it. However, when analyzing time series data, there is usually a lack of semantics in the numerical data itself, and we are mainly interested in modeling the temporal changes among _a continuous set of points_ . That is, the order itself plays the most crucial role. Consequently, we pose the following intriguing question: **_Are Transformers really effective for long-term time series forecasting?_** 

Moreover, while existing Transformer-based LTSF so- 

1 

lutions have demonstrated considerable prediction accuracy improvements over traditional methods, in their experiments, all the compared (non-Transformer) baselines perform autoregressive or iterated multi-step (IMS) forecasting [1, 2, 22, 24], which are known to suffer from significant error accumulation effects for the LTSF problem. Therefore, in this work, we challenge Transformer-based LTSF solutions with direct multi-step (DMS) forecasting strategies to validate their real performance. 

Not all time series are predictable, let alone long-term forecasting (e.g., for chaotic systems). We hypothesize that long-term forecasting is only feasible for those time series with a relatively clear trend and periodicity. As linear models can already extract such information, we introduce a set of embarrassingly simple models named **_LTSF-Linear_** as a new baseline for comparison. _LTSF-Linear_ regresses historical time series with a one-layer linear model to forecast future time series directly. We conduct extensive experiments on nine widely-used benchmark datasets that cover various real-life applications: traffic, energy, economics, weather, and disease predictions. Surprisingly, our results show that _LTSF-Linear_ outperforms existing complex Transformerbased models _in all cases, and often by a large margin (20% ∼ 50%)_ . Moreover, we find that, in contrast to the claims in existing Transformers, most of them fail to extract temporal relations from long sequences, i.e., the forecasting errors are not reduced (sometimes even increased) with the increase of look-back window sizes. Finally, we conduct various ablation studies on existing Transformer-based TSF solutions to study the impact of various design elements in them. 

To sum up, the contributions of this work include: 

- To the best of our knowledge, this is the first work to challenge the effectiveness of the booming Transformers for the long-term time series forecasting task. 

- To validate our claims, we introduce a set of embarrassingly simple one-layer linear models, named _LTSF-Linear_ , and compare them with existing Transformer-based LTSF solutions on nine benchmarks. _LTSF-Linear_ can be a new baseline for the LTSF problem. 

- We conduct comprehensive empirical studies on various aspects of existing Transformer-based solutions, including the capability of modeling long inputs, the sensitivity to time series order, the impact of positional encoding and sub-series embedding, and efficiency comparisons. Our findings would benefit future research in this area. 

With the above, we conclude that _the temporal modeling capabilities of Transformers for time series are exaggerated, at least for the existing LTSF benchmarks_ . At the same time, while _LTSF-Linear_ achieves a better prediction 

accuracy compared to existing works, it merely serves as a simple baseline for future research on the challenging longterm TSF problem. With our findings, we also advocate revisiting the validity of Transformer-based solutions for other time series analysis tasks in the future. 

## **2. Preliminaries: TSF Problem Formulation** 

For time series containing _C_ variates, given historical data _X_ = _{X_ 1<sup>_t, ..., X_</sup> _C_<sup>_t}_</sup> _t_<sup>_L_</sup> =1<sup>,wherein</sup><sup>_L_isthelook-back</sup> window size and _Xi_<sup>_t_is the value of the</sup><sup>_ith_variate at the</sup><sup>_tth_</sup> time step. The time series forecasting task is to predict the values _X_<sup>ˆ</sup> = _{X_<sup>ˆ</sup> 1<sup>_t, ...,X_ˆ</sup> _C_<sup>_t}L_</sup> _t_ =<sup>+</sup> _L_<sup>_T_</sup> +1<sup>at the</sup><sup>_T_future time steps.</sup> When _T >_ 1, iterated multi-step (IMS) forecasting [23] learns a single-step forecaster and iteratively applies it to obtain multi-step predictions. Alternatively, direct multistep (DMS) forecasting [4] directly optimizes the multi-step forecasting objective at once. 

Compared to DMS forecasting results, IMS predictions have smaller variance thanks to the autoregressive estimation procedure, but they inevitably suffer from error accumulation effects. Consequently, IMS forecasting is preferable when there is a highly-accurate single-step forecaster, and _T_ is relatively small. In contrast, DMS forecasting generates more accurate predictions when it is hard to obtain an unbiased single-step forecasting model, or _T_ is large. 

## **3. Transformer-Based LTSF Solutions** 

Transformer-based models [26] have achieved unparalleled performances in many long-standing AI tasks in natural language processing and computer vision fields, thanks to the effectiveness of the multi-head self-attention mechanism. This has also triggered lots of research interest in Transformer-based time series modeling techniques [20, 27]. In particular, a large amount of research works are dedicated to the LTSF task (e.g., [16, 18, 28, 30, 31]). Considering the ability to capture long-range dependencies with Transformer models, most of them focus on the lessexplored long-term forecasting problem ( _T ≫_ 1)<sup>1</sup> . 

When applying the vanilla Transformer model to the LTSF problem, it has some limitations, including the quadratic time/memory complexity with the original selfattention scheme and error accumulation caused by the autoregressive decoder design. Informer [30] addresses these issues and proposes a novel Transformer architecture with reduced complexity and a DMS forecasting strategy. Later, more Transformer variants introduce various time series features into their models for performance or efficiency improvements [18,28,31]. We summarize the design elements of existing Transformer-based LTSF solutions as follows (see Figure 1). 

> 1Due to page limit, we leave the discussion of non-Transformer forecasting solutions in the Appendix. 

2 



<!-- Start of picture text -->
LogSparse and convolutional  Iterated Multi-Step<br>Channel projection self-attention @ LogTrans (IMS) @ LogTrans<br>Normalization<br>ProbSparse and distilling  Direct Multi-Step<br>self-attention @ Informer (DMS) @ Informer<br>Fixed position<br>Timestamp Series auto-correlation with  DMS with auto-correlation and<br>preparation decomposition @ Autoformer decomposition @ Autoformer<br>Local timestamp<br>Multi-resolution pyramidal      DMS along spatio-temporal<br>Seasonal-trend  attention @ Pyraformer dimension @ Pyraformer<br>decomposition Global timestamp Frequency enhanced block with  DMS with frequency attention<br>decomposition @ FEDformer and decomposition@ FEDformer<br>(a) Preprocessing (b) Embedding (c) Encoder (d) Decoder<br>Inutp Output<br><!-- End of picture text -->

Figure 1. The pipeline of existing Transformer-based TSF solutions. In (a) and (b), the solid boxes are essential operations, and the dotted boxes are applied optionally. (c) and (d) are distinct for different methods [16, 18, 28, 30, 31]. 

**Time series decomposition:** For data preprocessing, normalization with zero-mean is common in TSF. Besides, Autoformer [28] first applies seasonal-trend decomposition behind each neural block, which is a standard method in time series analysis to make raw data more predictable [6, 13]. Specifically, they use a moving average kernel on the input sequence to extract the _trend-cyclical_ component of the time series. The difference between the original sequence and the trend component is regarded as the _seasonal_ component. On top of the decomposition scheme of Autoformer, FEDformer [31] further proposes the mixture of experts’ strategies to mix the trend components extracted by moving average kernels with various kernel sizes. 

**Input embedding strategies:** The self-attention layer in the Transformer architecture cannot preserve the positional information of the time series. However, local positional information, i.e. the ordering of time series, is important. Besides, global temporal information, such as hierarchical timestamps (week, month, year) and agnostic timestamps (holidays and events), is also informative [30]. To enhance the temporal context of time-series inputs, a practical design in the SOTA Transformer-based methods is injecting several embeddings, like a fixed positional encoding, a channel projection embedding, and learnable temporal embeddings into the input sequence. Moreover, temporal embeddings with a temporal convolution layer [16] or learnable timestamps [28] are introduced. 

**Self-attention schemes:** Transformers rely on the selfattention mechanism to extract the semantic dependencies between paired elements. Motivated by reducing the _O_ � _L_<sup>2�</sup> time and memory complexity of the vanilla Transformer, recent works propose two strategies for efficiency. On the one hand, LogTrans and Pyraformer explicitly introduce a sparsity bias into the self-attention scheme. Specifically, LogTrans uses a Logsparse mask to reduce the computational complexity to _O_ ( _LlogL_ ) while Pyraformer adopts pyramidal attention that captures hierarchically multi-scale temporal dependencies with an _O_ ( _L_ ) time and memory complexity. On the other hand, Informer and FEDformer use the low-rank property in the self-attention matrix. Informer proposes a ProbSparse self- 

attention mechanism and a self-attention distilling operation to decrease the complexity to _O_ ( _LlogL_ ), and FEDformer designs a Fourier enhanced block and a wavelet enhanced block with random selection to obtain _O_ ( _L_ ) complexity. Lastly, Autoformer designs a series-wise auto-correlation mechanism to replace the original self-attention layer. 

**Decoders:** The vanilla Transformer decoder outputs sequences in an autoregressive manner, resulting in a slow inference speed and error accumulation effects, especially for long-term predictions. Informer designs a generative-style decoder for DMS forecasting. Other Transformer variants employ similar DMS strategies. For instance, Pyraformer uses a fully-connected layer concatenating Spatio-temporal axes as the decoder. Autoformer sums up two refined decomposed features from trend-cyclical components and the stacked auto-correlation mechanism for seasonal components to get the final prediction. FEDformer also uses a decomposition scheme with the proposed frequency attention block to decode the final results. 

The premise of Transformer models is the semantic correlations between paired elements, while the self-attention mechanism itself is permutation-invariant, and its capability of modeling temporal relations largely depends on positional encodings associated with input tokens. Considering the raw numerical data in time series (e.g., stock prices or electricity values), there are hardly any point-wise semantic correlations between them. In time series modeling, we are mainly interested in the temporal relations among a continuous set of points, and the order of these elements instead of the paired relationship plays the most crucial role. While employing positional encoding and using tokens to embed sub-series facilitate preserving some ordering information, the nature of the permutation-invariant self-attention mechanism inevitably results in temporal information loss. Due to the above observations, we are interested in revisiting the effectiveness of Transformer-based LTSF solutions. 

## **4. An Embarrassingly Simple Baseline** 

In the experiments of existing Transformer-based LTSF solutions ( _T ≫_ 1), all the compared (non-Transformer) 

3 

baselines are IMS forecasting techniques, which are known to suffer from significant error accumulation effects. We hypothesize that the performance improvements in these works are largely due to the DMS strategy used in them. 



<!-- Start of picture text -->
Future 𝑇 timesteps<br>History 𝐿 timesteps<br><!-- End of picture text -->

Figure 2. Illustration of the basic linear model. 

To validate this hypothesis, we present the simplest DMS model via a temporal linear layer, named _LTSF-Linear_ , as a baseline for comparison. The basic formulation of _LTSFLinear_ directly regresses historical time series for future prediction via a weighted sum operation (as illustrated in Figure 2). The mathematical expression is _X_<sup>ˆ</sup> _i_ = _WXi_ , where _W ∈_ R<sup>_T ×L_</sup> is a linear layer along the temporal axis. _X_ ˆ _i_ and _Xi_ are the prediction and input for each _ith_ variate. Note that _LTSF-Linear_ shares weights across different variates and does not model any spatial correlations. 

_LTSF-Linear_ is a set of linear models. _Vanilla Linear_ is a one-layer linear model. To handle time series across different domains (e.g., finance, traffic, and energy domains), we further introduce two variants with two preprocessing methods, named _DLinear_ and _NLinear_ . 

- Specifically, _DLinear_ is a combination of a _Decomposition_ scheme used in Autoformer and FEDformer with linear layers. It first decomposes a raw data input into a trend component by a moving average kernel and a remainder (seasonal) component. Then, two one-layer linear layers are applied to each component, and we sum up the two features to get the final prediction. By explicitly handling trend, _DLinear_ enhances the performance of a vanilla linear when there is a clear trend in the data. 

- Meanwhile, to boost the performance of _LTSF-Linear_ when there is a distribution shift in the dataset, _NLinear_ first subtracts the input by the last value of the sequence. Then, the input goes through a linear layer, and the subtracted part is added back before making the final prediction. The subtraction and addition in _NLinear_ are a simple normalization for the input sequence. 

## **5. Experiments** 

### **5.1. Experimental Settings** 

**Dataset.** We conduct extensive experiments on nine widely-used real-world datasets, including ETT (Electricity Transformer Temperature) [30] (ETTh1, ETTh2, ETTm1, ETTm2), Traffic, Electricity, Weather, ILI, ExchangeRate [15]. All of them are multivariate time series. We leave _data descriptions_ in the Appendix. 

**Evaluation metric.** Following previous works [28, 30, 31], we use Mean Squared Error (MSE) and Mean Absolute Error (MAE) as the core metrics to compare performance. **Compared methods.** We include five recent Transformer-based methods: FEDformer [31], Autoformer [28], Informer [30], Pyraformer [18], and LogTrans [16]. Besides, we include a naive DMS method: Closest Repeat ( _Repeat_ ), which repeats the last value in the look-back window, as another simple baseline. Since there are two variants of FEDformer, we compare the one with better accuracy (FEDformer-f via Fourier transform). 

### **5.2. Comparison with Transformers** 

**Quantitative results.** In Table 2, we extensively evaluate all mentioned Transformers on nine benchmarks, following the experimental setting of previous work [28, 30, 31]. Surprisingly, the performance of _LTSF-Linear_ surpasses the SOTA FEDformer in most cases by 20% _∼_ 50% improvements on the _multivariate forecasting_ , where _LTSFLinear_ even does not model correlations among variates. For different time series benchmarks, _NLinear_ and _DLinear_ show the superiority to handle the distribution shift and trend-seasonality features. We also provide results for _univariate forecasting_ of ETT datasets in the Appendix, where _LTSF-Linear_ still consistently outperforms Transformerbased LTSF solutions by a large margin. 

FEDformer achieves competitive forecasting accuracy on ETTh1. This because FEDformer employs classical time series analysis techniques such as frequency processing, which brings in time series inductive bias and benefits the ability of temporal feature extraction. In summary, these results reveal that existing complex Transformer-based LTSF solutions are not seemingly effective on the existing nine benchmarks while _LTSF-Linear_ can be a powerful baseline. 

Another interesting observation is that even though the naive _Repeat_ method shows worse results when predicting long-term seasonal data (e.g., Electricity and Traffic), it surprisingly outperforms all Transformer-based methods on Exchange-Rate (around 45%). This is mainly caused by the wrong prediction of trends in Transformer-based solutions, which may overfit toward sudden change noises in the training data, resulting in significant accuracy degradation (see Figure 3(b)). Instead, _Repeat_ does not have the bias. 

**Qualitative results.** As shown in Figure 3, we plot 

4 

|||Datase<br>Variat|ts<br><br>es|ETTh1&<br>7|ETTh2<br>|ETT|m1&ET<br>7|Tm2<br>i|Traffic<br>862|Electric<br>321|ity<br>E|xchange<br>8|-Rate|Weath<br>21|er<br>I<br>|LI<br>7||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|||Timest<br>|eps<br>|17,<br>|420<br>||69,680<br>||17,544<br>|26,30<br>|4<br>|7,588<br>||52,69<br>|6<br>9<br><br>|66<br>||||
|||Granula|rity|1h|ur||5min||1hour|1hou||1day||10mi|1w|eek||||
|||||Table<br>|1. The s<br>|tatisti<br>|cs of the<br>|nine p<br>|opular d<br>|atasets<br>|for the<br>|LTSF<br>|proble<br>|m.<br>||||||
|Methods|IMP.|Line|ar*|NLi|near*|DLi|near*|FED|former|Autof|ormer|Info|rmer|Pyraf|ormer*|Log|Trans|_Rep_|_eat_*|
|Metric|MSE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
|ity<br>96|27.40%|**0.140**|**0.237**|0.141|**0.237**|**0.140**|**0.237**|0.193|0.308|0.201|0.317|0.274|0.368|0.386|0.449|0.258|0.357|1.588|0.946|
|ric<br>192|23.88%|**0.153**|0.250|0.154|**0.248**|**0.153**|0.249|0.201|0.315|0.222|0.334|0.296|0.386|0.386|0.443|0.266|0.368|1.595|0.950|
|lect<br>336|21.02%|**0.169**|0.268|0.171|**0.265**|**0.169**|0.267|0.214|0.329|0.231|0.338|0.300|0.394|0.378|0.443|0.280|0.380|1.617|0.961|
|E<br>720|17.47%|**0.203**|0.301|0.210|**0.297**|**0.203**|0.301|0.246|0.355|0.254|0.361|0.373|0.439|0.376|0.445|0.283|0.376|1.647|0.975|
|ge<br>96|45.27%|0.082|0.207|0.089|0.208|**0.081**|0.203|0.148|0.278|0.197|0.323|0.847|0.752|0.376|1.105|0.968|0.812|**0.081**|**0.196**|
|han<br>192|42.06%|0.167|0.304|0.180|0.300|**0.157**|0.293|0.271|0.380|0.300|0.369|1.204|0.895|1.748|1.151|1.040|0.851|0.167|**0.289**|
|xc<br>336|33.69%|0.328|0.432|0.331|0.415|**0.305**|0.414|0.460|0.500|0.509|0.524|1.672|1.036|1.874|1.172|1.659|1.081|**0.305**|**0.396**|
|E<br>720|46.19%|0.964|0.750|1.033|0.780|**0.643**|**0.601**|1.195|0.841|1.447|0.941|2.478|1.310|1.943|1.206|1.941|1.127|0.823|0.681|
|ic<br>96|30.15%|**0.410**|0.282|**0.410**|**0.279**|**0.410**|0.282|0.587|0.366|0.613|0.388|0.719|0.391|2.085|0.468|0.684|0.384|2.723|1.079|
|ffi<br>192|29.96%|**0.423**|0.287|**0.423**|**0.284**|**0.423**|0.287|0.604|0.373|0.616|0.382|0.696|0.379|0.867|0.467|0.685|0.390|2.756|1.087|
|Trai<br>336|29.95%|0.436|0.295|**0.435**|**0.290**|0.436|0.296|0.621|0.383|0.622|0.337|0.777|0.420|0.869|0.469|0.734|0.408|2.791|1.095|
|i<br>720|25.87%|0.466|0.315|**0.464**|**0.307**|0.466|0.315|0.626|0.382|0.660|0.408|0.864|0.472|0.881|0.473|0.717|0.396|2.811|1.097|
|er<br>96|18.89%|**0.176**|0.236|0.182|**0.232**|**0.176**|0.237|0.217|0.296|0.266|0.336|0.300|0.384|0.896|0.556|0.458|0.490|0.259|0.254|
|ath<br>192|21.01%|**0.218**|0.276|0.225|**0.269**|0.220|0.282|0.276|0.336|0.307|0.367|0.598|0.544|0.622|0.624|0.658|0.589|0.309|0.292|
|We<br>336|22.71%|**0.262**|0.312|0.271|**0.301**|0.265|0.319|0.339|0.380|0.359|0.395|0.578|0.523|0.739|0.753|0.797|0.652|0.377|0.338|
|720|19.85%|0.326|0.365|0.338|**0.348**|**0.323**|0.362|0.403|0.428|0.419|0.428|1.059|0.741|1.004|0.934|0.869|0.675|0.465|0.394|
|24|47.86%|1.947|0.985|**1.683**|**0.858**|2.215|1.081|3.228|1.260|3.483|1.287|5.764|1.677|1.420|2.012|4.480|1.444|6.587|1.701|
|LI<br>36|36.43%|2.182|1.036|**1.703**|**0.859**|1.963|0.963|2.679|1.080|3.103|1.148|4.755|1.467|7.394|2.031|4.799|1.467|7.130|1.884|
|I<br>48|34.43%|2.256|1.060|**1.719**|**0.884**|2.130|1.024|2.622|1.078|2.669|1.085|4.763|1.469|7.551|2.057|4.800|1.468|6.575|1.798|
|60|34.33%|2.390|1.104|**1.819**|**0.917**|2.368|1.096|2.857|1.157|2.770|1.125|5.264|1.564|7.662|2.100|5.278|1.560|5.893|1.677|
|1<br>96|0.80%|0.375|0.397|**0.374**|**0.394**|0.375|0.399|0.376|0.419|0.449|0.459|0.865|0.713|0.664|0.612|0.878|0.740|1.295|0.713|
|Th<br>192|3.57%|0.418|0.429|0.408|**0.415**|**0.405**|0.416|0.420|0.448|0.500|0.482|1.008|0.792|0.790|0.681|1.037|0.824|1.325|0.733|
|ET<br>336|6.54%|0.479|0.476|**0.429**|**0.427**|0.439|0.443|0.459|0.465|0.521|0.496|1.107|0.809|0.891|0.738|1.238|0.932|1.323|0.744|
|720|13.04%|0.624|0.592|**0.440**|**0.453**|0.472|0.490|0.506|0.507|0.514|0.512|1.181|0.865|0.963|0.782|1.135|0.852|1.339|0.756|
|2<br>96|19.94%|0.288|0.352|**0.277**|**0.338**|0.289|0.353|0.346|0.388|0.358|0.397|3.755|1.525|0.645|0.597|2.116|1.197|0.432|0.422|
|Th<br>192|19.81%|0.377|0.413|**0.344**|**0.381**|0.383|0.418|0.429|0.439|0.456|0.452|5.602|1.931|0.788|0.683|4.315|1.635|0.534|0.473|
|ET<br>336|25.93%|0.452|0.461|**0.357**|**0.400**|0.448|0.465|0.496|0.487|0.482|0.486|4.721|1.835|0.907|0.747|1.124|1.604|0.591|0.508|
|720|14.25%|0.698|0.595|**0.394**|**0.436**|0.605|0.551|0.463|0.474|0.515|0.511|3.647|1.625|0.963|0.783|3.188|1.540|0.588|0.517|
|1<br>96|21.10%|0.308|0.352|0.306|0.348|**0.299**|**0.343**|0.379|0.419|0.505|0.475|0.672|0.571|0.543|0.510|0.600|0.546|1.214|0.665|
|Tm<br>192|21.36%|0.340|0.369|0.349|0.375|**0.335**|**0.365**|0.426|0.441|0.553|0.496|0.795|0.669|0.557|0.537|0.837|0.700|1.261|0.690|
|ET<br>336|17.07%|0.376|0.393|0.375|0.388|**0.369**|**0.386**|0.445|0.459|0.621|0.537|1.212|0.871|0.754|0.655|1.124|0.832|1.283|0.707|
|720|21.73%|0.440|0.435|0.433|0.422|**0.425**|**0.421**|0.543|0.490|0.671|0.561|1.166|0.823|0.908|0.724|1.153|0.820|1.319|0.729|
|2<br>96|17.73%|0.168|0.262|**0.167**|**0.255**|**0.167**|0.260|0.203|0.287|0.255|0.339|0.365|0.453|0.435|0.507|0.768|0.642|0.266|0.328|
|Tm<br>192|17.84%|0.232|0.308|**0.221**|**0.293**|0.224|0.303|0.269|0.328|0.281|0.340|0.533|0.563|0.730|0.673|0.989|0.757|0.340|0.371|
|ET<br>336|15.69%|0.320|0.373|**0.274**|**0.327**|0.281|0.342|0.325|0.366|0.339|0.372|1.363|0.887|1.201|0.845|1.334|0.872|0.412|0.410|
|720|12.58%|0.413|0.435|**0.368**|**0.384**|0.397|0.421|0.421|0.415|0.433|0.432|3.379|1.338|3.625|1.451|3.048|1.328|0.521|0.465|
|- Methods|* are impleme|nted by us; Ot|her results|are from FED|former [31].|||||||||||||||



Table 2. Multivariate long-term forecasting errors in terms of MSE and MAE, the lower the better. Among them, ILI dataset is with forecasting horizon _T ∈{_ 24 _,_ 36 _,_ 48 _,_ 60 _}_ . For the others, _T ∈{_ 96 _,_ 192 _,_ 336 _,_ 720 _}_ . _Repeat_ repeats the last value in the look-back window. The **best results** are highlighted in **bold** and the best results of Transformers are highlighted with a <u>underline.</u> Accordingly, IMP. is the best result of linear models compared to the results of Transformer-based solutions. 

the prediction results on three selected time series datasets with Transformer-based solutions and _LTSF-Linear_ : Electricity (Sequence 1951, Variate 36), Exchange-Rate (Sequence 676, Variate 3), and ETTh2 ( Sequence 1241, Variate 2), where these datasets have different temporal patterns. When the input length is 96 steps, and the output horizon is 336 steps, Transformers [28, 30, 31] fail to capture the scale and bias of the future data on Electricity and ETTh2. Moreover, they can hardly predict a proper trend on aperiodic data such as Exchange-Rate. These phenomena further indicate the inadequacy of existing Transformer-based solutions for the LTSF task. 

### **5.3. More Analyses on LTSF-Transformers** 

**_Can existing LTSF-Transformers extract temporal relations well from longer input sequences?_** The size of the look-back window greatly impacts forecasting accuracy as 

it determines how much we can learn from historical data. Generally speaking, a powerful TSF model with a strong temporal relation extraction capability should be able to achieve better results with larger look-back window sizes. 

To study the impact of input look-back window sizes, we conduct experiments with _L ∈ {_ 24 _,_ 48 _,_ 72 _,_ 96 _,_ 120 _,_ 144 _,_ 168 _,_ 192 _,_ 336 _,_ 504 _,_ 672 _,_ 720 _}_ for long-term forecasting (T=720). Figure 4 demonstrates the MSE results on two datasets. Similar to the observations from previous studies [27, 30], existing Transformer-based models’ performance deteriorates or stays stable when the look-back window size increases. In contrast, the performances of all _LTSF-Linear_ are significantly boosted with the increase of look-back window size. Thus, existing solutions tend to overfit temporal noises instead of extracting temporal information if given a longer sequence, and the input size 96 is exactly suitable for most Transformers. 

5 



<!-- Start of picture text -->
GrouthTruth Autoformer Informer FEDformer DLinear GrouthTruth Autoformer Informer FEDformer DLinear GrouthTruth Autoformer Informer FEDformer DLinear<br>1.0<br>4<br>1.0<br>0.5<br>3<br>0.5<br>0.0<br>2<br>0.0<br>1 0.5<br>0.5<br>0 1.0<br>1.0<br>1 1.5<br>1.5<br>0 50 100 150 200 250 300 0 50 100 150 200 250 300 0 50 100 150 200 250 300<br>(a) Electricity (b) Exchange-Rate (c) ETTh2<br><!-- End of picture text -->

Figure 3. Illustration of the long-term forecasting output (Y-axis) of five models with an input length _L_ =96 and output length _T_ =192 (X-axis) on Electricity, Exchange-Rate, and ETTh2, respectively. 

Additionally, we provide more quantitative results in the Appendix, and our conclusion holds in almost all cases. 



<!-- Start of picture text -->
Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear<br>Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear<br>1.4<br>0.40<br>1.2<br>0.35<br>1.0<br>0.30<br>0.8<br>0.25<br>0.6<br>0.20<br>0.4<br>24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720<br>(a) 720  steps- Traffic (b) 720  steps- Electricity<br><!-- End of picture text -->

Figure 4. The MSE results (Y-axis) of models with different lookback window sizes (X-axis) of long-term forecasting (T= **720** ) on the Traffic and Electricity datasets. 

**_What can be learned for long-term forecasting?_** While the temporal dynamics in the look-back window significantly impact the forecasting accuracy of short-term time series forecasting, we hypothesize that long-term forecasting depends on whether _models can capture the trend and periodicity well only._ That is, the farther the forecasting horizon, the less impact the look-back window itself has. 

|Methods|FEDf|ormer|Autof|ormer|
|---|---|---|---|---|
|Input|_Close_|_Far_|_Close_|_Far_|
|Electricity|0.251|0.265|0.255|0.287|
|Traffic|0.631|0.645|0.677|0.675|



Table 3. Comparison of different input sequences under the MSE metric to explore what LTSF-Transformers depend on. If the input is _Close_ , we use the 96 _th, ...,_ 191 _th_ time steps as the input sequence. If the input is _Far_ , we use the 0 _th, ...,_ 95 _th_ time steps. Both of them forecast the 192 _th, ...,_ (192 + 720) _th_ time steps. 

To validate the above hypothesis, in Table 3, we compare the forecasting accuracy for the same future 720 time steps with data from two different look-back windows: (i). the original input L=96 setting (called _Close_ ) and (ii). the far input L=96 setting (called _Far_ ) that is before the original 

96 time steps. From the experimental results, the performance of the SOTA Transformers drops slightly, indicating these models only capture similar temporal information from the adjacent time series sequence. Since capturing the intrinsic characteristics of the dataset generally does not require a large number of parameters, i,e. one parameter can represent the periodicity. Using too many parameters will even cause overfitting, which partially explains why _LTSFLinear_ performs better than Transformer-based methods. 

**_Are the self-attention scheme effective for LTSF?_** We verify whether these complex designs in the existing Transformer (e.g., Informer) are essential. In Table 4, we gradually transform Informer to Linear. First, we replace each self-attention layer by a linear layer, called _Att.-Linear_ , since a self-attention layer can be regarded as a fullyconnected layer where weights are dynamically changed. Furthermore, we discard other auxiliary designs (e.g., FFN) in Informer to leave embedding layers and linear layers, named _Embed + Linear_ . Finally, we simplify the model to one linear layer. Surprisingly, the performance of Informer grows with the gradual simplification, indicating the unnecessary of the self-attention scheme and other complex modules at least for existing LTSF benchmarks. 

|Met|hods|Informer|_Att.-Linear_|_Embed + Linear_|Linear|
|---|---|---|---|---|---|
|ge|96|0.847|1.003|0.173|0.084|
|han|192|1.204|0.979|0.443|0.155|
|xc|336|1.672|1.498|1.288|0.301|
|E|720|2.478|2.102|2.026|0.763|
|1|96|0.865|0.613|0.454|0.400|
|Th|192|1.008|0.759|0.686|0.438|
|ET|336|1.107|0.921|0.821|0.479|
||720|1.181|0.902|1.051|0.515|



Table 4. The MSE comparisons of gradually transforming Informer to a Linear from the left to right columns. _Att.-Linear_ is a structure that replaces each attention layer with a linear layer. _Embed + Linear_ is to drop other designs and only keeps embedding layers and a linear layer. The look-back window size is 96. 

**_Can existing LTSF-Transformers preserve temporal order well?_** Self-attention is inherently permutation- 

6 

|Methods||Linear|||FEDform|er||Autoform|er||Informe|r|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Predict Length|_Ori._|_Shuf._|_Half-Ex._|_Ori._|_Shuf._|_Half-Ex._|_Ori._|_Shuf._|_Half-Ex._|_Ori._|_Shuf._|_Half-Ex._|
|ge<br>96|0.080|0.133|0.169|0.161|0.160|0.162|0.152|0.158|0.160|0.952|1.004|0.959|
|han<br>192|0.162|0.208|0.243|0.274|0.275|0.275|0.278|0.271|0.277|1.012|1.023|1.014|
|xc<br>336|0.286|0.320|0.345|0.439|0.439|0.439|0.435|0.430|0.435|1.177|1.181|1.177|
|E<br>720|0.806|0.819|0.836|1.122|1.122|1.122|1.113|1.113|1.113|1.198|1.210|1.196|
|Average Drop|N/A|27.26%|46.81%|N/A|-0.09%|0.20%|N/A|0.09%|1.12%|N/A|-0.12%|-0.18%|
|1<br>96|0.395|0.824|0.431|0.376|0.753|0.405|0.455|0.838|0.458|0.974|0.971|0.971|
|Th<br>192|0.447|0.824|0.471|0.419|0.730|0.436|0.486|0.774|0.491|1.233|1.232|1.231|
|ET<br>336|0.490|0.825|0.505|0.447|0.736|0.453|0.496|0.752|0.497|1.693|1.693|1.691|
|720|0.520|0.846|0.528|0.468|0.720|0.470|0.525|0.696|0.524|2.720|2.716|2.715|
|Average Drop|N/A|81.06%|4.78%|N/A|73.28%|3.44%|N/A|56.91%|0.46%|N/A|1.98%|0.18%|



Table 5. The MSE comparisons of models when shuffling the raw input sequence. _Shuf._ randomly shuffles the input sequence. _Half-EX._ randomly exchanges the first half of the input sequences with the second half. Average Drop is the average performance drop under all forecasting lengths after shuffling. All results are the average test MSE of five runs. 

invariant, i.e., regardless of the order. However, in timeseries forecasting, the sequence order often plays a crucial role. We argue that even with positional and temporal embeddings, existing Transformer-based methods still suffer from temporal information loss. In Table 5, we shuffle the raw input before the embedding strategies. Two shuffling strategies are presented: _Shuf._ randomly shuffles the whole input sequences and _Half-Ex._ exchanges the first half of the input sequence with the second half. Interestingly, compared with the original setting ( _Ori._ ) on the Exchange Rate, the performance of all Transformer-based methods does not fluctuate even when the input sequence is randomly shuffled. By contrary, the performance of _LTSF-Linear_ is damaged significantly. These indicate that LTSF-Transformers with different positional and temporal embeddings preserve quite limited temporal relations and are prone to overfit on noisy financial data, while the _LTSF-Linear_ can model the order naturally and avoid overfitting with fewer parameters. 

For the ETTh1 dataset, FEDformer and Autoformer introduce time series inductive bias into their models, making them can extract certain temporal information when the dataset has more clear temporal patterns (e.g., periodicity) than the Exchange Rate. Therefore, the average drops of the two Transformers are 73.28% and 56.91% under the _Shuf._ setting, where it loses the whole order information. Moreover, Informer still suffers less from both _Shuf._ and _Half-Ex._ settings due to its no such temporal inductive bias. Overall, the average drops of _LTSF-Linear_ are larger than Transformer-based methods for all cases, indicating the existing Transformers do not preserve temporal order well. 

**_How effective are different embedding strategies?_** We study the benefits of position and timestamp embeddings used in Transformer-based methods. In Table 6, the forecasting errors of Informer largely increase without positional embeddings (wo/Pos.). Without timestamp embeddings (wo/Temp.) will gradually damage the performance of Informer as the forecasting lengths increase. Since Informer uses a single time step for each token, it is necessary to introduce temporal information in tokens. 

|Methods|Embedding|96|Trai<br>192|ffic<br>336|720|
|---|---|---|---|---|---|
||All|0.597|0.606|0.627|0.649|
|FEDfrmr|wo/Pos.|**0.587**|**0.604**|**0.621**|**0.626**|
|oe|wo/Temp.|0.613|0.623|0.650|0.677|
||wo/Pos.-Temp.|0.613|0.622|0.648|0.663|
||All|0.629|0.647|0.676|**0.638**|
|Atf|wo/Pos.|**0.613**|**0.616**|**0.622**|0.660|
|uoormer|wo/Temp.|0.681|0.665|0.908|0.769|
||wo/Pos.-Temp.|0.672|0.811|1.133|1.300|
||All|**0.719**|**0.696**|**0.777**|**0.864**|
|If|wo/Pos.|1.035|1.186|1.307|1.472|
|normer|wo/Temp.|0.754|0.780|0.903|1.259|
||wo/Pos.-Temp.|1.038|1.351|1.491|1.512|



Table 6. The MSE comparisons of different embedding strategies on Transformer-based methods with look-back window size 96 and forecasting lengths _{_ 96 _,_ 192 _,_ 336 _,_ 720 _}_ . 

Rather than using a single time step in each token, FEDformer and Autoformer input a sequence of timestamps to embed the temporal information. Hence, they can achieve comparable or even better performance without fixed positional embeddings. However, without timestamp embeddings, the performance of Autoformer declines rapidly because of the loss of global temporal information. Instead, thanks to the frequency-enhanced module proposed in FEDformer to introduce temporal inductive bias, it suffers less from removing any position/timestamp embeddings. 

**_Is training data size a limiting factor for existing LTSFTransformers?_** Some may argue that the poor performance of Transformer-based solutions is due to the small sizes of the benchmark datasets. Unlike computer vision or natural language processing tasks, TSF is performed on collected time series, and it is difficult to scale up the training data size. In fact, the size of the training data would indeed have a significant impact on the model performance. Accordingly, we conduct experiments on Traffic, comparing the performance of the model trained on a full dataset (17,544*0.7 hours), named _Ori._ , with that trained on a shortened dataset (8,760 hours, i.e., 1 year), called _Short_ . Unexpectedly, Table 7 presents that the prediction errors 

7 

with reduced training data are lower in most cases. This might because the whole-year data maintains more clear temporal features than a longer but incomplete data size. While we cannot conclude that we should use less data for training, it demonstrates that the training data scale is not the limiting reason for the performances of Autoformer and FEDformer. 

contributions do not come from proposing a linear model but rather from throwing out an important question, showing surprising comparisons, and demonstrating why LTSFTransformers are not as effective as claimed in these works through various perspectives. We sincerely hope our comprehensive studies can benefit future work in this area. 

|Methods|FEDf|ormer|Autof|ormer|
|---|---|---|---|---|
|Dataset|_Ori._|_Short_|_Ori._|_Short_|
|96|0.587|**0.568**|0.613|**0.594**|
|192|0.604|**0.584**|**0.616**|0.621|
|336|0.621|**0.601**|0.622|**0.621**|
|720|0.626|**0.608**|0.660|**0.650**|



Table 7. The MSE comparison of two training data sizes. 

**_Is efficiency really a top-level priority?_** Existing LTSFTransformers claim that the _O_ � _L_<sup>2�</sup> complexity of the vanilla Transformer is unaffordable for the LTSF problem. Although they prove to be able to improve the theoretical time and memory complexity from _O_ � _L_<sup>2�</sup> to _O_ ( _L_ ), it is unclear whether _1) the actual inference time and memory cost on devices are improved, and 2) the memory issue is unacceptable and urgent for today’s GPU (e.g., an NVIDIA Titan XP here)._ In Table 8, we compare the average practical efficiencies with 5 runs. Interestingly, compared with the vanilla Transformer (with the same DMS decoder), most Transformer variants incur similar or even worse inference time and parameters in practice. These follow-ups introduce more additional design elements to make practical costs high. Moreover, the memory cost of the vanilla Transformer is practically acceptable, even for output length _L_ = 720, which weakens the importance of developing a memoryefficient Transformers, at least for existing benchmarks. 

|Method|MACs|Parameter|Time|Memory|
|---|---|---|---|---|
|DLinear|**0.04G**|**139.7K**|**0.4ms**|**687MiB**|
|Transformer_×_|4.03G|13.61M|26.8ms|6091MiB|
|Informer|3.93G|14.39M|49.3ms|3869MiB|
|Autoformer|4.41G|14.91M|164.1ms|7607MiB|
|Pyraformer|0.80G|241.4M<sup>_∗_</sup>|3.4ms|7017MiB|
|FEDformer|4.41G|20.68M|40.5ms|4143MiB|



- _×_ is modified into the same one-step decoder, which is implemented in the source code from Autoformer. 

- _∗_ 236.7M parameters of Pyraformer come from its linear decoder. 

Table 8. Comparison of practical efficiency of LTSF-Transformers under L=96 and T=720 on the Electricity. MACs are the number of multiply-accumulate operations. We use Dlinear for comparison since it has the double cost in _LTSF-Linear_ . The inference time averages 5 runs. 

## **6. Conclusion and Future Work** 

**Conclusion.** This work questions the effectiveness of emerging favored Transformer-based solutions for the longterm time series forecasting problem. We use an embarrassingly simple linear model _LTSF-Linear_ as a DMS forecasting baseline to verify our claims. Note that our 

**Future work.** _LTSF-Linear_ has a limited model capacity, and it merely serves a simple yet competitive baseline with strong interpretability for future research. For example, the one-layer linear network is hard to capture the temporal dynamics caused by change points [25]. Consequently, we believe there is a great potential for new model designs, data processing, and benchmarks to tackle the challenging LTSF problem. 

8 

# **Appendix: Are Transformers Effective for Time Series Forecasting?** 

In this Appendix, we provide descriptions of nonTransformer-based TSF solutions, detailed experimental settings, more comparisons under different look-back window sizes, and the visualization of _LTSF-Linear_ on all datasets. We also append our code to reproduce the results shown in the paper. 

## **A. Related Work: Non-Transformer-Based TSF Solutions** 

As a long-standing problem with a wide range of applications, statistical approaches (e.g., autoregressive integrated moving average (ARIMA) [1], exponential smoothing [12], and structural models [14]) for time series forecasting have been used from the 1970s onward. Generally speaking, the parametric models used in statistical methods require significant domain expertise to build. 

To relieve this burden, many machine learning techniques such as gradient boosting regression tree (GBRT) [10, 11] gain popularity, which learns the temporal dynamics of time series in a data-driven manner. However, these methods still require manual feature engineering and model designs. With the powerful representation learning capability of deep neural networks (DNNs) from abundant data, various deep learning-based TSF solutions are proposed in the literature, achieving better forecasting accuracy than traditional techniques in many cases. 

Besides Transformers, the other two popular DNN architectures are also applied for time series forecasting: 

- Recurrent neural networks (RNNs) based methods (e.g., [21]) summarize the past information compactly in internal memory states and recursively update themselves for forecasting. 

- Convolutional neural networks (CNNs) based methods (e.g., [3]), wherein convolutional filters are used to capture local temporal features. 

RNN-based TSF methods belong to IMS forecasting techniques. Depending on whether the decoder is implemented in an autoregressive manner, there are either IMS or DMS forecasting techniques for CNN-based TSF methods [3, 17]. 

## **B. Experimental Details** 

### **B.1. Data Descriptions** 

We use nine wildly-used datasets in the main paper. The details are listed in the following. 

- ETT (Electricity Transformer Temperature) [30]<sup>2</sup> consists of two hourly-level datasets (ETTh) and two 15minute-level datasets (ETTm). Each of them contains seven oil and load features of electricity transformers from July 2016 to July 2018. 

- Traffic<sup>3</sup> describes the road occupancy rates. It contains the hourly data recorded by the sensors of San Francisco freeways from 2015 to 2016. 

- Electricity<sup>4</sup> collects the hourly electricity consumption of 321 clients from 2012 to 2014. 

- Exchange-Rate [15]<sup>5</sup> collects the daily exchange rates of 8 countries from 1990 to 2016. 

- Weather<sup>6</sup> includes 21 indicators of weather, such as air temperature, and humidity. Its data is recorded every 10 min for 2020 in Germany. 

- ILI<sup>7</sup> describes the ratio of patients seen with influenzalike illness and the number of patients. It includes weekly data from the Centers for Disease Control and Prevention of the United States from 2002 to 2021. 

### **B.2. Implementation Details** 

For existing Transformer-based TSF solutions: the implementation of Autoformer [28], Informer [30], and the vanilla Transformer [26] are all taken from the Autoformer work [28]; the implementation of FEDformer [31] and Pyraformer [18] are from their respective code repository. We also adopt their default hyper-parameters to train the models. For _DLinear_ , the moving average kernel size for decomposition is 25, which is the same as Autoformer. The total parameters of a vanilla linear model and a _NLinear_ are TL. The total parameters of the _DLinear_ are 2TL. Since _LTSF-Linear_ will be underfitting when the input length is short, and LTSF-Transformers tend to overfit on a long lookback window size. To compare the best performance of existing LTSF-Transformers with _LTSF-Linear_ , we report L=336 for _LTSF-Linear_ and L=96 for Transformers by default. For more hyper-parameters of _LTSF-Linear_ , please refer to our code. 

> 2https://github.com/zhouhaoyi/ETDataset 

> 3http://pems.dot.ca.gov 

> 4https : / / archive . ics . uci . edu / ml / datasets / ElectricityLoadDiagrams20112014 

> 5https : / / github . com / laiguokun / multivariate - time-series-data 

> 6https://www.bgc-jena.mpg.de/wetter/ 

> 7https : / / gis . cdc . gov / grasp / fluview / fluportaldashboard.html 

9 

## **C. Additional Comparison with Transformers** 

We further compare _LTSF-Linear_ with LTSFTransformer for Univariate Forecasting on four ETT datasets. Moreover, in Figure 4 of the main paper, we demonstrate that existing Transformers fail to exploit large look-back window sizes with two examples. Here, we give comprehensive comparisons between _LTSF-Linear_ and Transformer-based TSF solutions under various look-back window sizes _on all benchmarks_ . 

### **C.1. Comparison of Univariate Forecasting** 

We present the univariate forecasting results on the four ETT datasets in table 9. Similarly, _LTSF-Linear_ , especially for _NLinear_ can consistently outperform all transformerbased methods by a large margin in most time. We find that there are serious distribution shifts between training and test sets (as shown in Fig. 5 (a), (b)) on ETTh1 and ETTh2 datasets. Simply normalization via the last value from the lookback window can greatly relieve the distribution shift problem. 

### **C.2. Comparison under Different Look-back Windows** 

In Figure 6, we provide the MSE comparisons of five LTSF-Transformers with _LTSF-Linear_ under different lookback window sizes to explore whether existing Transformers can extract temporal well from longer input sequences. For hourly granularity datasets (ETTh1, ETTh2, Traffic, and Electricity), the increasing look-back window sizes are {24, 48, 72, 96, 120, 144, 168, 192, 336, 504, 672, 720}, which represent {1, 2, 3, 4, 5, 6, 7, 8, 14, 21, 28, 30} days. The forecasting steps are {24, 720}, which mean {1, 30} days. For 5-minute granularity datasets (ETTm1 and ETTm2), we set the look-back window size as {24, 36, 48, 60, 72, 144, 288}, which represent {2, 3, 4, 5, 6, 12, 24} hours. For 10-minute granularity datasets (Weather), we set the look-back window size as {24, 48, 72, 96, 120, 144, 168, 192, 336, 504, 672, 720}, which mean {4, 8, 12, 16, 20, 24, 28, 32, 56, 84, 112, 120} hours. The forecasting steps are {24, 720} that are {4, 120} hours. For weekly granularity dataset (ILI), we set the look-back window size as {26, 52, 78, 104, 130, 156, 208}, which represent {0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4} years. The corresponding forecasting steps are {26, 208}, meaning {0.5, 4} years. 

As shown in Figure 6, with increased look-back window sizes, the performance of _LTSF-Linear_ is significantly boosted for most datasets (e.g., ETTm1 and Traffic), while this is not the case for Transformer-based TSF solutions. Most of their performance fluctuates or gets worse as the input lengths increase. To be specific, the results of Exchange-Rate do not show improved results with a long look-back window (from Figure 6(m) and (n)), and we at- 

tribute it to the low information-to-noise ratio in such financial data. 

## **D. Ablation study on the** **_LTSF-Linear_** 

### **D.1. Motivation of NLinear** 

If we normalize the test data by the mean and variance of train data, there could be a distribution shift in testing data, i.e, the mean value of testing data is not 0. If the model made a prediction that is out of the distribution of true value, a large error would occur. For example, there is a large error between the true value and the true value minus/add one. Therefore, in _NLinear_ , we use the subtraction and addition to shift the model prediction toward the distribution of true value. Then, large errors are avoided, and the model performances can be improved. Figure 5 illustrates histograms of the trainset-test set distributions, where each bar represents the number of data points. Clear distribution shifts between training and testing data can be observed in ETTh1, ETTh2, and ILI. Accordingly, from Table 9 and Table 2 in the main paper, we can observe that there are great improvements in the three datasets comparing the _NLinear_ to the _Linear_ , showing the effectiveness of the _NLinear_ in relieving distribution shifts. Moreover, for the datasets without obvious distribution shifts, like Electricity in Figure 5(c), using the vanilla _Linear_ can be enough, demonstrating the similar performance with _NLinear_ and _DLinear_ . 

### **D.2. The Features of LTSF-Linear** 

Although _LTSF-Linear_ is simple, it has some compelling characteristics: 

- **An** _O_ (1) **maximum signal traversing path length** : The shorter the path, the better the dependencies are captured [18], making _LTSF-Linear_ capable of capturing both short-range and long-range temporal relations. 

- **High-efficiency:** As _LTSF-Linear_ is a linear model with two linear layers at most, it costs much lower memory and fewer parameters and has a faster inference speed than existing Transformers (see Table 8 in main paper). 

- **Interpretability:** After training, we can visualize weights from the seasonality and trend branches to have some insights on the predicted values [9]. 

- **Easy-to-use:** _LTSF-Linear_ can be obtained easily without tuning model hyper-parameters. 

### **D.3. Interpretability of LTSF-Linear** 

Because _LTSF-Linear_ is a set of linear models, the weights of linear layers can directly reveal how _LTSFLinear_ works. The weight visualization of _LTSF-Linear_ can 

10 

|Methods|Lin|ear|NLi|near|DLi|near|FEDfo|rmer-f|FEDfor|mer-w|Autof|ormer|Info|rmer|Log|Trans|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Metric|MSE|MAE|MSE|MSE|MAE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|MSE|MAE|
|1<br>96|0.189|0.359|**0.053**|**0.177**|0.056|0.180|0.079|0.215|0.080|0.214|0.071|0.206|0.193|0.377|0.283|0.468|
|_Th_<br>192|0.078|0.212|**0.069**|**0.204**|0.071|0.204|0.104|0.245|0.105|0.256|0.114|0.262|0.217|0.395|0.234|0.409|
|_ET_<br>336|0.091|0.237|**0.081**|**0.226**|0.098|0.244|0.119|0.270|0.120|0.269|0.107|0.258|0.202|0.381|0.386|0.546|
|720|0.172|0.340|**0.080**|**0.226**|0.189|0.359|0.142|0.299|0.127|0.280|0.126|0.283|0.183|0.355|0.475|0.629|
|2<br>96|0.133|0.283|**0.129**|**0.278**|0.131|0.279|0.128|0.271|0.156|0.306|0.153|0.306|0.213|0.373|0.217|0.379|
|_Th_<br>192|0.176|0.330|**0.169**|**0.324**|0.176|0.329|0.185|0.330|0.238|0.380|0.204|0.351|0.227|0.387|0.281|0.429|
|_ET_<br>336|0.213|0.371|**0.194**|**0.355**|0.209|0.367|0.231|0.378|0.271|0.412|0.246|0.389|0.242|0.401|0.293|0.437|
|720|0.292|0.440|**0.225**|**0.381**|0.276|0.426|0.278|0.420|0.288|0.438|0.268|0.409|0.291|0.439|0.218|0.387|
|1<br>96|0.028|0.125|**0.026**|**0.122**|0.028|0.123|0.033|0.140|0.036|0.149|0.056|0.183|0.109|0.277|0.049|0.171|
|_Tm_<br>192|0.043|0.154|**0.039**|**0.149**|0.045|0.156|0.058|0.186|0.069|0.206|0.081|0.216|0.151|0.310|0.157|0.317|
|_T_<br>336|0.059|0.180|**0.052**|**0.172**|0.061|0.182|0.084|0.231|0.071|0.209|0.076|0.218|0.427|0.591|0.289|0.459|
|_E_<br>720|0.080|0.211|**0.073**|**0.207**|0.080|0.210|0.102|0.250|0.105|0.248|0.110|0.267|0.438|0.586|0.430|0.579|
|2<br>96|0.066|0.189|**0.063**|**0.182**|0.063|0.183|0.067|0.198|0.063|0.189|0.065|0.189|0.088|0.225|0.075|0.208|
|_Tm_<br>192|0.094|0.230|**0.090**|**0.223**|0.092|0.227|0.102|0.245|0.110|0.252|0.118|0.256|0.132|0.283|0.129|0.275|
|_T_<br>336|0.120|0.263|**0.117**|**0.259**|0.119|0.261|0.130|0.279|0.147|0.301|0.154|0.305|0.180|0.336|0.154|0.302|
|_E_<br>720|0.175|0.320|**0.170**|**0.318**|0.175|0.320|0.178|0.325|0.219|0.368|0.182|0.335|0.300|0.435|0.160|0.321|



Table 9. Univariate long sequence time-series forecasting results on ETT full benchmark. The **best results** are highlighted in **bold** and the <u>best results of Transformers</u> are highlighted with a <u>underline.</u> 











<!-- Start of picture text -->
(a) ETTh1 channel6 (b) ETTh2 channel3<br><!-- End of picture text -->



<!-- Start of picture text -->
(c) Electricity channel3 (d) ILI channel6<br><!-- End of picture text -->

Figure 5. Distribution of ETTh1, ETTh2, Electricity, and ILI dataset. A clear distribution shift between training and testing data can be observed in ETTh1, ETTh2, and ILI. 

also reveal certain characteristics in the data used for forecasting. 

Here we take DLinear as an example. Accordingly, we visualize the trend and remainder weights of all datasets with a fixed input length of 96 and four different forecasting horizons. To obtain a smooth weight with a clear pattern in visualization, we initialize the weights of the linear layers in DLinear as 1 _/L_ rather than random initialization. That is, we use the same weight for every forecasting time step in the look-back window at the start of training. 

**How the model works:** Figure 7(c) visualize the weights of the trend and the remaining layers on the Exchange-Rate dataset. Due to the lack of periodicity and seasonality in financial data, it is hard to observe clear patterns, but the trend layer reveals greater weights of information closer to the outputs, representing their larger contributions to the predicted values. 

**Periodicity of data:** For Traffic data, as shown in Figure 7(d), the model gives high weights to the latest time step of the look-back window for the 0,23,47...719 forecast- 

ing steps. Among these forecasting time steps, the 0, 167, 335, 503, 671 time steps have higher weights. Note that 24 time steps are a day, and 168 time steps are a week. This indicates that Traffic has a daily periodicity and a weekly periodicity. 

## **References** 

- [1] Adebiyi A Ariyo, Adewumi O Adewumi, and Charles K Ayo. Stock price prediction using the arima model. In _2014 UKSim-AMSS 16th International Conference on Computer Modelling and Simulation_ , pages 106–112. IEEE, 2014. 1, 2, 9 

- [2] Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. Neural machine translation by jointly learning to align and translate. _arXiv: Computation and Language_ , 2014. 2 

- [3] Shaojie Bai, J Zico Kolter, and Vladlen Koltun. An empirical evaluation of generic convolutional and 

11 



<!-- Start of picture text -->
Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear<br>Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear<br>1.0 5<br>0.9 1.4 1.2<br>4<br>1.0<br>0.8 1.2<br>0.7 0.8 3<br>1.0<br>0.6 0.8 0.6 2<br>0.5<br>0.4<br>0.4 0.6 1<br>0.2<br>0.3 0.4<br>24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720<br>(a) 24  steps- ETTh1 (b) 720  steps- ETTh1 (c) 24  steps- ETTh2 (d) 720  steps- ETTh2<br>Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear<br>Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear<br>1.2<br>0.6 1.1 0.30 4<br>1.0<br>0.5 0.9 0.25 3<br>0.4 0.80.7 0.20 2<br>0.3 0.6 0.15<br>1<br>0.5<br>0.2 0.4 0.10<br>24 36 48 60 72 144 288 24 36 48 60 72 144 288 24 36 48 60 72 144 288 24 36 48 60 72 144 288<br>(e) 24  steps- ETTm1 (f) 576  steps- ETTm1 (g) 24  steps- ETTm2 (h) 576  steps- ETTm2<br>Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear<br>Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear<br>0.50 1.6 0.9<br>0.45 1.4<br>1.4 0.8<br>0.40 1.2<br>0.35 1.2 0.7<br>0.30 1.0 1.0<br>0.6<br>0.25 0.8 0.8<br>0.20 0.6 0.5<br>0.15 0.4 0.4 0.6<br>0.10<br>0.4<br>24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720<br>(i) 24  steps- Weather (j) 720  steps- Weather (k) 24  steps- Traffic (l) 720  steps- Traffic<br>Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear Transformer Autoformer Pyraformer NLinear<br>Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear Informer FEDformer Linear DLinear<br>1.4 7 8<br>1.2 3.0<br>6 7<br>1.0 2.5 6<br>0.8 5<br>2.0 5<br>0.6 4<br>1.5 4<br>0.4 3<br>0.2 1.0 3<br>2 2<br>0.0 0.5<br>24 48 72 96 120 144 168 192 336 504 672 720 24 48 72 96 120 144 168 192 336 504 672 720 26 52 78 104 130 156 208 26 52 78 104 130 156 208<br>(m) 24  steps- Exchange (n) 720  steps- Exchange (o) 24  steps- ILI (p) 60  steps- ILI<br><!-- End of picture text -->

Figure 6. The MSE results (Y-axis) of models with different look-back window sizes (X-axis) of the long-term forecasting (e.g., **720** -time steps) and the short-term forecasting (e.g., **24** time steps) on different benchmarks. 

recurrent networks for sequence modeling. _arXiv preprint arXiv:1803.01271_ , 2018. 1, 9 

- [4] Guillaume Chevillon. Direct multi-step estimation and forecasting. _Journal of Economic Surveys_ , 21(4):746–785, 2007. 2 

- [5] Razvan-Gabriel Cirstea, Chenjuan Guo, Bin Yang, Tung Kieu, Xuanyi Dong, and Shirui Pan. Triformer: 

Triangular, variable-specific attentions for long sequence multivariate time series forecasting–full version. _arXiv preprint arXiv:2204.13767_ , 2022. 1 

- [6] R. B. Cleveland. Stl : A seasonal-trend decomposition procedure based on loess. _Journal of Office Statistics_ , 1990. 3 

- [7] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and 

12 



<!-- Start of picture text -->
(a1) Remainder (a2) Trend (a3) Remainder (a4) Trend (a5) Remainder (a6) Trend (a7) Remainder (a8) Trend<br>In-96,  Out-96 In-96,  Out-168 In-96,  Out-336 In-96,  Out-720<br>(b1) Remainder (b2) Trend (b3) Remainder (b4) Trend (b5) Remainder (b6) Trend (b7) Remainder (b8) Trend<br>In-96,  Out-96 In-96,  Out-192 In-96,  Out-336 In-96,  Out-720<br>(c1) Remainder (c2) Trend (c3) Remainder (c4) Trend (c5) Remainder (c6) Trend (c7) Remainder (c8) Trend<br>In-96,  Out-96 In-96,  Out-192 In-96,  Out-336 In-96,  Out-720<br>(d1) Remainder (d2) Trend (d3) Remainder (d4) Trend (d5) Remainder (d6) Trend (d7) Remainder (d8) Trend<br>In-96,  Out-96 In-96,  Out-192 In-96,  Out-336 In-96,  Out-720<br>(e1) Remainder (e2) Trend (e3) Remainder (e4) Trend (e5) Remainder (e6) Trend (e7) Remainder (e8) Trend<br>In-96,  Out-96 In-96,  Out-192 In-96,  Out-336 In-96,  Out-720<br>(f1) Remainder (f2) Trend (f3) Remainder (f4) Trend (f5) Remainder (f6) Trend (f7) Remainder (f8) Trend<br>In-36,  Out-24 In-36,  Out-36 In-36,  Out-48 In-36,  Out-60<br>ETTh1<br>Electricity<br>Exchange-Rate<br>Traffic<br>Weather<br>ILI<br><!-- End of picture text -->

Figure 7. Visualization of the weights(T*L) of _LTSF-Linear_ on several benchmarks. Models are trained with a look-back window L (X-axis) and different forecasting time steps T (Y-axis). We show weights in the remainder and trend layer. 

Kristina Toutanova. Bert: Pre-training of deep bidirec- 

tional transformers for language understanding. _arXiv_ 

13 

_preprint arXiv:1810.04805_ , 2018. 1 

- [8] Linhao Dong, Shuang Xu, and Bo Xu. Speechtransformer: a no-recurrence sequence-to-sequence model for speech recognition. In _2018 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)_ , pages 5884–5888. IEEE, 2018. 1 

- [9] Ruijun Dong and Witold Pedrycz. A granular time series approach to long-term forecasting and trend forecasting. _Physica A: Statistical Mechanics and its Applications_ , 387(13):3253–3270, 2008. 10 

- [10] Shereen Elsayed, Daniela Thyssens, Ahmed Rashed, Hadi Samer Jomaa, and Lars Schmidt-Thieme. Do we really need deep learning models for time series forecasting? _arXiv preprint arXiv:2101.02118_ , 2021. 9 

- [11] Jerome H Friedman. Greedy function approximation: a gradient boosting machine. _Annals of statistics_ , pages 1189–1232, 2001. 1, 9 

- [12] Everette S Gardner Jr. Exponential smoothing: The state of the art. _Journal of forecasting_ , 4(1):1–28, 1985. 9 

- [13] James Douglas Hamilton. _Time series analysis_ . Princeton university press, 2020. 3 

- [14] Andrew C Harvey. Forecasting, structural time series models and the kalman filter. 1990. 9 

- [15] Guokun Lai, Wei-Cheng Chang, Yiming Yang, and Hanxiao Liu. Modeling long- and short-term temporal patterns with deep neural networks. _international acm sigir conference on research and development in information retrieval_ , 2017. 1, 4, 9 

- [16] Shiyang Li, Xiaoyong Jin, Yao Xuan, Xiyou Zhou, Wenhu Chen, Yu-Xiang Wang, and Xifeng Yan. Enhancing the locality and breaking the memory bottleneck of transformer on time series forecasting. _Advances in Neural Information Processing Systems_ , 32, 2019. 1, 2, 3, 4 

- [17] Minhao Liu, Ailing Zeng, Zhijian Xu, Qiuxia Lai, and Qiang Xu. Time series is a special sequence: Forecasting with sample convolution and interaction. _arXiv preprint arXiv:2106.09305_ , 2021. 1, 9 

- [18] Shizhan Liu, Hang Yu, Cong Liao, Jianguo Li, Weiyao Lin, Alex X Liu, and Schahram Dustdar. Pyraformer: Low-complexity pyramidal attention for long-range time series modeling and forecasting. In _International Conference on Learning Representations_ , 2021. 1, 2, 3, 4, 9, 10 

- [19] Ze Liu, Yutong Lin, Yue Cao, Han Hu, Yixuan Wei, Zheng Zhang, Stephen Lin, and Baining Guo. Swin transformer: Hierarchical vision transformer using 

shifted windows. In _Proceedings of the IEEE/CVF International Conference on Computer Vision_ , pages 10012–10022, 2021. 1 

- [20] LIU Minhao, Ailing Zeng, LAI Qiuxia, Ruiyuan Gao, Min Li, Jing Qin, and Qiang Xu. T-wavenet: A treestructured wavelet neural network for time series signal analysis. In _International Conference on Learning Representations_ , 2021. 2 

- [21] Gábor Petneházi. Recurrent neural networks for time series forecasting. _arXiv preprint arXiv:1901.00069_ , 2019. 9 

- [22] David Salinas, Valentin Flunkert, and Jan Gasthaus. Deepar: Probabilistic forecasting with autoregressive recurrent networks. _International Journal of Forecasting_ , 2017. 2 

- [23] Souhaib Ben Taieb, Rob J Hyndman, et al. _Recursive and direct multi-step forecasting: the best of both worlds_ , volume 19. Citeseer, 2012. 2 

- [24] Sean J. Taylor and Benjamin Letham. Forecasting at scale. _PeerJ Prepr._ , 2017. 2 

- [25] Gerrit JJ van den Burg and Christopher KI Williams. An evaluation of change point detection algorithms. _arXiv preprint arXiv:2003.06222_ , 2020. 8 

- [26] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. _Advances in neural information processing systems_ , 30, 2017. 1, 2, 9 

- [27] Qingsong Wen, Tian Zhou, Chaoli Zhang, Weiqi Chen, Ziqing Ma, Junchi Yan, and Liang Sun. Transformers in time series: A survey. _arXiv preprint arXiv:2202.07125_ , 2022. 1, 2, 5 

- [28] Jiehui Xu, Jianmin Wang, Mingsheng Long, et al. Autoformer: Decomposition transformers with autocorrelation for long-term series forecasting. _Advances in Neural Information Processing Systems_ , 34, 2021. 1, 2, 3, 4, 5, 9 

- [29] Ailing Zeng, Xuan Ju, Lei Yang, Ruiyuan Gao, Xizhou Zhu, Bo Dai, and Qiang Xu. Deciwatch: A simple baseline for 10x efficient 2d and 3d pose estimation. _arXiv preprint arXiv:2203.08713_ , 2022. 1 

- [30] Haoyi Zhou, Shanghang Zhang, Jieqi Peng, Shuai Zhang, Jianxin Li, Hui Xiong, and Wancai Zhang. Informer: Beyond efficient transformer for long sequence time-series forecasting. In _The Thirty-Fifth AAAI Conference on Artificial Intelligence, AAAI 2021, Virtual Conference_ , volume 35, pages 11106– 11115. AAAI Press, 2021. 1, 2, 3, 4, 5, 9 

- [31] Tian Zhou, Ziqing Ma, Qingsong Wen, Xue Wang, Liang Sun, and Rong Jin. Fedformer: Frequency enhanced decomposed transformer for long-term series 

14 

forecasting. In _International Conference on Machine Learning_ , 2022. 1, 2, 3, 4, 5, 9 

15 

