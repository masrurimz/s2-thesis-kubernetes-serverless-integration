---
# --- bibliographic record ---
entry_type: misc
title: "Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)"
authors:
  - "Joelle Pineau"
  - "Philippe Vincent-Lamarre"
  - "Koustuv Sinha"
  - "Vincent Larivière"
  - "Alina Beygelzimer"
  - "Florence d&#39;Alché-Buc"
  - "Emily Fox"
  - "Hugo Larochelle"
year: 2020
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2003.12206"
url: "https://arxiv.org/abs/2003.12206"

# --- archive record ---
source_pdf: pineau-improving-reproducibility-ml-research-2021.pdf
source_sha256: 0ea62d8ae3eede31d18faedf4246d59f9c07346df59b4ca99407ef4323d2307f
pdf_pages: 22
converted: 2026-09-13
record_source: arxiv
key_insight: "The reproducibility checklist this work is written against: every reported number needs its data split, its selection criterion, its compute budget, and its code stated. A result without those is not a result."
first_page: "Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program) Joelle Pineau jpineau@cs.mcgill.ca School of Computer Science, McGill University (Mila)"
---
**Improving Reproducibility in Machine Learning Research (** **_A Report from the NeurIPS 2019 Reproducibility Program_ )** 

## **Joelle Pineau** 

jpineau@cs.mcgill.ca 

_School of Computer Science, McGill University (Mila) Facebook AI Research CIFAR_ 

**Philippe Vincent-Lamarre** philvlam@gmail.com 

_Ecole de biblioth`economie et des sciences de l’information, Universit´e de Montr´eal_ 

**Koustuv Sinha** koustuv.sinha@mail.mcgill.ca _School of Computer Science, McGill University (Mila) Facebook AI Research_ **Vincent Larivi`ere** vincent.lariviere@umontreal.ca _Ecole de biblioth´economie et des sciences de l’information, Universit´e de Montr´eal_ **Alina Beygelzimer** beygel@yahoo-inc.com _Yahoo! Research_ **Florence d’Alch´e-Buc** florence.dalche@telecom-paris.fr _T´el´ecom Paris, Institut Polytechnique de France_ **Emily Fox** ebfox@cs.washington.edu _University of Washington Apple_ **Hugo Larochelle** hugolarochelle@google.com _Google CIFAR_ 

# **Abstract** 

One of the challenges in machine learning research is to ensure that presented and published results are sound and reliable. Reproducibility, that is obtaining similar results as presented in a paper or talk, using the same code and data (when available), is a necessary step to verify the reliability of research findings. Reproducibility is also an important step to promote open and accessible research, thereby allowing the scientific community to quickly integrate new findings and convert ideas to practice. Reproducibility also promotes the use of robust experimental workflows, which potentially reduce unintentional errors. In 2019, the Neural Information Processing Systems (NeurIPS) conference, the premier international conference for research in machine learning, introduced a reproducibility program, designed to improve the standards across the community for how we conduct, communicate, and evaluate machine learning research. The program contained three components: a code submission policy, a community-wide reproducibility challenge, and the inclusion of the Machine Learning Reproducibility checklist as part of the paper submission process. In this paper, we describe each of these components, how it was deployed, as well as what we were able to learn from this initiative. 

### **Keywords:** Reproducibility, NeurIPS 2019 

