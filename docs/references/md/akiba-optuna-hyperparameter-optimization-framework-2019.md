---
# --- bibliographic record ---
entry_type: inproceedings
title: "Optuna: A Next-generation Hyperparameter Optimization Framework"
authors:
  - "Takuya Akiba"
  - "Shotaro Sano"
  - "Toshihiko Yanase"
  - "Takeru Ohta"
  - "Masanori Koyama"
year: 2019
venue: "Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining"
volume: ""
issue: ""
pages: "2623-2631"
publisher: "ACM"
doi: "10.1145/3292500.3330701"
arxiv: ""
url: "https://doi.org/10.1145/3292500.3330701"

# --- archive record ---
source_pdf: akiba-optuna-hyperparameter-optimization-framework-2019.pdf
source_sha256: a1ec86ba21a3f2e7bb774c00f8b108dc955993f39feed72f5d8ee3910b6d8a51
pdf_pages: 10
converted: 2026-11-12
record_source: crossref
review: "archive holds the arXiv preprint 1907.10902"
key_insight: "The framework that ran the search. TPE is one of its samplers and is credited to Bergstra et al., so the method cites both."
first_page: "Preprint doi Optuna: A Next-generation Hyperparameter Optimization Framework Preprint, compiled July 26, 2019 Takuya Akiba1∗, Shotaro Sano1, Toshihiko Yanase1, Takeru Ohta1, and Masanori Koyama1 1Pref"
---
# Optuna: A Next-generation Hyperparameter Optimization Framework 

Preprint, compiled July 26, 2019 

**Takuya Akiba**<sup>1∗</sup> **, Shotaro Sano**<sup>1</sup> **, Toshihiko Yanase**<sup>1</sup> **, Takeru Ohta**<sup>1</sup> **, and Masanori Koyama**<sup>1</sup> 

1Preferred Networks, Inc. 

## **A** bstract 

The purpose of this study is to introduce new design-criteria for next-generation hyperparameter optimization software. The criteria we propose include (1) _define-by-run API_ that allows users to construct the _parameter search space_ dynamically, (2) efficient implementation of both searching and pruning strategies, and (3) easy-to-setup, versatile architecture that can be deployed for various purposes, ranging from scalable distributed computing to light-weight experiment conducted via interactive interface. In order to prove our point, we will introduce _Optuna_ , an optimization software which is a culmination of our effort in the development of a next generation optimization software. As an optimization software designed with _define-by-run_ principle, _Optuna_ is particularly the first of its kind. We will present the design-techniques that became necessary in the development of the software that meets the above criteria, and demonstrate the power of our new design through experimental results and real world applications. Our software is available under the MIT license ( `https://github.com/pfnet/optuna/` ). 

## 1 Introduction 

Hyperparameter search is one of the most cumbersome tasks in machine learning projects. The complexity of deep learning method is growing with its popularity, and the framework of efficient automatic hyperparameter tuning is in higher demand than ever. Hyperparameter optimization softwares such as _Hyperopt_ [1], _Spearmint_ [2], _SMAC_ [3], _Autotune_ [4], and _Vizier_ [5] were all developed in order to meet this need. 

The choice of the parameter-sampling algorithms varies across frameworks. _Spearmint_ [2] and _GPyOpt_ use Gaussian Processes, and _Hyperopt_ [1] employs _tree-structured Parzen estimator_ (TPE) [6]. Hutter et al. proposed _SMAC_ [3] that uses random forests. Recent frameworks such as _Google Vizier_ [5], _Katib_ and _Tune_ [7] also support _pruning_ algorithms, which monitor the intermediate result of each trial and kills the unpromising trials prematurely in order to speed up the exploration. There is an active research field for the pruning algorithm in hyperparameter optimization. Domhan et al. proposed a method that uses parametric models to predict the learning curve [8]. Klein et al. constructed Bayesian neural networks to predict the expected learning curve [9]. Li et al. employed a bandit-based algorithm and proposed Hyperband [10]. 

A still another way to accelerate the optimization process is to use distributed computing, which enables parallel processing of multiple trials. _Katib_ is built on _Kubeflow_ , which is a computing platform for machine learning services that is based on _Kubernetes_ . _Tune_ also supports parallel optimization, and uses the _Ray_ distributed computing platform [11]. 

However, there are several serious problems that are being overlooked in many of these existing optimization frameworks. Firstly, all previous hyperparameter optimization frameworks to date require the user to statically construct the parameter-searchspace for each model, and the search space can be extremely hard to describe in these frameworks for large-scale experiments that involve massive number of candidate models of different types with large parameter spaces and many conditional variables. When the parameter space is not appropriately described by the user, application of advanced optimization method can 

be in vain. Secondly, many existing frameworks do not feature efficient pruning strategy, when in fact both _parameter searching strategy_ and _performance estimation strategy_ are important for high-performance optimization under limited resource availability [12][5][7]. Finally, in order to accommodate with a variety of models in a variety of situations, the architecture shall be able to handle both small and large scale experiments with minimum setup requirements. If possible, architecture shall be installable with a single command as well, and it shall be designed as an open source software so that it can continuously incorporate newest species of optimization methods by interacting with open source community. 

In order to address these concerns, we propose to introduce the following new design criteria for next-generation optimization framework: 

- _Define-by-run_ programming that allows the user to dynamically construct the search space, 

- Efficient sampling algorithm and pruning algorithm that allows some user-customization, 

- Easy-to-setup, versatile architecture that can be deployed for tasks of various types, ranging from light-weight experiments conducted via interactive interfaces to heavy-weight distributed computations. 

In this study, we will demonstrate the significance of these criteria through _Optuna_ , an open-source optimization software which is a culmination of our effort in making our definition of next-generation optimization framework come to reality. 

We will also present new design techniques and new optimization algorithms that we had to develop in order to meet our proposed criteria. Thanks to these new design techniques, our implementation outperforms many major black-box optimization frameworks while being easy to use and easy to setup in various environments. In what follows, we will elaborate each of our proposed criteria together with our technical solutions, and present experimental results in both real world applications and benchmark datasets. 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

2 

