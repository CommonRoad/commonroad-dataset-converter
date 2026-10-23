import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np
from commonroad.common.util import AngleInterval, Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem, PlanningProblemSet
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.state import CustomState, InitialState

from crdata.conversion.tabular.interface import Window
from crdata.conversion.util.planning_problem_utils import (
    _cut_lanelet_polygon,
)

_logger = logging.getLogger(__name__)


def _on_lanelet(state: pd.Series, lanelet_network: LaneletNetwork) -> bool:
    lanelets = lanelet_network.find_lanelet_by_position([state[["x", "y"]].values])
    return len(lanelets[0]) > 0


@dataclass
class EgoWindow(Window):
    ego: Sequence[int]


class PlanningProblemCreator:
    """Create an empty planning problem."""

    def __call__(
        self, window_job: Window, meta_scenario: Scenario
    ) -> PlanningProblemSet:
        return PlanningProblemSet()


@dataclass
class EgoPlanningProblemCreator(PlanningProblemCreator):
    """Create a planning problem for all specified dynamic obstacle ids.

    Planning problems are created by using the initial state of a dynamic obstacle as initial state
    of the planning problem and the final state as the center of the goal region.
    The goal region is an enlarged version of the vehicle's shape.
    Constraints on the goal time step, orientation, and velocity can be specified by interval half ranges.
    """

    #: Whether to keep the original ego vehicle's in the scenario.
    keep_ego: bool
    obstacles_start_at_zero: bool = True
    orientation_half_range: float = 0.2  # rad
    velocity_half_range: float = 10.0  # m/s
    #: Number of time steps the goal may be reached after the ego's last state.
    time_step_half_range: int = 100  # 1

    def __call__(  # type: ignore[override]
        self, window_job: EgoWindow, meta_scenario: Scenario
    ) -> PlanningProblemSet:
        planning_problem_set = PlanningProblemSet()
        for ego_id in window_job.ego:
            ego_meta = window_job.vehicle_meta.loc[ego_id]
            min_timestep = window_job.vehicle_states.index.get_level_values(-1).min()
            dynamic_obstacle_shape = Rectangle(ego_meta.length, ego_meta.width)
            states = window_job.vehicle_states.loc[ego_id]

            # Tracks may start or end beyond the map, so the initial and goal state
            # are the first and last state of the dynamic obstacle on a lanelet
            lanelet_network = meta_scenario.lanelet_network
            first_idx = next(
                (
                    i
                    for i in range(len(states))
                    if _on_lanelet(states.iloc[i], lanelet_network)
                ),
                None,
            )
            if first_idx is None:
                _logger.info(
                    "No state on a lanelet for dynamic obstacle %s, skipping it.",
                    ego_id,
                )
                continue
            last_idx = next(
                i
                for i in reversed(range(len(states)))
                if _on_lanelet(states.iloc[i], lanelet_network)
            )
            dynamic_obstacle_initial_state = states.iloc[first_idx]
            dynamic_obstacle_final_state = states.iloc[last_idx]
            ego_timestep = states.index.get_level_values(-1)[first_idx]

            # define orientation, velocity and time step intervals as goal region
            orientation_interval = AngleInterval(
                dynamic_obstacle_final_state.orientation - self.orientation_half_range,
                dynamic_obstacle_final_state.orientation + self.orientation_half_range,
            )
            velocity_interval = Interval(
                dynamic_obstacle_final_state.velocity - self.velocity_half_range,
                dynamic_obstacle_final_state.velocity + self.velocity_half_range,
            )

            # Only depends on the ego, not on the scenario end, so the goal deadline
            # does not change with --time-after-ego. It may exceed the scenario end.
            final_time_step = (
                window_job.vehicle_states.loc[ego_id].index.max()
                + self.time_step_half_range
            )

            # FIXME: should the time_step_interval start at the timestep of the initial state of the planning problem
            #  or of the first obstacle in the scenario?
            # -> Ansgar: I think it should start a few seconds before the planning problem. Then you have some obstacle history. If you start at the first obstacle you'll always have the entire recording in the scenario, right?! That would be too much data.

            time_step_interval = Interval(
                ego_timestep - min_timestep * self.obstacles_start_at_zero,
                final_time_step - min_timestep * self.obstacles_start_at_zero,
            )

            goal_shape = Rectangle(
                length=dynamic_obstacle_shape.length + 2.0,
                width=max(dynamic_obstacle_shape.width + 1.0, 3.5),
                center=dynamic_obstacle_final_state[["x", "y"]].values,
                orientation=dynamic_obstacle_final_state.orientation,
            )

            goal_position = _cut_lanelet_polygon(
                dynamic_obstacle_final_state[["x", "y"]].values,
                dynamic_obstacle_shape.length + 2.0,
                meta_scenario.lanelet_network,
            )
            if goal_position.shapely_object.area < goal_shape.shapely_object.area:
                goal_position = goal_shape

            goal_region = GoalRegion(
                [
                    CustomState(
                        position=goal_position,
                        orientation=orientation_interval,
                        velocity=velocity_interval,
                        time_step=time_step_interval,
                    )
                ]
            )

            dynamic_obstacle_initial_state = dynamic_obstacle_initial_state.copy()
            # do not always initialize these attributes
            dynamic_obstacle_initial_state["yaw_rate"] = 0.0
            dynamic_obstacle_initial_state["slip_angle"] = 0.0
            # FIXME
            planning_problem = PlanningProblem(
                ego_id + 100000,
                InitialState(
                    time_step=ego_timestep
                    - min_timestep * self.obstacles_start_at_zero,
                    position=dynamic_obstacle_initial_state[["x", "y"]].values,
                    **dynamic_obstacle_initial_state.drop(labels=["x", "y"]),
                ),
                goal_region,
            )
            planning_problem_set.add_planning_problem(planning_problem)
            if not self.keep_ego:
                window_job.vehicle_meta.drop(index=ego_id, inplace=True)

        return planning_problem_set