©2020 Joelle Pineau, Philippe Vincent-Lamarre, Koustuv Sinha, Vincent Larivi`ere, Alina Beygelzimer, Florence d’Alch´e-Buc, Emily Fox, Hugo Larochelle. Corresponding author: Joelle Pineau (jpineau@cs.mcgill.ca). 

Pineau et al. 

# **1. Introduction** 

At the very foundation of scientific inquiry is the process of specifying a hypothesis, running an experiment, analyzing the results, and drawing conclusions. Time and again, over the last several centuries, scientists have used this process to build our collective understanding of the natural world and the laws that govern it. However, for the findings to be valid and reliable, it is important that the experimental process be repeatable, and yield consistent results and conclusions. This is of course well-known, and to a large extent, the very foundation of the scientific process. Yet a 2016 survey in the journal Nature revealed that more than 70% of researchers failed in their attempt to reproduce another researcher’s experiments, and over 50% failed to reproduce one of their own experiments (Baker, 2016). 

In the area of computer science, while many of the findings from early years were derived from mathematics and theoretical analysis, in recent years, new knowledge is increasingly derived from practical experiments. Compared to other fields like biology, physics or sociology where experiments are made in the natural or social world, the reliability and reproducibility of experiments in computer science, where the experimental apparatus for the most part consists of a computer designed and built by humans, should be much easier to achieve. Yet in a surprisingly large number of instances, researchers have had difficulty reproducing the work of others (Henderson et al., 2018). 

Focusing more narrowly on machine learning research, where most often the experiment consists of training a model to learn to make predictions from observed data, the reasons for this gap are numerous and include: 

- Lack of access to the same training data / differences in data distribution; 

- Misspecification or under-specification of the model or training procedure; 

- Lack of availability of the code necessary to run the experiments, or errors in the code; 

- Under-specification of the metrics used to report results; 

- Improper use of statistics to analyze results, such as claiming significance without proper statistical testing or using the wrong statistic test; 

- Selective reporting of results and ignoring the danger of adaptive overfitting; 

- Over-claiming of the results, by drawing conclusions that go beyond the evidence presented (e.g. insufficient number of experiments, mismatch between hypothesis & claim). 

We spend significant time and energy (both of machines and humans), trying to overcome this gap. This is made worse by the bias in the field towards publishing positive results (rather than negative ones). Indeed, the evidence threshold for publishing a new positive finding is much lower than that for invalidating a previous finding. In the latter case, it may require several teams showing beyond the shadow of a doubt that a result is false for the research community to revise its opinion. Perhaps the most infamous instance of this is that of the false causal link between vaccines and autism. In short, we would argue that it is always more efficient to properly conduct the experiment and analysis in the first place. 

2 

Improving Reproducibility in Machine Learning Research 

In 2019, the Neural Information Processing Systems (NeurIPS) conference, the premier international conference for research in machine learning, introduced a reproducibility program, designed to improve the standards across the community for how we conduct, communicate, and evaluate machine learning research. The program contained three components: a code submission policy, a community-wide reproducibility challenge, and the inclusion of the Machine Learning Reproducibility checklist as part of the paper submission process. 

In this paper, we describe each of these components, how it was deployed, as well as what we were able to learn from this exercise. The goal is to better understand how such an approach is implemented, how it is perceived by the community (including authors and reviewers), and how it impacts the quality of the scientific work and the reliability of the findings presented in the conference’s technical program. We hope that this work will inform and inspire renewed commitment towards better scientific methodology, not only in the machine learning research community, but in several other research fields. 

# **2. Background** 

There is a growing interest in improving reproducibility across scientific disciplines. A full review of such work is beyond the scope of this paper, but the common motivation is to ensure transparency of scientific findings, a faster and more reliable discovery process, and high confidence in our scientific knowledge. In support of this direction, several biomedical journals agreed in 2014 on a set of principles and guidelines for reporting preclinical research in a way that ensured greater reproducibility (McNutt, 2014). 

There are challenges regarding reproducibility that appear to be unique (or at least more pronounced) in the field of ML compared to other disciplines. The first is an insufficient exploration of the variables (experimental conditions, hyperparameters) that might affect the conclusions of a study. In machine learning, a common goal for a model is to beat the top benchmarks scores. However, it is hard to assert if the aspect of a model claimed to have improved its performance is indeed the factor leading to the higher score. This limitation has been highlighted in a few studies reporting that new proposed methods are often not better than previous implementations when a more thorough search of hyper-parameters is performed (Lucic et al., 2018; Melis et al., 2017), or even when using different random parameter initializations (Bouthillier et al., 2019; Henderson et al., 2018). 

The second challenge refers to the proper documentation and reporting of the information necessary to reproduce the reported results (Gundersen and Kjensmo, 2018). A recent report indicated that 63.5% of the results in 255 manuscripts were successfully replicated (Raff, 2019). Strikingly, this study found that when the original authors provided assistance to the reproducers, 85% of results were successfully reproduced, compared to 4% when the authors didn’t respond. Although a selection bias could be at play (authors who knew their results would reproduce might have been more likely to provide assistance for the reproduction), this contrasts with large-scale replication studies in other disciplines that failed to observe similar improvement when the original authors of the study were involved (Klein et al., 2019). It therefore remains to be established if the field is having a reproduction problem similar to the other fields, or if it would be better described as a reporting problem. 

3 

Pineau et al. 



**Figure 1:** Reproducible Research. Adapted from: https://github.com/WhitakerLab/ReproducibleResearch 

Thirdly, as opposed to most scientific disciplines where uncertainty of the observed effects are routinely quantified, it appears like statistical analysis is seldom conducted in ML research (Forde and Paganini, 2019; Henderson et al., 2018). 

## **2.1 Defining Reproducibility** 

Before going any further, it is worth defining a few terms that have been used (sometimes interchangeably) to describe reproducibility & related concepts. We adopt the terminology from Figure 1, where Reproducible work consists of re-doing an experiment using the same data and same analytical tools, whereas Replicable work considers different data (presumably sampled from similar distribution or method), Robust work assumes the same data but different analysis (such as reimplementation of the code, perhaps different computer architecture), and Generalisable work leads to the same conclusions despite considering different data and different analytical tools. For the purposes of our work, we focus primarily on the notion of Reproducibility as defined here, and assume that any modification in analytical tools (e.g. re-running experiments on a different computer) was small enough as to be negligible. A recent report by the National Academies of Sciences, Engineering, and Medicine, provides more in-depth discussion of these concepts, as well as several recommendations for improving reproducibility broadly across scientific fields (National Academies of Sciences, Engineering, and Medicine, 2019). 

## **2.2 The Open Science movement** 

_“Open Science is transparent and accessible knowledge that is shared and developed through collaborative networks”_ (Vicente-S´aez and Mart´ınez-Fuentes, 2018). In other words, Open science is a movement to conduct science in a more transparent way. This includes making code, data, scientific communications and any other research artifact publicly available and easily accessible over the long-term, thereby increasing the transparency of the research process and improving the reporting quality in scientific manuscripts (Sonnenburg et al., 2007). The implementation of Open science practices has been identified as a core factor that could improve the reproducibility of science (Munaf`o et al., 2017; Gil et al., 2016). As such, the NeurIPS reproducibility program was designed to incorporate elements designed 

4 

Improving Reproducibility in Machine Learning Research 

to encourage researchers to share the artefacts of their research (code, data), in addition to their manuscripts. 

## **2.3 Code submission policies** 

It has become increasingly common in recent years to require the sharing of data and code, along with a paper, when computer experiments were used in the analysis. It is now standard expectation in the Nature research journals for authors to provide access to code and data to readers (Nature Research, 2021). Similarly, the policy at the journal Science specifies that authors are expected to satisfy all reasonable requests for data, code or materials (Science - AAAS, 2018). Within machine learning and AI conferences, the ability to include supplementary material has now been standard for several years, and many authors have used this to provide the data and/or code used to produce the paper. More recently, ICML 2019, the second largest international conference in machine learning has also rolled-out an explicit code submission policy (ICML, 2019). During initial submission for double-blind reviewing, this can be uploaded as supplementary material. For the final submission, it is best practice for data and code to be uploaded to a repository and given a DOI that can be cited. 

## **2.4 Reproducibility challenges** 

