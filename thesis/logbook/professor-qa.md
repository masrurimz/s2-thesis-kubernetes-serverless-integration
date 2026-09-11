# Professor Q&A Preparation

Short replies are Bahasa Indonesia (WhatsApp-ready). Deep answers are English (defense-ready). **Never answer from memory when a linked evidence section exists.** Every number carries its evidence role: `final` = the thesis claim (July bundle), `diagnostic` = replication/supporting.

Categories: contribution | drift | method | data/model | results/statistics | validity | cost | reproducibility | publication

> **Predictor numbers before 2026-09-11 are superseded.** Any answer in this file quoting 4.75%, 6.01%, 17.78%, 14.48%, or a live confidence range of 0.72 to 0.88 refers to the pre-leak-free protocol at horizon 5 with a synthetic-trained model. Current figures: synthetic arm RMSE 5.2% of the mean load, real deployment arm RMSE 39.6% with skill 0.216 against persistence, GRU 29.635 against LSTM 29.917 across three matched seeds, and a linear autoregression at 29.465 on the same window. See QA-016's correction, QA-017's supersession, and the predictor section of `../../results/claims/FINAL_NUMBERS.md`. The H1 and H2 answers are unaffected.

---

## QA-001 — Platform drift (GCP → k3d/Knative)
- Date added: 2026-08-07
- Status: actioned
- Category: drift
- Likely question (Bahasa Indonesia):
  > Kenapa platform penelitiannya berubah dari GCP ke k3d dan Knative? Apa hasilnya masih valid untuk klaim tentang cloud?
- WhatsApp-ready reply (Bahasa Indonesia, 2–4 sentences):
  > Perubahan ini memindahkan primitif cloud yang sama (HPA, KPA, node autoscaler) ke lingkungan lokal yang sepenuhnya terkontrol dan reproducible. Riset ini menguji algoritma keputusan autoscaling, bukan layanan cloud spesifik; semua komponen adalah open-source standar, dan validitasnya diperkuat replikasi independen.
- Deep defense answer (English):
  > The research question targets autoscaling decision logic, not cloud-specific services. k3d + Knative provide the identical primitives — HPA (CPU-based), KPA (concurrency-based), node autoscaler with a configurable provisioning delay (45–120 s) — under full experimental control: node CPU bounding for fairness, deterministic delays, and a testbed the experiment can be re-run on (139 evidence bundles). The GCP move was driven by resource constraints, and the drift is methodologically justified: the comparison S1–S4 isolates the decision algorithm, and every claim is scoped to the tested controllers and testbed.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D1
  - [../../docs/CALIBRATION_GUIDE.md](../../docs/CALIBRATION_GUIDE.md) (fairness calibration)
- Caveat / forbidden overclaim: do not claim "same as GCP" — claim "same primitives, controlled conditions".
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D1

## QA-002 — Synthetic GRU training data
- Date added: 2026-08-07
- Status: actioned
- Category: data/model
- Likely question (Bahasa Indonesia):
  > Kenapa model dilatih dengan data sintetis, bukan langsung pada jejak nyata (ClarkNet/Calgary)?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Data trafik produksi tidak tersedia di awal riset, jadi model dilatih pada arketipe beban sintetis dan divalidasi pada jejak ClarkNet nyata (MAPE 17,78% untuk horizon 5 menit). Fokus tesis adalah keputusan skala, bukan klaim akurasi prediksi — dan akurasi dilaporkan jujur, termasuk keterbatasannya.
- Deep defense answer (English):
  > Training data was synthesized to cover workload archetypes before any real trace was available; HPO improved synthetic RMSE from 6.01% to 4.75%. The model is validated against the real ClarkNet trace at 17.78% MAPE (5-min ahead) and this generalization gap is disclosed (D9) rather than hidden. The thesis does not claim SOTA forecasting; the contribution is the scaling-decision algorithm that consumes forecasts, and the experiment gates on 100% prediction delivery (treatment fidelity), not on forecast accuracy.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D2, D9
  - [../../results/models/gru/](../../results/models/gru/) (training artifacts; RMSE values in FINAL_NUMBERS)
- Caveat: never claim the GRU is accurate on real traffic.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D9

