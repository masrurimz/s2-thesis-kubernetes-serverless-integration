# Professor Q&A Preparation

Short replies are Bahasa Indonesia (WhatsApp-ready). Deep answers are English (defense-ready). **Never answer from memory when a linked evidence section exists.** Every number carries its evidence role: `final` = the thesis claim (July bundle), `diagnostic` = replication/supporting.

Categories: contribution | drift | method | data/model | results/statistics | validity | cost | reproducibility | publication

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

---

### Actual question event (append when asked)
- Date/time: YYYY-MM-DD HH:MM
- Exact question received: [verbatim]
- Answer given: [verbatim or faithful notes]
- Status: actioned
- New evidence or correction: [link]