Reproducibility tracks have been run prior in database systems conferences such as SIGMOD, as early as 2008 (Manolescu et al., 2008; Bonnet et al., 2011), using the term “repeatability” in lieu of our notion of reproducibility. A notable recommendation was to focus on accepted papers (to spend effort on the work likely to have more impact). Another useful recommendation was to provide wiki page associated with each paper so the community could comment on it, post code, etc. The organizers also found that the vast majority of author’s whose work was included in a repeatability study found the process helpful. 

The 2018 ICLR reproducibility challenge first introduced a dedicated platform to investigate reproducibility of papers for the Machine Learning community. The goal of this first iteration was to investigate reproducibility of empirical results submitted to the 2018 International Conference on Learning Representations (ICLR, 2018). The organizers chose ICLR for this challenge because the timing was right for course-based participants: most participants were drawn from graduate machine learning courses, where the challenge served as the final course project. The choice of ICLR was motivated by the fact that papers submitted to the conference were automatically made available publicly on OpenReview, including during the review period. This means anyone in the world could access the paper prior to selection, and could interact with the authors via the message board on OpenReview. This first challenge was followed a year later by the 2019 ICLR Reproducibility Challenge (Pineau et al., 2019), and followed by 2019 NeurIPS Reproducibility Challenge (Sinha et al., 2020) in this edition. Use of the OpenReview platform allowed a wiki-like interface to provide transparency into the replicability work and a conversation between authors and participants. 

Several less formal activities, including hackathons, course projects, online blogs, opensource code packages, have participated in the effort to carry out re-implementation and 

5 

Pineau et al. 

replication of previous work and should be considered in the same spirit as the effort described here. 

## **2.5 Checklists** 

The Checklist Manifesto presents a highly compelling case for the use of checklists in safetycritical systems (Gawande, 2010). It documents how pre-flight checklists were introduced at Boeing Corporation as early as 1935 following the unfortunate crash of an airplane prototype. Checklists are similarly used in surgery rooms across the world to prevent oversights. Similarly, the WHO Surgical Safety Checklist, which is employed in surgery rooms across the world, has been shown to significantly reduce morbidity and mortality (Clay-Williams and Colligan, 2015). 

In the case of scientific manuscripts, reporting checklists are meant to provide the minimal information that must be included in a manuscript, and are not necessarily exhaustive. The use of checklists in scientific research has been explored in a few instances. Reporting guidelines in the form of checklists have been introduced for a wide range of study design in health research (The EQUATOR Network, 2021), and the Transparency and Openness Promotion (TOP) guidelines have been adopted by multiple journals across disciplines (Nosek et al., 2015). There are now more than 400 checklists registered in the EQUATOR Network. CONSORT, one of the most popular guidelines used for randomized controlled trials was found to be effective and to improve the completeness of reporting for 22 checklist items (Turner et al., 2012). 

The ML checklist described below was significantly influenced by Nature’s Reporting Checklist for Life Sciences Articles (Checklist, 2021). Other guidelines are under development outside of the ML community, namely for the application of AI tools in clinical trials (Liu et al., 2019) and health-care (Collins and Moons, 2019). 

Concurrently with this work, a checklist was developed for AI publications that contain several of the same elements as we outline below, in terms of documenting data, code, methods and experiments (Gundersen et al., 2018). The checklist used at NeurIPS which we describe below is more oriented specifically towards machine learning experiments, with items related to test/validation/train splits, hyper-parameter ranges. 

## **2.6 Other considerations** 

Beyond reproducibility, there are several other factors that affect how scientific research is conducted, communicated and evaluated. One of the best practices used in many venues, including NeurIPS, is that of double-blind reviewing. It is worth remembering that in 2014, the then program chairs Neil Lawrence and Corinna Cortes ran an interesting experiment, by assigning 10% of submitted papers to be reviewed independently by two groups of reviewers (each lead by a different area chair). The results were surprising: overall the reviewers disagreed on 25.9% of papers, but when tasked with reaching a 22.5% acceptance rate, they disagreed on 57% of the list of accepted papers. We raise this point for two reasons. First, to emphasize that the NeurIPS community has for many years already demonstrated an openness towards trying new approaches, as well as looking introspectively on the effectiveness of its processes. Second, to emphasize that there are several steps that come into play when a paper is written, and selected for publication at a high-profile international 

6 

Improving Reproducibility in Machine Learning Research 

venue, and that a reproducibility program is only one aspect to consider when designing community standards to improve the quality of scientific practices. 

# **3. The NeurIPS 2019 code submission policy** 

The NeurIPS 2019 code submission policy, as defined for all authors (see Appendix, Figure 7), was drafted by the program chairs and officially approved by the NeurIPS board in winter 2019 (before the May 2019 paper submission deadline.) 

The most frequent objections we heard to having a code submission policy (at all) include: 

- **Dataset confidentiality** : There are cases where the dataset cannot be released for legitimate privacy reasons. This arises often when looking at applications of ML, for example in healthcare or finance. One strategy to mitigate this limitation is to provide complementary empirical results on an open-source benchmark dataset, in addition to the results on the confidential data. 

- **Proprietary software** : The software used to derive the result contains intellectual property, or is built on top of proprietary libraries. This is of particular concern to some researchers working in industry. Nonetheless, as shown in Figure 2(a), we see that many authors from industry were indeed able to submit code, and furthermore despite the policy, the acceptance rate for papers from authors in industry remained high (higher than authors from academia (Figure 2(b))). By the camera-ready deadline, most submissions from the industry reported having submitted code (Figure 2(a),2(b)). 

- **Computation infrastructure** : Even if data and code are provided, the experiments may require so much computation (time & number of machines) that it is impractical for any reviewer, or in fact most researchers, to attempt reproducing the work. This is the case for work on training very large neural models, for example the AlphaGo game playing agent (Silver et al., 2016) or the BERT language model (Devlin et al., 2018). Nonetheless it is worth noting that both these systems have been reproduced within months (if not weeks) of their release (tia, 2019). 

