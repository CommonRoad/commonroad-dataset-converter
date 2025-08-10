import unittest
from pathlib import Path

from crdata.datasets.tumdot.implementation import (
    TumdotRecordingGenerator,
)
from tests.tools.base_suite import BaseSuite


class TestTumdotConversion(BaseSuite.ConverterSuite):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = "tumdot"

    def test_recording_generator(self):
        generator = TumdotRecordingGenerator(Path(self.input_path))
        for r in generator:
            pass


if __name__ == "__main__":
    unittest.main()
