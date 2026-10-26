"""Repair the rounD maps in crdata/datasets/rounD/maps.

0. Duplicates: lanelets with the same bounds as a lanelet with a lower id are removed.
1. Diagonal edges: a dead end whose end edge runs diagonally across a neighbouring
   lanelet x (one corner at x's start, the other at x's end) is extended over x and
   linked to x's successors. Lanelets without predecessor are handled mirrored.
2. Broken links: existing links whose ends do not meet are repaired by moving the
   mismatched corner if the other corner already meets and the gap is at most
   MAX_CORNER_MOVE; all other broken links are removed.
3. Touching joints: lanelet ends and starts closer than SNAP_TOLERANCE are snapped
   together and linked.
4. Short arms: dead ends at the map boundary are extended until they cover all
   recorded vehicle states in front of them plus ARM_MARGIN, but stop before they
   would overlap other lanelets. Off-map states only count for the lanelet where their
   vehicle enters or leaves the map. Extensions are straight, except for the lanelets in
   CURVED_ARMS, which continue their own curvature and are extended last.

Afterwards, every successor link must satisfy predecessor end == successor start.

usage: poetry run python scripts/fix_round_maps.py <round_dataset_dir>
"""

import copy
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import shapely
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from lxml import etree

from crdata.conversion.util.yaml import load_yaml

ROUND_DIR = Path(__file__).parents[1] / "crdata/datasets/rounD"
DIAGONAL_TOLERANCE = 0.1  # m
SNAP_TOLERANCE = 0.5  # m
MAX_CORNER_MOVE = 3.0  # m
SNAP_MAX_HEADING = np.radians(30)
ARM_MARGIN = 5.0  # m
ARM_MAX_EXTENSION = 60.0  # m, ignore states further away
ARM_CURVATURE_LENGTH = 15.0  # m of centerline used to estimate an arm's curvature
ARM_STEP = 2.0  # m between new vertices of curved extensions
#: Curved slip lanes whose straight extension would cut into neighbouring lanelets
CURVED_ARMS = {"DEU_Neuweiler-1": {102, 135}}
VEHICLES = {"car", "truck", "van", "bus", "trailer", "motorcycle"}
PARKED_MAX_EXTENT = 1.0  # m


def vertex(lanelet: Lanelet, side: str, index: int) -> np.ndarray:
    return (lanelet.left_vertices if side == "left" else lanelet.right_vertices)[index]


def set_bounds(lanelet: Lanelet, left: np.ndarray, right: np.ndarray) -> None:
    lanelet.left_vertices, lanelet.right_vertices = left, right
    lanelet.center_vertices = (left + right) / 2


def set_vertex(lanelet: Lanelet, side: str, index: int, point: np.ndarray) -> None:
    left, right = lanelet.left_vertices.copy(), lanelet.right_vertices.copy()
    (left if side == "left" else right)[index] = point
    set_bounds(lanelet, left, right)


def link(a: Lanelet, b: Lanelet) -> None:
    a.add_successor(b.lanelet_id)
    b.add_predecessor(a.lanelet_id)


def close(p: np.ndarray, q: np.ndarray, tolerance: float) -> bool:
    return bool(np.linalg.norm(p - q) < tolerance)


def heading(points: np.ndarray) -> float:
    d = points[1] - points[0]
    return float(np.arctan2(d[1], d[0]))


def remove_duplicates(ln: LaneletNetwork) -> list[str]:
    """Remove lanelets whose bounds equal those of a lanelet with a lower id.

    :param ln: lanelet network, modified in place
    :return: description of every removed lanelet
    """
    fixes = []
    kept = {}
    for lanelet in sorted(ln.lanelets, key=lambda la: la.lanelet_id):
        bounds = (lanelet.left_vertices.tobytes(), lanelet.right_vertices.tobytes())
        if bounds in kept:
            ln.remove_lanelet(lanelet.lanelet_id)
            fixes.append(f"{lanelet.lanelet_id} duplicates {kept[bounds]}, removed")
        else:
            kept[bounds] = lanelet.lanelet_id
    return fixes


