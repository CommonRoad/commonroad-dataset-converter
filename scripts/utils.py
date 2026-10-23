from collections.abc import Callable
from pathlib import Path
from typing import Dict, List, Set, Union

import numpy as np
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import ScenarioID, Tag
from crdesigner.common.config.general_config import GeneralConfig, general_config
from crdesigner.common.config.lanelet2_config import Lanelet2Config, lanelet2_config
from crdesigner.common.config.opendrive_config import OpenDriveConfig, open_drive_config
from crdesigner.map_conversion.map_conversion_interface import (
    lanelet_to_commonroad,
    opendrive_to_commonroad,
)


def convert_map(
    conversion_function: Callable,
    paths: list[Path],
    postprocess: Callable,
    map_path: Path,
    scenario_ids: dict[int, str],
    general_conf: GeneralConfig,
    conversion_conf: Lanelet2Config | OpenDriveConfig,
    translation: dict[str, np.ndarray],
    tags_raw: dict[str, set[Tag]],
):
    for path in paths:
        try:
            scenario_num = int(path.stem[0])
        except ValueError:
            # If conversion fails, the string does not equal a number
            scenario_num = 0
        scenario_id = scenario_ids[scenario_num]
        sc_path = map_path / (scenario_id + ".xml")
        scenario = conversion_function(str(path), general_conf, conversion_conf)
        scenario.scenario_id = ScenarioID.from_benchmark_id(scenario_id, "2020a")
        if translation.get(scenario_id) is not None:
            scenario.translate_rotate(
                np.array(
                    [
                        -translation[scenario_id]["x_offset_lanelets"],
                        -translation[scenario_id]["y_offset_lanelets"],
                    ]
                ),
                0,
            )
            scenario.replace_lanelet_network(
                scenario.lanelet_network.create_from_lanelet_network(
                    scenario.lanelet_network
                )
            )  # TODO remove when translate_rotate supports recomputing strtree
        if tags_raw.get(scenario_id) is not None:
            tags = {Tag(str.lower(tag_name)) for tag_name in tags_raw[scenario_id]}
        else:
            tags = set()
        postprocess(scenario)

        writer = CommonRoadFileWriter(
            scenario=scenario,
            planning_problem_set=PlanningProblemSet(),
            author="Sebastian Maierhofer",
            affiliation="Technical University of Munich",
            source="CommonRoad Scenario Designer",
            tags=tags,
        )
        writer.write_to_file(str(sc_path), OverwriteExistingFile.ALWAYS)


def convert_lanelet2(
    paths: list[Path],
    postprocess: Callable,
    map_path: Path,
    scenario_ids: dict[int, str],
    general_conf: GeneralConfig = general_config,
    lanelet2_conf: Lanelet2Config = lanelet2_config,
    translation: dict[str, np.ndarray] = None,
    tags_raw: dict[str, set[Tag]] = None,
):
    convert_map(
        lanelet_to_commonroad,
        paths,
        postprocess,
        map_path,
        scenario_ids,
        general_conf,
        lanelet2_conf,
        translation,
        tags_raw,
    )


def convert_opendrive(
    paths: list[Path],
    postprocess: Callable,
    map_path: Path,
    scenario_ids: dict[int, str],
    general_conf: GeneralConfig = general_config,
    open_drive_conf: OpenDriveConfig = open_drive_config,
    translation: dict[str, np.ndarray] = None,
    tags: dict[str, set[Tag]] = None,
):
    convert_map(
        opendrive_to_commonroad,
        paths,
        postprocess,
        map_path,
        scenario_ids,
        general_conf,
        open_drive_conf,
        translation,
        tags,
    )
