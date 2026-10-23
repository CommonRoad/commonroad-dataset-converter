from unittest import TestCase
from unittest.mock import Mock, patch

import numpy as np
import numpy.testing
import pandas as pd
from commonroad.geometry.shape import Rectangle

from crdata.conversion.tabular.planning_problem import (
    EgoPlanningProblemCreator,
    EgoWindow,
    FixedEgoPlanningProblemCreator,
    RandomObstaclePlanningProblemWrapper,
)


class TestPlanningProblemCreator(TestCase):
    def setUp(self) -> None:
        self.states = np.empty((10, 6))
        # obstacle id
        self.states[:5, 0] = 0
        self.states[5:, 0] = 1
        # x, y
        self.states[:, 1] = np.arange(10)
        self.states[:, 2] = 0
        # velocity
        self.states[:, 3] = 1.0
        # orientation
        self.states[:, 4] = 0
        # time step
        self.states[:5, 5] = np.arange(5)
        self.states[5:, 5] = np.arange(5)

        vehicle_states = pd.DataFrame(
            self.states,
            columns=["obstacle_id", "x", "y", "velocity", "orientation", "time_step"],
        ).set_index(["obstacle_id", "time_step"])
        vehicle_meta = pd.DataFrame(
            [["car", 2, 5], ["car", 3, 6]],
            columns=["obstacle_type", "width", "length"],
            index=[0, 1],
        )
        self.ego_window = EgoWindow(vehicle_states, vehicle_meta, 1.0, [0])

    def test_ego_planning_problem_creator_keep_ego(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = EgoPlanningProblemCreator(keep_ego=True)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        self.assertEqual(1, len(pps.planning_problem_dict))
        pp = pps.planning_problem_dict[100000]
        numpy.testing.assert_array_equal(pp.initial_state.position, [0, 0])
        self.assertEqual(1, pp.initial_state.velocity)
        self.assertEqual(0, pp.initial_state.orientation)
        self.assertIn(0, self.ego_window.vehicle_meta.index.values)

    def test_ego_planning_problem_creator_no_keep_ego(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = EgoPlanningProblemCreator(keep_ego=False)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        self.assertEqual(1, len(pps.planning_problem_dict))
        pp = pps.planning_problem_dict[100000]
        numpy.testing.assert_array_equal(pp.initial_state.position, [0, 0])
        self.assertEqual(1, pp.initial_state.velocity)
        self.assertEqual(0, pp.initial_state.orientation)
        with self.assertRaises(KeyError):
            self.ego_window.vehicle_meta.loc[0]

    def test_goal_time_ends_after_ego_independent_of_window_end(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = EgoPlanningProblemCreator(keep_ego=True)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        goal_time = pps.planning_problem_dict[100000].goal.state_list[0].time_step
        # Ego's last state is at 4, the window also ends at 4
        self.assertEqual(4 + creator.time_step_half_range, goal_time.end)

    def test_ego_planning_problem_creator_cooperative(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock
        self.ego_window.ego = (0, 1)

        creator = EgoPlanningProblemCreator(keep_ego=False)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        self.assertEqual(2, len(pps.planning_problem_dict))
        self.assertIn(100000, pps.planning_problem_dict)
        self.assertIn(100001, pps.planning_problem_dict)

    def test_random_planning_problem_wrapper_keep_ego(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = EgoPlanningProblemCreator(keep_ego=True)
        creator = RandomObstaclePlanningProblemWrapper(creator, num_planning_problems=1)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        self.assertEqual(1, len(pps.planning_problem_dict))
        self.assertIn(0, self.ego_window.vehicle_meta.index.values)

    def test_random_planning_problem_wrapper_no_keep_ego(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = EgoPlanningProblemCreator(keep_ego=False)
        creator = RandomObstaclePlanningProblemWrapper(creator, num_planning_problems=1)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        self.assertEqual(1, len(pps.planning_problem_dict))
        self.assertEqual(1, len(self.ego_window.vehicle_meta.index))

    def test_random_planning_problem_wrapper_cooperative_no_keep_ego(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = EgoPlanningProblemCreator(keep_ego=False)
        creator = RandomObstaclePlanningProblemWrapper(creator, num_planning_problems=2)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        self.assertEqual(2, len(pps.planning_problem_dict))
        self.assertEqual(0, len(self.ego_window.vehicle_meta.index))

    def test_fixed_ego_time_range_keeps_window_time_steps(self):
        scenario_mock = Mock()
        lanelet_network_mock = Mock()
        lanelet_network_mock.find_lanelet_by_position.return_value = [[None]]
        scenario_mock.lanelet_network = lanelet_network_mock

        creator = FixedEgoPlanningProblemCreator(
            0, keep_ego=True, start_time_step=2, end_time_step=4
        )
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        pp = pps.planning_problem_dict[100000]
        # Window starts at 0, so the ego's start at 2 must not be shifted to 0
        self.assertEqual(2, pp.initial_state.time_step)
        numpy.testing.assert_array_equal(pp.initial_state.position, [2, 0])

    def test_initial_and_goal_state_on_lanelet(self):
        # Only positions 1 <= x <= 3 are on the map, the ego drives from x = 0 to 4
        scenario_mock = Mock()
        scenario_mock.lanelet_network.find_lanelet_by_position.side_effect = (
            lambda positions: [[1] if 1 <= positions[0][0] <= 3 else []]
        )

        creator = EgoPlanningProblemCreator(keep_ego=True)
        with patch(
            "crdata.conversion.tabular.planning_problem._cut_lanelet_polygon"
        ) as cut_ll_mock:
            cut_ll_mock.return_value = Rectangle(10, 10, np.array([10, 0]))
            pps = creator(self.ego_window, scenario_mock)
        pp = pps.planning_problem_dict[100000]
        self.assertEqual(1, pp.initial_state.time_step)
        numpy.testing.assert_array_equal(pp.initial_state.position, [1, 0])
        self.assertEqual(1, pp.goal.state_list[0].time_step.start)
        # Goal is centered on the last state on the map
        numpy.testing.assert_array_equal(cut_ll_mock.call_args[0][0], [3, 0])

    def test_no_state_on_lanelet_skips_ego(self):
        scenario_mock = Mock()
        scenario_mock.lanelet_network.find_lanelet_by_position.return_value = [[]]

        pps = EgoPlanningProblemCreator(keep_ego=True)(self.ego_window, scenario_mock)
        self.assertEqual(0, len(pps.planning_problem_dict))
