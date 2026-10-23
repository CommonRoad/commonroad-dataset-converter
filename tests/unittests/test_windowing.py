from unittest import TestCase
from unittest.mock import MagicMock

import numpy.testing
import pandas as pd

from crdata.conversion.tabular.interface import Window
from crdata.conversion.tabular.windowing import (
    DownsamplingWindowWrapper,
    ObstacleWindowGenerator,
    RollingWindowGenerator,
    TimeSliceSamplingWindowGenerator,
    VehicleSamplingWindowGenerator,
)


class TestWindowGenerator(TestCase):
    def setUp(self) -> None:
        self.t = [0, 1, 2, 3, 4, 5, 6]
        # Both cars move along x by one meter per time step
        vehicle_states = pd.DataFrame(
            {"t": self.t, "x": self.t, "y": 0.0},
            index=pd.MultiIndex.from_tuples(
                [(0, 0), (0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (1, 6)]
            ),
        )
        vehicle_meta = pd.DataFrame(
            ["car", "car"], columns=["obstacle_type"], index=[0, 1]
        )
        self.recording = Window(vehicle_states, vehicle_meta, 1.0)

    def test_obstacle_call(self):
        window_generator = ObstacleWindowGenerator()
        windows = list(window_generator(self.recording, None))
        self.assertEqual(2, len(windows))
        self.assertEqual(4, len(windows[0][0].vehicle_states.index))
        numpy.testing.assert_array_equal(
            windows[0][0].vehicle_states.t.values, self.t[:4]
        )
        self.assertEqual(3, len(windows[1][0].vehicle_states.index))
        numpy.testing.assert_array_equal(
            windows[1][0].vehicle_states.t.values, self.t[4:]
        )

    def test_obstacle_skips_parked_cars(self):
        self.recording.vehicle_states.loc[1, "x"] = 4.0
        windows = list(ObstacleWindowGenerator()(self.recording, None))
        self.assertEqual([0], [window.ego[0] for window, _ in windows])
        # An explicitly requested ego is used even if it is parked
        windows = list(ObstacleWindowGenerator(obstacle_id=1)(self.recording, None))
        self.assertEqual([1], [window.ego[0] for window, _ in windows])

    def test_obstacle_time_before_after_call(self):
        window_generator = ObstacleWindowGenerator(
            time_before_ego=1.0, time_after_ego=2.0
        )
        windows = list(window_generator(self.recording, None))
        # Clipped to the recording start, two steps added at the end
        numpy.testing.assert_array_equal(
            windows[0][0].vehicle_states.t.values, self.t[:6]
        )
        numpy.testing.assert_array_equal(
            windows[1][0].vehicle_states.t.values, self.t[3:]
        )

    def test_fixed_obstacle_call(self):
        window_generator = ObstacleWindowGenerator(
            time_before_ego=1.0, time_after_ego=1.0, obstacle_id=1, time_range=(5, 5)
        )
        windows = list(window_generator(self.recording, None))
        self.assertEqual(1, len(windows))
        self.assertEqual([1], windows[0][0].ego)
        numpy.testing.assert_array_equal(
            windows[0][0].vehicle_states.t.values, self.t[4:]
        )
        self.assertEqual(
            [], list(ObstacleWindowGenerator(obstacle_id=2)(self.recording, None))
        )

    def test_rolling_call(self):
        window_generator = RollingWindowGenerator(window_length=5)
        windows = list(window_generator(self.recording, None))
        self.assertEqual(2, len(windows))
        self.assertEqual(5, len(windows[0][0].vehicle_states.index))
        numpy.testing.assert_array_equal(
            windows[0][0].vehicle_states.t.values, self.t[:5]
        )
        self.assertEqual(2, len(windows[1][0].vehicle_states.index))
        numpy.testing.assert_array_equal(
            windows[1][0].vehicle_states.t.values, self.t[5:]
        )

    def test_downsampling_call(self):
        mock_window_generator = MagicMock()
        mock_window_generator.return_value = [(self.recording, None)]
        window_generator = DownsamplingWindowWrapper(mock_window_generator, 2)
        windows = list(window_generator(self.recording, None))
        self.assertEqual(1, len(windows))
        self.assertEqual(4, len(windows[0][0].vehicle_states.index))
        numpy.testing.assert_array_equal(
            windows[0][0].vehicle_states.t.values, self.t[::2]
        )

    def test_vehicle_sampling_call(self):
        for samples in (1, 2, 3):
            window_generator = VehicleSamplingWindowGenerator(
                samples_per_recording=samples,
                base_window_generator=ObstacleWindowGenerator(),
            )
            windows = list(window_generator(self.recording, None))
            # Only two cars in the recording, each sampled at most once
            self.assertEqual(min(samples, 2), len(windows))
            egos = [window.ego[0] for window, _ in windows]
            self.assertEqual(len(egos), len(set(egos)))

    def test_time_slice_sampling_call(self):
        window_generator = TimeSliceSamplingWindowGenerator(
            window_length=2, samples_per_recording=2
        )
        windows = list(window_generator(self.recording, None))
        self.assertEqual(2, len(windows))
        self.assertEqual(2, len(windows[0][0].vehicle_states.index))
        self.assertEqual(2, len(windows[1][0].vehicle_states.index))