- **Replication of mistakes** : Having a copy of the code used to produce the experimental results is not a guarantee that this code is correct, and there is significant value in reimplementing an algorithm directly from its description in a paper. This speaks more to the notion of Robustness defined above. It is indeed common that there are mistakes in code (as there may be in proofs for more theoretical papers). Nonetheless, the availability of the code (or proof) can be tremendously helpful to verify or re-implement the method. It is indeed much easier to verify a result (with the initial code or proof), then it is to produce from nothing (this is perhaps most poignantly illustrated by the longevity of the lack of proof for Fermat’s last theorem (Wikipedia, 2020).) 

It is worth noting that the NeurIPS 2019 code submission policy leaves significant time 

- & flexibility, in particular it says that it: _“_ **_expects_** _code_ **_only for accepted papers_** _, and_ 

7 

Pineau et al. 





<!-- Start of picture text -->
(a)<br>(b)<br><!-- End of picture text -->

**Figure 2:** Effect of code submission policy. 2(a) Link to code provided at initial submission and camera-ready, as a function of affiliation of the first and last authors. We observe for industry affiliated authors code is not provided in the initial submission, but later provided after camera ready. Overall, we observe authors from the academia are more prone to release the code of their papers. 2(b) Acceptance rate of submissions as a function of affiliation of the first and last authors. The red dashed line shows the acceptance rate for all submissions. We observe industry affiliated authors have higher chance of acceptance. 

8 

Improving Reproducibility in Machine Learning Research 







<!-- Start of picture text -->
(a) (b)<br><!-- End of picture text -->

**Figure 3:** 3(a) Diagram representing the transition of the code availability from initial submission to camera-ready only for submissions with an author from the industry (first or last). 3(b) Percentage of submissions reporting that they provided code on the checklist subsequently confirmed by the reviewers. 

_only_ **_by the camera-ready deadline_** _”_ . So code submission is not mandatory, and the code is not expected to be used during the review process to decide on the soundness of the work. Reviewers were asked as a part of their assessment to report if code was provided along the manuscript at the initial submission stage. About 40% of authors reported that they had provided code at this stage which was confirmed by the reviewers (if at least one reviewer indicated that the code was provided for each submission) for 71.5% of those submissions (Figure 3(b)). Note that authors are still able to provide code (or a link to code) as part of their initial submission. In Table 1, we provide a summary of code submission frequency for ICML 2019, as well as NeurIPS 2018 and 2019. We observe a growing trend towards more papers adding a link to code, even with only soft encouragement and no coercive measures. 

While the value of having code extends long beyond the review period, it is useful, in those cases where code is available during the review process, to know how it is used and perceived by the reviewers. When surveying reviewers at the end of the review period, we found: 

_Q. Was code provided (e.g. in the supplementary material)?_ Yes: 5298 

_If provided, did you look at the code?_ Yes: 2255 

_If provided, was the code useful in guiding your review?_ Yes: 1315 

_If not provided, did you wish code had been available?_ Yes: 3881 

We were positively surprised by the number of reviewers willing to engage with this type of artefact during the review process. Furthermore, we found that the availability of code at submission (as indicated on the checklist) was positively associated with the reviewer score ( _p <_ 1 _e −_ 08). 

9 

Pineau et al. 

|Conference|#<br>papers<br>submitted|%<br>papers<br>accepted|% papers w/code<br>at submission|% papers w/code<br>at camera-ready|Code submission policy|
|---|---|---|---|---|---|
|NeurIPS 2018|4856|20.8%||_<_50%|“Authors may submit up to<br>100MB of supplementary ma-<br>terial, such as proofs, deriva-<br>tions, data, or source code.”|
|ICML 2019|3424|22.6%|36%|67%|“To foster reproducibility, we<br>highly encourage authors to<br>submit code. Reproducibility<br>of results and easy availability<br>of code will be taken into ac-<br>count in the decision-making<br>process.”|
|NeurIPS 2019|6743|21.1%|40%|74.4%|“We expect (but not require)<br>accompanying code to be sub-<br>mitted with accepted papers<br>that contribute and present<br>experiments with a new algo-<br>rithm.” See Appendix, Fig. 7|



**Table 1:** Code submission frequency for recent ML conferences. Source for number of papers accepted and acceptance rates: https://github.com/lixin4ever/Conference-Acceptance-Rate. ICML 2019 numbers reproduced from the ICML 2019 Code-at-Submit-Time Experiment. 

# **4. The NeurIPS 2019 Reproducibility Challenge** 

The main goal of this challenge is to provide independent verification of the empirical claims in accepted NeurIPS papers, and to leave a public trace of the findings from this secondary analysis (Sinha et al., 2020). The reproducibility challenge officially started on Oct.31 2019, right after the final paper submission deadline, so that participants could have the benefit of any code submission by authors. By this time, the authors’ identity was also known, allowing collaborative interaction between participants and authors. We used OpenReview (OpenReview.net, 2021) to enable communication between authors and challenge participants. 

As shown in Table 2, a total of 173 papers were claimed for reproduction. This is a 92% increase since the last reproducibility challenge at ICLR 2019 (Pineau et al., 2019). We had participants from 73 different institutions distributed around the world (see Appendix, Figure 8), including 63 universities and 10 industrial labs. Institutions with the most participants came from 3 continents and include McGill University (Canada), KTH (Sweden), Brown University (US) and IIT Roorkee (India). In those cases (and several others), high participation rate occurred when a professor at the university used this challenge as a final course project. 

All reports submitted to the challenge are available on OpenReview<sup>1</sup> for the community; in many cases with a link to the reimplementation code. The goal of making these available is to two-fold: first to give examples of reproducibility reports so that the practice becomes more widespread in the community, and second so that other researchers can benefit from the knowledge, and avoid the pitfalls that invariably come with reproducing another team’s work. Most reports produced during the challenge offer a much more detailed & nuanced account of their efforts, and the level of fidelity to which they could reproduce the methods, 