|1<br>2<br>3|`import optuna`<br>`import ...`|
|---|---|
|4<br>5<br>6|`def objective(trial):`<br>`n`<br>`layers = trial.suggest`<br>`int(’n`<br>`layers’, 1, 4)`|
|7|`layers = []`<br><br>|
|8|`for i in range(n`<br>`layers):`<br>|
|9<br>10|`layers.append(trial.suggest`<br>`int(’n`<br>`units`<br>`l`{}`’.`<br>`format(i), 1, 128))`|
|11<br>12|`clf = MLPClassifier(tuple(layers))`|
|13<br>14<br>15|`mnist = fetch`<br>`mldata(’MNIST original’)`<br>`x`<br>`train , x`<br>`test , y`<br>`train , y`<br>`test = train`<br>`test`<br>`split(`<br>`mnist.data, mnist.target)`|
|16<br>17|`clf.fit(x`<br>`train , y`<br>`train)`|
|18<br>19|`return 1.0` −`clf.score(x`<br>`test , y`<br>`test)`|
|20<br>21|`study = optuna.create`<br>`study()`<br>`study.optimize(objective , n`<br>`trials=100)`|



Figure 1: An example code of _Optuna_ ’s _define-by-run_ style API. This code builds a space of hyperparameters for a classifier of the MNIST dataset and optimizes the number of layers and the number of hidden units at each layer. 

- 1 `import hyperopt` 2 `import ...` 3 4 `space =` { 5 `’n units l1’: hp.randint(’n units l1’, 128),` 6 `’l2’: hp.choice(’l2’, [` { 7 `’has l2’: True,` 8 `’n units l2’: hp.randint(’n units l2’, 128),` 9 `’l3’: hp.choice(’l3’, [` { 

- 10 `’has l3’: True,` 11 `’n units l3’: hp.randint(’n units l3’, 128),` 12 `’l4’: hp.choice(’l4’, [` { 13 `’has l4’: True,` 14 `’n units l4’: hp.randint(’n units l4’, 128),` 

- 15 } `,` { `’has l4’: False` } `]),` 16 } `,` { `’has l3’: False` } `]),` 17 } `,` { `’has l2’: False` } `]),` 18 } 19 20 `def objective(space):` 21 `layers = [space[’n units l1’] + 1]` 22 `for i in range (2, 5):` 23 `space = space[’l` {} `’. format (i)]` 24 `if not space[’has l` {} `’. format (i)]:` 25 `break` 26 `layers.append(space[’n units l` {} `’. format (i)] + 1)` 

- 27 28 `clf = MLPClassifier( tuple(layers))` 29 30 `mnist = fetch mldata(’MNIST original’)` 31 `x train , x test , y train , y test = train test split( mnist.data, mnist.target)` 

- 32 33 `clf.fit(x train , y train)` 34 35 `return 1.0` − `clf.score(x test , y test)` 36 37 `hyperopt.fmin(fn=objective , space=space, max evals=100, algo=hyperopt.tpe.suggest)` 

Figure 2: An example code of _Hyperopt_ [1] that has the exactly same functionality as the code in 1. _Hyperopt_ is an example of _define-and-run_ style API. 

_Optuna_ is released under the MIT license ( `https://github. com/pfnet/optuna/` ), and is in production use at Preferred Networks for more than one year. 

## 2 Define-by-run API 

In this section we describe the significance of the _define-by-run_ principle. As we will elaborate later, we are borrowing the term _define-by-run_ from a trending philosophy in deep learning frameworks that allows the user to dynamically program deep networks. Following the original definition, we use the term _define-by-run_ in the context of optimization framework to refer to a design that allows the user to dynamically construct the search space. In _define-by-run API_ , the user does not have to bear the full burden of explicitly defining everything in advance about the optimization strategy. 

The power of _define-by-run_ API is more easily understood with actual code. _Optuna_ formulates the hyperparameter optimization as a process of minimizing/maximizing an _objective function_ that takes a set of hyperparameters as an input and returns its (validation) score. Figure 1 is an example of an objective function written in _Optuna_ . This function dynamically constructs the search space of neural network architecture (the number of layers and the number of hidden units) without relying on externally defined static variables. _Optuna_ refers to each process of optimization as a _study_ , and to each evaluation of objective function as a _trial_ . In the code of Figure 1, _Optuna_ defines an objective function (Lines 4–18), and invokes the ‘ `optimize API` ’ that takes the objective function as an input (Line 21). Instead of hyperparameter values, an objective function in _Optuna_ receives a _living trial object_ , which is associated with a single _trial_ . 

_Optuna_ gradually builds the objective function through the interaction with the _trial_ object. The search spaces are constructed dynamically by the methods of the _trial_ object during the runtime of the objective function. The user is asked to invoke ‘ `s` uggest API’ inside the objective function in order to dynamically generate the hyperparameters for each _trial_ (Lines 5 and 9). Upon the invocation of ‘ `suggest API` ’, a hyperparameter is statistically sampled based on the history of previously evaluated _trials_ . At Line 5, ‘ `suggest` ~~`i`~~ `nt` ’ method suggests a value for ‘ `n` ~~`l`~~ `ayers` ’, the integer hyperparameter that determines the number of layers in the Multilayer Perceptron. Using loops and conditional statements written in usual _Python_ syntax, the user can easily represent a wide variety of parameter spaces. With this functionality, the user of _Optuna_ can even express heterogeneous parameter space with an intuitive and simple code (Figure 3). 

Meanwhile, Figure 2 is an example code of _Hyperopt_ that has the exactly same functionality as the _Optuna_ code in Figure 1. Note that the same function written in _Hyperopt_ (Figure 2) is significantly longer, more convoluted, and harder to interpret. It is not even obvious at first glance that the code in Figure 2 is in fact equivalent to the code in Figure 1! In order to write the same _for-loop_ in Figure 1 using _Hyperopt_ , the user must prepare the list of all the parameters in the parameter-space prior to the exploration (see line 4-18 in Figure 2). This requirement will lead the user to even darker nightmares when the optimization problem is more complicated. 

### _2.1 Modular Programming_ 

A keen reader might have noticed in Figure 3 that the optimization code written in _Optuna_ is highly modular, thanks to its _define-by-run_ design. Compatibility with modular programming 

3 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

Table 1: Software frameworks for deep learning and hyperparameter optimization, sorted by their API styles: _define-and-run_ and _define-by-run_ . 

