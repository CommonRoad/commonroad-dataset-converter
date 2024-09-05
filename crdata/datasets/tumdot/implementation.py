import copy
import importlib
import os

import pandas as pd
from pathlib import Path
from typing import Iterable, Tuple
from commonroad.scenario.scenario import Scenario
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.traffic_sign import TrafficSignIDCountries

from crdata.conversion.tabular.interface import (
    IMetaScenarioCreator,
    IRecordingGenerator,
    Window,
)
from dataclasses import dataclass
from crdata.datasets.common.obstacle_utils import get_velocity, get_acceleration


# Define a data class to store meta information for TumdotWindow
@dataclass
class TumdotWindowMeta:
    recording_id: str


# Define a data class to generate recordings from the dataset
@dataclass
class TumdotRecordingGenerator(IRecordingGenerator):
    data_path: Path  # Path to the dataset

    # Define an iterator method to generate windows and meta information
    def __iter__(self) -> Iterable[Tuple[Window, TumdotWindowMeta]]:
        folder = "Trajectory-Data"  # Folder containing the trajectory data
        dir = os.listdir(self.data_path / folder)  # List all files in the folder
        for file in dir:
            # Mapping of integer codes to obstacle types
            INTEGER_TO_OBSTACLE_TYPE = {
                1: "car",
                2: "pedestrian",
                3: "bicycle",
                4: "trailer",
                5: "motorcycle",
                6: "truck",
                7: "bus",
                8: "scooter",
                9: "streetcar",
            }
            x = "Trajectory-Data"
            track_df = pd.read_csv(
                self.data_path / x / file
            )  # Read the CSV file into a DataFrame

            # Rename columns to standardize names
            track_df.rename(
                columns={
                    "dimension_x": "length",
                    "dimension_y": "width",
                    "translation_x": "x",
                    "translation_y": "y",
                    "category": "obstacle_type",
                    "velocity_x": "xVelocity",
                    "velocity_y": "yVelocity",
                    "acceleration_y": "yAcceleration",
                    "acceleration_x": "xAcceleration",
                },
                inplace=True,
            )

            # Map obstacle types to their respective string representations
            track_df["obstacle_type"] = (
                track_df["obstacle_type"]
                .astype(int)
                .map(INTEGER_TO_OBSTACLE_TYPE)
                .fillna("Unknown")
            )

            # Exclude certain obstacle types
            track_df = track_df[track_df["obstacle_type"] != "trailer"]
            track_df = track_df[track_df["obstacle_type"] != "streetcar"]
            track_df = track_df[track_df["obstacle_type"] != "scooter"]

            # Calculate velocity and acceleration
            track_df["velocity"] = get_velocity(track_df)
            track_df["orientation"] = track_df["rotation_z"]
            track_df["acceleration"] = get_acceleration(track_df, track_df.orientation)

            # Sort values and create frame_id
            track_df.sort_values(["track_id", "timestamp"], inplace=True)
            # frame_id is reset to 0 after the track_id changes
            track_df["frame_id"] = track_df.groupby("track_id").cumcount()

            # Find out the initial time step of each trajectory and merge the first_appearence with the track_df on 'track_id'
            extra = track_df.copy()
            # compute the time offset to make sure there is no negative time stamp
            offset_time = (
                abs(extra["timestamp"].min()) if extra["timestamp"].min() < 0 else 0
            )
            extra["timestamp"] = ((extra["timestamp"] + offset_time) / 0.08).astype(int)
            extra = extra[["timestamp", "track_id"]]
            extra.rename(columns={"timestamp": "init"}, inplace=True)
            first_appearance = extra.drop_duplicates(subset="track_id", keep="first")
            track_df = track_df.merge(first_appearance, on="track_id", how="left")

            # Add the initial time step to 'frame_id'
            track_df["frame_id"] = track_df["frame_id"] + track_df["init"]

            # Set the index for the DataFrame
            track_df.set_index(["track_id", "frame_id"], inplace=True)

            # Extract meta information for each track
            track_meta = track_df.groupby(level=0)[
                ["obstacle_type", "length", "width"]
            ].first()

            # Select relevant columns for the window
            track_df = track_df[["x", "y", "velocity", "orientation", "acceleration"]]

            # Yield the window and meta information
            yield Window(track_df, track_meta, 0.08), TumdotWindowMeta(file)


