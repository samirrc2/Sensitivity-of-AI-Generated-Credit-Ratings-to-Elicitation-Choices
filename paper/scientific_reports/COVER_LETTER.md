# Cover letter — Scientific Reports

Dear Editors,

We submit our manuscript, **"Sensitivity of AI-Generated Credit Ratings to Elicitation Choices,"**
for consideration as an Article in *Scientific Reports*.

Large language models are increasingly used as credit, risk, and trading analysts, on the tacit
assumption that a model holds a stable latent assessment that the prompt merely reads out. We test
that assumption directly with a **pre-registered specification-curve design**: a fixed 90-item
firm-profile battery with an objective Altman Z″ benchmark, crossed with a factorial grid of
defensible elicitation choices (provider, model version, temperature, prompt paraphrase, output
format, few-shot exemplars, and answer presentation), replicated across seeds and three model
families (12,960 elicitations). We find that although firm fundamentals explain most rating
variation, the machine credit rating retains economically meaningful sensitivity to defensible
elicitation choices and to residual run-to-run variation, more than to any single tunable design
choice; that the fragility survives honored determinism and cannot be escaped by switching or
pooling vendors; and that the opinion holds no stable rating resolution, crossing the
investment-grade/high-yield line on 27% of matched elicitation pairs. We translate this into the
units a risk function acts on—portfolio turnover, credit spread, and a post-hoc Basel capital
recast—and, to answer the "use real data" objection, we first **demonstrate that naive real-firm LLM
evaluation can be contaminated by memorization** and then show, under a pre-registered fingerprinting
decontamination gate, that **substantial specification instability is also observed on real
anonymized issuers** benchmarked to disclosed agency ratings.

We believe the work fits *Scientific Reports* for three reasons. (i) **Broad relevance**: it concerns
the reliability of AI decision systems in a high-stakes deployment, of interest across machine
learning, finance, and metascience. (ii) **Methodological rigor**: the design is pre-registered, the
analyses are confirmatory with permutation tests and cluster-bootstrap intervals, and the
decontamination gate is, to our knowledge, the first direct evidence that anonymized real-firm LLM
evaluation can be memorization-contaminated even without names in the prompt. (iii) **Full
reproducibility**: the entire 12,960-response corpus, code, and manifest hashes are released; every
reported number regenerates offline and byte-for-byte from the frozen data.

The manuscript is original, not under consideration elsewhere, and all authors approve the
submission. We declare no competing interests. The corresponding author is Robin Chawla
(robin.chawla.cse14@iitbhu.ac.in).

Thank you for your consideration.

Sincerely,
Samir Chincholikar and Robin Chawla
Independent researchers, New York, USA