||**Deep Learning Frameworks**|**Hyperparameter Optimization Frameworks**|
|---|---|---|
|**Define-and-Run Style**|Torch(2002), Theano(2007), Caffe(2013),|SMAC(2011), Spearmint(2012), Hyperopt(2015), GPyOpt(2016),|
|(symbolic, static)|TensorFlow(2015), MXNet(2015), Keras(2015)|Vizier(2017), Katib(2018), Tune(2018), Autotune(2018)|
|**Define-by-Run Style**<br>(imperative, dynamic)|Chainer(2015), DyNet(2016), PyTorch(2016),<br>TensorFlow Eager(2017), Gluon(2017)|**_Optuna (2019; this work)_**|



Table 2: Comparison of previous hyperparameter optimization frameworks and _Optuna_ . There is a checkmark for _lightweight_ if the setup for the framework is easy and it can be easily used for lightweight purposes. 

|**Framework**|**API Style**|**Pruning**|**Lightweight**|**Distributed**|**Dashboard**|**OSS**|
|---|---|---|---|---|---|---|
|SMAC [3]|define-and-run||||||
|GPyOpt|define-and-run||||||
|Spearmint [2]|define-and-run||||||
|Hyperopt [1]|define-and-run||||||
|Autotune [4]|define-and-run||||||
|Vizier [5]|define-and-run||||||
|Katib|define-and-run||||||
|Tune [7]|define-and-run||||||
|Optuna (this work)|define-by-run||||||





<!-- Start of picture text -->
1 import sklearn<br>2 import ...<br>3<br>4 def create rf(trial):<br>5 rf max depth = trial.suggest int(’rf max depth’, 2,<br>32)<br>6 return RandomForestClassifier(max depth=<br>rf max depth)<br>7<br>8 def create mlp(trial):<br>9 n layers = trial.suggest int(’n layers’, 1, 4)<br>10<br>11 layers = []<br>12 for i in range(n layers):<br>13 layers.append(trial.suggest int(’n units l {} ’.<br>format (i), 1, 128))<br>14<br>15 return MLPClassifier(tuple (layers))<br>16<br>17 def objective(trial):<br>18 classifier name = trial.suggest categorical(’<br>classifier’, [’rf’ , ’mlp’])<br>19<br>20 if classifier name == ’rf’:<br>21 classifier obj = create rf(trial)<br>22 else:<br>23 classifier obj = create mlp(trial)<br>24<br>25 ...<br><!-- End of picture text -->

Figure 3: An example code of _Optuna_ for the construction of a heterogeneous parameter-space. This code simultaneously explores the parameter spaces of both random forest and MLP. 

is another important strength of the _define-by-run_ design. Figure 4 is another example code written in _Optuna_ for a more complex scenario. This code is capable of simultaneously optimizing both the topology of a multilayer perceptron (method ‘ `create` ~~`m`~~ `odel` ’) and the hyperparameters of stochastic gradient descent (method ‘ `create` ~~`o`~~ `ptimizer` ’). The method ‘ `create` ~~`m`~~ `odel` ’ generates ‘ `n` ~~`l`~~ `ayers` ’ in Line 5 and uses a _for loop_ to construct a neural network of depth equal to ‘ `n` ~~`l`~~ `ayers` ’. The method also generates ‘ `n` ~~`u`~~ `nits` _i_ ’ at each _i_ -th loop, a hyperparameter that determines the number of the units in the _i_ -th layer. The method ‘ `create` ~~`o`~~ `ptimizer` ’, on the other hand, makes suggestions for both learning rate and weight-decay parameter. Again, a complex space of hyperparameters is simply 

- 1 `import chainer` 2 `import ...` 3 4 `def create model(trial):` 5 `n layers = trial.suggest int(’n layers’, 1, 3)` 6 `layers = []` 7 `for i in range(n layers):` 8 `n units = trial.suggest int(’n units l` {} `’. format (i), 4, 128)` 

- 9 `layers.append(L.Linear(None, n units))` 

- 10 `layers.append(F.relu)` 11 `layers.append(L.Linear(None, 10))` 12 `return chainer.Sequential(` * `layers)` 13 14 `def create optimizer(trial, model):` 15 `lr = trial.suggest loguniform(’lr’, 1e` − `5, 1e` − `1)` 16 `optimizer = chainer.optimizers.MomentumSGD(lr=lr)` 17 `weight decay = trial.suggest loguniform(’ weight decay’, 1e` − `10, 1e` <u>−</u> `3)` 

- 18 `optimizer.setup(model)` 19 `optimizer.add hook(chainer.optimizer.WeightDecay( weight decay))` 

- 20 `return optimizer` 21 22 `def objective(trial):` 23 `model = create model(trial)` 24 `optimizer = create optimizer(trial, model)` 25 `...` 26 27 `study = optuna.create study()` 28 `study.optimize(objective , n trials=100)` 

Figure 4: Another example of _Optuna_ ’s objective function. This code simultaneously optimizes neural network architecture (the `create` ~~`m`~~ `odel` method) and the hyperparameters for stochastic gradient descent (the `create optimizer` method). 

expressed in _Optuna._ Most notably, in this example, the methods ‘ `create` ~~`m`~~ `odel` ’ and ‘ `create` ~~`o`~~ `ptimizer` ’ are independent of one another, so that we can make changes to each one of them separately. Thus, the user can easily augment this code with other conditional variables and methods for other set of parameters, and make a choice from more diverse pool of models. 

### _2.2 Deployment_ 

Indeed, the benefit of our _define-by-run_ API means nothing if we cannot easily deploy the model with the best set of hyperpa- 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

4 

rameters found by the algorithm. The above example (Figure 4) might make it seem as if the user has to write a different version of the objective function that does not invoke ‘ `trial.suggest` ’ in order to deploy the _best_ configuration. Luckily, this is not a concern. For deployment purpose, _Optuna_ features a separate class called ‘ `FixedTrial` ’ that can be passed to objective functions. The ‘ `FixedTrial` ’ object has practically the same set of functionalities as the _trial_ class, except that it will only suggest the user defined set of the hyperparameters when passed to the objective functions. Once a parameter-set of interest is found (e.g., the best ones), the user simply has to construct a ‘ `FixedTrial` ’ object with the parameter set. 