# Define a data class to create meta scenarios
@dataclass
class TumdotMetaScenarioCreator(IMetaScenarioCreator):
    # todo: use is_valid_traffic_sign
    allowed_sign_ids = {
        "101",
        "102",
        "103-10",
        "103-20",
        "108",
        "114",
        "123",
        "124",
        "125",
        "131",
        "133-10",
        "133-20",
        "138",
        "142-10",
        "145-50",
        "201",
        "205",
        "206",
        "208",
        "209",
        "209-10",
        "209-20",
        "211-20",
        "215",
        "220-10",
        "220-20",
        "222-10",
        "222-20",
        "223.2",
        "223.2-50",
        "223.2-51",
        "224-50",
        "237",
        "239",
        "240",
        "242.1",
        "242.2",
        "244.1",
        "244.2",
        "245",
        "250",
        "251",
        "253",
        "254",
        "255",
        "257-54",
        "259",
        "260",
        "261",
        "262",
        "264",
        "265",
        "266",
        "267",
        "270.1",
        "270.2",
        "272",
        "274",
        "274.1",
        "274.2",
        "275",
        "276",
        "277",
        "278",
        "280",
        "281",
        "282",
        "283-10",
        "283-30",
        "286-30",
        "301",
        "306",
        "308",
        "310",
        "311",
        "314",
        "314-10",
        "314-20",
        "314-30",
        "325.1",
        "325.2",
        "327",
        "328",
        "330.1",
        "330.2",
        "331.1",
        "331.2",
        "332",
        "332.1",
        "333",
        "333-21",
        "333-22",
        "350",
        "354",
        "356",
        "357",
        "363",
        "365-51",
        "365-52",
        "365-60",
        "386.1",
        "386.2",
        "386.3",
        "406-50",
        "418-20",
        "419-20",
        "434-50",
        "430-20",
        "432-10",
        "432-20",
        "434",
        "438",
        "439",
        "440",
        "448",
        "449",
        "450-50",
        "450-51",
        "450-52",
        "450-53",
        "450-54",
        "450-55",
        "453",
        "458",
        "455.1-30",
        "460-10",
        "460-12",
        "460-20",
        "460-21",
        "460-22",
        "460-30",
        "501-15",
        "501-16",
        "511-22",
        "521-30",
        "521-31",
        "521-32",
        "521-33",
        "525",
        "531-10",
        "531-20",
        "531-21",
        "533-22",
        "550-20",
        "600-35",
        "600-30",
        "600-31",
        "600-32",
        "600-34",
        "600-38",
        "605-10",
        "605-11",
        "605-20",
        "605-21",
        "605-31",
        "625-10",
        "625-11",
        "625-12",
        "625-13",
        "625-20",
        "625-21",
        "625-22",
        "625-23",
        "626-10",
        "626-20",
        "626-30",
        "626-31",
        "626-32",
        "628-10",
        "629-10",
        "629-20",
        "720",
        "1000",
        "1000-10",
        "1000-11",
        "1000-20",
        "1000-21",
        "1000-30",
        "1000-31",
        "1001-30",
        "1001-31",
        "1002-10",
        "1002-11",
        "1002-12",
        "1002-13",
        "1002-14",
        "1002-20",
        "1002-21",
        "1002-22",
        "1002-23",
        "1002-24",
        "1004-30",
        "1004-31",
        "1004-32",
        "1004-33",
        "1004-34",
        "1004-35",
        "1006-30",
        "1006-31",
        "1006-32",
        "1006-33",
        "1006-34",
        "1006-35",
        "1006-36",
        "1006-37",
        "1006-38",
        "1006-39",
        "1007-31",
        "1010-10",
        "1010-11",
        "1010-12",
        "1010-13",
        "1010-14",
        "1012-30",
        "1012-31",
        "1012-32",
        "1012-33",
        "1012-34",
        "1012-35",
        "1012-36",
        "1012-37",
        "1012-38",
        "1020-30",
        "1022-10",
        "1024-10",
        "1026-36",
        "1026-37",
        "1026-38",
        "1031-52",
        "1040-30",
        "1048-12",
        "1049-13",
        "1052-31",
        "1053-33",
        "1053-34",
        "1053-35",
        "2113",
        "R2-1",
        "R3-4",
        "CW20-1",
        "R7-1",
        "R7-4",
        "R7-201a",
        "R6-1L",
        "R6-1R",
        "R5-1",
        "R3-2",
        "R3-5R",
        "R3-8b",
        "R3-1",
        "R4-7",
        "W3-3",
        "R8-3gP",
        "R8-3",
        "R3-5L",
        "R3-27",
        "W1-3L",
        "W11-2",
        "M6-2aL",
        "W4-2R",
        "R7-8",
        "R7-107",
        "R8-3C",
        "R10-7",
        "W1-6L",
        "r1",
        "r2",
        "r100",
        "r101",
        "r106",
        "r107",
        "r205",
        "r301",
        "r305",
        "r307",
        "r308",
        "s13",
    }

    # Initialize the meta scenario creator
    def __post_init__(self) -> None:
        # Load the static map file
        with importlib.resources.path(
            "crdata.datasets.tumdot", "MUC_TUMDOT-1.xml"
        ) as map_path:
            self._meta_scenario = CommonRoadFileReader(str(map_path)).open()[0]
            self._meta_scenario.dt = 0.08  # Set the time step
            traffic_signs = self._meta_scenario.lanelet_network.traffic_signs
            for sign in traffic_signs:
                for element in sign.traffic_sign_elements:
                    value = element.traffic_sign_element_id.value
                    if value not in self.allowed_sign_ids:
                        # Remove traffic signs that are not allowed
                        self._meta_scenario.lanelet_network.remove_traffic_sign(
                            sign.traffic_sign_id
                        )
                    # if not self.is_valid_traffic_sign(element.traffic_sign_element_id.value):
                    #     self._meta_scenario.lanelet_network.remove_traffic_sign(sign.traffic_sign_id)

    # Create a scenario from a given window and meta information
    def __call__(self, _: Window, window_meta: TumdotWindowMeta) -> Scenario:
        meta_scenario = copy.deepcopy(
            self._meta_scenario
        )  # Deep copy the meta scenario
        id = window_meta.recording_id.split("_")[-1]  # Extract the recording ID
        meta_scenario.scenario_id.map_id = int(id)  # Set the map ID
        return meta_scenario  # Return the modified scenario

    @staticmethod
    def is_valid_traffic_sign(sign_id: str) -> bool:
        for traffic_sign_enum in TrafficSignIDCountries.values():
            if any(sign_id == item.value for item in traffic_sign_enum):
                return True
        return False