### Follow-up 2026-09-10 — correction plus stronger defense
- What changed: the 17.78% figure is the held-out test-split RMSE of a GRU retrained directly on ClarkNet (85/15 temporal split, 5-minute aggregates, bundle `results/models/gru/2026-02-13_training-clarknet-calgary`). It is not a zero-shot score of the synthetic model. The live experiment model remains the synthetic-trained `gru_model.json`, and that choice is deliberate.
- Why the live model stays synthetic-trained: the Phase B replay load is a window of ClarkNet itself (1995-09-02 04:35:30 to 04:55:00 UTC). That window falls inside the 85% training portion of the same trace (the first 85% of Aug 28 to Sep 3 ends around Sep 2, 22:00). Deploying a ClarkNet-trained predictor for a ClarkNet replay would give S4 memorized traffic and contaminate H2. The synthetic-trained model is therefore a zero-shot predictor, which is the stricter test.
- Literature check (from the archived PDFs, 2026-09-10): ElaX trains its LSTM per workload and evaluates on ClarkNet and Calgary; Mondal 2023 trains GRU, LSTM, and BiLSTM on Google clusterdata-2011-2 sequences; AAPA trains on AAPAset, 300K weakly labeled Azure Functions windows. Training on real traces is the literature norm. Our synthetic-live choice is a design decision motivated by replay contamination, and the thesis must present it as such, not as an oversight.
- WhatsApp-ready reply (revised, Bahasa Indonesia):
  > Model yang dipakai di eksperimen memang sengaja dilatih dengan data sintetis, Pak, karena beban replay-nya adalah ClarkNet itu sendiri. Kalau model dilatih pada trace yang sama dengan yang di-replay, S4 seperti mengerjakan ujian dengan kunci jawaban, jadi perbandingannya jadi tidak adil. Varian yang dilatih langsung pada ClarkNet juga sudah diuji terpisah dengan test split temporal (RMSE 17,78% pada agregasi 5 menit), dan gap itu dilaporkan sebagai keterbatasan.
- Evidence: [../../results/models/gru/2026-02-13_training-clarknet-calgary/report.md](../../results/models/gru/2026-02-13_training-clarknet-calgary/report.md); replay window from `ch3-replay`; split math from `train_gru_real.py` lines 165 to 168.

## QA-003 — What the GRU actually controls (scaling, not routing)
- Date added: 2026-08-07
- Status: actioned
- Category: drift
- Likely question (Bahasa Indonesia):
  > Prediksi GRU itu mengendalikan routing atau scaling? Proposal semula menyebut keduanya.
- WhatsApp-ready reply (Bahasa Indonesia):
  > GRU mengendalikan keputusan scaling (jumlah replica) melalui Algorithm 2 dan weight adjuster; routing tetap berbasis kapasitas. Ini dipilih agar S3 dan S4 hanya berbeda pada input prediksi — atribusi hasil menjadi bersih, dan alasan ini terdokumentasi sebagai Bug 13 dalam protokol.
- Deep defense answer (English):
  > The original proposal envisioned prediction-driven routing; the delivered system uses prediction for scaling decisions (Algorithm 2 + weight adjuster) while traffic routing remains capacity-driven. The methodological justification: S3 (reactive) and S4 (predictive) then differ ONLY in the forecast input to the same control path, so the measured p99 difference is attributable to prediction. This isolation is documented (D3/D5, protocol Bug 13) and is a strength, not a hidden change.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D3, D5
  - [../../thesis/protocol/EXPERIMENT_PROTOCOL.md](../../thesis/protocol/EXPERIMENT_PROTOCOL.md) (Bug 13)
- Caveat: don't say "prediction routes traffic"; say "prediction drives scaling".
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D5

## QA-004 — Forecast horizon 135 s
- Date added: 2026-08-07
- Status: actioned
- Category: method
- Likely question (Bahasa Indonesia):
  > Kenapa horizon prediksi 135 detik?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Horizon 9 langkah × 15 detik = 135 detik, dipilih agar mencakup delay provisioning VM (45–120 detik) plus margin — replica baru tersedia tepat saat beban puncak tiba.
- Deep defense answer (English):
  > The horizon is derived from the system's physical latency: simulated VM boot takes 45–120 s, so a 9-step (135 s) lookahead lets Algorithm 2 request capacity before the peak arrives. This is a calibrated design parameter (recorded in the definitive calibration file, `prediction_horizon=9`), not an arbitrary choice, and it is disclosed in the drift analysis.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D4
  - [../../results/calibration/2026-08-06_definitive-repro.json](../../results/calibration/2026-08-06_definitive-repro.json)
- Caveat: the horizon is tuned for THIS testbed's provisioning delay; do not present it as universal.
- Follow-up reading: [../../docs/CALIBRATION_GUIDE.md](../../docs/CALIBRATION_GUIDE.md)

