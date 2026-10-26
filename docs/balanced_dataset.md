# Balanced Dataset
The datasets contain different recordings from different locations and/or at different times. 
Some datasets, such as highD then split recordings into different driving directions. 
If you want to generate a balanced dataset from multiple source data, one easy way of doing that is
to set `--samples-per-recording N`, which randomly (seeded) selects N scenarios from each recording. 

## Dataset Overview

| Dataset | Recordings | Split recordings |
|---|---|---|
| `highd` | 60 | 120 |
| `round` | 24 | 24 |
| `exid`  | 93 | 93 |
| `mona`  | 298 | 298 |

## Example: 1000 scenarios per dataset

`--samples-per-recording N` creates at most `#split_recordings × N` scenarios. If you want around 1000 scenarios per dataset, you can use the table below to choose the CLI arg N. 

| Dataset | N | Max. scenarios generated |
|---|---|---|
| `highd` | 8 | 960 |
| `round` | 42 | 1008 |
| `exid` | 11 | 1023 |
| `mona` | 3 | 894 |

Note that the actual amount of scenarios may differ due to discarded planning problems.
