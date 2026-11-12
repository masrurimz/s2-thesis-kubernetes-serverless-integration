# AI-perception check, ICAIIC 2027 conference paper (2026-11-12)

Perception evidence only. No detector or judge decides authorship (see `writing-docs-papers` `references/ai-perception.md`).

## Automated scan
`scripts/thesis_paraphrase_audit.py` on the text of `paper/conference.pdf` before the references, against 79 archived references.
No verbatim, fingerprint or reordered-sentence overlap. Zero tell words. Two em-dashes, both template labels ("Abstract—", "Index Terms—"). Burstiness 0.87. Embedding tier skipped (sentence-transformers not installed).

## Blind judges, whole paper
The abstract and all 31 body paragraphs of the six-page build, in four groups of eight. Each group went to three independent judges in different orders, mixed with an obvious AI plant, a subtle AI plant (generic academic register) and a plain human control. Files `full-g*-j*.md`; the key is `answer-key.json`.

Validity: obvious plant 12/12 machine, subtle plant 12/12 machine, control 0/12 machine.

| Paragraph | Judges (H human, M machine, ? uncertain) | Start |
|---|---|---|
| P00 | HHH | Kubernetes adds pods only after the load has risen, so reque… |
| P01 | HHH | A Kubernetes deployment scales on load it has already seen. … |
| P02 | HHH | A hybrid deployment uses both. Reserved machines serve the s… |
| P03 | HHH | ElaX [6] makes the first decision, the pod count, from a for… |
| P04 | HHH | This paper asks whether ElaX's forecast-driven scaling decis… |
| P05 | HHH | The GRU does not beat a linear autoregression. Both hybrids … |
| P06 | HHH | Hybrid execution. The closest systems pair virtual machines … |
| P07 | HHH | Autoscaling with forecasts. HyPA combines reactive and model… |
| P08 | HMH | Serverless cost and cold starts. A survey of serverless reso… |
| P09 | HHH | ElaX. Table II lists what Algorithm 2 keeps from ElaX and wh… |
| P10 | HHH | Fig. 2 shows the system. HAProxy receives all requests and s… |
| P11 | HHH | One ready pod serves r_eff = r_sat · u = 33.3 × 0.5 = 16.65 … |
| P12 | HHH | Algorithm 2 computes the replica count from a load value v, … |
| P13 | H?M | Three choices separate this decision factor from a plain for… |
| P14 | HHH | Pods that cannot be scheduled trigger a node autoscaler. A t… |
| P15 | HHH | Model. A two-layer GRU [24] [25] with 256 hidden units reads… |
| P16 | HHH | Leak-free protocol. The ClarkNet HTTP trace [26] is aggregat… |
| P17 | HHH | Accuracy. Table II reports the error on the test portion at … |
| P18 | HHH | Testbed. Two clusters run on one host under k3d, which runs … |
| P19 | HHH | Workload. The load generator k6 replays a 20-minute ClarkNet… |
| P20 | HHH | Scenarios and batches. Table II lists the four scenarios. In… |
| P21 | HHH | Tests and validity. The primary endpoint is the per-run p99,… |
| P22 | HHH | Cost. We project the cost onto AWS prices. Kubernetes maps t… |
| P23 | HHH | Table II and Fig. 2 compare the four scenarios. The table gi… |
| P24 | HHH | The S4 results need a caveat. This batch ran before the leak… |
| P25 | HHH | Table II and Fig. 2 give the paired results. Batch A favoure… |
| P26 | HHH | The batches differ in host load. In batch B, the peak CPU-bu… |
| P27 | HHH | The forecast changed the replica count. In batch C, S4 made … |
| P28 | HHH | Both arms provisioned about 2.1 dynamic nodes per run, and t… |
| P29 | HHH | One explanation fits these results. Inside a hybrid, Knative… |
| P30 | HHH | Threats to validity. All clusters share one host, so the tes… |
| P31 | ?HM | A capacity-aware router and an ElaX-derived replica scaler r… |

## Retest after rewording P08, P13 and P31
Files `retest-j*.md`. Plants 6/6 machine, control 0/3.
P08 (serverless cost) HHH, P31 (conclusion) HHH, P13 (decision-factor reasoning) HM? with the machine verdict at 0.6, the same split as before the edit.