> 1. https://openreview.net/group?id=NeurIPS.cc/2019/Reproducibility ~~C~~ hallenge 

10 

Improving Reproducibility in Machine Learning Research 

|Conference|#<br>papers<br>submitted|Acceptance<br>rate|#<br>papers<br>claimed|#<br>par-<br>ticipating<br>institutions|#<br>reports<br>reviewed|
|---|---|---|---|---|---|
|ICLR 2018|981|32.0|123|31|n/a|
|ICLR 2019|1591|31.4|90|35|26|
|NeurIPS 2019|6743|21.1|173|73|84|



**Table 2:** Participation in the Reproducibility Challenge. Source for number of papers accepted and acceptance rates: https://github.com/lixin4ever/Conference-Acceptance-Rate 

results & claims of each paper. Similarly, while some readers may be looking for a “reproducibility score”, we have not found that the findings of most reproducibility studies lend themselves to such a coarse summary. 

Once submitted, all reproducibility reports underwent a review cycle (by reviewers of the NeurIPS conference), to select a small number of high-quality reports, which are published in the Sixth edition (Issue 2)<sup>2</sup> of the journal ReScience (ReScience C, 2020; Sinha et al., 2020). This provides a lasting archival record for this new type of research artefact. 

# **5. The NeurIPS 2019 ML reproducibility checklist** 

The third component of the reproducibility program involved use of the Machine Learning reproducibility checklist (see Appendix, Figure 9). This checklist was first proposed in late 2018, at the NeurIPS conference, in response to findings of recurrent gaps in experimental methodology found in recent machine learning papers. An earlier version (v.1.1) was first deployed as a trial with submission of the final camera-ready version for NeurIPS 2018 papers (due in January 2019); this initial test allowed collection of feedback from authors and some minor modifications to the content of the checklist (mostly edited for clarity and reduced some redundant questions). The edited version 1.2 was then deployed during the NeurIPS 2019 review process, and authors were obliged to fill it both at the initial paper submission phase (May 2019), and at the final camera-ready phase (October 2019). This allowed us to analyze any change in answers, which presumably resulted from the review feedback (or authors’ own improvements of the work). The checklist was implemented on the CMT platform; each question included a multiple choice “Yes, No, not applicable”, and an (optional) open comment field. 

Figure 4 shows the initial answers provided for each submitted paper. It is reassuring to see that 97% of submissions are said to contain Q#. _A clear description of the mathematical setting, algorithm, and/or model._ Since we expect all papers to contain this, the 3% no/na answers might reflect margin of error in how authors interpreted the questions. Next, we notice that 89% of submissions answered to the affirmative when asked Q#. _For all figures and tables that present empirical results, indicate if you include: A description of how experiments were run_ . This is reasonably consistent with the fact that 9% of NeurIPS 2019 submissions indicated “Theory” as their primary subject area, and thus may not contain empirical results. 

One set of responses that raises interesting questions is the following trio: 

> 2. https://rescience.github.io/read/#issue-2-neurips-2019-reproducibility-challenge 

11 

Pineau et al. 



**Figure 4:** Author responses to all checklist questions for NeurIPS 2019 submitted papers. 

Q#. _A clear definition of the specific measure or statistics used to report results._ 

- Q#. _Clearly defined error bars._ 

Q#. _A description of results with central tendency (e.g. mean) & variation (e.g. stddev)._ 

In particular, it seems surprising to have 87% of papers that see value in clearly defining the metrics and statistics used, yet 36% of papers judge that error bars are not applicable to their results. 

As shown in Figure 5, many checklist answers appear to be associated with a higher acceptance rate when the answer is “yes”. However, it is too early to rule out potential covariates (e.g. paper’s topic, reviewer expectations, etc.) At this stage, it is encouraging that answering “no” to any of the questions is not associated with a higher acceptance rate. There seems to be a higher acceptance rate associated with “NA” responses on a subset of questions related to “Figures and tables”. Although it is still unclear at this stage why this effect is observed, it disappears when we only include manuscripts for which the reviewers indicated that the checklist was useful for the review. 

Finally, it is worth considering the reviewers’ point of view on the usefulness of the ML checklist to assess the soundness of the papers. When asked _“Were the Reproducibility Checklist answers useful for evaluating the submission?”_ , 34% responded Yes. 

We also note, as shown in Figure 6, that reviewers who found the checklist useful gave higher scores. And that those who found the checklist useful or not useful were more confident in their assessment than those who had not read the checklist. Finally, papers where the checklist was assessed as useful were more likely to be accepted. 

12 

Improving Reproducibility in Machine Learning Research 



**Figure 5:** Acceptance rate per question. The x-axis corresponds to the question number on the checklist. The numbers within each bar show the number of submissions for each answer. See Fig. 4 (and in Appendix Fig. 9) for text corresponding to each Question # (x-axis). The red dashed line shows the acceptance rate for all submissions. 



**Figure 6:** Perceived usefulness of the ML reproducibility checklist vs the review outcomes. (a) Effect on the paper score (scale 1-10). (b) Effect on the reviewer confidence score (scale of 1 to 5, where 1 is lowest). (c) Effect on the final accept/reject decision. 

13 

Pineau et al. 

# **6. Discussion** 

We presented a summary of the activities & findings from the NeurIPS 2019 reproducibility program. Perhaps the best way to think of this effort is as a case study showing how three different mechanisms (code submission, reproducibility challenge, reproducibility checklist) can be incorporated into a conference program in an attempt to improve the quality of scientific contributions. At this stage, we do not have concluding evidence that these processes indeed have an impact on the quality of the work or of the papers that are submitted and published. 

However we note several encouraging indicators: 

- The number of submissions to NeurIPS increased by nearly 40% this year, therefore we can assume the changes introduced did not result in a significant drop of interest by authors to submit their work to NeurIPS. 

