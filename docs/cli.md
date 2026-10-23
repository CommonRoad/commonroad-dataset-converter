# CLI Usage

```bash
crconvert [OPTIONS] INPUT_DIR OUTPUT_DIR COMMAND
```

Run `crconvert --help` for all options and `crconvert INPUT_DIR OUTPUT_DIR COMMAND --help` for dataset-specific options.


## Full list of commands
```bash
Usage: crconvert [OPTIONS] INPUT_DIR OUTPUT_DIR COMMAND [ARGS]...

  Generates CommonRoad scenarios from different datasets.

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
  --downsample INTEGER            Increase dt to n*dt  [default: 1]
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
  sind         Convert the SinD dataset into CommonRoad scenario(s).
  tumdot       Convert the TUM-DOT dataset into CommonRoad scenario(s).
  unid         Convert the uniD dataset into CommonRoad scenario(s).
```
