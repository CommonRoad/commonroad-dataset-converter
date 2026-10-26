# Creating a Dataset from multiple source datasets
You can create a dataset from multiple source datasets, e.g., highD and exiD by sequentially running the converter to the same output dir, e.g.:
```bash
crconvert high_input_dir joint_output_dir highd
crconvert exid_input_dir joint_output_dir exid
```

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

For example, the following command sequence will generate a dataset containing around 1000 highD scenarios and 1000 exiD scenarios:
```bash
crconvert --samples-per-recording 8 high_input_dir joint_output_dir highd
crconvert --samples-per-recording 11 exid_input_dir joint_output_dir exid
```

Note that the actual amount of scenarios may differ due to discarded planning problems.
