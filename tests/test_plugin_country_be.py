# Copyright 2026 natashaklum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import unittest
from decimal import Decimal
from typing import Set

from rp2.plugin.country.be import (
    BE,
    apply_belgian_tax,
    rp2_entry,
    split_fee_proportionally,
)
from rp2.rp2_decimal import RP2Decimal


class TestPluginCountryBE(unittest.TestCase):
    def setUp(self) -> None:
        self.country = BE()

    def test_iso_codes(self) -> None:
        self.assertEqual(self.country.country_iso_code, "be")
        self.assertEqual(self.country.currency_iso_code, "eur")

    def test_long_term_capital_gain_period_is_disabled(self) -> None:
        self.assertEqual(self.country.get_long_term_capital_gain_period(), sys.maxsize)

    def test_accounting_methods(self) -> None:
        expected: Set[str] = {"fifo", "hifo", "lifo", "lofo", "moving_average"}
        self.assertEqual(self.country.get_accounting_methods(), expected)
        self.assertEqual(self.country.get_default_accounting_method(), "moving_average")

    def test_report_generators(self) -> None:
        expected: Set[str] = {"open_positions", "rp2_full_report"}
        self.assertEqual(self.country.get_report_generators(), expected)

    def test_default_generation_language(self) -> None:
        self.assertEqual(self.country.get_default_generation_language(), "en")

    def test_entry_point_is_callable(self) -> None:
        self.assertTrue(callable(rp2_entry))

    def test_belgian_tax_flat(self) -> None:
        result = apply_belgian_tax(RP2Decimal("1000"))
        self.assertEqual(result["tax_eur"], RP2Decimal("330"))
        self.assertEqual(result["total_eur"], result["tax_eur"] + result["communal_surcharge_eur"])

    def test_belgian_tax_loss_is_zero(self) -> None:
        result = apply_belgian_tax(RP2Decimal("-50"))
        self.assertEqual(result["total_eur"], RP2Decimal("0"))

    def test_fee_split_proportional(self) -> None:
        lots = {"a": Decimal("100"), "b": Decimal("300")}
        self.assertEqual(split_fee_proportionally(lots, Decimal("40")), {"a": Decimal("10"), "b": Decimal("30")})

    def test_fee_split_zero_falls_back_even(self) -> None:
        lots = {"a": Decimal("0"), "b": Decimal("0")}
        self.assertEqual(split_fee_proportionally(lots, Decimal("10")), {"a": Decimal("5"), "b": Decimal("5")})


if __name__ == "__main__":
    unittest.main()
