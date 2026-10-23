import os
from pathlib import Path

import numpy as np
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag
from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

input_path = (
    Path.cwd().parent.parent
    / "tests/map_conversion/test_maps/opendrive/thiergarten_000.xodr"
)
output_path = Path.cwd() / "example_files/opendrive/thiergarten.xml"

open_drive_config.proj_string_odr = gui_config.utm_default

# it was used in commonroad-dataset-designer
scenario = opendrive_to_commonroad(input_path, odr_conf=open_drive_config)
scenario.translate_rotate(np.array([292669.4681, 5630731.704]), 0)
"""
scenario.lanelet_network.remove_lanelet(68)
scenario.lanelet_network.remove_lanelet(47)
scenario.lanelet_network.remove_lanelet(87)

scenario.lanelet_network.remove_traffic_sign(10)
scenario.lanelet_network.remove_traffic_sign(11)
scenario.lanelet_network.remove_traffic_sign(6)
scenario.lanelet_network.remove_traffic_sign(7)
scenario.lanelet_network.remove_traffic_sign(8)
scenario.lanelet_network.remove_traffic_sign(9)
scenario.lanelet_network.remove_traffic_sign(12)
scenario.lanelet_network.remove_traffic_sign(13)
scenario.lanelet_network.remove_traffic_sign(14)
scenario.lanelet_network.remove_traffic_sign(163)
scenario.lanelet_network.remove_traffic_sign(167)

sidewalk_list = [33, 61, 62, 41, 25, 26, 32, 37, 125, 118, 112, 111, 121, 122, 131, 55, 61, 56, 93, 99, 94, 100, 129, 130, 65, 76, 85, 86, 105, 75, 84]
for i in sidewalk_list:
    scenario.lanelet_network.remove_lanelet(i)
"""

# store converted file as CommonRoad scenario
writer = CRDesignerFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)

# create a folder for the example file if it does not exist
if os.path.exists(Path.cwd() / "example_files") is False:
    os.mkdir(Path.cwd() / "example_files")
if os.path.exists(Path.cwd() / "example_files/opendrive") is False:
    os.mkdir(Path.cwd() / "example_files/opendrive")

writer.write_to_file(str(output_path), OverwriteExistingFile.ALWAYS)
