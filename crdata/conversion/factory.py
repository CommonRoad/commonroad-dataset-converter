from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from typing import Generic, TypeVar, Union

from pydantic import BaseModel

from .util.runner import WorkerRunner

JobT = TypeVar("JobT")


class AbstractConverterFactory(BaseModel, Generic[JobT], ABC):
    """Factory base class for building producer-consumer pipelines."""

    num_processes: int = 1

    @abstractmethod
    def build_job_generator(self) -> Iterable[JobT] | Sequence[JobT]:
        """Build a producer of independently runnable conversions jobs."""

    @abstractmethod
    def build_job_processor(self) -> Callable[[JobT], None]:
        """Build a consumer of independently runnable conversion jobs."""

    def build_job_filter(self) -> Callable[[JobT], bool]:
        """Build a filter function, returning true if a job is accepted."""

        def tautology(job: JobT):
            return True

        return tautology

    def build_runner(self) -> WorkerRunner:
        """Build a runner object running sequentially or parallel."""
        generator = filter(self.build_job_filter(), self.build_job_generator())
        processor = self.build_job_processor()
        runner = WorkerRunner(generator, processor, self.num_processes)
        return runner