## QA-005 — Is predictive-hybrid superiority established? (H2)
- Date added: 2026-08-07
- Status: actioned
- Category: results/statistics
- Likely question (Bahasa Indonesia):
  > Apakah hasil eksperimen membuktikan mode predictive (S4) lebih baik daripada reactive (S3)?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Ya, pada bundle definitif: S4 vs S3 pada p99 = 126.0 vs 188.5 ms (p=0.0304, d=−1.26), pelanggaran SLO turun 80%, biaya identik. Arah ini dikonfirmasi replikasi independen (S4 menang 9/10 pasangan). Cakupannya: controller, workload, dan testbed yang diuji.
- Deep defense answer (English):
  > The inferential claim is deliberately narrow: the pre-specified paired one-sided permutation test on the primary p99 metric supports S4 over S3 in the definitive n=5 ClarkNet comparison (p=0.0304, d=−1.26, S4 won 5/5 pairs, SLO violations −80% at identical proxy cost). The independent August replication (n=10, diagnostic tier) confirms the direction (9/10 pairs, pooled p=0.0030) — batch 2 alone reproduced p=0.0304 exactly. This is evidence for the tested controller, workload, calibration, and testbed — not a universal cloud-performance guarantee. Secondary metrics are reported descriptively.
- Evidence:
  - [../../results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/](../../results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/) (role=**final**)
  - [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6, §6b
- Caveat: never present the diagnostic pooled p=0.003 as THE thesis number — the thesis claim is the final bundle's p=0.0304; diagnostic bundles are replication.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b

## QA-006 — H1 is directional, not inferential
- Date added: 2026-08-07
- Status: actioned
- Category: results/statistics
- Likely question (Bahasa Indonesia):
  > Kenapa H1 tidak diuji secara statistik seperti H2?
- WhatsApp-ready reply (Bahasa Indonesia):
  > H1 memetakan trade-off empat arsitektur secara deskriptif (n=1 per skenario karena biaya komputasi 4×): S2 tercepat (77.7 ms) tapi biaya 2,8×, S1 paling lambat. Hipotesis inferensial utama adalah H2, yang diuji dengan desain berpasangan n=5.
- Deep defense answer (English):
  > H1 is an architecture trade-off map (n=1 diagnostic per scenario: S1 2421.3 / S2 77.7 / S3 98.8 / S4 118.2 ms p99; proxy cost 132/394/147/142), establishing direction and motivating the H2 design. The formal inferential test is H2 with a counterbalanced paired n=5 design — powering four scenarios statistically would have multiplied cost without changing the decision (which hybrid to use). This is disclosed (D6) rather than presented as four statistical claims.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D6
  - [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md) (H1 block)
- Caveat: do not call H1 "proven"; it is descriptive/directional.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D6

## QA-007 — Real-trace accuracy failure (GRU generalization)
- Date added: 2026-08-07
- Status: actioned
- Category: data/model
- Likely question (Bahasa Indonesia):
  > Model akurat pada data sintetis tapi MAPE-nya 17,78% pada jejak nyata — apa artinya bagi hasil Anda?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Itu kami laporkan jujur: akurasi bukan klaim tesis. Keputusan skala tetap konsisten unggul meski prediksi tidak sempurna, dan ada guardrail: prediksi yang tidak sehat tidak pernah dipakai (health check, stale-kill, fallback reaktif).
- Deep defense answer (English):
  > The synthetic-to-real generalization gap (4.75% vs 17.78% MAPE) is disclosed (D9) and interpreted correctly: the architecture evaluation does not depend on SOTA forecasting. S4's advantage comes from the decision algorithm converting imperfect forecasts into timely capacity, plus operational guards (health-aware GRU check, stale-kill, reactive fallback). Treatment fidelity (280/280 predictions delivered) proves the treatment ran as designed.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D9
  - [../../results/models/gru/](../../results/models/gru/)
- Caveat: never overclaim GRU accuracy; lead with the honesty.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D9

## QA-008 — Cost: measured billing or model?
- Date added: 2026-08-07
- Status: actioned
- Category: cost
- Likely question (Bahasa Indonesia):
  > Biaya yang dilaporkan itu dari billing cloud nyata atau dari model?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Model biaya proxy: node-seconds Kubernetes + estimasi invokasi serverless, dikalibrasi ke harga pasar. Karena S3 dan S4 memakai anggaran node yang sama, biayanya identik ($163) — artinya S4 mencapai SLO lebih baik tanpa biaya tambahan. Ini dicatat sebagai keterbatasan (D8).
- Deep defense answer (English):
  > The cost figure is a proxy model (node-seconds + serverless invocation estimates at market prices), not cloud billing (D8). Its key property for the thesis: S3 and S4 operate on the same node budget, so equal cost ($163) supports a dominance argument — better SLO at equal cost — without claiming absolute dollar realism. The proxy's limitations are disclosed wherever cost appears.
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D8
  - [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
- Caveat: "cost identical" is proxy-model equality, not billing.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D8

## QA-009 — Threats to validity
- Date added: 2026-08-07
- Status: actioned
- Category: validity
- Likely question (Bahasa Indonesia):
  > Apa ancaman validitas penelitian ini dan bagaimana Anda menanganinya?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Tercatat lengkap di dokumen threats: testbed lokal (bukan cloud nyata), data sintetis, cost proxy, n kecil. Mitigasinya: kalibrasi fairness (CPU node dibatasi), desain berpasangan, replikasi independen, dan pelaporan jujur tanpa menyembunyikan angka yang tidak signifikan.
- Deep defense answer (English):
  > Threats are documented in THREATS_TO_VALIDITY.md: local testbed vs real cloud (mitigated by primitive equivalence + node CPU bounding), synthetic training data (mitigated by real-trace validation + honest generalization reporting), proxy cost (mitigated by equal-budget design), small n (mitigated by paired counterbalanced design + independent replication). The replication batches — including the non-significant one — are reported, which is itself evidence of integrity.
- Evidence:
  - [../../thesis/protocol/THREATS_TO_VALIDITY.md](../../thesis/protocol/THREATS_TO_VALIDITY.md)
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Caveat: do not claim external validity to arbitrary clouds/workloads.
- Follow-up reading: [../../thesis/protocol/THREATS_TO_VALIDITY.md](../../thesis/protocol/THREATS_TO_VALIDITY.md)

## QA-010 — Actual contribution
- Date added: 2026-08-07
- Status: actioned
- Category: contribution
- Likely question (Bahasa Indonesia):
  > Apa kontribusi utama di luar sekadar mengintegrasikan komponen yang sudah ada?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Tiga hal: (1) arsitektur hibrida K8s+serverless dengan prediksi, diuji berpasangan; (2) perlakuan fairness autoscaling yang eksplisit (pembatasan CPU node + kalibrasi r_saturation) sehingga perbandingan HPA vs KPA adil; (3) pipeline eksperimen dengan evidence governance, treatment fidelity, dan replikasi — praktik yang jarang ada di riset autoscaling.
- Deep defense answer (English):
  > Contributions: (1) a hybrid architecture in which GRU forecasts drive scaling while routing stays capacity-driven, evaluated with a pre-specified paired design — showing S4's advantage at equal cost; (2) explicit autoscaler-fairness methodology (node CPU bounding, calibrated r_saturation/alpha) that makes HPA-vs-KPA comparisons defensible — often absent in prior work; (3) an evidence-governed, replicated experiment pipeline (typed registry, treatment-fidelity gating, 139 bundles, independent re-runs), which addresses the reproducibility crisis in autoscaling research. The integrated components exist separately; the contribution is the validated combination and the honest evidence discipline.
- Evidence:
  - Thesis ch01 (hypotheses), ch04 (`sec:replication`)
  - [../../docs/CALIBRATION_GUIDE.md](../../docs/CALIBRATION_GUIDE.md)
  - [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml)
- Caveat: do not claim novelty of individual components; claim the validated integration + methodology.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) (What did not drift)

## QA-011 — Replication batch 1 was not significant
- Date added: 2026-08-07
- Status: actioned
- Category: reproducibility
- Likely question (Bahasa Indonesia):
  > Replikasi batch pertama tidak signifikan (p=0.0958) — bagaimana Anda menjelaskannya?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Batch 1 (4/5 pasangan) menunjukkan varian antar-batch: baseline reaktif berjalan lebih cepat hari itu (131.7 vs 188.5 ms di Juli). Batch 2 mereplikasi hasil Juli hampir persis (p=0.0304, 5/5), dan gabungan n=10 signifikan (p=0.0030, 9/10). Kami melaporkan ketiganya apa adanya — varian itu justru bukti eksperimennya nyata.
- Deep defense answer (English):
  > Three independent batches: July definitive (p=0.0304, 5/5), August batch 1 (p=0.0958, 4/5 — direction correct but baseline ran faster), August batch 2 (p=0.0304, 5/5 — near-exact reproduction), pooled August n=10 (p=0.0030, 9/10). The non-significant batch is disclosed and explained by between-batch variance in the reactive baseline, which is exactly what a defensible replication story looks like: consistent direction, significance when pooled, no cherry-picking.
- Evidence:
  - [../../results/experiments/phase-b/2026-08-07_paired-h2_060200/](../../results/experiments/phase-b/2026-08-07_paired-h2_060200/) (role=diagnostic)
  - [../../results/experiments/phase-b/2026-08-07_paired-h2_104918/](../../results/experiments/phase-b/2026-08-07_paired-h2_104918/) (role=diagnostic)
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Caveat: never hide batch 1; frame it as variance evidence.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b

## QA-012 — Why not pure serverless (S2 was fastest)
- Date added: 2026-08-07
- Status: actioned
- Category: results/statistics
- Likely question (Bahasa Indonesia):
  > Di H1, S2 (serverless murni) paling cepat (77.7 ms). Kenapa tidak full serverless saja?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Karena biayanya 2,8× ($394 vs $147) dan tanpa node autoscaler — risiko cold start dan biaya tinggi saat skala besar. Hibrida prediktif mencapai 126 ms (mendekati S2) dengan biaya sama seperti K8s murni ($163), dan unggul pada uji berpasangan yang lebih ketat.
- Deep defense answer (English):
  > H1 (diagnostic) shows S2's latency advantage (77.7 ms) comes at 2.8× proxy cost (394 vs 147) and without a node autoscaler, which threatens cost and cold-start behavior under scale. S4 (126.0 ms) approaches S2's latency at the same cost as pure K8s ($163) while keeping a node autoscaler — and the paired inferential test compares the two hybrids (the actual design decision), not S2's raw latency. This trade-off framing is the thesis's argument for the hybrid, not for serverless-only.
- Evidence:
  - [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md) (H1 block)
  - [../../results/experiments/phase-b/2026-07-11_scaling_fix_n1/](../../results/experiments/phase-b/2026-07-11_scaling_fix_n1/) (role=diagnostic)
- Caveat: H1 numbers are n=1 diagnostics.
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D6

## QA-013 — Treatment fidelity (did S4 really use predictions?)
- Date added: 2026-08-07
- Status: actioned
- Category: method
- Likely question (Bahasa Indonesia):
  > Bagaimana Anda memastikan S4 benar-benar memakai prediksi GRU, bukan jatuh ke mode reaktif?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Ada gate treatment fidelity: setiap siklus S4 wajib menerima prediksi 100% pada siklus yang memenuhi syarat; jika tidak, run dinyatakan tidak valid dan dibuang. Semua run yang dilaporkan lolos gate ini (280/280 prediksi pada bundle definitif).
- Deep defense answer (English):
  > Treatment fidelity is structurally enforced: S4 runs are invalid unless every eligible cycle received a GRU prediction (`treatment_fidelity.delivered=True`), recorded per run in the bundle; invalid runs are excluded from analysis. The definitive bundle shows 280/280 delivered. Additionally, a health-aware guard refuses to use an unhealthy/stale GRU server rather than silently degrading — the experiment cannot claim a predictive treatment it did not deliver.
- Evidence:
  - Bundle meta/result.json `treatment_fidelity` field, e.g. [../../results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/](../../results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/)
  - [../../results/evidence/README.md](../../results/evidence/README.md) (S4 gate)
- Caveat: fidelity guarantees delivery, not accuracy — keep the two separate in answers.
- Follow-up reading: [../../results/evidence/README.md](../../results/evidence/README.md)

## QA-014 — Why permutation test, why one-sided
- Date added: 2026-08-07
- Status: actioned
- Category: results/statistics
- Likely question (Bahasa Indonesia):
  > Kenapa memakai permutation test satu sisi, bukan t-test berpasangan?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Desainnya berpasangan dengan n kecil; permutation test tidak mensyaratkan normalitas dan menguji langsung pada data. Satu sisi karena H2 bersifat directional (S4 ≤ S3), sesuai pre-registrasi.
- Deep defense answer (English):
  > The paired design with small n rules out normality assumptions; a sign-flip permutation test on paired differences is exact and assumption-light. One-sided because H2 was pre-registered as directional (predictive hybrid ≤ reactive hybrid on p99); the n=3 replication's p floor (1/8 ≈ 0.125) is reported rather than hidden. Counterbalancing handles order effects. The statistics protocol is documented (D13).
- Evidence:
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D13
  - [../../thesis/protocol/EXPERIMENT_PROTOCOL.md](../../thesis/protocol/EXPERIMENT_PROTOCOL.md)
- Caveat: do not present secondary metrics as independently significant claims (multiplicity).
- Follow-up reading: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) D13

