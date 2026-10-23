from pathlib import Path
from typing import Dict, List

import numpy as np
from commonroad.common.common_lanelet import LaneletType
from commonroad.scenario.scenario import Scenario
from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.config.opendrive_config import open_drive_config
from utils import convert_lanelet2

from crdata.conversion.util.yaml import load_yaml
from scripts.utils import convert_opendrive

lanelet2 = True
exid_path = Path("/path/to/exiD/")
if lanelet2:
    exid_map_path = exid_path / Path("exiD-dataset-v2.0/maps/lanelet2/")
    paths = list(exid_map_path.rglob("*osm"))
    general_config.proj_string_cr = "+proj=utm +zone=32 +ellps=WGS84"
else:
    exid_map_path = exid_path / Path("exiD-dataset-v2.0/maps/opendrive/")
    paths = list(exid_map_path.rglob("*xodr"))
    general_config.proj_string_cr = None
    open_drive_config.proj_string_odr = None

root_dir = Path(__file__).parent.parent
cr_path = root_dir / Path("crdata/datasets/exiD/maps")
config = load_yaml(str(root_dir / "crdata/datasets/exiD/config.yaml"))
tags = config["tags"]
translation = config["offsets"]
scenario_ids = config["locations"]

map_verification_formulas = []
map_verification_cores = 1

