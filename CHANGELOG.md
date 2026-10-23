# Changelog

## [1.0.0]

## [2026.1] - 2026-10-13

- changed default to obstacles-start-at-zero=True
- added `--enforced-planning-problem-selection` (default True): the planning problem is chosen from obstacles present at the first time step and for at least 75% (fallback 50%) of the scenario, otherwise the scenario is skipped; ignored for more than one planning problem
- bugfix initial state of planning problem was always k=0, even if planning problem was from a later timestep
- goal time interval now ends 100 time steps after the ego's last state (independent of the scenario end) and is shifted together with the obstacles
- added `--time-before-ego` / `--time-after-ego` (default 0): seconds of the recording to include before the ego vehicle appears and after it leaves, clipped to the recording; used with `--all-vehicles` and `--ego-vehicle-id`
- `--ego-vehicle-id` now creates one scenario per recording spanning the ego's lifetime (or `--start-time-step` to `--end-time-step`) instead of rolling windows
- bugfix planning problem time steps with `--ego-vehicle-id` and `--start/--end-time-step` were relative to the ego's first state instead of the scenario start
- the planning problem starts at the ego's first state on a lanelet instead of its first recorded state, which may lie beyond the map
- parked cars are no longer chosen as ego with `--all-vehicles`
- bugfix `--all-vehicles --samples-per-recording` crashed for more than one sample
- rounD maps: fixed map names of Kackertstrasse and Thiergarten (both were `ZAM_MUC-1`), and fix lanelet maps
- added `--seed` (default 42): seeds the random ego selection and the window sampling of `--samples-per-recording`, so conversions are reproducible; -1 disables seeding. Recordings are now read in sorted file order, so the result does not depend on the filesystem's listing order

### Added

## [2023.2] - 2023-11-03

### Added

## [2022.1.1] - 2023-07-12

### Added

## [2022.1] - 2022-11-08

### Added
