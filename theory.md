<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Rewrite in english

```md
# “For each scale, estimate the standard deviation σ(Δt)…”
How should the standard deviation be computed in this case?
```

Compute the usual **sample** standard deviation, but do it separately for each time scale using the array of “aggregated” deltas.[^1]

## Steps across scales

1. For a chosen scale $\Delta t$, first build the return series at that scale:

- If you have 1‑minute deltas $r_1,\dots,r_N$, then for a 5‑minute scale take sums of consecutive 5‑minute blocks:
$R_k = r_{5(k-1)+1} + \dots + r_{5k}$ (or the log‑return over that interval, if you work with logs).[^1]
- This gives the vector $R^{(\Delta t)} = (R_1,\dots,R_M)$ of length $M \approx N / \Delta t$.[^1]

2. For that vector, compute the sample standard deviation:

$$
\sigma(\Delta t)=\sqrt{\frac{1}{M-1}\sum_{k=1}^{M}\bigl(R_k-\bar R\bigr)^2},
$$

where $\bar R$ is the mean of all $R_k$ at that scale.[^1]

3. Repeat steps 1–2 for different $\Delta t$ (1m, 2m, 4m, 8m, …), obtain $\sigma(\Delta t)$, then plot $\log \sigma(\Delta t)$ versus $\log \Delta t$ and check whether there is power‑law scaling.[^1]

Key point: $\sigma$ is always computed “within windows of that size,” not on the original 1‑minute deltas, if you analyze a scale $\Delta t>1$.[^1]

<div align="center">⁂</div>

[^1]: theory.md

