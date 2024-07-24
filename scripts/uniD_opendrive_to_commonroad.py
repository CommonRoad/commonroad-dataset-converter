

import os
from pathlib import Path
import numpy as np
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
import warnings
warnings.filterwarnings('ignore')

input_path = Path.cwd().parent.parent / "/path/to/uniD/opendriveFile"
output_path = Path.cwd() / "commonroad_dataset_converter/datasets/uniD/maps/DEU_UNID-1.xml"



open_drive_config.proj_string_odr = None

# load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
scenario = opendrive_to_commonroad(input_path, odr_conf=open_drive_config)
scenario.translate_rotate(np.array([293923.5, 5629269.3]), 0)

# lanelet 11 is converted with a ring intersection, if needed remove following line
scenario.lanelet_network.remove_lanelet(11)

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