access_ramp_positions: dict[str, list[np.ndarray]] = {
    "DEU_AachenBrand-1": [
        np.array([780, -187]),
        np.array([741, -282]),
        np.array([678, -374]),
        np.array([763, -247]),
    ],
    "DEU_MerzenichRather-1": [
        np.array([145, -181]),
        np.array([179, -185]),
        np.array([215, -192]),
        np.array([330, -213]),
        np.array([421, -222]),
    ],
    "DEU_AachenLaurensberg-1": [
        np.array([182, -255]),
        np.array([358, -223]),
        np.array([419, -230]),
        np.array([526, -240]),
    ],
    "DEU_CologneKlettenberg-1": [
        np.array([211, -118]),
        np.array([257, -129]),
        np.array([290, -152]),
        np.array([449, -232]),
        np.array([480, -255]),
        np.array([493, -264]),
        np.array([509, -275]),
        np.array([527, -287]),
        np.array([548, -300]),
    ],
    "DEU_BergheimRoemer-1": [
        np.array([152, -119]),
        np.array([172, -114]),
        np.array([181, -114]),
        np.array([192, -117]),
        np.array([214, -126]),
        np.array([293, -169]),
    ],
    "DEU_CologneFortiib-1": [
        np.array([355, -178]),
        np.array([383, -203]),
        np.array([393, -212]),
        np.array([406, -228]),
        np.array([530, -380]),
        np.array([541, -394]),
        np.array([554, -407]),
        np.array([591, -379]),
        np.array([569, -361]),
    ],
    "DEU_CologneButzweiler-1": [
        np.array([274, -101]),
        np.array([310, -148]),
        np.array([267, -120]),
        np.array([305, -153]),
        np.array([324, -173]),
        np.array([327, -169]),
        np.array([339, -190]),
        np.array([342, -187]),
        np.array([354, -207]),
        np.array([357, -205]),
        np.array([371, -226]),
        np.array([375, -225]),
        np.array([403, -265]),
        np.array([412, -269]),
        np.array([454, -325]),
        np.array([457, -324]),
    ],
}
exit_ramp_positions: dict[str, list[np.ndarray]] = {
    "DEU_AachenBrand-1": [
        np.array([843, -225]),
        np.array([799, -256]),
        np.array([776, -278]),
        np.array([766, -289]),
        np.array([740, -328]),
    ],
    "DEU_MerzenichRather-1": [
        np.array([192, -154]),
    ],
    "DEU_AachenLaurensberg-1": [],
    "DEU_CologneKlettenberg-1": [],
    "DEU_BergheimRoemer-1": [
        np.array([308, -150]),
        np.array([212, -97]),
        np.array([190, -85]),
        np.array([176, -77]),
        np.array([165, -69]),
    ],
    "DEU_CologneFortiib-1": [
        np.array([430, -186]),
        np.array([429, -183]),
        np.array([422, -172]),
        np.array([413, -158]),
        np.array([408, -149]),
        np.array([406, -145]),
        np.array([396, -124]),
    ],
    "DEU_CologneButzweiler-1": [
        np.array([503, -341]),
        np.array([499, -340]),
        np.array([483, -314]),
        np.array([480, -316]),
        np.array([469, -302]),
        np.array([472, -299]),
        np.array([447, -270]),
        np.array([450, -269]),
        np.array([423, -236]),
        np.array([426, -234]),
        np.array([404, -209]),
        np.array([405, -204]),
    ],
}
shoulder_positions: dict[str, list[np.ndarray]] = {
    "DEU_AachenBrand-1": [
        np.array([654, -458]),
        np.array([607, -533]),
        np.array([580, -531]),
        np.array([630, -448]),
        np.array([779, -230]),
        np.array([810, -228]),
    ],
    "DEU_MerzenichRather-1": [
        np.array([544, -223]),
        np.array([514, -194]),
    ],
    "DEU_AachenLaurensberg-1": [
        np.array([625, -242]),
        np.array([661, -243]),
        np.array([200, -189]),
        np.array([259, -203]),
        np.array([623, -218]),
        np.array([566, -217]),
    ],
    "DEU_CologneKlettenberg-1": [
        np.array([302, -165]),
        np.array([345, -195]),
        np.array([483, -301]),
        np.array([239, -74]),
    ],
    "DEU_BergheimRoemer-1": [
        np.array([215, -130]),
        np.array([279, -166]),
        np.array([382, -224]),
        np.array([481, -287]),
        np.array([505, -275]),
        np.array([153, -67]),
    ],
    "DEU_CologneFortiib-1": [
        np.array([281, -63]),
        np.array([297, -83]),
        np.array([339, -139]),
        np.array([380, -192]),
        np.array([302, -74]),
        np.array([388, -129]),
        np.array([365, -119]),
    ],
    "DEU_CologneButzweiler-1": [
        np.array([607, -521]),
        np.array([567, -467]),
        np.array([604, -516]),
        np.array([439, -247]),
        np.array([429, -233]),
        np.array([411, -206]),
        np.array([391, -177]),
        np.array([370, -145]),
        np.array([351, -109]),
        np.array([420, -238]),
        np.array([377, -182]),
        np.array([301, -84]),
        np.array([315, -84]),
    ],
}
restricted_area_positions: dict[str, list[np.ndarray]] = {
    "DEU_AachenBrand-1": [
        np.array([773, -239]),
        np.array([797, -248]),
    ],
    "DEU_MerzenichRather-1": [
        np.array([147, -172]),
        np.array([168, -179]),
    ],
    "DEU_AachenLaurensberg-1": [
        np.array([290, -210]),
        np.array([316, -213]),
        np.array([337, -217]),
    ],
    "DEU_CologneKlettenberg-1": [
        np.array([248, -120]),
        np.array([494, -261]),
        np.array([504, -268]),
        np.array([526, -284]),
        np.array([486, -263]),
        np.array([493, -268]),
        np.array([511, -280]),
    ],
    "DEU_BergheimRoemer-1": [
        np.array([186, -110]),
        np.array([169, -76]),
        np.array([160, -71]),
    ],
    "DEU_CologneFortiib-1": [
        np.array([391, -205]),
        np.array([385, -198]),
        np.array([401, -148]),
        np.array([404, -151]),
        np.array([408, -157]),
        np.array([416, -168]),
        np.array([557, -425]),
        np.array([538, -401]),
        np.array([563, -420]),
        np.array([542, -399]),
        np.array([553, -400]),
        np.array([574, -372]),
    ],
    "DEU_CologneButzweiler-1": [
        np.array([302, -144]),
        np.array([322, -168]),
        np.array([402, -251]),
        np.array([364, -207]),
        np.array([361, -202]),
        np.array([353, -192]),
        np.array([331, -168]),
        np.array([375, -164]),
        np.array([362, -146]),
        np.array([545, -443]),
        np.array([464, -341]),
        np.array([476, -356]),
        np.array([502, -389]),
    ],
}


