# Project-Authored ML Question Bank

This question bank is authored for the Interviewing Agent project. It is intentionally concise, role-oriented, and suitable for deterministic local retrieval.

## Source: project-authored/ml-fundamentals

#### 1) How do bias and variance affect model generalization?

Bias is systematic error caused by restrictive assumptions, while variance is sensitivity to changes in the training sample. A useful model balances both by using validation data, regularization, appropriate capacity, and enough representative training examples.

#### 2) What evidence would tell you that a model is overfitting?

Training performance continues improving while validation performance stalls or degrades. The diagnosis should also consider leakage, unstable cross-validation results, calibration, and performance on important slices rather than only one aggregate metric.

#### 3) When is precision more important than recall, and when is recall more important?

Precision matters when false positives are expensive, while recall matters when missed positives are expensive. The final threshold should be selected using business costs, class prevalence, calibration, and downstream operational capacity.

#### 4) Why should a test set remain untouched during model development?

Repeated decisions based on the test set cause the development process to overfit to it. Validation data supports model selection, while the test set should provide a final estimate of generalization after choices are fixed.

#### 5) What is calibration, and why can a high-ranking model still be poorly calibrated?

Calibration measures whether predicted probabilities match observed frequencies. A model may rank examples correctly and achieve strong AUC while producing probability values that systematically overstate or understate real risk.

## Source: project-authored/production-ml

#### 6) How would you detect feature drift in a production model?

Compare production feature distributions against a trusted baseline using statistical distance, missingness, category changes, and slice-level monitoring. Drift alerts should be connected to model-quality and business metrics because distribution change does not always imply performance loss.

#### 7) What is the difference between data drift and concept drift?

Data drift means the input distribution changes. Concept drift means the relationship between inputs and the target changes, so the same features no longer predict outcomes in the same way.

#### 8) Why can offline model improvement fail to produce online impact?

Offline data may not represent live traffic, the metric may be a weak proxy for the product objective, serving constraints may alter predictions, or user behavior may change after deployment. Online experiments validate causal product impact.

#### 9) What should be monitored for an online inference service?

Monitor request volume, latency percentiles, errors, resource saturation, feature quality, prediction distributions, model-quality proxies, business outcomes, and performance across important user or data slices.

#### 10) When would you choose batch inference instead of online inference?

Batch inference is appropriate when predictions can be prepared ahead of time, freshness requirements are relaxed, and throughput matters more than per-request latency. Online inference is appropriate when predictions require current context or immediate decisions.

## Source: project-authored/genai-rag

#### 11) How does chunk size influence retrieval-augmented generation?

Small chunks improve targeting but may lose context, while large chunks preserve context but can dilute relevance and consume more prompt budget. The correct choice depends on document structure, embedding behavior, retrieval depth, and evaluation results.

#### 12) What is the practical difference between HNSW and IVF-style vector indexes?

HNSW builds a navigable graph that usually gives strong recall and low query latency at higher memory and build cost. IVF partitions vectors into clusters and searches selected partitions, offering tunable speed and memory trade-offs that depend on training and probe settings.

#### 13) How would you evaluate retrieval quality separately from generation quality?

Use labeled queries to measure whether relevant evidence appears in retrieved results with metrics such as recall at k, precision at k, MRR, or nDCG. Evaluate generation afterward for faithfulness, completeness, correctness, and citation support.

#### 14) When is fine-tuning preferable to retrieval augmentation?

Fine-tuning is useful for changing stable behavior, format, style, or task performance. Retrieval is preferable for frequently changing or source-grounded knowledge. Many systems combine both when they need behavioral adaptation and current evidence.

#### 15) What failure modes should a production RAG system monitor?

Monitor empty or irrelevant retrieval, stale documents, access-control leakage, unsupported answers, citation mismatch, excessive latency, prompt injection, embedding drift, and changes in query distribution.

#### 16) What is the difference between supervised fine-tuning and preference optimization?

Supervised fine-tuning trains the model to imitate target responses. Preference optimization uses comparisons or preference signals to make preferred outputs more likely relative to rejected outputs.

#### 17) Why do LLM guardrails need both input and output controls?

Input controls address malicious or disallowed requests before generation. Output controls validate generated content for policy, grounding, format, privacy, and downstream safety because safe input does not guarantee safe output.

## Source: project-authored/recommendation

#### 18) How do exploration and exploitation differ in a recommender system?

Exploitation selects options with the highest expected reward based on current knowledge. Exploration tests uncertain options to learn whether they may perform better, accepting short-term opportunity cost for better future decisions.

#### 19) Why can click-through rate be a misleading recommendation metric?

Clicks may reward sensational or repetitive content and may not represent satisfaction, retention, conversion, or long-term value. It should be paired with guardrails and metrics aligned to the actual product objective.

#### 20) How would you handle cold-start users in a recommendation system?

Use contextual features, popularity or quality priors, onboarding preferences, session behavior, and controlled exploration. The system should transition toward personalized signals as evidence accumulates.

#### 21) What is the difference between candidate generation and ranking?

Candidate generation retrieves a manageable set of plausible items from a large catalog with high recall. Ranking applies richer features and more expensive models to order those candidates for the final experience.

## Source: project-authored/computer-vision

#### 22) Why are convolutions effective for image data?

Convolutions use local connectivity and shared weights, which exploit spatial structure while reducing parameters compared with fully connected layers. Stacking them builds increasingly abstract features.

#### 23) What problem does non-maximum suppression solve in object detection?

Object detectors often produce several overlapping boxes for the same object. Non-maximum suppression keeps high-confidence boxes and removes lower-confidence boxes whose overlap exceeds a selected threshold.

#### 24) How should class imbalance be handled in an image classification problem?

Use representative splitting, suitable metrics, class weighting or sampling, targeted augmentation, threshold tuning, and slice analysis. The approach should reflect whether minority errors have distinct business costs.

#### 25) What is the role of an encoder-decoder architecture in image segmentation?

The encoder extracts increasingly abstract features while reducing spatial resolution. The decoder restores spatial detail to produce dense predictions, often using skip connections to recover fine-grained information.