def fix_diagonal_edges(ln: LaneletNetwork) -> list[str]:
    fixes = []
    by_id = {lanelet.lanelet_id: lanelet for lanelet in ln.lanelets}
    for a in ln.lanelets:
        for x in ln.lanelets:
            if x is a:
                continue
            for side, other in (("left", "right"), ("right", "left")):
                if not a.successor and (
                    close(vertex(a, side, -1), vertex(x, side, 0), DIAGONAL_TOLERANCE)
                    and close(
                        vertex(a, other, -1), vertex(x, other, -1), DIAGONAL_TOLERANCE
                    )
                ):
                    set_vertex(a, side, -1, vertex(x, side, -1))
                    for s in x.successor:
                        link(a, by_id[s])
                    fixes.append(
                        f"{a.lanelet_id} end over {x.lanelet_id} -> {x.successor}"
                    )
                if not a.predecessor and (
                    close(vertex(a, side, 0), vertex(x, side, -1), DIAGONAL_TOLERANCE)
                    and close(
                        vertex(a, other, 0), vertex(x, other, 0), DIAGONAL_TOLERANCE
                    )
                ):
                    set_vertex(a, side, 0, vertex(x, side, 0))
                    for p in x.predecessor:
                        link(by_id[p], a)
                    fixes.append(
                        f"{x.predecessor} -> {a.lanelet_id} start over {x.lanelet_id}"
                    )
    return fixes


def repair_broken_links(ln: LaneletNetwork) -> list[str]:
    fixes = []
    by_id = {lanelet.lanelet_id: lanelet for lanelet in ln.lanelets}
    for a in ln.lanelets:
        for b in [by_id[s] for s in a.successor]:
            gaps = {
                side: np.linalg.norm(vertex(a, side, -1) - vertex(b, side, 0))
                for side in ("left", "right")
            }
            if max(gaps.values()) < DIAGONAL_TOLERANCE:
                continue
            side = max(gaps, key=gaps.get)
            if (
                min(gaps.values()) < DIAGONAL_TOLERANCE
                and gaps[side] <= MAX_CORNER_MOVE
            ):
                # Move the corner on the side that has no other link at this joint
                if a.successor == [b.lanelet_id]:
                    set_vertex(a, side, -1, vertex(b, side, 0))
                    fixes.append(
                        f"{a.lanelet_id} -> {b.lanelet_id}: moved {a.lanelet_id}'s end-{side} {gaps[side]:.2f} m"
                    )
                    continue
                if b.predecessor == [a.lanelet_id]:
                    set_vertex(b, side, 0, vertex(a, side, -1))
                    fixes.append(
                        f"{a.lanelet_id} -> {b.lanelet_id}: moved {b.lanelet_id}'s start-{side} {gaps[side]:.2f} m"
                    )
                    continue
            a.remove_successor(b.lanelet_id)
            b.remove_predecessor(a.lanelet_id)
            fixes.append(
                f"{a.lanelet_id} -> {b.lanelet_id}: removed, ends {gaps['left']:.1f} / {gaps['right']:.1f} m apart"
            )
    return fixes


def snap_touching(ln: LaneletNetwork) -> list[str]:
    fixes = []
    for a in ln.lanelets:
        for b in ln.lanelets:
            if a is b or b.lanelet_id in a.successor:
                continue
            dh = abs(
                (
                    heading(a.center_vertices[-2:])
                    - heading(b.center_vertices[:2])
                    + np.pi
                )
                % (2 * np.pi)
                - np.pi
            )
            if (
                dh < SNAP_MAX_HEADING
                and close(vertex(a, "left", -1), vertex(b, "left", 0), SNAP_TOLERANCE)
                and close(vertex(a, "right", -1), vertex(b, "right", 0), SNAP_TOLERANCE)
            ):
                link(a, b)
                fixes.append(f"{a.lanelet_id} -> {b.lanelet_id}")
    # Snap every joint (all ends and starts connected by links) to the mean of its
    # points; joints spread wider than SNAP_TOLERANCE are wrong links, not noise
    joints = nx.Graph()
    for a in ln.lanelets:
        for s in a.successor:
            joints.add_edge(("end", a.lanelet_id), ("start", s))
    by_id = {lanelet.lanelet_id: lanelet for lanelet in ln.lanelets}
    for joint in nx.connected_components(joints):
        members = [
            (by_id[i], -1 if where == "end" else 0) for where, i in sorted(joint)
        ]
        means = {}
        for side in ("left", "right"):
            points = np.array([vertex(lanelet, side, i) for lanelet, i in members])
            means[side] = points.mean(axis=0)
            spread = np.linalg.norm(points - means[side], axis=1).max()
            if spread > SNAP_TOLERANCE:
                fixes.append(
                    f"NOT snapped, points {spread:.1f} m apart: {sorted(joint)}"
                )
                break
        else:
            for side, mean in means.items():
                for lanelet, i in members:
                    set_vertex(lanelet, side, i, mean)
    return fixes


