# Script for converting interaction dataset maps from Lanelet2 to CommonRoad
# Requires Scenario Designer version >=0.8.0
from pathlib import Path
import numpy as np

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from commonroad.scenario.scenario import Tag
from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.map_conversion.map_conversion_interface import lanelet_to_commonroad
from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad
from commonroad_dataset_converter.conversion.util.yaml import load_yaml
open_drive_config.proj_string_odr = gui_config.utm_default  # define gerreference according to the .xodr file
# load OpenStreetMap (OSM) file, parse it, and convert it to a CommonRoad scenario
input_path = Path("/home/tai/round-dataset-v1.1/maps/opendrive/1_kackertstrasse/kackertstrasse.xodr")
scenario = opendrive_to_commonroad(input_path, odr_conf=open_drive_config)
scenario.translate_rotate(np.array([292669.4681, 5630731.704]), 0)  # rotate with offset specified in the .xodr file
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Sebastian Maierhofer",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
)
writer.write_to_file("/home/tai/commonroad-dataset-converter/commonroad_dataset_converter/datasets/rounD/maps" + "/" +
                     "ZAM_OpenDRIVETest-1_1-T1.xml", OverwriteExistingFile.ALWAYS)
