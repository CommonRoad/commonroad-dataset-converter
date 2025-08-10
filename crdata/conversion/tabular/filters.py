from dataclasses import dataclass
from enum import Enum
import logging

from commonroad_route_planner.route_planner import RoutePlanner

from .job_producer import TabularJob

_logger = logging.getLogger(__name__)


class RoutabilityCheck(str, Enum):
    Nocheck = "nocheck"
    # Normal = "normal"
    Strict = "strict"


@dataclass
class RoutabilityFilter:
    routability_type: RoutabilityCheck

    def __call__(self, job: TabularJob) -> bool:
        """
        Checks if a planning problem is routable on scenario

        :return: bool, True if CommonRoad planning problem is routeable with max_difficulty
        """
        if self.routability_type == RoutabilityCheck.Nocheck:
            return True

        # TODO: Distinction between regular and strict?
        for planning_problem in job.planning_problem_set.planning_problem_dict.values():
            try:
                route_planner = RoutePlanner(
                    job.meta_scenario.lanelet_network,
                    planning_problem,
                    job.meta_scenario,
                )
                routes = route_planner.plan_routes()
                if len(routes) <= 0:
                    return False
            except Exception as e:
                _logger.error(
                    f"An error occurred during route planning for problem {planning_problem.planning_problem_id}: {e}"
                )
                return False  # or handle it in another way

        return True
