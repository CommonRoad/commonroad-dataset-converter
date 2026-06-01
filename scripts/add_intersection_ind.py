import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
from commonroad.common.common_lanelet import LaneletType
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.writer.file_writer_interface import OverwriteExistingFile
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement


def find_left_of(lanelet_network, incomings):
    """
    Assign the closest valid left-side incoming to each incoming.

    The assigned value is stored as:
        incoming.left_of = <incoming_id>

    Only one closest incoming is assigned because incoming.left_of is an int.
    """
    LANE_SEGMENT_ANGLE = 30

    def _incoming_direction(incoming):
        vectors = []

        for lanelet_id in sorted(incoming.incoming_lanelets):
            lanelet = lanelet_network.find_lanelet_by_id(lanelet_id)
            center_vertices = lanelet.center_vertices

            if len(center_vertices) < 2:
                continue

            # Use the local direction close to the intersection.
            start_idx = max(0, len(center_vertices) - 3)
            vec = center_vertices[-1] - center_vertices[start_idx]

            norm = np.linalg.norm(vec)
            if norm > 1e-9:
                vectors.append(vec / norm)

        if len(vectors) == 0:
            return None

        # Average directions over all lanelets of this incoming.
        # This makes multi-lane incomings more robust than choosing one lanelet.
        direction = np.mean(vectors, axis=0)
        norm = np.linalg.norm(direction)

        if norm <= 1e-9:
            return None

        return direction / norm

    def _angle_deg(vec):
        # Convert direction vector to an angle in [0, 360).
        angle = np.degrees(np.arctan2(vec[1], vec[0]))
        if angle < 0:
            angle += 360.0
        return angle

    incoming_angles = []

    for idx, incoming in enumerate(incomings):
        direction = _incoming_direction(incoming)

        if direction is None:
            incoming.left_of = None
            continue

        incoming_angles.append(
            {
                "index": idx,
                "incoming": incoming,
                "angle": _angle_deg(direction),
            }
        )

    if len(incoming_angles) == 0:
        return incomings

    # Sort by angle to make the assignment deterministic.
    incoming_angles.sort(key=lambda item: item["angle"])

    min_valid_angle = LANE_SEGMENT_ANGLE
    max_valid_angle = 180.0 - LANE_SEGMENT_ANGLE

    for current in incoming_angles:
        current_angle = current["angle"]

        best_candidate = None
        best_diff = float("inf")

        for candidate in incoming_angles:
            if candidate["index"] == current["index"]:
                continue

            candidate_angle = candidate["angle"]

            # Same convention as the original implementation:
            # candidate is left of current if current_angle - candidate_angle
            # lies in the valid left-side angular range.
            diff = current_angle - candidate_angle
            if diff < 0:
                diff += 360.0

            # Ignore nearly parallel incomings and opposite-side incomings.
            if min_valid_angle < diff <= max_valid_angle and diff < best_diff:
                best_diff = diff
                best_candidate = candidate

        if best_candidate is None:
            incoming = current["incoming"]
            incoming.left_of = None
        else:
            incoming = current["incoming"]
            incoming.left_of = best_candidate["incoming"].incoming_id

    print("=== Left-of incoming assignment ===")
    for item in incoming_angles:
        incoming = item["incoming"]
        angle = item["angle"]
        left_of = getattr(incoming, "left_of", None)

        print(
            f"incoming {incoming.incoming_id} "
            f"(angle={angle:.2f} deg) left_of: {left_of}"
        )

    return incomings


file_path = "maps/"
file_name = "DEU_AachenHeckstrasse-1_old"
# file_name = "DEU_AachenAseag-1_old"
scenario, planning_problem_set = CommonRoadFileReader(
    os.path.join(file_path, file_name + ".xml")
).open()

intersections = []