- The number of authors willingly submitting code is quickly increasing, from less than 50% a year ago, to nearly 75%. It seems a code submission policy based on voluntary participation is sufficient at this time. We are not necessarily aiming for 100% compliance, as there are some cases where this may not be desirable (e.g. pre-processing script for confidential data). 

- The number of reviewers indicating that they consulted the code, or wished to consult it is in the 1000’s, indicating that this is useful in the review process. 

- The number of participants in the reproducibility challenge continues to increase, as does the number of reproducibility reports, and reviewers of reproducibility reports. This suggests that an increasing segment of the community is willing to participate voluntarily in secondary analysis of research results. 

- One-third of reviewers found the checklist answers useful, furthermore reviewers who found the checklist useful gave higher scores to the paper, which suggests the checklist’s use is useful for both reviewers and authors. 

The work leaves several questions open, which would require further investigation, and a careful study design to elucidate: 

- What is the long-term value (e.g. reproducibility, robustness, generalization, impact of follow-up work) of the code submitted? 

- What is the effect of different incentive mechanisms (e.g. cash payment, conference registration, a point/badge system) on the participation rate & quality of work in the reproducibility challenge? 

- What is the benefit of using the checklist for authors? 

- What is the accuracy of the ML checklist answers (for each question) when filled by authors? 

- What is the measurable effect of the checklist on the quality of the final paper, e.g. in terms of soundness of results, clarity of writing? 

14 

Improving Reproducibility in Machine Learning Research 

- What is the measurable effect of the checklist on the review process, in terms of reliability (e.g. inter-rater agreement) and efficiency (e.g. need for response/rebuttal, discussion time)? 

A related direction to explore is the development of tools and platforms that enhance reproducibility. Throughout this work we have focused on processes & guidelines, but stayed away from prescribing any infrastructure or software tooling to support reproducibility. Many software tools, such as Docker<sup>3</sup> , ReproZip<sup>4</sup> , WholeTale<sup>5</sup> can encapsulate operating systems components, code, experimental variables and data files into a single package. Standardization of such tools would help sharing of information and improve ease of reproducibility. A comparison of different tools is provided in (Isdahl and Gundersen, 2019). We hope to see in the future some level of convergence on standadized tools for supporting reproducibility. 

A few other CS conferences have developed reproducibility programs, and explored mechanisms beyond what we introduced at NeurIPS 2019. For example, the ACM Multimedia conference, under the guidance of a Reproducibility Committee, has outlined specific reproducibility objectives, and included in 2021 a specific call for reproducibility papers<sup>6</sup> . The ACM and its affiliated events has also introduced Badges<sup>7</sup> that can been attributed to papers to indicate when they meet pre-defined standards of Artifact availability, Reproducibility and Replication. Beyond the CS community, other concrete suggestions have been provided to increase the trustworthiness in scientific findings (Hall Jamieson et al., 2019). 

One additional aspect worth emphasizing is the fact that achieving reproducible results across a research community, whether NeurIPS or another, requires a significant cultural and organizational changes, not just a code submission policy or a checklist. The initiative described here is just one step in helping the community adopt better practices, in terms of conducting, communicating, and evaluating scientific research. The NeurIPS community is far from alone in looking at this problem. Several workshops have been held in recent years to discuss the issue as it pertains to machine learning and computer science (SIGCOMM, 2017; ICML, 2017, 2018; ICLR, 2019). Specific calls for reproducibility papers have been issued (ECIR, 2020). An open-access peer-reviewed journal is dedicated to such papers (ReScience C, 2020), which was used to publish select reports in ICLR 2019 Reproducibility Challenge (Pineau et al., 2019) and NeurIPS 2019 Reproducibility Challenge (Sinha et al., 2020). And in the process, many labs are changing their practices to improve reproducibility of their own results. 

While this report focuses on the reproducibility program deployed for NeurIPS 2019, we expect many of the findings and recommendations to be more broadly applicable to other conferences and journals that represent machine learning research. Several other venues have already started defining code submission policies, though compliance varies. The ML checklist was crafted by consulting several other checklists, and could be adapted to other venues, as was done already for ICML 2020 and EMNLP 2020. The 2020 version of the ML 

> 3. `https://www.docker.com/` 

> 4. `https://www.reprozip.org/` 

> 5. `https://wholetale.org/` 

> 6. `https://project.inria.fr/acmmmreproducibility/` 

> 7. `https://www.acm.org/publications/policies/artifact-review-and-badging-current` 

15 

Pineau et al. 

reproducibility challenge was also extended to cover papers accepted at 7 leading conferences (NeurIPS, ICML, ICLR, CVPR, EMNLP, CVPR and ECCV). We do not foresee any major obstacles extending this to journal venues, where the longer review time and repeated interactions with the reviewers provide even more opportunity to meet high standards of reproducibility. 

# **Acknowledgments** 

We thank the NeurIPS board and the NeurIPS 2019 general chair (Hanna Wallach) their unfailing support of this initiative. Without their courage and spirit of experimentation, none of this work would have been possible. We thank the many authors who submitted their work to NeurIPS 2019 and agreed to participate in this large experiment. We thank the program committee (reviewers, area chairs) of NeurIPS 2019 who not only incorporated the reproducibility checklist into their task flow, but also provided feedback about its usefulness. We thank Zhenyu (Sherry) Xue for preparing the data on NeurIPS papers & reviews for the analysis presented here. We thank the OpenReview team (in particular Andrew McCallum, Pam Mandler, Melisa Bok, Michael Spector and Mohit Uniyal) who provided support to host the results of the reproducibility challenge. We thank CodeOcean (in particular Xu Fei) for providing free compute resources to reproducibility challenge participants. Thank you to Robert Stojnic and Yolanda Gil for valuable comments on an early version of the manuscript. Finally, we thank the several participants of the reproducibility challenge who dedicated time and effort to verify results that were not their own, to help strengthen our understanding of machine learning, and the types of problems we can solve today. 