### _2.3 Historical Remarks_ 

Historically, the term _define-by-run_ was coined by the developers of deep learning frameworks. In the beginning, most deep learning frameworks like _Theano_ and _Torch_ used to be _declarative_ , and constructed the networks in their _domain specific languages_ (DSL). These frameworks are called _define-and-run_ frameworks because they do not allow the user to alter the manipulation of intermediate variables once the network is defined. In _define-and-run_ frameworks, computation is conducted in two phases: (1) construction phase and (2) evaluation phase. In a way, contemporary optimization methods like _Hyperopt_ are built on the philosophy similar to _define-and-run_ , because there are two phases in their optimization: (1) construction of the search space and (3) exploration in the search space. 

Because of their difficulty of programming, the _define-and-run_ style deep learning frameworks are quickly being replaced by _define-by-run_ style deep learning frameworks like _Chainer_ [13], _DyNet_ [14], _PyTorch_ [15], eager-mode _TensorFlow_ [16], and _Gluon_ . In the _define-by-run_ style DL framework, there are no two separate phases for the construction of the network and the computation on the network. Instead, the user is allowed to directly program how each variables are to be manipulated in the network. What we propose in this article is an analogue of the _define-by-run_ DL framework for hyperparameter optimization, in which the framework asks the user to directly program the _parameter search-space_ (See Table 1) . Armed with the architecture built on the _define-by-run_ principle, our _Optuna_ can express highly sophisticated search space at ease. 

## 3 Efficient Sampling and Pruning Mechanism 

In general, the cost-effectiveness of hyperparameter optimization framework is determined by the efficiency of (1) _searching strategy_ that determines the set of parameters that shall be investigated, and (2) _performance estimation strategy_ that estimates the value of currently investigated parameters from learning curves and determines the set of parameters that shall be discarded. As we will experimentally show later, the efficiency of both searching strategy and performance estimation strategy is necessary for cost-effective optimization method. 

The strategy for the termination of unpromising _trials_ is often referred to as _pruning_ in many literatures, and it is also well known as _automated early stopping_ [5] [7]. We, however, refer to this functionality as _pruning_ in order to distinguish it from the _early stopping regularization_ in machine learning that exists as a countermeasure against overfitting. As shown in table 2, many 

existing frameworks do not provide efficient pruning strategies. In this section we will provide our design for both _sampling_ and _pruning_ . 

### _3.1 Sampling Methods on Dynamically Constructed Parameter Space_ 

There are generally two types of sampling method: _relational sampling_ that exploits the correlations among the parameters and _independent sampling_ that samples each parameter independently. The _independent sampling_ is not necessarily a naive option, because some sampling algorithms like TPE [6] are known to perform well even without using the parameter correlations, and the cost effectiveness for both relational and independent sampling depends on environment and task. Our _Optuna_ features both, and it can handle various independent sampling methods including TPE as well as relational sampling methods like CMA-ES. However, some words of caution are in order for the implementation of _relational sampling_ in _define-by-run_ framework. 

### _Relational sampling in define-by-run frameworks_ 

One valid claim about the advantage of the old _define-and-run_ optimization design is that the program is given the knowledge of the concurrence relations among the hyperparamters from the beginning of the optimization process. Implementing of optimization methods that takes the concurrence relations among the parameters into account is a nontrivial challenge when the search spaces are dynamically constructed. To overcome this challenge, _Optuna_ features an ability to identify _trial_ results that are informative about the concurrence relations. This way, the framework can identify the underlying concurrence relations after some number of independent samplings, and use the inferred concurrence relation to conduct user-selected relational sampling algorithms like CMA-ES [17] and GP-BO [18]. Being an open source software, _Optuna_ also allows the user to use his/her own customized sampling procedure. 

### _3.2 E_ ffi _cient Pruning Algorithm_ 

Pruning algorithm is essential in ensuring the ”cost” part of the cost-effectiveness. Pruning mechanism in general works in two phases. It _(1)_ periodically monitors the intermediate objective values, and _(2)_ terminates the _trial_ that does not meet the predefined condition. In _Optuna_ , ‘ `report API` ’ is responsible for the monitoring functionality, and ‘ `should` ~~`p`~~ `rune API` ’ is responsible for the premature termination of the unpromising _trials_ (see Figure 5). The background algorithm of ‘ `should` ~~`p`~~ `rune` ’ method is implemented by the family of _pruner_ classes. _Optuna_ features a variant of Asynchronous Successive Halving algorithm [19] , a recently developed _state of the art_ method that scales linearly with the number of workers in distributed environment. 

Asynchronous Successive Halving(ASHA) is an extension of Successive Halving [20] in which each worker is allowed to asynchronously execute aggressive early stopping based on provisional ranking of _trials_ . The most prominent advantage of asynchronous pruning is that it is particularly well suited for applications in distributional environment; because each worker does not have to wait for the results from other workers at each 

5 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 



<!-- Start of picture text -->
1 import ...<br>2<br>3 def objective(trial):<br>54 ...<br>6 lr = trial.suggest loguniform(’lr’, 1e − 5, 1e − 1)<br>7 clf = sklearn.linear model.SGDClassifier(<br>learning rate=lr)<br>8 for step in range (100):<br>9 clf.partial fit(x train , y train , classes)<br>10<br>11 # Report intermediate objective value.<br>12 intermediate value = clf.score(x val , y val)<br>13 trial.report(intermediate value , step=step)<br>14<br>15 # Handle pruning based on the intermediate value<br>16 if trial.should. prune(step):<br>17 raise TrialPruned()<br>18<br>19 return 1.0 − clf.score(x val , y val)<br>20<br>21 study = optuna.create study()<br>22 study.optimize(objective)<br><!-- End of picture text -->

Figure 5: An example of implementation of a pruning algorithm with _Optuna_ . An intermediate value is reported at each step of iterative training. The `Pruner` class stops unpromising _trials_ based on the history of reported values. 

### **Algorithm 1:** Pruning algorithm based on Successive Halving 

