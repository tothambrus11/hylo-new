# `tcx` — restartable experiment harness

All state is in `runs/<name>/results.jsonl`. The file is append-only, and each line is fsync'd as soon as it is written. Any process can be killed at any moment (Ctrl-C, `kill -9`, a crash or a PC shutdown), and re-running the same command continues where it stopped. A finished measurement is never repeated.

```sh
cd /home/hylo/hylo-tc/research/exp
python3 tcx.py queue specs/A.json specs/B.json   # run experiments in order, detached
python3 tcx.py status                           # progress / rate / ETA of every experiment
python3 tcx.py resume                           # after a reboot or crash: continue the queue
python3 tcx.py stop NAME                        # stop gracefully after the current measurement
python3 tcx.py analyze NAME                     # writes runs/NAME/report.md (also done automatically)
python3 tcx.py semtest --bin ID --configs "a,b;c" --corpus all   # soundness oracle
```

To restart automatically after a reboot, add this line to `crontab -e` (or to `~/.bashrc`):
`@reboot python3 /home/hylo/hylo-tc/research/exp/tcx.py resume`. It is safe to call `resume` while the queue is already running; a lock file prevents a second runner.

## Design choices

- **Frozen binaries.** `tcx.py freeze` copies `tc-bench` and its stdlib bundle to `bin/<sha>/`. A spec names the binary it measures, so rebuilding the compiler never contaminates an experiment.
- **Soundness gate.** Before timing a configuration, the harness compares its semantic dump of every workload with the baseline's. The dump covers the type of every syntax tree, every name binding (including implicit and witness arguments), the witness tables and the diagnostics. A configuration that differs is scored +∞.
- **Balanced, randomized order.** Measurements run repetition by repetition. Within each repetition block, the (config, workload) pairs are shuffled with a fixed seed. Slow drift (thermal throttling, background load) therefore spreads evenly across configurations, and a run stopped halfway still gives balanced data. The 1-minute load average is recorded with every sample.
- **Timing.** Each invocation runs `tc-bench --repeat inner`, pinned with `taskset` to `cpu`, and records the best in-process time per phase. A workload's statistic is the median over invocations. The stdlib phase is timed in every invocation, so the stdlib sample is pooled across all of them.
- **Objective.** The weighted geometric mean, over workloads, of median(config) / median(baseline). Confidence intervals come from a percentile bootstrap that resamples within each (config, workload) cell.
- **Designs:**
  - `full`: every subset of the flags (a 2^n factorial), from which main effects and two-way interactions are computed exactly.
  - `ga`: a deterministic (μ+λ) genetic search, followed by a confirmation stage that measures the top configurations and the winner's ±1-flag neighbourhood with more repetitions. The GA's random stream is seeded and its fitness values are recomputed from the log, so a restarted GA replays the same trajectory and only measures what is missing.
  - `neighborhood`: a given configuration together with its ±1-flag neighbours.
  - `list`: an explicit list of configurations.
- **Report.** `report.md` contains:
  - the ranking with CIs;
  - for each flag of the winner, a leave-one-out test of whether it is significantly needed;
  - for each other flag, an add-one test of whether it would help;
  - the most parsimonious configuration that is statistically indistinguishable from the winner;
  - for full designs, the factorial effects. A positive two-way interaction means the pair's benefits overlap (redundancy).
