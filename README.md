# Dataset Converters

This repository contains converters from different datasets to CommonRoad scenarios using a common commandline interface.
We recommend using it to generate large amounts of real-world datasets for machine learning in motion planning and prediction, as well
as for large-scale evaluations.

**Per agreement with the levelx-dataset owners (e.g., highD, exiD), we do not provide the converted scenarios but this tool to generate CommonRoad
scenarios directly from the download of their official website.**

Currently, we support:

- [highD](https://www.highd-dataset.com/),
- [inD](https://www.ind-dataset.com/),
- [exiD](https://www.exid-dataset.com/),
- [uniD](https://levelxdata.com/unid-dataset/),
- [rounD](https://www.round-dataset.com/),
- [TUMDOT-MUC](https://www.mos.ed.tum.de/en/vt/research/data-sets/tumdot-muc/),
- [INTERACTION](http://interaction-dataset.com/),
- [MONA](https://commonroad.in.tum.de/datasets),
- [SIND](https://github.com/SOTIF-AVLab/SinD).

See [docs/datasets.md](docs/datasets.md) for an overview of the datasets.

## Documentation

The documentation can be found [here](https://commonroad-dataset-converters-cps-commonroad-259f4c7766707dbbd5.pages.gitlab.lrz.de/).

## Install

```bash
pip install commonroad-dataset-converter
```

### Install with support for nuplan dataset

```bash
pip install commonroad-dataset-converter[nuplan]
```

## Development setup

This project is managed by [Poetry](https://python-poetry.org/). To install it with the development and documentation dependencies, run:

```bash
poetry env use 3.11
poetry sync --with dev,docs
```

## Examples

If you want to generate a scenario dataset for learning-based motion planning deterministically, we recommend:

```bash
crconvert --all-vehicles --time-before-ego 4 --time-after-ego 5 \
    --samples-per-recording K --downsample D --num-processes N \
    INPUT_DIR OUTPUT_DIR COMMAND
```

For more information, refer to [Examples](docs/examples.md) or the [Documentation](https://commonroad-dataset-converters-cps-commonroad-259f4c7766707dbbd5.pages.gitlab.lrz.de/).

## Usage

Type following command for help

```bash
$ crconvert --help
Usage: crconvert [OPTIONS] INPUT_DIR OUTPUT_DIR COMMAND [ARGS]...

  Generates CommonRoad scenarios from different datasets

Arguments:
  INPUT_DIR   Path to the data folder  [required]
  OUTPUT_DIR  Directory to store generated CommonRoad files  [required]

Options:
  --num-time-steps INTEGER        Maximum number of time steps in the
                                  CommonRoad scenario  [default: 150]
  --num-planning-problems INTEGER
                                  Number of planning problems per CommonRoad
                                  scenario. More than one creates a
                                  cooperative scenario.  [default: 1]
  --keep-ego / --no-keep-ego      Vehicles used for planning problem should be
                                  kept in the scenario.  [default: no-keep-
                                  ego]
  --obstacles-start-at-zero / --no-obstacles-start-at-zero
                                  The lowest time step in the scenario is set
                                  to zero.  [default: obstacles-start-at-zero]
  --downsample INTEGER            Decrease dt by n*dt  [default: 1]
  --num-processes INTEGER         Number of processes to convert dataset.
                                  [default: 1]
  --all-vehicles / --no-all-vehicles
                                  Create one planning problem/scenario for
                                  each valid vehicle. Invalidates num-time-
                                  steps.  [default: no-all-vehicles]
  --routability-check [nocheck|strict]
                                  Check routability of planning_problem
                                  [default: strict]
  --output-type [xml|pb]          File type of CommonRoad scenarios  [default:
                                  xml]
  --max-scenarios INTEGER         Only create up to n scenarios.
  --samples-per-recording INTEGER
                                  Randomly sample n scenarios from each
                                  recording.
  --start-time-step INTEGER       Start time step for scenario window.
  --end-time-step INTEGER         End time step for scenario window.
  --ego-vehicle-id INTEGER        ID of the ego-vehicle for the planning
                                  problem. Creates one scenario per recording
                                  spanning the ego's lifetime (or
                                  --start/--end-time-step).
  --enforced-planning-problem-selection / --no-enforced-planning-problem-selection
                                  Only choose the planning problem from
                                  obstacles that are present at the first time
                                  step and for at least 75% (fallback 50%) of
                                  the scenario, otherwise skip the scenario.
                                  Ignored for more than one planning problem.
                                  [default: enforced-planning-problem-
                                  selection]
  --seed INTEGER [x>=-1]    Seed for the random selection of egos and
                                  sampled windows. -1 is unseeded random sampling.
                                  [default: 42]
  --time-before-ego FLOAT RANGE   Seconds of the recording to include before
                                  the ego vehicle appears (or before --start-
                                  time-step), clipped to the recording. Only
                                  used with --all-vehicles or --ego-vehicle-
                                  id.  [default: 0.0; x>=0.0]
  --time-after-ego FLOAT RANGE    Seconds of the recording to include after
                                  the ego vehicle leaves (or after --end-time-
                                  step), clipped to the recording. Only used
                                  with --all-vehicles or --ego-vehicle-id.
                                  [default: 0.0; x>=0.0]
  --help                          Show this message and exit.

Commands:
  exid         Convert the exiD dataset into CommonRoad scenario(s).
  highd        Convert the highD dataset into CommonRoad scenario(s).
  ind          Convert the inD dataset into CommonRoad scenario(s).
  interaction  Convert the INTERACTION dataset into CommonRoad scenario(s).
  mona         Convert the MONA dataset into CommonRoad scenario(s).
  round        Convert the rounD dataset into CommonRoad scenario(s).
  sind         Convert the SIND dataset into CommonRoad scenario(s).
  tumdot       Convert the TUM-DOT dataset into CommonRoad scenario(s).
  unid         Convert the uniD dataset into CommonRoad scenario(s)
```

### Scenario time span

The options select how the recordings are cut into scenarios and which vehicle becomes the planning problem:

| Options                                    | Scenarios                                                                                                            | Planning problem (ego)                                                                        |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| default                                    | Consecutive, non-overlapping windows of `--num-time-steps`                                                           | Random car, see `--enforced-planning-problem-selection`. Its trajectory is cut to the window. |
| `--samples-per-recording K`                | K randomly placed windows of `--num-time-steps` per recording (may overlap)                                          | As above                                                                                      |
| `--all-vehicles`                           | One scenario per car, spanning its whole lifetime                                                                    | That car                                                                                      |
| `--all-vehicles --samples-per-recording K` | As above, for K random cars per recording                                                                            | That car                                                                                      |
| `--ego-vehicle-id ID`                      | One scenario per recording containing track `ID`, spanning its lifetime, or `--start-time-step` to `--end-time-step` | Track `ID`                                                                                    |

For the last three rows, `--time-before-ego` and `--time-after-ego` add seconds of surrounding traffic before the ego vehicle appears and after it leaves.
For a detailed description of how scenarios are extracted, refer to [docs/time_spans.md](docs/time_spans.md).

Example: one rounD scenario per car with 2 s of traffic before and 1 s after the ego vehicle:

```bash
crconvert --all-vehicles --time-before-ego 2 --time-after-ego 1 --keep-ego ROUND_DIR OUTPUT_DIR round
```

## Docker

The dataset converter can also be used within a docker container. We provide a [Dockerfile](./Dockerfile) to build the image.

```bash
docker build -t commonroad-dataset-converter .
```

The image's entrypoint calls `crconvert`. Any arguments passed to `docker run` are passed to the executable. To access the original dataset and converted scenarios, provide it as a volume mount `-v PATH_TO_DATASET:/data:ro` and `-v PATH_TO_OUTPUT_DIRECTORY:/output`

Example: Convert the highD dataset

```bash
docker run -v `pwd`/highd_dataset:/data:ro -v `pwd`/highd_scenarios:/output commonroad-dataset-converter \
    --max-scenarios 20 --samples-per-recording 20 /data /output highd
```