**Input:** target trial `trial` , current step `step` , minimum resource _r_ , reduction factor η, minimum early-stopping rate _s_ . **Output: true** if the trial should be pruned, **false** otherwise. **1** `rung` ← max(0, log η(⌊ `step` / _r_ ⌋) − _s_ ) **2 if** `step` � _r_ η<sup>_s_+</sup><sup>`rung`</sup> **then 3 return false** 

- **4 end 5** `value` ←get ~~t~~ rial ~~i~~ ntermediate ~~v~~ alue( `trial` , `step` ) **6** `values` ←get ~~a~~ ll ~~t~~ rials ~~i~~ ntermediate ~~v~~ alues( `step` ) **7** `top` ~~`k v`~~ `alues` ←top ~~k~~ ( `values` , ⌊| `values` |/η⌋) **8 if** `top` ~~`k`~~ `values` = ∅ **then 9** `top` ~~`k`~~ `values` ←top ~~k~~ ( `values` , 1) 

**10 end** 

**11 return** `value` � `top` ~~`k v`~~ `alues` 

round of the pruning, the parallel computation can process multiple _trials_ simultaneously without delay. 

Algorithm 1 is the actual pruning algorithm implemented in _Optuna_ . Inputs to the algorithm include the _trial_ that is subject to pruning, number of steps, reducing factor, minimum resource to be used before the pruning, and minimum early stopping rate. Algorithm begins by computing the current _rung_ for the _trial_ , which is the number of times the _trial_ has survived the pruning. The _trial_ is allowed to enter the next round of the competition if its provisional ranking is within top 1/η. If the number of _trials_ with the same rung is less than η, the best _trial_ among the _trials_ with the same _rung_ becomes promoted. In order to avoid having to record massive number of checkpointed configurations(snapshots), our implementation does not allow repechage. As experimentally verify in the next section, our modified implementation of Successive Halving scales linearly with the number of workers without any problem. We will present the details of our optimization performance in Section 5.2. 



Figure 6: Overview of _Optuna_ ’s system design. Each worker executes one instance of an objective function in each _study_ . The Objective function runs its _trial_ using _Optuna_ APIs. When the API is invoked, the objective function accesses the shared storage and obtains the information of the past _studies_ from the storage when necessary. Each worker runs the objective function independently and shares the progress of the current _study_ via the storage. 

- 4 Scalable and versatile System that is Easy to setup 

Our last criterion for the next generation optimization software is a scalable system that can handle a wide variety of tasks, ranging from a heavy experiment that requires a massive number of workers to a trial-level, light-weight computation conducted through interactive interfaces like _Jupyter Notebook_ . The figure 6 illustrates how the database( _storage_ ) is incorporated into the system of _Optuna_ ; the _trial_ objects shares the evaluations history of objective functions via storage. _Optuna_ features a mechanism that allows the user to change the storage backend to meet his/her need. 

For example, when the user wants to run experiment with _Jupyter Notebook_ in a local machine, the user may want to avoid spending effort in accessing a multi-tenant system deployed by some organization or in deploying a database on his/her own. When there is no specification given, _Optuna_ automatically uses its built-in in-memory data-structure as the storage back-end. From general user’s perspective, that the framework can be easily used for lightweight purposes is one of the most essential strengths of _Optuna_ , and it is a particularly important part of our criteria for next-generation optimization frameworks. This _lightweight purpose compatibility_ is also featured by select few frameworks like _Hyperopt_ and _GPyOt_ as well. The user of _Optuna_ can also conduct more involved analysis by exporting the results in the _pandas_ [21] dataframe, which is highly compatible with interactive analysis frameworks like _Jupyter Notebooks_ [22]. _Optuna_ also provides web-dashboard for visualization and analysis of _studies_ in real time (see Figure 8). 

Meanwhile, when the user wants to conduct distributed computation, the user of _Optuna_ can deploy relational database as the backend. The user of _Optuna_ can also use _SQLite_ database as well. The figure 7b is an example code that deploys _SQLite_ database. This code conducts distributed computation by simply executing run.py multiple times with the same _study_ identifier and the same storage URL. 

6 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

- 1 `import ...` 2 3 `def objective(trial):` 54 `...return objective value` 6 7 `study name = sys.argv[1]` 8 `storage = sys.argv[2]` 9 

- 10 `study = optuna.Study(study name , storage)` 11 `study.optimize(objective)` 

#### (a) Python code: run.py 

- 1 `# Setup: the shared storage URL and study identifier.` 2 `STORAGE URL =` ' `sqlite:///example.db` ' 3 `STUDY ID=` $ `(optuna create` − `study` −− `storage` $ `STORAGE URL)` 4 5 `# Run the script from multiple processes and/or nodes.` 6 `# Their execution can be asynchronous.` 7 `python run.py` $ `STUDY ID` $ `STORAGE URL &` 8 `python run.py` $ `STUDY ID` $ `STORAGE URL &` 9 `python run.py` $ `STUDY ID` $ `STORAGE URL &` 

- 10 `...` 



Figure 9: Result of comparing TPE+CMA-ES against other existing methods in terms of best attained objective value. Each algorithm was applied to each _study_ 30 times, and Paired MannWhitney U test with α = 0.0005 was used to determine whether TPE+CMA-ES outperforms each rival. 

#### (b) Shell 

Figure 7: Distributed optimization in _Optuna_ . Figure (a) is the optimization script executed by one worker. Figure (b) is an example _shell_ for the optimization with multiple workers in a distributed environment. 



Figure 8: _Optuna_ dashboard. This example shows the online transition of objective values, the parallel coordinates plot of sampled parameters, the learning curves, and the tabular descriptions of investigated _trials_ . 

_Optuna_ ’s new design thus significantly reduces the effort required for storage deployment. This new design can be easily incorporated into a container-orchestration system like _Kubernetes_ as well. As we verify in the experiment section, the distributed computations conducted with our flexible system-design scales linearly with the number of workers. _Optuna_ is also an open source software that can be installed to user’s system with one command. 

## 5 Experimental Evaluation 

We demonstrate the efficiency of the new design-framework through three sets of experiments. 

### _5.1 Performance Evaluation Using a Collection of Tests_ 

As described in the previous section, _Optuna_ not only allows the user to use his/her own customized sampling procedure that suits 

