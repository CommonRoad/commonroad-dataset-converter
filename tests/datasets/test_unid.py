import unittest

from tests.tools.base_suite import BaseSuite


class TestUniDConversion(BaseSuite.ConverterSuite):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = "unid"


if __name__ == "__main__":
    unittest.main()