# intersection for AachenAseag
# inc_1 = IntersectionIncomingElement(incoming_id=scenario.generate_object_id(),
#                                     incoming_lanelets={139, 140, 143, 144,152, 135, 141, 147,148, 150},
#                                     successors_straight={155, 157, 202, 153, 154, 206},
#                                     successors_left={214, 212},
#                                     successors_right=set())
# intersections.append(inc_1)
# # todo: add other incomings
# inc_2 = IntersectionIncomingElement(incoming_id=scenario.generate_object_id(), incoming_lanelets={171, 168},
#                                     successors_straight={166, 164, 163,  159, 158, 167, 165, 162, 161, 160},
#                                     successors_left=set(),
#                                     successors_right={173, 233, 234, 213})
# intersections.append(inc_2)
#
# inc_4 = IntersectionIncomingElement(incoming_id=scenario.generate_object_id(), incoming_lanelets={195, 246, 192, 194},
#                                     successors_straight=set(),
#                                     successors_left={197, 196, 199},
#                                     successors_right={216, 215, 217, 225 })
# intersections.append(inc_4)

# intersection for AachenHeckstrasse
inc_1 = IntersectionIncomingElement(
    incoming_id=scenario.generate_object_id(),
    incoming_lanelets={124, 123, 125, 127, 128},
    successors_straight=set(),
    successors_left={155, 151},
    successors_right={136},
)
intersections.append(inc_1)
inc_2 = IntersectionIncomingElement(
    incoming_id=scenario.generate_object_id(),
    incoming_lanelets={105, 108},
    successors_straight=set(),
    successors_left={107},
    successors_right=set(),
)
intersections.append(inc_2)
inc_3 = IntersectionIncomingElement(
    incoming_id=scenario.generate_object_id(),
    incoming_lanelets={115, 142, 117, 150, 111},
    successors_straight={152, 132, 129},
    successors_left=set(),
    successors_right=set(),
)
intersections.append(inc_3)

inc_4 = IntersectionIncomingElement(
    incoming_id=scenario.generate_object_id(),
    incoming_lanelets={102, 130},
    successors_straight={131, 135, 143},
    successors_left=set(),
    successors_right=set(),
)
intersections.append(inc_4)

intersections = find_left_of(scenario.lanelet_network, intersections)

for inc in intersections:
    successors = inc.successors_straight | inc.successors_left | inc.successors_right
    for lanelet_id in list(successors):
        lanelet = scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
        lanelet.lanelet_type = lanelet.lanelet_type | {LaneletType.INTERSECTION}


intersection = Intersection(
    intersection_id=scenario.generate_object_id(), incomings=intersections
)

scenario.lanelet_network.add_intersection(intersection)
author = scenario.author
affiliation = scenario.affiliation
source = scenario.source
tags = scenario.tags

# write new scenario
fw = CommonRoadFileWriter(
    scenario, planning_problem_set, author, affiliation, source, tags
)

file_name = "maps/" + file_name[:-4] + ".xml"
fw.write_to_file(file_name, OverwriteExistingFile.ALWAYS)

fig, ax = plt.subplots(figsize=(25, 10))
rnd = MPRenderer(ax=ax)
# rnd.draw_params.lanelet_network.lanelet.show_label = True
rnd.draw_params.lanelet_network.intersection.show_label = True
rnd.draw_params.lanelet_network.intersection.draw_intersections = True
rnd.draw_params.lanelet_network.intersection.draw_incoming_lanelets = True
rnd.draw_params.lanelet_network.intersection.show_label = True
rnd.draw_params.lanelet_network.intersection.successors_left_color = "red"
rnd.draw_params.lanelet_network.intersection.successors_right_color = "blue"
rnd.draw_params.lanelet_network.intersection.successors_straight_color = "green"
scenario.draw(rnd)
planning_problem_set.draw(rnd)
for sign in scenario.lanelet_network.traffic_signs:
    sign.draw(rnd)
rnd.render(show=False)
rnd.ax.set_title(file_name, pad=12)

plt.tight_layout()
plt.show()