the purpose, but also comes with multiple built-in optimization algorithms including the mixture of independent and relational sampling, which is not featured in currently existing frameworks. For example, _Optuna_ can use the mixture of TPE and CMA-ES. We compared the optimization performance of the TPE+CMAES against those of other sampling algorithms on a collection of tests for black-box optimization [23, 24], which contains 56 test cases. We implemented four adversaries to compare against TPE+CMA-ES: random search as a baseline method, _Hyperopt_ [1] as a TPE-based method, _SMAC3_ [3] as a random-forest based method, and _GPyOpt_ as a Gaussian Process based method. For TPE+CMA-ES, we used TPE for the first 40 steps and used CMA-ES for the rest. For the evaluation metric, we used the best-attained objective value found in 80 _trials_ . Following the work of Dewancker et al. [24], we repeated each _study_ 30 times for each algorithm and applied Paired Mann-Whitney U test with α = 0.0005 to the results in order to statistically compare TPE+CMA-ES’s performance against the rival algorithms. 

The results are shown in Figure 9. TPE+CMA-ES finds statistically worse solution than random search in only 1/56 test cases, performs worse than _Hyperopt_ in 1/56 cases, and performs worse than _SMAC3_ in 3/56 cases. Meanwhile, _GPyOpt_ performed better than TPE+CMA-ES in 34/56 cases in terms of the best-attained loss value. At the same time, TPE+CMA-ES takes an order-of-magnitude less times per trial than _GPyOpt_ . 

Figure 10 shows the average time spent for each test case. TPE+CMA-ES, _Hyperopt_ , _SMAC3_ , and random search finished one _study_ within few seconds even for the test case with more than ten design variables. On the other hand, _GPyOpt_ required twenty times longer duration to complete a _study_ . We see that the mixture of TPE and CMA-ES is a cost-effective choice among current lines of advanced optimization algorithms. If the time of evaluation is a bottleneck, the user may use Gaussian Process based method as a sampling algorithm. We plan in near future to also develop an interface on which the user of _Optuna_ can easily deploy external optimization software as well. 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

7 



Figure 10: Computational time spent by different frameworks for each test case. 

### _5.2 Performance Evaluation of Pruning_ 

We evaluated the performance gain from the pruning procedure in the _Optuna_ -implemented optimization of Alex Krizhevsky’s neural network (AlexNet) [25] on the Street View House Numbers (SVHN) dataset [26]. We tested our pruning system together with random search and TPE. Following the experiment in [10], we used a subnetwork of AlexNet (hereinafter called simplified AlexNet), which consists of three convolutional layers and a fully-connected layer and involves 8 hyperparameters. 

For each experiment, we executed a _study_ with one NVIDIA Tesla P100 card, and terminated each _study_ 4 hours into the experiment. We repeated each _study_ 40 times. With pruning, both TPE and random search was able to conduct a greater number of _trials_ within the same time limit. On average, TPE and random search _without_ pruning completed 35.8 and 36.0 _trials_ per _study_ , respectively. On the other hand, TPE _with_ pruning explored 1278.6 _trials_ on average per _study_ , of which 1271.5 were pruned during the process. Random search _with_ pruning explored 1119.3 _trials_ with 1111.3 pruned _trials_ . 

Figure 11a shows the transition of the average test errors. The result clearly suggests that pruning can significantly accelerate the optimization for both TPE and random search. Our implementation of ASHA significantly outperforms Median pruning, a pruning method featured in _Vizier_ . This result also suggests that sampling algorithm alone is not sufficient for cost-effective optimization. The bottleneck of sampling algorithm is the computational cost required for each _trial_ , and pruning algorithm is necessary for fast optimization. 

### _5.3 Performance Evaluation of Distributed Optimization_ 

We also evaluated the scalability of _Optuna_ ’s distributed optimization. Based on the same experimental setup used in Section 5.2, we recorded the transition of the best scores obtained by TPE with 1, 2, 4, and 8 workers in a distributed environment. Figure 11b shows the relationship between optimization score and execution time. We can see that the convergence speed increases with the number of workers. 

In the interpretation of this experimental results, however, we have to give a consideration to the fact that the relationship between the number of workers and the efficiency of optimization is not as intuitive as the relationship between the number of 

<mark>workers and</mark> the number of _trials_ . This is especially the case for a SMBO [3] such as TPE, where the algorithm is designed to sequentially evaluate each _trial_ . The result illustrated in Figure 11c resolves this concern. Note that the optimization scores per the number of _trials_ (i.e., parallelization efficiency) barely changes with the number of workers. This shows that the performance is linearly scaling with the number of _trials_ , and hence with the number of workers. Figure 12 illustrates the result of optimization that uses both parallel computation and pruning. The result suggests that our optimization scales linearly with the number of workers even when implemented with a pruning algorithm. 

## 6 Real World Applications 

_Optuna_ is already in production use, and it has been successfully applied to a number of real world applications. _Optuna_ is also being actively used by third parties for various purposes, including projects based on _TensorFlow_ and _PyTorch_ . Some projects use _Optuna_ as a part of pipeline for machine-learning framework (e.g., _redshells_<sup>2</sup> , _pyannote-pipeline_<sup>3</sup> ). In this section, we present the examples of _Optuna_ ’s applications in the projects at Preferred Networks. 

**Open Images Object Detection Track 2018.** _Optuna_ was a key player in the development of Preferred Networks’ FasterRCNN models for Google AI Open Images Object Detection Track 2018 on Kaggle<sup>4</sup> , whose dataset is at present the largest in the field of object detection [27]. Our final model, PFDet [28], won the 2nd place in the competition. 

As a versatile next generation optimization software, _Optuna_ can be used in applications outside the field of machine learning as well. Followings are applications of _Optuna_ for non-machine learning tasks. 

**High Performance Linpack for TOP500.** The _Linpack_ benchmark is a task whose purpose is to measure the floating point computation power of a system in which the system is asked to solve a dense matrix LU factorization. The performance on this task is used as a measure of sheer computing power of a system and is used to rank the supercomputers in the TOP500 list<sup>5</sup> . _High Performance Linpack_ (HPL) is one of the implementations for Linpack. HPL involves many hyperparameters, and the performance result of any system heavily relies on them. We used _Optuna_ to optimize these hyperparameters in the evaluation of the maximum performance of _MN-1b_ , an in-house supercomputer owned by Preferred Networks. 

