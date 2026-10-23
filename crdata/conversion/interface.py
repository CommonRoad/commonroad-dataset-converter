from abc import ABC, ABCMeta, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

JobT = TypeVar("JobT")


class IScenarioJobProducer(ABC, Generic[JobT]):
    """Iterable of independent jobs."""

    @abstractmethod
    def __iter__(self) -> Iterator[JobT]:
        pass


class IScenarioJobConsumer(Generic[JobT], metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, job: JobT) -> None:
        pass
