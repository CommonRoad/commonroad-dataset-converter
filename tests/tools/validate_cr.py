import traceback
from pathlib import Path
from typing import Set, Tuple

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.obstacle import DynamicObstacle, StaticObstacle
from commonroad.scenario.scenario import Scenario
from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.verification.formula_ids import (
    extract_formula_ids,
)

# from crdesigner.verification_repairing.verification.map_verifier import MapVerifier
from lxml import etree


def check_obstacle_off_road(scenario: Scenario):
    errors = 0
    for obs in scenario.obstacles:
        off_road = True
        if isinstance(obs, DynamicObstacle):
            for s in obs.prediction.trajectory.state_list:
                if scenario.lanelet_network.find_lanelet_by_position([s.position]):
                    off_road = False
                    break
            else:
                off_road = True
        elif isinstance(obs, StaticObstacle):
            off_road = not scenario.lanelet_network.find_lanelet_by_position(
                [obs.initial_state.position]
            )

        if off_road:
            print(f"Obstacle {obs.obstacle_id} is off the road at all times")
            errors += 1

    return errors


def validate(xml_path: Path) -> int:
    # test whether a scenario file passes the schema test
    xsd_path = Path(__file__).parent / "XML_commonRoad_XSD.xsd"
    try:
        # assert xml_path.exists()
        etree.clear_error_log()
        xmlschema = etree.XMLSchema(etree.parse(str(xsd_path)))
        tmp = etree.parse(str(xml_path))
        xmlschema.assertValid(tmp)
    except AssertionError:
        print("File not found")
        return 1
    except etree.DocumentInvalid as e:
        print("File invalid: {}".format(e))
        return 1
    except Exception as e:
        print("Unknown error: {}".format(e))
        return 1
    return 0
    # assert xml_path.exists()
    # with xml_path.open("rb") as fp:
    #     xml_bytes = fp.read()
    # return CommonRoadFileWriter.check_validity_of_commonroad_file(xml_bytes)


# todo: avtivate map evaluation after cr-designer is updated
# def eval_map(scenario: Scenario, map_ids: Set[int]) -> Tuple[bool, int]:
#     map_name = (
#         scenario.scenario_id.country_id
#         + "_"
#         + scenario.scenario_id.map_name
#         + "-"
#         + str(scenario.scenario_id.map_id)
#     )
#     if map_name not in map_ids:
#         map_ids.add(map_name)
#         lanelet_network = scenario.lanelet_network
#         config = MapVerParams()
#         config.verification.formulas = extract_formula_ids()
#         verifier = MapVerifier(lanelet_network, config)
#         try:
#             res = verifier.verify()
#             return True, sum([len(val) for val in res.values()])
#         except Exception as e:
#             print(
#                 f"Error verifying map {map_name}: {e}. This has to be solve in the map verification."
#             )
#             return False, 0


def validate_all(path: Path, xsd_path: str):
    path = Path(path)
    xsd_path = Path(xsd_path)
    assert xsd_path.exists(), f"file path {xsd_path} doesn't exist"

    # map_ids = set()
    total_errors = 0

    fns = sorted(path.glob("*.xml"))
    for input_file in fns:
        print(f"Validating {input_file}")
        errors = 0

        # Check XML validity
        errors += validate(input_file)

        # Additionally check if adjacent right/left is always assigned respectively
        scenario, planning_problem_set = CommonRoadFileReader(input_file).open()

        # TODO improve map verification first
        # if not (res := eval_map(scenario, map_ids))[0:
        #     errors += res[1]

        # Check that no obstacle is off the road all the time
        errors += check_obstacle_off_road(scenario)

        total_errors += errors

    if total_errors > 0:
        print(f"{total_errors} Errors where detected")
        raise ValueError
    else:
        print("No errors")
