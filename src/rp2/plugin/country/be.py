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

# Belgian country plugin for rp2.
# WIB/CIR Art. 90 S1 (divers inkomen, 33% flat + communal surcharge) and
# Art. 37 (beroepsinkomen, progressive). No Spekulationsfrist, no
# GlobalAllocator, no Alt/Neu split. Single cost basis method for the whole run.

import sys
from decimal import Decimal
from typing import Dict, Optional, Set

from rp2.abstract_country import AbstractCountry
from rp2.rp2_decimal import RP2Decimal
from rp2.rp2_main import rp2_main

DIVERS_INKOMEN_RATE = RP2Decimal("0.33")
COMMUNAL_SURCHARGE_DEFAULT = RP2Decimal("0.07")


def apply_belgian_tax(
    gain_loss_eur: RP2Decimal,
    classification: str = "goede_huisvader",
    communal_surcharge: RP2Decimal = COMMUNAL_SURCHARGE_DEFAULT,
    marginal_rate_eur: Optional[RP2Decimal] = None,
) -> Dict[str, RP2Decimal]:
    """Belgian tax on a realised gain (helper, not an rp2 hook).

    Kept in the country plugin so the fork is self-contained; utxoproof
    carries a plain-Decimal mirror for use without the rp2 dependency.
    """
    if gain_loss_eur <= RP2Decimal("0"):
        return {
            "tax_eur": RP2Decimal("0"),
            "communal_surcharge_eur": RP2Decimal("0"),
            "total_eur": RP2Decimal("0"),
        }
    if classification == "speculator":
        rate = marginal_rate_eur if marginal_rate_eur is not None else DIVERS_INKOMEN_RATE
    else:
        rate = DIVERS_INKOMEN_RATE
    tax = gain_loss_eur * rate
    communal = tax * communal_surcharge
    return {
        "tax_eur": tax,
        "communal_surcharge_eur": communal,
        "total_eur": tax + communal,
    }


def split_fee_proportionally(
    lot_values_eur: Dict[str, Decimal],
    total_fee_eur: Decimal,
) -> Dict[str, Decimal]:
    """Proportional fee split across lots; even split on zero total value."""
    if not lot_values_eur:
        return {}
    total_value = sum(lot_values_eur.values(), Decimal("0"))
    if total_value == Decimal("0"):
        per_lot = total_fee_eur / len(lot_values_eur)
        return dict.fromkeys(lot_values_eur, per_lot)
    return {lot_id: (total_fee_eur * value / total_value) for lot_id, value in lot_values_eur.items()}


# Belgium-specific class
class BE(AbstractCountry):
    def __init__(self) -> None:
        super().__init__("be", "eur")

    # Measured in days. Belgium has no holding-period exemption: disposals are
    # taxed at 33% (goede huisvader) or progressive rates (speculator)
    # regardless of holding period, so the generic long/short split is disabled.
    def get_long_term_capital_gain_period(self) -> int:
        return sys.maxsize

    # Default accounting method. SPF Finances expects a consistent methodology
    # across the taxpayer's entire Bitcoin portfolio; moving average is the default.
    def get_default_accounting_method(self) -> str:
        return "moving_average"

    # Set of accounting methods accepted in the country.
    def get_accounting_methods(self) -> Set[str]:
        return {"fifo", "hifo", "lifo", "lofo", "moving_average"}

    # Default set of generators. The Belgian HTML tax report lives in utxoproof;
    # rp2 ships the generic computation reports.
    def get_report_generators(self) -> Set[str]:
        return {
            "open_positions",
            "rp2_full_report",
        }

    # Default language to use at report generation if the user doesn't specify it.
    def get_default_generation_language(self) -> str:
        return "en"


# Belgium-specific entry point
def rp2_entry() -> None:
    rp2_main(BE())
