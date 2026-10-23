import glob
import logging
import traceback
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import List

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.visualization.mp_renderer import MPRenderer
from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_scenario,
)
from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    LaneletFormulaID,
)

date_strftime_format = "%d-%b-%y %H:%M:%S"
message_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(
    encoding="utf-8",
    level=logging.INFO,
    format=message_format,
    datefmt=date_strftime_format,
)

formulas = []


def eval_maps(config: MapVerParams, path: str):
    if (
        "datasets/sind" in path
    ):  # traffic lights are added during dataset conversion itself
        config.verification.excluded_formulas = [LaneletFormulaID.STOP_LINE_REFERENCES]
    sc, pps = CommonRoadFileReader(path).open()
    rnd = MPRenderer()
    sc.lanelet_network.draw(rnd)
    rnd.render(
        filename=f"{Path(__file__).parent.parent / Path('figures')}/{sc.scenario_id}_org"
    )
    try:
        sc, valid = verify_and_repair_scenario(sc, config)
        rnd = MPRenderer()
        sc.lanelet_network.draw(rnd)
        rnd.render(
            filename=f"{Path(__file__).parent.parent / Path('figures')}/{sc.scenario_id}_new"
        )
        if not valid:
            CommonRoadFileWriter(sc, pps).write_to_file(
                path, OverwriteExistingFile.ALWAYS
            )
        else:
            logging.info(f"eval map {sc.scenario_id} is valid")
    except Exception:
        logging.error(f"eval map {sc.scenario_id}, error: {traceback.format_exc()}")


def prepare_and_execute_eval(
    scenario_base_dir: Path, selected_formulas: list[FormulaID], num_cores: int = 1
):
    relevant_scenario_paths = glob.glob(f"{scenario_base_dir}/**/*.xml", recursive=True)
    path = Path(__file__).parent.parent / Path("figures")
    if not path.exists():
        path.mkdir()
    config = MapVerParams()
    config.verification.formulas = selected_formulas
    config.verification.max_iterations = 10
    config.evaluation.overwrite_scenario = True
    func = partial(eval_maps, config)
    with Pool(processes=num_cores) as pool:
        pool.map(func, relevant_scenario_paths)


if __name__ == "__main__":
    prepare_and_execute_eval(
        Path(__file__).parent.parent / Path("crdata/datasets/exiD"), formulas
    )
