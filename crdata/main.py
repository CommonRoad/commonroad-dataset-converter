import inspect
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from commonroad.common.file_writer import FileFormat

from crdata.conversion.factory import AbstractConverterFactory
from crdata.conversion.tabular.filters import RoutabilityCheck
from crdata.datasets.exiD import ExiDConverterFactory
from crdata.datasets.highD import HighdConverterFactory
from crdata.datasets.uniD import UnidConverterFactory
from crdata.datasets.INTERACTION import (
    InteractionConverterFactory,
)
from crdata.datasets.inD import IndConverterFactory
from crdata.datasets.mona import MonaConverterFactory
from crdata.datasets.rounD import RounDConverterFactory
from crdata.datasets.sind import SindConverterFactory
from crdata.datasets.tumdot import TumdotConverterFactory

_logger = logging.getLogger(__name__)

cli = typer.Typer(help="Generates CommonRoad scenarios from different datasets")


# TODO: Can be simplified with next CommonRoad release
class CommonRoadFileType(Enum):
    XML = "xml"
    PROTOBUF = "pb"

    def to_type(self) -> FileFormat:
        if self == self.XML:
            return FileFormat.XML
        else:
            return FileFormat.PROTOBUF


def _main(factory: AbstractConverterFactory) -> None:
    start_time = time.time()
    runner = factory.build_runner()
    runner.run()
    elapsed_time = time.time() - start_time
    _logger.info("Elapsed time: %.3f s", elapsed_time)


@cli.callback()
def main(
    ctx: typer.Context,
    input_dir: Path = typer.Argument(..., help="Path to the data folder"),
    output_dir: Path = typer.Argument(
        ..., help="Directory to store generated CommonRoad files"
    ),
    num_time_steps: int = typer.Option(
        150, help="Maximum number of time steps in the CommonRoad scenario"
    ),
    num_planning_problems: int = typer.Option(
        1,
        help="Number of planning problems per CommonRoad scenario. More than one creates a cooperative scenario.",
    ),
    keep_ego: bool = typer.Option(
        False,
        help="Vehicles used for planning problem should be kept in the scenario.",
    ),
    obstacles_start_at_zero: bool = typer.Option(
        False,
        help="The lowest time step in the scenario is set to zero.",
    ),
    downsample: int = typer.Option(1, help="Decrease dt by n*dt"),
    num_processes: int = typer.Option(
        1, help="Number of processes to convert dataset."
    ),
    all_vehicles: bool = typer.Option(
        False,
        help="Create one planning problem/scenario for each valid vehicle. Invalidates num-time-steps.",
    ),
    routability_check: RoutabilityCheck = typer.Option(
        RoutabilityCheck.Strict, help="Check routability of planning_problem"
    ),
    output_type: CommonRoadFileType = typer.Option(
        default="xml", help="File type of CommonRoad scenarios"
    ),
    max_scenarios: Optional[int] = typer.Option(
        None, help="Only create up to n scenarios."
    ),
    samples_per_recording: Optional[int] = typer.Option(
        None, help="Randomly sample n scenarios from each recording."
    ),
    start_time_step: Optional[int] = typer.Option(
        None, help="Start time step for scenario window."
    ),
    end_time_step: Optional[int] = typer.Option(
        None, help="End time step for scenario window."
    ),
    ego_vehicle_id: Optional[int] = typer.Option(
        None, help="ID of the ego-vehicle for the planning problem."
    ),
) -> None:
    # Relay all common parameters to all datasets without repeating the method signature.
    frame = inspect.currentframe()
    assert frame is not None
    f_back = frame.f_back
    assert f_back is not None
    kwargs = inspect.getargvalues(f_back)[3]["kwargs"]
    values = locals()
    params = {
        k: values[k]
        for k in kwargs.keys()
        if k not in ["ctx", "all_vehicles", "output_type"]
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    params["file_writer_type"] = output_type.to_type()
    params["num_time_steps"] = num_time_steps if not all_vehicles else None
    if all_vehicles:
        params["obstacles_start_at_zero"] = True
    params["start_time_step"] = start_time_step
    params["end_time_step"] = end_time_step
    if start_time_step is not None and end_time_step is not None:
        params["num_time_steps"] = end_time_step - start_time_step
    params["ego_vehicle_id"] = ego_vehicle_id
    ctx.obj = params


@cli.command()
def highD(
    ctx: typer.Context,
    num_vertices: int = typer.Option(10, help="Number of straight lane waypoints"),
    shoulder: bool = typer.Option(False, help="Add shoulder lane to map"),
    extend_width: float = typer.Option(0.0, help="Extend width of the outer lanes [m]"),
    keep_direction: bool = typer.Option(
        False,
        help="Prevents rotating the upper driving direction (right to left) by PI",
    ),
    lane_change: bool = typer.Option(
        False, help="Whether only use lane changing vehicles as planning problem"
    ),
) -> None:
    """Convert the highD dataset into CommonRoad scenario(s)."""
    assert extend_width >= 0.0
    factory = HighdConverterFactory(
        num_vertices=num_vertices,
        shoulder=shoulder,
        extend_width=extend_width,
        keep_direction=keep_direction,
        lane_change=lane_change,
        **ctx.obj,
    )
    _main(factory)


@cli.command()
def inD(
    ctx: typer.Context,
) -> None:
    """Convert the inD dataset into CommonRoad scenario(s)."""
    factory = IndConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def uniD(
    ctx: typer.Context,
) -> None:
    """Convert the uniD dataset into CommonRoad scenario(s)"""
    factory = UnidConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def rounD(
    ctx: typer.Context,
) -> None:
    """Convert the rounD dataset into CommonRoad scenario(s)."""
    factory = RounDConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def exid(
    ctx: typer.Context,
) -> None:
    """Convert the exiD dataset into CommonRoad scenario(s)."""
    factory = ExiDConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def interaction(
    ctx: typer.Context,
) -> None:
    """Convert the INTERACTION dataset into CommonRoad scenario(s)."""
    factory = InteractionConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def mona(ctx: typer.Context) -> None:
    """
    Convert the MONA dataset into CommonRoad scenario(s).

    Nomenclature of created scenarios: [map name][day][segment index]-[map version]_[start frame]_T-[ego id]
    """

    factory = MonaConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def sind(
    ctx: typer.Context,
    location: str = typer.Option(
        "Tianjin", help="Location/Map: Changchun, Chongqing, Xian, Tianjin"
    ),
) -> None:
    """Convert the SIND dataset into CommonRoad scenario(s)."""
    ctx.obj["location"] = location
    factory = SindConverterFactory(**ctx.obj)
    _main(factory)


@cli.command()
def tumdot(ctx: typer.Context) -> None:
    """Convert the TUM-DOT dataset into CommonRoad scenario(s)."""
    factory = TumdotConverterFactory(**ctx.obj)
    _main(factory)


if __name__ == "__main__":
    cli()
