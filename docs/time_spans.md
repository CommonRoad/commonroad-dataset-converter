# Scenario Selection and Time Spans

This page describes how to control the scenario time windows and how planning problems are selected.
It also describes how to add history and future trajectory data outside the planning problem's time window.

## Scenario time span

These options select how recordings are cut into scenarios and which car becomes the planning problem (ego):

| Approach | Options                                    | Scenarios                                                                                                            | Planning problem (ego)                                                                       |
| -------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| A        | default                                    | Consecutive, non-overlapping windows of `--num-time-steps`                                                           | Random car, see `--enforced-planning-problem-selection`; its trajectory is cut to the window |
| B        | `--samples-per-recording K`                | K randomly placed windows of `--num-time-steps` per recording (may overlap)                                          | As in A                                                                                      |
| C        | `--all-vehicles`                           | One scenario per car, spanning its whole lifetime                                                                    | That car                                                                                     |
| C.2      | `--all-vehicles --samples-per-recording K` | As in C, for K random cars per recording                                                                             | That car                                                                                     |
| D        | `--ego-vehicle-id ID`                      | One scenario per recording containing track `ID`, spanning its lifetime, or `--start-time-step` to `--end-time-step` | Track `ID`                                                                                   |

For approaches C and D, `--time-before-ego Tb` and `--time-after-ego Ta` add `Tb` seconds of surrounding traffic before the ego car appears and `Ta` seconds after it leaves.

### Illustrations

#### Approach A: Default, consecutive windows

**Option**: `--num-time-steps N` (here N = 150)

```text
recording          |----------------------------------------------------------|
windows            |-----N-----|-----N-----|-----N-----|-----N-----|----N-----|
ego track                             .....|==========|...... random car present at the window start
obstacles                                  |----------| every track cut to the window
planning_problem              initial_time |-------------------| goal_region.time.ub
```

#### Approach B: Random windows

**Option**: `--samples-per-recording K`: K windows of N time steps at random positions, which may overlap

```text
recording          |----------------------------------------------------------|
sample 1               |----------|
sample 2                      |----------|
sample 3                                                 |----------|
```

#### Approach C: One scenario per car

**Option**: `--all-vehicles`: each scenario spans the car's lifetime

```text
recording          |----------------------------------------------------------|
ego track                            |======================|
obstacles                            |----------------------| every track cut to the ego's lifetime
planning_problem        initial_time |-------------------------------| goal_region.time.ub
```

#### Approach C.1: One scenario per car with surrounding traffic before and after

**Option**: `--all-vehicles --time-before-ego Tb --time-after-ego Ta`

```text
recording          |----------------------------------------------------------|
ego track                            |======================|
obstacles                      |----------------------------------|
time_before/after           Tb |----|                        |----| Ta
planning_problem        initial_time |-------------------------------| goal_region.time.ub
```

#### Approach C.2: One scenario for each of K random cars

**Option**: `--all-vehicles --samples-per-recording K`: like C, for K random cars per recording (here K = 2)

```text
recording          |----------------------------------------------------------|
car 3                |=================| -> scenario
car 7                            |==================|
car 9                                            |========================| -> scenario
```

#### Approach D: One scenario for a specific track ID

**Option**: `--ego-vehicle-id ID`: one scenario per recording that contains track `ID`, spanning its lifetime (`Tb` and `Ta` apply)

```text
recording 07       |----------------------------------------------------------|
track ID                               |===================| -> scenario
recording 09       |----------------------------------------------------------|
track ID               |==========| -> scenario (same ID, other car)
```

#### Approach D.1: Specific track ID within a fixed time span

**Option**: `--ego-vehicle-id ID --start-time-step S --end-time-step E`: `S` and `E` replace the ego's lifetime (`Tb` and `Ta` apply)

```text
recording          |----------------------------------------------------------|
ego track                  ......|==========================|.........
start/end                            S |--------------| E
obstacles                        |--------------------------| ego included with --keep-ego
time_before/after             Tb |----|                |----| Ta
planning_problem          initial_time |-----------------------| goal_region.time.ub
```

**Legend**:

- `=` is the ego car's track, `.` is the part of a track outside the scenario.
- `obstacles` is the scenario's time span. Each obstacle is cut to it; obstacles with only a single state in it are dropped.
- `initial_time` is the ego's first state on a lanelet (tracks may start before the map does). The goal position is its last state on a lanelet. The goal time interval ends 100 time steps after the ego's last state (`goal_region.time.ub = ego end + 100`), independent of the scenario end and `--time-after-ego`, so it can exceed the scenario end.
- With `--obstacles-start-at-zero` (default), time step 0 is the scenario start.

**Notes**:

- `--ego-vehicle-id` matches the track ID in every recording of `INPUT_DIR`. To convert a single recording, point `INPUT_DIR` to a folder containing only that recording's files.
- With `--ego-vehicle-id`, `--num-time-steps` and `--samples-per-recording` are ignored.
- `--enforced-planning-problem-selection` only applies to approaches A and B.
- Without `--keep-ego`, the ego car is removed from its own scenario only; it remains an obstacle in all other scenarios.
