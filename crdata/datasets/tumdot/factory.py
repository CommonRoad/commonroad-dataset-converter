from pathlib import Path

from crdata.conversion.tabular.factory import (
    TabularConverterFactory,
)
from .implementation import (
    TumdotRecordingGenerator,
    TumdotWindowMeta,
    TumdotMetaScenarioCreator,
)


class TumdotConverterFactory(TabularConverterFactory[TumdotWindowMeta]):
    input_dir: Path

    def build_recording_generator(self) -> TumdotRecordingGenerator:
        return TumdotRecordingGenerator(self.input_dir)

    def build_meta_scenario_creator(self) -> TumdotMetaScenarioCreator:
        return TumdotMetaScenarioCreator()