## QA-015 — Config drift: default cap 6 vs definitive override 10
- Date added: 2026-08-07
- Status: actioned
- Category: reproducibility
- Likely question (Bahasa Indonesia):
  > Ada dua konfigurasi kapasitas (max 6 vs 10 replica)? Mana yang benar?
- WhatsApp-ready reply (Bahasa Indonesia):
  > Default (6) adalah batas adil HPA untuk S1; eksperimen H2 definitif memakai override 10, tercatat eksplisit di FINAL_NUMBERS dan file kalibrasi. Reproduksi dengan default menghasilkan perbandingan berbeda (S3 meluap ke serverless) — ini kami dokumentasikan sebagai temuan config-drift, bukan disembunyikan, dan file kalibrasi menjamin replikasi memakai input yang sama.
- Deep defense answer (English):
  > `max_k8s_replicas` defaults to 6 (the S1 HPA fairness cap); the definitive paired experiment used the experiment-local override of 10, recorded in FINAL_NUMBERS.md and persisted in `results/calibration/2026-08-06_definitive-repro.json`. A default-cap reproduction produced a qualitatively different comparison (S3 absorbing peaks via serverless overflow) and is documented as a config-drift diagnostic, not evidence. The definitive configuration is now the recorded default for re-triggers — the drift is disclosed in the thesis (ch03, appendix A), the drift report, and calibration docs.