# **References** 

- Elf opengo: an analysis and open reimplementation of alphazero. In _Proceedings of the 36th International Conference on Machine Learning_ , 2019. 

- Monya Baker. 1,500 scientists lift the lid on reproducibility. _Nature News_ , 533 (7604):452, May 2016. doi: 10.1038/533452a. URL `https://www.nature.com/news/ 1-500-scientists-lift-the-lid-on-reproducibility-1.19970` . 

- Philippe Bonnet, Stefan Manegold, Matias Bjørling, Wei Cao, Javier Gonzalez, Joel Granados, Nancy Hall, Stratos Idreos, Milena Ivanova, Ryan Johnson, David Koop, Tim Kraska, Ren´e M¨uller, Dan Olteanu, Paolo Papotti, Christine Reilly, Dimitris Tsirogiannis, Cong Yu, Juliana Freire, and Dennis Shasha. Repeatability and workability evaluation of sigmod 2011. _SIGMOD Rec._ , 40(2):45–48, September 2011. ISSN 0163-5808. doi: 10.1145/2034863.2034873. URL `https://doi.org/10.1145/2034863.2034873` . 

- Xavier Bouthillier, C´esar Laurent, and Pascal Vincent. Unreproducible research is reproducible. In Kamalika Chaudhuri and Ruslan Salakhutdinov, editors, _Proceedings of the 36th International Conference on Machine Learning_ , volume 97 of _Proceedings of Machine Learning Research_ , pages 725–734, Long Beach, California, USA, 09–15 Jun 2019. PMLR. URL `http://proceedings.mlr.press/v97/bouthillier19a.html` . 

16 

Improving Reproducibility in Machine Learning Research 

- Nature Checklist. Nature checklist. 2021. URL `https://media.nature.com/original/ nature-assets/ng/journal/v49/n10/extref/ng.3933-S2.pdf` . 

- Robyn Clay-Williams and Lacey Colligan. Back to basics: Checklists in aviation and healthcare. _BMJ Quality & Safety_ , 24(7):428–431, July 2015. ISSN 2044-5415, 2044-5423. doi: 10.1136/bmjqs-2015-003957. 

- Gary S. Collins and Karel G. M. Moons. Reporting of artificial intelligence prediction models. _The Lancet_ , 393(10181):1577–1579, April 2019. ISSN 0140-6736, 1474-547X. doi: 10.1016/S0140-6736(19)30037-6. 

- Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. _arXiv:1810.04805 [cs]_ , October 2018. 

- ECIR. Call for Reproducibility papers. April 2020. URL `ecir2020.org` . 

- Jessica Zosa Forde and Michela Paganini. The Scientific Method in the Science of Machine Learning. _arXiv:1904.10922 [cs, stat]_ , April 2019. URL `http://arxiv.org/abs/1904. 10922` . 

- Atul Gawande. _Checklist manifesto, the (HB)_ . Penguin Books India, 2010. 

- Yolanda Gil, C´edric H. David, Ibrahim Demir, Bakinam T. Essawy, Robinson W. Fulweiler, Jonathan L. Goodall, Leif Karlstrom, Huikyo Lee, Heath J. Mills, Ji-Hyun Oh, Suzanne A. Pierce, Allen Pope, Mimi W. Tzeng, Sandra R. Villamizar, and Xuan Yu. Toward the geoscience paper of the future: Best practices for documenting and sharing research from data to software to provenance. _Earth and Space Science_ , 3(10):388–415, 2016. doi: https://doi.org/10.1002/2015EA000136. URL `https://agupubs.onlinelibrary. wiley.com/doi/abs/10.1002/2015EA000136` . 

- Odd Erik Gundersen and Sigbjørn Kjensmo. State of the art: Reproducibility in artificial intelligence. In _Thirty-second AAAI conference on artificial intelligence_ , 2018. 

- Odd Erik Gundersen, Yolanda Gil, and David W Aha. On reproducible ai: Towards reproducible research, open science and digital scholarship in ai publications. _AI Magazine_ , 39 (3), 2018. 

- Kathleen Hall Jamieson, Marcia McNutt, Veronique Kiermer, and Richard Sever. Signaling the trustworthiness of science. _PNAS_ , 116(29):19231–19236, 2019. 

- Peter Henderson, Riashat Islam, Philip Bachman, Joelle Pineau, Doina Precup, and David Meger. Deep reinforcement learning that matters. In _Thirty-Second AAAI Conference on Artificial Intelligence_ , 2018. 

- ICLR. ICLR 2018 Reproducibility Challenge. 2018. URL `https://www.cs.mcgill.ca/ ~`<sup>`jpineau/ICLR2018-ReproducibilityChallenge.html`.</sup> 

- ICLR. Reproducibility in Machine Learning Workshop. 2019. URL `https://sites. google.com/view/icml-reproducibility-workshop/home` . 

17 

Pineau et al. 

- ICML. Reproducibility in Machine Learning Workshop. 2017. URL `https://sites.google.com/view/icml-reproducibility-workshop/icml2017/ talks-and-abstracts` . 

- ICML. Reproducibility in Machine Learning Workshop. 2018. URL `https://sites. google.com/view/icml-reproducibility-workshop/icml2018/home` . 

- ICML. Call for papers. 2019. URL `https://icml.cc/Conferences/2019/CallForPapers` . 

- Ricahrd Isdahl and Odd Erik Gundersen. Out-of-the-box reproducibility: A survey of machine learning platforms. In _15th International Conference on eScience_ , 2019. 

- Richard A Klein, Corey L Cook, Charles R Ebersole, Christine Vitiello, Brian A Nosek, Christopher R Chartier, Cody D Christopherson, Samuel Clay, Brian Collisson, Jarret Crawford, et al. Many labs 4: Failure to replicate mortality salience effect with and without original author involvement. 2019. 