def lanelet_area(ln: LaneletNetwork):
    # Some converted lanelets have self-intersecting outlines
    return shapely.union_all(
        [
            shapely.make_valid(
                shapely.Polygon(
                    np.concatenate(
                        [lanelet.right_vertices, lanelet.left_vertices[::-1]]
                    )
                )
            )
            for lanelet in ln.lanelets
        ]
    )


def vehicle_states(
    data_dir: Path, location: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Positions of moving vehicles at a location (every 5th state, sorted by track and
    time), their track keys, and the first position of every track."""
    states, keys, firsts = [], [], []
    for meta_path in sorted(data_dir.glob("*_recordingMeta.csv")):
        if int(pd.read_csv(meta_path).locationId[0]) != location:
            continue
        prefix = meta_path.name.split("_")[0]
        tracks = pd.read_csv(
            data_dir / f"{prefix}_tracks.csv",
            usecols=["trackId", "frame", "xCenter", "yCenter"],
        )
        meta = pd.read_csv(data_dir / f"{prefix}_tracksMeta.csv")
        tracks = tracks[tracks.trackId.isin(meta.trackId[meta["class"].isin(VEHICLES)])]
        positions = tracks.groupby("trackId")[["xCenter", "yCenter"]]
        extent = positions.max() - positions.min()
        moving = extent.index[
            np.hypot(extent.xCenter, extent.yCenter) >= PARKED_MAX_EXTENT
        ]
        tracks = tracks[tracks.trackId.isin(moving)].sort_values(["trackId", "frame"])
        states.append(tracks[["xCenter", "yCenter"]].values[::5])
        keys.append(int(prefix) * 100_000 + tracks.trackId.values[::5])
        firsts.append(tracks.groupby("trackId")[["xCenter", "yCenter"]].first().values)
    return np.vstack(states), np.concatenate(keys), np.vstack(firsts)


def edge_curvature(lanelet: Lanelet, index: int) -> float:
    """Signed curvature of the centerline near an edge, in outward direction."""
    center = lanelet.center_vertices if index == -1 else lanelet.center_vertices[::-1]
    segments = np.diff(center, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    headings = np.unwrap(np.arctan2(segments[:, 1], segments[:, 0]))
    first = len(segments) - 1
    while first > 0 and lengths[first:].sum() < ARM_CURVATURE_LENGTH:
        first -= 1
    if first == len(segments) - 1:
        return 0.0
    # heading change between the midpoints of the first and the last segment
    distance = (lengths[first] + lengths[-1]) / 2 + lengths[first + 1 : -1].sum()
    return float((headings[-1] - headings[first]) / distance)


def arc_coordinates(
    points: np.ndarray, start: np.ndarray, direction: np.ndarray, kappa: float
):
    """Distance along and lateral offset from an arc (a line if kappa == 0)."""
    rel = points - start
    if kappa == 0.0:
        return rel @ direction, np.abs(
            rel[:, 0] * direction[1] - rel[:, 1] * direction[0]
        )
    center = start + np.array([-direction[1], direction[0]]) / kappa
    m, v = start - center, points - center
    angle = np.arctan2(m[0] * v[:, 1] - m[1] * v[:, 0], v @ m)
    return angle / kappa, np.abs(np.linalg.norm(v, axis=1) - 1 / abs(kappa))


def move_along(
    points: np.ndarray,
    start: np.ndarray,
    direction: np.ndarray,
    kappa: float,
    distance: float,
):
    """Rigidly move points along an arc (a line if kappa == 0) through start."""
    if kappa == 0.0:
        return points + distance * direction
    center = start + np.array([-direction[1], direction[0]]) / kappa
    a = distance * kappa
    rotation = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return (points - center) @ rotation.T + center


def steps_before_overlap(ln: LaneletNetwork, edges_along: dict) -> int:
    """Number of extension steps before the first one overlapping another lanelet."""
    others = shapely.union_all(
        [
            shapely.make_valid(
                shapely.Polygon(
                    np.concatenate(
                        [lanelet.right_vertices, lanelet.left_vertices[::-1]]
                    )
                )
            )
            for lanelet in ln.lanelets
            if lanelet.lanelet_id not in edges_along
        ]
    )
    steps = len(next(iter(edges_along.values()))) - 1
    for k in range(1, steps + 1):
        for along in edges_along.values():
            (l0, r0), (l1, r1) = along[k - 1], along[k]
            if shapely.Polygon([l0, l1, r1, r0]).intersection(others).area > 0.1:
                return k - 1
    return steps


def extend_arms(
    ln: LaneletNetwork, states: np.ndarray, keys: np.ndarray, curved: set[int]
) -> list[str]:
    area = lanelet_area(ln)
    hull = area.convex_hull
    on_map = shapely.contains_xy(area, states[:, 0], states[:, 1])
    # Outward edges: ends without successor and starts without predecessor that point
    # out of the map; once outside the convex hull, the extension cannot cross the map
    edges = {}
    for lanelet in ln.lanelets:
        if any(t.value == "sidewalk" for t in lanelet.lanelet_type):
            continue
        candidates = []
        if not lanelet.successor:
            candidates.append(
                (-1, lanelet.center_vertices[-1] - lanelet.center_vertices[-2])
            )
        if not lanelet.predecessor:
            candidates.append(
                (0, lanelet.center_vertices[0] - lanelet.center_vertices[1])
            )
        for i, d in candidates:
            d = d / np.linalg.norm(d)
            if not shapely.contains_xy(hull, *(lanelet.center_vertices[i] + 2.0 * d)):
                edges[(lanelet.lanelet_id, i)] = (lanelet, i, d)
    # Edges sharing a boundary point (adjacent lanes of one arm) are extended together
    groups = nx.Graph()
    groups.add_nodes_from(edges)
    for k1, (l1, i1, _) in edges.items():
        for k2, (l2, i2, _) in edges.items():
            points1 = [vertex(l1, s, i1) for s in ("left", "right")]
            points2 = [vertex(l2, s, i2) for s in ("left", "right")]
            if k1 < k2 and any(
                close(p, q, DIAGONAL_TOLERANCE) for p in points1 for q in points2
            ):
                groups.add_edge(k1, k2)
    # Curved groups last: straight arms keep their length, curved ones stop before them
    plans = []
    for group in sorted(
        nx.connected_components(groups),
        key=lambda g: (all(k[0] in curved for k in g), sorted(g)),
    ):
        members = [edges[k] for k in sorted(group)]
        direction = np.mean([d for _, _, d in members], axis=0)
        direction /= np.linalg.norm(direction)
        start = np.mean(
            [
                (vertex(lanelet, "left", i) + vertex(lanelet, "right", i)) / 2
                for lanelet, i, _ in members
            ],
            axis=0,
        )
        kappa = 0.0
        if all(lanelet.lanelet_id in curved for lanelet, _, _ in members):
            kappa = float(
                np.mean([edge_curvature(lanelet, i) for lanelet, i, _ in members])
            )
        plans.append((group, members, direction, start, kappa))

    # An off-map state belongs to the lanelets where its vehicle is first (before
    # entering) or last (after leaving) seen on the map
    anchors = np.full(len(states), -1)
    boundaries = np.flatnonzero(np.diff(keys)) + 1
    for track in np.split(np.arange(len(states)), boundaries):
        inside = track[on_map[track]]
        if len(inside):
            anchors[track[track < inside[0]]] = inside[0]
            anchors[track[track > inside[-1]]] = inside[-1]
    off = np.flatnonzero(anchors >= 0)
    polygons = {
        lanelet.lanelet_id: shapely.make_valid(
            shapely.Polygon(
                np.concatenate([lanelet.right_vertices, lanelet.left_vertices[::-1]])
            )
        )
        for lanelet in ln.lanelets
    }
    anchor_points = states[anchors[off]]
    distance = {}
    for g, (_, members, direction, _, kappa) in enumerate(plans):
        for lanelet, i, d in members:
            owned = off[
                shapely.contains_xy(
                    polygons[lanelet.lanelet_id],
                    anchor_points[:, 0],
                    anchor_points[:, 1],
                )
            ]
            if not len(owned):
                continue
            mid = (vertex(lanelet, "left", i) + vertex(lanelet, "right", i)) / 2
            s, _ = arc_coordinates(
                states[owned], mid, d if kappa == 0.0 else direction, kappa
            )
            ahead = s[(s > 0) & (s <= ARM_MAX_EXTENSION)]
            if len(ahead):
                distance[g] = max(distance.get(g, 0.0), float(ahead.max()))

    fixes = []
    for g, (group, members, direction, start, kappa) in enumerate(plans):
        if g not in distance:
            continue
        required = distance[g]
        length = required + ARM_MARGIN
        steps = int(np.ceil(length / ARM_STEP))
        edges_along = {
            lanelet.lanelet_id: [
                move_along(
                    np.array([vertex(lanelet, "left", i), vertex(lanelet, "right", i)]),
                    start,
                    direction,
                    kappa,
                    length * k / steps,
                )
                for k in range(steps + 1)
            ]
            for lanelet, i, _ in members
        }
        kept = steps_before_overlap(ln, edges_along)
        if kept == 0:
            continue
        length *= kept / steps
        for lanelet, i, _ in members:
            along = edges_along[lanelet.lanelet_id]
            # curved: one vertex per step; straight: only the last one
            new = along[1 : kept + 1] if kappa != 0.0 else along[kept : kept + 1]
            new_left, new_right = (
                np.array([p[0] for p in new]),
                np.array([p[1] for p in new]),
            )
            if i == -1:
                set_bounds(
                    lanelet,
                    np.vstack([lanelet.left_vertices, new_left]),
                    np.vstack([lanelet.right_vertices, new_right]),
                )
            else:
                set_bounds(
                    lanelet,
                    np.vstack([new_left[::-1], lanelet.left_vertices]),
                    np.vstack([new_right[::-1], lanelet.right_vertices]),
                )
        shape = "straight" if kappa == 0.0 else f"curved, radius {abs(1 / kappa):.0f} m"
        fixes.append(f"{sorted(k[0] for k in group)} by {length:.1f} m, {shape}")
    return fixes


def set_points(bound, vertices: np.ndarray) -> None:
    """Replace the points of an XML bound if they differ from the vertices.

    Compared as written (4 decimals), not with a tolerance: joints must match exactly, or
    the lanelet union keeps a hairline slit along them that off-road checks report.
    """
    points = bound.findall("point")
    old = [(float(p.findtext("x")), float(p.findtext("y"))) for p in points]
    new = [(float(f"{x:.4f}"), float(f"{y:.4f}")) for x, y in vertices]
    if old == new:
        return
    index = list(bound).index(points[0])
    tails = (points[0].tail, points[-1].tail)
    for p in points:
        bound.remove(p)
    for k, vertex_ in enumerate(new):
        # Keep unchanged points verbatim to keep the diff small
        same = [p for p, o in zip(points, old) if o == vertex_]
        point = copy.deepcopy(same[0] if same else points[0])
        if not same:
            point.find("x").text, point.find("y").text = (f"{c:.4f}" for c in vertex_)
        point.tail = tails[1] if k == len(vertices) - 1 else tails[0]
        bound.insert(index + k, point)


def insert_link(element, tag: str, ref: int) -> None:
    """Insert a predecessor/successor reference in the order the XML schema requires."""
    order = (
        ["rightBound", "predecessor"]
        if tag == "predecessor"
        else ["rightBound", "predecessor", "successor"]
    )
    anchor = [child for child in element if child.tag in order][-1]
    link = etree.Element(tag, ref=str(ref))
    link.tail = anchor.tail
    anchor.addnext(link)


def write_changes(path: Path, ln: LaneletNetwork) -> None:
    """Write changed bounds and links into the map file, leaving everything else as is.

    :param path: map file, overwritten
    :param ln: repaired lanelet network; lanelets missing in it are removed from the file
    """
    tree = etree.parse(str(path))
    for element in list(tree.getroot().iter("lanelet")):
        lanelet = ln.find_lanelet_by_id(int(element.get("id")))
        if lanelet is None:
            element.getparent().remove(element)
            continue
        set_points(element.find("leftBound"), lanelet.left_vertices)
        set_points(element.find("rightBound"), lanelet.right_vertices)
        for tag, refs in (
            ("predecessor", lanelet.predecessor),
            ("successor", lanelet.successor),
        ):
            existing = set()
            for e in element.findall(tag):
                ref = int(e.get("ref"))
                if ref not in refs or ref in existing:
                    element.remove(e)
                existing.add(ref)
            for ref in refs:
                if ref not in existing:
                    insert_link(element, tag, ref)
        for tag, ref in (
            ("adjacentLeft", lanelet.adj_left),
            ("adjacentRight", lanelet.adj_right),
        ):
            e = element.find(tag)
            if e is not None and ref is None:
                element.remove(e)
    tree.write(str(path), xml_declaration=True, encoding="UTF-8")
    with open(path, "a") as f:
        f.write("\n")


def report(
    name: str, ln: LaneletNetwork, states: np.ndarray, firsts: np.ndarray
) -> None:
    by_id = {lanelet.lanelet_id: lanelet for lanelet in ln.lanelets}
    broken = [
        (a.lanelet_id, s)
        for a in ln.lanelets
        for s in a.successor
        if not (
            np.array_equal(a.left_vertices[-1], by_id[s].left_vertices[0])
            and np.array_equal(a.right_vertices[-1], by_id[s].right_vertices[0])
        )
    ]
    graph = nx.DiGraph([(a.lanelet_id, s) for a in ln.lanelets for s in a.successor])
    graph.add_nodes_from(by_id)
    area = lanelet_area(ln)
    on = shapely.contains_xy(area, states[:, 0], states[:, 1]).mean()
    first_off = 1 - shapely.contains_xy(area, firsts[:, 0], firsts[:, 1]).mean()
    print(
        f"  {name}: states on map {on:.1%}, tracks starting off map {first_off:.1%}, "
        f"lane graph components {nx.number_weakly_connected_components(graph)}, "
        f"links with end != start {broken}"
    )


def main(dataset_dir: Path) -> None:
    locations = load_yaml(str(ROUND_DIR / "config.yaml"))["locations"]
    for location, map_name in locations.items():
        path = ROUND_DIR / "maps" / f"{map_name}.xml"
        ln = CommonRoadFileReader(str(path)).open()[0].lanelet_network
        states, keys, firsts = vehicle_states(dataset_dir / "data", location)
        print(map_name)
        report("before", ln, states, firsts)
        for step in (
            remove_duplicates,
            fix_diagonal_edges,
            repair_broken_links,
            snap_touching,
        ):
            for fix in step(ln):
                print(f"  {step.__name__}: {fix}")
        for fix in extend_arms(ln, states, keys, CURVED_ARMS.get(map_name, set())):
            print(f"  extend_arms: {fix}")
        write_changes(path, ln)
        report(
            "after",
            CommonRoadFileReader(str(path)).open()[0].lanelet_network,
            states,
            firsts,
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