**_RocksDB_ .** _RocksDB_ [29] is a persistent key-value store for fast storage that has over hundred user-customizable parameters. As described by the developers in the official website, ”configuring _RocksDB_ optimally is not trivial”, and even the ” _RocksDB_ developers don’t fully understand the effect of each configuration change”<sup>6</sup> . For this experiment, we prepared a set of 500,000 files 

> 2 `https://github.com/m3dev/redshells` 

> 3 `https://github.com/pyannote/pyannote-pipeline` 

> 4 `https://www.kaggle.com/c/google-ai-open-images-object-detection-track` 

> 5 `https://www.top500.org/` 

> 6 `https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide#` 

> `final-thoughts` 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

8 







<!-- Start of picture text -->
(a) (b) (c)<br><!-- End of picture text -->

Figure 11: The transition of average test errors of simplified AlexNet for SVHN dataset. Figure (a) illustrates the effect of pruning mechanisms on TPE and random search. Figure (b) illustrates the effect of the number of workers on the performance. Figure (c) plots the test errors against the number of _trials_ for different number of workers. Note that the number of workers has no effect on the relation between the number of executed _trials_ and the test error. The result also shows the superiority of ASHA pruning over median pruning. 



Figure 12: Distributed hyperparameter optimization process for the minimization of average test errors of simplified AlexNet for SVHN dataset. The optimization was done with ASHA pruning. 

of size 10KB each, and used _Optuna_ to look for parameter-set that minimizes the computation time required for applying a certain set of operations(store, search, delete) to this file set. Out of over hundred customizable parameters, we used _Optuna_ to explore the space of 34 parameters. With the default parameter setting, _RocksDB_ takes 372seconds on HDD to apply the set of operation to the file set. With pruning, _Optuna_ was able to find a parameter-set that reduces the computation time to 30 seconds. Within the same 4 hours, the algorithm with pruning explores 937 sets of parameters while the algorithm without pruning only explores 39. When we disable the time-out option for the evaluation process, the algorithm without pruning explores only 2 _trials_ . This experiment again verifies the crucial role of pruning. 

**Encoder Parameters for** **_FFmpeg_ .** _FFmpeg_<sup>7</sup> is a multimedia framework that is widely used in the world for decoding, encoding and streaming of movies and audio dataset. _FFmpeg_ has numerous customizable parameters for encoding. However, finding of good encoding parameter-set for _FFmpeg_ is a nontrivial task, as it requires expert knowledge of codec. We used _Optuna_ to seek the encoding parameter-set that minimizes the reconstruction error for the Blender Open Movie Project’s ”Big 

Buck Bunny”<sup>8</sup> . _Optuna_ was able to find a parameter-set whose performance is on par with the second best parameter-set among the presets provided by the developers. 

## 7 Conclusions 

The efficacy of _Optuna_ strongly supports our claim that our new design criteria for next generation optimization frameworks are worth adopting in the development of future frameworks. The _define-by-run_ principle enables the user to dynamically construct the search space in the way that has never been possible with previous hyperparameter tuning frameworks. Combination of efficient searching and pruning algorithm greatly improves the cost effectiveness of optimization. Finally, scalable and versatile design allows users of various types to deploy the frameworks for a wide variety of purposes. As an open source software, _Optuna_ itself can also evolve even further as a next generation software by interacting with open source community. It is our strong hope that the set of design techniques we developed for _Optuna_ will serve as a basis of other next generation optimization frameworks to be developed in the future. 

**Acknowledgement.** The authors thank R. Calland, S. Tokui, H. Maruyama, K. Fukuda, K. Nakago, M. Yoshikawa, M. Abe, H. Imamura, and Y. Kitamura for valuable feedback and suggestion. 

## References 

- [1] James Bergstra, Brent Komer, Chris Eliasmith, Dan Yamins, and David D Cox. Hyperopt: a Python library for model selection and hyperparameter optimization. _Computational Science_ & _Discovery_ , 8(1):14008, 2015. 

- [2] Jasper Snoek, Hugo Larochelle, and Ryan P Adams. Practical bayesian optimization of machine learning algorithms. In _NIPS_ , pages 2951–2959, 2012. 

- [3] Frank Hutter, Holger H. Hoos, and Kevin Leyton-Brown. Sequential model-based optimization for general algorithm 

> 8 Blender Foundation — www.blender.org 

> 7 `https://www.ffmpeg.org/` 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

9 

   - configuration. In _LION_ , pages 507–523, 2011. ISBN 9783-642-25565-6. 

- [4] Patrick Koch, Oleg Golovidov, Steven Gardner, Brett Wujek, Joshua Griffin, and Yan Xu. Autotune: A derivativefree optimization framework for hyperparameter tuning. In _KDD_ , pages 443–452, 2018. ISBN 978-1-4503-5552-0. 

- [5] Daniel Golovin, Benjamin Solnik, Subhodeep Moitra, Greg Kochanski, John Karro, and D Sculley. Google Vizier: A service for black-box optimization. In _KDD_ , pages 1487–1495, 2017. ISBN 978-1-4503-4887-4. 

- [6] James Bergstra, Remi´ Bardenet, Yoshua Bengio, and Balazs K´ egl. Algorithms for hyper-parameter optimization.´ In _NIPS_ , pages 2546–2554, 2011. 

- [7] Richard Liaw, Eric Liang, Robert Nishihara, Philipp Moritz, Joseph E. Gonzalez, and Ion Stoica. Tune: A research platform for distributed model selection and training. In _ICML Workshop on AutoML_ , 2018. 

- [8] Tobias Domhan, Jost Tobias Springenberg, and Frank Hutter. Speeding up automatic hyperparameter optimization of deep neural networks by extrapolation of learning curves. In _IJCAI_ , pages 3460–3468, 2015. 

- [9] Aaron Klein, Stefan Falkner, Jost Tobias Springenberg, and Frank Hutter. Learning curve prediction with Bayesian neural networks. In _ICLR_ , 2017. 

- [10] Lisha Li, Kevin Jamieson, Giulia DeSalvo, Afshin Rostamizadeh, and Ameet Talwalkar. Hyperband: A novel bandit-based approach to hyperparameter optimization. _Journal of Machine Learning Research_ , 18(185):1–52, 2018. 

