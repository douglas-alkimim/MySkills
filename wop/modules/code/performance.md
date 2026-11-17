# Code Performance Module

Performance work requires a workload, metric, environment, and budget.

Record baseline evidence when available. Define latency percentiles, throughput, concurrency, memory, CPU, storage, network, or cost limits as relevant. Separate user-visible budgets from internal optimization targets.

Plan measurement before optimization. Identify the critical path, likely bottleneck, data volume, cache behavior, warm/cold states, and representative fixtures. Preserve correctness and security under load.

Acceptance must compare reproducible results to the stated budget and include environment, dataset, command or procedure, sample size, and variance caveats. Do not claim improvement from intuition or a microbenchmark unrelated to the actual workload.
