from collections.abc import Iterable
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from crdata.conversion.tabular.interface import (
    IWindowGenerator,
    Window,
    WindowMetaT,
)
from crdata.conversion.tabular.planning_problem import EgoWindow

#: Cars whose positions span less than this many meters are considered parked.
PARKED_MAX_EXTENT = 1.0


@dataclass
class ObstacleWindowGenerator(IWindowGenerator):
    """Create a window for each dynamic obstacle."""

    #: Seconds included before the obstacle's time range, clipped to the recording.
    time_before_ego: float = 0.0
    #: Seconds included after the obstacle's time range, clipped to the recording.
    time_after_ego: float = 0.0
    #: Only create a window for this obstacle (of any type) instead of for every car.
    obstacle_id: int | None = None
    #: Time steps (start, end) used instead of the obstacle's first and last time step.
    time_range: tuple[int, int] | None = None

    def __call__(
        self, recording: Window, window_meta: WindowMetaT
    ) -> Iterable[tuple[EgoWindow, WindowMetaT]]:
        for obstacle in self._get_index(recording):
            window = self.get_obstacle_window(obstacle, recording)
            yield window, window_meta

    def get_obstacle_window(self, obstacle, recording):
        obstacle_states = recording.vehicle_states.loc[(obstacle,) + (slice(None),)]
        start_timestep, end_timestep = self.time_range or (
            obstacle_states.index.get_level_values(-1).min(),
            obstacle_states.index.get_level_values(-1).max(),
        )
        start_timestep -= round(self.time_before_ego / recording.dt)
        end_timestep += round(self.time_after_ego / recording.dt)
        states: pd.DataFrame = recording.vehicle_states.loc[
            (recording.vehicle_states.index.get_level_values(-1) >= start_timestep)
            & (recording.vehicle_states.index.get_level_values(-1) <= end_timestep)
        ]
        meta = recording.vehicle_meta.loc[states.index.droplevel(-1).unique()]
        window = EgoWindow(states, meta, recording.dt, [obstacle])
        return window

    def _get_index(self, recording: Window) -> pd.Index:
        """Provide index values of ego obstacles."""
        if self.obstacle_id is not None:
            return recording.vehicle_meta.index.intersection([self.obstacle_id])
        index = recording.vehicle_meta.index[
            recording.vehicle_meta.obstacle_type == "car"
        ]
        # Skip parked cars: their planning problems are trivial (goal = start)
        positions = recording.vehicle_states[["x", "y"]].groupby(level=-2)
        extent = positions.max() - positions.min()
        moving = extent.index[(extent.x**2 + extent.y**2) ** 0.5 >= PARKED_MAX_EXTENT]
        return index.intersection(moving)


@dataclass
class RollingWindowGenerator(IWindowGenerator):
    """Create windows of fixed length from a recording."""

    #: Window length in time steps.
    window_length: int

    def __call__(
        self, recording: Window, window_meta: WindowMetaT
    ) -> Iterable[tuple[Window, WindowMetaT]]:
        states = recording.vehicle_states.copy()
        # Not actually using seconds, just pseudo for resampling
        states["timestamp"] = pd.to_timedelta(
            states.index.get_level_values(-1), unit="s"
        )
        resampler = states.resample(
            pd.Timedelta(self.window_length, unit="s"), on="timestamp"
        )

        for period, resampled_states in resampler:
            meta = recording.vehicle_meta.loc[
                resampled_states.index.droplevel(-1).unique()
            ]
            # TODO: Filter
            window = Window(
                resampled_states.drop(columns=["timestamp"]), meta, recording.dt
            )
            yield window, window_meta