- Xiaoxuan Liu, Livia Faes, Melanie J Calvert, and Alastair K Denniston. Extension of the consort and spirit statements. _The Lancet_ , 394(10205):1225, 2019. 

- Mario Lucic, Karol Kurach, Marcin Michalski, Sylvain Gelly, and Olivier Bousquet. Are gans created equal? a large-scale study. In _Advances in neural information processing systems_ , pages 700–709, 2018. 

- Ioana Manolescu, Loredana Afanasiev, Andrei Arion, Jens Dittrich, Stefan Manegold, Neoklis Polyzotis, Karl Schnaitter, Pierre Senellart, Spyros Zoupanos, and Dennis Shasha. The repeatability experiment of sigmod 2008. _ACM SIGMOD Record_ , 37(1):39–45, 2008. 

- Marcia McNutt. Journals unite for reproducibility. _Science_ , 346(6210):679, 2014. 

- G´abor Melis, Chris Dyer, and Phil Blunsom. On the state of the art of evaluation in neural language models. _arXiv preprint arXiv:1707.05589_ , 2017. 

- Marcus R Munaf`o, Brian A Nosek, Dorothy VM Bishop, Katherine S Button, Christopher D Chambers, Nathalie Percie Du Sert, Uri Simonsohn, Eric-Jan Wagenmakers, Jennifer J Ware, and John PA Ioannidis. A manifesto for reproducible science. _Nature human behaviour_ , 1(1):1–9, 2017. 

- National Academies of Sciences, Engineering, and Medicine. _Reproducibility and replicability in science_ . National Academies Press, 2019. 

- Nature Research. Reporting standards and availability of data, materials, code and protocols, 2021. URL `https://www.nature.com/nature-research/editorial-policies/ reporting-standards` . 

- Brian A Nosek, George Alter, George C Banks, Denny Borsboom, Sara D Bowman, Steven J Breckler, Stuart Buck, Christopher D Chambers, Gilbert Chin, Garret Christensen, et al. Promoting an open research culture. _Science_ , 348(6242):1422–1425, 2015. 

- OpenReview.net. Neurips 2019 reproducibility challenge, 2021. URL `https://openreview. net/group?id=NeurIPS.cc/2019/Reproducibility_Challenge` . 

18 

Improving Reproducibility in Machine Learning Research 

- Joelle Pineau, Koustuv Sinha, Genevieve Fried, Rosemary Nan Ke, and Hugo Larochelle. ICLR Reproducibility Challenge 2019. _ReScience C_ , 5(2):5, May 2019. doi: 10.5281/ zenodo.3158244. URL `https://zenodo.org/record/3158244/files/article.pdf` . 

- Edward Raff. A step toward quantifying independently reproducible machine learning research. In _Advances in Neural Information Processing Systems_ , pages 5486–5496, 2019. 

- ReScience C. The rescience journal. reproducible science is good. replicated science is better., 2020. URL `http://rescience.github.io/` . 

- Science - AAAS. Science journals: Editorial policies., 2018. URL `https://www. sciencemag.org/authors/science-journals-editorial-policies` . 

- SIGCOMM. Reproducibility ’17: Proceedings of the reproducibility workshop. 2017. URL `https://dl.acm.org/doi/proceedings/10.1145/3097766` . 

- David Silver, Aja Huang, Chris J Maddison, Arthur Guez, Laurent Sifre, George Van Den Driessche, Julian Schrittwieser, Ioannis Antonoglou, Veda Panneershelvam, Marc Lanctot, et al. Mastering the game of go with deep neural networks and tree search. _nature_ , 529(7587):484, 2016. 

- Koustuv Sinha, Joelle Pineau, Jessica Forde, Rosemary Nan Ke, and Hugo Larochelle. NeurIPS 2019 Reproducibility Challenge. _ReScience C_ , 6(2):11, May 2020. doi: 10.5281/ zenodo.3818627. URL `https://zenodo.org/record/3818627/files/article.pdf` . 

- SAk¸ren Sonnenburg, Mikio L Braun, Cheng Soon Ong, Samy Bengio, Leon Bottou, Geoffrey<sup>˜</sup> Holmes, Yann LeCun, Klaus-Robert MAˇzller, Fernando Pereira, Carl Edward Rasmussen,<sup>˜</sup> et al. The need for open source software in machine learning. _Journal of Machine Learning Research_ , 8(Oct):2443–2466, 2007. 

- The EQUATOR Network. Enhancing the quality and transparency of health research., 2021. URL `https://www.equator-network.org/` . 

- Lucy Turner, Larissa Shamseer, Douglas G Altman, Laura Weeks, Jodi Peters, Thilo Kober, Sofia Dias, Kenneth F Schulz, Amy C Plint, and David Moher. Consolidated standards of reporting trials (consort) and the completeness of reporting of randomised controlled trials (rcts) published in medical journals. _Cochrane Database of Systematic Reviews_ , (11), 2012. 

- Rub´en Vicente-S´aez and Clara Mart´ınez-Fuentes. Open science now: A systematic literature review for an integrated definition. _Journal of business research_ , 88:428–436, 2018. 

- Wikipedia. Fermat’s Last Theorem. March 2020. URL `https://en.wikipedia.org/wiki/ Fermat%27s_Last_Theorem` . Page Version ID: 944945734. 

19 

Pineau et al. 



**Figure 7:** The NeurIPS 2019 code submission policy. Reproduced (with permission) from: [ADD URL 

20 

Improving Reproducibility in Machine Learning Research 



**Figure 8:** NeurIPS 2019 Reproducibility Challenge Participants by geographical location. 

21 

Pineau et al. 



**Figure 9:** The Machine Learning Reproducibility Checklist, version 1.2, used during the NeurIPS 2019 review process. 

22 

