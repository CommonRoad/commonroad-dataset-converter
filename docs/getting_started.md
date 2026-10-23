# Getting Started

In general, this converter supports many use cases, including generating scenarios with:

- one planning problem starting at k=0 or randomly generated from recorded vehicles in the data
- multiple planning problems in the same scenario for cooperative driving.
- adding history and future data to obstacles outside the scenario time window
- seeding for reproducibility
- ...

This page gives an overview of commonly used functionalities.

## Steps

1. Install this tool; we recommend Anaconda as an environment
2. Download a supported [dataset](./datasets.md) you want to use
3. You can either use some frequently used commands from this page or review the [full command list](./cli.md) to customize the output

## Ground Truth Trajectories

The vehicle that was used to generate the planning problem (ego vehicle) is excluded by default, so it does not interfere with the planner, but you may wish to include it via `--keep-ego` and remove it in your own code so that you have a real-world ground truth trajectory.

# Recommended Settings for Frequent Use Cases

We recommend the following settings for frequent use cases:

## Classic Motion Planning

For motion planning, we recommend generating one planning problem per scenario and force it to start at k=0. The ego vehicle is removed. This is achieved using the default configurations of our tool, i.e.:

```bash
crconvert INPUT_DIR OUTPUT_DIR COMMAND
```

Use cases include the CommonRoad-Reactive-Planner, CommonRoad-Reach, the Frenetix-Planner, and our and other people's research on classical motion planning.

## Deep-Learning-based Motion Planning

If you want to do learning-based motion planning, you might want to use the same configuration as for classic motion planning but keep the ego vehicle trajectory to use as ground truth:

```bash
crconvert --keep-ego INPUT_DIR OUTPUT_DIR COMMAND
```

Use cases include the CommonRoad-Diffusion-Planning toolbox and our and other people's research on deep learning in motion planning.

## One Scenario per Car

To create one scenario per car, spanning the car's entire lifetime, run:

```bash
crconvert --all-vehicles INPUT_DIR OUTPUT_DIR COMMAND
```

For a more detailed example, see [Converting Scenarios for Learning](./examples.md#converting-scenarios-for-learning).

**Next**, see the [full CLI command list](./cli.md), the [supported datasets](./datasets.md), or [how scenarios are selected](./time_spans.md).
