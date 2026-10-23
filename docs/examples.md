# Examples

This page shows how to create CommonRoad scenarios for different purposes. It assumes you have already downloaded the source dataset; if not, see [Getting Started](getting_started.md).

## CLI Examples

For a detailed explanation of the CLI arguments, refer to [CLI Usage](cli.md).

### Converting Scenarios for Learning

For learning-based motion planners (e.g., reinforcement learning), we recommend scenarios that

1. are as numerous as possible,
2. are long and diverse,
3. contain obstacle information before the initial time, which the planner can use as history context, and
4. contain obstacle information after the ego car leaves.

We therefore generate one scenario per car in the recording, spanning its entire lifetime, with surrounding traffic before and after (see approach C.1 in [Scenario Selection and Time Spans](time_spans.md#approach-c1-one-scenario-per-car-with-surrounding-traffic-before-and-after)):

```bash
crconvert --all-vehicles --time-before-ego 4 --time-after-ego 5 \
    --samples-per-recording K --downsample D --num-processes N \
    INPUT_DIR OUTPUT_DIR COMMAND
```

- `K` limits the number of scenarios. For example, MONA contains ~300 recordings, so `K=10` results in ~3000 scenarios.
- `D` downsamples the scenarios to reduce the amount of data. Choose it so that the resulting time step is close to your simulation step size.
- `N` sets the number of parallel worker processes.

For imitation learning, add `--keep-ego` to keep the original car in its scenario.

## Python Examples

For more details, refer to [Python Usage](python_usage.md).
