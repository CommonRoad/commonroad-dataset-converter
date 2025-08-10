from pathlib import Path
from commonroad.scenario.scenario import Scenario

from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.config.general_config import general_config
from crdata.conversion.util.yaml import load_yaml
from scripts.utils import convert_opendrive
from utils import convert_lanelet2


lanelet2 = False
if lanelet2:
    exid_path = Path("/media/sebastian/TUM/06_code/scenarios/uniD/") / Path(
        "uniD-dataset-v1.1/maps/lanelet2/"
    )
    paths = list(exid_path.rglob("*osm"))
    general_config.proj_string_cr = "+proj=utm +zone=32 +ellps=WGS84"
else:
    exid_path = Path("/media/sebastian/TUM/06_code/scenarios/uniD/") / Path(
        "uniD-dataset-v1.1/maps/opendrive/"
    )
    paths = list(exid_path.rglob("*xodr"))
    general_config.proj_string_cr = None
    open_drive_config.proj_string_odr = None

root_dir = Path(__file__).parent.parent
cr_path = root_dir / Path("crdata/datasets/uniD/maps")
config = load_yaml(str(root_dir / "crdata/datasets/uniD/config.yaml"))
tags = config["tags"]
translation = config["offsets"]
scenario_ids = config["locations"]

map_verification_formulas = []
map_verification_cores = 1


def post_process(sc: Scenario):
    return


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
            translation,
            tags,
        )