- [11] Philipp Moritz, Robert Nishihara, Stephanie Wang, Alexey Tumanov, Richard Liaw, Eric Liang, William Paul, Michael I. Jordan, and Ion Stoica. Ray: A distributed framework for emerging AI applications. _CoRR_ , abs/1712.05889, 2017. URL `http://arxiv.org/abs/ 1712.05889` . 

- [12] Frank Hutter, Lars Kotthoff, and Joaquin Vanschoren, editors. _Automatic Machine Learning: Methods, Systems, Challenges_ . Springer, 2018. In press, available at http://automl.org/book. 

- [13] Seiya Tokui, Kenta Oono, Shohei Hido, and Justin Clayton. Chainer: a next-generation open source framework for deep learning. In _NIPS Workshop on Machine Learning Systems_ , 2015. 

- [14] Graham Neubig, Chris Dyer, Yoav Goldberg, Austin Matthews, Waleed Ammar, Antonios Anastasopoulos, Miguel Ballesteros, David Chiang, Daniel Clothiaux, Trevor Cohn, Kevin Duh, Manaal Faruqui, Cynthia Gan, Dan Garrette, Yangfeng Ji, Lingpeng Kong, Adhiguna Kuncoro, Gaurav Kumar, Chaitanya Malaviya, Paul Michel, Yusuke Oda, Matthew Richardson, Naomi Saphra, Swabha Swayamdipta, and Pengcheng Yin. Dynet: The dynamic neural network toolkit. _CoRR_ , abs/1701.03980, 2017. 

- [15] Adam Paszke, Sam Gross, Soumith Chintala, Gregory Chanan, Edward Yang, Zachary DeVito, Zeming Lin, Alban Desmaison, Luca Antiga, and Adam Lerer. Automatic differentiation in PyTorch. In _NIPS Autodi_ ff _Workshop_ , 2017. 

- [16] Mart´ın Abadi, Paul Barham, Jianmin Chen, Zhifeng Chen, Andy Davis, Jeffrey Dean, Matthieu Devin, Sanjay Ghemawat, Geoffrey Irving, Michael Isard, Manjunath Kudlur, Josh Levenberg, Rajat Monga, Sherry Moore, Derek G. Murray, Benoit Steiner, Paul Tucker, Vijay Vasudevan, Pete Warden, Martin Wicke, Yuan Yu, and Xiaoqiang Zheng. TensorFlow: A system for large-scale machine learning. In _OSDI_ , pages 265–283, 2016. 

- [17] Nikolaus Hansen and Andreas Ostermeier. Completely derandomized self-adaptation in evolution strategies. _Evolutionary Computation_ , 9(2):159–195, 2001. 

- [18] Bobak Shahriari, Kevin Swersky, Ziyu Wang, Ryan P Adams, and Nando De Freitas. Taking the human out of the loop: A review of bayesian optimization. _Proceedings of the IEEE_ , 104(1):148–175, 2016. 

- [19] Liam Li, Kevin Jamieson, Afshin Rostamizadeh, Ekaterina Gonina, Moritz Hardt, Benjamin Recht, and Ameet Talwalkar. Massively parallel hyperparameter tuning. In _NeurIPS Workshop on Machine Learning Systems_ , 2018. 

- [20] Kevin Jamieson and Ameet Talwalkar. Non-stochastic best arm identification and hyperparameter optimization. In _Artificial Intelligence and Statistics_ , pages 240–248, 2016. 

- [21] Wes McKinney. Pandas: a foundational python library for data analysis and statistics. In _SC Workshop on Python for High Performance and Scientific Computing_ , 2011. 

- [22] Thomas Kluyver, Benjamin Ragan-Kelley, Fernando Perez,´ Brian Granger, Matthias Bussonnier, Jonathan Frederic, Kyle Kelley, Jessica Hamrick, Jason Grout, Sylvain Corlay, Paul Ivanov, Damian Avila, Safia Abdalla, and Carol´ Willing. Jupyter notebooks – a publishing format for reproducible computational workflows. In F. Loizides and B. Schmidt, editors, _Positioning and Power in Academic Publishing: Players, Agents and Agendas_ , pages 87 – 90. IOS Press, 2016. 

- [23] Michael McCourt. Benchmark suite of test functions suitable for evaluating black-box optimization strategies. `https://github.com/sigopt/evalset` , 2016. 

- [24] Ian Dewancker, Michael McCourt, Scott Clark, Patrick Hayes, Alexandra Johnson, and George Ke. A strategy for ranking optimization methods using multiple criteria. In _ICML Workshop on AutoML_ , pages 11–20, 2016. 

- [25] Alex Krizhevsky, Ilya Sutskever, and Geoffrey E Hinton. ImageNet classification with deep convolutional neural networks. In _NIPS_ , pages 1097–1105, 2012. 

- [26] Yuval Netzer, Tao Wang, Adam Coates, Alessandro Bissacco, Bo Wu, and Andrew Y Ng. Reading digits in natural images with unsupervised feature learning. In _NIPS Workshop on Deep Learning and Unsupervised Feature Learning_ , 2011. 

- [27] Alina Kuznetsova, Hassan Rom, Neil Alldrin, Jasper R. R. Uijlings, Ivan Krasin, Jordi Pont-Tuset, Shahab Kamali, Stefan Popov, Matteo Malloci, Tom Duerig, and Vittorio Ferrari. The open images dataset V4: unified image classification, object detection, and visual relationship detection at scale. _CoRR_ , abs/1811.00982, 2018. 

- [28] Takuya Akiba, Tommi Kerola, Yusuke Niitani, Toru Ogawa, Shotaro Sano, and Shuji Suzuki. PFDet: 2nd 

Preprint – Optuna: A Next-generation Hyperparameter Optimization Framework 

10 

place solution to open images challenge 2018 object detection track. In _ECCV Workshop on Open Images Challenge_ , 2018. 

- [29] Siying Dong, Mark Callaghan, Leonidas Galanis, Dhruba Borthakur, Tony Savor, and Michael Strum. Optimizing space amplification in rocksdb. In _CIDR_ , 2017. 

