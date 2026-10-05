# Awon Aziz

**AI/ML Engineer — I build the operational half of machine learning: evaluation, drift detection, and promotion gates.**

A model isn't finished when it trains well. It's finished when you can prove it still works, detect when it stops, and
refuse to promote a replacement that only looks better. That's the part I work on.

Every repository below ships with tests, a CI run, and numbers I measured myself — including the ones that came out worse
than expected.

---

## Pinned work

### [from-scratch-to-served](https://github.com/AwonAziz/from-scratch-to-served)
LoRA fine-tuning built on a **hand-written NumPy autodiff**, exported to ONNX, quantised to INT8, served behind FastAPI.
Every layer proved against its reference implementation:

| Checked against | Result |
|---|---|
| Central differences, every op | worst error `5.9e-09` |
| `torch.optim`, same trajectories | agree to `1e-09` |
| `nn.MultiheadAttention` | max diff `1.19e-07` |
| Hugging Face `peft`, same weights and factors | **exactly 0.0** |
| ONNX vs PyTorch predictions | **1.0000 agreement** |
| INT8 vs fp32 | **67.8 MB vs 268.6 MB**, 98.4% agreement, −0.002 accuracy |

LoRA reached **0.9217 against 0.9295 for full fine-tuning while training 1.1% of the weights** (McNemar p=0.006). The
finding I did not expect: **LoRA is better calibrated than full fine-tuning** (ECE 0.0180 vs 0.0306) — a low-rank update
keeps weights near the pretrained solution, so if you threshold on a predicted probability the cheap method is the safer
one to ship. 80 tests, one CI job, runs offline on CPU.

### [llm-drift-monitor](https://github.com/AwonAziz/llm-drift-monitor)
Embedding drift, output-quality drift and LLM-as-judge regression tracking for a production-shaped LLM application.
Six drift signals — permutation-calibrated MMD, sliced Wasserstein, domain-classifier AUC, normalised Fréchet, k-NN
novelty, concept gap — where **effect size sets severity and significance only confirms**.

Output quality covers accuracy, macro-F1, ECE/MCE/adaptive-ECE, Brier, AUC, reliability curves, abstention and per-intent
damage, with separate in-scope and out-of-scope baselines. Quality is attributed to the window that *served* the request,
not the window the label arrived in. The triage policy **refuses to retrain on input drift alone** and weights quality
above input shift.

Platform: SQLite system of record with schema migration and upserts, 17 API endpoints, a 5-tab dashboard, Docker and
Makefile. **Six calibration bugs found and pinned by regression tests** — an inflated domain-classifier null, a mismatched
MMD permutation null, a novelty cutoff without leave-one-out, tautological accuracy, a missing judge veto cap, and quality
baselines averaged over out-of-scope traffic. 184 tests, four CI jobs.

### [Hybrid-retrieval](https://github.com/AwonAziz/Hybrid-retrieval)
Sparse TF-IDF and dense retrieval fused with Reciprocal Rank Fusion over Chroma, feeding a two-agent pipeline that
proposes root-cause hypotheses for human review — advisory only, never auto-executes.

Ships an 8-case golden harness scoring Hit@1/Hit@3, hypothesis correctness, confidence calibration, and appropriate
uncertainty on a deliberate no-match case. **The harness caught a regression in my own fusion method**: the LSA fallback
ranked an unrelated incident first on 2 of 8 cases that sparse retrieval alone solved. Diagnosed as insufficient
co-occurrence data at small corpus size, fixed with a corpus-size trust gate that falls back to sparse-only below 50
documents. 38 tests, no API key required.

### [ml-lifecycle-platform](https://github.com/AwonAziz/ml-lifecycle-platform)
MLflow-tracked training and model registry, FastAPI serving (`/predict`, `/health`, `/metrics`, `/drift/status`), and a
model-health dashboard. **Champion/challenger promotion is gated on a measured F1 gain**, and drift is watched with
Population Stability Index, Kolmogorov–Smirnov and Jensen–Shannon divergence — mean PSI **1.66 across five features**
after injected drift. Champion at **F1 0.873 / AUC 0.937** on the project's own synthetic data, under 5 ms p99.

---

## Also here

- **[ai-incident-response-system](https://github.com/AwonAziz/ai-incident-response-system)** — multi-cloud Isolation Forest
  anomaly detection over AWS, Azure and GCP telemetry into a rule engine, triage engine, and notification router.
  Extended by **[agentic-incident-copilot](https://github.com/AwonAziz/agentic-incident-copilot)**, which adds a
  Chroma-backed postmortem knowledge base, hybrid TF-IDF + dense retrieval, two CrewAI agents, a human-review UI and
  Kubernetes manifests.
- **[AI-Pair-Engineer](https://github.com/AwonAziz/AI-Pair-Engineer)** — a four-stage review pipeline where each stage
  receives only the upstream findings relevant to its own job, cutting token cost and blocking context propagation. Every
  model response is schema-validated with retry-and-correct; **submitted code is never executed or interpolated into a
  shell command.**
- **[cleanjobfunnel](https://github.com/AwonAziz/cleanjobfunnel)** — has run unattended across 18 job boards reading
  Greenhouse, Lever, Ashby and SmartRecruiters directly, refreshed every ~20 minutes by a scheduled workflow and
  published to a live dashboard. 476 commits. Built to run my own search, no scraping, no middleman board.
- **Infrastructure labs** — 200+ hands-on commits across
  [DevOps & CI/CD](https://github.com/AwonAziz/Devops-CICD-labs),
  [Red Hat Linux](https://github.com/AwonAziz/RedHat-Linux-Labs) and
  [Cybersecurity](https://github.com/AwonAziz/Cybersecurity-labs).

## How I work

I would rather ship a small system I can measure than a large one I can't. Every project here reports what broke and why —
the LSA regression, the six calibration bugs, the two bugs inside `from-scratch-to-served` — because a repository that only
shows its successes teaches the wrong lesson.

## Background

Diploma in Artificial Intelligence Operations, **EduQual (UK), RQF Level 6** (bachelor's-level equivalent), Al Nafi
International Colleges, 2026 — 90%.

## Contact

Islamabad, Pakistan — **open to remote (EU or US overlap) and relocation to UAE, Saudi Arabia, Qatar, UK or EU.**

[awonaziz786@gmail.com](mailto:awonaziz786@gmail.com) ·
[linkedin.com/in/awonaziz](https://linkedin.com/in/awonaziz) ·
+92 335 5528211