@dataclass
class DownsamplingWindowWrapper(IWindowGenerator):
    """Wrap a window generator to downsample the time domain by a fixed factor."""

    base_window_generator: IWindowGenerator
    #: Only use every n-th time step of the input window.
    downsampling_factor: int

    def __call__(
        self, recording: Window, window_meta: WindowMetaT
    ) -> Iterable[tuple[Window, WindowMetaT]]:
        for window, window_meta in self.base_window_generator(recording, window_meta):
            window.vehicle_states = window.vehicle_states.assign(
                time_stamp=pd.to_timedelta(
                    window.vehicle_states.index.get_level_values(-1), unit="s"
                )
            )
            window.vehicle_states = window.vehicle_states.groupby(
                [
                    pd.Grouper(key="time_stamp", freq=f"{self.downsampling_factor}s"),
                    pd.Grouper(level=-2),
                ],
                group_keys=True,
            ).first()
            # Apply downsampling factor to DateTimeIndex and reorder to obstacle_id, time_step
            window.vehicle_states.index = window.vehicle_states.index.set_levels(
                window.vehicle_states.index.levels[0].seconds
                // self.downsampling_factor,
                level=0,
            ).swaplevel()
            # Select vehicles that are still available after downsampling
            vehicles = window.vehicle_states.index.levels[-2]
            window.vehicle_meta = window.vehicle_meta.loc[vehicles]
            window.dt = window.dt * self.downsampling_factor
            yield window, window_meta


@dataclass
class TimeSliceSamplingWindowGenerator(IWindowGenerator):
    """
    Sample windows from recording by window sizes.

    Note: Resulting windows may overlap!
    """

    window_length: int
    samples_per_recording: int
    random_state: np.random.Generator | None = None

    def __call__(
        self, window: Window, window_meta: WindowMetaT
    ) -> Iterable[tuple[Window, WindowMetaT]]:
        time_steps = (
            window.vehicle_states.index.get_level_values(-1)
            .unique()
            .to_series()
            .sort_values()
        )
        # Make sure we have full windows
        time_steps = time_steps.head(-self.window_length)
        start_ts = time_steps.sample(
            n=min(self.samples_per_recording, len(time_steps.index)),
            random_state=self.random_state,
        ).values
        for ts in start_ts:
            vehicle_states = window.vehicle_states[
                (window.vehicle_states.index.get_level_values(-1) >= ts)
                & (
                    window.vehicle_states.index.get_level_values(-1)
                    < ts + self.window_length
                )
            ]
            vehicles = vehicle_states.index.get_level_values(-2).unique()
            vehicle_meta = window.vehicle_meta.loc[vehicles]
            yield Window(vehicle_states, vehicle_meta, window.dt), window_meta


@dataclass
class VehicleSamplingWindowGenerator(IWindowGenerator):
    samples_per_recording: int
    base_window_generator: ObstacleWindowGenerator
    random_state: np.random.Generator | None = None

    def __call__(
        self, window: Window, window_meta: WindowMetaT
    ) -> Iterable[tuple[Window, WindowMetaT]]:
        for obstacle in self._get_index(window):
            yield (
                self.base_window_generator.get_obstacle_window(obstacle, window),
                window_meta,
            )

    def _get_index(self, recording: Window) -> pd.Index:
        """Provide index values of ego obstacles."""
        index = self.base_window_generator._get_index(recording)
        df = index.to_frame().sample(
            n=min(self.samples_per_recording, len(index)),
            random_state=self.random_state,
        )
        return df.index


@dataclass
class FixedTimeRangeWindowGenerator(IWindowGenerator):
    start_time_step: int
    end_time_step: int

    def __call__(self, window: Window, window_meta: WindowMetaT):
        vehicle_states = window.vehicle_states[
            (window.vehicle_states.index.get_level_values(-1) >= self.start_time_step)
            & (window.vehicle_states.index.get_level_values(-1) <= self.end_time_step)
        ]
        vehicles = vehicle_states.index.get_level_values(-2).unique()
        vehicle_meta = window.vehicle_meta.loc[vehicles]
        yield Window(vehicle_states, vehicle_meta, window.dt), window_meta