def post_process(sc: Scenario):
    lanelets = set()
    if (
        access_ramp_positions.get(str(sc.scenario_id)) is not None
        and len(access_ramp_positions.get(str(sc.scenario_id))) > 0
    ):
        for la_ids in sc.lanelet_network.find_lanelet_by_position(
            access_ramp_positions[str(sc.scenario_id)]
        ):
            la = sc.lanelet_network.find_lanelet_by_id(la_ids[0])
            lanelets.add(la_ids[0])
            la.lanelet_type = la.lanelet_type.union({LaneletType.ACCESS_RAMP})

    if (
        exit_ramp_positions.get(str(sc.scenario_id)) is not None
        and len(exit_ramp_positions.get(str(sc.scenario_id))) > 0
    ):
        for la_ids in sc.lanelet_network.find_lanelet_by_position(
            exit_ramp_positions[str(sc.scenario_id)]
        ):
            la = sc.lanelet_network.find_lanelet_by_id(la_ids[0])
            lanelets.add(la_ids[0])
            la.lanelet_type = la.lanelet_type.union({LaneletType.EXIT_RAMP})

    if (
        shoulder_positions.get(str(sc.scenario_id)) is not None
        and len(shoulder_positions.get(str(sc.scenario_id))) > 0
    ):
        for la_ids in sc.lanelet_network.find_lanelet_by_position(
            shoulder_positions[str(sc.scenario_id)]
        ):
            la = sc.lanelet_network.find_lanelet_by_id(la_ids[0])
            lanelets.add(la_ids[0])
            la.lanelet_type = la.lanelet_type.union({LaneletType.SHOULDER})

    if (
        restricted_area_positions.get(str(sc.scenario_id)) is not None
        and len(restricted_area_positions.get(str(sc.scenario_id))) > 0
    ):
        for la_ids in sc.lanelet_network.find_lanelet_by_position(
            restricted_area_positions[str(sc.scenario_id)]
        ):
            la = sc.lanelet_network.find_lanelet_by_id(la_ids[0])
            lanelets.add(la_ids[0])
            la.lanelet_type = la.lanelet_type.union({LaneletType.SHOULDER})

    for la in sc.lanelet_network.lanelets:
        if la.lanelet_id not in lanelets:
            la.lanelet_type = la.lanelet_type.union({LaneletType.MAIN_CARRIAGE_WAY})
        if LaneletType.URBAN in la.lanelet_type:
            la.lanelet_type.remove(LaneletType.URBAN)
        la.lanelet_type.add(LaneletType.HIGHWAY)
        la.lanelet_type.add(LaneletType.INTERSTATE)
        la.user_bidirectional = set()

    # TODO remove as soon as fixed in scenario-designer
    if str(sc.scenario_id) == "DEU_CologneButzweiler-1":
        la_id = list(
            set(
                sc.lanelet_network.find_lanelet_by_position([np.array([340, -172])])[0]
            ).intersection(
                set(
                    sc.lanelet_network.find_lanelet_by_position(
                        [np.array([362, -195])]
                    )[0]
                )
            )
        )[0]
        sc.remove_lanelet(sc.lanelet_network.find_lanelet_by_id(la_id))
        la_r = sc.lanelet_network.find_lanelet_by_position([np.array([345, -185])])[0][
            0
        ]
        la_c = sc.lanelet_network.find_lanelet_by_position([np.array([342, -175])])[0][
            0
        ]
        la_l = sc.lanelet_network.find_lanelet_by_position([np.array([350, -178])])[0][
            0
        ]
        sc.lanelet_network.find_lanelet_by_id(la_l).adj_right = la_c
        sc.lanelet_network.find_lanelet_by_id(la_l).adj_right_same_direction = True
        sc.lanelet_network.find_lanelet_by_id(la_c).adj_left = la_l
        sc.lanelet_network.find_lanelet_by_id(la_c).adj_left_same_direction = True
        sc.lanelet_network.find_lanelet_by_id(la_c).adj_right = la_r
        sc.lanelet_network.find_lanelet_by_id(la_c).adj_right_same_direction = True
        sc.lanelet_network.find_lanelet_by_id(la_r).adj_left = la_c
        sc.lanelet_network.find_lanelet_by_id(la_r).adj_left_same_direction = True


if __name__ == "__main__":
    if lanelet2:
        convert_lanelet2(
            paths,
            post_process,
            cr_path,
            scenario_ids,
            general_config,
            lanelet2_config,
            translation,
            tags,
        )
    else:
        convert_opendrive(
            paths,
            post_process,
            cr_path,
            scenario_ids,
            general_config,
            open_drive_config,
        )
    # TODO repair maps
