# Python Usage

## Custom scenario selection

Some datasets provide additional metadata for each car that can be used to select scenarios. For example, highD provides each car's minimum time-to-collision (TTC), which indicates how critical its driving behavior is. To convert only scenarios whose ego car has a low TTC, we customize two parts of the conversion:

1. A window generator that keeps only cars with a minimum TTC below `min_ttc`.
2. A factory that builds the converter with this window generator.

```python
from pathlib import Path

import pandas as pd
from pydantic.dataclasses import dataclass

from crdata.conversion.tabular.interface import Window
from crdata.datasets.highD import HighdConverterFactory
from crdata.datasets.highD.implementation import (
    HighdObstacleWindowGenerator,
)


# Create a class that only provides index values of vehicles with a
# minimum time-to-collision of less than 2 s.
@dataclass
class HighdTtcVehicleWindowGenerator(HighdObstacleWindowGenerator):
    min_ttc: float = 2.0

    def _get_index(self, recording: Window) -> pd.Index:
        index = super()._get_index(recording)
        # Get metadata of vehicles selected by parent class.
        meta = recording.vehicle_meta.loc[index]
        # Vehicles without a leading vehicle have a minimum TTC of -1.0.
        index = meta[(meta["minTTC"] < self.min_ttc) & (meta["minTTC"] >= 0.0)].index
        return index


# Customize the factory to use the newly created class.
class HighdTtcFactory(HighdConverterFactory):
    min_ttc: float = 2.0

    def build_obstacle_window_generator(self):
        return HighdTtcVehicleWindowGenerator(
            self.time_before_ego,
            self.time_after_ego,
            lane_change=self.lane_change,
            min_ttc=self.min_ttc,
        )


if __name__ == "__main__":
    input_dir = Path("../tests/resources/highd")
    output_dir = Path("/tmp/highd_ttc_scenarios")
    output_dir.mkdir(exist_ok=True)

    # Create the factory
    factory = HighdTtcFactory(
        input_dir=input_dir, output_dir=output_dir, num_time_steps=None
    )
    # Build the runner
    runner = factory.build_runner()
    # Run it
    runner.run()
```

The full script is in [`examples/highd_ttc.py`](https://gitlab.lrz.de/cps/commonroad/commonroad-dataset-converter/-/blob/develop/examples/highd_ttc.py). For the classes involved, see [Architecture](contributing/architecture.md).