- Evidence:
  - [../../results/calibration/2026-08-06_definitive-repro.json](../../results/calibration/2026-08-06_definitive-repro.json)
  - [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
  - [../../docs/CALIBRATION_GUIDE.md](../../docs/CALIBRATION_GUIDE.md)
- Caveat: never claim default == definitive; the override is the recorded evidence config.
- Follow-up reading: [../../docs/CALIBRATION_GUIDE.md](../../docs/CALIBRATION_GUIDE.md)

## QA-016 — HPO was tuned on ClarkNet (the replay trace)
- Date added: 2026-09-10
- Status: pending (needs one disclosure paragraph in ch03/ch05, and one sensitivity run)
- Category: data/model | validity
- Likely question (Bahasa Indonesia):
  > Hyperparameter GRU-nya dipilih pakai data apa? Kalau pakai ClarkNet, bukankah itu trace yang di-replay juga?
- Facts (verified 2026-09-10):
  - `apps/experiment/experiment/tuning/gru_hpo.py` `_load_data()` accepts only `clarknet` or `calgary`, and the CLI default is `--data clarknet`. There is no synthetic option, so the July HPO necessarily ran on ClarkNet.
  - Bundle: `results/models/gru/2026-07-12_clarknet-15s-hpo` (empty directory, never committed). Objective: mean normalized RMSE plus 2x normalized underprediction on rising edges, expanding-window temporal CV on the first 80% of the trace, 20% holdout, with a promotion gate against persistence and linear-trend baselines.
  - Selected config: learning rate 0.00038, dropout 0.104, hidden 128, sequence 30. The deployed model `data/models/gru_model.json` (2026-07-13, RMSE 6.61) carries that config, and the definitive run's daemon log validates `prediction_horizon=9` for it.
  - The replay window (1995-09-02 04:35:30 to 04:55:00 UTC) falls inside the ClarkNet series used for HPO (Aug 28 to Sep 3), hence inside the HPO development region.
  - Weights are synthetic-trained (FINAL_NUMBERS: retrained on CPU, 18 s, synthetic data).
- Why this does not invalidate the comparison, but must be disclosed:
  - Only S4 consumes a forecast. S3 is prediction-free, so trace-aware tuning can only inflate the arm the thesis claims wins. That is why it must be stated, not discovered by an examiner.
  - Tuning a predictor on the workload it serves mirrors production and the literature: ElaX trains its LSTM per workload, Mondal 2023 trains on Google clusterdata, AAPA trains on Azure-derived AAPAset.
  - Narrow the claim: weights are synthetic-trained, hyperparameters were selected by CV on the deployment trace.
- Cheapest defensible follow-up, in order:
  1. Disclosure paragraph in ch03 (training and HPO provenance) plus one clause in ch05.
  2. Sensitivity run: HPO on Calgary (already supported) to test whether the selected hyperparameters are trace-specific. Same region means the concern is bounded.
  3. Optional: add a synthetic source to `_load_data()`, rerun HPO, report the delta. Training is about 18 s per trial.
  4. Full paired rerun (10 runs) only if the configuration proves trace-specific and cannot be bounded.
- WhatsApp-ready reply (Bahasa Indonesia):
  > Betul Pak, hyperparameter-nya dicari dengan cross-validation pada trace ClarkNet, sementara bobot modelnya dilatih pada data sintetis. Ini kami laporkan terbuka karena dua alasan: pengaruhnya hanya ke S4 (S3 tidak memakai forecast sama sekali), dan menuning prediktor pada beban yang dilayani itu praktik umum di produksi. Yang perlu saya rapikan adalah rumusan klaimnya di naskah, supaya tidak terdengar seolah seluruh pipeline zero-shot.
- Evidence: `apps/experiment/experiment/tuning/gru_hpo.py`; `apps/experiment/experiment/cli.py` line 694; `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/s4-hybrid-predictive_run1/daemon.log`
- Caveat / forbidden overclaim: never say the predictor never saw ClarkNet, or that the pipeline is fully zero-shot. Say: weights trained on synthetic data, hyperparameters selected on the deployment trace, S3 consumes no forecast.

### Correction 2026-09-10 — the HPO data source, and where the replay window now sits
- The inference above ("no synthetic option, so the July HPO necessarily ran on ClarkNet") is contradicted by the study's own record. `results/experiments/tuning/gru_hpo_2026-07-09_224736/study.json` carries `"data_source": "synthetic"`, 30 trials, best objective 4.745 percent. Chapter 4's "on synthetic validation data" matches that record; the run-time `_load_data` accepted only `clarknet` or `calgary`, so one of the two was mislabelled and neither could be trusted from the code alone.
- The deployment artifact is `data/models/gru_model.pt`, not `.json`: schema v2, cell gru, horizon 9, sequence 30, learning rate 3.8e-4, rmse 6.6079, mae 5.0106, upper-envelope coverage 0.899, scaler mean 86.62, standard deviation 37.63, which is synthetic training at `base_rps` 100.
- The leak-free harness resolves the ambiguity structurally. It runs explicit `--data-sources clarknet,synthetic` arms and records the source in each arm's JSON, so "which data selected the model" is now a recorded field, not an inference.
- The replay-window exposure is closed rather than disclosed. In the new study the splits are train 0 to 22500, validation 22539 to 26205, test 26243 to 40315, and the replay window at 15-second samples 28940 to 29020 falls inside the test portion, which is never trained on. The old risk, where the window at 71.8 percent of the series sat inside the development region, no longer exists.
- What remains true for the examiner: the predictor is refit per deployment trace by design, as ElaX and Mondal also do, and only S4 consumes a forecast, so any trace-aware tuning can only inflate the arm the thesis claims wins.

## QA-017 — Why GRU and not LSTM (the architecture swap from ElaX)
- Date added: 2026-09-10
- Status: actioned
- Category: data/model | contribution
- Likely question (Bahasa Indonesia):
  > ElaX memakai LSTM. Kenapa diganti GRU? Apa sudah dibandingkan?
- Decision (2026-09-10): no new experiment. The head-to-head already exists in the literature with protocol and numbers, including one paper we already cite and that reports the comparison we need on real cluster traces. Rerunning it locally would add no information and would not change any testbed result, because only S4 consumes a forecast and S3 is prediction-free.
- Evidence from the archived papers:
  - Mondal et al. 2023 trained LSTM, BiLSTM, and GRU under one protocol (Adam, 200 epochs, batch 512, MSE loss) on real Google clusterdata-2011-2 sequences, with 10 held-out sequences for test. Result: GRU best on all three accuracy metrics at about half the training cost. Best step size GRU 24 against 47 LSTM and 45 BiLSTM; MSE 0.00194 against 0.00195 and 0.00195; RMSE 0.04360 against 0.04367 and 0.04369; MAE 0.03057 against 0.03274 and 0.03101; training time 0.75 s against 1.44 s and 2.41 s; prediction time 0.0651 s against 0.0661 s and 0.0665 s. Their text: the performance of GRU and LSTM does not vary much, and GRU has the most stable performance.
  - Chung et al. 2014, the canonical evaluation: GRU comparable to LSTM across sequence-modeling tasks, and on some datasets faster to converge in CPU time. Now archived as `docs/references/chung-empirical-evaluation-gated-recurrent-2014.pdf`.
  - Cho et al. 2014 introduced the GRU; now archived as `docs/references/cho-learning-phrase-representations-rnn-2014.pdf`.
- Thesis text updated 2026-09-10: `ch02-literature.typ` now carries the Mondal numbers and the two missing citation keys (`@cho2014learning`, `@chung2014empirical`), which were previously named without citations. The same numbers are recorded in the reference manifest.
- Scope note: Mondal compares horizons of 1 and 5 steps at minute granularity, while this thesis forecasts 9 steps at 15 s. The comparison transfers because it isolates the cell type, not the horizon. State that framing if asked.
- WhatsApp-ready reply (Bahasa Indonesia):
  > Betul Pak, LSTM ElaX kami ganti GRU, dan pembandingannya sudah ada di literatur sehingga tidak perlu eksperimen ulang. Mondal dkk. melatih LSTM, BiLSTM, dan GRU dengan protokol yang sama pada data klaster Google, dan GRU unggul di ketiga metrik akurasi dengan waktu latih sekitar separuh. Chung dkk. juga menemukan GRU setara LSTM secara umum. Kami sitasi keduanya di Bab 2, dan karena hanya S4 yang memakai forecast, pilihan sel ini tidak mengubah hasil perbandingan S3 dan S4.
- Evidence: [../../docs/references/REFERENCES.md](../../docs/references/REFERENCES.md) rows for Mondal, Chung, Cho; table 3 of the Mondal PDF.

### Clarification 2026-09-10 — what the Mondal comparison does and does not show
- Inference time is effectively identical in their measurement: 0.0651 s (GRU) against 0.0661 s (LSTM) and 0.0665 s (BiLSTM), about 1.5 percent apart. Do not cite Mondal for an inference advantage. The inference evidence in this thesis is our own live measurement (about 40 ms against the 50 ms target, Chapter 4) plus the parameter-count math (three gate sets against four).
- The data is the same for all three models: Google clusterdata-2011-2 sequences for training, ten held-out sequences for test, one recipe (TensorFlow 2, Adam, 200 epochs, batch 512, MSE). Two differences matter. Hidden size is 50 for LSTM and GRU but 100 for BiLSTM, so the GRU-versus-LSTM arm is capacity-matched while BiLSTM has double capacity and still trails. Each model is reported at its own best step size (GRU 24, LSTM 47, BiLSTM 45), so the accuracy comparison is each model at its best horizon, not one shared horizon.
- Timing is hardware-dependent, and the paper states only TensorFlow 2 on Ubuntu 16.04 virtual machines, with no CPU or GPU model. The absolute seconds are therefore not transferable to this testbed. Quote them only as a within-paper relative comparison.
- Net defensible claim: GRU matches LSTM accuracy at equal capacity and trains faster in that study. Everything else about speed has to come from our own measurements.
- WhatsApp-ready reply (revised, Bahasa Indonesia):
  > Yang terukur berbeda di paper itu adalah waktu latih: 0,75 detik (GRU) vs 1,44 detik (LSTM) pada data dan protokol yang sama, dengan hidden unit sama-sama 50. Waktu inferensinya praktis sama (0,0651 vs 0,0661 detik), jadi klaim kecepatan inferensi tidak kami ambil dari sana, melainkan dari pengukuran kami sendiri di testbed, sekitar 40 ms terhadap target 50 ms. Hardware-nya juga tidak disebutkan di paper, jadi angkanya kami perlakukan sebagai perbandingan relatif, bukan angka absolut.

### Superseded by our own measurement, 2026-09-10
- The literature comparison is no longer the load-bearing justification. The repo now trains GRU and LSTM under one protocol, one trial budget, and one seed set on the amplified ClarkNet series at horizon 9, with the replay window held out, and reports a paired test.
- Measured, three matched seeds, held-out region: GRU RMSE 29.635 ± 0.016 and MAE 22.486 ± 0.079, against LSTM 29.917 ± 0.159 and MAE 23.202 ± 0.243. GRU is better on all three seeds, paired Cohen's d 1.86, bootstrap CI [0.121, 0.422] above zero, one-sided permutation p = 0.1255, the smallest attainable with three pairs. GRU also carries ten times lower seed variance and a much better spike-archetype error, 26.58 against 36.78. Baselines on identical windows: persistence 37.813, linear trend 46.534, seasonal naive 53.688.
- The uncomfortable result to state before an examiner states it: a linear autoregression on the same 30-sample window scores 29.46, within noise of the GRU. So the honest claim is not "GRU is more accurate", it is "GRU and a linear model are equivalent here, and both beat persistence by about 22 percent". If asked why GRU at all, the answer is ElaX lineage plus equivalent accuracy at lower parameter count, not a measured accuracy win.
- A predictor improvement round is queued in `docs/plans/2026-09-10-gru-leakfree-retrain.md` Phase 6, testing longer input windows, calendar features, reversible instance normalization, a log target, a pinball loss, and seed ensembling, each gated on beating the linear benchmark. If none clears that gate, the thesis reports the parity as a limitation and leans on the control layer for novelty.

---

### Actual question event (append when asked)
- Date/time: YYYY-MM-DD HH:MM
- Exact question received: [verbatim]
- Answer given: [verbatim or faithful notes]
- Status: actioned
- New evidence or correction: [link]