@dataclass
class RandomObstaclePlanningProblemWrapper(PlanningProblemCreator):
    """Randomly choose dynamic obstacles from a window as a basis for planning problems.

    Only dynamic obstacles of type "car" are considered!
    """

    wrapped_planning_problem_creator: PlanningProblemCreator
    #: Number of planning problems to create per scenario
    num_planning_problems: int = 1
    #: Only choose obstacles that are present at the first time step and for at least
    #: 75% (fallback 50%) of the window. Only supported for a single planning problem.
    enforced_selection: bool = True
    #: Random generator for the ego selection. None uses numpy's global state.
    random_state: np.random.Generator | None = None

    def __post_init__(self) -> None:
        if self.enforced_selection and self.num_planning_problems > 1:
            _logger.warning(
                "Enforced planning problem selection only supports one planning "
                "problem, ignoring it."
            )
            self.enforced_selection = False

    def __call__(self, window: Window, meta_scenario: Scenario) -> PlanningProblemSet:
        num_states = window.vehicle_states.groupby(level=0).x.count()
        eligible = (num_states > 1) & (window.vehicle_meta.obstacle_type == "car")
        if self.enforced_selection:
            steps = window.vehicle_states.index.get_level_values(-1)
            first_step = (
                steps.to_series(index=window.vehicle_states.index)
                .groupby(level=0)
                .min()
            )
            at_start = first_step == steps.min()
            share = num_states / (steps.max() - steps.min() + 1)
            for min_share in (0.75, 0.5):
                candidates = window.vehicle_meta.loc[
                    eligible & at_start & (share >= min_share)
                ]
                if len(candidates) >= self.num_planning_problems:
                    break
            else:
                _logger.warning(
                    "No obstacle is present from the first time step for at least "
                    "50%% of scenario %s, skipping it.",
                    meta_scenario.scenario_id,
                )
                return PlanningProblemSet()
        else:
            candidates = window.vehicle_meta.loc[eligible]
        if len(candidates) >= self.num_planning_problems:
            ego_ids = candidates.sample(
                self.num_planning_problems, random_state=self.random_state
            ).index.values
            ego_window_job = EgoWindow(
                window.vehicle_states, window.vehicle_meta, window.dt, ego_ids
            )
            return self.wrapped_planning_problem_creator(ego_window_job, meta_scenario)
        else:
            return super().__call__(window, meta_scenario)


@dataclass
class FixedEgoPlanningProblemCreator(PlanningProblemCreator):
    """
    Creates a PlanningProblemSet for a fixed ego vehicle within a specified time interval.

    Attributes:
        ego_vehicle_id (int): The ID of the ego vehicle for which the planning problem is to be created.
        keep_ego (bool): Indicates whether the ego vehicle should be retained in the meta-scenario.
        start_time_step (Optional[int]): Start time step for selecting the ego vehicle's states.
        end_time_step (Optional[int]): End time step for selecting the ego vehicle's states.
        obstacles_start_at_zero (bool): Whether obstacles should start at time step 0.

    Methods:
        __call__(window_job: Window, meta_scenario: Scenario) -> PlanningProblemSet:
            Creates a PlanningProblemSet for the specified ego vehicle and time interval.
    """

    ego_vehicle_id: int
    keep_ego: bool
    start_time_step: int | None = None
    end_time_step: int | None = None
    obstacles_start_at_zero: bool = True

    def __call__(
        self, window_job: Window, meta_scenario: Scenario
    ) -> PlanningProblemSet:
        if self.ego_vehicle_id not in window_job.vehicle_meta.index:
            return PlanningProblemSet()
        vehicle_states = window_job.vehicle_states
        if self.start_time_step is not None and self.end_time_step is not None:
            # Only restrict the ego's states, so the time steps stay relative to the window
            idx = vehicle_states.index
            is_ego = idx.get_level_values(-2) == self.ego_vehicle_id
            in_range = (idx.get_level_values(-1) >= self.start_time_step) & (
                idx.get_level_values(-1) <= self.end_time_step
            )
            if not (is_ego & in_range).any():
                return PlanningProblemSet()
            vehicle_states = vehicle_states[~is_ego | in_range]
        ego_window_job = EgoWindow(
            vehicle_states,
            window_job.vehicle_meta,
            window_job.dt,
            [self.ego_vehicle_id],
        )
        return EgoPlanningProblemCreator(self.keep_ego, self.obstacles_start_at_zero)(
            ego_window_job, meta_scenario
        )
